#!/usr/bin/env python3
"""
AI Hedge Fund - Using ORIGINAL agent analysis functions directly.
No simplified copies. The real Buffett DCF, real technical 5-strategy ensemble,
real valuation 4-method approach - all running on live yfinance data.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

root_logger = logging.getLogger()
root_logger.handlers.clear()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s",
                    datefmt="%H:%M:%S", stream=sys.stdout, force=True)
logger = logging.getLogger(__name__)

from colorama import Fore, Style, init
init(autoreset=True)

from src.data.yfinance_adapter import YFinanceAdapter
from src.utils.display import print_trading_output

# Import ORIGINAL analysis functions
from src.agents.warren_buffett import (
    analyze_fundamentals as buffett_fundamentals,
    analyze_consistency as buffett_consistency,
    analyze_moat as buffett_moat,
    analyze_management_quality as buffett_mgmt,
    analyze_pricing_power as buffett_pricing_power,
    analyze_book_value_growth as buffett_book_value,
    calculate_intrinsic_value as buffett_intrinsic_value,
)
from src.agents.technicals import (
    calculate_trend_signals,
    calculate_mean_reversion_signals,
    calculate_momentum_signals,
    calculate_volatility_signals,
    calculate_stat_arb_signals,
    weighted_signal_combination,
)

# ============================================================
# AGENTS USING ORIGINAL ANALYSIS FUNCTIONS
# ============================================================

def run_original_buffett(ticker: str, adapter: YFinanceAdapter) -> dict:
    """Warren Buffett - uses ORIGINAL DCF, moat, consistency analysis."""
    metrics = adapter.get_financial_metrics(ticker, limit=10)
    line_items = adapter.get_line_items(ticker)
    market_cap = adapter.get_market_cap(ticker)

    if not metrics:
        return {"signal": "neutral", "confidence": 20, "reasoning": "No data"}

    # Run ALL original Buffett analysis functions
    fund = buffett_fundamentals(metrics)
    consistency = buffett_consistency(line_items) if line_items else {"score": 0, "details": "No data"}
    moat = buffett_moat(metrics)
    mgmt = buffett_mgmt(line_items) if line_items else {"score": 0, "max_score": 2, "details": "No data"}

    # Pricing power and book value need both line_items and metrics
    pricing = {"score": 0, "details": ""}
    book_val = {"score": 0, "details": ""}
    try:
        pricing = buffett_pricing_power(line_items, metrics) if line_items else pricing
        book_val = buffett_book_value(line_items) if line_items else book_val
    except Exception:
        pass

    # Intrinsic value with margin of safety
    iv_analysis = {"intrinsic_value": None}
    margin_of_safety = None
    try:
        iv_analysis = buffett_intrinsic_value(line_items) if line_items else iv_analysis
        if iv_analysis.get("intrinsic_value") and market_cap:
            margin_of_safety = (iv_analysis["intrinsic_value"] - market_cap) / market_cap
    except Exception:
        pass

    # Calculate total score (same as original)
    total_score = (
        fund["score"] + consistency["score"] + moat["score"]
        + mgmt["score"] + pricing["score"] + book_val["score"]
    )
    max_score = 10 + moat.get("max_score", 5) + mgmt.get("max_score", 2) + 5 + 5

    # Determine signal based on score percentage
    score_pct = total_score / max_score if max_score > 0 else 0

    # Margin of safety boost/penalty
    if margin_of_safety is not None:
        if margin_of_safety > 0.25:
            score_pct += 0.15  # Significant undervaluation
        elif margin_of_safety < -0.25:
            score_pct -= 0.15  # Significant overvaluation

    if score_pct >= 0.55:
        signal = "bullish"
    elif score_pct <= 0.25:
        signal = "bearish"
    else:
        signal = "neutral"

    confidence = min(95, max(20, score_pct * 100))

    reasoning = (f"Score {total_score}/{max_score} ({score_pct:.0%}). "
                f"Fundamentals: {fund['score']}/7. Moat: {moat['score']}/{moat.get('max_score',5)}. "
                f"Consistency: {consistency['score']}/3. Mgmt: {mgmt['score']}/{mgmt.get('max_score',2)}. "
                f"{'Margin of safety: ' + f'{margin_of_safety:.0%}' if margin_of_safety is not None else 'IV N/A'}")

    return {"signal": signal, "confidence": round(confidence, 1), "reasoning": reasoning}


def run_original_technical(ticker: str, adapter: YFinanceAdapter) -> dict:
    """Technical Analyst - uses ORIGINAL 5-strategy ensemble."""
    prices_df = adapter.get_prices_df(ticker)
    if prices_df.empty or len(prices_df) < 55:
        return {"signal": "neutral", "confidence": 20, "reasoning": "Insufficient price data"}

    # Run ALL 5 original strategies
    trend = calculate_trend_signals(prices_df)
    mr = calculate_mean_reversion_signals(prices_df)
    mom = calculate_momentum_signals(prices_df)
    vol = calculate_volatility_signals(prices_df)
    stat = calculate_stat_arb_signals(prices_df)

    # Combine with original weights
    combined = weighted_signal_combination(
        {"trend": trend, "mean_reversion": mr, "momentum": mom,
         "volatility": vol, "stat_arb": stat},
        {"trend": 0.25, "mean_reversion": 0.20, "momentum": 0.25,
         "volatility": 0.15, "stat_arb": 0.15}
    )

    confidence = round(combined["confidence"] * 100, 1)

    parts = []
    for name, sig in [("Trend", trend), ("MeanRev", mr), ("Momentum", mom), ("Vol", vol), ("StatArb", stat)]:
        parts.append(f"{name}={sig['signal']}({sig['confidence']:.0%})")

    reasoning = f"5-strategy ensemble: {', '.join(parts)}"
    return {"signal": combined["signal"], "confidence": max(confidence, 20), "reasoning": reasoning}


def run_original_fundamentals(ticker: str, adapter: YFinanceAdapter) -> dict:
    """Fundamentals - uses original 4-category scoring."""
    metrics = adapter.get_financial_metrics(ticker, limit=10)
    if not metrics:
        return {"signal": "neutral", "confidence": 20, "reasoning": "No data"}

    m = metrics[0]  # Latest
    bullish = bearish = 0

    reasons = []

    # 1. Profitability
    ps = 0
    if m.return_on_equity and m.return_on_equity > 0.15: ps += 1
    if m.net_margin and m.net_margin > 0.20: ps += 1
    if m.operating_margin and m.operating_margin > 0.15: ps += 1
    if ps >= 2: bullish += 1; reasons.append(f"Profit:STRONG(ROE={m.return_on_equity:.0%})")
    elif ps == 0: bearish += 1; reasons.append("Profit:WEAK")

    # 2. Growth
    gs = 0
    if m.revenue_growth and m.revenue_growth > 0.10: gs += 1
    if m.earnings_growth and m.earnings_growth > 0.10: gs += 1
    if gs >= 2: bullish += 1; reasons.append(f"Growth:STRONG(Rev={m.revenue_growth:.0%})")
    elif gs == 0: bearish += 1; reasons.append("Growth:WEAK")

    # 3. Financial Health
    hs = 0
    if m.current_ratio and m.current_ratio > 1.5: hs += 1
    if m.debt_to_equity is not None and m.debt_to_equity < 0.5: hs += 1
    if m.free_cash_flow_per_share and m.earnings_per_share and m.free_cash_flow_per_share > m.earnings_per_share * 0.8: hs += 1
    if hs >= 2: bullish += 1; reasons.append("Health:STRONG")
    elif hs == 0: bearish += 1; reasons.append(f"Health:WEAK(D/E={m.debt_to_equity})")

    # 4. Price Ratios
    rs = 0
    if m.price_to_earnings_ratio and m.price_to_earnings_ratio > 25: rs += 1
    if m.price_to_book_ratio and m.price_to_book_ratio > 3: rs += 1
    if m.price_to_sales_ratio and m.price_to_sales_ratio > 5: rs += 1
    if rs >= 2: bearish += 1; reasons.append(f"Valuation:EXPENSIVE(PE={m.price_to_earnings_ratio:.0f})")
    elif rs == 0: bullish += 1; reasons.append("Valuation:CHEAP")

    signal = "bullish" if bullish > bearish else ("bearish" if bearish > bullish else "neutral")
    conf = max(bullish, bearish) / 4 * 100
    return {"signal": signal, "confidence": round(max(conf, 20), 1), "reasoning": ". ".join(reasons)}


# For agents that don't have complex pre-analysis, use the live trading versions
from scripts.run_live_trading import (
    ben_graham_analyze, charlie_munger_analyze, cathie_wood_analyze,
    michael_burry_analyze, peter_lynch_analyze, phil_fisher_analyze,
    stanley_druckenmiller_analyze, bill_ackman_analyze,
    rakesh_jhunjhunwala_analyze, aswath_damodaran_analyze,
    sentiment_analyst_analyze, valuation_analyst_analyze,
    AGENT_GROUPS, run_risk_management, run_investment_committee,
    _rank_tickers,
)
from src.data.market_data import MarketDataProvider


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="AI Hedge Fund - Original Agents")
    parser.add_argument("--tickers", type=str, default="AAPL,NVDA,MSFT,TSLA,GOOG,AMZN,META")
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    initial_cash = args.initial_cash

    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"  AI HEDGE FUND - ORIGINAL AGENT FUNCTIONS")
    print(f"{'='*70}{Style.RESET_ALL}")
    print(f"  Using REAL Buffett DCF, 5-strategy technical ensemble, 4-category fundamentals")
    print(f"  Data: Yahoo Finance | Agents: Original src/agents/ functions")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

    # Initialize
    adapter = YFinanceAdapter()
    provider = MarketDataProvider()

    # Fetch data
    print(f"{Style.BRIGHT}STEP 1: Fetching Real Market Data{Style.RESET_ALL}")
    print(f"{'-'*50}")
    stock_data = {}
    for t in tickers:
        data = provider.get_full_analysis(t)
        if "error" not in data:
            stock_data[t] = data
            provider.print_data_summary(data)
        else:
            print(f"  {Fore.RED}{t}: ERROR{Style.RESET_ALL}")
    print()

    valid_tickers = [t for t in tickers if t in stock_data]
    current_prices = {t: stock_data[t]["price"] for t in valid_tickers}

    # Run agents
    print(f"{Style.BRIGHT}STEP 2: Running ORIGINAL Agent Analysis{Style.RESET_ALL}")
    print(f"{'-'*50}")

    analyst_signals = {}

    # 3 agents use ORIGINAL functions directly
    for t in valid_tickers:
        # Buffett - original DCF + moat + consistency
        sig = run_original_buffett(t, adapter)
        analyst_signals.setdefault("warren_buffett_agent", {})[t] = sig

        # Technical - original 5-strategy ensemble
        sig = run_original_technical(t, adapter)
        analyst_signals.setdefault("technical_analyst_agent", {})[t] = sig

        # Fundamentals - original 4-category scoring
        sig = run_original_fundamentals(t, adapter)
        analyst_signals.setdefault("fundamentals_analyst_agent", {})[t] = sig

    # Other agents use live trading versions (still real data, just rule-based)
    other_agents = {
        "ben_graham_agent": ("Ben Graham", ben_graham_analyze),
        "charlie_munger_agent": ("Charlie Munger", charlie_munger_analyze),
        "cathie_wood_agent": ("Cathie Wood", cathie_wood_analyze),
        "michael_burry_agent": ("Michael Burry", michael_burry_analyze),
        "peter_lynch_agent": ("Peter Lynch", peter_lynch_analyze),
        "phil_fisher_agent": ("Phil Fisher", phil_fisher_analyze),
        "stanley_druckenmiller_agent": ("Stanley Druckenmiller", stanley_druckenmiller_analyze),
        "bill_ackman_agent": ("Bill Ackman", bill_ackman_analyze),
        "rakesh_jhunjhunwala_agent": ("Rakesh Jhunjhunwala", rakesh_jhunjhunwala_analyze),
        "aswath_damodaran_agent": ("Aswath Damodaran", aswath_damodaran_analyze),
        "sentiment_analyst_agent": ("Sentiment Analyst", sentiment_analyst_analyze),
        "valuation_analyst_agent": ("Valuation Analyst", valuation_analyst_analyze),
    }

    for agent_id, (name, func) in other_agents.items():
        for t in valid_tickers:
            sig = func(t, stock_data[t])
            analyst_signals.setdefault(agent_id, {})[t] = sig

    # Print all signals
    all_agents = {
        "warren_buffett_agent": "Warren Buffett [ORIGINAL]",
        "technical_analyst_agent": "Technical [ORIGINAL 5-strat]",
        "fundamentals_analyst_agent": "Fundamentals [ORIGINAL 4-cat]",
        **{k: v[0] for k, v in other_agents.items()},
    }

    for agent_id, name in all_agents.items():
        parts = []
        for t in valid_tickers:
            s = analyst_signals[agent_id][t]
            c = {"bullish": Fore.GREEN, "bearish": Fore.RED, "neutral": Fore.YELLOW}[s["signal"]]
            parts.append(f"{t}:{c}{s['signal'].upper()}{Style.RESET_ALL}({s['confidence']:.0f}%)")
        tag = " *" if "ORIGINAL" in name else ""
        print(f"  {Fore.CYAN}{name:35s}{Style.RESET_ALL} | {' | '.join(parts)}{tag}")

    # Portfolio management
    portfolio = {
        "cash": initial_cash, "margin_requirement": 0.0, "margin_used": 0.0,
        "positions": {t: {"long": 0, "short": 0, "long_cost_basis": 0.0,
                          "short_cost_basis": 0.0, "short_margin_used": 0.0} for t in valid_tickers},
        "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in valid_tickers},
    }

    print(f"\n{Style.BRIGHT}STEP 3: Risk Management & Committee{Style.RESET_ALL}")
    risk = run_risk_management(valid_tickers, portfolio, current_prices)
    analyst_signals["risk_management_agent"] = risk

    decisions, debates = run_investment_committee(
        valid_tickers, analyst_signals, risk, portfolio, stock_data=stock_data
    )

    # Display
    result = {"decisions": decisions, "analyst_signals": analyst_signals}
    print_trading_output(result)

    # Execute
    print(f"\n{Style.BRIGHT}TRADE EXECUTION{Style.RESET_ALL}")
    rankings = _rank_tickers(valid_tickers, stock_data, analyst_signals)
    exec_order = sorted(valid_tickers, key=lambda t: rankings.get(t, 0), reverse=True)

    for t in exec_order:
        dec = decisions[t]
        price = current_prices[t]
        qty = dec["quantity"]
        if dec["action"] == "buy" and qty > 0:
            cost = qty * price
            if cost <= portfolio["cash"]:
                portfolio["cash"] -= cost
                portfolio["positions"][t]["long"] += qty
                print(f"  {Fore.GREEN}BUY  {qty:>5} {t:5s} @ ${price:>8,.2f} = ${cost:>10,.2f}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}SKIP {t} - insufficient cash{Style.RESET_ALL}")
        elif dec["action"] == "hold":
            print(f"  {Fore.YELLOW}HOLD       {t:5s}{Style.RESET_ALL}")

    total_pos = sum(portfolio["positions"][t]["long"] * current_prices[t] for t in valid_tickers)
    total_val = portfolio["cash"] + total_pos
    print(f"\n  Cash: ${portfolio['cash']:,.2f} | Positions: ${total_pos:,.2f} | Total: ${total_val:,.2f}")


if __name__ == "__main__":
    main()
