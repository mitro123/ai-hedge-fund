#!/usr/bin/env python3
"""
AI Hedge Fund - Adaptive Stock Selection
Agents scan a broad universe of 50+ stocks across all sectors
and dynamically select the best 5-10 for the portfolio each month.

The fund rotates between stocks as conditions change.
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

from src.data.market_data import MarketDataProvider
from scripts.run_live_trading import (
    AGENTS, AGENT_GROUPS, _rank_tickers,
    run_risk_management, run_investment_committee,
)
from src.utils.display import print_trading_output


# ============================================================
# STOCK UNIVERSE - All major sectors
# ============================================================
UNIVERSE = {
    # Technology
    "AAPL": "Tech/Consumer Electronics",
    "MSFT": "Tech/Cloud",
    "NVDA": "Tech/AI Semiconductors",
    "GOOG": "Tech/Search & Ads",
    "META": "Tech/Social Media",
    "AMZN": "Tech/E-commerce & Cloud",
    "CRM": "Tech/Enterprise SaaS",
    "ADBE": "Tech/Creative Software",
    "AMD": "Tech/Semiconductors",
    "INTC": "Tech/Semiconductors",
    "NFLX": "Tech/Streaming",
    "ORCL": "Tech/Enterprise",

    # Finance
    "JPM": "Finance/Banking",
    "V": "Finance/Payments",
    "MA": "Finance/Payments",
    "GS": "Finance/Investment Banking",
    "BRK-B": "Finance/Conglomerate",

    # Healthcare
    "UNH": "Healthcare/Insurance",
    "JNJ": "Healthcare/Pharma",
    "LLY": "Healthcare/Pharma",
    "PFE": "Healthcare/Pharma",
    "ABBV": "Healthcare/Pharma",

    # Consumer
    "WMT": "Consumer/Retail",
    "COST": "Consumer/Retail",
    "KO": "Consumer/Beverages",
    "PG": "Consumer/Staples",
    "MCD": "Consumer/Restaurants",
    "NKE": "Consumer/Apparel",
    "HD": "Consumer/Home Improvement",

    # Industrial & Energy
    "CAT": "Industrial/Machinery",
    "BA": "Industrial/Aerospace",
    "XOM": "Energy/Oil & Gas",
    "CVX": "Energy/Oil & Gas",
    "NEE": "Energy/Utilities",

    # Speculative/High Growth
    "COIN": "Crypto/Exchange",
    "PLTR": "Tech/AI & Data",
    "SQ": "Fintech/Payments",
    "UBER": "Tech/Ride-sharing",
    "SHOP": "Tech/E-commerce Platform",
    "ROKU": "Tech/Streaming Devices",
    "SNAP": "Tech/Social Media",

    # Other
    "TSLA": "Auto/EV & Energy",
    "DIS": "Media/Entertainment",
}


def scan_universe(provider: MarketDataProvider, max_stocks: int = 30) -> Dict[str, Dict]:
    """Scan the full stock universe and fetch data for all."""
    print(f"\n{Style.BRIGHT}SCANNING UNIVERSE: {len(UNIVERSE)} stocks across all sectors{Style.RESET_ALL}")
    print(f"{'-'*70}")

    stock_data = {}
    errors = 0
    for i, (symbol, sector) in enumerate(UNIVERSE.items()):
        try:
            data = provider.get_full_analysis(symbol)
            if "error" not in data:
                stock_data[symbol] = data
                # Quick summary
                pe = data.get("pe", 0)
                m12 = data.get("momentum_12m", 0)
                score = data.get("analyst_score", 3.0)
                rec = data.get("analyst_recommendation", "?")
                print(f"  {symbol:6s} {sector:30s} ${data['price']:>8.2f}  PE={pe:>6.1f}  12m={m12:>+6.1%}  {rec}")
            else:
                errors += 1
        except Exception as e:
            errors += 1

    print(f"\n  Scanned {len(stock_data)} stocks successfully ({errors} errors)")
    return stock_data


def select_portfolio(stock_data: Dict, analyst_signals: Dict, target_size: int = 7) -> List[str]:
    """Select the best stocks for the portfolio based on agent rankings."""
    rankings = _rank_tickers(list(stock_data.keys()), stock_data, analyst_signals)

    # Sort by ranking score
    sorted_stocks = sorted(rankings.items(), key=lambda x: x[1], reverse=True)

    # Filter: only include stocks with positive rank score
    candidates = [(t, s) for t, s in sorted_stocks if s > 0]

    selected = [t for t, s in candidates[:target_size]]

    print(f"\n{Style.BRIGHT}PORTFOLIO SELECTION (top {target_size} from {len(candidates)} candidates):{Style.RESET_ALL}")
    for i, (ticker, score) in enumerate(sorted_stocks[:target_size + 5]):
        selected_marker = f"{Fore.GREEN}>> SELECTED{Style.RESET_ALL}" if ticker in selected else ""
        sector = UNIVERSE.get(ticker, "?")
        print(f"  #{i+1:2d} {ticker:6s} score={score:>6.1f}  ({sector:30s}) {selected_marker}")

    return selected


def main():
    parser = argparse.ArgumentParser(description="AI Hedge Fund - Adaptive Stock Selection")
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--portfolio-size", type=int, default=7, help="Target number of stocks")
    args = parser.parse_args()

    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"  AI HEDGE FUND - ADAPTIVE PORTFOLIO")
    print(f"  Scanning {len(UNIVERSE)} stocks | Selecting top {args.portfolio_size}")
    print(f"{'='*70}{Style.RESET_ALL}")

    provider = MarketDataProvider()

    # Step 1: Scan entire universe
    stock_data = scan_universe(provider)

    # Step 2: Run ALL 15 agents on ALL stocks
    print(f"\n{Style.BRIGHT}RUNNING 15 AI AGENTS on {len(stock_data)} stocks...{Style.RESET_ALL}")
    analyst_signals = {}
    for agent_id, (name, func) in AGENTS.items():
        signals = {}
        for t in stock_data:
            try:
                signals[t] = func(t, stock_data[t])
            except Exception:
                signals[t] = {"signal": "neutral", "confidence": 20, "reasoning": "Error"}
        analyst_signals[agent_id] = signals

    # Show agent summary for top stocks
    rankings = _rank_tickers(list(stock_data.keys()), stock_data, analyst_signals)
    top10 = sorted(rankings.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n{Style.BRIGHT}TOP 10 STOCKS BY RANKING:{Style.RESET_ALL}")
    for agent_id, (name, _) in list(AGENTS.items())[:5]:  # Show first 5 agents
        parts = []
        for t, _ in top10:
            s = analyst_signals[agent_id].get(t, {})
            sig = s.get("signal", "?")
            c = {"bullish": Fore.GREEN, "bearish": Fore.RED, "neutral": Fore.YELLOW}.get(sig, Fore.WHITE)
            parts.append(f"{t}:{c}{sig[:4].upper()}{Style.RESET_ALL}")
        print(f"  {name:25s} | {' | '.join(parts)}")

    # Step 3: Select portfolio
    selected = select_portfolio(stock_data, analyst_signals, args.portfolio_size)
    current_prices = {t: stock_data[t]["price"] for t in selected}

    # Step 4: Run investment committee on selected stocks
    portfolio = {
        "cash": args.initial_cash, "margin_requirement": 0.0, "margin_used": 0.0,
        "positions": {t: {"long": 0, "short": 0, "long_cost_basis": 0.0,
                          "short_cost_basis": 0.0, "short_margin_used": 0.0} for t in selected},
        "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in selected},
    }

    risk = run_risk_management(selected, portfolio, current_prices)
    analyst_signals["risk_management_agent"] = risk

    decisions, debates = run_investment_committee(
        selected, analyst_signals, risk, portfolio, stock_data=stock_data
    )

    # Display
    result = {"decisions": decisions, "analyst_signals": {k: {t: v for t, v in sigs.items() if t in selected} for k, sigs in analyst_signals.items()}}
    print_trading_output(result)

    # Execute
    print(f"\n{Style.BRIGHT}TRADE EXECUTION:{Style.RESET_ALL}")
    exec_order = sorted(selected, key=lambda t: rankings.get(t, 0), reverse=True)
    for t in exec_order:
        dec = decisions[t]
        price = current_prices[t]
        qty = dec["quantity"]
        if dec["action"] == "buy" and qty > 0:
            cost = qty * price
            if cost <= portfolio["cash"]:
                portfolio["cash"] -= cost
                portfolio["positions"][t]["long"] += qty
                print(f"  {Fore.GREEN}BUY  {qty:>5} {t:6s} @ ${price:>8.2f} = ${cost:>10,.2f}{Style.RESET_ALL}  ({UNIVERSE.get(t, '?')})")
            else:
                print(f"  {Fore.RED}SKIP {t} - insufficient cash{Style.RESET_ALL}")
        elif dec["action"] == "hold":
            print(f"  {Fore.YELLOW}HOLD       {t:6s}{Style.RESET_ALL}")

    # Summary
    total_pos = sum(portfolio["positions"][t]["long"] * current_prices[t] for t in selected)
    total = portfolio["cash"] + total_pos
    invested = (1 - portfolio["cash"] / total) * 100 if total > 0 else 0

    print(f"\n{Style.BRIGHT}ADAPTIVE PORTFOLIO:{Style.RESET_ALL}")
    print(f"{'='*70}")
    for t in exec_order:
        p = portfolio["positions"][t]
        if p["long"] > 0:
            val = p["long"] * current_prices[t]
            pct = val / total * 100
            print(f"  {Fore.CYAN}{t:6s}{Style.RESET_ALL}: {p['long']:>4d} shares  ${val:>10,.2f}  ({pct:.1f}%)  {UNIVERSE.get(t, '')}")
    print(f"\n  Cash:      ${portfolio['cash']:>10,.2f}")
    print(f"  Positions: ${total_pos:>10,.2f}")
    print(f"  Total:     ${total:>10,.2f}")
    print(f"  Invested:  {invested:.0f}%")
    print(f"  Stocks:    {sum(1 for t in selected if portfolio['positions'][t]['long'] > 0)} out of {len(UNIVERSE)} scanned")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
