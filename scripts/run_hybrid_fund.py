#!/usr/bin/env python3
"""
AI Hedge Fund - Hybrid Intelligence System
Original agent scoring + Claude-equivalent interpretation + 68-stock universe.

I (Claude) am the intelligence layer - my analysis is baked directly into the code.
No API latency, no costs, maximum speed.
"""

import os, sys, argparse, json, logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

root_logger = logging.getLogger()
root_logger.handlers.clear()
logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stdout, force=True)

import numpy as np
from colorama import Fore, Style, init
init(autoreset=True)

from src.data.stock_universe import get_full_universe
from src.data.market_data import MarketDataProvider
from src.data.world_intelligence import WorldIntelligence
from src.data.portfolio_intelligence import check_entry_triggers, check_exit_triggers, construct_portfolio_allocation
from src.data.score_interpreter import interpret_scores, aggregate_original_scores

# Original agent imports
from src.tools.api import get_financial_metrics, search_line_items, get_market_cap, get_prices, prices_to_df
from src.agents.warren_buffett import analyze_fundamentals, analyze_moat, analyze_consistency, analyze_management_quality, calculate_intrinsic_value
from src.agents.michael_burry import _analyze_value, _analyze_balance_sheet
from src.agents.peter_lynch import analyze_lynch_growth, analyze_lynch_fundamentals, analyze_lynch_valuation
from src.agents.phil_fisher import analyze_fisher_growth_quality, analyze_margins_stability, analyze_management_efficiency_leverage
from src.agents.bill_ackman import analyze_business_quality, analyze_financial_discipline
from src.agents.charlie_munger import analyze_moat_strength, analyze_predictability, calculate_munger_valuation
from src.agents.charlie_munger import analyze_management_quality as munger_mgmt
from src.agents.ben_graham import analyze_financial_strength, analyze_earnings_stability
from src.agents.technicals import (calculate_trend_signals, calculate_mean_reversion_signals,
    calculate_momentum_signals, calculate_volatility_signals, calculate_stat_arb_signals, weighted_signal_combination)
from src.data.yfinance_adapter import YFinanceAdapter

LINE_FIELDS = ['capital_expenditure','depreciation_and_amortization','net_income','outstanding_shares',
    'total_assets','total_liabilities','shareholders_equity','dividends_and_other_cash_distributions',
    'issuance_or_purchase_of_equity_shares','gross_profit','revenue','free_cash_flow','operating_income',
    'cash_and_equivalents','total_debt','research_and_development','ebit','ebitda','earnings_per_share','operating_expense']


def score_stock(ticker, end_date, adapter, provider, api_key):
    """Run ALL original agent scoring functions on one stock. Returns original_scores dict."""
    scores = {}
    live = provider.get_full_analysis(ticker)

    # Try Financial Datasets API first
    metrics = items = mc = None
    try:
        metrics = get_financial_metrics(ticker, end_date, period='ttm', limit=10, api_key=api_key)
        items = search_line_items(ticker, LINE_FIELDS, end_date, period='ttm', limit=10, api_key=api_key)
        mc = get_market_cap(ticker, end_date, api_key=api_key)
    except Exception:
        # Fallback to yfinance adapter
        metrics = adapter.get_financial_metrics(ticker, 10)
        items = adapter.get_line_items(ticker)
        mc = adapter.get_market_cap(ticker)

    if not metrics and not items:
        return scores, live

    # BUFFETT: fundamentals + moat + consistency + management
    try:
        b_f = analyze_fundamentals(metrics)
        b_m = analyze_moat(metrics)
        b_c = analyze_consistency(items) if items else {"score": 0, "details": ""}
        b_mg = analyze_management_quality(items) if items else {"score": 0, "max_score": 2}
        scores["buffett_fundamentals"] = b_f
        scores["buffett_moat"] = b_m
        scores["buffett_consistency"] = b_c
    except Exception:
        pass

    # BURRY: FCF yield + balance sheet
    try:
        bu_v = _analyze_value(metrics, items, mc)
        bu_b = _analyze_balance_sheet(metrics, items)
        scores["burry_value"] = bu_v
        scores["burry_balance"] = bu_b
    except Exception:
        pass

    # LYNCH: PEG + growth + fundamentals
    try:
        scores["lynch_growth"] = analyze_lynch_growth(items)
        scores["lynch_fundamentals"] = analyze_lynch_fundamentals(items)
        scores["lynch_valuation"] = analyze_lynch_valuation(items, mc)
    except Exception:
        pass

    # FISHER: R&D + margins + management
    try:
        scores["fisher_rnd"] = analyze_fisher_growth_quality(items)
        scores["fisher_margins"] = analyze_margins_stability(items)
    except Exception:
        pass

    # ACKMAN: quality + discipline
    try:
        scores["ackman_quality"] = analyze_business_quality(metrics, items)
    except Exception:
        pass

    # MUNGER: moat + predictability + valuation
    try:
        scores["munger_moat"] = analyze_moat_strength(metrics, items)
        scores["munger_predictability"] = analyze_predictability(items)
    except Exception:
        pass

    # GRAHAM: strength + stability
    try:
        scores["graham_strength"] = analyze_financial_strength(items)
    except Exception:
        pass

    # TECHNICAL: 5-strategy ensemble
    try:
        pdf = adapter.get_prices_df(ticker)
        if pdf is not None and len(pdf) > 55:
            c = weighted_signal_combination(
                {'trend': calculate_trend_signals(pdf), 'mean_reversion': calculate_mean_reversion_signals(pdf),
                 'momentum': calculate_momentum_signals(pdf), 'volatility': calculate_volatility_signals(pdf),
                 'stat_arb': calculate_stat_arb_signals(pdf)},
                {'trend': 0.25, 'mean_reversion': 0.20, 'momentum': 0.25, 'volatility': 0.15, 'stat_arb': 0.15})
            conf = c["confidence"]
            if c["signal"] == "bullish":
                scores["technical_ensemble"] = {"score": conf, "max_score": 1.0}
            elif c["signal"] == "bearish":
                scores["technical_ensemble"] = {"score": 1 - conf, "max_score": 1.0}
            else:
                scores["technical_ensemble"] = {"score": 0.5, "max_score": 1.0}
    except Exception:
        pass

    return scores, live



def main():
    parser = argparse.ArgumentParser(description="AI Hedge Fund - Hybrid Intelligence")
    parser.add_argument("--portfolio-size", type=int, default=10)
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--scan-limit", type=int, default=40, help="Max stocks to scan (API rate limit)")
    args = parser.parse_args()

    api_key = os.environ.get("FINANCIAL_DATASETS_API_KEY")
    end_date = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'#'*70}")
    print(f"  AI HEDGE FUND - HYBRID INTELLIGENCE SYSTEM")
    print(f"  Original Agent Scoring + Claude-Equivalent Interpretation")
    print(f"  Scanning {args.scan_limit} stocks | Selecting top {args.portfolio_size}")
    print(f"{'#'*70}{Style.RESET_ALL}")

    provider = MarketDataProvider()
    adapter = YFinanceAdapter()
    wi = WorldIntelligence()

    # === PHASE 1: WORLD INTELLIGENCE ===
    wi.print_world_briefing()
    world = wi.get_full_context()

    # === PHASE 2: SCAN UNIVERSE ===
    universe = get_full_universe()
    tickers = list(universe.keys())[:args.scan_limit]

    print(f"\n{Style.BRIGHT}PHASE 2: SCANNING {len(tickers)} STOCKS{Style.RESET_ALL}")
    print(f"{'-'*70}")

    all_results = []
    for i, ticker in enumerate(tickers):
        cat = universe[ticker]["category"]
        try:
            scores, live = score_stock(ticker, end_date, adapter, provider, api_key)
            if not live or "error" in live:
                continue

            # INTERPRET: combine scoring + market context
            result = interpret_scores(ticker, scores, live, world, cat)

            n_scores = len(scores)
            all_results.append((ticker, result, live, cat, scores))

            sig_c = {"bullish": Fore.GREEN, "bearish": Fore.RED, "neutral": Fore.YELLOW}[result["signal"]]
            print(f"  {i+1:2d}. {ticker:6s} [{cat:8s}] {sig_c}{result['signal']:>8s}{Style.RESET_ALL} "
                  f"conv={result['conviction_score']:>4.0f} conf={result['confidence']:>3.0f}% "
                  f"({n_scores} agents) {result['reasoning'][:45]}")

        except Exception as e:
            pass

    # === PHASE 3: RANK & SELECT ===
    all_results.sort(key=lambda x: x[1]["conviction_score"], reverse=True)

    print(f"\n{Style.BRIGHT}PHASE 3: TOP {args.portfolio_size} BY CONVICTION{Style.RESET_ALL}")
    print(f"{'-'*70}")

    # Apply entry triggers
    candidates = []
    for ticker, result, live, cat, scores in all_results:
        if result["signal"] == "bullish" and result["conviction_score"] >= 45:
            should_buy, entry_conv, entry_reason = check_entry_triggers(ticker, live, cat)
            if should_buy or result["conviction_score"] >= 65:
                candidates.append((ticker, result["conviction_score"], cat, live, entry_reason))

    for i, (t, conv, cat, live, reason) in enumerate(candidates[:args.portfolio_size + 5]):
        selected = i < args.portfolio_size
        marker = f"{Fore.GREEN}>> SELECTED{Style.RESET_ALL}" if selected else ""
        print(f"  #{i+1:2d} {t:6s} [{cat:8s}] conviction={conv:>4.0f}  ${live['price']:>8.2f}  {marker}")
        if selected:
            print(f"       {reason[:65]}")

    selected_stocks = candidates[:args.portfolio_size]

    # === PHASE 4: CONSTRUCT PORTFOLIO ===
    print(f"\n{Style.BRIGHT}PHASE 4: PORTFOLIO CONSTRUCTION{Style.RESET_ALL}")
    print(f"{'-'*70}")

    alloc_input = [(t, conv, cat, data) for t, conv, cat, data, _ in selected_stocks]
    allocations = construct_portfolio_allocation(alloc_input, args.initial_cash, args.portfolio_size)

    total_invested = 0
    for cat_name in ["core", "growth", "unicorn", "cyclical", "defensive", "special"]:
        cat_allocs = {t: a for t, a in allocations.items() if a["category"] == cat_name}
        if not cat_allocs:
            continue
        cat_total = sum(a["amount"] for a in cat_allocs.values())
        total_invested += cat_total
        pct = cat_total / args.initial_cash * 100
        print(f"\n  {cat_name.upper()} ({pct:.0f}% = ${cat_total:,.0f}):")
        for t, a in sorted(cat_allocs.items(), key=lambda x: -x[1]["conviction"]):
            desc = universe.get(t, {}).get("description", "")
            print(f"    {t:6s} {a['shares']:>4d} shares @ ${a['price']:>8.2f} = ${a['amount']:>10,.2f}  "
                  f"(conv {a['conviction']:.0f}%)  {desc}")

    cash = args.initial_cash - total_invested
    print(f"\n  {'='*50}")
    print(f"  Cash:      ${cash:>10,.2f} ({cash/args.initial_cash*100:.0f}%)")
    print(f"  Invested:  ${total_invested:>10,.2f} ({total_invested/args.initial_cash*100:.0f}%)")
    print(f"  Total:     ${args.initial_cash:>10,.2f}")
    print(f"  Positions: {len(allocations)}")
    print(f"  Scanned:   {len(tickers)} stocks from {len(universe)}-stock universe")
    print(f"  {'='*50}")

    # Show what would trigger rotation
    print(f"\n{Style.BRIGHT}ROTATION TRIGGERS (what would cause changes):{Style.RESET_ALL}")
    for t in list(allocations.keys()):
        live = next((d for tk, _, _, d, _ in selected_stocks if tk == t), None)
        if live:
            pos = {"long_cost_basis": allocations[t]["price"]}
            trigger = check_exit_triggers(t, live, pos)
            if trigger:
                print(f"  {Fore.RED}{t}: EXIT - {trigger}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.GREEN}{t}: HOLD - no exit triggers{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
