import { useState, useEffect, useCallback } from 'react';
import { backtestApi } from '@/services/backtest-api';
import {
  BacktestAdvancedMetrics,
  BacktestChartsData,
  BacktestListItem,
  BacktestResults,
  BacktestStatus,
  TradeHistoryItem
} from '@/services/types';

interface UseBacktestDataOptions {
  backtestId?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseBacktestDataReturn {
  // Data
  backtest: BacktestResults | null;
  status: BacktestStatus | null;
  metrics: BacktestAdvancedMetrics | null;
  trades: TradeHistoryItem[];
  charts: BacktestChartsData | null;
  backtestList: BacktestListItem[];
  
  // Loading states
  loading: boolean;
  loadingMetrics: boolean;
  loadingTrades: boolean;
  loadingCharts: boolean;
  loadingList: boolean;
  
  // Error states
  error: string | null;
  metricsError: string | null;
  tradesError: string | null;
  chartsError: string | null;
  listError: string | null;
  
  // Actions
  fetchBacktest: (id: string) => Promise<void>;
  fetchStatus: (id: string) => Promise<void>;
  fetchMetrics: (id: string) => Promise<void>;
  fetchTrades: (id: string, options?: {
    ticker?: string;
    action?: 'buy' | 'sell' | 'short' | 'cover';
    limit?: number;
    offset?: number;
  }) => Promise<void>;
  fetchCharts: (id: string) => Promise<void>;
  fetchBacktestList: (limit?: number, offset?: number) => Promise<void>;
  deleteBacktest: (id: string) => Promise<void>;
  pollStatus: (id: string, onProgress?: (status: BacktestStatus) => void) => Promise<void>;
  
  // Utilities
  refresh: () => Promise<void>;
  clearData: () => void;
}

export function useBacktestData(options: UseBacktestDataOptions = {}): UseBacktestDataReturn {
  const { backtestId, autoRefresh = false, refreshInterval = 5000 } = options;
  
  // Data states
  const [backtest, setBacktest] = useState<BacktestResults | null>(null);
  const [status, setStatus] = useState<BacktestStatus | null>(null);
  const [metrics, setMetrics] = useState<BacktestAdvancedMetrics | null>(null);
  const [trades, setTrades] = useState<TradeHistoryItem[]>([]);
  const [charts, setCharts] = useState<BacktestChartsData | null>(null);
  const [backtestList, setBacktestList] = useState<BacktestListItem[]>([]);
  
  // Loading states
  const [loading, setLoading] = useState(false);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [loadingTrades, setLoadingTrades] = useState(false);
  const [loadingCharts, setLoadingCharts] = useState(false);
  const [loadingList, setLoadingList] = useState(false);
  
  // Error states
  const [error, setError] = useState<string | null>(null);
  const [metricsError, setMetricsError] = useState<string | null>(null);
  const [tradesError, setTradesError] = useState<string | null>(null);
  const [chartsError, setChartsError] = useState<string | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  
  // Fetch backtest results
  const fetchBacktest = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await backtestApi.getBacktestResults(id);
      setBacktest(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Chyba při načítání backtestingu';
      setError(errorMessage);
      console.error('Error fetching backtest:', err);
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Fetch backtest status
  const fetchStatus = useCallback(async (id: string) => {
    try {
      const result = await backtestApi.getBacktestStatus(id);
      setStatus(result);
    } catch (err) {
      console.error('Error fetching backtest status:', err);
    }
  }, []);
  
  // Fetch advanced metrics
  const fetchMetrics = useCallback(async (id: string) => {
    setLoadingMetrics(true);
    setMetricsError(null);
    
    try {
      const result = await backtestApi.getBacktestMetrics(id);
      setMetrics(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Chyba při načítání metrik';
      setMetricsError(errorMessage);
      console.error('Error fetching metrics:', err);
    } finally {
      setLoadingMetrics(false);
    }
  }, []);
  
  // Fetch trade history
  const fetchTrades = useCallback(async (
    id: string, 
    options: {
      ticker?: string;
      action?: 'buy' | 'sell' | 'short' | 'cover';
      limit?: number;
      offset?: number;
    } = {}
  ) => {
    setLoadingTrades(true);
    setTradesError(null);
    
    try {
      const result = await backtestApi.getBacktestTrades(id, options);
      setTrades(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Chyba při načítání obchodů';
      setTradesError(errorMessage);
      console.error('Error fetching trades:', err);
    } finally {
      setLoadingTrades(false);
    }
  }, []);
  
  // Fetch chart data
  const fetchCharts = useCallback(async (id: string) => {
    setLoadingCharts(true);
    setChartsError(null);
    
    try {
      const result = await backtestApi.getBacktestCharts(id);
      setCharts(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Chyba při načítání grafů';
      setChartsError(errorMessage);
      console.error('Error fetching charts:', err);
    } finally {
      setLoadingCharts(false);
    }
  }, []);
  
  // Fetch backtest list
  const fetchBacktestList = useCallback(async (limit: number = 50, offset: number = 0) => {
    setLoadingList(true);
    setListError(null);
    
    try {
      const result = await backtestApi.listBacktests(limit, offset);
      setBacktestList(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Chyba při načítání seznamu backtestů';
      setListError(errorMessage);
      console.error('Error fetching backtest list:', err);
    } finally {
      setLoadingList(false);
    }
  }, []);
  
  // Delete backtest
  const deleteBacktest = useCallback(async (id: string) => {
    try {
      await backtestApi.deleteBacktest(id);
      // Remove from list if it exists
      setBacktestList(prev => prev.filter(bt => bt.id !== id));
      // Clear current data if it's the deleted backtest
      if (backtest?.id === id) {
        clearData();
      }
    } catch (err) {
      console.error('Error deleting backtest:', err);
      throw err;
    }
  }, [backtest?.id]);
  
  // Poll status until completion
  const pollStatus = useCallback(async (
    id: string, 
    onProgress?: (status: BacktestStatus) => void
  ) => {
    try {
      await backtestApi.pollBacktestStatus(id, (status) => {
        setStatus(status);
        if (onProgress) {
          onProgress(status);
        }
      });
    } catch (err) {
      console.error('Error polling backtest status:', err);
      throw err;
    }
  }, []);
  
  // Refresh all data for current backtest
  const refresh = useCallback(async () => {
    if (!backtestId) return;
    
    await Promise.allSettled([
      fetchBacktest(backtestId),
      fetchStatus(backtestId),
      fetchMetrics(backtestId),
      fetchTrades(backtestId),
      fetchCharts(backtestId)
    ]);
  }, [backtestId, fetchBacktest, fetchStatus, fetchMetrics, fetchTrades, fetchCharts]);
  
  // Clear all data
  const clearData = useCallback(() => {
    setBacktest(null);
    setStatus(null);
    setMetrics(null);
    setTrades([]);
    setCharts(null);
    setError(null);
    setMetricsError(null);
    setTradesError(null);
    setChartsError(null);
  }, []);
  
  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh || !backtestId) return;
    
    const interval = setInterval(() => {
      // Only refresh if backtest is still in progress
      if (status?.status === 'IN_PROGRESS' || status?.status === 'PENDING') {
        refresh();
      }
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [autoRefresh, backtestId, status?.status, refresh, refreshInterval]);
  
  // Initial data fetch
  useEffect(() => {
    if (backtestId) {
      refresh();
    }
  }, [backtestId, refresh]);
  
  return {
    // Data
    backtest,
    status,
    metrics,
    trades,
    charts,
    backtestList,
    
    // Loading states
    loading,
    loadingMetrics,
    loadingTrades,
    loadingCharts,
    loadingList,
    
    // Error states
    error,
    metricsError,
    tradesError,
    chartsError,
    listError,
    
    // Actions
    fetchBacktest,
    fetchStatus,
    fetchMetrics,
    fetchTrades,
    fetchCharts,
    fetchBacktestList,
    deleteBacktest,
    pollStatus,
    
    // Utilities
    refresh,
    clearData
  };
}

// Hook for creating new backtests
export function useBacktestCreation() {
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const createBacktest = useCallback(async (request: any) => {
    setCreating(true);
    setError(null);
    
    try {
      const result = await backtestApi.createBacktest(request);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Chyba při vytváření backtestingu';
      setError(errorMessage);
      throw err;
    } finally {
      setCreating(false);
    }
  }, []);
  
  return {
    createBacktest,
    creating,
    error
  };
}
