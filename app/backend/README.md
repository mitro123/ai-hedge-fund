# AI Hedge Fund - Backend 🚀

**Verze:** v1.5 Production-ready Beta  
**Status:** Plně funkční FastAPI backend s 36 API endpointy

Production-ready backend server pro projekt AI Hedge Fund. Poskytuje kompletní REST API pro interakci se systémem AI Hedge Fund s 17 specializovanými investičními agenty, umožňuje vám spustit hedge fund prostřednictvím webového rozhraní.

## 🎯 Aktuální stav (v1.5)

### ✅ Dokončené komponenty:
- **FastAPI Backend** - Production-ready s 36 API endpointy
- **17 AI Agentů** - Všichni plně funkční a implementovaní
- **Multi-LLM Podpora** - 6 providerů (OpenAI, Anthropic, Groq, DeepSeek, Google, Ollama)
- **Database Layer** - SQLite/PostgreSQL s Alembic migrations
- **API Documentation** - Automatická OpenAPI/Swagger dokumentace
- **Error Handling** - Robustní error handling napříč API

### 🔄 V procesu:
- Security improvements (13 identifikovaných issues)
- Test coverage enhancement (aktuálně 2.9%)
- Code quality optimizations

## Přehled

Tento backend projekt je pokročilá FastAPI aplikace, která slouží jako serverová komponenta systému AI Hedge Fund. Vystavuje 36 endpointů pro spuštění hedge fund obchodního systému, backtesteru a management všech 17 AI agentů.

Backend je plně integrován s React Flow frontend aplikací, která umožňuje uživatelům interakci se systémem AI Hedge Fund prostřednictvím intuitivního drag & drop rozhraní.

## Instalace

### Použití Poetry

1. Klonujte repozitář:
```bash
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund
```

2. Nainstalujte Poetry (pokud ještě není nainstalováno):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Nainstalujte závislosti:
```bash
# Z kořenového adresáře
poetry install
```

4. Nastavte proměnné prostředí:
```bash
# Vytvořte .env soubor pro vaše API klíče (v kořenovém adresáři)
cp .env.example .env
```

5. Upravte .env soubor pro přidání vašich API klíčů:
```bash
# Pro spuštění LLM hostovaných OpenAI (gpt-4o, gpt-4o-mini, atd.)
OPENAI_API_KEY=váš-openai-api-klíč

# Pro spuštění LLM hostovaných Groq (deepseek, llama3, atd.)
GROQ_API_KEY=váš-groq-api-klíč

# Pro získání finančních dat pro hedge fund
FINANCIAL_DATASETS_API_KEY=váš-financial-datasets-api-klíč
```

## Spuštění serveru

Pro spuštění vývojového serveru:

```bash
# Přejděte do backend adresáře
cd app/backend

# Spusťte FastAPI server s uvicorn
poetry run uvicorn main:app --reload
```

Toto spustí FastAPI server s povoleným hot-reloadingem.

API bude dostupné na:
- API Endpoint: http://localhost:8000
- API dokumentace: http://localhost:8000/docs

## 📋 API Endpointy (36 celkem)

### 🤖 Hedge Fund Operations
- `POST /hedge-fund/run`: Spustí AI Hedge Fund se specifikovanými parametry
- `GET /hedge-fund/agents`: Seznam všech 17 dostupných AI agentů
- `POST /hedge-fund/backtest`: Spustí backtesting s historickými daty

### 🔑 API Keys Management
- `GET /api-keys`: Seznam všech API klíčů
- `POST /api-keys`: Vytvoří nový API klíč
- `PUT /api-keys/{key_id}`: Aktualizuje existující API klíč
- `DELETE /api-keys/{key_id}`: Smaže API klíč

### 🔄 Workflow Management
- `GET /flows`: Seznam všech workflow
- `POST /flows`: Vytvoří nový workflow
- `GET /flows/{flow_id}`: Detail konkrétního workflow
- `PUT /flows/{flow_id}`: Aktualizuje workflow
- `DELETE /flows/{flow_id}`: Smaže workflow

### ▶️ Flow Runs
- `GET /flow-runs`: Seznam všech spuštění
- `POST /flow-runs`: Spustí nový workflow
- `GET /flow-runs/{run_id}`: Detail konkrétního spuštění
- `PUT /flow-runs/{run_id}`: Aktualizuje spuštění
- `DELETE /flow-runs/{run_id}`: Zruší spuštění

### 🧠 Language Models
- `GET /language-models`: Seznam dostupných LLM
- `POST /language-models/test`: Test LLM připojení
- `GET /language-models/providers`: Seznam LLM providerů

### 🐋 Ollama Integration
- `GET /ollama/status`: Status Ollama serveru
- `POST /ollama/start`: Spustí Ollama server
- `POST /ollama/stop`: Zastaví Ollama server
- `GET /ollama/models`: Seznam dostupných modelů
- `POST /ollama/models/download`: Stáhne nový model
- `DELETE /ollama/models/{model_name}`: Smaže model

### 💾 Storage & Health
- `GET /storage/files`: Seznam uložených souborů
- `POST /storage/upload`: Nahraje soubor
- `GET /health`: Health check endpoint
- `GET /ping`: Jednoduchý ping endpoint

**Kompletní API dokumentace:** http://localhost:8000/docs

## Struktura projektu

```
app/backend/
├── alembic/                  # Databázové migrace
│   ├── versions/             # Migration soubory
│   └── env.py               # Alembic konfigurace
├── database/                 # Databázová vrstva
│   ├── connection.py         # Databázové připojení
│   └── models.py            # SQLAlchemy modely
├── models/                   # API modely a schémata
│   ├── __init__.py
│   ├── events.py            # Event modely
│   └── schemas.py           # Pydantic schémata
├── repositories/             # Data access layer
│   ├── api_key_repository.py
│   ├── flow_repository.py
│   └── flow_run_repository.py
├── routes/                   # API endpointy
│   ├── __init__.py
│   ├── api_keys.py          # API klíče management
│   ├── flows.py             # Workflow management
│   ├── flow_runs.py         # Spuštění workflow
│   ├── hedge_fund.py        # Hedge fund operace
│   ├── health.py            # Health checks
│   ├── language_models.py   # LLM konfigurace
│   ├── ollama.py            # Ollama integrace
│   └── storage.py           # File storage
├── services/                 # Business logika
│   ├── agent_service.py     # Agent management
│   ├── api_key_service.py   # API klíče služby
│   ├── backtest_service.py  # Backtesting
│   ├── graph.py             # Workflow graph
│   ├── ollama_service.py    # Ollama služby
│   └── portfolio.py         # Portfolio management
├── alembic.ini              # Alembic konfigurace
├── hedge_fund.db            # SQLite databáze
├── main.py                  # FastAPI aplikace
└── migrate_api_keys.py      # Migration utility
```

## Prohlášení o vyloučení odpovědnosti

Tento projekt je určen **pouze pro vzdělávací a výzkumné účely**.

- Není určen pro skutečné obchodování nebo investování
- Neposkytuje žádné záruky nebo garance
- Tvůrce nepřebírá odpovědnost za finanční ztráty
- Pro investiční rozhodnutí se poraďte s finančním poradcem

Používáním tohoto softwaru souhlasíte s jeho použitím pouze pro vzdělávací účely.
