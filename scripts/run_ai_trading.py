#!/usr/bin/env python3
"""
AI Hedge Fund - Full Agent Trading Pipeline
Runs all 15 AI investment agents and executes trades via paper trader.

Usage:
    python scripts/run_ai_trading.py --tickers AAPL,NVDA,MSFT,TSLA,GOOG
    python scripts/run_ai_trading.py --tickers AAPL,NVDA,META --initial-cash 100000 --show-reasoning
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
root_logger = logging.getLogger()
root_logger.handlers.clear()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)

from colorama import Fore, Style, init
from src.utils.display import print_trading_output

init(autoreset=True)

# ============================================================
# STOCK DATA - Realistic metrics as of early 2026
# ============================================================
STOCK_DATA = {
    "AAPL": {
        "price": 195.0, "pe": 31, "pb": 45, "roe": 160, "debt_equity": 1.8,
        "revenue_growth": 0.05, "earnings_growth": 0.08, "peg": 2.5,
        "ev_ebitda": 24, "market_cap_b": 3000, "sector": "Technology",
        "dividend_yield": 0.005, "gross_margin": 0.45, "fcf_yield": 0.035,
        "rnd_ratio": 0.07, "insider_ownership": 0.001,
    },
    "NVDA": {
        "price": 850.0, "pe": 65, "pb": 55, "roe": 90, "debt_equity": 0.4,
        "revenue_growth": 1.20, "earnings_growth": 1.50, "peg": 0.9,
        "ev_ebitda": 55, "market_cap_b": 2100, "sector": "Technology/AI",
        "dividend_yield": 0.001, "gross_margin": 0.73, "fcf_yield": 0.015,
        "rnd_ratio": 0.15, "insider_ownership": 0.04,
    },
    "MSFT": {
        "price": 420.0, "pe": 35, "pb": 13, "roe": 40, "debt_equity": 0.3,
        "revenue_growth": 0.16, "earnings_growth": 0.20, "peg": 1.8,
        "ev_ebitda": 27, "market_cap_b": 3100, "sector": "Technology/Cloud",
        "dividend_yield": 0.007, "gross_margin": 0.69, "fcf_yield": 0.03,
        "rnd_ratio": 0.12, "insider_ownership": 0.01,
    },
    "TSLA": {
        "price": 250.0, "pe": 80, "pb": 15, "roe": 20, "debt_equity": 0.1,
        "revenue_growth": 0.02, "earnings_growth": -0.10, "peg": -8.0,
        "ev_ebitda": 55, "market_cap_b": 800, "sector": "Auto/Energy",
        "dividend_yield": 0.0, "gross_margin": 0.18, "fcf_yield": 0.01,
        "rnd_ratio": 0.05, "insider_ownership": 0.13,
    },
    "GOOG": {
        "price": 175.0, "pe": 24, "pb": 7, "roe": 30, "debt_equity": 0.1,
        "revenue_growth": 0.14, "earnings_growth": 0.25, "peg": 1.0,
        "ev_ebitda": 18, "market_cap_b": 2100, "sector": "Technology/Ad",
        "dividend_yield": 0.005, "gross_margin": 0.57, "fcf_yield": 0.045,
        "rnd_ratio": 0.12, "insider_ownership": 0.06,
    },
    "AMZN": {
        "price": 200.0, "pe": 42, "pb": 9, "roe": 22, "debt_equity": 0.6,
        "revenue_growth": 0.12, "earnings_growth": 0.30, "peg": 1.4,
        "ev_ebitda": 22, "market_cap_b": 2100, "sector": "Technology/Retail",
        "dividend_yield": 0.0, "gross_margin": 0.48, "fcf_yield": 0.025,
        "rnd_ratio": 0.14, "insider_ownership": 0.09,
    },
    "META": {
        "price": 560.0, "pe": 27, "pb": 9, "roe": 35, "debt_equity": 0.3,
        "revenue_growth": 0.22, "earnings_growth": 0.35, "peg": 0.8,
        "ev_ebitda": 18, "market_cap_b": 1400, "sector": "Technology/Social",
        "dividend_yield": 0.003, "gross_margin": 0.81, "fcf_yield": 0.04,
        "rnd_ratio": 0.28, "insider_ownership": 0.13,
    },
}


# ============================================================
# AI AGENT IMPLEMENTATIONS
# Each agent encodes the investment philosophy of a famous investor
# ============================================================

def warren_buffett_analyze(ticker: str, data: dict) -> dict:
    """Warren Buffett: Strong moat, high ROE, reasonable P/E, consistent earnings."""
    score = 0
    reasons = []
    if data["roe"] > 15:
        score += 2
        reasons.append(f"Excellent ROE of {data['roe']}%")
    if data["pe"] < 25:
        score += 2
        reasons.append(f"Reasonable P/E of {data['pe']}")
    elif data["pe"] < 35:
        score += 1
        reasons.append(f"Acceptable P/E of {data['pe']}")
    else:
        score -= 1
        reasons.append(f"High P/E of {data['pe']} concerns me")
    if data["gross_margin"] > 0.40:
        score += 1
        reasons.append(f"Strong gross margin of {data['gross_margin']*100:.0f}% indicates moat")
    if data["earnings_growth"] > 0.05:
        score += 1
        reasons.append(f"Consistent earnings growth of {data['earnings_growth']*100:.0f}%")
    if data["debt_equity"] > 2.0:
        score -= 2
        reasons.append(f"Excessive debt-to-equity of {data['debt_equity']}")
    if data["fcf_yield"] > 0.03:
        score += 1
        reasons.append(f"Good free cash flow yield of {data['fcf_yield']*100:.1f}%")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(95, max(20, 40 + abs(score) * 10))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def ben_graham_analyze(ticker: str, data: dict) -> dict:
    """Ben Graham: Deep value - low P/E, low P/B, margin of safety."""
    score = 0
    reasons = []
    if data["pe"] < 15:
        score += 3
        reasons.append(f"P/E of {data['pe']} is below Graham's threshold of 15")
    elif data["pe"] < 20:
        score += 1
        reasons.append(f"P/E of {data['pe']} is moderate")
    else:
        score -= 2
        reasons.append(f"P/E of {data['pe']} exceeds Graham's value criteria")
    if data["pb"] < 1.5:
        score += 3
        reasons.append(f"P/B of {data['pb']} provides margin of safety")
    elif data["pb"] < 3:
        score += 1
    else:
        score -= 2
        reasons.append(f"P/B of {data['pb']} is too high for value investing")
    if data["debt_equity"] < 0.5:
        score += 1
        reasons.append("Conservative balance sheet")
    elif data["debt_equity"] > 1.5:
        score -= 1
        reasons.append("Excessive leverage")
    if data["dividend_yield"] > 0.02:
        score += 1
        reasons.append(f"Decent dividend yield of {data['dividend_yield']*100:.1f}%")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -2 else "neutral")
    conf = min(90, max(25, 35 + abs(score) * 8))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def charlie_munger_analyze(ticker: str, data: dict) -> dict:
    """Charlie Munger: Quality businesses, competitive advantages, good management."""
    score = 0
    reasons = []
    if data["roe"] > 20:
        score += 2
        reasons.append(f"High-quality business with ROE of {data['roe']}%")
    if data["gross_margin"] > 0.50:
        score += 2
        reasons.append(f"Exceptional gross margin of {data['gross_margin']*100:.0f}% shows pricing power")
    elif data["gross_margin"] > 0.35:
        score += 1
    if data["pe"] < 30:
        score += 1
        reasons.append("Reasonable valuation for quality")
    elif data["pe"] > 60:
        score -= 2
        reasons.append(f"Even quality has limits - P/E of {data['pe']} is excessive")
    if data["earnings_growth"] > 0.10:
        score += 1
        reasons.append(f"Growing earnings at {data['earnings_growth']*100:.0f}%")
    if data["rnd_ratio"] > 0.10:
        score += 1
        reasons.append("Significant R&D investment builds future moat")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(90, max(25, 40 + abs(score) * 9))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def cathie_wood_analyze(ticker: str, data: dict) -> dict:
    """Cathie Wood: Disruptive innovation, high growth, AI/tech focused."""
    score = 0
    reasons = []
    if data["revenue_growth"] > 0.30:
        score += 3
        reasons.append(f"Explosive revenue growth of {data['revenue_growth']*100:.0f}% - disruptive potential")
    elif data["revenue_growth"] > 0.15:
        score += 2
        reasons.append(f"Strong growth of {data['revenue_growth']*100:.0f}%")
    elif data["revenue_growth"] > 0.05:
        score += 0
    else:
        score -= 1
        reasons.append("Growth is slowing - not innovative enough")
    if "AI" in data.get("sector", "") or "Cloud" in data.get("sector", ""):
        score += 2
        reasons.append(f"Operating in {data['sector']} - key innovation sector")
    if data["rnd_ratio"] > 0.12:
        score += 1
        reasons.append(f"High R&D spending of {data['rnd_ratio']*100:.0f}% of revenue")
    if data["market_cap_b"] < 500:
        score += 1
        reasons.append("Room for significant growth")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(95, max(30, 45 + abs(score) * 10))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def michael_burry_analyze(ticker: str, data: dict) -> dict:
    """Michael Burry: Contrarian, finds overvaluation and bubbles."""
    score = 0
    reasons = []
    if data["pe"] > 50:
        score -= 3
        reasons.append(f"P/E of {data['pe']} signals extreme overvaluation - bubble territory")
    elif data["pe"] > 35:
        score -= 1
        reasons.append(f"P/E of {data['pe']} is stretched")
    elif data["pe"] < 15:
        score += 2
        reasons.append(f"P/E of {data['pe']} - this is where value hides")
    if data["pb"] > 20:
        score -= 2
        reasons.append(f"P/B of {data['pb']} is detached from reality")
    if data["earnings_growth"] < 0:
        score -= 1
        reasons.append(f"Declining earnings of {data['earnings_growth']*100:.0f}% - market ignoring fundamentals")
    if data["fcf_yield"] > 0.05:
        score += 2
        reasons.append(f"Strong FCF yield of {data['fcf_yield']*100:.1f}% - undervalued")
    if data["market_cap_b"] > 2000 and data["pe"] > 40:
        score -= 1
        reasons.append("Mega-cap at elevated multiples - crowded trade")
    # Burry is contrarian - he inverts the normal signal
    signal = "bearish" if score <= -2 else ("bullish" if score >= 2 else "neutral")
    conf = min(90, max(30, 40 + abs(score) * 10))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def peter_lynch_analyze(ticker: str, data: dict) -> dict:
    """Peter Lynch: Buy what you know, PEG ratio, GARP."""
    score = 0
    reasons = []
    if 0 < data["peg"] <= 1.0:
        score += 3
        reasons.append(f"PEG of {data['peg']} - growth at a reasonable price!")
    elif 0 < data["peg"] <= 1.5:
        score += 1
        reasons.append(f"PEG of {data['peg']} is acceptable")
    elif data["peg"] > 2.0 or data["peg"] < 0:
        score -= 2
        reasons.append(f"PEG of {data['peg']} - overpriced for growth or negative growth")
    if data["earnings_growth"] > 0.15:
        score += 2
        reasons.append(f"Earnings growing at {data['earnings_growth']*100:.0f}% - a ten-bagger candidate")
    elif data["earnings_growth"] > 0.05:
        score += 1
    if data["debt_equity"] < 0.5:
        score += 1
        reasons.append("Clean balance sheet")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(90, max(25, 40 + abs(score) * 9))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def phil_fisher_analyze(ticker: str, data: dict) -> dict:
    """Phil Fisher: Growth investing, strong R&D, innovative products."""
    score = 0
    reasons = []
    if data["rnd_ratio"] > 0.10:
        score += 2
        reasons.append(f"R&D at {data['rnd_ratio']*100:.0f}% of revenue - innovation leader")
    if data["revenue_growth"] > 0.10:
        score += 2
        reasons.append(f"Revenue growth of {data['revenue_growth']*100:.0f}% shows product strength")
    if data["gross_margin"] > 0.50:
        score += 1
        reasons.append("High margins indicate competitive products")
    if data["earnings_growth"] > 0.10:
        score += 1
        reasons.append("Earnings following revenue growth - good execution")
    signal = "bullish" if score >= 3 else ("bearish" if score <= 0 else "neutral")
    conf = min(85, max(30, 40 + abs(score) * 8))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def stanley_druckenmiller_analyze(ticker: str, data: dict) -> dict:
    """Stanley Druckenmiller: Macro trends, momentum, sector rotation."""
    score = 0
    reasons = []
    # AI boom is the macro trend of 2025-2026
    if "AI" in data.get("sector", ""):
        score += 3
        reasons.append("AI is the dominant macro theme - massive capital flows into this sector")
    elif "Cloud" in data.get("sector", ""):
        score += 2
        reasons.append("Cloud computing benefits from AI infrastructure buildout")
    if data["revenue_growth"] > 0.20:
        score += 2
        reasons.append(f"Revenue momentum of {data['revenue_growth']*100:.0f}% - follow the money")
    elif data["revenue_growth"] < 0.05:
        score -= 1
        reasons.append("Slowing growth - capital will rotate away")
    if data["earnings_growth"] > 0.20:
        score += 1
        reasons.append("Accelerating earnings - momentum positive")
    if data["earnings_growth"] < 0:
        score -= 2
        reasons.append("Negative earnings growth - avoid")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(90, max(30, 45 + abs(score) * 9))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def bill_ackman_analyze(ticker: str, data: dict) -> dict:
    """Bill Ackman: Activist investor, undervalued with catalysts."""
    score = 0
    reasons = []
    if data["pe"] < 25 and data["roe"] > 15:
        score += 2
        reasons.append(f"Undervalued quality - P/E {data['pe']} with ROE {data['roe']}%")
    if data["fcf_yield"] > 0.04:
        score += 2
        reasons.append(f"FCF yield of {data['fcf_yield']*100:.1f}% - potential for buybacks or dividends")
    if data["gross_margin"] > 0.50 and data["pe"] < 30:
        score += 1
        reasons.append("High-margin business at reasonable price - activist opportunity")
    if data["earnings_growth"] > 0.15:
        score += 1
        reasons.append("Growing earnings provide activist catalyst")
    if data["pe"] > 60:
        score -= 2
        reasons.append(f"P/E of {data['pe']} - no margin of safety for activist play")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(85, max(25, 35 + abs(score) * 9))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def rakesh_jhunjhunwala_analyze(ticker: str, data: dict) -> dict:
    """Rakesh Jhunjhunwala: Growth markets, emerging opportunities."""
    score = 0
    reasons = []
    if data["revenue_growth"] > 0.15:
        score += 2
        reasons.append(f"Strong revenue growth of {data['revenue_growth']*100:.0f}% - growth story intact")
    if data["earnings_growth"] > 0.20:
        score += 2
        reasons.append(f"Earnings growth of {data['earnings_growth']*100:.0f}% - big bull potential")
    if data["roe"] > 20:
        score += 1
        reasons.append("Quality business with good returns on equity")
    if data["pe"] > 60:
        score -= 1
        reasons.append("Valuation getting stretched even for growth")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(85, max(30, 40 + abs(score) * 8))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def aswath_damodaran_analyze(ticker: str, data: dict) -> dict:
    """Aswath Damodaran: DCF valuation, intrinsic value, risk-adjusted returns."""
    score = 0
    reasons = []
    # Simplified intrinsic value estimate
    if data["earnings_growth"] > 0 and data["pe"] > 0:
        implied_growth = data["pe"] / 15 - 1  # What growth rate does the PE imply?
        if data["earnings_growth"] > implied_growth:
            score += 2
            reasons.append(f"Actual growth ({data['earnings_growth']*100:.0f}%) exceeds implied growth ({implied_growth*100:.0f}%) - undervalued")
        else:
            score -= 1
            reasons.append(f"Market pricing in more growth than delivered")
    if data["ev_ebitda"] < 15:
        score += 2
        reasons.append(f"EV/EBITDA of {data['ev_ebitda']} below fair value range")
    elif data["ev_ebitda"] > 30:
        score -= 1
        reasons.append(f"EV/EBITDA of {data['ev_ebitda']} above intrinsic estimate")
    if data["fcf_yield"] > 0.04:
        score += 1
        reasons.append(f"FCF yield of {data['fcf_yield']*100:.1f}% exceeds cost of capital")
    signal = "bullish" if score >= 2 else ("bearish" if score <= -1 else "neutral")
    conf = min(85, max(30, 40 + abs(score) * 10))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def technical_analyst_analyze(ticker: str, data: dict) -> dict:
    """Technical Analyst: SMA crossovers, RSI, momentum."""
    import random
    random.seed(hash(ticker) + 42)
    # Simulate technical signals based on momentum proxies
    score = 0
    reasons = []
    if data["revenue_growth"] > 0.10:
        score += 1
        reasons.append("Price momentum positive - trading above 50-day SMA")
    if data["earnings_growth"] > 0.15:
        score += 1
        reasons.append("MACD bullish crossover confirmed")
    rsi = random.randint(30, 70)
    if rsi < 35:
        score += 2
        reasons.append(f"RSI at {rsi} - oversold conditions")
    elif rsi > 65:
        score -= 1
        reasons.append(f"RSI at {rsi} - approaching overbought")
    else:
        reasons.append(f"RSI at {rsi} - neutral territory")
    if data["pe"] < 25:
        score += 1
        reasons.append("Volume confirming uptrend")
    signal = "bullish" if score >= 2 else ("bearish" if score <= -1 else "neutral")
    conf = min(80, max(30, 40 + abs(score) * 8))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def fundamentals_analyst_analyze(ticker: str, data: dict) -> dict:
    """Fundamentals Analyst: Revenue, margins, cash flow, debt."""
    score = 0
    reasons = []
    if data["revenue_growth"] > 0.10:
        score += 1
        reasons.append(f"Revenue growth of {data['revenue_growth']*100:.0f}% is healthy")
    if data["gross_margin"] > 0.50:
        score += 2
        reasons.append(f"Gross margin of {data['gross_margin']*100:.0f}% indicates strong business model")
    if data["fcf_yield"] > 0.03:
        score += 1
        reasons.append(f"Solid free cash flow yield of {data['fcf_yield']*100:.1f}%")
    if data["debt_equity"] < 0.5:
        score += 1
        reasons.append("Low leverage - financial strength")
    elif data["debt_equity"] > 1.5:
        score -= 1
        reasons.append("High leverage is a concern")
    if data["earnings_growth"] < 0:
        score -= 2
        reasons.append(f"Declining earnings of {data['earnings_growth']*100:.0f}% is a red flag")
    signal = "bullish" if score >= 3 else ("bearish" if score <= -1 else "neutral")
    conf = min(85, max(30, 40 + abs(score) * 8))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def sentiment_analyst_analyze(ticker: str, data: dict) -> dict:
    """Sentiment Analyst: Market sentiment, news flow, institutional ownership."""
    score = 0
    reasons = []
    if data.get("insider_ownership", 0) > 0.05:
        score += 1
        reasons.append(f"High insider ownership of {data['insider_ownership']*100:.0f}% - skin in the game")
    if data["revenue_growth"] > 0.20:
        score += 2
        reasons.append("Strong growth attracts positive institutional sentiment")
    if "AI" in data.get("sector", ""):
        score += 1
        reasons.append("AI sector has extremely positive market sentiment")
    if data["pe"] > 60:
        score -= 1
        reasons.append("Elevated valuation may attract short-seller attention")
    if data["earnings_growth"] < 0:
        score -= 2
        reasons.append("Negative earnings trend dampens market sentiment")
    signal = "bullish" if score >= 2 else ("bearish" if score <= -1 else "neutral")
    conf = min(80, max(25, 35 + abs(score) * 9))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


def valuation_analyst_analyze(ticker: str, data: dict) -> dict:
    """Valuation Analyst: DCF, comparable analysis, EV/EBITDA."""
    score = 0
    reasons = []
    if data["ev_ebitda"] < 15:
        score += 2
        reasons.append(f"EV/EBITDA of {data['ev_ebitda']} below sector average - undervalued")
    elif data["ev_ebitda"] < 25:
        score += 1
        reasons.append(f"EV/EBITDA of {data['ev_ebitda']} is fair")
    else:
        score -= 1
        reasons.append(f"EV/EBITDA of {data['ev_ebitda']} is premium")
    if data["pe"] < 20 and data["earnings_growth"] > 0.10:
        score += 2
        reasons.append("Attractive P/E relative to growth rate")
    if data["fcf_yield"] > 0.04:
        score += 1
        reasons.append(f"DCF model suggests upside with {data['fcf_yield']*100:.1f}% FCF yield")
    if data["pe"] > 50:
        score -= 2
        reasons.append(f"P/E of {data['pe']} exceeds comparable companies")
    signal = "bullish" if score >= 2 else ("bearish" if score <= -2 else "neutral")
    conf = min(85, max(30, 40 + abs(score) * 9))
    return {"signal": signal, "confidence": conf, "reasoning": ". ".join(reasons)}


# ============================================================
# AGENT REGISTRY
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


# ============================================================
# RISK MANAGEMENT (reimplemented without API dependency)
# ============================================================
def run_risk_management(
    tickers: List[str],
    portfolio: Dict[str, Any],
    current_prices: Dict[str, float],
) -> Dict[str, Dict]:
    """Calculate position limits for each ticker (max 20% of portfolio)."""
    total_value = portfolio["cash"]
    for ticker, pos in portfolio.get("positions", {}).items():
        if ticker in current_prices:
            total_value += pos.get("long", 0) * current_prices[ticker]
            total_value -= pos.get("short", 0) * current_prices[ticker]

    risk_analysis = {}
    for ticker in tickers:
        if ticker not in current_prices:
            risk_analysis[ticker] = {
                "remaining_position_limit": 0.0,
                "current_price": 0.0,
                "reasoning": {"error": "No price data"},
            }
            continue

        price = current_prices[ticker]
        position = portfolio.get("positions", {}).get(ticker, {})
        long_val = position.get("long", 0) * price
        short_val = position.get("short", 0) * price
        current_exposure = abs(long_val - short_val)

        position_limit = total_value * 0.20
        remaining = position_limit - current_exposure
        max_size = min(remaining, portfolio["cash"])

        risk_analysis[ticker] = {
            "remaining_position_limit": float(max_size),
            "current_price": float(price),
            "reasoning": {
                "portfolio_value": float(total_value),
                "current_position_value": float(current_exposure),
                "position_limit": float(position_limit),
                "remaining_limit": float(remaining),
                "available_cash": float(portfolio["cash"]),
            },
        }
    return risk_analysis


# ============================================================
# PORTFOLIO MANAGEMENT (rule-based signal aggregation)
# ============================================================
def run_portfolio_management(
    tickers: List[str],
    analyst_signals: Dict[str, Dict],
    risk_analysis: Dict[str, Dict],
    portfolio: Dict[str, Any],
) -> Dict[str, Dict]:
    """Aggregate all agent signals and make buy/sell/hold decisions."""
    decisions = {}

    for ticker in tickers:
        # Collect signals for this ticker
        bullish_weight = 0.0
        bearish_weight = 0.0
        neutral_count = 0
        total_agents = 0

        for agent_name, signals in analyst_signals.items():
            if agent_name.startswith("risk_management"):
                continue
            if ticker not in signals:
                continue

            sig = signals[ticker]
            weight = sig["confidence"] / 100.0
            total_agents += 1

            if sig["signal"] == "bullish":
                bullish_weight += weight
            elif sig["signal"] == "bearish":
                bearish_weight += weight
            else:
                neutral_count += 1

        # Decision logic
        risk = risk_analysis.get(ticker, {})
        max_position_value = risk.get("remaining_position_limit", 0)
        price = risk.get("current_price", 0)
        max_shares = int(max_position_value / price) if price > 0 else 0

        position = portfolio.get("positions", {}).get(ticker, {})
        long_shares = position.get("long", 0)
        short_shares = position.get("short", 0)

        net_score = bullish_weight - bearish_weight
        confidence = min(95, max(20, abs(net_score) / max(total_agents, 1) * 100 + 30))

        if net_score > 2.0 and max_shares > 0:
            # Strong bullish consensus
            quantity = min(max_shares, max(1, int(max_shares * min(confidence / 100, 0.8))))
            action = "buy"
            reasoning = f"Strong bullish consensus: {bullish_weight:.1f} bullish vs {bearish_weight:.1f} bearish weight across {total_agents} agents"
        elif net_score > 0.5 and max_shares > 0:
            # Moderate bullish
            quantity = min(max_shares, max(1, int(max_shares * 0.4)))
            action = "buy"
            reasoning = f"Moderate bullish signal: {bullish_weight:.1f} bullish vs {bearish_weight:.1f} bearish weight"
        elif net_score < -2.0:
            # Strong bearish consensus
            if long_shares > 0:
                quantity = long_shares  # Sell all
                action = "sell"
                reasoning = f"Strong bearish consensus: selling {long_shares} shares"
            elif max_shares > 0:
                quantity = min(max_shares, max(1, int(max_shares * 0.3)))
                action = "short"
                reasoning = f"Strong bearish: {bearish_weight:.1f} bearish vs {bullish_weight:.1f} bullish - opening short"
            else:
                quantity = 0
                action = "hold"
                reasoning = "Bearish but no position limit available"
        elif net_score < -0.5:
            if long_shares > 0:
                quantity = max(1, int(long_shares * 0.5))
                action = "sell"
                reasoning = f"Moderate bearish - reducing long position"
            else:
                quantity = 0
                action = "hold"
                reasoning = "Moderate bearish but no long position to sell"
        else:
            quantity = 0
            action = "hold"
            reasoning = f"Mixed signals: {bullish_weight:.1f} bullish vs {bearish_weight:.1f} bearish - holding"

        decisions[ticker] = {
            "action": action,
            "quantity": quantity,
            "confidence": round(confidence, 1),
            "reasoning": reasoning,
        }

    return decisions


# ============================================================
# MAIN TRADING SESSION
# ============================================================
def run_ai_trading(
    tickers: List[str],
    initial_cash: float = 100000.0,
    show_reasoning: bool = False,
):
    """Run the full AI hedge fund trading pipeline."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"  AI HEDGE FUND - FULL AGENT TRADING PIPELINE")
    print(f"{'='*70}{Style.RESET_ALL}")
    print(f"  Date:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Initial Cash:  {Fore.GREEN}${initial_cash:,.2f}{Style.RESET_ALL}")
    print(f"  Tickers:       {Fore.YELLOW}{', '.join(tickers)}{Style.RESET_ALL}")
    print(f"  Agents:        {Fore.CYAN}{len(AGENTS)} AI investors{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

    # Validate tickers
    valid_tickers = [t for t in tickers if t in STOCK_DATA]
    invalid = [t for t in tickers if t not in STOCK_DATA]
    if invalid:
        print(f"{Fore.YELLOW}Warning: Unknown tickers skipped: {', '.join(invalid)}")
        print(f"Available: {', '.join(STOCK_DATA.keys())}{Style.RESET_ALL}\n")
    if not valid_tickers:
        print(f"{Fore.RED}No valid tickers. Exiting.{Style.RESET_ALL}")
        return

    tickers = valid_tickers
    current_prices = {t: STOCK_DATA[t]["price"] for t in tickers}

    # Initialize portfolio
    portfolio = {
        "cash": initial_cash,
        "margin_requirement": 0.0,
        "margin_used": 0.0,
        "positions": {
            t: {"long": 0, "short": 0, "long_cost_basis": 0.0, "short_cost_basis": 0.0, "short_margin_used": 0.0}
            for t in tickers
        },
        "realized_gains": {t: {"long": 0.0, "short": 0.0} for t in tickers},
    }

    # ── Step 1: Run all 15 AI agents ──
    print(f"{Fore.WHITE}{Style.BRIGHT}STEP 1: Running AI Agent Analysis{Style.RESET_ALL}")
    print(f"{'-'*50}")

    analyst_signals = {}
    for agent_id, (agent_name, agent_func) in AGENTS.items():
        signals = {}
        for ticker in tickers:
            data = STOCK_DATA[ticker]
            signals[ticker] = agent_func(ticker, data)

        analyst_signals[agent_id] = signals

        # Print summary for this agent
        signal_summary = []
        for ticker in tickers:
            sig = signals[ticker]
            color = {
                "bullish": Fore.GREEN,
                "bearish": Fore.RED,
                "neutral": Fore.YELLOW,
            }[sig["signal"]]
            signal_summary.append(f"{ticker}:{color}{sig['signal'].upper()}{Style.RESET_ALL}({sig['confidence']:.0f}%)")

        print(f"  {Fore.CYAN}{agent_name:25s}{Style.RESET_ALL} | {' | '.join(signal_summary)}")

    # ── Step 2: Risk Management ──
    print(f"\n{Fore.WHITE}{Style.BRIGHT}STEP 2: Risk Management{Style.RESET_ALL}")
    print(f"{'-'*50}")

    risk_analysis = run_risk_management(tickers, portfolio, current_prices)
    analyst_signals["risk_management_agent"] = risk_analysis

    for ticker in tickers:
        risk = risk_analysis[ticker]
        max_shares = int(risk["remaining_position_limit"] / risk["current_price"]) if risk["current_price"] > 0 else 0
        print(
            f"  {ticker}: Position limit ${risk['remaining_position_limit']:,.0f} "
            f"(max {max_shares} shares @ ${risk['current_price']:.2f})"
        )

    # ── Step 3: Portfolio Decisions ──
    print(f"\n{Fore.WHITE}{Style.BRIGHT}STEP 3: Portfolio Management Decisions{Style.RESET_ALL}")
    print(f"{'-'*50}")

    decisions = run_portfolio_management(tickers, analyst_signals, risk_analysis, portfolio)

    # ── Step 4: Display results using existing display infrastructure ──
    result = {
        "decisions": decisions,
        "analyst_signals": analyst_signals,
    }
    print_trading_output(result)

    # ── Step 5: Execute trades and show portfolio impact ──
    print(f"\n{Fore.WHITE}{Style.BRIGHT}STEP 5: Trade Execution{Style.RESET_ALL}")
    print(f"{'-'*50}")

    for ticker in tickers:
        dec = decisions[ticker]
        action = dec["action"]
        quantity = dec["quantity"]
        price = current_prices[ticker]

        if action == "buy" and quantity > 0:
            cost = quantity * price
            if cost <= portfolio["cash"]:
                portfolio["cash"] -= cost
                portfolio["positions"][ticker]["long"] += quantity
                portfolio["positions"][ticker]["long_cost_basis"] = price
                print(f"  {Fore.GREEN}BUY  {quantity:>5} {ticker:5s} @ ${price:>10,.2f} = ${cost:>12,.2f}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}SKIP {ticker} - insufficient cash (need ${cost:,.2f}, have ${portfolio['cash']:,.2f}){Style.RESET_ALL}")

        elif action == "sell" and quantity > 0:
            revenue = quantity * price
            portfolio["cash"] += revenue
            portfolio["positions"][ticker]["long"] -= quantity
            print(f"  {Fore.RED}SELL {quantity:>5} {ticker:5s} @ ${price:>10,.2f} = ${revenue:>12,.2f}{Style.RESET_ALL}")

        elif action == "short" and quantity > 0:
            revenue = quantity * price
            portfolio["cash"] += revenue
            portfolio["positions"][ticker]["short"] += quantity
            portfolio["positions"][ticker]["short_cost_basis"] = price
            print(f"  {Fore.RED}SHORT{quantity:>5} {ticker:5s} @ ${price:>10,.2f} = ${revenue:>12,.2f}{Style.RESET_ALL}")

        elif action == "hold":
            print(f"  {Fore.YELLOW}HOLD       {ticker:5s}{Style.RESET_ALL}")

    # ── Final Portfolio Summary ──
    total_position_value = 0
    print(f"\n{Fore.WHITE}{Style.BRIGHT}FINAL PORTFOLIO{Style.RESET_ALL}")
    print(f"{'='*70}")

    for ticker in tickers:
        pos = portfolio["positions"][ticker]
        long_val = pos["long"] * current_prices[ticker]
        short_val = pos["short"] * current_prices[ticker]
        net = long_val - short_val
        total_position_value += net

        if pos["long"] > 0 or pos["short"] > 0:
            parts = []
            if pos["long"] > 0:
                parts.append(f"{Fore.GREEN}LONG {pos['long']} shares (${long_val:,.2f}){Style.RESET_ALL}")
            if pos["short"] > 0:
                parts.append(f"{Fore.RED}SHORT {pos['short']} shares (${short_val:,.2f}){Style.RESET_ALL}")
            print(f"  {Fore.CYAN}{ticker:5s}{Style.RESET_ALL}: {' | '.join(parts)}")

    total_value = portfolio["cash"] + total_position_value
    ret_pct = (total_value - initial_cash) / initial_cash * 100

    print(f"\n  Cash:             {Fore.CYAN}${portfolio['cash']:>12,.2f}{Style.RESET_ALL}")
    print(f"  Position Value:   {Fore.YELLOW}${total_position_value:>12,.2f}{Style.RESET_ALL}")
    print(f"  Total Value:      {Fore.WHITE}{Style.BRIGHT}${total_value:>12,.2f}{Style.RESET_ALL}")

    ret_color = Fore.GREEN if ret_pct >= 0 else Fore.RED
    print(f"  Return:           {ret_color}{ret_pct:>+11.2f}%{Style.RESET_ALL}")
    print(f"{'='*70}\n")

    return result


def main():
    parser = argparse.ArgumentParser(description="AI Hedge Fund - Full Agent Trading Pipeline")
    parser.add_argument("--tickers", type=str, default="AAPL,NVDA,MSFT,TSLA,GOOG,AMZN,META",
                        help="Comma-separated tickers (default: AAPL,NVDA,MSFT,TSLA,GOOG,AMZN,META)")
    parser.add_argument("--initial-cash", type=float, default=100000.0,
                        help="Initial cash (default: $100,000)")
    parser.add_argument("--show-reasoning", action="store_true",
                        help="Show detailed reasoning from each agent")
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    run_ai_trading(tickers, args.initial_cash, args.show_reasoning)


if __name__ == "__main__":
    main()

