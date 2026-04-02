"""Unit testy pro src/data/cache.py - In-memory cache."""

import pytest

from src.data.cache import Cache, get_cache


class TestCache:
    def setup_method(self):
        self.cache = Cache()

    # --- Prices ---

    def test_get_prices_empty(self):
        assert self.cache.get_prices("AAPL") is None

    def test_set_and_get_prices(self):
        prices = [
            {"open": 150.0, "close": 155.0, "high": 156.0, "low": 149.0, "volume": 1000000, "time": "2024-01-15"},
            {"open": 155.0, "close": 157.0, "high": 158.0, "low": 154.0, "volume": 900000, "time": "2024-01-16"},
        ]
        self.cache.set_prices("AAPL", prices)
        result = self.cache.get_prices("AAPL")
        assert result is not None
        assert len(result) == 2
        assert result[0]["time"] == "2024-01-15"

    def test_prices_merge_deduplication(self):
        prices1 = [
            {"open": 150.0, "close": 155.0, "high": 156.0, "low": 149.0, "volume": 1000000, "time": "2024-01-15"},
        ]
        prices2 = [
            {"open": 150.0, "close": 155.0, "high": 156.0, "low": 149.0, "volume": 1000000, "time": "2024-01-15"},
            {"open": 155.0, "close": 157.0, "high": 158.0, "low": 154.0, "volume": 900000, "time": "2024-01-16"},
        ]
        self.cache.set_prices("AAPL", prices1)
        self.cache.set_prices("AAPL", prices2)
        result = self.cache.get_prices("AAPL")
        assert len(result) == 2  # No duplicates

    # --- Financial Metrics ---

    def test_get_financial_metrics_empty(self):
        assert self.cache.get_financial_metrics("AAPL") is None

    def test_set_and_get_financial_metrics(self):
        metrics = [
            {"ticker": "AAPL", "report_period": "2024-Q1", "period": "ttm", "currency": "USD", "market_cap": 3e12},
        ]
        self.cache.set_financial_metrics("AAPL", metrics)
        result = self.cache.get_financial_metrics("AAPL")
        assert result is not None
        assert len(result) == 1
        assert result[0]["market_cap"] == 3e12

    def test_financial_metrics_merge_deduplication(self):
        metrics1 = [{"report_period": "2024-Q1", "market_cap": 3e12}]
        metrics2 = [{"report_period": "2024-Q1", "market_cap": 3.1e12}, {"report_period": "2024-Q2", "market_cap": 3.2e12}]
        self.cache.set_financial_metrics("AAPL", metrics1)
        self.cache.set_financial_metrics("AAPL", metrics2)
        result = self.cache.get_financial_metrics("AAPL")
        assert len(result) == 2  # Q1 deduplicated, Q2 added

    # --- Line Items ---

    def test_get_line_items_empty(self):
        assert self.cache.get_line_items("AAPL") is None

    def test_set_and_get_line_items(self):
        items = [{"report_period": "2024-Q1", "revenue": 100000000}]
        self.cache.set_line_items("AAPL", items)
        result = self.cache.get_line_items("AAPL")
        assert result is not None
        assert len(result) == 1

    # --- Insider Trades ---

    def test_get_insider_trades_empty(self):
        assert self.cache.get_insider_trades("AAPL") is None

    def test_set_and_get_insider_trades(self):
        trades = [{"filing_date": "2024-01-16", "name": "Tim Cook", "transaction_shares": 50000}]
        self.cache.set_insider_trades("AAPL", trades)
        result = self.cache.get_insider_trades("AAPL")
        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "Tim Cook"

    def test_insider_trades_merge_deduplication(self):
        trades1 = [{"filing_date": "2024-01-16", "name": "Tim Cook"}]
        trades2 = [{"filing_date": "2024-01-16", "name": "Tim Cook"}, {"filing_date": "2024-01-20", "name": "Jeff Williams"}]
        self.cache.set_insider_trades("AAPL", trades1)
        self.cache.set_insider_trades("AAPL", trades2)
        result = self.cache.get_insider_trades("AAPL")
        assert len(result) == 2

    # --- Company News ---

    def test_get_company_news_empty(self):
        assert self.cache.get_company_news("AAPL") is None

    def test_set_and_get_company_news(self):
        news = [{"date": "2024-01-15", "title": "Apple Earnings"}]
        self.cache.set_company_news("AAPL", news)
        result = self.cache.get_company_news("AAPL")
        assert result is not None
        assert len(result) == 1

    def test_company_news_merge_deduplication(self):
        news1 = [{"date": "2024-01-15", "title": "Apple Earnings"}]
        news2 = [{"date": "2024-01-15", "title": "Apple Earnings"}, {"date": "2024-01-16", "title": "Apple Update"}]
        self.cache.set_company_news("AAPL", news1)
        self.cache.set_company_news("AAPL", news2)
        result = self.cache.get_company_news("AAPL")
        assert len(result) == 2

    # --- Merge Logic ---

    def test_merge_data_with_empty_existing(self):
        new_data = [{"time": "2024-01-15"}, {"time": "2024-01-16"}]
        result = self.cache._merge_data(None, new_data, "time")
        assert len(result) == 2

    def test_merge_data_with_empty_new(self):
        existing = [{"time": "2024-01-15"}]
        result = self.cache._merge_data(existing, [], "time")
        assert len(result) == 1

    def test_merge_data_no_duplicates(self):
        existing = [{"time": "2024-01-15", "value": 100}]
        new_data = [{"time": "2024-01-16", "value": 200}]
        result = self.cache._merge_data(existing, new_data, "time")
        assert len(result) == 2

    def test_merge_data_with_duplicates(self):
        existing = [{"time": "2024-01-15", "value": 100}]
        new_data = [{"time": "2024-01-15", "value": 101}, {"time": "2024-01-16", "value": 200}]
        result = self.cache._merge_data(existing, new_data, "time")
        assert len(result) == 2
        # Existing value should be preserved (not overwritten)
        assert result[0]["value"] == 100

    # --- Different Tickers ---

    def test_different_tickers_isolated(self):
        self.cache.set_prices("AAPL", [{"time": "2024-01-15", "close": 150.0}])
        self.cache.set_prices("GOOGL", [{"time": "2024-01-15", "close": 140.0}])
        assert self.cache.get_prices("AAPL")[0]["close"] == 150.0
        assert self.cache.get_prices("GOOGL")[0]["close"] == 140.0
        assert self.cache.get_prices("MSFT") is None


class TestGetCache:
    def test_returns_cache_instance(self):
        cache = get_cache()
        assert isinstance(cache, Cache)

    def test_returns_singleton(self):
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2
