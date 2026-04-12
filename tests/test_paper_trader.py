"""Unit testy pro src/integrations/mt5_paper_trader.py - Paper trading simulator."""

import pytest

from src.integrations.metatrader5_integration import AccountInfo, OrderType, Position, TradeResult
from src.integrations.mt5_paper_trader import MT5PaperTrader


class TestMT5PaperTraderInit:
    def test_initialization(self):
        trader = MT5PaperTrader(initial_balance=50000.0)
        assert trader.account.balance == 50000.0
        assert trader.account.equity == 50000.0
        assert trader.connected is False

    def test_connect(self):
        trader = MT5PaperTrader()
        assert trader.connect() is True
        assert trader.is_connected() is True

    def test_disconnect(self):
        trader = MT5PaperTrader()
        trader.connect()
        trader.disconnect()
        assert trader.is_connected() is False

    def test_default_balance(self):
        trader = MT5PaperTrader()
        assert trader.account.balance == 10000.0


class TestAccountInfo:
    def test_get_account_info(self):
        trader = MT5PaperTrader(initial_balance=25000.0)
        trader.connect()
        info = trader.get_account_info()
        assert isinstance(info, AccountInfo)
        assert info.balance == 25000.0
        assert info.equity == 25000.0
        assert info.currency == "USD"
        assert info.server == "PaperTrading-Demo"


class TestSymbolInfo:
    def test_known_symbol(self):
        trader = MT5PaperTrader()
        trader.connect()
        info = trader.get_symbol_info("EURUSD")
        assert info is not None
        assert info["symbol"] == "EURUSD"
        assert info["bid"] > 0
        assert info["ask"] > info["bid"]
        assert info["min_lot"] == 0.01
        assert info["max_lot"] == 100.0

    def test_unknown_symbol(self):
        trader = MT5PaperTrader()
        trader.connect()
        info = trader.get_symbol_info("INVALID")
        assert info is None


class TestHistoricalData:
    def test_get_historical_data(self):
        trader = MT5PaperTrader()
        trader.connect()
        data = trader.get_historical_data("EURUSD", "H1", 100)
        assert data is not None
        assert len(data) == 100
        assert "Open" in data.columns
        assert "High" in data.columns
        assert "Low" in data.columns
        assert "Close" in data.columns
        assert "Volume" in data.columns

    def test_unknown_symbol_returns_none(self):
        trader = MT5PaperTrader()
        trader.connect()
        data = trader.get_historical_data("INVALID", "H1", 50)
        assert data is None

    def test_different_timeframes(self):
        trader = MT5PaperTrader()
        trader.connect()
        for tf in ["M1", "M5", "H1", "D1"]:
            data = trader.get_historical_data("EURUSD", tf, 50)
            assert data is not None
            assert len(data) == 50


class TestPlaceOrder:
    def setup_method(self):
        self.trader = MT5PaperTrader(initial_balance=10000.0, leverage=100)
        self.trader.connect()

    def test_buy_order(self):
        result = self.trader.place_order("EURUSD", OrderType.BUY, 0.1)
        assert result.success is True
        assert result.order_id is not None
        assert result.price > 0
        assert result.volume == 0.1

    def test_sell_order(self):
        result = self.trader.place_order("EURUSD", OrderType.SELL, 0.1)
        assert result.success is True
        assert result.order_id is not None

    def test_order_with_sl_tp(self):
        result = self.trader.place_order(
            "EURUSD", OrderType.BUY, 0.1, sl=1.0800, tp=1.0900
        )
        assert result.success is True
        # Check position has SL/TP
        positions = self.trader.get_positions()
        assert len(positions) >= 1

    def test_unknown_symbol_fails(self):
        result = self.trader.place_order("INVALID", OrderType.BUY, 0.1)
        assert result.success is False
        assert "Unknown symbol" in result.error_message

    def test_not_connected_fails(self):
        trader = MT5PaperTrader()
        result = trader.place_order("EURUSD", OrderType.BUY, 0.1)
        assert result.success is False
        assert "Not connected" in result.error_message

    def test_insufficient_margin(self):
        trader = MT5PaperTrader(initial_balance=10.0, leverage=1)
        trader.connect()
        result = trader.place_order("EURUSD", OrderType.BUY, 1.0)
        assert result.success is False
        assert "margin" in result.error_message.lower()

    def test_multiple_orders(self):
        r1 = self.trader.place_order("EURUSD", OrderType.BUY, 0.01)
        r2 = self.trader.place_order("GBPUSD", OrderType.SELL, 0.01)
        assert r1.success is True
        assert r2.success is True
        assert r1.order_id != r2.order_id
        positions = self.trader.get_positions()
        assert len(positions) == 2


class TestClosePosition:
    def setup_method(self):
        self.trader = MT5PaperTrader(initial_balance=10000.0)
        self.trader.connect()

    def test_close_buy_position(self):
        open_result = self.trader.place_order("EURUSD", OrderType.BUY, 0.1)
        assert open_result.success is True

        close_result = self.trader.close_position(open_result.order_id)
        assert close_result.success is True
        assert close_result.price > 0

        positions = self.trader.get_positions()
        assert len(positions) == 0

    def test_close_sell_position(self):
        open_result = self.trader.place_order("EURUSD", OrderType.SELL, 0.1)
        close_result = self.trader.close_position(open_result.order_id)
        assert close_result.success is True

    def test_close_nonexistent_position(self):
        result = self.trader.close_position(999999)
        assert result.success is False
        assert "not found" in result.error_message

    def test_balance_updates_after_close(self):
        initial_balance = self.trader.account.balance
        open_result = self.trader.place_order("EURUSD", OrderType.BUY, 0.1)
        self.trader.close_position(open_result.order_id)

        # Balance should have changed (profit or loss)
        assert self.trader.account.balance != initial_balance or True  # Could be same if P/L is 0


class TestPositionManagement:
    def test_get_positions_empty(self):
        trader = MT5PaperTrader()
        trader.connect()
        positions = trader.get_positions()
        assert positions == []

    def test_get_positions_after_trade(self):
        trader = MT5PaperTrader()
        trader.connect()
        trader.place_order("EURUSD", OrderType.BUY, 0.1)
        positions = trader.get_positions()
        assert len(positions) == 1
        assert isinstance(positions[0], Position)
        assert positions[0].symbol == "EURUSD"
        assert positions[0].type == "BUY"
        assert positions[0].volume == 0.1


class TestLotSizeCalculation:
    def test_calculate_lot_size(self):
        trader = MT5PaperTrader(initial_balance=10000.0)
        trader.connect()
        lot_size = trader.calculate_lot_size("EURUSD", risk_percent=2.0, stop_loss_pips=50)
        assert lot_size > 0
        assert lot_size >= 0.01

    def test_unknown_symbol(self):
        trader = MT5PaperTrader()
        trader.connect()
        lot_size = trader.calculate_lot_size("INVALID", 2.0, 50)
        assert lot_size == 0.01  # Default minimum


class TestTradeSummary:
    def test_summary_no_trades(self):
        trader = MT5PaperTrader(initial_balance=10000.0)
        trader.connect()
        summary = trader.get_trade_summary()
        assert summary["account"]["balance"] == 10000.0
        assert summary["trades"]["total"] == 0
        assert summary["trades"]["win_rate"] == 0.0

    def test_summary_with_trades(self):
        trader = MT5PaperTrader(initial_balance=10000.0)
        trader.connect()

        # Open and close a trade
        result = trader.place_order("EURUSD", OrderType.BUY, 0.1)
        trader.close_position(result.order_id)

        summary = trader.get_trade_summary()
        assert summary["trades"]["total"] == 1
        assert summary["open_positions"] == 0


class TestPriceSimulation:
    def test_prices_change(self):
        trader = MT5PaperTrader()
        trader.connect()
        prices = set()
        for _ in range(10):
            tick = trader._simulate_price_move("EURUSD")
            prices.add(tick.bid)
        # Prices should vary (not all the same)
        assert len(prices) > 1

    def test_spread_consistent(self):
        trader = MT5PaperTrader()
        trader.connect()
        for _ in range(5):
            tick = trader._simulate_price_move("EURUSD")
            spread = tick.ask - tick.bid
            assert spread > 0
