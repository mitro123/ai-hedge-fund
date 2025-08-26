#!/usr/bin/env python3
"""
Instalační skript pro OpenBB Platform integraci do AI Hedge Fund projektu.

Tento skript automatizuje proces instalace a konfigurace OpenBB Platform
pro použití s naším AI Hedge Fund systémem.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Konfigurace logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenBBInstaller:
    """Instalátor pro OpenBB Platform."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Inicializace instalátoru.
        
        Args:
            project_root: Kořenový adresář projektu (default: aktuální adresář)
        """
        self.project_root = project_root or Path.cwd()
        self.openbb_path = self.project_root / "OpenBB"
        self.openbb_platform_path = self.openbb_path / "openbb_platform"
        
        logger.info(f"Projekt root: {self.project_root}")
        logger.info(f"OpenBB cesta: {self.openbb_path}")
    
    def check_prerequisites(self) -> bool:
        """Zkontroluje předpoklady pro instalaci."""
        logger.info("Kontrola předpokladů...")
        
        # Kontrola Python verze
        python_version = sys.version_info
        if python_version < (3, 8):
            logger.error(f"Python 3.8+ je vyžadován. Aktuální verze: {python_version}")
            return False
        
        logger.info(f"✓ Python verze: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Kontrola git
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✓ Git: {result.stdout.strip()}")
            else:
                logger.error("Git není dostupný")
                return False
        except FileNotFoundError:
            logger.error("Git není nainstalován")
            return False
        
        # Kontrola pip
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✓ Pip: {result.stdout.strip()}")
            else:
                logger.error("Pip není dostupný")
                return False
        except Exception as e:
            logger.error(f"Chyba při kontrole pip: {e}")
            return False
        
        return True
    
    def clone_openbb_repository(self) -> bool:
        """Naklonuje OpenBB repozitář."""
        logger.info("Klonování OpenBB repozitáře...")
        
        if self.openbb_path.exists():
            logger.info("OpenBB repozitář již existuje. Aktualizace...")
            try:
                # Aktualizace existujícího repozitáře
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=self.openbb_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    logger.info("✓ OpenBB repozitář aktualizován")
                    return True
                else:
                    logger.error(f"Chyba při aktualizaci: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"Chyba při aktualizaci repozitáře: {e}")
                return False
        else:
            try:
                # Klonování nového repozitáře
                result = subprocess.run([
                    "git", "clone", 
                    "https://github.com/OpenBB-finance/OpenBB.git",
                    str(self.openbb_path)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✓ OpenBB repozitář naklonován")
                    return True
                else:
                    logger.error(f"Chyba při klonování: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"Chyba při klonování repozitáře: {e}")
                return False
    
    def install_openbb_platform(self) -> bool:
        """Nainstaluje OpenBB Platform."""
        logger.info("Instalace OpenBB Platform...")
        
        if not self.openbb_platform_path.exists():
            logger.error(f"OpenBB Platform adresář neexistuje: {self.openbb_platform_path}")
            return False
        
        try:
            # Instalace v development módu
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-e", "."
            ], cwd=self.openbb_platform_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✓ OpenBB Platform nainstalována")
                return True
            else:
                logger.error(f"Chyba při instalaci: {result.stderr}")
                # Zkusíme základní instalaci
                logger.info("Zkouším základní instalaci...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "openbb"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✓ OpenBB základní verze nainstalována")
                    return True
                else:
                    logger.error(f"Chyba při základní instalaci: {result.stderr}")
                    return False
        except Exception as e:
            logger.error(f"Chyba při instalaci OpenBB Platform: {e}")
            return False
    
    def install_additional_dependencies(self) -> bool:
        """Nainstaluje dodatečné závislosti."""
        logger.info("Instalace dodatečných závislostí...")
        
        dependencies = [
            "yfinance",
            "pandas",
            "numpy",
            "requests",
            "python-dotenv"
        ]
        
        for dep in dependencies:
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"✓ {dep} nainstalován")
                else:
                    logger.warning(f"Chyba při instalaci {dep}: {result.stderr}")
            except Exception as e:
                logger.warning(f"Chyba při instalaci {dep}: {e}")
        
        return True
    
    def test_openbb_import(self) -> bool:
        """Otestuje import OpenBB."""
        logger.info("Testování OpenBB importu...")
        
        try:
            # Test základního importu
            result = subprocess.run([
                sys.executable, "-c", "from openbb import obb; print('OpenBB import úspěšný')"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✓ OpenBB import úspěšný")
                return True
            else:
                logger.error(f"Chyba při importu OpenBB: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Chyba při testování importu: {e}")
            return False
    
    def create_configuration_file(self) -> bool:
        """Vytvoří konfigurační soubor pro OpenBB."""
        logger.info("Vytváření konfiguračního souboru...")
        
        config = {
            "openbb": {
                "installed": True,
                "version": "latest",
                "path": str(self.openbb_path),
                "platform_path": str(self.openbb_platform_path)
            },
            "providers": {
                "yfinance": {
                    "enabled": True,
                    "requires_api_key": False
                },
                "fred": {
                    "enabled": True,
                    "requires_api_key": False
                },
                "benzinga": {
                    "enabled": True,
                    "requires_api_key": False,
                    "note": "Limited free tier"
                },
                "fmp": {
                    "enabled": False,
                    "requires_api_key": True,
                    "api_key_env": "FINANCIAL_MODELING_PREP_API_KEY"
                },
                "alpha_vantage": {
                    "enabled": False,
                    "requires_api_key": True,
                    "api_key_env": "ALPHA_VANTAGE_API_KEY"
                },
                "polygon": {
                    "enabled": False,
                    "requires_api_key": True,
                    "api_key_env": "POLYGON_API_KEY"
                }
            }
        }
        
        config_path = self.project_root / "openbb_config.json"
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Konfigurační soubor vytvořen: {config_path}")
            return True
        except Exception as e:
            logger.error(f"Chyba při vytváření konfiguračního souboru: {e}")
            return False
    
    def create_env_template(self) -> bool:
        """Vytvoří template pro environment variables."""
        logger.info("Vytváření .env template...")
        
        env_template = """
# OpenBB Platform API Keys (volitelné)
# Získejte API klíče od příslušných poskytovatelů pro rozšířené funkce

# Financial Modeling Prep - https://financialmodelingprep.com/
# FINANCIAL_MODELING_PREP_API_KEY=your_fmp_api_key_here

# Alpha Vantage - https://www.alphavantage.co/
# ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Polygon - https://polygon.io/
# POLYGON_API_KEY=your_polygon_api_key_here

# Intrinio - https://intrinio.com/
# INTRINIO_API_KEY=your_intrinio_api_key_here

# Tiingo - https://www.tiingo.com/
# TIINGO_API_KEY=your_tiingo_api_key_here

# Benzinga - https://www.benzinga.com/
# BENZINGA_API_KEY=your_benzinga_api_key_here
"""
        
        env_template_path = self.project_root / ".env.openbb.template"
        
        try:
            with open(env_template_path, 'w', encoding='utf-8') as f:
                f.write(env_template.strip())
            
            logger.info(f"✓ .env template vytvořen: {env_template_path}")
            logger.info("Zkopírujte .env.openbb.template do .env a nastavte API klíče podle potřeby")
            return True
        except Exception as e:
            logger.error(f"Chyba při vytváření .env template: {e}")
            return False
    
    def run_installation(self) -> bool:
        """Spustí kompletní instalaci."""
        logger.info("=== Spouštění OpenBB Platform instalace ===")
        
        steps = [
            ("Kontrola předpokladů", self.check_prerequisites),
            ("Klonování repozitáře", self.clone_openbb_repository),
            ("Instalace OpenBB Platform", self.install_openbb_platform),
            ("Instalace závislostí", self.install_additional_dependencies),
            ("Test importu", self.test_openbb_import),
            ("Vytvoření konfigurace", self.create_configuration_file),
            ("Vytvoření .env template", self.create_env_template)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n--- {step_name} ---")
            if not step_func():
                logger.error(f"Krok '{step_name}' selhal!")
                return False
        
        logger.info("\n=== OpenBB Platform instalace dokončena úspěšně! ===")
        logger.info("\nDalší kroky:")
        logger.info("1. Zkontrolujte .env.openbb.template a nastavte API klíče")
        logger.info("2. Spusťte backend server: cd app && python -m backend.main")
        logger.info("3. Otestujte OpenBB endpointy: GET /openbb/status")
        logger.info("4. Přečtěte si dokumentaci: docs/OPENBB_INTEGRATION.md")
        
        return True


def main():
    """Hlavní funkce skriptu."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Instalace OpenBB Platform pro AI Hedge Fund")
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Cesta k root adresáři projektu (default: aktuální adresář)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose výstup"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    installer = OpenBBInstaller(args.project_root)
    
    try:
        success = installer.run_installation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nInstalace přerušena uživatelem")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Neočekávaná chyba: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
