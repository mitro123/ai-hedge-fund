import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { 
  Play, 
  Pause, 
  Trash2, 
  Eye, 
  RefreshCw, 
  Plus, 
  Search, 
  Filter,
  Calendar,
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { useBacktestContext } from '@/contexts/backtest-context';
import { BacktestListItem, BacktestStatus } from '@/services/types';
// Simplified date formatting without date-fns dependency
function formatTimeAgo(date: string): string {
  const now = new Date();
  const past = new Date(date);
  const diffMs = now.getTime() - past.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 60) {
    return `před ${diffMins} minutami`;
  } else if (diffHours < 24) {
    return `před ${diffHours} hodinami`;
  } else {
    return `před ${diffDays} dny`;
  }
}

interface BacktestManagerProps {
  onSelectBacktest?: (backtestId: string) => void;
  onCreateBacktest?: () => void;
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'COMPLETE':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'IN_PROGRESS':
      return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
    case 'PENDING':
      return <Clock className="h-4 w-4 text-yellow-500" />;
    case 'ERROR':
      return <XCircle className="h-4 w-4 text-red-500" />;
    default:
      return <AlertCircle className="h-4 w-4 text-gray-500" />;
  }
}

function getStatusBadgeVariant(status: string): "secondary" | "destructive" | "outline" {
  switch (status) {
    case 'COMPLETE':
      return 'secondary';
    case 'IN_PROGRESS':
      return 'secondary';
    case 'PENDING':
      return 'outline';
    case 'ERROR':
      return 'destructive';
    default:
      return 'outline';
  }
}

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A';
  return new Intl.NumberFormat('cs-CZ', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A';
  const formatted = value.toFixed(2);
  return `${value >= 0 ? '+' : ''}${formatted}%`;
}

export function BacktestManager({ onSelectBacktest, onCreateBacktest }: BacktestManagerProps) {
  const {
    backtestList,
    loadingList,
    listError,
    fetchBacktestList,
    deleteBacktest,
    setSelectedBacktestId
  } = useBacktestContext();

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedBacktest, setSelectedBacktest] = useState<BacktestListItem | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Load backtest list on mount
  useEffect(() => {
    fetchBacktestList();
  }, [fetchBacktestList]);

  // Filter backtests based on search and status
  const filteredBacktests = backtestList.filter(backtest => {
    const matchesSearch = backtest.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         backtest.tickers.some(ticker => ticker.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || backtest.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Sort backtests by creation date (newest first)
  const sortedBacktests = [...filteredBacktests].sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const handleViewBacktest = (backtest: BacktestListItem) => {
    setSelectedBacktest(backtest);
    setShowDetails(true);
  };

  const handleSelectBacktest = (backtest: BacktestListItem) => {
    setSelectedBacktestId(backtest.id);
    if (onSelectBacktest) {
      onSelectBacktest(backtest.id);
    }
  };

  const handleDeleteBacktest = async (id: string) => {
    setDeletingId(id);
    try {
      await deleteBacktest(id);
    } catch (error) {
      console.error('Error deleting backtest:', error);
    } finally {
      setDeletingId(null);
    }
  };

  const handleRefresh = () => {
    fetchBacktestList();
  };

  // Statistics
  const stats = {
    total: backtestList.length,
    completed: backtestList.filter(bt => bt.status === 'COMPLETE').length,
    inProgress: backtestList.filter(bt => bt.status === 'IN_PROGRESS').length,
    failed: backtestList.filter(bt => bt.status === 'ERROR').length,
    avgReturn: backtestList
      .filter(bt => bt.total_return !== null && bt.total_return !== undefined)
      .reduce((sum, bt) => sum + (bt.total_return || 0), 0) / 
      Math.max(1, backtestList.filter(bt => bt.total_return !== null).length)
  };

  return (
    <div className="space-y-6">
      {/* Header with stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="h-4 w-4 text-blue-500" />
              <div>
                <p className="text-xs text-muted-foreground">Celkem</p>
                <p className="text-lg font-semibold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-xs text-muted-foreground">Dokončené</p>
                <p className="text-lg font-semibold">{stats.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-yellow-500" />
              <div>
                <p className="text-xs text-muted-foreground">Probíhající</p>
                <p className="text-lg font-semibold">{stats.inProgress}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <XCircle className="h-4 w-4 text-red-500" />
              <div>
                <p className="text-xs text-muted-foreground">Chybné</p>
                <p className="text-lg font-semibold">{stats.failed}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              {stats.avgReturn >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <div>
                <p className="text-xs text-muted-foreground">Průměrný výnos</p>
                <p className={cn(
                  "text-lg font-semibold",
                  stats.avgReturn >= 0 ? "text-green-500" : "text-red-500"
                )}>
                  {formatPercentage(stats.avgReturn)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Správa backtestů</CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={loadingList}
              >
                <RefreshCw className={cn("h-4 w-4", loadingList && "animate-spin")} />
                Obnovit
              </Button>
              {onCreateBacktest && (
                <Button
                  size="sm"
                  onClick={onCreateBacktest}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Nový backtest
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4 mb-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Hledat podle názvu nebo tickeru..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="w-full sm:w-48">
              <select 
                value={statusFilter} 
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm"
              >
                <option value="all">Všechny stavy</option>
                <option value="COMPLETE">Dokončené</option>
                <option value="IN_PROGRESS">Probíhající</option>
                <option value="PENDING">Čekající</option>
                <option value="ERROR">Chybné</option>
              </select>
            </div>
          </div>

          {/* Error state */}
          {listError && (
            <div className="text-center py-8">
              <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <p className="text-red-500 mb-2">Chyba při načítání backtestů</p>
              <p className="text-sm text-muted-foreground mb-4">{listError}</p>
              <Button variant="outline" onClick={handleRefresh}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Zkusit znovu
              </Button>
            </div>
          )}

          {/* Loading state */}
          {loadingList && !listError && (
            <div className="text-center py-8">
              <RefreshCw className="h-12 w-12 text-blue-500 mx-auto mb-4 animate-spin" />
              <p className="text-muted-foreground">Načítání backtestů...</p>
            </div>
          )}

          {/* Empty state */}
          {!loadingList && !listError && sortedBacktests.length === 0 && (
            <div className="text-center py-8">
              <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-2">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Žádné backtesty neodpovídají filtrům'
                  : 'Zatím žádné backtesty'
                }
              </p>
              {!searchTerm && statusFilter === 'all' && onCreateBacktest && (
                <Button variant="outline" onClick={onCreateBacktest}>
                  <Plus className="h-4 w-4 mr-2" />
                  Vytvořit první backtest
                </Button>
              )}
            </div>
          )}

          {/* Backtest table */}
          {!loadingList && !listError && sortedBacktests.length > 0 && (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Název</TableHead>
                    <TableHead>Stav</TableHead>
                    <TableHead>Tickery</TableHead>
                    <TableHead>Konečná hodnota</TableHead>
                    <TableHead>Celkový výnos</TableHead>
                    <TableHead>Vytvořeno</TableHead>
                    <TableHead className="text-right">Akce</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedBacktests.map((backtest) => (
                    <TableRow key={backtest.id}>
                      <TableCell className="font-medium">
                        <div>
                          <p className="font-medium">{backtest.name}</p>
                          <p className="text-xs text-muted-foreground">ID: {backtest.id.slice(0, 8)}...</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(backtest.status)} className="flex items-center gap-1 w-fit">
                          {getStatusIcon(backtest.status)}
                          {backtest.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {backtest.tickers.slice(0, 3).map((ticker) => (
                            <Badge key={ticker} variant="outline" className="text-xs">
                              {ticker}
                            </Badge>
                          ))}
                          {backtest.tickers.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{backtest.tickers.length - 3}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {formatCurrency(backtest.final_value)}
                      </TableCell>
                      <TableCell>
                        <span className={cn(
                          "font-medium",
                          backtest.total_return !== null && backtest.total_return !== undefined
                            ? backtest.total_return >= 0 ? "text-green-500" : "text-red-500"
                            : "text-muted-foreground"
                        )}>
                          {formatPercentage(backtest.total_return)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <p>{formatTimeAgo(backtest.created_at)}</p>
                          {backtest.completed_at && (
                            <p className="text-xs text-muted-foreground">
                              Dokončeno {formatTimeAgo(backtest.completed_at)}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewBacktest(backtest)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {backtest.status === 'COMPLETE' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleSelectBacktest(backtest)}
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            disabled={deletingId === backtest.id}
                            onClick={() => {
                              if (window.confirm(`Opravdu chcete smazat backtest "${backtest.name}"? Tato akce je nevratná.`)) {
                                handleDeleteBacktest(backtest.id);
                              }
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Backtest details dialog */}
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Detail backtestingu</DialogTitle>
            <DialogDescription>
              Podrobné informace o backtestingu
            </DialogDescription>
          </DialogHeader>
          
          {selectedBacktest && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Název</label>
                  <p className="text-sm text-muted-foreground">{selectedBacktest.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">Stav</label>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={getStatusBadgeVariant(selectedBacktest.status)} className="flex items-center gap-1">
                      {getStatusIcon(selectedBacktest.status)}
                      {selectedBacktest.status}
                    </Badge>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">ID</label>
                  <p className="text-sm text-muted-foreground font-mono">{selectedBacktest.id}</p>
                </div>
                <div>
                  <label className="text-sm font-medium">Vytvořeno</label>
                  <p className="text-sm text-muted-foreground">
                    {new Date(selectedBacktest.created_at).toLocaleString('cs-CZ')}
                  </p>
                </div>
                {selectedBacktest.completed_at && (
                  <div>
                    <label className="text-sm font-medium">Dokončeno</label>
                    <p className="text-sm text-muted-foreground">
                      {new Date(selectedBacktest.completed_at).toLocaleString('cs-CZ')}
                    </p>
                  </div>
                )}
              </div>

              <div>
                <label className="text-sm font-medium">Tickery</label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {selectedBacktest.tickers.map((ticker) => (
                    <Badge key={ticker} variant="outline">
                      {ticker}
                    </Badge>
                  ))}
                </div>
              </div>

              {selectedBacktest.status === 'COMPLETE' && (
                <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                  <div>
                    <label className="text-sm font-medium">Konečná hodnota</label>
                    <p className="text-lg font-semibold">
                      {formatCurrency(selectedBacktest.final_value)}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Celkový výnos</label>
                    <p className={cn(
                      "text-lg font-semibold",
                      selectedBacktest.total_return !== null && selectedBacktest.total_return !== undefined
                        ? selectedBacktest.total_return >= 0 ? "text-green-500" : "text-red-500"
                        : "text-muted-foreground"
                    )}>
                      {formatPercentage(selectedBacktest.total_return)}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetails(false)}>
              Zavřít
            </Button>
            {selectedBacktest?.status === 'COMPLETE' && (
              <Button onClick={() => {
                handleSelectBacktest(selectedBacktest);
                setShowDetails(false);
              }}>
                <Play className="h-4 w-4 mr-2" />
                Zobrazit výsledky
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
