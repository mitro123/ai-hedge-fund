"""
World Intelligence - Real-time global market intelligence.
Tracks everything agents need: macro, sectors, sentiment, central banks, news.
All data from Yahoo Finance - no API keys required.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class WorldIntelligence:
    """
    Provides real-time global context for investment decisions.
    Agents see the FULL picture: macro, sectors, sentiment, news.
    """

    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def _fetch(self, symbol: str, period: str = "3mo") -> pd.DataFrame:
        """Cached fetch."""
        key = f"{symbol}_{period}"
        if key not in self._cache:
            try:
                self._cache[key] = yf.Ticker(symbol).history(period=period)
            except Exception:
                self._cache[key] = pd.DataFrame()
        return self._cache[key]

    def get_full_context(self) -> Dict[str, Any]:
        """Get complete world intelligence snapshot."""
        return {
            "macro": self.get_macro_data(),
            "sectors": self.get_sector_rotation(),
            "yield_curve": self.get_yield_curve(),
            "fear_greed": self.get_fear_greed(),
            "commodities": self.get_commodities(),
            "market_regime": self.detect_market_regime(),
            "timestamp": datetime.now().isoformat(),
        }

    def get_macro_data(self) -> Dict[str, Any]:
        """Central bank rates, inflation proxies, dollar strength."""
        macro = {}

        # Fed funds proxy (13-week T-bill)
        h = self._fetch("^IRX", "5d")
        macro["fed_funds_proxy"] = round(float(h["Close"].iloc[-1]), 2) if not h.empty else None

        # 10-Year Treasury
        h = self._fetch("^TNX", "1y")
        if not h.empty:
            macro["us_10y"] = round(float(h["Close"].iloc[-1]), 2)
            macro["us_10y_3m_ago"] = round(float(h["Close"].iloc[-63]), 2) if len(h) > 63 else None
            macro["rates_direction"] = "rising" if macro["us_10y"] > (macro.get("us_10y_3m_ago") or macro["us_10y"]) else "falling"

        # Dollar index
        h = self._fetch("DX-Y.NYB", "6mo")
        if not h.empty:
            macro["dollar_index"] = round(float(h["Close"].iloc[-1]), 2)
            macro["dollar_6m_change"] = round(float(h["Close"].iloc[-1] / h["Close"].iloc[0] - 1), 4)
            macro["dollar_trend"] = "strengthening" if macro["dollar_6m_change"] > 0.02 else ("weakening" if macro["dollar_6m_change"] < -0.02 else "stable")

        return macro

    def get_sector_rotation(self) -> Dict[str, Dict]:
        """Real-time sector performance - which sectors are leading/lagging."""
        sectors = {
            "XLK": "Technology", "XLF": "Financials", "XLV": "Healthcare",
            "XLE": "Energy", "XLY": "Consumer Disc", "XLP": "Consumer Staples",
            "XLI": "Industrials", "XLU": "Utilities", "XLRE": "Real Estate",
        }

        results = {}
        for etf, name in sectors.items():
            h = self._fetch(etf, "6mo")
            if not h.empty and len(h) > 20:
                ret_1m = float(h["Close"].iloc[-1] / h["Close"].iloc[-21] - 1) if len(h) > 21 else 0
                ret_3m = float(h["Close"].iloc[-1] / h["Close"].iloc[-63] - 1) if len(h) > 63 else 0
                sma50 = float(h["Close"].rolling(50).mean().iloc[-1]) if len(h) >= 50 else float(h["Close"].mean())
                above_sma50 = float(h["Close"].iloc[-1]) > sma50

                results[name] = {
                    "etf": etf,
                    "return_1m": round(ret_1m, 4),
                    "return_3m": round(ret_3m, 4),
                    "above_sma50": above_sma50,
                    "trend": "bullish" if ret_3m > 0.05 and above_sma50 else ("bearish" if ret_3m < -0.05 else "neutral"),
                }

        # Sort by 3m return
        results = dict(sorted(results.items(), key=lambda x: x[1]["return_3m"], reverse=True))
        return results

    def get_yield_curve(self) -> Dict[str, Any]:
        """Yield curve shape - predictor of recession/expansion."""
        yields = {}
        for sym, tenor in [("^IRX", "3M"), ("^FVX", "5Y"), ("^TNX", "10Y"), ("^TYX", "30Y")]:
            h = self._fetch(sym, "5d")
            if not h.empty:
                yields[tenor] = round(float(h["Close"].iloc[-1]), 2)

        # Yield curve analysis
        spread_10y_3m = (yields.get("10Y", 0) or 0) - (yields.get("3M", 0) or 0)
        spread_10y_5y = (yields.get("10Y", 0) or 0) - (yields.get("5Y", 0) or 0)

        return {
            "yields": yields,
            "spread_10y_3m": round(spread_10y_3m, 2),
            "inverted": spread_10y_3m < 0,
            "interpretation": (
                "INVERTED - recession signal" if spread_10y_3m < -0.5 else
                "FLAT - late cycle" if abs(spread_10y_3m) < 0.3 else
                "NORMAL - expansion" if spread_10y_3m > 0.5 else "TRANSITIONING"
            ),
        }

    def get_fear_greed(self) -> Dict[str, Any]:
        """Market fear/greed indicators from VIX and put/call."""
        vix = self._fetch("^VIX", "3mo")
        if vix.empty:
            return {"vix": None, "regime": "unknown"}

        current = float(vix["Close"].iloc[-1])
        avg_30d = float(vix["Close"].tail(21).mean())
        high_30d = float(vix["Close"].tail(21).max())
        low_30d = float(vix["Close"].tail(21).min())

        if current > 30:
            regime = "extreme_fear"
        elif current > 25:
            regime = "fear"
        elif current > 20:
            regime = "caution"
        elif current > 15:
            regime = "neutral"
        elif current > 12:
            regime = "greed"
        else:
            regime = "extreme_greed"

        return {
            "vix": round(current, 2),
            "vix_30d_avg": round(avg_30d, 2),
            "vix_30d_range": [round(low_30d, 2), round(high_30d, 2)],
            "regime": regime,
            "vix_trend": "rising" if current > avg_30d * 1.1 else ("falling" if current < avg_30d * 0.9 else "stable"),
            "interpretation": (
                "PANIC - potential buying opportunity for contrarians" if regime == "extreme_fear" else
                "FEAR - market stressed, defensive posture" if regime == "fear" else
                "CAUTIOUS - elevated risk" if regime == "caution" else
                "COMPLACENT - watch for surprises" if regime in ("greed", "extreme_greed") else
                "NORMAL - standard volatility"
            ),
        }

    def get_commodities(self) -> Dict[str, Dict]:
        """Key commodity prices and trends."""
        commodities = {
            "Gold": "GC=F", "Oil (WTI)": "CL=F", "Silver": "SI=F",
            "Copper": "HG=F", "Bitcoin": "BTC-USD",
        }

        results = {}
        for name, sym in commodities.items():
            h = self._fetch(sym, "6mo")
            if not h.empty and len(h) > 20:
                price = float(h["Close"].iloc[-1])
                ret_1m = float(h["Close"].iloc[-1] / h["Close"].iloc[-21] - 1) if len(h) > 21 else 0
                ret_3m = float(h["Close"].iloc[-1] / h["Close"].iloc[0] - 1)
                results[name] = {
                    "price": round(price, 2),
                    "return_1m": round(ret_1m, 4),
                    "return_3m": round(ret_3m, 4),
                    "trend": "bullish" if ret_3m > 0.05 else ("bearish" if ret_3m < -0.05 else "neutral"),
                }

        return results

    def detect_market_regime(self) -> Dict[str, Any]:
        """Comprehensive market regime detection."""
        spy = self._fetch("SPY", "1y")
        if spy.empty or len(spy) < 200:
            return {"regime": "unknown", "confidence": 0}

        close = spy["Close"]
        current = float(close.iloc[-1])
        sma50 = float(close.rolling(50).mean().iloc[-1])
        sma200 = float(close.rolling(200).mean().iloc[-1])
        ret_3m = float(close.iloc[-1] / close.iloc[-63] - 1) if len(close) > 63 else 0
        ret_6m = float(close.iloc[-1] / close.iloc[-126] - 1) if len(close) > 126 else 0

        # Regime detection
        if current > sma50 > sma200 and ret_3m > 0.05:
            regime = "strong_bull"
            recommendation = "Aggressive: max growth + unicorns, min defensive"
        elif current > sma200 and sma50 > sma200:
            regime = "bull"
            recommendation = "Growth-tilted: overweight growth, normal unicorns"
        elif current > sma200 and sma50 < sma200:
            regime = "recovery"
            recommendation = "Transitioning: balanced with early-cycle tilt"
        elif current < sma50 and current > sma200:
            regime = "correction"
            recommendation = "Defensive: increase core + defensive, reduce unicorns"
        elif current < sma200 and ret_3m < -0.10:
            regime = "bear"
            recommendation = "Risk-off: max defensive + cash, min growth + unicorns"
        else:
            regime = "sideways"
            recommendation = "Balanced: equal weight all categories"

        # Confidence based on signal alignment
        signals = [current > sma50, current > sma200, sma50 > sma200, ret_3m > 0, ret_6m > 0]
        bull_signals = sum(signals)
        confidence = abs(bull_signals - 2.5) / 2.5  # 0=split, 1=unanimous

        return {
            "regime": regime,
            "confidence": round(confidence, 2),
            "spy_price": round(current, 2),
            "spy_sma50": round(sma50, 2),
            "spy_sma200": round(sma200, 2),
            "spy_3m_return": round(ret_3m, 4),
            "spy_6m_return": round(ret_6m, 4),
            "recommendation": recommendation,
        }

    def get_company_news_sentiment(self, ticker: str) -> Dict[str, Any]:
        """Get latest news for a specific company."""
        try:
            t = yf.Ticker(ticker)
            news = t.news or []

            # Analyze headlines
            positive_words = {"beat", "surge", "rally", "growth", "profit", "upgrade", "record", "innovation", "launch", "deal", "acquire", "partnership"}
            negative_words = {"miss", "decline", "loss", "lawsuit", "investigation", "downgrade", "layoff", "cut", "warning", "recall", "fraud", "bankruptcy"}

            pos_count = neg_count = 0
            headlines = []
            for n in news[:10]:
                title = (n.get("title") or "").lower()
                headlines.append(n.get("title", ""))
                if any(w in title for w in positive_words):
                    pos_count += 1
                if any(w in title for w in negative_words):
                    neg_count += 1

            total = pos_count + neg_count
            if total > 0:
                sentiment_score = (pos_count - neg_count) / total  # -1 to +1
            else:
                sentiment_score = 0

            return {
                "headline_count": len(news),
                "positive": pos_count,
                "negative": neg_count,
                "sentiment_score": round(sentiment_score, 2),
                "sentiment": "positive" if sentiment_score > 0.3 else ("negative" if sentiment_score < -0.3 else "neutral"),
                "recent_headlines": headlines[:5],
            }
        except Exception:
            return {"headline_count": 0, "sentiment": "unknown", "sentiment_score": 0, "recent_headlines": []}

    def get_earnings_calendar(self, ticker: str) -> Dict[str, Any]:
        """Get upcoming earnings date and expectations."""
        try:
            t = yf.Ticker(ticker)
            cal = t.calendar
            if cal:
                return {
                    "next_earnings": str(cal.get("Earnings Date", [None])[0]) if cal.get("Earnings Date") else None,
                    "earnings_estimate": cal.get("Earnings Average"),
                    "revenue_estimate": cal.get("Revenue Average"),
                    "earnings_high": cal.get("Earnings High"),
                    "earnings_low": cal.get("Earnings Low"),
                }
        except Exception:
            pass
        return {}

    def print_world_briefing(self):
        """Print a comprehensive world intelligence briefing."""
        ctx = self.get_full_context()

        print(f"\n{'='*70}")
        print(f"  WORLD INTELLIGENCE BRIEFING - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}")

        # Market Regime
        mr = ctx["market_regime"]
        print(f"\n  MARKET REGIME: {mr['regime'].upper()} (confidence {mr['confidence']:.0%})")
        print(f"    SPY ${mr['spy_price']:.2f} | SMA50 ${mr['spy_sma50']:.2f} | SMA200 ${mr['spy_sma200']:.2f}")
        print(f"    3m return: {mr['spy_3m_return']:+.1%} | 6m: {mr['spy_6m_return']:+.1%}")
        print(f"    >> {mr['recommendation']}")

        # Fear/Greed
        fg = ctx["fear_greed"]
        print(f"\n  FEAR/GREED: VIX {fg.get('vix', '?')} ({fg['regime'].upper()})")
        print(f"    {fg.get('interpretation', '')}")

        # Macro
        m = ctx["macro"]
        print(f"\n  MACRO:")
        print(f"    Fed Funds: {m.get('fed_funds_proxy', '?')}% | 10Y: {m.get('us_10y', '?')}% ({m.get('rates_direction', '?')})")
        print(f"    Dollar: {m.get('dollar_index', '?')} ({m.get('dollar_trend', '?')})")

        # Yield Curve
        yc = ctx["yield_curve"]
        print(f"\n  YIELD CURVE: {yc['interpretation']}")
        print(f"    Spread 10Y-3M: {yc['spread_10y_3m']}% {'INVERTED!' if yc['inverted'] else ''}")

        # Sectors
        print(f"\n  SECTOR ROTATION (3m performance):")
        for name, data in ctx["sectors"].items():
            trend_c = "+" if data["return_3m"] > 0 else ""
            sma = "↑" if data["above_sma50"] else "↓"
            print(f"    {name:20s}: {trend_c}{data['return_3m']*100:>5.1f}%  {sma}SMA50  [{data['trend']}]")

        # Commodities
        print(f"\n  COMMODITIES:")
        for name, data in ctx["commodities"].items():
            print(f"    {name:15s}: ${data['price']:>10,.2f}  3m: {data['return_3m']*100:+.1f}%  [{data['trend']}]")

        print(f"\n{'='*70}")
