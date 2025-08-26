# Frontend Backtest Components Documentation

## Overview

Tato dokumentace popisuje nové frontend komponenty vytvořené pro pokročilé backtest funkce v AI Hedge Fund aplikaci. Komponenty poskytují interaktivní vizualizace, pokročilé metriky a uživatelsky přívětivé rozhraní pro analýzu trading performance.

## Nové Komponenty

### 1. AdvancedPerformanceMetrics

**Umístění:** `app/frontend/src/components/panels/bottom/tabs/advanced-performance-metrics.tsx`

**Účel:** Zobrazuje pokročilé performance metriky s vizuálními indikátory a benchmarky.

**Funkce:**
- **Performance Rating:** Automatické hodnocení strategie (Excellent/Good/Fair/Poor)
- **Return Metrics:** Total Return, Best/Worst Day, Win Rate
- **Risk Metrics:** Volatility, Max Drawdown, VaR 95%, Expected Shortfall
- **Risk-Adjusted Ratios:** Sharpe, Sortino, Calmar, Win/Loss Ratio
- **Trading Metrics:** Consecutive wins/losses, Long/Short ratio
- **Benchmark Comparison:** Porovnání s benchmarky (10% return, 1.0 Sharpe, atd.)

**Props:**
```typescript
interface AdvancedPerformanceMetricsProps {
  metrics: BacktestPerformanceMetrics;
  className?: string;
}
```

### 2. TradeHistoryViewer

**Umístění:** `app/frontend/src/components/panels/bottom/tabs/trade-history-viewer.tsx`

**Účel:** Interaktivní prohlížeč historie obchodů s filtrováním a exportem.

**Funkce:**
- **Trade Statistics:** Celkové statistiky (počet obchodů, volume, průměrná velikost)
- **Advanced Filtering:** Podle tickeru, akce, data
- **Search Functionality:** Vyhledávání v historii
- **Export to CSV:** Export dat do CSV formátu
- **Visual Indicators:** Barevné rozlišení akcí (BUY/SELL/SHORT/COVER)
- **Responsive Design:** Optimalizováno pro různé velikosti obrazovek

**Props:**
```typescript
interface TradeHistoryViewerProps {
  trades: TradeHistoryItem[];
  className?: string;
}
```

### 3. InteractiveCharts

**Umístění:** `app/frontend/src/components/panels/bottom/tabs/interactive-charts.tsx`

**Účel:** Dashboard pro interaktivní grafy (připraveno pro Plotly.js integraci).

**Funkce:**
- **Chart Selection:** Výběr z 6 typů grafů
- **Portfolio Value Chart:** Vývoj hodnoty portfolia s trade markery
- **Daily Returns Distribution:** Histogram denních výnosů
- **Underwater Plot:** Drawdown analýza
- **Price Chart with Trades:** Ceny s buy/sell markery
- **Rolling Sharpe Ratio:** 30-denní klouzavý Sharpe ratio
- **Monthly Heatmap:** Kalendářní pohled na měsíční výkonnost
- **Export Functionality:** Export grafů do PNG/SVG/PDF

**Props:**
```typescript
interface InteractiveChartsProps {
  trades: TradeHistoryItem[];
  portfolioValues: Array<{
    date: string;
    value: number;
    dailyReturn?: number;
    drawdown?: number;
  }>;
  metrics: BacktestPerformanceMetrics;
  className?: string;
}
```

### 4. Enhanced BacktestOutput

**Umístění:** `app/frontend/src/components/panels/bottom/tabs/backtest-output.tsx`

**Účel:** Hlavní komponenta s tab rozhraním pro všechny backtest funkce.

**Nové funkce:**
- **Tab Interface:** 5 tabů (Overview, Advanced Metrics, Trade History, Interactive Charts, Activity Log)
- **Data Conversion:** Automatická konverze backtest dat pro nové komponenty
- **Real-time Updates:** Aktualizace dat během běhu backtesteru
- **Responsive Layout:** Optimalizované rozložení pro různé obrazovky

**Taby:**
1. **Overview:** Původní přehled s progress a základními metrikami
2. **Advanced Metrics:** Pokročilé performance metriky
3. **Trade History:** Historie obchodů s filtrováním
4. **Interactive Charts:** Interaktivní grafy a vizualizace
5. **Activity Log:** Detailní log aktivit backtesteru

## Datové Typy

### BacktestPerformanceMetrics
```typescript
interface BacktestPerformanceMetrics {
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
```

### TradeHistoryItem
```typescript
interface TradeHistoryItem {
  date: string;
  ticker: string;
  action: 'BUY' | 'SELL' | 'SHORT' | 'COVER' | 'HOLD';
  quantity: number;
  price: number;
}
```

### BacktestVisualizationConfig
```typescript
interface BacktestVisualizationConfig {
  enable_interactive_charts?: boolean;
  enable_performance_dashboard?: boolean;
  chart_types?: string[];
}
```

## Integrace s Backend

### Požadované API Endpointy

1. **GET /api/backtest/{id}/advanced-metrics**
   - Vrací pokročilé performance metriky
   - Response: `BacktestPerformanceMetrics`

2. **GET /api/backtest/{id}/trade-history**
   - Vrací historii všech obchodů
   - Response: `TradeHistoryItem[]`

3. **GET /api/backtest/{id}/portfolio-values**
   - Vrací časovou řadu hodnot portfolia
   - Response: `Array<{date: string, value: number, dailyReturn?: number}>`

4. **POST /api/backtest/{id}/export**
   - Export dat v různých formátech
   - Body: `{format: 'csv' | 'json' | 'excel', data_type: 'trades' | 'metrics' | 'charts'}`

### WebSocket Events

Pro real-time aktualizace:
```typescript
// Nová trade data
ws.send({
  type: 'trade_executed',
  data: TradeHistoryItem
});

// Aktualizované metriky
ws.send({
  type: 'metrics_updated',
  data: BacktestPerformanceMetrics
});

// Nová portfolio hodnota
ws.send({
  type: 'portfolio_value_updated',
  data: {date: string, value: number}
});
```

## Budoucí Vylepšení

### Plotly.js Integrace
```typescript
// Příklad implementace pro portfolio chart
import Plot from 'react-plotly.js';

const PortfolioChart = ({ data }) => (
  <Plot
    data={[{
      x: data.map(d => d.date),
      y: data.map(d => d.value),
      type: 'scatter',
      mode: 'lines',
      name: 'Portfolio Value'
    }]}
    layout={{
      title: 'Portfolio Performance',
      xaxis: { title: 'Date' },
      yaxis: { title: 'Value ($)' }
    }}
  />
);
```

### Pokročilé Filtry
- Časové rozmezí
- Typ instrumentu
- Velikost pozice
- P&L rozmezí

### Customizace
- Uživatelské dashboardy
- Vlastní metriky
- Barevné schéma
- Export nastavení

## Testování

### Unit Tests
```bash
# Spuštění testů pro nové komponenty
npm test -- --testPathPattern="advanced-performance-metrics|trade-history-viewer|interactive-charts"
```

### Integration Tests
```bash
# Test integrace s backend API
npm run test:integration
```

### E2E Tests
```bash
# Test celého backtest workflow
npm run test:e2e -- --spec="backtest-workflow.cy.ts"
```

## Performance Optimalizace

### Lazy Loading
```typescript
// Lazy loading pro velké datasety
const TradeHistoryViewer = lazy(() => import('./trade-history-viewer'));
```

### Virtualizace
```typescript
// Pro velké seznamy obchodů
import { FixedSizeList as List } from 'react-window';
```

### Memoization
```typescript
// Optimalizace výpočtů metrik
const metrics = useMemo(() => calculateMetrics(data), [data]);
```

## Troubleshooting

### Časté Problémy

1. **Chybějící data:** Zkontrolujte API endpointy
2. **Pomalé renderování:** Implementujte virtualizaci
3. **Memory leaks:** Použijte cleanup v useEffect
4. **TypeScript chyby:** Zkontrolujte typy v services/types.ts

### Debug Mode
```typescript
// Zapnutí debug módu
localStorage.setItem('backtest_debug', 'true');
```

## Závěr

Nové frontend komponenty poskytují komprehensivní řešení pro analýzu backtest výsledků s moderním, interaktivním rozhraním. Komponenty jsou navrženy pro snadnou rozšiřitelnost a integraci s existujícím systémem.

Pro další informace kontaktujte vývojový tým nebo se podívejte na související dokumentaci v `docs/` složce.
