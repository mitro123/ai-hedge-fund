"""Unit testy pro src/data/models.py - Pydantic data modely."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.data.models import (
    AgentStateData,
    AgentStateMetadata,
    AnalystSignal,
    CompanyFacts,
    CompanyNews,
    FinancialMetrics,
    InsiderTrade,
    LineItem,
    Portfolio,
    Position,
    Price,
    PriceResponse,
    TickerAnalysis,
)


class TestPrice:
    def test_create_valid_price(self):
        price = Price(open=150.0, close=155.0, high=156.0, low=149.0, volume=1000000, time="2024-01-15")
        assert price.open == 150.0
        assert price.close == 155.0
        assert price.high == 156.0
        assert price.low == 149.0
        assert price.volume == 1000000
        assert price.time == "2024-01-15"

    def test_price_model_dump(self):
        price = Price(open=150.0, close=155.0, high=156.0, low=149.0, volume=1000000, time="2024-01-15")
        data = price.model_dump()
        assert data["open"] == 150.0
        assert data["time"] == "2024-01-15"

    def test_price_missing_field_raises(self):
        with pytest.raises(PydanticValidationError):
            Price(open=150.0, close=155.0, high=156.0, low=149.0, time="2024-01-15")  # missing volume


class TestPriceResponse:
    def test_create_price_response(self):
        prices = [Price(open=150.0, close=155.0, high=156.0, low=149.0, volume=1000000, time="2024-01-15")]
        response = PriceResponse(ticker="AAPL", prices=prices)
        assert response.ticker == "AAPL"
        assert len(response.prices) == 1

    def test_empty_prices(self):
        response = PriceResponse(ticker="AAPL", prices=[])
        assert response.prices == []


class TestFinancialMetrics:
    def test_create_with_required_fields_only(self):
        metrics = FinancialMetrics(
            ticker="AAPL",
            report_period="2024-Q1",
            period="ttm",
            currency="USD",
            market_cap=None, enterprise_value=None, price_to_earnings_ratio=None,
            price_to_book_ratio=None, price_to_sales_ratio=None,
            enterprise_value_to_ebitda_ratio=None, enterprise_value_to_revenue_ratio=None,
            free_cash_flow_yield=None, peg_ratio=None, gross_margin=None,
            operating_margin=None, net_margin=None, return_on_equity=None,
            return_on_assets=None, return_on_invested_capital=None, asset_turnover=None,
            inventory_turnover=None, receivables_turnover=None, days_sales_outstanding=None,
            operating_cycle=None, working_capital_turnover=None, current_ratio=None,
            quick_ratio=None, cash_ratio=None, operating_cash_flow_ratio=None,
            debt_to_equity=None, debt_to_assets=None, interest_coverage=None,
            revenue_growth=None, earnings_growth=None, book_value_growth=None,
            earnings_per_share_growth=None, free_cash_flow_growth=None,
            operating_income_growth=None, ebitda_growth=None, payout_ratio=None,
            earnings_per_share=None, book_value_per_share=None, free_cash_flow_per_share=None,
        )
        assert metrics.ticker == "AAPL"
        assert metrics.market_cap is None
        assert metrics.price_to_earnings_ratio is None

    def test_create_with_optional_fields(self):
        metrics = FinancialMetrics(
            ticker="AAPL",
            report_period="2024-Q1",
            period="ttm",
            currency="USD",
            market_cap=3000000000000.0,
            price_to_earnings_ratio=28.5,
            return_on_equity=0.45,
            gross_margin=0.44,
            enterprise_value=None, price_to_book_ratio=None, price_to_sales_ratio=None,
            enterprise_value_to_ebitda_ratio=None, enterprise_value_to_revenue_ratio=None,
            free_cash_flow_yield=None, peg_ratio=None,
            operating_margin=None, net_margin=None,
            return_on_assets=None, return_on_invested_capital=None, asset_turnover=None,
            inventory_turnover=None, receivables_turnover=None, days_sales_outstanding=None,
            operating_cycle=None, working_capital_turnover=None, current_ratio=None,
            quick_ratio=None, cash_ratio=None, operating_cash_flow_ratio=None,
            debt_to_equity=None, debt_to_assets=None, interest_coverage=None,
            revenue_growth=None, earnings_growth=None, book_value_growth=None,
            earnings_per_share_growth=None, free_cash_flow_growth=None,
            operating_income_growth=None, ebitda_growth=None, payout_ratio=None,
            earnings_per_share=None, book_value_per_share=None, free_cash_flow_per_share=None,
        )
        assert metrics.market_cap == 3000000000000.0
        assert metrics.price_to_earnings_ratio == 28.5
        assert metrics.return_on_equity == 0.45

    def test_all_optional_fields_are_none_by_default(self):
        # FinancialMetrics fields are not truly optional (no default), so we pass None explicitly
        metrics = FinancialMetrics(
            ticker="AAPL", report_period="2024-Q1", period="ttm", currency="USD",
            market_cap=None, enterprise_value=None, price_to_earnings_ratio=None,
            price_to_book_ratio=None, price_to_sales_ratio=None,
            enterprise_value_to_ebitda_ratio=None, enterprise_value_to_revenue_ratio=None,
            free_cash_flow_yield=None, peg_ratio=None, gross_margin=None,
            operating_margin=None, net_margin=None, return_on_equity=None,
            return_on_assets=None, return_on_invested_capital=None, asset_turnover=None,
            inventory_turnover=None, receivables_turnover=None, days_sales_outstanding=None,
            operating_cycle=None, working_capital_turnover=None, current_ratio=None,
            quick_ratio=None, cash_ratio=None, operating_cash_flow_ratio=None,
            debt_to_equity=None, debt_to_assets=None, interest_coverage=None,
            revenue_growth=None, earnings_growth=None, book_value_growth=None,
            earnings_per_share_growth=None, free_cash_flow_growth=None,
            operating_income_growth=None, ebitda_growth=None, payout_ratio=None,
            earnings_per_share=None, book_value_per_share=None, free_cash_flow_per_share=None,
        )
        optional_fields = [
            "market_cap", "enterprise_value", "price_to_earnings_ratio", "price_to_book_ratio",
            "price_to_sales_ratio", "enterprise_value_to_ebitda_ratio", "gross_margin",
            "operating_margin", "net_margin", "return_on_equity", "return_on_assets",
            "current_ratio", "quick_ratio", "debt_to_equity", "revenue_growth",
        ]
        for field in optional_fields:
            assert getattr(metrics, field) is None


class TestLineItem:
    def test_create_with_extra_fields(self):
        item = LineItem(
            ticker="AAPL",
            report_period="2024-Q1",
            period="ttm",
            currency="USD",
            revenue=100000000.0,
            net_income=25000000.0,
        )
        assert item.ticker == "AAPL"
        assert item.revenue == 100000000.0
        assert item.net_income == 25000000.0

    def test_extra_fields_allowed(self):
        item = LineItem(
            ticker="AAPL",
            report_period="2024-Q1",
            period="ttm",
            currency="USD",
            custom_metric=42.0,
        )
        assert item.custom_metric == 42.0


class TestInsiderTrade:
    def test_create_insider_trade(self):
        trade = InsiderTrade(
            ticker="AAPL",
            issuer="Apple Inc.",
            name="Tim Cook",
            title="CEO",
            is_board_director=False,
            transaction_date="2024-01-15",
            transaction_shares=50000.0,
            transaction_price_per_share=185.0,
            transaction_value=9250000.0,
            shares_owned_before_transaction=1000000.0,
            shares_owned_after_transaction=950000.0,
            security_title="Common Stock",
            filing_date="2024-01-16",
        )
        assert trade.ticker == "AAPL"
        assert trade.name == "Tim Cook"
        assert trade.transaction_shares == 50000.0

    def test_minimal_insider_trade(self):
        trade = InsiderTrade(
            ticker="AAPL", filing_date="2024-01-16",
            issuer=None, name=None, title=None, is_board_director=None,
            transaction_date=None, transaction_shares=None,
            transaction_price_per_share=None, transaction_value=None,
            shares_owned_before_transaction=None, shares_owned_after_transaction=None,
            security_title=None,
        )
        assert trade.issuer is None
        assert trade.name is None
        assert trade.transaction_shares is None


class TestCompanyNews:
    def test_create_company_news(self):
        news = CompanyNews(
            ticker="AAPL",
            title="Apple Reports Q1 Earnings",
            author="John Doe",
            source="Reuters",
            date="2024-01-15",
            url="https://example.com/news",
            sentiment="positive",
        )
        assert news.ticker == "AAPL"
        assert news.sentiment == "positive"

    def test_sentiment_defaults_to_none(self):
        news = CompanyNews(
            ticker="AAPL",
            title="Apple News",
            author="Author",
            source="Source",
            date="2024-01-15",
            url="https://example.com",
        )
        assert news.sentiment is None


class TestCompanyFacts:
    def test_create_company_facts(self):
        facts = CompanyFacts(ticker="AAPL", name="Apple Inc.")
        assert facts.ticker == "AAPL"
        assert facts.name == "Apple Inc."
        assert facts.industry is None
        assert facts.market_cap is None

    def test_full_company_facts(self):
        facts = CompanyFacts(
            ticker="AAPL",
            name="Apple Inc.",
            industry="Technology",
            sector="Technology",
            exchange="NASDAQ",
            is_active=True,
            market_cap=3000000000000.0,
            number_of_employees=164000,
        )
        assert facts.is_active is True
        assert facts.number_of_employees == 164000


class TestPosition:
    def test_default_values(self):
        pos = Position(ticker="AAPL")
        assert pos.cash == 0.0
        assert pos.shares == 0

    def test_custom_values(self):
        pos = Position(ticker="AAPL", cash=10000.0, shares=50)
        assert pos.cash == 10000.0
        assert pos.shares == 50


class TestPortfolio:
    def test_create_portfolio(self):
        positions = {
            "AAPL": Position(ticker="AAPL", cash=5000.0, shares=10),
            "GOOGL": Position(ticker="GOOGL", cash=3000.0, shares=5),
        }
        portfolio = Portfolio(positions=positions, total_cash=100000.0)
        assert portfolio.total_cash == 100000.0
        assert len(portfolio.positions) == 2
        assert portfolio.positions["AAPL"].shares == 10

    def test_empty_portfolio(self):
        portfolio = Portfolio(positions={})
        assert portfolio.total_cash == 0.0
        assert len(portfolio.positions) == 0


class TestAnalystSignal:
    def test_create_bullish_signal(self):
        signal = AnalystSignal(signal="bullish", confidence=85.0, reasoning="Strong fundamentals")
        assert signal.signal == "bullish"
        assert signal.confidence == 85.0

    def test_create_with_dict_reasoning(self):
        signal = AnalystSignal(
            signal="bearish",
            confidence=70.0,
            reasoning={"key_factor": "declining revenue", "risk": "high"},
        )
        assert isinstance(signal.reasoning, dict)

    def test_all_fields_optional(self):
        signal = AnalystSignal()
        assert signal.signal is None
        assert signal.confidence is None
        assert signal.reasoning is None
        assert signal.max_position_size is None


class TestTickerAnalysis:
    def test_create_ticker_analysis(self):
        signals = {
            "warren_buffett": AnalystSignal(signal="bullish", confidence=80.0),
            "ben_graham": AnalystSignal(signal="neutral", confidence=60.0),
        }
        analysis = TickerAnalysis(ticker="AAPL", analyst_signals=signals)
        assert analysis.ticker == "AAPL"
        assert len(analysis.analyst_signals) == 2
        assert analysis.analyst_signals["warren_buffett"].signal == "bullish"


class TestAgentStateData:
    def test_create_agent_state_data(self):
        portfolio = Portfolio(
            positions={"AAPL": Position(ticker="AAPL", cash=0, shares=10)},
            total_cash=100000.0,
        )
        state_data = AgentStateData(
            tickers=["AAPL", "GOOGL"],
            portfolio=portfolio,
            start_date="2024-01-01",
            end_date="2024-03-31",
            ticker_analyses={},
        )
        assert state_data.tickers == ["AAPL", "GOOGL"]
        assert state_data.portfolio.total_cash == 100000.0


class TestAgentStateMetadata:
    def test_default_show_reasoning(self):
        metadata = AgentStateMetadata()
        assert metadata.show_reasoning is False

    def test_extra_fields_allowed(self):
        metadata = AgentStateMetadata(show_reasoning=True, model_name="gpt-4")
        assert metadata.show_reasoning is True
        assert metadata.model_name == "gpt-4"
