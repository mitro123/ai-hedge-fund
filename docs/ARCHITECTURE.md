# AI Hedge Fund - Architektura systému

**Verze:** 2.0  
**Poslední aktualizace:** 3. ledna 2025  
**Autor:** AI Hedge Fund Development Team  
**Aktuální stav:** Production-ready beta (v1.5)

## 🔗 Související dokumentace

- **[📚 Hlavní dokumentace](README.md)** - Kompletní přehled všech dokumentů
- **[📡 API Reference](API.md)** - Kompletní API dokumentace
- **[🚀 Deployment](DEPLOYMENT.md)** - Nasazení a produkční prostředí
- **[💻 Development Guide](DEVELOPMENT.md)** - Vývojové prostředí a standardy
- **[📊 Analýza struktury](DOKUMENTACE_A_STRUKTURA_ANALYZA.md)** - Analýza kódu a struktury

## 📋 Přehled

AI Hedge Fund je komplexní multi-agent systém pro automatizované investiční rozhodování s webovým rozhraním pro drag & drop vytváření investičních workflow.

### 🎯 Aktuální stav implementace
- ✅ **17 funkčních AI agentů** - Kompletně implementováno a testováno
- ✅ **React Flow frontend** - Plně funkční drag & drop editor
- ✅ **FastAPI backend** - Production-ready REST API
- ✅ **Multi-LLM podpora** - 6 LLM providerů integrováno
- ✅ **Docker deployment** - Kompletní containerizace
- ⚠️ **Security hardening** - 13 bezpečnostních problémů identifikováno
- ⚠️ **Test coverage** - Pouze 2.9%, vyžaduje zlepšení

---

## 🏗️ Vysokoúrovňová architektura

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Hedge Fund System                     │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React)          │  Backend (FastAPI)             │
│  ┌─────────────────────┐   │  ┌─────────────────────────┐   │
│  │ React Flow Editor   │   │  │ REST API Endpoints      │   │
│  │ - Drag & Drop UI    │◄──┤  │ - Workflow Management   │   │
│  │ - Agent Management  │   │  │ - Agent Orchestration   │   │
│  │ - Visualization     │   │  │ - Data Processing       │   │
│  └─────────────────────┘   │  └─────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    Core Agent System                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Multi-Agent Investment Framework (LangGraph)            │ │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │ │
│  │ │ Investment  │ │ Technical   │ │ Portfolio & Risk    │ │ │
│  │ │ Agents      │ │ Analysts    │ │ Management          │ │ │
│  │ │ (17 agents) │ │ (4 agents)  │ │ (2 agents)          │ │ │
│  │ └─────────────┘ └─────────────┘ └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    External Integrations                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ LLM         │ │ Financial   │ │ Local Models            │ │
│  │ Providers   │ │ Data APIs   │ │ (Ollama)                │ │
│  │ - OpenAI    │ │ - Financial │ │ - Llama                 │ │
│  │ - Anthropic │ │   Datasets  │ │ - Mistral               │ │
│  │ - Groq      │ │ - SEC EDGAR │ │ - Custom Models         │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Klíčové komponenty

### 1. Frontend Layer (React + TypeScript)

#### React Flow Workflow Editor
```typescript
// Hlavní komponenty pro workflow editor
interface WorkflowEditor {
  components: {
    Flow: ReactFlowComponent;           // Hlavní canvas
    NodePalette: AgentPalette;         // Paleta agentů
    PropertyPanel: ConfigPanel;        // Konfigurace uzlů
    ExecutionPanel: RunPanel;          // Spuštění workflow
  };
  
  state: {
    nodes: AgentNode[];                // Uzly workflow
    edges: Connection[];               // Propojení mezi uzly
    execution: ExecutionState;         // Stav spuštění
  };
}
```

#### State Management
```typescript
// Zustand stores pro state management
interface AppState {
  workflow: WorkflowState;             // Stav workflow
  agents: AgentState;                  // Konfigurace agentů
  execution: ExecutionState;           // Stav spuštění
  ui: UIState;                         // UI stav
}

// React Context pro globální stav
const FlowContext = createContext<FlowContextType>();
const NodeContext = createContext<NodeContextType>();
const TabsContext = createContext<TabsContextType>();
```

### 2. Backend Layer (FastAPI + Python)

#### API Layer
```python
# FastAPI aplikace s modulární strukturou
app/backend/
├── main.py                    # FastAPI app instance
├── routes/                    # API endpointy
│   ├── hedge_fund.py         # Hlavní workflow endpointy
│   ├── api_keys.py           # API klíče management
│   ├── flows.py              # Workflow CRUD
│   └── language_models.py    # LLM konfigurace
├── services/                  # Business logika
│   ├── graph.py              # Workflow orchestration
│   ├── agent_service.py      # Agent management
│   └── backtest_service.py   # Backtesting engine
└── repositories/             # Data access layer
    ├── flow_repository.py    # Workflow persistence
    └── api_key_repository.py # API klíče storage
```

#### Database Layer
```python
# SQLAlchemy modely pro persistence
class HedgeFundFlow(Base):
    """Workflow definice."""
    id: int
    name: str
    description: str
    graph_data: JSON              # React Flow graf
    created_at: datetime

class HedgeFundFlowRun(Base):
    """Historie spuštění workflow."""
    id: int
    flow_id: int
    status: ExecutionStatus
    result: JSON                  # Výsledky analýzy
    started_at: datetime
    completed_at: datetime

class ApiKey(Base):
    """API klíče pro externí služby."""
    id: int
    provider: str                 # openai, anthropic, etc.
    key_name: str
    key_value: str (encrypted)
    is_active: bool
```

### 3. Core Agent System (LangGraph)

#### Agent State Management
```python
# Centrální stav pro všechny agenty
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    data: Annotated[dict[str, any], merge_dicts]
    metadata: Annotated[dict[str, any], merge_dicts]

# Data struktura pro agent state
class AgentStateData:
    tickers: List[str]                # Analyzované akcie
    portfolio: Dict[str, float]       # Současné portfolio
    start_date: str                   # Začátek analýzy
    end_date: str                     # Konec analýzy
    analyst_signals: Dict[str, Any]   # Signály od agentů
```

#### Investment Agents
```python
# 17 investičních agentů s různými strategiemi
INVESTMENT_AGENTS = {
    # Value Investors
    "warren_buffett": BuffettAgent,      # Value investing
    "ben_graham": GrahamAgent,           # Deep value
    "charlie_munger": MungerAgent,       # Quality focus
    
    # Growth Investors  
    "peter_lynch": LynchAgent,           # Growth at reasonable price
    "cathie_wood": WoodAgent,            # Disruptive innovation
    "phil_fisher": FisherAgent,          # Growth investing
    
    # Hedge Fund Managers
    "bill_ackman": AckmanAgent,          # Activist investing
    "michael_burry": BurryAgent,         # Contrarian value
    "stanley_druckenmiller": DruckenAgent, # Macro trading
    
    # International Investors
    "rakesh_jhunjhunwala": JhunjhunAgent, # Indian markets
    "aswath_damodaran": DamodaranAgent,   # Valuation expert
    
    # Technical & Fundamental Analysts
    "technicals": TechnicalAgent,         # Technical analysis
    "fundamentals": FundamentalAgent,     # Fundamental analysis
    "sentiment": SentimentAgent,          # Market sentiment
    "valuation": ValuationAgent,          # Valuation models
    
    # Risk & Portfolio Management
    "risk_manager": RiskAgent,            # Risk assessment
    "portfolio_manager": PortfolioAgent,  # Portfolio optimization
}
```

#### Workflow Orchestration
```python
# LangGraph workflow pro agent orchestration
def create_graph(graph_nodes: list, graph_edges: list) -> StateGraph:
    """Vytvoří workflow graf z React Flow definice."""
    graph = StateGraph(AgentState)
    
    # Přidání agent uzlů
    for node in graph_nodes:
        agent_func = get_agent_function(node.agent_type)
        graph.add_node(node.id, agent_func)
    
    # Přidání propojení
    for edge in graph_edges:
        graph.add_edge(edge.source, edge.target)
    
    # Nastavení entry a exit pointů
    graph.set_entry_point("start_node")
    graph.add_edge("portfolio_manager", END)
    
    return graph.compile()
```

---

## 🔄 Data Flow

### 1. Workflow Creation Flow
```
User Input → React Flow Editor → Frontend State → API Call → 
Backend Validation → Database Storage → Response → UI Update
```

### 2. Workflow Execution Flow
```
Execution Request → Graph Creation → Agent Orchestration → 
Data Fetching → LLM Processing → Signal Generation → 
Portfolio Decisions → Results Storage → Response → Visualization
```

### 3. Agent Processing Flow
```
Agent Input (State) → Data Validation → External API Calls → 
LLM Analysis → Signal Generation → State Update → Next Agent
```

---

## 🧠 LLM Integration Architecture

### Multi-Provider Support
```python
# Abstraktní LLM interface
class LLMProvider:
    def get_model(self, model_name: str) -> ChatModel:
        """Získá model instance."""
        pass
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validuje API klíč."""
        pass

# Konkrétní implementace
class OpenAIProvider(LLMProvider):
    def get_model(self, model_name: str) -> ChatOpenAI:
        return ChatOpenAI(model=model_name, api_key=self.api_key)

class AnthropicProvider(LLMProvider):
    def get_model(self, model_name: str) -> ChatAnthropic:
        return ChatAnthropic(model=model_name, api_key=self.api_key)
```

### Model Selection Strategy
```python
# Dynamická volba modelu pro každého agenta
def get_agent_model_config(state: AgentState, agent_name: str) -> ChatModel:
    """Získá optimální model pro daného agenta."""
    
    # Priorita: Agent-specific → User preference → Default
    model_config = (
        get_agent_specific_model(agent_name) or
        get_user_preferred_model(state) or
        get_default_model()
    )
    
    return create_model_instance(model_config)
```

---

## 📊 Data Architecture

### External Data Sources
```python
# Financial data integrations
class DataSources:
    financial_datasets: FinancialDatasetsAPI  # Hlavní finanční data
    sec_edgar: SECEdgarAPI                    # SEC filings
    market_data: MarketDataAPI                # Real-time data
    
    def get_comprehensive_data(self, ticker: str) -> CompanyData:
        """Získá kompletní data o společnosti."""
        return {
            "financial_metrics": self.financial_datasets.get_metrics(ticker),
            "sec_filings": self.sec_edgar.get_filings(ticker),
            "market_data": self.market_data.get_current_data(ticker),
            "historical_prices": self.market_data.get_historical(ticker)
        }
```

### Data Processing Pipeline
```python
# ETL pipeline pro finanční data
class DataProcessor:
    def extract(self, ticker: str) -> RawData:
        """Extrakce dat z externích zdrojů."""
        pass
    
    def transform(self, raw_data: RawData) -> ProcessedData:
        """Transformace a čištění dat."""
        pass
    
    def load(self, processed_data: ProcessedData) -> None:
        """Uložení do cache/databáze."""
        pass
```

---

## 🔒 Security Architecture

### API Key Management
```python
# Bezpečné uložení API klíčů
class SecureKeyManager:
    def store_key(self, provider: str, key: str) -> None:
        """Uloží zašifrovaný API klíč."""
        encrypted_key = self.encrypt(key)
        self.db.store(provider, encrypted_key)
    
    def get_key(self, provider: str) -> str:
        """Získá dešifrovaný API klíč."""
        encrypted_key = self.db.get(provider)
        return self.decrypt(encrypted_key)
```

### Request Validation
```python
# Validace a sanitizace vstupů
class RequestValidator:
    def validate_workflow(self, workflow_data: dict) -> bool:
        """Validuje workflow definici."""
        pass
    
    def sanitize_tickers(self, tickers: List[str]) -> List[str]:
        """Sanitizuje ticker symboly."""
        pass
```

---

## ⚡ Performance Architecture

### Caching Strategy
```python
# Multi-level caching
class CacheManager:
    redis_cache: RedisCache        # Fast in-memory cache
    db_cache: DatabaseCache        # Persistent cache
    local_cache: LocalCache        # Process-level cache
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Získá data z cache s fallback strategií."""
        return (
            self.local_cache.get(key) or
            self.redis_cache.get(key) or
            self.db_cache.get(key)
        )
```

### Async Processing
```python
# Asynchronní zpracování pro lepší performance
async def run_graph_async(graph: StateGraph, **kwargs) -> dict:
    """Asynchronní spuštění workflow."""
    loop = asyncio.get_running_loop()
    
    # Spuštění v thread pool pro CPU-intensive operace
    result = await loop.run_in_executor(
        None, 
        lambda: run_graph_sync(graph, **kwargs)
    )
    
    return result
```

---

## 🔧 Deployment Architecture

### Container Strategy
```yaml
# Multi-container deployment
services:
  frontend:
    image: ai-hedge-fund-frontend
    ports: ["5173:5173"]
    
  backend:
    image: ai-hedge-fund-backend  
    ports: ["8000:8000"]
    depends_on: [database, redis]
    
  database:
    image: postgres:15
    volumes: ["postgres_data:/var/lib/postgresql/data"]
    
  redis:
    image: redis:alpine
    volumes: ["redis_data:/data"]
    
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    depends_on: [frontend, backend]
```

### Scaling Strategy
```python
# Horizontální škálování pro high-load scenarios
class LoadBalancer:
    def distribute_requests(self, request: Request) -> str:
        """Distribuuje requesty mezi backend instance."""
        pass
    
    def health_check(self, instance: str) -> bool:
        """Kontroluje zdraví backend instance."""
        pass
```

---

## 📈 Monitoring Architecture

### Application Monitoring
```python
# Monitoring a observability
class MonitoringSystem:
    metrics: PrometheusMetrics      # Application metrics
    logging: StructuredLogging      # Centralized logging
    tracing: DistributedTracing     # Request tracing
    
    def track_agent_performance(self, agent_name: str, duration: float):
        """Sleduje performance jednotlivých agentů."""
        self.metrics.histogram("agent_duration", duration, {"agent": agent_name})
```

### Health Checks
```python
# Comprehensive health monitoring
class HealthChecker:
    def check_database(self) -> HealthStatus:
        """Kontroluje databázové připojení."""
        pass
    
    def check_external_apis(self) -> HealthStatus:
        """Kontroluje dostupnost externích API."""
        pass
    
    def check_llm_providers(self) -> HealthStatus:
        """Kontroluje LLM provider dostupnost."""
        pass
```

---

## 🔮 Future Architecture Considerations

### Planned Enhancements
1. **Real-time Data Streaming** - WebSocket integrace pro live data
2. **Advanced Caching** - Distributed caching s Redis Cluster
3. **Microservices** - Rozdělení na menší, nezávislé služby
4. **Event Sourcing** - Event-driven architektura pro audit trail
5. **ML Pipeline** - Vlastní ML modely pro predikce
6. **Multi-tenancy** - Podpora více uživatelů/organizací

### Scalability Roadmap
```python
# Budoucí architektura pro enterprise scale
class EnterpriseArchitecture:
    api_gateway: APIGateway           # Centrální API gateway
    service_mesh: ServiceMesh         # Inter-service communication
    event_bus: EventBus               # Event-driven messaging
    ml_pipeline: MLPipeline           # Custom ML models
    data_lake: DataLake               # Big data storage
    analytics: AnalyticsEngine        # Advanced analytics
```

---

## 📞 Podpora

Pro architekturní otázky:
- GitHub Issues: [ai-hedge-fund/issues](https://github.com/virattt/ai-hedge-fund/issues)
- Architecture Discussions: [ai-hedge-fund/discussions](https://github.com/virattt/ai-hedge-fund/discussions)
- Documentation: [README.md](../README.md)

---

## 🔗 Související dokumentace

- **[Přehled dokumentace](./README.md)** - Hlavní dokumentační rozcestník
- **[API Dokumentace](./API.md)** - Detailní popis API endpointů a jejich implementace
- **[Development Guide](./DEVELOPMENT.md)** - Vývojové nástroje a architektonické vzory
- **[Deployment Guide](./DEPLOYMENT.md)** - Infrastruktura a deployment strategie

---

**Poslední aktualizace**: 3. srpna 2025  
**Verze architektury**: v2.0  
**Kompatibilní s**: AI Hedge Fund v1.0+
