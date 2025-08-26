import itertools
import sys
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import questionary
import seaborn as sns
from colorama import Fore, init, Style
from dateutil.relativedelta import relativedelta
from typing_extensions import Callable
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.llm.models import get_model_info, LLM_ORDER, ModelProvider, OLLAMA_LLM_ORDER
from src.main import run_hedge_fund
from src.tools.api import get_company_news, get_financial_metrics, get_insider_trades, get_price_data, get_prices
from src.utils.analysts import ANALYST_ORDER
from src.utils.display import format_backtest_row, print_backtest_results
from src.utils.ollama import ensure_ollama_and_model

init(autoreset=True)


class Backtester:
    def __init__(
        self,
        agent: Callable,
        tickers: list[str],
        start_date: str,
        end_date: str,
        initial_capital: float,
        model_name: str = "gpt-4.1",
        model_provider: str = "OpenAI",
        selected_analysts: list[str] = [],
        initial_margin_requirement: float = 0.0,
    ):
        """
        :param agent: The trading agent (Callable).
        :param tickers: List of tickers to backtest.
        :param start_date: Start date string (YYYY-MM-DD).
        :param end_date: End date string (YYYY-MM-DD).
        :param initial_capital: Starting portfolio cash.
        :param model_name: Which LLM model name to use (gpt-4, etc).
        :param model_provider: Which LLM provider (OpenAI, etc).
        :param selected_analysts: List of analyst names or IDs to incorporate.
        :param initial_margin_requirement: The margin ratio (e.g. 0.5 = 50%).
        """
        self.agent = agent
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.model_name = model_name
        self.model_provider = model_provider
        self.selected_analysts = selected_analysts

        # Initialize portfolio with support for long/short positions
        self.portfolio_values = []
        self.trades_history = []  # Track all trades for visualization
        self.price_history = {}  # Track price history for each ticker
        self.portfolio = {
            "cash": initial_capital,
            "margin_used": 0.0,  # total margin usage across all short positions
            "margin_requirement": initial_margin_requirement,  # The margin ratio required for shorts
            "positions": {
                ticker: {
                    "long": 0,
                    "short": 0,
                    "long_cost_basis": 0.0,
                    "short_cost_basis": 0.0,
                    "short_margin_used": 0.0,
                }
                for ticker in tickers
            },  # Number of shares held long  # Number of shares held short  # Average cost basis per share (long)  # Average cost basis per share (short)  # Dollars of margin used for this ticker's short
            "realized_gains": {
                ticker: {
                    "long": 0.0,  # Realized gains from long positions
                    "short": 0.0,  # Realized gains from short positions
                }
                for ticker in tickers
            },
        }

    def execute_trade(self, ticker: str, action: str, quantity: float, current_price: float):
        """
        Execute trades with support for both long and short positions.
        `quantity` is the number of shares the agent wants to buy/sell/short/cover.
        We will only trade integer shares to keep it simple.
        """
        if quantity <= 0:
            return 0

        quantity = int(quantity)  # force integer shares
        position = self.portfolio["positions"][ticker]

        if action == "buy":
            cost = quantity * current_price
            if cost <= self.portfolio["cash"]:
                # Weighted average cost basis for the new total
                old_shares = position["long"]
                old_cost_basis = position["long_cost_basis"]
                new_shares = quantity
                total_shares = old_shares + new_shares

                if total_shares > 0:
                    total_old_cost = old_cost_basis * old_shares
                    total_new_cost = cost
                    position["long_cost_basis"] = (total_old_cost + total_new_cost) / total_shares

                position["long"] += quantity
                self.portfolio["cash"] -= cost
                return quantity
            else:
                # Calculate maximum affordable quantity
                max_quantity = int(self.portfolio["cash"] / current_price)
                if max_quantity > 0:
                    cost = max_quantity * current_price
                    old_shares = position["long"]
                    old_cost_basis = position["long_cost_basis"]
                    total_shares = old_shares + max_quantity

                    if total_shares > 0:
                        total_old_cost = old_cost_basis * old_shares
                        total_new_cost = cost
                        position["long_cost_basis"] = (total_old_cost + total_new_cost) / total_shares

                    position["long"] += max_quantity
                    self.portfolio["cash"] -= cost
                    return max_quantity
                return 0

        elif action == "sell":
            # You can only sell as many as you own
            quantity = min(quantity, position["long"])
            if quantity > 0:
                # Realized gain/loss using average cost basis
                avg_cost_per_share = position["long_cost_basis"] if position["long"] > 0 else 0
                realized_gain = (current_price - avg_cost_per_share) * quantity
                self.portfolio["realized_gains"][ticker]["long"] += realized_gain

                position["long"] -= quantity
                self.portfolio["cash"] += quantity * current_price

                if position["long"] == 0:
                    position["long_cost_basis"] = 0.0

                return quantity

        elif action == "short":
            """
            Typical short sale flow:
              1) Receive proceeds = current_price * quantity
              2) Post margin_required = proceeds * margin_ratio
              3) Net effect on cash = +proceeds - margin_required
            """
            proceeds = current_price * quantity
            margin_required = proceeds * self.portfolio["margin_requirement"]
            if margin_required <= self.portfolio["cash"]:
                # Weighted average short cost basis
                old_short_shares = position["short"]
                old_cost_basis = position["short_cost_basis"]
                new_shares = quantity
                total_shares = old_short_shares + new_shares

                if total_shares > 0:
                    total_old_cost = old_cost_basis * old_short_shares
                    total_new_cost = current_price * new_shares
                    position["short_cost_basis"] = (total_old_cost + total_new_cost) / total_shares

                position["short"] += quantity

                # Update margin usage
                position["short_margin_used"] += margin_required
                self.portfolio["margin_used"] += margin_required

                # Increase cash by proceeds, then subtract the required margin
                self.portfolio["cash"] += proceeds
                self.portfolio["cash"] -= margin_required
                return quantity
            else:
                # Calculate maximum shortable quantity
                margin_ratio = self.portfolio["margin_requirement"]
                if margin_ratio > 0:
                    max_quantity = int(self.portfolio["cash"] / (current_price * margin_ratio))
                else:
                    max_quantity = 0

                if max_quantity > 0:
                    proceeds = current_price * max_quantity
                    margin_required = proceeds * margin_ratio

                    old_short_shares = position["short"]
                    old_cost_basis = position["short_cost_basis"]
                    total_shares = old_short_shares + max_quantity

                    if total_shares > 0:
                        total_old_cost = old_cost_basis * old_short_shares
                        total_new_cost = current_price * max_quantity
                        position["short_cost_basis"] = (total_old_cost + total_new_cost) / total_shares

                    position["short"] += max_quantity
                    position["short_margin_used"] += margin_required
                    self.portfolio["margin_used"] += margin_required

                    self.portfolio["cash"] += proceeds
                    self.portfolio["cash"] -= margin_required
                    return max_quantity
                return 0

        elif action == "cover":
            """
            When covering shares:
              1) Pay cover cost = current_price * quantity
              2) Release a proportional share of the margin
              3) Net effect on cash = -cover_cost + released_margin
            """
            quantity = min(quantity, position["short"])
            if quantity > 0:
                cover_cost = quantity * current_price
                avg_short_price = position["short_cost_basis"] if position["short"] > 0 else 0
                realized_gain = (avg_short_price - current_price) * quantity

                if position["short"] > 0:
                    portion = quantity / position["short"]
                else:
                    portion = 1.0

                margin_to_release = portion * position["short_margin_used"]

                position["short"] -= quantity
                position["short_margin_used"] -= margin_to_release
                self.portfolio["margin_used"] -= margin_to_release

                # Pay the cost to cover, but get back the released margin
                self.portfolio["cash"] += margin_to_release
                self.portfolio["cash"] -= cover_cost

                self.portfolio["realized_gains"][ticker]["short"] += realized_gain

                if position["short"] == 0:
                    position["short_cost_basis"] = 0.0
                    position["short_margin_used"] = 0.0

                return quantity

        return 0

    def calculate_portfolio_value(self, current_prices):
        """
        Calculate total portfolio value, including:
          - cash
          - market value of long positions
          - unrealized gains/losses for short positions
        """
        total_value = self.portfolio["cash"]

        for ticker in self.tickers:
            position = self.portfolio["positions"][ticker]
            price = current_prices[ticker]

            # Long position value
            long_value = position["long"] * price
            total_value += long_value

            # Short position unrealized PnL = short_shares * (short_cost_basis - current_price)
            if position["short"] > 0:
                total_value -= position["short"] * price

        return total_value

    def _debug_agent_output(self, output, current_date):
        """Debug helper to print agent output."""
        print(f"\n=== DEBUG {current_date} ===")
        print(f"Raw output type: {type(output)}")
        print(f"Raw output keys: {output.keys() if isinstance(output, dict) else 'Not a dict'}")
        if isinstance(output, dict):
            decisions = output.get("decisions")
            print(f"Decisions type: {type(decisions)}")
            print(f"Decisions: {decisions}")
            print(f"Analyst signals: {output.get('analyst_signals', {})}")
        print("========================\n")

    def _safe_parse_decisions(self, output):
        """Safely parse decisions from agent output."""
        if not isinstance(output, dict):
            print(f"Warning: Agent output is not a dict: {type(output)}")
            return {ticker: {"action": "hold", "quantity": 0} for ticker in self.tickers}
        
        decisions = output.get("decisions")
        if decisions is None:
            print("Warning: No decisions found in agent output")
            return {ticker: {"action": "hold", "quantity": 0} for ticker in self.tickers}
        
        if not isinstance(decisions, dict):
            print(f"Warning: Decisions is not a dict: {type(decisions)}")
            return {ticker: {"action": "hold", "quantity": 0} for ticker in self.tickers}
        
        # Validate each decision
        validated_decisions = {}
        for ticker in self.tickers:
            decision = decisions.get(ticker, {"action": "hold", "quantity": 0})
            validated_decisions[ticker] = self._validate_decision(decision)
        
        return validated_decisions

    def _validate_decision(self, decision):
        """Validate a single trading decision."""
        if not isinstance(decision, dict):
            return {"action": "hold", "quantity": 0}
        
        action = decision.get("action", "hold")
        if isinstance(action, str):
            action = action.lower()
        else:
            action = "hold"
        
        if action not in ["buy", "sell", "hold", "short", "cover"]:
            action = "hold"
        
        quantity = decision.get("quantity", 0)
        if not isinstance(quantity, (int, float)) or quantity < 0:
            quantity = 0
        
        return {"action": action, "quantity": quantity}

    def _fallback_strategy(self, current_prices):
        """Simple fallback strategy when agent fails."""
        print("Using fallback strategy (simple moving average)")
        decisions = {}
        
        for ticker in self.tickers:
            try:
                # Get recent price data for simple moving average
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                
                price_data = get_price_data(ticker, start_date, end_date)
                if price_data.empty or len(price_data) < 5:
                    decisions[ticker] = {"action": "hold", "quantity": 0}
                    continue
                
                # Simple moving average strategy
                sma_short = price_data['close'].rolling(5).mean().iloc[-1]
                sma_long = price_data['close'].rolling(20).mean().iloc[-1] if len(price_data) >= 20 else sma_short
                current_price = current_prices[ticker]
                
                if sma_short > sma_long and current_price > sma_short:
                    # Buy signal
                    quantity = max(1, int(1000 / current_price))  # $1000 worth, minimum 1 share
                    decisions[ticker] = {"action": "buy", "quantity": quantity}
                elif sma_short < sma_long and current_price < sma_short:
                    # Sell signal (if we have positions)
                    position = self.portfolio["positions"][ticker]
                    if position["long"] > 0:
                        decisions[ticker] = {"action": "sell", "quantity": min(100, position["long"])}
                    else:
                        decisions[ticker] = {"action": "hold", "quantity": 0}
                else:
                    decisions[ticker] = {"action": "hold", "quantity": 0}
                    
            except Exception as e:
                print(f"Error in fallback strategy for {ticker}: {e}")
                decisions[ticker] = {"action": "hold", "quantity": 0}
        
        return decisions

    def prefetch_data(self):
        """Pre-fetch all data needed for the backtest period."""
        print("\nPre-fetching data for the entire backtest period...")

        # Convert end_date string to datetime, fetch up to 1 year before
        end_date_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
        start_date_dt = end_date_dt - relativedelta(years=1)
        start_date_str = start_date_dt.strftime("%Y-%m-%d")

        for ticker in self.tickers:
            # Fetch price data for the entire period, plus 1 year
            get_prices(ticker, start_date_str, self.end_date)

            # Fetch financial metrics
            get_financial_metrics(ticker, self.end_date, limit=10)

            # Fetch insider trades
            get_insider_trades(ticker, self.end_date, start_date=self.start_date, limit=1000)

            # Fetch company news
            get_company_news(ticker, self.end_date, start_date=self.start_date, limit=1000)

        print("Data pre-fetch complete.")

    def run_backtest(self):
        # Pre-fetch all data at the start
        self.prefetch_data()

        dates = pd.date_range(self.start_date, self.end_date, freq="B")
        table_rows = []
        performance_metrics = {
            "sharpe_ratio": None,
            "sortino_ratio": None,
            "max_drawdown": None,
            "long_short_ratio": None,
            "gross_exposure": None,
            "net_exposure": None,
        }

        print("\nStarting backtest...")

        # Initialize portfolio values list with initial capital
        if len(dates) > 0:
            self.portfolio_values = [{"Date": dates[0], "Portfolio Value": self.initial_capital}]
        else:
            self.portfolio_values = []

        for current_date in dates:
            lookback_start = (current_date - timedelta(days=30)).strftime("%Y-%m-%d")
            current_date_str = current_date.strftime("%Y-%m-%d")
            previous_date_str = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")

            # Skip if there's no prior day to look back (i.e., first date in the range)
            if lookback_start == current_date_str:
                continue

            # Get current prices for all tickers
            try:
                current_prices = {}
                missing_data = False

                for ticker in self.tickers:
                    try:
                        price_data = get_price_data(ticker, previous_date_str, current_date_str)
                        if price_data.empty:
                            print(f"Warning: No price data for {ticker} on {current_date_str}")
                            missing_data = True
                            break
                        current_prices[ticker] = price_data.iloc[-1]["close"]
                    except Exception as e:
                        print(
                            f"Error fetching price for {ticker} between {previous_date_str} and {current_date_str}: {e}"
                        )
                        missing_data = True
                        break

                if missing_data:
                    print(f"Skipping trading day {current_date_str} due to missing price data")
                    continue

            except Exception as e:
                # If there's a general API error, log it and skip this day
                print(f"Error fetching prices for {current_date_str}: {e}")
                continue

            # ---------------------------------------------------------------
            # 1) Execute the agent's trades
            # ---------------------------------------------------------------
            try:
                output = self.agent(
                    tickers=self.tickers,
                    start_date=lookback_start,
                    end_date=current_date_str,
                    portfolio=self.portfolio,
                    model_name=self.model_name,
                    model_provider=self.model_provider,
                    selected_analysts=self.selected_analysts,
                )
                
                # Debug output
                self._debug_agent_output(output, current_date_str)
                
                # Safe parsing of decisions
                decisions = self._safe_parse_decisions(output)
                analyst_signals = output.get("analyst_signals", {})
                
            except Exception as e:
                print(f"Error running agent for {current_date_str}: {e}")
                # Use fallback strategy
                decisions = self._fallback_strategy(current_prices)
                analyst_signals = {}

            # Execute trades for each ticker
            executed_trades = {}
            for ticker in self.tickers:
                decision = decisions.get(ticker, {"action": "hold", "quantity": 0})
                action, quantity = decision.get("action", "hold"), decision.get("quantity", 0)

                executed_quantity = self.execute_trade(ticker, action, quantity, current_prices[ticker])
                executed_trades[ticker] = executed_quantity
                
                # Track trades and prices for visualization
                if executed_quantity > 0:
                    self.track_trade(current_date_str, ticker, action, executed_quantity, current_prices[ticker])
                
                self.track_price(current_date_str, ticker, current_prices[ticker])

            # ---------------------------------------------------------------
            # 2) Now that trades have executed trades, recalculate the final
            #    portfolio value for this day.
            # ---------------------------------------------------------------
            total_value = self.calculate_portfolio_value(current_prices)

            # Also compute long/short exposures for final post‐trade state
            long_exposure = sum(self.portfolio["positions"][t]["long"] * current_prices[t] for t in self.tickers)
            short_exposure = sum(self.portfolio["positions"][t]["short"] * current_prices[t] for t in self.tickers)

            # Calculate gross and net exposures
            gross_exposure = long_exposure + short_exposure
            net_exposure = long_exposure - short_exposure
            long_short_ratio = long_exposure / short_exposure if short_exposure > 1e-9 else float("inf")

            # Track each day's portfolio value in self.portfolio_values
            self.portfolio_values.append(
                {
                    "Date": current_date,
                    "Portfolio Value": total_value,
                    "Long Exposure": long_exposure,
                    "Short Exposure": short_exposure,
                    "Gross Exposure": gross_exposure,
                    "Net Exposure": net_exposure,
                    "Long/Short Ratio": long_short_ratio,
                }
            )

            # ---------------------------------------------------------------
            # 3) Build the table rows to display
            # ---------------------------------------------------------------
            date_rows = []

            # For each ticker, record signals/trades
            for ticker in self.tickers:
                ticker_signals = {}
                for agent_name, signals in analyst_signals.items():
                    if ticker in signals:
                        ticker_signals[agent_name] = signals[ticker]

                bullish_count = len([s for s in ticker_signals.values() if s.get("signal", "").lower() == "bullish"])
                bearish_count = len([s for s in ticker_signals.values() if s.get("signal", "").lower() == "bearish"])
                neutral_count = len([s for s in ticker_signals.values() if s.get("signal", "").lower() == "neutral"])

                # Calculate net position value
                pos = self.portfolio["positions"][ticker]
                long_val = pos["long"] * current_prices[ticker]
                short_val = pos["short"] * current_prices[ticker]
                net_position_value = long_val - short_val

                # Get the action and quantity from the decisions
                action = decisions.get(ticker, {}).get("action", "hold")
                quantity = executed_trades.get(ticker, 0)

                # Append the agent action to the table rows
                date_rows.append(
                    format_backtest_row(
                        date=current_date_str,
                        ticker=ticker,
                        action=action,
                        quantity=quantity,
                        price=current_prices[ticker],
                        shares_owned=pos["long"] - pos["short"],  # net shares
                        position_value=net_position_value,
                        bullish_count=bullish_count,
                        bearish_count=bearish_count,
                        neutral_count=neutral_count,
                    )
                )
            # ---------------------------------------------------------------
            # 4) Calculate performance summary metrics
            # ---------------------------------------------------------------
            # Calculate portfolio return vs. initial capital
            # The realized gains are already reflected in cash balance, so we don't add them separately
            portfolio_return = (total_value / self.initial_capital - 1) * 100

            # Add summary row for this day
            date_rows.append(
                format_backtest_row(
                    date=current_date_str,
                    ticker="",
                    action="",
                    quantity=0,
                    price=0,
                    shares_owned=0,
                    position_value=0,
                    bullish_count=0,
                    bearish_count=0,
                    neutral_count=0,
                    is_summary=True,
                    total_value=total_value,
                    return_pct=portfolio_return,
                    cash_balance=self.portfolio["cash"],
                    total_position_value=total_value - self.portfolio["cash"],
                    sharpe_ratio=performance_metrics["sharpe_ratio"],
                    sortino_ratio=performance_metrics["sortino_ratio"],
                    max_drawdown=performance_metrics["max_drawdown"],
                ),
            )

            table_rows.extend(date_rows)
            print_backtest_results(table_rows)

            # Update performance metrics if we have enough data
            if len(self.portfolio_values) > 3:
                self._update_performance_metrics(performance_metrics)

        # Store the final performance metrics for reference in analyze_performance
        self.performance_metrics = performance_metrics
        return performance_metrics

    def _update_performance_metrics(self, performance_metrics):
        """Helper method to update performance metrics using daily returns."""
        values_df = pd.DataFrame(self.portfolio_values).set_index("Date")
        values_df["Daily Return"] = values_df["Portfolio Value"].pct_change()
        clean_returns = values_df["Daily Return"].dropna()

        if len(clean_returns) < 2:
            return  # not enough data points

        # Assumes 252 trading days/year
        daily_risk_free_rate = 0.0434 / 252
        excess_returns = clean_returns - daily_risk_free_rate
        mean_excess_return = excess_returns.mean()
        std_excess_return = excess_returns.std()

        # Sharpe ratio
        if std_excess_return > 1e-12:
            performance_metrics["sharpe_ratio"] = np.sqrt(252) * (mean_excess_return / std_excess_return)
        else:
            performance_metrics["sharpe_ratio"] = 0.0

        # Sortino ratio
        negative_returns = excess_returns[excess_returns < 0]
        if len(negative_returns) > 0:
            downside_std = negative_returns.std()
            if downside_std > 1e-12:
                performance_metrics["sortino_ratio"] = np.sqrt(252) * (mean_excess_return / downside_std)
            else:
                performance_metrics["sortino_ratio"] = float("inf") if mean_excess_return > 0 else 0
        else:
            performance_metrics["sortino_ratio"] = float("inf") if mean_excess_return > 0 else 0

        # Maximum drawdown (ensure it's stored as a negative percentage)
        rolling_max = values_df["Portfolio Value"].cummax()
        drawdown = (values_df["Portfolio Value"] - rolling_max) / rolling_max

        if len(drawdown) > 0:
            min_drawdown = drawdown.min()
            # Store as a negative percentage
            performance_metrics["max_drawdown"] = min_drawdown * 100

            # Store the date of max drawdown for reference
            if min_drawdown < 0:
                min_date = drawdown.idxmin()
                if hasattr(min_date, 'strftime'):
                    performance_metrics["max_drawdown_date"] = min_date.strftime("%Y-%m-%d")
                else:
                    performance_metrics["max_drawdown_date"] = str(min_date)
            else:
                performance_metrics["max_drawdown_date"] = None
        else:
            performance_metrics["max_drawdown"] = 0.0
            performance_metrics["max_drawdown_date"] = None

    def analyze_performance(self):
        """Creates a performance DataFrame, prints summary stats, and plots equity curve."""
        if not self.portfolio_values:
            print("No portfolio data found. Please run the backtest first.")
            return pd.DataFrame()

        performance_df = pd.DataFrame(self.portfolio_values).set_index("Date")
        if performance_df.empty:
            print("No valid performance data to analyze.")
            return performance_df

        final_portfolio_value = performance_df["Portfolio Value"].iloc[-1]
        total_return = ((final_portfolio_value - self.initial_capital) / self.initial_capital) * 100

        print(f"\n{Fore.WHITE}{Style.BRIGHT}PORTFOLIO PERFORMANCE SUMMARY:{Style.RESET_ALL}")
        print(f"Total Return: {Fore.GREEN if total_return >= 0 else Fore.RED}{total_return:.2f}%{Style.RESET_ALL}")

        # Print realized P&L for informational purposes only
        total_realized_gains = sum(
            self.portfolio["realized_gains"][ticker]["long"] + self.portfolio["realized_gains"][ticker]["short"]
            for ticker in self.tickers
        )
        print(
            f"Total Realized Gains/Losses: {Fore.GREEN if total_realized_gains >= 0 else Fore.RED}${total_realized_gains:,.2f}{Style.RESET_ALL}"
        )

        # Plot the portfolio value over time
        plt.figure(figsize=(12, 6))
        plt.plot(performance_df.index, performance_df["Portfolio Value"], color="blue")
        plt.title("Portfolio Value Over Time")
        plt.ylabel("Portfolio Value ($)")
        plt.xlabel("Date")
        plt.grid(True)
        plt.show()

        # Compute daily returns
        performance_df["Daily Return"] = performance_df["Portfolio Value"].pct_change().fillna(0)
        daily_rf = 0.0434 / 252  # daily risk-free rate
        mean_daily_return = performance_df["Daily Return"].mean()
        std_daily_return = performance_df["Daily Return"].std()

        # Annualized Sharpe Ratio
        if std_daily_return != 0:
            annualized_sharpe = np.sqrt(252) * ((mean_daily_return - daily_rf) / std_daily_return)
        else:
            annualized_sharpe = 0
        print(f"\nSharpe Ratio: {Fore.YELLOW}{annualized_sharpe:.2f}{Style.RESET_ALL}")

        # Use the max drawdown value calculated during the backtest if available
        max_drawdown = getattr(self, "performance_metrics", {}).get("max_drawdown")
        max_drawdown_date = getattr(self, "performance_metrics", {}).get("max_drawdown_date")

        # If no value exists yet, calculate it
        if max_drawdown is None:
            rolling_max = performance_df["Portfolio Value"].cummax()
            drawdown = (performance_df["Portfolio Value"] - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100
            min_date = drawdown.idxmin()
            if pd.notnull(min_date) and hasattr(min_date, 'strftime'):
                max_drawdown_date = min_date.strftime("%Y-%m-%d")
            else:
                max_drawdown_date = str(min_date) if pd.notnull(min_date) else None

        if max_drawdown_date:
            print(f"Maximum Drawdown: {Fore.RED}{abs(max_drawdown):.2f}%{Style.RESET_ALL} (on {max_drawdown_date})")
        else:
            print(f"Maximum Drawdown: {Fore.RED}{abs(max_drawdown):.2f}%{Style.RESET_ALL}")

        # Win Rate
        winning_days = len(performance_df[performance_df["Daily Return"] > 0])
        total_days = max(len(performance_df) - 1, 1)
        win_rate = (winning_days / total_days) * 100
        print(f"Win Rate: {Fore.GREEN}{win_rate:.2f}%{Style.RESET_ALL}")

        # Average Win/Loss Ratio
        positive_returns = performance_df[performance_df["Daily Return"] > 0]["Daily Return"]
        negative_returns = performance_df[performance_df["Daily Return"] < 0]["Daily Return"]
        avg_win = positive_returns.mean() if not positive_returns.empty else 0
        avg_loss = abs(negative_returns.mean()) if not negative_returns.empty else 0
        if avg_loss != 0:
            win_loss_ratio = avg_win / avg_loss
        else:
            win_loss_ratio = float("inf") if avg_win > 0 else 0
        print(f"Win/Loss Ratio: {Fore.GREEN}{win_loss_ratio:.2f}{Style.RESET_ALL}")

        # Maximum Consecutive Wins / Losses
        returns_binary = (performance_df["Daily Return"] > 0).astype(int)
        if len(returns_binary) > 0:
            max_consecutive_wins = max(
                (len(list(g)) for k, g in itertools.groupby(returns_binary) if k == 1), default=0
            )
            max_consecutive_losses = max(
                (len(list(g)) for k, g in itertools.groupby(returns_binary) if k == 0), default=0
            )
        else:
            max_consecutive_wins = 0
            max_consecutive_losses = 0

        print(f"Max Consecutive Wins: {Fore.GREEN}{max_consecutive_wins}{Style.RESET_ALL}")
        print(f"Max Consecutive Losses: {Fore.RED}{max_consecutive_losses}{Style.RESET_ALL}")

        return performance_df

    def create_interactive_charts(self):
        """Create interactive charts showing trades, price movements, and performance."""
        if not self.portfolio_values or not self.trades_history:
            print("No data available for visualization. Run backtest first.")
            return

        # Create subplots
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=('Price Chart with Trades', 'Portfolio Value', 'Daily Returns', 'Drawdown'),
            vertical_spacing=0.08,
            specs=[[{"secondary_y": True}],
                   [{"secondary_y": False}],
                   [{"secondary_y": False}],
                   [{"secondary_y": False}]]
        )

        # Color scheme
        colors = px.colors.qualitative.Set1

        # 1. Price chart with trade markers
        for i, ticker in enumerate(self.tickers):
            if ticker in self.price_history:
                price_data = pd.DataFrame(self.price_history[ticker])
                
                # Add price line
                fig.add_trace(
                    go.Scatter(
                        x=price_data['date'],
                        y=price_data['price'],
                        mode='lines',
                        name=f'{ticker} Price',
                        line=dict(color=colors[i % len(colors)]),
                        yaxis='y'
                    ),
                    row=1, col=1
                )

                # Add buy/sell markers
                buy_trades = [t for t in self.trades_history if t['ticker'] == ticker and t['action'] == 'buy']
                sell_trades = [t for t in self.trades_history if t['ticker'] == ticker and t['action'] == 'sell']
                
                if buy_trades:
                    fig.add_trace(
                        go.Scatter(
                            x=[t['date'] for t in buy_trades],
                            y=[t['price'] for t in buy_trades],
                            mode='markers',
                            name=f'{ticker} BUY',
                            marker=dict(
                                symbol='triangle-up',
                                size=12,
                                color='green',
                                line=dict(width=2, color='darkgreen')
                            ),
                            text=[f"BUY {t['quantity']} @ ${t['price']:.2f}" for t in buy_trades],
                            hovertemplate='<b>%{text}</b><br>Date: %{x}<extra></extra>',
                            yaxis='y'
                        ),
                        row=1, col=1
                    )

                if sell_trades:
                    fig.add_trace(
                        go.Scatter(
                            x=[t['date'] for t in sell_trades],
                            y=[t['price'] for t in sell_trades],
                            mode='markers',
                            name=f'{ticker} SELL',
                            marker=dict(
                                symbol='triangle-down',
                                size=12,
                                color='red',
                                line=dict(width=2, color='darkred')
                            ),
                            text=[f"SELL {t['quantity']} @ ${t['price']:.2f}" for t in sell_trades],
                            hovertemplate='<b>%{text}</b><br>Date: %{x}<extra></extra>',
                            yaxis='y'
                        ),
                        row=1, col=1
                    )

        # 2. Portfolio value over time
        portfolio_df = pd.DataFrame(self.portfolio_values)
        fig.add_trace(
            go.Scatter(
                x=portfolio_df['Date'],
                y=portfolio_df['Portfolio Value'],
                mode='lines',
                name='Portfolio Value',
                line=dict(color='blue', width=3),
                fill='tonexty'
            ),
            row=2, col=1
        )

        # Add benchmark line (initial capital)
        fig.add_hline(
            y=self.initial_capital,
            line_dash="dash",
            line_color="gray",
            annotation_text="Initial Capital",
            row=2, col=1
        )

        # 3. Daily returns
        portfolio_df['Daily Return'] = portfolio_df['Portfolio Value'].pct_change() * 100
        fig.add_trace(
            go.Scatter(
                x=portfolio_df['Date'],
                y=portfolio_df['Daily Return'],
                mode='lines',
                name='Daily Returns (%)',
                line=dict(color='orange')
            ),
            row=3, col=1
        )

        # Add zero line for returns
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=3, col=1)

        # 4. Drawdown
        rolling_max = portfolio_df['Portfolio Value'].cummax()
        drawdown = (portfolio_df['Portfolio Value'] - rolling_max) / rolling_max * 100
        
        fig.add_trace(
            go.Scatter(
                x=portfolio_df['Date'],
                y=drawdown,
                mode='lines',
                name='Drawdown (%)',
                line=dict(color='red'),
                fill='tonexty'
            ),
            row=4, col=1
        )

        # Update layout
        fig.update_layout(
            title='Backtest Analysis Dashboard',
            height=1200,
            showlegend=True,
            hovermode='x unified'
        )

        # Update y-axes labels
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Portfolio Value ($)", row=2, col=1)
        fig.update_yaxes(title_text="Daily Return (%)", row=3, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=4, col=1)

        # Update x-axes labels
        fig.update_xaxes(title_text="Date", row=4, col=1)

        # Show the plot
        fig.show()

    def create_performance_metrics_dashboard(self):
        """Create a comprehensive performance metrics dashboard."""
        if not self.portfolio_values:
            print("No portfolio data available. Run backtest first.")
            return

        portfolio_df = pd.DataFrame(self.portfolio_values)
        portfolio_df['Daily Return'] = portfolio_df['Portfolio Value'].pct_change()

        # Calculate comprehensive metrics
        metrics = self._calculate_comprehensive_metrics(portfolio_df)

        # Create metrics visualization
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                'Return Distribution', 'Rolling Sharpe Ratio', 'Monthly Returns Heatmap',
                'Risk-Return Scatter', 'Underwater Plot', 'Trade Analysis'
            ),
            specs=[[{"type": "histogram"}, {"type": "scatter"}, {"type": "heatmap"}],
                   [{"type": "scatter"}, {"type": "scatter"}, {"type": "bar"}]]
        )

        # 1. Return Distribution
        returns = portfolio_df['Daily Return'].dropna() * 100
        fig.add_trace(
            go.Histogram(
                x=returns,
                nbinsx=50,
                name='Daily Returns',
                marker_color='lightblue',
                opacity=0.7
            ),
            row=1, col=1
        )

        # 2. Rolling Sharpe Ratio (30-day window)
        rolling_sharpe = self._calculate_rolling_sharpe(portfolio_df, window=30)
        fig.add_trace(
            go.Scatter(
                x=portfolio_df['Date'][30:],
                y=rolling_sharpe,
                mode='lines',
                name='30-Day Rolling Sharpe',
                line=dict(color='green')
            ),
            row=1, col=2
        )

        # 3. Monthly Returns Heatmap
        monthly_returns = self._calculate_monthly_returns(portfolio_df)
        if not monthly_returns.empty:
            fig.add_trace(
                go.Heatmap(
                    z=monthly_returns.values,
                    x=monthly_returns.columns,
                    y=monthly_returns.index,
                    colorscale='RdYlGn',
                    name='Monthly Returns'
                ),
                row=1, col=3
            )

        # 4. Risk-Return Scatter (if multiple periods)
        if len(portfolio_df) > 252:  # More than a year of data
            periods = self._get_period_risk_return(portfolio_df)
            fig.add_trace(
                go.Scatter(
                    x=periods['Risk'],
                    y=periods['Return'],
                    mode='markers',
                    name='Risk-Return',
                    marker=dict(size=10, color='blue')
                ),
                row=2, col=1
            )

        # 5. Underwater Plot (Drawdown)
        rolling_max = portfolio_df['Portfolio Value'].cummax()
        drawdown = (portfolio_df['Portfolio Value'] - rolling_max) / rolling_max * 100
        
        fig.add_trace(
            go.Scatter(
                x=portfolio_df['Date'],
                y=drawdown,
                mode='lines',
                name='Drawdown',
                line=dict(color='red'),
                fill='tonexty'
            ),
            row=2, col=2
        )

        # 6. Trade Analysis
        if self.trades_history:
            trade_analysis = self._analyze_trades()
            fig.add_trace(
                go.Bar(
                    x=list(trade_analysis.keys()),
                    y=list(trade_analysis.values()),
                    name='Trade Stats',
                    marker_color='lightgreen'
                ),
                row=2, col=3
            )

        # Update layout
        fig.update_layout(
            title='Performance Metrics Dashboard',
            height=800,
            showlegend=False
        )

        fig.show()

        # Print comprehensive metrics
        self._print_comprehensive_metrics(metrics)

    def _calculate_comprehensive_metrics(self, portfolio_df):
        """Calculate comprehensive performance metrics."""
        returns = portfolio_df['Daily Return'].dropna()
        
        metrics = {}
        
        # Basic metrics
        total_return = (portfolio_df['Portfolio Value'].iloc[-1] / self.initial_capital - 1) * 100
        metrics['Total Return (%)'] = total_return
        
        # Risk metrics
        volatility = returns.std() * np.sqrt(252) * 100
        metrics['Annualized Volatility (%)'] = volatility
        
        # Sharpe ratio
        risk_free_rate = 0.0434  # 4.34% annual
        excess_returns = returns - risk_free_rate/252
        sharpe = np.sqrt(252) * excess_returns.mean() / returns.std() if returns.std() > 0 else 0
        metrics['Sharpe Ratio'] = sharpe
        
        # Sortino ratio
        negative_returns = returns[returns < 0]
        downside_std = negative_returns.std() if len(negative_returns) > 0 else 0
        sortino = np.sqrt(252) * excess_returns.mean() / downside_std if downside_std > 0 else 0
        metrics['Sortino Ratio'] = sortino
        
        # Maximum drawdown
        rolling_max = portfolio_df['Portfolio Value'].cummax()
        drawdown = (portfolio_df['Portfolio Value'] - rolling_max) / rolling_max
        max_dd = drawdown.min() * 100
        metrics['Maximum Drawdown (%)'] = max_dd
        
        # Calmar ratio
        calmar = total_return / abs(max_dd) if max_dd != 0 else 0
        metrics['Calmar Ratio'] = calmar
        
        # Win rate
        winning_days = len(returns[returns > 0])
        total_days = len(returns)
        win_rate = (winning_days / total_days) * 100 if total_days > 0 else 0
        metrics['Win Rate (%)'] = win_rate
        
        # Best/Worst day
        metrics['Best Day (%)'] = returns.max() * 100
        metrics['Worst Day (%)'] = returns.min() * 100
        
        # Value at Risk (95%)
        var_95 = np.percentile(returns, 5) * 100
        metrics['VaR 95% (%)'] = var_95
        
        # Expected Shortfall (95%)
        es_95 = returns[returns <= np.percentile(returns, 5)].mean() * 100
        metrics['Expected Shortfall 95% (%)'] = es_95
        
        return metrics

    def _calculate_rolling_sharpe(self, portfolio_df, window=30):
        """Calculate rolling Sharpe ratio."""
        returns = portfolio_df['Portfolio Value'].pct_change().dropna()
        risk_free_rate = 0.0434 / 252
        
        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()
        
        rolling_sharpe = np.sqrt(252) * (rolling_mean - risk_free_rate) / rolling_std
        return rolling_sharpe.dropna()

    def _calculate_monthly_returns(self, portfolio_df):
        """Calculate monthly returns for heatmap."""
        portfolio_df = portfolio_df.copy()
        portfolio_df['Date'] = pd.to_datetime(portfolio_df['Date'])
        portfolio_df.set_index('Date', inplace=True)
        
        monthly_returns = portfolio_df['Portfolio Value'].resample('M').last().pct_change() * 100
        monthly_returns.index = monthly_returns.index.strftime('%Y-%m')
        
        # Reshape for heatmap (years vs months)
        monthly_df = monthly_returns.to_frame('Return')
        monthly_df['Year'] = pd.to_datetime(monthly_returns.index).year
        monthly_df['Month'] = pd.to_datetime(monthly_returns.index).month
        
        heatmap_data = monthly_df.pivot(index='Year', columns='Month', values='Return')
        return heatmap_data.fillna(0)

    def _get_period_risk_return(self, portfolio_df):
        """Get risk-return data for different periods."""
        # Split data into quarters
        periods = []
        quarter_size = len(portfolio_df) // 4
        
        for i in range(4):
            start_idx = i * quarter_size
            end_idx = (i + 1) * quarter_size if i < 3 else len(portfolio_df)
            
            period_data = portfolio_df.iloc[start_idx:end_idx]
            returns = period_data['Portfolio Value'].pct_change().dropna()
            
            period_return = (period_data['Portfolio Value'].iloc[-1] / period_data['Portfolio Value'].iloc[0] - 1) * 100
            period_risk = returns.std() * np.sqrt(252) * 100
            
            periods.append({'Return': period_return, 'Risk': period_risk})
        
        return pd.DataFrame(periods)

    def _analyze_trades(self):
        """Analyze trading patterns."""
        if not self.trades_history:
            return {}
        
        trades_df = pd.DataFrame(self.trades_history)
        
        analysis = {}
        analysis['Total Trades'] = len(trades_df)
        analysis['Buy Trades'] = len(trades_df[trades_df['action'] == 'buy'])
        analysis['Sell Trades'] = len(trades_df[trades_df['action'] == 'sell'])
        
        # Average trade size
        analysis['Avg Trade Size'] = trades_df['quantity'].mean()
        
        return analysis

    def _print_comprehensive_metrics(self, metrics):
        """Print comprehensive metrics in a formatted way."""
        print(f"\n{Fore.WHITE}{Style.BRIGHT}COMPREHENSIVE PERFORMANCE METRICS:{Style.RESET_ALL}")
        print("=" * 60)
        
        # Group metrics by category
        return_metrics = ['Total Return (%)', 'Best Day (%)', 'Worst Day (%)']
        risk_metrics = ['Annualized Volatility (%)', 'Maximum Drawdown (%)', 'VaR 95% (%)', 'Expected Shortfall 95% (%)']
        ratio_metrics = ['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio']
        other_metrics = ['Win Rate (%)']
        
        categories = [
            ("RETURN METRICS", return_metrics),
            ("RISK METRICS", risk_metrics),
            ("RISK-ADJUSTED RATIOS", ratio_metrics),
            ("OTHER METRICS", other_metrics)
        ]
        
        for category_name, metric_list in categories:
            print(f"\n{Fore.CYAN}{category_name}:{Style.RESET_ALL}")
            for metric in metric_list:
                if metric in metrics:
                    value = metrics[metric]
                    if 'Return' in metric or 'Day' in metric:
                        color = Fore.GREEN if value >= 0 else Fore.RED
                    elif 'Drawdown' in metric or 'VaR' in metric or 'Shortfall' in metric:
                        color = Fore.RED if value < 0 else Fore.GREEN
                    elif 'Ratio' in metric:
                        color = Fore.GREEN if value > 1 else Fore.YELLOW if value > 0 else Fore.RED
                    else:
                        color = Fore.WHITE
                    
                    print(f"  {metric}: {color}{value:.2f}{Style.RESET_ALL}")

    def track_trade(self, date, ticker, action, quantity, price):
        """Track individual trades for visualization."""
        if quantity > 0:  # Only track actual trades
            self.trades_history.append({
                'date': date,
                'ticker': ticker,
                'action': action,
                'quantity': quantity,
                'price': price
            })

    def track_price(self, date, ticker, price):
        """Track price history for visualization."""
        if ticker not in self.price_history:
            self.price_history[ticker] = []
        
        self.price_history[ticker].append({
            'date': date,
            'price': price
        })


### 4. Run the Backtest #####
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run backtesting simulation")
    parser.add_argument(
        "--tickers",
        type=str,
        required=False,
        help="Comma-separated list of stock ticker symbols (e.g., AAPL,MSFT,GOOGL)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=(datetime.now() - relativedelta(months=1)).strftime("%Y-%m-%d"),
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=100000,
        help="Initial capital amount (default: 100000)",
    )
    parser.add_argument(
        "--margin-requirement",
        type=float,
        default=0.0,
        help="Margin ratio for short positions, e.g. 0.5 for 50% (default: 0.0)",
    )
    parser.add_argument(
        "--analysts",
        type=str,
        required=False,
        help="Comma-separated list of analysts to use (e.g., michael_burry,other_analyst)",
    )
    parser.add_argument(
        "--analysts-all",
        action="store_true",
        help="Use all available analysts (overrides --analysts)",
    )
    parser.add_argument("--ollama", action="store_true", help="Use Ollama for local LLM inference")

    args = parser.parse_args()

    # Parse tickers from comma-separated string
    tickers = [ticker.strip() for ticker in args.tickers.split(",")] if args.tickers else []

    # Parse analysts from command-line flags
    selected_analysts = None
    if args.analysts_all:
        selected_analysts = [a[1] for a in ANALYST_ORDER]
    elif args.analysts:
        selected_analysts = [a.strip() for a in args.analysts.split(",") if a.strip()]
    else:
        # Choose analysts interactively
        choices = questionary.checkbox(
            "Use the Space bar to select/unselect analysts.",
            choices=[questionary.Choice(display, value=value) for display, value in ANALYST_ORDER],
            instruction="\n\nPress 'a' to toggle all.\n\nPress Enter when done to run the hedge fund.",
            validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
            style=questionary.Style(
                [
                    ("checkbox-selected", "fg:green"),
                    ("selected", "fg:green noinherit"),
                    ("highlighted", "noinherit"),
                    ("pointer", "noinherit"),
                ]
            ),
        ).ask()
        if not choices:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)
        else:
            selected_analysts = choices
            print(
                f"\nSelected analysts: "
                f"{', '.join(Fore.GREEN + choice.title().replace('_', ' ') + Style.RESET_ALL for choice in choices)}"
            )

    # Select LLM model based on whether Ollama is being used
    model_name = ""
    model_provider = None

    if args.ollama:
        print(f"{Fore.CYAN}Using Ollama for local LLM inference.{Style.RESET_ALL}")

        # Select from Ollama-specific models
        model_name = questionary.select(
            "Select your Ollama model:",
            choices=[questionary.Choice(display, value=value) for display, value, _ in OLLAMA_LLM_ORDER],
            style=questionary.Style(
                [
                    ("selected", "fg:green bold"),
                    ("pointer", "fg:green bold"),
                    ("highlighted", "fg:green"),
                    ("answer", "fg:green bold"),
                ]
            ),
        ).ask()

        if not model_name:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)

        if model_name == "-":
            model_name = questionary.text("Enter the custom model name:").ask()
            if not model_name:
                print("\n\nInterrupt received. Exiting...")
                sys.exit(0)

        # Ensure Ollama is installed, running, and the model is available
        if not ensure_ollama_and_model(model_name):
            print(f"{Fore.RED}Cannot proceed without Ollama and the selected model.{Style.RESET_ALL}")
            sys.exit(1)

        model_provider = ModelProvider.OLLAMA.value
        print(
            f"\nSelected {Fore.CYAN}Ollama{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}{model_name}{Style.RESET_ALL}\n"
        )
    else:
        # Use the standard cloud-based LLM selection
        model_choice = questionary.select(
            "Select your LLM model:",
            choices=[questionary.Choice(display, value=(name, provider)) for display, name, provider in LLM_ORDER],
            style=questionary.Style(
                [
                    ("selected", "fg:green bold"),
                    ("pointer", "fg:green bold"),
                    ("highlighted", "fg:green"),
                    ("answer", "fg:green bold"),
                ]
            ),
        ).ask()

        if not model_choice:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)

        model_name, model_provider = model_choice

        model_info = get_model_info(model_name, model_provider)
        if model_info:
            if model_info.is_custom():
                model_name = questionary.text("Enter the custom model name:").ask()
                if not model_name:
                    print("\n\nInterrupt received. Exiting...")
                    sys.exit(0)

            print(
                f"\nSelected {Fore.CYAN}{model_provider}{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}{model_name}{Style.RESET_ALL}\n"
            )
        else:
            model_provider = "Unknown"
            print(f"\nSelected model: {Fore.GREEN + Style.BRIGHT}{model_name}{Style.RESET_ALL}\n")

    # Create and run the backtester
    backtester = Backtester(
        agent=run_hedge_fund,
        tickers=tickers,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.initial_capital,
        model_name=model_name,
        model_provider=model_provider,
        selected_analysts=selected_analysts,
        initial_margin_requirement=args.margin_requirement,
    )

    performance_metrics = backtester.run_backtest()
    performance_df = backtester.analyze_performance()
    
    # Ask user if they want to see interactive visualizations
    try:
        show_charts = questionary.confirm(
            "Would you like to see interactive charts and advanced metrics?",
            default=True
        ).ask()
        
        if show_charts:
            print("\nGenerating interactive charts...")
            try:
                backtester.create_interactive_charts()
                backtester.create_performance_metrics_dashboard()
            except ImportError as e:
                print(f"{Fore.YELLOW}Warning: Interactive charts require additional packages.{Style.RESET_ALL}")
                print(f"Error: {e}")
                print(f"{Fore.CYAN}To install required packages, run:{Style.RESET_ALL}")
                print("pip install plotly seaborn")
                print("\nShowing basic performance analysis instead...")
            except Exception as e:
                print(f"{Fore.RED}Error creating interactive charts: {e}{Style.RESET_ALL}")
                print("Showing basic performance analysis instead...")
    except KeyboardInterrupt:
        print("\nSkipping interactive charts...")
