import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Badge } from '../../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { Separator } from '../../ui/separator';
import { 
  TrendingUp, 
  Target, 
  PieChart, 
  Calculator,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Plus,
  Trash2
} from 'lucide-react';

interface Asset {
  symbol: string;
  weight: number;
  expected_return: number;
  volatility: number;
  current_price: number;
  price_change_24h: number;
}

interface PortfolioMetrics {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  var_95: number;
  max_drawdown: number;
  beta: number;
}

interface OptimizationResult {
  optimization_objective: string;
  timestamp: string;
  assets: Asset[];
  metrics: PortfolioMetrics;
  efficient_frontier: Array<{
    return: number;
    risk: number;
    weights: Record<string, number>;
  }>;
  constraints: any;
  lookback_days: number;
  data_points: number;
}

interface OptimizationRequest {
  symbols: string[];
  objective: 'max_sharpe' | 'min_volatility' | 'max_return';
  constraints: {
    max_weight: number;
    min_weight: number;
    target_return?: number;
    target_volatility?: number;
  };
  lookback_days: number;
}

export const PortfolioOptimizer: React.FC = () => {
  const [symbols, setSymbols] = useState<string[]>(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'CL=F']);
  const [newSymbol, setNewSymbol] = useState('');
  const [objective, setObjective] = useState<'max_sharpe' | 'min_volatility' | 'max_return'>('max_sharpe');
  const [maxWeight, setMaxWeight] = useState(0.4);
  const [minWeight, setMinWeight] = useState(0.05);
  const [targetReturn, setTargetReturn] = useState(0.12);
  const [lookbackDays, setLookbackDays] = useState(252);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const addSymbol = () => {
    if (newSymbol.trim() && !symbols.includes(newSymbol.toUpperCase())) {
      setSymbols([...symbols, newSymbol.toUpperCase()]);
      setNewSymbol('');
    }
  };

  const removeSymbol = (symbolToRemove: string) => {
    setSymbols(symbols.filter(symbol => symbol !== symbolToRemove));
  };

  const optimizePortfolio = async () => {
    if (symbols.length < 2) {
      setError('Potřebujete alespoň 2 symboly pro optimalizaci');
      return;
    }

    setLoading(true);
    setError(null);

    const request: OptimizationRequest = {
      symbols,
      objective,
      constraints: {
        max_weight: maxWeight,
        min_weight: minWeight,
        ...(objective === 'max_return' && { target_return: targetReturn })
      },
      lookback_days: lookbackDays
    };

    try {
      const response = await fetch('http://localhost:8000/openbb/portfolio/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error('Chyba při optimalizaci portfolia');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError('Chyba při optimalizaci portfolia');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getObjectiveLabel = (obj: string) => {
    switch (obj) {
      case 'max_sharpe': return 'Maximalizovat Sharpe Ratio';
      case 'min_volatility': return 'Minimalizovat Volatilitu';
      case 'max_return': return 'Maximalizovat Výnos';
      default: return obj;
    }
  };

  const getRiskLevel = (volatility: number) => {
    if (volatility < 0.15) return { level: 'Nízké', color: 'text-green-600' };
    if (volatility < 0.25) return { level: 'Střední', color: 'text-yellow-600' };
    return { level: 'Vysoké', color: 'text-red-600' };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Portfolio Optimization
          </CardTitle>
          <CardDescription>
            Modern Portfolio Theory - optimalizace portfolia podle Markowitze
          </CardDescription>
        </CardHeader>
      </Card>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="setup" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="setup">Nastavení</TabsTrigger>
          <TabsTrigger value="results">Výsledky</TabsTrigger>
          <TabsTrigger value="frontier">Efficient Frontier</TabsTrigger>
        </TabsList>

        {/* Nastavení */}
        <TabsContent value="setup" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Symboly */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Symboly Akcií</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Přidat symbol (např. NVDA)"
                    value={newSymbol}
                    onChange={(e) => setNewSymbol(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
                    className="flex-1"
                  />
                  <Button onClick={addSymbol} size="sm">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex flex-wrap gap-2">
                  {symbols.map((symbol) => (
                    <Badge key={symbol} variant="outline" className="flex items-center gap-1">
                      {symbol}
                      <button
                        onClick={() => removeSymbol(symbol)}
                        className="ml-1 hover:text-red-600"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>

                <div className="text-sm text-gray-600">
                  Celkem: {symbols.length} symbolů
                </div>
              </CardContent>
            </Card>

            {/* Optimalizační parametry */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Parametry Optimalizace</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Cíl optimalizace</label>
                  <select
                    value={objective}
                    onChange={(e) => setObjective(e.target.value as any)}
                    className="w-full mt-1 p-2 border rounded-md"
                  >
                    <option value="max_sharpe">Maximalizovat Sharpe Ratio</option>
                    <option value="min_volatility">Minimalizovat Volatilitu</option>
                    <option value="max_return">Maximalizovat Výnos</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Max. váha (%)</label>
                    <Input
                      type="number"
                      value={maxWeight * 100}
                      onChange={(e) => setMaxWeight(Number(e.target.value) / 100)}
                      min="1"
                      max="100"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Min. váha (%)</label>
                    <Input
                      type="number"
                      value={minWeight * 100}
                      onChange={(e) => setMinWeight(Number(e.target.value) / 100)}
                      min="0"
                      max="50"
                      className="mt-1"
                    />
                  </div>
                </div>

                {objective === 'max_return' && (
                  <div>
                    <label className="text-sm font-medium">Cílový výnos (%)</label>
                    <Input
                      type="number"
                      value={targetReturn * 100}
                      onChange={(e) => setTargetReturn(Number(e.target.value) / 100)}
                      min="1"
                      max="50"
                      className="mt-1"
                    />
                  </div>
                )}

                <div>
                  <label className="text-sm font-medium">Lookback období (dny)</label>
                  <Input
                    type="number"
                    value={lookbackDays}
                    onChange={(e) => setLookbackDays(Number(e.target.value))}
                    min="30"
                    max="1000"
                    className="mt-1"
                  />
                </div>

                <Button 
                  onClick={optimizePortfolio}
                  disabled={loading || symbols.length < 2}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Optimalizuji...
                    </>
                  ) : (
                    <>
                      <Calculator className="h-4 w-4 mr-2" />
                      Optimalizovat Portfolio
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Výsledky */}
        <TabsContent value="results" className="space-y-4">
          {result ? (
            <div className="space-y-6">
              {/* Portfolio metriky */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    Optimalizované Portfolio
                  </CardTitle>
                  <CardDescription>
                    Cíl: {getObjectiveLabel(objective)} | Aktualizováno: {new Date(result.timestamp).toLocaleString('cs-CZ')}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">Očekávaný výnos</div>
                      <div className="text-2xl font-bold text-green-600">
                        {(result.metrics.expected_return * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Volatilita</div>
                      <div className={`text-2xl font-bold ${getRiskLevel(result.metrics.volatility).color}`}>
                        {(result.metrics.volatility * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Sharpe Ratio</div>
                      <div className="text-2xl font-bold">
                        {result.metrics.sharpe_ratio.toFixed(3)}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">VaR (95%)</div>
                      <div className="text-2xl font-bold text-red-600">
                        {(result.metrics.var_95 * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Max Drawdown</div>
                      <div className="text-2xl font-bold text-red-600">
                        {(result.metrics.max_drawdown * 100).toFixed(2)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Beta</div>
                      <div className="text-2xl font-bold">
                        {result.metrics.beta.toFixed(3)}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Alokace aktiv */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="h-5 w-5" />
                    Alokace Aktiv
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {result.assets.map((asset) => (
                      <div key={asset.symbol} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center gap-4">
                          <div className="font-medium text-lg">{asset.symbol}</div>
                          <div className="text-sm text-gray-600">
                            ${asset.current_price.toFixed(2)}
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <div className="text-sm text-gray-600">Váha</div>
                            <div className="text-lg font-bold">
                              {(asset.weight * 100).toFixed(1)}%
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-gray-600">Očekávaný výnos</div>
                            <div className="text-lg font-semibold text-green-600">
                              {(asset.expected_return * 100).toFixed(1)}%
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-gray-600">Volatilita</div>
                            <div className={`text-lg font-semibold ${getRiskLevel(asset.volatility).color}`}>
                              {(asset.volatility * 100).toFixed(1)}%
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Rizikové metriky */}
              <Card>
                <CardHeader>
                  <CardTitle>Analýza Rizika</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium mb-2">Rizikový profil</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Úroveň rizika:</span>
                          <Badge className={getRiskLevel(result.metrics.volatility).color}>
                            {getRiskLevel(result.metrics.volatility).level}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>Beta k trhu:</span>
                          <span>{result.metrics.beta.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Diverzifikace:</span>
                          <span>{result.assets.length} aktiv</span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">Výkonnostní metriky</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Risk-adjusted return:</span>
                          <span>{result.metrics.sharpe_ratio.toFixed(3)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Worst case (VaR):</span>
                          <span className="text-red-600">
                            {(result.metrics.var_95 * 100).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Max ztráta:</span>
                          <span className="text-red-600">
                            {(result.metrics.max_drawdown * 100).toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-gray-500">
                  <Calculator className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Spusťte optimalizaci pro zobrazení výsledků</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Efficient Frontier */}
        <TabsContent value="frontier" className="space-y-4">
          {result && result.efficient_frontier ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Efficient Frontier
                </CardTitle>
                <CardDescription>
                  Optimální kombinace rizika a výnosu
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-sm text-gray-600 mb-4">
                    Graf zobrazuje optimální portfolia pro různé úrovně rizika
                  </div>
                  
                  {/* Placeholder pro graf - bude implementován s Chart.js */}
                  <div className="h-64 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <TrendingUp className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p>Efficient Frontier Chart</p>
                      <p className="text-xs">(Bude implementován s Chart.js)</p>
                    </div>
                  </div>

                  {/* Tabulka s daty */}
                  <div className="mt-6">
                    <h4 className="font-medium mb-3">Efficient Frontier Data</h4>
                    <div className="max-h-64 overflow-y-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="p-2 text-left">Výnos (%)</th>
                            <th className="p-2 text-left">Riziko (%)</th>
                            <th className="p-2 text-left">Sharpe Ratio</th>
                            <th className="p-2 text-left">Top Holdings</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.efficient_frontier.map((point, index) => (
                            <tr key={index} className="border-b">
                              <td className="p-2">{(point.return * 100).toFixed(2)}%</td>
                              <td className="p-2">{(point.risk * 100).toFixed(2)}%</td>
                              <td className="p-2">{(point.return / point.risk).toFixed(3)}</td>
                              <td className="p-2">
                                {Object.entries(point.weights)
                                  .sort(([,a], [,b]) => (b as number) - (a as number))
                                  .slice(0, 2)
                                  .map(([symbol, weight]) => `${symbol}: ${((weight as number) * 100).toFixed(0)}%`)
                                  .join(', ')}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-gray-500">
                  <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Spusťte optimalizaci pro zobrazení Efficient Frontier</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};
