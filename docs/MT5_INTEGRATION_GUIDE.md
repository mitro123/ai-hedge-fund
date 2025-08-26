# MetaTrader 5 Integration Guide

## Přehled

AI Hedge Fund systém nyní podporuje live trading přes MetaTrader 5 (MT5) terminál. Tato integrace umožňuje:

- **Live Trading**: Přímé provádění obchodů na finančních trzích
- **AI Analýza**: Kombinace AI analýzy s reálným tradingem
- **Risk Management**: Automatický výpočet velikosti pozic
- **Portfolio Management**: Sledování pozic a výkonnosti

## Instalace a Setup

### 1. Instalace MetaTrader 5 Package

```bash
pip install MetaTrader5
```

### 2. Instalace MetaTrader 5 Terminalu

1. Stáhněte MT5 terminál z [MetaQuotes](https://www.metatrader5.com/)
2. Nainstalujte a spusťte terminál
3. Vytvořte demo nebo live účet u brokera

### 3. Konfigurace Připojení

```python
from src.integrations.metatrader5_integration import MT5Config

config = MT5Config(
    login=12345678,        # Váš trading účet
    password="password",   # Heslo k účtu
    server="Broker-Server" # Server brokera
)
```

## Použití MT5 Integrace

### Základní Připojení

```python
from src.integrations.metatrader5_integration import get_mt5_integration

# Získání MT5 integrace
mt5 = get_mt5_integration()

# Připojení k MT5
success = mt5.connect(
    login=12345678,
    password="password", 
    server="Broker-Server"
)

if success:
    print("Úspěšně připojeno k MT5")
else:
    print("Připojení selhalo")
```

### Získání Informací o Účtu

```python
# Informace o účtu
account_info = mt5.get_account_info()
print(f"Balance: {account_info.balance}")
print(f"Equity: {account_info.equity}")
print(f"Free Margin: {account_info.free_margin}")

# Otevřené pozice
positions = mt5.get_positions()
for pos in positions:
    print(f"Symbol: {pos.symbol}, Volume: {pos.volume}, Profit: {pos.profit}")
```

### Placení Objednávek

```python
from src.integrations.metatrader5_integration import OrderType

# Market order - BUY
result = mt5.place_order(
    symbol="EURUSD",
    order_type=OrderType.BUY,
    volume=0.1,  # 0.1 lot
    sl=1.0950,   # Stop Loss
    tp=1.1050,   # Take Profit
    comment="AI Hedge Fund Trade"
)

if result.success:
    print(f"Order placed successfully: {result.order_id}")
else:
    print(f"Order failed: {result.error_message}")
```

### Historická Data

```python
# Získání historických dat
data = mt5.get_historical_data(
    symbol="EURUSD",
    timeframe="H1",  # 1 hodina
    count=100        # posledních 100 barů
)

print(data.head())
```

## Použití MT5 Trading Agent

### Inicializace Agenta

```python
from src.agents.mt5_trading_agent import get_mt5_trading_agent

# Získání trading agenta
agent = get_mt5_trading_agent()

# Připojení
success = agent.connect(
    login=12345678,
    password="password",
    server="Broker-Server"
)
```

### AI Analýza Trhu

```python
# Analýza konkrétního symbolu
analysis = agent.analyze_market(
    symbol="EURUSD",
    timeframe="H1",
    count=100
)

print("AI Analýza:")
print(analysis['ai_analysis'])
print(f"Aktuální cena: {analysis['current_price']}")
print(f"Změna ceny: {analysis['price_change_percent']:.2f}%")
```

### Automatické Trading Příležitosti

```python
# Analýza více symbolů
symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
opportunities = agent.get_trading_opportunities(symbols)

for opp in opportunities:
    print(f"Symbol: {opp['symbol']}")
    print(f"Doporučení: {opp['recommendation']}")
    print(f"Navrhovaný objem: {opp['suggested_volume']}")
    print("---")
```

### Provedení Obchodu

```python
# Provedení obchodu na základě AI analýzy
result = agent.execute_trade(
    symbol="EURUSD",
    action="BUY",
    volume=0.1,
    stop_loss=1.0950,
    take_profit=1.1050
)

if result.success:
    print(f"Obchod úspěšný: Order ID {result.order_id}")
```

### Portfolio Summary

```python
# Přehled portfolia
summary = agent.get_portfolio_summary()

print("Account Info:")
print(f"Balance: {summary['account']['balance']}")
print(f"Equity: {summary['account']['equity']}")

print("Performance:")
print(f"P&L: {summary['performance']['profit_loss']}")
print(f"P&L %: {summary['performance']['profit_loss_percent']:.2f}%")
```

## Risk Management

### Automatický Výpočet Velikosti Pozice

```python
# Výpočet optimální velikosti pozice
lot_size = agent.calculate_position_size(
    symbol="EURUSD",
    risk_percent=2.0,    # 2% riziko z účtu
    stop_loss_pips=50.0  # 50 pips stop loss
)

print(f"Doporučená velikost pozice: {lot_size} lots")
```

### Uzavření Pozic

```python
# Uzavření konkrétní pozice
positions = mt5.get_positions()
if positions:
    ticket = positions[0].ticket
    result = agent.close_position(ticket)
    
    if result.success:
        print(f"Pozice {ticket} uzavřena")
```

## Podporované Symboly

MT5 integrace podporuje všechny symboly dostupné u vašeho brokera:

- **Forex**: EURUSD, GBPUSD, USDJPY, atd.
- **Indexy**: US30, SPX500, NAS100, atd.
- **Komodity**: XAUUSD (zlato), XTIUSD (ropa), atd.
- **Kryptoměny**: BTCUSD, ETHUSD (pokud broker podporuje)

## Timeframes

Podporované timeframes pro analýzu:

- `M1` - 1 minuta
- `M5` - 5 minut
- `M15` - 15 minut
- `M30` - 30 minut
- `H1` - 1 hodina
- `H4` - 4 hodiny
- `D1` - 1 den
- `W1` - 1 týden
- `MN1` - 1 měsíc

## Bezpečnost a Doporučení

### Demo Trading
- **Vždy začněte s demo účtem** pro testování
- Ověřte všechny funkce před použitím live účtu

### Risk Management
- Nikdy neriskujte více než 1-2% účtu na jeden obchod
- Vždy používejte stop loss
- Diverzifikujte portfolio

### Monitoring
- Pravidelně kontrolujte otevřené pozice
- Sledujte výkonnost a upravte strategie

### API Klíče
- Uchovávejte přihlašovací údaje v bezpečí
- Používejte silná hesla
- Pravidelně měňte hesla

## Troubleshooting

### Časté Problémy

1. **Připojení selhává**
   - Ověřte přihlašovací údaje
   - Zkontrolujte, zda je MT5 terminál spuštěn
   - Ověřte internetové připojení

2. **Symbol není dostupný**
   - Zkontrolujte, zda broker symbol podporuje
   - Ověřte správný název symbolu

3. **Obchod selhal**
   - Zkontrolujte dostupnou marži
   - Ověřte minimální velikost pozice
   - Zkontrolujte trading hodiny

### Logování

```python
import logging

# Zapnutí debug logování
logging.basicConfig(level=logging.DEBUG)
```

## Příklady Použití

### Kompletní Trading Bot

```python
from src.agents.mt5_trading_agent import get_mt5_trading_agent
import time

def run_trading_bot():
    agent = get_mt5_trading_agent()
    
    # Připojení
    if not agent.connect(login=12345678, password="password", server="server"):
        print("Připojení selhalo")
        return
    
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    
    while True:
        try:
            # Analýza příležitostí
            opportunities = agent.get_trading_opportunities(symbols)
            
            for opp in opportunities:
                if opp['recommendation'] in ['BUY', 'SELL']:
                    # Provedení obchodu
                    result = agent.execute_trade(
                        symbol=opp['symbol'],
                        action=opp['recommendation'],
                        volume=opp['suggested_volume']
                    )
                    
                    if result.success:
                        print(f"Obchod proveden: {opp['symbol']} {opp['recommendation']}")
            
            # Čekání 1 hodinu
            time.sleep(3600)
            
        except Exception as e:
            print(f"Chyba: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_trading_bot()
```

## Závěr

MT5 integrace poskytuje výkonné nástroje pro live trading s AI analýzou. Vždy testujte na demo účtu a používejte odpovědné risk management praktiky.

Pro další podporu a dotazy kontaktujte tým AI Hedge Fund.
