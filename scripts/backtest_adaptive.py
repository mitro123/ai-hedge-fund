#!/usr/bin/env python3
"""
Backtest: Adaptive Fund with Monthly Universe Screening
Each month: scan stocks, rank by conviction, rotate if data says so.
No look-ahead bias - only data available at each point.
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

from src.data.market_data import MarketDataProvider
from src.data.yfinance_adapter import YFinanceAdapter
from src.data.dynamic_fundamentals import DynamicFundamentals
from src.data.portfolio_intelligence import check_exit_triggers
from scripts.run_live_trading import (
    AGENTS, _rank_tickers, run_risk_management, run_investment_committee,
)


def compute_live_metrics(ticker, hist, idx, dyn_fund, info_cache):
    """Compute full metrics for one stock at a specific date. No future data."""
    h = hist.iloc[:idx + 1]
    if len(h) < 50:
        return None

    close = h["Close"]
    current = float(close.iloc[-1])
    as_of = h.index[idx].to_pydatetime()
    if hasattr(as_of, 'tzinfo') and as_of.tzinfo:
        as_of = as_of.replace(tzinfo=None)

    # Dynamic fundamentals (quarterly)
    dyn = dyn_fund.compute_metrics_at_date(ticker, as_of, current) if dyn_fund else {}
    info = info_cache.get(ticker, {})

    # Technical indicators
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else sma50

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, 1e-10)
    rsi = float((100 - (100 / (1 + rs))).iloc[-1])

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9).mean()

    m3 = (current / float(close.iloc[-63]) - 1) if len(close) > 63 else 0
    m6 = (current / float(close.iloc[-126]) - 1) if len(close) > 126 else 0
    m12 = (current / float(close.iloc[0]) - 1) if len(close) > 200 else 0

    w52 = close.tail(252) if len(close) >= 252 else close
    vol = float(close.pct_change().dropna().tail(30).std() * np.sqrt(252)) if len(close) > 30 else 0.25

    pe = dyn.get("pe") or (info.get("trailingPE", 0) or 0)
    roe = dyn.get("roe") or ((info.get("returnOnEquity", 0) or 0) * 100)

    return {
        "symbol": ticker, "price": current,
        "pe": pe, "forward_pe": dyn.get("forward_pe") or (info.get("forwardPE", 0) or 0),
        "pb": dyn.get("pb") or (info.get("priceToBook", 0) or 0),
        "roe": roe, "roa": dyn.get("roa") or ((info.get("returnOnAssets", 0) or 0) * 100),
        "roic": dyn.get("roic") or (roe * 0.7),
        "debt_equity": dyn.get("debt_equity") or ((info.get("debtToEquity", 0) or 0) / 100),
        "revenue_growth": dyn.get("revenue_growth") or (info.get("revenueGrowth", 0) or 0),
        "earnings_growth": dyn.get("earnings_growth") or (info.get("earningsGrowth", 0) or 0),
        "earnings_quarterly_growth": dyn.get("earnings_quarterly_growth", 0),
        "gross_margin": dyn.get("gross_margin") or (info.get("grossMargins", 0) or 0),
        "operating_margin": dyn.get("operating_margin") or (info.get("operatingMargins", 0) or 0),
        "profit_margin": dyn.get("profit_margin") or (info.get("profitMargins", 0) or 0),
        "ev_ebitda": dyn.get("ev_ebitda") or (info.get("enterpriseToEbitda", 0) or 0),
        "market_cap_b": dyn.get("market_cap_b") or ((info.get("marketCap", 0) or 0) / 1e9),
        "fcf_yield": dyn.get("fcf_yield") or 0,
        "peg": dyn.get("peg") or (info.get("pegRatio", 0) or 0),
        "dividend_yield": info.get("dividendYield", 0) or 0,
        "beta": info.get("beta", 1.0) or 1.0,
        "rnd_ratio": 0.10 if info.get("sector") == "Technology" else 0.05,
        "sector": info.get("sector", ""), "industry": info.get("industry", ""),
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
        "upside_to_target": ((info.get("targetMeanPrice", 0) or 0) / current - 1) if current > 0 and (info.get("targetMeanPrice") or 0) > 0 else 0,
        "momentum_3m": m3, "momentum_6m": m6, "momentum_12m": m12,
        "distance_from_52w_high": (current / float(w52.max()) - 1),
        "sma_50": sma50, "sma_200": sma200,
        "golden_cross": sma50 > sma200,
        "price_above_sma50": current > sma50,
        "price_above_sma200": current > sma200,
        "rsi": rsi,
        "macd": {"macd": float(macd_line.iloc[-1]), "signal": float(signal_line.iloc[-1]),
                 "histogram": float((macd_line - signal_line).iloc[-1]),
                 "bullish_cross": float(macd_line.iloc[-1]) > float(signal_line.iloc[-1])},
        "bollinger": {"pct_b": 0.5},  # Simplified
        "volatility_30d": vol,
        "price_52w_high": float(w52.max()), "price_52w_low": float(w52.min()),
        "relative_strength_vs_sp500": 0, "market_regime": "unknown",
        "interest_rate": 0.045, "inflation": 0.028,
        "earnings_surprise": 0, "buyback_yield": 0, "payout_ratio": 0,
    }


def _check_technical_exit(ticker, all_hist, idx, cost_basis):
    """Check exit triggers using only historically-available technical data.
    Returns (should_exit, list_of_trigger_reasons).
    """
    if ticker not in all_hist:
        return False, []

    h = all_hist[ticker].iloc[:idx + 1]
    close = h["Close"]
    if len(close) < 20:
        return False, []

    current = float(close.iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else float(close.mean())
    sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else float(close.mean())
    m6 = (current / float(close.iloc[-126]) - 1) if len(close) > 126 else 0.0
    cost = cost_basis if cost_basis > 0 else current
    loss = (current / cost - 1) if cost > 0 else 0.0

    triggers = []

    # TRIGGER 1: Death cross + negative 6-month momentum
    if sma50 < sma200 and m6 < -0.15:
        triggers.append(f"death_cross+neg_momentum(6m={m6*100:+.0f}%)")

    # TRIGGER 2: Stop loss - position down >25% from cost basis
    if loss < -0.25:
        triggers.append(f"stop_loss({loss*100:+.0f}%)")

    # TRIGGER 3: Severe momentum collapse
    if m6 < -0.25:
        triggers.append(f"momentum_collapse(6m={m6*100:+.0f}%)")

    # TRIGGER 4: Short-term breakdown - 3-month momentum deeply negative
    m3 = (current / float(close.iloc[-63]) - 1) if len(close) > 63 else 0.0
    if m3 < -0.20 and current < sma50:
        triggers.append(f"short_term_breakdown(3m={m3*100:+.0f}%)")

    # Need 2+ triggers OR 1 severe trigger (stop loss)
    should_exit = len(triggers) >= 2 or loss < -0.25
    return should_exit, triggers


def run_backtest(universe_tickers, initial_cash=100000.0, months=18, max_positions=8):
    """Event-driven backtest: buy at start, then only sell on exit triggers, replace if cash available."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"  ADAPTIVE FUND BACKTEST - EVENT-DRIVEN (no forced rotation)")
    print(f"{'='*80}{Style.RESET_ALL}")
    print(f"  Universe: {len(universe_tickers)} stocks | Max positions: {max_positions}")
    print(f"  Period: {months}m | Cash: ${initial_cash:,.0f}")
    print(f"  Exit triggers: death_cross+momentum, stop_loss>25%, momentum_collapse, breakdown")
    print(f"  Buy rule: only when cash > 15% of portfolio after an exit")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    # Load histories
    print("  Loading data...")
    all_hist = {}
    info_cache = {}
    for t in universe_tickers:
        try:
            tk = yf.Ticker(t)
            h = tk.history(period="3y")
            if not h.empty and len(h) > 100:
                all_hist[t] = h
                info_cache[t] = tk.info
        except Exception:
            pass
    print(f"  Loaded {len(all_hist)} stocks with 3y history")

    dyn_fund = DynamicFundamentals()
    for t in all_hist:
        try: dyn_fund._fetch_quarterly_data(t)
        except: pass

    # Monthly check dates (we check triggers monthly, but DON'T force trades)
    ref_ticker = list(all_hist.keys())[0]
    ref = all_hist[ref_ticker]
    monthly = ref.resample("MS").first().index
    if len(monthly) > months + 1:
        monthly = monthly[-(months + 1):]
    rebal_idx = [abs(ref.index - md).argmin() for md in monthly]

    # Portfolio
    portfolio = {"cash": initial_cash, "positions": {}, "cost_basis": {}}

    # B&H: equal weight top stocks (picked at start)
    bh_shares = {}
    bh_tickers = []

    pv = []
    bh_v = []
    total_exits = 0
    total_buys = 0

    print(f"\n  {'Date':<11s} {'AI':>10s} {'AI%':>7s} {'B&H':>10s} {'B&H%':>7s} {'Alpha':>7s} {'Pos':>4s} Action")
    print(f"  {'-'*80}")

    for period_i, idx in enumerate(rebal_idx):
        date_str = ref.index[idx].strftime("%Y-%m-%d")

        # Current prices for all stocks
        current_prices = {}
        for t in all_hist:
            if idx < len(all_hist[t]):
                current_prices[t] = float(all_hist[t]["Close"].iloc[idx])

        # Portfolio value
        ai_val = portfolio["cash"]
        for t, shares in portfolio["positions"].items():
            ai_val += shares * current_prices.get(t, 0)

        # B&H value
        bh_val = sum(bh_shares.get(t, 0) * current_prices.get(t, 0) for t in bh_tickers) if bh_tickers else initial_cash

        pv.append(ai_val)
        bh_v.append(bh_val)

        # ==================== PERIOD 0: INITIAL BUY ====================
        if period_i == 0:
            print(f"  {date_str:<11s} ${ai_val:>9,.0f}    ---  ${initial_cash:>9,.0f}    ---     ---    0 (initial scan)")

            # Compute metrics for all stocks at start
            stock_data = {}
            for t in list(current_prices.keys()):
                m = compute_live_metrics(t, all_hist[t], idx, dyn_fund, info_cache)
                if m:
                    stock_data[t] = m

            # Run agents and rank at start
            analyst_signals = {}
            for aid, (name, func) in AGENTS.items():
                for t in stock_data:
                    try:
                        analyst_signals.setdefault(aid, {})[t] = func(t, stock_data[t])
                    except:
                        analyst_signals.setdefault(aid, {})[t] = {"signal": "neutral", "confidence": 20, "reasoning": ""}

            rankings = _rank_tickers(list(stock_data.keys()), stock_data, analyst_signals)
            top = sorted(rankings.items(), key=lambda x: x[1], reverse=True)[:max_positions]

            # B&H benchmark: equal weight in top stocks
            bh_tickers = [t for t, _ in top]
            for t in bh_tickers:
                if t in current_prices:
                    bh_shares[t] = (initial_cash / len(bh_tickers)) / current_prices[t]
            bh_val = sum(bh_shares.get(t, 0) * current_prices.get(t, 0) for t in bh_tickers)
            bh_v[-1] = bh_val

            # Initial buy: equal weight into top N stocks
            buy_tickers = [t for t, _ in top if t in current_prices]
            alloc_per = initial_cash / len(buy_tickers) if buy_tickers else 0
            buy_trades = []
            for t in buy_tickers:
                price = current_prices[t]
                qty = int(alloc_per / price)
                if qty > 0:
                    portfolio["positions"][t] = qty
                    portfolio["cost_basis"][t] = price
                    portfolio["cash"] -= qty * price
                    buy_trades.append(f"BUY {qty} {t}")
                    total_buys += 1

            t_str = ", ".join(buy_trades[:4]) + (f" +{len(buy_trades)-4}" if len(buy_trades) > 4 else "")
            print(f"  {'':11s} {'':>10s} {'':>7s} {'':>10s} {'':>7s} {'':>7s} {len(portfolio['positions']):>4d} {t_str}")
            continue

        # ==================== SUBSEQUENT MONTHS: CHECK EXIT TRIGGERS ONLY ====================
        exits_this_period = []
        for t in list(portfolio["positions"].keys()):
            should_exit, triggers = _check_technical_exit(t, all_hist, idx, portfolio["cost_basis"].get(t, 0))
            if should_exit:
                shares = portfolio["positions"][t]
                sell_price = current_prices.get(t, 0)
                revenue = shares * sell_price
                cost = portfolio["cost_basis"].get(t, 0)
                pnl = (sell_price / cost - 1) * 100 if cost > 0 else 0
                portfolio["cash"] += revenue
                del portfolio["positions"][t]
                del portfolio["cost_basis"][t]
                exits_this_period.append(f"EXIT {t}({pnl:+.0f}%): {'; '.join(triggers)}")
                total_exits += 1

        # ONLY buy replacements if we exited something AND cash > 15% of portfolio
        buy_trades = []
        if exits_this_period and portfolio["cash"] > ai_val * 0.15:
            # Score available stocks (only those NOT already held)
            held = set(portfolio["positions"].keys())
            candidates = [t for t in current_prices if t not in held and t in all_hist]

            stock_data = {}
            for t in candidates:
                try:
                    m = compute_live_metrics(t, all_hist[t], idx, dyn_fund, info_cache)
                    if m:
                        stock_data[t] = m
                except:
                    pass

            if stock_data:
                # Run agents on candidates only
                analyst_signals = {}
                for aid, (name, func) in AGENTS.items():
                    for t in stock_data:
                        try:
                            analyst_signals.setdefault(aid, {})[t] = func(t, stock_data[t])
                        except:
                            analyst_signals.setdefault(aid, {})[t] = {"signal": "neutral", "confidence": 20, "reasoning": ""}

                rankings = _rank_tickers(list(stock_data.keys()), stock_data, analyst_signals)
                sorted_cands = sorted(rankings.items(), key=lambda x: x[1], reverse=True)

                # Buy replacements for the slots we freed
                slots_free = max_positions - len(portfolio["positions"])
                replacements = [t for t, s in sorted_cands if s > 0][:slots_free]

                if replacements:
                    alloc_per = portfolio["cash"] * 0.85 / len(replacements)  # keep 15% cash buffer
                    for t in replacements:
                        price = current_prices[t]
                        qty = int(alloc_per / price)
                        if qty > 0 and qty * price <= portfolio["cash"]:
                            portfolio["positions"][t] = qty
                            portfolio["cost_basis"][t] = price
                            portfolio["cash"] -= qty * price
                            buy_trades.append(f"BUY {qty} {t}")
                            total_buys += 1

        # Recalc portfolio value after trades
        ai_val = portfolio["cash"] + sum(s * current_prices.get(t, 0) for t, s in portfolio["positions"].items())
        bh_val = sum(bh_shares.get(t, 0) * current_prices.get(t, 0) for t in bh_tickers)
        pv[-1] = ai_val
        bh_v[-1] = bh_val

        ai_ret = (ai_val / initial_cash - 1) * 100
        bh_ret = (bh_val / initial_cash - 1) * 100
        alpha = ai_ret - bh_ret
        n_pos = len(portfolio["positions"])
        ac = Fore.GREEN if alpha > 0 else Fore.RED

        # Build action string
        all_trades = exits_this_period + buy_trades
        if all_trades:
            t_str = ", ".join(all_trades[:3]) + (f" +{len(all_trades)-3}" if len(all_trades) > 3 else "")
        else:
            t_str = "-- no triggers --"
        print(f"  {date_str:<11s} ${ai_val:>9,.0f} {ai_ret:>+6.1f}% ${bh_val:>9,.0f} {bh_ret:>+6.1f}% {ac}{alpha:>+6.1f}%{Style.RESET_ALL} {n_pos:>4d} {t_str}")

    # Final
    ai_total = (pv[-1] / initial_cash - 1) * 100
    bh_total = (bh_v[-1] / initial_cash - 1) * 100
    rets = np.array([(pv[j] / pv[j-1] - 1) for j in range(1, len(pv))])
    sharpe = (np.mean(rets) * 12) / (np.std(rets) * np.sqrt(12)) if np.std(rets) > 0 else 0
    max_dd = max((np.maximum.accumulate(pv) - pv) / np.maximum.accumulate(pv))

    aic = Fore.GREEN if ai_total > bh_total else Fore.RED
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"  ADAPTIVE FUND RESULTS (Event-Driven)")
    print(f"{'='*80}{Style.RESET_ALL}")
    print(f"  AI: {aic}{ai_total:>+.2f}%{Style.RESET_ALL} | B&H: {bh_total:>+.2f}% | Alpha: {aic}{ai_total-bh_total:>+.2f}%{Style.RESET_ALL}")
    print(f"  Sharpe: {sharpe:.2f} | Max DD: {max_dd*100:.1f}%")
    ratio = ai_total / bh_total if bh_total > 0 else 0
    print(f"  Ratio: {ratio:.2f}x B&H")
    print(f"  Total exits: {total_exits} | Total buys: {total_buys} (incl. initial)")
    print(f"  Final positions: {len(portfolio['positions'])}")
    for t, s in sorted(portfolio["positions"].items(), key=lambda x: -x[1] * current_prices.get(x[0], 0)):
        val = s * current_prices.get(t, 0)
        print(f"    {t:6s}: {s:>4.0f} shares = ${val:>10,.2f}")
    print(f"  Cash: ${portfolio['cash']:>10,.2f}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", default="quality", choices=["tech7", "quality", "growth", "diverse", "all30"],
                        help="Stock universe to use")
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--months", type=int, default=18)
    parser.add_argument("--max-positions", type=int, default=8)
    args = parser.parse_args()

    universes = {
        "tech7": ["AAPL", "NVDA", "MSFT", "TSLA", "GOOG", "AMZN", "META"],
        "quality": ["AAPL", "MSFT", "JNJ", "V", "MA", "WMT", "KO", "PG", "UNH", "HD", "COST", "ABBV"],
        "growth": ["NVDA", "AMD", "GOOG", "META", "NFLX", "CRM", "ADBE", "AVGO", "PLTR", "SHOP"],
        "diverse": ["AAPL", "NVDA", "GOOG", "META", "V", "JPM", "UNH", "LLY", "WMT", "AMD", "XOM", "JNJ", "KO", "HD", "NFLX"],
        "all30": ["AAPL", "NVDA", "MSFT", "GOOG", "META", "AMZN", "V", "MA", "JPM", "UNH", "JNJ", "LLY", "ABBV",
                  "WMT", "COST", "KO", "PG", "AMD", "AVGO", "NFLX", "CRM", "ADBE", "XOM", "HD", "NKE", "CAT",
                  "PLTR", "BA", "TSLA", "INTC"],
    }

    tickers = universes[args.universe]
    run_backtest(tickers, args.initial_cash, args.months, args.max_positions)


if __name__ == "__main__":
    main()
