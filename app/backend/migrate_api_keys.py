#!/usr/bin/env python3
"""
Script pro migraci API klíčů z environment variables do databáze.
Spustí se jednou pro přenos existujících API klíčů.
"""

import os
import sys
from pathlib import Path

# Přidej backend directory do Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    from database.connection import get_db
    from dotenv import load_dotenv
    from repositories.api_key_repository import ApiKeyRepository
    from services.api_key_service import ApiKeyService
except ImportError as e:
    print(f"❌ Chyba při importu: {e}")
    print("Ujisti se, že jsi v app/backend directory a máš nainstalované dependencies")
    sys.exit(1)


def migrate_api_keys():
    """Přenese API klíče z environment variables do databáze."""

    try:
        # Load environment variables z root directory
        root_env_path = backend_dir.parent.parent / ".env"
        if root_env_path.exists():
            load_dotenv(root_env_path)
            print(f"✅ Načten .env soubor z: {root_env_path}")
        else:
            print(f"⚠️  .env soubor nenalezen v: {root_env_path}")
            return

        # Mapping environment variables na provider názvy
        env_to_provider = {
            # LLM API klíče
            "OPENAI_API_KEY": "OPENAI_API_KEY",
            "GROQ_API_KEY": "GROQ_API_KEY",
            "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
            "DEEPSEEK_API_KEY": "DEEPSEEK_API_KEY",
            "GOOGLE_API_KEY": "GOOGLE_API_KEY",
            "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
            # Finanční data API klíče
            "FINANCIAL_DATASETS_API_KEY": "FINANCIAL_DATASETS_API_KEY",
            # OpenBB Platform API klíče
            "FMP_API_KEY": "FMP_API_KEY",
            "ALPHA_VANTAGE_API_KEY": "ALPHA_VANTAGE_API_KEY",
            "POLYGON_API_KEY": "POLYGON_API_KEY",
            "TIINGO_API_KEY": "TIINGO_API_KEY",
            "INTRINIO_API_KEY": "INTRINIO_API_KEY",
            "BENZINGA_API_KEY": "BENZINGA_API_KEY",
            "FRED_API_KEY": "FRED_API_KEY",
            "QUANDL_API_KEY": "QUANDL_API_KEY",
            "EOD_API_KEY": "EOD_API_KEY",
            "TRADIER_API_KEY": "TRADIER_API_KEY",
            "CBOE_API_KEY": "CBOE_API_KEY",
            "NASDAQ_API_KEY": "NASDAQ_API_KEY",
        }

        # Získej databázové připojení
        try:
            db = next(get_db())
            api_key_service = ApiKeyService(db)
            api_key_repository = ApiKeyRepository(db)
        except Exception as e:
            print(f"❌ Chyba při připojení k databázi: {e}")
            return

        print("🔄 Migrace API klíčů z environment variables do databáze...")

        migrated_count = 0
        skipped_count = 0

        for env_var, provider in env_to_provider.items():
            api_key = os.getenv(env_var)

            if api_key and not api_key.startswith("your-") and len(api_key) > 10:
                # Platný API klíč nalezen
                try:
                    # Zkontroluj, zda už klíč v databázi existuje
                    existing_keys = api_key_service.get_api_keys_dict()

                    if provider in existing_keys and existing_keys[provider]:
                        print(f"⏭️  {provider}: Klíč už existuje v databázi")
                        skipped_count += 1
                    else:
                        # Přidej klíč do databáze
                        api_key_repository.create_or_update_api_key(
                            provider=provider,
                            key_value=api_key,
                            description=f"Migrováno z environment variable {env_var}",
                        )
                        masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else api_key
                        print(f"✅ {provider}: Klíč úspěšně migrován ({masked_key})")
                        migrated_count += 1

                except Exception as e:
                    print(f"❌ {provider}: Chyba při migraci - {e}")
                    skipped_count += 1
            else:
                if api_key and api_key.startswith("your-"):
                    print(f"⚠️  {provider}: Placeholder hodnota, přeskakuji")
                elif api_key and len(api_key) <= 10:
                    print(f"⚠️  {provider}: Klíč příliš krátký, přeskakuji")
                else:
                    print(f"⚠️  {provider}: Klíč nenalezen v environment variables")
                skipped_count += 1

        print(f"\n📊 Výsledky migrace:")
        print(f"   ✅ Migrováno: {migrated_count} klíčů")
        print(f"   ⏭️  Přeskočeno: {skipped_count} klíčů")

        # Zobraz aktuální stav databáze
        try:
            print(f"\n📋 Aktuální API klíče v databázi:")
            current_keys = api_key_service.get_api_keys_dict()
            for provider, key in current_keys.items():
                if key:
                    masked_key = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else key
                    print(f"   ✅ {provider}: {masked_key}")
                else:
                    print(f"   ❌ {provider}: Není nastaven")
        except Exception as e:
            print(f"❌ Chyba při zobrazení aktuálního stavu: {e}")

    except Exception as e:
        print(f"❌ Neočekávaná chyba: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    migrate_api_keys()
