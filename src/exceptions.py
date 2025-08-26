"""
Konzistentní exception hierarchy pro AI Hedge Fund projekt.

Tento modul definuje všechny custom exceptions používané v projektu
pro standardizované error handling a lepší debugging.
"""

import logging
from typing import Any, Dict, Optional


class HedgeFundError(Exception):
    """
    Základní exception třída pro všechny AI Hedge Fund chyby.

    Všechny custom exceptions v projektu by měly dědit z této třídy.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        """
        Inicializace základní HedgeFund exception.

        Args:
            message: Lidsky čitelná zpráva o chybě
            error_code: Unikátní kód chyby pro programatické zpracování
            details: Dodatečné detaily o chybě (např. ticker, agent_name, atd.)
            original_exception: Původní exception, pokud je tato chyba wrapper
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.original_exception = original_exception

        # Automaticky loguj chybu
        self._log_error()

    def _log_error(self):
        """Automaticky loguj chybu s příslušnými detaily."""
        logger = logging.getLogger(self.__class__.__module__)

        log_message = f"{self.error_code}: {self.message}"
        if self.details:
            log_message += f" | Details: {self.details}"

        if self.original_exception:
            logger.error(log_message, exc_info=self.original_exception)
        else:
            logger.error(log_message)

    def to_dict(self) -> Dict[str, Any]:
        """Převede exception na dictionary pro API responses."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# =============================================================================
# API a Data Fetching Errors
# =============================================================================


class APIError(HedgeFundError):
    """Základní třída pro všechny API-related chyby."""

    pass


class APIKeyError(APIError):
    """Chyby související s API klíči."""

    def __init__(self, api_key_name: str, message: Optional[str] = None):
        self.api_key_name = api_key_name
        default_message = f"API klíč '{api_key_name}' není dostupný nebo je neplatný"
        super().__init__(
            message or default_message, error_code="API_KEY_MISSING", details={"api_key_name": api_key_name}
        )


class APIRateLimitError(APIError):
    """Chyby související s rate limiting."""

    def __init__(self, retry_after: Optional[int] = None, message: Optional[str] = None):
        self.retry_after = retry_after
        default_message = f"API rate limit dosažen"
        if retry_after:
            default_message += f", zkuste znovu za {retry_after} sekund"

        super().__init__(message or default_message, error_code="API_RATE_LIMIT", details={"retry_after": retry_after})


class APIResponseError(APIError):
    """Chyby související s neočekávanými API responses."""

    def __init__(self, status_code: int, response_text: str, url: Optional[str] = None):
        self.status_code = status_code
        self.response_text = response_text
        self.url = url

        message = f"API request failed with status {status_code}"
        if url:
            message += f" for URL: {url}"

        super().__init__(
            message,
            error_code="API_RESPONSE_ERROR",
            details={
                "status_code": status_code,
                "response_text": response_text[:500],  # Limit response text length
                "url": url,
            },
        )


class DataFetchError(HedgeFundError):
    """Chyby při získávání finančních dat."""

    def __init__(self, ticker: str, data_type: str, message: Optional[str] = None):
        self.ticker = ticker
        self.data_type = data_type
        default_message = f"Nepodařilo se získat {data_type} data pro ticker {ticker}"

        super().__init__(
            message or default_message,
            error_code="DATA_FETCH_ERROR",
            details={"ticker": ticker, "data_type": data_type},
        )


# =============================================================================
# LLM a Model Errors
# =============================================================================


class LLMError(HedgeFundError):
    """Základní třída pro všechny LLM-related chyby."""

    pass


class ModelNotFoundError(LLMError):
    """Chyba když požadovaný model není dostupný."""

    def __init__(self, model_name: str, provider: str):
        self.model_name = model_name
        self.provider = provider

        super().__init__(
            f"Model '{model_name}' není dostupný u providera '{provider}'",
            error_code="MODEL_NOT_FOUND",
            details={"model_name": model_name, "provider": provider},
        )


class LLMResponseError(LLMError):
    """Chyby při zpracování LLM odpovědí."""

    def __init__(self, agent_name: str, message: Optional[str] = None, response_content: Optional[str] = None):
        self.agent_name = agent_name
        self.response_content = response_content
        default_message = f"Chyba při zpracování LLM odpovědi pro agenta {agent_name}"

        super().__init__(
            message or default_message,
            error_code="LLM_RESPONSE_ERROR",
            details={
                "agent_name": agent_name,
                "response_content": response_content[:200] if response_content else None,
            },
        )


class LLMTimeoutError(LLMError):
    """Chyba při timeout LLM requestu."""

    def __init__(self, agent_name: str, timeout_seconds: int):
        self.agent_name = agent_name
        self.timeout_seconds = timeout_seconds

        super().__init__(
            f"LLM request pro agenta {agent_name} překročil timeout {timeout_seconds}s",
            error_code="LLM_TIMEOUT",
            details={"agent_name": agent_name, "timeout_seconds": timeout_seconds},
        )


# =============================================================================
# Agent a Analysis Errors
# =============================================================================


class AgentError(HedgeFundError):
    """Základní třída pro všechny agent-related chyby."""

    pass


class AgentNotFoundError(AgentError):
    """Chyba když požadovaný agent není dostupný."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

        super().__init__(
            f"Agent '{agent_name}' není dostupný", error_code="AGENT_NOT_FOUND", details={"agent_name": agent_name}
        )


class AgentAnalysisError(AgentError):
    """Chyby při analýze agenta."""

    def __init__(self, agent_name: str, ticker: str, message: Optional[str] = None):
        self.agent_name = agent_name
        self.ticker = ticker
        default_message = f"Chyba při analýze {ticker} agentem {agent_name}"

        super().__init__(
            message or default_message,
            error_code="AGENT_ANALYSIS_ERROR",
            details={"agent_name": agent_name, "ticker": ticker},
        )


class InsufficientDataError(AgentError):
    """Chyba při nedostatku dat pro analýzu."""

    def __init__(self, ticker: str, required_data: str, agent_name: Optional[str] = None):
        self.ticker = ticker
        self.required_data = required_data
        self.agent_name = agent_name

        message = f"Nedostatek dat pro analýzu {ticker}: chybí {required_data}"
        if agent_name:
            message += f" (agent: {agent_name})"

        super().__init__(
            message,
            error_code="INSUFFICIENT_DATA",
            details={"ticker": ticker, "required_data": required_data, "agent_name": agent_name},
        )


# =============================================================================
# Portfolio a Trading Errors
# =============================================================================


class PortfolioError(HedgeFundError):
    """Základní třída pro všechny portfolio-related chyby."""

    pass


class InsufficientFundsError(PortfolioError):
    """Chyba při nedostatku prostředků pro obchod."""

    def __init__(self, required_amount: float, available_amount: float, ticker: str):
        self.required_amount = required_amount
        self.available_amount = available_amount
        self.ticker = ticker

        super().__init__(
            f"Nedostatek prostředků pro nákup {ticker}: potřeba ${required_amount:,.2f}, dostupné ${available_amount:,.2f}",
            error_code="INSUFFICIENT_FUNDS",
            details={"required_amount": required_amount, "available_amount": available_amount, "ticker": ticker},
        )


class InvalidPositionError(PortfolioError):
    """Chyba při neplatné pozici v portfoliu."""

    def __init__(self, ticker: str, message: Optional[str] = None):
        self.ticker = ticker
        default_message = f"Neplatná pozice pro ticker {ticker}"

        super().__init__(message or default_message, error_code="INVALID_POSITION", details={"ticker": ticker})


# =============================================================================
# Configuration a Validation Errors
# =============================================================================


class ConfigurationError(HedgeFundError):
    """Chyby v konfiguraci systému."""

    def __init__(self, config_key: str, message: Optional[str] = None):
        self.config_key = config_key
        default_message = f"Chyba v konfiguraci: {config_key}"

        super().__init__(
            message or default_message, error_code="CONFIGURATION_ERROR", details={"config_key": config_key}
        )


class ValidationError(HedgeFundError):
    """Chyby při validaci vstupních dat."""

    def __init__(self, field_name: str, value: Any, message: Optional[str] = None):
        self.field_name = field_name
        self.value = value
        default_message = f"Neplatná hodnota pro pole {field_name}: {value}"

        super().__init__(
            message or default_message,
            error_code="VALIDATION_ERROR",
            details={"field_name": field_name, "value": str(value)},
        )


# =============================================================================
# Utility Functions
# =============================================================================


def handle_exception(func):
    """
    Decorator pro automatické zachycení a konverzi exceptions na HedgeFundError.

    Použití:
        @handle_exception
        def some_function():
            # kód který může vyhodit exception
            pass
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HedgeFundError:
            # Již je to naše exception, jen ji předáme dál
            raise
        except Exception as e:
            # Konvertuj na naši exception
            raise HedgeFundError(
                message=f"Neočekávaná chyba v {func.__name__}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                details={"function": func.__name__},
                original_exception=e,
            )

    return wrapper


def safe_execute(func, default_value=None, error_message: Optional[str] = None):
    """
    Bezpečně vykonej funkci a vrať default_value při chybě.

    Args:
        func: Funkce k vykonání
        default_value: Hodnota k vrácení při chybě
        error_message: Custom error message

    Returns:
        Výsledek funkce nebo default_value při chybě
    """
    try:
        return func()
    except Exception as e:
        logger = logging.getLogger(__name__)
        message = error_message or f"Chyba při vykonávání {func.__name__}: {str(e)}"
        logger.warning(message)
        return default_value
