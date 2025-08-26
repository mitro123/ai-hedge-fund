"""Peter Lynch Agent - Růst za rozumnou cenu (GARP) s důrazem na PEG poměr a srozumitelné podniky."""

import json
from typing import Any, cast, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing_extensions import Literal

from src.exceptions import APIKeyError
from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_company_news, get_insider_trades, get_market_cap, search_line_items
from src.utils.api_key import get_api_key_from_state
from src.utils.llm import call_llm
from src.utils.progress import progress


class PeterLynchSignal(BaseModel):
    """
    Container for the Peter Lynch-style output signal.
    """

    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def peter_lynch_agent(state: AgentState, agent_id: str = "peter_lynch_agent") -> Dict[str, Any]:
    """
    Analyzuje akcie pomocí Peter Lynch's investičních principů:
      - Investujte do toho, co znáte (jasné, srozumitelné podniky).
      - Růst za rozumnou cenu (GARP), zdůrazňující PEG poměr.
      - Hledejte konzistentní růst tržeb a EPS a zvládnutelný dluh.
      - Buďte pozorní na potenciální "ten-baggery" (vysokorostoucí příležitosti).
      - Vyhýbejte se příliš složitým nebo vysoce pákovým podnikům.
      - Používejte sentiment zpráv a insider obchody jako sekundární vstupy.
      - Pokud fundamenty silně odpovídají GARP, buďte agresivnější.

    Výsledkem je bullish/bearish/neutral signál spolu s
    spolehlivostí (0–100) a textovým vysvětlením zdůvodnění.
    """

    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")
    if api_key is None:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")

    analysis_data = {}
    lynch_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Shromažďování finančních položek")
        # Relevantní položky pro Peter Lynch's přístup
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",
                "earnings_per_share",
                "net_income",
                "operating_income",
                "gross_margin",
                "operating_margin",
                "free_cash_flow",
                "capital_expenditure",
                "cash_and_equivalents",
                "total_debt",
                "shareholders_equity",
                "outstanding_shares",
            ],
            end_date,
            period="annual",
            limit=5,
            api_key=api_key,
        )

        progress.update_status(agent_id, ticker, "Získávání tržní kapitalizace")
        market_cap = get_market_cap(ticker, end_date, api_key=api_key)

        progress.update_status(agent_id, ticker, "Načítání insider obchodů")
        insider_trades = get_insider_trades(ticker, end_date, limit=50, api_key=api_key)

        progress.update_status(agent_id, ticker, "Načítání firemních zpráv")
        company_news = get_company_news(ticker, end_date, limit=50, api_key=api_key)

        # Provedení dílčích analýz:
        progress.update_status(agent_id, ticker, "Analýza růstu")
        growth_analysis = analyze_lynch_growth(financial_line_items)

        progress.update_status(agent_id, ticker, "Analýza fundamentů")
        fundamentals_analysis = analyze_lynch_fundamentals(financial_line_items)

        progress.update_status(agent_id, ticker, "Analýza ocenění (zaměření na PEG)")
        valuation_analysis = analyze_lynch_valuation(financial_line_items, market_cap)

        progress.update_status(agent_id, ticker, "Analýza sentimentu")
        sentiment_analysis = analyze_sentiment(company_news)

        progress.update_status(agent_id, ticker, "Analýza insider aktivity")
        insider_activity = analyze_insider_activity(insider_trades)

        # Kombinace dílčích skóre s váhami typickými pro Peter Lynch:
        #   30% Růst, 25% Ocenění, 20% Fundamenty,
        #   15% Sentiment, 10% Insider aktivita = 100%
        total_score = (
            growth_analysis["score"] * 0.30
            + valuation_analysis["score"] * 0.25
            + fundamentals_analysis["score"] * 0.20
            + sentiment_analysis["score"] * 0.15
            + insider_activity["score"] * 0.10
        )

        max_possible_score = 10.0

        # Mapování finálního skóre na signál
        if total_score >= 7.5:
            signal = "bullish"
        elif total_score <= 4.5:
            signal = "bearish"
        else:
            signal = "neutral"

        analysis_data[ticker] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "growth_analysis": growth_analysis,
            "valuation_analysis": valuation_analysis,
            "fundamentals_analysis": fundamentals_analysis,
            "sentiment_analysis": sentiment_analysis,
            "insider_activity": insider_activity,
        }

        progress.update_status(agent_id, ticker, "Generování Peter Lynch analýzy")
        lynch_output = generate_lynch_output(
            ticker=ticker,
            analysis_data=analysis_data[ticker],
            state=state,
            agent_id=agent_id,
        )

        lynch_analysis[ticker] = {
            "signal": lynch_output.signal,
            "confidence": lynch_output.confidence,
            "reasoning": lynch_output.reasoning,
        }

        progress.update_status(agent_id, ticker, "Done", analysis=lynch_output.reasoning)

    # Zabalení výsledků
    message = HumanMessage(content=json.dumps(lynch_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(lynch_analysis, "Peter Lynch Agent")

    # Uložení signálů do stavu
    state["data"]["analyst_signals"][agent_id] = lynch_analysis

    progress.update_status(agent_id, None, "Done")

    return {"messages": [message], "data": state["data"]}


def analyze_lynch_growth(financial_line_items: List[Any]) -> Dict[str, Any]:
    """
    Vyhodnocení růstu na základě trendů tržeb a EPS:
      - Konzistentní růst tržeb
      - Konzistentní růst EPS
    Peter Lynch měl rád společnosti se stabilním, srozumitelným růstem,
    často hledal potenciální 'ten-baggery' s dlouhou dráhou.
    """
    if not financial_line_items or len(financial_line_items) < 2:
        return {"score": 0, "details": "Insufficient financial data for growth analysis"}

    details = []
    raw_score = 0  # Sečteme body, pak škálujeme na 0–10

    # 1) Růst tržeb
    revenues = [fi.revenue for fi in financial_line_items if fi.revenue is not None]
    if len(revenues) >= 2:
        latest_rev = revenues[0]
        older_rev = revenues[-1]
        if older_rev > 0:
            rev_growth = (latest_rev - older_rev) / abs(older_rev)
            if rev_growth > 0.25:
                raw_score += 3
                details.append(f"Strong revenue growth: {rev_growth:.1%}")
            elif rev_growth > 0.10:
                raw_score += 2
                details.append(f"Moderate revenue growth: {rev_growth:.1%}")
            elif rev_growth > 0.02:
                raw_score += 1
                details.append(f"Slight revenue growth: {rev_growth:.1%}")
            else:
                details.append(f"Flat or negative revenue growth: {rev_growth:.1%}")
        else:
            details.append("Older revenue is zero/negative; can't compute revenue growth.")
    else:
        details.append("Not enough revenue data to assess growth.")

    # 2) Růst EPS
    eps_values = [fi.earnings_per_share for fi in financial_line_items if fi.earnings_per_share is not None]
    if len(eps_values) >= 2:
        latest_eps = eps_values[0]
        older_eps = eps_values[-1]
        if abs(older_eps) > 1e-9:
            eps_growth = (latest_eps - older_eps) / abs(older_eps)
            if eps_growth > 0.25:
                raw_score += 3
                details.append(f"Strong EPS growth: {eps_growth:.1%}")
            elif eps_growth > 0.10:
                raw_score += 2
                details.append(f"Moderate EPS growth: {eps_growth:.1%}")
            elif eps_growth > 0.02:
                raw_score += 1
                details.append(f"Slight EPS growth: {eps_growth:.1%}")
            else:
                details.append(f"Minimal or negative EPS growth: {eps_growth:.1%}")
        else:
            details.append("Older EPS is near zero; skipping EPS growth calculation.")
    else:
        details.append("Not enough EPS data for growth calculation.")

    # raw_score může být až 6 => škálování na 0–10
    final_score = min(10, (raw_score / 6) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_lynch_fundamentals(financial_line_items: List[Any]) -> Dict[str, Any]:
    """
    Vyhodnocení základních fundamentů:
      - Dluh/Vlastní kapitál
      - Provozní marže (nebo hrubá marže)
      - Pozitivní Free Cash Flow
    Lynch se vyhýbal silně zadluženým nebo složitým podnikům.
    """
    if not financial_line_items:
        return {"score": 0, "details": "Insufficient fundamentals data"}

    details = []
    raw_score = 0  # Nahromadíme až 6 bodů, pak škálujeme na 0–10

    # 1) Dluh k vlastnímu kapitálu
    debt_values = [fi.total_debt for fi in financial_line_items if fi.total_debt is not None]
    eq_values = [fi.shareholders_equity for fi in financial_line_items if fi.shareholders_equity is not None]
    if debt_values and eq_values and len(debt_values) == len(eq_values) and len(debt_values) > 0:
        recent_debt = debt_values[0]
        recent_equity = eq_values[0] if eq_values[0] else 1e-9
        de_ratio = recent_debt / recent_equity
        if de_ratio < 0.5:
            raw_score += 2
            details.append(f"Low debt-to-equity: {de_ratio:.2f}")
        elif de_ratio < 1.0:
            raw_score += 1
            details.append(f"Moderate debt-to-equity: {de_ratio:.2f}")
        else:
            details.append(f"High debt-to-equity: {de_ratio:.2f}")
    else:
        details.append("No consistent debt/equity data available.")

    # 2) Provozní marže
    om_values = [fi.operating_margin for fi in financial_line_items if fi.operating_margin is not None]
    if om_values:
        om_recent = om_values[0]
        if om_recent > 0.20:
            raw_score += 2
            details.append(f"Strong operating margin: {om_recent:.1%}")
        elif om_recent > 0.10:
            raw_score += 1
            details.append(f"Moderate operating margin: {om_recent:.1%}")
        else:
            details.append(f"Low operating margin: {om_recent:.1%}")
    else:
        details.append("No operating margin data available.")

    # 3) Pozitivní Free Cash Flow
    fcf_values = [fi.free_cash_flow for fi in financial_line_items if fi.free_cash_flow is not None]
    if fcf_values and fcf_values[0] is not None:
        if fcf_values[0] > 0:
            raw_score += 2
            details.append(f"Positive free cash flow: {fcf_values[0]:,.0f}")
        else:
            details.append(f"Recent FCF is negative: {fcf_values[0]:,.0f}")
    else:
        details.append("No free cash flow data available.")

    # raw_score až 6 => škálování na 0–10
    final_score = min(10, (raw_score / 6) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_lynch_valuation(financial_line_items: List[Any], market_cap: Optional[float]) -> Dict[str, Any]:
    """
    Peter Lynch's přístup k 'Růstu za rozumnou cenu' (GARP):
      - Zdůrazňuje PEG poměr: (P/E) / Míra růstu
      - Také zvažuje základní P/E pokud PEG není dostupný
    PEG < 1 je velmi atraktivní; 1-2 je férové; >2 je drahé.
    """
    if not financial_line_items or market_cap is None:
        return {"score": 0, "details": "Insufficient data for valuation"}

    details = []
    raw_score = 0

    # Shromáždění dat pro P/E
    net_incomes = [fi.net_income for fi in financial_line_items if fi.net_income is not None]
    eps_values = [fi.earnings_per_share for fi in financial_line_items if fi.earnings_per_share is not None]

    # Aproximace P/E přes (tržní kap / čistý zisk) pokud je čistý zisk pozitivní
    pe_ratio = None
    if net_incomes and net_incomes[0] and net_incomes[0] > 0:
        pe_ratio = market_cap / net_incomes[0]
        details.append(f"Estimated P/E: {pe_ratio:.2f}")
    else:
        details.append("No positive net income => can't compute approximate P/E")

    # Pokud máme alespoň 2 datové body EPS, odhadneme růst
    eps_growth_rate = None
    if len(eps_values) >= 2:
        latest_eps = eps_values[0]
        older_eps = eps_values[-1]
        if older_eps > 0:
            eps_growth_rate = (latest_eps - older_eps) / older_eps
            details.append(f"Approx EPS growth rate: {eps_growth_rate:.1%}")
        else:
            details.append("Cannot compute EPS growth rate (older EPS <= 0)")
    else:
        details.append("Not enough EPS data to compute growth rate")

    # Výpočet PEG pokud je možný
    peg_ratio = None
    if pe_ratio and eps_growth_rate and eps_growth_rate > 0:
        # Peg ratio typically uses a percentage growth rate
        # So if growth rate is 0.25, we treat it as 25 for the formula => PE / 25
        # Alternatively, some treat it as 0.25 => we do (PE / (0.25 * 100)).
        # Implementation can vary, but let's do a standard approach: PEG = PE / (Growth * 100).
        peg_ratio = pe_ratio / (eps_growth_rate * 100)
        details.append(f"PEG ratio: {peg_ratio:.2f}")

    # Logika bodování:
    #   - P/E < 15 => +2, < 25 => +1
    #   - PEG < 1 => +3, < 2 => +2, < 3 => +1
    if pe_ratio is not None:
        if pe_ratio < 15:
            raw_score += 2
        elif pe_ratio < 25:
            raw_score += 1

    if peg_ratio is not None:
        if peg_ratio < 1:
            raw_score += 3
        elif peg_ratio < 2:
            raw_score += 2
        elif peg_ratio < 3:
            raw_score += 1

    final_score = min(10, (raw_score / 5) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_sentiment(news_items: List[Any]) -> Dict[str, Any]:
    """
    Základní kontrola sentimentu zpráv. Negativní titulky zatěžují finální skóre.
    """
    if not news_items:
        return {"score": 5, "details": "No news data; default to neutral sentiment"}

    negative_keywords = ["lawsuit", "fraud", "negative", "downturn", "decline", "investigation", "recall"]
    negative_count = 0
    for news in news_items:
        title_lower = (news.title or "").lower()
        if any(word in title_lower for word in negative_keywords):
            negative_count += 1

    details = []
    if negative_count > len(news_items) * 0.3:
        # More than 30% negative => somewhat bearish => 3/10
        score = 3
        details.append(f"High proportion of negative headlines: {negative_count}/{len(news_items)}")
    elif negative_count > 0:
        # Some negativity => 6/10
        score = 6
        details.append(f"Some negative headlines: {negative_count}/{len(news_items)}")
    else:
        # Mostly positive => 8/10
        score = 8
        details.append("Mostly positive or neutral headlines")

    return {"score": score, "details": "; ".join(details)}


def analyze_insider_activity(insider_trades: List[Any]) -> Dict[str, Any]:
    """
    Jednoduchá analýza insider obchodů:
      - Pokud jsou těžké insider nákupy, je to pozitivní znamení.
      - Pokud je většinou prodej, je to negativní znamení.
      - Jinak neutrální.
    """
    # Výchozí 5 (neutrální)
    score = 5
    details = []

    if not insider_trades:
        details.append("No insider trades data; defaulting to neutral")
        return {"score": score, "details": "; ".join(details)}

    buys, sells = 0, 0
    for trade in insider_trades:
        if trade.transaction_shares is not None:
            if trade.transaction_shares > 0:
                buys += 1
            elif trade.transaction_shares < 0:
                sells += 1

    total = buys + sells
    if total == 0:
        details.append("No significant buy/sell transactions found; neutral stance")
        return {"score": score, "details": "; ".join(details)}

    buy_ratio = buys / total
    if buy_ratio > 0.7:
        # Heavy buying => +3 => total 8
        score = 8
        details.append(f"Heavy insider buying: {buys} buys vs. {sells} sells")
    elif buy_ratio > 0.4:
        # Some buying => +1 => total 6
        score = 6
        details.append(f"Moderate insider buying: {buys} buys vs. {sells} sells")
    else:
        # Mostly selling => -1 => total 4
        score = 4
        details.append(f"Mostly insider selling: {buys} buys vs. {sells} sells")

    return {"score": score, "details": "; ".join(details)}


def generate_lynch_output(
    ticker: str,
    analysis_data: Dict[str, Any],
    state: AgentState,
    agent_id: str,
) -> PeterLynchSignal:
    """
    Generates a final JSON signal in Peter Lynch's voice & style.
    """
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Jste Peter Lynch AI agent. Činíte investiční rozhodnutí na základě Peter Lynch's známých principů:
                
                1. Investujte do toho, co znáte: Zdůrazňujte srozumitelné podniky, možná objevené v každodenním životě.
                2. Růst za rozumnou cenu (GARP): Spoléhejte na PEG poměr jako hlavní metriku.
                3. Hledejte 'Ten-Baggery': Společnosti schopné podstatně zvýšit zisky a cenu akcií.
                4. Stabilní růst: Upřednostňujte konzistentní expanzi tržeb/zisků, méně se starejte o krátkodobý šum.
                5. Vyhýbejte se vysokému dluhu: Pozor na nebezpečnou páku.
                6. Management a příběh: Dobrý 'příběh' za akcií, ale ne přehnaně propagovaný nebo příliš složitý.
                
                Když poskytujete své zdůvodnění, dělejte to Peter Lynch's hlasem:
                - Citujte PEG poměr
                - Zmíňte 'ten-bagger' potenciál pokud je aplikovatelný
                - Odkazujte na osobní nebo anekdotická pozorování (např. "Pokud moje děti milují produkt...")
                - Používejte praktický, lidový jazyk
                - Poskytněte klíčová pozitiva a negativa
                - Zakončete jasným postojem (bullish, bearish nebo neutral)
                
                Vraťte svůj finální výstup striktně v JSON s poli:
                {{
                  "signal": "bullish" | "bearish" | "neutral",
                  "confidence": 0 až 100,
                  "reasoning": "string"
                }}
                """,
            ),
            (
                "human",
                """Na základě následujících dat analýzy pro {ticker}, vytvořte svůj Peter Lynch–style investiční signál.

                Data analýzy:
                {analysis_data}

                Vraťte pouze platný JSON s "signal", "confidence" a "reasoning".
                """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    def create_default_signal():
        return PeterLynchSignal(signal="neutral", confidence=0.0, reasoning="Chyba v analýze; výchozí neutral")

    result = call_llm(
        prompt=prompt,
        pydantic_model=PeterLynchSignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_signal,
    )
    return cast(PeterLynchSignal, result)
