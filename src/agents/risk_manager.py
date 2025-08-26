"""Risk Manager - Manages position sizing based on real risk factors for multiple tickers."""

import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage

from src.exceptions import APIKeyError
from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_prices, prices_to_df
from src.utils.api_key import get_api_key_from_state
from src.utils.progress import progress


# Risk Management Agent
def risk_management_agent(state: AgentState, agent_id: str = "risk_management_agent") -> Dict[str, Any]:
    """Řídí velikost pozic na základě reálných rizikových faktorů pro více tickerů."""
    portfolio = state["data"]["portfolio"]
    data = state["data"]
    tickers = data["tickers"]
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")
    if api_key is None:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")
    # Inicializace rizikové analýzy pro každý ticker
    risk_analysis = {}
    current_prices = {}  # Uložení cen zde pro zamezení redundantních API volání

    # Nejprve načtení cen pro všechny relevantní tickery
    all_tickers = set(tickers) | set(portfolio.get("positions", {}).keys())

    for ticker in all_tickers:
        progress.update_status(agent_id, ticker, "Načítání cenových dat")

        prices = get_prices(
            ticker=ticker,
            start_date=data["start_date"],
            end_date=data["end_date"],
            api_key=api_key,
        )

        if not prices:
            progress.update_status(agent_id, ticker, "Varování: Nenalezena žádná cenová data")
            continue

        prices_df = prices_to_df(prices)

        if not prices_df.empty:
            current_price = prices_df["close"].iloc[-1]
            current_prices[ticker] = current_price
            progress.update_status(agent_id, ticker, f"Aktuální cena: {current_price}")
        else:
            progress.update_status(agent_id, ticker, "Varování: Prázdná cenová data")

    # Výpočet celkové hodnoty portfolia na základě aktuálních tržních cen (Net Liquidation Value)
    total_portfolio_value = portfolio.get("cash", 0.0)

    for ticker, position in portfolio.get("positions", {}).items():
        if ticker in current_prices:
            # Přidání tržní hodnoty long pozic
            total_portfolio_value += position.get("long", 0) * current_prices[ticker]
            # Odečtení tržní hodnoty short pozic
            total_portfolio_value -= position.get("short", 0) * current_prices[ticker]

    progress.update_status(agent_id, None, f"Celková hodnota portfolia: {total_portfolio_value}")

    # Výpočet rizikových limitů pro každý ticker ve vesmíru
    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Výpočet pozičních limitů")

        if ticker not in current_prices:
            progress.update_status(agent_id, ticker, "Selhalo: Žádná cenová data nejsou k dispozici")
            risk_analysis[ticker] = {
                "remaining_position_limit": 0.0,
                "current_price": 0.0,
                "reasoning": {"error": "Chybí cenová data pro výpočet rizika"},
            }
            continue

        current_price = current_prices[ticker]

        # Výpočet aktuální tržní hodnoty této pozice
        position = portfolio.get("positions", {}).get(ticker, {})
        long_value = position.get("long", 0) * current_price
        short_value = position.get("short", 0) * current_price
        current_position_value = abs(long_value - short_value)  # Použití absolutní expozice

        # Výpočet pozičního limitu (20% z celkového portfolia)
        position_limit = total_portfolio_value * 0.20

        # Výpočet zbývajícího limitu pro tuto pozici
        remaining_position_limit = position_limit - current_position_value

        # Zajištění, že nepřekročíme dostupnou hotovost
        max_position_size = min(remaining_position_limit, portfolio.get("cash", 0))

        risk_analysis[ticker] = {
            "remaining_position_limit": float(max_position_size),
            "current_price": float(current_price),
            "reasoning": {
                "portfolio_value": float(total_portfolio_value),
                "current_position_value": float(current_position_value),
                "position_limit": float(position_limit),
                "remaining_limit": float(remaining_position_limit),
                "available_cash": float(portfolio.get("cash", 0)),
            },
        }

        progress.update_status(agent_id, None, "Done")

    message = HumanMessage(
        content=json.dumps(risk_analysis),
        name=agent_id,
    )

    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(risk_analysis, "Risk Management Agent")

    # Přidání signálu do seznamu analyst_signals
    state["data"]["analyst_signals"][agent_id] = risk_analysis

    return {
        "messages": state["messages"] + [message],
        "data": data,
    }
