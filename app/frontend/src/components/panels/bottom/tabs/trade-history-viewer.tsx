import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { 
  TrendingUp, 
  TrendingDown, 
  Search, 
  Filter, 
  Download,
  Calendar,
  DollarSign,
  Activity,
  AlertTriangle
} from 'lucide-react';
import { TradeHistoryItem } from '@/services/types';
import { useState, useMemo } from 'react';
import { useBacktestContext } from '@/contexts/backtest-context';

interface TradeHistoryViewerProps {
  className?: string;
}

interface TradeStats {
  totalTrades: number;
  buyTrades: number;
  sellTrades: number;
  shortTrades: number;
  coverTrades: number;
  totalVolume: number;
  averageTradeSize: number;
  uniqueTickers: number;
}

function getActionIcon(action: string) {
  switch (action.toLowerCase()) {
    case 'buy':
      return <TrendingUp className="h-4 w-4 text-green-500" />;
    case 'sell':
      return <TrendingDown className="h-4 w-4 text-red-500" />;
    case 'short':
      return <TrendingDown className="h-4 w-4 text-orange-500" />;
    case 'cover':
      return <TrendingUp className="h-4 w-4 text-blue-500" />;
    default:
      return <Activity className="h-4 w-4 text-gray-500" />;
  }
}

function getActionColor(action: string) {
  switch (action.toLowerCase()) {
    case 'buy':
      return 'text-green-500';
    case 'sell':
      return 'text-red-500';
    case 'short':
      return 'text-orange-500';
    case 'cover':
      return 'text-blue-500';
    default:
      return 'text-gray-500';
  }
}

function getActionBadgeVariant(action: string): "secondary" | "destructive" | "outline" | "warning" | "success" {
  switch (action.toLowerCase()) {
    case 'buy':
      return 'success';
    case 'sell':
      return 'destructive';
    case 'short':
      return 'warning';
    case 'cover':
      return 'secondary';
    default:
      return 'outline';
  }
}

export function TradeHistoryViewer({ className }: TradeHistoryViewerProps) {
  const { backtest, loading, error } = useBacktestContext();
  
  // Extract trades from context
  const trades = backtest?.trade_history || [];
  
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [tickerFilter, setTickerFilter] = useState<string>('all');

  // Show loading state
  if (loading) {
    return (
      <Card className={cn("bg-transparent", className)}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Trade History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-4 opacity-50 animate-pulse" />
            <p>Načítání historie obchodů...</p>
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
            Trade History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-red-500" />
            <p>Chyba při načítání historie obchodů</p>
            <p className="text-sm">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate trade statistics
  const tradeStats: TradeStats = useMemo(() => {
    const stats = {
      totalTrades: trades.length,
      buyTrades: trades.filter(t => t.action.toLowerCase() === 'buy').length,
      sellTrades: trades.filter(t => t.action.toLowerCase() === 'sell').length,
      shortTrades: trades.filter(t => t.action.toLowerCase() === 'short').length,
      coverTrades: trades.filter(t => t.action.toLowerCase() === 'cover').length,
      totalVolume: trades.reduce((sum, t) => sum + (t.quantity * t.price), 0),
      averageTradeSize: 0,
      uniqueTickers: new Set(trades.map(t => t.ticker)).size
    };
    
    stats.averageTradeSize = stats.totalTrades > 0 ? stats.totalVolume / stats.totalTrades : 0;
    
    return stats;
  }, [trades]);

  // Get unique tickers for filter
  const uniqueTickers = useMemo(() => {
    return Array.from(new Set(trades.map(t => t.ticker))).sort();
  }, [trades]);

  // Filter trades based on search and filters
  const filteredTrades = useMemo(() => {
    return trades.filter(trade => {
      const matchesSearch = searchTerm === '' || 
        trade.ticker.toLowerCase().includes(searchTerm.toLowerCase()) ||
        trade.date.includes(searchTerm);
      
      const matchesAction = actionFilter === 'all' || trade.action.toLowerCase() === actionFilter.toLowerCase();
      const matchesTicker = tickerFilter === 'all' || trade.ticker === tickerFilter;
      
      return matchesSearch && matchesAction && matchesTicker;
    });
  }, [trades, searchTerm, actionFilter, tickerFilter]);

  // Sort trades by date (newest first)
  const sortedTrades = useMemo(() => {
    return [...filteredTrades].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [filteredTrades]);

  const exportTrades = () => {
    const csvContent = [
      ['Date', 'Ticker', 'Action', 'Quantity', 'Price', 'Total Value'].join(','),
      ...sortedTrades.map(trade => [
        trade.date,
        trade.ticker,
        trade.action,
        trade.quantity,
        trade.price.toFixed(2),
        (trade.quantity * trade.price).toFixed(2)
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trade-history-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (trades.length === 0) {
    return (
      <Card className={cn("bg-transparent", className)}>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Trade History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No trades executed yet</p>
            <p className="text-sm">Trade history will appear here once the backtest runs</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Trade Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card className="bg-transparent">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-500" />
              <div>
                <div className="text-2xl font-bold">{tradeStats.totalTrades}</div>
                <div className="text-xs text-muted-foreground">Total Trades</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-transparent">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <div>
                <div className="text-2xl font-bold">{tradeStats.buyTrades}</div>
                <div className="text-xs text-muted-foreground">Buy Orders</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-transparent">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-red-500" />
              <div>
                <div className="text-2xl font-bold">{tradeStats.sellTrades}</div>
                <div className="text-xs text-muted-foreground">Sell Orders</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-transparent">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-yellow-500" />
              <div>
                <div className="text-2xl font-bold">${tradeStats.totalVolume.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                <div className="text-xs text-muted-foreground">Total Volume</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-transparent">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-purple-500" />
              <div>
                <div className="text-2xl font-bold">${tradeStats.averageTradeSize.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                <div className="text-xs text-muted-foreground">Avg Trade Size</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-transparent">
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-cyan-500" />
              <div>
                <div className="text-2xl font-bold">{tradeStats.uniqueTickers}</div>
                <div className="text-xs text-muted-foreground">Unique Tickers</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <Card className="bg-transparent">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Trade History ({filteredTrades.length} trades)
            </CardTitle>
            <Button onClick={exportTrades} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by ticker or date..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Action Filter */}
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="px-3 py-2 border border-input bg-background rounded-md text-sm"
            >
              <option value="all">All Actions</option>
              <option value="BUY">Buy</option>
              <option value="SELL">Sell</option>
              <option value="SHORT">Short</option>
              <option value="COVER">Cover</option>
            </select>

            {/* Ticker Filter */}
            <select
              value={tickerFilter}
              onChange={(e) => setTickerFilter(e.target.value)}
              className="px-3 py-2 border border-input bg-background rounded-md text-sm"
            >
              <option value="all">All Tickers</option>
              {uniqueTickers.map(ticker => (
                <option key={ticker} value={ticker}>{ticker}</option>
              ))}
            </select>
          </div>

          {/* Trade Table */}
          <div className="max-h-96 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Ticker</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead className="text-right">Quantity</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead className="text-right">Total Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedTrades.map((trade, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">
                      {new Date(trade.date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono">
                        {trade.ticker}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getActionIcon(trade.action)}
                        <Badge variant={getActionBadgeVariant(trade.action)}>
                          {trade.action}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {trade.quantity.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      ${trade.price.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right font-mono font-medium">
                      ${(trade.quantity * trade.price).toLocaleString(undefined, { 
                        minimumFractionDigits: 2, 
                        maximumFractionDigits: 2 
                      })}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {filteredTrades.length === 0 && trades.length > 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No trades match your filters</p>
              <p className="text-sm">Try adjusting your search criteria</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
