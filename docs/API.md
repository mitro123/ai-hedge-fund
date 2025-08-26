# AI Hedge Fund - API Dokumentace

## 📋 Přehled

Backend API poskytuje RESTful endpointy pro správu AI hedge fund operací, včetně workflow managementu, backtestingu a správy API klíčů. API je ve stavu **Production-ready beta** s kompletní funkcionalitou pro všech 17 AI agentů.

**Aktuální stav**: ✅ **Production-ready beta (v1.5)**  
**Počet endpointů**: 36 aktivních endpointů  
**Base URL:** `http://localhost:8000`  
**API Dokumentace:** `http://localhost:8000/docs` (Swagger UI)  
**Redoc:** `http://localhost:8000/redoc`

### 🎯 Co je hotové
- ✅ **Kompletní FastAPI backend** - všech 36 endpointů funkčních
- ✅ **17 AI agentů** - všichni plně implementováni a funkční
- ✅ **Multi-LLM podpora** - 6 providerů (OpenAI, Anthropic, Groq, DeepSeek, Google, Ollama)
- ✅ **React Flow integrace** - plně funkční drag & drop workflow editor
- ✅ **Databázové operace** - SQLite/PostgreSQL podpora
- ✅ **Docker deployment** - kompletní containerizace

### ⚠️ Identifikované problémy
- **1,397 code issues** - vyžadují refaktoring
- **13 bezpečnostních problémů** - prioritní opravy
- **2.9% test coverage** - potřeba rozšířit testování

---

## 🔐 Autentifikace

API momentálně nepoužívá autentifikaci. API klíče pro externí služby jsou spravovány interně přes databázi.

---

## 📚 API Endpointy

### Health Check

#### `GET /ping`
Základní health check endpoint.

**Response:**
```json
{
  "message": "pong"
}
```

---

### Hedge Fund Operations

#### `POST /hedge-fund/run`
Spustí AI hedge fund workflow s danými parametry. Podporuje všech 17 implementovaných AI agentů.

**Dostupní agenti:**
- **Warren Buffett** - Value investing strategie
- **Ben Graham** - Deep value analysis
- **Charlie Munger** - Quality business focus
- **Peter Lynch** - Growth at reasonable price
- **Phil Fisher** - Growth investing
- **Cathie Wood** - Disruptive innovation
- **Michael Burry** - Contrarian analysis
- **Bill Ackman** - Activist investing
- **Stanley Druckenmiller** - Macro trading
- **Rakesh Jhunjhunwala** - Emerging markets
- **Aswath Damodaran** - Valuation expert
- **Fundamentals Agent** - Fundamental analysis
- **Technical Agent** - Technical analysis
- **Sentiment Agent** - Market sentiment
- **Risk Manager** - Risk assessment
- **Valuation Agent** - Company valuation
- **Portfolio Manager** - Portfolio optimization

**Request Body:**
```json
{
  "portfolio": {
    "AAPL": 1000,
    "GOOGL": 500,
    "MSFT": 750
  },
  "tickers": ["AAPL", "GOOGL", "MSFT"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "model_name": "gpt-4o-mini",
  "model_provider": "openai",
  "graph_nodes": [
    {
      "id": "warren_buffett_abc123",
      "type": "agent",
      "position": {"x": 100, "y": 100},
      "data": {"label": "Warren Buffett"}
    }
  ],
  "graph_edges": [
    {
      "id": "edge1",
      "source": "warren_buffett_abc123",
      "target": "portfolio_manager_def456"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "portfolio_decisions": {
      "AAPL": {
        "action": "buy",
        "quantity": 100,
        "confidence": 0.85,
        "reasoning": "Strong fundamentals and growth prospects"
      }
    },
    "total_return": 0.15,
    "sharpe_ratio": 1.2
  }
}
```

---

### API Keys Management

#### `GET /api-keys`
Získá seznam všech API klíčů.

**Response:**
```json
[
  {
    "id": 1,
    "provider": "openai",
    "key_name": "OPENAI_API_KEY",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### `POST /api-keys`
Vytvoří nový API klíč.

**Request Body:**
```json
{
  "provider": "openai",
  "key_name": "OPENAI_API_KEY",
  "key_value": "sk-...",
  "is_active": true
}
```

#### `PUT /api-keys/{key_id}`
Aktualizuje existující API klíč.

#### `DELETE /api-keys/{key_id}`
Smaže API klíč.

---

### Workflow Management

#### `GET /flows`
Získá seznam všech uložených workflow.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Conservative Strategy",
    "description": "Low-risk investment approach",
    "graph_data": {...},
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### `POST /flows`
Vytvoří nový workflow.

**Request Body:**
```json
{
  "name": "Aggressive Growth",
  "description": "High-growth focused strategy",
  "graph_data": {
    "nodes": [...],
    "edges": [...]
  }
}
```

#### `GET /flows/{flow_id}`
Získá konkrétní workflow.

#### `PUT /flows/{flow_id}`
Aktualizuje workflow.

#### `DELETE /flows/{flow_id}`
Smaže workflow.

---

### Flow Runs

#### `GET /flow-runs`
Získá historii spuštění workflow.

**Query Parameters:**
- `flow_id` (optional): Filtruje podle workflow ID
- `limit` (optional): Počet výsledků (default: 50)
- `offset` (optional): Offset pro paginaci

**Response:**
```json
[
  {
    "id": 1,
    "flow_id": 1,
    "status": "completed",
    "result": {...},
    "started_at": "2024-01-01T10:00:00Z",
    "completed_at": "2024-01-01T10:05:00Z"
  }
]
```

#### `POST /flow-runs`
Spustí workflow.

**Request Body:**
```json
{
  "flow_id": 1,
  "parameters": {
    "tickers": ["AAPL", "GOOGL"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }
}
```

#### `GET /flow-runs/{run_id}`
Získá detaily konkrétního spuštění.

---

### Language Models

#### `GET /language-models`
Získá seznam dostupných LLM modelů.

**Response:**
```json
{
  "openai": [
    {
      "id": "gpt-4o",
      "name": "GPT-4 Omni",
      "provider": "openai",
      "context_length": 128000
    }
  ],
  "anthropic": [
    {
      "id": "claude-3-5-sonnet-20241022",
      "name": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "context_length": 200000
    }
  ]
}
```

---

### Ollama Integration

#### `GET /ollama/models`
Získá seznam lokálních Ollama modelů.

#### `POST /ollama/pull`
Stáhne nový Ollama model.

**Request Body:**
```json
{
  "model_name": "llama3.1:8b"
}
```

#### `DELETE /ollama/models/{model_name}`
Smaže Ollama model.

---

### File Storage

#### `POST /storage/upload`
Nahraje soubor.

**Request:** Multipart form data s file

**Response:**
```json
{
  "filename": "strategy.json",
  "path": "/uploads/strategy.json",
  "size": 1024
}
```

#### `GET /storage/files`
Získá seznam nahraných souborů.

---

## 🔧 Error Handling

API používá standardní HTTP status kódy:

- `200` - OK
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

**Error Response Format:**
```json
{
  "detail": "Error message",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## 📊 Rate Limiting

API momentálně neimplementuje rate limiting, ale je doporučeno pro produkční použití.

---

## 🧪 Testování API

### Pomocí curl

```bash
# Health check
curl -X GET "http://localhost:8000/ping"

# Spuštění hedge fund
curl -X POST "http://localhost:8000/hedge-fund/run" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": {"AAPL": 1000},
    "tickers": ["AAPL"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "model_name": "gpt-4o-mini",
    "model_provider": "openai",
    "graph_nodes": [],
    "graph_edges": []
  }'
```

### Pomocí Python requests

```python
import requests

# Health check
response = requests.get("http://localhost:8000/ping")
print(response.json())

# Spuštění hedge fund
payload = {
    "portfolio": {"AAPL": 1000},
    "tickers": ["AAPL"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "model_name": "gpt-4o-mini",
    "model_provider": "openai",
    "graph_nodes": [],
    "graph_edges": []
}

response = requests.post(
    "http://localhost:8000/hedge-fund/run",
    json=payload
)
print(response.json())
```

---

## 🔄 WebSocket Support

API momentálně nepodporuje WebSocket připojení, ale je plánováno pro real-time updates.

---

## 📝 Changelog

### v1.5 (Production-ready beta) - Srpen 2025
- ✅ **17 AI agentů** - všichni plně implementováni a funkční
- ✅ **36 API endpointů** - kompletní funkcionalita
- ✅ **Multi-LLM podpora** - 6 providerů (OpenAI, Anthropic, Groq, DeepSeek, Google, Ollama)
- ✅ **React Flow integrace** - drag & drop workflow editor
- ✅ **Docker deployment** - kompletní containerizace
- ✅ **Databázové operace** - SQLite/PostgreSQL podpora
- ⚠️ **Identifikované problémy**: 1,397 code issues, 13 security issues, 2.9% test coverage

### v1.0
- Základní API endpointy
- Hedge fund workflow spuštění
- API keys management
- Workflow management
- Ollama integrace

### v0.1.0
- Počáteční implementace
- Základní struktura API

---

## 🚀 Roadmap

### Prioritní úkoly (Q3 2025)
1. **Security fixes** - Oprava 13 bezpečnostních problémů
2. **Code quality** - Refaktoring 1,397 code issues
3. **Testing** - Zvýšení test coverage z 2.9% na 80%+
4. **Production deployment** - Finální příprava pro produkci

### Plánované funkce (Q4 2025)
- Rate limiting implementace
- WebSocket real-time updates
- Advanced authentication
- Performance optimalizace
- Monitoring a logging

---

## 🤝 Přispívání

Pro přispívání k API:

1. Přidejte nové endpointy do `app/backend/routes/`
2. Aktualizujte Pydantic schémata v `app/backend/models/schemas.py`
3. Přidejte testy do `tests/`
4. Aktualizujte tuto dokumentaci

**Aktuální priorita**: Security fixes a code quality improvements

---

## 🔗 Související dokumentace

- **[Přehled dokumentace](./README.md)** - Hlavní dokumentační rozcestník
- **[Architektura systému](./ARCHITECTURE.md)** - Detailní architektura API a backend služeb
- **[Development Guide](./DEVELOPMENT.md)** - Nastavení vývojového prostředí a testování API
- **[Deployment Guide](./DEPLOYMENT.md)** - Nasazení API do produkce

---

## 📞 Podpora

Pro technickou podporu:
- **GitHub Issues**: [ai-hedge-fund/issues](https://github.com/virattt/ai-hedge-fund/issues)
- **Dokumentace**: [README.md](../README.md)
- **API Reference**: Dostupná na `/docs` endpointu při spuštění serveru
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

**Poslední aktualizace**: 3. srpna 2025  
**Verze API**: v1.5 (Production-ready beta)  
**Kompatibilní s**: AI Hedge Fund v1.5+
