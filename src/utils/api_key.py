import os
from typing import Any, Dict, Optional, TYPE_CHECKING, Union

from src.exceptions import APIKeyError

if TYPE_CHECKING:
    from src.graph.state import AgentState


def get_api_key_from_state(state: Union[Dict[str, Any], "AgentState"], api_key_name: str) -> str:
    """
    Get an API key from the state object or environment variables.

    Args:
        state: State object containing request metadata
        api_key_name: Name of the API key to retrieve

    Returns:
        str: The API key value

    Raises:
        APIKeyError: If the API key is not found or is empty
    """
    api_key = None

    # Try to get from state first
    if state and state.get("metadata", {}).get("request"):
        request = state["metadata"]["request"]
        if hasattr(request, "api_keys") and request.api_keys:
            api_key = request.api_keys.get(api_key_name)

    # Fallback: try to get from environment variables
    if not api_key:
        api_key = os.getenv(api_key_name)

    # Validate that we have a non-empty API key
    if not api_key or api_key.strip() == "":
        raise APIKeyError(api_key_name)

    return api_key


def get_api_key_from_state_optional(state: Union[Dict[str, Any], "AgentState"], api_key_name: str) -> Optional[str]:
    """
    Get an API key from the state object or environment variables, returning None if not found.

    This is a non-throwing version for cases where the API key is optional.

    Args:
        state: State object containing request metadata
        api_key_name: Name of the API key to retrieve

    Returns:
        Optional[str]: The API key value or None if not found
    """
    try:
        return get_api_key_from_state(state, api_key_name)
    except APIKeyError:
        return None
