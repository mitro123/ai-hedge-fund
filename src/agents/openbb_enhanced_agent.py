"""Enhanced AI agent using OpenBB Platform for comprehensive financial analysis."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from ..exceptions import APIKeyError
from ..integrations.openbb_integration import get_openbb_provider


class OpenBBEnhancedAgent:
    """Enhanced AI agent leveraging OpenBB Platform for advanced financial analysis."""

    def __init__(self, name: str = "OpenBB Enhanced Agent"):
        """Initialize the enhanced agent."""
        self.name = name
        self.openbb = get_openbb_provider()

        if not self.openbb.is_available():
            logging.warning("OpenBB Platform not available. Agent will have limited functionality.")

    def analyze_stock_comprehensive(self, symbol: str, days: int = 30, provider: str = "yfinance") -> Dict[str, Any]:
        """
        Perform comprehensive stock analysis using OpenBB data.

        Args:
            symbol: Stock symbol to analyze
            days: Number of days of historical data
            provider: Data provider to use

        Returns:
            Comprehensive analysis results
        """
        analysis = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "data_provider": provider,
            "analysis_period_days": days,
            "openbb_available": self.openbb.is_available(),
        }

        if not self.openbb.is_available():
            analysis["error"] = "OpenBB Platform not available"
            return analysis

        try:
            # Get historical price data
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            price_data = self.openbb.get_historical_prices(
                symbol=symbol, start_date=start_date, end_date=end_date, provider=provider
            )

            if price_data is not None and not price_data.empty:
                analysis["price_analysis"] = self._analyze_price_data(price_data)
            else:
                analysis["price_analysis"] = {"error": "No price data available"}

            # Get company information
            company_info = self.openbb.get_company_info(symbol, provider)
            if company_info:
                analysis["company_info"] = company_info

            # Get financial statements
            income_statement = self.openbb.get_financial_statements(symbol, "income", "annual", 3, provider)
            if income_statement is not None and not income_statement.empty:
                analysis["financial_health"] = self._analyze_financials(income_statement)

            # Get market news
            news = self.openbb.get_market_news(symbol, limit=5, provider="benzinga")
            if news is not None and not news.empty:
                analysis["recent_news"] = self._analyze_news_sentiment(news)

            # Generate trading recommendation
            analysis["recommendation"] = self._generate_recommendation(analysis)

        except Exception as e:
            logging.error(f"Error in comprehensive analysis for {symbol}: {e}")
            analysis["error"] = str(e)

        return analysis

    def _analyze_price_data(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price data and calculate technical indicators."""
        try:
            latest_price = float(price_data["close"].iloc[-1])
            price_change = float(price_data["close"].iloc[-1] - price_data["close"].iloc[-2])
            price_change_pct = (price_change / price_data["close"].iloc[-2]) * 100

            # Calculate moving averages
            ma_5 = float(price_data["close"].tail(5).mean())
            ma_20 = float(price_data["close"].tail(20).mean()) if len(price_data) >= 20 else ma_5

            # Calculate volatility
            returns = price_data["close"].pct_change().dropna()
            volatility = float(returns.std() * (252**0.5))  # Annualized volatility

            # Calculate RSI (simplified)
            delta = price_data["close"].diff()

            # Calculate gains and losses manually to avoid type issues
            gains = []
            losses = []
            for val in delta:
                try:
                    # Handle different types safely
                    if val is None or pd.isna(val):
                        gains.append(0.0)
                        losses.append(0.0)
                    elif isinstance(val, (int, float)):
                        float_val = float(val)
                        if float_val > 0:
                            gains.append(float_val)
                            losses.append(0.0)
                        else:
                            gains.append(0.0)
                            losses.append(-float_val)
                    else:
                        # Try to convert to float, fallback to 0 if fails
                        try:
                            float_val = float(val)
                            if float_val > 0:
                                gains.append(float_val)
                                losses.append(0.0)
                            else:
                                gains.append(0.0)
                                losses.append(-float_val)
                        except (TypeError, ValueError):
                            gains.append(0.0)
                            losses.append(0.0)
                except (TypeError, ValueError, OverflowError):
                    gains.append(0.0)
                    losses.append(0.0)

            gain_series = pd.Series(gains, index=delta.index)
            loss_series = pd.Series(losses, index=delta.index)

            avg_gain = gain_series.rolling(window=14).mean()
            avg_loss = loss_series.rolling(window=14).mean()

            # Ensure we have valid data for RSI calculation
            if (
                not avg_gain.empty
                and not avg_loss.empty
                and not pd.isna(avg_gain.iloc[-1])
                and not pd.isna(avg_loss.iloc[-1])
                and avg_loss.iloc[-1] != 0
            ):
                rs = avg_gain.iloc[-1] / avg_loss.iloc[-1]
                rsi = float(100 - (100 / (1 + rs)))
            else:
                rsi = 50.0

            # Support and resistance levels
            high_52w = float(price_data["high"].max())
            low_52w = float(price_data["low"].min())

            return {
                "latest_price": latest_price,
                "price_change": price_change,
                "price_change_percent": price_change_pct,
                "moving_average_5": ma_5,
                "moving_average_20": ma_20,
                "volatility_annualized": volatility,
                "rsi": rsi,
                "52_week_high": high_52w,
                "52_week_low": low_52w,
                "volume_latest": int(price_data["volume"].iloc[-1]),
                "volume_average": int(price_data["volume"].mean()),
                "trend_signal": "Bullish" if latest_price > ma_20 else "Bearish",
                "momentum_signal": "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral",
            }
        except Exception as e:
            logging.error(f"Error analyzing price data: {e}")
            return {"error": str(e)}

    def _analyze_financials(self, financial_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze financial statements."""
        try:
            if financial_data.empty:
                return {"error": "No financial data available"}

            # Get latest financial metrics
            latest = financial_data.iloc[0] if len(financial_data) > 0 else None
            if latest is None:
                return {"error": "No latest financial data"}

            analysis = {"revenue_growth": None, "profit_margin": None, "financial_strength": "Unknown"}

            # Calculate revenue growth if multiple periods available
            if len(financial_data) >= 2:
                current_revenue = latest.get("revenue", latest.get("total_revenue", 0))
                previous_revenue = financial_data.iloc[1].get("revenue", financial_data.iloc[1].get("total_revenue", 0))

                if current_revenue and previous_revenue and previous_revenue != 0:
                    revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
                    analysis["revenue_growth"] = float(revenue_growth)

            # Calculate profit margin
            revenue = latest.get("revenue", latest.get("total_revenue", 0))
            net_income = latest.get("net_income", latest.get("net_income_loss", 0))

            if revenue and revenue != 0 and net_income is not None:
                profit_margin = (net_income / revenue) * 100
                analysis["profit_margin"] = float(profit_margin)

            # Determine financial strength
            if analysis["profit_margin"] is not None:
                if analysis["profit_margin"] > 15:
                    analysis["financial_strength"] = "Strong"
                elif analysis["profit_margin"] > 5:
                    analysis["financial_strength"] = "Moderate"
                else:
                    analysis["financial_strength"] = "Weak"

            return analysis

        except Exception as e:
            logging.error(f"Error analyzing financial data: {e}")
            return {"error": str(e)}

    def _analyze_news_sentiment(self, news_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze news sentiment (simplified)."""
        try:
            if news_data.empty:
                return {"error": "No news data available"}

            # Simple sentiment analysis based on keywords
            positive_keywords = ["growth", "profit", "increase", "strong", "beat", "exceed", "positive", "bullish"]
            negative_keywords = ["loss", "decline", "decrease", "weak", "miss", "negative", "bearish", "concern"]

            sentiment_scores = []
            news_items = []

            for _, row in news_data.head(5).iterrows():
                title = str(row.get("title", "")).lower()
                summary = str(row.get("summary", row.get("text", ""))).lower()
                content = f"{title} {summary}"

                positive_count = sum(1 for word in positive_keywords if word in content)
                negative_count = sum(1 for word in negative_keywords if word in content)

                if positive_count > negative_count:
                    sentiment = "Positive"
                    score = 1
                elif negative_count > positive_count:
                    sentiment = "Negative"
                    score = -1
                else:
                    sentiment = "Neutral"
                    score = 0

                sentiment_scores.append(score)
                news_items.append(
                    {
                        "title": row.get("title", "No title"),
                        "sentiment": sentiment,
                        "date": str(row.get("date", row.get("published_utc", "Unknown"))),
                    }
                )

            overall_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

            if overall_sentiment > 0.2:
                overall = "Positive"
            elif overall_sentiment < -0.2:
                overall = "Negative"
            else:
                overall = "Neutral"

            return {
                "overall_sentiment": overall,
                "sentiment_score": overall_sentiment,
                "news_count": len(news_items),
                "recent_news": news_items,
            }

        except Exception as e:
            logging.error(f"Error analyzing news sentiment: {e}")
            return {"error": str(e)}

    def _generate_recommendation(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading recommendation based on analysis."""
        try:
            recommendation = {"action": "HOLD", "confidence": 0.5, "reasoning": [], "risk_level": "Medium"}

            score = 0
            reasoning = []

            # Price analysis factors
            price_analysis = analysis.get("price_analysis", {})
            if isinstance(price_analysis, dict) and "error" not in price_analysis:
                # Trend analysis
                if price_analysis.get("trend_signal") == "Bullish":
                    score += 1
                    reasoning.append("Bullish price trend (above 20-day MA)")
                elif price_analysis.get("trend_signal") == "Bearish":
                    score -= 1
                    reasoning.append("Bearish price trend (below 20-day MA)")

                # Momentum analysis
                rsi = price_analysis.get("rsi", 50)
                if rsi < 30:
                    score += 0.5
                    reasoning.append("Oversold conditions (RSI < 30)")
                elif rsi > 70:
                    score -= 0.5
                    reasoning.append("Overbought conditions (RSI > 70)")

                # Volatility analysis
                volatility = price_analysis.get("volatility_annualized", 0.2)
                if volatility > 0.4:
                    recommendation["risk_level"] = "High"
                    reasoning.append("High volatility detected")
                elif volatility < 0.15:
                    recommendation["risk_level"] = "Low"

            # Financial health factors
            financial_health = analysis.get("financial_health", {})
            if isinstance(financial_health, dict) and "error" not in financial_health:
                profit_margin = financial_health.get("profit_margin")
                if profit_margin is not None:
                    if profit_margin > 15:
                        score += 1
                        reasoning.append("Strong profit margins (>15%)")
                    elif profit_margin < 0:
                        score -= 1
                        reasoning.append("Negative profit margins")

                revenue_growth = financial_health.get("revenue_growth")
                if revenue_growth is not None:
                    if revenue_growth > 10:
                        score += 0.5
                        reasoning.append("Strong revenue growth (>10%)")
                    elif revenue_growth < -5:
                        score -= 0.5
                        reasoning.append("Declining revenue (<-5%)")

            # News sentiment factors
            news_sentiment = analysis.get("recent_news", {})
            if isinstance(news_sentiment, dict) and "error" not in news_sentiment:
                sentiment = news_sentiment.get("overall_sentiment")
                if sentiment == "Positive":
                    score += 0.5
                    reasoning.append("Positive news sentiment")
                elif sentiment == "Negative":
                    score -= 0.5
                    reasoning.append("Negative news sentiment")

            # Generate final recommendation
            if score >= 1.5:
                recommendation["action"] = "BUY"
                recommendation["confidence"] = min(0.9, 0.5 + (score - 1.5) * 0.2)
            elif score <= -1.5:
                recommendation["action"] = "SELL"
                recommendation["confidence"] = min(0.9, 0.5 + abs(score + 1.5) * 0.2)
            else:
                recommendation["action"] = "HOLD"
                recommendation["confidence"] = 0.5 + abs(score) * 0.1

            recommendation["reasoning"] = reasoning
            recommendation["score"] = score

            return recommendation

        except Exception as e:
            logging.error(f"Error generating recommendation: {e}")
            return {
                "action": "HOLD",
                "confidence": 0.5,
                "reasoning": ["Error in analysis"],
                "risk_level": "Unknown",
                "error": str(e),
            }

    def get_market_overview(self, provider: str = "yfinance") -> Dict[str, Any]:
        """Get comprehensive market overview."""
        if not self.openbb.is_available():
            return {"error": "OpenBB Platform not available"}

        try:
            indices = ["SPY", "QQQ", "IWM", "DIA", "VTI"]
            overview = {"timestamp": datetime.now().isoformat(), "indices": {}, "market_sentiment": "Neutral"}

            positive_count = 0
            total_count = 0

            for index in indices:
                data = self.openbb.get_historical_prices(
                    symbol=index,
                    start_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                    provider=provider,
                )

                if data is not None and not data.empty:
                    latest_price = float(data["close"].iloc[-1])
                    prev_price = float(data["close"].iloc[-2])
                    change_pct = ((latest_price - prev_price) / prev_price) * 100

                    overview["indices"][index] = {
                        "price": latest_price,
                        "change_percent": change_pct,
                        "trend": "Up" if change_pct > 0 else "Down",
                    }

                    if change_pct > 0:
                        positive_count += 1
                    total_count += 1

            # Determine overall market sentiment
            if total_count > 0:
                positive_ratio = positive_count / total_count
                if positive_ratio >= 0.7:
                    overview["market_sentiment"] = "Bullish"
                elif positive_ratio <= 0.3:
                    overview["market_sentiment"] = "Bearish"
                else:
                    overview["market_sentiment"] = "Neutral"

            return overview

        except Exception as e:
            logging.error(f"Error getting market overview: {e}")
            return {"error": str(e)}

    def analyze_portfolio_diversification(self, symbols: List[str], provider: str = "yfinance") -> Dict[str, Any]:
        """Analyze portfolio diversification using OpenBB data."""
        if not self.openbb.is_available():
            return {"error": "OpenBB Platform not available"}

        try:
            portfolio_analysis = {
                "timestamp": datetime.now().isoformat(),
                "symbols": symbols,
                "correlations": {},
                "risk_metrics": {},
                "diversification_score": 0.0,
            }

            # Get price data for all symbols
            price_data = {}
            for symbol in symbols:
                data = self.openbb.get_historical_prices(
                    symbol=symbol,
                    start_date=(datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
                    end_date=datetime.now().strftime("%Y-%m-%d"),
                    provider=provider,
                )
                if data is not None and not data.empty:
                    price_data[symbol] = data["close"]

            if len(price_data) < 2:
                return {"error": "Insufficient data for diversification analysis"}

            # Calculate correlations
            df = pd.DataFrame(price_data)
            returns = df.pct_change().dropna()
            correlation_matrix = returns.corr()

            # Calculate average correlation (excluding diagonal)
            correlations = []
            for i in range(len(symbols)):
                for j in range(i + 1, len(symbols)):
                    if symbols[i] in correlation_matrix.index and symbols[j] in correlation_matrix.columns:
                        corr = correlation_matrix.loc[symbols[i], symbols[j]]
                        if not pd.isna(corr) and isinstance(corr, (int, float)):
                            correlations.append(abs(float(corr)))

            avg_correlation = sum(correlations) / len(correlations) if correlations else 0

            # Diversification score (lower correlation = better diversification)
            diversification_score = max(0, 1 - avg_correlation)

            portfolio_analysis["correlations"] = correlation_matrix.to_dict()
            portfolio_analysis["average_correlation"] = avg_correlation
            portfolio_analysis["diversification_score"] = diversification_score

            # Risk assessment
            if diversification_score > 0.7:
                portfolio_analysis["diversification_rating"] = "Excellent"
            elif diversification_score > 0.5:
                portfolio_analysis["diversification_rating"] = "Good"
            elif diversification_score > 0.3:
                portfolio_analysis["diversification_rating"] = "Moderate"
            else:
                portfolio_analysis["diversification_rating"] = "Poor"

            return portfolio_analysis

        except Exception as e:
            logging.error(f"Error analyzing portfolio diversification: {e}")
            return {"error": str(e)}


# Create global instance
openbb_enhanced_agent = OpenBBEnhancedAgent()


def get_openbb_enhanced_agent() -> OpenBBEnhancedAgent:
    """Get the global OpenBB enhanced agent instance."""
    return openbb_enhanced_agent
