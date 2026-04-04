"""
Portfolio Intelligence - Event-driven rotation and smart portfolio construction.
Rotates based on DATA TRIGGERS, not calendar.
Constructs portfolio with multiple buckets: core, growth, unicorns, defensive.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================
# ROTATION TRIGGERS - Data-driven, not time-driven
# ============================================================

def check_exit_triggers(ticker: str, data: dict, position: dict) -> Optional[str]:
    """
    Check if a stock should be SOLD based on data triggers.
    Returns reason string if should exit, None if should hold.
    """
    reasons = []

    # TRIGGER 1: Death cross (SMA50 < SMA200) + negative 6m momentum
    if not data.get("golden_cross", True) and not data.get("price_above_sma200", True):
        if data.get("momentum_6m", 0) < -0.15:
            reasons.append(f"Death cross + 6m momentum {data.get('momentum_6m',0)*100:+.0f}%")

    # TRIGGER 2: Analyst downgrade to SELL
    if data.get("analyst_score", 3.0) >= 4.0:
        reasons.append(f"Analyst consensus: SELL (score {data.get('analyst_score',0):.1f})")

    # TRIGGER 3: Earnings collapse (>30% decline) while PE expanding
    if data.get("earnings_growth", 0) < -0.30 and data.get("pe", 0) > 40:
        reasons.append(f"Earnings collapse {data.get('earnings_growth',0)*100:+.0f}% with PE {data.get('pe',0):.0f}")

    # TRIGGER 4: Revenue declining for growth stock
    if data.get("revenue_growth", 0) < -0.05:
        reasons.append(f"Revenue declining {data.get('revenue_growth',0)*100:+.0f}%")

    # TRIGGER 5: Position down >25% from cost basis (stop loss)
    cost_basis = position.get("long_cost_basis", 0)
    if cost_basis > 0 and data.get("price", 0) > 0:
        loss = (data["price"] / cost_basis - 1)
        if loss < -0.25:
            reasons.append(f"Stop loss: down {loss*100:+.0f}% from entry")

    # Need at least 2 triggers to sell (avoid false signals)
    if len(reasons) >= 2:
        return "; ".join(reasons)
    return None


def check_entry_triggers(ticker: str, data: dict, category: str) -> Tuple[bool, float, str]:
    """
    Check if a stock should be ADDED to portfolio.
    Returns (should_buy, conviction_score, reason).
    Conviction 0-100, higher = allocate more.
    """
    score = 0
    reasons = []

    # Analyst consensus BUY or STRONG_BUY
    analyst_score = data.get("analyst_score", 3.0)
    if analyst_score <= 1.5:
        score += 25; reasons.append(f"Wall Street STRONG BUY ({analyst_score:.1f})")
    elif analyst_score <= 2.0:
        score += 15; reasons.append(f"Wall Street BUY ({analyst_score:.1f})")
    elif analyst_score >= 3.5:
        score -= 20  # Avoid stocks analysts don't like

    # Upside to analyst target
    upside = data.get("upside_to_target", 0)
    if upside > 0.30:
        score += 20; reasons.append(f"Target upside {upside*100:.0f}%")
    elif upside > 0.15:
        score += 10

    # Earnings growth
    eg = data.get("earnings_growth", 0)
    if eg > 0.50:
        score += 20; reasons.append(f"Earnings surge +{eg*100:.0f}%")
    elif eg > 0.20:
        score += 10; reasons.append(f"Strong earnings +{eg*100:.0f}%")
    elif eg < -0.20:
        score -= 15

    # Revenue growth (especially important for unicorns)
    rg = data.get("revenue_growth", 0)
    if rg > 0.30:
        score += 15; reasons.append(f"Revenue +{rg*100:.0f}%")
    elif rg > 0.15:
        score += 8

    # Momentum (12m positive trend)
    m12 = data.get("momentum_12m", 0)
    if m12 > 0.30:
        score += 15; reasons.append(f"Strong momentum +{m12*100:.0f}%")
    elif m12 > 0.10:
        score += 8
    elif m12 < -0.10:
        score -= 10

    # Technical health
    if data.get("golden_cross", False):
        score += 5
    if data.get("price_above_sma200", False):
        score += 5

    # Quality metrics
    roe = data.get("roe", 0)
    if roe > 25:
        score += 10; reasons.append(f"High ROE {roe:.0f}%")

    margin = data.get("gross_margin", 0)
    if margin > 0.60:
        score += 5

    # Relative strength vs S&P
    rs = data.get("relative_strength_vs_sp500", 0)
    if rs > 0.15:
        score += 10; reasons.append(f"Outperforming S&P by {rs*100:.0f}%")

    # UNICORN BONUS: Small cap + high growth = extra conviction
    if category == "unicorn":
        mcap = data.get("market_cap_b", 0)
        if mcap < 50 and rg > 0.20:
            score += 15; reasons.append(f"Unicorn: ${mcap:.0f}B cap + {rg*100:.0f}% growth")
        if mcap < 20 and rg > 0.30:
            score += 10; reasons.append("Early-stage high growth")

    should_buy = score >= 40
    return should_buy, max(0, min(100, score)), "; ".join(reasons) if reasons else "Mixed signals"


# ============================================================
# PORTFOLIO CONSTRUCTION
# ============================================================

def construct_portfolio_allocation(
    ranked_stocks: List[Tuple[str, float, str, dict]],  # (ticker, conviction, category, data)
    initial_cash: float,
    max_positions: int = 10,
) -> Dict[str, Dict]:
    """
    Construct a balanced portfolio with multiple buckets.

    Target allocation:
    - Core (stable): 30-40% of portfolio
    - Growth (proven growth): 25-35%
    - Unicorn (high potential): 15-25%
    - Defensive/Cyclical: 5-15%

    Within each bucket, allocate proportional to conviction score.
    """
    BUCKET_TARGETS = {
        "core": (0.30, 0.40),      # min 30%, max 40%
        "growth": (0.25, 0.35),
        "unicorn": (0.15, 0.25),
        "cyclical": (0.05, 0.15),
        "defensive": (0.05, 0.15),
        "special": (0.00, 0.10),
    }

    # Group by category
    by_category = {}
    for ticker, conviction, category, data in ranked_stocks:
        by_category.setdefault(category, []).append((ticker, conviction, data))

    # Sort each category by conviction
    for cat in by_category:
        by_category[cat].sort(key=lambda x: x[1], reverse=True)

    allocations = {}
    remaining_cash = initial_cash
    positions_used = 0

    # First pass: allocate minimum to each category with top picks
    for cat, (min_pct, max_pct) in BUCKET_TARGETS.items():
        if cat not in by_category or positions_used >= max_positions:
            continue

        stocks = by_category[cat]
        # How many from this category (at least 1 if available, up to proportional)
        cat_slots = max(1, min(len(stocks), int(max_positions * max_pct)))
        cat_budget = initial_cash * min_pct

        for ticker, conviction, data in stocks[:cat_slots]:
            if positions_used >= max_positions:
                break

            price = data.get("price", 0)
            if price <= 0:
                continue

            # Allocation based on conviction within bucket budget
            alloc_pct = (conviction / 100) * (cat_budget / initial_cash)
            alloc_amount = initial_cash * max(alloc_pct, 0.05)  # Minimum 5% per position
            alloc_amount = min(alloc_amount, remaining_cash * 0.30)  # Max 30% of remaining

            shares = int(alloc_amount / price)
            if shares <= 0:
                continue

            allocations[ticker] = {
                "shares": shares,
                "amount": shares * price,
                "category": cat,
                "conviction": conviction,
                "price": price,
            }

            remaining_cash -= shares * price
            positions_used += 1

    # Second pass: deploy remaining cash into highest-conviction picks
    if remaining_cash > initial_cash * 0.05:
        all_ranked = sorted(ranked_stocks, key=lambda x: x[1], reverse=True)
        for ticker, conviction, category, data in all_ranked:
            if ticker in allocations or remaining_cash < initial_cash * 0.03:
                continue
            if positions_used >= max_positions:
                break

            price = data.get("price", 0)
            if price <= 0:
                continue

            alloc = min(remaining_cash * 0.40, initial_cash * 0.15)
            shares = int(alloc / price)
            if shares > 0:
                allocations[ticker] = {
                    "shares": shares,
                    "amount": shares * price,
                    "category": category,
                    "conviction": conviction,
                    "price": price,
                }
                remaining_cash -= shares * price
                positions_used += 1

    return allocations
