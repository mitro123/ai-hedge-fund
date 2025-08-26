import { useLayoutContext } from '@/contexts/layout-context';
import { useResizable } from '@/hooks/use-resizable';
import { cn } from '@/lib/utils';
import { FileText, X, TrendingUp, BarChart3, Activity, History, Settings } from 'lucide-react';
import { ReactNode, useEffect } from 'react';
import { Button } from '../../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { 
  OutputTab, 
  BacktestManager, 
  BacktestOutput, 
  InteractiveCharts, 
  AdvancedPerformanceMetrics, 
  TradeHistoryViewer 
} from './tabs';

interface BottomPanelProps {
  children?: ReactNode;
  isCollapsed: boolean;
  onCollapse: () => void;
  onExpand: () => void;
  onToggleCollapse: () => void;
  onHeightChange?: (height: number) => void;
}

export function BottomPanel({
  isCollapsed,
  onToggleCollapse,
  onHeightChange,
}: BottomPanelProps) {
  const { currentBottomTab, setBottomPanelTab } = useLayoutContext();
  
  // Use our custom hooks for vertical resizing
  const { height, isDragging, elementRef, startResize } = useResizable({
    defaultHeight: 300,
    minHeight: 200,
    maxHeight: window.innerHeight,
    side: 'bottom',
  });
  
  // Notify parent component of height changes
  useEffect(() => {
    onHeightChange?.(height);
  }, [height, onHeightChange]);

  if (isCollapsed) {
    return null;
  }

  return (
    <div 
      ref={elementRef}
      className={cn(
        "bg-panel flex flex-col relative border-t",
        isDragging ? "select-none" : ""
      )}
      style={{ 
        height: `${height}px`,
      }}
    >
      {/* Resize handle - on the top for bottom panel */}
      {!isDragging && (
        <div 
          className="absolute top-0 left-0 right-0 h-1 cursor-ns-resize transition-all duration-150 z-10 hover-bg"
          onMouseDown={startResize}
        />
      )}

      {/* Header with tabs and close button */}
      <div className="flex items-center justify-between border-b px-4 py-2">
        <Tabs value={currentBottomTab} onValueChange={setBottomPanelTab} className="flex-1">
          <div className="flex items-center justify-between">
            <TabsList className="bg-transparent border-none p-0 h-auto">
              <TabsTrigger 
                value="output"
                className="flex items-center gap-2 px-3 py-1.5 text-sm data-[state=active]:active-item text-muted-foreground"
              >
                <FileText size={14} />
                Výstup
              </TabsTrigger>
              <TabsTrigger 
                value="backtest-manager"
                className="flex items-center gap-2 px-3 py-1.5 text-sm data-[state=active]:active-item text-muted-foreground"
              >
                <Settings size={14} />
                Správa Backtestů
              </TabsTrigger>
              <TabsTrigger 
                value="backtest-output"
                className="flex items-center gap-2 px-3 py-1.5 text-sm data-[state=active]:active-item text-muted-foreground"
              >
                <TrendingUp size={14} />
                Výsledky
              </TabsTrigger>
              <TabsTrigger 
                value="interactive-charts"
                className="flex items-center gap-2 px-3 py-1.5 text-sm data-[state=active]:active-item text-muted-foreground"
              >
                <BarChart3 size={14} />
                Grafy
              </TabsTrigger>
              <TabsTrigger 
                value="performance-metrics"
                className="flex items-center gap-2 px-3 py-1.5 text-sm data-[state=active]:active-item text-muted-foreground"
              >
                <Activity size={14} />
                Metriky
              </TabsTrigger>
              <TabsTrigger 
                value="trade-history"
                className="flex items-center gap-2 px-3 py-1.5 text-sm data-[state=active]:active-item text-muted-foreground"
              >
                <History size={14} />
                Historie
              </TabsTrigger>
            </TabsList>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggleCollapse}
              className="h-6 w-6 text-primary hover-bg"
              aria-label="Zavřít panel"
            >
              <X size={14} />
            </Button>
          </div>
        </Tabs>
      </div>

      {/* Content area */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <Tabs value={currentBottomTab} className="h-full">
          <TabsContent value="output" className="h-full m-0 p-4">
            <OutputTab className="h-full" />
          </TabsContent>
          <TabsContent value="backtest-manager" className="h-full m-0 p-4">
            <BacktestManager />
          </TabsContent>
          <TabsContent value="backtest-output" className="h-full m-0 p-4">
            <BacktestOutput />
          </TabsContent>
          <TabsContent value="interactive-charts" className="h-full m-0 p-4">
            <InteractiveCharts />
          </TabsContent>
          <TabsContent value="performance-metrics" className="h-full m-0 p-4">
            <AdvancedPerformanceMetrics />
          </TabsContent>
          <TabsContent value="trade-history" className="h-full m-0 p-4">
            <TradeHistoryViewer />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
