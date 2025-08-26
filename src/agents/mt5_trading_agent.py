"""
MetaTrader 5 Trading Agent for AI Hedge Fund
Provides live trading capabilities using MT5 integration.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

from ..integrations.metatrader5_integration import (
    get_mt5_integration, 
    OrderType, 
    TradeResult, 
    AccountInfo, 
    Position,
    MT5Config,
    is_mt5_available
)
from ..utils.llm import call_llm
from pydantic import BaseModel, Field


class MarketAnalysis(BaseModel):
    """Pydantic model for AI market analysis response."""
    analysis: str = Field(description="Detailed market analysis")


class MT5TradingAgent:
    """
    AI Trading Agent that executes trades through MetaTrader 5.
    Combines AI analysis with live trading execution.
    """
    
    def __init__(self, config: Optional[MT5Config] = None):
        """
        Initialize MT5 Trading Agent.
        
        Args:
            config: MT5 connection configuration
        """
        self.mt5 = get_mt5_integration()
        self.config = config
        self.connected = False
        
        if not is_mt5_available():
            logging.error("MetaTrader5 not available. Please install MetaTrader5 package.")
            return
        
        logging.info("MT5 Trading Agent initialized")
    
    def connect(self, login: Optional[int] = None, password: Optional[str] = None, 
                server: Optional[str] = None) -> bool:
        """
        Connect to MetaTrader 5 terminal.
        
        Args:
            login: Trading account login
            password: Trading account password
            server: Trading server name
            
        Returns:
            True if connection successful
        """
        try:
            self.connected = self.mt5.connect(login, password, server)
            if self.connected:
                logging.info("MT5 Trading Agent connected successfully")
            else:
                logging.error("Failed to connect MT5 Trading Agent")
            return self.connected
        except Exception as e:
            logging.error(f"Error connecting MT5 Trading Agent: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MetaTrader 5."""
        self.mt5.disconnect()
        self.connected = False
        logging.info("MT5 Trading Agent disconnected")
    
    def is_connected(self) -> bool:
        """Check if connected to MT5."""
        return self.connected and self.mt5.is_connected()
    
    def get_account_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current account status and information.
        
        Returns:
            Dictionary with account information
        """
        if not self.is_connected():
            return None
        
        try:
            account_info = self.mt5.get_account_info()
            positions = self.mt5.get_positions()
            
            if not account_info:
                return None
            
            return {
                "account_info": account_info.dict(),
                "positions_count": len(positions),
                "positions": [pos.dict() for pos in positions],
                "connected": True,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error getting account status: {e}")
            return None
    
    def analyze_market(self, symbol: str, timeframe: str = "H1", 
                      count: int = 100) -> Optional[Dict[str, Any]]:
        """
        Analyze market data for a symbol using AI.
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            timeframe: Timeframe for analysis
            count: Number of bars to analyze
            
        Returns:
            AI analysis results
        """
        if not self.is_connected():
            return None
        
        try:
            # Get historical data
            data = self.mt5.get_historical_data(symbol, timeframe, count)
            if data is None or data.empty:
                logging.error(f"No data available for {symbol}")
                return None
            
            # Get symbol info
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                logging.error(f"Symbol info not available for {symbol}")
                return None
            
            # Prepare data for AI analysis
            latest_price = data['Close'].iloc[-1]
            price_change = ((latest_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
            
            # Calculate technical indicators
            sma_20 = data['Close'].rolling(20).mean().iloc[-1]
            sma_50 = data['Close'].rolling(50).mean().iloc[-1] if len(data) >= 50 else None
            
            volatility = data['Close'].pct_change().std() * 100
            
            # Create analysis prompt
            prompt = f"""
            Analyze the following market data for {symbol}:
            
            Current Price: {latest_price:.5f}
            Price Change: {price_change:.2f}%
            20-period SMA: {sma_20:.5f}
            50-period SMA: {sma_50:.5f if sma_50 else 'N/A'}
            Volatility: {volatility:.2f}%
            Bid: {symbol_info['bid']:.5f}
            Ask: {symbol_info['ask']:.5f}
            Spread: {symbol_info['spread']} points
            
            Recent price data (last 10 bars):
            {data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10).to_string()}
            
            Provide a trading analysis including:
            1. Market trend direction
            2. Support and resistance levels
            3. Trading recommendation (BUY/SELL/HOLD)
            4. Risk assessment
            5. Suggested entry and exit points
            
            Format your response as a structured analysis.
            """
            
            # Get AI analysis
            try:
                analysis_result = call_llm(prompt, MarketAnalysis, agent_name="MT5TradingAgent")
                analysis = getattr(analysis_result, 'analysis', 'AI analysis unavailable')
            except Exception as e:
                logging.error(f"Error getting AI analysis: {e}")
                analysis = "AI analysis unavailable due to error"
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": latest_price,
                "price_change_percent": price_change,
                "technical_indicators": {
                    "sma_20": sma_20,
                    "sma_50": sma_50,
                    "volatility": volatility
                },
                "symbol_info": symbol_info,
                "ai_analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error analyzing market for {symbol}: {e}")
            return None
    
    def execute_trade(self, symbol: str, action: str, volume: float,
                     stop_loss: Optional[float] = None, 
                     take_profit: Optional[float] = None,
                     comment: str = "AI Hedge Fund - MT5 Agent") -> TradeResult:
        """
        Execute a trade based on AI analysis.
        
        Args:
            symbol: Trading symbol
            action: Trade action ("BUY" or "SELL")
            volume: Trade volume in lots
            stop_loss: Stop loss price
            take_profit: Take profit price
            comment: Trade comment
            
        Returns:
            TradeResult with execution details
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
            # Validate action
            if action.upper() not in ["BUY", "SELL"]:
                return TradeResult(
                    success=False,
                    order_id=None,
                    error_code=None,
                    error_message=f"Invalid action: {action}. Use BUY or SELL",
                    price=None,
                    volume=None
                )
            
            # Convert action to OrderType
            order_type = OrderType.BUY if action.upper() == "BUY" else OrderType.SELL
            
            # Execute the trade
            result = self.mt5.place_order(
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                sl=stop_loss,
                tp=take_profit,
                comment=comment
            )
            
            if result.success:
                logging.info(f"Trade executed successfully: {action} {volume} lots of {symbol}")
            else:
                logging.error(f"Trade execution failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            logging.error(f"Error executing trade: {e}")
            return TradeResult(
                success=False,
                order_id=None,
                error_code=None,
                error_message=str(e),
                price=None,
                volume=None
            )
    
    def calculate_position_size(self, symbol: str, risk_percent: float = 2.0,
                              stop_loss_pips: float = 50.0) -> float:
        """
        Calculate optimal position size based on risk management.
        
        Args:
            symbol: Trading symbol
            risk_percent: Risk percentage of account balance
            stop_loss_pips: Stop loss distance in pips
            
        Returns:
            Calculated lot size
        """
        if not self.is_connected():
            return 0.0
        
        try:
            return self.mt5.calculate_lot_size(symbol, risk_percent, stop_loss_pips)
        except Exception as e:
            logging.error(f"Error calculating position size: {e}")
            return 0.0
    
    def close_position(self, ticket: int) -> TradeResult:
        """
        Close an open position.
        
        Args:
            ticket: Position ticket number
            
        Returns:
            TradeResult with close operation details
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
            result = self.mt5.close_position(ticket)
            
            if result.success:
                logging.info(f"Position {ticket} closed successfully")
            else:
                logging.error(f"Failed to close position {ticket}: {result.error_message}")
            
            return result
            
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
    
    def get_trading_opportunities(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple symbols and identify trading opportunities.
        
        Args:
            symbols: List of symbols to analyze
            
        Returns:
            List of trading opportunities
        """
        if not self.is_connected():
            return []
        
        opportunities = []
        
        for symbol in symbols:
            try:
                analysis = self.analyze_market(symbol)
                if analysis and analysis.get('ai_analysis'):
                    # Extract trading recommendation from AI analysis
                    ai_text = analysis['ai_analysis'].lower()
                    
                    recommendation = "HOLD"
                    if "buy" in ai_text and "recommend" in ai_text:
                        recommendation = "BUY"
                    elif "sell" in ai_text and "recommend" in ai_text:
                        recommendation = "SELL"
                    
                    # Calculate suggested position size
                    position_size = self.calculate_position_size(symbol)
                    
                    opportunity = {
                        "symbol": symbol,
                        "recommendation": recommendation,
                        "current_price": analysis['current_price'],
                        "price_change": analysis['price_change_percent'],
                        "suggested_volume": position_size,
                        "analysis": analysis['ai_analysis'],
                        "timestamp": analysis['timestamp']
                    }
                    
                    opportunities.append(opportunity)
                    
            except Exception as e:
                logging.error(f"Error analyzing {symbol}: {e}")
                continue
        
        return opportunities
    
    def get_portfolio_summary(self) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive portfolio summary.
        
        Returns:
            Portfolio summary with positions and performance
        """
        if not self.is_connected():
            return None
        
        try:
            account_info = self.mt5.get_account_info()
            positions = self.mt5.get_positions()
            
            if not account_info:
                return None
            
            # Calculate portfolio metrics
            total_profit = sum(pos.profit for pos in positions)
            total_volume = sum(pos.volume for pos in positions)
            
            # Group positions by symbol
            positions_by_symbol = {}
            for pos in positions:
                if pos.symbol not in positions_by_symbol:
                    positions_by_symbol[pos.symbol] = []
                positions_by_symbol[pos.symbol].append(pos)
            
            return {
                "account": {
                    "balance": account_info.balance,
                    "equity": account_info.equity,
                    "margin": account_info.margin,
                    "free_margin": account_info.free_margin,
                    "margin_level": account_info.margin_level,
                    "currency": account_info.currency
                },
                "positions": {
                    "total_count": len(positions),
                    "total_volume": total_volume,
                    "total_profit": total_profit,
                    "by_symbol": positions_by_symbol
                },
                "performance": {
                    "profit_loss": total_profit,
                    "profit_loss_percent": (total_profit / account_info.balance) * 100 if account_info.balance > 0 else 0,
                    "equity_ratio": (account_info.equity / account_info.balance) * 100 if account_info.balance > 0 else 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting portfolio summary: {e}")
            return None


# Global instance
mt5_trading_agent = MT5TradingAgent()


def get_mt5_trading_agent() -> MT5TradingAgent:
    """Get the global MT5 trading agent instance."""
    return mt5_trading_agent
