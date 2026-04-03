#!/usr/bin/env python3
"""
AI Hedge Fund - Comparative Backtest
Compares v1 (original) vs v2 (enhanced) vs Buy & Hold
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
root_logger = logging.getLogger()
root_logger.handlers.clear()
logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stdout, force=True)

import io
import contextlib
import numpy as np
import pandas as pd
from colorama import Fore, Style, init
init(autoreset=True)

from scripts.backtest_ai_agents import AIAgentBacktester, STOCK_PARAMS


def calc_metrics(values, initial=100000.0):
    """Calculate comprehensive risk/return metrics."""
    monthly_returns = np.array([(values[i] / values[i-1] - 1) for i in range(1, len(values))])
    total_ret = (values[-1] / initial - 1) * 100
    avg_m = np.mean(monthly_returns)
    std_m = np.std(monthly_returns)
    
    # Sharpe (annualized)
    sharpe = (avg_m * 12) / (std_m * np.sqrt(12)) if std_m > 0 else 0
    
    # Sortino
    downside = monthly_returns[monthly_returns < 0]
    ds = np.std(downside) if len(downside) > 0 else 0.001
    sortino = (avg_m * 12) / (ds * np.sqrt(12))
    
    # Max drawdown
    peak = values[0]
    max_dd = 0
    for v in values:
        if v > peak: peak = v
        dd = (peak - v) / peak
        if dd > max_dd: max_dd = dd
    
    # Calmar ratio
    calmar = (total_ret / 100 * 12 / len(monthly_returns)) / max_dd if max_dd > 0 else 0
    
    # Win rate
    win_months = sum(1 for r in monthly_returns if r > 0)
    
    return {
        "total_return": total_ret,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd * 100,
        "calmar": calmar,
        "volatility": std_m * np.sqrt(12) * 100,
        "avg_monthly": avg_m * 100,
        "win_rate": win_months / len(monthly_returns) * 100,
        "best_month": max(monthly_returns) * 100,
        "worst_month": min(monthly_returns) * 100,
    }


def run_comparison():
    tickers = list(STOCK_PARAMS.keys())
    initial = 100000.0
    periods = 24
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"  COMPARATIVE BACKTEST: v1 Committee vs Buy & Hold")
    print(f"  {periods} months | {len(tickers)} stocks | ${initial:,.0f} initial")
    print(f"{'='*80}{Style.RESET_ALL}\n")
    
    # Run v1 (committee)
    print("  Running v1 (Investment Committee)...", end=" ", flush=True)
    bt = AIAgentBacktester(tickers, initial, periods)
    with contextlib.redirect_stdout(io.StringIO()):
        bt.run()
    v1_values = [v["value"] for v in bt.portfolio_values]
    v1_trades = len(bt.trade_log)
    print(f"{Fore.GREEN}Done{Style.RESET_ALL}")
    
    # Run Buy & Hold (equal weight)
    print("  Running Buy & Hold (equal weight)...", end=" ", flush=True)
    from scripts.backtest_ai_agents import generate_price_history
    price_data = {t: generate_price_history(t, periods) for t in tickers}
    
    bh_values = [initial]
    bh_shares = {}
    weight = 1.0 / len(tickers)
    for t in tickers:
        start_p = price_data[t]["price"].iloc[0]
        bh_shares[t] = (initial * weight) / start_p
    
    for period in range(1, periods + 1):
        val = sum(bh_shares[t] * price_data[t]["price"].iloc[period] for t in tickers)
        bh_values.append(val)
    print(f"{Fore.GREEN}Done{Style.RESET_ALL}")
    
    # Try to run v2 if available
    v2_available = False
    try:
        from scripts.run_ai_trading_v2 import AGENTS as V2_AGENTS, run_investment_committee as v2_committee
        from scripts.run_ai_trading_v2 import run_risk_management as v2_risk
        v2_available = True
        print("  Running v2 (Enhanced Committee)...", end=" ", flush=True)
        # Would need a v2-compatible backtester - skip for now
        print(f"{Fore.YELLOW}Available but needs v2 backtester{Style.RESET_ALL}")
    except ImportError:
        print(f"  v2 not yet available - will compare when ready")
    
    # Calculate metrics
    v1_m = calc_metrics(v1_values, initial)
    bh_m = calc_metrics(bh_values, initial)
    
    # Display comparison
    print(f"\n{Style.BRIGHT}  {'Metric':<25s} {'AI Committee':>15s} {'Buy & Hold':>15s} {'Winner':>12s}{Style.RESET_ALL}")
    print(f"  {'-'*70}")
    
    comparisons = [
        ("Total Return", "total_return", "%", True),
        ("Sharpe Ratio", "sharpe", "", True),
        ("Sortino Ratio", "sortino", "", True),
        ("Max Drawdown", "max_drawdown", "%", False),
        ("Annual Volatility", "volatility", "%", False),
        ("Win Rate (months)", "win_rate", "%", True),
        ("Best Month", "best_month", "%", True),
        ("Worst Month", "worst_month", "%", False),
        ("Avg Monthly Return", "avg_monthly", "%", True),
    ]
    
    v1_wins = 0
    bh_wins = 0
    
    for name, key, suffix, higher_better in comparisons:
        v1_val = v1_m[key]
        bh_val = bh_m[key]
        
        if higher_better:
            winner = "AI" if v1_val > bh_val else "B&H"
        else:
            winner = "AI" if v1_val < bh_val else "B&H"
        
        if winner == "AI":
            v1_wins += 1
            w_str = f"{Fore.GREEN}AI Wins{Style.RESET_ALL}"
        else:
            bh_wins += 1
            w_str = f"{Fore.RED}B&H Wins{Style.RESET_ALL}"
        
        print(f"  {name:<25s} {v1_val:>+14.2f}{suffix} {bh_val:>+14.2f}{suffix} {w_str:>22s}")
    
    print(f"  {'-'*70}")
    print(f"  {'Score':<25s} {v1_wins:>15d} {bh_wins:>15d}")
    
    # Detailed analysis of WHERE AI wins/loses
    print(f"\n{Style.BRIGHT}  MONTH-BY-MONTH COMPARISON:{Style.RESET_ALL}")
    ai_better = 0
    bh_better = 0
    for i in range(1, min(len(v1_values), len(bh_values))):
        v1_ret = (v1_values[i] / v1_values[i-1] - 1) * 100
        bh_ret = (bh_values[i] / bh_values[i-1] - 1) * 100
        diff = v1_ret - bh_ret
        
        date = bt.portfolio_values[i]["date"]
        color = Fore.GREEN if diff > 0 else Fore.RED
        marker = ">>>" if abs(diff) > 5 else ""
        
        if diff > 0: ai_better += 1
        else: bh_better += 1
        
        print(f"    {date}: AI {v1_ret:>+6.2f}% | B&H {bh_ret:>+6.2f}% | Diff: {color}{diff:>+6.2f}%{Style.RESET_ALL} {marker}")
    
    print(f"\n  AI better in {ai_better}/{ai_better+bh_better} months ({ai_better/(ai_better+bh_better)*100:.0f}%)")
    
    # Key insight
    print(f"\n{Style.BRIGHT}  KEY INSIGHTS:{Style.RESET_ALL}")
    alpha = v1_m["total_return"] - bh_m["total_return"]
    if alpha > 0:
        print(f"  {Fore.GREEN}+ AI generated {alpha:+.2f}% alpha over buy & hold{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}- AI underperformed buy & hold by {abs(alpha):.2f}%{Style.RESET_ALL}")
    
    if v1_m["max_drawdown"] < bh_m["max_drawdown"]:
        print(f"  {Fore.GREEN}+ AI had better risk management (DD: {v1_m['max_drawdown']:.1f}% vs {bh_m['max_drawdown']:.1f}%){Style.RESET_ALL}")
    
    if v1_m["sharpe"] > bh_m["sharpe"]:
        print(f"  {Fore.GREEN}+ AI had better risk-adjusted returns (Sharpe: {v1_m['sharpe']:.2f} vs {bh_m['sharpe']:.2f}){Style.RESET_ALL}")
    
    cash_pct = bt.portfolio["cash"] / v1_values[-1] * 100
    if cash_pct > 20:
        print(f"  {Fore.YELLOW}! AI held {cash_pct:.0f}% cash at end - opportunity cost{Style.RESET_ALL}")
    
    trades_per_month = v1_trades / periods
    print(f"  {Fore.WHITE}  Trading frequency: {trades_per_month:.1f} trades/month{Style.RESET_ALL}")


if __name__ == "__main__":
    run_comparison()
