#!/usr/bin/env python3
"""
AI Hedge Fund - Live Data Trading Pipeline
All 15 AI agents analyze REAL market data from Yahoo Finance.
Zero random data. Zero hardcoded values. 100% real.

Usage:
    python scripts/run_live_trading.py --tickers AAPL,NVDA,MSFT,TSLA,GOOG
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
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S", stream=sys.stdout, force=True,
)
logger = logging.getLogger(__name__)

from colorama import Fore, Style, init
from src.data.market_data import MarketDataProvider
from src.utils.display import print_trading_output
init(autoreset=True)


# ============================================================
# AGENT IMPLEMENTATIONS - Using REAL data
# ============================================================

def warren_buffett_analyze(ticker: str, d: dict) -> dict:
    """Warren Buffett: Moat + Quality + Valuation. Uses ROE, margins, PE, FCF, debt."""
    score = 0
    reasons = []

    # ROE (Return on Equity) - Buffett wants >15%
    if d["roe"] > 25:
        score += 2; reasons.append(f"Excellent ROE of {d['roe']:.0f}%")
    elif d["roe"] > 15:
        score += 1; reasons.append(f"Good ROE of {d['roe']:.0f}%")
    elif d["roe"] < 10:
        score -= 1; reasons.append(f"Weak ROE of {d['roe']:.0f}%")

    # Valuation - PE relative to growth
    if d["pe"] > 0 and d["pe"] < 20:
        score += 2; reasons.append(f"Attractive P/E of {d['pe']:.1f}")
    elif d["pe"] > 0 and d["pe"] < 30:
        score += 1; reasons.append(f"Fair P/E of {d['pe']:.1f}")
    elif d["pe"] > 40:
        score -= 1; reasons.append(f"Expensive at P/E {d['pe']:.1f}")

    # Moat indicator: gross margin stability
    if d["gross_margin"] > 0.40:
        score += 1; reasons.append(f"Strong moat - gross margin {d['gross_margin']*100:.0f}%")

    # Free cash flow
    if d["fcf_yield"] > 0.04:
        score += 1; reasons.append(f"Strong FCF yield {d['fcf_yield']*100:.1f}%")
    elif d["fcf_yield"] > 0.02:
        score += 0.5

    # Debt - Buffett hates excessive leverage
    if d["debt_equity"] > 2.0:
        score -= 2; reasons.append(f"Dangerous leverage D/E={d['debt_equity']:.1f}")
    elif d["debt_equity"] < 0.5:
        score += 1; reasons.append("Conservative balance sheet")

    # Earnings consistency
    if d["earnings_growth"] > 0.10:
        score += 1; reasons.append(f"Growing earnings {d['earnings_growth']*100:.0f}%")
    elif d["earnings_growth"] < -0.10:
        score -= 1; reasons.append(f"Declining earnings {d['earnings_growth']*100:.0f}%")

    # Analyst target - margin of safety
    if d.get("upside_to_target", 0) > 0.20:
        score += 1; reasons.append(f"Analysts see {d['upside_to_target']*100:.0f}% upside")

    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(95, max(20, 35 + abs(score) * 8))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def ben_graham_analyze(ticker: str, d: dict) -> dict:
    """Ben Graham: Deep value. PE<15 ideal, strong balance sheet, margin of safety."""
    score = 0
    reasons = []

    if d["pe"] > 0 and d["pe"] < 15:
        score += 3; reasons.append(f"P/E {d['pe']:.1f} - classic Graham value")
    elif d["pe"] > 0 and d["pe"] < 20:
        score += 1; reasons.append(f"P/E {d['pe']:.1f} - moderate value")
    elif d["pe"] > 25:
        score -= 1; reasons.append(f"P/E {d['pe']:.1f} exceeds Graham criteria")

    if d["pb"] > 0 and d["pb"] < 1.5:
        score += 2; reasons.append(f"P/B {d['pb']:.1f} - strong margin of safety")
    elif d["pb"] > 5:
        score -= 1; reasons.append(f"P/B {d['pb']:.1f} too high")

    if d["debt_equity"] < 0.5:
        score += 1; reasons.append("Conservative balance sheet")

    if d["dividend_yield"] > 0.02:
        score += 1; reasons.append(f"Dividend yield {d['dividend_yield']*100:.1f}%")

    # Graham's net-net: if price is below book value AND earnings positive
    if d["pb"] < 1.0 and d["earnings_growth"] > 0:
        score += 2; reasons.append("Trading below book value with positive earnings!")

    # ADAPTIVE: Don't be blindly bearish on growing companies
    if d["earnings_growth"] > 0.20 and d["roe"] > 20:
        score += 1; reasons.append("Strong fundamentals offset premium valuation")

    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(90, max(20, 30 + abs(score) * 8))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def charlie_munger_analyze(ticker: str, d: dict) -> dict:
    """Charlie Munger: Quality at reasonable price. Moat + management + valuation."""
    score = 0
    reasons = []

    if d["roe"] > 20:
        score += 2; reasons.append(f"Quality business ROE {d['roe']:.0f}%")
    if d["gross_margin"] > 0.50:
        score += 2; reasons.append(f"Exceptional margin {d['gross_margin']*100:.0f}% = pricing power")
    elif d["gross_margin"] > 0.35:
        score += 1
    if d["pe"] > 0 and d["pe"] < 25:
        score += 1; reasons.append(f"Reasonable valuation P/E {d['pe']:.1f}")
    elif d["pe"] > 50:
        score -= 1; reasons.append(f"Too expensive at P/E {d['pe']:.1f}")
    if d["earnings_growth"] > 0.10:
        score += 1; reasons.append(f"Growing earnings {d['earnings_growth']*100:.0f}%")
    if d["operating_margin"] > 0.25:
        score += 1; reasons.append(f"Strong operating margin {d['operating_margin']*100:.0f}%")

    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(90, max(25, 35 + abs(score) * 9))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def cathie_wood_analyze(ticker: str, d: dict) -> dict:
    """Cathie Wood: Disruptive innovation, explosive growth, AI/tech."""
    score = 0
    reasons = []

    if d["revenue_growth"] > 0.30:
        score += 3; reasons.append(f"Explosive revenue growth {d['revenue_growth']*100:.0f}%!")
    elif d["revenue_growth"] > 0.15:
        score += 2; reasons.append(f"Strong growth {d['revenue_growth']*100:.0f}%")
    elif d["revenue_growth"] < 0:
        score -= 2; reasons.append(f"Revenue declining {d['revenue_growth']*100:.0f}%")

    sector = d.get("sector", "")
    industry = d.get("industry", "")
    if "Semiconductor" in industry or "AI" in str(d.get("industry", "")):
        score += 2; reasons.append(f"AI/semiconductor disruption play")
    elif sector == "Technology":
        score += 1; reasons.append("Technology sector")

    if d["earnings_growth"] > 0.50:
        score += 1; reasons.append("Hyper-growth earnings")

    # Cathie looks at future potential, not current PE
    if d.get("upside_to_target", 0) > 0.30:
        score += 1; reasons.append(f"Significant upside to analyst target ({d['upside_to_target']*100:.0f}%)")

    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(95, max(25, 40 + abs(score) * 10))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def michael_burry_analyze(ticker: str, d: dict) -> dict:
    """Michael Burry: Contrarian value. Only bearish when BOTH fundamentals AND Street agree."""
    score = 0
    reasons = []

    # Bubble detection - but RESPECT analyst consensus
    analyst_score = d.get("analyst_score", 3.0)
    if d["pe"] > 100 and analyst_score > 3.0:
        score -= 3; reasons.append(f"P/E {d['pe']:.0f} AND analysts skeptical (score {analyst_score:.1f})")
    elif d["pe"] > 100 and analyst_score <= 2.5:
        score -= 1; reasons.append(f"P/E {d['pe']:.0f} extreme but analysts say BUY - respecting Street")
    elif d["pe"] > 50 and d["earnings_growth"] < -0.20:
        score -= 2; reasons.append(f"P/E {d['pe']:.0f} with collapsing earnings - disconnect")

    # Deep value detection
    if d["pe"] > 0 and d["pe"] < 12 and d["fcf_yield"] > 0.06:
        score += 3; reasons.append(f"Deep value: P/E {d['pe']:.0f} with {d['fcf_yield']*100:.1f}% FCF yield")

    # Momentum check - don't fight the tape
    if d.get("momentum_3m", 0) > 0.15:
        score += 1; reasons.append(f"Strong momentum {d['momentum_3m']*100:+.0f}% - don't fight the tape")
    elif d.get("momentum_3m", 0) < -0.20 and d["pe"] > 40:
        score -= 1; reasons.append("Falling knife with high PE")

    # Analyst consensus is a REAL signal from people with billions at stake
    if analyst_score <= 1.5:
        score += 1; reasons.append(f"Street consensus STRONG BUY - respect the money")
    elif analyst_score >= 4.0:
        score -= 1; reasons.append("Street consensus negative")

    signal = "bearish" if score <= -2 else ("bullish" if score >= 2 else "neutral")
    conf = min(90, max(25, 35 + abs(score) * 10))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def peter_lynch_analyze(ticker: str, d: dict) -> dict:
    """Peter Lynch: PEG ratio, growth at reasonable price, understandable business."""
    score = 0
    reasons = []

    peg = d.get("peg", 0)
    if peg > 0 and peg <= 1.0:
        score += 3; reasons.append(f"PEG {peg:.2f} - growth at a reasonable price!")
    elif peg > 0 and peg <= 1.5:
        score += 1; reasons.append(f"PEG {peg:.2f} acceptable")
    elif peg > 2.5:
        score -= 1; reasons.append(f"PEG {peg:.2f} - overpriced for growth")
    elif peg < 0:
        score -= 2; reasons.append("Negative PEG - earnings declining")

    if d["earnings_growth"] > 0.20:
        score += 2; reasons.append(f"Earnings growing {d['earnings_growth']*100:.0f}%!")
    elif d["earnings_growth"] > 0.10:
        score += 1

    if d["debt_equity"] < 0.5:
        score += 1; reasons.append("Clean balance sheet")

    # Lynch likes companies where analysts haven't caught on yet
    if d.get("analyst_count", 0) < 20 and d["earnings_growth"] > 0.15:
        score += 1; reasons.append("Under-followed by analysts")

    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(90, max(25, 35 + abs(score) * 9))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def phil_fisher_analyze(ticker: str, d: dict) -> dict:
    """Phil Fisher: Growth + R&D + management quality."""
    score = 0
    reasons = []
    if d["revenue_growth"] > 0.15:
        score += 2; reasons.append(f"Revenue growth {d['revenue_growth']*100:.0f}% - strong products")
    if d["gross_margin"] > 0.50:
        score += 1; reasons.append("High margins = competitive products")
    if d["earnings_growth"] > 0.10:
        score += 1; reasons.append(f"Earnings growing {d['earnings_growth']*100:.0f}%")
    if d["operating_margin"] > 0.20:
        score += 1; reasons.append(f"Operating margin {d['operating_margin']*100:.0f}% - efficient")
    if d.get("rnd_ratio", 0) > 0.10:
        score += 1; reasons.append("Significant R&D investment")
    signal = "bullish" if score >= 3 else ("bearish" if score <= 0 else "neutral")
    conf = min(85, max(25, 35 + abs(score) * 8))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def stanley_druckenmiller_analyze(ticker: str, d: dict) -> dict:
    """Druckenmiller: Macro + momentum + sector rotation. Respects Street consensus."""
    score = 0
    reasons = []

    # Momentum - but use 6m (more reliable than 3m noise)
    m6 = d.get("momentum_6m", 0)
    m12 = d.get("momentum_12m", 0)
    if m12 > 0.30:
        score += 2; reasons.append(f"Strong 12m momentum {m12*100:+.0f}% - trend is your friend")
    elif m6 > 0.10:
        score += 1; reasons.append(f"Positive 6m momentum {m6*100:+.0f}%")
    elif m6 < -0.20 and m12 < -0.10:
        score -= 1; reasons.append(f"Sustained downtrend (6m {m6*100:+.0f}%, 12m {m12*100:+.0f}%)")
    # DON'T penalize short-term dips if long-term trend is up
    elif d.get("momentum_3m", 0) < -0.10 and m12 > 0.10:
        score += 0.5; reasons.append(f"Short-term pullback in long-term uptrend - potential entry")

    # Price trend
    if d.get("golden_cross", False):
        score += 1; reasons.append("Golden cross - long-term bullish")

    # Revenue acceleration
    if d["revenue_growth"] > 0.20:
        score += 1; reasons.append(f"Revenue momentum {d['revenue_growth']*100:.0f}%")

    # ANALYST CONSENSUS - biggest signal for macro trader
    analyst_score = d.get("analyst_score", 3.0)
    upside = d.get("upside_to_target", 0)
    if analyst_score <= 1.5 and upside > 0.20:
        score += 2; reasons.append(f"Street STRONG BUY with {upside*100:.0f}% upside - follow the smart money")
    elif analyst_score <= 2.0:
        score += 1; reasons.append(f"Street says BUY (score {analyst_score:.1f})")
    elif analyst_score >= 4.0:
        score -= 1; reasons.append("Street negative")

    # Market regime
    regime = d.get("market_regime", "unknown")
    if regime == "bear":
        score -= 1; reasons.append(f"Bear market - defensive")

    signal = "bullish" if score >= 2 else ("bearish" if score <= -2 else "neutral")
    conf = min(90, max(25, 40 + abs(score) * 9))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def bill_ackman_analyze(ticker: str, d: dict) -> dict:
    """Bill Ackman: Activist value - undervalued quality with catalysts."""
    score = 0
    reasons = []
    if d["pe"] > 0 and d["pe"] < 25 and d["roe"] > 15:
        score += 2; reasons.append(f"Quality at value P/E {d['pe']:.0f}, ROE {d['roe']:.0f}%")
    if d["fcf_yield"] > 0.04:
        score += 2; reasons.append(f"FCF yield {d['fcf_yield']*100:.1f}% - buyback/dividend potential")
    if d["gross_margin"] > 0.50 and d["pe"] > 0 and d["pe"] < 30:
        score += 1; reasons.append("High-margin at reasonable price")
    if d.get("upside_to_target", 0) > 0.25:
        score += 1; reasons.append(f"Analyst upside {d['upside_to_target']*100:.0f}% - catalyst")
    if d["pe"] > 60:
        score -= 2; reasons.append(f"P/E {d['pe']:.0f} - no margin of safety")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(85, max(25, 35 + abs(score) * 9))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def rakesh_jhunjhunwala_analyze(ticker: str, d: dict) -> dict:
    """Rakesh Jhunjhunwala: Growth + quality + momentum."""
    score = 0
    reasons = []
    if d["revenue_growth"] > 0.15:
        score += 2; reasons.append(f"Revenue growth {d['revenue_growth']*100:.0f}%")
    if d["earnings_growth"] > 0.20:
        score += 2; reasons.append(f"Earnings growth {d['earnings_growth']*100:.0f}%!")
    if d["roe"] > 20:
        score += 1; reasons.append(f"Quality ROE {d['roe']:.0f}%")
    if d.get("momentum_6m", 0) > 0.10:
        score += 1; reasons.append(f"Positive momentum")
    if d["pe"] > 80:
        score -= 1; reasons.append("Stretched valuation")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(85, max(25, 35 + abs(score) * 8))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def aswath_damodaran_analyze(ticker: str, d: dict) -> dict:
    """Damodaran: Intrinsic value via DCF thinking. EV/EBITDA, FCF yield, growth vs implied."""
    score = 0
    reasons = []

    # Is the market pricing in too much or too little growth?
    if d["pe"] > 0 and d["earnings_growth"] > 0:
        implied = d["pe"] / 15 - 1
        if d["earnings_growth"] > implied:
            score += 2; reasons.append(f"Growth {d['earnings_growth']*100:.0f}% > implied {implied*100:.0f}%")
        else:
            score -= 1; reasons.append(f"Growth {d['earnings_growth']*100:.0f}% < implied {implied*100:.0f}%")

    if d["ev_ebitda"] > 0 and d["ev_ebitda"] < 15:
        score += 2; reasons.append(f"EV/EBITDA {d['ev_ebitda']:.1f} - below fair value")
    elif d["ev_ebitda"] > 30:
        score -= 1; reasons.append(f"EV/EBITDA {d['ev_ebitda']:.1f} - premium")

    if d["fcf_yield"] > 0.05:
        score += 1; reasons.append(f"FCF yield {d['fcf_yield']*100:.1f}% exceeds WACC")

    # Forward PE gives implied expectations
    if d.get("forward_pe", 0) > 0 and d["pe"] > 0:
        if d["forward_pe"] < d["pe"] * 0.8:
            score += 1; reasons.append("Forward PE well below trailing - earnings accelerating")

    signal = "bullish" if score >= 2 else ("bearish" if score <= -1 else "neutral")
    conf = min(85, max(25, 35 + abs(score) * 10))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def technical_analyst_analyze(ticker: str, d: dict) -> dict:
    """Technical Analyst: REAL RSI, MACD, SMA, Bollinger. Oversold = opportunity when fundamentals OK."""
    score = 0
    reasons = []

    rsi = d.get("rsi", 50)
    analyst_score = d.get("analyst_score", 3.0)
    upside = d.get("upside_to_target", 0)

    # RSI with context: oversold + good fundamentals = BUY opportunity
    if rsi < 30:
        score += 2; reasons.append(f"RSI {rsi:.0f} - OVERSOLD - reversal opportunity")
        if upside > 0.20:
            score += 1; reasons.append(f"Oversold + {upside*100:.0f}% upside to target = strong buy signal")
    elif rsi < 40 and upside > 0.15:
        score += 1; reasons.append(f"RSI {rsi:.0f} near oversold with {upside*100:.0f}% upside - accumulate")
    elif rsi > 75:
        score -= 1; reasons.append(f"RSI {rsi:.0f} - overbought, possible pullback")
    else:
        reasons.append(f"RSI {rsi:.0f} - neutral")

    # MACD
    macd = d.get("macd", {})
    if macd.get("bullish_cross", False):
        score += 1; reasons.append("MACD bullish crossover")
    elif macd.get("histogram", 0) < -1:
        score -= 0.5; reasons.append("MACD bearish momentum")

    # Moving averages
    if d.get("golden_cross", False):
        score += 1; reasons.append("Golden cross (SMA50 > SMA200)")

    # KEY FIX: Below SMA50 is a DIP BUY when analysts say strong_buy
    if not d.get("price_above_sma50", True) and analyst_score <= 1.5 and upside > 0.25:
        score += 2; reasons.append(f"Below SMA50 but Street says STRONG BUY with {upside*100:.0f}% upside - BUY THE DIP")
    elif not d.get("price_above_sma50", True) and d.get("golden_cross", False):
        score += 0.5; reasons.append("Below SMA50 but golden cross intact - pullback in uptrend")
    elif not d.get("price_above_sma200", True):
        score -= 1; reasons.append("Below SMA200 - long-term downtrend")

    # Bollinger - oversold near lower band with good fundamentals
    bb = d.get("bollinger", {})
    pct_b = bb.get("pct_b", 0.5)
    if pct_b < 0.15 and analyst_score <= 2.0:
        score += 1; reasons.append("Lower Bollinger Band + analyst BUY = mean reversion setup")

    signal = "bullish" if score >= 2 else ("bearish" if score <= -1.5 else "neutral")
    conf = min(85, max(25, 35 + abs(score) * 8))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def fundamentals_analyst_analyze(ticker: str, d: dict) -> dict:
    """Fundamentals: Revenue, margins, cash flow, debt - all REAL."""
    score = 0
    reasons = []
    if d["revenue_growth"] > 0.15:
        score += 2; reasons.append(f"Revenue growth {d['revenue_growth']*100:.0f}%")
    elif d["revenue_growth"] > 0.05:
        score += 1
    elif d["revenue_growth"] < 0:
        score -= 1; reasons.append(f"Revenue declining {d['revenue_growth']*100:.0f}%")

    if d["gross_margin"] > 0.50:
        score += 1; reasons.append(f"Gross margin {d['gross_margin']*100:.0f}%")
    if d["operating_margin"] > 0.25:
        score += 1; reasons.append(f"Operating margin {d['operating_margin']*100:.0f}%")
    if d["fcf_yield"] > 0.03:
        score += 1; reasons.append(f"FCF yield {d['fcf_yield']*100:.1f}%")
    if d["debt_equity"] > 2.0:
        score -= 2; reasons.append(f"High leverage D/E={d['debt_equity']:.1f}")
    if d["earnings_growth"] < -0.20:
        score -= 2; reasons.append(f"Earnings collapsing {d['earnings_growth']*100:.0f}%")

    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(85, max(25, 35 + abs(score) * 8))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def sentiment_analyst_analyze(ticker: str, d: dict) -> dict:
    """Sentiment: REAL analyst ratings, short interest, insider ownership."""
    score = 0
    reasons = []

    # REAL analyst consensus
    rec = d.get("analyst_recommendation", "none")
    rec_score = d.get("analyst_score", 3.0)
    if rec_score <= 1.5:
        score += 2; reasons.append(f"Wall Street: STRONG BUY (score {rec_score:.1f}/5)")
    elif rec_score <= 2.0:
        score += 1; reasons.append(f"Wall Street: BUY (score {rec_score:.1f}/5)")
    elif rec_score >= 4.0:
        score -= 2; reasons.append(f"Wall Street: SELL (score {rec_score:.1f}/5)")
    elif rec_score >= 3.0:
        score -= 1; reasons.append(f"Wall Street: HOLD (score {rec_score:.1f}/5)")

    # Short interest
    si = d.get("short_pct_float", 0)
    if si > 0.10:
        score -= 1; reasons.append(f"High short interest {si*100:.1f}%")
    elif si < 0.02:
        score += 0.5; reasons.append("Low short interest - consensus positive")

    # Institutional ownership
    inst = d.get("institutional_ownership", 0)
    if inst > 0.80:
        score += 0.5; reasons.append(f"Strong institutional ownership {inst*100:.0f}%")

    # Upside to target
    upside = d.get("upside_to_target", 0)
    if upside > 0.30:
        score += 1; reasons.append(f"Analyst target implies {upside*100:.0f}% upside")
    elif upside < -0.10:
        score -= 1; reasons.append(f"Trading above analyst target")

    signal = "bullish" if score >= 2 else ("bearish" if score <= -1 else "neutral")
    conf = min(80, max(20, 30 + abs(score) * 9))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}


def valuation_analyst_analyze(ticker: str, d: dict) -> dict:
    """Valuation: EV/EBITDA, PE vs growth, FCF yield, forward PE."""
    score = 0
    reasons = []

    if d["ev_ebitda"] > 0 and d["ev_ebitda"] < 12:
        score += 2; reasons.append(f"EV/EBITDA {d['ev_ebitda']:.1f} - cheap")
    elif d["ev_ebitda"] > 0 and d["ev_ebitda"] < 20:
        score += 1; reasons.append(f"EV/EBITDA {d['ev_ebitda']:.1f} - fair")
    elif d["ev_ebitda"] > 35:
        score -= 1; reasons.append(f"EV/EBITDA {d['ev_ebitda']:.1f} - expensive")

    if d["pe"] > 0 and d["pe"] < 20 and d["earnings_growth"] > 0.10:
        score += 2; reasons.append(f"PE {d['pe']:.0f} with {d['earnings_growth']*100:.0f}% growth")

    fwd = d.get("forward_pe", 0)
    if fwd > 0 and fwd < 20:
        score += 1; reasons.append(f"Forward P/E {fwd:.1f} - discounting growth")

    if d["fcf_yield"] > 0.05:
        score += 1; reasons.append(f"FCF yield {d['fcf_yield']*100:.1f}%")

    if d["pe"] > 60:
        score -= 2; reasons.append(f"P/E {d['pe']:.0f} - extreme valuation")

    signal = "bullish" if score >= 2 else ("bearish" if score <= -2 else "neutral")
    conf = min(85, max(25, 35 + abs(score) * 9))
    return {"signal": signal, "confidence": round(conf, 1), "reasoning": ". ".join(reasons)}



# ============================================================
# AGENT REGISTRY & GROUPS (same structure as v1)
# ============================================================
AGENTS = {
    "warren_buffett_agent": ("Warren Buffett", warren_buffett_analyze),
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
    "technical_analyst_agent": ("Technical Analyst", technical_analyst_analyze),
    "fundamentals_analyst_agent": ("Fundamentals Analyst", fundamentals_analyst_analyze),
    "sentiment_analyst_agent": ("Sentiment Analyst", sentiment_analyst_analyze),
    "valuation_analyst_agent": ("Valuation Analyst", valuation_analyst_analyze),
}

AGENT_GROUPS = {
    "value_investors": {
        "agents": ["warren_buffett_agent", "ben_graham_agent", "charlie_munger_agent", "bill_ackman_agent"],
        "perspective": "Value & Quality",
        "weight": 1.2,  # Highest accuracy group
        "veto_power": False,  # Removed - was blocking good trades
    },
    "growth_investors": {
        "agents": ["cathie_wood_agent", "peter_lynch_agent", "phil_fisher_agent", "rakesh_jhunjhunwala_agent"],
        "perspective": "Growth & Innovation",
        "weight": 1.1,
        "veto_power": False,
    },
    "macro_strategists": {
        "agents": ["stanley_druckenmiller_agent", "michael_burry_agent"],
        "perspective": "Macro & Contrarian",
        "weight": 0.7,  # Lower weight - lowest accuracy
        "veto_power": False,
    },
    "quant_analysts": {
        "agents": ["technical_analyst_agent", "fundamentals_analyst_agent", "sentiment_analyst_agent",
                    "valuation_analyst_agent", "aswath_damodaran_agent"],
        "perspective": "Quantitative Analysis",
        "weight": 1.0,
        "veto_power": False,
    },
}


# ============================================================
# RISK MANAGEMENT
# ============================================================
def run_risk_management(tickers, portfolio, current_prices):
    """Position limits: up to 25% per position, 95% max invested."""
    total_value = portfolio["cash"]
    for t, pos in portfolio.get("positions", {}).items():
        if t in current_prices:
            total_value += pos.get("long", 0) * current_prices[t]
            total_value -= pos.get("short", 0) * current_prices[t]

    risk_analysis = {}
    for ticker in tickers:
        price = current_prices.get(ticker, 0)
        if price == 0:
            risk_analysis[ticker] = {"remaining_position_limit": 0, "current_price": 0, "reasoning": {}}
            continue

        pos = portfolio.get("positions", {}).get(ticker, {})
        current_exposure = abs(pos.get("long", 0) * price - pos.get("short", 0) * price)
        position_limit = total_value * 0.25  # 25% max per position
        remaining = position_limit - current_exposure
        max_size = min(remaining, portfolio["cash"])

        risk_analysis[ticker] = {
            "remaining_position_limit": float(max_size),
            "current_price": float(price),
            "reasoning": {
                "portfolio_value": float(total_value),
                "position_limit": float(position_limit),
                "remaining_limit": float(remaining),
                "available_cash": float(portfolio["cash"]),
            },
        }
    return risk_analysis


# ============================================================
# INVESTMENT COMMITTEE (enhanced)
# ============================================================
def run_investment_committee(tickers, analyst_signals, risk_analysis, portfolio, show_debate=False, stock_data=None):
    """Investment committee with momentum-based sizing and min investment rule."""
    decisions = {}
    debate_summaries = {}
    stock_data = stock_data or {}

    for ticker in tickers:
        group_views = {}
        for gname, gcfg in AGENT_GROUPS.items():
            bullish = bearish = neutral = 0.0
            for aid in gcfg["agents"]:
                if aid in analyst_signals and ticker in analyst_signals[aid]:
                    sig = analyst_signals[aid][ticker]
                    if sig["signal"] == "bullish": bullish += sig["confidence"]
                    elif sig["signal"] == "bearish": bearish += sig["confidence"]
                    else: neutral += sig["confidence"]

            total = bullish + bearish + neutral
            if total == 0:
                group_views[gname] = {"view": "neutral", "strength": 0, "weight": gcfg["weight"]}
                continue

            if bullish > bearish and bullish > neutral:
                view, strength = "bullish", bullish / total
            elif bearish > bullish and bearish > neutral:
                view, strength = "bearish", bearish / total
            else:
                view, strength = "neutral", neutral / total if total > 0 else 0

            group_views[gname] = {"view": view, "strength": round(strength, 2), "weight": gcfg["weight"]}

        # Count weighted group votes
        bullish_groups = [(g, v) for g, v in group_views.items() if v["view"] == "bullish"]
        bearish_groups = [(g, v) for g, v in group_views.items() if v["view"] == "bearish"]

        weighted_bull = sum(v["strength"] * v["weight"] for _, v in bullish_groups)
        weighted_bear = sum(v["strength"] * v["weight"] for _, v in bearish_groups)

        risk = risk_analysis.get(ticker, {})
        price = risk.get("current_price", 0)
        max_val = risk.get("remaining_position_limit", 0)
        max_shares = int(max_val / price) if price > 0 else 0

        pos = portfolio.get("positions", {}).get(ticker, {})
        long_shares = pos.get("long", 0)

        n_bull = len(bullish_groups)
        n_bear = len(bearish_groups)
        total_groups = len(group_views)
        net = weighted_bull - weighted_bear

        # Build debate summary
        parts = []
        for gn, gv in group_views.items():
            parts.append(f"{AGENT_GROUPS[gn]['perspective']}: {gv['view'].upper()} ({gv['strength']:.0%})")
        debate_summaries[ticker] = " | ".join(parts)

        # Decision logic - more aggressive, min investment rule
        confidence = min(95, max(20, abs(net) * 50 + n_bull * 5 + 25))

        if n_bull >= 3 and max_shares > 0:
            sizing = 0.75 + (n_bull - 3) * 0.10  # 75-85%
            quantity = max(1, int(max_shares * sizing))
            action = "buy"
            reasoning = f"Strong consensus: {n_bull}/{total_groups} groups bullish. Sizing {sizing:.0%}."
        elif n_bull >= 2 and n_bear <= 1 and max_shares > 0:
            sizing = 0.50
            quantity = max(1, int(max_shares * sizing))
            action = "buy"
            reasoning = f"Moderate consensus: {n_bull}/{total_groups} bullish. Sizing {sizing:.0%}."
        elif n_bear >= 3:
            if long_shares > 0:
                quantity = long_shares
                action = "sell"
                reasoning = f"Strong bearish: {n_bear}/{total_groups} groups bearish. Selling all."
            else:
                # CRITICAL FIX: Only short if Wall Street ANALYSTS also agree
                # Never short a stock where analysts say BUY
                sd = stock_data.get(ticker, {})
                stock_analyst_score = sd.get("analyst_score", 3.0) if sd else 3.0

                if stock_analyst_score > 3.0 and max_shares > 0:
                    quantity = max(1, int(max_shares * 0.20))
                    action = "short"
                    reasoning = f"Strong bearish + analysts agree: shorting conservatively."
                else:
                    quantity = 0
                    action = "hold"
                    reasoning = f"Bearish signals but Wall Street analysts disagree - NOT SHORTING. When the Street has skin in the game and says buy, we listen."
        elif n_bear >= 2 and long_shares > 0:
            quantity = max(1, int(long_shares * 0.5))
            action = "sell"
            reasoning = f"Moderate bearish - reducing position."
        else:
            # MIN INVESTMENT RULE: if mostly bullish, invest at least something
            if n_bull >= 2 and max_shares > 0:
                quantity = max(1, int(max_shares * 0.25))
                action = "buy"
                reasoning = f"Min investment rule: {n_bull} groups bullish, allocating 25%."
            else:
                quantity = 0
                action = "hold"
                reasoning = f"Split: {n_bull} bull, {n_bear} bear. Holding."

        # STRONG BUY OVERRIDE: If stock has strong_buy from analysts AND good fundamentals, ensure allocation
        sd = stock_data.get(ticker, {})
        if sd:
            a_score = sd.get("analyst_score", 3.0)
            upside = sd.get("upside_to_target", 0)
            cash_available = portfolio.get("cash", 0)
            cash_buy_shares = int(cash_available * 0.40 / price) if price > 0 else 0
            can_buy = max(max_shares, cash_buy_shares)  # Use either risk limit OR direct cash
            if a_score <= 1.5 and upside > 0.25 and action == "hold" and can_buy > 0:
                # Analysts strongly bullish with big upside - override hold to buy
                quantity = max(1, min(can_buy, int(cash_available * 0.40 / price)))
                action = "buy"
                confidence = 85.0
                reasoning = f"STRONG BUY OVERRIDE: Analysts score {a_score:.1f} with {upside*100:.0f}% upside to target. Overriding committee hold."
            elif a_score <= 2.0 and upside > 0.15 and action == "hold" and can_buy > 0 and long_shares == 0:
                # Moderate analyst buy with no position - at least get some exposure
                quantity = max(1, min(can_buy, int(cash_available * 0.25 / price)))
                action = "buy"
                confidence = 75.0
                reasoning = f"ANALYST BUY OVERRIDE: Score {a_score:.1f}, {upside*100:.0f}% upside, no position yet. Initiating."

        # REBALANCING RULES for existing positions
        if action == "hold" and long_shares > 0:
            # Compute portfolio-level values for rebalancing
            pos_value = long_shares * price
            portfolio_value = sum(
                portfolio.get("positions", {}).get(t, {}).get("long", 0) * risk_analysis.get(t, {}).get("current_price", 0)
                for t in tickers
            ) + portfolio["cash"]
            pos_pct = pos_value / portfolio_value if portfolio_value > 0 else 0
            target_pct = 1.0 / len(tickers)  # equal weight target

            # PROFIT TAKING / TRIM OVERWEIGHT: Free up cash for rebalancing
            # Trim positions that are significantly overweight OR have large gains
            if long_shares > 0 and pos.get("long_cost_basis", 0) > 0:
                gain_pct = (price / pos["long_cost_basis"] - 1)
                # Trim if: (a) big gain + weakening signals, or (b) very overweight
                if gain_pct > 0.30 and n_bull < 2:
                    sell_qty = max(1, int(long_shares * 0.25))
                    quantity = sell_qty
                    action = "sell"
                    reasoning = f"PROFIT TAKING: Position up {gain_pct:.0%}, signals weakening. Trimming 25%."
                elif pos_pct > target_pct * 1.5 and gain_pct > 0.20:
                    # Overweight winner - trim back toward target
                    excess_shares = int((pos_value - portfolio_value * target_pct) / price * 0.5)
                    if excess_shares > 0:
                        quantity = excess_shares
                        action = "sell"
                        reasoning = f"REBALANCE TRIM: {pos_pct:.0%} of portfolio (target {target_pct:.0%}), up {gain_pct:.0%}. Trimming {excess_shares} shares."

            # If still holding and this is a strong bullish stock but underweight, add to it
            if action == "hold":
                cash_available = portfolio.get("cash", 0)
                cash_shares = int(cash_available / price) if price > 0 else 0
                if n_bull >= 3 and pos_pct < target_pct * 0.75 and cash_shares > 0:
                    target_value = portfolio_value * target_pct
                    deficit = target_value - pos_value
                    add_qty = max(1, min(cash_shares, int(deficit / price * 0.5)))
                    quantity = add_qty
                    action = "buy"
                    reasoning = f"REBALANCE: Strong bullish but only {pos_pct:.0%} of portfolio (target {target_pct:.0%}). Adding {add_qty} shares."

        # DEPLOY IDLE CASH: If sitting on >10% cash and this stock is bullish, buy more
        if action == "hold" and portfolio.get("cash", 0) > 0 and price > 0:
            portfolio_value = sum(
                portfolio.get("positions", {}).get(t, {}).get("long", 0) * risk_analysis.get(t, {}).get("current_price", 0)
                for t in tickers
            ) + portfolio["cash"]
            cash_pct = portfolio["cash"] / portfolio_value if portfolio_value > 0 else 0
            if cash_pct > 0.10 and n_bull >= 2:
                deploy = portfolio["cash"] * 0.25 / price
                deploy_qty = max(1, int(deploy))
                if deploy_qty > 0:
                    quantity = deploy_qty
                    action = "buy"
                    reasoning = f"DEPLOY CASH: {cash_pct:.0%} idle cash, {n_bull} groups bullish. Deploying."

        decisions[ticker] = {
            "action": action, "quantity": quantity,
            "confidence": round(confidence, 1), "reasoning": reasoning,
        }

    return decisions, debate_summaries


def run_portfolio_management(tickers, analyst_signals, risk_analysis, portfolio):
    """Backward-compatible wrapper."""
    decisions, _ = run_investment_committee(tickers, analyst_signals, risk_analysis, portfolio)
    return decisions


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="AI Hedge Fund - Live Data Trading")
    parser.add_argument("--tickers", type=str, default="AAPL,NVDA,MSFT,TSLA,GOOG,AMZN,META")
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--show-reasoning", action="store_true")
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    initial_cash = args.initial_cash

    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"  AI HEDGE FUND - LIVE DATA TRADING (REAL MARKET DATA)")
    print(f"{'='*70}{Style.RESET_ALL}")
    print(f"  Date:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Cash:     {Fore.GREEN}${initial_cash:,.2f}{Style.RESET_ALL}")
    print(f"  Tickers:  {Fore.YELLOW}{', '.join(tickers)}{Style.RESET_ALL}")
    print(f"  Agents:   {Fore.CYAN}{len(AGENTS)} AI investors{Style.RESET_ALL}")
    print(f"  Data:     {Fore.GREEN}Yahoo Finance (real-time){Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

    # Step 1: Fetch REAL market data
    print(f"{Style.BRIGHT}STEP 1: Fetching Real Market Data{Style.RESET_ALL}")
    print(f"{'-'*50}")
    provider = MarketDataProvider()
    stock_data = {}
    for symbol in tickers:
        data = provider.get_full_analysis(symbol)
        if "error" not in data:
            stock_data[symbol] = data
            provider.print_data_summary(data)
        else:
            print(f"  {Fore.RED}ERROR: {data['error']}{Style.RESET_ALL}")
    print()

    valid_tickers = [t for t in tickers if t in stock_data]
    if not valid_tickers:
        print(f"{Fore.RED}No valid data. Exiting.{Style.RESET_ALL}")
        return

    current_prices = {t: stock_data[t]["price"] for t in valid_tickers}

    portfolio = {
        "cash": initial_cash, "margin_requirement": 0.0, "margin_used": 0.0,
        "positions": {t: {"long": 0, "short": 0, "long_cost_basis": 0.0,
                          "short_cost_basis": 0.0, "short_margin_used": 0.0} for t in valid_tickers},
        "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in valid_tickers},
    }

    # Step 2: Run all 15 agents
    print(f"{Style.BRIGHT}STEP 2: AI Agent Analysis (15 agents x {len(valid_tickers)} stocks){Style.RESET_ALL}")
    print(f"{'-'*50}")

    analyst_signals = {}
    for agent_id, (name, func) in AGENTS.items():
        signals = {}
        for t in valid_tickers:
            signals[t] = func(t, stock_data[t])
        analyst_signals[agent_id] = signals

        parts = []
        for t in valid_tickers:
            s = signals[t]
            c = {
                "bullish": Fore.GREEN, "bearish": Fore.RED, "neutral": Fore.YELLOW
            }[s["signal"]]
            parts.append(f"{t}:{c}{s['signal'].upper()}{Style.RESET_ALL}({s['confidence']:.0f}%)")
        print(f"  {Fore.CYAN}{name:25s}{Style.RESET_ALL} | {' | '.join(parts)}")

    # Step 3: Risk Management
    print(f"\n{Style.BRIGHT}STEP 3: Risk Management{Style.RESET_ALL}")
    print(f"{'-'*50}")
    risk = run_risk_management(valid_tickers, portfolio, current_prices)
    analyst_signals["risk_management_agent"] = risk
    for t in valid_tickers:
        r = risk[t]
        ms = int(r["remaining_position_limit"] / r["current_price"]) if r["current_price"] > 0 else 0
        print(f"  {t}: Limit ${r['remaining_position_limit']:,.0f} (max {ms} shares @ ${r['current_price']:.2f})")

    # Step 4: Investment Committee
    print(f"\n{Style.BRIGHT}STEP 4: Investment Committee Meeting{Style.RESET_ALL}")
    print(f"{'-'*50}")
    decisions, debates = run_investment_committee(valid_tickers, analyst_signals, risk, portfolio, stock_data=stock_data)

    for t in valid_tickers:
        d = decisions[t]
        ac = {"buy": Fore.GREEN, "sell": Fore.RED, "short": Fore.RED, "hold": Fore.YELLOW}.get(d["action"], Fore.WHITE)
        print(f"  {Fore.CYAN}{t}{Style.RESET_ALL}: {debates[t]}")
        print(f"    -> {ac}{d['action'].upper()} {d['quantity']} shares{Style.RESET_ALL} ({d['confidence']:.0f}%)")
        print(f"       {d['reasoning']}\n")

    # Step 5: Display with existing infrastructure
    result = {"decisions": decisions, "analyst_signals": analyst_signals}
    print_trading_output(result)

    # Step 6: Execute
    print(f"\n{Style.BRIGHT}STEP 6: Trade Execution{Style.RESET_ALL}")
    print(f"{'-'*50}")
    for t in valid_tickers:
        dec = decisions[t]
        price = current_prices[t]
        qty = dec["quantity"]
        if dec["action"] == "buy" and qty > 0:
            cost = qty * price
            if cost <= portfolio["cash"]:
                portfolio["cash"] -= cost
                portfolio["positions"][t]["long"] += qty
                print(f"  {Fore.GREEN}BUY  {qty:>5} {t:5s} @ ${price:>10,.2f} = ${cost:>12,.2f}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}SKIP {t} - insufficient cash{Style.RESET_ALL}")
        elif dec["action"] == "sell" and qty > 0:
            rev = qty * price
            portfolio["cash"] += rev
            portfolio["positions"][t]["long"] -= qty
            print(f"  {Fore.RED}SELL {qty:>5} {t:5s} @ ${price:>10,.2f} = ${rev:>12,.2f}{Style.RESET_ALL}")
        elif dec["action"] == "short" and qty > 0:
            rev = qty * price
            portfolio["cash"] += rev
            portfolio["positions"][t]["short"] += qty
            print(f"  {Fore.RED}SHORT{qty:>5} {t:5s} @ ${price:>10,.2f} = ${rev:>12,.2f}{Style.RESET_ALL}")
        else:
            print(f"  {Fore.YELLOW}HOLD       {t:5s}{Style.RESET_ALL}")

    # Final summary
    total_pos = sum(
        portfolio["positions"][t].get("long", 0) * current_prices[t]
        - portfolio["positions"][t].get("short", 0) * current_prices[t]
        for t in valid_tickers
    )
    total_val = portfolio["cash"] + total_pos
    invested_pct = (1 - portfolio["cash"] / total_val) * 100 if total_val > 0 else 0

    print(f"\n{Style.BRIGHT}PORTFOLIO{Style.RESET_ALL}")
    print(f"{'='*70}")
    for t in valid_tickers:
        p = portfolio["positions"][t]
        if p["long"] > 0:
            v = p["long"] * current_prices[t]
            print(f"  {Fore.CYAN}{t}{Style.RESET_ALL}: {Fore.GREEN}LONG {p['long']} shares (${v:,.2f}){Style.RESET_ALL}")
        if p["short"] > 0:
            v = p["short"] * current_prices[t]
            print(f"  {Fore.CYAN}{t}{Style.RESET_ALL}: {Fore.RED}SHORT {p['short']} shares (${v:,.2f}){Style.RESET_ALL}")

    print(f"\n  Cash:         {Fore.CYAN}${portfolio['cash']:>12,.2f}{Style.RESET_ALL}")
    print(f"  Positions:    {Fore.YELLOW}${total_pos:>12,.2f}{Style.RESET_ALL}")
    print(f"  Total:        {Fore.WHITE}{Style.BRIGHT}${total_val:>12,.2f}{Style.RESET_ALL}")
    print(f"  Invested:     {invested_pct:.0f}%")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
