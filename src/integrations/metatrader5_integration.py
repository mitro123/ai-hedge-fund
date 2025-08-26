"""
MetaTrader 5 Integration for AI Hedge Fund
Provides connection to MT5 terminal for live trading execution.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Type-safe conditional import for MetaTrader5
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    # Create a stub object for type safety when MT5 is not available
    class MT5Stub:
        """Stub class for MetaTrader5 when package is not available."""
        def __getattr__(self, name):
            raise ImportError("MetaTrader5 package not installed. Install with: pip install MetaTrader5")
    
    mt5 = MT5Stub()  # type: ignore
    MT5_AVAILABLE = False
    logging.warning("MetaTrader5 package not installed. Install with: pip install MetaTrader5")

import pandas as pd
from pydantic import BaseModel, Field


class OrderType(Enum):
    """Order types for MetaTrader 5."""
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


class TradeResult(BaseModel):
    """Result of a trade operation."""
    success: bool = Field(description="Whether the trade was successful")
    order_id: Optional[int] = Field(description="Order ID if successful")
    error_code: Optional[int] = Field(description="Error code if failed")
    error_message: Optional[str] = Field(description="Error message if failed")
    price: Optional[float] = Field(description="Execution price")
    volume: Optional[float] = Field(description="Trade volume")


class AccountInfo(BaseModel):
    """MetaTrader 5 account information."""
    login: int = Field(description="Account login")
    balance: float = Field(description="Account balance")
    equity: float = Field(description="Account equity")
    margin: float = Field(description="Used margin")
    free_margin: float = Field(description="Free margin")
    margin_level: float = Field(description="Margin level percentage")
    currency: str = Field(description="Account currency")
    server: str = Field(description="Trading server")
    company: str = Field(description="Broker company")


class Position(BaseModel):
    """Open position information."""
    ticket: int = Field(description="Position ticket")
    symbol: str = Field(description="Trading symbol")
    type: str = Field(description="Position type (buy/sell)")
    volume: float = Field(description="Position volume")
    price_open: float = Field(description="Opening price")
    price_current: float = Field(description="Current price")
    profit: float = Field(description="Current profit/loss")
    swap: float = Field(description="Swap")
    comment: str = Field(description="Position comment")


@dataclass
class MT5Config:
    """MetaTrader 5 connection configuration."""
    login: Optional[int] = None
    password: Optional[str] = None
    server: Optional[str] = None
    path: Optional[str] = None
    timeout: int = 60000  # Connection timeout in milliseconds


class MetaTrader5Integration:
    """
    Integration class for connecting AI Hedge Fund with MetaTrader 5.
    Provides live trading capabilities through MT5 terminal.
    """
    
    def __init__(self, config: Optional[MT5Config] = None):
        """
        Initialize MetaTrader 5 integration.
        
        Args:
            config: MT5 connection configuration
        """
        self.config = config or MT5Config()
        self.connected = False
        self.account_info = None
        
        if not MT5_AVAILABLE:
            logging.error("MetaTrader5 package not available. Please install it first.")
            return
        
        logging.info("MetaTrader5 integration initialized")
    
    def connect(self, login: Optional[int] = None, password: Optional[str] = None, 
                server: Optional[str] = None) -> bool:
        """
        Connect to MetaTrader 5 terminal.
        
        Args:
            login: Trading account login
            password: Trading account password  
            server: Trading server name
            
        Returns:
            True if connection successful, False otherwise
        """
        if not MT5_AVAILABLE:
            logging.error("MetaTrader5 package not available")
            return False
        
        try:
            # Initialize MT5 connection
            if not mt5.initialize(
                path=self.config.path,
                login=login or self.config.login,
                password=password or self.config.password,
                server=server or self.config.server,
                timeout=self.config.timeout
            ):
                error = mt5.last_error()
                logging.error(f"Failed to initialize MT5: {error}")
                return False
            
            # Login if credentials provided
            if login and password and server:
                if not mt5.login(login, password, server):
                    error = mt5.last_error()
                    logging.error(f"Failed to login to MT5: {error}")
                    mt5.shutdown()
                    return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                logging.error("Failed to get account info")
                mt5.shutdown()
                return False
            
            self.account_info = AccountInfo(
                login=account_info.login,
                balance=account_info.balance,
                equity=account_info.equity,
                margin=account_info.margin,
                free_margin=account_info.margin_free,
                margin_level=account_info.margin_level,
                currency=account_info.currency,
                server=account_info.server,
                company=account_info.company
            )
            
            self.connected = True
            logging.info(f"Successfully connected to MT5 account {account_info.login}")
            return True
            
        except Exception as e:
            logging.error(f"Error connecting to MT5: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MetaTrader 5 terminal."""
        if MT5_AVAILABLE and self.connected:
            mt5.shutdown()
            self.connected = False
            logging.info("Disconnected from MT5")
    
    def is_connected(self) -> bool:
        """Check if connected to MT5."""
        return self.connected and MT5_AVAILABLE
    
    def get_account_info(self) -> Optional[AccountInfo]:
        """Get current account information."""
        if not self.is_connected():
            return None
        
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return None
            
            return AccountInfo(
                login=account_info.login,
                balance=account_info.balance,
                equity=account_info.equity,
                margin=account_info.margin,
                free_margin=account_info.margin_free,
                margin_level=account_info.margin_level,
                currency=account_info.currency,
                server=account_info.server,
                company=account_info.company
            )
        except Exception as e:
            logging.error(f"Error getting account info: {e}")
            return None
    
    def get_positions(self) -> List[Position]:
        """Get all open positions."""
        if not self.is_connected():
            return []
        
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append(Position(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    type="BUY" if pos.type == 0 else "SELL",
                    volume=pos.volume,
                    price_open=pos.price_open,
                    price_current=pos.price_current,
                    profit=pos.profit,
                    swap=pos.swap,
                    comment=pos.comment
                ))
            
            return result
            
        except Exception as e:
            logging.error(f"Error getting positions: {e}")
            return []
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information."""
        if not self.is_connected():
            return None
        
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None
            
            return {
                "symbol": symbol_info.name,
                "bid": symbol_info.bid,
                "ask": symbol_info.ask,
                "spread": symbol_info.spread,
                "digits": symbol_info.digits,
                "point": symbol_info.point,
                "min_lot": symbol_info.volume_min,
                "max_lot": symbol_info.volume_max,
                "lot_step": symbol_info.volume_step,
                "contract_size": symbol_info.trade_contract_size,
                "currency_base": symbol_info.currency_base,
                "currency_profit": symbol_info.currency_profit,
                "currency_margin": symbol_info.currency_margin
            }
            
        except Exception as e:
            logging.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, timeframe: str = "M1", 
                          count: int = 1000) -> Optional[pd.DataFrame]:
        """
        Get historical price data.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
            count: Number of bars to retrieve
            
        Returns:
            DataFrame with OHLCV data
        """
        if not self.is_connected():
            return None
        
        try:
            # Map timeframe strings to MT5 constants
            timeframe_map = {
                "M1": mt5.TIMEFRAME_M1,
                "M5": mt5.TIMEFRAME_M5,
                "M15": mt5.TIMEFRAME_M15,
                "M30": mt5.TIMEFRAME_M30,
                "H1": mt5.TIMEFRAME_H1,
                "H4": mt5.TIMEFRAME_H4,
                "D1": mt5.TIMEFRAME_D1,
                "W1": mt5.TIMEFRAME_W1,
                "MN1": mt5.TIMEFRAME_MN1
            }
            
            mt5_timeframe = timeframe_map.get(timeframe, mt5.TIMEFRAME_M1)
            
            # Get rates
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
            if rates is None:
                logging.error(f"Failed to get rates for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Rename columns to standard format
            df.rename(columns={
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'tick_volume': 'Volume'
            }, inplace=True)
            
            return df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
        except Exception as e:
            logging.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def place_order(self, symbol: str, order_type: OrderType, volume: float,
                   price: Optional[float] = None, sl: Optional[float] = None,
                   tp: Optional[float] = None, comment: str = "AI Hedge Fund") -> TradeResult:
        """
        Place a trading order.
        
        Args:
            symbol: Trading symbol
            order_type: Type of order (BUY, SELL, etc.)
            volume: Order volume in lots
            price: Order price (for limit/stop orders)
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            
        Returns:
            TradeResult with operation details
        """
        if not self.is_connected():
            return TradeResult(
                success=False,
                order_id=None,
                error_code=None,
                error_message="Not connected to MT5",
                price=None,
                volume=None
            )
        
        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return TradeResult(
                    success=False,
                    order_id=None,
                    error_code=None,
                    error_message=f"Symbol {symbol} not found",
                    price=None,
                    volume=None
                )
            
            # Prepare order request
            if order_type == OrderType.BUY:
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = symbol_info.ask if price is None else price
            elif order_type == OrderType.SELL:
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = symbol_info.bid if price is None else price
            elif order_type == OrderType.BUY_LIMIT:
                order_type_mt5 = mt5.ORDER_TYPE_BUY_LIMIT
            elif order_type == OrderType.SELL_LIMIT:
                order_type_mt5 = mt5.ORDER_TYPE_SELL_LIMIT
            elif order_type == OrderType.BUY_STOP:
                order_type_mt5 = mt5.ORDER_TYPE_BUY_STOP
            elif order_type == OrderType.SELL_STOP:
                order_type_mt5 = mt5.ORDER_TYPE_SELL_STOP
            else:
                return TradeResult(
                    success=False,
                    order_id=None,
                    error_code=None,
                    error_message=f"Unsupported order type: {order_type}",
                    price=None,
                    volume=None
                )
            
            # Validate volume
            volume = max(symbol_info.volume_min, 
                        min(symbol_info.volume_max, volume))
            
            # Round volume to step
            volume_step = symbol_info.volume_step
            volume = round(volume / volume_step) * volume_step
            
            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type_mt5,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add SL/TP if provided
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                return TradeResult(
                    success=False,
                    order_id=None,
                    error_code=error[0],
                    error_message=error[1],
                    price=None,
                    volume=None
                )
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResult(
                    success=False,
                    order_id=None,
                    error_code=result.retcode,
                    error_message=f"Order failed with retcode: {result.retcode}",
                    price=None,
                    volume=None
                )
            
            return TradeResult(
                success=True,
                order_id=result.order,
                error_code=None,
                error_message=None,
                price=result.price,
                volume=result.volume
            )
            
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            return TradeResult(
                success=False,
                order_id=None,
                error_code=None,
                error_message=str(e),
                price=None,
                volume=None
            )
    
    def close_position(self, ticket: int) -> TradeResult:
        """
        Close an open position.
        
        Args:
            ticket: Position ticket number
            
        Returns:
            TradeResult with operation details
        """
        if not self.is_connected():
            return TradeResult(
                success=False,
                order_id=None,
                error_code=None,
                error_message="Not connected to MT5",
                price=None,
                volume=None
            )
        
        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                return TradeResult(
                    success=False,
                    order_id=None,
                    error_code=None,
                    error_message=f"Position {ticket} not found",
                    price=None,
                    volume=None
                )
            
            pos = position[0]
            
            # Determine close order type
            if pos.type == 0:  # Buy position
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(pos.symbol).bid
            else:  # Sell position
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(pos.symbol).ask
            
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "AI Hedge Fund - Position Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                return TradeResult(
                    success=False,
                    order_id=None,
                    error_code=error[0],
                    error_message=error[1],
                    price=None,
                    volume=None
                )
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResult(
                    success=False,
                    order_id=None,
                    error_code=result.retcode,
                    error_message=f"Close failed with retcode: {result.retcode}",
                    price=None,
                    volume=None
                )
            
            return TradeResult(
                success=True,
                order_id=result.order,
                error_code=None,
                error_message=None,
                price=result.price,
                volume=result.volume
            )
            
        except Exception as e:
            logging.error(f"Error closing position {ticket}: {e}")
            return TradeResult(
                success=False,
                order_id=None,
                error_code=None,
                error_message=str(e),
                price=None,
                volume=None
            )
    
    def calculate_lot_size(self, symbol: str, risk_percent: float, 
                          stop_loss_pips: float) -> float:
        """
        Calculate optimal lot size based on risk management.
        
        Args:
            symbol: Trading symbol
            risk_percent: Risk percentage of account balance (e.g., 2.0 for 2%)
            stop_loss_pips: Stop loss distance in pips
            
        Returns:
            Calculated lot size
        """
        if not self.is_connected():
            return 0.0
        
        try:
            account_info = self.get_account_info()
            symbol_info = self.get_symbol_info(symbol)
            
            if not account_info or not symbol_info:
                return 0.0
            
            # Calculate risk amount
            risk_amount = account_info.balance * (risk_percent / 100)
            
            # Calculate pip value
            pip_value = symbol_info["point"] * symbol_info["contract_size"]
            
            # Calculate lot size
            lot_size = risk_amount / (stop_loss_pips * pip_value)
            
            # Round to symbol's lot step
            lot_step = symbol_info["lot_step"]
            lot_size = round(lot_size / lot_step) * lot_step
            
            # Ensure within limits
            lot_size = max(symbol_info["min_lot"], 
                          min(symbol_info["max_lot"], lot_size))
            
            return lot_size
            
        except Exception as e:
            logging.error(f"Error calculating lot size: {e}")
            return 0.0


# Global instance
mt5_integration = MetaTrader5Integration()


def get_mt5_integration() -> MetaTrader5Integration:
    """Get the global MT5 integration instance."""
    return mt5_integration


def is_mt5_available() -> bool:
    """Check if MetaTrader5 package is available."""
    return MT5_AVAILABLE
