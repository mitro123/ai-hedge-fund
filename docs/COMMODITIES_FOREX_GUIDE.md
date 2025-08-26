# Komodity a Forex v AI Hedge Fund

Tento návod vám ukáže, jak používat komodity a forex v AI Hedge Fund systému.

## Přehled

AI Hedge Fund nyní podporuje:
- **Komodity**: Zlato, stříbro, ropa, zemní plyn, měď, zemědělské produkty
- **Forex**: Všechny hlavní měnové páry (EUR/USD, GBP/USD, USD/JPY, atd.)
- **Kryptoměny**: Bitcoin, Ethereum a další

## Jak přidat komodity a forex do analýzy

### 1. Konfigurace API klíčů

Před použitím komodit a forex je potřeba nakonfigurovat API klíče v nastavení:

1. Otevřete AI Hedge Fund aplikaci na http://localhost:5173
2. Klikněte na "Settings" (ikona ozubeného kola)
3. V sekci "OpenBB Platform" přidejte potřebné API klíče:

#### Doporučené API klíče pro začátek:
- **Financial Modeling Prep (FMP)**: Pro finanční výkazy a company profily
- **Alpha Vantage**: Pro historická data akcií, forex a komodit  
- **FRED API**: Pro ekonomická data (zdarma od Federal Reserve)
- **Polygon.io**: Pro real-time a historická tržní data

#### Volitelné API klíče pro pokročilé funkce:
- **Tiingo**: Pro akcie, ETF, forex a krypto data
- **Benzinga**: Pro zprávy a market sentiment
- **Intrinio**: Pro pokročilou fundamentální analýzu

**Poznámka**: Většina poskytovatelů nabízí bezplatné tier s omezeními. Pro produkční použití doporučujeme placené plány.

### 2. Použití symbolů

#### Komodity (Futures symboly):
```
GC=F    # Zlato
SI=F    # Stříbro
CL=F    # Ropa (Crude Oil)
NG=F    # Zemní plyn
HG=F    # Měď
ZC=F    # Kukuřice
ZS=F    # Sója
ZW=F    # Pšenice
KC=F    # Káva
SB=F    # Cukr
CT=F    # Bavlna
LBS=F   # Dřevo
```

#### Forex (Měnové páry):
```
EURUSD=X    # EUR/USD
GBPUSD=X    # GBP/USD
USDJPY=X    # USD/JPY
USDCHF=X    # USD/CHF
AUDUSD=X    # AUD/USD
USDCAD=X    # USD/CAD
NZDUSD=X    # NZD/USD
```

#### Kryptoměny:
```
BTC-USD     # Bitcoin
ETH-USD     # Ethereum
ADA-USD     # Cardano
```

### 2. Přidání do frontendu

Ve frontend aplikaci můžete přidat tyto symboly do pole "Tickers":

1. Otevřete AI Hedge Fund aplikaci na http://localhost:5173
2. V poli "Tickers" přidejte symboly oddělené čárkami:
   ```
   AAPL,MSFT,GC=F,EURUSD=X,BTC-USD
   ```
3. Spusťte analýzu

### 3. Programové použití

#### Analýza komodit:
```python
from src.agents.commodities_agent import get_commodities_agent

# Získání agenta
commodities_agent = get_commodities_agent()

# Analýza zlata
gold_analysis = commodities_agent.analyze_commodity("GC=F", state)

# Portfolio komodit
commodity_symbols = ["GC=F", "SI=F", "CL=F", "HG=F"]
portfolio_analysis = commodities_agent.analyze_commodity_portfolio(commodity_symbols, state)

# Přehled trhu komodit
market_overview = commodities_agent.get_commodity_market_overview(state)
```

#### Analýza forex:
```python
from src.agents.forex_agent import get_forex_agent

# Získání agenta
forex_agent = get_forex_agent()

# Analýza EUR/USD
eurusd_analysis = forex_agent.analyze_currency_pair("EURUSD=X", state)

# Portfolio měnových párů
forex_symbols = ["EURUSD=X", "GBPUSD=X", "USDJPY=X"]
portfolio_analysis = forex_agent.analyze_forex_portfolio(forex_symbols, state)

# Přehled forex trhu
market_overview = forex_agent.get_forex_market_overview(state)
```

#### Použití OpenBB integrace:
```python
from src.integrations.openbb_integration import (
    get_commodities_overview,
    get_forex_overview,
    get_commodities_data_convenience,
    get_forex_data_convenience
)

# Přehled hlavních komodit
commodities_data = get_commodities_overview()

# Přehled hlavních měnových párů
forex_data = get_forex_overview()

# Historická data pro zlato
gold_data = get_commodities_data_convenience("GC=F", days=30)

# Historická data pro EUR/USD
eurusd_data = get_forex_data_convenience("EURUSD=X", days=30)
```

## Funkce a možnosti

### Komodity Agent
- **Technická analýza**: Moving averages, volatilita, support/resistance
- **Fundamentální analýza**: Supply/demand faktory, sezónní vzorce
- **Geopolitická analýza**: Vliv geopolitických událostí
- **Ekonomické indikátory**: Inflace, síla dolaru, úrokové sazby
- **Sektorová diverzifikace**: Drahé kovy, energie, zemědělství, průmyslové kovy

### Forex Agent
- **Technická analýza**: RSI, moving averages, chart patterns
- **Fundamentální analýza**: Úrokové diferenciály, ekonomický růst
- **Centrální banky**: Měnová politika, forward guidance
- **Ekonomická data**: GDP, zaměstnanost, inflace, PMI
- **Geopolitické faktory**: Politické události, obchodní vztahy
- **Měnová síla**: Analýza síly jednotlivých měn

### OpenBB Integrace
- **Historická data**: OHLCV data pro všechny asset třídy
- **Ekonomická data**: FRED ekonomické indikátory
- **Zprávy**: Market news a sentiment analýza
- **Finanční výkazy**: Pro akcie a ETF
- **Opce**: Options chains a volatilita

## Příklady portfolií

### Diverzifikované portfolio:
```
# Akcie
AAPL,MSFT,GOOGL,TSLA

# Komodity
GC=F,CL=F,HG=F

# Forex
EURUSD=X,GBPUSD=X

# Krypto
BTC-USD,ETH-USD
```

### Komoditní portfolio:
```
# Drahé kovy
GC=F,SI=F

# Energie
CL=F,NG=F

# Průmyslové kovy
HG=F

# Zemědělství
ZC=F,ZS=F,ZW=F
```

### Forex portfolio:
```
# Hlavní páry
EURUSD=X,GBPUSD=X,USDJPY=X,USDCHF=X

# Komoditní měny
AUDUSD=X,USDCAD=X,NZDUSD=X

# Cross páry
EURGBP=X,EURJPY=X,GBPJPY=X
```

## Výhody použití komodit a forex

### Diverzifikace
- **Nízká korelace**: Komodity a forex často mají nízkou korelaci s akciemi
- **Inflační ochrana**: Komodity poskytují ochranu proti inflaci
- **Měnové hedging**: Forex umožňuje hedging měnového rizika

### Obchodní příležitosti
- **24/5 obchodování**: Forex trhy jsou otevřené 24 hodin denně
- **Vysoká likvidita**: Hlavní měnové páry mají vysokou likviditu
- **Leverage**: Možnost použití pákového efektu

### Makroekonomická analýza
- **Ekonomické cykly**: Komodity reagují na ekonomické cykly
- **Měnová politika**: Forex reaguje na změny úrokových sazeb
- **Geopolitické události**: Oba trhy reagují na geopolitické napětí

## Rizika a upozornění

### Vysoká volatilita
- Komodity a forex mohou být velmi volatilní
- Důležité je správné řízení rizika

### Leverage riziko
- Pákový efekt může zvýšit jak zisky, tak ztráty
- Používejte konzervativní pozice

### Makroekonomické faktory
- Silný vliv centrálních bank a ekonomických dat
- Sledujte ekonomický kalendář

## Doporučení

1. **Začněte malými pozicemi** při testování nových asset tříd
2. **Diverzifikujte** napříč různými sektory a měnami
3. **Sledujte ekonomický kalendář** pro důležité události
4. **Používejte stop-loss** pro řízení rizika
5. **Kombinujte technickou a fundamentální analýzu**

## Další zdroje

- [OpenBB Platform Documentation](https://docs.openbb.co/)
- [Forex Factory Economic Calendar](https://www.forexfactory.com/calendar)
- [Investing.com Commodities](https://www.investing.com/commodities/)
- [TradingView Charts](https://www.tradingview.com/)

---

Pro více informací nebo pomoc s implementací kontaktujte vývojový tým.
