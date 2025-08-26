# AI Hedge Fund - Development Guide

**Verze:** 1.5 (Production-ready beta)  
**Poslední aktualizace:** 3. srpna 2025  
**Autor:** AI Hedge Fund Development Team

## 📋 Přehled

Tento guide pokrývá nastavení vývojového prostředí, coding standards, a best practices pro přispívání do AI Hedge Fund projektu. Projekt je ve stavu **Production-ready beta** s identifikovanými problémy, které vyžadují pozornost vývojářů.

**Aktuální stav**: ✅ **Production-ready beta (v1.5)**  
**Vývojové prostředí**: ✅ **Plně funkční**  
**Identifikované problémy**: ⚠️ **1,397 code issues, 13 security issues, 2.9% test coverage**

### 🎯 Co je hotové
- ✅ **17 AI agentů** - všichni plně implementováni a funkční
- ✅ **FastAPI backend** - 36 endpointů, production-ready
- ✅ **React Flow frontend** - drag & drop workflow editor
- ✅ **Multi-LLM podpora** - 6 providerů (OpenAI, Anthropic, Groq, DeepSeek, Google, Ollama)
- ✅ **Docker development** - kompletní containerizace
- ✅ **Database migrations** - Alembic setup

### ⚠️ Prioritní vývojové úkoly
1. **Security fixes** - 13 bezpečnostních problémů
2. **Code quality** - 1,397 code issues k refaktoringu
3. **Testing** - zvýšit coverage z 2.9% na 80%+
4. **Performance** - optimalizace pro produkci

## 🔗 Související dokumentace

- **[📚 Hlavní dokumentace](README.md)** - Kompletní přehled všech dokumentů
- **[🏗️ Architektura](ARCHITECTURE.md)** - Detailní architektura systému
- **[🚀 Deployment](DEPLOYMENT.md)** - Nasazení a produkční prostředí
- **[📡 API Reference](API.md)** - Kompletní API dokumentace
- **[📊 Analýza struktury](DOKUMENTACE_A_STRUKTURA_ANALYZA.md)** - Analýza kódu a struktury

---

## 🛠️ Development Setup

### Předpoklady

- **Python 3.11+** (doporučeno 3.11)
- **Node.js 18+** a npm
- **Poetry** pro Python dependency management
- **Git** pro version control
- **VS Code** nebo jiný editor s Python/TypeScript podporou

### Rychlé nastavení

```bash
# 1. Klonování repozitáře
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund

# 2. Python environment setup
poetry install
poetry shell

# 3. Frontend dependencies
cd app/frontend
npm install
cd ../..

# 4. Environment variables
cp .env.example .env
# Upravte .env s vašimi API klíči

# 5. Databáze setup
cd app/backend
alembic upgrade head
cd ../..

# 6. Spuštění development serverů
# Terminal 1 - Backend
cd app/backend && poetry run uvicorn main:app --reload

# Terminal 2 - Frontend
cd app/frontend && npm run dev
```

---

## 🏗️ Architektura projektu

### Struktura adresářů

```
ai-hedge-fund/
├── src/                      # CLI verze aplikace
│   ├── agents/               # Investment agents
│   ├── data/                 # Data models
│   ├── graph/                # Workflow state management
│   ├── llm/                  # LLM integrations
│   ├── tools/                # External API tools
│   └── utils/                # Utility functions
├── app/                      # Webová aplikace
│   ├── backend/              # FastAPI backend
│   │   ├── database/         # Database layer
│   │   ├── models/           # API schemas
│   │   ├── repositories/     # Data access layer
│   │   ├── routes/           # API endpoints
│   │   └── services/         # Business logic
│   └── frontend/             # React frontend
│       ├── src/
│       │   ├── components/   # React components
│       │   ├── contexts/     # React contexts
│       │   ├── hooks/        # Custom hooks
│       │   ├── services/     # API services
│       │   └── types/        # TypeScript types
├── tests/                    # Test files
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

### Klíčové komponenty

#### 1. Investment Agents
```python
# src/agents/warren_buffett.py
def warren_buffett_agent(state: AgentState, agent_id: str = "warren_buffett_agent") -> Dict[str, Any]:
    """
    Analyzuje akcie pomocí Buffett's principů.
    
    Args:
        state: Current agent state with market data
        agent_id: Unique identifier for this agent
        
    Returns:
        Dictionary s investment signals a reasoning
    """
```

#### 2. Workflow State Management
```python
# src/graph/state.py
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    data: Annotated[dict[str, any], merge_dicts]
    metadata: Annotated[dict[str, any], merge_dicts]
```

#### 3. React Flow Integration
```typescript
// app/frontend/src/components/Flow.tsx
export function Flow() {
  const { nodes, edges, onNodesChange, onEdgesChange } = useFlow();
  
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
    />
  );
}
```

---

## 🎯 Coding Standards

### Python Standards

#### 1. Code Style
```python
# Použijte Black formatter
poetry run black .

# Type hints jsou povinné
def process_data(data: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
    """Process financial data and return metrics."""
    pass

# Docstrings ve Google style
def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio for given returns.
    
    Args:
        returns: Series of investment returns
        risk_free_rate: Risk-free rate for calculation
        
    Returns:
        Sharpe ratio value
        
    Raises:
        ValueError: If returns series is empty
    """
```

#### 2. Error Handling
```python
# Konzistentní error handling pattern
class HedgeFundError(Exception):
    """Base exception for hedge fund operations."""
    pass

class APIKeyError(HedgeFundError):
    """Raised when API key is missing or invalid."""
    pass

def get_market_data(ticker: str) -> Dict[str, Any]:
    """Get market data for ticker."""
    try:
        response = api_client.get(f"/data/{ticker}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise DataFetchError(f"Failed to fetch data for {ticker}: {e}")
```

#### 3. Logging
```python
import logging

logger = logging.getLogger(__name__)

def process_agent_signal(agent_name: str, signal: Dict[str, Any]) -> None:
    """Process agent signal with proper logging."""
    logger.info(f"Processing signal from {agent_name}")
    
    try:
        # Process signal
        result = validate_signal(signal)
        logger.info(f"Signal processed successfully: {result}")
    except ValidationError as e:
        logger.error(f"Signal validation failed for {agent_name}: {e}")
        raise
```

### TypeScript Standards

#### 1. Type Safety
```typescript
// Definujte přesné typy
interface AgentNode {
  id: string;
  type: 'agent' | 'portfolio_manager' | 'risk_manager';
  position: { x: number; y: number };
  data: {
    label: string;
    agentType: string;
    isMultiNode?: boolean;
  };
}

// Použijte union types pro známé hodnoty
type ModelProvider = 'openai' | 'anthropic' | 'groq' | 'deepseek' | 'google';

// Generic types pro reusability
interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}
```

#### 2. React Best Practices
```typescript
// Custom hooks pro logic separation
function useAgentFlow() {
  const [nodes, setNodes] = useState<AgentNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  
  const addAgent = useCallback((agentType: string) => {
    // Add agent logic
  }, []);
  
  return { nodes, edges, addAgent };
}

// Komponenty s proper typing
interface AgentPanelProps {
  agents: Agent[];
  onAgentSelect: (agent: Agent) => void;
  isLoading?: boolean;
}

export function AgentPanel({ agents, onAgentSelect, isLoading = false }: AgentPanelProps) {
  // Component implementation
}
```

---

## 🧪 Testing Strategy

### Test Structure
```
tests/
├── unit/                     # Unit tests
│   ├── test_agents/          # Agent tests
│   ├── test_utils/           # Utility tests
│   └── test_llm/             # LLM tests
├── integration/              # Integration tests
│   ├── test_api/             # API tests
│   └── test_workflow/        # Workflow tests
├── e2e/                      # End-to-end tests
│   └── test_full_workflow/   # Complete workflow tests
└── fixtures/                 # Test data
    └── sample_data/
```

### Unit Testing

#### Python Tests
```python
# tests/unit/test_agents/test_warren_buffett.py
import pytest
from unittest.mock import Mock, patch
from src.agents.warren_buffett import warren_buffett_agent
from src.graph.state import AgentState

class TestWarrenBuffettAgent:
    @pytest.fixture
    def mock_state(self):
        return {
            "data": {
                "tickers": ["AAPL"],
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            },
            "metadata": {
                "model_name": "gpt-4o-mini",
                "model_provider": "openai"
            }
        }
    
    @patch('src.agents.warren_buffett.get_financial_data')
    def test_warren_buffett_agent_success(self, mock_get_data, mock_state):
        # Arrange
        mock_get_data.return_value = {"revenue": 100000, "profit": 20000}
        
        # Act
        result = warren_buffett_agent(mock_state)
        
        # Assert
        assert "AAPL" in result["data"]["analyst_signals"]
        assert result["data"]["analyst_signals"]["AAPL"]["signal"] in ["buy", "sell", "hold"]
        assert 0 <= result["data"]["analyst_signals"]["AAPL"]["confidence"] <= 1
```

#### Frontend Tests
```typescript
// app/frontend/src/components/__tests__/AgentPanel.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentPanel } from '../AgentPanel';

describe('AgentPanel', () => {
  const mockAgents = [
    { id: '1', name: 'Warren Buffett', type: 'value' },
    { id: '2', name: 'Peter Lynch', type: 'growth' }
  ];

  it('renders agent list correctly', () => {
    const onAgentSelect = jest.fn();
    
    render(
      <AgentPanel 
        agents={mockAgents} 
        onAgentSelect={onAgentSelect} 
      />
    );
    
    expect(screen.getByText('Warren Buffett')).toBeInTheDocument();
    expect(screen.getByText('Peter Lynch')).toBeInTheDocument();
  });

  it('calls onAgentSelect when agent is clicked', () => {
    const onAgentSelect = jest.fn();
    
    render(
      <AgentPanel 
        agents={mockAgents} 
        onAgentSelect={onAgentSelect} 
      />
    );
    
    fireEvent.click(screen.getByText('Warren Buffett'));
    expect(onAgentSelect).toHaveBeenCalledWith(mockAgents[0]);
  });
});
```

### Integration Testing

```python
# tests/integration/test_api/test_hedge_fund_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)

class TestHedgeFundEndpoints:
    def test_hedge_fund_run_success(self):
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
        
        response = client.post("/hedge-fund/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
```

### Running Tests

```bash
# Python tests
poetry run pytest tests/ -v

# Frontend tests
cd app/frontend
npm test

# Coverage reports
poetry run pytest --cov=src tests/
npm run test:coverage
```

---

## 🔧 Development Tools

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

### VS Code Configuration

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### Development Scripts

```json
// package.json scripts
{
  "scripts": {
    "dev": "concurrently \"npm run dev:backend\" \"npm run dev:frontend\"",
    "dev:backend": "cd app/backend && poetry run uvicorn main:app --reload",
    "dev:frontend": "cd app/frontend && npm run dev",
    "test": "poetry run pytest && cd app/frontend && npm test",
    "lint": "poetry run flake8 src/ app/backend/ && cd app/frontend && npm run lint",
    "format": "poetry run black src/ app/backend/ && cd app/frontend && npm run format"
  }
}
```

---

## 🚀 Contributing Workflow

### 1. Feature Development

```bash
# 1. Vytvořte feature branch
git checkout -b feature/new-agent-integration

# 2. Implementujte feature
# - Přidejte kód
# - Napište testy
# - Aktualizujte dokumentaci

# 3. Spusťte testy
npm run test

# 4. Commit changes
git add .
git commit -m "feat: add new agent integration"

# 5. Push a create PR
git push origin feature/new-agent-integration
```

### 2. Code Review Process

#### Checklist pro reviewery:
- [ ] Kód následuje coding standards
- [ ] Testy pokrývají novou funkcionalitou
- [ ] Dokumentace je aktualizována
- [ ] Žádné breaking changes bez migrace
- [ ] Performance impact je zvážen
- [ ] Security implications jsou ošetřeny

### 3. Release Process

```bash
# 1. Update version
poetry version patch  # nebo minor/major

# 2. Update CHANGELOG.md
# 3. Create release branch
git checkout -b release/v0.2.0

# 4. Final testing
npm run test:all

# 5. Merge to main
git checkout main
git merge release/v0.2.0

# 6. Tag release
git tag v0.2.0
git push origin v0.2.0
```

---

## 🐛 Debugging

### Backend Debugging

```python
# Použijte debugger
import pdb; pdb.set_trace()

# Nebo VS Code debugger
# launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/app/backend/main.py",
      "console": "integratedTerminal",
      "args": ["--reload"]
    }
  ]
}
```

### Frontend Debugging

```typescript
// React Developer Tools
// Chrome DevTools
// VS Code debugger pro TypeScript

// Debug logging
const DEBUG = process.env.NODE_ENV === 'development';

function debugLog(message: string, data?: any) {
  if (DEBUG) {
    console.log(`[DEBUG] ${message}`, data);
  }
}
```

---

## 📊 Performance Monitoring

### Backend Monitoring

```python
# app/backend/middleware/performance.py
import time
from fastapi import Request

async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.url} took {process_time:.2f}s")
    
    return response
```

### Frontend Performance

```typescript
// Performance monitoring
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric: any) {
  // Send to your analytics service
  console.log(metric);
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

---

## 📞 Podpora

Pro development podporu:
- GitHub Issues: [ai-hedge-fund/issues](https://github.com/virattt/ai-hedge-fund/issues)
- Discussions: [ai-hedge-fund/discussions](https://github.com/virattt/ai-hedge-fund/discussions)
- Documentation: [README.md](../README.md)
