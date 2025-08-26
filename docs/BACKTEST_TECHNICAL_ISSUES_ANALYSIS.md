# Analýza technických problémů v Backtesteru

## 🔍 Identifikované problémy z analýzy kódu a screenshotu

### 1. **KRITICKÝ PROBLÉM: Nekompatibilita s MT5 integrací**
- Backtester používá pouze stock data API (get_prices, get_price_data)
- **CHYBÍ**: Integrace s MetaTrader 5 pro forex/commodities data
- **DŮSLEDEK**: Nemůže testovat TSLA s forex/commodities strategiemi

### 2. **Problém s parsing výsledků agentů**
```python
# V run_hedge_fund():
return {
    "decisions": parse_hedge_fund_response(final_state["messages"][-1].content),
    "analyst_signals": final_state["data"]["analyst_signals"],
}

# V backtesteru:
decisions = output["decisions"]  # Může být None pokud parsing selže!
```
**PROBLÉM**: Pokud `parse_hedge_fund_response()` vrátí `None`, backtest crashne

### 3. **Chybějící error handling pro trading decisions**
```python
# Současný kód:
for ticker in self.tickers:
    decision = decisions.get(ticker, {"action": "hold", "quantity": 0})
    action, quantity = decision.get("action", "hold"), decision.get("quantity", 0)
```
**PROBLÉM**: Pokud `decisions` je `None`, `.get()` selže

### 4. **Nekonzistentní data struktura**
- Backtester očekává `decisions[ticker] = {"action": "buy", "quantity": 100}`
- Agenti mohou vracet různé formáty nebo chybové stavy

### 5. **Chybějící validace vstupních dat**
- Žádná kontrola, zda ticker existuje v daném období
- Žádná kontrola dostupnosti dat pro celé období
- Chybí fallback pro chybějící price data

### 6. **Performance problémy**
- Pre-fetch dat je neefektivní pro velké období
- Opakované API volání i přes cache
- Žádná optimalizace pro forex/commodities data

### 7. **Problém s timeframe synchronizací**
```python
# Backtester používá business days:
dates = pd.date_range(self.start_date, self.end_date, freq="B")

# Ale forex trhy běží 24/5, commodities mají jiné hodiny
```

### 8. **Chybějící MT5 specific features**
- Žádná podpora pro spread costs
- Žádná podpora pro leverage
- Žádná podpora pro swap rates
- Žádná podpora pro margin requirements

## 🛠️ Konkrétní technické chyby ze screenshotu

### Z obrázku vidím:
1. **Všechny akce jsou HOLD** - agent neprovádí žádné obchody
2. **Množství = 0** - žádné quantity není vypočítáno
3. **Cena $321.20-$332.56** - TSLA stock data, ne forex
4. **Celkový výnos: +0.00%** - žádná aktivita
5. **Processing 2025-07-30 (151/153)** - běží téměř na konci

### Pravděpodobné příčiny:
1. **Agent parsing error**: Decisions se neparsují správně
2. **Data mismatch**: TSLA stock vs forex/commodities strategie
3. **Model response format**: LLM vrací neočekávaný formát

## 🔧 Potřebné opravy

### 1. **Okamžité opravy**
```python
# Robustní error handling:
def safe_parse_decisions(output):
    decisions = output.get("decisions")
    if decisions is None:
        return {ticker: {"action": "hold", "quantity": 0} for ticker in self.tickers}
    return decisions

# Validace decision formátu:
def validate_decision(decision):
    if not isinstance(decision, dict):
        return {"action": "hold", "quantity": 0}
    
    action = decision.get("action", "hold").lower()
    if action not in ["buy", "sell", "hold", "short", "cover"]:
        action = "hold"
    
    quantity = decision.get("quantity", 0)
    if not isinstance(quantity, (int, float)) or quantity < 0:
        quantity = 0
    
    return {"action": action, "quantity": quantity}
```

### 2. **MT5 integrace do backtesteru**
```python
class MT5Backtester(Backtester):
    def __init__(self, use_mt5=False, **kwargs):
        super().__init__(**kwargs)
        self.use_mt5 = use_mt5
        if use_mt5:
            from src.agents.mt5_trading_agent import get_mt5_trading_agent
            self.mt5_agent = get_mt5_trading_agent()
    
    def get_price_data(self, ticker, date):
        if self.use_mt5 and self.is_forex_symbol(ticker):
            return self.mt5_agent.mt5.get_historical_data(ticker, "D1", 1)
        else:
            return super().get_price_data(ticker, date)
```

### 3. **Debug logging**
```python
# Přidat do backtesteru:
def debug_agent_output(self, output, current_date):
    print(f"\n=== DEBUG {current_date} ===")
    print(f"Raw output: {output}")
    print(f"Decisions: {output.get('decisions')}")
    print(f"Analyst signals: {output.get('analyst_signals')}")
    print("========================\n")
```

### 4. **Forex/Commodities podpora**
```python
def is_forex_symbol(self, symbol):
    forex_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
    return symbol.upper() in forex_pairs

def is_commodity_symbol(self, symbol):
    commodities = ["XAUUSD", "XAGUSD", "XTIUSD", "XBRUSD"]
    return symbol.upper() in commodities
```

## 🚨 Okamžité kroky k opravě

### 1. **Přidat debug output**
```bash
# Spustit backtest s debug informacemi
python src/backtester.py --tickers EURUSD --start-date 2025-01-01 --end-date 2025-01-31 --debug
```

### 2. **Zkontrolovat agent response**
- Přidat print statements do `run_hedge_fund()`
- Ověřit formát LLM odpovědi
- Zkontrolovat JSON parsing

### 3. **Testovat s jednoduchými daty**
- Použít kratší období (1 týden)
- Použít pouze 1 ticker
- Použít pouze 1 analytika

### 4. **Implementovat fallback strategii**
```python
# Pokud agent selže, použít simple moving average strategii
def fallback_strategy(self, ticker, price_data):
    if len(price_data) < 20:
        return {"action": "hold", "quantity": 0}
    
    sma_short = price_data['close'].rolling(5).mean().iloc[-1]
    sma_long = price_data['close'].rolling(20).mean().iloc[-1]
    current_price = price_data['close'].iloc[-1]
    
    if sma_short > sma_long:
        quantity = int(1000 / current_price)  # $1000 worth
        return {"action": "buy", "quantity": quantity}
    elif sma_short < sma_long:
        return {"action": "sell", "quantity": 100}
    else:
        return {"action": "hold", "quantity": 0}
```

## 📊 Doporučené testovací scénáře

### 1. **Minimální test**
```bash
python src/backtester.py --tickers AAPL --start-date 2025-01-15 --end-date 2025-01-20 --initial-capital 10000
```

### 2. **Forex test (po MT5 integraci)**
```bash
python src/backtester.py --tickers EURUSD --start-date 2025-01-01 --end-date 2025-01-31 --use-mt5
```

### 3. **Multi-asset test**
```bash
python src/backtester.py --tickers AAPL,EURUSD,XAUUSD --start-date 2025-01-01 --end-date 2025-01-31
```

## 🎯 Priorita oprav

### **VYSOKÁ PRIORITA** (okamžitě)
1. ✅ Error handling pro None decisions
2. ✅ Debug logging pro agent output
3. ✅ Validace decision formátu
4. ✅ Fallback strategie

### **STŘEDNÍ PRIORITA** (tento týden)
1. 🔄 MT5 integrace do backtesteru
2. 🔄 Forex/commodities data podpora
3. 🔄 Spread/commission modeling
4. 🔄 Performance optimalizace

### **NÍZKÁ PRIORITA** (příští týden)
1. ⏳ Advanced risk metrics
2. ⏳ Multi-timeframe support
3. ⏳ Portfolio rebalancing
4. ⏳ Benchmark comparison

Hlavní problém je v **nekompatibilitě mezi stock-focused backtesterem a forex/commodities agenty**. Backtester potřebuje MT5 integraci pro správné testování trading strategií.
