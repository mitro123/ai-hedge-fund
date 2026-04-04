"""
Adapter: Converts yfinance data to Financial Datasets API format.
This allows us to use the ORIGINAL agent analysis functions directly.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

from src.data.models import FinancialMetrics, LineItem

logger = logging.getLogger(__name__)


class YFinanceAdapter:
    """
    Converts yfinance data into the exact format that original agents expect.
    This lets us use the REAL agent analysis functions (DCF, moat scoring, etc.)
    without needing the Financial Datasets API key.
    """

    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def _get_ticker(self, symbol: str) -> yf.Ticker:
        if symbol not in self._cache:
            self._cache[symbol] = yf.Ticker(symbol)
        return self._cache[symbol]

    def get_financial_metrics(self, symbol: str, limit: int = 10) -> List[FinancialMetrics]:
        """
        Create FinancialMetrics objects from yfinance data.
        Returns list of metrics (most recent first), mimicking Financial Datasets API.
        """
        try:
            ticker = self._get_ticker(symbol)
            info = ticker.info
            q_fin = ticker.quarterly_financials
            a_fin = ticker.financials
            q_bal = ticker.quarterly_balance_sheet

            # Build metrics from quarterly + annual data
            metrics_list = []

            # Create current period metrics from info
            current = FinancialMetrics(
                ticker=symbol,
                report_period=datetime.now().strftime("%Y-%m-%d"),
                period="ttm",
                currency="USD",
                market_cap=info.get("marketCap"),
                enterprise_value=info.get("enterpriseValue"),
                price_to_earnings_ratio=info.get("trailingPE"),
                price_to_book_ratio=info.get("priceToBook"),
                price_to_sales_ratio=info.get("priceToSalesTrailing12Months"),
                enterprise_value_to_ebitda_ratio=info.get("enterpriseToEbitda"),
                enterprise_value_to_revenue_ratio=info.get("enterpriseToRevenue"),
                free_cash_flow_yield=((info.get("freeCashflow") or 0) / max(info.get("marketCap") or 1, 1)),
                peg_ratio=info.get("pegRatio"),
                gross_margin=info.get("grossMargins"),
                operating_margin=info.get("operatingMargins"),
                net_margin=info.get("profitMargins"),
                return_on_equity=info.get("returnOnEquity"),
                return_on_assets=info.get("returnOnAssets"),
                return_on_invested_capital=None,  # Not directly available
                asset_turnover=None,
                inventory_turnover=None,
                receivables_turnover=None,
                days_sales_outstanding=None,
                operating_cycle=None,
                working_capital_turnover=None,
                current_ratio=info.get("currentRatio"),
                quick_ratio=info.get("quickRatio"),
                cash_ratio=None,
                operating_cash_flow_ratio=None,
                debt_to_equity=(info.get("debtToEquity") or 0) / 100 if info.get("debtToEquity") else None,
                debt_to_assets=None,
                interest_coverage=None,
                revenue_growth=info.get("revenueGrowth"),
                earnings_growth=info.get("earningsGrowth"),
                book_value_growth=info.get("bookValue"),  # Will be used differently
                earnings_per_share_growth=None,
                free_cash_flow_growth=None,
                operating_income_growth=None,
                ebitda_growth=None,
                payout_ratio=info.get("payoutRatio"),
                earnings_per_share=info.get("trailingEps"),
                book_value_per_share=info.get("bookValue"),
                free_cash_flow_per_share=(info.get("freeCashflow") or 0) / max(info.get("sharesOutstanding") or 1, 1),
            )
            metrics_list.append(current)

            # Create historical metrics from annual financials (for moat/consistency analysis)
            if a_fin is not None and not a_fin.empty:
                for col in a_fin.columns[:limit - 1]:
                    try:
                        rev = float(a_fin.loc["Total Revenue", col]) if "Total Revenue" in a_fin.index else None
                        ni = float(a_fin.loc["Net Income", col]) if "Net Income" in a_fin.index else None
                        gp = float(a_fin.loc["Gross Profit", col]) if "Gross Profit" in a_fin.index else None
                        oi = float(a_fin.loc["Operating Income", col]) if "Operating Income" in a_fin.index else None

                        gm = gp / rev if (gp and rev and rev > 0) else None
                        om = oi / rev if (oi and rev and rev > 0) else None
                        nm = ni / rev if (ni and rev and rev > 0) else None

                        # Get equity for ROE
                        equity = None
                        if q_bal is not None and not q_bal.empty:
                            for bc in q_bal.columns:
                                if abs((bc - col).days) < 120 and "Stockholders Equity" in q_bal.index:
                                    eq_val = q_bal.loc["Stockholders Equity", bc]
                                    if pd.notna(eq_val):
                                        equity = float(eq_val)
                                    break

                        roe = ni / equity if (ni and equity and equity > 0) else None

                        hist_metric = FinancialMetrics(
                            ticker=symbol,
                            report_period=col.strftime("%Y-%m-%d"),
                            period="annual",
                            currency="USD",
                            market_cap=info.get("marketCap"),
                            enterprise_value=info.get("enterpriseValue"),
                            price_to_earnings_ratio=None,
                            price_to_book_ratio=None,
                            price_to_sales_ratio=None,
                            enterprise_value_to_ebitda_ratio=None,
                            enterprise_value_to_revenue_ratio=None,
                            free_cash_flow_yield=None,
                            peg_ratio=None,
                            gross_margin=gm,
                            operating_margin=om,
                            net_margin=nm,
                            return_on_equity=roe,
                            return_on_assets=None,
                            return_on_invested_capital=None,
                            asset_turnover=None,
                            inventory_turnover=None,
                            receivables_turnover=None,
                            days_sales_outstanding=None,
                            operating_cycle=None,
                            working_capital_turnover=None,
                            current_ratio=None,
                            quick_ratio=None,
                            cash_ratio=None,
                            operating_cash_flow_ratio=None,
                            debt_to_equity=None,
                            debt_to_assets=None,
                            interest_coverage=None,
                            revenue_growth=None,
                            earnings_growth=None,
                            book_value_growth=None,
                            earnings_per_share_growth=None,
                            free_cash_flow_growth=None,
                            operating_income_growth=None,
                            ebitda_growth=None,
                            payout_ratio=None,
                            earnings_per_share=None,
                            book_value_per_share=None,
                            free_cash_flow_per_share=None,
                        )
                        metrics_list.append(hist_metric)
                    except Exception:
                        continue

            return metrics_list[:limit]

        except Exception as e:
            logger.error(f"Error creating metrics for {symbol}: {e}")
            return []

    def get_line_items(self, symbol: str) -> List[LineItem]:
        """Create LineItem objects from yfinance quarterly financials."""
        try:
            ticker = self._get_ticker(symbol)
            q_fin = ticker.quarterly_financials
            a_fin = ticker.financials
            q_bal = ticker.quarterly_balance_sheet

            items = []
            fin_data = q_fin if q_fin is not None and not q_fin.empty else a_fin

            if fin_data is None or fin_data.empty:
                return items

            for col in fin_data.columns[:10]:
                try:
                    def safe_get(df, row, c):
                        if df is not None and row in df.index and c in df.columns:
                            v = df.loc[row, c]
                            return float(v) if pd.notna(v) else None
                        return None

                    item = LineItem(
                        ticker=symbol,
                        report_period=col.strftime("%Y-%m-%d"),
                        period="quarterly" if fin_data is q_fin else "annual",
                        currency="USD",
                    )
                    # Pre-initialize ALL fields agents might access (avoid AttributeError)
                    for field in [
                        "net_income", "revenue", "gross_profit", "operating_income",
                        "depreciation_and_amortization", "capital_expenditure",
                        "ebit", "ebitda", "operating_expense", "research_and_development",
                        "interest_expense", "earnings_per_share", "free_cash_flow",
                        "total_assets", "total_liabilities", "shareholders_equity",
                        "outstanding_shares", "total_debt", "cash_and_equivalents",
                        "current_assets", "current_liabilities", "working_capital",
                        "gross_margin", "operating_margin", "debt_to_equity",
                        "book_value_per_share", "free_cash_flow_per_share",
                        "dividends_and_other_cash_distributions",
                        "issuance_or_purchase_of_equity_shares",
                    ]:
                        setattr(item, field, None)

                    # Set financial fields from data
                    item.net_income = safe_get(fin_data, "Net Income", col)
                    item.revenue = safe_get(fin_data, "Total Revenue", col)
                    item.gross_profit = safe_get(fin_data, "Gross Profit", col)
                    item.operating_income = safe_get(fin_data, "Operating Income", col)
                    item.depreciation_and_amortization = safe_get(fin_data, "Reconciled Depreciation", col)
                    item.capital_expenditure = safe_get(fin_data, "Capital Expenditure", col) if "Capital Expenditure" in fin_data.index else None
                    item.ebit = safe_get(fin_data, "EBIT", col)
                    item.ebitda = safe_get(fin_data, "EBITDA", col) or safe_get(fin_data, "Normalized EBITDA", col)
                    item.operating_expense = safe_get(fin_data, "Operating Expense", col) or safe_get(fin_data, "Total Operating Expenses", col)
                    item.research_and_development = safe_get(fin_data, "Research And Development", col) or safe_get(fin_data, "Research Development", col)
                    item.interest_expense = safe_get(fin_data, "Interest Expense", col)
                    item.earnings_per_share = safe_get(fin_data, "Diluted EPS", col) or safe_get(fin_data, "Basic EPS", col)

                    # Compute free_cash_flow from components
                    ni = item.net_income
                    da = item.depreciation_and_amortization
                    ce = item.capital_expenditure
                    if ni is not None and da is not None and ce is not None:
                        item.free_cash_flow = ni + da + ce  # capex is negative
                    elif ni is not None:
                        item.free_cash_flow = ni * 0.8  # rough proxy
                    else:
                        item.free_cash_flow = None

                    # Balance sheet items
                    if q_bal is not None and not q_bal.empty:
                        for bc in q_bal.columns:
                            if abs((bc - col).days) < 60:
                                item.total_assets = safe_get(q_bal, "Total Assets", bc)
                                item.total_liabilities = safe_get(q_bal, "Total Liabilities Net Minority Interest", bc)
                                item.shareholders_equity = safe_get(q_bal, "Stockholders Equity", bc)
                                item.outstanding_shares = safe_get(q_bal, "Ordinary Shares Number", bc) or safe_get(q_bal, "Share Issued", bc)
                                item.total_debt = safe_get(q_bal, "Total Debt", bc)
                                item.cash_and_equivalents = safe_get(q_bal, "Cash And Cash Equivalents", bc) or safe_get(q_bal, "Cash Cash Equivalents And Short Term Investments", bc)
                                item.current_assets = safe_get(q_bal, "Current Assets", bc)
                                item.current_liabilities = safe_get(q_bal, "Current Liabilities", bc)
                                item.working_capital = (item.current_assets or 0) - (item.current_liabilities or 0) if item.current_assets else None
                                item.gross_margin = (item.gross_profit / item.revenue) if (item.gross_profit and item.revenue and item.revenue > 0) else None
                                item.operating_margin = (item.operating_income / item.revenue) if (item.operating_income and item.revenue and item.revenue > 0) else None
                                item.debt_to_equity = (item.total_debt / item.shareholders_equity) if (item.total_debt and item.shareholders_equity and item.shareholders_equity > 0) else None
                                # Computed per-share metrics
                                shares = item.outstanding_shares or 1
                                item.book_value_per_share = (item.shareholders_equity / shares) if item.shareholders_equity else None
                                if not getattr(item, 'earnings_per_share', None) and item.net_income:
                                    item.earnings_per_share = item.net_income / shares
                                item.free_cash_flow_per_share = (getattr(item, 'free_cash_flow', None) or 0) / shares if shares > 0 else None
                                # Dividends
                                item.dividends_and_other_cash_distributions = None
                                item.issuance_or_purchase_of_equity_shares = None
                                break

                    items.append(item)
                except Exception:
                    continue

            return items

        except Exception as e:
            logger.error(f"Error creating line items for {symbol}: {e}")
            return []

    def get_prices_df(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Get price DataFrame in format expected by technical analysis functions."""
        ticker = self._get_ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return pd.DataFrame()
        return hist.rename(columns={
            "Close": "close", "Open": "open", "High": "high",
            "Low": "low", "Volume": "volume",
        })

    def get_market_cap(self, symbol: str) -> Optional[float]:
        """Get current market cap."""
        ticker = self._get_ticker(symbol)
        return ticker.info.get("marketCap")
