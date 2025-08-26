#!/usr/bin/env python3
"""
Robustní Test Suite pro AI Hedge Fund projekt
==============================================

Jednoduchý a robustní testovací systém, který funguje bez pytest
a gracefully zvládá chybějící závislosti.
"""

import os
import sys
import time
import json
import traceback
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Přidání project root do Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestResult:
    """Třída pro ukládání výsledků testů."""
    
    def __init__(self, name: str, success: bool, message: str = "", duration: float = 0.0):
        self.name = name
        self.success = success
        self.message = message
        self.duration = duration
        self.timestamp = datetime.now()

class RobustTestSuite:
    """Robustní testovací suite."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        """Logování zpráv."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Spustí jednotlivý test a zachytí výsledek."""
        self.log(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start_time
            
            if result is True or (isinstance(result, dict) and result.get('success', False)):
                test_result = TestResult(test_name, True, "Test passed", duration)
                self.log(f"✅ {test_name} - PASSED ({duration:.2f}s)")
            else:
                message = result.get('message', 'Test failed') if isinstance(result, dict) else str(result)
                test_result = TestResult(test_name, False, message, duration)
                self.log(f"❌ {test_name} - FAILED: {message}")
                
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            test_result = TestResult(test_name, False, error_msg, duration)
            self.log(f"❌ {test_name} - ERROR: {error_msg}")
            
            if self.verbose:
                self.log(f"Traceback: {traceback.format_exc()}", "DEBUG")
        
        self.results.append(test_result)
        return test_result
    
    def print_header(self, title: str):
        """Vytiskne formátovaný header."""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    
    def test_environment_setup(self) -> bool:
        """Test základního nastavení prostředí."""
        try:
            # Python verze
            if sys.version_info < (3, 11):
                return {"success": False, "message": f"Python 3.11+ required, got {sys.version_info}"}
            
            # Základní adresáře
            required_dirs = ["src", "app", "docs", "logs"]
            missing_dirs = [d for d in required_dirs if not (PROJECT_ROOT / d).exists()]
            
            if missing_dirs:
                return {"success": False, "message": f"Missing directories: {missing_dirs}"}
            
            # Základní soubory
            required_files = ["launcher.py", "pyproject.toml", "README.md"]
            missing_files = [f for f in required_files if not (PROJECT_ROOT / f).exists()]
            
            if missing_files:
                return {"success": False, "message": f"Missing files: {missing_files}"}
            
            return True
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_imports(self) -> bool:
        """Test importů základních modulů."""
        try:
            # Standard library
            import os, sys, json, time
            from pathlib import Path
            from datetime import datetime
            
            # Pokus o import project modulů
            try:
                import launcher
                self.log("✅ Launcher module imported successfully")
            except ImportError as e:
                self.log(f"⚠️ Launcher import failed: {e}", "WARNING")
            
            try:
                from test_mocks import MockLLMClient
                self.log("✅ Test mocks imported successfully")
            except ImportError as e:
                self.log(f"⚠️ Test mocks import failed: {e}", "WARNING")
            
            return True
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_optional_dependencies(self) -> bool:
        """Test volitelných závislostí."""
        dependencies = {
            "pandas": "Data processing",
            "numpy": "Numerical computing", 
            "requests": "HTTP requests",
            "fastapi": "Web framework",
            "rich": "Rich terminal output",
            "questionary": "Interactive prompts",
            "pytest": "Testing framework",
            "psutil": "System monitoring"
        }
        
        available = []
        missing = []
        
        for dep, description in dependencies.items():
            try:
                __import__(dep)
                available.append(f"{dep} ({description})")
            except ImportError:
                missing.append(f"{dep} ({description})")
        
        self.log(f"Available dependencies: {len(available)}")
        self.log(f"Missing dependencies: {len(missing)}")
        
        if self.verbose:
            for dep in available:
                self.log(f"  ✅ {dep}")
            for dep in missing:
                self.log(f"  ❌ {dep}")
        
        return {"success": True, "message": f"Available: {len(available)}, Missing: {len(missing)}"}
    
    def test_launcher_functionality(self) -> bool:
        """Test funkčnosti launcheru."""
        try:
            import launcher
            
            # Test konfigurace
            if not hasattr(launcher, 'CONFIG'):
                return {"success": False, "message": "CONFIG not found in launcher"}
            
            config = launcher.CONFIG
            required_keys = ['backend', 'frontend', 'monitoring']
            missing_keys = [key for key in required_keys if key not in config]
            
            if missing_keys:
                return {"success": False, "message": f"Missing config keys: {missing_keys}"}
            
            # Test funkcí
            functions = ['check_prerequisites', 'install_dependencies', 'start_web_app']
            missing_functions = [func for func in functions if not hasattr(launcher, func)]
            
            if missing_functions:
                return {"success": False, "message": f"Missing functions: {missing_functions}"}
            
            return True
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_mock_implementations(self) -> bool:
        """Test mock implementací."""
        try:
            from test_mocks import (
                MockLLMClient, WarrenBuffettAgent, MichaelBurryAgent,
                FundamentalsAgent, TechnicalAgent, PortfolioManager
            )
            
            # Test vytvoření objektů
            llm_client = MockLLMClient()
            warren = WarrenBuffettAgent(llm_client=llm_client)
            burry = MichaelBurryAgent(llm_client=llm_client)
            fundamentals = FundamentalsAgent(llm_client=llm_client)
            technical = TechnicalAgent()
            portfolio_manager = PortfolioManager(llm_client=llm_client)
            
            # Test základních metod
            response = llm_client.generate_response("test prompt")
            if not isinstance(response, str):
                return {"success": False, "message": "LLM client response is not string"}
            
            return True
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_data_processing(self) -> bool:
        """Test zpracování dat."""
        try:
            # Test s pandas pokud je dostupné
            try:
                import pandas as pd
                import numpy as np
                
                # Vytvoření testovacích dat
                dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
                prices = np.random.uniform(100, 200, len(dates))
                
                df = pd.DataFrame({
                    'Date': dates,
                    'Close': prices,
                    'Volume': np.random.randint(1000000, 10000000, len(dates))
                })
                
                # Základní výpočty
                mean_price = df['Close'].mean()
                std_price = df['Close'].std()
                
                if mean_price <= 0 or std_price <= 0:
                    return {"success": False, "message": "Invalid statistical calculations"}
                
                return {"success": True, "message": f"Processed {len(df)} rows, mean: {mean_price:.2f}"}
                
            except ImportError:
                # Fallback bez pandas
                import random
                prices = [random.uniform(100, 200) for _ in range(31)]
                mean_price = sum(prices) / len(prices)
                
                return {"success": True, "message": f"Basic processing without pandas, mean: {mean_price:.2f}"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_file_operations(self) -> bool:
        """Test souborových operací."""
        try:
            # Test čtení konfiguračních souborů
            config_files = ["pyproject.toml", "README.md", ".env.example"]
            readable_files = []
            
            for file_path in config_files:
                path = PROJECT_ROOT / file_path
                if path.exists():
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content:
                                readable_files.append(file_path)
                    except Exception as e:
                        self.log(f"Error reading {file_path}: {e}", "WARNING")
            
            # Test zápisu do logs adresáře
            logs_dir = PROJECT_ROOT / "logs"
            if logs_dir.exists():
                test_file = logs_dir / "test_write.log"
                try:
                    with open(test_file, 'w') as f:
                        f.write(f"Test write at {datetime.now()}")
                    
                    # Cleanup
                    if test_file.exists():
                        test_file.unlink()
                        
                    return {"success": True, "message": f"File operations OK, readable files: {len(readable_files)}"}
                except Exception as e:
                    return {"success": False, "message": f"Write test failed: {e}"}
            else:
                return {"success": False, "message": "Logs directory not found"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_system_resources(self) -> bool:
        """Test systémových zdrojů."""
        try:
            # Test paměti
            try:
                import psutil
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                if memory.available < 1024 * 1024 * 1024:  # 1GB
                    return {"success": False, "message": "Low memory available"}
                
                if disk.free < 1024 * 1024 * 1024:  # 1GB
                    return {"success": False, "message": "Low disk space"}
                
                return {"success": True, "message": f"Memory: {memory.available//1024//1024}MB, Disk: {disk.free//1024//1024}MB"}
                
            except ImportError:
                # Fallback bez psutil
                return {"success": True, "message": "System resources check skipped (psutil not available)"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_network_connectivity(self) -> bool:
        """Test síťového připojení."""
        try:
            try:
                import requests
                
                # Test připojení k localhost (pro development server)
                try:
                    response = requests.get("http://localhost:8000/health", timeout=5)
                    if response.status_code == 200:
                        return {"success": True, "message": "Local server is running"}
                except:
                    pass
                
                # Test externí připojení
                try:
                    response = requests.get("https://httpbin.org/status/200", timeout=5)
                    if response.status_code == 200:
                        return {"success": True, "message": "External connectivity OK"}
                except:
                    return {"success": False, "message": "No external connectivity"}
                    
            except ImportError:
                return {"success": True, "message": "Network test skipped (requests not available)"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def run_all_tests(self):
        """Spustí všechny testy."""
        self.print_header("ROBUSTNÍ TEST SUITE - AI HEDGE FUND")
        
        # Základní testy
        self.print_header("ZÁKLADNÍ TESTY")
        self.run_test("Environment Setup", self.test_environment_setup)
        self.run_test("Basic Imports", self.test_imports)
        self.run_test("Optional Dependencies", self.test_optional_dependencies)
        
        # Funkční testy
        self.print_header("FUNKČNÍ TESTY")
        self.run_test("Launcher Functionality", self.test_launcher_functionality)
        self.run_test("Mock Implementations", self.test_mock_implementations)
        self.run_test("Data Processing", self.test_data_processing)
        
        # Systémové testy
        self.print_header("SYSTÉMOVÉ TESTY")
        self.run_test("File Operations", self.test_file_operations)
        self.run_test("System Resources", self.test_system_resources)
        self.run_test("Network Connectivity", self.test_network_connectivity)
        
        # Výsledky
        self.print_results()
    
    def print_results(self):
        """Vytiskne výsledky testů."""
        total_time = time.time() - self.start_time
        
        self.print_header("VÝSLEDKY TESTŮ")
        
        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed
        
        print(f"Celkem testů: {len(self.results)}")
        print(f"Úspěšné: {passed}")
        print(f"Neúspěšné: {failed}")
        print(f"Celkový čas: {total_time:.2f}s")
        print(f"Úspěšnost: {(passed/len(self.results)*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ NEÚSPĚŠNÉ TESTY:")
            for result in self.results:
                if not result.success:
                    print(f"  - {result.name}: {result.message}")
        
        # Uložení výsledků
        self.save_results()
    
    def save_results(self):
        """Uloží výsledky do JSON souboru."""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "total_time": time.time() - self.start_time,
            "python_version": sys.version,
            "platform": sys.platform,
            "tests": [
                {
                    "name": r.name,
                    "success": r.success,
                    "message": r.message,
                    "duration": r.duration,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
        
        try:
            with open("test_results.json", "w", encoding="utf-8") as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            print(f"\n📊 Výsledky uloženy do: test_results.json")
        except Exception as e:
            print(f"\n⚠️ Chyba při ukládání výsledků: {e}")

def main():
    """Hlavní funkce."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Robustní Test Suite pro AI Hedge Fund")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick tests only")
    
    args = parser.parse_args()
    
    # Spuštění testů
    suite = RobustTestSuite(verbose=args.verbose)
    
    try:
        suite.run_all_tests()
        
        # Exit code based on results
        failed = sum(1 for r in suite.results if not r.success)
        sys.exit(0 if failed == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Testy přerušeny uživatelem")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Kritická chyba: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
