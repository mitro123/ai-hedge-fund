"""
Score Interpreter - "LLM-equivalent" decision engine.
Takes raw scores from all original agents + market context
and produces unified buy/sell/hold decisions.

This replaces the LLM call with deterministic logic that captures
what a smart portfolio manager would conclude from the data.

Key principle: NEVER override market reality with theoretical valuation.
DCF says "overvalued" for most tech stocks, but the market disagrees.
We listen to the market (analyst consensus, momentum) while using
fundamental scores for QUALITY assessment.
"""

from typing import Any, Dict, List, Optional, Tuple


# Dynamic agent weight adjustments by market regime
REGIME_WEIGHT_ADJUSTMENTS = {
    "strong_bull": {
        "momentum": 1.8, "analyst_consensus": 2.2,
        "buffett_dcf": 0.2, "graham_valuation": 0.2,
    },
    "bull": {},  # Use defaults
    "correction": {
        "momentum": 0.8, "buffett_dcf": 0.8, "graham_valuation": 0.7,
        "buffett_moat": 2.0, "analyst_consensus": 1.5,
    },
    "bear": {
        "momentum": 0.3, "buffett_dcf": 0.8, "graham_valuation": 0.8,
        "graham_strength": 1.5, "buffett_moat": 2.2,
        "analyst_consensus": 1.0, "relative_strength": 0.5,
    },
    "sideways": {
        "momentum": 0.7, "buffett_moat": 1.5, "munger_predictability": 1.5,
    },
    "recovery": {
        "momentum": 1.2, "buffett_dcf": 0.6, "relative_strength": 1.5,
    },
}

# Base agent accuracy weights (from our deep analysis)
AGENT_WEIGHTS = {
    "buffett_fundamentals": 1.5,    # ROE, margins, balance sheet = high quality
    "buffett_moat": 1.8,            # Moat consistency = best long-term predictor
    "buffett_consistency": 1.3,     # Earnings trend
    "buffett_dcf": 0.3,            # DCF is almost always "overvalued" = low signal
    "technical_ensemble": 1.4,      # 5-strategy = good timing
    "burry_value": 0.5,            # Too conservative in bull market
    "burry_balance": 0.8,          # Balance sheet quality matters
    "lynch_peg": 1.2,              # PEG is predictive for growth
    "lynch_growth": 1.1,           # Revenue/EPS growth
    "fisher_rnd": 1.0,             # R&D investment = future moat
    "fisher_margins": 1.1,         # Margin stability
    "ackman_quality": 1.0,         # Business quality
    "ackman_dcf": 0.4,             # Same DCF problem as Buffett
    "munger_moat": 1.3,            # ROIC consistency
    "munger_predictability": 1.2,  # Revenue/margin stability
    "graham_strength": 0.9,        # Balance sheet
    "graham_valuation": 0.3,       # Too strict for tech
    "analyst_consensus": 2.0,      # HIGHEST weight - real money behind it
    "momentum": 1.5,               # Trend following works
    "relative_strength": 1.0,      # Outperformance vs index
}


def interpret_scores(
    ticker: str,
    original_scores: Dict[str, Any],
    live_data: Dict[str, Any],
    world_context: Optional[Dict] = None,
    category: str = "core",
) -> Dict[str, Any]:
    """
    Interpret multiple agent scores + market context into a unified signal.

    This is the "brain" - it weighs fundamental quality (from originals)
    against market reality (analyst consensus, momentum, regime).

    Args:
        ticker: Stock symbol
        original_scores: Dict of agent_name -> {score, max_score, details}
        live_data: Real-time data from MarketDataProvider
        world_context: Global market intelligence
        category: Stock category (core/growth/unicorn/cyclical/defensive)

    Returns:
        {signal, confidence, reasoning, conviction_score}
    """
    if not live_data or "error" in live_data:
        return {"signal": "neutral", "confidence": 20, "reasoning": "No data", "conviction_score": 0}

    weighted_bull = 0.0
    weighted_bear = 0.0
    total_weight = 0.0
    reasons = []

    # Determine market regime for dynamic weight adjustment
    regime = "unknown"
    if world_context:
        regime = world_context.get("market_regime", {}).get("regime", "unknown")
    regime_adjustments = REGIME_WEIGHT_ADJUSTMENTS.get(regime, {})

    # === PHASE 0: Detect stock type for agent weight adjustment ===
    # Value agents are useless on pre-profit/high-PE growth stocks
    pe = live_data.get("pe", 0)
    rg = live_data.get("revenue_growth", 0)
    is_speculative = (pe > 50 or pe <= 0) and rg > 0.15
    if is_speculative:
        # Reduce value agents, boost growth agents
        regime_adjustments = dict(regime_adjustments)  # copy
        regime_adjustments["buffett_dcf"] = 0.1
        regime_adjustments["graham_valuation"] = 0.1
        regime_adjustments["graham_strength"] = 0.5
        regime_adjustments["burry_value"] = 0.2
        regime_adjustments["burry_balance"] = 0.4

    # === PHASE 1: Process original agent scores ===
    for agent_key, score_data in original_scores.items():
        if not score_data or not isinstance(score_data, dict):
            continue

        score = score_data.get("score", 0)
        max_score = score_data.get("max_score", 1)
        # Dynamic weight: base * regime adjustment
        base_weight = AGENT_WEIGHTS.get(agent_key, 1.0)
        weight = regime_adjustments.get(agent_key, base_weight)

        if max_score <= 0:
            continue

        pct = min(score / max_score, 1.0)  # Cap at 100%
        total_weight += weight

        if pct >= 0.65:
            weighted_bull += weight * pct
            if weight >= 1.0:
                reasons.append(f"{agent_key}:BULL({pct:.0%})")
        elif pct <= 0.30:
            weighted_bear += weight * (1 - pct)  # Inverse: lower score = more bearish
            if weight >= 1.0:
                reasons.append(f"{agent_key}:BEAR({pct:.0%})")
        # Neutral scores don't vote

    # === PHASE 2: Market reality overlay ===

    # Analyst consensus (HIGHEST WEIGHT)
    analyst_score = live_data.get("analyst_score", 3.0)
    analyst_weight = regime_adjustments.get("analyst_consensus", AGENT_WEIGHTS["analyst_consensus"])
    total_weight += analyst_weight

    if analyst_score <= 1.5:
        weighted_bull += analyst_weight * 0.9
        reasons.append(f"Street:STRONG_BUY({analyst_score:.1f})")
    elif analyst_score <= 2.0:
        weighted_bull += analyst_weight * 0.7
        reasons.append(f"Street:BUY({analyst_score:.1f})")
    elif analyst_score >= 4.0:
        weighted_bear += analyst_weight * 0.8
        reasons.append(f"Street:SELL({analyst_score:.1f})")
    elif analyst_score >= 3.0:
        weighted_bear += analyst_weight * 0.4

    # Upside to analyst target
    upside = live_data.get("upside_to_target", 0)
    if upside > 0.30:
        weighted_bull += 1.0
        reasons.append(f"Upside:{upside:.0%}")
    elif upside < -0.10:
        weighted_bear += 0.5

    # Momentum (SECOND HIGHEST)
    m12 = live_data.get("momentum_12m", 0)
    m6 = live_data.get("momentum_6m", 0)
    mom_weight = regime_adjustments.get("momentum", AGENT_WEIGHTS["momentum"])
    total_weight += mom_weight

    mom_score = 0.4 * (live_data.get("momentum_3m", 0)) + 0.3 * m6 + 0.3 * m12
    if mom_score > 0.05:
        weighted_bull += mom_weight * min(mom_score * 3, 1.0)
        if m12 > 0.20:
            reasons.append(f"Momentum:+{m12:.0%}")
    elif mom_score < -0.05:
        weighted_bear += mom_weight * min(abs(mom_score) * 3, 1.0)
        if m12 < -0.10:
            reasons.append(f"Momentum:{m12:.0%}")

    # Technical health
    if live_data.get("golden_cross", False):
        weighted_bull += 0.5
    if not live_data.get("price_above_sma200", True):
        weighted_bear += 0.5
        reasons.append("Below_SMA200")

    # RSI context
    rsi = live_data.get("rsi", 50)
    if rsi < 30 and analyst_score <= 2.0:
        weighted_bull += 1.0  # Oversold + analyst buy = strong opportunity
        reasons.append(f"Oversold_RSI{rsi:.0f}")
    elif rsi > 75:
        weighted_bear += 0.3

    # Relative strength vs S&P
    rs = live_data.get("relative_strength_vs_sp500", 0)
    rs_weight = regime_adjustments.get("relative_strength", AGENT_WEIGHTS["relative_strength"])
    total_weight += rs_weight
    if rs > 0.10:
        weighted_bull += rs_weight * 0.7
    elif rs < -0.15:
        weighted_bear += rs_weight * 0.5

    # === PHASE 3: World context adjustments ===
    if world_context:
        regime = world_context.get("market_regime", {}).get("regime", "unknown")
        vix = world_context.get("fear_greed", {}).get("vix", 20)

        # Bear market: reduce aggression
        if regime == "bear":
            weighted_bear += 1.5
            if category in ("unicorn", "special"):
                weighted_bear += 1.5  # Extra penalty for risky stocks in bear
        elif regime == "strong_bull":
            weighted_bull += 0.5  # Tailwind in strong bull

        # VIX: REGIME-AWARE (Bull+HighVIX = opportunity, Bear+HighVIX = danger)
        vix = world_context.get("fear_greed", {}).get("vix", 20)
        if regime in ("bear", "correction") and vix > 25:
            # Bear + fear = genuinely dangerous for risky stocks
            if category in ("unicorn", "growth", "special"):
                weighted_bear += 1.5
                reasons.append(f"BEAR+VIX={vix:.0f}")
            elif category == "defensive":
                weighted_bull += 1.0  # Strong flight to safety
        elif regime in ("strong_bull", "bull") and vix > 25:
            # Bull + elevated VIX = buying opportunity (83% win rate!)
            weighted_bear += 0.3  # Only mild caution
            # Quality dips in bull = buy signal
            if category in ("core", "growth"):
                weighted_bull += 0.3
                reasons.append(f"BullDip_VIX={vix:.0f}")

        # Yield curve inversion = recession signal
        yc = world_context.get("yield_curve", {})
        if yc.get("inverted", False):
            weighted_bear += 0.5
            if category in ("cyclical", "unicorn"):
                weighted_bear += 0.5
                reasons.append("Yield_INVERTED")

        # Sector rotation: follow the money flow between sectors
        sectors = world_context.get("sectors", {})
        stock_sector = live_data.get("sector", "")
        for sec_name, sec_data in sectors.items():
            if sec_name.lower() in stock_sector.lower():
                sec_ret_3m = sec_data.get("return_3m", 0)
                if sec_data.get("trend") == "bullish" and sec_ret_3m > 0.10:
                    weighted_bull += 1.5  # Strong sector tailwind
                    reasons.append(f"Sector_Leader:{sec_name}({sec_ret_3m:+.0%})")
                elif sec_data.get("trend") == "bullish":
                    weighted_bull += 0.7
                elif sec_data.get("trend") == "bearish" and sec_ret_3m < -0.05:
                    weighted_bear += 1.0  # Sector headwind
                    reasons.append(f"Sector_Lagging:{sec_name}({sec_ret_3m:+.0%})")
                break  # Only match one sector
                reasons.append(f"Sector_Leader:{sec_name}")
                break

    # === PHASE 4: Earnings Intelligence ===
    beats = live_data.get("earnings_beat_history", {})
    beat_rate = beats.get("beat_rate", 0)
    if beat_rate >= 0.75:
        weighted_bull += 1.0  # Consistent beater = reliable management
        reasons.append(f"Beats:{beat_rate:.0%}")
    elif beat_rate <= 0.25 and beats.get("total", 0) >= 3:
        weighted_bear += 0.5  # Consistent misser

    # Forward growth estimates from analysts
    fwd_growth = live_data.get("forward_growth_estimate", {})
    next_q_growth = fwd_growth.get("0q", 0)
    if next_q_growth > 0.50:
        weighted_bull += 1.0  # Expected >50% growth next quarter
        reasons.append(f"FwdGrowth:{next_q_growth:+.0%}")
    elif next_q_growth > 0.20:
        weighted_bull += 0.5

    # Target spread = uncertainty measure
    spread = live_data.get("analyst_target_spread", {})
    spread_pct = spread.get("spread_pct", 0)
    if spread_pct > 1.5:
        # Very wide spread = high uncertainty, reduce conviction
        weighted_bear += 0.3
        reasons.append(f"HighUncertainty({spread_pct:.0%})")

    # === PHASE 4b: Options Market Intelligence (smart money) ===
    opts = live_data.get("options_sentiment", {})
    pc_ratio = opts.get("put_call_ratio", 1.0)
    if pc_ratio > 1.5:
        # Very high put/call = extreme fear - CONTRARIAN bullish
        weighted_bull += 0.8
        reasons.append(f"Options:FEAR(P/C={pc_ratio:.1f})")
    elif pc_ratio < 0.5:
        # Very low put/call = extreme greed - caution
        weighted_bear += 0.3

    # === PHASE 4c: EPS Revision Momentum (strongest quant alpha signal) ===
    eps_rev = live_data.get("eps_revisions", {})
    rev_momentum = eps_rev.get("revision_momentum", "flat")
    if rev_momentum == "strong_up":
        weighted_bull += 1.5  # Strong upward revisions = analysts getting more bullish
        reasons.append(f"EPS_Revisions:STRONG_UP({eps_rev.get('up_30d',0)}up/{eps_rev.get('down_30d',0)}down)")
    elif rev_momentum == "up":
        weighted_bull += 0.7
    elif rev_momentum == "down":
        weighted_bear += 0.7
        reasons.append(f"EPS_Revisions:DOWN")

    # Estimate change (how much has EPS estimate moved in 90 days)
    est_change = eps_rev.get("estimate_change_90d", 0)
    if est_change > 0.10:
        weighted_bull += 0.5  # Estimates rising >10% in 90 days
    elif est_change < -0.10:
        weighted_bear += 0.5

    # === PHASE 5: Unicorn bonus ===
    if category == "unicorn":
        mcap = live_data.get("market_cap_b", 0)
        rg = live_data.get("revenue_growth", 0)
        if mcap < 50 and rg > 0.25:
            weighted_bull += 1.5
            reasons.append(f"Unicorn:${mcap:.0f}B+{rg:.0%}growth")

    # === PHASE 5: Anti-short rule ===
    # NEVER recommend shorting when analysts say buy
    net_signal = weighted_bull - weighted_bear

    # === CONFIDENCE DAMPENING: Extreme consensus on growth stocks ===
    # If >80% agents bearish on a growing stock, they're outside their
    # circle of competence, not genuinely bearish
    if is_speculative and weighted_bear > weighted_bull * 2:
        if rg > 0.20:
            # Growing revenue + unanimous bearish = value agents don't understand this stock
            damping = 0.5
            weighted_bear *= damping
            reasons.append(f"Dampened:value_agents_OOC({rg:+.0%}growth)")

    # === FINAL DECISION ===
    if total_weight > 0:
        bull_pct = weighted_bull / total_weight
        bear_pct = weighted_bear / total_weight
    else:
        bull_pct = bear_pct = 0

    net = bull_pct - bear_pct

    if net > 0.15:
        signal = "bullish"
    elif net < -0.10:
        signal = "bearish"
    else:
        signal = "neutral"

    # Confidence: how strong is the signal (0-95)
    confidence = min(95, max(20, abs(net) * 150 + 25))

    # Conviction score (0-100) for portfolio RANKING and sizing
    # Uses more granular scoring to differentiate between stocks
    # Count how many different agents agree
    n_bull_agents = len([r for r in reasons if "BULL" in r])
    n_bear_agents = len([r for r in reasons if "BEAR" in r])

    # Base conviction from net signal
    base_conviction = net * 80 + 50  # -0.5 to +0.5 maps to 10 to 90

    # Boost for analyst consensus
    if analyst_score <= 1.5: base_conviction += 10
    elif analyst_score <= 2.0: base_conviction += 5

    # Boost for momentum
    if m12 > 0.30: base_conviction += 10
    elif m12 > 0.15: base_conviction += 5

    # Boost for strong fundamentals agreement
    if n_bull_agents >= 5: base_conviction += 10
    elif n_bull_agents >= 3: base_conviction += 5

    # Penalty for being below SMA200
    if not live_data.get("price_above_sma200", True):
        base_conviction -= 10

    conviction = min(100, max(0, base_conviction))

    return {
        "signal": signal,
        "confidence": round(confidence, 1),
        "reasoning": "; ".join(reasons[:8]),
        "conviction_score": round(conviction, 1),
        "bull_weight": round(weighted_bull, 2),
        "bear_weight": round(weighted_bear, 2),
        "net_signal": round(net, 3),
    }


def aggregate_original_scores(
    buffett_scores: Optional[Dict] = None,
    burry_scores: Optional[Dict] = None,
    lynch_scores: Optional[Dict] = None,
    fisher_scores: Optional[Dict] = None,
    ackman_scores: Optional[Dict] = None,
    munger_scores: Optional[Dict] = None,
    graham_scores: Optional[Dict] = None,
    technical_signal: Optional[Dict] = None,
) -> Dict[str, Dict]:
    """
    Aggregate all original agent sub-scores into a flat dict for interpret_scores().
    """
    scores = {}

    if buffett_scores:
        if "fundamentals" in buffett_scores:
            scores["buffett_fundamentals"] = buffett_scores["fundamentals"]
        if "moat" in buffett_scores:
            scores["buffett_moat"] = buffett_scores["moat"]
        if "consistency" in buffett_scores:
            scores["buffett_consistency"] = buffett_scores["consistency"]
        if "intrinsic_value" in buffett_scores:
            scores["buffett_dcf"] = buffett_scores["intrinsic_value"]
        if "management" in buffett_scores:
            scores["buffett_management"] = buffett_scores["management"]

    if burry_scores:
        if "value" in burry_scores:
            scores["burry_value"] = burry_scores["value"]
        if "balance_sheet" in burry_scores:
            scores["burry_balance"] = burry_scores["balance_sheet"]

    if lynch_scores:
        for key in ("growth", "fundamentals", "valuation"):
            if key in lynch_scores:
                scores[f"lynch_{key}"] = lynch_scores[key]

    if fisher_scores:
        for key in ("growth_quality", "margins", "management", "valuation"):
            if key in fisher_scores:
                scores[f"fisher_{key.replace('growth_quality', 'rnd')}"] = fisher_scores[key]

    if ackman_scores:
        if "quality" in ackman_scores:
            scores["ackman_quality"] = ackman_scores["quality"]
        if "valuation" in ackman_scores:
            scores["ackman_dcf"] = ackman_scores["valuation"]

    if munger_scores:
        if "moat" in munger_scores:
            scores["munger_moat"] = munger_scores["moat"]
        if "predictability" in munger_scores:
            scores["munger_predictability"] = munger_scores["predictability"]

    if graham_scores:
        if "strength" in graham_scores:
            scores["graham_strength"] = graham_scores["strength"]
        if "valuation" in graham_scores:
            scores["graham_valuation"] = graham_scores["valuation"]

    if technical_signal:
        # Technical is already a signal, convert to score format
        conf = technical_signal.get("confidence", 50) / 100
        if technical_signal.get("signal") == "bullish":
            scores["technical_ensemble"] = {"score": conf, "max_score": 1.0}
        elif technical_signal.get("signal") == "bearish":
            scores["technical_ensemble"] = {"score": 1 - conf, "max_score": 1.0}
        else:
            scores["technical_ensemble"] = {"score": 0.5, "max_score": 1.0}

    return scores
