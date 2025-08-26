"""AI Hedge Fund - Hlavní modul pro spuštění hedge fund systému s AI agenty."""

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import questionary
from colorama import Fore, init, Style
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from src.agents.portfolio_manager import portfolio_management_agent
from src.agents.risk_manager import risk_management_agent
from src.graph.state import AgentState
from src.llm.models import get_model_info, LLM_ORDER, ModelProvider, OLLAMA_LLM_ORDER
from src.utils.analysts import ANALYST_ORDER, get_analyst_nodes
from src.utils.display import print_trading_output
from src.utils.ollama import ensure_ollama_and_model
from src.utils.progress import progress
from src.utils.visualize import save_graph_as_png

# Load environment variables from .env file
load_dotenv()

init(autoreset=True)


def parse_hedge_fund_response(response: str) -> Optional[Dict[str, Any]]:
    """Parses a JSON string and returns a dictionary."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}\nResponse: {repr(response)}")
        return None
    except TypeError as e:
        print(f"Invalid response type (expected string, got {type(response).__name__}): {e}")
        return None


def run_hedge_fund(
    fund_tickers: List[str],
    fund_start_date: str,
    fund_end_date: str,
    fund_portfolio: Dict[str, Any],
    show_reasoning: bool = False,
    selected_analysts: Optional[List[str]] = None,
    model_name: str = "gpt-4.1",
    model_provider: str = "OpenAI",
) -> Dict[str, Any]:
    """Spustí hedge fund systém s danými parametry."""
    # Start progress tracking
    progress.start()

    try:
        # Create a new workflow if analysts are customized
        if selected_analysts:
            workflow = create_workflow(selected_analysts)
            agent = workflow.compile()
        else:
            # Use default workflow with all analysts
            default_workflow = create_workflow()
            agent = default_workflow.compile()

        final_state = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="Make trading decisions based on the provided data.",
                    )
                ],
                "data": {
                    "tickers": fund_tickers,
                    "portfolio": fund_portfolio,
                    "start_date": fund_start_date,
                    "end_date": fund_end_date,
                    "analyst_signals": {},
                },
                "metadata": {
                    "show_reasoning": show_reasoning,
                    "model_name": model_name,
                    "model_provider": model_provider,
                },
            },
        )

        return {
            "decisions": parse_hedge_fund_response(final_state["messages"][-1].content),
            "analyst_signals": final_state["data"]["analyst_signals"],
        }
    finally:
        # Stop progress tracking
        progress.stop()


def start(state: AgentState) -> AgentState:
    """Initialize the workflow with the input message."""
    return state


def create_workflow(selected_analysts: Optional[List[str]] = None) -> StateGraph:
    """Create the workflow with selected analysts."""
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)

    # Get analyst nodes from the configuration
    analyst_nodes = get_analyst_nodes()

    # Default to all analysts if none selected
    if selected_analysts is None:
        selected_analysts = list(analyst_nodes.keys())

    # Add selected analyst nodes
    for analyst_key in selected_analysts:
        node_name, node_func = analyst_nodes[analyst_key]
        workflow.add_node(node_name, node_func)
        workflow.add_edge("start_node", node_name)

    # Always add risk and portfolio management
    workflow.add_node("risk_management_agent", risk_management_agent)
    workflow.add_node("portfolio_manager", portfolio_management_agent)

    # Connect selected analysts to risk management
    for analyst_key in selected_analysts:
        node_name = analyst_nodes[analyst_key][0]
        workflow.add_edge(node_name, "risk_management_agent")

    workflow.add_edge("risk_management_agent", "portfolio_manager")
    workflow.add_edge("portfolio_manager", END)

    workflow.set_entry_point("start_node")
    return workflow


def validate_date_format(date_string: str, date_name: str) -> None:
    """Validuje formát data."""
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{date_name} must be in YYYY-MM-DD format") from exc


def select_analysts() -> List[str]:
    """Umožní uživateli vybrat analytiky."""
    choices = questionary.checkbox(
        "Select your AI analysts.",
        choices=[questionary.Choice(display, value=value) for display, value in ANALYST_ORDER],
        instruction=(
            "\n\nInstructions: \n"
            "1. Press Space to select/unselect analysts.\n"
            "2. Press 'a' to select/unselect all.\n"
            "3. Press Enter when done to run the hedge fund.\n"
        ),
        validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not choices:
        print("\n\nInterrupt received. Exiting...")
        sys.exit(0)

    print(
        f"\nSelected analysts: {', '.join(Fore.GREEN + choice.title().replace('_', ' ') + Style.RESET_ALL for choice in choices)}\n"
    )

    return choices


def select_ollama_model() -> str:
    """Vybere Ollama model."""
    print(f"{Fore.CYAN}Using Ollama for local LLM inference.{Style.RESET_ALL}")

    # Select from Ollama-specific models
    model_name: str = questionary.select(
        "Select your Ollama model:",
        choices=[questionary.Choice(display, value=value) for display, value, _ in OLLAMA_LLM_ORDER],
        style=questionary.Style(
            [
                ("selected", "fg:green bold"),
                ("pointer", "fg:green bold"),
                ("highlighted", "fg:green"),
                ("answer", "fg:green bold"),
            ]
        ),
    ).ask()

    if not model_name:
        print("\n\nInterrupt received. Exiting...")
        sys.exit(0)

    if model_name == "-":
        custom_model = questionary.text("Enter the custom model name:").ask()
        if not custom_model:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)
        model_name = custom_model

    # Ensure Ollama is installed, running, and the model is available
    if not ensure_ollama_and_model(model_name):
        print(f"{Fore.RED}Cannot proceed without Ollama and the selected model.{Style.RESET_ALL}")
        sys.exit(1)

    print(
        f"\nSelected {Fore.CYAN}Ollama{Style.RESET_ALL} model: "
        f"{Fore.GREEN + Style.BRIGHT}{model_name}{Style.RESET_ALL}\n"
    )

    return model_name


def select_cloud_model() -> tuple[str, str]:
    """Vybere cloud-based LLM model."""
    # Use the standard cloud-based LLM selection
    model_choice = questionary.select(
        "Select your LLM model:",
        choices=[questionary.Choice(display, value=(name, provider)) for display, name, provider in LLM_ORDER],
        style=questionary.Style(
            [
                ("selected", "fg:green bold"),
                ("pointer", "fg:green bold"),
                ("highlighted", "fg:green"),
                ("answer", "fg:green bold"),
            ]
        ),
    ).ask()

    if not model_choice:
        print("\n\nInterrupt received. Exiting...")
        sys.exit(0)

    selected_model_name, selected_model_provider = model_choice

    # Get model info using the helper function
    model_info = get_model_info(selected_model_name, selected_model_provider)
    if model_info:
        if model_info.is_custom():
            custom_model = questionary.text("Enter the custom model name:").ask()
            if not custom_model:
                print("\n\nInterrupt received. Exiting...")
                sys.exit(0)
            selected_model_name = custom_model

        print(
            f"\nSelected {Fore.CYAN}{selected_model_provider}{Style.RESET_ALL} model: "
            f"{Fore.GREEN + Style.BRIGHT}{selected_model_name}{Style.RESET_ALL}\n"
        )
    else:
        print(f"\nSelected model: " f"{Fore.GREEN + Style.BRIGHT}{selected_model_name}{Style.RESET_ALL}\n")

    return selected_model_name, selected_model_provider


def main() -> None:
    """Hlavní funkce aplikace."""
    parser = argparse.ArgumentParser(description="Run the hedge fund trading system")
    parser.add_argument(
        "--initial-cash", type=float, default=100000.0, help="Initial cash position. Defaults to 100000.0"
    )
    parser.add_argument(
        "--margin-requirement", type=float, default=0.0, help="Initial margin requirement. Defaults to 0.0"
    )
    parser.add_argument("--tickers", type=str, required=True, help="Comma-separated list of stock ticker symbols")
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD). Defaults to 3 months before end date",
    )
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD). Defaults to today")
    parser.add_argument("--show-reasoning", action="store_true", help="Show reasoning from each agent")
    parser.add_argument("--show-agent-graph", action="store_true", help="Show the agent graph")
    parser.add_argument("--ollama", action="store_true", help="Use Ollama for local LLM inference")

    args = parser.parse_args()

    # Parse tickers from comma-separated string
    tickers = [ticker.strip() for ticker in args.tickers.split(",")]

    # Select analysts
    selected_analysts = select_analysts()

    # Select LLM model based on whether Ollama is being used
    if args.ollama:
        model_name = select_ollama_model()
        model_provider = ModelProvider.OLLAMA.value
    else:
        model_name, model_provider = select_cloud_model()

    # Create the workflow with selected analysts
    workflow = create_workflow(selected_analysts)
    app = workflow.compile()

    if args.show_agent_graph:
        graph_file_path = ""
        if selected_analysts is not None:
            for selected_analyst in selected_analysts:
                graph_file_path += selected_analyst + "_"
            graph_file_path += "graph.png"
        save_graph_as_png(app, graph_file_path)

    # Validate dates if provided
    if args.start_date:
        validate_date_format(args.start_date, "Start date")

    if args.end_date:
        validate_date_format(args.end_date, "End date")

    # Set the start and end dates
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    if not args.start_date:
        # Calculate 3 months before end_date
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_date_obj - relativedelta(months=3)).strftime("%Y-%m-%d")
    else:
        start_date = args.start_date

    # Initialize portfolio with cash amount and stock positions
    portfolio = {
        "cash": args.initial_cash,  # Initial cash amount
        "margin_requirement": args.margin_requirement,  # Initial margin requirement
        "margin_used": 0.0,  # total margin usage across all short positions
        "positions": {
            ticker: {
                "long": 0,  # Number of shares held long
                "short": 0,  # Number of shares held short
                "long_cost_basis": 0.0,  # Average cost basis for long positions
                "short_cost_basis": 0.0,  # Average price at which shares were sold short
                "short_margin_used": 0.0,  # Dollars of margin used for this ticker's short
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,  # Realized gains from long positions
                "short": 0.0,  # Realized gains from short positions
            }
            for ticker in tickers
        },
    }

    # Run the hedge fund
    result = run_hedge_fund(
        fund_tickers=tickers,
        fund_start_date=start_date,
        fund_end_date=end_date,
        fund_portfolio=portfolio,
        show_reasoning=args.show_reasoning,
        selected_analysts=selected_analysts,
        model_name=model_name,
        model_provider=model_provider,
    )
    print_trading_output(result)


if __name__ == "__main__":
    main()
