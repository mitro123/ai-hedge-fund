#!/usr/bin/env python3
"""
AI Hedge Fund - Backtest with 15 AI Agents on Historical Data

Simulates historical price data and runs the full agent pipeline
across multiple time periods to measure profitability.

Usage:
    python scripts/backtest_ai_agents.py
    python scripts/backtest_ai_agents.py --tickers AAPL,NVDA,GOOG --periods 24
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

root_logger = logging.getLogger()
root_logger.handlers.clear()
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,
)

from colorama import Fore, Style, init
init(autoreset=True)


# ============================================================
# HISTORICAL STOCK DATA GENERATOR
# Generates realistic price paths for backtesting
# ============================================================

# Real approximate parameters based on 2023-2025 data
STOCK_PARAMS = {
    "AAPL": {"start_price": 130.0, "annual_return": 0.25, "annual_vol": 0.28, "pe_range": (25, 35), "roe": 160, "gross_margin": 0.45, "rnd_ratio": 0.07, "debt_equity": 1.8, "sector": "Technology"},
    "NVDA": {"start_price": 150.0, "annual_return": 1.50, "annual_vol": 0.55, "pe_range": (40, 80), "roe": 90, "gross_margin": 0.73, "rnd_ratio": 0.15, "debt_equity": 0.4, "sector": "Technology/AI"},
    "MSFT": {"start_price": 250.0, "annual_return": 0.30, "annual_vol": 0.25, "pe_range": (28, 38), "roe": 40, "gross_margin": 0.69, "rnd_ratio": 0.12, "debt_equity": 0.3, "sector": "Technology/Cloud"},
    "TSLA": {"start_price": 120.0, "annual_return": 0.10, "annual_vol": 0.60, "pe_range": (50, 100), "roe": 20, "gross_margin": 0.18, "rnd_ratio": 0.05, "debt_equity": 0.1, "sector": "Auto/Energy"},
    "GOOG": {"start_price": 100.0, "annual_return": 0.35, "annual_vol": 0.27, "pe_range": (20, 28), "roe": 30, "gross_margin": 0.57, "rnd_ratio": 0.12, "debt_equity": 0.1, "sector": "Technology/Ad"},
    "AMZN": {"start_price": 100.0, "annual_return": 0.30, "annual_vol": 0.30, "pe_range": (35, 55), "roe": 22, "gross_margin": 0.48, "rnd_ratio": 0.14, "debt_equity": 0.6, "sector": "Technology/Retail"},
    "META": {"start_price": 180.0, "annual_return": 0.60, "annual_vol": 0.40, "pe_range": (18, 30), "roe": 35, "gross_margin": 0.81, "rnd_ratio": 0.28, "debt_equity": 0.3, "sector": "Technology/Social"},
}


def generate_price_history(ticker: str, periods: int = 24) -> pd.DataFrame:
    """Generate realistic monthly price data using geometric Brownian motion."""
    params = STOCK_PARAMS[ticker]
    np.random.seed(hash(ticker) % 2**31)

    monthly_return = params["annual_return"] / 12
    monthly_vol = params["annual_vol"] / np.sqrt(12)

    prices = [params["start_price"]]
    for i in range(periods):
        ret = np.random.normal(monthly_return, monthly_vol)
        prices.append(prices[-1] * (1 + ret))

    dates = pd.date_range(start="2024-01-01", periods=periods + 1, freq="MS")
    df = pd.DataFrame({"date": dates, "price": prices})
    return df


def compute_dynamic_metrics(ticker: str, price: float, prev_price: float, period_idx: int, total_periods: int) -> dict:
    """Compute time-varying stock metrics based on price movements."""
    params = STOCK_PARAMS[ticker]
    price_change = (price - prev_price) / prev_price if prev_price > 0 else 0

    # PE oscillates within range based on price momentum
    pe_lo, pe_hi = params["pe_range"]
    pe_mid = (pe_lo + pe_hi) / 2
    pe = pe_mid + (price_change * 50)  # Higher prices -> higher PE
    pe = max(pe_lo, min(pe_hi, pe))

    # Earnings growth correlates with price momentum
    earnings_growth = max(-0.20, min(1.5, price_change * 4 + 0.10))

    # Revenue growth is smoother
    revenue_growth = max(-0.05, min(1.2, price_change * 2 + 0.08))

    # PEG ratio
    peg = pe / max(earnings_growth * 100, 1) if earnings_growth > 0 else -5.0

    # EV/EBITDA correlates with PE
    ev_ebitda = pe * 0.7

    # FCF yield inversely related to PE
    fcf_yield = max(0.005, 1.0 / pe * 0.8)

    return {
        "price": round(price, 2),
        "pe": round(pe, 1),
        "pb": round(pe * 0.3, 1),  # Simplified
        "roe": params["roe"],
        "debt_equity": params["debt_equity"],
        "revenue_growth": round(revenue_growth, 3),
        "earnings_growth": round(earnings_growth, 3),
        "peg": round(peg, 2),
        "ev_ebitda": round(ev_ebitda, 1),
        "market_cap_b": round(price * 15, 0),  # Simplified
        "sector": params["sector"],
        "dividend_yield": 0.005,
        "gross_margin": params["gross_margin"],
        "fcf_yield": round(fcf_yield, 4),
        "rnd_ratio": params["rnd_ratio"],
        "insider_ownership": 0.05,
    }


# ============================================================
# IMPORT AGENT FUNCTIONS FROM run_ai_trading.py
# ============================================================
from scripts.run_ai_trading import (
    AGENTS,
    run_risk_management,
    run_portfolio_management,
)


# ============================================================
# BACKTESTER
# ============================================================

class AIAgentBacktester:
    """Backtest the 15 AI agents across historical price data."""

    def __init__(self, tickers: List[str], initial_cash: float = 100000.0, periods: int = 24):
        self.tickers = [t for t in tickers if t in STOCK_PARAMS]
        self.initial_cash = initial_cash
        self.periods = periods

        # Generate price histories
        self.price_data = {}
        for ticker in self.tickers:
            self.price_data[ticker] = generate_price_history(ticker, periods)

        # Portfolio state
        self.portfolio = {
            "cash": initial_cash,
            "margin_requirement": 0.0,
            "margin_used": 0.0,
            "positions": {
                t: {"long": 0, "short": 0, "long_cost_basis": 0.0,
                    "short_cost_basis": 0.0, "short_margin_used": 0.0}
                for t in self.tickers
            },
            "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in self.tickers},
        }

        # Track history
        self.portfolio_values = []
        self.trade_log = []

    def get_portfolio_value(self, prices: dict) -> float:
        """Calculate total portfolio value at given prices."""
        value = self.portfolio["cash"]
        for ticker in self.tickers:
            pos = self.portfolio["positions"][ticker]
            price = prices.get(ticker, 0)
            value += pos["long"] * price
            value -= pos["short"] * price
        return value

    def execute_trade(self, ticker: str, action: str, quantity: int, price: float) -> int:
        """Execute a trade and return actual quantity traded."""
        if quantity <= 0:
            return 0

        pos = self.portfolio["positions"][ticker]

        if action == "buy":
            cost = quantity * price
            if cost > self.portfolio["cash"]:
                quantity = int(self.portfolio["cash"] / price)
                cost = quantity * price
            if quantity > 0:
                old = pos["long"]
                if old + quantity > 0:
                    pos["long_cost_basis"] = (pos["long_cost_basis"] * old + cost) / (old + quantity)
                pos["long"] += quantity
                self.portfolio["cash"] -= cost
                return quantity

        elif action == "sell":
            quantity = min(quantity, pos["long"])
            if quantity > 0:
                gain = (price - pos["long_cost_basis"]) * quantity
                self.portfolio["realized_gains"][ticker]["long"] += gain
                pos["long"] -= quantity
                self.portfolio["cash"] += quantity * price
                if pos["long"] == 0:
                    pos["long_cost_basis"] = 0.0
                return quantity

        elif action == "short":
            proceeds = quantity * price
            pos["short"] += quantity
            pos["short_cost_basis"] = price
            self.portfolio["cash"] += proceeds
            return quantity

        elif action == "cover":
            quantity = min(quantity, pos["short"])
            if quantity > 0:
                cost = quantity * price
                gain = (pos["short_cost_basis"] - price) * quantity
                self.portfolio["realized_gains"][ticker]["short"] += gain
                pos["short"] -= quantity
                self.portfolio["cash"] -= cost
                if pos["short"] == 0:
                    pos["short_cost_basis"] = 0.0
                return quantity

        return 0

    def run(self):
        """Run the full backtest."""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
        print(f"  AI HEDGE FUND BACKTEST - 15 AI AGENTS")
        print(f"{'='*70}{Style.RESET_ALL}")
        print(f"  Period:       {self.periods} months (2024-01 to {(datetime(2024,1,1) + timedelta(days=30*self.periods)).strftime('%Y-%m')})")
        print(f"  Initial Cash: {Fore.GREEN}${self.initial_cash:,.2f}{Style.RESET_ALL}")
        print(f"  Tickers:      {Fore.YELLOW}{', '.join(self.tickers)}{Style.RESET_ALL}")
        print(f"  Agents:       {Fore.CYAN}{len(AGENTS)} AI investors{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

        # Record initial value
        initial_prices = {t: self.price_data[t]["price"].iloc[0] for t in self.tickers}
        self.portfolio_values.append({"period": 0, "date": "2024-01", "value": self.initial_cash})

        for period in range(1, self.periods + 1):
            # Get current and previous prices
            current_prices = {}
            prev_prices = {}
            for ticker in self.tickers:
                current_prices[ticker] = self.price_data[ticker]["price"].iloc[period]
                prev_prices[ticker] = self.price_data[ticker]["price"].iloc[period - 1]

            date_str = self.price_data[self.tickers[0]]["date"].iloc[period].strftime("%Y-%m")

            # Compute dynamic metrics for each stock
            stock_metrics = {}
            for ticker in self.tickers:
                stock_metrics[ticker] = compute_dynamic_metrics(
                    ticker, current_prices[ticker], prev_prices[ticker], period, self.periods
                )

            # Run all 15 agents
            analyst_signals = {}
            for agent_id, (agent_name, agent_func) in AGENTS.items():
                signals = {}
                for ticker in self.tickers:
                    signals[ticker] = agent_func(ticker, stock_metrics[ticker])
                analyst_signals[agent_id] = signals

            # Risk management
            risk_analysis = run_risk_management(self.tickers, self.portfolio, current_prices)
            analyst_signals["risk_management_agent"] = risk_analysis

            # Portfolio decisions
            decisions = run_portfolio_management(
                self.tickers, analyst_signals, risk_analysis, self.portfolio
            )

            # Execute trades
            period_trades = []
            for ticker in self.tickers:
                dec = decisions[ticker]
                action = dec["action"]
                quantity = dec["quantity"]
                price = current_prices[ticker]

                if action != "hold" and quantity > 0:
                    actual = self.execute_trade(ticker, action, quantity, price)
                    if actual > 0:
                        period_trades.append(f"{action.upper()} {actual} {ticker} @${price:.2f}")
                        self.trade_log.append({
                            "period": period, "date": date_str, "ticker": ticker,
                            "action": action, "quantity": actual, "price": price,
                        })

            # Record portfolio value
            port_value = self.get_portfolio_value(current_prices)
            self.portfolio_values.append({"period": period, "date": date_str, "value": port_value})

            # Print period summary
            ret = (port_value / self.initial_cash - 1) * 100
            ret_color = Fore.GREEN if ret >= 0 else Fore.RED
            trades_str = ", ".join(period_trades) if period_trades else "No trades"

            print(f"  {Fore.WHITE}{date_str}{Style.RESET_ALL} | "
                  f"Value: {Fore.WHITE}${port_value:>10,.2f}{Style.RESET_ALL} | "
                  f"Return: {ret_color}{ret:>+7.2f}%{Style.RESET_ALL} | "
                  f"{trades_str}")

        # Final summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive backtest results."""
        values = [v["value"] for v in self.portfolio_values]
        dates = [v["date"] for v in self.portfolio_values]
        final_value = values[-1]
        total_return = (final_value / self.initial_cash - 1) * 100

        # Calculate monthly returns for Sharpe/Sortino
        monthly_returns = []
        for i in range(1, len(values)):
            monthly_returns.append(values[i] / values[i-1] - 1)

        monthly_returns = np.array(monthly_returns)
        avg_monthly = np.mean(monthly_returns)
        std_monthly = np.std(monthly_returns)

        # Sharpe ratio (annualized, assuming 0% risk-free)
        sharpe = (avg_monthly * 12) / (std_monthly * np.sqrt(12)) if std_monthly > 0 else 0

        # Sortino ratio (downside deviation only)
        downside = monthly_returns[monthly_returns < 0]
        downside_std = np.std(downside) if len(downside) > 0 else 0.001
        sortino = (avg_monthly * 12) / (downside_std * np.sqrt(12)) if downside_std > 0 else 0

        # Max drawdown
        peak = values[0]
        max_dd = 0
        for v in values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            if dd > max_dd:
                max_dd = dd

        # Buy & Hold benchmark (equal weight)
        bh_value = self.initial_cash
        weights = {t: 1.0 / len(self.tickers) for t in self.tickers}
        bh_shares = {}
        for t in self.tickers:
            start_price = self.price_data[t]["price"].iloc[0]
            bh_shares[t] = (bh_value * weights[t]) / start_price

        bh_final = 0
        for t in self.tickers:
            end_price = self.price_data[t]["price"].iloc[-1]
            bh_final += bh_shares[t] * end_price
        bh_return = (bh_final / self.initial_cash - 1) * 100

        # Trade statistics
        total_trades = len(self.trade_log)
        buys = sum(1 for t in self.trade_log if t["action"] == "buy")
        sells = sum(1 for t in self.trade_log if t["action"] == "sell")
        shorts = sum(1 for t in self.trade_log if t["action"] == "short")

        # Print results
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
        print(f"  BACKTEST RESULTS")
        print(f"{'='*70}{Style.RESET_ALL}")

        print(f"\n{Style.BRIGHT}  PERFORMANCE:{Style.RESET_ALL}")
        ret_color = Fore.GREEN if total_return >= 0 else Fore.RED
        bh_color = Fore.GREEN if bh_return >= 0 else Fore.RED
        alpha_val = total_return - bh_return
        alpha_color = Fore.GREEN if alpha_val >= 0 else Fore.RED

        print(f"    Initial Value:     ${self.initial_cash:>12,.2f}")
        print(f"    Final Value:       ${final_value:>12,.2f}")
        print(f"    Total Return:      {ret_color}{total_return:>+11.2f}%{Style.RESET_ALL}")
        print(f"    Buy & Hold Return: {bh_color}{bh_return:>+11.2f}%{Style.RESET_ALL}")
        print(f"    Alpha (vs B&H):    {alpha_color}{alpha_val:>+11.2f}%{Style.RESET_ALL}")

        print(f"\n{Style.BRIGHT}  RISK METRICS:{Style.RESET_ALL}")
        print(f"    Sharpe Ratio:      {sharpe:>11.2f}")
        print(f"    Sortino Ratio:     {sortino:>11.2f}")
        print(f"    Max Drawdown:      {Fore.RED}{max_dd*100:>10.2f}%{Style.RESET_ALL}")
        print(f"    Monthly Volatility:{std_monthly*100:>10.2f}%")

        print(f"\n{Style.BRIGHT}  TRADING ACTIVITY:{Style.RESET_ALL}")
        print(f"    Total Trades:      {total_trades:>11d}")
        print(f"    Buys:              {buys:>11d}")
        print(f"    Sells:             {sells:>11d}")
        print(f"    Shorts:            {shorts:>11d}")

        print(f"\n{Style.BRIGHT}  FINAL POSITIONS:{Style.RESET_ALL}")
        for ticker in self.tickers:
            pos = self.portfolio["positions"][ticker]
            end_price = self.price_data[ticker]["price"].iloc[-1]
            if pos["long"] > 0:
                val = pos["long"] * end_price
                gain = (end_price - pos["long_cost_basis"]) / pos["long_cost_basis"] * 100 if pos["long_cost_basis"] > 0 else 0
                g_color = Fore.GREEN if gain >= 0 else Fore.RED
                print(f"    {ticker:5s}: LONG  {pos['long']:>5} shares @ ${end_price:>8.2f} = ${val:>10,.2f} ({g_color}{gain:>+.1f}%{Style.RESET_ALL})")
            if pos["short"] > 0:
                val = pos["short"] * end_price
                print(f"    {ticker:5s}: SHORT {pos['short']:>5} shares @ ${end_price:>8.2f} = ${val:>10,.2f}")

        print(f"    Cash:  ${self.portfolio['cash']:>12,.2f}")

        # Price performance table
        print(f"\n{Style.BRIGHT}  STOCK PRICE CHANGES:{Style.RESET_ALL}")
        for ticker in self.tickers:
            start_p = self.price_data[ticker]["price"].iloc[0]
            end_p = self.price_data[ticker]["price"].iloc[-1]
            chg = (end_p / start_p - 1) * 100
            c = Fore.GREEN if chg >= 0 else Fore.RED
            print(f"    {ticker:5s}: ${start_p:>8.2f} -> ${end_p:>8.2f}  ({c}{chg:>+.1f}%{Style.RESET_ALL})")

        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

        # Verdict
        if total_return > bh_return:
            print(f"  {Fore.GREEN}{Style.BRIGHT}VERDICT: AI agents OUTPERFORMED buy & hold by {alpha_val:+.2f}%{Style.RESET_ALL}")
        elif total_return > 0:
            print(f"  {Fore.YELLOW}{Style.BRIGHT}VERDICT: AI agents were profitable (+{total_return:.2f}%) but underperformed buy & hold{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}{Style.BRIGHT}VERDICT: AI agents lost money ({total_return:.2f}%){Style.RESET_ALL}")

        print()


def main():
    parser = argparse.ArgumentParser(description="AI Hedge Fund Backtest")
    parser.add_argument("--tickers", type=str, default="AAPL,NVDA,MSFT,TSLA,GOOG,AMZN,META",
                        help="Comma-separated tickers")
    parser.add_argument("--initial-cash", type=float, default=100000.0,
                        help="Initial cash (default: $100,000)")
    parser.add_argument("--periods", type=int, default=24,
                        help="Number of monthly periods (default: 24 = 2 years)")
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    bt = AIAgentBacktester(tickers, args.initial_cash, args.periods)
    bt.run()


if __name__ == "__main__":
    main()
