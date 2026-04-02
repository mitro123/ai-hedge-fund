"""Unit testy pro src/backtester.py - Backtesting engine."""

import pytest

from src.backtester import Backtester


def dummy_agent(*args, **kwargs):
    """Placeholder agent for testing."""
    return {}


class TestBacktesterInit:
    def test_initialization(self):
        bt = Backtester(
            agent=dummy_agent,
            tickers=["AAPL", "GOOGL"],
            start_date="2024-01-01",
            end_date="2024-03-31",
            initial_capital=100000.0,
        )
        assert bt.initial_capital == 100000.0
        assert bt.portfolio["cash"] == 100000.0
        assert "AAPL" in bt.portfolio["positions"]
        assert "GOOGL" in bt.portfolio["positions"]

    def test_initial_positions_are_zero(self):
        bt = Backtester(
            agent=dummy_agent, tickers=["AAPL"], start_date="2024-01-01", end_date="2024-03-31", initial_capital=50000.0
        )
        pos = bt.portfolio["positions"]["AAPL"]
        assert pos["long"] == 0
        assert pos["short"] == 0
        assert pos["long_cost_basis"] == 0.0
        assert pos["short_cost_basis"] == 0.0
        assert pos["short_margin_used"] == 0.0

    def test_realized_gains_initialized(self):
        bt = Backtester(
            agent=dummy_agent, tickers=["AAPL"], start_date="2024-01-01", end_date="2024-03-31", initial_capital=50000.0
        )
        assert bt.portfolio["realized_gains"]["AAPL"]["long"] == 0.0
        assert bt.portfolio["realized_gains"]["AAPL"]["short"] == 0.0

    def test_margin_requirement(self):
        bt = Backtester(
            agent=dummy_agent,
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-03-31",
            initial_capital=100000.0,
            initial_margin_requirement=0.5,
        )
        assert bt.portfolio["margin_requirement"] == 0.5


class TestExecuteTradeBuy:
    def setup_method(self):
        self.bt = Backtester(
            agent=dummy_agent,
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-03-31",
            initial_capital=100000.0,
        )

    def test_buy_basic(self):
        executed = self.bt.execute_trade("AAPL", "buy", 10, 150.0)
        assert executed == 10
        assert self.bt.portfolio["positions"]["AAPL"]["long"] == 10
        assert self.bt.portfolio["cash"] == 100000.0 - (10 * 150.0)

    def test_buy_updates_cost_basis(self):
        self.bt.execute_trade("AAPL", "buy", 10, 100.0)
        self.bt.execute_trade("AAPL", "buy", 10, 200.0)
        pos = self.bt.portfolio["positions"]["AAPL"]
        assert pos["long"] == 20
        assert pos["long_cost_basis"] == 150.0  # Weighted average

    def test_buy_insufficient_funds_partial(self):
        # Can only afford 6 shares at 150 with 1000 cash
        self.bt.portfolio["cash"] = 1000.0
        executed = self.bt.execute_trade("AAPL", "buy", 10, 150.0)
        assert executed == 6  # int(1000 / 150)
        assert self.bt.portfolio["positions"]["AAPL"]["long"] == 6

    def test_buy_zero_quantity(self):
        executed = self.bt.execute_trade("AAPL", "buy", 0, 150.0)
        assert executed == 0

    def test_buy_negative_quantity(self):
        executed = self.bt.execute_trade("AAPL", "buy", -5, 150.0)
        assert executed == 0

    def test_buy_completely_insufficient(self):
        self.bt.portfolio["cash"] = 10.0
        executed = self.bt.execute_trade("AAPL", "buy", 10, 150.0)
        assert executed == 0

    def test_buy_forces_integer_shares(self):
        executed = self.bt.execute_trade("AAPL", "buy", 10.7, 150.0)
        assert executed == 10
        assert self.bt.portfolio["positions"]["AAPL"]["long"] == 10


class TestExecuteTradeSell:
    def setup_method(self):
        self.bt = Backtester(
            agent=dummy_agent,
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-03-31",
            initial_capital=100000.0,
        )
        # Buy 20 shares at $100
        self.bt.execute_trade("AAPL", "buy", 20, 100.0)

    def test_sell_basic(self):
        executed = self.bt.execute_trade("AAPL", "sell", 10, 150.0)
        assert executed == 10
        assert self.bt.portfolio["positions"]["AAPL"]["long"] == 10
        # Cash: 100000 - 2000 (buy) + 1500 (sell) = 99500
        assert self.bt.portfolio["cash"] == 100000.0 - 2000.0 + 1500.0

    def test_sell_calculates_realized_gains(self):
        self.bt.execute_trade("AAPL", "sell", 10, 150.0)
        # Bought at 100, sold at 150, 10 shares = $500 gain
        assert self.bt.portfolio["realized_gains"]["AAPL"]["long"] == 500.0

    def test_sell_more_than_owned(self):
        executed = self.bt.execute_trade("AAPL", "sell", 30, 150.0)
        assert executed == 20  # Can only sell 20

    def test_sell_all_resets_cost_basis(self):
        self.bt.execute_trade("AAPL", "sell", 20, 150.0)
        assert self.bt.portfolio["positions"]["AAPL"]["long"] == 0
        assert self.bt.portfolio["positions"]["AAPL"]["long_cost_basis"] == 0.0

    def test_sell_with_loss(self):
        self.bt.execute_trade("AAPL", "sell", 10, 80.0)
        # Bought at 100, sold at 80, 10 shares = -$200 loss
        assert self.bt.portfolio["realized_gains"]["AAPL"]["long"] == -200.0


class TestExecuteTradeShort:
    def setup_method(self):
        self.bt = Backtester(
            agent=dummy_agent,
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-03-31",
            initial_capital=100000.0,
            initial_margin_requirement=0.5,
        )

    def test_short_basic(self):
        executed = self.bt.execute_trade("AAPL", "short", 10, 150.0)
        assert executed == 10
        pos = self.bt.portfolio["positions"]["AAPL"]
        assert pos["short"] == 10
        assert pos["short_cost_basis"] == 150.0
        # Cash: 100000 + 1500 (proceeds) - 750 (margin) = 100750
        assert self.bt.portfolio["cash"] == 100750.0

    def test_short_updates_margin(self):
        self.bt.execute_trade("AAPL", "short", 10, 150.0)
        pos = self.bt.portfolio["positions"]["AAPL"]
        assert pos["short_margin_used"] == 750.0  # 10 * 150 * 0.5
        assert self.bt.portfolio["margin_used"] == 750.0

    def test_short_insufficient_margin(self):
        self.bt.portfolio["cash"] = 100.0
        executed = self.bt.execute_trade("AAPL", "short", 10, 150.0)
        # Can afford margin for: int(100 / (150 * 0.5)) = int(1.33) = 1 share
        assert executed == 1

    def test_short_zero_margin_requirement(self):
        self.bt.portfolio["margin_requirement"] = 0.0
        executed = self.bt.execute_trade("AAPL", "short", 10, 150.0)
        # With 0 margin, max_quantity would be 0 in the insufficient branch
        # But since margin_required = 0 <= cash, it should succeed
        assert executed == 10


class TestExecuteTradeCover:
    def setup_method(self):
        self.bt = Backtester(
            agent=dummy_agent,
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-03-31",
            initial_capital=100000.0,
            initial_margin_requirement=0.5,
        )
        # Short 10 shares at $150
        self.bt.execute_trade("AAPL", "short", 10, 150.0)

    def test_cover_basic(self):
        initial_cash = self.bt.portfolio["cash"]
        executed = self.bt.execute_trade("AAPL", "cover", 5, 130.0)
        assert executed == 5
        assert self.bt.portfolio["positions"]["AAPL"]["short"] == 5

    def test_cover_more_than_shorted(self):
        executed = self.bt.execute_trade("AAPL", "cover", 20, 130.0)
        assert executed == 10  # Can only cover 10


class TestMultipleTradesSequence:
    def test_buy_sell_cycle(self):
        bt = Backtester(
            agent=dummy_agent,
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-03-31",
            initial_capital=10000.0,
        )
        bt.execute_trade("AAPL", "buy", 10, 100.0)
        assert bt.portfolio["cash"] == 9000.0
        bt.execute_trade("AAPL", "sell", 10, 120.0)
        assert bt.portfolio["cash"] == 10200.0
        assert bt.portfolio["realized_gains"]["AAPL"]["long"] == 200.0

    def test_multiple_tickers(self):
        bt = Backtester(
            agent=dummy_agent,
            tickers=["AAPL", "GOOGL"],
            start_date="2024-01-01",
            end_date="2024-03-31",
            initial_capital=100000.0,
        )
        bt.execute_trade("AAPL", "buy", 10, 150.0)
        bt.execute_trade("GOOGL", "buy", 5, 140.0)
        assert bt.portfolio["positions"]["AAPL"]["long"] == 10
        assert bt.portfolio["positions"]["GOOGL"]["long"] == 5
        assert bt.portfolio["cash"] == 100000.0 - 1500.0 - 700.0
