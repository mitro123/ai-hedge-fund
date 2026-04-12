"""
Comprehensive unit tests for the 15 AI trading agents defined in
scripts/run_live_trading.py.

Tests verify:
  - Return format (signal, confidence, reasoning) for every agent
  - Per-agent logic on strong, weak, and TSLA-like data
  - Committee logic respects analyst consensus (no shorting analyst-favored stocks)
"""

import copy
import sys
from pathlib import Path

import pytest

# Ensure the project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_live_trading import (
    warren_buffett_analyze,
    ben_graham_analyze,
    charlie_munger_analyze,
    cathie_wood_analyze,
    michael_burry_analyze,
    peter_lynch_analyze,
    phil_fisher_analyze,
    stanley_druckenmiller_analyze,
    bill_ackman_analyze,
    rakesh_jhunjhunwala_analyze,
    aswath_damodaran_analyze,
    technical_analyst_analyze,
    fundamentals_analyst_analyze,
    sentiment_analyst_analyze,
    valuation_analyst_analyze,
    AGENTS,
    AGENT_GROUPS,
    run_investment_committee,
    run_risk_management,
)

# ============================================================
# SAMPLE DATA
# ============================================================

SAMPLE_STRONG_STOCK = {
    "price": 200.0, "pe": 20, "forward_pe": 18, "pb": 5, "roe": 35, "roa": 15,
    "roic": 25, "debt_equity": 0.3, "revenue_growth": 0.20, "earnings_growth": 0.25,
    "earnings_quarterly_growth": 0.20, "gross_margin": 0.60, "operating_margin": 0.30,
    "profit_margin": 0.25, "ev_ebitda": 15, "market_cap_b": 500, "fcf_yield": 0.05,
    "peg": 0.8, "dividend_yield": 0.01, "beta": 1.1, "rnd_ratio": 0.12,
    "sector": "Technology", "industry": "Software",
    "insider_ownership": 0.05, "institutional_ownership": 0.75,
    "short_ratio": 2.0, "short_pct_float": 0.02,
    "analyst_recommendation": "strong_buy", "analyst_score": 1.3,
    "analyst_target_mean": 280, "analyst_target_high": 320, "analyst_target_low": 220,
    "analyst_count": 30, "upside_to_target": 0.40,
    "momentum_3m": 0.08, "momentum_6m": 0.15, "momentum_12m": 0.30,
    "distance_from_52w_high": -0.05, "volatility_30d": 0.22,
    "sma_50": 195, "sma_200": 180, "golden_cross": True,
    "price_above_sma50": True, "price_above_sma200": True,
    "rsi": 55, "macd": {"macd": 2.0, "signal": 1.5, "histogram": 0.5, "bullish_cross": True},
    "bollinger": {"upper": 220, "lower": 185, "middle": 200, "pct_b": 0.5},
    "price_52w_high": 210, "price_52w_low": 150,
    "relative_strength_vs_sp500": 0.10, "market_regime": "bull",
    "interest_rate": 0.045, "inflation": 0.028, "earnings_surprise": 0.05,
    "buyback_yield": 0.02, "payout_ratio": 0.2,
}

SAMPLE_WEAK_STOCK = {
    "price": 50.0, "pe": 300, "forward_pe": 250, "pb": 12, "roe": 3, "roa": 1,
    "roic": 2, "debt_equity": 4.0, "revenue_growth": -0.15, "earnings_growth": -0.50,
    "earnings_quarterly_growth": -0.40, "gross_margin": 0.20, "operating_margin": 0.02,
    "profit_margin": 0.01, "ev_ebitda": 50, "market_cap_b": 5, "fcf_yield": 0.005,
    "peg": -3.0, "dividend_yield": 0.0, "beta": 2.0, "rnd_ratio": 0.01,
    "sector": "Consumer Cyclical", "industry": "Retail",
    "insider_ownership": 0.01, "institutional_ownership": 0.30,
    "short_ratio": 8.0, "short_pct_float": 0.15,
    "analyst_recommendation": "sell", "analyst_score": 4.0,
    "analyst_target_mean": 35, "analyst_target_high": 45, "analyst_target_low": 20,
    "analyst_count": 5, "upside_to_target": -0.30,
    "momentum_3m": -0.25, "momentum_6m": -0.30, "momentum_12m": -0.40,
    "distance_from_52w_high": -0.60, "volatility_30d": 0.55,
    "sma_50": 60, "sma_200": 75, "golden_cross": False,
    "price_above_sma50": False, "price_above_sma200": False,
    "rsi": 80, "macd": {"macd": -3.0, "signal": -1.0, "histogram": -2.0, "bullish_cross": False},
    "bollinger": {"upper": 70, "lower": 40, "middle": 55, "pct_b": 0.9},
    "price_52w_high": 120, "price_52w_low": 40,
    "relative_strength_vs_sp500": -0.30, "market_regime": "bear",
    "interest_rate": 0.045, "inflation": 0.028, "earnings_surprise": -0.10,
    "buyback_yield": 0.0, "payout_ratio": 0.0,
}

# TSLA-like: expensive on paper but analysts say BUY
SAMPLE_TSLA_LIKE = {
    "price": 350.0, "pe": 334, "forward_pe": 150, "pb": 20, "roe": 10, "roa": 5,
    "roic": 8, "debt_equity": 0.7, "revenue_growth": 0.01, "earnings_growth": -0.61,
    "earnings_quarterly_growth": -0.50, "gross_margin": 0.18, "operating_margin": 0.08,
    "profit_margin": 0.06, "ev_ebitda": 60, "market_cap_b": 1100, "fcf_yield": 0.01,
    "peg": -5.0, "dividend_yield": 0.0, "beta": 2.3, "rnd_ratio": 0.05,
    "sector": "Consumer Cyclical", "industry": "Auto Manufacturers",
    "insider_ownership": 0.13, "institutional_ownership": 0.45,
    "short_ratio": 1.5, "short_pct_float": 0.03,
    "analyst_recommendation": "buy", "analyst_score": 2.4,
    "analyst_target_mean": 300, "analyst_target_high": 450, "analyst_target_low": 120,
    "analyst_count": 40, "upside_to_target": -0.14,
    "momentum_3m": -0.10, "momentum_6m": 0.05, "momentum_12m": 0.40,
    "distance_from_52w_high": -0.20, "volatility_30d": 0.60,
    "sma_50": 370, "sma_200": 300, "golden_cross": True,
    "price_above_sma50": False, "price_above_sma200": True,
    "rsi": 42, "macd": {"macd": -5.0, "signal": -3.0, "histogram": -2.0, "bullish_cross": False},
    "bollinger": {"upper": 400, "lower": 320, "middle": 360, "pct_b": 0.3},
    "price_52w_high": 440, "price_52w_low": 140,
    "relative_strength_vs_sp500": 0.05, "market_regime": "bull",
    "interest_rate": 0.045, "inflation": 0.028, "earnings_surprise": -0.05,
    "buyback_yield": 0.0, "payout_ratio": 0.0,
}

ALL_AGENTS = [
    ("warren_buffett", warren_buffett_analyze),
    ("ben_graham", ben_graham_analyze),
    ("charlie_munger", charlie_munger_analyze),
    ("cathie_wood", cathie_wood_analyze),
    ("michael_burry", michael_burry_analyze),
    ("peter_lynch", peter_lynch_analyze),
    ("phil_fisher", phil_fisher_analyze),
    ("stanley_druckenmiller", stanley_druckenmiller_analyze),
    ("bill_ackman", bill_ackman_analyze),
    ("rakesh_jhunjhunwala", rakesh_jhunjhunwala_analyze),
    ("aswath_damodaran", aswath_damodaran_analyze),
    ("technical_analyst", technical_analyst_analyze),
    ("fundamentals_analyst", fundamentals_analyst_analyze),
    ("sentiment_analyst", sentiment_analyst_analyze),
    ("valuation_analyst", valuation_analyst_analyze),
]


# ============================================================
# 1. FORMAT TESTS - Every agent must return correct structure
# ============================================================

class TestAgentReturnFormat:
    """Every agent must return {signal, confidence, reasoning} with correct types."""

    @pytest.mark.parametrize("name,fn", ALL_AGENTS)
    def test_return_has_required_keys(self, name, fn):
        result = fn("TEST", SAMPLE_STRONG_STOCK)
        assert "signal" in result, f"{name} missing 'signal'"
        assert "confidence" in result, f"{name} missing 'confidence'"
        assert "reasoning" in result, f"{name} missing 'reasoning'"

    @pytest.mark.parametrize("name,fn", ALL_AGENTS)
    def test_signal_is_valid(self, name, fn):
        result = fn("TEST", SAMPLE_STRONG_STOCK)
        assert result["signal"] in ("bullish", "bearish", "neutral"), (
            f"{name} returned invalid signal: {result['signal']}"
        )

    @pytest.mark.parametrize("name,fn", ALL_AGENTS)
    def test_confidence_is_numeric(self, name, fn):
        result = fn("TEST", SAMPLE_STRONG_STOCK)
        assert isinstance(result["confidence"], (int, float)), (
            f"{name} confidence is not numeric: {type(result['confidence'])}"
        )
        assert 0 <= result["confidence"] <= 100, (
            f"{name} confidence out of range: {result['confidence']}"
        )

    @pytest.mark.parametrize("name,fn", ALL_AGENTS)
    def test_reasoning_is_string(self, name, fn):
        result = fn("TEST", SAMPLE_STRONG_STOCK)
        assert isinstance(result["reasoning"], str), (
            f"{name} reasoning is not a string"
        )

    @pytest.mark.parametrize("name,fn", ALL_AGENTS)
    def test_works_with_weak_stock(self, name, fn):
        """Agents must not crash on weak stock data."""
        result = fn("WEAK", SAMPLE_WEAK_STOCK)
        assert result["signal"] in ("bullish", "bearish", "neutral")

    @pytest.mark.parametrize("name,fn", ALL_AGENTS)
    def test_works_with_tsla_like(self, name, fn):
        """Agents must not crash on TSLA-like data."""
        result = fn("TSLA", SAMPLE_TSLA_LIKE)
        assert result["signal"] in ("bullish", "bearish", "neutral")


# ============================================================
# 2. WARREN BUFFETT
# ============================================================

class TestWarrenBuffett:
    def test_bullish_on_high_roe_low_pe(self):
        """High ROE (35%) + low PE (20) + strong FCF + low debt -> bullish."""
        result = warren_buffett_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert result["signal"] == "bullish"

    def test_bearish_on_high_debt(self):
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["debt_equity"] = 5.0
        d["roe"] = 5
        d["pe"] = 60
        d["fcf_yield"] = 0.01
        d["earnings_growth"] = -0.20
        d["gross_margin"] = 0.20
        d["upside_to_target"] = -0.10
        result = warren_buffett_analyze("BAD", d)
        assert result["signal"] == "bearish"

    def test_reasons_mention_roe(self):
        result = warren_buffett_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert "ROE" in result["reasoning"]

    def test_weak_stock_not_bullish(self):
        result = warren_buffett_analyze("WEAK", SAMPLE_WEAK_STOCK)
        assert result["signal"] != "bullish"

    def test_upside_adds_score(self):
        """upside_to_target > 20% should be mentioned."""
        result = warren_buffett_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert "upside" in result["reasoning"].lower()


# ============================================================
# 3. BEN GRAHAM
# ============================================================

class TestBenGraham:
    def test_bearish_on_high_pe_and_pb(self):
        """PE>25 and PB>5 should trigger bearish."""
        d = copy.deepcopy(SAMPLE_WEAK_STOCK)
        # PE=300, PB=12, no dividend, high debt - definitely bearish
        result = ben_graham_analyze("WEAK", d)
        assert result["signal"] == "bearish"

    def test_bullish_on_low_pe(self):
        """PE<15 is classic Graham value."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["pe"] = 10
        d["pb"] = 1.0
        d["dividend_yield"] = 0.03
        result = ben_graham_analyze("VALUE", d)
        assert result["signal"] == "bullish"

    def test_pe_criteria_in_reasoning(self):
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["pe"] = 10
        result = ben_graham_analyze("VALUE", d)
        assert "Graham" in result["reasoning"]

    def test_net_net_bonus(self):
        """Price below book value with positive earnings should add score."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["pe"] = 12
        d["pb"] = 0.8  # below book
        d["earnings_growth"] = 0.15
        result = ben_graham_analyze("NNET", d)
        assert result["signal"] == "bullish"
        assert "below book" in result["reasoning"].lower()


# ============================================================
# 4. CHARLIE MUNGER
# ============================================================

class TestCharlieMunger:
    def test_bullish_on_high_margins_quality(self):
        """High ROE (35%) + gross margin 60% + operating margin 30% -> bullish."""
        result = charlie_munger_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert result["signal"] == "bullish"

    def test_mentions_quality(self):
        result = charlie_munger_analyze("AAPL", SAMPLE_STRONG_STOCK)
        reasoning = result["reasoning"].lower()
        assert "quality" in reasoning or "margin" in reasoning or "pricing power" in reasoning

    def test_weak_stock_not_bullish(self):
        result = charlie_munger_analyze("WEAK", SAMPLE_WEAK_STOCK)
        assert result["signal"] != "bullish"

    def test_expensive_pe_penalized(self):
        """PE > 50 should hurt the score."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["pe"] = 80
        d["roe"] = 8
        d["gross_margin"] = 0.25
        d["earnings_growth"] = -0.05
        d["operating_margin"] = 0.10
        result = charlie_munger_analyze("EXP", d)
        assert result["signal"] != "bullish"


# ============================================================
# 5. MICHAEL BURRY - Respects analyst consensus
# ============================================================

class TestMichaelBurry:
    def test_not_bearish_when_analysts_buy(self):
        """High PE but analyst_score <= 2.0 means Burry should NOT be bearish.
        This is the key behavioral test: Burry respects the Street."""
        d = copy.deepcopy(SAMPLE_TSLA_LIKE)
        # PE=334, earnings_growth=-0.61, BUT analyst_score=2.4 (<= 2.5 threshold)
        result = michael_burry_analyze("TSLA", d)
        # With analyst_score 2.4 (<= 2.5), PE>100 only gets -1 not -3
        # So it should NOT be strongly bearish (need <= -2 for bearish)
        assert result["signal"] != "bearish" or result["confidence"] < 60

    def test_bearish_when_analysts_agree(self):
        """High PE AND analyst_score > 3.0 -> Burry goes bearish."""
        d = copy.deepcopy(SAMPLE_WEAK_STOCK)
        d["pe"] = 200
        d["analyst_score"] = 4.5
        result = michael_burry_analyze("BAD", d)
        assert result["signal"] == "bearish"

    def test_deep_value_detection(self):
        """Low PE + high FCF yield -> bullish."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["pe"] = 8
        d["fcf_yield"] = 0.08
        d["analyst_score"] = 1.5
        result = michael_burry_analyze("VAL", d)
        assert result["signal"] == "bullish"

    def test_respects_street_consensus(self):
        """analyst_score <= 1.5 should add score."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["pe"] = 25  # not extreme
        d["analyst_score"] = 1.2
        result = michael_burry_analyze("GOOD", d)
        assert "respect" in result["reasoning"].lower() or "strong buy" in result["reasoning"].lower()


# ============================================================
# 6. CATHIE WOOD
# ============================================================

class TestCathieWood:
    def test_bullish_on_high_growth_tech(self):
        """High revenue growth + Technology sector -> bullish."""
        result = cathie_wood_analyze("NVDA", SAMPLE_STRONG_STOCK)
        assert result["signal"] == "bullish"

    def test_semiconductor_bonus(self):
        """Semiconductor industry gets extra score."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["industry"] = "Semiconductor"
        d["revenue_growth"] = 0.35
        result = cathie_wood_analyze("NVDA", d)
        assert result["signal"] == "bullish"
        assert "semiconductor" in result["reasoning"].lower() or "AI" in result["reasoning"]

    def test_bearish_on_declining_revenue(self):
        """Revenue declining -> bearish penalty."""
        d = copy.deepcopy(SAMPLE_WEAK_STOCK)
        d["revenue_growth"] = -0.20
        result = cathie_wood_analyze("OLD", d)
        assert result["signal"] == "bearish"

    def test_upside_mentioned(self):
        """Strong upside to analyst target should factor in."""
        result = cathie_wood_analyze("AAPL", SAMPLE_STRONG_STOCK)
        # 40% upside in strong stock
        assert "upside" in result["reasoning"].lower()


# ============================================================
# 7. PETER LYNCH - PEG ratio
# ============================================================

class TestPeterLynch:
    def test_bullish_on_low_peg(self):
        """PEG <= 1.0 is Lynch's sweet spot."""
        result = peter_lynch_analyze("AAPL", SAMPLE_STRONG_STOCK)
        # PEG = 0.8, earnings_growth = 25%
        assert result["signal"] == "bullish"
        assert "PEG" in result["reasoning"]

    def test_peg_ratio_used(self):
        """PEG is explicitly mentioned in reasoning."""
        result = peter_lynch_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert "PEG" in result["reasoning"]
        assert "0.80" in result["reasoning"]

    def test_negative_peg_penalized(self):
        """Negative PEG means declining earnings."""
        d = copy.deepcopy(SAMPLE_WEAK_STOCK)
        d["peg"] = -3.0
        result = peter_lynch_analyze("BAD", d)
        assert result["signal"] == "bearish"

    def test_high_peg_penalized(self):
        """PEG > 2.5 is overpriced."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["peg"] = 3.5
        d["earnings_growth"] = 0.05
        d["debt_equity"] = 1.5
        d["analyst_count"] = 40
        result = peter_lynch_analyze("EXP", d)
        # Should at least not be bullish
        assert result["signal"] != "bullish"


# ============================================================
# 8. DRUCKENMILLER - momentum + analyst targets
# ============================================================

class TestDruckenmiller:
    def test_bullish_on_strong_momentum_and_analysts(self):
        """Strong 12m momentum + analyst strong buy + golden cross -> bullish."""
        result = stanley_druckenmiller_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert result["signal"] == "bullish"

    def test_respects_analyst_targets(self):
        """Analyst score <= 1.5 with upside > 20% adds score."""
        result = stanley_druckenmiller_analyze("AAPL", SAMPLE_STRONG_STOCK)
        reasoning = result["reasoning"].lower()
        assert "strong buy" in reasoning or "smart money" in reasoning

    def test_uses_momentum(self):
        """12m momentum is used for scoring."""
        result = stanley_druckenmiller_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert "momentum" in result["reasoning"].lower()

    def test_bear_market_penalty(self):
        """Bear market regime subtracts score."""
        d = copy.deepcopy(SAMPLE_WEAK_STOCK)
        result = stanley_druckenmiller_analyze("WEAK", d)
        assert "bear" in result["reasoning"].lower() or "defensive" in result["reasoning"].lower()

    def test_golden_cross_bonus(self):
        """golden_cross adds score."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["golden_cross"] = True
        result = stanley_druckenmiller_analyze("GC", d)
        assert "golden cross" in result["reasoning"].lower()


# ============================================================
# 9. TECHNICAL ANALYST - uses RSI, MACD, SMA (NOT random)
# ============================================================

class TestTechnicalAnalyst:
    def test_uses_rsi(self):
        """RSI should appear in reasoning."""
        result = technical_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert "RSI" in result["reasoning"]

    def test_uses_macd(self):
        """MACD bullish cross should be detected."""
        result = technical_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert "MACD" in result["reasoning"]

    def test_oversold_rsi_bullish(self):
        """RSI < 30 = oversold -> bullish signal."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["rsi"] = 25
        result = technical_analyst_analyze("DIP", d)
        assert "oversold" in result["reasoning"].lower()

    def test_overbought_rsi_warning(self):
        """RSI > 75 = overbought -> warning."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["rsi"] = 80
        result = technical_analyst_analyze("HOT", d)
        assert "overbought" in result["reasoning"].lower()

    def test_golden_cross_detected(self):
        """Golden cross should appear."""
        result = technical_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert "golden cross" in result["reasoning"].lower()

    def test_deterministic_results(self):
        """Same input -> same output (no randomness)."""
        r1 = technical_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        r2 = technical_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert r1 == r2

    def test_buy_the_dip_logic(self):
        """Below SMA50 + analyst strong buy + upside -> buy the dip."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        d["price_above_sma50"] = False
        d["analyst_score"] = 1.3
        d["upside_to_target"] = 0.35
        result = technical_analyst_analyze("DIP", d)
        assert "dip" in result["reasoning"].lower() or "buy" in result["reasoning"].lower()


# ============================================================
# 10. SENTIMENT ANALYST - uses real analyst_score and recommendation
# ============================================================

class TestSentimentAnalyst:
    def test_uses_analyst_score(self):
        """analyst_score should drive the signal."""
        result = sentiment_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert "score" in result["reasoning"].lower() or "strong buy" in result["reasoning"].lower()

    def test_bullish_on_strong_buy(self):
        """analyst_score <= 1.5 -> bullish."""
        result = sentiment_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert result["signal"] == "bullish"

    def test_bearish_on_sell_rating(self):
        """analyst_score >= 4.0 -> bearish."""
        result = sentiment_analyst_analyze("WEAK", SAMPLE_WEAK_STOCK)
        assert result["signal"] == "bearish"

    def test_high_short_interest_penalty(self):
        """short_pct_float > 10% subtracts score."""
        result = sentiment_analyst_analyze("WEAK", SAMPLE_WEAK_STOCK)
        assert "short interest" in result["reasoning"].lower()

    def test_upside_target_bonus(self):
        """upside_to_target > 30% adds to bullish."""
        result = sentiment_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert "upside" in result["reasoning"].lower()

    def test_deterministic(self):
        """No randomness: same input same output."""
        r1 = sentiment_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        r2 = sentiment_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert r1 == r2


# ============================================================
# OTHER AGENTS - basic correctness
# ============================================================

class TestPhilFisher:
    def test_bullish_on_growth_and_rnd(self):
        """Revenue growth + high margins + R&D -> bullish."""
        result = phil_fisher_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert result["signal"] == "bullish"

    def test_rnd_mentioned(self):
        result = phil_fisher_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert "R&D" in result["reasoning"]


class TestBillAckman:
    def test_bullish_on_quality_value(self):
        """PE<25 + ROE>15 + FCF>4% -> bullish."""
        result = bill_ackman_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert result["signal"] == "bullish"

    def test_bearish_on_expensive(self):
        """PE>60 -> penalty."""
        result = bill_ackman_analyze("WEAK", SAMPLE_WEAK_STOCK)
        assert result["signal"] == "bearish"


class TestRakeshJhunjhunwala:
    def test_bullish_on_growth_momentum(self):
        result = rakesh_jhunjhunwala_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert result["signal"] == "bullish"


class TestAswathDamodaran:
    def test_growth_vs_implied_logic(self):
        """When growth exceeds implied rate (PE/15 - 1), should be bullish."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        # PE=12, implied = 12/15-1 = -0.2, earnings_growth=0.25 >> implied -> +2
        # EV/EBITDA=10 -> +2, FCF 0.05 -> +1 => total 5, bullish
        d["pe"] = 12
        d["ev_ebitda"] = 10
        result = aswath_damodaran_analyze("VAL", d)
        assert result["signal"] == "bullish"
        assert "implied" in result["reasoning"].lower()

    def test_implied_growth_check_matters(self):
        """When PE implies higher growth than actual, score is penalized."""
        d = copy.deepcopy(SAMPLE_STRONG_STOCK)
        # PE=20 -> implied = 20/15-1 = 0.333, earnings_growth=0.25 < 0.333 -> -1
        result = aswath_damodaran_analyze("AAPL", d)
        assert "implied" in result["reasoning"].lower()


class TestFundamentalsAnalyst:
    def test_bullish_on_strong_fundamentals(self):
        result = fundamentals_analyst_analyze("AAPL", SAMPLE_STRONG_STOCK)
        assert result["signal"] == "bullish"

    def test_bearish_on_weak_fundamentals(self):
        result = fundamentals_analyst_analyze("WEAK", SAMPLE_WEAK_STOCK)
        assert result["signal"] == "bearish"


class TestValuationAnalyst:
    def test_extreme_pe_bearish(self):
        result = valuation_analyst_analyze("WEAK", SAMPLE_WEAK_STOCK)
        # PE=300, EV/EBITDA=50 -> bearish
        assert result["signal"] == "bearish"


# ============================================================
# 11. COMMITTEE LOGIC - analyst_score <= 2.0 stocks NOT shorted
# ============================================================

class TestCommitteeLogic:
    """Test that the investment committee respects analyst consensus."""

    def _build_all_bearish_signals(self, ticker):
        """Simulate all agents returning bearish for a ticker."""
        signals = {}
        for agent_id in AGENTS:
            signals[agent_id] = {
                ticker: {"signal": "bearish", "confidence": 80.0, "reasoning": "Test bearish"}
            }
        return signals

    def _build_all_bullish_signals(self, ticker):
        signals = {}
        for agent_id in AGENTS:
            signals[agent_id] = {
                ticker: {"signal": "bullish", "confidence": 80.0, "reasoning": "Test bullish"}
            }
        return signals

    def test_no_short_when_analyst_buy(self):
        """Stocks with analyst_score <= 2.0 must NOT be shorted even if all agents bearish."""
        ticker = "TSLA"
        signals = self._build_all_bearish_signals(ticker)
        portfolio = {"cash": 100000, "positions": {}}
        risk = {ticker: {"remaining_position_limit": 50000, "current_price": 350.0}}
        stock_data = {ticker: {"analyst_score": 2.0, "upside_to_target": 0.10}}

        decisions, _ = run_investment_committee(
            [ticker], signals, risk, portfolio, stock_data=stock_data
        )
        assert decisions[ticker]["action"] != "short", (
            f"Committee shorted {ticker} despite analyst_score=2.0!"
        )

    def test_short_allowed_when_analyst_sell(self):
        """Stocks with analyst_score > 3.0 CAN be shorted when agents agree."""
        ticker = "BAD"
        signals = self._build_all_bearish_signals(ticker)
        portfolio = {"cash": 100000, "positions": {}}
        risk = {ticker: {"remaining_position_limit": 50000, "current_price": 50.0}}
        stock_data = {ticker: {"analyst_score": 4.5, "upside_to_target": -0.30}}

        decisions, _ = run_investment_committee(
            [ticker], signals, risk, portfolio, stock_data=stock_data
        )
        assert decisions[ticker]["action"] == "short", (
            f"Committee refused to short {ticker} even with analyst_score=4.5"
        )

    def test_strong_buy_override(self):
        """analyst_score <= 1.5 + upside > 25% should override hold to buy."""
        ticker = "NVDA"
        # Mixed signals -> would normally hold
        signals = {}
        for agent_id in AGENTS:
            signals[agent_id] = {
                ticker: {"signal": "neutral", "confidence": 50.0, "reasoning": "Mixed"}
            }
        portfolio = {"cash": 100000, "positions": {}}
        risk = {ticker: {"remaining_position_limit": 50000, "current_price": 200.0}}
        stock_data = {ticker: {"analyst_score": 1.3, "upside_to_target": 0.40}}

        decisions, _ = run_investment_committee(
            [ticker], signals, risk, portfolio, stock_data=stock_data
        )
        assert decisions[ticker]["action"] == "buy", (
            f"Strong buy override failed: got {decisions[ticker]['action']}"
        )

    def test_bullish_consensus_buys(self):
        """When most groups bullish, committee should buy."""
        ticker = "AAPL"
        signals = self._build_all_bullish_signals(ticker)
        portfolio = {"cash": 100000, "positions": {}}
        risk = {ticker: {"remaining_position_limit": 50000, "current_price": 200.0}}

        decisions, _ = run_investment_committee(
            [ticker], signals, risk, portfolio, stock_data={}
        )
        assert decisions[ticker]["action"] == "buy"

    def test_committee_returns_all_tickers(self):
        """Committee should return decisions for all tickers."""
        tickers = ["AAPL", "MSFT", "GOOG"]
        signals = {}
        for agent_id in AGENTS:
            signals[agent_id] = {}
            for t in tickers:
                signals[agent_id][t] = {
                    "signal": "bullish", "confidence": 70.0, "reasoning": "Test"
                }
        portfolio = {"cash": 100000, "positions": {}}
        risk = {t: {"remaining_position_limit": 25000, "current_price": 200.0} for t in tickers}

        decisions, debates = run_investment_committee(
            tickers, signals, risk, portfolio, stock_data={}
        )
        for t in tickers:
            assert t in decisions
            assert t in debates


# ============================================================
# AGENT REGISTRY
# ============================================================

class TestAgentRegistry:
    def test_all_15_agents_registered(self):
        assert len(AGENTS) == 15

    def test_all_groups_have_valid_agents(self):
        for gname, gcfg in AGENT_GROUPS.items():
            for aid in gcfg["agents"]:
                assert aid in AGENTS, f"Group {gname} references unknown agent {aid}"

    def test_all_agents_in_some_group(self):
        grouped = set()
        for gcfg in AGENT_GROUPS.values():
            grouped.update(gcfg["agents"])
        for aid in AGENTS:
            assert aid in grouped, f"Agent {aid} not in any group"
