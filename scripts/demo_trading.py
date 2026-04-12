#!/usr/bin/env python3
"""
AI Hedge Fund - Demo Trading Script
Runs the AI trading pipeline in paper trading mode.

Usage:
    python scripts/demo_trading.py
    python scripts/demo_trading.py --symbols EURUSD XAUUSD --balance 50000
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging BEFORE any imports that might set up their own handlers
# Force reconfigure by removing existing handlers
root_logger = logging.getLogger()
root_logger.handlers.clear()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)

from src.integrations.mt5_paper_trader import MT5PaperTrader, OrderType


class DemoTradingSession:
    """
    Demo trading session that simulates AI-driven forex/commodity trading.
    Uses technical analysis to generate signals and executes paper trades.
    """

    def __init__(
        self,
        symbols: List[str],
        initial_balance: float = 10000.0,
        risk_per_trade: float = 2.0,
        max_positions: int = 5,
    ):
        self.symbols = symbols
        self.risk_per_trade = risk_per_trade
        self.max_positions = max_positions

        # Initialize paper trader
        self.trader = MT5PaperTrader(initial_balance=initial_balance)
        self.trader.connect()

        logger.info("=" * 60)
        logger.info("AI HEDGE FUND - DEMO TRADING SESSION")
        logger.info("=" * 60)
        logger.info(f"Balance: ${initial_balance:,.2f}")
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Risk per trade: {risk_per_trade}%")
        logger.info(f"Max positions: {max_positions}")
        logger.info("=" * 60)

    def analyze_symbol(self, symbol: str) -> Dict:
        """
        Perform technical analysis on a symbol using simulated data.
        Returns trading signal based on SMA crossover and momentum.
        """
        data = self.trader.get_historical_data(symbol, "H1", 200)
        if data is None or len(data) < 50:
            return {"symbol": symbol, "signal": "HOLD", "confidence": 0}

        # Calculate indicators
        close = data["Close"]

        # Simple Moving Averages
        sma_20 = close.rolling(20).mean()
        sma_50 = close.rolling(50).mean()

        # RSI (14-period)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))

        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal_line = macd.ewm(span=9).mean()

        # Bollinger Bands
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std

        # Current values
        current_price = close.iloc[-1]
        current_sma20 = sma_20.iloc[-1]
        current_sma50 = sma_50.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_macd = macd.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_bb_upper = bb_upper.iloc[-1]
        current_bb_lower = bb_lower.iloc[-1]

        # Generate trading signal
        score = 0
        reasons = []

        # SMA crossover
        if current_sma20 > current_sma50:
            score += 1
            reasons.append("SMA20 > SMA50 (bullish trend)")
        else:
            score -= 1
            reasons.append("SMA20 < SMA50 (bearish trend)")

        # RSI
        if current_rsi < 30:
            score += 2
            reasons.append(f"RSI={current_rsi:.1f} (oversold)")
        elif current_rsi > 70:
            score -= 2
            reasons.append(f"RSI={current_rsi:.1f} (overbought)")
        elif current_rsi < 45:
            score += 0.5
            reasons.append(f"RSI={current_rsi:.1f} (leaning bearish)")
        elif current_rsi > 55:
            score -= 0.5
            reasons.append(f"RSI={current_rsi:.1f} (leaning bullish)")

        # MACD
        if current_macd > current_signal:
            score += 1
            reasons.append("MACD above signal (bullish)")
        else:
            score -= 1
            reasons.append("MACD below signal (bearish)")

        # Bollinger Bands
        if current_price < current_bb_lower:
            score += 1.5
            reasons.append("Price below lower BB (potential bounce)")
        elif current_price > current_bb_upper:
            score -= 1.5
            reasons.append("Price above upper BB (potential reversal)")

        # Determine signal
        confidence = min(abs(score) / 5.0 * 100, 95)

        if score >= 2:
            signal = "BUY"
        elif score <= -2:
            signal = "SELL"
        else:
            signal = "HOLD"

        # Calculate SL/TP levels
        atr = (data["High"] - data["Low"]).rolling(14).mean().iloc[-1]

        if signal == "BUY":
            stop_loss = current_price - 2 * atr
            take_profit = current_price + 3 * atr
        elif signal == "SELL":
            stop_loss = current_price + 2 * atr
            take_profit = current_price - 3 * atr
        else:
            stop_loss = None
            take_profit = None

        return {
            "symbol": symbol,
            "signal": signal,
            "confidence": round(confidence, 1),
            "score": round(score, 2),
            "current_price": current_price,
            "sma_20": round(current_sma20, 5),
            "sma_50": round(current_sma50, 5),
            "rsi": round(current_rsi, 1),
            "macd": round(current_macd, 6),
            "stop_loss": round(stop_loss, 5) if stop_loss else None,
            "take_profit": round(take_profit, 5) if take_profit else None,
            "atr": round(atr, 5),
            "reasons": reasons,
        }

    def execute_signals(self, analyses: List[Dict]):
        """Execute trades based on analysis signals."""
        open_positions = self.trader.get_positions()
        open_symbols = {p.symbol for p in open_positions}

        for analysis in analyses:
            symbol = analysis["symbol"]
            signal = analysis["signal"]
            confidence = analysis["confidence"]

            # Skip if already have position in this symbol
            if symbol in open_symbols:
                logger.info(f"  {symbol}: Skip - already have open position")
                continue

            # Skip if at max positions
            if len(open_positions) >= self.max_positions and signal != "HOLD":
                logger.info(f"  {symbol}: Skip - max positions ({self.max_positions}) reached")
                continue

            # Only trade with sufficient confidence
            if confidence < 40:
                logger.info(f"  {symbol}: Skip - low confidence ({confidence}%)")
                continue

            if signal in ("BUY", "SELL"):
                # Calculate position size
                stop_loss_pips = abs(analysis["current_price"] - analysis["stop_loss"]) / self.trader.SYMBOL_CONFIG[symbol]["point"]
                volume = self.trader.calculate_lot_size(symbol, self.risk_per_trade, stop_loss_pips)

                order_type = OrderType.BUY if signal == "BUY" else OrderType.SELL

                result = self.trader.place_order(
                    symbol=symbol,
                    order_type=order_type,
                    volume=volume,
                    sl=analysis["stop_loss"],
                    tp=analysis["take_profit"],
                    comment=f"AI Signal: {signal} conf={confidence}%",
                )

                if result.success:
                    logger.info(f"  {symbol}: {signal} {volume} lots @ {result.price} | SL={analysis['stop_loss']} TP={analysis['take_profit']}")
                else:
                    logger.warning(f"  {symbol}: Failed - {result.error_message}")

    def manage_positions(self):
        """Manage existing positions (check for exit signals)."""
        positions = self.trader.get_positions()

        for pos in positions:
            analysis = self.analyze_symbol(pos.symbol)

            # Close if signal reversed
            if pos.type == "BUY" and analysis["signal"] == "SELL" and analysis["confidence"] > 50:
                logger.info(f"  Closing BUY {pos.symbol} (signal reversed to SELL)")
                self.trader.close_position(pos.ticket)
            elif pos.type == "SELL" and analysis["signal"] == "BUY" and analysis["confidence"] > 50:
                logger.info(f"  Closing SELL {pos.symbol} (signal reversed to BUY)")
                self.trader.close_position(pos.ticket)

    def run_cycle(self, cycle_num: int):
        """Run one trading cycle."""
        logger.info(f"\n{'='*60}")
        logger.info(f"CYCLE {cycle_num} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*60}")

        # 1. Analyze all symbols
        logger.info("\n[ANALYSIS]")
        analyses = []
        for symbol in self.symbols:
            analysis = self.analyze_symbol(symbol)
            analyses.append(analysis)

            signal_emoji = {"BUY": ">>", "SELL": "<<", "HOLD": "--"}[analysis["signal"]]
            logger.info(
                f"  {symbol}: {signal_emoji} {analysis['signal']} "
                f"(conf={analysis['confidence']}%, score={analysis['score']}) "
                f"RSI={analysis['rsi']}"
            )
            for reason in analysis["reasons"]:
                logger.info(f"    - {reason}")

        # 2. Manage existing positions
        logger.info("\n[POSITION MANAGEMENT]")
        self.manage_positions()

        # 3. Execute new signals
        logger.info("\n[EXECUTION]")
        self.execute_signals(analyses)

        # 4. Account summary
        account = self.trader.get_account_info()
        positions = self.trader.get_positions()
        logger.info(f"\n[ACCOUNT]")
        logger.info(f"  Balance: ${account.balance:,.2f} | Equity: ${account.equity:,.2f}")
        logger.info(f"  Margin: ${account.margin:,.2f} | Free: ${account.free_margin:,.2f}")
        logger.info(f"  Open positions: {len(positions)}")
        for pos in positions:
            pl_sign = "+" if pos.profit >= 0 else ""
            logger.info(f"    {pos.type} {pos.volume} {pos.symbol} @ {pos.price_open} | P/L: {pl_sign}${pos.profit:.2f}")

    def run(self, cycles: int = 10, delay_seconds: float = 2.0):
        """Run the demo trading session."""
        try:
            for i in range(1, cycles + 1):
                self.run_cycle(i)

                # Simulate price movement between cycles
                for symbol in self.symbols:
                    for _ in range(10):  # 10 price ticks between cycles
                        self.trader._simulate_price_move(symbol)

                if i < cycles:
                    time.sleep(delay_seconds)

        except KeyboardInterrupt:
            logger.info("\n\nSession interrupted by user.")

        # Final summary
        self.print_summary()

    def print_summary(self):
        """Print final trading summary."""
        summary = self.trader.get_trade_summary()

        logger.info(f"\n{'='*60}")
        logger.info("TRADING SESSION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"\n[ACCOUNT]")
        logger.info(f"  Final Balance:  ${summary['account']['balance']:,.2f}")
        logger.info(f"  Final Equity:   ${summary['account']['equity']:,.2f}")
        logger.info(f"  Total Return:   {summary['account']['total_return_pct']:+.2f}%")

        logger.info(f"\n[TRADES]")
        logger.info(f"  Total trades:    {summary['trades']['total']}")
        logger.info(f"  Winning trades:  {summary['trades']['winning']}")
        logger.info(f"  Losing trades:   {summary['trades']['losing']}")
        logger.info(f"  Win rate:        {summary['trades']['win_rate']}%")
        logger.info(f"  Total P/L:       ${summary['trades']['total_profit']:,.2f}")
        logger.info(f"  Avg win:         ${summary['trades']['avg_win']:,.2f}")
        logger.info(f"  Avg loss:        ${summary['trades']['avg_loss']:,.2f}")
        logger.info(f"  Profit factor:   {summary['trades']['profit_factor']}")

        logger.info(f"\n[OPEN POSITIONS]")
        logger.info(f"  Count:           {summary['open_positions']}")
        logger.info(f"  Unrealized P/L:  ${summary['unrealized_pl']:,.2f}")

        logger.info(f"\n  Trade log saved: {summary['trade_log']}")
        logger.info(f"{'='*60}")

        # Close remaining positions
        positions = self.trader.get_positions()
        if positions:
            logger.info(f"\nClosing {len(positions)} remaining positions...")
            for pos in positions:
                self.trader.close_position(pos.ticket)

            # Final summary after closing all
            final = self.trader.get_trade_summary()
            logger.info(f"\n[FINAL RESULT after closing all positions]")
            logger.info(f"  Balance: ${final['account']['balance']:,.2f}")
            logger.info(f"  Return:  {final['account']['total_return_pct']:+.2f}%")
            logger.info(f"  Win rate: {final['trades']['win_rate']}%")

        self.trader.disconnect()


def main():
    parser = argparse.ArgumentParser(description="AI Hedge Fund - Demo Trading")
    parser.add_argument("--symbols", nargs="+", default=["EURUSD", "GBPUSD", "XAUUSD", "USDJPY"], help="Symbols to trade")
    parser.add_argument("--balance", type=float, default=10000.0, help="Initial balance (default: $10,000)")
    parser.add_argument("--cycles", type=int, default=10, help="Number of trading cycles (default: 10)")
    parser.add_argument("--risk", type=float, default=2.0, help="Risk per trade in %% (default: 2%%)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between cycles in seconds (default: 1)")
    parser.add_argument("--max-positions", type=int, default=5, help="Max open positions (default: 5)")

    args = parser.parse_args()

    session = DemoTradingSession(
        symbols=args.symbols,
        initial_balance=args.balance,
        risk_per_trade=args.risk,
        max_positions=args.max_positions,
    )

    session.run(cycles=args.cycles, delay_seconds=args.delay)


if __name__ == "__main__":
    main()
