# 📊 Backtest Visualization & Advanced Metrics Guide

## 🎯 Přehled nových funkcí

Backtester byl rozšířen o pokročilé vizualizace a komplexní metriky pro detailní analýzu trading performance. Nyní můžete vidět přesně kde a kdy AI agent nakupoval/prodával a analyzovat výkonnost v reálném čase.

## 🚀 Rychlý start

### 1. **Instalace požadovaných balíčků**
```bash
# Automatická instalace
python scripts/install_visualization_packages.py

# Nebo manuálně
pip install plotly>=5.0.0 seaborn>=0.11.0 kaleido>=0.2.1
```

### 2. **Spuštění backtesteru s vizualizacemi**
```bash
# Základní backtest
python src/backtester.py --tickers AAPL --start-date 2025-01-01 --end-date 2025-01-31

# Po dokončení backtesteru se zobrazí dotaz:
# "Would you like to see interactive charts and advanced metrics? (Y/n)"
# Odpovězte 'Y' pro zobrazení interaktivních grafů
```

## 📈 Dostupné vizualizace

### 1. **Interactive Trading Dashboard**
**Funkce:** `backtester.create_interactive_charts()`

**Obsahuje 4 panely:**

#### 📊 **Panel 1: Price Chart with Trades**
- **Cenový graf** pro každý ticker
- **Zelené trojúhelníky ↗** = BUY obchody
- **Červené trojúhelníky ↘** = SELL obchody
- **Hover informace**: Datum, cena, množství
- **Interaktivní**: Zoom, pan, toggle legendy

#### 💰 **Panel 2: Portfolio Value**
- **Modrá křivka**: Hodnota portfolia v čase
- **Šedá čárkovaná**: Počáteční kapitál (benchmark)
- **Fill area**: Vizuální reprezentace růstu/poklesu

#### 📊 **Panel 3: Daily Returns**
- **Oranžová křivka**: Denní výnosy v %
- **Nulová linie**: Reference pro pozitivní/negativní dny
- **Volatilita**: Vizuální reprezentace rizika

#### 🔻 **Panel 4: Drawdown**
- **Červená křivka**: Pokles z maxima v %
- **Fill area**: Underwater periods
- **Maximum drawdown**: Nejhorší období

### 2. **Performance Metrics Dashboard**
**Funkce:** `backtester.create_performance_metrics_dashboard()`

**Obsahuje 6 analytických panelů:**

#### 📊 **Panel 1: Return Distribution**
- **Histogram**: Distribuce denních výnosů
- **Normalita**: Vizuální kontrola normálního rozdělení
- **Skewness & Kurtosis**: Asymetrie a špičatost

#### 📈 **Panel 2: Rolling Sharpe Ratio**
- **30-denní klouzavý Sharpe ratio**
- **Trend**: Zlepšování/zhoršování risk-adjusted returns
- **Stabilita**: Konzistence výkonnosti

#### 🔥 **Panel 3: Monthly Returns Heatmap**
- **Barevná mapa**: Měsíční výnosy
- **Zelená**: Pozitivní měsíce
- **Červená**: Negativní měsíce
- **Sezónnost**: Identifikace vzorců

#### 🎯 **Panel 4: Risk-Return Scatter**
- **Čtvrtletní analýza**: Risk vs Return
- **Optimální kvadrant**: Vysoký return, nízké riziko
- **Konzistence**: Stabilita napříč obdobími

#### 🌊 **Panel 5: Underwater Plot**
- **Detailní drawdown analýza**
- **Recovery periods**: Doba návratu k maximu
- **Depth & Duration**: Hloubka a délka poklesů

#### 📋 **Panel 6: Trade Analysis**
- **Celkový počet obchodů**
- **Buy vs Sell ratio**
- **Průměrná velikost obchodu**
- **Trading frequency**

## 📊 Rozšířené metriky

### **Return Metrics**
- **Total Return (%)**: Celkový výnos
- **Best Day (%)**: Nejlepší den
- **Worst Day (%)**: Nejhorší den

### **Risk Metrics**
- **Annualized Volatility (%)**: Roční volatilita
- **Maximum Drawdown (%)**: Maximální pokles
- **VaR 95% (%)**: Value at Risk (95% confidence)
- **Expected Shortfall 95% (%)**: Průměrná ztráta v nejhorších 5%

### **Risk-Adjusted Ratios**
- **Sharpe Ratio**: Risk-adjusted return
- **Sortino Ratio**: Downside risk-adjusted return
- **Calmar Ratio**: Return/Max Drawdown ratio

### **Other Metrics**
- **Win Rate (%)**: Procento ziskových dní
- **Win/Loss Ratio**: Poměr průměrného zisku/ztráty
- **Max Consecutive Wins/Losses**: Nejdelší série

## 🔧 Technické detaily

### **Trade Tracking**
```python
# Automatické sledování obchodů
def track_trade(self, date, ticker, action, quantity, price):
    if quantity > 0:
        self.trades_history.append({
            'date': date,
            'ticker': ticker,
            'action': action,
            'quantity': quantity,
            'price': price
        })
```

### **Price History**
```python
# Sledování cenové historie
def track_price(self, date, ticker, price):
    if ticker not in self.price_history:
        self.price_history[ticker] = []
    
    self.price_history[ticker].append({
        'date': date,
        'price': price
    })
```

### **Error Handling**
```python
# Robustní zpracování chyb
try:
    backtester.create_interactive_charts()
    backtester.create_performance_metrics_dashboard()
except ImportError as e:
    print("Warning: Interactive charts require additional packages.")
    print("To install: pip install plotly seaborn")
except Exception as e:
    print(f"Error creating charts: {e}")
```

## 🎨 Customizace

### **Barevné schéma**
```python
# Plotly kvalitativní paleta
colors = px.colors.qualitative.Set1

# Custom barvy pro trade markery
buy_color = 'green'
sell_color = 'red'
portfolio_color = 'blue'
```

### **Chart rozměry**
```python
# Hlavní dashboard
fig.update_layout(
    title='Backtest Analysis Dashboard',
    height=1200,  # Upravitelná výška
    showlegend=True,
    hovermode='x unified'
)

# Metrics dashboard
fig.update_layout(
    title='Performance Metrics Dashboard',
    height=800,   # Kompaktnější
    showlegend=False
)
```

## 🚨 Troubleshooting

### **Problém: Import Error**
```bash
# Chyba: ModuleNotFoundError: No module named 'plotly'
# Řešení:
pip install plotly seaborn kaleido

# Nebo použijte instalační skript:
python scripts/install_visualization_packages.py
```

### **Problém: Prázdné grafy**
```python
# Příčina: Žádné obchody nebo data
# Kontrola:
if not self.trades_history:
    print("No trades executed - check agent decisions")

if not self.portfolio_values:
    print("No portfolio data - run backtest first")
```

### **Problém: Pomalé vykreslování**
```python
# Optimalizace pro velké datasety
# Redukce datových bodů pro rychlejší rendering
if len(price_data) > 1000:
    price_data = price_data.iloc[::10]  # Každý 10. bod
```

## 📋 Příklady použití

### **1. Rychlá analýza AAPL**
```bash
python src/backtester.py --tickers AAPL --start-date 2025-01-01 --end-date 2025-01-31 --initial-capital 50000
# Odpovězte 'Y' na dotaz o vizualizacích
```

### **2. Multi-ticker analýza**
```bash
python src/backtester.py --tickers AAPL,MSFT,GOOGL --start-date 2024-12-01 --end-date 2025-01-31 --initial-capital 100000
```

### **3. Forex backtest (s MT5)**
```bash
python src/backtester.py --tickers EURUSD --start-date 2025-01-01 --end-date 2025-01-31 --initial-capital 10000
```

### **4. Programmatic použití**
```python
from src.backtester import Backtester
from src.main import run_hedge_fund

# Vytvoření backtesteru
backtester = Backtester(
    agent=run_hedge_fund,
    tickers=['AAPL'],
    start_date='2025-01-01',
    end_date='2025-01-31',
    initial_capital=50000
)

# Spuštění
performance = backtester.run_backtest()
df = backtester.analyze_performance()

# Vizualizace
backtester.create_interactive_charts()
backtester.create_performance_metrics_dashboard()
```

## 🎯 Best Practices

### **1. Optimální období pro testování**
- **Krátké testy**: 1-4 týdny pro rychlou analýzu
- **Střední testy**: 1-3 měsíce pro trend analýzu
- **Dlouhé testy**: 6-12 měsíců pro robustnost

### **2. Interpretace metrik**
- **Sharpe > 1.0**: Dobrá risk-adjusted performance
- **Max Drawdown < 20%**: Přijatelné riziko
- **Win Rate > 50%**: Pozitivní trend
- **Calmar > 0.5**: Dobrý poměr return/risk

### **3. Analýza obchodů**
- **Sledujte clustering**: Příliš mnoho obchodů najednou
- **Kontrolujte timing**: Nákupy na vrcholech, prodeje na dnech
- **Analyzujte velikosti**: Konzistentní vs adaptivní sizing

### **4. Performance monitoring**
- **Rolling metrics**: Sledujte trendy v čase
- **Drawdown periods**: Identifikujte problematická období
- **Return distribution**: Kontrolujte normalitu a outliers

## 🔮 Budoucí rozšíření

### **Plánované funkce:**
1. **Benchmark comparison**: Porovnání s S&P 500, NASDAQ
2. **Sector analysis**: Analýza podle sektorů
3. **Risk attribution**: Dekompozice zdrojů rizika
4. **Monte Carlo simulation**: Stress testing
5. **Live trading integration**: Real-time monitoring
6. **Custom indicators**: RSI, MACD, Bollinger Bands
7. **Portfolio optimization**: Markowitz, Black-Litterman
8. **Alternative data**: Sentiment, news impact

Nové vizualizace poskytují kompletní pohled na trading performance a umožňují identifikovat silné a slabé stránky AI trading strategií v reálném čase.
