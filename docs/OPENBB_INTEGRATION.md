# OpenBB Platform Integration

Tento dokument popisuje integraci OpenBB Platform do AI Hedge Fund projektu, která poskytuje pokročilé finanční data a analýzy.

## Přehled

OpenBB Platform je open-source finanční data platforma, která poskytuje jednotné API pro přístup k datům z více než 100 různých poskytovatelů finančních dat. Naše integrace umožňuje:

- **Historická cenová data** - akcie, kryptoměny, forex
- **Fundamentální analýza** - finanční výkazy, klíčové metriky
- **Zpravodajství** - firemní a tržní zprávy
- **Ekonomická data** - makroekonomické indikátory
- **Opční data** - opční řetězce a analýzy
- **Pokročilé analýzy** - technické indikátory, sentiment analýza

## Architektura

### Komponenty

1. **OpenBB Integration Layer** (`src/integrations/openbb_integration.py`)
   - Základní wrapper pro OpenBB Platform
   - Správa připojení a error handling
   - Jednotné API pro různé datové zdroje

2. **Enhanced AI Agent** (`src/agents/openbb_enhanced_agent.py`)
   - Pokročilý AI agent využívající OpenBB data
   - Komplexní analýzy akcií a portfolií
   - Automatické generování doporučení

3. **FastAPI Endpoints** (`app/backend/routes/openbb_integration.py`)
   - REST API pro přístup k OpenBB funkcionalitě
   - Validace vstupů a error handling
   - Dokumentace API pomocí OpenAPI/Swagger

## Instalace a Konfigurace

### 1. Klonování OpenBB Platform

```bash
# Klonování OpenBB repozitáře do projektu
cd /workspaces/ai-hedge-fund
git clone https://github.com/OpenBB-finance/OpenBB.git
```

### 2. Instalace závislostí

OpenBB Platform vyžaduje Python 3.8+ a specifické závislosti:

```bash
# Instalace OpenBB Platform
cd OpenBB/openbb_platform
pip install -e .

# Nebo pomocí poetry (doporučeno)
poetry install
```

### 3. Konfigurace API klíčů

OpenBB podporuje mnoho datových poskytovatelů. Některé vyžadují API klíče:

```bash
# Nastavení API klíčů (volitelné)
export FINANCIAL_MODELING_PREP_API_KEY="your_fmp_key"
export ALPHA_VANTAGE_API_KEY="your_av_key"
export POLYGON_API_KEY="your_polygon_key"
```

## API Endpointy

### Status a Konfigurace

#### `GET /openbb/status`
Vrací stav OpenBB integrace a dostupné poskytovatele dat.

**Response:**
```json
{
  "openbb_available": true,
  "integration_status": "active",
  "supported_providers": [
    "yfinance", "alpha_vantage", "fmp", "intrinio",
    "polygon", "tiingo", "benzinga", "fred"
  ]
}
```

### Historická Data

#### `GET /openbb/historical/{symbol}`
Získá historická cenová data pro zadaný symbol.

**Parametry:**
- `symbol` (path): Symbol akcie (např. "AAPL")
- `start_date` (query): Počáteční datum (YYYY-MM-DD)
- `end_date` (query): Koncové datum (YYYY-MM-DD)
- `interval` (query): Interval dat ("1d", "1h", "5m", atd.)
- `provider` (query): Poskytovatel dat (default: "yfinance")

**Příklad:**
```bash
curl "http://localhost:8000/openbb/historical/AAPL?start_date=2024-01-01&end_date=2024-12-31"
```

### Komplexní Analýza

#### `POST /openbb/analyze/stock`
Provede komplexní analýzu akcie pomocí AI agenta.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "days": 30,
  "provider": "yfinance"
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "timestamp": "2024-01-15T10:30:00",
  "price_analysis": {
    "latest_price": 185.50,
    "price_change_percent": 2.3,
    "moving_average_20": 180.25,
    "rsi": 65.2,
    "trend_signal": "Bullish",
    "momentum_signal": "Neutral"
  },
  "financial_health": {
    "revenue_growth": 8.5,
    "profit_margin": 23.1,
    "financial_strength": "Strong"
  },
  "recent_news": {
    "overall_sentiment": "Positive",
    "news_count": 5
  },
  "recommendation": {
    "action": "BUY",
    "confidence": 0.75,
    "reasoning": [
      "Bullish price trend (above 20-day MA)",
      "Strong profit margins (>15%)",
      "Positive news sentiment"
    ],
    "risk_level": "Medium"
  }
}
```

### Tržní Přehled

#### `GET /openbb/market/overview`
Poskytuje přehled hlavních tržních indexů.

**Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "market_sentiment": "Bullish",
  "indices": {
    "SPY": {
      "price": 485.20,
      "change_percent": 1.2,
      "trend": "Up"
    },
    "QQQ": {
      "price": 395.80,
      "change_percent": 0.8,
      "trend": "Up"
    }
  }
}
```

### Portfolio Analýza

#### `POST /openbb/analyze/portfolio`
Analyzuje diverzifikaci portfolia.

**Request Body:**
```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
  "provider": "yfinance"
}
```

**Response:**
```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
  "average_correlation": 0.65,
  "diversification_score": 0.35,
  "diversification_rating": "Moderate",
  "correlations": {
    "AAPL": {"GOOGL": 0.72, "MSFT": 0.68, "TSLA": 0.45}
  }
}
```

### Zpravodajství

#### `GET /openbb/news/{symbol}`
Získá nejnovější zprávy pro zadanou společnost.

**Parametry:**
- `symbol` (path): Symbol společnosti
- `limit` (query): Počet zpráv (default: 10)
- `provider` (query): Poskytovatel zpráv (default: "benzinga")

### Finanční Výkazy

#### `GET /openbb/financials/{symbol}`
Získá finanční výkazy společnosti.

**Parametry:**
- `symbol` (path): Symbol společnosti
- `statement_type` (query): Typ výkazu ("income", "balance", "cash")
- `period` (query): Období ("annual", "quarter")
- `limit` (query): Počet období (default: 5)
- `provider` (query): Poskytovatel dat (default: "fmp")

### Ekonomická Data

#### `GET /openbb/economic/{indicator}`
Získá makroekonomická data.

**Parametry:**
- `indicator` (path): Ekonomický indikátor (např. "GDP", "UNRATE")
- `start_date` (query): Počáteční datum
- `end_date` (query): Koncové datum
- `provider` (query): Poskytovatel dat (default: "fred")

### Opční Data

#### `GET /openbb/options/{symbol}`
Získá data o opcích pro zadaný symbol.

### Kryptoměny

#### `GET /openbb/crypto/{symbol}`
Získá data o kryptoměnách.

### Forex

#### `GET /openbb/forex/{symbol}`
Získá data o měnových párech.

## Použití v AI Agentech

### Základní Použití

```python
from src.integrations.openbb_integration import get_openbb_provider

# Získání poskytovatele
provider = get_openbb_provider()

# Kontrola dostupnosti
if provider.is_available():
    # Získání historických dat
    data = provider.get_historical_prices("AAPL", days=30)
    
    # Získání zpráv
    news = provider.get_market_news("AAPL", limit=5)
```

### Pokročilé Analýzy

```python
from src.agents.openbb_enhanced_agent import get_openbb_enhanced_agent

# Získání enhanced agenta
agent = get_openbb_enhanced_agent()

# Komplexní analýza akcie
analysis = agent.analyze_stock_comprehensive("AAPL", days=30)

# Tržní přehled
overview = agent.get_market_overview()

# Portfolio analýza
portfolio = agent.analyze_portfolio_diversification(["AAPL", "GOOGL", "MSFT"])
```

## Podporovaní Poskytovatelé Dat

### Bezplatní Poskytovatelé
- **yfinance** - Yahoo Finance (default pro většinu endpointů)
- **fred** - Federal Reserve Economic Data
- **benzinga** - Zpravodajství (omezené)

### Placení Poskytovatelé (vyžadují API klíč)
- **Financial Modeling Prep (FMP)** - Komplexní finanční data
- **Alpha Vantage** - Historická data a indikátory
- **Polygon** - Real-time a historická data
- **Intrinio** - Institucionální finanční data
- **Tiingo** - Alternativní datový zdroj

## Error Handling

Integrace obsahuje robustní error handling:

1. **Graceful Degradation** - Pokud OpenBB není dostupná, API vrací chybové zprávy
2. **Provider Fallback** - Automatické přepnutí na alternativní poskytovatele
3. **Data Validation** - Validace vstupních parametrů
4. **Logging** - Detailní logování pro debugging

## Výkon a Optimalizace

### Caching
- Implementace cache pro často používaná data
- Konfigurovatelné TTL pro různé typy dat

### Rate Limiting
- Respektování rate limitů poskytovatelů
- Automatické throttling při překročení limitů

### Asynchronní Zpracování
- Asynchronní volání pro lepší výkon
- Paralelní zpracování více symbolů

## Bezpečnost

### API Klíče
- Bezpečné ukládání API klíčů v environment variables
- Rotace klíčů podle potřeby

### Data Privacy
- Žádná citlivá data se neukládají trvale
- Compliance s GDPR a dalšími regulacemi

## Testování

### Unit Testy
```bash
# Spuštění testů pro OpenBB integraci
pytest tests/test_openbb_integration.py -v
```

### Integration Testy
```bash
# Testování s reálnými daty (vyžaduje API klíče)
pytest tests/test_openbb_live.py -v --api-keys
```

## Troubleshooting

### Časté Problémy

1. **OpenBB není dostupná**
   - Zkontrolujte instalaci: `pip list | grep openbb`
   - Ověřte Python path v `openbb_integration.py`

2. **API klíče nefungují**
   - Ověřte environment variables
   - Zkontrolujte platnost klíčů u poskytovatelů

3. **Pomalé odpovědi**
   - Zkuste jiného poskytovatele dat
   - Snižte množství požadovaných dat

4. **Chybějící data**
   - Zkontrolujte symbol (může být specifický pro poskytovatele)
   - Ověřte dostupnost dat pro zadané období

### Logování

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Detailní logy pro OpenBB operace
logger = logging.getLogger('openbb_integration')
```

## Budoucí Rozšíření

### Plánované Funkce
1. **Real-time Data Streaming** - WebSocket připojení pro live data
2. **Advanced Analytics** - Pokročilé technické indikátory
3. **Custom Indicators** - Vlastní indikátory a strategie
4. **Portfolio Optimization** - Automatická optimalizace portfolia
5. **Risk Management** - Pokročilé risk metriky
6. **Backtesting Integration** - Propojení s backtesting enginem

### Rozšíření Poskytovatelů
- **Bloomberg API** - Institucionální data
- **Refinitiv** - Professional data feeds
- **IEX Cloud** - Alternativní datový zdroj
- **Quandl** - Alternativní a ekonomická data

## Závěr

OpenBB integrace významně rozšiřuje možnosti AI Hedge Fund platformy o pokročilé finanční data a analýzy. Poskytuje jednotné API pro přístup k datům z mnoha zdrojů a umožňuje vytváření sofistikovaných investičních strategií.

Pro více informací o OpenBB Platform navštivte: https://openbb.co/
