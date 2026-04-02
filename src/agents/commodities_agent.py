"""Commodities Trading Agent - Specialized agent for commodity market analysis and trading."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..graph.state import AgentState
from ..integrations.openbb_integration import get_openbb_provider
from ..utils.llm import call_llm


class CommodityAnalysis(BaseModel):
    """Pydantic model for commodity analysis results."""

    symbol: str = Field(description="Commodity symbol")
    commodity_name: str = Field(description="Human readable commodity name")
    current_price: float = Field(description="Current commodity price")
    price_change_percent: float = Field(description="Price change percentage")
    trend_analysis: str = Field(description="Trend analysis (Bullish/Bearish/Neutral)")
    supply_demand_factors: str = Field(description="Key supply and demand factors")
    seasonal_patterns: str = Field(description="Seasonal patterns affecting the commodity")
    geopolitical_impact: str = Field(description="Geopolitical factors impact")
    economic_indicators: str = Field(description="Relevant economic indicators")
    trading_recommendation: str = Field(description="Trading recommendation (BUY/SELL/HOLD)")
    risk_assessment: str = Field(description="Risk assessment (Low/Medium/High)")
    price_targets: Dict[str, float] = Field(description="Price targets (support, resistance)")
    confidence_score: float = Field(description="Confidence score (0-1)")


class CommoditiesAgent:
    """Specialized agent for commodity market analysis and trading decisions."""

    def __init__(self, name: str = "Commodities Specialist"):
        """Initialize the commodities agent."""
        self.name = name
        self.openbb = get_openbb_provider()

        # Commodity mappings
        self.commodity_symbols = {
            "GC=F": "Gold",
            "SI=F": "Silver",
            "CL=F": "Crude Oil",
            "NG=F": "Natural Gas",
            "HG=F": "Copper",
            "ZC=F": "Corn",
            "ZS=F": "Soybeans",
            "ZW=F": "Wheat",
            "KC=F": "Coffee",
            "SB=F": "Sugar",
            "CT=F": "Cotton",
            "LBS=F": "Lumber",
        }

        if not self.openbb.is_available():
            logging.warning("OpenBB Platform not available. Commodities agent will have limited functionality.")

    def analyze_commodity(self, symbol: str, state: Optional[AgentState] = None, days: int = 60) -> CommodityAnalysis:
        """
        Analyze a specific commodity with comprehensive market analysis.

        Args:
            symbol: Commodity symbol (e.g., 'GC=F' for Gold)
            state: Agent state for LLM configuration
            days: Number of days of historical data to analyze

        Returns:
            CommodityAnalysis with detailed analysis
        """
        try:
            # Get commodity name
            commodity_name = self.commodity_symbols.get(symbol, symbol)

            # Get historical data
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            price_data = None
            if self.openbb.is_available():
                price_data = self.openbb.get_commodities_data(symbol=symbol, start_date=start_date, end_date=end_date)

            # Prepare analysis context
            analysis_context = {
                "symbol": symbol,
                "commodity_name": commodity_name,
                "has_price_data": price_data is not None and not price_data.empty,
                "analysis_period": days,
            }

            if price_data is not None and not price_data.empty:
                # Calculate technical indicators
                latest_price = float(price_data["close"].iloc[-1])
                prev_price = float(price_data["close"].iloc[-2])
                price_change_pct = ((latest_price - prev_price) / prev_price) * 100

                # Moving averages
                ma_20 = float(price_data["close"].tail(20).mean())
                ma_50 = float(price_data["close"].tail(50).mean()) if len(price_data) >= 50 else ma_20

                # Volatility
                returns = price_data["close"].pct_change().dropna()
                volatility = float(returns.std() * (252**0.5))

                # Support and resistance
                high_52w = float(price_data["high"].max())
                low_52w = float(price_data["low"].min())

                analysis_context.update(
                    {
                        "current_price": latest_price,
                        "price_change_percent": price_change_pct,
                        "ma_20": ma_20,
                        "ma_50": ma_50,
                        "volatility": volatility,
                        "52_week_high": high_52w,
                        "52_week_low": low_52w,
                        "trend_signal": "Bullish" if latest_price > ma_20 else "Bearish",
                    }
                )
            else:
                analysis_context.update(
                    {"current_price": 0.0, "price_change_percent": 0.0, "error": "No price data available"}
                )

            # Create analysis prompt
            prompt = self._create_commodity_analysis_prompt(analysis_context)

            # Call LLM for analysis
            analysis = call_llm(prompt=prompt, pydantic_model=CommodityAnalysis, agent_name=self.name, state=state)

            # Type cast to ensure correct return type
            if isinstance(analysis, CommodityAnalysis):
                return analysis
            else:
                # Fallback if LLM returns unexpected type
                return CommodityAnalysis(
                    symbol=symbol,
                    commodity_name=commodity_name,
                    current_price=analysis_context.get("current_price", 0.0),
                    price_change_percent=analysis_context.get("price_change_percent", 0.0),
                    trend_analysis="Analysis completed with limited data",
                    supply_demand_factors="Limited analysis available",
                    seasonal_patterns="Limited analysis available",
                    geopolitical_impact="Limited analysis available",
                    economic_indicators="Limited analysis available",
                    trading_recommendation="HOLD",
                    risk_assessment="Medium",
                    price_targets={"support": 0.0, "resistance": 0.0},
                    confidence_score=0.5,
                )

        except Exception as e:
            logging.error(f"Error analyzing commodity {symbol}: {e}")
            # Return default analysis on error
            return CommodityAnalysis(
                symbol=symbol,
                commodity_name=self.commodity_symbols.get(symbol, symbol),
                current_price=0.0,
                price_change_percent=0.0,
                trend_analysis="Unable to analyze due to data error",
                supply_demand_factors="Data unavailable",
                seasonal_patterns="Data unavailable",
                geopolitical_impact="Data unavailable",
                economic_indicators="Data unavailable",
                trading_recommendation="HOLD",
                risk_assessment="High",
                price_targets={"support": 0.0, "resistance": 0.0},
                confidence_score=0.0,
            )

    def _create_commodity_analysis_prompt(self, context: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for commodity analysis."""

        prompt = f"""
You are a world-class commodities trading expert with deep knowledge of global commodity markets, supply chains, geopolitical factors, and economic indicators.

Analyze the following commodity:

**Commodity Information:**
- Symbol: {context['symbol']}
- Name: {context['commodity_name']}
- Analysis Period: {context['analysis_period']} days

"""

        if context.get("has_price_data"):
            prompt += f"""
**Technical Analysis Data:**
- Current Price: ${context['current_price']:.2f}
- Price Change: {context['price_change_percent']:.2f}%
- 20-day Moving Average: ${context['ma_20']:.2f}
- 50-day Moving Average: ${context['ma_50']:.2f}
- Volatility (Annualized): {context['volatility']:.2f}
- 52-Week High: ${context['52_week_high']:.2f}
- 52-Week Low: ${context['52_week_low']:.2f}
- Trend Signal: {context['trend_signal']}
"""
        else:
            prompt += "\n**Note:** Limited price data available for technical analysis.\n"

        prompt += f"""
**Analysis Requirements:**

1. **Trend Analysis**: Analyze the current price trend considering technical indicators and market momentum.

2. **Supply & Demand Factors**: Identify key supply and demand drivers specific to {context['commodity_name']}:
   - Production levels and capacity
   - Inventory levels
   - Consumption patterns
   - Weather impacts (if applicable)
   - Transportation and logistics

3. **Seasonal Patterns**: Analyze seasonal factors affecting {context['commodity_name']}:
   - Harvest cycles (for agricultural commodities)
   - Weather patterns
   - Seasonal demand variations
   - Historical seasonal trends

4. **Geopolitical Impact**: Assess geopolitical factors:
   - Major producing/consuming countries
   - Trade policies and tariffs
   - Political stability in key regions
   - Currency impacts

5. **Economic Indicators**: Consider relevant economic factors:
   - Global economic growth
   - Industrial demand
   - Inflation expectations
   - Dollar strength
   - Interest rates

6. **Trading Recommendation**: Provide a clear BUY/SELL/HOLD recommendation with reasoning.

7. **Risk Assessment**: Evaluate risk level (Low/Medium/High) considering volatility and market factors.

8. **Price Targets**: Estimate support and resistance levels based on technical and fundamental analysis.

9. **Confidence Score**: Rate your confidence in this analysis (0.0 to 1.0).

Provide a comprehensive analysis that considers both technical and fundamental factors specific to commodity markets.
"""

        return prompt

    def analyze_commodity_portfolio(self, symbols: List[str], state: Optional[AgentState] = None) -> Dict[str, Any]:
        """
        Analyze a portfolio of commodities for diversification and correlation.

        Args:
            symbols: List of commodity symbols
            state: Agent state for LLM configuration

        Returns:
            Portfolio analysis results
        """
        try:
            portfolio_analysis = {
                "timestamp": datetime.now().isoformat(),
                "commodities": {},
                "diversification_analysis": {},
                "sector_allocation": {},
                "risk_metrics": {},
            }

            # Analyze each commodity
            for symbol in symbols:
                analysis = self.analyze_commodity(symbol, state)
                portfolio_analysis["commodities"][symbol] = {
                    "name": analysis.commodity_name,
                    "recommendation": analysis.trading_recommendation,
                    "risk_level": analysis.risk_assessment,
                    "confidence": analysis.confidence_score,
                }

            # Categorize commodities by sector
            sectors = {
                "Precious Metals": ["GC=F", "SI=F"],
                "Energy": ["CL=F", "NG=F"],
                "Industrial Metals": ["HG=F"],
                "Agriculture": ["ZC=F", "ZS=F", "ZW=F", "KC=F", "SB=F", "CT=F"],
                "Materials": ["LBS=F"],
            }

            sector_counts = {}
            for sector, sector_symbols in sectors.items():
                count = len([s for s in symbols if s in sector_symbols])
                if count > 0:
                    sector_counts[sector] = count

            portfolio_analysis["sector_allocation"] = sector_counts

            # Calculate diversification score
            total_commodities = len(symbols)
            unique_sectors = len(sector_counts)
            diversification_score = min(1.0, unique_sectors / 4.0)  # Max 4 main sectors

            portfolio_analysis["diversification_analysis"] = {
                "total_commodities": total_commodities,
                "sectors_represented": unique_sectors,
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
            logging.error(f"Error analyzing commodity portfolio: {e}")
            return {"error": str(e)}

    def get_commodity_market_overview(self, state: Optional[AgentState] = None) -> Dict[str, Any]:
        """
        Get comprehensive overview of commodity markets.

        Args:
            state: Agent state for LLM configuration

        Returns:
            Market overview with key insights
        """
        try:
            # Major commodities to analyze
            major_commodities = ["GC=F", "CL=F", "HG=F", "ZC=F"]

            overview = {
                "timestamp": datetime.now().isoformat(),
                "market_sentiment": "Neutral",
                "key_commodities": {},
                "sector_performance": {},
                "market_insights": [],
            }

            bullish_count = 0
            total_count = 0

            # Analyze key commodities
            for symbol in major_commodities:
                try:
                    analysis = self.analyze_commodity(symbol, state, days=30)
                    overview["key_commodities"][symbol] = {
                        "name": analysis.commodity_name,
                        "trend": analysis.trend_analysis,
                        "recommendation": analysis.trading_recommendation,
                        "confidence": analysis.confidence_score,
                    }

                    if analysis.trading_recommendation == "BUY":
                        bullish_count += 1
                    total_count += 1

                except Exception as e:
                    logging.warning(f"Error analyzing {symbol} for overview: {e}")
                    continue

            # Determine overall market sentiment
            if total_count > 0:
                bullish_ratio = bullish_count / total_count
                if bullish_ratio >= 0.7:
                    overview["market_sentiment"] = "Bullish"
                elif bullish_ratio <= 0.3:
                    overview["market_sentiment"] = "Bearish"
                else:
                    overview["market_sentiment"] = "Mixed"

            return overview

        except Exception as e:
            logging.error(f"Error getting commodity market overview: {e}")
            return {"error": str(e)}


# Create global instance
commodities_agent = CommoditiesAgent()


def get_commodities_agent() -> CommoditiesAgent:
    """Get the global commodities agent instance."""
    return commodities_agent


def commodities_analyst_agent(state: AgentState, agent_id: str = "commodities_analyst_agent") -> Dict[str, Any]:
    """
    Commodities analyst agent for analyzing commodity markets and generating trading signals.

    Args:
        state: Agent state containing data and metadata
        agent_id: Unique identifier for this agent instance

    Returns:
        Dictionary with messages and updated data
    """
    import json

    from langchain_core.messages import HumanMessage

    from src.graph.state import show_agent_reasoning
    from src.utils.progress import progress

    data = state.get("data", {})
    tickers = data.get("tickers", [])

    if not tickers:
        raise ValueError("tickers not found in state data")

    # Initialize commodities analysis for each ticker
    commodities_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Analyzing commodity")

        try:
            # Use the commodities agent to analyze the ticker
            analysis = commodities_agent.analyze_commodity(ticker, state)

            # Convert to format expected by the system
            signal = "neutral"
            if analysis.trading_recommendation == "BUY":
                signal = "bullish"
            elif analysis.trading_recommendation == "SELL":
                signal = "bearish"

            # Create structured reasoning
            reasoning = {
                "commodity_info": {
                    "symbol": analysis.symbol,
                    "name": analysis.commodity_name,
                    "current_price": analysis.current_price,
                    "price_change_percent": analysis.price_change_percent,
                },
                "trend_analysis": {"trend": analysis.trend_analysis, "confidence": analysis.confidence_score},
                "fundamental_factors": {
                    "supply_demand": analysis.supply_demand_factors,
                    "seasonal_patterns": analysis.seasonal_patterns,
                    "geopolitical_impact": analysis.geopolitical_impact,
                    "economic_indicators": analysis.economic_indicators,
                },
                "trading_decision": {
                    "recommendation": analysis.trading_recommendation,
                    "risk_assessment": analysis.risk_assessment,
                    "price_targets": analysis.price_targets,
                    "signal_determination": f"{signal.capitalize()} na základě komoditní analýzy",
                },
            }

            commodities_analysis[ticker] = {
                "signal": signal,
                "confidence": round(analysis.confidence_score * 100, 2),
                "reasoning": reasoning,
            }

            progress.update_status(agent_id, ticker, "Hotovo", analysis=json.dumps(reasoning, indent=4))

        except Exception as e:
            logging.error(f"Error analyzing commodity {ticker}: {e}")
            # Provide fallback analysis
            commodities_analysis[ticker] = {
                "signal": "neutral",
                "confidence": 0,
                "reasoning": {
                    "error": f"Unable to analyze commodity {ticker}: {str(e)}",
                    "signal_determination": "Neutral due to analysis error",
                },
            }
            progress.update_status(agent_id, ticker, "Error", analysis=f"Error: {str(e)}")

    # Create message
    message = HumanMessage(
        content=json.dumps(commodities_analysis),
        name=agent_id,
    )

    # Show reasoning if enabled
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(commodities_analysis, "Commodities Analysis Agent")

    # Add signals to analyst_signals
    if "analyst_signals" not in state["data"]:
        state["data"]["analyst_signals"] = {}
    state["data"]["analyst_signals"][agent_id] = commodities_analysis

    progress.update_status(agent_id, None, "Hotovo")

    return {
        "messages": [message],
        "data": data,
    }
