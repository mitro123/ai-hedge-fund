"""
Hlavní FastAPI aplikace pro AI Hedge Fund backend.

Tento modul obsahuje konfiguraci FastAPI serveru, middleware pro CORS,
inicializaci databáze a správu životního cyklu aplikace včetně Ollama integrace.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Načtení proměnných prostředí ze .env souboru
load_dotenv()

from app.backend.database.connection import engine
from app.backend.database.models import Base
from app.backend.routes import api_router
from app.backend.services.ollama_service import ollama_service

# Konfigurace logování
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Správce životního cyklu aplikace pro startup a shutdown události."""
    # Spuštění aplikace
    try:
        logger.info("Kontrola dostupnosti Ollama...")
        status = await ollama_service.check_ollama_status()

        if status["installed"]:
            if status["running"]:
                logger.info(f"✓ Ollama je nainstalována a běží na {status['server_url']}")
                if status["available_models"]:
                    logger.info(f"✓ Dostupné modely: {', '.join(status['available_models'])}")
                else:
                    logger.info("ℹ Žádné modely nejsou aktuálně staženy")
            else:
                logger.info("ℹ Ollama je nainstalována, ale neběží")
                logger.info("ℹ Můžete ji spustit ze stránky Nastavení nebo manuálně pomocí 'ollama serve'")
        else:
            logger.info("ℹ Ollama není nainstalována. Nainstalujte ji pro použití lokálních modelů.")
            logger.info("ℹ Navštivte https://ollama.com pro stažení a instalaci Ollama")

    except Exception as e:
        logger.warning(f"Nelze zkontrolovat stav Ollama: {e}")
        logger.info("ℹ Ollama integrace je dostupná, pokud ji nainstalujete později")

    yield

    # Ukončení aplikace
    logger.info("Ukončování AI Hedge Fund API...")


app = FastAPI(
    title="AI Hedge Fund API", description="Backend API for AI Hedge Fund", version="0.1.0", lifespan=lifespan
)

# Inicializace databázových tabulek (bezpečné pro opakované spuštění)
Base.metadata.create_all(bind=engine)

# Konfigurace CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],  # Frontend URL adresy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Zahrnutí všech routes
app.include_router(api_router)
