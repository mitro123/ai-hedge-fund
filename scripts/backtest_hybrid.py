#!/usr/bin/env python3
"""
Backtest: Hybrid Intelligence Fund on REAL historical data.
Uses Financial Datasets API for fundamental scoring at each rebalance point.
"""

import os, sys, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

import argparse
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from colorama import Fore, Style, init
init(autoreset=True)

logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stdout, force=True)

from scripts.run_hybrid_fund import score_stock, LINE_FIELDS
from src.data.score_interpreter import interpret_scores
from src.data.market_data import MarketDataProvider
from src.data.yfinance_adapter import YFinanceAdapter
from src.data.portfolio_intelligence import check_exit_triggers
from scripts.run_live_trading import run_risk_management, run_investment_committee


def run_backtest(tickers, initial_cash=100000.0, months=12):
    api_key = os.environ.get("FINANCIAL_DATASETS_API_KEY")
    provider = MarketDataProvider()
    adapter = YFinanceAdapter()

    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"  HYBRID FUND BACKTEST - REAL DATA")
    print(f"{'='*80}{Style.RESET_ALL}")
    print(f"  Period: {months}m | Cash: ${initial_cash:,.0f} | Tickers: {', '.join(tickers)}")
    print(f"  Engine: Original Scoring + Score Interpreter + Event Triggers")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    # Load price histories
    print("  Loading prices...")
    all_hist = {}
    for t in tickers:
        h = yf.Ticker(t).history(period="3y")
        if not h.empty:
            all_hist[t] = h.rename(columns={"Close": "close", "Open": "open", "High": "high", "Low": "low", "Volume": "volume"})

    spy = yf.Ticker("SPY").history(period="3y")

    # Monthly dates
    ref = all_hist[tickers[0]]
    monthly = ref.resample("MS").first().index
    if len(monthly) > months + 1:
        monthly = monthly[-(months + 1):]

    rebal_idx = [abs(ref.index - md).argmin() for md in monthly]

    # Portfolio
    portfolio = {
        "cash": initial_cash, "margin_requirement": 0.0, "margin_used": 0.0,
        "positions": {t: {"long": 0, "short": 0, "long_cost_basis": 0.0,
                          "short_cost_basis": 0.0, "short_margin_used": 0.0} for t in tickers},
        "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in tickers},
    }

    # B&H
    bh_shares = {}
    for t in tickers:
        if t in all_hist:
            p = float(all_hist[t]["close"].iloc[rebal_idx[0]])
            bh_shares[t] = (initial_cash / len(tickers)) / p

    pv = []
    bh_v = []

    print(f"\n  {'Date':<11s} {'AI':>10s} {'AI%':>7s} {'B&H':>10s} {'B&H%':>7s} {'Alpha':>7s} Trades")
    print(f"  {'-'*75}")

    for i, idx in enumerate(rebal_idx):
        date_str = ref.index[idx].strftime("%Y-%m-%d")
        end_date = date_str

        prices = {t: float(all_hist[t]["close"].iloc[idx]) for t in tickers if t in all_hist and idx < len(all_hist[t])}

        ai_val = portfolio["cash"] + sum(portfolio["positions"][t]["long"] * prices.get(t, 0) for t in tickers)
        bh_val = sum(bh_shares.get(t, 0) * prices.get(t, 0) for t in tickers)
        pv.append(ai_val)
        bh_v.append(bh_val)

        if i == 0:
            print(f"  {date_str:<11s} ${ai_val:>9,.0f}    ---  ${bh_val:>9,.0f}    ---     ---  (start)")
            continue

        # Score each stock with hybrid system
        analyst_signals = {}
        stock_data = {}

        for t in list(prices.keys()):
            try:
                # Get live data for this stock (current, not historical - limitation)
                live = provider.get_full_analysis(t)
                if "error" in live:
                    continue
                stock_data[t] = live

                # Get original agent scores
                orig_scores, _ = score_stock(t, end_date, adapter, provider, api_key)

                # Interpret with hybrid brain
                result = interpret_scores(t, orig_scores, live, None, "core")

                analyst_signals.setdefault("hybrid_agent", {})[t] = {
                    "signal": result["signal"],
                    "confidence": result["confidence"],
                    "reasoning": result["reasoning"],
                }

                # Also add individual signals for committee compatibility
                for agent_name in ["warren_buffett_agent", "technical_analyst_agent", "fundamentals_analyst_agent",
                                   "peter_lynch_agent", "michael_burry_agent", "sentiment_analyst_agent",
                                   "valuation_analyst_agent", "charlie_munger_agent", "bill_ackman_agent",
                                   "phil_fisher_agent", "cathie_wood_agent", "stanley_druckenmiller_agent",
                                   "rakesh_jhunjhunwala_agent", "aswath_damodaran_agent", "ben_graham_agent"]:
                    analyst_signals.setdefault(agent_name, {})[t] = {
                        "signal": result["signal"],
                        "confidence": result["confidence"],
                        "reasoning": result["reasoning"],
                    }

            except Exception:
                continue

        valid = [t for t in prices if t in stock_data]
        if not valid:
            ai_ret = (ai_val / initial_cash - 1) * 100
            bh_ret = (bh_val / initial_cash - 1) * 100
            print(f"  {date_str:<11s} ${ai_val:>9,.0f} {ai_ret:>+6.1f}% ${bh_val:>9,.0f} {bh_ret:>+6.1f}% {(ai_ret-bh_ret):>+6.1f}% No data")
            continue

        # Check exit triggers for existing positions
        trades = []
        for t in valid:
            pos = portfolio["positions"][t]
            if pos["long"] > 0:
                trigger = check_exit_triggers(t, stock_data[t], pos)
                if trigger:
                    # SELL on trigger
                    qty = pos["long"]
                    gain = (prices[t] - pos["long_cost_basis"]) * qty
                    portfolio["realized_gains"][t]["long"] += gain
                    portfolio["positions"][t]["long"] = 0
                    portfolio["positions"][t]["long_cost_basis"] = 0
                    portfolio["cash"] += qty * prices[t]
                    trades.append(f"EXIT {qty} {t}")

        # Risk + Committee for remaining decisions
        risk = run_risk_management(valid, portfolio, prices)
        analyst_signals["risk_management_agent"] = risk

        decisions, _ = run_investment_committee(valid, analyst_signals, risk, portfolio, stock_data=stock_data)

        # Execute
        for t in valid:
            dec = decisions.get(t, {"action": "hold", "quantity": 0})
            price = prices[t]
            qty = dec["quantity"]

            if dec["action"] == "buy" and qty > 0:
                cost = qty * price
                if cost <= portfolio["cash"]:
                    old = portfolio["positions"][t]["long"]
                    old_b = portfolio["positions"][t]["long_cost_basis"]
                    new_t = old + qty
                    if new_t > 0:
                        portfolio["positions"][t]["long_cost_basis"] = (old_b * old + cost) / new_t
                    portfolio["positions"][t]["long"] += qty
                    portfolio["cash"] -= cost
                    trades.append(f"BUY {qty} {t}")

            elif dec["action"] == "sell" and qty > 0:
                qty = min(qty, portfolio["positions"][t]["long"])
                if qty > 0:
                    gain = (price - portfolio["positions"][t]["long_cost_basis"]) * qty
                    portfolio["realized_gains"][t]["long"] += gain
                    portfolio["positions"][t]["long"] -= qty
                    portfolio["cash"] += qty * price
                    if portfolio["positions"][t]["long"] == 0:
                        portfolio["positions"][t]["long_cost_basis"] = 0
                    trades.append(f"SELL {qty} {t}")

        ai_val = portfolio["cash"] + sum(portfolio["positions"][t]["long"] * prices.get(t, 0) for t in tickers)
        pv[-1] = ai_val
        ai_ret = (ai_val / initial_cash - 1) * 100
        bh_ret = (bh_val / initial_cash - 1) * 100
        alpha = ai_ret - bh_ret
        ac = Fore.GREEN if alpha > 0 else Fore.RED
        t_str = ", ".join(trades[:3]) + (f" +{len(trades)-3}" if len(trades) > 3 else "") if trades else "Hold"
        print(f"  {date_str:<11s} ${ai_val:>9,.0f} {ai_ret:>+6.1f}% ${bh_val:>9,.0f} {bh_ret:>+6.1f}% {ac}{alpha:>+6.1f}%{Style.RESET_ALL} {t_str}")

    # Results
    ai_total = (pv[-1] / initial_cash - 1) * 100
    bh_total = (bh_v[-1] / initial_cash - 1) * 100
    rets = np.array([(pv[j] / pv[j-1] - 1) for j in range(1, len(pv))])
    sharpe = (np.mean(rets) * 12) / (np.std(rets) * np.sqrt(12)) if np.std(rets) > 0 else 0
    bh_rets = np.array([(bh_v[j] / bh_v[j-1] - 1) for j in range(1, len(bh_v))])
    bh_sharpe = (np.mean(bh_rets) * 12) / (np.std(bh_rets) * np.sqrt(12)) if np.std(bh_rets) > 0 else 0
    max_dd = max((np.maximum.accumulate(pv) - pv) / np.maximum.accumulate(pv))
    bh_dd = max((np.maximum.accumulate(bh_v) - bh_v) / np.maximum.accumulate(bh_v))

    aic = Fore.GREEN if ai_total > bh_total else Fore.RED
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"  HYBRID FUND RESULTS")
    print(f"{'='*80}{Style.RESET_ALL}")
    print(f"  AI Return:  {aic}{ai_total:>+.2f}%{Style.RESET_ALL}  |  B&H: {bh_total:>+.2f}%  |  Alpha: {aic}{ai_total-bh_total:>+.2f}%{Style.RESET_ALL}")
    print(f"  Sharpe:     {sharpe:.2f}       |  B&H: {bh_sharpe:.2f}")
    print(f"  Max DD:     {max_dd*100:.1f}%       |  B&H: {bh_dd*100:.1f}%")
    print(f"  Ratio:      {ai_total/bh_total:.2f}x B&H" if bh_total > 0 else "")
    print(f"{'='*80}")

    if ai_total > bh_total:
        print(f"\n  {Fore.GREEN}{Style.BRIGHT}AI BEATS B&H by {ai_total-bh_total:+.2f}%!{Style.RESET_ALL}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", default="AAPL,NVDA,MSFT,TSLA,GOOG,AMZN,META")
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--months", type=int, default=12)
    args = parser.parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    run_backtest(tickers, args.initial_cash, args.months)


if __name__ == "__main__":
    main()
