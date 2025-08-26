import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Activity, Target, Shield, BarChart3, AlertTriangle } from 'lucide-react';
import { useBacktestContext } from '@/contexts/backtest-context';
import { BacktestPerformanceMetrics } from '@/services/types';

interface AdvancedPerformanceMetricsProps {
  className?: string;
}

interface MetricCardProps {
  title: string;
  value: number | undefined;
  format: 'percentage' | 'ratio' | 'currency' | 'number';
  icon: React.ReactNode;
  description?: string;
  colorScheme?: 'default' | 'success' | 'warning' | 'danger';
  benchmark?: number;
}

function MetricCard({ 
  title, 
  value, 
  format, 
  icon, 
  description, 
  colorScheme = 'default',
  benchmark 
}: MetricCardProps) {
  const formatValue = (val: number | undefined) => {
    if (val === undefined || val === null) return 'N/A';
    
    switch (format) {
      case 'percentage':
        return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`;
      case 'ratio':
        return val === Infinity ? '∞' : val.toFixed(2);
      case 'currency':
        return `$${val.toLocaleString()}`;
      case 'number':
        return val.toLocaleString();
      default:
        return val.toString();
    }
  };

  const getValueColor = () => {
    if (value === undefined || value === null) return 'text-muted-foreground';
    
    switch (colorScheme) {
      case 'success':
        return value > 0 ? 'text-green-500' : 'text-red-500';
      case 'warning':
        return value > 0 ? 'text-yellow-500' : 'text-red-500';
      case 'danger':
        return value < 0 ? 'text-red-500' : 'text-green-500';
      default:
        return 'text-foreground';
    }
  };

  const getBenchmarkComparison = () => {
    if (!benchmark || value === undefined || value === null) return null;
    
    const diff = value - benchmark;
    const isPositive = diff > 0;
    
    return (
      <div className={cn("text-xs flex items-center gap-1", 
        isPositive ? "text-green-500" : "text-red-500"
      )}>
        {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
        {isPositive ? '+' : ''}{diff.toFixed(2)} vs benchmark
      </div>
    );
  };

  return (
    <Card className="bg-transparent">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-muted">
              {icon}
            </div>
            <div>
              <h4 className="font-medium text-sm">{title}</h4>
              {description && (
                <p className="text-xs text-muted-foreground">{description}</p>
              )}
            </div>
          </div>
        </div>
        <div className="mt-3">
          <div className={cn("text-2xl font-bold", getValueColor())}>
            {formatValue(value)}
          </div>
          {getBenchmarkComparison()}
        </div>
      </CardContent>
    </Card>
  );
}

export function AdvancedPerformanceMetrics({ className }: AdvancedPerformanceMetricsProps) {
  const { backtest, loading, error } = useBacktestContext();
  
  // Extract metrics from context
  const metrics = backtest?.performance_metrics || {};

  // Show loading state
  if (loading) {
    return (
      <Card className={cn("bg-transparent", className)}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Advanced Performance Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-4 opacity-50 animate-pulse" />
            <p>Načítání pokročilých metrik...</p>
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
            <Activity className="h-5 w-5" />
            Advanced Performance Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-red-500" />
            <p>Chyba při načítání metrik</p>
            <p className="text-sm">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show empty state if no metrics
  if (!backtest || !metrics) {
    return (
      <Card className={cn("bg-transparent", className)}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Advanced Performance Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Žádné metriky nejsou k dispozici</p>
            <p className="text-sm">Metriky se zobrazí po dokončení backtestingu</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  const returnMetrics = [
    {
      title: 'Total Return',
      value: metrics.total_return,
      format: 'percentage' as const,
      icon: <TrendingUp className="h-4 w-4" />,
      description: 'Overall portfolio performance',
      colorScheme: 'success' as const,
      benchmark: 10 // 10% benchmark
    },
    {
      title: 'Best Day',
      value: metrics.best_day,
      format: 'percentage' as const,
      icon: <TrendingUp className="h-4 w-4 text-green-500" />,
      description: 'Highest single-day return',
      colorScheme: 'success' as const
    },
    {
      title: 'Worst Day',
      value: metrics.worst_day,
      format: 'percentage' as const,
      icon: <TrendingDown className="h-4 w-4 text-red-500" />,
      description: 'Lowest single-day return',
      colorScheme: 'danger' as const
    },
    {
      title: 'Win Rate',
      value: metrics.win_rate,
      format: 'percentage' as const,
      icon: <Target className="h-4 w-4" />,
      description: 'Percentage of profitable days',
      colorScheme: 'success' as const,
      benchmark: 50 // 50% benchmark
    }
  ];

  const riskMetrics = [
    {
      title: 'Volatility',
      value: metrics.volatility,
      format: 'percentage' as const,
      icon: <Activity className="h-4 w-4" />,
      description: 'Annualized volatility',
      colorScheme: 'warning' as const
    },
    {
      title: 'Maximum Drawdown',
      value: metrics.max_drawdown ? Math.abs(metrics.max_drawdown) : undefined,
      format: 'percentage' as const,
      icon: <AlertTriangle className="h-4 w-4 text-red-500" />,
      description: 'Largest peak-to-trough decline',
      colorScheme: 'danger' as const
    },
    {
      title: 'VaR (95%)',
      value: metrics.var_95 ? Math.abs(metrics.var_95) : undefined,
      format: 'percentage' as const,
      icon: <Shield className="h-4 w-4" />,
      description: 'Value at Risk (95% confidence)',
      colorScheme: 'warning' as const
    },
    {
      title: 'Expected Shortfall',
      value: metrics.expected_shortfall_95 ? Math.abs(metrics.expected_shortfall_95) : undefined,
      format: 'percentage' as const,
      icon: <AlertTriangle className="h-4 w-4" />,
      description: 'Average loss beyond VaR',
      colorScheme: 'danger' as const
    }
  ];

  const ratioMetrics = [
    {
      title: 'Sharpe Ratio',
      value: metrics.sharpe_ratio,
      format: 'ratio' as const,
      icon: <TrendingUp className="h-4 w-4" />,
      description: 'Risk-adjusted return',
      colorScheme: 'success' as const,
      benchmark: 1.0 // 1.0 benchmark for good Sharpe
    },
    {
      title: 'Sortino Ratio',
      value: metrics.sortino_ratio,
      format: 'ratio' as const,
      icon: <TrendingUp className="h-4 w-4" />,
      description: 'Downside risk-adjusted return',
      colorScheme: 'success' as const,
      benchmark: 1.0
    },
    {
      title: 'Calmar Ratio',
      value: metrics.calmar_ratio,
      format: 'ratio' as const,
      icon: <Shield className="h-4 w-4" />,
      description: 'Return vs max drawdown',
      colorScheme: 'success' as const,
      benchmark: 0.5
    },
    {
      title: 'Win/Loss Ratio',
      value: metrics.win_loss_ratio,
      format: 'ratio' as const,
      icon: <Target className="h-4 w-4" />,
      description: 'Average win vs average loss',
      colorScheme: 'success' as const,
      benchmark: 1.0
    }
  ];

  const tradingMetrics = [
    {
      title: 'Max Consecutive Wins',
      value: metrics.max_consecutive_wins,
      format: 'number' as const,
      icon: <TrendingUp className="h-4 w-4 text-green-500" />,
      description: 'Longest winning streak',
      colorScheme: 'success' as const
    },
    {
      title: 'Max Consecutive Losses',
      value: metrics.max_consecutive_losses,
      format: 'number' as const,
      icon: <TrendingDown className="h-4 w-4 text-red-500" />,
      description: 'Longest losing streak',
      colorScheme: 'danger' as const
    },
    {
      title: 'Long/Short Ratio',
      value: metrics.long_short_ratio,
      format: 'ratio' as const,
      icon: <Activity className="h-4 w-4" />,
      description: 'Portfolio exposure balance',
      colorScheme: 'default' as const
    }
  ];

  const getOverallRating = () => {
    let score = 0;
    let maxScore = 0;

    // Sharpe ratio (0-3 points)
    if (metrics.sharpe_ratio !== undefined) {
      maxScore += 3;
      if (metrics.sharpe_ratio > 2) score += 3;
      else if (metrics.sharpe_ratio > 1) score += 2;
      else if (metrics.sharpe_ratio > 0) score += 1;
    }

    // Total return (0-3 points)
    if (metrics.total_return !== undefined) {
      maxScore += 3;
      if (metrics.total_return > 20) score += 3;
      else if (metrics.total_return > 10) score += 2;
      else if (metrics.total_return > 0) score += 1;
    }

    // Max drawdown (0-2 points)
    if (metrics.max_drawdown !== undefined) {
      maxScore += 2;
      const absDrawdown = Math.abs(metrics.max_drawdown);
      if (absDrawdown < 5) score += 2;
      else if (absDrawdown < 15) score += 1;
    }

    // Win rate (0-2 points)
    if (metrics.win_rate !== undefined) {
      maxScore += 2;
      if (metrics.win_rate > 60) score += 2;
      else if (metrics.win_rate > 50) score += 1;
    }

    const percentage = maxScore > 0 ? (score / maxScore) * 100 : 0;
    
    if (percentage >= 80) return { rating: 'Excellent', color: 'text-green-500', badge: 'success' };
    if (percentage >= 60) return { rating: 'Good', color: 'text-blue-500', badge: 'default' };
    if (percentage >= 40) return { rating: 'Fair', color: 'text-yellow-500', badge: 'warning' };
    return { rating: 'Poor', color: 'text-red-500', badge: 'destructive' };
  };

  const overallRating = getOverallRating();

  return (
    <div className={cn("space-y-6", className)}>
      {/* Overall Rating */}
      <Card className="bg-transparent">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Performance Rating</CardTitle>
            <Badge variant={overallRating.badge as any} className="text-sm">
              {overallRating.rating}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className={cn("text-2xl font-bold", overallRating.color)}>
            {overallRating.rating}
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Based on risk-adjusted returns, drawdown control, and consistency
          </p>
        </CardContent>
      </Card>

      {/* Return Metrics */}
      <div>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Return Metrics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {returnMetrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>
      </div>

      {/* Risk Metrics */}
      <div>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Risk Metrics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {riskMetrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>
      </div>

      {/* Risk-Adjusted Ratios */}
      <div>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Risk-Adjusted Ratios
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {ratioMetrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>
      </div>

      {/* Trading Metrics */}
      <div>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Target className="h-5 w-5" />
          Trading Metrics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tradingMetrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>
      </div>

      {/* Additional Info */}
      {metrics.max_drawdown_date && (
        <Card className="bg-transparent">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <AlertTriangle className="h-4 w-4" />
              Maximum drawdown occurred on {metrics.max_drawdown_date}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
