import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Badge } from '../../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { Separator } from '../../ui/separator';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  DollarSign, 
  BarChart3, 
  Globe,
  AlertCircle,
  CheckCircle,
  Loader2,
  PieChart
} from 'lucide-react';
import { PortfolioOptimizer } from './portfolio-optimizer';

interface OpenBBStatus {
  openbb_available: boolean;
  integration_status: string;
  supported_providers: string[];
}

interface MarketOverview {
  timestamp: string;
  market_sentiment: string;
  indices: Record<string, {
    price: number;
    change_percent: number;
    trend: string;
  }>;
}

interface StockAnalysis {
  symbol: string;
  timestamp: string;
  openbb_available: boolean;
  price_analysis: {
    latest_price: number;
    price_change_percent: number;
    moving_average_20: number;
    rsi: number;
    trend_signal: string;
    momentum_signal: string;
  };
  financial_health: {
    revenue_growth: number;
    profit_margin: number;
    financial_strength: string;
  };
  recent_news: {
    overall_sentiment: string;
    news_count: number;
  };
  recommendation: {
    action: string;
    confidence: number;
    reasoning: string[];
    risk_level: string;
  };
}

export const OpenBBPanel: React.FC = () => {
  const [status, setStatus] = useState<OpenBBStatus | null>(null);
  const [marketOverview, setMarketOverview] = useState<MarketOverview | null>(null);
  const [stockAnalysis, setStockAnalysis] = useState<StockAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [symbol, setSymbol] = useState('AAPL');
  const [error, setError] = useState<string | null>(null);

  // Načtení OpenBB statusu
  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/openbb/status');
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      setError('Chyba při načítání OpenBB statusu');
    }
  };

  // Načtení tržního přehledu
  const fetchMarketOverview = async () => {
    try {
      const response = await fetch('http://localhost:8000/openbb/market/overview');
      const data = await response.json();
      setMarketOverview(data);
    } catch (err) {
      setError('Chyba při načítání tržního přehledu');
    }
  };

  // Analýza akcie
  const analyzeStock = async () => {
    if (!symbol.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/openbb/analyze/stock', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: symbol.toUpperCase(),
          days: 30,
          provider: 'yfinance'
        }),
      });
      
      const data = await response.json();
      setStockAnalysis(data);
    } catch (err) {
      setError('Chyba při analýze akcie');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchMarketOverview();
  }, []);

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'bullish': return 'text-green-600';
      case 'bearish': return 'text-red-600';
      case 'positive': return 'text-green-600';
      case 'negative': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getActionColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'buy': return 'bg-green-100 text-green-800';
      case 'sell': return 'bg-red-100 text-red-800';
      case 'hold': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTrendIcon = (trend: string) => {
    return trend === 'Up' ? (
      <TrendingUp className="h-4 w-4 text-green-600" />
    ) : (
      <TrendingDown className="h-4 w-4 text-red-600" />
    );
  };

  return (
    <div className="space-y-6">
      {/* Header s OpenBB statusem */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            OpenBB Platform Integration
          </CardTitle>
          <CardDescription>
            Pokročilé finanční data a analýzy
          </CardDescription>
        </CardHeader>
        <CardContent>
          {status ? (
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                {status.openbb_available ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-600" />
                )}
                <span className={status.openbb_available ? 'text-green-600' : 'text-red-600'}>
                  {status.openbb_available ? 'Aktivní' : 'Nedostupné'}
                </span>
              </div>
              <Badge variant="outline">
                {status.supported_providers.length} poskytovatelů
              </Badge>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Načítání statusu...</span>
            </div>
          )}
        </CardContent>
      </Card>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="market" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="market">Tržní Přehled</TabsTrigger>
          <TabsTrigger value="analysis">Analýza Akcií</TabsTrigger>
          <TabsTrigger value="portfolio">Portfolio Optimizer</TabsTrigger>
          <TabsTrigger value="providers">Poskytovatelé</TabsTrigger>
        </TabsList>

        {/* Tržní Přehled */}
        <TabsContent value="market" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Tržní Sentiment
              </CardTitle>
            </CardHeader>
            <CardContent>
              {marketOverview ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Celkový sentiment:</span>
                    <Badge className={getSentimentColor(marketOverview.market_sentiment)}>
                      {marketOverview.market_sentiment}
                    </Badge>
                  </div>
                  
                  <Separator />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(marketOverview.indices).map(([symbol, data]) => (
                      <Card key={symbol} className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium">{symbol}</div>
                            <div className="text-2xl font-bold">
                              ${data.price.toFixed(2)}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="flex items-center gap-1">
                              {getTrendIcon(data.trend)}
                              <span className={data.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}>
                                {data.change_percent >= 0 ? '+' : ''}{data.change_percent.toFixed(2)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Načítání tržních dat...</span>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analýza Akcií */}
        <TabsContent value="analysis" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Analýza Akcie
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Symbol akcie (např. AAPL)"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="flex-1"
                />
                <Button 
                  onClick={analyzeStock}
                  disabled={loading || !symbol.trim()}
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    'Analyzovat'
                  )}
                </Button>
              </div>

              {stockAnalysis && (
                <div className="space-y-6">
                  {/* Cenová analýza */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4" />
                        Cenová Analýza - {stockAnalysis.symbol}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <div className="text-sm text-gray-600">Aktuální cena</div>
                          <div className="text-2xl font-bold">
                            ${stockAnalysis.price_analysis.latest_price.toFixed(2)}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Změna</div>
                          <div className={`text-lg font-semibold ${
                            stockAnalysis.price_analysis.price_change_percent >= 0 
                              ? 'text-green-600' 
                              : 'text-red-600'
                          }`}>
                            {stockAnalysis.price_analysis.price_change_percent >= 0 ? '+' : ''}
                            {stockAnalysis.price_analysis.price_change_percent.toFixed(2)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">RSI</div>
                          <div className="text-lg font-semibold">
                            {stockAnalysis.price_analysis.rsi.toFixed(1)}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Trend</div>
                          <Badge className={getSentimentColor(stockAnalysis.price_analysis.trend_signal)}>
                            {stockAnalysis.price_analysis.trend_signal}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Finanční zdraví */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Finanční Zdraví</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <div className="text-sm text-gray-600">Růst tržeb</div>
                          <div className="text-lg font-semibold">
                            {stockAnalysis.financial_health.revenue_growth.toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Zisková marže</div>
                          <div className="text-lg font-semibold">
                            {stockAnalysis.financial_health.profit_margin.toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-600">Finanční síla</div>
                          <Badge variant="outline">
                            {stockAnalysis.financial_health.financial_strength}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* AI Doporučení */}
                  <Card>
                    <CardHeader>
                      <CardTitle>AI Doporučení</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-center gap-4">
                          <Badge className={getActionColor(stockAnalysis.recommendation.action)}>
                            {stockAnalysis.recommendation.action}
                          </Badge>
                          <div className="text-sm">
                            Důvěra: {(stockAnalysis.recommendation.confidence * 100).toFixed(0)}%
                          </div>
                          <div className="text-sm">
                            Riziko: {stockAnalysis.recommendation.risk_level}
                          </div>
                        </div>
                        
                        <div>
                          <div className="text-sm font-medium mb-2">Důvody:</div>
                          <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                            {stockAnalysis.recommendation.reasoning.map((reason, index) => (
                              <li key={index}>{reason}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Portfolio Optimizer */}
        <TabsContent value="portfolio" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Portfolio Optimizer
              </CardTitle>
              <CardDescription>
                Modern Portfolio Theory optimalizace s OpenBB daty
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PortfolioOptimizer />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Poskytovatelé */}
        <TabsContent value="providers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Dostupní Poskytovatelé Dat</CardTitle>
              <CardDescription>
                OpenBB Platform podporuje více než 100 poskytovatelů finančních dat
              </CardDescription>
            </CardHeader>
            <CardContent>
              {status && (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {status.supported_providers.map((provider) => (
                    <Badge key={provider} variant="outline" className="justify-center">
                      {provider}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
