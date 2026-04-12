"""
Tests for MetaTrader 5 Integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

try:
    import MetaTrader5
    HAS_MT5 = True
except ImportError:
    HAS_MT5 = False

pytestmark = pytest.mark.skipif(not HAS_MT5, reason="MetaTrader5 not installed")

from src.integrations.metatrader5_integration import (
    MetaTrader5Integration,
    OrderType,
    TradeResult,
    AccountInfo,
    Position,
    MT5Config,
    is_mt5_available,
    get_mt5_integration
)
from src.agents.mt5_trading_agent import MT5TradingAgent, get_mt5_trading_agent


class TestMT5Integration:
    """Test cases for MetaTrader 5 integration."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = MT5Config(
            login=12345678,
            password="test_password",
            server="test_server"
        )
        self.integration = MetaTrader5Integration(self.config)
    
    def test_mt5_config_creation(self):
        """Test MT5Config creation."""
        config = MT5Config(
            login=12345678,
            password="password",
            server="server",
            timeout=30000
        )
        
        assert config.login == 12345678
        assert config.password == "password"
        assert config.server == "server"
        assert config.timeout == 30000
    
    def test_integration_initialization(self):
        """Test integration initialization."""
        integration = MetaTrader5Integration()
        assert integration.config is not None
        assert not integration.connected
        assert integration.account_info is None
    
    @patch('src.integrations.metatrader5_integration.MT5_AVAILABLE', True)
    @patch('src.integrations.metatrader5_integration.mt5')
    def test_successful_connection(self, mock_mt5):
        """Test successful MT5 connection."""
        # Mock MT5 responses
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        
        mock_account_info = Mock()
        mock_account_info.login = 12345678
        mock_account_info.balance = 10000.0
        mock_account_info.equity = 10000.0
        mock_account_info.margin = 0.0
        mock_account_info.margin_free = 10000.0
        mock_account_info.margin_level = 0.0
        mock_account_info.currency = "USD"
        mock_account_info.server = "test_server"
        mock_account_info.company = "Test Broker"
        
        mock_mt5.account_info.return_value = mock_account_info
        
        # Test connection
        result = self.integration.connect(
            login=12345678,
            password="password",
            server="server"
        )
        
        assert result is True
        assert self.integration.connected is True
        assert self.integration.account_info is not None
        assert self.integration.account_info.login == 12345678
    
    @patch('src.integrations.metatrader5_integration.MT5_AVAILABLE', True)
    @patch('src.integrations.metatrader5_integration.mt5')
    def test_failed_connection(self, mock_mt5):
        """Test failed MT5 connection."""
        mock_mt5.initialize.return_value = False
        mock_mt5.last_error.return_value = (1, "Connection failed")
        
        result = self.integration.connect()
        
        assert result is False
        assert self.integration.connected is False
    
    def test_connection_without_mt5_package(self):
        """Test connection when MT5 package is not available."""
        with patch('src.integrations.metatrader5_integration.MT5_AVAILABLE', False):
            integration = MetaTrader5Integration()
            result = integration.connect()
            assert result is False
    
    @patch('src.integrations.metatrader5_integration.MT5_AVAILABLE', True)
    @patch('src.integrations.metatrader5_integration.mt5')
    def test_get_historical_data(self, mock_mt5):
        """Test getting historical data."""
        self.integration.connected = True
        
        # Mock historical data
        mock_rates = [
            {'time': 1640995200, 'open': 1.1300, 'high': 1.1350, 'low': 1.1280, 'close': 1.1320, 'tick_volume': 1000},
            {'time': 1640998800, 'open': 1.1320, 'high': 1.1340, 'low': 1.1300, 'close': 1.1310, 'tick_volume': 1200},
        ]
        
        mock_mt5.copy_rates_from_pos.return_value = mock_rates
        mock_mt5.TIMEFRAME_H1 = 16385
        
        result = self.integration.get_historical_data("EURUSD", "H1", 2)
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert 'Open' in result.columns
        assert 'High' in result.columns
        assert 'Low' in result.columns
        assert 'Close' in result.columns
        assert 'Volume' in result.columns
    
    @patch('src.integrations.metatrader5_integration.MT5_AVAILABLE', True)
    @patch('src.integrations.metatrader5_integration.mt5')
    def test_place_buy_order(self, mock_mt5):
        """Test placing a BUY order."""
        self.integration.connected = True
        
        # Mock symbol info
        mock_symbol_info = Mock()
        mock_symbol_info.ask = 1.1300
        mock_symbol_info.bid = 1.1298
        mock_symbol_info.volume_min = 0.01
        mock_symbol_info.volume_max = 100.0
        mock_symbol_info.volume_step = 0.01
        
        mock_mt5.symbol_info.return_value = mock_symbol_info
        
        # Mock order result
        mock_result = Mock()
        mock_result.retcode = 10009  # TRADE_RETCODE_DONE
        mock_result.order = 123456
        mock_result.price = 1.1300
        mock_result.volume = 0.1
        
        mock_mt5.order_send.return_value = mock_result
        mock_mt5.TRADE_RETCODE_DONE = 10009
        mock_mt5.ORDER_TYPE_BUY = 0
        mock_mt5.TRADE_ACTION_DEAL = 1
        mock_mt5.ORDER_TIME_GTC = 0
        mock_mt5.ORDER_FILLING_IOC = 1
        
        result = self.integration.place_order(
            symbol="EURUSD",
            order_type=OrderType.BUY,
            volume=0.1
        )
        
        assert result.success is True
        assert result.order_id == 123456
        assert result.price == 1.1300
        assert result.volume == 0.1
    
    @patch('src.integrations.metatrader5_integration.MT5_AVAILABLE', True)
    @patch('src.integrations.metatrader5_integration.mt5')
    def test_place_order_failure(self, mock_mt5):
        """Test order placement failure."""
        self.integration.connected = True
        
        mock_mt5.symbol_info.return_value = None
        
        result = self.integration.place_order(
            symbol="INVALID",
            order_type=OrderType.BUY,
            volume=0.1
        )
        
        assert result.success is False
        assert result.error_message is not None and "not found" in result.error_message
    
    @patch('src.integrations.metatrader5_integration.MT5_AVAILABLE', True)
    @patch('src.integrations.metatrader5_integration.mt5')
    def test_close_position(self, mock_mt5):
        """Test closing a position."""
        self.integration.connected = True
        
        # Mock position info
        mock_position = Mock()
        mock_position.type = 0  # BUY position
        mock_position.symbol = "EURUSD"
        mock_position.volume = 0.1
        
        mock_mt5.positions_get.return_value = [mock_position]
        
        # Mock tick info
        mock_tick = Mock()
        mock_tick.bid = 1.1300
        mock_mt5.symbol_info_tick.return_value = mock_tick
        
        # Mock close result
        mock_result = Mock()
        mock_result.retcode = 10009  # TRADE_RETCODE_DONE
        mock_result.order = 123457
        mock_result.price = 1.1300
        mock_result.volume = 0.1
        
        mock_mt5.order_send.return_value = mock_result
        mock_mt5.TRADE_RETCODE_DONE = 10009
        mock_mt5.ORDER_TYPE_SELL = 1
        mock_mt5.TRADE_ACTION_DEAL = 1
        mock_mt5.ORDER_TIME_GTC = 0
        mock_mt5.ORDER_FILLING_IOC = 1
        
        result = self.integration.close_position(123456)
        
        assert result.success is True
        assert result.order_id == 123457
    
    def test_calculate_lot_size(self):
        """Test lot size calculation."""
        self.integration.connected = True
        
        with patch.object(self.integration, 'get_account_info') as mock_account, \
             patch.object(self.integration, 'get_symbol_info') as mock_symbol:
            
            # Mock account info
            mock_account.return_value = AccountInfo(
                login=12345678,
                balance=10000.0,
                equity=10000.0,
                margin=0.0,
                free_margin=10000.0,
                margin_level=0.0,
                currency="USD",
                server="test",
                company="test"
            )
            
            # Mock symbol info
            mock_symbol.return_value = {
                "point": 0.00001,
                "contract_size": 100000,
                "min_lot": 0.01,
                "max_lot": 100.0,
                "lot_step": 0.01
            }
            
            lot_size = self.integration.calculate_lot_size("EURUSD", 2.0, 50.0)
            
            assert lot_size > 0
            assert lot_size >= 0.01  # Min lot size
            assert lot_size <= 100.0  # Max lot size


class TestMT5TradingAgent:
    """Test cases for MT5 Trading Agent."""
    
    def setup_method(self):
        """Setup test environment."""
        self.agent = MT5TradingAgent()
    
    @patch('src.agents.mt5_trading_agent.is_mt5_available')
    def test_agent_initialization_without_mt5(self, mock_available):
        """Test agent initialization when MT5 is not available."""
        mock_available.return_value = False
        
        agent = MT5TradingAgent()
        assert agent.mt5 is not None
        assert not agent.connected
    
    @patch.object(MetaTrader5Integration, 'connect')
    def test_agent_connection(self, mock_connect):
        """Test agent connection."""
        mock_connect.return_value = True
        
        result = self.agent.connect(12345678, "password", "server")
        
        assert result is True
        assert self.agent.connected is True
    
    @patch.object(MetaTrader5Integration, 'get_account_info')
    @patch.object(MetaTrader5Integration, 'get_positions')
    def test_get_account_status(self, mock_positions, mock_account):
        """Test getting account status."""
        self.agent.connected = True
        
        # Mock account info
        mock_account.return_value = AccountInfo(
            login=12345678,
            balance=10000.0,
            equity=10000.0,
            margin=0.0,
            free_margin=10000.0,
            margin_level=0.0,
            currency="USD",
            server="test",
            company="test"
        )
        
        # Mock positions
        mock_positions.return_value = [
            Position(
                ticket=123456,
                symbol="EURUSD",
                type="BUY",
                volume=0.1,
                price_open=1.1300,
                price_current=1.1320,
                profit=20.0,
                swap=0.0,
                comment="test"
            )
        ]
        
        with patch.object(self.agent, 'is_connected', return_value=True):
            status = self.agent.get_account_status()
        
        assert status is not None
        assert status['connected'] is True
        assert status['positions_count'] == 1
        assert len(status['positions']) == 1
    
    @patch.object(MetaTrader5Integration, 'get_historical_data')
    @patch.object(MetaTrader5Integration, 'get_symbol_info')
    @patch('src.agents.mt5_trading_agent.call_llm')
    def test_analyze_market(self, mock_llm, mock_symbol, mock_data):
        """Test market analysis."""
        self.agent.connected = True
        
        # Mock historical data
        mock_data.return_value = pd.DataFrame({
            'Open': [1.1300, 1.1320, 1.1310],
            'High': [1.1350, 1.1340, 1.1330],
            'Low': [1.1280, 1.1300, 1.1290],
            'Close': [1.1320, 1.1310, 1.1325],
            'Volume': [1000, 1200, 1100]
        })
        
        # Mock symbol info
        mock_symbol.return_value = {
            'bid': 1.1320,
            'ask': 1.1322,
            'spread': 2
        }
        
        # Mock LLM response
        mock_analysis = Mock()
        mock_analysis.analysis = "Market is bullish. Recommend BUY."
        mock_llm.return_value = mock_analysis
        
        with patch.object(self.agent, 'is_connected', return_value=True):
            result = self.agent.analyze_market("EURUSD")
        
        assert result is not None
        assert result['symbol'] == "EURUSD"
        assert 'ai_analysis' in result
        assert 'current_price' in result
        assert 'technical_indicators' in result
    
    @patch.object(MetaTrader5Integration, 'place_order')
    def test_execute_trade(self, mock_place_order):
        """Test trade execution."""
        self.agent.connected = True
        
        # Mock successful order
        mock_place_order.return_value = TradeResult(
            success=True,
            order_id=123456,
            error_code=None,
            error_message=None,
            price=1.1300,
            volume=0.1
        )
        
        with patch.object(self.agent, 'is_connected', return_value=True):
            result = self.agent.execute_trade("EURUSD", "BUY", 0.1)
        
        assert result.success is True
        assert result.order_id == 123456
    
    def test_execute_trade_invalid_action(self):
        """Test trade execution with invalid action."""
        self.agent.connected = True
        
        with patch.object(self.agent, 'is_connected', return_value=True):
            result = self.agent.execute_trade("EURUSD", "INVALID", 0.1)
        
        assert result.success is False
        assert result.error_message is not None and "Invalid action" in result.error_message
    
    @patch.object(MetaTrader5Integration, 'calculate_lot_size')
    def test_calculate_position_size(self, mock_calculate):
        """Test position size calculation."""
        self.agent.connected = True
        mock_calculate.return_value = 0.05
        
        with patch.object(self.agent, 'is_connected', return_value=True):
            lot_size = self.agent.calculate_position_size("EURUSD", 2.0, 50.0)
        
        assert lot_size == 0.05
    
    def test_global_instances(self):
        """Test global instance functions."""
        integration = get_mt5_integration()
        agent = get_mt5_trading_agent()
        
        assert isinstance(integration, MetaTrader5Integration)
        assert isinstance(agent, MT5TradingAgent)


class TestTradeResult:
    """Test TradeResult model."""
    
    def test_successful_trade_result(self):
        """Test successful trade result creation."""
        result = TradeResult(
            success=True,
            order_id=123456,
            error_code=None,
            error_message=None,
            price=1.1300,
            volume=0.1
        )
        
        assert result.success is True
        assert result.order_id == 123456
        assert result.price == 1.1300
        assert result.volume == 0.1
    
    def test_failed_trade_result(self):
        """Test failed trade result creation."""
        result = TradeResult(
            success=False,
            order_id=None,
            error_code=1001,
            error_message="Insufficient margin",
            price=None,
            volume=None
        )
        
        assert result.success is False
        assert result.error_code == 1001
        assert result.error_message == "Insufficient margin"


if __name__ == "__main__":
    pytest.main([__file__])
