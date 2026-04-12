"""
Dynamic Fundamentals Engine
Computes time-varying fundamental metrics from quarterly financial data.
At each backtest date, uses ONLY data that was available at that time.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class DynamicFundamentals:
    """
    Fetches quarterly financials and computes fundamental metrics
    as they would have been known at any historical date.

    Key principle: NO FUTURE DATA LEAKAGE.
    At date T, we only use earnings reports filed BEFORE T.
    """

    # Earnings are typically reported ~1 month after quarter end
    REPORTING_LAG_DAYS = 45

    def __init__(self):
        self._cache: Dict[str, Dict] = {}

    def _fetch_quarterly_data(self, symbol: str) -> Dict:
        """Fetch quarterly + annual data. Annual fills gaps for older periods."""
        if symbol in self._cache:
            return self._cache[symbol]

        try:
            ticker = yf.Ticker(symbol)

            # Quarterly (last ~5 quarters) + Annual (last ~5 years)
            q_fin = ticker.quarterly_financials
            a_fin = ticker.financials
            q_bal = ticker.quarterly_balance_sheet
            a_bal = ticker.balance_sheet

            # Merge: quarterly has priority, annual covers older periods
            financials = self._merge_quarterly_annual(q_fin, a_fin)
            balance = self._merge_quarterly_annual(q_bal, a_bal)

            info = ticker.info
            hist = ticker.history(period="3y")

            data = {"financials": financials, "balance": balance, "info": info, "history": hist}
            self._cache[symbol] = data
            return data

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return {"financials": None, "balance": None, "info": {}, "history": pd.DataFrame()}

    @staticmethod
    def _merge_quarterly_annual(quarterly: Optional[pd.DataFrame], annual: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Merge quarterly and annual data - quarterly has priority, annual fills older dates."""
        if quarterly is None or quarterly.empty:
            return annual
        if annual is None or annual.empty:
            return quarterly

        result = quarterly.copy()
        for col in annual.columns:
            # Only add annual column if no quarterly data within 45 days
            has_match = any(abs((col - qc).days) < 45 for qc in result.columns)
            if not has_match:
                result = pd.concat([result, annual[[col]]], axis=1)

        return result.sort_index(axis=1, ascending=False)

    def _get_available_quarters(self, financials: pd.DataFrame, as_of_date: datetime) -> pd.DataFrame:
        """
        Get quarters whose earnings were REPORTED before as_of_date.
        Earnings for Q ending Dec 31 are typically reported ~Feb 1.
        """
        if financials is None or financials.empty:
            return pd.DataFrame()

        available_cols = []
        # Normalize as_of_date to naive datetime for comparison
        if hasattr(as_of_date, 'tzinfo') and as_of_date.tzinfo is not None:
            as_of_date = as_of_date.replace(tzinfo=None)

        for col in financials.columns:
            quarter_end = col
            # Strip timezone if present
            if hasattr(quarter_end, 'tzinfo') and quarter_end.tzinfo is not None:
                quarter_end = quarter_end.tz_localize(None)
            # Earnings available ~45 days after quarter end
            report_date = quarter_end + timedelta(days=self.REPORTING_LAG_DAYS)
            if report_date <= as_of_date:
                available_cols.append(col)

        if not available_cols:
            return pd.DataFrame()

        return financials[available_cols]

    def compute_metrics_at_date(self, symbol: str, as_of_date: datetime, price: float) -> Dict[str, Any]:
        """
        Compute fundamental metrics as they would have been known at as_of_date.

        Returns dict compatible with agent input format.
        """
        data = self._fetch_quarterly_data(symbol)
        info = data.get("info", {})
        financials = data.get("financials")
        balance = data.get("balance")

        # Get only quarters reported BEFORE as_of_date
        avail_fin = self._get_available_quarters(financials, as_of_date)
        avail_bal = self._get_available_quarters(balance, as_of_date)

        # Default values
        result = {
            "pe": 0, "forward_pe": 0, "pb": 0,
            "roe": 0, "roa": 0, "roic": 0,
            "debt_equity": 0,
            "revenue_growth": 0, "earnings_growth": 0,
            "earnings_quarterly_growth": 0,
            "gross_margin": 0, "operating_margin": 0, "profit_margin": 0,
            "ev_ebitda": 0, "fcf_yield": 0,
            "market_cap_b": 0, "peg": 0,
        }

        shares = info.get("sharesOutstanding", 0) or 0
        if shares == 0:
            shares = info.get("impliedSharesOutstanding", 1e9) or 1e9

        market_cap = price * shares
        result["market_cap_b"] = round(market_cap / 1e9, 1)

        # === INCOME STATEMENT METRICS ===
        if not avail_fin.empty and len(avail_fin.columns) >= 1:
            latest_q = avail_fin.columns[0]

            # TTM (trailing twelve months) = sum of last 4 quarters
            ttm_cols = avail_fin.columns[:4] if len(avail_fin.columns) >= 4 else avail_fin.columns

            def safe_ttm(row_name):
                if row_name in avail_fin.index:
                    vals = avail_fin.loc[row_name, ttm_cols].dropna()
                    return float(vals.sum()) if len(vals) > 0 else 0
                return 0

            def safe_val(row_name, col=None):
                col = col or latest_q
                if row_name in avail_fin.index:
                    v = avail_fin.loc[row_name, col]
                    return float(v) if pd.notna(v) else 0
                return 0

            ttm_revenue = safe_ttm("Total Revenue")
            ttm_net_income = safe_ttm("Net Income")
            ttm_gross_profit = safe_ttm("Gross Profit")
            ttm_operating_income = safe_ttm("Operating Income") or safe_ttm("EBIT")
            ttm_ebitda = safe_ttm("EBITDA") or safe_ttm("Normalized EBITDA")

            # EPS and PE
            ttm_eps = ttm_net_income / shares if shares > 0 else 0
            result["pe"] = round(price / ttm_eps, 2) if ttm_eps > 0 else 0

            # Margins
            if ttm_revenue > 0:
                result["gross_margin"] = round(ttm_gross_profit / ttm_revenue, 4)
                result["operating_margin"] = round(ttm_operating_income / ttm_revenue, 4)
                result["profit_margin"] = round(ttm_net_income / ttm_revenue, 4)

            # EV/EBITDA
            if ttm_ebitda > 0:
                # Simplified EV = market_cap + debt - cash
                total_debt = 0
                cash = 0
                if not avail_bal.empty:
                    if "Total Debt" in avail_bal.index:
                        total_debt = float(avail_bal.loc["Total Debt"].iloc[0]) if pd.notna(avail_bal.loc["Total Debt"].iloc[0]) else 0
                    if "Cash And Cash Equivalents" in avail_bal.index:
                        cash = float(avail_bal.loc["Cash And Cash Equivalents"].iloc[0]) if pd.notna(avail_bal.loc["Cash And Cash Equivalents"].iloc[0]) else 0

                ev = market_cap + total_debt - cash
                result["ev_ebitda"] = round(ev / ttm_ebitda, 2) if ttm_ebitda > 0 else 0

            # FCF yield (simplified: net income + depreciation - capex proxy)
            if market_cap > 0:
                result["fcf_yield"] = round(ttm_net_income * 0.8 / market_cap, 4)  # Rough proxy

            # === GROWTH RATES (YoY) ===
            # Find pairs of periods ~1 year apart (avoid mixing quarterly/annual)
            col_dates = list(avail_fin.columns)
            recent_col = col_dates[0]
            yoy_col = None

            # Find the column closest to 365 days before the most recent
            target_date = recent_col - timedelta(days=365)
            best_diff = 999
            for c in col_dates[1:]:
                diff = abs((c - target_date).days)
                if diff < best_diff and diff < 120:  # Within 4 months of 1-year-ago
                    best_diff = diff
                    yoy_col = c

            if yoy_col is not None:
                recent_rev = safe_val("Total Revenue", recent_col)
                yoy_rev = safe_val("Total Revenue", yoy_col)
                recent_ni = safe_val("Net Income", recent_col)
                yoy_ni = safe_val("Net Income", yoy_col)

                if yoy_rev > 0 and recent_rev > 0:
                    g = round((recent_rev / yoy_rev - 1), 4)
                    if abs(g) < 5.0:  # Sanity check: >500% growth is likely data mismatch
                        result["revenue_growth"] = g
                if yoy_ni > 0 and recent_ni > 0:
                    g = round((recent_ni / yoy_ni - 1), 4)
                    if abs(g) < 10.0:  # Sanity: >1000% is data mismatch
                        result["earnings_growth"] = g
                        result["earnings_quarterly_growth"] = g
            elif len(col_dates) >= 2:
                # Sequential comparison as fallback
                q1_rev = safe_val("Total Revenue", col_dates[0])
                q2_rev = safe_val("Total Revenue", col_dates[1])
                if q2_rev > 0:
                    result["revenue_growth"] = round((q1_rev / q2_rev - 1), 4)

            # PEG
            if result["pe"] > 0 and result["earnings_growth"] > 0:
                result["peg"] = round(result["pe"] / (result["earnings_growth"] * 100), 2)

        # === BALANCE SHEET ===
        if not avail_bal.empty:
            latest_bs = avail_bal.columns[0]

            def safe_bs(row_name):
                if row_name in avail_bal.index:
                    v = avail_bal.loc[row_name, latest_bs]
                    return float(v) if pd.notna(v) else 0
                return 0

            total_assets = safe_bs("Total Assets")
            total_equity = safe_bs("Stockholders Equity") or safe_bs("Total Equity Gross Minority Interest")
            total_debt = safe_bs("Total Debt")
            total_liabilities = safe_bs("Total Liabilities Net Minority Interest")

            # P/B
            if total_equity > 0:
                result["pb"] = round(market_cap / total_equity, 2)
                result["roe"] = round((result.get("profit_margin", 0) * (safe_ttm("Total Revenue") if not avail_fin.empty else 0)) / total_equity * 100, 2) if avail_fin is not None and not avail_fin.empty else 0

            # ROA
            if total_assets > 0:
                result["roa"] = round(ttm_net_income / total_assets * 100, 2) if not avail_fin.empty else 0

            # D/E
            if total_equity > 0:
                result["debt_equity"] = round(total_debt / total_equity, 2) if total_debt > 0 else 0

            # ROIC
            invested_capital = total_equity + total_debt
            if invested_capital > 0 and not avail_fin.empty:
                ttm_nopat = ttm_operating_income * 0.75  # After tax
                result["roic"] = round(ttm_nopat / invested_capital * 100, 2)

        # Forward PE (estimate: current PE * (1 - growth_rate))
        if result["pe"] > 0 and result["earnings_growth"] > 0:
            result["forward_pe"] = round(result["pe"] / (1 + result["earnings_growth"]), 2)

        return result


def safe_ttm_placeholder():
    """Placeholder to avoid undefined in nested scope."""
    return 0
