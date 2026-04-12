"""OpenBB integration endpoints for AI Hedge Fund."""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.agents.openbb_enhanced_agent import get_openbb_enhanced_agent
from src.integrations.openbb_integration import get_openbb_provider

router = APIRouter(prefix="/openbb", tags=["OpenBB Integration"])


class StockAnalysisRequest(BaseModel):
    """Request model for stock analysis."""

    symbol: str
    days: int = 30
    provider: str = "yfinance"


class PortfolioAnalysisRequest(BaseModel):
    """Request model for portfolio analysis."""

    symbols: List[str]
    provider: str = "yfinance"


class PortfolioOptimizationRequest(BaseModel):
    """Request model for portfolio optimization."""

    symbols: List[str]
    objective: str = "max_sharpe"  # max_sharpe, min_volatility, max_return
    constraints: Dict[str, Any] = {"max_weight": 0.4, "min_weight": 0.05, "target_return": None}
    lookback_days: int = 252
    provider: str = "yfinance"


@router.get("/status")
async def get_openbb_status() -> Dict[str, Any]:
    """Get OpenBB integration status."""
    provider = get_openbb_provider()
    return {
        "openbb_available": provider.is_available(),
        "integration_status": "active" if provider.is_available() else "inactive",
        "supported_providers": [
            "yfinance",
            "alpha_vantage",
            "fmp",
            "intrinio",
            "polygon",
            "tiingo",
            "benzinga",
            "fred",
        ],
    }


@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Data interval"),
    provider: str = Query("yfinance", description="Data provider"),
) -> Dict[str, Any]:
    """Get historical price data for a symbol."""
    try:
        openbb_provider = get_openbb_provider()

        if not openbb_provider.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        data = openbb_provider.get_historical_prices(
            symbol=symbol, start_date=start_date, end_date=end_date, interval=interval, provider=provider
        )

        if data is None or data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")

        return {
            "symbol": symbol,
            "provider": provider,
            "interval": interval,
            "data_points": len(data),
            "data": data.to_dict(orient="records"),
        }

    except Exception as e:
        logging.error(f"Error fetching historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/stock")
async def analyze_stock_comprehensive(request: StockAnalysisRequest) -> Dict[str, Any]:
    """Perform comprehensive stock analysis using OpenBB data."""
    try:
        agent = get_openbb_enhanced_agent()

        if not agent.openbb.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        analysis = agent.analyze_stock_comprehensive(
            symbol=request.symbol, days=request.days, provider=request.provider
        )

        return analysis

    except Exception as e:
        logging.error(f"Error in comprehensive stock analysis for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/overview")
async def get_market_overview(provider: str = Query("yfinance", description="Data provider")) -> Dict[str, Any]:
    """Get comprehensive market overview."""
    try:
        agent = get_openbb_enhanced_agent()

        if not agent.openbb.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        overview = agent.get_market_overview(provider=provider)

        return overview

    except Exception as e:
        logging.error(f"Error getting market overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/portfolio")
async def analyze_portfolio_diversification(request: PortfolioAnalysisRequest) -> Dict[str, Any]:
    """Analyze portfolio diversification using OpenBB data."""
    try:
        agent = get_openbb_enhanced_agent()

        if not agent.openbb.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        if len(request.symbols) < 2:
            raise HTTPException(status_code=400, detail="At least 2 symbols required for diversification analysis")

        analysis = agent.analyze_portfolio_diversification(symbols=request.symbols, provider=request.provider)

        return analysis

    except Exception as e:
        logging.error(f"Error in portfolio diversification analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/optimize")
async def optimize_portfolio(request: PortfolioOptimizationRequest) -> Dict[str, Any]:
    """Optimize portfolio using Modern Portfolio Theory."""
    try:
        from datetime import datetime, timedelta

        import numpy as np

        openbb_provider = get_openbb_provider()

        if not openbb_provider.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        if len(request.symbols) < 2:
            raise HTTPException(status_code=400, detail="At least 2 symbols required for optimization")

        if request.objective not in ["max_sharpe", "min_volatility", "max_return"]:
            raise HTTPException(
                status_code=400, detail="Invalid objective. Use: max_sharpe, min_volatility, or max_return"
            )

        # Získání historických dat
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.lookback_days)

        price_data = {}
        for symbol in request.symbols:
            try:
                data = openbb_provider.get_historical_prices(
                    symbol=symbol,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    provider=request.provider,
                )
                if data is not None and not data.empty and "close" in data.columns:
                    price_data[symbol] = data["close"]
                else:
                    logging.warning(f"No price data found for {symbol}")
            except Exception as e:
                logging.warning(f"Error fetching data for {symbol}: {e}")

        if len(price_data) < 2:
            raise HTTPException(status_code=400, detail="Insufficient price data for optimization")

        # Vytvoření DataFrame s cenami
        prices_df = pd.DataFrame(price_data)
        prices_df = prices_df.dropna()

        if len(prices_df) < 30:
            raise HTTPException(status_code=400, detail="Insufficient historical data (minimum 30 days required)")

        # Výpočet výnosů
        returns = prices_df.pct_change().dropna()

        # Základní statistiky
        mean_returns = returns.mean() * 252  # Anualizované výnosy
        cov_matrix = returns.cov() * 252  # Anualizovaná kovariační matice

        # Simulace portfolií pro Efficient Frontier
        num_portfolios = 10000
        results = np.zeros((3, num_portfolios))
        weights_array = np.zeros((num_portfolios, len(request.symbols)))

        np.random.seed(42)

        for i in range(num_portfolios):
            # Generování náhodných vah
            weights = np.random.random(len(request.symbols))
            weights = weights / np.sum(weights)

            # Aplikace omezení
            weights = np.clip(weights, request.constraints["min_weight"], request.constraints["max_weight"])
            weights = weights / np.sum(weights)  # Renormalizace

            weights_array[i] = weights

            # Portfolio výnos
            portfolio_return = np.sum(weights * mean_returns)

            # Portfolio volatilita
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            # Sharpe ratio (předpokládáme risk-free rate 2%)
            risk_free_rate = 0.02
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility

            results[0, i] = portfolio_return
            results[1, i] = portfolio_volatility
            results[2, i] = sharpe_ratio

        # Optimální portfolio podle cíle
        if request.objective == "max_sharpe":
            optimal_idx = np.argmax(results[2])
        elif request.objective == "min_volatility":
            optimal_idx = np.argmin(results[1])
        else:  # max_return
            optimal_idx = np.argmax(results[0])

        optimal_weights = weights_array[optimal_idx]
        optimal_return = results[0, optimal_idx]
        optimal_volatility = results[1, optimal_idx]
        optimal_sharpe = results[2, optimal_idx]

        # Vytvoření výsledků
        assets = []
        for i, symbol in enumerate(request.symbols):
            latest_price = float(prices_df[symbol].iloc[-1])
            price_change = float((prices_df[symbol].iloc[-1] / prices_df[symbol].iloc[-2] - 1) * 100)

            assets.append(
                {
                    "symbol": symbol,
                    "weight": float(optimal_weights[i]),
                    "expected_return": float(mean_returns[symbol]),
                    "volatility": float(np.sqrt(cov_matrix.loc[symbol, symbol])),
                    "current_price": latest_price,
                    "price_change_24h": price_change,
                }
            )

        # Risk metrics
        portfolio_returns = returns.dot(optimal_weights)
        var_95 = float(np.percentile(portfolio_returns, 5) * np.sqrt(252))
        max_drawdown = float((portfolio_returns.cumsum().expanding().max() - portfolio_returns.cumsum()).max())

        # Beta (vs SPY jako benchmark)
        try:
            spy_data = openbb_provider.get_historical_prices(
                symbol="SPY",
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                provider=request.provider,
            )
            if spy_data is not None and not spy_data.empty:
                spy_returns = spy_data["close"].pct_change().dropna()
                # Align dates
                common_dates = portfolio_returns.index.intersection(spy_returns.index)
                if len(common_dates) > 30:
                    portfolio_aligned = portfolio_returns.loc[common_dates]
                    spy_aligned = spy_returns.loc[common_dates]
                    # Convert to numpy arrays for covariance calculation
                    portfolio_array = np.array(portfolio_aligned)
                    spy_array = np.array(spy_aligned)
                    beta = float(np.cov(portfolio_array, spy_array)[0, 1] / np.var(spy_array))
                else:
                    beta = 1.0
            else:
                beta = 1.0
        except:
            beta = 1.0

        # Efficient Frontier body (vzorkování)
        efficient_frontier = []
        for i in range(0, num_portfolios, num_portfolios // 50):  # 50 bodů
            efficient_frontier.append(
                {
                    "return": float(results[0, i]),
                    "risk": float(results[1, i]),
                    "weights": {symbol: float(weights_array[i][j]) for j, symbol in enumerate(request.symbols)},
                }
            )

        return {
            "optimization_objective": request.objective,
            "timestamp": datetime.now().isoformat(),
            "assets": assets,
            "metrics": {
                "expected_return": float(optimal_return),
                "volatility": float(optimal_volatility),
                "sharpe_ratio": float(optimal_sharpe),
                "var_95": var_95,
                "max_drawdown": max_drawdown,
                "beta": beta,
            },
            "efficient_frontier": efficient_frontier,
            "constraints": request.constraints,
            "lookback_days": request.lookback_days,
            "data_points": len(prices_df),
        }

    except Exception as e:
        logging.error(f"Error in portfolio optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/{symbol}")
async def get_company_news(
    symbol: str,
    limit: int = Query(10, description="Number of news items"),
    provider: str = Query("benzinga", description="News provider"),
) -> Dict[str, Any]:
    """Get company-specific news."""
    try:
        openbb_provider = get_openbb_provider()

        if not openbb_provider.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        news = openbb_provider.get_market_news(symbol=symbol, limit=limit, provider=provider)

        if news is None or news.empty:
            return {"symbol": symbol, "news_count": 0, "news": []}

        return {"symbol": symbol, "provider": provider, "news_count": len(news), "news": news.to_dict(orient="records")}

    except Exception as e:
        logging.error(f"Error fetching news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financials/{symbol}")
async def get_financial_statements(
    symbol: str,
    statement_type: str = Query("income", description="Statement type (income, balance, cash)"),
    period: str = Query("annual", description="Period (annual, quarter)"),
    limit: int = Query(5, description="Number of periods"),
    provider: str = Query("fmp", description="Data provider"),
) -> Dict[str, Any]:
    """Get financial statements for a company."""
    try:
        openbb_provider = get_openbb_provider()

        if not openbb_provider.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        if statement_type not in ["income", "balance", "cash"]:
            raise HTTPException(status_code=400, detail="Invalid statement type. Use: income, balance, or cash")

        data = openbb_provider.get_financial_statements(
            symbol=symbol, statement_type=statement_type, period=period, limit=limit, provider=provider
        )

        if data is None or data.empty:
            return {"symbol": symbol, "statement_type": statement_type, "period": period, "data_points": 0, "data": []}

        return {
            "symbol": symbol,
            "statement_type": statement_type,
            "period": period,
            "provider": provider,
            "data_points": len(data),
            "data": data.to_dict(orient="records"),
        }

    except Exception as e:
        logging.error(f"Error fetching {statement_type} statement for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/economic/{indicator}")
async def get_economic_data(
    indicator: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    provider: str = Query("fred", description="Data provider"),
) -> Dict[str, Any]:
    """Get economic indicator data."""
    try:
        openbb_provider = get_openbb_provider()

        if not openbb_provider.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        data = openbb_provider.get_economic_data(
            indicator=indicator, start_date=start_date, end_date=end_date, provider=provider
        )

        if data is None or data.empty:
            return {"indicator": indicator, "data_points": 0, "data": []}

        return {
            "indicator": indicator,
            "provider": provider,
            "data_points": len(data),
            "data": data.to_dict(orient="records"),
        }

    except Exception as e:
        logging.error(f"Error fetching economic data for {indicator}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options/{symbol}")
async def get_options_data(
    symbol: str,
    expiration: Optional[str] = Query(None, description="Expiration date (YYYY-MM-DD)"),
    provider: str = Query("yfinance", description="Data provider"),
) -> Dict[str, Any]:
    """Get options data for a symbol."""
    try:
        openbb_provider = get_openbb_provider()

        if not openbb_provider.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        data = openbb_provider.get_options_data(symbol=symbol, expiration=expiration, provider=provider)

        if data is None:
            return {"symbol": symbol, "calls_count": 0, "puts_count": 0, "calls": [], "puts": []}

        calls_data = data.get("calls", pd.DataFrame())
        puts_data = data.get("puts", pd.DataFrame())

        return {
            "symbol": symbol,
            "provider": provider,
            "expiration": expiration,
            "calls_count": len(calls_data) if calls_data is not None else 0,
            "puts_count": len(puts_data) if puts_data is not None else 0,
            "calls": calls_data.to_dict(orient="records") if calls_data is not None and not calls_data.empty else [],
            "puts": puts_data.to_dict(orient="records") if puts_data is not None and not puts_data.empty else [],
        }

    except Exception as e:
        logging.error(f"Error fetching options data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crypto/{symbol}")
async def get_crypto_data(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Data interval"),
    provider: str = Query("yfinance", description="Data provider"),
) -> Dict[str, Any]:
    """Get cryptocurrency data."""
    try:
        openbb_provider = get_openbb_provider()

        if not openbb_provider.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        data = openbb_provider.get_crypto_data(
            symbol=symbol, start_date=start_date, end_date=end_date, interval=interval, provider=provider
        )

        if data is None or data.empty:
            raise HTTPException(status_code=404, detail=f"No crypto data found for symbol {symbol}")

        return {
            "symbol": symbol,
            "provider": provider,
            "interval": interval,
            "data_points": len(data),
            "data": data.to_dict(orient="records"),
        }

    except Exception as e:
        logging.error(f"Error fetching crypto data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/forex/{symbol}")
async def get_forex_data(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Data interval"),
    provider: str = Query("yfinance", description="Data provider"),
) -> Dict[str, Any]:
    """Get forex data."""
    try:
        openbb_provider = get_openbb_provider()

        if not openbb_provider.is_available():
            raise HTTPException(status_code=503, detail="OpenBB Platform not available")

        data = openbb_provider.get_forex_data(
            symbol=symbol, start_date=start_date, end_date=end_date, interval=interval, provider=provider
        )

        if data is None or data.empty:
            raise HTTPException(status_code=404, detail=f"No forex data found for symbol {symbol}")

        return {
            "symbol": symbol,
            "provider": provider,
            "interval": interval,
            "data_points": len(data),
            "data": data.to_dict(orient="records"),
        }

    except Exception as e:
        logging.error(f"Error fetching forex data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
