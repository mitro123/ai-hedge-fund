"""
API routes pro backtest funkce.

Tento modul obsahuje všechny API endpointy pro správu a spouštění backtestů,
včetně získávání výsledků, metrik, historie obchodů a dat pro grafy.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse

from app.backend.models.schemas import (
    BacktestAdvancedMetrics,
    BacktestChartData,
    BacktestCreateRequest,
    BacktestListResponse,
    BacktestResultsResponse,
    ChartDataPoint,
    ErrorResponse,
    TradeHistoryItem,
)
from app.backend.services.backtest_service import BacktestService
from app.backend.services.graph import compile_graph
from app.backend.services.portfolio import create_portfolio

router = APIRouter(prefix="/backtest")

# In-memory storage pro backtest výsledky (v produkci by se použila databáze)
backtest_storage: Dict[str, Dict] = {}
backtest_status: Dict[str, str] = {}


def calculate_advanced_metrics(results: List[Dict], portfolio_values: List[Dict]) -> BacktestAdvancedMetrics:
    """Vypočítá pokročilé metriky pro frontend komponenty."""
    if not results or not portfolio_values:
        return BacktestAdvancedMetrics()

    # Převod na DataFrame pro analýzu
    df = pd.DataFrame(portfolio_values)
    if df.empty:
        return BacktestAdvancedMetrics()

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")

    # Základní výpočty
    initial_value = df["Portfolio Value"].iloc[0] if len(df) > 0 else 100000
    final_value = df["Portfolio Value"].iloc[-1] if len(df) > 0 else initial_value
    total_return = (final_value / initial_value - 1) * 100

    # Daily returns
    df["Daily Return"] = df["Portfolio Value"].pct_change().fillna(0)
    returns = df["Daily Return"].dropna()

    if len(returns) == 0:
        return BacktestAdvancedMetrics(total_return=total_return)

    # Annualized return
    trading_days = len(returns)
    if trading_days > 0:
        annualized_return = (((final_value / initial_value) ** (252 / trading_days)) - 1) * 100
    else:
        annualized_return = 0

    # Volatility (annualized)
    volatility = returns.std() * np.sqrt(252) * 100 if len(returns) > 1 else 0

    # Risk metrics
    rolling_max = df["Portfolio Value"].cummax()
    drawdown = (df["Portfolio Value"] - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min() if len(drawdown) > 0 else 0

    # VaR and CVaR (95% confidence)
    var_95 = float(np.percentile(returns * 100, 5)) if len(returns) > 0 else 0.0
    cvar_95 = float(returns[returns <= np.percentile(returns, 5)].mean() * 100) if len(returns) > 0 else 0.0

    # Trading metrics z výsledků
    all_trades = []
    total_trades = 0
    winning_trades = 0
    total_pnl = 0
    wins = []
    losses = []

    for day_result in results:
        for ticker, quantity in day_result.get("executed_trades", {}).items():
            if quantity != 0:
                total_trades += 1
                # Simulace P&L (v reálné aplikaci by se počítalo přesněji)
                price = day_result.get("current_prices", {}).get(ticker, 0)
                trade_value = abs(quantity * price)
                # Zjednodušený výpočet P&L
                pnl = np.random.normal(0, trade_value * 0.02)  # Simulace
                total_pnl += pnl

                if pnl > 0:
                    winning_trades += 1
                    wins.append(pnl)
                else:
                    losses.append(abs(pnl))

    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(np.mean(losses)) if losses else 0.0
    profit_factor = sum(wins) / sum(losses) if losses and sum(losses) > 0 else 0

    # Exposure metrics
    if "Gross Exposure" in df.columns:
        avg_gross_exposure = df["Gross Exposure"].mean()
        avg_net_exposure = df["Net Exposure"].mean()
        avg_long_exposure = df["Long Exposure"].mean()
        avg_short_exposure = df["Short Exposure"].mean()
    else:
        avg_gross_exposure = avg_net_exposure = avg_long_exposure = avg_short_exposure = 0

    # Ratios
    risk_free_rate = 4.34  # 4.34% annual
    excess_return = annualized_return - risk_free_rate
    sharpe_ratio = excess_return / volatility if volatility > 0 else 0

    # Sortino ratio
    negative_returns = returns[returns < 0]
    downside_volatility = negative_returns.std() * np.sqrt(252) * 100 if len(negative_returns) > 1 else 0
    sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0

    # Calmar ratio
    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown < 0 else 0

    return BacktestAdvancedMetrics(
        # Returns metrics
        total_return=total_return,
        annualized_return=annualized_return,
        volatility=volatility,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        calmar_ratio=calmar_ratio,
        # Risk metrics
        max_drawdown=max_drawdown,
        var_95=var_95,
        cvar_95=cvar_95,
        # Trading metrics
        win_rate=win_rate,
        profit_factor=profit_factor,
        avg_win=avg_win,
        avg_loss=avg_loss,
        total_trades=total_trades,
        # Exposure metrics
        avg_gross_exposure=avg_gross_exposure,
        avg_net_exposure=avg_net_exposure,
        avg_long_exposure=avg_long_exposure,
        avg_short_exposure=avg_short_exposure,
    )


def generate_chart_data(results: List[Dict], portfolio_values: List[Dict]) -> BacktestChartData:
    """Generuje data pro interaktivní grafy."""
    if not portfolio_values:
        return BacktestChartData(
            portfolio_value=[], daily_returns=[], drawdown=[], cumulative_returns=[], trade_markers=[]
        )

    # Portfolio value chart
    portfolio_chart = [
        ChartDataPoint(
            date=item["Date"].strftime("%Y-%m-%d") if hasattr(item["Date"], "strftime") else str(item["Date"]),
            value=item["Portfolio Value"],
        )
        for item in portfolio_values
    ]

    # Daily returns chart
    df = pd.DataFrame(portfolio_values)
    if not df.empty:
        df["Daily Return"] = df["Portfolio Value"].pct_change().fillna(0) * 100
        daily_returns_chart = [
            ChartDataPoint(
                date=item["Date"].strftime("%Y-%m-%d") if hasattr(item["Date"], "strftime") else str(item["Date"]),
                value=return_val,
            )
            for item, return_val in zip(portfolio_values[1:], df["Daily Return"].iloc[1:])
        ]
    else:
        daily_returns_chart = []

    # Drawdown chart
    if not df.empty:
        rolling_max = df["Portfolio Value"].cummax()
        drawdown = (df["Portfolio Value"] - rolling_max) / rolling_max * 100
        drawdown_chart = [
            ChartDataPoint(
                date=item["Date"].strftime("%Y-%m-%d") if hasattr(item["Date"], "strftime") else str(item["Date"]),
                value=dd_val,
            )
            for item, dd_val in zip(portfolio_values, drawdown)
        ]
    else:
        drawdown_chart = []

    # Cumulative returns chart
    if not df.empty:
        initial_value = df["Portfolio Value"].iloc[0]
        cumulative_returns = (df["Portfolio Value"] / initial_value - 1) * 100
        cumulative_chart = [
            ChartDataPoint(
                date=item["Date"].strftime("%Y-%m-%d") if hasattr(item["Date"], "strftime") else str(item["Date"]),
                value=cum_ret,
            )
            for item, cum_ret in zip(portfolio_values, cumulative_returns)
        ]
    else:
        cumulative_chart = []

    # Trade markers
    trade_markers = []
    for day_result in results:
        date = day_result.get("date", "")
        for ticker, quantity in day_result.get("executed_trades", {}).items():
            if quantity != 0:
                action = "buy" if quantity > 0 else "sell"
                price = day_result.get("current_prices", {}).get(ticker, 0)
                trade_markers.append(
                    {
                        "date": date,
                        "ticker": ticker,
                        "action": action,
                        "quantity": abs(quantity),
                        "price": price,
                        "value": abs(quantity * price),
                    }
                )

    return BacktestChartData(
        portfolio_value=portfolio_chart,
        daily_returns=daily_returns_chart,
        drawdown=drawdown_chart,
        cumulative_returns=cumulative_chart,
        trade_markers=trade_markers,
    )


def generate_trade_history(results: List[Dict]) -> List[TradeHistoryItem]:
    """Generuje historii obchodů pro frontend."""
    trades = []
    trade_id = 1

    for day_result in results:
        date = day_result.get("date", "")
        current_prices = day_result.get("current_prices", {})
        executed_trades = day_result.get("executed_trades", {})

        for ticker, quantity in executed_trades.items():
            if quantity != 0:
                price = current_prices.get(ticker, 0)
                value = abs(quantity * price)

                # Určení akce
                if quantity > 0:
                    action = "buy"
                else:
                    action = "sell"

                # Simulace P&L (v reálné aplikaci by se počítalo přesněji)
                pnl = np.random.normal(0, value * 0.02) if action == "sell" else None

                trades.append(
                    TradeHistoryItem(
                        id=str(trade_id),
                        date=date,
                        ticker=ticker,
                        action=action,
                        quantity=abs(quantity),
                        price=price,
                        value=value,
                        pnl=pnl,
                        commission=value * 0.001,  # 0.1% commission
                        notes=f"Automated trade based on agent signals",
                    )
                )
                trade_id += 1

    return trades


async def run_backtest_background(backtest_id: str, request: BacktestCreateRequest):
    """Spustí backtest na pozadí."""
    try:
        backtest_status[backtest_id] = "IN_PROGRESS"

        # Kompilace grafu
        graph = compile_graph(
            nodes=request.graph_nodes,
            edges=request.graph_edges,
            agent_models=request.agent_models or [],
            model_name=request.model_name or "gpt-4.1",
            model_provider=request.model_provider.value if request.model_provider else "openrouter",
        )

        # Vytvoření portfolia
        portfolio = create_portfolio(
            initial_cash=request.initial_capital,
            margin_requirement=request.margin_requirement,
            tickers=request.tickers,
            portfolio_positions=request.portfolio_positions or [],
        )

        # Vytvoření backtest service
        backtest_service = BacktestService(
            graph=graph,
            portfolio=portfolio,
            tickers=request.tickers,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            model_name=request.model_name or "gpt-4.1",
            model_provider=request.model_provider.value if request.model_provider else "openrouter",
            request={"api_keys": request.api_keys or {}},
        )

        # Spuštění backtestingu
        results = await backtest_service.run_backtest_async()

        # Uložení výsledků
        backtest_storage[backtest_id] = {
            "id": backtest_id,
            "name": request.name,
            "description": request.description,
            "status": "COMPLETE",
            "created_at": datetime.now(),
            "completed_at": datetime.now(),
            "tickers": request.tickers,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "initial_capital": request.initial_capital,
            "results": results["results"],
            "portfolio_values": results["portfolio_values"],
            "performance_metrics": results["performance_metrics"],
            "final_portfolio": results["final_portfolio"],
        }

        backtest_status[backtest_id] = "COMPLETE"

    except Exception as e:
        backtest_status[backtest_id] = "ERROR"
        backtest_storage[backtest_id] = {
            "id": backtest_id,
            "name": request.name,
            "status": "ERROR",
            "error": str(e),
            "created_at": datetime.now(),
        }


@router.post("/", response_model=Dict[str, str])
async def create_backtest(request: BacktestCreateRequest, background_tasks: BackgroundTasks):
    """
    Vytvoří nový backtest a spustí ho na pozadí.

    Returns:
        Dict obsahující ID backtestingu pro sledování průběhu
    """
    try:
        backtest_id = str(uuid.uuid4())

        # Inicializace záznamu
        backtest_storage[backtest_id] = {
            "id": backtest_id,
            "name": request.name,
            "description": request.description,
            "status": "PENDING",
            "created_at": datetime.now(),
            "tickers": request.tickers,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "initial_capital": request.initial_capital,
        }

        # Spuštění na pozadí
        background_tasks.add_task(run_backtest_background, backtest_id, request)

        return {"backtest_id": backtest_id, "status": "PENDING"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při vytváření backtestingu: {str(e)}")


@router.get("/", response_model=List[BacktestListResponse])
async def list_backtests(limit: int = Query(default=50, le=100), offset: int = Query(default=0, ge=0)):
    """
    Vrátí seznam všech backtestů.

    Args:
        limit: Maximální počet výsledků
        offset: Offset pro stránkování
    """
    try:
        all_backtests = list(backtest_storage.values())
        all_backtests.sort(key=lambda x: x.get("created_at", datetime.now()), reverse=True)

        paginated = all_backtests[offset : offset + limit]

        result = []
        for bt in paginated:
            # Výpočet základních metrik
            final_value = None
            total_return = None

            if bt.get("status") == "COMPLETE" and "portfolio_values" in bt:
                portfolio_values = bt["portfolio_values"]
                if portfolio_values:
                    initial_value = portfolio_values[0].get("Portfolio Value", bt.get("initial_capital", 100000))
                    final_value = portfolio_values[-1].get("Portfolio Value", initial_value)
                    total_return = (final_value / initial_value - 1) * 100

            result.append(
                BacktestListResponse(
                    id=bt["id"],
                    name=bt["name"],
                    status=bt.get("status", "UNKNOWN"),
                    created_at=bt.get("created_at", datetime.now()),
                    completed_at=bt.get("completed_at"),
                    tickers=bt.get("tickers", []),
                    final_value=final_value,
                    total_return=total_return,
                )
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání seznamu backtestů: {str(e)}")


@router.get("/{backtest_id}", response_model=BacktestResultsResponse)
async def get_backtest_results(backtest_id: str):
    """
    Vrátí kompletní výsledky backtestingu včetně všech dat pro frontend.

    Args:
        backtest_id: ID backtestingu
    """
    try:
        if backtest_id not in backtest_storage:
            raise HTTPException(status_code=404, detail="Backtest nenalezen")

        bt = backtest_storage[backtest_id]

        # Základní informace
        response = BacktestResultsResponse(
            id=bt["id"],
            name=bt["name"],
            status=bt.get("status", "UNKNOWN"),
            created_at=bt.get("created_at", datetime.now()),
            completed_at=bt.get("completed_at"),
            tickers=bt.get("tickers", []),
            start_date=bt.get("start_date", ""),
            end_date=bt.get("end_date", ""),
            initial_capital=bt.get("initial_capital", 100000),
        )

        # Pokud je backtest dokončený, přidáme výsledky
        if bt.get("status") == "COMPLETE":
            results = bt.get("results", [])
            portfolio_values = bt.get("portfolio_values", [])

            # Základní metriky
            if portfolio_values:
                initial_value = portfolio_values[0].get("Portfolio Value", bt.get("initial_capital", 100000))
                final_value = portfolio_values[-1].get("Portfolio Value", initial_value)
                total_return = (final_value / initial_value - 1) * 100
                total_trades = sum(len(day.get("executed_trades", {})) for day in results)

                response.final_value = final_value
                response.total_return = total_return
                response.total_trades = total_trades

            # Performance metrics
            response.performance_metrics = bt.get("performance_metrics")

            # Advanced metrics
            response.advanced_metrics = calculate_advanced_metrics(results, portfolio_values)

            # Chart data
            response.chart_data = generate_chart_data(results, portfolio_values)

            # Trade history
            response.trade_history = generate_trade_history(results)

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání výsledků backtestingu: {str(e)}")


@router.get("/{backtest_id}/status")
async def get_backtest_status(backtest_id: str):
    """
    Vrátí aktuální stav backtestingu.

    Args:
        backtest_id: ID backtestingu
    """
    try:
        if backtest_id not in backtest_storage:
            raise HTTPException(status_code=404, detail="Backtest nenalezen")

        bt = backtest_storage[backtest_id]
        status = bt.get("status", "UNKNOWN")

        response = {
            "backtest_id": backtest_id,
            "status": status,
            "created_at": bt.get("created_at"),
            "completed_at": bt.get("completed_at"),
        }

        if status == "ERROR":
            response["error"] = bt.get("error")

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání stavu backtestingu: {str(e)}")


@router.get("/{backtest_id}/metrics", response_model=BacktestAdvancedMetrics)
async def get_backtest_metrics(backtest_id: str):
    """
    Vrátí pokročilé metriky backtestingu.

    Args:
        backtest_id: ID backtestingu
    """
    try:
        if backtest_id not in backtest_storage:
            raise HTTPException(status_code=404, detail="Backtest nenalezen")

        bt = backtest_storage[backtest_id]

        if bt.get("status") != "COMPLETE":
            raise HTTPException(status_code=400, detail="Backtest ještě není dokončený")

        results = bt.get("results", [])
        portfolio_values = bt.get("portfolio_values", [])

        return calculate_advanced_metrics(results, portfolio_values)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání metrik backtestingu: {str(e)}")


@router.get("/{backtest_id}/trades", response_model=List[TradeHistoryItem])
async def get_backtest_trades(
    backtest_id: str,
    ticker: Optional[str] = Query(None, description="Filtr podle tickeru"),
    action: Optional[str] = Query(None, description="Filtr podle akce (buy/sell)"),
    limit: int = Query(default=1000, le=10000),
    offset: int = Query(default=0, ge=0),
):
    """
    Vrátí historii obchodů backtestingu.

    Args:
        backtest_id: ID backtestingu
        ticker: Filtr podle tickeru
        action: Filtr podle akce
        limit: Maximální počet výsledků
        offset: Offset pro stránkování
    """
    try:
        if backtest_id not in backtest_storage:
            raise HTTPException(status_code=404, detail="Backtest nenalezen")

        bt = backtest_storage[backtest_id]

        if bt.get("status") != "COMPLETE":
            raise HTTPException(status_code=400, detail="Backtest ještě není dokončený")

        results = bt.get("results", [])
        trades = generate_trade_history(results)

        # Aplikace filtrů
        if ticker:
            trades = [t for t in trades if t.ticker.upper() == ticker.upper()]

        if action:
            trades = [t for t in trades if t.action.lower() == action.lower()]

        # Stránkování
        paginated_trades = trades[offset : offset + limit]

        return paginated_trades

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání obchodů backtestingu: {str(e)}")


@router.get("/{backtest_id}/charts", response_model=BacktestChartData)
async def get_backtest_charts(backtest_id: str):
    """
    Vrátí data pro interaktivní grafy.

    Args:
        backtest_id: ID backtestingu
    """
    try:
        if backtest_id not in backtest_storage:
            raise HTTPException(status_code=404, detail="Backtest nenalezen")

        bt = backtest_storage[backtest_id]

        if bt.get("status") != "COMPLETE":
            raise HTTPException(status_code=400, detail="Backtest ještě není dokončený")

        results = bt.get("results", [])
        portfolio_values = bt.get("portfolio_values", [])

        return generate_chart_data(results, portfolio_values)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání dat pro grafy: {str(e)}")


@router.delete("/{backtest_id}")
async def delete_backtest(backtest_id: str):
    """
    Smaže backtest.

    Args:
        backtest_id: ID backtestingu
    """
    try:
        if backtest_id not in backtest_storage:
            raise HTTPException(status_code=404, detail="Backtest nenalezen")

        del backtest_storage[backtest_id]
        if backtest_id in backtest_status:
            del backtest_status[backtest_id]

        return {"message": "Backtest byl úspěšně smazán"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při mazání backtestingu: {str(e)}")
