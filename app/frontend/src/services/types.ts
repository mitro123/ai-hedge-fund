// Shared types for API requests and responses
export enum ModelProvider {
  OPENAI = 'OpenAI',
  ANTHROPIC = 'Anthropic',
  GROQ = 'Groq',
  OLLAMA = 'Ollama',
}

export interface AgentModelConfig {
  agent_id: string;
  model_name?: string;
  model_provider?: ModelProvider;
}

export interface GraphNode {
  id: string;
  type?: string;
  data?: any;
  position?: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  data?: any;
}

export interface PortfolioPosition {
  ticker: string;
  quantity: number;
  trade_price: number;
}

// Base interface for shared fields between HedgeFundRequest and BacktestRequest
export interface BaseHedgeFundRequest {
  tickers: string[];
  graph_nodes: GraphNode[];
  graph_edges: GraphEdge[];
  agent_models?: AgentModelConfig[];
  model_name?: string;
  model_provider?: ModelProvider;
  margin_requirement?: number;
  portfolio_positions?: PortfolioPosition[];
}

export interface HedgeFundRequest extends BaseHedgeFundRequest {
  end_date?: string;
  start_date?: string;
  initial_cash?: number;
}

export interface BacktestRequest extends BaseHedgeFundRequest {
  start_date: string;
  end_date: string;
  initial_capital?: number;
}

export interface BacktestDayResult {
  date: string;
  portfolio_value: number;
  cash: number;
  decisions: Record<string, any>;
  executed_trades: Record<string, number>;
  analyst_signals: Record<string, any>;
  current_prices: Record<string, number>;
  long_exposure: number;
  short_exposure: number;
  gross_exposure: number;
  net_exposure: number;
  long_short_ratio: number | null;
}

export interface BacktestPerformanceMetrics {
  sharpe_ratio?: number;
  sortino_ratio?: number;
  calmar_ratio?: number;
  max_drawdown?: number;
  max_drawdown_date?: string;
  long_short_ratio?: number;
  gross_exposure?: number;
  net_exposure?: number;
  total_return?: number;
  win_rate?: number;
  win_loss_ratio?: number;
  best_day?: number;
  worst_day?: number;
  volatility?: number;
  var_95?: number;
  expected_shortfall_95?: number;
  max_consecutive_wins?: number;
  max_consecutive_losses?: number;
}

export interface TradeHistoryItem {
  id: string;
  date: string;
  ticker: string;
  action: 'buy' | 'sell' | 'short' | 'cover';
  quantity: number;
  price: number;
  value: number;
  pnl?: number;
  commission?: number;
  notes?: string;
}

export interface ChartDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface BacktestChartsData {
  portfolio_value: ChartDataPoint[];
  daily_returns: ChartDataPoint[];
  drawdown: ChartDataPoint[];
  cumulative_returns: ChartDataPoint[];
  trade_markers: Array<{
    date: string;
    ticker: string;
    action: string;
    quantity: number;
    price: number;
    value: number;
  }>;
  benchmark_comparison?: ChartDataPoint[];
}

export interface BacktestAdvancedMetrics {
  // Returns metrics
  total_return?: number;
  annualized_return?: number;
  volatility?: number;
  sharpe_ratio?: number;
  sortino_ratio?: number;
  calmar_ratio?: number;
  
  // Risk metrics
  max_drawdown?: number;
  max_drawdown_duration?: number;
  var_95?: number;
  cvar_95?: number;
  beta?: number;
  
  // Efficiency metrics
  information_ratio?: number;
  treynor_ratio?: number;
  jensen_alpha?: number;
  tracking_error?: number;
  
  // Trading metrics
  win_rate?: number;
  profit_factor?: number;
  avg_win?: number;
  avg_loss?: number;
  total_trades?: number;
  
  // Exposure metrics
  avg_gross_exposure?: number;
  avg_net_exposure?: number;
  avg_long_exposure?: number;
  avg_short_exposure?: number;
}

export interface BacktestResults {
  id: string;
  name: string;
  status: string;
  created_at: string;
  completed_at?: string;
  
  // Configuration
  tickers: string[];
  start_date: string;
  end_date: string;
  initial_capital: number;
  
  // Results summary
  final_value?: number;
  total_return?: number;
  total_trades?: number;
  
  // Performance metrics
  performance_metrics?: BacktestPerformanceMetrics;
  advanced_metrics?: BacktestAdvancedMetrics;
  
  // Chart data
  chart_data?: BacktestChartsData;
  
  // Trade history
  trade_history?: TradeHistoryItem[];
}

export interface BacktestListItem {
  id: string;
  name: string;
  status: string;
  created_at: string;
  completed_at?: string;
  tickers: string[];
  final_value?: number;
  total_return?: number;
}

export interface BacktestCreateRequest {
  name: string;
  description?: string;
  
  // Backtest configuration
  tickers: string[];
  start_date: string;
  end_date: string;
  initial_capital?: number;
  
  // Graph configuration
  graph_nodes: GraphNode[];
  graph_edges: GraphEdge[];
  agent_models?: AgentModelConfig[];
  
  // Model settings
  model_name?: string;
  model_provider?: ModelProvider;
  
  // Portfolio settings
  margin_requirement?: number;
  portfolio_positions?: PortfolioPosition[];
  
  // API keys
  api_keys?: Record<string, string>;
}

export interface BacktestStatus {
  backtest_id: string;
  status: string;
  created_at?: string;
  completed_at?: string;
  error?: string;
}

export interface BacktestVisualizationConfig {
  enable_interactive_charts?: boolean;
  enable_performance_dashboard?: boolean;
  chart_types?: string[];
}
