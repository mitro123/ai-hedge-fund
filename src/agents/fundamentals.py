"""Fundamentals Analyst - Analyzes fundamental data and generates trading signals for multiple tickers."""

import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage

from src.exceptions import APIKeyError
from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_financial_metrics
from src.utils.api_key import get_api_key_from_state
from src.utils.constants import COMMODITY_SYMBOLS
from src.utils.progress import progress


# Agent fundamentální analýzy
def fundamentals_analyst_agent(
    state: AgentState, agent_id: str = "fundamentals_analyst_agent"
) -> Dict[str, Any]:
    """Analyzuje fundamentální data a generuje obchodní signály pro více tickerů."""
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")
    if api_key is None:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")
    # Inicializace fundamentální analýzy pro každý ticker
    fundamental_analysis = {}

    for ticker in tickers:
        # Handle commodity symbols with specialized fundamental analysis
        if ticker in COMMODITY_SYMBOLS:
            progress.update_status(agent_id, ticker, "Analýza komoditních fundamentů")
            fundamental_analysis[ticker] = analyze_commodity_fundamentals(ticker, end_date, api_key, agent_id)
            continue
        progress.update_status(agent_id, ticker, "Načítání finančních metrik")

        # Získání finančních metrik
        financial_metrics = get_financial_metrics(
            ticker=ticker,
            end_date=end_date,
            period="ttm",
            limit=10,
            api_key=api_key,
        )

        if not financial_metrics:
            progress.update_status(agent_id, ticker, "Chyba: Nenalezeny finanční metriky")
            continue

        # Získání nejnovějších finančních metrik
        metrics = financial_metrics[0]

        # Inicializace seznamu signálů pro různé fundamentální aspekty
        signals = []
        reasoning = {}

        progress.update_status(agent_id, ticker, "Analýza ziskovosti")
        # 1. Analýza ziskovosti
        return_on_equity = metrics.return_on_equity
        net_margin = metrics.net_margin
        operating_margin = metrics.operating_margin

        thresholds = [
            (return_on_equity, 0.15),  # Silný ROE nad 15%
            (net_margin, 0.20),  # Zdravé ziskové marže
            (operating_margin, 0.15),  # Silná provozní efektivita
        ]
        profitability_score = sum(metric is not None and metric > threshold for metric, threshold in thresholds)

        signals.append("bullish" if profitability_score >= 2 else "bearish" if profitability_score == 0 else "neutral")
        reasoning["profitability_signal"] = {
            "signal": signals[0],
            "details": (f"ROE: {return_on_equity:.2%}" if return_on_equity else "ROE: N/A")
            + ", "
            + (f"Net Margin: {net_margin:.2%}" if net_margin else "Net Margin: N/A")
            + ", "
            + (f"Op Margin: {operating_margin:.2%}" if operating_margin else "Op Margin: N/A"),
        }

        progress.update_status(agent_id, ticker, "Analýza růstu")
        # 2. Analýza růstu
        revenue_growth = metrics.revenue_growth
        earnings_growth = metrics.earnings_growth
        book_value_growth = metrics.book_value_growth

        thresholds = [
            (revenue_growth, 0.10),  # 10% růst tržeb
            (earnings_growth, 0.10),  # 10% růst zisků
            (book_value_growth, 0.10),  # 10% růst účetní hodnoty
        ]
        growth_score = sum(metric is not None and metric > threshold for metric, threshold in thresholds)

        signals.append("bullish" if growth_score >= 2 else "bearish" if growth_score == 0 else "neutral")
        reasoning["growth_signal"] = {
            "signal": signals[1],
            "details": (f"Revenue Growth: {revenue_growth:.2%}" if revenue_growth else "Revenue Growth: N/A")
            + ", "
            + (f"Earnings Growth: {earnings_growth:.2%}" if earnings_growth else "Earnings Growth: N/A"),
        }

        progress.update_status(agent_id, ticker, "Analýza finančního zdraví")
        # 3. Finanční zdraví
        current_ratio = metrics.current_ratio
        debt_to_equity = metrics.debt_to_equity
        free_cash_flow_per_share = metrics.free_cash_flow_per_share
        earnings_per_share = metrics.earnings_per_share

        health_score = 0
        if current_ratio and current_ratio > 1.5:  # Silná likvidita
            health_score += 1
        if debt_to_equity and debt_to_equity < 0.5:  # Konzervativní úroveň dluhu
            health_score += 1
        if (
            free_cash_flow_per_share and earnings_per_share and free_cash_flow_per_share > earnings_per_share * 0.8
        ):  # Silná konverze FCF
            health_score += 1

        signals.append("bullish" if health_score >= 2 else "bearish" if health_score == 0 else "neutral")
        reasoning["financial_health_signal"] = {
            "signal": signals[2],
            "details": (f"Current Ratio: {current_ratio:.2f}" if current_ratio else "Current Ratio: N/A")
            + ", "
            + (f"D/E: {debt_to_equity:.2f}" if debt_to_equity else "D/E: N/A"),
        }

        progress.update_status(agent_id, ticker, "Analýza oceňovacích poměrů")
        # 4. Poměry cena k X
        pe_ratio = metrics.price_to_earnings_ratio
        pb_ratio = metrics.price_to_book_ratio
        ps_ratio = metrics.price_to_sales_ratio

        thresholds = [
            (pe_ratio, 25),  # Rozumný P/E poměr
            (pb_ratio, 3),  # Rozumný P/B poměr
            (ps_ratio, 5),  # Rozumný P/S poměr
        ]
        price_ratio_score = sum(metric is not None and metric > threshold for metric, threshold in thresholds)

        signals.append("bearish" if price_ratio_score >= 2 else "bullish" if price_ratio_score == 0 else "neutral")
        reasoning["price_ratios_signal"] = {
            "signal": signals[3],
            "details": (f"P/E: {pe_ratio:.2f}" if pe_ratio else "P/E: N/A")
            + ", "
            + (f"P/B: {pb_ratio:.2f}" if pb_ratio else "P/B: N/A")
            + ", "
            + (f"P/S: {ps_ratio:.2f}" if ps_ratio else "P/S: N/A"),
        }

        progress.update_status(agent_id, ticker, "Výpočet finálního signálu")
        # Určení celkového signálu
        bullish_signals = signals.count("bullish")
        bearish_signals = signals.count("bearish")

        if bullish_signals > bearish_signals:
            overall_signal = "bullish"
        elif bearish_signals > bullish_signals:
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"

        # Výpočet úrovně spolehlivosti
        total_signals = len(signals)
        confidence = round(max(bullish_signals, bearish_signals) / total_signals, 2) * 100

        fundamental_analysis[ticker] = {
            "signal": overall_signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        progress.update_status(agent_id, ticker, "Done", analysis=json.dumps(reasoning, indent=4))

    # Vytvoření zprávy fundamentální analýzy
    message = HumanMessage(
        content=json.dumps(fundamental_analysis),
        name=agent_id,
    )

    # Zobrazení zdůvodnění pokud je nastaven příznak
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(fundamental_analysis, "Agent fundamentální analýzy")

    # Přidání signálu do seznamu analyst_signals
    if "analyst_signals" not in state["data"]:
        state["data"]["analyst_signals"] = {}
    state["data"]["analyst_signals"][agent_id] = fundamental_analysis

    progress.update_status(agent_id, None, "Done")

    return {
        "messages": [message],
        "data": data,
    }


def analyze_commodity_fundamentals(ticker: str, end_date: str, api_key: str, agent_id: str) -> Dict[str, Any]:
    """Analyzuje fundamentální faktory pro komodity."""
    from src.tools.api import get_prices, prices_to_df
    import pandas as pd
    
    progress.update_status(agent_id, ticker, "Načítání cenových dat komodity")
    
    # Získání cenových dat pro analýzu volatility a trendů
    prices = get_prices(
        ticker=ticker,
        start_date="2023-01-01",  # Delší historie pro fundamentální analýzu
        end_date=end_date,
        api_key=api_key,
    )
    
    if not prices:
        progress.update_status(agent_id, ticker, "Chyba: Nenalezena cenová data")
        return {
            "signal": "neutral",
            "confidence": 0.0,
            "reasoning": {
                "message": f"Nelze získat cenová data pro komoditu {ticker}"
            },
        }
    
    prices_df = prices_to_df(prices)
    
    # Komoditní fundamentální analýza
    signals = []
    reasoning = {}
    
    progress.update_status(agent_id, ticker, "Analýza volatility komodity")
    
    # 1. Analýza volatility (klíčová pro komodity)
    returns = prices_df["close"].pct_change().dropna()
    volatility = returns.std() * (252 ** 0.5)  # Anualizovaná volatilita
    
    # Vysoká volatilita může signalizovat nejistotu nebo příležitosti
    if volatility > 0.3:  # Vysoká volatilita
        vol_signal = "neutral"  # Vysoká volatilita = nejistota
    elif volatility > 0.15:  # Střední volatilita
        vol_signal = "bullish"  # Zdravá volatilita pro trading
    else:  # Nízká volatilita
        vol_signal = "bearish"  # Možná stagnace
    
    signals.append(vol_signal)
    reasoning["volatility_analysis"] = {
        "signal": vol_signal,
        "details": f"Anualizovaná volatilita: {volatility:.2%}",
        "interpretation": "Vysoká volatilita = nejistota, střední = příležitost, nízká = stagnace"
    }
    
    progress.update_status(agent_id, ticker, "Analýza trendu komodity")
    
    # 2. Trendová analýza (důležitá pro komodity)
    short_ma = prices_df["close"].rolling(20).mean()
    long_ma = prices_df["close"].rolling(50).mean()
    
    current_price = prices_df["close"].iloc[-1]
    current_short_ma = short_ma.iloc[-1]
    current_long_ma = long_ma.iloc[-1]
    
    if current_price > current_short_ma > current_long_ma:
        trend_signal = "bullish"
        trend_desc = "Silný vzestupný trend"
    elif current_price < current_short_ma < current_long_ma:
        trend_signal = "bearish"
        trend_desc = "Silný sestupný trend"
    else:
        trend_signal = "neutral"
        trend_desc = "Smíšený nebo boční trend"
    
    signals.append(trend_signal)
    reasoning["trend_analysis"] = {
        "signal": trend_signal,
        "details": f"Cena: ${current_price:.2f}, MA20: ${current_short_ma:.2f}, MA50: ${current_long_ma:.2f}",
        "interpretation": trend_desc
    }
    
    progress.update_status(agent_id, ticker, "Analýza momentum komodity")
    
    # 3. Momentum analýza
    momentum_1m = returns.rolling(21).sum().iloc[-1]  # 1-měsíční momentum
    momentum_3m = returns.rolling(63).sum().iloc[-1]  # 3-měsíční momentum
    
    if momentum_1m > 0.05 and momentum_3m > 0.1:
        momentum_signal = "bullish"
        momentum_desc = "Silné pozitivní momentum"
    elif momentum_1m < -0.05 and momentum_3m < -0.1:
        momentum_signal = "bearish"
        momentum_desc = "Silné negativní momentum"
    else:
        momentum_signal = "neutral"
        momentum_desc = "Smíšené momentum"
    
    signals.append(momentum_signal)
    reasoning["momentum_analysis"] = {
        "signal": momentum_signal,
        "details": f"1M momentum: {momentum_1m:.2%}, 3M momentum: {momentum_3m:.2%}",
        "interpretation": momentum_desc
    }
    
    progress.update_status(agent_id, ticker, "Analýza sezónnosti komodity")
    
    # 4. Sezónní analýza (specifická pro komodity)
    try:
        prices_df['month'] = pd.to_datetime(prices_df.index).month
        monthly_returns = prices_df.groupby('month')['close'].pct_change().mean()
        current_month = pd.to_datetime(end_date).month
        
        # Bezpečné ověření, zda monthly_returns je Series a obsahuje current_month
        if hasattr(monthly_returns, 'index') and current_month in monthly_returns.index:
            seasonal_return = monthly_returns.loc[current_month]
            if seasonal_return > 0.02:  # Historicky silný měsíc
                seasonal_signal = "bullish"
                seasonal_desc = "Historicky silný sezónní měsíc"
            elif seasonal_return < -0.02:  # Historicky slabý měsíc
                seasonal_signal = "bearish"
                seasonal_desc = "Historicky slabý sezónní měsíc"
            else:
                seasonal_signal = "neutral"
                seasonal_desc = "Neutrální sezónní období"
        else:
            seasonal_signal = "neutral"
            seasonal_return = 0.0
            seasonal_desc = "Nedostatek sezónních dat"
    except Exception:
        seasonal_signal = "neutral"
        seasonal_return = 0.0
        seasonal_desc = "Chyba při sezónní analýze"
        current_month = 1  # Výchozí hodnota pro případ chyby
    
    signals.append(seasonal_signal)
    reasoning["seasonal_analysis"] = {
        "signal": seasonal_signal,
        "details": f"Průměrný výnos v měsíci {current_month}: {seasonal_return:.2%}",
        "interpretation": seasonal_desc
    }
    
    progress.update_status(agent_id, ticker, "Výpočet finálního signálu komodity")
    
    # Určení celkového signálu
    bullish_signals = signals.count("bullish")
    bearish_signals = signals.count("bearish")
    
    if bullish_signals > bearish_signals:
        overall_signal = "bullish"
    elif bearish_signals > bullish_signals:
        overall_signal = "bearish"
    else:
        overall_signal = "neutral"
    
    # Výpočet úrovně spolehlivosti
    total_signals = len(signals)
    confidence = round(max(bullish_signals, bearish_signals) / total_signals, 2) * 100
    
    progress.update_status(agent_id, ticker, "Hotovo - komodita", analysis=json.dumps(reasoning, indent=4))
    
    return {
        "signal": overall_signal,
        "confidence": confidence,
        "reasoning": reasoning,
    }
