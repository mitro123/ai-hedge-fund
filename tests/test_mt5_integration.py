"""
Tests for MetaTrader 5 Integration
Tests that need actual MT5 connection are skipped on Linux.
Model and configuration tests run everywhere.
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime

from src.integrations.metatrader5_integration import (
    MetaTrader5Integration,
    OrderType,
    TradeResult,
    AccountInfo,
    Position,
    MT5Config,
    MT5_AVAILABLE,
)


# ============================================================
# Tests that run EVERYWHERE (no MT5 needed)
# ============================================================

class TestMT5Models:
    """Test Pydantic models and enums - no MT5 required."""

    def test_mt5_config_creation(self):
        config = MT5Config(login=12345678, password="pw", server="srv", timeout=30000)
        assert config.login == 12345678
        assert config.timeout == 30000

    def test_mt5_config_defaults(self):
        config = MT5Config(login=1, password="p", server="s")
        assert config.timeout == 60000

    def test_order_type_enum(self):
        assert OrderType.BUY.value == "BUY"
        assert OrderType.SELL.value == "SELL"
        assert OrderType.BUY_LIMIT.value == "BUY_LIMIT"
        assert OrderType.SELL_LIMIT.value == "SELL_LIMIT"

    def test_trade_result_success(self):
        result = TradeResult(success=True, order_id=123, error_code=None,
                            error_message=None, price=1.13, volume=0.1)
        assert result.success is True
        assert result.order_id == 123
        assert result.price == 1.13

    def test_trade_result_failure(self):
        result = TradeResult(success=False, order_id=None, error_code=10006,
                            error_message="Rejected", price=None, volume=None)
        assert result.success is False
        assert result.error_code == 10006

    def test_account_info_model(self):
        info = AccountInfo(login=123, balance=10000, equity=10000, margin=0,
                          free_margin=10000, margin_level=0, currency="USD",
                          server="test", company="Test Broker")
        assert info.balance == 10000
        assert info.currency == "USD"

    def test_position_model(self):
        pos = Position(ticket=1, symbol="EURUSD", type="BUY", volume=0.1,
                      price_open=1.13, price_current=1.14, profit=100,
                      swap=-2.5, comment="AI Trade")
        assert pos.profit == 100
        assert pos.symbol == "EURUSD"

    def test_position_model_dump(self):
        pos = Position(ticket=1, symbol="EURUSD", type="BUY", volume=0.1,
                      price_open=1.13, price_current=1.14, profit=100,
                      swap=0, comment="")
        d = pos.model_dump()
        assert d["ticket"] == 1
        assert d["volume"] == 0.1


class TestMT5IntegrationBase:
    """Test integration class initialization - no MT5 connection needed."""

    def test_initialization_default(self):
        integration = MetaTrader5Integration()
        assert integration.config is not None
        assert not integration.connected

    def test_initialization_with_config(self):
        config = MT5Config(login=123, password="pw", server="srv")
        integration = MetaTrader5Integration(config)
        assert integration.config.login == 123

    def test_connection_without_mt5(self):
        """Connection should fail gracefully when MT5 not available."""
        with patch('src.integrations.metatrader5_integration.MT5_AVAILABLE', False):
            integration = MetaTrader5Integration()
            result = integration.connect()
            assert result is False

    def test_not_connected_by_default(self):
        integration = MetaTrader5Integration()
        assert integration.is_connected() is False

    def test_disconnect_when_not_connected(self):
        integration = MetaTrader5Integration()
        integration.disconnect()  # Should not crash
        assert integration.connected is False

    def test_get_positions_not_connected(self):
        integration = MetaTrader5Integration()
        positions = integration.get_positions()
        assert positions == []

    def test_place_order_not_connected(self):
        integration = MetaTrader5Integration()
        result = integration.place_order("EURUSD", OrderType.BUY, 0.1)
        assert result.success is False

    def test_close_position_not_connected(self):
        integration = MetaTrader5Integration()
        result = integration.close_position(12345)
        assert result.success is False


# ============================================================
# Tests that need MT5 mocking (still run everywhere via patch)
# ============================================================

@pytest.mark.skipif(not MT5_AVAILABLE, reason="MetaTrader5 not installed - mock tests need real MT5 module for proper patching")
class TestMT5WithMocks:
    """Tests requiring MT5 module for proper mock patching."""

    @patch('src.integrations.metatrader5_integration.mt5')
    def test_successful_connection(self, mock_mt5):
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_account = Mock()
        mock_account.login = 123
        mock_account.balance = 10000.0
        mock_account.equity = 10000.0
        mock_account.margin = 0.0
        mock_account.margin_free = 10000.0
        mock_account.margin_level = 0.0
        mock_account.currency = "USD"
        mock_account.server = "test"
        mock_account.company = "Test"
        mock_mt5.account_info.return_value = mock_account

        integration = MetaTrader5Integration()
        result = integration.connect(login=123, password="pw", server="srv")
        assert result is True
