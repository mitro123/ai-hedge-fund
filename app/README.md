# AI Hedge Fund - Webová aplikace 🚀

**Verze:** v1.5 Production-ready Beta  
**Status:** Plně funkční webová aplikace s 17 AI agenty

Kompletní webová aplikace pro AI-řízený hedge fund s intuitivním drag & drop rozhraním pro vytváření investičních workflow. Aplikace AI Hedge Fund je production-ready systém s frontend i backend komponentami, který vám umožňuje spustit AI-řízený hedge fund obchodní systém prostřednictvím webového rozhraní na vašem vlastním počítači.

## 🎯 Aktuální stav (v1.5)

### ✅ Dokončené komponenty:
- **FastAPI Backend** - Production-ready s 36 API endpointy
- **React Flow Frontend** - Plně funkční drag & drop workflow editor
- **17 AI Agentů** - Všichni plně funkční a implementovaní
- **Multi-LLM Podpora** - 6 providerů (OpenAI, Anthropic, Groq, DeepSeek, Google, Ollama)
- **Database Layer** - SQLite/PostgreSQL s Alembic migrations
- **Docker Support** - Kompletní containerizace

### 🔄 V procesu:
- Security improvements (13 identifikovaných issues)
- Test coverage enhancement (aktuálně 2.9%)
- Code quality optimizations

<img width="1692" alt="Screenshot 2025-05-15 at 8 57 56 PM" src="https://github.com/user-attachments/assets/2173fa5b-1029-49dd-8b04-d7583616de1b" />

## Přehled

AI Hedge Fund se skládá z:

- **Backend**: FastAPI aplikace, která poskytuje REST API pro spuštění hedge fund obchodního systému a backtesteru
- **Frontend**: React/Vite aplikace, která nabízí uživatelsky přívětivé rozhraní pro vizualizaci a ovládání operací hedge fondu

## Obsah

- [🚀 Rychlý start (Pro netechnické uživatele)](#-rychlý-start-pro-netechnické-uživatele)
  - [Možnost 1: Použití 1-řádkového shell skriptu (Doporučeno)](#možnost-1-použití-1-řádkového-shell-skriptu-doporučeno)
  - [Možnost 2: Použití npm (Alternativa)](#možnost-2-použití-npm-alternativa)
- [🛠️ Manuální nastavení (Pro vývojáře)](#️-manuální-nastavení-pro-vývojáře)
  - [Předpoklady](#předpoklady)
  - [Instalace](#instalace)
  - [Spuštění aplikace](#spuštění-aplikace)
- [Podrobná dokumentace](#podrobná-dokumentace)
- [Prohlášení o vyloučení odpovědnosti](#prohlášení-o-vyloučení-odpovědnosti)
- [Řešení problémů](#řešení-problémů)

## 🚀 Rychlý start (Pro netechnické uživatele)

**Jednořádkový příkaz pro nastavení a spuštění:**

### Možnost 1: Použití 1-řádkového shell skriptu (Doporučeno)

#### Pro Mac/Linux:
```bash
./run.sh
```

Pokud dostanete chybu "permission denied", nejprve spusťte:
```bash
chmod +x run.sh && ./run.sh
```

Nebo alternativně můžete spustit:
```bash
bash run.sh
```

#### Pro Windows:
```cmd
run.bat
```

### Možnost 2: Použití npm (Alternativa)
```bash
cd app && npm install && npm run setup
```

**To je vše!** Tyto skripty:
1. Zkontrolují požadované závislosti (Node.js, Python, Poetry)
2. Automaticky nainstalují všechny závislosti
3. Spustí frontend i backend služby
4. **Automaticky otevřou váš webový prohlížeč** s aplikací

**Požadavky:**
- [Node.js](https://nodejs.org/) (zahrnuje npm)
- [Python 3](https://python.org/)
- [Poetry](https://python-poetry.org/)

**Po spuštění můžete přistupovat k:**
- Frontend (Webové rozhraní): http://localhost:5173
- Backend API: http://localhost:8000
- API dokumentace: http://localhost:8000/docs

---

## 🛠️ Manuální nastavení (Pro vývojáře)

Pokud preferujete manuální nastavení každé komponenty nebo potřebujete větší kontrolu:

### Předpoklady

- Node.js a npm pro frontend
- Python 3.8+ a Poetry pro backend

### Instalace

1. Klonujte repozitář:
```bash
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund
```

2. Nastavte proměnné prostředí:
```bash
# Vytvořte .env soubor pro vaše API klíče (v kořenovém adresáři)
cp .env.example .env
```

3. Upravte .env soubor pro přidání vašich API klíčů:
```bash
# Pro spuštění LLM hostovaných OpenAI (gpt-4o, gpt-4o-mini, atd.)
OPENAI_API_KEY=váš-openai-api-klíč

# Pro spuštění LLM hostovaných Groq (deepseek, llama3, atd.)
GROQ_API_KEY=váš-groq-api-klíč

# Pro získání finančních dat pro hedge fund
FINANCIAL_DATASETS_API_KEY=váš-financial-datasets-api-klíč
```

4. Nainstalujte Poetry (pokud ještě není nainstalováno):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

5. Nainstalujte závislosti kořenového projektu:
```bash
# Z kořenového adresáře
poetry install
```

6. Nainstalujte závislosti backend aplikace:
```bash
# Přejděte do backend adresáře
cd app/backend
pip install -r requirements.txt  # Pokud existuje soubor requirements.txt
# NEBO
poetry install  # Pokud existuje pyproject.toml v backend adresáři
```

7. Nainstalujte závislosti frontend aplikace:
```bash
cd app/frontend
npm install  # nebo pnpm install nebo yarn install
```

### Spuštění aplikace

1. Spusťte backend server:
```bash
# V jednom terminálu, z backend adresáře
cd app/backend
poetry run uvicorn main:app --reload
```

2. Spusťte frontend aplikaci:
```bash
# V jiném terminálu, z frontend adresáře
cd app/frontend
npm run dev
```

Nyní můžete přistupovat k:
- Frontend aplikace: http://localhost:5173
- Backend API: http://localhost:8000
- API dokumentace: http://localhost:8000/docs

## Podrobná dokumentace

Pro podrobnější informace:
- [Backend dokumentace](./backend/README.md)
- [Frontend dokumentace](./frontend/README.md)

## Prohlášení o vyloučení odpovědnosti

Tento projekt je určen **pouze pro vzdělávací a výzkumné účely**.

- Není určen pro skutečné obchodování nebo investování
- Neposkytuje žádné záruky nebo garance
- Tvůrce nepřebírá odpovědnost za finanční ztráty
- Pro investiční rozhodnutí se poraďte s finančním poradcem

Používáním tohoto softwaru souhlasíte s jeho použitím pouze pro vzdělávací účely.

## Řešení problémů

### Běžné problémy

#### Chyba "Command not found: uvicorn"
Pokud vidíte tuto chybu při spuštění setup skriptu:

```bash
[ERROR] Backend se nepodařilo spustit. Zkontrolujte logy:
Command not found: uvicorn
```

**Řešení:**
1. **Vyčistěte Poetry prostředí:**
   ```bash
   cd app/backend
   poetry env remove --all
   poetry install
   ```

2. **Nebo vynuťte přeinstalaci:**
   ```bash
   cd app/backend
   poetry install --sync
   ```

3. **Ověřte instalaci:**
   ```bash
   cd app/backend
   poetry run python -c "import uvicorn; import fastapi"
   ```

#### Problémy s verzí Python
- **Použijte Python 3.11**: Python 3.13+ může mít problémy s kompatibilitou
- **Zkontrolujte vaši verzi Python:** `python --version`
- **Přepněte verze Python pokud je potřeba** (pomocí pyenv, conda, atd.)

#### Problémy s proměnnými prostředí
- **Ujistěte se, že .env soubor existuje** v kořenovém adresáři projektu
- **Zkopírujte ze šablony:** `cp .env.example .env`
- **Přidejte vaše API klíče** do .env souboru

#### Problémy s oprávněními (Mac/Linux)
Pokud dostanete "permission denied":
```bash
chmod +x run.sh
./run.sh
```

#### Port již používán
Pokud jsou porty 8000 nebo 5173 používány:
- **Ukončete existující procesy:** `pkill -f "uvicorn\|vite"`
- **Nebo použijte jiné porty** úpravou skriptů

### Získání pomoci
- Zkontrolujte [GitHub Issues](https://github.com/virattt/ai-hedge-fund/issues)
- Sledujte aktualizace na [Twitter](https://x.com/virattt)
