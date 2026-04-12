#!/usr/bin/env python3
"""
AI Hedge Fund - Backtest with FULL Financial Datasets API + Original Agents
Uses real API data for fundamentals, yfinance for technicals and real-time.
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load API key
from dotenv import load_dotenv
load_dotenv()

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

from src.tools.api import get_financial_metrics, search_line_items, get_market_cap, get_prices, prices_to_df
from src.agents.warren_buffett import (
    analyze_fundamentals, analyze_consistency, analyze_moat,
    analyze_management_quality, calculate_intrinsic_value,
)
from src.agents.michael_burry import _analyze_value, _analyze_balance_sheet
from src.agents.stanley_druckenmiller import analyze_growth_and_momentum, analyze_druckenmiller_valuation
from src.agents.cathie_wood import analyze_disruptive_potential, analyze_innovation_growth, analyze_cathie_wood_valuation
from src.agents.ben_graham import analyze_financial_strength, analyze_earnings_stability, analyze_valuation_graham
from src.agents.peter_lynch import analyze_lynch_growth, analyze_lynch_fundamentals, analyze_lynch_valuation
from src.agents.phil_fisher import analyze_fisher_growth_quality, analyze_margins_stability, analyze_management_efficiency_leverage, analyze_fisher_valuation
from src.agents.bill_ackman import analyze_business_quality, analyze_financial_discipline, analyze_activism_potential, analyze_valuation as ackman_valuation
from src.agents.charlie_munger import analyze_moat_strength, analyze_management_quality as munger_mgmt, analyze_predictability, calculate_munger_valuation
from src.agents.technicals import (
    calculate_trend_signals, calculate_mean_reversion_signals,
    calculate_momentum_signals, calculate_volatility_signals,
    calculate_stat_arb_signals, weighted_signal_combination,
)

from scripts.run_live_trading import (
    run_risk_management, run_investment_committee,
    sentiment_analyst_analyze, valuation_analyst_analyze,
    stanley_druckenmiller_analyze, cathie_wood_analyze,
    rakesh_jhunjhunwala_analyze, aswath_damodaran_analyze,
)
from src.data.market_data import MarketDataProvider

LINE_FIELDS = [
    'capital_expenditure', 'depreciation_and_amortization', 'net_income',
    'outstanding_shares', 'total_assets', 'total_liabilities',
    'shareholders_equity', 'dividends_and_other_cash_distributions',
    'issuance_or_purchase_of_equity_shares', 'gross_profit', 'revenue',
    'free_cash_flow', 'operating_income', 'cash_and_equivalents',
    'total_debt', 'research_and_development', 'ebit', 'ebitda',
    'earnings_per_share', 'operating_expense',
]


def score_to_signal(score, max_score, bull_thresh=0.6, bear_thresh=0.3):
    """Convert a numeric score to bullish/bearish/neutral signal."""
    pct = score / max_score if max_score > 0 else 0
    signal = "bullish" if pct >= bull_thresh else ("bearish" if pct <= bear_thresh else "neutral")
    conf = min(95, max(20, pct * 100))
    return signal, round(conf, 1)


def run_original_agent_suite(ticker, end_date, prices_df, live_data):
    """
    Run ALL original agents for one ticker using Financial Datasets API.
    Returns dict of agent_id -> {signal, confidence, reasoning}.
    """
    api_key = os.environ.get("FINANCIAL_DATASETS_API_KEY")
    signals = {}

    try:
        metrics = get_financial_metrics(ticker, end_date, period='ttm', limit=10, api_key=api_key)
        items = search_line_items(ticker, LINE_FIELDS, end_date, period='ttm', limit=10, api_key=api_key)
        mc = get_market_cap(ticker, end_date, api_key=api_key)
    except Exception as e:
        # Fallback: return live_data based signals for all
        return None

    # 1. WARREN BUFFETT (original 7-module scoring)
    try:
        b_fund = analyze_fundamentals(metrics)['score']
        b_moat = analyze_moat(metrics)
        b_cons = analyze_consistency(items)['score']
        b_mgmt = analyze_management_quality(items)['score']
        total = b_fund + b_moat['score'] + b_cons + b_mgmt
        max_s = 7 + b_moat['max_score'] + 3 + b_mgmt.get('max_score', 2) if isinstance(b_mgmt, dict) else 17
        sig, conf = score_to_signal(total, 17)

        # Margin of safety adjustment
        iv = calculate_intrinsic_value(items)
        if iv.get('intrinsic_value') and mc:
            mos = (iv['intrinsic_value'] - mc) / mc
            if mos > 0.20: conf = min(95, conf + 15)
            elif mos < -0.50: conf = max(20, conf - 10)

        signals["warren_buffett_agent"] = {"signal": sig, "confidence": conf,
            "reasoning": f"Buffett {total}/17. Fund={b_fund}/7 Moat={b_moat['score']}/{b_moat['max_score']} Cons={b_cons}/3"}
    except Exception:
        pass

    # 2. TECHNICAL ANALYST (original 5-strategy)
    try:
        if prices_df is not None and len(prices_df) > 55:
            c = weighted_signal_combination(
                {'trend': calculate_trend_signals(prices_df),
                 'mean_reversion': calculate_mean_reversion_signals(prices_df),
                 'momentum': calculate_momentum_signals(prices_df),
                 'volatility': calculate_volatility_signals(prices_df),
                 'stat_arb': calculate_stat_arb_signals(prices_df)},
                {'trend': 0.25, 'mean_reversion': 0.20, 'momentum': 0.25, 'volatility': 0.15, 'stat_arb': 0.15})
            signals["technical_analyst_agent"] = {"signal": c["signal"],
                "confidence": round(max(20, c["confidence"] * 100), 1), "reasoning": "5-strategy technical ensemble"}
    except Exception:
        pass

    # 3. MICHAEL BURRY (FCF yield + balance sheet)
    try:
        bu_v = _analyze_value(metrics, items, mc)
        bu_b = _analyze_balance_sheet(metrics, items)
        total = bu_v['score'] + bu_b['score']
        max_s = bu_v['max_score'] + bu_b['max_score']
        sig, conf = score_to_signal(total, max_s, 0.7, 0.3)
        signals["michael_burry_agent"] = {"signal": sig, "confidence": conf,
            "reasoning": f"Burry {total}/{max_s}. {bu_v['details'][:50]}"}
    except Exception:
        pass

    # 4. PETER LYNCH (PEG + growth + fundamentals)
    try:
        lg = analyze_lynch_growth(items)
        lf = analyze_lynch_fundamentals(items)
        lv = analyze_lynch_valuation(items, mc)
        score = lg['score']*0.30 + lf['score']*0.20 + lv['score']*0.25
        sig, conf = score_to_signal(score, 7.5, 0.65, 0.30)
        signals["peter_lynch_agent"] = {"signal": sig, "confidence": conf,
            "reasoning": f"Lynch {score:.1f}/7.5. Growth={lg['score']:.0f} Funds={lf['score']:.0f} Val={lv['score']:.0f}"}
    except Exception:
        pass

    # 5. PHIL FISHER (R&D + margins + management)
    try:
        fg = analyze_fisher_growth_quality(items)
        fm = analyze_margins_stability(items)
        fmg = analyze_management_efficiency_leverage(items)
        fv = analyze_fisher_valuation(items, mc)
        score = fg['score']*0.30 + fm['score']*0.25 + fmg['score']*0.20 + fv['score']*0.15
        sig, conf = score_to_signal(score, 9.0, 0.65, 0.30)
        signals["phil_fisher_agent"] = {"signal": sig, "confidence": conf,
            "reasoning": f"Fisher {score:.1f}/9.0. Growth={fg['score']:.0f} Margins={fm['score']:.0f}"}
    except Exception:
        pass

    # 6. BILL ACKMAN (quality + DCF + activism)
    try:
        aq = analyze_business_quality(metrics, items)
        ad = analyze_financial_discipline(metrics, items)
        aa = analyze_activism_potential(items)
        av = ackman_valuation(items, mc)
        total = aq['score'] + ad['score'] + aa['score'] + av['score']
        sig, conf = score_to_signal(total, 16, 0.7, 0.3)
        signals["bill_ackman_agent"] = {"signal": sig, "confidence": conf,
            "reasoning": f"Ackman {total}/16. Quality={aq['score']} DCF={av['score']}"}
    except Exception:
        pass

    # 7. CHARLIE MUNGER (moat + management + predictability + valuation)
    try:
        moat = analyze_moat_strength(metrics, items)
        mgmt = munger_mgmt(items, [])
        pred = analyze_predictability(items)
        val = calculate_munger_valuation(items, mc)
        score = moat['score']*0.35 + mgmt['score']*0.25 + pred['score']*0.25 + val['score']*0.15
        sig, conf = score_to_signal(score, 10, 0.75, 0.45)
        signals["charlie_munger_agent"] = {"signal": sig, "confidence": conf,
            "reasoning": f"Munger {score:.1f}/10. Moat={moat['score']:.0f} Pred={pred['score']:.0f} Val={val['score']:.0f}"}
    except Exception:
        pass

    # 8. BEN GRAHAM (financial strength + stability + valuation)
    try:
        gs = analyze_financial_strength(items)
        ge = analyze_earnings_stability(metrics, items)
        gv = analyze_valuation_graham(items, mc)
        total = gs['score'] + ge['score'] + gv['score']
        sig, conf = score_to_signal(total, 15, 0.7, 0.3)
        signals["ben_graham_agent"] = {"signal": sig, "confidence": conf,
            "reasoning": f"Graham {total}/15. Strength={gs['score']} Stability={ge['score']} Val={gv['score']}"}
    except Exception:
        pass

    # 9. DRUCKENMILLER (growth + valuation from API)
    try:
        prices_raw = get_prices(ticker, (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=90)).strftime('%Y-%m-%d'), end_date, api_key=api_key)
        dg = analyze_growth_and_momentum(items, prices_raw or [])
        dv = analyze_druckenmiller_valuation(items, mc)
        score = dg['score']*0.35 + dv['score']*0.20
        sig, conf = score_to_signal(score, 5.5, 0.6, 0.3)
        signals["stanley_druckenmiller_agent"] = {"signal": sig, "confidence": conf,
            "reasoning": f"Druck G={dg['score']:.0f}/10 V={dv['score']:.0f}/10"}
    except Exception:
        pass

    # 10. CATHIE WOOD (disruptive + innovation + valuation)
    try:
        cd = analyze_disruptive_potential(metrics, items)
        ci = analyze_innovation_growth(metrics, items)
        cv = analyze_cathie_wood_valuation(items, mc)
        total = cd['score'] + ci['score'] + cv['score']
        sig, conf = score_to_signal(total, 13, 0.7, 0.35)
        signals["cathie_wood_agent"] = {"signal": sig, "confidence": conf,
            "reasoning": f"CathieWood {total:.1f}/13. Disrupt={cd['score']:.1f} Innov={ci['score']:.1f}"}
    except Exception:
        pass

    # 11-15: Rule-based agents using live yfinance data
    if live_data:
        for aid, func in [
            ("fundamentals_analyst_agent", lambda d: valuation_analyst_analyze(ticker, d)),
            ("sentiment_analyst_agent", lambda d: sentiment_analyst_analyze(ticker, d)),
            ("valuation_analyst_agent", lambda d: valuation_analyst_analyze(ticker, d)),
            ("rakesh_jhunjhunwala_agent", lambda d: rakesh_jhunjhunwala_analyze(ticker, d)),
            ("aswath_damodaran_agent", lambda d: aswath_damodaran_analyze(ticker, d)),
        ]:
            try:
                if aid not in signals:
                    signals[aid] = func(live_data)
            except Exception:
                pass

    return signals


def run_backtest(tickers, initial_cash=100000.0, months=18):
    """Walk-forward backtest with original agents + Financial Datasets API."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"  BACKTEST: ORIGINAL AGENTS + FINANCIAL DATASETS API")
    print(f"{'='*80}{Style.RESET_ALL}")
    print(f"  Period: {months} months | Cash: ${initial_cash:,.0f} | Tickers: {', '.join(tickers)}")
    print(f"  Data: Financial Datasets API + Yahoo Finance")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    # Fetch price history from yfinance for technicals
    print("  Loading price history...")
    all_hist = {}
    provider = MarketDataProvider()
    for t in tickers:
        h = yf.Ticker(t).history(period="3y")
        if not h.empty:
            all_hist[t] = h.rename(columns={"Close": "close", "Open": "open", "High": "high", "Low": "low", "Volume": "volume"})
        print(f"    {t}: {len(all_hist.get(t, []))} days")

    spy = yf.Ticker("SPY").history(period="3y")

    # Monthly rebalance dates
    ref = all_hist[tickers[0]]
    monthly = ref.resample("MS").first().index
    if len(monthly) > months + 1:
        monthly = monthly[-(months + 1):]

    rebalance_indices = []
    for md in monthly:
        diffs = abs(ref.index - md)
        rebalance_indices.append(diffs.argmin())

    # Portfolio
    portfolio = {
        "cash": initial_cash, "margin_requirement": 0.0, "margin_used": 0.0,
        "positions": {t: {"long": 0, "short": 0, "long_cost_basis": 0.0,
                          "short_cost_basis": 0.0, "short_margin_used": 0.0} for t in tickers},
        "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in tickers},
    }

    # B&H
    bh_shares = {}
    first_prices = {}
    for t in tickers:
        if t in all_hist:
            p = float(all_hist[t]["close"].iloc[rebalance_indices[0]])
            first_prices[t] = p
            bh_shares[t] = (initial_cash / len(tickers)) / p

    portfolio_values = []
    bh_values = []

    print(f"\n  {'Date':<12s} {'AI':>10s} {'AI%':>7s} {'B&H':>10s} {'B&H%':>7s} {'Alpha':>7s} Trades")
    print(f"  {'-'*75}")

    for i, idx in enumerate(rebalance_indices):
        date_str = ref.index[idx].strftime("%Y-%m-%d")
        end_date = ref.index[idx].strftime("%Y-%m-%d")

        current_prices = {}
        for t in tickers:
            if t in all_hist and idx < len(all_hist[t]):
                current_prices[t] = float(all_hist[t]["close"].iloc[idx])

        # Portfolio values
        ai_val = portfolio["cash"]
        for t in tickers:
            if t in current_prices:
                ai_val += portfolio["positions"][t]["long"] * current_prices[t]
        bh_val = sum(bh_shares.get(t, 0) * current_prices.get(t, 0) for t in tickers)

        portfolio_values.append(ai_val)
        bh_values.append(bh_val)

        if i == 0:
            print(f"  {date_str:<12s} ${ai_val:>9,.0f}    ---  ${bh_val:>9,.0f}    ---     ---  (start)")
            continue

        # Get live data for rule-based agents
        live_data = {}
        for t in tickers:
            try:
                live_data[t] = provider.get_full_analysis(t)
            except Exception:
                pass

        # Run ALL original agents
        all_signals = {}
        trades = []
        for t in tickers:
            if t not in current_prices:
                continue

            prices_df = all_hist[t].iloc[:idx+1] if t in all_hist else None
            orig_signals = run_original_agent_suite(t, end_date, prices_df, live_data.get(t))

            if orig_signals:
                for aid, sig in orig_signals.items():
                    all_signals.setdefault(aid, {})[t] = sig

        # Risk management + committee
        risk = run_risk_management(list(current_prices.keys()), portfolio, current_prices)
        all_signals["risk_management_agent"] = risk

        stock_data = live_data  # For committee ranking
        decisions, _ = run_investment_committee(
            list(current_prices.keys()), all_signals, risk, portfolio, stock_data=stock_data
        )

        # Execute
        for t in list(current_prices.keys()):
            dec = decisions.get(t, {"action": "hold", "quantity": 0})
            price = current_prices[t]
            qty = dec["quantity"]

            if dec["action"] == "buy" and qty > 0:
                cost = qty * price
                if cost <= portfolio["cash"]:
                    old = portfolio["positions"][t]["long"]
                    old_b = portfolio["positions"][t]["long_cost_basis"]
                    new_total = old + qty
                    if new_total > 0:
                        portfolio["positions"][t]["long_cost_basis"] = (old_b * old + cost) / new_total
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

        # Recalculate
        ai_val = portfolio["cash"]
        for t in tickers:
            if t in current_prices:
                ai_val += portfolio["positions"][t]["long"] * current_prices[t]
        portfolio_values[-1] = ai_val

        ai_ret = (ai_val / initial_cash - 1) * 100
        bh_ret = (bh_val / initial_cash - 1) * 100
        alpha = ai_ret - bh_ret
        ac = Fore.GREEN if alpha > 0 else Fore.RED
        trades_str = ", ".join(trades[:3]) + (f" +{len(trades)-3}" if len(trades) > 3 else "") if trades else "Hold"

        print(f"  {date_str:<12s} ${ai_val:>9,.0f} {ai_ret:>+6.1f}% ${bh_val:>9,.0f} {bh_ret:>+6.1f}% {ac}{alpha:>+6.1f}%{Style.RESET_ALL} {trades_str}")

    # Results
    final_ai = portfolio_values[-1]
    final_bh = bh_values[-1]
    ai_total = (final_ai / initial_cash - 1) * 100
    bh_total = (final_bh / initial_cash - 1) * 100

    returns = np.array([(portfolio_values[j] / portfolio_values[j-1] - 1) for j in range(1, len(portfolio_values))])
    bh_rets = np.array([(bh_values[j] / bh_values[j-1] - 1) for j in range(1, len(bh_values))])
    sharpe = (np.mean(returns) * 12) / (np.std(returns) * np.sqrt(12)) if np.std(returns) > 0 else 0
    bh_sharpe = (np.mean(bh_rets) * 12) / (np.std(bh_rets) * np.sqrt(12)) if np.std(bh_rets) > 0 else 0
    max_dd = max((np.maximum.accumulate(portfolio_values) - portfolio_values) / np.maximum.accumulate(portfolio_values))
    bh_dd = max((np.maximum.accumulate(bh_values) - bh_values) / np.maximum.accumulate(bh_values))

    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}")
    print(f"  RESULTS: ORIGINAL AGENTS + FINANCIAL DATASETS API")
    print(f"{'='*80}{Style.RESET_ALL}")
    aic = Fore.GREEN if ai_total > bh_total else Fore.RED
    print(f"  AI Return:     {aic}{ai_total:>+.2f}%{Style.RESET_ALL}")
    print(f"  B&H Return:    {bh_total:>+.2f}%")
    print(f"  Alpha:         {aic}{(ai_total-bh_total):>+.2f}%{Style.RESET_ALL}")
    print(f"  AI Sharpe:     {sharpe:.2f}")
    print(f"  B&H Sharpe:    {bh_sharpe:.2f}")
    print(f"  AI Max DD:     {max_dd*100:.1f}%")
    print(f"  B&H Max DD:    {bh_dd*100:.1f}%")
    print(f"{'='*80}")

    if ai_total > bh_total:
        print(f"\n  {Fore.GREEN}{Style.BRIGHT}AI BEATS BUY & HOLD by {ai_total-bh_total:+.2f}%!{Style.RESET_ALL}")
    else:
        print(f"\n  {Fore.RED}B&H wins by {bh_total-ai_total:.2f}%{Style.RESET_ALL}")


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
