from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.backend.services.graph import extract_base_agent_key
from src.llm.models import ModelProvider


class FlowRunStatus(str, Enum):
    IDLE = "IDLE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class AgentModelConfig(BaseModel):
    agent_id: str
    model_name: Optional[str] = None
    model_provider: Optional[ModelProvider] = None


class PortfolioPosition(BaseModel):
    ticker: str
    quantity: float
    trade_price: float

    @field_validator("trade_price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Trade price must be positive!")
        return v


class GraphNode(BaseModel):
    id: str
    type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, Any]] = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class HedgeFundResponse(BaseModel):
    decisions: dict
    analyst_signals: dict


class ErrorResponse(BaseModel):
    message: str
    error: str | None = None


# Base class for shared fields between HedgeFundRequest and BacktestRequest
class BaseHedgeFundRequest(BaseModel):
    tickers: List[str]
    graph_nodes: List[GraphNode]
    graph_edges: List[GraphEdge]
    agent_models: Optional[List[AgentModelConfig]] = None
    model_name: Optional[str] = "gpt-4.1"
    model_provider: Optional[ModelProvider] = ModelProvider.OPENROUTER
    margin_requirement: float = 0.0
    portfolio_positions: Optional[List[PortfolioPosition]] = None
    api_keys: Optional[Dict[str, str]] = None

    def get_agent_ids(self) -> List[str]:
        """Extract agent IDs from graph structure"""
        return [node.id for node in self.graph_nodes]

    def get_agent_model_config(self, agent_id: str) -> tuple[str, str]:
        """Get model configuration for a specific agent"""
        if self.agent_models:
            # Extract base agent key from unique node ID for matching
            base_agent_key = extract_base_agent_key(agent_id)

            for config in self.agent_models:
                # Check both unique node ID and base agent key for matches
                config_base_key = extract_base_agent_key(config.agent_id)
                if config.agent_id == agent_id or config_base_key == base_agent_key:
                    # Konverze ModelProvider enum na string hodnotu
                    provider = config.model_provider or self.model_provider or ModelProvider.OPENROUTER
                    provider_str = provider.value if isinstance(provider, ModelProvider) else str(provider)
                    return (
                        config.model_name or self.model_name or "anthropic/claude-3.5-sonnet",
                        provider_str,
                    )
        # Fallback to global model settings
        provider = self.model_provider or ModelProvider.OPENROUTER
        provider_str = provider.value if isinstance(provider, ModelProvider) else str(provider)
        return (self.model_name or "anthropic/claude-3.5-sonnet", provider_str)


class BacktestRequest(BaseHedgeFundRequest):
    start_date: str
    end_date: str
    initial_capital: float = 100000.0


class BacktestDayResult(BaseModel):
    date: str
    portfolio_value: float
    cash: float
    decisions: Dict[str, Any]
    executed_trades: Dict[str, int]
    analyst_signals: Dict[str, Any]
    current_prices: Dict[str, float]
    long_exposure: float
    short_exposure: float
    gross_exposure: float
    net_exposure: float
    long_short_ratio: Optional[float] = None


class BacktestPerformanceMetrics(BaseModel):
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    max_drawdown_date: Optional[str] = None
    long_short_ratio: Optional[float] = None
    gross_exposure: Optional[float] = None
    net_exposure: Optional[float] = None


class BacktestResponse(BaseModel):
    results: List[BacktestDayResult]
    performance_metrics: BacktestPerformanceMetrics
    final_portfolio: Dict[str, Any]


class HedgeFundRequest(BaseHedgeFundRequest):
    end_date: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    start_date: Optional[str] = None
    initial_cash: float = 100000.0

    def get_start_date(self) -> str:
        """Calculate start date if not provided"""
        if self.start_date:
            return self.start_date
        end_date = self.end_date or datetime.now().strftime("%Y-%m-%d")
        return (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")


# Flow-related schemas
class FlowCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    viewport: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    is_template: bool = False
    tags: Optional[List[str]] = None


class FlowUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    viewport: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    is_template: Optional[bool] = None
    tags: Optional[List[str]] = None


class FlowResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    viewport: Optional[Dict[str, Any]]
    data: Optional[Dict[str, Any]]
    is_template: bool
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class FlowSummaryResponse(BaseModel):
    """Lightweight flow response without nodes/edges for listing"""

    id: int
    name: str
    description: Optional[str]
    is_template: bool
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Flow Run schemas
class FlowRunCreateRequest(BaseModel):
    """Request to create a new flow run"""

    request_data: Optional[Dict[str, Any]] = None


class FlowRunUpdateRequest(BaseModel):
    """Request to update an existing flow run"""

    status: Optional[FlowRunStatus] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class FlowRunResponse(BaseModel):
    """Complete flow run response"""

    id: int
    flow_id: int
    status: FlowRunStatus
    run_number: int
    created_at: datetime
    updated_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    request_data: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class FlowRunSummaryResponse(BaseModel):
    """Lightweight flow run response for listing"""

    id: int
    flow_id: int
    status: FlowRunStatus
    run_number: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


# API Key schemas
class ApiKeyCreateRequest(BaseModel):
    """Request to create or update an API key"""

    provider: str = Field(..., min_length=1, max_length=100)
    key_value: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_active: bool = True


class ApiKeyUpdateRequest(BaseModel):
    """Request to update an existing API key"""

    key_value: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ApiKeyResponse(BaseModel):
    """Complete API key response"""

    id: int
    provider: str
    key_value: str
    is_active: bool
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    last_used: Optional[datetime]

    class Config:
        from_attributes = True


class ApiKeySummaryResponse(BaseModel):
    """API key response without the actual key value"""

    id: int
    provider: str
    is_active: bool
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    last_used: Optional[datetime]
    has_key: bool = True  # Indicates if a key is set

    class Config:
        from_attributes = True


class ApiKeyBulkUpdateRequest(BaseModel):
    """Request to update multiple API keys at once"""

    api_keys: List[ApiKeyCreateRequest]


# Backtest API schemas pro frontend komponenty
class TradeHistoryItem(BaseModel):
    """Individual trade item for trade history viewer"""

    id: str
    date: str
    ticker: str
    action: str  # buy, sell, short, cover
    quantity: int
    price: float
    value: float
    pnl: Optional[float] = None
    commission: Optional[float] = None
    notes: Optional[str] = None


class ChartDataPoint(BaseModel):
    """Data point for charts"""

    date: str
    value: float
    label: Optional[str] = None


class BacktestChartData(BaseModel):
    """Chart data for interactive charts"""

    portfolio_value: List[ChartDataPoint]
    daily_returns: List[ChartDataPoint]
    drawdown: List[ChartDataPoint]
    cumulative_returns: List[ChartDataPoint]
    trade_markers: List[Dict[str, Any]]
    benchmark_comparison: Optional[List[ChartDataPoint]] = None


class BacktestAdvancedMetrics(BaseModel):
    """Advanced performance metrics for frontend"""

    # Returns metrics
    total_return: Optional[float] = None
    annualized_return: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None

    # Risk metrics
    max_drawdown: Optional[float] = None
    max_drawdown_duration: Optional[int] = None
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None
    beta: Optional[float] = None

    # Efficiency metrics
    information_ratio: Optional[float] = None
    treynor_ratio: Optional[float] = None
    jensen_alpha: Optional[float] = None
    tracking_error: Optional[float] = None

    # Trading metrics
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    total_trades: Optional[int] = None

    # Exposure metrics
    avg_gross_exposure: Optional[float] = None
    avg_net_exposure: Optional[float] = None
    avg_long_exposure: Optional[float] = None
    avg_short_exposure: Optional[float] = None


class BacktestResultsResponse(BaseModel):
    """Complete backtest results for frontend"""

    id: str
    name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Configuration
    tickers: List[str]
    start_date: str
    end_date: str
    initial_capital: float

    # Results summary
    final_value: Optional[float] = None
    total_return: Optional[float] = None
    total_trades: Optional[int] = None

    # Performance metrics
    performance_metrics: Optional[BacktestPerformanceMetrics] = None
    advanced_metrics: Optional[BacktestAdvancedMetrics] = None

    # Chart data
    chart_data: Optional[BacktestChartData] = None

    # Trade history
    trade_history: Optional[List[TradeHistoryItem]] = None


class BacktestListResponse(BaseModel):
    """Lightweight backtest list item"""

    id: str
    name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    tickers: List[str]
    final_value: Optional[float] = None
    total_return: Optional[float] = None


class BacktestCreateRequest(BaseModel):
    """Request to create a new backtest"""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None

    # Backtest configuration
    tickers: List[str]

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: List[str]) -> List[str]:
        if len(v) < 1:
            raise ValueError("At least one ticker must be provided")
        return v

    start_date: str
    end_date: str
    initial_capital: float = Field(default=100000.0, gt=0)

    # Graph configuration
    graph_nodes: List[GraphNode]
    graph_edges: List[GraphEdge]
    agent_models: Optional[List[AgentModelConfig]] = None

    # Model settings
    model_name: Optional[str] = "gpt-4.1"
    model_provider: Optional[ModelProvider] = ModelProvider.OPENROUTER

    # Portfolio settings
    margin_requirement: float = Field(default=0.0, ge=0.0, le=1.0)
    portfolio_positions: Optional[List[PortfolioPosition]] = None

    # API keys
    api_keys: Optional[Dict[str, str]] = None
