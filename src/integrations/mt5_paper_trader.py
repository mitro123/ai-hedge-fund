"""
MT5 Paper Trading Simulator
Simulates MetaTrader 5 trading for demo/testing purposes.
Works on any platform (Linux, macOS, Windows) without MT5 installed.
"""

import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from src.integrations.metatrader5_integration import (
    AccountInfo,
    MT5Config,
    OrderType,
    Position,
    TradeResult,
)

logger = logging.getLogger(__name__)


class SimulatedTick:
    """Simulated price tick."""

    def __init__(self, bid: float, ask: float, spread: float):
        self.bid = bid
        self.ask = ask
        self.spread = spread


class PaperTradingAccount(BaseModel):
    """Paper trading account state."""

    login: int = 12345678
    balance: float = 10000.0
    equity: float = 10000.0
    margin: float = 0.0
    free_margin: float = 10000.0
    margin_level: float = 0.0
    currency: str = "USD"
    server: str = "PaperTrading-Demo"
    company: str = "AI Hedge Fund Simulator"


class PaperTrade(BaseModel):
    """Record of a paper trade."""

    ticket: int
    symbol: str
    order_type: str
    volume: float
    open_price: float
    open_time: str
    close_price: Optional[float] = None
    close_time: Optional[str] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    profit: float = 0.0
    swap: float = 0.0
    comment: str = ""
    status: str = "open"  # open, closed


class MT5PaperTrader:
    """
    Paper trading simulator that mimics MetaTrader 5 API.
    Generates realistic price data and simulates order execution.
    """

    # Predefined symbol configurations
    SYMBOL_CONFIG = {
        "EURUSD": {"digits": 5, "point": 0.00001, "spread": 12, "pip_value": 10.0, "base_price": 1.0850, "volatility": 0.0008},
        "GBPUSD": {"digits": 5, "point": 0.00001, "spread": 15, "pip_value": 10.0, "base_price": 1.2650, "volatility": 0.0010},
        "USDJPY": {"digits": 3, "point": 0.001, "spread": 10, "pip_value": 7.5, "base_price": 151.500, "volatility": 0.08},
        "USDCHF": {"digits": 5, "point": 0.00001, "spread": 14, "pip_value": 10.0, "base_price": 0.8850, "volatility": 0.0007},
        "AUDUSD": {"digits": 5, "point": 0.00001, "spread": 14, "pip_value": 10.0, "base_price": 0.6550, "volatility": 0.0009},
        "XAUUSD": {"digits": 2, "point": 0.01, "spread": 30, "pip_value": 1.0, "base_price": 2650.00, "volatility": 15.0},
        "US500":  {"digits": 2, "point": 0.01, "spread": 50, "pip_value": 1.0, "base_price": 5200.00, "volatility": 25.0},
        "BTCUSD": {"digits": 2, "point": 0.01, "spread": 500, "pip_value": 1.0, "base_price": 65000.00, "volatility": 800.0},
    }

    def __init__(
        self,
        initial_balance: float = 10000.0,
        leverage: int = 100,
        log_dir: Optional[str] = None,
    ):
        self.account = PaperTradingAccount(
            balance=initial_balance,
            equity=initial_balance,
            free_margin=initial_balance,
        )
        self.leverage = leverage
        self.positions: List[PaperTrade] = []
        self.trade_history: List[PaperTrade] = []
        self.next_ticket = 100001
        self.connected = False

        # Price simulation state
        self._current_prices: Dict[str, SimulatedTick] = {}
        self._initialize_prices()

        # Logging
        self.log_dir = Path(log_dir or "logs/paper_trading")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.trade_log_path = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        logger.info(f"Paper Trader initialized: balance=${initial_balance}, leverage=1:{leverage}")

    def _initialize_prices(self):
        """Initialize current prices for all symbols."""
        for symbol, config in self.SYMBOL_CONFIG.items():
            spread_in_price = config["spread"] * config["point"]
            base = config["base_price"]
            self._current_prices[symbol] = SimulatedTick(
                bid=base,
                ask=base + spread_in_price,
                spread=spread_in_price,
            )

    def _simulate_price_move(self, symbol: str) -> SimulatedTick:
        """Simulate a small price movement for a symbol."""
        if symbol not in self.SYMBOL_CONFIG:
            raise ValueError(f"Unknown symbol: {symbol}")

        config = self.SYMBOL_CONFIG[symbol]
        current = self._current_prices[symbol]

        # Random walk with mean reversion
        volatility = config["volatility"] * 0.1  # Scale down for per-tick movement
        drift = (config["base_price"] - current.bid) * 0.001  # Mean reversion
        change = drift + random.gauss(0, volatility)

        new_bid = current.bid + change
        spread = config["spread"] * config["point"]
        new_ask = new_bid + spread

        tick = SimulatedTick(bid=round(new_bid, config["digits"]), ask=round(new_ask, config["digits"]), spread=spread)
        self._current_prices[symbol] = tick
        return tick

    def connect(self, login: Optional[int] = None, password: Optional[str] = None, server: Optional[str] = None) -> bool:
        """Simulate connecting to MT5."""
        self.connected = True
        if login:
            self.account.login = login
        logger.info(f"[PAPER] Connected to paper trading account {self.account.login}")
        return True

    def disconnect(self):
        """Simulate disconnecting."""
        self._save_trade_log()
        self.connected = False
        logger.info("[PAPER] Disconnected from paper trading")

    def is_connected(self) -> bool:
        return self.connected

    def get_account_info(self) -> AccountInfo:
        """Get simulated account info."""
        self._update_equity()
        return AccountInfo(
            login=self.account.login,
            balance=round(self.account.balance, 2),
            equity=round(self.account.equity, 2),
            margin=round(self.account.margin, 2),
            free_margin=round(self.account.free_margin, 2),
            margin_level=round(self.account.margin_level, 2),
            currency=self.account.currency,
            server=self.account.server,
            company=self.account.company,
        )

    def get_positions(self) -> List[Position]:
        """Get all open positions."""
        self._update_positions()
        result = []
        for trade in self.positions:
            if trade.status == "open":
                result.append(
                    Position(
                        ticket=trade.ticket,
                        symbol=trade.symbol,
                        type=trade.order_type,
                        volume=trade.volume,
                        price_open=trade.open_price,
                        price_current=self._get_current_price(trade.symbol, trade.order_type),
                        profit=trade.profit,
                        swap=trade.swap,
                        comment=trade.comment,
                    )
                )
        return result

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information."""
        if symbol not in self.SYMBOL_CONFIG:
            return None

        config = self.SYMBOL_CONFIG[symbol]
        tick = self._simulate_price_move(symbol)

        return {
            "symbol": symbol,
            "bid": tick.bid,
            "ask": tick.ask,
            "spread": config["spread"],
            "digits": config["digits"],
            "point": config["point"],
            "min_lot": 0.01,
            "max_lot": 100.0,
            "lot_step": 0.01,
            "contract_size": 100000 if config["digits"] >= 3 else 100,
            "currency_base": symbol[:3] if len(symbol) >= 6 else "USD",
            "currency_profit": symbol[3:6] if len(symbol) >= 6 else "USD",
            "currency_margin": "USD",
        }

    def get_historical_data(self, symbol: str, timeframe: str = "H1", count: int = 100) -> Optional[pd.DataFrame]:
        """Generate simulated historical OHLCV data."""
        if symbol not in self.SYMBOL_CONFIG:
            return None

        config = self.SYMBOL_CONFIG[symbol]

        # Timeframe to minutes mapping
        tf_map = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
        minutes = tf_map.get(timeframe, 60)

        # Generate realistic OHLCV data using random walk
        np.random.seed(42)  # Reproducible for consistency
        base_price = config["base_price"]
        volatility = config["volatility"]

        dates = pd.date_range(end=datetime.now(), periods=count, freq=f"{minutes}min")
        returns = np.random.normal(0, volatility / np.sqrt(1440 / minutes), count)
        prices = base_price * np.exp(np.cumsum(returns))

        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            high_low_range = abs(np.random.normal(0, volatility * 0.5))
            open_price = close * (1 + np.random.normal(0, volatility * 0.1))
            high = max(open_price, close) + high_low_range
            low = min(open_price, close) - high_low_range
            volume = int(np.random.exponential(1000) + 100)

            data.append({
                "time": date,
                "Open": round(open_price, config["digits"]),
                "High": round(high, config["digits"]),
                "Low": round(low, config["digits"]),
                "Close": round(close, config["digits"]),
                "Volume": volume,
            })

        df = pd.DataFrame(data)
        df.set_index("time", inplace=True)
        return df

    def place_order(
        self,
        symbol: str,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = "AI Hedge Fund",
    ) -> TradeResult:
        """Execute a simulated trade."""
        if not self.connected:
            return TradeResult(success=False, order_id=None, error_code=None, error_message="Not connected", price=None, volume=None)

        if symbol not in self.SYMBOL_CONFIG:
            return TradeResult(success=False, order_id=None, error_code=None, error_message=f"Unknown symbol: {symbol}", price=None, volume=None)

        # Get current price
        tick = self._simulate_price_move(symbol)
        if order_type in (OrderType.BUY, OrderType.BUY_LIMIT, OrderType.BUY_STOP):
            exec_price = tick.ask if price is None else price
            trade_type = "BUY"
        else:
            exec_price = tick.bid if price is None else price
            trade_type = "SELL"

        # Validate volume
        volume = max(0.01, min(100.0, round(volume / 0.01) * 0.01))

        # Calculate margin required
        config = self.SYMBOL_CONFIG[symbol]
        contract_size = 100000 if config["digits"] >= 3 else 100
        margin_required = (volume * contract_size * exec_price) / self.leverage

        if margin_required > self.account.free_margin:
            return TradeResult(
                success=False, order_id=None, error_code=10019,
                error_message=f"Not enough free margin. Required: ${margin_required:.2f}, Available: ${self.account.free_margin:.2f}",
                price=None, volume=None,
            )

        # Create trade
        ticket = self.next_ticket
        self.next_ticket += 1

        trade = PaperTrade(
            ticket=ticket,
            symbol=symbol,
            order_type=trade_type,
            volume=volume,
            open_price=exec_price,
            open_time=datetime.now().isoformat(),
            stop_loss=sl,
            take_profit=tp,
            comment=comment,
        )

        self.positions.append(trade)
        self.account.margin += margin_required
        self.account.free_margin -= margin_required

        logger.info(f"[PAPER] Opened {trade_type} {volume} lots {symbol} @ {exec_price} (ticket: {ticket})")

        self._save_trade_log()

        return TradeResult(
            success=True,
            order_id=ticket,
            error_code=None,
            error_message=None,
            price=exec_price,
            volume=volume,
        )

    def close_position(self, ticket: int) -> TradeResult:
        """Close an open position."""
        if not self.connected:
            return TradeResult(success=False, order_id=None, error_code=None, error_message="Not connected", price=None, volume=None)

        trade = None
        for t in self.positions:
            if t.ticket == ticket and t.status == "open":
                trade = t
                break

        if not trade:
            return TradeResult(success=False, order_id=None, error_code=None, error_message=f"Position {ticket} not found", price=None, volume=None)

        # Get close price
        tick = self._simulate_price_move(trade.symbol)
        if trade.order_type == "BUY":
            close_price = tick.bid
        else:
            close_price = tick.ask

        # Calculate profit
        config = self.SYMBOL_CONFIG[trade.symbol]
        contract_size = 100000 if config["digits"] >= 3 else 100
        if trade.order_type == "BUY":
            profit = (close_price - trade.open_price) * trade.volume * contract_size
        else:
            profit = (trade.open_price - close_price) * trade.volume * contract_size

        # Update trade
        trade.close_price = close_price
        trade.close_time = datetime.now().isoformat()
        trade.profit = round(profit, 2)
        trade.status = "closed"

        # Update account
        margin_released = (trade.volume * contract_size * trade.open_price) / self.leverage
        self.account.balance += profit
        self.account.margin -= margin_released
        self.account.free_margin += margin_released + profit

        # Move to history
        self.trade_history.append(trade)
        self.positions = [t for t in self.positions if t.ticket != ticket]

        logger.info(f"[PAPER] Closed {trade.order_type} {trade.volume} lots {trade.symbol} @ {close_price} | P/L: ${profit:.2f}")

        self._save_trade_log()

        return TradeResult(
            success=True,
            order_id=ticket,
            error_code=None,
            error_message=None,
            price=close_price,
            volume=trade.volume,
        )

    def calculate_lot_size(self, symbol: str, risk_percent: float, stop_loss_pips: float) -> float:
        """Calculate position size based on risk."""
        if symbol not in self.SYMBOL_CONFIG:
            return 0.01

        config = self.SYMBOL_CONFIG[symbol]
        risk_amount = self.account.balance * (risk_percent / 100)
        pip_value = config["point"] * (100000 if config["digits"] >= 3 else 100)
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        lot_size = max(0.01, min(100.0, round(lot_size / 0.01) * 0.01))
        return lot_size

    def _get_current_price(self, symbol: str, trade_type: str) -> float:
        """Get current closing price for a position."""
        tick = self._current_prices.get(symbol)
        if not tick:
            return 0.0
        return tick.bid if trade_type == "BUY" else tick.ask

    def _update_positions(self):
        """Update P/L for all open positions."""
        for trade in self.positions:
            if trade.status == "open":
                current_price = self._get_current_price(trade.symbol, trade.order_type)
                config = self.SYMBOL_CONFIG.get(trade.symbol, {})
                contract_size = 100000 if config.get("digits", 5) >= 3 else 100

                if trade.order_type == "BUY":
                    trade.profit = round((current_price - trade.open_price) * trade.volume * contract_size, 2)
                else:
                    trade.profit = round((trade.open_price - current_price) * trade.volume * contract_size, 2)

                # Check SL/TP
                self._check_sl_tp(trade, current_price)

    def _check_sl_tp(self, trade: PaperTrade, current_price: float):
        """Check if stop loss or take profit has been hit."""
        if trade.stop_loss:
            if (trade.order_type == "BUY" and current_price <= trade.stop_loss) or \
               (trade.order_type == "SELL" and current_price >= trade.stop_loss):
                logger.info(f"[PAPER] Stop Loss hit for ticket {trade.ticket}")
                self.close_position(trade.ticket)
                return

        if trade.take_profit:
            if (trade.order_type == "BUY" and current_price >= trade.take_profit) or \
               (trade.order_type == "SELL" and current_price <= trade.take_profit):
                logger.info(f"[PAPER] Take Profit hit for ticket {trade.ticket}")
                self.close_position(trade.ticket)

    def _update_equity(self):
        """Update account equity based on open positions."""
        self._update_positions()
        unrealized_pl = sum(t.profit for t in self.positions if t.status == "open")
        self.account.equity = round(self.account.balance + unrealized_pl, 2)
        self.account.free_margin = round(self.account.equity - self.account.margin, 2)
        if self.account.margin > 0:
            self.account.margin_level = round((self.account.equity / self.account.margin) * 100, 2)
        else:
            self.account.margin_level = 0.0

    def _save_trade_log(self):
        """Save trade history to JSON file."""
        log_data = {
            "account": self.account.model_dump(),
            "open_positions": [t.model_dump() for t in self.positions],
            "trade_history": [t.model_dump() for t in self.trade_history],
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.trade_log_path, "w") as f:
            json.dump(log_data, f, indent=2, default=str)

    def get_trade_summary(self) -> Dict[str, Any]:
        """Get summary of all trading activity."""
        self._update_equity()

        closed_trades = [t for t in self.trade_history if t.status == "closed"]
        winning = [t for t in closed_trades if t.profit > 0]
        losing = [t for t in closed_trades if t.profit < 0]

        total_profit = sum(t.profit for t in closed_trades)
        total_winning = sum(t.profit for t in winning)
        total_losing = sum(t.profit for t in losing)

        return {
            "account": {
                "balance": self.account.balance,
                "equity": self.account.equity,
                "margin": self.account.margin,
                "free_margin": self.account.free_margin,
                "initial_balance": 10000.0,
                "total_return_pct": round(((self.account.balance - 10000.0) / 10000.0) * 100, 2),
            },
            "trades": {
                "total": len(closed_trades),
                "winning": len(winning),
                "losing": len(losing),
                "win_rate": round(len(winning) / max(len(closed_trades), 1) * 100, 1),
                "total_profit": round(total_profit, 2),
                "avg_win": round(total_winning / max(len(winning), 1), 2),
                "avg_loss": round(total_losing / max(len(losing), 1), 2),
                "profit_factor": round(abs(total_winning / min(total_losing, -0.01)), 2) if total_losing else float("inf"),
            },
            "open_positions": len(self.positions),
            "unrealized_pl": round(sum(t.profit for t in self.positions if t.status == "open"), 2),
            "trade_log": str(self.trade_log_path),
        }
