"""Forex Trading Agent - Specialized agent for foreign exchange market analysis and trading."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..graph.state import AgentState
from ..integrations.openbb_integration import get_openbb_provider
from ..utils.llm import call_llm


class ForexAnalysis(BaseModel):
    """Pydantic model for forex analysis results."""

    symbol: str = Field(description="Currency pair symbol")
    pair_name: str = Field(description="Human readable currency pair name")
    current_rate: float = Field(description="Current exchange rate")
    rate_change_percent: float = Field(description="Rate change percentage")
    trend_analysis: str = Field(description="Trend analysis (Bullish/Bearish/Neutral)")
    technical_indicators: str = Field(description="Technical analysis summary")
    fundamental_factors: str = Field(description="Key fundamental factors")
    central_bank_policy: str = Field(description="Central bank policy impact")
    economic_data_impact: str = Field(description="Economic data and indicators impact")
    geopolitical_factors: str = Field(description="Geopolitical factors affecting the pair")
    trading_recommendation: str = Field(description="Trading recommendation (BUY/SELL/HOLD)")
    risk_assessment: str = Field(description="Risk assessment (Low/Medium/High)")
    support_resistance: Dict[str, float] = Field(description="Support and resistance levels")
    confidence_score: float = Field(description="Confidence score (0-1)")


class ForexAgent:
    """Specialized agent for forex market analysis and trading decisions."""

    def __init__(self, name: str = "Forex Specialist"):
        """Initialize the forex agent."""
        self.name = name
        self.openbb = get_openbb_provider()

        # Currency pair mappings
        self.currency_pairs = {
            "EURUSD=X": "EUR/USD",
            "GBPUSD=X": "GBP/USD",
            "USDJPY=X": "USD/JPY",
            "USDCHF=X": "USD/CHF",
            "AUDUSD=X": "AUD/USD",
            "USDCAD=X": "USD/CAD",
            "NZDUSD=X": "NZD/USD",
            "EURGBP=X": "EUR/GBP",
            "EURJPY=X": "EUR/JPY",
            "GBPJPY=X": "GBP/JPY",
            "CHFJPY=X": "CHF/JPY",
            "AUDCAD=X": "AUD/CAD",
            "AUDCHF=X": "AUD/CHF",
            "AUDJPY=X": "AUD/JPY",
            "CADCHF=X": "CAD/CHF",
            "CADJPY=X": "CAD/JPY",
            "EURCHF=X": "EUR/CHF",
            "EURNZD=X": "EUR/NZD",
            "EURAUD=X": "EUR/AUD",
            "EURCAD=X": "EUR/CAD",
            "GBPAUD=X": "GBP/AUD",
            "GBPCAD=X": "GBP/CAD",
            "GBPCHF=X": "GBP/CHF",
            "GBPNZD=X": "GBP/NZD",
            "NZDCAD=X": "NZD/CAD",
            "NZDCHF=X": "NZD/CHF",
            "NZDJPY=X": "NZD/JPY",
        }

        # Major currency information
        self.currency_info = {
            "USD": {"name": "US Dollar", "central_bank": "Federal Reserve"},
            "EUR": {"name": "Euro", "central_bank": "European Central Bank"},
            "GBP": {"name": "British Pound", "central_bank": "Bank of England"},
            "JPY": {"name": "Japanese Yen", "central_bank": "Bank of Japan"},
            "CHF": {"name": "Swiss Franc", "central_bank": "Swiss National Bank"},
            "AUD": {"name": "Australian Dollar", "central_bank": "Reserve Bank of Australia"},
            "CAD": {"name": "Canadian Dollar", "central_bank": "Bank of Canada"},
            "NZD": {"name": "New Zealand Dollar", "central_bank": "Reserve Bank of New Zealand"},
        }

        if not self.openbb.is_available():
            logging.warning("OpenBB Platform not available. Forex agent will have limited functionality.")

    def analyze_currency_pair(self, symbol: str, state: Optional[AgentState] = None, days: int = 60) -> ForexAnalysis:
        """
        Analyze a specific currency pair with comprehensive market analysis.

        Args:
            symbol: Currency pair symbol (e.g., 'EURUSD=X')
            state: Agent state for LLM configuration
            days: Number of days of historical data to analyze

        Returns:
            ForexAnalysis with detailed analysis
        """
        try:
            # Get pair name
            pair_name = self.currency_pairs.get(symbol, symbol)

            # Extract base and quote currencies
            base_currency, quote_currency = self._extract_currencies(symbol)

            # Get historical data
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            price_data = None
            if self.openbb.is_available():
                price_data = self.openbb.get_forex_data(symbol=symbol, start_date=start_date, end_date=end_date)

            # Prepare analysis context
            analysis_context = {
                "symbol": symbol,
                "pair_name": pair_name,
                "base_currency": base_currency,
                "quote_currency": quote_currency,
                "has_price_data": price_data is not None and not price_data.empty,
                "analysis_period": days,
            }

            if price_data is not None and not price_data.empty:
                # Calculate technical indicators
                latest_rate = float(price_data["close"].iloc[-1])
                prev_rate = float(price_data["close"].iloc[-2])
                rate_change_pct = ((latest_rate - prev_rate) / prev_rate) * 100

                # Moving averages
                ma_20 = float(price_data["close"].tail(20).mean())
                ma_50 = float(price_data["close"].tail(50).mean()) if len(price_data) >= 50 else ma_20

                # Volatility
                returns = price_data["close"].pct_change().dropna()
                volatility = float(returns.std() * (252**0.5))

                # Support and resistance
                high_period = float(price_data["high"].max())
                low_period = float(price_data["low"].min())

                # RSI calculation (simplified)
                delta = price_data["close"].diff()
                gains = delta.where(delta > 0, 0).rolling(window=14).mean()
                losses = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gains / losses
                rsi = 100 - (100 / (1 + rs))
                current_rsi = float(rsi.iloc[-1]) if not rsi.empty and rsi.iloc[-1] is not None else 50.0

                analysis_context.update(
                    {
                        "current_rate": latest_rate,
                        "rate_change_percent": rate_change_pct,
                        "ma_20": ma_20,
                        "ma_50": ma_50,
                        "volatility": volatility,
                        "period_high": high_period,
                        "period_low": low_period,
                        "rsi": current_rsi,
                        "trend_signal": "Bullish" if latest_rate > ma_20 else "Bearish",
                    }
                )
            else:
                analysis_context.update(
                    {"current_rate": 0.0, "rate_change_percent": 0.0, "error": "No price data available"}
                )

            # Add currency-specific information
            if base_currency in self.currency_info:
                analysis_context["base_currency_info"] = self.currency_info[base_currency]
            if quote_currency in self.currency_info:
                analysis_context["quote_currency_info"] = self.currency_info[quote_currency]

            # Create analysis prompt
            prompt = self._create_forex_analysis_prompt(analysis_context)

            # Call LLM for analysis
            analysis = call_llm(prompt=prompt, pydantic_model=ForexAnalysis, agent_name=self.name, state=state)

            # Type cast to ensure correct return type
            if isinstance(analysis, ForexAnalysis):
                return analysis
            else:
                # Fallback if LLM returns unexpected type
                return ForexAnalysis(
                    symbol=symbol,
                    pair_name=pair_name,
                    current_rate=analysis_context.get("current_rate", 0.0),
                    rate_change_percent=analysis_context.get("rate_change_percent", 0.0),
                    trend_analysis="Analysis completed with limited data",
                    technical_indicators="Limited analysis available",
                    fundamental_factors="Limited analysis available",
                    central_bank_policy="Limited analysis available",
                    economic_data_impact="Limited analysis available",
                    geopolitical_factors="Limited analysis available",
                    trading_recommendation="HOLD",
                    risk_assessment="Medium",
                    support_resistance={"support": 0.0, "resistance": 0.0},
                    confidence_score=0.5,
                )

        except Exception as e:
            logging.error(f"Error analyzing currency pair {symbol}: {e}")
            # Return default analysis on error
            return ForexAnalysis(
                symbol=symbol,
                pair_name=self.currency_pairs.get(symbol, symbol),
                current_rate=0.0,
                rate_change_percent=0.0,
                trend_analysis="Unable to analyze due to data error",
                technical_indicators="Data unavailable",
                fundamental_factors="Data unavailable",
                central_bank_policy="Data unavailable",
                economic_data_impact="Data unavailable",
                geopolitical_factors="Data unavailable",
                trading_recommendation="HOLD",
                risk_assessment="High",
                support_resistance={"support": 0.0, "resistance": 0.0},
                confidence_score=0.0,
            )

    def _extract_currencies(self, symbol: str) -> tuple[str, str]:
        """Extract base and quote currencies from symbol."""
        # Remove =X suffix if present
        clean_symbol = symbol.replace("=X", "")

        # Common 6-character pairs
        if len(clean_symbol) == 6:
            return clean_symbol[:3], clean_symbol[3:]

        # Handle special cases
        if "USD" in clean_symbol:
            if clean_symbol.startswith("USD"):
                return "USD", clean_symbol[3:]
            else:
                return clean_symbol.replace("USD", ""), "USD"

        # Default fallback
        return clean_symbol[:3], clean_symbol[3:] if len(clean_symbol) >= 6 else "USD"

    def _create_forex_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for forex analysis."""

        prompt = f"""
You are a world-class forex trading expert with deep knowledge of global currency markets, central bank policies, economic indicators, and geopolitical factors.

Analyze the following currency pair:

**Currency Pair Information:**
- Symbol: {context['symbol']}
- Pair: {context['pair_name']}
- Base Currency: {context['base_currency']}
- Quote Currency: {context['quote_currency']}
- Analysis Period: {context['analysis_period']} days

"""

        if context.get("has_price_data"):
            prompt += f"""
**Technical Analysis Data:**
- Current Rate: {context['current_rate']:.5f}
- Rate Change: {context['rate_change_percent']:.2f}%
- 20-day Moving Average: {context['ma_20']:.5f}
- 50-day Moving Average: {context['ma_50']:.5f}
- Volatility (Annualized): {context['volatility']:.2f}
- Period High: {context['period_high']:.5f}
- Period Low: {context['period_low']:.5f}
- RSI: {context['rsi']:.1f}
- Trend Signal: {context['trend_signal']}
"""
        else:
            prompt += "\n**Note:** Limited price data available for technical analysis.\n"

        # Add currency-specific information
        if context.get("base_currency_info"):
            prompt += f"\n**Base Currency ({context['base_currency']}):**\n"
            prompt += f"- Name: {context['base_currency_info']['name']}\n"
            prompt += f"- Central Bank: {context['base_currency_info']['central_bank']}\n"

        if context.get("quote_currency_info"):
            prompt += f"\n**Quote Currency ({context['quote_currency']}):**\n"
            prompt += f"- Name: {context['quote_currency_info']['name']}\n"
            prompt += f"- Central Bank: {context['quote_currency_info']['central_bank']}\n"

        prompt += f"""

**Analysis Requirements:**

1. **Trend Analysis**: Analyze the current trend considering technical indicators, momentum, and price action.

2. **Technical Indicators**: Summarize key technical signals:
   - Moving average crossovers
   - RSI levels and momentum
   - Support and resistance levels
   - Chart patterns

3. **Fundamental Factors**: Identify key fundamental drivers:
   - Interest rate differentials
   - Economic growth prospects
   - Inflation expectations
   - Trade balances
   - Political stability

4. **Central Bank Policy**: Assess central bank policies and their impact:
   - Current monetary policy stance
   - Recent policy changes or announcements
   - Forward guidance and expectations
   - Policy divergence between countries

5. **Economic Data Impact**: Consider recent and upcoming economic data:
   - GDP growth rates
   - Employment data
   - Inflation reports
   - Manufacturing and services PMI
   - Consumer confidence

6. **Geopolitical Factors**: Evaluate geopolitical influences:
   - Political events and elections
   - Trade relations and agreements
   - Global risk sentiment
   - Safe-haven flows

7. **Trading Recommendation**: Provide a clear BUY/SELL/HOLD recommendation with reasoning.

8. **Risk Assessment**: Evaluate risk level (Low/Medium/High) considering volatility and market factors.

9. **Support and Resistance**: Identify key technical levels for support and resistance.

10. **Confidence Score**: Rate your confidence in this analysis (0.0 to 1.0).

Provide a comprehensive analysis that considers both technical and fundamental factors specific to forex markets.
"""

        return prompt

    def analyze_forex_portfolio(self, symbols: List[str], state: Optional[AgentState] = None) -> Dict[str, Any]:
        """
        Analyze a portfolio of currency pairs for diversification and correlation.

        Args:
            symbols: List of currency pair symbols
            state: Agent state for LLM configuration

        Returns:
            Portfolio analysis results
        """
        try:
            portfolio_analysis = {
                "timestamp": datetime.now().isoformat(),
                "currency_pairs": {},
                "currency_exposure": {},
                "diversification_analysis": {},
                "risk_metrics": {},
            }

            # Track currency exposure
            currency_exposure = {}

            # Analyze each currency pair
            for symbol in symbols:
                analysis = self.analyze_currency_pair(symbol, state)
                portfolio_analysis["currency_pairs"][symbol] = {
                    "pair_name": analysis.pair_name,
                    "recommendation": analysis.trading_recommendation,
                    "risk_level": analysis.risk_assessment,
                    "confidence": analysis.confidence_score,
                }

                # Track currency exposure
                base_currency, quote_currency = self._extract_currencies(symbol)
                currency_exposure[base_currency] = currency_exposure.get(base_currency, 0) + 1
                currency_exposure[quote_currency] = currency_exposure.get(quote_currency, 0) + 1

            portfolio_analysis["currency_exposure"] = currency_exposure

            # Calculate diversification metrics
            total_pairs = len(symbols)
            unique_currencies = len(currency_exposure)
            max_exposure = max(currency_exposure.values()) if currency_exposure else 0

            # Diversification score (lower concentration = better diversification)
            concentration_ratio = max_exposure / (total_pairs * 2) if total_pairs > 0 else 0
            diversification_score = max(0, 1 - concentration_ratio)

            portfolio_analysis["diversification_analysis"] = {
                "total_pairs": total_pairs,
                "unique_currencies": unique_currencies,
                "max_currency_exposure": max_exposure,
                "concentration_ratio": concentration_ratio,
                "diversification_score": diversification_score,
                "diversification_rating": (
                    "Excellent"
                    if diversification_score > 0.8
                    else (
                        "Good" if diversification_score > 0.6 else "Moderate" if diversification_score > 0.4 else "Poor"
                    )
                ),
            }

            return portfolio_analysis

        except Exception as e:
            logging.error(f"Error analyzing forex portfolio: {e}")
            return {"error": str(e)}

    def get_forex_market_overview(self, state: Optional[AgentState] = None) -> Dict[str, Any]:
        """
        Get comprehensive overview of forex markets.

        Args:
            state: Agent state for LLM configuration

        Returns:
            Market overview with key insights
        """
        try:
            # Major currency pairs to analyze
            major_pairs = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X"]

            overview = {
                "timestamp": datetime.now().isoformat(),
                "market_sentiment": "Neutral",
                "major_pairs": {},
                "currency_strength": {},
                "market_insights": [],
            }

            usd_bullish_count = 0
            total_usd_pairs = 0

            # Analyze major pairs
            for symbol in major_pairs:
                try:
                    analysis = self.analyze_currency_pair(symbol, state, days=30)
                    overview["major_pairs"][symbol] = {
                        "pair_name": analysis.pair_name,
                        "trend": analysis.trend_analysis,
                        "recommendation": analysis.trading_recommendation,
                        "confidence": analysis.confidence_score,
                    }

                    # Track USD strength
                    if "USD" in symbol:
                        total_usd_pairs += 1
                        if (symbol.startswith("USD") and analysis.trading_recommendation == "BUY") or (
                            not symbol.startswith("USD") and analysis.trading_recommendation == "SELL"
                        ):
                            usd_bullish_count += 1

                except Exception as e:
                    logging.warning(f"Error analyzing {symbol} for overview: {e}")
                    continue

            # Determine USD strength
            if total_usd_pairs > 0:
                usd_strength_ratio = usd_bullish_count / total_usd_pairs
                if usd_strength_ratio >= 0.7:
                    overview["currency_strength"]["USD"] = "Strong"
                elif usd_strength_ratio <= 0.3:
                    overview["currency_strength"]["USD"] = "Weak"
                else:
                    overview["currency_strength"]["USD"] = "Neutral"

            return overview

        except Exception as e:
            logging.error(f"Error getting forex market overview: {e}")
            return {"error": str(e)}


# Create global instance
forex_agent = ForexAgent()


def get_forex_agent() -> ForexAgent:
    """Get the global forex agent instance."""
    return forex_agent
