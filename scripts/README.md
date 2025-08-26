# AI Hedge Fund - Skripty pro správu agentů

**Verze:** v1.5 Production-ready Beta  
**Status:** Všech 17 agentů je plně funkčních

Tento adresář obsahuje užitečné skripty pro správu a testování agentů v AI hedge fondu. Všechny skripty jsou aktualizovány pro v1.5 a podporují všech 17 funkčních AI agentů.

## 📋 Přehled skriptů

### 1. `fix_agents.py` - Profesionální nástroj pro opravu agentů

Komplexní Python skript pro automatickou opravu import chyb v agentech.

**Funkce:**
- ✅ Automatické testování všech 17 agentů
- 🔧 Automatická oprava běžných import problémů
- 📊 Detailní zpráva o stavu agentů
- 💾 Export výsledků do JSON
- 🎯 Inteligentní detekce názvů funkcí agentů
- 🔍 Type safety validation
- 📋 Production readiness check

**Spuštění:**
```bash
python scripts/fix_agents.py
```

**Výstup:**
- Konzolová zpráva s přehledem výsledků
- `agent_test_report.json` - detailní zpráva

### 2. `test_all_agents.sh` - Rychlý test agentů

Jednoduchý bash skript pro rychlé ověření funkčnosti všech agentů.

**Funkce:**
- ⚡ Rychlé testování importů
- 📈 Základní statistiky
- 🎯 Jednoduché použití

**Spuštění:**
```bash
chmod +x scripts/test_all_agents.sh
./scripts/test_all_agents.sh
```

## 🚀 Doporučené použití

### Pro běžné testování:
```bash
./scripts/test_all_agents.sh
```

### Pro detailní analýzu a opravu:
```bash
python scripts/fix_agents.py
```

### Pro kontinuální integraci:
```bash
# V CI/CD pipeline
python scripts/fix_agents.py
if [ $? -ne 0 ]; then
    echo "Některé agenty nefungují!"
    exit 1
fi
```

## 🔧 Jak skripty fungují

### Automatická oprava importů

Skripty automaticky opravují tyto běžné problémy:

1. **Chybějící importy** - přidává standardní importy
2. **Špatné pořadí importů** - reorganizuje podle PEP 8
3. **Chybějící `__future__` importy** - přidává pro kompatibilitu
4. **Detekce funkcí agentů** - inteligentně hledá hlavní funkce

### Podporované vzory názvů funkcí:

- `{agent_name}_agent`
- `{agent_name}_analyst_agent`
- `portfolio_management_agent`
- `risk_management_agent`
- `technical_analyst_agent`
- `sentiment_analyst_agent`
- `fundamentals_analyst_agent`
- `valuation_analyst_agent`

[18:50:42] INFO: Spouštím komplexní test agentů...
[18:50:42] INFO: Nalezeno 17 souborů agentů
[18:50:42] INFO: Testování agenta: aswath_damodaran
[18:50:45] INFO: ✅ aswath_damodaran - import úspěšný
...

AI HEDGE FUND - ZPRÁVA O TESTOVÁNÍ AGENTŮ
Čas: 2025-08-01T18:50:42.200461
Celkem agentů: 17
Úspěšné importy: 17
Neúspěšné importy: 0
Opravené agenty: 0

Úspěšnost: 100.0%

🎉 Všechny agenty fungují správně!
```
## 📊 Příklad výstupu (v1.5)

```
🚀 AI Hedge Fund - Agent Import Fixer v1.5
[18:50:42] INFO: Spouštím komplexní test agentů...
[18:50:42] INFO: Nalezeno 17 souborů agentů
[18:50:42] INFO: Testování agenta: aswath_damodaran
[18:50:45] INFO: ✅ aswath_damodaran - import úspěšný
[18:50:45] INFO: Testování agenta: warren_buffett
[18:50:46] INFO: ✅ warren_buffett - import úspěšný
[18:50:46] INFO: Testování agenta: portfolio_manager
[18:50:47] INFO: ✅ portfolio_manager - import úspěšný
...

AI HEDGE FUND - ZPRÁVA O TESTOVÁNÍ AGENTŮ (v1.5)
Čas: 2025-03-08T18:50:42.200461
Celkem agentů: 17
Úspěšné importy: 17
Neúspěšné importy: 0
Opravené agenty: 0
Production ready: ✅ ANO

Úspěšnost: 100.0%
Type Safety: ✅ Vylepšena (95%+ Pylance errors resolved)
Code Quality: 🔄 V procesu (1,397 issues identifikováno)

🎉 Všech 17 agentů je plně funkčních a production-ready!

📋 Seznam funkčních agentů:
✅ aswath_damodaran    ✅ ben_graham         ✅ bill_ackman
✅ cathie_wood         ✅ charlie_munger     ✅ fundamentals
✅ michael_burry       ✅ peter_lynch        ✅ phil_fisher
✅ portfolio_manager   ✅ rakesh_jhunjhunwala ✅ risk_manager
✅ sentiment           ✅ stanley_druckenmiller ✅ technicals
✅ valuation           ✅ warren_buffett
```
==================================================
[18:50:42] INFO: Spouštím komplexní test agentů...
[18:50:42] INFO: Nalezeno 17 souborů agentů
[18:50:42] INFO: Testování agenta: aswath_damodaran
[18:50:45] INFO: ✅ aswath_damodaran - import úspěšný
...

============================================================
AI HEDGE FUND - ZPRÁVA O TESTOVÁNÍ AGENTŮ
============================================================
Čas: 2025-08-01T18:50:42.200461
Celkem agentů: 17
Úspěšné importy: 17
Neúspěšné importy: 0
Opravené agenty: 0

Úspěšnost: 100.0%

🎉 Všechny agenty fungují správně!
```

## 🛠️ Požadavky

- Python 3.8+ (doporučeno 3.11)
- Poetry
- Bash (pro shell skript)
- Všechny závislosti z pyproject.toml

## 📝 Poznámky (v1.5)

- Skripty musí být spuštěny z kořenového adresáře projektu
- Automaticky kontrolují přítomnost Poetry
- Bezpečně testují importy bez ovlivnění systému
- Vytváří zálohy před úpravami souborů
- Podporují všech 17 AI agentů v production-ready stavu
- Integrované s type safety improvements
- Kompatibilní s multi-LLM architekturou

## 🎯 Aktuální stav (v1.5)

### ✅ Dokončeno:
- Všech 17 agentů je plně funkčních
- Type safety významně vylepšena
- Import errors vyřešeny
- Production readiness ověřena

### 🔄 V procesu:
- Code quality improvements (1,397 issues)
- Security fixes (13 issues)
- Test coverage enhancement

## 🤝 Přispívání

Pokud najdete chybu nebo máte nápad na vylepšení, vytvořte issue nebo pull request.

## 📄 Licence

Tyto skripty jsou součástí AI Hedge Fund projektu a podléhají stejné MIT licenci.
