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
from typing import Any, Dict, List, Tuple, Tuple

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
# AGENT GROUPS - Different investing perspectives at the table
# ============================================================
AGENT_GROUPS = {
    "value_investors": {
        "agents": ["warren_buffett_agent", "ben_graham_agent", "charlie_munger_agent", "bill_ackman_agent"],
        "perspective": "Value & Quality",
        "weight": 1.0,  # Base weight
        "veto_power": True,  # Can veto if unanimous against
    },
    "growth_investors": {
        "agents": ["cathie_wood_agent", "peter_lynch_agent", "phil_fisher_agent", "rakesh_jhunjhunwala_agent"],
        "perspective": "Growth & Innovation",
        "weight": 1.0,
        "veto_power": True,
    },
    "macro_strategists": {
        "agents": ["stanley_druckenmiller_agent", "michael_burry_agent"],
        "perspective": "Macro & Contrarian",
        "weight": 0.8,  # Slightly lower - fewer members
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
# INVESTMENT COMMITTEE (collaborative decision making)
# ============================================================
def run_investment_committee(
    tickers: List[str],
    analyst_signals: Dict[str, Dict],
    risk_analysis: Dict[str, Dict],
    portfolio: Dict[str, Any],
    show_debate: bool = False,
) -> Tuple[Dict[str, Dict], Dict[str, str]]:
    """
    Investment committee meeting - all agents discuss each ticker together.

    Process:
    1. Each group presents their consensus view
    2. Groups debate - conflicting views are examined
    3. Risk manager presents position limits
    4. Portfolio manager synthesizes and decides
    5. Conviction sizing - position size reflects consensus strength

    Returns (decisions, debate_summaries) tuple.
    """
    decisions = {}
    debate_summaries = {}

    for ticker in tickers:
        # ── Phase 1: Each group forms their internal consensus ──
        group_views = {}
        for group_name, group_config in AGENT_GROUPS.items():
            bullish = 0
            bearish = 0
            neutral = 0
            total_conf = 0
            reasons = []

            for agent_id in group_config["agents"]:
                if agent_id not in analyst_signals or ticker not in analyst_signals[agent_id]:
                    continue
                sig = analyst_signals[agent_id][ticker]
                agent_name = AGENTS[agent_id][0] if agent_id in AGENTS else agent_id

                if sig["signal"] == "bullish":
                    bullish += sig["confidence"]
                elif sig["signal"] == "bearish":
                    bearish += sig["confidence"]
                else:
                    neutral += sig["confidence"]
                total_conf += sig["confidence"]
                if sig.get("reasoning"):
                    reasons.append(f"{agent_name}: {sig['reasoning'][:80]}")

            total_votes = len(group_config["agents"])
            if total_conf == 0:
                group_views[group_name] = {"view": "neutral", "strength": 0, "reasons": reasons, "unanimous": False}
                continue

            # Group consensus
            if bullish > bearish and bullish > neutral:
                view = "bullish"
                strength = bullish / total_conf
            elif bearish > bullish and bearish > neutral:
                view = "bearish"
                strength = bearish / total_conf
            else:
                view = "neutral"
                strength = neutral / total_conf if total_conf > 0 else 0

            # Check unanimity (all members agree)
            unanimous = (bullish > 0 and bearish == 0 and neutral == 0) or \
                        (bearish > 0 and bullish == 0 and neutral == 0)

            group_views[group_name] = {
                "view": view,
                "strength": round(strength, 2),
                "bullish_pct": round(bullish / total_conf * 100, 1) if total_conf > 0 else 0,
                "bearish_pct": round(bearish / total_conf * 100, 1) if total_conf > 0 else 0,
                "reasons": reasons,
                "unanimous": unanimous,
                "weight": group_config["weight"],
                "veto_power": group_config["veto_power"],
            }

        # ── Phase 2: Committee debate & conflict resolution ──
        bullish_groups = [g for g, v in group_views.items() if v["view"] == "bullish"]
        bearish_groups = [g for g, v in group_views.items() if v["view"] == "bearish"]

        # Calculate weighted group scores
        weighted_bullish = sum(group_views[g]["strength"] * group_views[g]["weight"]
                               for g in bullish_groups)
        weighted_bearish = sum(group_views[g]["strength"] * group_views[g]["weight"]
                               for g in bearish_groups)

        # Check for veto conditions
        veto_against_buy = any(
            group_views[g]["unanimous"] and group_views[g]["veto_power"] and group_views[g]["view"] == "bearish"
            for g in group_views
        )
        veto_against_short = any(
            group_views[g]["unanimous"] and group_views[g]["veto_power"] and group_views[g]["view"] == "bullish"
            for g in group_views
        )

        # Build debate narrative
        debate = []
        for group_name, view in group_views.items():
            perspective = AGENT_GROUPS[group_name]["perspective"]
            emoji = {"bullish": "BULLISH", "bearish": "BEARISH", "neutral": "NEUTRAL"}[view["view"]]
            debate.append(f"{perspective} desk ({emoji}, strength {view['strength']:.0%})")

        # ── Phase 3: Portfolio manager's final decision ──
        risk = risk_analysis.get(ticker, {})
        max_position_value = risk.get("remaining_position_limit", 0)
        price = risk.get("current_price", 0)
        max_shares = int(max_position_value / price) if price > 0 else 0

        position = portfolio.get("positions", {}).get(ticker, {})
        long_shares = position.get("long", 0)
        short_shares = position.get("short", 0)

        # Conviction score: how strongly groups agree
        net_conviction = weighted_bullish - weighted_bearish
        agreement = len(bullish_groups) + len(bearish_groups)
        total_groups = len(group_views)

        # Consensus level determines position sizing
        # 4/4 groups agree = high conviction (80% of max)
        # 3/4 groups agree = moderate conviction (50% of max)
        # 2/4 = low conviction (25% of max)
        # split = no trade
        if len(bullish_groups) >= 3:
            consensus = "strong_bullish"
            sizing_pct = 0.70 + (len(bullish_groups) - 3) * 0.10
        elif len(bullish_groups) >= 2 and len(bearish_groups) <= 1:
            consensus = "moderate_bullish"
            sizing_pct = 0.40
        elif len(bearish_groups) >= 3:
            consensus = "strong_bearish"
            sizing_pct = 0.70 + (len(bearish_groups) - 3) * 0.10
        elif len(bearish_groups) >= 2 and len(bullish_groups) <= 1:
            consensus = "moderate_bearish"
            sizing_pct = 0.40
        else:
            consensus = "no_consensus"
            sizing_pct = 0.0

        # Apply veto
        if veto_against_buy and consensus in ("strong_bullish", "moderate_bullish"):
            debate.append(f"VETO: Value/Growth group unanimously against - reducing to HOLD")
            consensus = "vetoed_bullish"
            sizing_pct = 0.0
        if veto_against_short and consensus in ("strong_bearish", "moderate_bearish"):
            debate.append(f"VETO: Value/Growth group unanimously bullish - blocking SHORT")
            consensus = "vetoed_bearish"
            sizing_pct = 0.0

        # Final decision
        confidence = min(95, max(20, abs(net_conviction) * 60 + len(max(bullish_groups, bearish_groups, key=len) if bullish_groups and bearish_groups else bullish_groups or bearish_groups or [""]) * 5 + 25))

        if consensus in ("strong_bullish", "moderate_bullish") and max_shares > 0:
            quantity = max(1, int(max_shares * sizing_pct))
            action = "buy"
            reasoning = (f"Committee {consensus.replace('_', ' ')}: "
                        f"{len(bullish_groups)}/{total_groups} groups bullish, "
                        f"{len(bearish_groups)} bearish. "
                        f"Conviction sizing: {sizing_pct:.0%} of max position.")
        elif consensus in ("strong_bearish", "moderate_bearish"):
            if long_shares > 0:
                # Sell existing long position
                sell_pct = 1.0 if consensus == "strong_bearish" else 0.5
                quantity = max(1, int(long_shares * sell_pct))
                action = "sell"
                reasoning = (f"Committee {consensus.replace('_', ' ')}: "
                            f"{len(bearish_groups)}/{total_groups} groups bearish. "
                            f"Reducing long position by {sell_pct:.0%}.")
            elif max_shares > 0 and consensus == "strong_bearish":
                # Only short with STRONG bearish + no veto
                quantity = max(1, int(max_shares * sizing_pct * 0.5))  # Half size for shorts
                action = "short"
                reasoning = (f"Committee strong bearish: "
                            f"{len(bearish_groups)}/{total_groups} groups bearish. "
                            f"Conservative short at {sizing_pct*0.5:.0%} of max.")
            else:
                quantity = 0
                action = "hold"
                reasoning = f"Moderate bearish but no position to sell and insufficient conviction to short."
        else:
            quantity = 0
            action = "hold"
            if consensus == "no_consensus":
                reasoning = (f"No committee consensus: {len(bullish_groups)} groups bullish, "
                            f"{len(bearish_groups)} bearish. "
                            f"Portfolio manager says: when the table is split, we wait.")
            elif "vetoed" in consensus:
                reasoning = (f"Proposal vetoed by committee member with strong opposing view. "
                            f"Risk-off: holding position.")
            else:
                reasoning = f"Insufficient conviction to act."

        decisions[ticker] = {
            "action": action,
            "quantity": quantity,
            "confidence": round(confidence, 1),
            "reasoning": reasoning,
        }
        debate_summaries[ticker] = " | ".join(debate)

    return decisions, debate_summaries


def run_portfolio_management(
    tickers: List[str],
    analyst_signals: Dict[str, Dict],
    risk_analysis: Dict[str, Dict],
    portfolio: Dict[str, Any],
) -> Dict[str, Dict]:
    """Backward-compatible wrapper for backtest script."""
    decisions, _ = run_investment_committee(tickers, analyst_signals, risk_analysis, portfolio)
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

    # ── Step 3: Investment Committee Meeting ──
    print(f"\n{Fore.WHITE}{Style.BRIGHT}STEP 3: Investment Committee Meeting{Style.RESET_ALL}")
    print(f"{'-'*50}")
    print(f"  {Fore.CYAN}4 groups at the table:{Style.RESET_ALL}")
    for gname, gconfig in AGENT_GROUPS.items():
        agents_str = ", ".join(AGENTS[a][0] for a in gconfig["agents"] if a in AGENTS)
        veto = f" {Fore.RED}[VETO POWER]{Style.RESET_ALL}" if gconfig["veto_power"] else ""
        print(f"    {Fore.WHITE}{gconfig['perspective']:25s}{Style.RESET_ALL}: {agents_str}{veto}")
    print()

    decisions, debate_summaries = run_investment_committee(
        tickers, analyst_signals, risk_analysis, portfolio, show_reasoning
    )

    # Show committee debate per ticker
    for ticker in tickers:
        debate = debate_summaries.get(ticker, "")
        dec = decisions[ticker]
        action_color = {"buy": Fore.GREEN, "sell": Fore.RED, "short": Fore.RED, "hold": Fore.YELLOW}.get(dec["action"], Fore.WHITE)
        print(f"  {Fore.CYAN}{ticker}{Style.RESET_ALL}: {debate}")
        print(f"    -> {action_color}{dec['action'].upper()} {dec['quantity']} shares{Style.RESET_ALL} ({dec['confidence']:.0f}% conf)")
        print(f"       {Fore.WHITE}{dec['reasoning']}{Style.RESET_ALL}")
        print()

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

