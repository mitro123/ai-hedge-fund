"""Phil Fisher Agent - Dlouhodobý růstový investor zaměřený na kvalitu managementu a R&D."""

import json
import statistics
from typing import Any, cast, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing_extensions import Literal

from src.exceptions import APIKeyError
from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_company_news, get_insider_trades, get_market_cap, search_line_items
from src.utils.api_key import get_api_key_from_state
from src.utils.constants import COMMODITY_SYMBOLS
from src.utils.llm import call_llm
from src.utils.progress import progress


class PhilFisherSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def phil_fisher_agent(state: AgentState, agent_id: str = "phil_fisher_agent") -> Dict[str, Any]:
    """
    Analyzuje akcie pomocí Phil Fisher's investičních principů:
      - Hledá společnosti s dlouhodobým nadprůměrným růstovým potenciálem
      - Zdůrazňuje kvalitu managementu a R&D
      - Hledá silné marže, konzistentní růst a zvládnutelnou páku
      - Kombinuje fundamentální 'scuttlebutt' kontroly se základním sentimentem a insider daty
      - Ochoten zaplatit za kvalitu, ale stále pozorný na ocenění
      - Obecně se zaměřuje na dlouhodobé skládání

    Vrací bullish/bearish/neutral signál se spolehlivostí a zdůvodněním.
    """
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")
    if api_key is None:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")
    analysis_data = {}
    fisher_analysis = {}

    for ticker in tickers:
        # Skip commodity symbols as Phil Fisher analysis is designed for stocks
        if ticker in COMMODITY_SYMBOLS:
            progress.update_status(agent_id, ticker, "Přeskakuji komoditu")
            fisher_analysis[ticker] = {
                "signal": "neutral",
                "confidence": 0.0,
                "reasoning": f"Phil Fisher analýza není vhodná pro komodity ({ticker}). Komodity jsou analyzovány specializovaným komoditním agentem.",
            }
            progress.update_status(agent_id, ticker, "Přeskočeno - komodita", analysis="Komodita přeskočena")
            continue
        progress.update_status(agent_id, ticker, "Shromažďování finančních položek")
        # Zahrnuje relevantní položky pro Phil Fisher's přístup:
        #   - Růst a kvalita: tržby, čistý zisk, zisk na akcii, R&D výdaje
        #   - Marže a stabilita: provozní zisk, provozní marže, hrubá marže
        #   - Efektivita managementu a páka: celkový dluh, vlastní kapitál, volný peněžní tok
        #   - Ocenění: čistý zisk, volný peněžní tok (pro P/E, P/FCF), ebit, ebitda
        financial_line_items = search_line_items(
            ticker,
            [
                "revenue",
                "net_income",
                "earnings_per_share",
                "free_cash_flow",
                "research_and_development",
                "operating_income",
                "operating_margin",
                "gross_margin",
                "total_debt",
                "shareholders_equity",
                "cash_and_equivalents",
                "ebit",
                "ebitda",
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

        progress.update_status(agent_id, ticker, "Analýza růstu a kvality")
        growth_quality = analyze_fisher_growth_quality(financial_line_items)

        progress.update_status(agent_id, ticker, "Analýza marží a stability")
        margins_stability = analyze_margins_stability(financial_line_items)

        progress.update_status(agent_id, ticker, "Analýza efektivity managementu a páky")
        mgmt_efficiency = analyze_management_efficiency_leverage(financial_line_items)

        progress.update_status(agent_id, ticker, "Analýza ocenění (Fisher styl)")
        fisher_valuation = analyze_fisher_valuation(financial_line_items, market_cap)

        progress.update_status(agent_id, ticker, "Analýza insider aktivity")
        insider_activity = analyze_insider_activity(insider_trades)

        progress.update_status(agent_id, ticker, "Analýza sentimentu")
        sentiment_analysis = analyze_sentiment(company_news)

        # Kombinace dílčích skóre s váhami typickými pro Fisher:
        #   30% Růst a kvalita
        #   25% Marže a stabilita
        #   20% Efektivita managementu
        #   15% Ocenění
        #   5% Insider aktivita
        #   5% Sentiment
        total_score = (
            growth_quality["score"] * 0.30
            + margins_stability["score"] * 0.25
            + mgmt_efficiency["score"] * 0.20
            + fisher_valuation["score"] * 0.15
            + insider_activity["score"] * 0.05
            + sentiment_analysis["score"] * 0.05
        )

        max_possible_score = 10

        # Jednoduchý bullish/neutral/bearish signál
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
            "growth_quality": growth_quality,
            "margins_stability": margins_stability,
            "management_efficiency": mgmt_efficiency,
            "valuation_analysis": fisher_valuation,
            "insider_activity": insider_activity,
            "sentiment_analysis": sentiment_analysis,
        }

        progress.update_status(agent_id, ticker, "Generování Phil Fisher-style analýzy")
        fisher_output = generate_fisher_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        fisher_analysis[ticker] = {
            "signal": fisher_output.signal,
            "confidence": fisher_output.confidence,
            "reasoning": fisher_output.reasoning,
        }

        progress.update_status(agent_id, ticker, "Done", analysis=fisher_output.reasoning)

    # Zabalení výsledků do jedné zprávy
    message = HumanMessage(content=json.dumps(fisher_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(fisher_analysis, "Phil Fisher Agent")

    if "analyst_signals" not in state["data"]:
        state["data"]["analyst_signals"] = {}
    state["data"]["analyst_signals"][agent_id] = fisher_analysis

    progress.update_status(agent_id, None, "Done")

    return {"messages": [message], "data": state["data"]}


def analyze_fisher_growth_quality(financial_line_items: List[Any]) -> Dict[str, Any]:
    """
    Vyhodnocení růstu a kvality:
      - Konzistentní růst tržeb
      - Konzistentní růst EPS
      - R&D jako % z tržeb (pokud je relevantní, indikuje budoucně orientované výdaje)
    """
    if not financial_line_items or len(financial_line_items) < 2:
        return {
            "score": 0,
            "details": "Nedostatečná finanční data pro analýzu růstu/kvality",
        }

    details = []
    raw_score = 0  # až 9 surových bodů => škálování na 0–10

    # 1. Růst tržeb (YoY)
    revenues = [fi.revenue for fi in financial_line_items if fi.revenue is not None]
    if len(revenues) >= 2:
        # Podíváme se na nejstarší vs. nejnovější pro odhad víceletého růstu pokud je možný
        latest_rev = revenues[0]
        oldest_rev = revenues[-1]
        if oldest_rev > 0:
            rev_growth = (latest_rev - oldest_rev) / abs(oldest_rev)
            if rev_growth > 0.80:
                raw_score += 3
                details.append(f"Velmi silný víceletý růst tržeb: {rev_growth:.1%}")
            elif rev_growth > 0.40:
                raw_score += 2
                details.append(f"Mírný víceletý růst tržeb: {rev_growth:.1%}")
            elif rev_growth > 0.10:
                raw_score += 1
                details.append(f"Mírný víceletý růst tržeb: {rev_growth:.1%}")
            else:
                details.append(f"Minimální nebo negativní víceletý růst tržeb: {rev_growth:.1%}")
        else:
            details.append("Nejstarší tržby jsou nulové/negativní; nelze vypočítat růst.")
    else:
        details.append("Nedostatek datových bodů tržeb pro výpočet růstu.")

    # 2. Růst EPS (YoY)
    eps_values = [fi.earnings_per_share for fi in financial_line_items if fi.earnings_per_share is not None]
    if len(eps_values) >= 2:
        latest_eps = eps_values[0]
        oldest_eps = eps_values[-1]
        if abs(oldest_eps) > 1e-9:
            eps_growth = (latest_eps - oldest_eps) / abs(oldest_eps)
            if eps_growth > 0.80:
                raw_score += 3
                details.append(f"Velmi silný víceletý růst EPS: {eps_growth:.1%}")
            elif eps_growth > 0.40:
                raw_score += 2
                details.append(f"Mírný víceletý růst EPS: {eps_growth:.1%}")
            elif eps_growth > 0.10:
                raw_score += 1
                details.append(f"Mírný víceletý růst EPS: {eps_growth:.1%}")
            else:
                details.append(f"Minimální nebo negativní víceletý růst EPS: {eps_growth:.1%}")
        else:
            details.append("Nejstarší EPS blízko nuly; přeskakuji výpočet růstu EPS.")
    else:
        details.append("Nedostatek datových bodů EPS pro výpočet růstu.")

    # 3. R&D jako % z tržeb (pokud máme R&D data)
    rnd_values = [fi.research_and_development for fi in financial_line_items if fi.research_and_development is not None]
    if rnd_values and revenues and len(rnd_values) == len(revenues):
        # Podíváme se jen na nejnovější pro jednoduché měření
        recent_rnd = rnd_values[0]
        recent_rev = revenues[0] if revenues[0] else 1e-9
        rnd_ratio = recent_rnd / recent_rev
        # Obecně Fisher obdivoval společnosti, které agresivně investují do R&D,
        # ale musí to být vhodné. Předpokládáme, že "3%-15%" je zdravé, jen jako příklad.
        if 0.03 <= rnd_ratio <= 0.15:
            raw_score += 3
            details.append(f"R&D poměr {rnd_ratio:.1%} indikuje významnou investici do budoucího růstu")
        elif rnd_ratio > 0.15:
            raw_score += 2
            details.append(f"R&D poměr {rnd_ratio:.1%} je velmi vysoký (může být dobré pokud je dobře řízené)")
        elif rnd_ratio > 0.0:
            raw_score += 1
            details.append(f"R&D poměr {rnd_ratio:.1%} je poněkud nízký ale stále pozitivní")
        else:
            details.append("Žádný významný poměr R&D výdajů")
    else:
        details.append("Nedostatečná R&D data k vyhodnocení")

    # škálování raw_score (max 9) na 0–10
    final_score = min(10, (raw_score / 9) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_margins_stability(financial_line_items: List[Any]) -> Dict[str, Any]:
    """
    Zkoumá konzistenci marží (hrubá/provozní marže) a obecnou stabilitu v čase.
    """
    if not financial_line_items or len(financial_line_items) < 2:
        return {
            "score": 0,
            "details": "Nedostatečná data pro analýzu stability marží",
        }

    details = []
    raw_score = 0  # až 6 => škálování na 0-10

    # 1. Konzistence provozní marže
    op_margins = [fi.operating_margin for fi in financial_line_items if fi.operating_margin is not None]
    if len(op_margins) >= 2:
        # Kontrola zda jsou marže stabilní nebo se zlepšují (porovnání nejstarší s nejnovější)
        oldest_op_margin = op_margins[-1]
        newest_op_margin = op_margins[0]
        if newest_op_margin >= oldest_op_margin > 0:
            raw_score += 2
            details.append(
                f"Provozní marže stabilní nebo se zlepšuje ({oldest_op_margin:.1%} -> {newest_op_margin:.1%})"
            )
        elif newest_op_margin > 0:
            raw_score += 1
            details.append("Provozní marže pozitivní ale mírně poklesla")
        else:
            details.append("Provozní marže může být negativní nebo nejistá")
    else:
        details.append("Nedostatek datových bodů provozní marže")

    # 2. Úroveň hrubé marže
    gm_values = [fi.gross_margin for fi in financial_line_items if fi.gross_margin is not None]
    if gm_values:
        # Vezmeme jen nejnovější
        recent_gm = gm_values[0]
        if recent_gm > 0.5:
            raw_score += 2
            details.append(f"Silná hrubá marže: {recent_gm:.1%}")
        elif recent_gm > 0.3:
            raw_score += 1
            details.append(f"Mírná hrubá marže: {recent_gm:.1%}")
        else:
            details.append(f"Nízká hrubá marže: {recent_gm:.1%}")
    else:
        details.append("Žádná data hrubé marže nejsou k dispozici")

    # 3. Víceletá stabilita marže
    #   např. pokud máme alespoň 3 datové body, zjistíme zda je směrodatná odchylka nízká.
    if len(op_margins) >= 3:
        stdev = statistics.pstdev(op_margins)
        if stdev < 0.02:
            raw_score += 2
            details.append("Provozní marže extrémně stabilní po několik let")
        elif stdev < 0.05:
            raw_score += 1
            details.append("Provozní marže rozumně stabilní")
        else:
            details.append("Volatilita provozní marže je vysoká")
    else:
        details.append("Nedostatek datových bodů marže pro kontrolu volatility")

    # škálování raw_score (max 6) na 0-10
    final_score = min(10, (raw_score / 6) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_management_efficiency_leverage(financial_line_items: List[Any]) -> Dict[str, Any]:
    """
    Vyhodnocení efektivity managementu a páky:
      - Návratnost vlastního kapitálu (ROE)
      - Poměr dluh k vlastnímu kapitálu
      - Možná kontrola zda je volný peněžní tok konzistentně pozitivní
    """
    if not financial_line_items:
        return {
            "score": 0,
            "details": "Žádná finanční data pro analýzu efektivity managementu",
        }

    details = []
    raw_score = 0  # až 6 => škálování na 0–10

    # 1. Návratnost vlastního kapitálu (ROE)
    ni_values = [fi.net_income for fi in financial_line_items if fi.net_income is not None]
    eq_values = [fi.shareholders_equity for fi in financial_line_items if fi.shareholders_equity is not None]
    if ni_values and eq_values and len(ni_values) == len(eq_values):
        recent_ni = ni_values[0]
        recent_eq = eq_values[0] if eq_values[0] else 1e-9
        if recent_ni > 0:
            roe = recent_ni / recent_eq
            if roe > 0.2:
                raw_score += 3
                details.append(f"Vysoký ROE: {roe:.1%}")
            elif roe > 0.1:
                raw_score += 2
                details.append(f"Mírný ROE: {roe:.1%}")
            elif roe > 0:
                raw_score += 1
                details.append(f"Pozitivní ale nízký ROE: {roe:.1%}")
            else:
                details.append(f"ROE je blízko nuly nebo negativní: {roe:.1%}")
        else:
            details.append("Nedávný čistý zisk je nulový nebo negativní, škodí ROE")
    else:
        details.append("Nedostatečná data pro výpočet ROE")

    # 2. Dluh k vlastnímu kapitálu
    debt_values = [fi.total_debt for fi in financial_line_items if fi.total_debt is not None]
    if debt_values and eq_values and len(debt_values) == len(eq_values):
        recent_debt = debt_values[0]
        recent_equity = eq_values[0] if eq_values[0] else 1e-9
        dte = recent_debt / recent_equity
        if dte < 0.3:
            raw_score += 2
            details.append(f"Nízký dluh k vlastnímu kapitálu: {dte:.2f}")
        elif dte < 1.0:
            raw_score += 1
            details.append(f"Zvládnutelný dluh k vlastnímu kapitálu: {dte:.2f}")
        else:
            details.append(f"Vysoký dluh k vlastnímu kapitálu: {dte:.2f}")
    else:
        details.append("Nedostatečná data pro analýzu dluh/vlastní kapitál")

    # 3. Konzistence FCF
    fcf_values = [fi.free_cash_flow for fi in financial_line_items if fi.free_cash_flow is not None]
    if fcf_values and len(fcf_values) >= 2:
        # Kontrola zda je FCF pozitivní v posledních letech
        positive_fcf_count = sum(1 for x in fcf_values if x and x > 0)
        # Budeme jednoduší: pokud je většina pozitivní, odměníme
        ratio = positive_fcf_count / len(fcf_values)
        if ratio > 0.8:
            raw_score += 1
            details.append(f"Většina období má pozitivní FCF ({positive_fcf_count}/{len(fcf_values)})")
        else:
            details.append("Volný peněžní tok je nekonzistentní nebo často negativní")
    else:
        details.append("Nedostatečná nebo žádná FCF data pro kontrolu konzistence")

    final_score = min(10, (raw_score / 6) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_fisher_valuation(financial_line_items: List[Any], market_cap: Optional[float]) -> Dict[str, Any]:
    """
    Phil Fisher je ochoten zaplatit za kvalitu a růst, ale stále kontroluje:
      - P/E
      - P/FCF
      - (Volitelně) Enterprise Value metriky, ale jednodušší přístup je typický
    Udělíme až 2 body pro každou ze dvou metrik => max 4 surové => škálování na 0–10.
    """
    if not financial_line_items or market_cap is None:
        return {"score": 0, "details": "Nedostatečná data pro provedení ocenění"}

    details = []
    raw_score = 0

    # Shromáždění potřebných dat
    net_incomes = [fi.net_income for fi in financial_line_items if fi.net_income is not None]
    fcf_values = [fi.free_cash_flow for fi in financial_line_items if fi.free_cash_flow is not None]

    # 1) P/E
    recent_net_income = net_incomes[0] if net_incomes else None
    if recent_net_income and recent_net_income > 0:
        pe = market_cap / recent_net_income
        pe_points = 0
        if pe < 20:
            pe_points = 2
            details.append(f"Rozumně atraktivní P/E: {pe:.2f}")
        elif pe < 30:
            pe_points = 1
            details.append(f"Poněkud vysoký ale možná ospravedlnitelný P/E: {pe:.2f}")
        else:
            details.append(f"Velmi vysoký P/E: {pe:.2f}")
        raw_score += pe_points
    else:
        details.append("Žádný pozitivní čistý zisk pro výpočet P/E")

    # 2) P/FCF
    recent_fcf = fcf_values[0] if fcf_values else None
    if recent_fcf and recent_fcf > 0:
        pfcf = market_cap / recent_fcf
        pfcf_points = 0
        if pfcf < 20:
            pfcf_points = 2
            details.append(f"Rozumný P/FCF: {pfcf:.2f}")
        elif pfcf < 30:
            pfcf_points = 1
            details.append(f"Poněkud vysoký P/FCF: {pfcf:.2f}")
        else:
            details.append(f"Nadměrně vysoký P/FCF: {pfcf:.2f}")
        raw_score += pfcf_points
    else:
        details.append("Žádný pozitivní volný peněžní tok pro výpočet P/FCF")

    # škálování raw_score (max 4) na 0–10
    final_score = min(10, (raw_score / 4) * 10)
    return {"score": final_score, "details": "; ".join(details)}


def analyze_insider_activity(insider_trades: List[Any]) -> Dict[str, Any]:
    """
    Jednoduchá analýza insider obchodů:
      - Pokud jsou těžké insider nákupy, posuneme skóre nahoru.
      - Pokud je většinou prodej, snížíme ho.
      - Jinak neutrální.
    """
    # Výchozí je neutrální (5/10).
    score = 5
    details = []

    if not insider_trades:
        details.append("Žádná data insider obchodů; výchozí neutrální")
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
        details.append("Nenalezeny žádné nákup/prodej transakce; neutrální")
        return {"score": score, "details": "; ".join(details)}

    buy_ratio = buys / total
    if buy_ratio > 0.7:
        score = 8
        details.append(f"Těžké insider nákupy: {buys} nákupů vs. {sells} prodejů")
    elif buy_ratio > 0.4:
        score = 6
        details.append(f"Mírné insider nákupy: {buys} nákupů vs. {sells} prodejů")
    else:
        score = 4
        details.append(f"Většinou insider prodeje: {buys} nákupů vs. {sells} prodejů")

    return {"score": score, "details": "; ".join(details)}


def analyze_sentiment(news_items: List[Any]) -> Dict[str, Any]:
    """
    Základní sentiment zpráv: kontrola negativních klíčových slov vs. celkový objem.
    """
    if not news_items:
        return {"score": 5, "details": "Žádná data zpráv; výchozí neutrální sentiment"}

    negative_keywords = ["lawsuit", "fraud", "negative", "downturn", "decline", "investigation", "recall"]
    negative_count = 0
    for news in news_items:
        title_lower = (news.title or "").lower()
        if any(word in title_lower for word in negative_keywords):
            negative_count += 1

    details = []
    if negative_count > len(news_items) * 0.3:
        score = 3
        details.append(f"Vysoký podíl negativních titulků: {negative_count}/{len(news_items)}")
    elif negative_count > 0:
        score = 6
        details.append(f"Některé negativní titulky: {negative_count}/{len(news_items)}")
    else:
        score = 8
        details.append("Většinou pozitivní/neutrální titulky")

    return {"score": score, "details": "; ".join(details)}


def generate_fisher_output(
    ticker: str,
    analysis_data: Dict[str, Any],
    state: AgentState,
    agent_id: str,
) -> PhilFisherSignal:
    """
    Generuje JSON signál ve stylu Phil Fisher.
    """
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """Jste Phil Fisher AI agent, činíte investiční rozhodnutí pomocí jeho principů:

              1. Zdůrazňujte dlouhodobý růstový potenciál a kvalitu managementu.
              2. Zaměřte se na společnosti investující do R&D pro budoucí produkty/služby.
              3. Hledejte silnou ziskovost a konzistentní marže.
              4. Ochotni zaplatit více za výjimečné společnosti, ale stále pozorní na ocenění.
              5. Spoléhejte na důkladný výzkum (scuttlebutt) a důkladné fundamentální kontroly.

              Při poskytování svého zdůvodnění buďte důkladní a konkrétní:
              1. Diskutujte růstové vyhlídky společnosti detailně s konkrétními metrikami a trendy
              2. Vyhodnoťte kvalitu managementu a jejich rozhodnutí o alokaci kapitálu
              3. Zdůrazněte R&D investice a produktovou pipeline, která by mohla řídit budoucí růst
              4. Posouďte konzistenci marží a ziskových metrik s přesnými čísly
              5. Vysvětlete konkurenční výhody, které by mohly udržet růst po 3-5+ let
              6. Používejte Phil Fisher's metodický, na růst zaměřený a dlouhodobě orientovaný hlas

              Například, pokud bullish: "Tata společnost vykazuje charakteristiky trvalého růstu, které hledáme,
              s tržbami rostoucími o 18% ročně po pět let. Management prokázal výjimečnou prozíravost alokací
              15% tržeb do R&D, což vyprodukovalo tři slibné nové produktové linie. Konzistentní provozní marže
              22-24% indikují cenovou sílu a provozní efektivitu, která by měla pokračovat..."

              Například, pokud bearish: "Navzdory působení v rostoucím odvětví se managementu nepodařilo přeložit
              R&D investice (pouze 5% tržeb) do smysluplných nových produktů. Marže kolísaly mezi 10-15%, ukazující
              nekonzistentní provozní realizaci. Společnost čelí rostoucí konkurenci od tří větších konkurentů
              s lepšími distribučními sítěmi. Vzhledem k těmto obavám o dlouhodobou udržitelnost růstu..."

              Musíte vyprodukovat JSON objekt s:
                - "signal": "bullish" nebo "bearish" nebo "neutral"
                - "confidence": float mezi 0 a 100
                - "reasoning": detailní vysvětlení
              """,
            ),
            (
                "human",
                """Na základě následující analýzy vytvořte Phil Fisher-style investiční signál.

              Data analýzy pro {ticker}:
              {analysis_data}

              Vraťte obchodní signál v tomto JSON formátu:
              {{
                "signal": "bullish/bearish/neutral",
                "confidence": float (0-100),
                "reasoning": "string"
              }}
              """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    def create_default_signal():
        return PhilFisherSignal(signal="neutral", confidence=0.0, reasoning="Chyba v analýze, výchozí neutral")

    result = call_llm(
        prompt=prompt,
        pydantic_model=PhilFisherSignal,
        state=state,
        agent_name=agent_id,
        default_factory=create_default_signal,
    )
    return cast(PhilFisherSignal, result)
