"""Unit testy pro src/tools/api.py - Financial API wrapper."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.data.cache import Cache
from src.data.models import CompanyNews, FinancialMetrics, InsiderTrade, LineItem, Price
from src.exceptions import APIKeyError, APIRateLimitError, APIResponseError, DataFetchError
from src.tools.api import (
    get_company_news,
    get_financial_metrics,
    get_insider_trades,
    get_market_cap,
    get_prices,
    prices_to_df,
    search_line_items,
)


@pytest.fixture(autouse=True)
def fresh_cache():
    """Reset global cache before each test."""
    import src.tools.api as api_module

    api_module._cache = Cache()
    yield
    api_module._cache = Cache()


class TestGetPrices:
    @patch("src.tools.api._make_api_request")
    def test_successful_fetch(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ticker": "AAPL",
            "prices": [
                {"open": 150.0, "close": 155.0, "high": 156.0, "low": 149.0, "volume": 1000000, "time": "2024-01-15"}
            ],
        }
        mock_request.return_value = mock_response

        result = get_prices("AAPL", "2024-01-01", "2024-01-31", api_key="test-key")
        assert len(result) == 1
        assert isinstance(result[0], Price)
        assert result[0].close == 155.0

    @patch("src.tools.api._make_api_request")
    def test_empty_response(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ticker": "AAPL", "prices": []}
        mock_request.return_value = mock_response

        result = get_prices("AAPL", "2024-01-01", "2024-01-31", api_key="test-key")
        assert result == []

    def test_missing_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(APIKeyError):
                get_prices("AAPL", "2024-01-01", "2024-01-31")

    @patch("src.tools.api._make_api_request")
    def test_api_error_response(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_request.return_value = mock_response

        with pytest.raises(APIResponseError):
            get_prices("AAPL", "2024-01-01", "2024-01-31", api_key="test-key")

    @patch("src.tools.api._make_api_request")
    def test_caching_works(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ticker": "AAPL",
            "prices": [
                {"open": 150.0, "close": 155.0, "high": 156.0, "low": 149.0, "volume": 1000000, "time": "2024-01-15"}
            ],
        }
        mock_request.return_value = mock_response

        # First call - hits API
        result1 = get_prices("AAPL", "2024-01-01", "2024-01-31", api_key="test-key")
        # Second call - should use cache
        result2 = get_prices("AAPL", "2024-01-01", "2024-01-31", api_key="test-key")

        assert mock_request.call_count == 1  # Only called once
        assert len(result1) == len(result2)


class TestGetFinancialMetrics:
    @patch("src.tools.api._make_api_request")
    def test_successful_fetch(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        # FinancialMetrics requires all fields explicitly
        metric_data = {
            "ticker": "AAPL", "report_period": "2024-Q1", "period": "ttm", "currency": "USD",
            "market_cap": 3000000000000.0, "enterprise_value": None,
            "price_to_earnings_ratio": None, "price_to_book_ratio": None,
            "price_to_sales_ratio": None, "enterprise_value_to_ebitda_ratio": None,
            "enterprise_value_to_revenue_ratio": None, "free_cash_flow_yield": None,
            "peg_ratio": None, "gross_margin": None, "operating_margin": None,
            "net_margin": None, "return_on_equity": None, "return_on_assets": None,
            "return_on_invested_capital": None, "asset_turnover": None,
            "inventory_turnover": None, "receivables_turnover": None,
            "days_sales_outstanding": None, "operating_cycle": None,
            "working_capital_turnover": None, "current_ratio": None,
            "quick_ratio": None, "cash_ratio": None, "operating_cash_flow_ratio": None,
            "debt_to_equity": None, "debt_to_assets": None, "interest_coverage": None,
            "revenue_growth": None, "earnings_growth": None, "book_value_growth": None,
            "earnings_per_share_growth": None, "free_cash_flow_growth": None,
            "operating_income_growth": None, "ebitda_growth": None, "payout_ratio": None,
            "earnings_per_share": None, "book_value_per_share": None,
            "free_cash_flow_per_share": None,
        }
        mock_response.json.return_value = {"financial_metrics": [metric_data]}
        mock_request.return_value = mock_response

        result = get_financial_metrics("AAPL", "2024-03-31", api_key="test-key")
        assert len(result) == 1
        assert isinstance(result[0], FinancialMetrics)
        assert result[0].market_cap == 3000000000000.0

    def test_missing_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(APIKeyError):
                get_financial_metrics("AAPL", "2024-03-31")


class TestSearchLineItems:
    @patch("src.tools.api._make_api_request")
    def test_successful_search(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "search_results": [
                {"ticker": "AAPL", "report_period": "2024-Q1", "period": "ttm", "currency": "USD", "revenue": 100e9}
            ]
        }
        mock_request.return_value = mock_response

        result = search_line_items("AAPL", ["revenue"], "2024-03-31", api_key="test-key")
        assert len(result) == 1
        assert isinstance(result[0], LineItem)

    def test_missing_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(APIKeyError):
                search_line_items("AAPL", ["revenue"], "2024-03-31")


class TestGetInsiderTrades:
    @patch("src.tools.api._make_api_request")
    def test_successful_fetch(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "insider_trades": [
                {
                    "ticker": "AAPL", "filing_date": "2024-01-16", "name": "Tim Cook",
                    "transaction_shares": 50000.0, "issuer": "Apple Inc.", "title": "CEO",
                    "is_board_director": False, "transaction_date": "2024-01-15",
                    "transaction_price_per_share": 185.0, "transaction_value": 9250000.0,
                    "shares_owned_before_transaction": 1000000.0,
                    "shares_owned_after_transaction": 950000.0, "security_title": "Common Stock",
                }
            ]
        }
        mock_request.return_value = mock_response

        result = get_insider_trades("AAPL", "2024-03-31", api_key="test-key")
        assert len(result) == 1
        assert isinstance(result[0], InsiderTrade)

    @patch("src.tools.api._make_api_request")
    def test_empty_response(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"insider_trades": []}
        mock_request.return_value = mock_response

        result = get_insider_trades("AAPL", "2024-03-31", api_key="test-key")
        assert result == []


class TestGetCompanyNews:
    @patch("src.tools.api._make_api_request")
    def test_successful_fetch(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "news": [
                {
                    "ticker": "AAPL",
                    "title": "Apple Earnings",
                    "author": "J. Doe",
                    "source": "Reuters",
                    "date": "2024-01-15",
                    "url": "https://example.com",
                }
            ]
        }
        mock_request.return_value = mock_response

        result = get_company_news("AAPL", "2024-03-31", api_key="test-key")
        assert len(result) == 1
        assert isinstance(result[0], CompanyNews)
        assert result[0].title == "Apple Earnings"


class TestPricesToDf:
    def test_converts_to_dataframe(self):
        prices = [
            Price(open=150.0, close=155.0, high=156.0, low=149.0, volume=1000000, time="2024-01-15"),
            Price(open=155.0, close=157.0, high=158.0, low=154.0, volume=900000, time="2024-01-16"),
        ]
        df = prices_to_df(prices)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "close" in df.columns
        assert "open" in df.columns
        assert df.index.name == "Date"

    def test_empty_prices_raises(self):
        # prices_to_df does not handle empty list - KeyError on missing 'time' column
        with pytest.raises(KeyError):
            prices_to_df([])

    def test_numeric_columns(self):
        prices = [Price(open=150.0, close=155.0, high=156.0, low=149.0, volume=1000000, time="2024-01-15")]
        df = prices_to_df(prices)
        assert df["close"].dtype in ["float64", "int64"]
        assert df["volume"].dtype in ["float64", "int64"]

    def test_sorted_by_date(self):
        prices = [
            Price(open=155.0, close=157.0, high=158.0, low=154.0, volume=900000, time="2024-01-16"),
            Price(open=150.0, close=155.0, high=156.0, low=149.0, volume=1000000, time="2024-01-15"),
        ]
        df = prices_to_df(prices)
        assert df.index[0] < df.index[1]
