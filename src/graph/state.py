"""
Definice stavu agentů a pomocné funkce pro AI Hedge Fund systém.

Tento modul obsahuje TypedDict definici pro AgentState a utility funkce
pro zobrazení reasoning výstupů agentů.
"""

import json
import operator
from typing import Any

from langchain_core.messages import BaseMessage
from typing_extensions import Annotated, Sequence, TypedDict


def merge_dicts(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Sloučí dva slovníky dohromady."""
    return {**a, **b}


# Definice stavu agenta
class AgentState(TypedDict):
    """
    Stav agenta obsahující zprávy, data a metadata.

    Attributes:
        messages: Sekvence zpráv s automatickým přidáváním
        data: Slovník dat s automatickým slučováním
        metadata: Slovník metadat s automatickým slučováním
    """

    messages: Annotated[Sequence[BaseMessage], operator.add]
    data: Annotated[dict[str, Any], merge_dicts]
    metadata: Annotated[dict[str, Any], merge_dicts]


def show_agent_reasoning(output, agent_name):
    """
    Zobrazí reasoning výstup agenta v přehledném formátu.

    Args:
        output: Výstup agenta k zobrazení
        agent_name: Jméno agenta pro hlavičku
    """
    print(f"\n{'=' * 10} {agent_name.center(28)} {'=' * 10}")

    def convert_to_serializable(obj):
        """Převede objekt na JSON serializovatelný formát."""
        if hasattr(obj, "to_dict"):  # Zpracování Pandas Series/DataFrame
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):  # Zpracování vlastních objektů
            return obj.__dict__
        elif isinstance(obj, (int, float, bool, str)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: convert_to_serializable(value) for key, value in obj.items()}
        else:
            return str(obj)  # Fallback na string reprezentaci

    if isinstance(output, (dict, list)):
        # Převod výstupu na JSON serializovatelný formát
        serializable_output = convert_to_serializable(output)
        print(json.dumps(serializable_output, indent=2))
    else:
        try:
            # Parsování stringu jako JSON a pretty print
            parsed_output = json.loads(output)
            print(json.dumps(parsed_output, indent=2))
        except json.JSONDecodeError:
            # Fallback na původní string pokud není platný JSON
            print(output)

    print("=" * 48)
