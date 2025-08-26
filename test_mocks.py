"""
Mock implementace pro testování AI Hedge Fund projektu.
Obsahuje mock verze tříd, které nemusí být plně implementované.
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from unittest.mock import Mock


class MockLLMClient:
    """Mock LLM client pro testování."""
    
    def __init__(self):
        self.responses = {}
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """Generuje mock odpověď."""
        return json.dumps({
            "signal": "BUY",
            "confidence": 0.8,
            "reasoning": "Mock analysis"
        })
    
    async def generate_response_async(self, prompt: str, **kwargs) -> str:
        """Generuje mock asynchronní odpověď."""
        return json.dumps({
            "signal": "BUY",
            "confidence": 0.8,
            "reasoning": "Mock async analysis"
        })


class MockAgent:
    """Základní mock agent."""
    
    def __init__(self, name: str = "Mock Agent", llm_client=None):
        self.name = name
        self.llm_client = llm_client or MockLLMClient()
    
    def analyze_stock(self, ticker: str, data: Dict) -> Dict:
        """Mock analýza akcie."""
        return {
            "signal": np.random.choice(["BUY", "SELL", "HOLD"]),
            "confidence": np.random.uniform(0.5, 1.0),
            "reasoning": f"Mock analysis for {ticker}"
        }
    
    async def analyze_stock_async(self, ticker: str, data: Dict) -> Dict:
        """Mock asynchronní analýza akcie."""
        return self.analyze_stock(ticker, data)


class WarrenBuffettAgent(MockAgent):
    """Mock Warren Buffett agent."""
    
    def __init__(self, llm_client=None):
        super().__init__("Warren Buffett", llm_client)


class MichaelBurryAgent(MockAgent):
    """Mock Michael Burry agent."""
    
    def __init__(self, llm_client=None):
        super().__init__("Michael Burry", llm_client)


class FundamentalsAgent(MockAgent):
    """Mock Fundamentals agent."""
    
    def __init__(self, llm_client=None):
        super().__init__("Fundamentals", llm_client)
    
    def analyze_stock(self, ticker: str, data: Dict) -> Dict:
        """Mock fundamentální analýza."""
        return {
            "signal": "BUY",
            "confidence": 0.8,
            "pe_ratio": 25.5,
            "debt_to_equity": 0.3,
            "roe": 0.15
        }


class TechnicalAgent(MockAgent):
    """Mock Technical agent s technickými indikátory."""
    
    def __init__(self, llm_client=None):
        super().__init__("Technical", llm_client)
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Výpočet RSI indikátoru."""
        if len(prices) == 0:
            return pd.Series([])
        
        delta = prices.diff()
        gain = delta.clip(lower=0).rolling(window=period).mean()
        loss = (-delta.clip(upper=0)).rolling(window=period).mean()
        
        # Avoid division by zero
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)  # Fill NaN with neutral value
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Výpočet MACD indikátoru."""
        if len(prices) == 0:
            return pd.Series([]), pd.Series([]), pd.Series([])
        
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2):
        """Výpočet Bollinger Bands."""
        if len(prices) == 0:
            return pd.Series([]), pd.Series([]), pd.Series([])
        
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower


class SentimentAgent(MockAgent):
    """Mock Sentiment agent."""
    
    def __init__(self, llm_client=None):
        super().__init__("Sentiment", llm_client)


class ValuationAgent(MockAgent):
    """Mock Valuation agent."""
    
    def __init__(self, llm_client=None):
        super().__init__("Valuation", llm_client)


class MockPortfolio:
    """Mock portfolio třída."""
    
    def __init__(self, initial_cash: float = 100000, margin_requirement: float = 0.5):
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.margin_requirement = margin_requirement
        self.positions = {}
        self.total_value = initial_cash
    
    def buy_stock(self, ticker: str, quantity: int, price: float):
        """Nákup akcie."""
        cost = quantity * price
        if cost <= self.cash:
            self.cash -= cost
            if ticker in self.positions:
                self.positions[ticker] += quantity
            else:
                self.positions[ticker] = quantity
            return True
        return False
    
    def sell_stock(self, ticker: str, quantity: int, price: float):
        """Prodej akcie."""
        if ticker in self.positions and self.positions[ticker] >= quantity:
            self.cash += quantity * price
            self.positions[ticker] -= quantity
            if self.positions[ticker] == 0:
                del self.positions[ticker]
            return True
        return False


def create_portfolio(initial_cash: float, tickers: List[str], margin_requirement: float = 0.5, portfolio_positions: List = None) -> MockPortfolio:
    """Vytvoří mock portfolio."""
    return MockPortfolio(initial_cash, margin_requirement)


class PortfolioManager:
    """Mock Portfolio Manager."""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client or MockLLMClient()
    
    def make_decisions(self, agent_signals: Dict, portfolio_data: Dict) -> Dict:
        """Mock rozhodování portfolia."""
        return {
            "decisions": {
                "AAPL": {"action": "BUY", "quantity": 10, "reasoning": "Strong signals"}
            }
        }


class RiskManager:
    """Mock Risk Manager."""
    
    def __init__(self):
        pass
    
    def calculate_position_size(self, portfolio_value: float, risk_per_trade: float, stop_loss: float) -> float:
        """Výpočet velikosti pozice."""
        max_risk = portfolio_value * risk_per_trade
        position_size = max_risk / stop_loss
        return min(position_size, portfolio_value * 0.1)  # Max 10% per position


class Backtester:
    """Mock Backtester."""
    
    def __init__(self, tickers: List[str], start_date: str, end_date: str, initial_capital: float, agent=None):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.agent = agent
    
    def run_backtest(self) -> Dict:
        """Spustí mock backtest."""
        return {
            "total_return": 15.5,
            "sharpe_ratio": 1.2,
            "max_drawdown": -8.5,
            "total_trades": 25
        }


class BacktestService:
    """Mock Backtest Service."""
    
    def __init__(self, graph, portfolio, tickers: List[str], start_date: str, end_date: str, 
                 initial_capital: float, model_name: str = "gpt-4", model_provider: str = "openrouter",
                 request: Dict = None):
        self.graph = graph
        self.portfolio = portfolio
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.model_name = model_name
        self.model_provider = model_provider
        self.request = request or {}
    
    async def run_backtest_async(self) -> Dict:
        """Spustí mock asynchronní backtest."""
        return {
            "results": [],
            "portfolio_values": [],
            "performance_metrics": {},
            "final_portfolio": {}
        }


def compile_graph(nodes: List, edges: List, agent_models: List = None, 
                 model_name: str = "gpt-4", model_provider: str = "openrouter"):
    """Mock kompilace grafu."""
    return Mock()


# Mock FastAPI app
try:
    from fastapi import FastAPI
    app = FastAPI(title="Mock AI Hedge Fund API")
    
    @app.get("/health")
    def health_check():
        return {"status": "ok"}
    
except ImportError:
    app = Mock()


# Mock database engine
try:
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///mock.db")
except ImportError:
    engine = Mock()
