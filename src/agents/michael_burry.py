"""Michael Burry Agent - Deep-value contrarian analýza zaměřená na tvrdá čísla a katalyzátory."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, cast, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing_extensions import Literal

from src.exceptions import APIKeyError
from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_company_news, get_financial_metrics, get_insider_trades, get_market_cap, search_line_items
from src.utils.api_key import get_api_key_from_state
from src.utils.constants import COMMODITY_SYMBOLS
from src.utils.llm import call_llm
from src.utils.progress import progress


class MichaelBurrySignal(BaseModel):
    """Schema returned by the LLM."""

    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float  # 0–100
    reasoning: str


def michael_burry_agent(state: AgentState, agent_id: str = "michael_burry_agent") -> Dict[str, Any]:
    """Analyzuje akcie pomocí Michael Burry's deep-value, contrarian frameworku."""
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")
    if api_key is None:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")

    data = state["data"]
    end_date: str = data["end_date"]  # YYYY‑MM‑DD
    tickers: List[str] = data["tickers"]

    # Hledáme jeden rok zpět pro insider obchody / zpravodajský tok
    start_date = (datetime.fromisoformat(end_date) - timedelta(days=365)).date().isoformat()

    analysis_data: Dict[str, Dict[str, Any]] = {}
    burry_analysis: Dict[str, Dict[str, Any]] = {}

    for ticker in tickers:
        # Skip commodity symbols as Michael Burry analysis is designed for stocks
        if ticker in COMMODITY_SYMBOLS:
            progress.update_status(agent_id, ticker, "Přeskakuji komoditu")
            burry_analysis[ticker] = {
                "signal": "neutral",
                "confidence": 0.0,
                "reasoning": f"Michael Burry analýza není vhodná pro komodity ({ticker}). Komodity jsou analyzovány specializovaným komoditním agentem.",
            }
            progress.update_status(agent_id, ticker, "Přeskočeno - komodita", analysis="Komodita přeskočena")
            continue

        # ------------------------------------------------------------------
        # Načtení surových dat
        # ------------------------------------------------------------------
        progress.update_status(agent_id, ticker, "Načítání finančních metrik")
        metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=5, api_key=api_key)

        progress.update_status(agent_id, ticker, "Načítání položek")
        line_items = search_line_items(
            ticker,
            [
                "free_cash_flow",
                "net_income",
                "total_debt",
                "cash_and_equivalents",
                "total_assets",
                "total_liabilities",
                "outstanding_shares",
                "issuance_or_purchase_of_equity_shares",
            ],
            end_date,
            api_key=api_key,
        )

        progress.update_status(agent_id, ticker, "Načítání insider obchodů")
        insider_trades = get_insider_trades(ticker, end_date=end_date, start_date=start_date)

        progress.update_status(agent_id, ticker, "Načítání firemních zpráv")
        news = get_company_news(ticker, end_date=end_date, start_date=start_date, limit=250)

        progress.update_status(agent_id, ticker, "Načítání tržní kapitalizace")
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)

        # ------------------------------------------------------------------
        # Spuštění dílčích analýz
        # ------------------------------------------------------------------
        progress.update_status(agent_id, ticker, "Analýza hodnoty")
        value_analysis = _analyze_value(metrics, line_items, market_cap)

        progress.update_status(agent_id, ticker, "Analýza rozvahy")
        balance_sheet_analysis = _analyze_balance_sheet(metrics, line_items)

        progress.update_status(agent_id, ticker, "Analýza insider aktivity")
        insider_analysis = _analyze_insider_activity(insider_trades)

        progress.update_status(agent_id, ticker, "Analýza contrarian sentimentu")
        contrarian_analysis = _analyze_contrarian_sentiment(news)

        # ------------------------------------------------------------------
        # Agregace skóre a odvození předběžného signálu
        # ------------------------------------------------------------------
        total_score = (
            value_analysis["score"]
            + balance_sheet_analysis["score"]
            + insider_analysis["score"]
            + contrarian_analysis["score"]
        )
        max_score = (
            value_analysis["max_score"]
            + balance_sheet_analysis["max_score"]
            + insider_analysis["max_score"]
            + contrarian_analysis["max_score"]
        )

        if total_score >= 0.7 * max_score:
            signal = "bullish"
        elif total_score <= 0.3 * max_score:
            signal = "bearish"
        else:
            signal = "neutral"

        # ------------------------------------------------------------------
        # Shromáždění dat pro LLM zdůvodnění a výstup
        # ------------------------------------------------------------------
        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_score,
            "value_analysis": value_analysis,
            "balance_sheet_analysis": balance_sheet_analysis,
            "insider_analysis": insider_analysis,
            "contrarian_analysis": contrarian_analysis,
            "market_cap": market_cap,
        }

        progress.update_status(agent_id, ticker, "Generování LLM výstupu")
        burry_output = _generate_burry_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        burry_analysis[ticker] = {
            "signal": burry_output.signal,
            "confidence": burry_output.confidence,
            "reasoning": burry_output.reasoning,
        }

        progress.update_status(agent_id, ticker, "Done", analysis=burry_output.reasoning)

    # ----------------------------------------------------------------------
    # Návrat do grafu
    # ----------------------------------------------------------------------
    message = HumanMessage(content=json.dumps(burry_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(burry_analysis, "Michael Burry Agent")

    if "analyst_signals" not in state["data"]:
        state["data"]["analyst_signals"] = {}
    state["data"]["analyst_signals"][agent_id] = burry_analysis

    progress.update_status(agent_id, None, "Done")

    return {"messages": [message], "data": state["data"]}


###############################################################################
# Pomocníci pro dílčí analýzy
###############################################################################


def _latest_line_item(line_items: List[Any]) -> Any:
    """Vrátí nejnovější objekt položky nebo *None*."""
    return line_items[0] if line_items else None


# ----- Hodnota ----------------------------------------------------------------


def _analyze_value(metrics: Any, line_items: List[Any], market_cap: Optional[float]) -> Dict[str, Any]:
    """Free cash-flow yield, EV/EBIT, další klasické deep-value metriky."""

    max_score = 6  # 4 body pro FCF-yield, 2 body pro EV/EBIT
    score = 0
    details: List[str] = []

    # Free-cash-flow yield
    latest_item = _latest_line_item(line_items)
    fcf = getattr(latest_item, "free_cash_flow", None) if latest_item else None
    if fcf is not None and market_cap:
        fcf_yield = fcf / market_cap
        if fcf_yield >= 0.15:
            score += 4
            details.append(f"Extraordinary FCF yield {fcf_yield:.1%}")
        elif fcf_yield >= 0.12:
            score += 3
            details.append(f"Very high FCF yield {fcf_yield:.1%}")
        elif fcf_yield >= 0.08:
            score += 2
            details.append(f"Respectable FCF yield {fcf_yield:.1%}")
        else:
            details.append(f"Low FCF yield {fcf_yield:.1%}")
    else:
        details.append("FCF data unavailable")

    # EV/EBIT (z finančních metrik)
    if metrics:
        ev_ebit = getattr(metrics[0], "ev_to_ebit", None)
        if ev_ebit is not None:
            if ev_ebit < 6:
                score += 2
                details.append(f"EV/EBIT {ev_ebit:.1f} (<6)")
            elif ev_ebit < 10:
                score += 1
                details.append(f"EV/EBIT {ev_ebit:.1f} (<10)")
            else:
                details.append(f"High EV/EBIT {ev_ebit:.1f}")
        else:
            details.append("EV/EBIT data unavailable")
    else:
        details.append("Financial metrics unavailable")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


# ----- Rozvaha --------------------------------------------------------


def _analyze_balance_sheet(metrics: Any, line_items: List[Any]) -> Dict[str, Any]:
    """Kontroly pákového efektu a likvidity."""

    max_score = 3
    score = 0
    details: List[str] = []

    latest_metrics = metrics[0] if metrics else None
    latest_item = _latest_line_item(line_items)

    debt_to_equity = getattr(latest_metrics, "debt_to_equity", None) if latest_metrics else None
    if debt_to_equity is not None:
        if debt_to_equity < 0.5:
            score += 2
            details.append(f"Low D/E {debt_to_equity:.2f}")
        elif debt_to_equity < 1:
            score += 1
            details.append(f"Moderate D/E {debt_to_equity:.2f}")
        else:
            details.append(f"High leverage D/E {debt_to_equity:.2f}")
    else:
        details.append("Debt‑to‑equity data unavailable")

    # Rychlá kontrola likvidity (hotovost vs celkový dluh)
    if latest_item is not None:
        cash = getattr(latest_item, "cash_and_equivalents", None)
        total_debt = getattr(latest_item, "total_debt", None)
        if cash is not None and total_debt is not None:
            if cash > total_debt:
                score += 1
                details.append("Net cash position")
            else:
                details.append("Net debt position")
        else:
            details.append("Cash/debt data unavailable")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


# ----- Insider aktivita -----------------------------------------------------


def _analyze_insider_activity(insider_trades: Any) -> Dict[str, Any]:
    """Čisté insider nákupy za posledních 12 měsíců působí jako tvrdý katalyzátor."""

    max_score = 2
    score = 0
    details: List[str] = []

    if not insider_trades:
        details.append("No insider trade data")
        return {"score": score, "max_score": max_score, "details": "; ".join(details)}

    shares_bought = sum(t.transaction_shares or 0 for t in insider_trades if (t.transaction_shares or 0) > 0)
    shares_sold = abs(sum(t.transaction_shares or 0 for t in insider_trades if (t.transaction_shares or 0) < 0))
    net = shares_bought - shares_sold
    if net > 0:
        score += 2 if net / max(shares_sold, 1) > 1 else 1
        details.append(f"Net insider buying of {net:,} shares")
    else:
        details.append("Net insider selling")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


# ----- Contrarian sentiment -------------------------------------------------


def _analyze_contrarian_sentiment(news: Any) -> Dict[str, Any]:
    """Velmi hrubý odhad: zeď nedávných negativních titulků může být *pozitivní* pro contrarian."""

    max_score = 1
    score = 0
    details: List[str] = []

    if not news:
        details.append("No recent news")
        return {"score": score, "max_score": max_score, "details": "; ".join(details)}

    # Počítání článků s negativním sentimentem
    sentiment_negative_count = sum(1 for n in news if n.sentiment and n.sentiment.lower() in ["negative", "bearish"])

    if sentiment_negative_count >= 5:
        score += 1  # Čím více nenáviděné, tím lepší (za předpokladu, že fundamenty drží)
        details.append(f"{sentiment_negative_count} negative headlines (contrarian opportunity)")
    else:
        details.append("Limited negative press")

    return {"score": score, "max_score": max_score, "details": "; ".join(details)}


###############################################################################
# LLM generování
###############################################################################


def _generate_burry_output(
    ticker: str,
    analysis_data: dict,
    state: AgentState,
    agent_id: str,
) -> MichaelBurrySignal:
    """Zavolá LLM pro vytvoření finálního obchodního signálu Burry's hlasem."""

    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Jste AI agent emulující Dr. Michael J. Burry. Váš mandát:
                - Lovte deep value v amerických akciích pomocí tvrdých čísel (free cash flow, EV/EBIT, rozvaha)
                - Buďte contrarian: nenávist v tisku může být váš přítel, pokud jsou fundamenty solidní
                - Zaměřte se nejprve na downside – vyhýbejte se pákovým rozvahám
                - Hledejte tvrdé katalyzátory jako insider nákupy, zpětné odkupy nebo prodeje aktiv
                - Komunikujte Burry's stručným, na data zaměřeným stylem

                Při poskytování svého zdůvodnění buďte důkladní a konkrétní:
                1. Začněte klíčovou metrikou(ami), která řídila vaše rozhodnutí
                2. Citujte konkrétní čísla (např. "FCF yield 14.7%", "EV/EBIT 5.3")
                3. Zdůrazněte rizikové faktory a proč jsou (ne)přijatelné
                4. Zmíňte relevantní insider aktivitu nebo contrarian příležitosti
                5. Používejte Burry's přímý, na čísla zaměřený komunikační styl s minimem slov
                
                Například, pokud bullish: "FCF yield 12.8%. EV/EBIT 6.2. Debt-to-equity 0.4. Čisté insider nákupy 25k akcií. Trh přehlíží hodnotu kvůli přehnané reakci na nedávnou žalobu. Silný nákup."
                Například, pokud bearish: "FCF yield pouze 2.1%. Debt-to-equity znepokojující na 2.3. Management ředí akcionáře. Odmítnout."
                """,
            ),
            (
                "human",
                """Na základě následujících dat vytvořte investiční signál, jak by to udělal Michael Burry:

                Data analýzy pro {ticker}:
                {analysis_data}

                Vraťte obchodní signál přesně v následujícím JSON formátu:
                {{
                  "signal": "bullish" | "bearish" | "neutral",
                  "confidence": float mezi 0 a 100,
                  "reasoning": "string"
                }}
                """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    # Výchozí záložní signál v případě selhání parsování
    def create_default_michael_burry_signal():
        return MichaelBurrySignal(signal="neutral", confidence=0.0, reasoning="Chyba parsování – výchozí neutral")

    result = call_llm(
        prompt=prompt,
        pydantic_model=MichaelBurrySignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_michael_burry_signal,
    )
    return cast(MichaelBurrySignal, result)
