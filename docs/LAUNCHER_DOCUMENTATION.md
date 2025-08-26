# AI Hedge Fund Launcher - Dokumentace

## Přehled

Profesionální Python launcher pro AI Hedge Fund projekt s pokročilými funkcemi pro monitoring, health checks a správu aplikace.

## Funkce

### 🚀 Hlavní Funkce

1. **Spuštění Webové Aplikace**
   - Automatické spuštění backend (FastAPI) a frontend (Vite) serverů
   - Health checks s timeout kontrolou
   - Real-time monitoring stavu serverů
   - Automatické otevření prohlížeče
   - Graceful shutdown s signal handling

2. **AI Agent CLI**
   - Interaktivní konfigurace parametrů
   - Podpora pro Ollama lokální modely
   - Volitelné zobrazení zdůvodnění

3. **Backtester CLI**
   - Konfigurace tickerů pro backtesting
   - Podpora pro Ollama modely

4. **Pokročilé Testy**
   - Základní testy (Unit + Integration)
   - Performance testy
   - Security testy
   - Stress testy
   - Coverage reporting

### 📊 Monitoring a Diagnostika

5. **Status Serverů**
   - Real-time kontrola stavu backend/frontend
   - Barevné indikátory stavu
   - URL a timestamp informace

6. **Zobrazení Logů**
   - Launcher, Backend, Frontend logy
   - Barevné zvýraznění podle typu (ERROR, WARNING, INFO)
   - Zobrazení posledních 50 řádků

7. **Restart Serverů**
   - Graceful shutdown stávajících procesů
   - Automatické spuštění nových instancí

### 🔧 Správa Prostředí

8. **Instalace Závislostí**
   - Poetry pro Python balíčky
   - npm pro Node.js balíčky
   - Progress indikátory

9. **Kontrola Prostředí**
   - Python 3.11+ verze
   - Poetry, Node.js, npm dostupnost

## Technické Detaily

### Health Check Systém

```python
def check_backend_health():
    """Zkontroluje zdraví backend serveru."""
    try:
        response = requests.get(
            f"http://{CONFIG['backend']['host']}:{CONFIG['backend']['port']}{CONFIG['backend']['health_endpoint']}", 
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Backend health check failed: {e}")
        return False
```

### Konfigurace

```python
CONFIG = {
    "backend": {
        "host": "127.0.0.1",
        "port": 8000,
        "health_endpoint": "/health"
    },
    "frontend": {
        "host": "localhost", 
        "port": 5173
    },
    "monitoring": {
        "health_check_interval": 10,
        "startup_timeout": 60
    }
}
```

### Real-time Monitoring

- Používá Rich Live display pro real-time aktualizace
- Monitoring běží v separátním vlákně
- Automatické obnovování každých 10 sekund
- Barevné indikátory stavu (zelená/červená)

### Graceful Shutdown

- Signal handling pro SIGINT a SIGTERM
- Postupné ukončování procesů s timeout
- Force kill jako fallback
- Cleanup globálních proměnných

## Použití

### Základní Spuštění

```bash
python launcher.py
```

### Interaktivní Menu

Launcher nabízí intuitivní menu s následujícími možnostmi:

1. 🚀 Spustit kompletní webovou aplikaci (Backend + Frontend)
2. 🤖 Spustit AI agenta (CLI režim)
3. 📊 Spustit Backtester (CLI režim)
4. 🧪 Spustit pokročilé testy (Advanced Test Suite)
5. 📋 Zobrazit status serverů
6. 📝 Zobrazit logy aplikace
7. 🔄 Restart serverů
8. 📦 Nainstalovat/aktualizovat všechny závislosti
9. 🔍 Zkontrolovat prostředí
10. ❌ Ukončit

### Klávesové Zkratky

- **Ctrl+C**: Graceful shutdown při běhu serverů
- **q + Enter**: Ukončení při běhu serverů
- **Enter**: Návrat do hlavního menu

## Logování

### Log Soubory

- `logs/launcher.log` - Launcher aktivity
- `logs/backend.log` - Backend server výstup
- `logs/frontend.log` - Frontend server výstup

### Log Formát

```
2024-01-15 10:30:45,123 - INFO - Server started successfully
2024-01-15 10:30:46,456 - WARNING - Health check timeout
2024-01-15 10:30:47,789 - ERROR - Connection failed
```

## Požadavky

### Systémové Požadavky

- Python 3.11+
- Poetry (Python dependency management)
- Node.js 18+
- npm (Node.js package manager)

### Python Balíčky

```python
# Povinné
questionary  # Interaktivní prompts
rich        # Rich terminal output
psutil      # System monitoring
requests    # HTTP requests

# Volitelné (pro pokročilé funkce)
pytest      # Testing framework
coverage    # Code coverage
```

## Architektura

### Struktura Kódu

```
launcher.py
├── Globální konfigurace a proměnné
├── Pomocné funkce
│   ├── print_panel()
│   ├── command_exists()
│   └── run_command()
├── Health Check funkce
│   ├── check_backend_health()
│   ├── check_frontend_health()
│   └── wait_for_server_startup()
├── Monitoring funkce
│   ├── monitor_servers()
│   ├── stop_monitoring()
│   └── graceful_shutdown()
├── Hlavní funkce
│   ├── start_web_app()
│   ├── run_agent()
│   ├── run_backtester()
│   └── run_advanced_tests()
├── Diagnostické funkce
│   ├── show_server_status()
│   ├── show_logs()
│   └── restart_servers()
├── Správa prostředí
│   ├── check_prerequisites()
│   └── install_dependencies()
└── main_menu()
```

### Threading Model

- **Hlavní vlákno**: UI a user interaction
- **Monitoring vlákno**: Real-time server monitoring (daemon)
- **Subprocess**: Backend a Frontend servery

### Error Handling

- Try-catch bloky pro všechny kritické operace
- Graceful degradation při chybějících závislostech
- Detailní error reporting s traceback
- Automatické cleanup při chybách

## Rozšíření

### Přidání Nové Funkce

1. Vytvořte novou funkci v launcher.py
2. Přidejte volbu do `main_menu()` choices
3. Přidejte handling do `main_menu()` if-elif bloku
4. Aktualizujte dokumentaci

### Konfigurace

Upravte `CONFIG` dictionary pro změnu:
- Portů serverů
- Health check intervalů
- Timeout hodnot
- Endpoint cest

## Troubleshooting

### Časté Problémy

1. **"Chyba: Potřebné knihovny nejsou nainstalovány"**
   - Řešení: `pip install questionary rich psutil requests`

2. **"Backend server se nepodařilo spustit"**
   - Zkontrolujte port 8000 dostupnost
   - Ověřte Poetry instalaci
   - Zkontrolujte backend logy

3. **"Frontend server se nepodařilo spustit"**
   - Zkontrolujte port 5173 dostupnost
   - Ověřte npm instalaci
   - Zkontrolujte frontend logy

4. **Health Check Selhání**
   - Zkontrolujte síťové připojení
   - Ověřte firewall nastavení
   - Zkontrolujte server logy

### Debug Režim

Pro detailní debugging:

1. Nastavte logging level na DEBUG
2. Zkontrolujte log soubory
3. Použijte verbose režim v testech
4. Zkontrolujte process status

## Bezpečnost

### Bezpečnostní Opatření

- Localhost binding pro servery
- Timeout pro všechny síťové operace
- Graceful shutdown pro zabránění data corruption
- Log rotation pro zabránění disk space issues

### Doporučení

- Spouštějte pouze v trusted prostředí
- Pravidelně aktualizujte závislosti
- Monitorujte log soubory
- Používejte firewall pro production

## Performance

### Optimalizace

- Asynchronní monitoring v separátním vlákně
- Lazy loading pro volitelné závislosti
- Efficient subprocess management
- Memory-conscious log handling

### Metriky

- Startup time: ~3-5 sekund
- Memory usage: ~50-100MB
- CPU usage: <5% při monitoring
- Disk usage: Minimální (pouze logy)

## Changelog

### v1.0.0 (2024-01-15)

- ✅ Základní launcher funkcionalita
- ✅ Health check systém
- ✅ Real-time monitoring
- ✅ Graceful shutdown
- ✅ Pokročilé testování
- ✅ Log management
- ✅ Server restart funkcionalita
- ✅ Rich UI s progress indikátory
- ✅ Automatické otevření prohlížeče
- ✅ Signal handling
- ✅ Comprehensive error handling

## Licence

Součást AI Hedge Fund projektu. Viz hlavní LICENSE soubor.
