import { createContext, ReactNode, useContext, useState } from 'react';
import { useBacktestData, useBacktestCreation } from '@/hooks/use-backtest-data';
import {
  BacktestAdvancedMetrics,
  BacktestChartsData,
  BacktestListItem,
  BacktestResults,
  BacktestStatus,
  TradeHistoryItem
} from '@/services/types';

interface BacktestContextType {
  // Current selected backtest
  selectedBacktestId: string | null;
  setSelectedBacktestId: (id: string | null) => void;
  
  // Data from useBacktestData hook
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
  
  // Creation
  createBacktest: (request: any) => Promise<any>;
  creating: boolean;
  creationError: string | null;
  
  // Utilities
  refresh: () => Promise<void>;
  clearData: () => void;
}

const BacktestContext = createContext<BacktestContextType | null>(null);

export function useBacktestContext() {
  const context = useContext(BacktestContext);
  if (!context) {
    throw new Error('useBacktestContext must be used within a BacktestProvider');
  }
  return context;
}

interface BacktestProviderProps {
  children: ReactNode;
}

export function BacktestProvider({ children }: BacktestProviderProps) {
  const [selectedBacktestId, setSelectedBacktestId] = useState<string | null>(null);
  
  // Use the backtest data hook
  const backtestData = useBacktestData({
    backtestId: selectedBacktestId || undefined,
    autoRefresh: true,
    refreshInterval: 5000
  });
  
  // Use the backtest creation hook
  const { createBacktest, creating, error: creationError } = useBacktestCreation();
  
  const value: BacktestContextType = {
    // Current selected backtest
    selectedBacktestId,
    setSelectedBacktestId,
    
    // Data from useBacktestData hook
    backtest: backtestData.backtest,
    status: backtestData.status,
    metrics: backtestData.metrics,
    trades: backtestData.trades,
    charts: backtestData.charts,
    backtestList: backtestData.backtestList,
    
    // Loading states
    loading: backtestData.loading,
    loadingMetrics: backtestData.loadingMetrics,
    loadingTrades: backtestData.loadingTrades,
    loadingCharts: backtestData.loadingCharts,
    loadingList: backtestData.loadingList,
    
    // Error states
    error: backtestData.error,
    metricsError: backtestData.metricsError,
    tradesError: backtestData.tradesError,
    chartsError: backtestData.chartsError,
    listError: backtestData.listError,
    
    // Actions
    fetchBacktest: backtestData.fetchBacktest,
    fetchStatus: backtestData.fetchStatus,
    fetchMetrics: backtestData.fetchMetrics,
    fetchTrades: backtestData.fetchTrades,
    fetchCharts: backtestData.fetchCharts,
    fetchBacktestList: backtestData.fetchBacktestList,
    deleteBacktest: backtestData.deleteBacktest,
    pollStatus: backtestData.pollStatus,
    
    // Creation
    createBacktest,
    creating,
    creationError,
    
    // Utilities
    refresh: backtestData.refresh,
    clearData: backtestData.clearData
  };

  return (
    <BacktestContext.Provider value={value}>
      {children}
    </BacktestContext.Provider>
  );
}
