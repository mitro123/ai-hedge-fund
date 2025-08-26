# AI Hedge Fund

**Verze:** v1.5 Production-ready Beta  
**Status:** Plně funkční AI-řízený hedge fund s 17 investičními agenty

Toto je pokročilý AI-řízený hedge fund systém využívající 17 specializovaných investičních agentů pro komplexní analýzu a obchodní rozhodnutí. Projekt kombinuje moderní AI technologie s proven investičními strategiemi legendárních investorů. Tento projekt je určen **pouze pro vzdělávací** účely a není určen pro skutečné obchodování nebo investování.

## 📚 Kompletní dokumentace

**➡️ [Přejít na kompletní dokumentaci](docs/README.md)** - Detailní přehled všech funkcí, architektury a nasazení

### Rychlé odkazy:
- **[🏗️ Architektura systému](docs/ARCHITECTURE.md)** - Detailní technická architektura
- **[📋 API Reference](docs/API.md)** - Kompletní API dokumentace (36 endpointů)
- **[🚀 Deployment Guide](docs/DEPLOYMENT.md)** - Docker nasazení a production setup
- **[💻 Development Guide](docs/DEVELOPMENT.md)** - Vývojové prostředí a standardy
- **[🤖 AI Agenti](docs/AGENT_FIX_SUMMARY.md)** - Status všech 17 AI agentů

## 🚀 Rychlý start s Launcherem (Doporučeno)

Pro nejjednodušší způsob, jak spustit celý projekt, použijte interaktivní Python launcher. Tento skript vás provede instalací závislostí a umožní vám spustit webovou aplikaci nebo jednotlivé agenty z přehledného menu.

1.  **Ujistěte se, že máte nainstalovaný Python 3.11+ a Poetry.**
2.  Spusťte launcher:

```bash
python3 launcher.py
```

Launcher se postará o vše ostatní – od kontroly prostředí po spuštění serverů.

## 🎯 Aktuální stav (v1.5)

### ✅ Dokončené komponenty:
- **17 AI Agentů** - Všichni plně funkční a implementovaní
- **FastAPI Backend** - Production-ready s 36 API endpointy
- **React Flow Frontend** - Plně funkční drag & drop workflow editor
- **Multi-LLM Podpora** - 6 providerů (OpenAI, Anthropic, Groq, DeepSeek, Google, Ollama)
- **Docker Deployment** - Kompletní containerizace pro production

### 🔄 V procesu:
- Security fixes (13 identifikovaných issues)
- Test coverage improvement (aktuálně 2.9%)
- Code quality improvements (1,397 identifikovaných issues)

Tento systém využívá několik agentů pracujících společně:

1. Agent Aswath Damodaran - Děkan oceňování, zaměřuje se na příběh, čísla a disciplinované oceňování
2. Agent Ben Graham - Kmotr hodnotového investování, kupuje pouze skryté klenoty s bezpečnostní rezervou
3. Agent Bill Ackman - Aktivistický investor, zaujímá odvážné pozice a prosazuje změny
4. Agent Cathie Wood - Královna růstového investování, věří v sílu inovací a disrupcí
5. Agent Charlie Munger - Partner Warrena Buffetta, kupuje pouze skvělé podniky za férové ceny
6. Agent Michael Burry - Kontrariánský investor z Big Short, který loví hlubokou hodnotu
7. Agent Peter Lynch - Praktický investor, který hledá "desetinásobky" v každodenních podnicích
8. Agent Phil Fisher - Pečlivý růstový investor, který používá hluboký "scuttlebutt" výzkum
9. Agent Rakesh Jhunjhunwala - Velký býk Indie
10. Agent Stanley Druckenmiller - Makro legenda, která loví asymetrické příležitosti s růstovým potenciálem
11. Agent Warren Buffett - Věštec z Omahy, hledá skvělé společnosti za férovou cenu
12. Agent oceňování - Vypočítává vnitřní hodnotu akcie a generuje obchodní signály
13. Agent sentimentu - Analyzuje tržní sentiment a generuje obchodní signály
14. Agent fundamentů - Analyzuje fundamentální data a generuje obchodní signály
15. Agent technické analýzy - Analyzuje technické indikátory a generuje obchodní signály
16. Manažer rizik - Vypočítává rizikové metriky a stanovuje pozice
17. Manažer portfolia - Činí konečná obchodní rozhodnutí a generuje příkazy

<img width="1042" alt="Screenshot 2025-03-22 at 6 19 07 PM" src="https://github.com/user-attachments/assets/cbae3dcf-b571-490d-b0ad-3f0f035ac0d4" />

Poznámka: systém ve skutečnosti neprovádí žádné obchody.

[![Twitter Follow](https://img.shields.io/twitter/follow/virattt?style=social)](https://twitter.com/virattt)

## Prohlášení o vyloučení odpovědnosti

Tento projekt je určen **pouze pro vzdělávací a výzkumné účely**.

- Není určen pro skutečné obchodování nebo investování
- Neposkytuje investiční poradenství ani záruky
- Tvůrce nepřebírá odpovědnost za finanční ztráty
- Pro investiční rozhodnutí se poraďte s finančním poradcem
- Minulá výkonnost nezaručuje budoucí výsledky

Používáním tohoto softwaru souhlasíte s jeho použitím pouze pro vzdělávací účely.

## Obsah
- [Jak nainstalovat](#jak-nainstalovat)
- [Jak spustit](#jak-spustit)
  - [⌨️ Rozhraní příkazové řádky](#️-rozhraní-příkazové-řádky)
  - [🖥️ Webová aplikace (NOVÉ!)](#️-webová-aplikace)
- [Přispívání](#přispívání)
- [Požadavky na funkce](#požadavky-na-funkce)
- [Licence](#licence)

## Jak nainstalovat

Před spuštěním AI Hedge Fund je třeba jej nainstalovat a nastavit API klíče. Tyto kroky jsou společné pro webovou aplikaci i rozhraní příkazové řádky.

### 1. Klonování repozitáře

```bash
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund
```

### 2. Nastavení API klíčů

Vytvořte soubor `.env` pro vaše API klíče:
```bash
# Vytvořte .env soubor pro vaše API klíče (v kořenovém adresáři)
cp .env.example .env
```

Otevřete a upravte soubor `.env` pro přidání vašich API klíčů:
```bash
# Pro spuštění LLM hostovaných OpenAI (gpt-4o, gpt-4o-mini, atd.)
OPENAI_API_KEY=váš-openai-api-klíč

# Pro spuštění LLM hostovaných Groq (deepseek, llama3, atd.)
GROQ_API_KEY=váš-groq-api-klíč

# Pro získání finančních dat pro hedge fund
FINANCIAL_DATASETS_API_KEY=váš-financial-datasets-api-klíč
```

**Důležité**: Musíte nastavit alespoň jeden LLM API klíč (`OPENAI_API_KEY`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, nebo `DEEPSEEK_API_KEY`) pro fungování hedge fondu.

**Finanční data**: Data pro AAPL, GOOGL, MSFT, NVDA a TSLA jsou zdarma a nevyžadují API klíč. Pro jakýkoli jiný ticker budete muset nastavit `FINANCIAL_DATASETS_API_KEY` v .env souboru.

## Jak spustit

### ⌨️ Rozhraní příkazové řádky

Pro uživatele, kteří preferují práci s nástroji příkazové řádky, můžete spustit AI Hedge Fund přímo přes terminál. Tento přístup nabízí větší kontrolu a je užitečný pro automatizaci, skriptování a integrační účely.

<img width="992" alt="Screenshot 2025-01-06 at 5 50 17 PM" src="https://github.com/user-attachments/assets/e8ca04bf-9989-4a7d-a8b4-34e04666663b" />

Vyberte jednu z následujících metod instalace:

#### Použití Poetry

1. Nainstalujte Poetry (pokud ještě není nainstalováno):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Nainstalujte závislosti:
```bash
poetry install
```

#### Použití Docker

1. Ujistěte se, že máte Docker nainstalovaný ve vašem systému. Pokud ne, můžete si jej stáhnout z [oficiálních stránek Docker](https://www.docker.com/get-started).

2. Přejděte do adresáře docker:
```bash
cd docker
```

3. Sestavte Docker obraz:
```bash
# Na Linux/Mac:
./run.sh build

# Na Windows:
run.bat build
```

#### Spuštění AI Hedge Fund (s Poetry)
```bash
poetry run python src/main.py --ticker AAPL,MSFT,NVDA
```

#### Spuštění AI Hedge Fund (s Docker)
```bash
# Nejprve přejděte do adresáře docker
cd docker

# Na Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA main

# Na Windows:
run.bat --ticker AAPL,MSFT,NVDA main
```

Můžete také specifikovat příznak `--ollama` pro spuštění AI hedge fondu s lokálními LLM.

```bash
# S Poetry:
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --ollama

# S Docker (z adresáře docker/):
# Na Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA --ollama main

# Na Windows:
run.bat --ticker AAPL,MSFT,NVDA --ollama main
```

Můžete také specifikovat příznak `--show-reasoning` pro výpis uvažování každého agenta do konzole.

```bash
# S Poetry:
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --show-reasoning

# S Docker (z adresáře docker/):
# Na Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA --show-reasoning main

# Na Windows:
run.bat --ticker AAPL,MSFT,NVDA --show-reasoning main
```

Volitelně můžete specifikovat počáteční a koncové datum pro rozhodování v konkrétním časovém období.

```bash
# S Poetry:
poetry run python src/main.py --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01 

# S Docker (z adresáře docker/):
# Na Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01 main

# Na Windows:
run.bat --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01 main
```

#### Spuštění Backtesteru (s Poetry)
```bash
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA
```

#### Spuštění Backtesteru (s Docker)
```bash
# Nejprve přejděte do adresáře docker
cd docker

# Na Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA backtest

# Na Windows:
run.bat --ticker AAPL,MSFT,NVDA backtest
```

**Příklad výstupu:**
<img width="941" alt="Screenshot 2025-01-06 at 5 47 52 PM" src="https://github.com/user-attachments/assets/00e794ea-8628-44e6-9a84-8f8a31ad3b47" />

Volitelně můžete specifikovat počáteční a koncové datum pro backtesting v konkrétním časovém období.

```bash
# S Poetry:
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01

# S Docker (z adresáře docker/):
# Na Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01 backtest

# Na Windows:
run.bat --ticker AAPL,MSFT,NVDA --start-date 2024-01-01 --end-date 2024-03-01 backtest
```

Můžete také specifikovat příznak `--ollama` pro spuštění backtesteru s lokálními LLM.
```bash
# S Poetry:
poetry run python src/backtester.py --ticker AAPL,MSFT,NVDA --ollama

# S Docker (z adresáře docker/):
# Na Linux/Mac:
./run.sh --ticker AAPL,MSFT,NVDA --ollama backtest

# Na Windows:
run.bat --ticker AAPL,MSFT,NVDA --ollama backtest
```

### 🖥️ Webová aplikace

Nový způsob spuštění AI Hedge Fund je prostřednictvím naší webové aplikace, která poskytuje uživatelsky přívětivé rozhraní. **Toto je doporučeno pro většinu uživatelů, zejména těch, kteří preferují vizuální rozhraní před nástroji příkazové řádky.**

<img width="1721" alt="Screenshot 2025-06-28 at 6 41 03 PM" src="https://github.com/user-attachments/assets/b95ab696-c9f4-416c-9ad1-51feb1f5374b" />

#### Pro Mac/Linux:
```bash
cd app && ./run.sh
```

Pokud dostanete chybu "permission denied", nejprve spusťte:
```bash
cd app && chmod +x run.sh && ./run.sh
```

#### Pro Windows:
```bash
# Přejděte do adresáře /app
cd app

# Spusťte aplikaci
\.run.bat
```

**To je vše!** Tyto skripty:
1. Zkontrolují požadované závislosti (Node.js, Python, Poetry)
2. Automaticky nainstalují všechny závislosti
3. Spustí frontend i backend služby
4. **Automaticky otevřou váš webový prohlížeč** s aplikací

#### Podrobné pokyny k nastavení

Pro podrobné pokyny k nastavení, řešení problémů a pokročilé možnosti konfigurace viz:
- [Dokumentace Full-Stack aplikace](./app/README.md)
- [Dokumentace Frontend](./app/frontend/README.md)  
- [Dokumentace Backend](./app/backend/README.md)

## Přispívání

1. Forkněte repozitář
2. Vytvořte větev pro funkci
3. Commitněte vaše změny
4. Pushněte do větve
5. Vytvořte Pull Request

**Důležité**: Prosím udržujte vaše pull requesty malé a zaměřené. To usnadní jejich kontrolu a sloučení.

## Požadavky na funkce

Pokud máte požadavek na funkci, prosím otevřete [issue](https://github.com/virattt/ai-hedge-fund/issues) a ujistěte se, že je označen jako `enhancement`.

## Licence

Tento projekt je licencován pod MIT licencí - viz soubor LICENSE pro podrobnosti.
