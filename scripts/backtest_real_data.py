#!/usr/bin/env python3
"""
AI Hedge Fund - Backtest on REAL Historical Data (Yahoo Finance)
Walk-forward test: at each month, compute metrics from data known at that time.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import logging
root_logger = logging.getLogger()
root_logger.handlers.clear()
logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stdout, force=True)

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from colorama import Fore, Style, init
init(autoreset=True)

from scripts.run_live_trading import (
    AGENTS, run_risk_management, run_investment_committee
)
from src.data.dynamic_fundamentals import DynamicFundamentals


def fetch_all_history(tickers, period="3y"):
    """Fetch full price history for all tickers + SPY benchmark."""
    print(f"  Fetching historical data from Yahoo Finance...")
    data = {}
    for t in tickers + ["SPY"]:
        ticker = yf.Ticker(t)
        hist = ticker.history(period=period)
        if not hist.empty:
            data[t] = hist
            print(f"    {t}: {len(hist)} days ({hist.index[0].strftime('%Y-%m-%d')} to {hist.index[-1].strftime('%Y-%m-%d')})")
        else:
            print(f"    {t}: NO DATA")
    return data


def compute_metrics_at_date(ticker, hist, spy_hist, date_idx, info_cache, dynamic_fund=None):
    """Compute all agent metrics using only data available up to date_idx."""
    # Slice history up to this date
    h = hist.iloc[:date_idx + 1]
    if len(h) < 50:
        return None

    close = h["Close"]
    current = float(close.iloc[-1])

    # Momentum
    m3 = (current / float(close.iloc[-63]) - 1) if len(close) > 63 else 0
    m6 = (current / float(close.iloc[-126]) - 1) if len(close) > 126 else 0
    m12 = (current / float(close.iloc[-252]) - 1) if len(close) > 252 else 0

    # SMA
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else sma50

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, 1e-10)
    rsi = float((100 - (100 / (1 + rs))).iloc[-1])

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9).mean()
    macd = {
        "macd": float(macd_line.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float((macd_line - signal_line).iloc[-1]),
        "bullish_cross": float(macd_line.iloc[-1]) > float(signal_line.iloc[-1]),
    }

    # Bollinger
    bb_sma = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = float((bb_sma + 2 * bb_std).iloc[-1])
    bb_lower = float((bb_sma - 2 * bb_std).iloc[-1])
    pct_b = (current - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
    bollinger = {"upper": bb_upper, "lower": bb_lower, "middle": float(bb_sma.iloc[-1]), "pct_b": pct_b}

    # Volatility
    daily_ret = close.pct_change().dropna()
    vol = float(daily_ret.tail(30).std() * np.sqrt(252)) if len(daily_ret) > 30 else 0.25

    # 52w high/low
    w52 = close.tail(252) if len(close) >= 252 else close
    high_52 = float(w52.max())
    low_52 = float(w52.min())
    dist_high = (current / high_52 - 1) if high_52 > 0 else 0

    # Relative strength vs SPY
    spy_slice = spy_hist.iloc[:date_idx + 1]["Close"] if spy_hist is not None else None
    rel_strength = 0
    if spy_slice is not None and len(spy_slice) > 252:
        spy_ret = float(spy_slice.iloc[-1] / spy_slice.iloc[-252] - 1)
        rel_strength = m12 - spy_ret

    # Market regime from SPY
    regime = "unknown"
    if spy_slice is not None and len(spy_slice) >= 200:
        spy_close = spy_slice
        spy_sma50 = float(spy_close.rolling(50).mean().iloc[-1])
        spy_sma200 = float(spy_close.rolling(200).mean().iloc[-1])
        spy_now = float(spy_close.iloc[-1])
        if spy_now > spy_sma50 > spy_sma200:
            regime = "bull"
        elif spy_now < spy_sma200:
            regime = "bear"
        else:
            regime = "sideways"

    # DYNAMIC FUNDAMENTALS: compute PE, growth, margins as known at this date
    as_of = hist.index[date_idx].to_pydatetime()
    if hasattr(as_of, 'tz') and as_of.tzinfo is not None:
        as_of = as_of.replace(tzinfo=None)

    if dynamic_fund is not None:
        dyn = dynamic_fund.compute_metrics_at_date(ticker, as_of, current)
    else:
        dyn = {}

    # Fallback to static info_cache for fields dynamic doesn't cover
    info = info_cache.get(ticker, {})

    # Use dynamic values when available, fall back to static
    pe = dyn.get("pe") or (info.get("trailingPE", 0) or 0)
    fwd_pe = dyn.get("forward_pe") or (info.get("forwardPE", 0) or 0)
    pb = dyn.get("pb") or (info.get("priceToBook", 0) or 0)
    roe = dyn.get("roe") or ((info.get("returnOnEquity", 0) or 0) * 100)
    rev_growth = dyn.get("revenue_growth") or (info.get("revenueGrowth", 0) or 0)
    eps_growth = dyn.get("earnings_growth") or (info.get("earningsGrowth", 0) or 0)
    gross_margin = dyn.get("gross_margin") or (info.get("grossMargins", 0) or 0)
    op_margin = dyn.get("operating_margin") or (info.get("operatingMargins", 0) or 0)
    ev_ebitda = dyn.get("ev_ebitda") or (info.get("enterpriseToEbitda", 0) or 0)
    debt_eq = dyn.get("debt_equity") or ((info.get("debtToEquity", 0) or 0) / 100)
    fcf_yield = dyn.get("fcf_yield") or ((info.get("freeCashflow", 0) or 0) / max(info.get("marketCap", 1), 1))

    return {
        "symbol": ticker, "price": current,
        "pe": pe,
        "forward_pe": fwd_pe,
        "pb": pb,
        "roe": roe,
        "roa": dyn.get("roa") or ((info.get("returnOnAssets", 0) or 0) * 100),
        "roic": dyn.get("roic") or (roe * 0.7),
        "debt_equity": debt_eq,
        "revenue_growth": rev_growth,
        "earnings_growth": eps_growth,
        "earnings_quarterly_growth": dyn.get("earnings_quarterly_growth") or eps_growth,
        "gross_margin": gross_margin,
        "operating_margin": op_margin,
        "profit_margin": dyn.get("profit_margin") or (info.get("profitMargins", 0) or 0),
        "ev_ebitda": ev_ebitda,
        "market_cap_b": dyn.get("market_cap_b") or ((info.get("marketCap", 0) or 0) / 1e9),
        "fcf_yield": fcf_yield,
        "peg": dyn.get("peg") or (info.get("pegRatio", 0) or 0),
        "dividend_yield": info.get("dividendYield", 0) or 0,
        "beta": info.get("beta", 1.0) or 1.0,
        "rnd_ratio": 0.10 if info.get("sector") == "Technology" else 0.05,
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "insider_ownership": info.get("heldPercentInsiders", 0) or 0,
        "institutional_ownership": info.get("heldPercentInstitutions", 0) or 0,
        "short_ratio": info.get("shortRatio", 0) or 0,
        "short_pct_float": info.get("shortPercentOfFloat", 0) or 0,
        "analyst_recommendation": info.get("recommendationKey", "none"),
        "analyst_score": info.get("recommendationMean", 3.0) or 3.0,
        "analyst_target_mean": info.get("targetMeanPrice", 0) or 0,
        "analyst_target_high": info.get("targetHighPrice", 0) or 0,
        "analyst_target_low": info.get("targetLowPrice", 0) or 0,
        "analyst_count": info.get("numberOfAnalystOpinions", 0) or 0,
        "upside_to_target": ((info.get("targetMeanPrice", 0) or 0) / current - 1) if current > 0 and (info.get("targetMeanPrice", 0) or 0) > 0 else 0,
        # Technicals (REAL)
        "momentum_3m": m3, "momentum_6m": m6, "momentum_12m": m12,
        "distance_from_52w_high": dist_high,
        "sma_50": sma50, "sma_200": sma200,
        "golden_cross": sma50 > sma200,
        "price_above_sma50": current > sma50,
        "price_above_sma200": current > sma200,
        "rsi": rsi, "macd": macd, "bollinger": bollinger,
        "volatility_30d": vol,
        "price_52w_high": high_52, "price_52w_low": low_52,
        "relative_strength_vs_sp500": rel_strength,
        "market_regime": regime,
        "interest_rate": 0.045, "inflation": 0.028,
    }


def run_backtest(tickers, initial_cash=100000.0, months=18):
    """Run walk-forward backtest on real data."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"  AI HEDGE FUND BACKTEST - REAL HISTORICAL DATA")
    print(f"{'='*80}{Style.RESET_ALL}")
    print(f"  Period:  {months} months")
    print(f"  Cash:    ${initial_cash:,.0f}")
    print(f"  Tickers: {', '.join(tickers)}")
    print(f"  Agents:  {len(AGENTS)}")
    print(f"  Data:    Yahoo Finance (real historical prices)")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    # Fetch real data
    all_hist = fetch_all_history(tickers, "3y")
    spy_hist = all_hist.get("SPY")

    # Dynamic fundamentals engine - computes PE, growth etc. at each point in time
    print(f"  Loading dynamic fundamental data (quarterly earnings)...")
    dyn_fund = DynamicFundamentals()
    info_cache = {}
    for t in tickers:
        if t in all_hist:
            # Pre-fetch to cache
            dyn_fund._fetch_quarterly_data(t)
            info_cache[t] = yf.Ticker(t).info  # Static fallback
            print(f"    {t}: sector={info_cache[t].get('sector', 'N/A')}")
    print(f"  Dynamic fundamentals loaded - PE, growth, margins change each period.")
    print()

    # Find common trading dates (monthly rebalancing)
    # Use first trading day of each month
    reference = all_hist[tickers[0]]
    monthly_dates = reference.resample("MS").first().index
    # Take last N months
    if len(monthly_dates) > months + 1:
        monthly_dates = monthly_dates[-(months + 1):]

    # Map to actual trading day indices
    rebalance_indices = []
    for md in monthly_dates:
        # Find closest trading day
        diffs = abs(reference.index - md)
        idx = diffs.argmin()
        rebalance_indices.append(idx)

    # Initialize portfolio
    portfolio = {
        "cash": initial_cash, "margin_requirement": 0.0, "margin_used": 0.0,
        "positions": {t: {"long": 0, "short": 0, "long_cost_basis": 0.0,
                          "short_cost_basis": 0.0, "short_margin_used": 0.0} for t in tickers},
        "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in tickers},
    }

    # Buy & Hold baseline
    bh_shares = {}
    first_prices = {}
    for t in tickers:
        if t in all_hist:
            p = float(all_hist[t]["Close"].iloc[rebalance_indices[0]])
            first_prices[t] = p
            bh_shares[t] = (initial_cash / len(tickers)) / p

    portfolio_values = []
    bh_values = []
    trade_log = []

    print(f"  {'Date':<12s} {'AI Value':>12s} {'AI Ret':>8s} {'B&H Value':>12s} {'B&H Ret':>8s} {'Alpha':>8s} Trades")
    print(f"  {'-'*85}")

    for i, idx in enumerate(rebalance_indices):
        date_str = reference.index[idx].strftime("%Y-%m-%d")

        # Get current prices
        current_prices = {}
        for t in tickers:
            if t in all_hist and idx < len(all_hist[t]):
                current_prices[t] = float(all_hist[t]["Close"].iloc[idx])

        # Compute AI portfolio value
        ai_val = portfolio["cash"]
        for t in tickers:
            if t in current_prices:
                pos = portfolio["positions"][t]
                ai_val += pos["long"] * current_prices[t]
                ai_val -= pos["short"] * current_prices[t]

        # B&H value
        bh_val = sum(bh_shares.get(t, 0) * current_prices.get(t, 0) for t in tickers)

        portfolio_values.append(ai_val)
        bh_values.append(bh_val)

        ai_ret = (ai_val / initial_cash - 1) * 100
        bh_ret = (bh_val / initial_cash - 1) * 100
        alpha = ai_ret - bh_ret

        # Skip first period (just recording initial values)
        if i == 0:
            ai_ret_str = f"{'---':>7s}"
            bh_ret_str = f"{'---':>7s}"
            alpha_str = f"{'---':>7s}"
            print(f"  {date_str:<12s} ${ai_val:>10,.0f} {ai_ret_str} ${bh_val:>10,.0f} {bh_ret_str} {alpha_str} (start)")
            continue

        # Compute metrics for each stock
        stock_metrics = {}
        valid_tickers = []
        for t in tickers:
            if t in all_hist:
                metrics = compute_metrics_at_date(t, all_hist[t], spy_hist, idx, info_cache, dyn_fund)
                if metrics:
                    stock_metrics[t] = metrics
                    valid_tickers.append(t)

        if not valid_tickers:
            continue

        # Run agents
        analyst_signals = {}
        for agent_id, (_, func) in AGENTS.items():
            signals = {}
            for t in valid_tickers:
                signals[t] = func(t, stock_metrics[t])
            analyst_signals[agent_id] = signals

        # Risk management
        risk = run_risk_management(valid_tickers, portfolio, current_prices)
        analyst_signals["risk_management_agent"] = risk

        # Committee decision
        decisions, _ = run_investment_committee(valid_tickers, analyst_signals, risk, portfolio, stock_data=stock_metrics)

        # Execute trades
        period_trades = []
        for t in valid_tickers:
            dec = decisions[t]
            price = current_prices[t]
            qty = dec["quantity"]

            if dec["action"] == "buy" and qty > 0:
                cost = qty * price
                if cost <= portfolio["cash"]:
                    old = portfolio["positions"][t]["long"]
                    old_basis = portfolio["positions"][t]["long_cost_basis"]
                    new_total = old + qty
                    if new_total > 0:
                        portfolio["positions"][t]["long_cost_basis"] = (old_basis * old + cost) / new_total
                    portfolio["positions"][t]["long"] += qty
                    portfolio["cash"] -= cost
                    period_trades.append(f"BUY {qty} {t}")

            elif dec["action"] == "sell" and qty > 0:
                qty = min(qty, portfolio["positions"][t]["long"])
                if qty > 0:
                    basis = portfolio["positions"][t]["long_cost_basis"]
                    gain = (price - basis) * qty
                    portfolio["realized_gains"][t]["long"] += gain
                    portfolio["positions"][t]["long"] -= qty
                    portfolio["cash"] += qty * price
                    if portfolio["positions"][t]["long"] == 0:
                        portfolio["positions"][t]["long_cost_basis"] = 0
                    period_trades.append(f"SELL {qty} {t}")

            elif dec["action"] == "short" and qty > 0:
                portfolio["positions"][t]["short"] += qty
                portfolio["positions"][t]["short_cost_basis"] = price
                portfolio["cash"] += qty * price
                period_trades.append(f"SHORT {qty} {t}")

        # Recalculate after trades
        ai_val = portfolio["cash"]
        for t in tickers:
            if t in current_prices:
                pos = portfolio["positions"][t]
                ai_val += pos["long"] * current_prices[t]
                ai_val -= pos["short"] * current_prices[t]
        portfolio_values[-1] = ai_val
        ai_ret = (ai_val / initial_cash - 1) * 100

        ac = Fore.GREEN if alpha > 0 else Fore.RED
        arc = Fore.GREEN if ai_ret > 0 else Fore.RED
        trades_str = ", ".join(period_trades[:3]) if period_trades else "Hold"
        if len(period_trades) > 3:
            trades_str += f" +{len(period_trades)-3} more"

        print(f"  {date_str:<12s} ${ai_val:>10,.0f} {arc}{ai_ret:>+7.1f}%{Style.RESET_ALL} ${bh_val:>10,.0f} {bh_ret:>+7.1f}% {ac}{alpha:>+7.1f}%{Style.RESET_ALL} {trades_str}")
        trade_log.extend(period_trades)

    # === FINAL RESULTS ===
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"  BACKTEST RESULTS - REAL DATA")
    print(f"{'='*80}{Style.RESET_ALL}")

    final_ai = portfolio_values[-1]
    final_bh = bh_values[-1]
    ai_total = (final_ai / initial_cash - 1) * 100
    bh_total = (final_bh / initial_cash - 1) * 100
    alpha_total = ai_total - bh_total

    # Risk metrics
    ai_returns = np.array([(portfolio_values[i] / portfolio_values[i-1] - 1) for i in range(1, len(portfolio_values))])
    bh_returns = np.array([(bh_values[i] / bh_values[i-1] - 1) for i in range(1, len(bh_values))])

    ai_sharpe = (np.mean(ai_returns) * 12) / (np.std(ai_returns) * np.sqrt(12)) if np.std(ai_returns) > 0 else 0
    bh_sharpe = (np.mean(bh_returns) * 12) / (np.std(bh_returns) * np.sqrt(12)) if np.std(bh_returns) > 0 else 0

    ai_dd = max((np.maximum.accumulate(portfolio_values) - portfolio_values) / np.maximum.accumulate(portfolio_values))
    bh_dd = max((np.maximum.accumulate(bh_values) - bh_values) / np.maximum.accumulate(bh_values))

    ai_win = sum(1 for r in ai_returns if r > 0) / len(ai_returns) * 100

    ai_down = ai_returns[ai_returns < 0]
    ai_sortino = (np.mean(ai_returns) * 12) / (np.std(ai_down) * np.sqrt(12)) if len(ai_down) > 0 and np.std(ai_down) > 0 else 0

    aic = Fore.GREEN if ai_total > 0 else Fore.RED
    bhc = Fore.GREEN if bh_total > 0 else Fore.RED
    alc = Fore.GREEN if alpha_total > 0 else Fore.RED

    print(f"\n  {'Metric':<25s} {'AI Committee':>15s} {'Buy & Hold':>15s}")
    print(f"  {'-'*58}")
    print(f"  {'Total Return':<25s} {aic}{ai_total:>+14.2f}%{Style.RESET_ALL} {bhc}{bh_total:>+14.2f}%{Style.RESET_ALL}")
    print(f"  {'Alpha':<25s} {alc}{alpha_total:>+14.2f}%{Style.RESET_ALL}")
    print(f"  {'Sharpe Ratio':<25s} {ai_sharpe:>15.2f} {bh_sharpe:>15.2f}")
    print(f"  {'Sortino Ratio':<25s} {ai_sortino:>15.2f}")
    print(f"  {'Max Drawdown':<25s} {Fore.RED}{ai_dd*100:>14.2f}%{Style.RESET_ALL} {Fore.RED}{bh_dd*100:>14.2f}%{Style.RESET_ALL}")
    print(f"  {'Win Rate (months)':<25s} {ai_win:>14.0f}%")
    print(f"  {'Total Trades':<25s} {len(trade_log):>15d}")

    # Final positions
    print(f"\n  {Style.BRIGHT}FINAL POSITIONS:{Style.RESET_ALL}")
    for t in tickers:
        pos = portfolio["positions"][t]
        if pos["long"] > 0:
            p = current_prices.get(t, 0)
            v = pos["long"] * p
            g = (p / pos["long_cost_basis"] - 1) * 100 if pos["long_cost_basis"] > 0 else 0
            gc = Fore.GREEN if g > 0 else Fore.RED
            print(f"    {t}: LONG {pos['long']} @ ${p:.2f} = ${v:,.0f} ({gc}{g:+.1f}%{Style.RESET_ALL})")
        if pos["short"] > 0:
            p = current_prices.get(t, 0)
            v = pos["short"] * p
            print(f"    {t}: SHORT {pos['short']} @ ${p:.2f} = ${v:,.0f}")
    print(f"    Cash: ${portfolio['cash']:,.0f}")

    # Stock performance
    print(f"\n  {Style.BRIGHT}STOCK PERFORMANCE:{Style.RESET_ALL}")
    for t in tickers:
        if t in current_prices and t in first_prices:
            chg = (current_prices[t] / first_prices[t] - 1) * 100
            c = Fore.GREEN if chg > 0 else Fore.RED
            print(f"    {t}: ${first_prices[t]:.2f} -> ${current_prices[t]:.2f} ({c}{chg:+.1f}%{Style.RESET_ALL})")

    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

    if alpha_total > 0:
        print(f"\n  {Fore.GREEN}{Style.BRIGHT}AI HEDGE FUND BEAT BUY & HOLD by {alpha_total:+.2f}%{Style.RESET_ALL}")
    else:
        print(f"\n  {Fore.RED}{Style.BRIGHT}Buy & Hold won by {abs(alpha_total):.2f}%{Style.RESET_ALL}")
        if ai_dd < bh_dd:
            print(f"  {Fore.GREEN}But AI had better risk management (DD: {ai_dd*100:.1f}% vs {bh_dd*100:.1f}%){Style.RESET_ALL}")
    print()


def main():
    parser = argparse.ArgumentParser(description="AI Hedge Fund - Real Data Backtest")
    parser.add_argument("--tickers", type=str, default="AAPL,NVDA,MSFT,TSLA,GOOG,AMZN,META")
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--months", type=int, default=18, help="Months to backtest (default: 18)")
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    run_backtest(tickers, args.initial_cash, args.months)


if __name__ == "__main__":
    main()
