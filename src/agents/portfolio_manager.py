"""Portfolio Manager - Makes final trading decisions and generates orders for multiple tickers."""

import json
from typing import Any, cast, Dict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing_extensions import Literal

from src.graph.state import AgentState, show_agent_reasoning
from src.utils.llm import call_llm
from src.utils.progress import progress


class PortfolioDecision(BaseModel):
    """Rozhodnutí portfolio managera pro konkrétní ticker."""

    action: Literal["buy", "sell", "short", "cover", "hold"]
    quantity: int = Field(description="Number of shares to trade")
    confidence: float = Field(description="Confidence in the decision, between 0.0 and 100.0")
    reasoning: str = Field(description="Reasoning for the decision")


class PortfolioManagerOutput(BaseModel):
    """Výstup portfolio managera s rozhodnutími pro všechny tickery."""

    decisions: dict[str, PortfolioDecision] = Field(description="Dictionary of ticker to trading decisions")


##### Portfolio Management Agent #####
def portfolio_management_agent(state: AgentState, agent_id: str = "portfolio_manager") -> Dict[str, Any]:
    """Činí finální obchodní rozhodnutí a generuje příkazy pro více tickerů"""

    # Získání portfolia a analytických signálů
    portfolio = state["data"]["portfolio"]
    analyst_signals = state["data"]["analyst_signals"]
    tickers = state["data"]["tickers"]

    # Získání pozičních limitů, aktuálních cen a signálů pro každý ticker
    position_limits = {}
    current_prices = {}
    max_shares = {}
    signals_by_ticker = {}
    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Zpracování analytických signálů")

        # Získání pozičních limitů a aktuálních cen pro ticker
        # Nalezení odpovídajícího risk managera pro tohoto portfolio managera
        if agent_id.startswith("portfolio_manager_"):
            suffix = agent_id.split("_")[-1]
            risk_manager_id = f"risk_management_agent_{suffix}"
        else:
            risk_manager_id = "risk_management_agent"  # Záložní pro starší verze

        risk_data = analyst_signals.get(risk_manager_id, {}).get(ticker, {})
        position_limits[ticker] = risk_data.get("remaining_position_limit", 0)
        current_prices[ticker] = risk_data.get("current_price", 0)

        # Výpočet maximálního počtu akcií povolených na základě pozičního limitu a ceny
        if current_prices[ticker] > 0:
            max_shares[ticker] = int(position_limits[ticker] / current_prices[ticker])
        else:
            max_shares[ticker] = 0

        # Získání signálů pro ticker
        ticker_signals = {}
        for agent, signals in analyst_signals.items():
            # Přeskočení všech risk management agentů (mají jinou strukturu signálů)
            if not agent.startswith("risk_management_agent") and ticker in signals:
                ticker_signals[agent] = {
                    "signal": signals[ticker]["signal"],
                    "confidence": signals[ticker]["confidence"],
                }
        signals_by_ticker[ticker] = ticker_signals

    # Přidání current_prices do state dat, aby bylo dostupné v celém workflow
    state["data"]["current_prices"] = current_prices

    progress.update_status(agent_id, None, "Generování obchodních rozhodnutí")

    # Generování obchodního rozhodnutí
    result = generate_trading_decision(
        tickers=tickers,
        signals_by_ticker=signals_by_ticker,
        current_prices=current_prices,
        max_shares=max_shares,
        portfolio=portfolio,
        agent_id=agent_id,
        state=state,
    )

    # Vytvoření zprávy portfolio managementu
    message = HumanMessage(
        content=json.dumps({ticker: decision.model_dump() for ticker, decision in result.decisions.items()}),
        name=agent_id,
    )

    # Tisk rozhodnutí pokud je nastaven příznak
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(
            {ticker: decision.model_dump() for ticker, decision in result.decisions.items()}, "Portfolio Manager"
        )

    progress.update_status(agent_id, None, "Done")

    return {
        "messages": list(state["messages"]) + [message],
        "data": state["data"],
    }


def generate_trading_decision(
    tickers: list[str],
    signals_by_ticker: dict[str, dict],
    current_prices: dict[str, float],
    max_shares: dict[str, int],
    portfolio: dict[str, float],
    agent_id: str,
    state: AgentState,
) -> PortfolioManagerOutput:
    """Pokouší se získat rozhodnutí z LLM s retry logikou"""
    # Vytvoření prompt šablony
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Jste portfolio manager činící finální obchodní rozhodnutí na základě více tickerů.

DŮLEŽITÉ: Spravujete existující portfolio s aktuálními pozicemi. Portfolio_positions ukazuje:
- "long": počet akcií aktuálně držených long
- "short": počet akcií aktuálně držených short
- "long_cost_basis": průměrná cena zaplacená za long akcie
- "short_cost_basis": průměrná cena obdržená za short akcie

Obchodní pravidla:
- Pro long pozice:
  * Kupujte pouze pokud máte dostupnou hotovost
  * Prodávejte pouze pokud aktuálně držíte long akcie daného tickeru
  * Množství prodeje musí být ≤ aktuální long pozice akcií
  * Množství nákupu musí být ≤ max_shares pro daný ticker

- Pro short pozice:
  * Shortujte pouze pokud máte dostupnou marži (hodnota pozice × požadavek na marži)
  * Kryjte pouze pokud aktuálně máte short akcie daného tickeru
  * Množství krytí musí být ≤ aktuální short pozice akcií
  * Množství shortu musí respektovat požadavky na marži

- Hodnoty max_shares jsou předpočítané pro respektování pozičních limitů
- Zvažte jak long tak short příležitosti na základě signálů
- Udržujte vhodné řízení rizik s long i short expozicí

Dostupné akce:
- "buy": Otevřít nebo přidat k long pozici
- "sell": Zavřít nebo snížit long pozici (pouze pokud aktuálně držíte long akcie)
- "short": Otevřít nebo přidat k short pozici
- "cover": Zavřít nebo snížit short pozici (pouze pokud aktuálně držíte short akcie)
- "hold": Udržet aktuální pozici bez změn (množství by mělo být 0 pro hold)

Vstupy:
- signals_by_ticker: slovník ticker → signály
- max_shares: maximální akcie povolené na ticker
- portfolio_cash: aktuální hotovost v portfoliu
- portfolio_positions: aktuální pozice (long i short)
- current_prices: aktuální ceny pro každý ticker
- margin_requirement: aktuální požadavek na marži pro short pozice (např. 0.5 znamená 50%)
- total_margin_used: celková marže aktuálně používaná
""",
            ),
            (
                "human",
                """Na základě analýzy týmu udělejte svá obchodní rozhodnutí pro každý ticker.

Zde jsou signály podle tickerů:
{signals_by_ticker}

Aktuální ceny:
{current_prices}

Maximální akcie povolené pro nákupy:
{max_shares}

Hotovost portfolia: {portfolio_cash}
Aktuální pozice: {portfolio_positions}
Aktuální požadavek na marži: {margin_requirement}
Celková použitá marže: {total_margin_used}

DŮLEŽITÁ PRAVIDLA ROZHODOVÁNÍ:
- Pokud aktuálně držíte LONG akcie tickeru (long > 0), můžete:
  * HOLD: Udržet svou aktuální pozici (množství = 0)
  * SELL: Snížit/zavřít svou long pozici (množství = akcie k prodeji)
  * BUY: Přidat k své long pozici (množství = další akcie k nákupu)
  
- Pokud aktuálně držíte SHORT akcie tickeru (short > 0), můžete:
  * HOLD: Udržet svou aktuální pozici (množství = 0)
  * COVER: Snížit/zavřít svou short pozici (množství = akcie k krytí)
  * SHORT: Přidat k své short pozici (množství = další akcie k shortu)
  
- Pokud aktuálně NEDržíte žádné akcie tickeru (long = 0, short = 0), můžete:
  * HOLD: Zůstat mimo pozici (množství = 0)
  * BUY: Otevřít novou long pozici (množství = akcie k nákupu)
  * SHORT: Otevřít novou short pozici (množství = akcie k shortu)

Výstup striktně v JSON s následující strukturou:
{{
  "decisions": {{
    "TICKER1": {{
      "action": "buy/sell/short/cover/hold",
      "quantity": integer,
      "confidence": float mezi 0 a 100,
      "reasoning": "string vysvětlující vaše rozhodnutí s ohledem na aktuální pozici"
    }},
    "TICKER2": {{
      ...
    }},
    ...
  }}
}}
""",
            ),
        ]
    )

    # Generování promptu
    prompt_data = {
        "signals_by_ticker": json.dumps(signals_by_ticker, indent=2),
        "current_prices": json.dumps(current_prices, indent=2),
        "max_shares": json.dumps(max_shares, indent=2),
        "portfolio_cash": f"{portfolio.get('cash', 0):.2f}",
        "portfolio_positions": json.dumps(portfolio.get("positions", {}), indent=2),
        "margin_requirement": f"{portfolio.get('margin_requirement', 0):.2f}",
        "total_margin_used": f"{portfolio.get('margin_used', 0):.2f}",
    }

    prompt = template.invoke(prompt_data)

    # Vytvoření výchozí factory pro PortfolioManagerOutput
    def create_default_portfolio_output():
        return PortfolioManagerOutput(
            decisions={
                ticker: PortfolioDecision(
                    action="hold", quantity=0, confidence=0.0, reasoning="Chyba v portfolio managementu, výchozí hold"
                )
                for ticker in tickers
            }
        )

    result = call_llm(
        prompt=prompt,
        pydantic_model=PortfolioManagerOutput,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_portfolio_output,
    )
    return cast(PortfolioManagerOutput, result)
