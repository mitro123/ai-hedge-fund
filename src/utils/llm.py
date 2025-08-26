"""Pomocné funkce pro práci s LLM modely"""

import json
import logging
from typing import Any, Callable, cast, Dict, Optional, Tuple, Type, Union

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

from src.exceptions import LLMError, LLMResponseError, LLMTimeoutError, ModelNotFoundError
from src.graph.state import AgentState
from src.llm.models import get_model, get_model_info, ModelProvider
from src.utils.progress import progress


def call_llm(
    prompt: Any,
    pydantic_model: Type[BaseModel],
    agent_name: Optional[str] = None,
    state: Optional[AgentState] = None,
    max_retries: int = 3,
    default_factory: Optional[Callable] = None,
) -> BaseModel:
    """
    Provádí volání LLM s retry logikou, zpracovává modely s i bez JSON podpory.

    Args:
        prompt: Prompt k odeslání do LLM
        pydantic_model: Pydantic model třída pro strukturování výstupu
        agent_name: Volitelné jméno agenta pro progress aktualizace a konfiguraci modelu
        state: Volitelný state objekt pro extrakci agent-specifické konfigurace modelu
        max_retries: Maximální počet opakování (výchozí: 3)
        default_factory: Volitelná factory funkce pro vytvoření výchozí odpovědi při selhání

    Returns:
        Instance specifikovaného Pydantic modelu

    Raises:
        LLMResponseError: Když LLM odpověď nelze parsovat nebo je neplatná
        LLMTimeoutError: Když LLM volání vyprší po maximálním počtu opakování
        ModelNotFoundError: Když specifikovaný model není dostupný
        LLMError: Pro ostatní LLM-související chyby po maximálním počtu opakování
    """

    # Extrakce konfigurace modelu pokud je state a agent_name k dispozici
    if state and agent_name:
        model_name, model_provider = get_agent_model_config(state, agent_name)
    else:
        # Použití systémových výchozích hodnot když není state nebo agent_name
        model_name = "anthropic/claude-3.5-sonnet"
        model_provider = "OpenRouter"

    # Extrakce API klíčů ze state pokud jsou k dispozici
    api_keys = None
    if state:
        request = state.get("metadata", {}).get("request")
        if request and hasattr(request, "api_keys"):
            api_keys = request.api_keys

    model_info = get_model_info(model_name, model_provider)
    
    # Konverze model_provider na ModelProvider enum pokud je to string
    if isinstance(model_provider, str):
        try:
            provider_enum = ModelProvider(model_provider)
        except ValueError:
            # Pokud string není platná hodnota enum, zkusíme najít odpovídající enum
            provider_enum = None
            for provider in ModelProvider:
                if provider.value == model_provider:
                    provider_enum = provider
                    break
            if provider_enum is None:
                raise ModelNotFoundError(model_name=model_name, provider=model_provider)
    else:
        provider_enum = model_provider
    
    llm = get_model(model_name, provider_enum, api_keys or {})

    # Pro modely bez JSON podpory můžeme použít strukturovaný výstup
    if not (model_info and not model_info.has_json_mode()):
        if llm is not None and hasattr(llm, "with_structured_output"):
            llm = llm.with_structured_output(
                pydantic_model,
                method="json_mode",
            )

    # Volání LLM s opakováním
    for attempt in range(max_retries):
        try:
            # Volání LLM
            if llm is not None and hasattr(llm, "invoke"):
                result = llm.invoke(prompt)
            else:
                raise LLMError(
                    message="LLM objekt není dostupný nebo nemá invoke metodu", error_code="LLM_OBJECT_ERROR"
                )

            # Pro modely bez JSON podpory musíme extrahovat a parsovat JSON manuálně
            if model_info and not model_info.has_json_mode():
                content = getattr(result, "content", None) if result else None
                if content is not None:
                    parsed_result = extract_json_from_response(content)
                else:
                    raise LLMResponseError(
                        agent_name=agent_name or "neznamy",
                        message="LLM odpověď neobsahuje content atribut",
                        response_content="Žádný obsah",
                    )
                if parsed_result:
                    return pydantic_model(**parsed_result)
                else:
                    raise LLMResponseError(
                        agent_name=agent_name or "neznamy",
                        message=f"Nepodařilo se extrahovat platný JSON z LLM odpovědi pro model {model_name}",
                        response_content=str(content)[:500] if content else "Žádný obsah",
                    )
            else:
                # Pro modely s JSON podporou, result je už správný typ
                if isinstance(result, BaseModel):
                    return result
                else:
                    # Fallback pro neočekávané typy
                    return create_default_response(pydantic_model)

        except LLMResponseError:
            # Znovu vyhodit LLM-specifické chyby bez úprav
            raise
        except TimeoutError as e:
            if agent_name:
                progress.update_status(agent_name, None, f"Timeout - pokus {attempt + 1}/{max_retries}")

            if attempt == max_retries - 1:
                raise LLMTimeoutError(agent_name=agent_name or "neznamy", timeout_seconds=30)  # Výchozí timeout hodnota
        except Exception as e:
            if agent_name:
                progress.update_status(agent_name, None, f"Chyba - pokus {attempt + 1}/{max_retries}")

            if attempt == max_retries - 1:
                # Kontrola zda se jedná o chybu související s modelem
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ["model", "not found", "invalid model", "unknown model"]):
                    raise ModelNotFoundError(model_name=model_name, provider=model_provider)
                else:
                    raise LLMError(
                        message=f"LLM volání selhalo po {max_retries} pokusech pro model {model_name}",
                        error_code="LLM_CALL_FAILED",
                        details={
                            "model_name": model_name,
                            "model_provider": model_provider,
                            "agent_name": agent_name,
                            "max_retries": max_retries,
                            "original_error": str(e),
                        },
                    )

                # Fallback na výchozí odpověď (toto by nemělo být dosaženo kvůli raises výše)
                if default_factory:
                    return default_factory()
                return create_default_response(pydantic_model)

    # Toto by nikdy nemělo být dosaženo kvůli retry logice výše
    return create_default_response(pydantic_model)


def create_default_response(model_class: Type[BaseModel]) -> BaseModel:
    """Vytváří bezpečnou výchozí odpověď na základě polí modelu."""
    default_values = {}
    for field_name, field in model_class.model_fields.items():
        if field.annotation == str:
            default_values[field_name] = "Chyba v analýze, používá se výchozí hodnota"
        elif field.annotation == float:
            default_values[field_name] = 0.0
        elif field.annotation == int:
            default_values[field_name] = 0
        elif hasattr(field.annotation, "__origin__") and getattr(field.annotation, "__origin__", None) == dict:
            default_values[field_name] = {}
        else:
            # Pro ostatní typy (jako Literal), zkusit použít první povolenou hodnotu
            if hasattr(field.annotation, "__args__") and getattr(field.annotation, "__args__", None):
                default_values[field_name] = getattr(field.annotation, "__args__")[0]
            else:
                default_values[field_name] = None

    return model_class(**default_values)


def extract_json_from_response(content: str) -> Optional[Dict[str, Any]]:
    """
    Extrahuje JSON z markdown-formátované odpovědi.

    Args:
        content: Obsah odpovědi pro extrakci JSON

    Returns:
        Parsovaný JSON slovník nebo None pokud extrakce selže

    Raises:
        LLMResponseError: Pokud extrakce JSON selže s neplatným formátem
    """
    try:
        json_start = content.find("```json")
        if json_start != -1:
            json_text = content[json_start + 7 :]  # Přeskočit ```json
            json_end = json_text.find("```")
            if json_end != -1:
                json_text = json_text[:json_end].strip()
                return json.loads(json_text)
        return None
    except json.JSONDecodeError as e:
        raise LLMResponseError(
            agent_name="json_extraktor",
            message=f"Nepodařilo se parsovat JSON z odpovědi: {str(e)}",
            response_content=content[:200],
        )
    except Exception as e:
        # Pro ostatní neočekávané chyby, logovat a vrátit None pro graceful degradaci
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Neočekávaná chyba při extrakci JSON z odpovědi: {e}")
        return None


def get_agent_model_config(state: Union[AgentState, Dict[str, Any]], agent_name: str) -> Tuple[str, str]:
    """
    Získá konfiguraci modelu pro specifického agenta ze state.
    Fallback na globální konfiguraci modelu pokud agent-specifická konfigurace není dostupná.
    Vždy vrací platné model_name a model_provider hodnoty.

    Args:
        state: State objekt obsahující metadata a konfiguraci
        agent_name: Jméno agenta pro který získáváme konfiguraci

    Returns:
        Tuple[str, str]: (model_name, model_provider)
    """
    request = state.get("metadata", {}).get("request")

    if request and hasattr(request, "get_agent_model_config"):
        # Získání agent-specifické konfigurace modelu
        try:
            model_name, model_provider = request.get_agent_model_config(agent_name)
            # Zajištění že máme platné hodnoty
            if model_name and model_provider:
                # Konverze ModelProvider enum na jeho hodnotu
                if isinstance(model_provider, ModelProvider):
                    provider_str = model_provider.value
                else:
                    provider_str = str(model_provider)
                return model_name, provider_str
        except Exception as e:
            # Logování chyby a pokračování s fallback
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Chyba při získávání agent-specifické konfigurace pro {agent_name}: {e}")

    # Fallback na globální konfiguraci (systémové výchozí hodnoty)
    model_name = state.get("metadata", {}).get("model_name") or "anthropic/claude-3.5-sonnet"
    model_provider = state.get("metadata", {}).get("model_provider") or "OpenRouter"

    # Konverze enum na string pokud je to nutné
    if isinstance(model_provider, ModelProvider):
        provider_str = model_provider.value
    else:
        provider_str = str(model_provider)

    return model_name, provider_str
