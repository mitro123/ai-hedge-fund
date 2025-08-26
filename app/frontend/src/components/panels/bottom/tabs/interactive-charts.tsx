import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { 
  BarChart3, 
  LineChart, 
  PieChart, 
  TrendingUp,
  TrendingDown,
  Activity,
  Download,
  Maximize2,
  Settings,
  AlertTriangle
} from 'lucide-react';
import { TradeHistoryItem, BacktestPerformanceMetrics } from '@/services/types';
import { useState } from 'react';
import { useBacktestContext } from '@/contexts/backtest-context';

interface InteractiveChartsProps {
  className?: string;
}

interface ChartConfig {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  type: 'line' | 'bar' | 'scatter' | 'heatmap';
  enabled: boolean;
}

export function InteractiveCharts({ 
  className 
}: InteractiveChartsProps) {
  const { backtest, loading, error } = useBacktestContext();
  
  // Extract data from context
  const trades = backtest?.trade_history || [];
  const portfolioValues = backtest?.chart_data?.portfolio_value || [];
  const metrics = backtest?.performance_metrics;

  // Show loading state
  if (loading) {
    return (
      <Card className={cn("bg-transparent", className)}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Interactive Charts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50 animate-pulse" />
            <p>Načítání dat pro grafy...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show error state
  if (error) {
    return (
      <Card className={cn("bg-transparent", className)}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Interactive Charts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-red-500" />
            <p>Chyba při načítání dat</p>
            <p className="text-sm">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  const [selectedCharts, setSelectedCharts] = useState<string[]>([
    'portfolio-value',
    'daily-returns',
    'drawdown',
    'trade-markers'
  ]);

  const availableCharts: ChartConfig[] = [
    {
      id: 'portfolio-value',
      title: 'Hodnota Portfolia v Čase',
      description: 'Sledování výkonnosti portfolia s obchodními markery',
      icon: <LineChart className="h-4 w-4" />,
      type: 'line',
      enabled: true
    },
    {
      id: 'daily-returns',
      title: 'Distribuce Denních Výnosů',
      description: 'Histogram denních výnosů v procentech',
      icon: <BarChart3 className="h-4 w-4" />,
      type: 'bar',
      enabled: true
    },
    {
      id: 'drawdown',
      title: 'Graf Poklesů (Underwater)',
      description: 'Periody poklesů a obnovy portfolia',
      icon: <TrendingDown className="h-4 w-4" />,
      type: 'line',
      enabled: true
    },
    {
      id: 'trade-markers',
      title: 'Cenový Graf s Obchody',
      description: 'Ceny akcií s markery nákupů a prodejů',
      icon: <Activity className="h-4 w-4" />,
      type: 'scatter',
      enabled: true
    },
    {
      id: 'rolling-sharpe',
      title: 'Klouzavý Sharpe Poměr',
      description: '30-denní klouzavé rizikově upravené výnosy',
      icon: <TrendingUp className="h-4 w-4" />,
      type: 'line',
      enabled: false
    },
    {
      id: 'monthly-heatmap',
      title: 'Měsíční Heatmapa Výnosů',
      description: 'Kalendářní pohled na měsíční výkonnost',
      icon: <PieChart className="h-4 w-4" />,
      type: 'heatmap',
      enabled: false
    }
  ];

  const toggleChart = (chartId: string) => {
    setSelectedCharts(prev => 
      prev.includes(chartId) 
        ? prev.filter(id => id !== chartId)
        : [...prev, chartId]
    );
  };

  const exportCharts = () => {
    // Placeholder for chart export functionality
    console.log('Exporting charts...', selectedCharts);
    // In real implementation, this would generate and download chart images
  };

  // Chart components with basic visualizations
  const PortfolioValueChart = () => {
    const maxValue = Math.max(...portfolioValues.map(p => p.value));
    const minValue = Math.min(...portfolioValues.map(p => p.value));
    const range = maxValue - minValue;
    
    return (
      <Card className="bg-transparent">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Hodnota Portfolia v Čase</CardTitle>
              <p className="text-sm text-muted-foreground">Sledování výkonnosti portfolia s obchodními markery</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm">
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-muted/10 rounded-lg p-4 relative overflow-hidden">
            <div className="absolute inset-4">
              {/* Y-axis labels */}
              <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-muted-foreground">
                <span>${maxValue.toLocaleString()}</span>
                <span>${((maxValue + minValue) / 2).toLocaleString()}</span>
                <span>${minValue.toLocaleString()}</span>
              </div>
              
              {/* Chart area */}
              <div className="ml-16 mr-4 h-full relative">
                <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                  {/* Grid lines */}
                  <defs>
                    <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                      <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeWidth="0.1" opacity="0.3"/>
                    </pattern>
                  </defs>
                  <rect width="100" height="100" fill="url(#grid)" />
                  
                  {/* Portfolio value line */}
                  <polyline
                    fill="none"
                    stroke="rgb(34, 197, 94)"
                    strokeWidth="0.5"
                    points={portfolioValues.map((point, index) => {
                      const x = (index / (portfolioValues.length - 1)) * 100;
                      const y = 100 - ((point.value - minValue) / range) * 100;
                      return `${x},${y}`;
                    }).join(' ')}
                  />
                  
                  {/* Trade markers */}
                  {trades.map((trade, index) => {
                    const portfolioIndex = portfolioValues.findIndex(p => p.date === trade.date);
                    if (portfolioIndex === -1) return null;
                    
                    const x = (portfolioIndex / (portfolioValues.length - 1)) * 100;
                    const y = 100 - ((portfolioValues[portfolioIndex].value - minValue) / range) * 100;
                    
                    return (
                      <circle
                        key={index}
                        cx={x}
                        cy={y}
                        r="1"
                        fill={trade.action === 'buy' || trade.action === 'cover' ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'}
                        stroke="white"
                        strokeWidth="0.2"
                      />
                    );
                  })}
                </svg>
                
                {/* X-axis labels */}
                <div className="absolute -bottom-6 left-0 right-0 flex justify-between text-xs text-muted-foreground">
                  <span>{portfolioValues[0]?.date}</span>
                  <span>{portfolioValues[portfolioValues.length - 1]?.date}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const DailyReturnsChart = () => {
    const dailyReturnsData = backtest?.chart_data?.daily_returns || [];
    const returns = dailyReturnsData.map(p => p.value || 0);
    const maxReturn = Math.max(...returns);
    const minReturn = Math.min(...returns);
    const range = maxReturn - minReturn;
    
    // Create histogram bins
    const bins = 10;
    const binSize = range / bins;
    const histogram = Array(bins).fill(0);
    
    returns.forEach(ret => {
      const binIndex = Math.min(Math.floor((ret - minReturn) / binSize), bins - 1);
      histogram[binIndex]++;
    });
    
    const maxCount = Math.max(...histogram);
    
    return (
      <Card className="bg-transparent">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Distribuce Denních Výnosů</CardTitle>
              <p className="text-sm text-muted-foreground">Histogram denních výnosů v procentech</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm">
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-muted/10 rounded-lg p-4 relative">
            <div className="absolute inset-4">
              {/* Y-axis labels */}
              <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-muted-foreground">
                <span>{maxCount}</span>
                <span>{Math.floor(maxCount / 2)}</span>
                <span>0</span>
              </div>
              
              {/* Chart area */}
              <div className="ml-12 mr-4 h-full flex items-end justify-between gap-1">
                {histogram.map((count, index) => (
                  <div
                    key={index}
                    className="bg-blue-500 rounded-t"
                    style={{
                      height: `${(count / maxCount) * 100}%`,
                      width: `${100 / bins - 2}%`
                    }}
                    title={`${(minReturn + index * binSize).toFixed(2)}% - ${(minReturn + (index + 1) * binSize).toFixed(2)}%: ${count} days`}
                  />
                ))}
              </div>
              
              {/* X-axis labels */}
              <div className="absolute -bottom-6 left-12 right-4 flex justify-between text-xs text-muted-foreground">
                <span>{minReturn.toFixed(1)}%</span>
                <span>0%</span>
                <span>{maxReturn.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const DrawdownChart = () => {
    let peak = portfolioValues[0]?.value || 0;
    const drawdowns = portfolioValues.map(point => {
      if (point.value > peak) peak = point.value;
      return ((point.value - peak) / peak) * 100;
    });
    
    const minDrawdown = Math.min(...drawdowns);
    
    return (
      <Card className="bg-transparent">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Graf Poklesů (Underwater)</CardTitle>
              <p className="text-sm text-muted-foreground">Periody poklesů a obnovy portfolia</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm">
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-muted/10 rounded-lg p-4 relative">
            <div className="absolute inset-4">
              {/* Y-axis labels */}
              <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-muted-foreground">
                <span>0%</span>
                <span>{(minDrawdown / 2).toFixed(1)}%</span>
                <span>{minDrawdown.toFixed(1)}%</span>
              </div>
              
              {/* Chart area */}
              <div className="ml-12 mr-4 h-full relative">
                <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                  {/* Zero line */}
                  <line x1="0" y1="0" x2="100" y2="0" stroke="currentColor" strokeWidth="0.2" opacity="0.5" />
                  
                  {/* Drawdown area */}
                  <polygon
                    fill="rgb(239, 68, 68)"
                    fillOpacity="0.3"
                    stroke="rgb(239, 68, 68)"
                    strokeWidth="0.5"
                    points={[
                      '0,0',
                      ...drawdowns.map((dd, index) => {
                        const x = (index / (drawdowns.length - 1)) * 100;
                        const y = Math.abs(dd / minDrawdown) * 100;
                        return `${x},${y}`;
                      }),
                      '100,0'
                    ].join(' ')}
                  />
                </svg>
                
                {/* X-axis labels */}
                <div className="absolute -bottom-6 left-0 right-0 flex justify-between text-xs text-muted-foreground">
                  <span>{portfolioValues[0]?.date}</span>
                  <span>{portfolioValues[portfolioValues.length - 1]?.date}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const TradeMarkersChart = () => {
    const tradesByTicker = trades.reduce((acc, trade) => {
      if (!acc[trade.ticker]) acc[trade.ticker] = [];
      acc[trade.ticker].push(trade);
      return acc;
    }, {} as Record<string, TradeHistoryItem[]>);
    
    return (
      <Card className="bg-transparent">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Cenový Graf s Obchody</CardTitle>
              <p className="text-sm text-muted-foreground">Ceny akcií s markery nákupů a prodejů</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm">
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-muted/10 rounded-lg p-4">
            <div className="grid grid-cols-1 gap-4 h-full">
              {Object.entries(tradesByTicker).slice(0, 3).map(([ticker, tickerTrades]) => {
                const prices = tickerTrades.map(t => t.price);
                const maxPrice = Math.max(...prices);
                const minPrice = Math.min(...prices);
                const range = maxPrice - minPrice;
                
                return (
                  <div key={ticker} className="relative">
                    <div className="text-sm font-medium mb-2">{ticker}</div>
                    <div className="h-16 relative">
                      <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                        {tickerTrades.map((trade, index) => {
                          const x = (index / (tickerTrades.length - 1)) * 100;
                          const y = 100 - ((trade.price - minPrice) / range) * 100;
                          
                          return (
                            <circle
                              key={index}
                              cx={x}
                              cy={y}
                              r="3"
                              fill={trade.action === 'buy' || trade.action === 'cover' ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)'}
                              stroke="white"
                              strokeWidth="1"
                            />
                          );
                        })}
                      </svg>
                      <div className="absolute right-0 top-0 text-xs text-muted-foreground">
                        ${maxPrice.toFixed(2)}
                      </div>
                      <div className="absolute right-0 bottom-0 text-xs text-muted-foreground">
                        ${minPrice.toFixed(2)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  const ChartPlaceholder = ({ 
    title, 
    description, 
    type 
  }: { 
    title: string; 
    description: string; 
    type: string; 
  }) => (
    <Card className="bg-transparent">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">{title}</CardTitle>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm">
              <Maximize2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-64 bg-muted/20 rounded-lg flex items-center justify-center border-2 border-dashed border-muted">
          <div className="text-center">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground font-medium">Interactive {type} Chart</p>
            <p className="text-sm text-muted-foreground mt-1">
              Plotly.js integration will render here
            </p>
            <Badge variant="outline" className="mt-2">
              {portfolioValues.length} data points
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (portfolioValues.length === 0) {
    return (
      <Card className={cn("bg-transparent", className)}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Interactive Charts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No data available for visualization</p>
            <p className="text-sm">Charts will appear here once the backtest runs</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Chart Controls */}
      <Card className="bg-transparent">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Dashboard Interaktivních Grafů
            </CardTitle>
            <div className="flex gap-2">
              <Button onClick={exportCharts} variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Exportovat Grafy
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-3">Available Charts</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {availableCharts.map(chart => (
                  <div
                    key={chart.id}
                    className={cn(
                      "p-3 border rounded-lg cursor-pointer transition-colors",
                      selectedCharts.includes(chart.id)
                        ? "border-primary bg-primary/5"
                        : "border-muted hover:border-muted-foreground/50"
                    )}
                    onClick={() => toggleChart(chart.id)}
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded bg-muted">
                        {chart.icon}
                      </div>
                      <div className="flex-1">
                        <h5 className="font-medium text-sm">{chart.title}</h5>
                        <p className="text-xs text-muted-foreground">{chart.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge 
                            variant={selectedCharts.includes(chart.id) ? "success" : "outline"}
                            className="text-xs"
                          >
                            {selectedCharts.includes(chart.id) ? "Enabled" : "Disabled"}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {chart.type}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Chart Statistics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
              <div className="text-center">
                <div className="text-2xl font-bold">{selectedCharts.length}</div>
                <div className="text-xs text-muted-foreground">Active Charts</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{portfolioValues.length}</div>
                <div className="text-xs text-muted-foreground">Data Points</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">{trades.length}</div>
                <div className="text-xs text-muted-foreground">Trade Markers</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">
                  {new Set(trades.map(t => t.ticker)).size}
                </div>
                <div className="text-xs text-muted-foreground">Unique Tickers</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Render Selected Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {selectedCharts.map(chartId => {
          const chart = availableCharts.find(c => c.id === chartId);
          if (!chart) return null;

          // Render actual chart components based on chartId
          switch (chartId) {
            case 'portfolio-value':
              return <PortfolioValueChart key={chartId} />;
            case 'daily-returns':
              return <DailyReturnsChart key={chartId} />;
            case 'drawdown':
              return <DrawdownChart key={chartId} />;
            case 'trade-markers':
              return <TradeMarkersChart key={chartId} />;
            default:
              return (
                <ChartPlaceholder
                  key={chartId}
                  title={chart.title}
                  description={chart.description}
                  type={chart.type}
                />
              );
          }
        })}
      </div>

      {selectedCharts.length === 0 && (
        <Card className="bg-transparent">
          <CardContent className="p-8">
            <div className="text-center text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No charts selected</p>
              <p className="text-sm">Select charts from the options above to display them</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Implementation Notes */}
      <Card className="bg-transparent border-dashed">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Implementation Notes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-500 mt-2"></div>
              <div>
                <strong>Plotly.js Integration:</strong> Charts will be rendered using Plotly.js for interactive visualizations
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500 mt-2"></div>
              <div>
                <strong>Real-time Updates:</strong> Charts will update automatically as backtest data streams in
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-yellow-500 mt-2"></div>
              <div>
                <strong>Export Functionality:</strong> Charts can be exported as PNG, SVG, or PDF formats
              </div>
            </div>
            <div className="flex items-start gap-2">
              <div className="w-2 h-2 rounded-full bg-purple-500 mt-2"></div>
              <div>
                <strong>Customization:</strong> Users can customize chart appearance, timeframes, and indicators
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
