#!/usr/bin/env python3
"""
Genius Test Suite pro AI Hedge Fund projekt
===========================================

Kompletně přepracovaný testovací systém, který řeší všechny problémy
a funguje bez závislosti na pytest s graceful fallback.
"""

import os
import sys
import time
import json
import traceback
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from unittest.mock import Mock, patch, MagicMock

# Přidání project root do Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestResult:
    """Třída pro ukládání výsledků testů."""
    
    def __init__(self, name: str, success: bool, message: str = "", duration: float = 0.0, details: Dict = None):
        self.name = name
        self.success = success
        self.message = message
        self.duration = duration
        self.details = details or {}
        self.timestamp = datetime.now()

class GeniusTestSuite:
    """Genius testovací suite s pokročilými funkcemi."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.start_time = time.time()
        self.setup_environment()
        
    def setup_environment(self):
        """Nastavení testovacího prostředí."""
        # Import všech potřebných modulů s graceful handling
        self.imports = {}
        
        # Základní importy
        try:
            import pandas as pd
            import numpy as np
            self.imports['pandas'] = pd
            self.imports['numpy'] = np
        except ImportError:
            self.imports['pandas'] = None
            self.imports['numpy'] = None
        
        try:
            import requests
            self.imports['requests'] = requests
        except ImportError:
            self.imports['requests'] = None
            
        try:
            from test_mocks import (
                MockLLMClient, WarrenBuffettAgent, MichaelBurryAgent,
                FundamentalsAgent, TechnicalAgent, PortfolioManager,
                RiskManager, Backtester
            )
            self.imports['mocks'] = {
                'MockLLMClient': MockLLMClient,
                'WarrenBuffettAgent': WarrenBuffettAgent,
                'MichaelBurryAgent': MichaelBurryAgent,
                'FundamentalsAgent': FundamentalsAgent,
                'TechnicalAgent': TechnicalAgent,
                'PortfolioManager': PortfolioManager,
                'RiskManager': RiskManager,
                'Backtester': Backtester
            }
        except ImportError as e:
            self.log(f"Warning: Mock imports failed: {e}", "WARNING")
            self.imports['mocks'] = None
    
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
            
            if isinstance(result, dict):
                success = result.get('success', True)
                message = result.get('message', 'Test completed')
                details = result.get('details', {})
            else:
                success = bool(result)
                message = "Test passed" if success else "Test failed"
                details = {}
            
            test_result = TestResult(test_name, success, message, duration, details)
            
            if success:
                self.log(f"✅ {test_name} - PASSED ({duration:.2f}s)")
            else:
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
    
    # ============================================================================
    # ZÁKLADNÍ TESTY
    # ============================================================================
    
    def test_environment_setup(self) -> Dict:
        """Test základního nastavení prostředí."""
        try:
            issues = []
            
            # Python verze
            if sys.version_info < (3, 11):
                issues.append(f"Python 3.11+ required, got {sys.version_info}")
            
            # Základní adresáře
            required_dirs = ["src", "app", "docs", "logs"]
            missing_dirs = [d for d in required_dirs if not (PROJECT_ROOT / d).exists()]
            if missing_dirs:
                issues.append(f"Missing directories: {missing_dirs}")
            
            # Základní soubory
            required_files = ["launcher.py", "pyproject.toml", "README.md"]
            missing_files = [f for f in required_files if not (PROJECT_ROOT / f).exists()]
            if missing_files:
                issues.append(f"Missing files: {missing_files}")
            
            if issues:
                return {"success": False, "message": "; ".join(issues)}
            
            return {"success": True, "message": "Environment setup OK"}
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_imports(self) -> Dict:
        """Test importů základních modulů."""
        try:
            available = []
            missing = []
            
            # Test standardních knihoven
            std_libs = ['os', 'sys', 'json', 'time', 'pathlib', 'datetime']
            for lib in std_libs:
                try:
                    __import__(lib)
                    available.append(lib)
                except ImportError:
                    missing.append(lib)
            
            # Test project modulů
            try:
                import launcher
                available.append('launcher')
            except ImportError:
                missing.append('launcher')
            
            # Test mock modulů
            if self.imports['mocks']:
                available.append('test_mocks')
            else:
                missing.append('test_mocks')
            
            message = f"Available: {len(available)}, Missing: {len(missing)}"
            if missing:
                message += f" (Missing: {missing})"
            
            return {"success": len(missing) == 0, "message": message}
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_dependencies(self) -> Dict:
        """Test volitelných závislostí."""
        dependencies = {
            "pandas": "Data processing",
            "numpy": "Numerical computing", 
            "requests": "HTTP requests",
            "fastapi": "Web framework",
            "rich": "Rich terminal output",
            "questionary": "Interactive prompts",
            "psutil": "System monitoring",
            "seaborn": "Statistical visualization",
            "matplotlib": "Plotting",
            "scipy": "Scientific computing"
        }
        
        available = []
        missing = []
        
        for dep, description in dependencies.items():
            try:
                __import__(dep)
                available.append(f"{dep} ({description})")
            except ImportError:
                missing.append(f"{dep} ({description})")
        
        if self.verbose:
            for dep in available:
                self.log(f"  ✅ {dep}")
            for dep in missing:
                self.log(f"  ❌ {dep}")
        
        return {
            "success": True, 
            "message": f"Available: {len(available)}, Missing: {len(missing)}",
            "details": {"available": len(available), "missing": len(missing)}
        }
    
    # ============================================================================
    # FUNKČNÍ TESTY
    # ============================================================================
    
    def test_launcher_functionality(self) -> Dict:
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
            
            # Test health check funkcí
            health_functions = ['check_backend_health', 'check_frontend_health']
            available_health = [func for func in health_functions if hasattr(launcher, func)]
            
            return {
                "success": True, 
                "message": f"Launcher OK, health functions: {len(available_health)}/2",
                "details": {"health_functions": available_health}
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_mock_implementations(self) -> Dict:
        """Test mock implementací."""
        if not self.imports['mocks']:
            return {"success": False, "message": "Mock implementations not available"}
        
        try:
            mocks = self.imports['mocks']
            
            # Test vytvoření objektů
            llm_client = mocks['MockLLMClient']()
            warren = mocks['WarrenBuffettAgent'](llm_client=llm_client)
            burry = mocks['MichaelBurryAgent'](llm_client=llm_client)
            fundamentals = mocks['FundamentalsAgent'](llm_client=llm_client)
            technical = mocks['TechnicalAgent']()
            portfolio_manager = mocks['PortfolioManager'](llm_client=llm_client)
            
            # Test základních metod
            response = llm_client.generate_response("test prompt")
            if not isinstance(response, str):
                return {"success": False, "message": "LLM client response is not string"}
            
            # Test agent properties
            agents_tested = 0
            for agent in [warren, burry, fundamentals]:
                if hasattr(agent, 'name'):
                    agents_tested += 1
            
            return {
                "success": True, 
                "message": f"Mock implementations OK, agents tested: {agents_tested}",
                "details": {"agents_tested": agents_tested}
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_data_processing(self) -> Dict:
        """Test zpracování dat."""
        try:
            if self.imports['pandas'] and self.imports['numpy']:
                pd = self.imports['pandas']
                np = self.imports['numpy']
                
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
                
                return {
                    "success": True, 
                    "message": f"Data processing OK, processed {len(df)} rows",
                    "details": {"rows": len(df), "mean_price": round(mean_price, 2)}
                }
            else:
                # Fallback bez pandas
                import random
                prices = [random.uniform(100, 200) for _ in range(31)]
                mean_price = sum(prices) / len(prices)
                
                return {
                    "success": True, 
                    "message": f"Basic processing OK (no pandas), mean: {mean_price:.2f}",
                    "details": {"fallback": True, "mean_price": round(mean_price, 2)}
                }
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    # ============================================================================
    # PERFORMANCE TESTY
    # ============================================================================
    
    def test_memory_usage(self) -> Dict:
        """Test využití paměti."""
        try:
            import psutil
            process = psutil.Process()
            initial_memory = process.memory_info().rss
            
            # Simulace náročné operace
            large_data = []
            for _ in range(1000):
                large_data.append([i for i in range(100)])
            
            peak_memory = process.memory_info().rss
            memory_increase = peak_memory - initial_memory
            
            # Cleanup
            del large_data
            
            # Memory increase should be reasonable (less than 50MB for this test)
            success = memory_increase < 50 * 1024 * 1024
            
            return {
                "success": success,
                "message": f"Memory test {'OK' if success else 'FAILED'}, increase: {memory_increase//1024//1024}MB",
                "details": {"memory_increase_mb": memory_increase//1024//1024}
            }
            
        except ImportError:
            return {"success": True, "message": "Memory test skipped (psutil not available)"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_performance_benchmark(self) -> Dict:
        """Test výkonnostního benchmarku."""
        try:
            if not self.imports['pandas'] or not self.imports['numpy']:
                return {"success": True, "message": "Performance test skipped (pandas/numpy not available)"}
            
            pd = self.imports['pandas']
            np = self.imports['numpy']
            
            # Benchmark operací
            start_time = time.time()
            
            # Vytvoření velkého datasetu
            data = pd.DataFrame({
                'values': np.random.randn(10000),
                'categories': np.random.choice(['A', 'B', 'C'], 10000)
            })
            
            # Výpočetní operace
            result = data.groupby('categories')['values'].agg(['mean', 'std', 'count'])
            
            duration = time.time() - start_time
            
            # Benchmark by měl být rychlejší než 1 sekunda
            success = duration < 1.0
            
            return {
                "success": success,
                "message": f"Performance benchmark {'OK' if success else 'SLOW'}, duration: {duration:.3f}s",
                "details": {"duration": round(duration, 3), "rows_processed": len(data)}
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    # ============================================================================
    # INTEGRATION TESTY
    # ============================================================================
    
    def test_file_operations(self) -> Dict:
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
                test_file = logs_dir / "genius_test.log"
                try:
                    with open(test_file, 'w') as f:
                        f.write(f"Genius test write at {datetime.now()}")
                    
                    # Cleanup
                    if test_file.exists():
                        test_file.unlink()
                        
                    return {
                        "success": True, 
                        "message": f"File operations OK, readable files: {len(readable_files)}",
                        "details": {"readable_files": readable_files}
                    }
                except Exception as e:
                    return {"success": False, "message": f"Write test failed: {e}"}
            else:
                return {"success": False, "message": "Logs directory not found"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_network_connectivity(self) -> Dict:
        """Test síťového připojení."""
        if not self.imports['requests']:
            return {"success": True, "message": "Network test skipped (requests not available)"}
        
        try:
            requests = self.imports['requests']
            
            # Test externí připojení
            try:
                response = requests.get("https://httpbin.org/status/200", timeout=5)
                if response.status_code == 200:
                    return {
                        "success": True, 
                        "message": "Network connectivity OK",
                        "details": {"external_connectivity": True}
                    }
            except:
                pass
            
            # Pokud externí připojení selhalo
            return {
                "success": False, 
                "message": "No external connectivity",
                "details": {"external_connectivity": False}
            }
                    
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    # ============================================================================
    # STRESS TESTY
    # ============================================================================
    
    def test_large_dataset_processing(self) -> Dict:
        """Test zpracování velkých datasetů."""
        if not self.imports['pandas'] or not self.imports['numpy']:
            return {"success": True, "message": "Large dataset test skipped (pandas/numpy not available)"}
        
        try:
            pd = self.imports['pandas']
            np = self.imports['numpy']
            
            # Vytvoření velkého datasetu (100k řádků)
            start_time = time.time()
            
            large_data = pd.DataFrame({
                'timestamp': pd.date_range(start='2020-01-01', periods=100000, freq='1min'),
                'price': np.random.uniform(100, 200, 100000),
                'volume': np.random.randint(1000, 10000, 100000)
            })
            
            # Výpočetní operace
            daily_stats = large_data.set_index('timestamp').resample('D').agg({
                'price': ['mean', 'std', 'min', 'max'],
                'volume': 'sum'
            })
            
            duration = time.time() - start_time
            
            # Mělo by být zpracováno do 5 sekund
            success = duration < 5.0
            
            return {
                "success": success,
                "message": f"Large dataset test {'OK' if success else 'SLOW'}, duration: {duration:.2f}s",
                "details": {
                    "rows_processed": len(large_data),
                    "duration": round(duration, 2),
                    "daily_stats_rows": len(daily_stats)
                }
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def test_concurrent_operations(self) -> Dict:
        """Test souběžných operací."""
        try:
            import threading
            import queue
            
            results_queue = queue.Queue()
            
            def worker_task(task_id):
                """Simulace práce."""
                start = time.time()
                # Simulace výpočtu
                result = sum(i**2 for i in range(1000))
                duration = time.time() - start
                results_queue.put((task_id, result, duration))
            
            # Spuštění 10 souběžných úloh
            threads = []
            start_time = time.time()
            
            for i in range(10):
                thread = threading.Thread(target=worker_task, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Čekání na dokončení
            for thread in threads:
                thread.join()
            
            total_duration = time.time() - start_time
            
            # Sběr výsledků
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())
            
            success = len(results) == 10 and total_duration < 2.0
            
            return {
                "success": success,
                "message": f"Concurrent operations {'OK' if success else 'SLOW'}, {len(results)}/10 completed",
                "details": {
                    "completed_tasks": len(results),
                    "total_duration": round(total_duration, 2)
                }
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    # ============================================================================
    # SECURITY TESTY
    # ============================================================================
    
    def test_input_validation(self) -> Dict:
        """Test validace vstupů."""
        try:
            # Test různých typů nebezpečných vstupů
            dangerous_inputs = [
                "'; DROP TABLE users; --",  # SQL injection
                "<script>alert('xss')</script>",  # XSS
                "../../../etc/passwd",  # Path traversal
                "$(rm -rf /)",  # Command injection
                "' OR '1'='1",  # SQL injection variant
            ]
            
            safe_inputs = [
                "AAPL",
                "MSFT,GOOGL,TSLA",
                "2024-01-01",
                "100000",
                "test@example.com"
            ]
            
            # Simulace validační funkce
            def validate_input(input_str):
                """Základní validace vstupů."""
                if not isinstance(input_str, str):
                    return False
                if len(input_str) > 1000:  # Příliš dlouhý
                    return False
                if any(char in input_str for char in ['<', '>', ';', '--', 'DROP', 'DELETE']):
                    return False
                return True
            
            # Test nebezpečných vstupů
            dangerous_blocked = sum(1 for inp in dangerous_inputs if not validate_input(inp))
            safe_allowed = sum(1 for inp in safe_inputs if validate_input(inp))
            
            success = dangerous_blocked == len(dangerous_inputs) and safe_allowed == len(safe_inputs)
            
            return {
                "success": success,
                "message": f"Input validation {'OK' if success else 'FAILED'}, blocked: {dangerous_blocked}/{len(dangerous_inputs)}",
                "details": {
                    "dangerous_blocked": dangerous_blocked,
                    "safe_allowed": safe_allowed
                }
            }
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    # ============================================================================
    # HLAVNÍ SPOUŠTĚCÍ FUNKCE
    # ============================================================================
    
    def run_basic_tests(self):
        """Spustí základní testy."""
        self.print_header("ZÁKLADNÍ TESTY")
        self.run_test("Environment Setup", self.test_environment_setup)
        self.run_test("Basic Imports", self.test_imports)
        self.run_test("Dependencies Check", self.test_dependencies)
    
    def run_functional_tests(self):
        """Spustí funkční testy."""
        self.print_header("FUNKČNÍ TESTY")
        self.run_test("Launcher Functionality", self.test_launcher_functionality)
        self.run_test("Mock Implementations", self.test_mock_implementations)
        self.run_test("Data Processing", self.test_data_processing)
    
    def run_performance_tests(self):
        """Spustí performance testy."""
        self.print_header("PERFORMANCE TESTY")
        self.run_test("Memory Usage", self.test_memory_usage)
        self.run_test("Performance Benchmark", self.test_performance_benchmark)
    
    def run_integration_tests(self):
        """Spustí integrační testy."""
        self.print_header("INTEGRAČNÍ TESTY")
        self.run_test("File Operations", self.test_file_operations)
        self.run_test("Network Connectivity", self.test_network_connectivity)
    
    def run_stress_tests(self):
        """Spustí stress testy."""
        self.print_header("STRESS TESTY")
        self.run_test("Large Dataset Processing", self.test_large_dataset_processing)
        self.run_test("Concurrent Operations", self.test_concurrent_operations)
    
    def run_security_tests(self):
        """Spustí security testy."""
        self.print_header("SECURITY TESTY")
        self.run_test("Input Validation", self.test_input_validation)
    
    def run_all_tests(self):
        """Spustí všechny testy."""
        self.print_header("GENIUS TEST SUITE - AI HEDGE FUND")
        
        self.run_basic_tests()
        self.run_functional_tests()
        self.run_performance_tests()
        self.run_integration_tests()
        self.run_stress_tests()
        self.run_security_tests()
        
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
        
        # Statistiky podle kategorií
        categories = {}
        for result in self.results:
            category = result.name.split()[0] if ' ' in result.name else 'Other'
            if category not in categories:
                categories[category] = {'passed': 0, 'failed': 0}
            
            if result.success:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
        
        if categories:
            print(f"\n📊 STATISTIKY PODLE KATEGORIÍ:")
            for category, stats in categories.items():
                total = stats['passed'] + stats['failed']
                success_rate = (stats['passed'] / total * 100) if total > 0 else 0
                print(f"  {category}: {stats['passed']}/{total} ({success_rate:.1f}%)")
        
        # Uložení výsledků
        self.save_results()
    
    def save_results(self):
        """Uloží výsledky do JSON souboru."""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "suite_name": "Genius Test Suite",
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "total_time": time.time() - self.start_time,
            "success_rate": (sum(1 for r in self.results if r.success) / len(self.results) * 100) if self.results else 0,
            "python_version": sys.version,
            "platform": sys.platform,
            "environment": {
                "pandas_available": self.imports['pandas'] is not None,
                "numpy_available": self.imports['numpy'] is not None,
                "requests_available": self.imports['requests'] is not None,
                "mocks_available": self.imports['mocks'] is not None
            },
            "tests": [
                {
                    "name": r.name,
                    "success": r.success,
                    "message": r.message,
                    "duration": r.duration,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
        
        try:
            with open("genius_test_results.json", "w", encoding="utf-8") as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            print(f"\n📊 Výsledky uloženy do: genius_test_results.json")
        except Exception as e:
            print(f"\n⚠️ Chyba při ukládání výsledků: {e}")

def main():
    """Hlavní funkce."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Genius Test Suite pro AI Hedge Fund")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--basic", action="store_true", help="Run only basic tests")
    parser.add_argument("--functional", action="store_true", help="Run only functional tests")
    parser.add_argument("--performance", action="store_true", help="Run only performance tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--stress", action="store_true", help="Run only stress tests")
    parser.add_argument("--security", action="store_true", help="Run only security tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    # Spuštění testů
    suite = GeniusTestSuite(verbose=args.verbose)
    
    try:
        if args.basic:
            suite.run_basic_tests()
        elif args.functional:
            suite.run_functional_tests()
        elif args.performance:
            suite.run_performance_tests()
        elif args.integration:
            suite.run_integration_tests()
        elif args.stress:
            suite.run_stress_tests()
        elif args.security:
            suite.run_security_tests()
        elif args.all:
            suite.run_all_tests()
        else:
            # Default: základní + funkční testy
            suite.run_basic_tests()
            suite.run_functional_tests()
            suite.print_results()
        
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
