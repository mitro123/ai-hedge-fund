"""Agent pro ocenění - Implementuje čtyři komplementární metodologie ocenění a agreguje je s konfiguratelnými váhami."""

import json
from statistics import median
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage

from src.exceptions import APIKeyError
from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_financial_metrics, get_market_cap, search_line_items
from src.utils.api_key import get_api_key_from_state
from src.utils.constants import COMMODITY_SYMBOLS
from src.utils.progress import progress


def valuation_analyst_agent(state: AgentState, agent_id: str = "valuation_analyst_agent") -> Dict[str, Any]:
    """Spustí ocenění napříč tickery a zapíše signály zpět do `state`."""

    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")
    if api_key is None:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")
    valuation_analysis: Dict[str, Dict[str, Any]] = {}

    for ticker in tickers:
        # Skip commodity symbols as valuation analysis is designed for stocks
        if ticker in COMMODITY_SYMBOLS:
            progress.update_status(agent_id, ticker, "Přeskakuji komoditu")
            valuation_analysis[ticker] = {
                "signal": "neutral",
                "confidence": 0.0,
                "reasoning": {
                    "message": f"Oceňovací analýza není vhodná pro komodity ({ticker}). Komodity jsou analyzovány specializovaným komoditním agentem."
                },
            }
            progress.update_status(agent_id, ticker, "Přeskočeno - komodita", analysis="Komodita přeskočena")
            continue
        progress.update_status(agent_id, ticker, "Načítání finančních dat")

        # --- Historické finanční metriky (získání 8 nejnovějších TTM snímků pro mediány) ---
        financial_metrics = get_financial_metrics(
            ticker=ticker,
            end_date=end_date,
            period="ttm",
            limit=8,
            api_key=api_key,
        )
        if not financial_metrics:
            progress.update_status(agent_id, ticker, "Selhalo: Nenalezeny finanční metriky")
            continue
        most_recent_metrics = financial_metrics[0]

        # --- Detailní položky (potřebujeme dvě období pro výpočet změny WC) ---
        progress.update_status(agent_id, ticker, "Shromažďování položek")
        line_items = search_line_items(
            ticker=ticker,
            line_items=[
                "free_cash_flow",
                "net_income",
                "depreciation_and_amortization",
                "capital_expenditure",
                "working_capital",
            ],
            end_date=end_date,
            period="ttm",
            limit=2,
            api_key=api_key,
        )
        if len(line_items) < 2:
            progress.update_status(agent_id, ticker, "Selhalo: Nedostatečné finanční položky")
            continue
        li_curr, li_prev = line_items[0], line_items[1]

        # ------------------------------------------------------------------
        # Modely ocenění
        # ------------------------------------------------------------------
        wc_curr = getattr(li_curr, "working_capital", None)
        wc_prev = getattr(li_prev, "working_capital", None)
        wc_change = (wc_curr or 0) - (wc_prev or 0)

        # Vlastnické výnosy
        owner_val = calculate_owner_earnings_value(
            net_income=getattr(li_curr, "net_income", None),
            depreciation=getattr(li_curr, "depreciation_and_amortization", None),
            capex=getattr(li_curr, "capital_expenditure", None),
            working_capital_change=wc_change,
            growth_rate=most_recent_metrics.earnings_growth or 0.05,
        )

        # Diskontovaný peněžní tok
        dcf_val = calculate_intrinsic_value(
            free_cash_flow=getattr(li_curr, "free_cash_flow", None),
            growth_rate=most_recent_metrics.earnings_growth or 0.05,
            discount_rate=0.10,
            terminal_growth_rate=0.03,
            num_years=5,
        )

        # Implikovaná hodnota vlastního kapitálu
        ev_ebitda_val = calculate_ev_ebitda_value(financial_metrics)

        # Model reziduálního příjmu
        rim_val = calculate_residual_income_value(
            market_cap=most_recent_metrics.market_cap,
            net_income=getattr(li_curr, "net_income", None),
            price_to_book_ratio=most_recent_metrics.price_to_book_ratio,
            book_value_growth=most_recent_metrics.book_value_growth or 0.03,
        )

        # ------------------------------------------------------------------
        # Agregace a signál
        # ------------------------------------------------------------------
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)
        if not market_cap:
            progress.update_status(agent_id, ticker, "Selhalo: Tržní kapitalizace nedostupná")
            continue

        method_values = {
            "dcf": {"value": dcf_val, "weight": 0.35},
            "owner_earnings": {"value": owner_val, "weight": 0.35},
            "ev_ebitda": {"value": ev_ebitda_val, "weight": 0.20},
            "residual_income": {"value": rim_val, "weight": 0.10},
        }

        total_weight = sum(v["weight"] for v in method_values.values() if v["value"] > 0)
        if total_weight == 0:
            progress.update_status(agent_id, ticker, "Selhalo: Všechny metody ocenění nulové")
            continue

        for v in method_values.values():
            v["gap"] = (v["value"] - market_cap) / market_cap if v["value"] > 0 else None

        weighted_gap = (
            sum(v["weight"] * v["gap"] for v in method_values.values() if v["gap"] is not None) / total_weight
        )

        signal = "bullish" if weighted_gap > 0.15 else "bearish" if weighted_gap < -0.15 else "neutral"
        confidence = round(min(abs(weighted_gap) / 0.30 * 100, 100))

        reasoning = {
            f"{m}_analysis": {
                "signal": (
                    "bullish"
                    if vals["gap"] and vals["gap"] > 0.15
                    else "bearish" if vals["gap"] and vals["gap"] < -0.15 else "neutral"
                ),
                "details": (
                    f"Value: ${vals['value']:,.2f}, Market Cap: ${market_cap:,.2f}, "
                    f"Gap: {vals['gap']:.1%}, Weight: {vals['weight']*100:.0f}%"
                ),
            }
            for m, vals in method_values.items()
            if vals["value"] > 0
        }

        valuation_analysis[ticker] = {
            "signal": signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }
        progress.update_status(agent_id, ticker, "Hotovo", analysis=json.dumps(reasoning, indent=4))

    # ---- Vyslání zprávy (pro LLM tool chain) ----
    msg = HumanMessage(content=json.dumps(valuation_analysis), name=agent_id)
    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(valuation_analysis, "Valuation Analysis Agent")

    # Přidání signálu do seznamu analyst_signals
    if "analyst_signals" not in state["data"]:
        state["data"]["analyst_signals"] = {}
    state["data"]["analyst_signals"][agent_id] = valuation_analysis

    progress.update_status(agent_id, None, "Hotovo")

    return {"messages": [msg], "data": data}


#############################
# Pomocné funkce pro ocenění
#############################


def calculate_owner_earnings_value(
    net_income: float | None,
    depreciation: float | None,
    capex: float | None,
    working_capital_change: float | None,
    growth_rate: float = 0.05,
    required_return: float = 0.15,
    margin_of_safety: float = 0.25,
    num_years: int = 5,
) -> float:
    """Buffettovo ocenění vlastnických výnosů s bezpečnostní rezervou."""
    if not all(isinstance(x, (int, float)) for x in [net_income, depreciation, capex, working_capital_change]):
        return 0

    # Type narrowing - we know these are floats now due to the check above
    net_income = net_income or 0.0
    depreciation = depreciation or 0.0
    capex = capex or 0.0
    working_capital_change = working_capital_change or 0.0

    owner_earnings = net_income + depreciation - capex - working_capital_change
    if owner_earnings <= 0:
        return 0

    pv = 0.0
    for yr in range(1, num_years + 1):
        future = owner_earnings * (1 + growth_rate) ** yr
        pv += future / (1 + required_return) ** yr

    terminal_growth = min(growth_rate, 0.03)
    term_val = (owner_earnings * (1 + growth_rate) ** num_years * (1 + terminal_growth)) / (
        required_return - terminal_growth
    )
    pv_term = term_val / (1 + required_return) ** num_years

    intrinsic = pv + pv_term
    return intrinsic * (1 - margin_of_safety)


def calculate_intrinsic_value(
    free_cash_flow: float | None,
    growth_rate: float = 0.05,
    discount_rate: float = 0.10,
    terminal_growth_rate: float = 0.02,
    num_years: int = 5,
) -> float:
    """Klasický DCF na FCF s konstantním růstem a terminální hodnotou."""
    if free_cash_flow is None or free_cash_flow <= 0:
        return 0

    pv = 0.0
    for yr in range(1, num_years + 1):
        fcft = free_cash_flow * (1 + growth_rate) ** yr
        pv += fcft / (1 + discount_rate) ** yr

    term_val = (free_cash_flow * (1 + growth_rate) ** num_years * (1 + terminal_growth_rate)) / (
        discount_rate - terminal_growth_rate
    )
    pv_term = term_val / (1 + discount_rate) ** num_years

    return pv + pv_term


def calculate_ev_ebitda_value(financial_metrics: list):
    """Implikovaná hodnota vlastního kapitálu přes mediánový násobek EV/EBITDA."""
    if not financial_metrics:
        return 0
    m0 = financial_metrics[0]
    if not (m0.enterprise_value and m0.enterprise_value_to_ebitda_ratio):
        return 0
    if m0.enterprise_value_to_ebitda_ratio == 0:
        return 0

    ebitda_now = m0.enterprise_value / m0.enterprise_value_to_ebitda_ratio
    med_mult = median(
        [m.enterprise_value_to_ebitda_ratio for m in financial_metrics if m.enterprise_value_to_ebitda_ratio]
    )
    ev_implied = med_mult * ebitda_now
    net_debt = (m0.enterprise_value or 0) - (m0.market_cap or 0)
    return max(ev_implied - net_debt, 0)


def calculate_residual_income_value(
    market_cap: float | None,
    net_income: float | None,
    price_to_book_ratio: float | None,
    book_value_growth: float = 0.03,
    cost_of_equity: float = 0.10,
    terminal_growth_rate: float = 0.03,
    num_years: int = 5,
):
    """Model reziduálního příjmu (Edwards‑Bell‑Ohlson)."""
    if not (market_cap and net_income and price_to_book_ratio and price_to_book_ratio > 0):
        return 0

    book_val = market_cap / price_to_book_ratio
    ri0 = net_income - cost_of_equity * book_val
    if ri0 <= 0:
        return 0

    pv_ri = 0.0
    for yr in range(1, num_years + 1):
        ri_t = ri0 * (1 + book_value_growth) ** yr
        pv_ri += ri_t / (1 + cost_of_equity) ** yr

    term_ri = ri0 * (1 + book_value_growth) ** (num_years + 1) / (cost_of_equity - terminal_growth_rate)
    pv_term = term_ri / (1 + cost_of_equity) ** num_years

    intrinsic = book_val + pv_ri + pv_term
    return intrinsic * 0.8  # 20% bezpečnostní rezerva
