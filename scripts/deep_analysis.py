#!/usr/bin/env python3
"""
AI Hedge Fund - Deep Analysis
Comprehensive analysis of the investment committee performance.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
root_logger = logging.getLogger()
root_logger.handlers.clear()
logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stdout, force=True)

import numpy as np
import pandas as pd
from colorama import Fore, Style, init
init(autoreset=True)

from scripts.run_ai_trading import AGENTS, AGENT_GROUPS, STOCK_DATA
from scripts.run_ai_trading import run_risk_management, run_investment_committee
from scripts.backtest_ai_agents import (
    AIAgentBacktester, STOCK_PARAMS, generate_price_history, compute_dynamic_metrics
)


def separator(title):
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}{Style.RESET_ALL}\n")


# ============================================================
# ANALYSIS 1: Per-Agent Signal Accuracy
# ============================================================
def analyze_agent_accuracy():
    separator("ANALYSIS 1: Agent Signal Accuracy (24-month backtest)")

    tickers = list(STOCK_PARAMS.keys())
    periods = 24
    price_data = {t: generate_price_history(t, periods) for t in tickers}

    # Track each agent's signal vs actual price movement
    agent_results = {aid: {"correct": 0, "wrong": 0, "neutral": 0, "total": 0}
                     for aid in AGENTS}

    for period in range(1, periods):
        for ticker in tickers:
            price_now = price_data[ticker]["price"].iloc[period]
            price_next = price_data[ticker]["price"].iloc[period + 1]
            actual_move = "up" if price_next > price_now else "down"

            metrics = compute_dynamic_metrics(
                ticker, price_now,
                price_data[ticker]["price"].iloc[period - 1],
                period, periods
            )

            for agent_id, (agent_name, agent_func) in AGENTS.items():
                signal = agent_func(ticker, metrics)
                agent_results[agent_id]["total"] += 1

                if signal["signal"] == "neutral":
                    agent_results[agent_id]["neutral"] += 1
                elif (signal["signal"] == "bullish" and actual_move == "up") or \
                     (signal["signal"] == "bearish" and actual_move == "down"):
                    agent_results[agent_id]["correct"] += 1
                else:
                    agent_results[agent_id]["wrong"] += 1

    # Print results sorted by accuracy
    print(f"  {'Agent':<28s} {'Accuracy':>8s} {'Correct':>8s} {'Wrong':>8s} {'Neutral':>8s} {'Signals':>8s}")
    print(f"  {'-'*72}")

    results = []
    for agent_id, r in agent_results.items():
        decisions = r["correct"] + r["wrong"]
        accuracy = r["correct"] / decisions * 100 if decisions > 0 else 0
        results.append((AGENTS[agent_id][0], accuracy, r["correct"], r["wrong"], r["neutral"], r["total"]))

    for name, acc, correct, wrong, neutral, total in sorted(results, key=lambda x: -x[1]):
        color = Fore.GREEN if acc >= 55 else (Fore.RED if acc < 45 else Fore.YELLOW)
        print(f"  {name:<28s} {color}{acc:>7.1f}%{Style.RESET_ALL} {correct:>8d} {wrong:>8d} {neutral:>8d} {total:>8d}")

    # Group accuracy
    print(f"\n  {'Group':<28s} {'Accuracy':>8s}")
    print(f"  {'-'*40}")
    for gname, gconfig in AGENT_GROUPS.items():
        correct = sum(agent_results[a]["correct"] for a in gconfig["agents"])
        wrong = sum(agent_results[a]["wrong"] for a in gconfig["agents"])
        decisions = correct + wrong
        acc = correct / decisions * 100 if decisions > 0 else 0
        color = Fore.GREEN if acc >= 55 else (Fore.RED if acc < 45 else Fore.YELLOW)
        print(f"  {gconfig['perspective']:<28s} {color}{acc:>7.1f}%{Style.RESET_ALL}")


# ============================================================
# ANALYSIS 2: Per-Ticker Performance Attribution
# ============================================================
def analyze_per_ticker():
    separator("ANALYSIS 2: Per-Ticker Performance Attribution")

    tickers = list(STOCK_PARAMS.keys())
    results = {}

    for exclude_ticker in [None] + tickers:
        test_tickers = [t for t in tickers if t != exclude_ticker] if exclude_ticker else tickers
        bt = AIAgentBacktester(test_tickers, 100000.0, 24)

        # Run silently
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            bt.run()

        final = bt.portfolio_values[-1]["value"]
        ret = (final / 100000 - 1) * 100
        results[exclude_ticker or "ALL"] = ret

    print(f"  {'Configuration':<25s} {'Return':>10s} {'Impact':>10s}")
    print(f"  {'-'*50}")

    all_ret = results["ALL"]
    print(f"  {'All tickers':<25s} {Fore.WHITE}{all_ret:>+9.2f}%{Style.RESET_ALL}   {'baseline':>9s}")

    for ticker in tickers:
        ret = results[ticker]
        impact = all_ret - ret
        color = Fore.GREEN if impact > 0 else Fore.RED
        print(f"  {'Without ' + ticker:<25s} {ret:>+9.2f}%   {color}{impact:>+9.2f}%{Style.RESET_ALL}")

    # Identify biggest contributor
    impacts = {t: all_ret - results[t] for t in tickers}
    best = max(impacts, key=impacts.get)
    worst = min(impacts, key=impacts.get)
    print(f"\n  Biggest contributor:    {Fore.GREEN}{best} ({impacts[best]:+.2f}% impact){Style.RESET_ALL}")
    print(f"  Biggest drag:          {Fore.RED}{worst} ({impacts[worst]:+.2f}% impact){Style.RESET_ALL}")


# ============================================================
# ANALYSIS 3: Sensitivity to Starting Capital
# ============================================================
def analyze_capital_sensitivity():
    separator("ANALYSIS 3: Sensitivity to Starting Capital")

    tickers = ["AAPL", "NVDA", "MSFT", "GOOG", "META"]

    print(f"  {'Capital':>12s} {'Final Value':>14s} {'Return':>10s} {'Trades':>8s} {'MaxDD':>8s}")
    print(f"  {'-'*58}")

    for capital in [10000, 25000, 50000, 100000, 250000, 500000]:
        bt = AIAgentBacktester(tickers, float(capital), 24)
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            bt.run()

        values = [v["value"] for v in bt.portfolio_values]
        final = values[-1]
        ret = (final / capital - 1) * 100

        # Max drawdown
        peak = values[0]
        max_dd = 0
        for v in values:
            if v > peak: peak = v
            dd = (peak - v) / peak
            if dd > max_dd: max_dd = dd

        trades = len(bt.trade_log)
        color = Fore.GREEN if ret > 0 else Fore.RED

        print(f"  ${capital:>11,d} ${final:>13,.2f} {color}{ret:>+9.2f}%{Style.RESET_ALL} {trades:>8d} {max_dd*100:>7.2f}%")


# ============================================================
# ANALYSIS 4: Committee vs Simple Averaging
# ============================================================
def analyze_committee_vs_simple():
    separator("ANALYSIS 4: Investment Committee vs Simple Averaging")

    tickers = list(STOCK_PARAMS.keys())
    periods = 24

    # Run committee version
    bt_committee = AIAgentBacktester(tickers, 100000.0, periods)
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        bt_committee.run()

    committee_values = [v["value"] for v in bt_committee.portfolio_values]
    committee_ret = (committee_values[-1] / 100000 - 1) * 100
    committee_trades = len(bt_committee.trade_log)

    # Now simulate simple averaging (override portfolio management)
    # We'll run manually with a simple weighted vote
    price_data = {t: generate_price_history(t, periods) for t in tickers}
    portfolio_simple = {
        "cash": 100000.0, "margin_requirement": 0.0, "margin_used": 0.0,
        "positions": {t: {"long": 0, "short": 0, "long_cost_basis": 0.0,
                          "short_cost_basis": 0.0, "short_margin_used": 0.0} for t in tickers},
        "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in tickers},
    }

    simple_values = [100000.0]
    simple_trades = 0

    for period in range(1, periods + 1):
        current_prices = {t: price_data[t]["price"].iloc[period] for t in tickers}
        prev_prices = {t: price_data[t]["price"].iloc[period - 1] for t in tickers}

        stock_metrics = {t: compute_dynamic_metrics(t, current_prices[t], prev_prices[t], period, periods) for t in tickers}

        # Run agents
        analyst_signals = {}
        for agent_id, (_, agent_func) in AGENTS.items():
            analyst_signals[agent_id] = {t: agent_func(t, stock_metrics[t]) for t in tickers}

        risk_analysis = run_risk_management(tickers, portfolio_simple, current_prices)

        # Simple averaging decision
        for ticker in tickers:
            bullish_w = sum(analyst_signals[a][ticker]["confidence"] / 100 for a in AGENTS
                           if analyst_signals[a][ticker]["signal"] == "bullish")
            bearish_w = sum(analyst_signals[a][ticker]["confidence"] / 100 for a in AGENTS
                           if analyst_signals[a][ticker]["signal"] == "bearish")

            risk = risk_analysis.get(ticker, {})
            price = risk.get("current_price", 0)
            max_val = risk.get("remaining_position_limit", 0)
            max_shares = int(max_val / price) if price > 0 else 0

            pos = portfolio_simple["positions"][ticker]
            net = bullish_w - bearish_w

            if net > 2.0 and max_shares > 0:
                qty = max(1, int(max_shares * 0.6))
                cost = qty * price
                if cost <= portfolio_simple["cash"]:
                    old = pos["long"]
                    if old + qty > 0:
                        pos["long_cost_basis"] = (pos["long_cost_basis"] * old + cost) / (old + qty)
                    pos["long"] += qty
                    portfolio_simple["cash"] -= cost
                    simple_trades += 1
            elif net < -2.0:
                if pos["long"] > 0:
                    portfolio_simple["cash"] += pos["long"] * price
                    pos["long"] = 0
                    pos["long_cost_basis"] = 0
                    simple_trades += 1
                elif max_shares > 0:
                    qty = max(1, int(max_shares * 0.3))
                    pos["short"] += qty
                    pos["short_cost_basis"] = price
                    portfolio_simple["cash"] += qty * price
                    simple_trades += 1

        # Calculate value
        val = portfolio_simple["cash"]
        for t in tickers:
            p = portfolio_simple["positions"][t]
            val += p["long"] * current_prices[t]
            val -= p["short"] * current_prices[t]
        simple_values.append(val)

    simple_ret = (simple_values[-1] / 100000 - 1) * 100

    # Calculate risk metrics for both
    def calc_metrics(values):
        returns = [(values[i] / values[i-1] - 1) for i in range(1, len(values))]
        returns = np.array(returns)
        avg = np.mean(returns)
        std = np.std(returns)
        sharpe = avg * 12 / (std * np.sqrt(12)) if std > 0 else 0
        peak = values[0]
        max_dd = 0
        for v in values:
            if v > peak: peak = v
            dd = (peak - v) / peak
            if dd > max_dd: max_dd = dd
        downside = returns[returns < 0]
        ds = np.std(downside) if len(downside) > 0 else 0.001
        sortino = avg * 12 / (ds * np.sqrt(12))
        return sharpe, sortino, max_dd, std

    c_sharpe, c_sortino, c_dd, c_vol = calc_metrics(committee_values)
    s_sharpe, s_sortino, s_dd, s_vol = calc_metrics(simple_values)

    print(f"  {'Metric':<25s} {'Committee':>15s} {'Simple Avg':>15s} {'Winner':>10s}")
    print(f"  {'-'*70}")

    def compare(name, c_val, s_val, fmt="+.2f", suffix="", higher_better=True):
        c_str = f"{c_val:{fmt}}{suffix}"
        s_str = f"{s_val:{fmt}}{suffix}"
        if (c_val > s_val) == higher_better:
            winner = f"{Fore.GREEN}Committee{Style.RESET_ALL}"
        elif c_val == s_val:
            winner = "Tie"
        else:
            winner = f"{Fore.RED}Simple{Style.RESET_ALL}"
        print(f"  {name:<25s} {c_str:>15s} {s_str:>15s} {winner:>20s}")

    compare("Total Return", committee_ret, simple_ret, "+.2f", "%")
    compare("Sharpe Ratio", c_sharpe, s_sharpe, ".2f")
    compare("Sortino Ratio", c_sortino, s_sortino, ".2f")
    compare("Max Drawdown", c_dd * 100, s_dd * 100, ".2f", "%", higher_better=False)
    compare("Monthly Volatility", c_vol * 100, s_vol * 100, ".2f", "%", higher_better=False)
    compare("Total Trades", committee_trades, simple_trades, "d", higher_better=False)


# ============================================================
# ANALYSIS 5: Group Contribution Analysis
# ============================================================
def analyze_group_contribution():
    separator("ANALYSIS 5: Which Group Contributes Most?")

    tickers = list(STOCK_PARAMS.keys())

    # Baseline: all groups
    bt_all = AIAgentBacktester(tickers, 100000.0, 24)
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        bt_all.run()
    all_ret = (bt_all.portfolio_values[-1]["value"] / 100000 - 1) * 100

    print(f"  {'Configuration':<35s} {'Return':>10s} {'vs All':>10s}")
    print(f"  {'-'*60}")
    print(f"  {'All groups (baseline)':<35s} {all_ret:>+9.2f}%   {'---':>9s}")

    # Test removing each group
    from scripts.run_ai_trading import AGENT_GROUPS as AG
    original_groups = dict(AG)

    for remove_group in list(AG.keys()):
        # Temporarily remove the group's agents from AGENTS
        removed_agents = AG[remove_group]["agents"]
        saved = {}
        for a in removed_agents:
            if a in AGENTS:
                saved[a] = AGENTS.pop(a)

        bt = AIAgentBacktester(tickers, 100000.0, 24)
        with contextlib.redirect_stdout(io.StringIO()):
            bt.run()

        ret = (bt.portfolio_values[-1]["value"] / 100000 - 1) * 100
        diff = all_ret - ret

        # Restore
        AGENTS.update(saved)

        color = Fore.GREEN if diff > 0 else Fore.RED
        perspective = AG[remove_group]["perspective"]
        print(f"  {'Without ' + perspective:<35s} {ret:>+9.2f}%   {color}{diff:>+9.2f}%{Style.RESET_ALL}")


# ============================================================
# ANALYSIS 6: Monthly Return Distribution
# ============================================================
def analyze_return_distribution():
    separator("ANALYSIS 6: Monthly Return Distribution")

    tickers = list(STOCK_PARAMS.keys())
    bt = AIAgentBacktester(tickers, 100000.0, 24)
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        bt.run()

    values = [v["value"] for v in bt.portfolio_values]
    returns = [(values[i] / values[i-1] - 1) * 100 for i in range(1, len(values))]

    positive = [r for r in returns if r > 0]
    negative = [r for r in returns if r < 0]
    flat = [r for r in returns if r == 0]

    print(f"  Total months:        {len(returns)}")
    print(f"  Positive months:     {Fore.GREEN}{len(positive)} ({len(positive)/len(returns)*100:.0f}%){Style.RESET_ALL}")
    print(f"  Negative months:     {Fore.RED}{len(negative)} ({len(negative)/len(returns)*100:.0f}%){Style.RESET_ALL}")
    print(f"  Flat months:         {len(flat)}")
    print(f"")
    print(f"  Best month:          {Fore.GREEN}{max(returns):>+.2f}%{Style.RESET_ALL}")
    print(f"  Worst month:         {Fore.RED}{min(returns):>+.2f}%{Style.RESET_ALL}")
    print(f"  Average month:       {np.mean(returns):>+.2f}%")
    print(f"  Median month:        {np.median(returns):>+.2f}%")
    print(f"  Std deviation:       {np.std(returns):.2f}%")
    print(f"")

    # Histogram
    print(f"  Monthly returns distribution:")
    buckets = [(-100, -10), (-10, -5), (-5, -2), (-2, 0), (0, 2), (2, 5), (5, 10), (10, 50), (50, 200)]
    for lo, hi in buckets:
        count = sum(1 for r in returns if lo <= r < hi)
        bar = "#" * (count * 3)
        color = Fore.RED if hi <= 0 else Fore.GREEN
        print(f"    {lo:>+4d}% to {hi:>+4d}%: {color}{bar} ({count}){Style.RESET_ALL}")

    # Equity curve
    print(f"\n  Equity curve (monthly):")
    for i, v in enumerate(bt.portfolio_values):
        bar_len = int(v["value"] / 5000)
        date = v["date"]
        ret = (v["value"] / 100000 - 1) * 100
        color = Fore.GREEN if ret >= 0 else Fore.RED
        bar = "|" * min(bar_len, 60)
        print(f"    {date:>7s} ${v['value']:>10,.0f} {color}{ret:>+7.1f}%{Style.RESET_ALL} {Fore.CYAN}{bar}{Style.RESET_ALL}")


# ============================================================
# ANALYSIS 7: Stress Test - Different Market Regimes
# ============================================================
def analyze_stress_test():
    separator("ANALYSIS 7: Stress Test - Different Seed Scenarios")

    tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOG", "META"]

    print(f"  Running 10 different market scenarios...")
    print(f"  {'Scenario':>10s} {'Return':>10s} {'MaxDD':>8s} {'Sharpe':>8s} {'Trades':>8s}")
    print(f"  {'-'*50}")

    all_returns = []
    for seed in range(10):
        # Override random seed for each scenario
        old_seed_func = np.random.seed

        # Monkey-patch generate_price_history for this run
        original_func = generate_price_history.__code__
        # Instead, we'll add an offset to the hash
        import scripts.backtest_ai_agents as bmod
        orig_gen = bmod.generate_price_history

        def patched_gen(ticker, periods=24, _seed=seed):
            params = STOCK_PARAMS[ticker]
            np.random.seed((hash(ticker) + _seed * 7919) % 2**31)
            monthly_return = params["annual_return"] / 12
            monthly_vol = params["annual_vol"] / np.sqrt(12)
            prices = [params["start_price"]]
            for i in range(periods):
                ret = np.random.normal(monthly_return, monthly_vol)
                prices.append(prices[-1] * (1 + ret))
            dates = pd.date_range(start="2024-01-01", periods=periods + 1, freq="MS")
            return pd.DataFrame({"date": dates, "price": prices})

        bmod.generate_price_history = patched_gen

        bt = AIAgentBacktester(tickers, 100000.0, 24)
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            bt.run()

        bmod.generate_price_history = orig_gen

        values = [v["value"] for v in bt.portfolio_values]
        ret = (values[-1] / 100000 - 1) * 100
        all_returns.append(ret)

        # Metrics
        monthly = np.array([(values[i] / values[i-1] - 1) for i in range(1, len(values))])
        avg = np.mean(monthly)
        std = np.std(monthly)
        sharpe = avg * 12 / (std * np.sqrt(12)) if std > 0 else 0
        peak = values[0]
        max_dd = 0
        for v in values:
            if v > peak: peak = v
            dd = (peak - v) / peak
            if dd > max_dd: max_dd = dd

        color = Fore.GREEN if ret > 0 else Fore.RED
        print(f"  {'#' + str(seed+1):>10s} {color}{ret:>+9.2f}%{Style.RESET_ALL} {max_dd*100:>7.2f}% {sharpe:>7.2f} {len(bt.trade_log):>8d}")

    all_returns = np.array(all_returns)
    print(f"  {'-'*50}")
    print(f"  {'Average':>10s} {np.mean(all_returns):>+9.2f}%")
    print(f"  {'Median':>10s} {np.median(all_returns):>+9.2f}%")
    print(f"  {'Best':>10s} {Fore.GREEN}{np.max(all_returns):>+9.2f}%{Style.RESET_ALL}")
    print(f"  {'Worst':>10s} {Fore.RED}{np.min(all_returns):>+9.2f}%{Style.RESET_ALL}")
    print(f"  {'Profitable':>10s} {sum(1 for r in all_returns if r > 0)}/10 scenarios")
    print(f"  {'Std Dev':>10s} {np.std(all_returns):.2f}%")


# ============================================================
# RUN ALL ANALYSES
# ============================================================
if __name__ == "__main__":
    print(f"\n{Fore.WHITE}{Style.BRIGHT}{'#'*80}")
    print(f"  AI HEDGE FUND - COMPREHENSIVE DEEP ANALYSIS")
    print(f"  15 AI Agents | Investment Committee Model | 7 Stocks")
    print(f"{'#'*80}{Style.RESET_ALL}")

    analyze_agent_accuracy()
    analyze_per_ticker()
    analyze_capital_sensitivity()
    analyze_committee_vs_simple()
    analyze_group_contribution()
    analyze_return_distribution()
    analyze_stress_test()

    separator("ANALYSIS COMPLETE")
