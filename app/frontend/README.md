# AI Hedge Fund - Frontend 🎨

**Verze:** v1.5 Production-ready Beta  
**Status:** Plně funkční React Flow aplikace s drag & drop editorem

Moderní React aplikace s pokročilým drag & drop workflow editorem pro vytváření a správu AI investičních strategií s 17 specializovanými investičními agenty.

## 🎯 Aktuální stav (v1.5)

### ✅ Dokončené komponenty:
- **React Flow Frontend** - Plně funkční drag & drop workflow editor
- **17 AI Agentů** - Všichni dostupní v UI s drag & drop funkcionalitou
- **Multi-LLM UI** - Rozhraní pro 6 LLM providerů
- **Real-time Integration** - Živé propojení s FastAPI backendem
- **Responsive Design** - Optimalizováno pro desktop i mobile
- **Type Safety** - Kompletní TypeScript implementace

### 🔄 V procesu:
- UI/UX improvements
- Performance optimizations
- Additional workflow features

## 🚀 Přehled

Frontend aplikace poskytuje intuitivní webové rozhraní pro:
- **Drag & Drop Workflow Editor** - Vizuální vytváření investičních pipeline s React Flow
- **Multi-Agent Management** - Správa všech 17 investičních agentů
- **Real-time Backtesting** - Okamžité testování strategií s live výsledky
- **Portfolio Visualization** - Grafické zobrazení výsledků a metrik
- **API Keys Management** - Bezpečná správa přístupových klíčů pro LLM
- **Multi-LLM Support** - UI pro všech 6 podporovaných LLM providerů

## 🛠️ Technologie

### Core Framework
- **React 18** - Moderní UI framework s concurrent features
- **TypeScript** - Type-safe development pro robustní kód
- **Vite** - Rychlý build tool a dev server s HMR

### UI & Styling
- **React Flow** - Pokročilý drag & drop workflow editor
- **Tailwind CSS** - Utility-first CSS framework
- **Shadcn/ui** - Moderní komponenty UI knihovna
- **Lucide React** - Ikony pro konzistentní design

### State Management
- **Zustand** - Lightweight state management
- **React Query** - Server state management a caching
- **Context API** - Local component state management

### Development Tools
- **ESLint** - Code linting pro kvalitní kód
- **Prettier** - Code formatting
- **PostCSS** - CSS processing

## 📁 Struktura projektu

```
app/frontend/
├── public/                   # Statické soubory
├── src/
│   ├── components/           # React komponenty
│   │   ├── custom-controls.tsx
│   │   ├── Flow.tsx         # Hlavní React Flow komponenta
│   │   ├── Layout.tsx       # Layout wrapper
│   │   ├── layout/          # Layout komponenty
│   │   ├── panels/          # Side panely (left/right)
│   │   ├── settings/        # Settings komponenty
│   │   ├── tabs/            # Tab management
│   │   └── ui/              # Shadcn/ui komponenty
│   ├── contexts/            # React contexts
│   │   ├── flow-context.tsx
│   │   ├── layout-context.tsx
│   │   ├── node-context.tsx
│   │   └── tabs-context.tsx
│   ├── data/                # Data definice
│   │   ├── agents.ts        # 17 AI agentů definice
│   │   ├── models.ts        # LLM modely
│   │   ├── node-mappings.ts # Node mappings
│   │   └── sidebar-components.ts
│   ├── edges/               # React Flow edges
│   ├── hooks/               # Custom React hooks
│   ├── nodes/               # React Flow nodes
│   ├── services/            # API služby
│   ├── types/               # TypeScript typy
│   └── utils/               # Utility funkce
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

## 🚀 Instalace a spuštění

### Rychlá instalace
```bash
# Instalace závislostí
npm install # nebo `pnpm install` nebo `yarn install`

# Spuštění dev serveru
npm run dev
```

### Dostupné skripty
```bash
npm run dev          # Spustí development server
npm run build        # Vytvoří production build
npm run preview      # Preview production buildu
npm run lint         # Spustí ESLint
npm run lint:fix     # Opraví ESLint chyby
```

### Development server
Po spuštění `npm run dev` bude aplikace dostupná na:
- **Frontend:** http://localhost:5173
- **Hot Module Replacement:** Automatické obnovení při změnách

## 🎨 Klíčové funkce

### Drag & Drop Workflow Editor
- Vizuální editor pro vytváření investičních pipeline
- 17 různých AI agent nodů
- Propojování agentů pomocí edges
- Real-time validace workflow

### Multi-Agent Interface
- UI pro všech 17 investičních agentů
- Konfigurace parametrů pro každého agenta
- Live status monitoring

### LLM Provider Management
- UI pro 6 LLM providerů (OpenAI, Anthropic, Groq, DeepSeek, Google, Ollama)
- API key management
- Model selection interface

### Responsive Design
- Optimalizováno pro desktop i tablet
- Mobile-friendly layout
- Adaptive UI komponenty

## Prohlášení o vyloučení odpovědnosti

Tento projekt je určen **pouze pro vzdělávací a výzkumné účely**.

- Není určen pro skutečné obchodování nebo investování
- Neposkytuje žádné záruky nebo garance
- Tvůrce nepřebírá odpovědnost za finanční ztráty
- Pro investiční rozhodnutí se poraďte s finančním poradcem

Používáním tohoto softwaru souhlasíte s jeho použitím pouze pro vzdělávací účely.
