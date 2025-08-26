#!/usr/bin/env python3
"""
AI Hedge Fund - Agent Import Fixer Script
==========================================

Profesionální skript pro automatickou opravu import chyb v agentech AI hedge fondu.
Tento skript:
1. Analyzuje všechny agenty v src/agents/
2. Testuje jejich importy
3. Automaticky opravuje běžné import problémy
4. Generuje detailní zprávu o stavu

Autor: AI Assistant
Verze: 1.0
Datum: 2025-01-08
"""

import json
import re
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Přidání src do Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class AgentImportFixer:
    """Hlavní třída pro opravu importů agentů."""

    def __init__(self, agents_dir: str = "src/agents"):
        self.agents_dir = Path(agents_dir)
        self.results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "fixed_agents": 0,
            "agents": {},
        }

        # Známé funkční vzory importů
        self.working_import_patterns: Dict[str, List[str]] = {
            "standard": [
                "from __future__ import annotations",
                "",
                "from datetime import datetime, timedelta",
                "import json",
                "from typing_extensions import Literal",
                "",
                "from src.graph.state import AgentState, show_agent_reasoning",
                "from langchain_core.messages import HumanMessage",
                "from langchain_core.prompts import ChatPromptTemplate",
                "from pydantic import BaseModel",
                "",
                "from src.tools.api import (",
                "    get_company_news,",
                "    get_financial_metrics,",
                "    get_insider_trades,",
                "    get_market_cap,",
                "    search_line_items,",
                ")",
                "from src.utils.llm import call_llm",
                "from src.utils.progress import progress",
                "from src.utils.api_key import get_api_key_from_state",
            ]
        }

    def log(self, message: str, level: str = "INFO"):
        """Logování zpráv s časovým razítkem."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def find_agent_files(self) -> List[Path]:
        """Najde všechny Python soubory agentů."""
        agent_files: List[Path] = []
        if not self.agents_dir.exists():
            self.log(f"Adresář {self.agents_dir} neexistuje!", "ERROR")
            return agent_files

        for file_path in self.agents_dir.glob("*.py"):
            if file_path.name != "__init__.py":
                agent_files.append(file_path)

        self.log(f"Nalezeno {len(agent_files)} souborů agentů")
        return sorted(agent_files)

    def test_agent_import(self, agent_file: Path) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Testuje import agenta pomocí poetry run.

        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (success, error_message, function_name)
        """
        function_name: Optional[str] = None
        try:
            # Načtení souboru pro nalezení hlavní funkce agenta
            with open(agent_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Hledání hlavní funkce agenta
            function_name = self.extract_main_function(content, agent_file.stem)
            if not function_name:
                return False, "Hlavní funkce agenta nenalezena", None

            # Vytvoření import příkazu
            module_path = f"src.agents.{agent_file.stem}"
            import_cmd = f"from {module_path} import {function_name}; print('{function_name} import successful')"

            # Spuštění testu pomocí poetry
            result = subprocess.run(
                ["poetry", "run", "python", "-c", import_cmd], capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                return True, None, function_name
            else:
                return False, result.stderr.strip(), function_name

        except subprocess.TimeoutExpired:
            return False, "Timeout při testování importu", function_name
        except Exception as e:
            return False, f"Chyba při testování: {str(e)}", function_name

    def extract_main_function(self, content: str, agent_name: str) -> Optional[str]:
        """Extrahuje název hlavní funkce agenta ze souboru."""
        # Běžné vzory názvů funkcí agentů
        possible_names = [
            f"{agent_name}_agent",
            f"{agent_name.replace('_', '')}_agent",
            f"{agent_name}_analyst_agent",
            f"{agent_name.replace('_', '')}_analyst_agent",
            "portfolio_management_agent",
            "risk_management_agent",
            "technical_analyst_agent",
            "sentiment_analyst_agent",
            "fundamentals_analyst_agent",
            "valuation_analyst_agent",
        ]

        for name in possible_names:
            if f"def {name}(" in content:
                return name

        # Fallback: hledání jakékoli funkce končící na _agent
        matches = re.findall(r"def (\w*_agent)\(", content)
        if matches:
            return matches[0]

        return None

    def analyze_import_issues(self, error_message: str) -> List[str]:
        """Analyzuje chybové zprávy a identifikuje problémy s importy."""
        issues: List[str] = []

        if "ModuleNotFoundError" in error_message:
            issues.append("missing_module")
        if "ImportError" in error_message:
            issues.append("import_error")
        if "circular import" in error_message.lower():
            issues.append("circular_import")
        if "cannot import name" in error_message:
            issues.append("missing_function")
        if "SyntaxError" in error_message:
            issues.append("syntax_error")

        return issues

    def fix_common_import_issues(self, agent_file: Path, error_message: str) -> bool:
        """
        Pokusí se automaticky opravit běžné problémy s importy.

        Returns:
            bool: True pokud byla provedena oprava
        """
        try:
            with open(agent_file, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            issues = self.analyze_import_issues(error_message)

            # Oprava 1: Přidání chybějících importů
            if "missing_module" in issues or "import_error" in issues:
                content = self.fix_missing_imports(content)

            # Oprava 2: Oprava pořadí importů
            content = self.fix_import_order(content)

            # Oprava 3: Přidání __future__ importů
            if "__future__" not in content:
                content = "from __future__ import annotations\n\n" + content

            # Uložení pouze pokud se obsah změnil
            if content != original_content:
                with open(agent_file, "w", encoding="utf-8") as f:
                    f.write(content)
                self.log(f"Opraveny importy v {agent_file.name}")
                return True

            return False

        except Exception as e:
            self.log(f"Chyba při opravě {agent_file.name}: {str(e)}", "ERROR")
            return False

    def fix_missing_imports(self, content: str) -> str:
        """Přidá chybějící standardní importy."""
        lines = content.split("\n")

        # Standardní importy, které by měly být přítomny
        required_imports: List[str] = [
            "from src.graph.state import AgentState, show_agent_reasoning",
            "from src.utils.progress import progress",
            "from src.utils.api_key import get_api_key_from_state",
            "from langchain_core.messages import HumanMessage",
            "import json",
        ]

        # Kontrola, které importy chybí
        missing_imports: List[str] = []
        for imp in required_imports:
            if not any(imp in line for line in lines):
                missing_imports.append(imp)

        if missing_imports:
            # Najdeme místo pro vložení importů (po __future__ importech)
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith("from __future__"):
                    insert_index = i + 1
                elif line.strip() == "" and i > insert_index:
                    insert_index = i
                    break
                elif line.startswith("from ") or line.startswith("import "):
                    break

            # Vložíme chybějící importy
            for imp in reversed(missing_imports):
                lines.insert(insert_index, imp)

            # Přidáme prázdný řádek po importech
            if lines[insert_index + len(missing_imports)].strip() != "":
                lines.insert(insert_index + len(missing_imports), "")

        return "\n".join(lines)

    def fix_import_order(self, content: str) -> str:
        """Opraví pořadí importů podle PEP 8."""
        lines = content.split("\n")

        # Rozdělíme obsah na sekce
        future_imports: List[str] = []
        stdlib_imports: List[str] = []
        third_party_imports: List[str] = []
        local_imports: List[str] = []
        other_lines: List[str] = []

        in_imports = True

        for line in lines:
            stripped = line.strip()

            if not stripped and in_imports:
                continue  # Přeskočíme prázdné řádky v import sekci
            elif stripped.startswith("from __future__"):
                future_imports.append(line)
            elif stripped.startswith(("import ", "from ")) and in_imports:
                if stripped.startswith("from src.") or stripped.startswith("import src."):
                    local_imports.append(line)
                elif any(lib in stripped for lib in ["langchain", "pydantic", "pandas", "numpy"]):
                    third_party_imports.append(line)
                else:
                    stdlib_imports.append(line)
            else:
                in_imports = False
                other_lines.append(line)

        # Sestavíme nový obsah s správným pořadím
        new_lines: List[str] = []

        if future_imports:
            new_lines.extend(future_imports)
            new_lines.append("")

        if stdlib_imports:
            new_lines.extend(sorted(stdlib_imports))
            new_lines.append("")

        if third_party_imports:
            new_lines.extend(sorted(third_party_imports))
            new_lines.append("")

        if local_imports:
            new_lines.extend(sorted(local_imports))
            new_lines.append("")

        new_lines.extend(other_lines)

        return "\n".join(new_lines)

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Spustí komplexní test všech agentů."""
        self.log("Spouštím komplexní test agentů...")

        agent_files = self.find_agent_files()
        self.results["total_agents"] = len(agent_files)

        for agent_file in agent_files:
            agent_name = agent_file.stem
            self.log(f"Testování agenta: {agent_name}")

            # První test
            success, error, function_name = self.test_agent_import(agent_file)

            agent_result: Dict[str, Any] = {
                "file": str(agent_file),
                "function_name": function_name,
                "initial_test": {"success": success, "error": error},
                "fixed": False,
                "final_test": None,
            }

            if success:
                self.log(f"✅ {agent_name} - import úspěšný")
                self.results["successful_imports"] += 1
            else:
                self.log(f"❌ {agent_name} - chyba importu: {error}")

                # Pokus o opravu
                if self.fix_common_import_issues(agent_file, error or ""):
                    agent_result["fixed"] = True
                    self.results["fixed_agents"] += 1

                    # Test po opravě
                    success_after, error_after, _ = self.test_agent_import(agent_file)
                    agent_result["final_test"] = {"success": success_after, "error": error_after}

                    if success_after:
                        self.log(f"✅ {agent_name} - opraveno a funguje")
                        self.results["successful_imports"] += 1
                    else:
                        self.log(f"❌ {agent_name} - stále nefunguje po opravě: {error_after}")
                        self.results["failed_imports"] += 1
                else:
                    self.results["failed_imports"] += 1

            self.results["agents"][agent_name] = agent_result

        return self.results

    def generate_report(self) -> str:
        """Generuje detailní zprávu o výsledcích."""
        report: List[str] = []
        report.append("=" * 60)
        report.append("AI HEDGE FUND - ZPRÁVA O TESTOVÁNÍ AGENTŮ")
        report.append("=" * 60)
        report.append(f"Čas: {self.results['timestamp']}")
        report.append(f"Celkem agentů: {self.results['total_agents']}")
        report.append(f"Úspěšné importy: {self.results['successful_imports']}")
        report.append(f"Neúspěšné importy: {self.results['failed_imports']}")
        report.append(f"Opravené agenty: {self.results['fixed_agents']}")
        report.append("")

        # Úspěšnost v procentech
        if self.results["total_agents"] > 0:
            success_rate: float = (self.results["successful_imports"] / self.results["total_agents"]) * 100
            report.append(f"Úspěšnost: {success_rate:.1f}%")

        report.append("")
        report.append("DETAILNÍ VÝSLEDKY:")
        report.append("-" * 40)

        for agent_name, result in self.results["agents"].items():
            status = "✅ FUNGUJE" if result["initial_test"]["success"] else "❌ NEFUNGUJE"
            if result["fixed"] and result["final_test"] and result["final_test"]["success"]:
                status = "🔧 OPRAVENO"
            elif result["fixed"]:
                status = "❌ OPRAVA SELHALA"

            report.append(f"{agent_name:25} | {status}")

            if result["initial_test"]["error"]:
                report.append(f"  └─ Chyba: {result['initial_test']['error'][:80]}...")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def save_detailed_report(self, filename: str = "agent_test_report.json"):
        """Uloží detailní zprávu do JSON souboru."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            self.log(f"Detailní zpráva uložena do {filename}")
        except Exception as e:
            self.log(f"Chyba při ukládání zprávy: {str(e)}", "ERROR")


def main():
    """Hlavní funkce skriptu."""
    print("🚀 AI Hedge Fund - Agent Import Fixer")
    print("=" * 50)

    # Kontrola, že jsme ve správném adresáři
    if not Path("src/agents").exists():
        print("❌ Chyba: Adresář src/agents nenalezen!")
        print("   Ujistěte se, že spouštíte skript z kořenového adresáře projektu.")
        sys.exit(1)

    # Kontrola Poetry
    try:
        subprocess.run(["poetry", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Chyba: Poetry není nainstalováno nebo není dostupné!")
        print("   Nainstalujte Poetry: https://python-poetry.org/docs/#installation")
        sys.exit(1)

    # Spuštění fixeru
    fixer = AgentImportFixer()

    try:
        results = fixer.run_comprehensive_test()

        # Výpis zprávy
        report = fixer.generate_report()
        print(report)

        # Uložení detailní zprávy
        fixer.save_detailed_report()

        # Exit kód podle výsledků
        if results["failed_imports"] == 0:
            print("\n🎉 Všechny agenty fungují správně!")
            sys.exit(0)
        else:
            print(f"\n⚠️  {results['failed_imports']} agentů stále nefunguje.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⏹️  Test přerušen uživatelem.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Neočekávaná chyba: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
