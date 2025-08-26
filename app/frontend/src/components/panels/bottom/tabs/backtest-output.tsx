import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { MoreHorizontal, BarChart3, Activity, TrendingUp } from 'lucide-react';
import { getActionColor } from './output-tab-utils';
import { AdvancedPerformanceMetrics } from './advanced-performance-metrics';
import { TradeHistoryViewer } from './trade-history-viewer';
import { InteractiveCharts } from './interactive-charts';
import { useBacktestContext } from '@/contexts/backtest-context';
import { type TradeHistoryItem, type BacktestPerformanceMetrics as ImportedBacktestPerformanceMetrics } from '@/services/types';

// Define TypeScript interfaces for the data structures
interface BacktestAgent {
  message?: string;
  status?: string;
  backtestResults?: BacktestResult[];
}

interface BacktestResult {
  date: string;
  portfolio_value: number;
  cash: number;
  portfolio_return: number;
  ticker_details?: TickerDetail[];
  long_short_ratio?: number;
  performance_metrics?: PerformanceMetrics;
}

interface TickerDetail {
  ticker: string;
  action: string;
  quantity: number;
  price: number;
  shares_owned: number;
  long_shares: number;
  short_shares: number;
  position_value: number;
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
}

interface PerformanceMetrics {
  sharpe_ratio?: number;
  sortino_ratio?: number;
  max_drawdown?: number;
  gross_exposure?: number;
  net_exposure?: number;
  long_short_ratio?: number;
}

interface FinalPortfolio {
  cash: number;
  margin_used: number;
  positions?: Record<string, Position>;
}

interface Position {
  long: number;
  short: number;
  long_cost_basis: number;
  short_cost_basis: number;
}

interface BacktestOutputData {
  performance_metrics?: PerformanceMetrics;
  final_portfolio: FinalPortfolio;
  total_days: number;
}

// Component for displaying backtest progress
function BacktestProgress({ agentData }: { agentData: Record<string, unknown> }) {
  const backtestAgent = agentData['backtest'] as BacktestAgent | undefined;
  
  if (!backtestAgent) return null;
  
  return (
    <Card className="bg-transparent mb-4">
      <CardHeader>
        <CardTitle className="text-lg">Průběh backtestingu</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Current Status */}
          <div className="flex items-center gap-2">
            <MoreHorizontal className="h-4 w-4 text-yellow-500" />
            <span className="font-medium">Spouštěč backtestu</span>
            <span className="text-yellow-500 flex-1">{backtestAgent.message || backtestAgent.status}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Component for displaying backtest trading table (similar to CLI)
function BacktestTradingTable({ agentData }: { agentData: Record<string, unknown> }) {
  const backtestAgent = agentData['backtest'] as BacktestAgent | undefined;

  // console.log("backtestAgent", backtestAgent);
  
  if (!backtestAgent || !backtestAgent.backtestResults) {
    return null;
  }
    
  // Get the backtest results directly from the agent data
  const backtestResults = backtestAgent.backtestResults || [];
  
  if (backtestResults.length === 0) {
    return null;
  }
  
  // Build table rows similar to CLI format
  const tableRows: {type: string; date: string; [key: string]: any}[] = [];
  
  backtestResults.forEach((backtestResult: BacktestResult) => {    
    // Add ticker rows for this period
    if (backtestResult.ticker_details) {
      backtestResult.ticker_details.forEach((ticker: TickerDetail) => {
        tableRows.push({
          type: 'ticker',
          date: backtestResult.date,
          ticker: ticker.ticker,
          action: ticker.action,
          quantity: ticker.quantity,
          price: ticker.price,
          shares_owned: ticker.shares_owned,
          long_shares: ticker.long_shares,
          short_shares: ticker.short_shares,
          position_value: ticker.position_value,
          bullish_count: ticker.bullish_count,
          bearish_count: ticker.bearish_count,
          neutral_count: ticker.neutral_count,
        });
      });
    }
    
    // Add portfolio summary row for this period
    tableRows.push({
      type: 'summary',
      date: backtestResult.date,
      portfolio_value: backtestResult.portfolio_value,
      cash: backtestResult.cash,
      portfolio_return: backtestResult.portfolio_return,
      total_position_value: backtestResult.portfolio_value - backtestResult.cash,
      performance_metrics: backtestResult.performance_metrics,
    });
  });
    
  // Sort by date descending (newest first) and show only the last 50 rows to avoid performance issues
  const recentRows = tableRows
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 50);
  
  
  return (
    <Card className="bg-transparent mb-4">
      <CardHeader>
        <CardTitle className="text-lg">Aktivita</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="max-h-96 overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Datum</TableHead>
                <TableHead>Ticker</TableHead>
                <TableHead>Akce</TableHead>
                <TableHead>Množství</TableHead>
                <TableHead>Cena</TableHead>
                <TableHead>Akcie</TableHead>
                <TableHead>Hodnota pozice</TableHead>
                <TableHead>Býčí</TableHead>
                <TableHead>Medvědí</TableHead>
                <TableHead>Neutrální</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentRows.map((row: any, idx: number) => {
                if (row.type === 'ticker') {
                  return (
                    <TableRow key={idx}>
                      <TableCell className="font-medium">{row.date}</TableCell>
                      <TableCell className="font-medium text-cyan-500">{row.ticker}</TableCell>
                      <TableCell>
                        <span className={cn("font-medium", getActionColor(row.action || ''))}>
                          {row.action?.toUpperCase() || 'DRŽET'}
                        </span>
                      </TableCell>
                      <TableCell className={cn("font-medium", getActionColor(row.action || ''))}>
                        {row.action === 'COVER' && row.quantity === 0 ? 
                          (Math.abs(row.short_shares || 0)).toLocaleString() : 
                          (row.quantity?.toLocaleString() || '0')
                        }
                      </TableCell>
                      <TableCell>${row.price?.toFixed(2) || '0.00'}</TableCell>
                      <TableCell>
                        {row.action === 'COVER' ? 
                          `${row.long_shares || 0} / ${Math.abs(row.short_shares || 0)}` :
                          (row.shares_owned?.toLocaleString() || '0')
                        }
                      </TableCell>
                      <TableCell className="text-primary">
                        ${Math.abs(row.position_value || 0).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-green-500">{row.bullish_count || 0}</TableCell>
                      <TableCell className="text-red-500">{row.bearish_count || 0}</TableCell>
                      <TableCell className="text-blue-500">{row.neutral_count || 0}</TableCell>
                    </TableRow>
                  );
                }
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

// Component for displaying backtest results
function BacktestResults({ outputData }: { outputData: BacktestOutputData }) {
  if (!outputData) {
    return null;
  }

  console.log("outputData", outputData);
  
  if (!outputData.performance_metrics) {
    return (
      <Card className="bg-transparent mb-4">
        <CardHeader>
          <CardTitle className="text-lg">Výsledky backtestingu</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            Backtesting dokončen. Metriky výkonnosti se zobrazí zde.
          </div>
        </CardContent>
      </Card>
    );
  }
  
  const { performance_metrics, final_portfolio, total_days } = outputData;
  
  return (
    <Card className="bg-transparent mb-4">
      <CardHeader>
        <CardTitle className="text-lg">Výsledky backtestingu</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {/* Performance Metrics */}
          <div className="space-y-2">
            <h4 className="font-medium">Metriky výkonnosti</h4>
            <div className="space-y-1 text-sm">
              {performance_metrics.sharpe_ratio !== null && performance_metrics.sharpe_ratio !== undefined && (
                <div className="flex justify-between">
                  <span>Sharpe Ratio:</span>
                  <span className={cn("font-medium", performance_metrics.sharpe_ratio > 1 ? "text-green-500" : "text-red-500")}>
                    {performance_metrics.sharpe_ratio.toFixed(2)}
                  </span>
                </div>
              )}
              {performance_metrics.sortino_ratio !== null && performance_metrics.sortino_ratio !== undefined && (
                <div className="flex justify-between">
                  <span>Sortino Ratio:</span>
                  <span className={cn("font-medium", performance_metrics.sortino_ratio > 1 ? "text-green-500" : "text-red-500")}>
                    {performance_metrics.sortino_ratio.toFixed(2)}
                  </span>
                </div>
              )}
              {performance_metrics.max_drawdown !== null && performance_metrics.max_drawdown !== undefined && (
                <div className="flex justify-between">
                  <span>Max. pokles:</span>
                  <span className="font-medium text-red-500">
                    {Math.abs(performance_metrics.max_drawdown).toFixed(2)}%
                  </span>
                </div>
              )}
            </div>
          </div>
          
          {/* Portfolio Summary */}
          <div className="space-y-2">
            <h4 className="font-medium">Shrnutí portfolia</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Celkem dní:</span>
                <span className="font-medium">{total_days}</span>
              </div>
              <div className="flex justify-between">
                <span>Konečná hotovost:</span>
                <span className="font-medium">${final_portfolio.cash.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Použitá marže:</span>
                <span className="font-medium">${final_portfolio.margin_used.toLocaleString()}</span>
              </div>
            </div>
          </div>
          
          {/* Exposure Metrics */}
          <div className="space-y-2">
            <h4 className="font-medium">Metriky expozice</h4>
            <div className="space-y-1 text-sm">
              {performance_metrics.gross_exposure !== null && performance_metrics.gross_exposure !== undefined && (
                <div className="flex justify-between">
                  <span>Hrubá expozice:</span>
                  <span className="font-medium">${performance_metrics.gross_exposure.toLocaleString()}</span>
                </div>
              )}
              {performance_metrics.net_exposure !== null && performance_metrics.net_exposure !== undefined && (
                <div className="flex justify-between">
                  <span>Čistá expozice:</span>
                  <span className="font-medium">${performance_metrics.net_exposure.toLocaleString()}</span>
                </div>
              )}
              {performance_metrics.long_short_ratio !== null && performance_metrics.long_short_ratio !== undefined && (
                <div className="flex justify-between">
                  <span>Poměr Long/Short:</span>
                  <span className="font-medium">
                    {performance_metrics.long_short_ratio === Infinity || performance_metrics.long_short_ratio === null ? '∞' : performance_metrics.long_short_ratio.toFixed(2)}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Final Positions */}
        {final_portfolio.positions && (
          <div>
            <h4 className="font-medium mb-2">Konečné pozice</h4>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ticker</TableHead>
                  <TableHead>Long akcie</TableHead>
                  <TableHead>Short akcie</TableHead>
                  <TableHead>Long nákladová báze</TableHead>
                  <TableHead>Short nákladová báze</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(final_portfolio.positions).map(([ticker, position]: [string, any]) => (
                  <TableRow key={ticker}>
                    <TableCell className="font-medium">{ticker}</TableCell>
                    <TableCell className={cn(position.long > 0 ? "text-green-500" : "text-muted-foreground")}>
                      {position.long}
                    </TableCell>
                    <TableCell className={cn(position.short > 0 ? "text-red-500" : "text-muted-foreground")}>
                      {position.short}
                    </TableCell>
                    <TableCell>${position.long_cost_basis.toFixed(2)}</TableCell>
                    <TableCell>${position.short_cost_basis.toFixed(2)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Component for displaying real-time backtest performance
function BacktestPerformanceMetrics({ agentData }: { agentData: Record<string, unknown> }) {
  const backtestAgent = agentData['backtest'] as BacktestAgent | undefined;
  
  if (!backtestAgent || !backtestAgent.backtestResults) return null;
  
  // Get the backtest results directly from the agent data
  const backtestResults = backtestAgent.backtestResults || [];
  
  if (backtestResults.length === 0) return null;
  
  const firstPeriod = backtestResults[0];
  const latestPeriod = backtestResults[backtestResults.length - 1];
  
  // Calculate performance metrics
  const initialValue = firstPeriod.portfolio_value;
  const currentValue = latestPeriod.portfolio_value;
  const totalReturn = ((currentValue - initialValue) / initialValue) * 100;
  
  // Calculate win rate (periods with positive returns)
  const periodReturns = backtestResults.slice(1).map((period: BacktestResult, idx: number) => {
    const prevPeriod = backtestResults[idx];
    return ((period.portfolio_value - prevPeriod.portfolio_value) / prevPeriod.portfolio_value) * 100;
  });
  
  const winningPeriods = periodReturns.filter((ret: number) => ret > 0).length;
  const winRate = periodReturns.length > 0 ? (winningPeriods / periodReturns.length) * 100 : 0;
  
  // Calculate max drawdown
  let maxDrawdown = 0;
  let peak = initialValue;
  
  backtestResults.forEach((period: BacktestResult) => {
    if (period.portfolio_value > peak) {
      peak = period.portfolio_value;
    }
    const drawdown = ((period.portfolio_value - peak) / peak) * 100;
    if (drawdown < maxDrawdown) {
      maxDrawdown = drawdown;
    }
  });
  
  return (
    <Card className="bg-transparent mb-4">
      <CardHeader>
        <CardTitle className="text-lg">Výkonnost</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Celkový výnos</div>
            <div className={cn("font-sm", totalReturn >= 0 ? "text-green-500" : "text-red-500")}>
              {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Úspěšnost</div>
            <div className="font-sm">{winRate.toFixed(1)}%</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Max. pokles</div>
            <div className="font-sm text-red-500">{Math.abs(maxDrawdown).toFixed(2)}%</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Obchodovaná období</div>
            <div className="font-sm">{backtestResults.length}</div>
          </div>
        </div>
        
        {/* Additional metrics */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Aktuální hodnota</div>
            <div className="font-sm">${currentValue?.toLocaleString()}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Počáteční hodnota</div>
            <div className="font-sm">${initialValue?.toLocaleString()}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Zisk/Ztráta</div>
            <div className={cn("font-sm", totalReturn >= 0 ? "text-green-500" : "text-red-500")}>
              ${(currentValue - initialValue).toLocaleString()}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Poměr Long/Short</div>
            <div className="font-sm">
              {latestPeriod.long_short_ratio === Infinity || latestPeriod.long_short_ratio === null ? '∞' : latestPeriod.long_short_ratio?.toFixed(2)}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Main component for backtest output
export function BacktestOutput() {
  const { backtest, selectedBacktestId, loading, error } = useBacktestContext();
  
  // If no backtest is selected, show selection prompt
  if (!selectedBacktestId) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground mb-2">Žádný backtest není vybrán</p>
          <p className="text-sm text-muted-foreground">Vyberte backtest ze správy backtestů pro zobrazení výsledků</p>
        </div>
      </div>
    );
  }
  
  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Activity className="h-12 w-12 text-blue-500 mx-auto mb-4 animate-pulse" />
          <p className="text-muted-foreground">Načítání výsledků backtestingu...</p>
        </div>
      </div>
    );
  }
  
  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Activity className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-500 mb-2">Chyba při načítání backtestingu</p>
          <p className="text-sm text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }
  
  // No backtest data
  if (!backtest) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">Backtest nebyl nalezen</p>
        </div>
      </div>
    );
  }
  
  // Create mock agent data and output data from backtest results
  const agentData = {
    backtest: {
      message: `Backtest ${backtest.name} dokončen`,
      status: backtest.status,
      backtestResults: [] // This would be populated from actual backtest data
    }
  };
  
  const outputData: BacktestOutputData = {
    performance_metrics: {
      sharpe_ratio: backtest.performance_metrics?.sharpe_ratio,
      sortino_ratio: backtest.performance_metrics?.sortino_ratio,
      max_drawdown: backtest.performance_metrics?.max_drawdown,
      gross_exposure: backtest.performance_metrics?.gross_exposure,
      net_exposure: backtest.performance_metrics?.net_exposure,
      long_short_ratio: backtest.performance_metrics?.long_short_ratio
    },
    final_portfolio: {
      cash: backtest.final_value || 0,
      margin_used: 0,
      positions: {}
    },
    total_days: Math.floor((new Date(backtest.end_date).getTime() - new Date(backtest.start_date).getTime()) / (1000 * 60 * 60 * 24))
  };
  // Extract data for new components
  const backtestAgent = agentData['backtest'] as BacktestAgent | undefined;
  const backtestResults = backtestAgent?.backtestResults || [];
  
  // Convert backtest results to trade history format
  const tradeHistory: TradeHistoryItem[] = [];
  
  // Debug: Log the raw data to understand the structure
  console.log("Debug - backtestResults:", backtestResults);
  
  backtestResults.forEach((result: BacktestResult) => {
    if (result.ticker_details) {
      result.ticker_details.forEach((ticker: TickerDetail) => {
        console.log("Debug - ticker detail:", ticker);
        
        // Include all actions except HOLD, and ensure we have valid data
        if (ticker.action && ticker.action !== 'HOLD' && ticker.ticker && ticker.price > 0) {
          // For COVER actions, use the absolute value of short_shares if quantity is 0
          let actualQuantity = ticker.quantity || 0;
          if (ticker.action === 'COVER' && actualQuantity === 0) {
            actualQuantity = Math.abs(ticker.short_shares || 0);
          }
          
          // Only add trades with valid quantity
          if (actualQuantity > 0) {
            const trade = {
              id: `${result.date}-${ticker.ticker}-${actualQuantity}`,
              date: result.date,
              ticker: ticker.ticker,
              action: ticker.action.toLowerCase() as 'buy' | 'sell' | 'short' | 'cover',
              quantity: actualQuantity,
              price: ticker.price,
              value: actualQuantity * ticker.price,
              pnl: ticker.position_value ? (ticker.position_value - (actualQuantity * ticker.price)) : undefined,
              commission: (actualQuantity * ticker.price) * 0.001, // 0.1% commission
              notes: `Automated ${ticker.action.toLowerCase()} signal`
            };
            
            console.log("Debug - adding trade:", trade);
            tradeHistory.push(trade);
          }
        }
      });
    }
  });
  
  console.log("Debug - final tradeHistory:", tradeHistory);

  // Convert portfolio values for charts
  const portfolioValues = backtestResults.map((result: BacktestResult, index: number) => {
    const prevValue = index > 0 ? backtestResults[index - 1].portfolio_value : result.portfolio_value;
    const dailyReturn = index > 0 ? ((result.portfolio_value - prevValue) / prevValue) * 100 : 0;
    
    return {
      date: result.date,
      value: result.portfolio_value,
      dailyReturn,
      drawdown: result.portfolio_return || 0
    };
  });

  // Convert performance metrics
  const performanceMetrics: ImportedBacktestPerformanceMetrics = {
    sharpe_ratio: outputData?.performance_metrics?.sharpe_ratio,
    sortino_ratio: outputData?.performance_metrics?.sortino_ratio,
    max_drawdown: outputData?.performance_metrics?.max_drawdown,
    gross_exposure: outputData?.performance_metrics?.gross_exposure,
    net_exposure: outputData?.performance_metrics?.net_exposure,
    long_short_ratio: outputData?.performance_metrics?.long_short_ratio,
    // Calculate additional metrics from available data
    total_return: portfolioValues.length > 1 ? 
      ((portfolioValues[portfolioValues.length - 1].value - portfolioValues[0].value) / portfolioValues[0].value) * 100 : 0,
    win_rate: portfolioValues.length > 1 ? 
      (portfolioValues.filter(p => (p.dailyReturn || 0) > 0).length / (portfolioValues.length - 1)) * 100 : 0,
    volatility: portfolioValues.length > 1 ? 
      Math.sqrt(portfolioValues.reduce((sum, p) => sum + Math.pow(p.dailyReturn || 0, 2), 0) / portfolioValues.length) * Math.sqrt(252) : 0
  };

  return (
    <Tabs defaultValue="overview" className="w-full">
      <TabsList className="grid w-full grid-cols-5">
        <TabsTrigger value="overview" className="text-xs sm:text-sm">
          <span className="flex items-center gap-1 sm:gap-2">
            <Activity className="h-3 w-3 sm:h-4 sm:w-4" />
            <span className="hidden sm:inline">Overview</span>
            <span className="sm:hidden">Overview</span>
          </span>
        </TabsTrigger>
        <TabsTrigger value="metrics" className="text-xs sm:text-sm">
          <span className="flex items-center gap-1 sm:gap-2">
            <TrendingUp className="h-3 w-3 sm:h-4 sm:w-4" />
            <span className="hidden sm:inline">Advanced Metrics</span>
            <span className="sm:hidden">Metrics</span>
          </span>
        </TabsTrigger>
        <TabsTrigger value="trades" className="text-xs sm:text-sm">
          <span className="flex items-center gap-1 sm:gap-2">
            <Activity className="h-3 w-3 sm:h-4 sm:w-4" />
            <span className="hidden sm:inline">Trade History</span>
            <span className="sm:hidden">Trades</span>
          </span>
        </TabsTrigger>
        <TabsTrigger value="charts" className="text-xs sm:text-sm">
          <span className="flex items-center gap-1 sm:gap-2">
            <BarChart3 className="h-3 w-3 sm:h-4 sm:w-4" />
            <span className="hidden sm:inline">Interactive Charts</span>
            <span className="sm:hidden">Charts</span>
          </span>
        </TabsTrigger>
        <TabsTrigger value="activity" className="text-xs sm:text-sm">
          <span className="flex items-center gap-1 sm:gap-2">
            <MoreHorizontal className="h-3 w-3 sm:h-4 sm:w-4" />
            <span className="hidden sm:inline">Activity Log</span>
            <span className="sm:hidden">Activity</span>
          </span>
        </TabsTrigger>
      </TabsList>

      <TabsContent value="overview" className="space-y-4">
        <BacktestProgress agentData={agentData} />
        {outputData && <BacktestResults outputData={outputData} />}
        <BacktestPerformanceMetrics agentData={agentData} />
      </TabsContent>

      <TabsContent value="metrics" className="space-y-4">
        <AdvancedPerformanceMetrics />
      </TabsContent>

      <TabsContent value="trades" className="space-y-4">
        <TradeHistoryViewer />
      </TabsContent>

      <TabsContent value="charts" className="space-y-4">
        <InteractiveCharts />
      </TabsContent>

      <TabsContent value="activity" className="space-y-4">
        <BacktestTradingTable agentData={agentData} />
      </TabsContent>
    </Tabs>
  );
}
