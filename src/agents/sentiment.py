"""Sentiment Analyst - Analyzes market sentiment and generates trading signals for multiple tickers."""

import json
from typing import Any, Dict

import numpy as np
import pandas as pd
from langchain_core.messages import HumanMessage

from src.exceptions import APIKeyError
from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_company_news, get_insider_trades
from src.utils.api_key import get_api_key_from_state
from src.utils.constants import COMMODITY_SYMBOLS
from src.utils.progress import progress


# Agent pro analýzu sentimentu
def sentiment_analyst_agent(state: AgentState, agent_id: str = "sentiment_analyst_agent") -> Dict[str, Any]:
    """Analyzuje tržní sentiment a generuje obchodní signály pro více tickerů."""
    data = state.get("data", {})
    end_date = data.get("end_date")
    if end_date is None:
        raise ValueError("end_date not found in state data")
    tickers = data.get("tickers")
    if tickers is None:
        raise ValueError("tickers not found in state data")
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")
    if api_key is None:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")
    # Inicializace analýzy sentimentu pro každý ticker
    sentiment_analysis = {}

    for ticker in tickers:
        # Handle commodity symbols with specialized sentiment analysis
        if ticker in COMMODITY_SYMBOLS:
            progress.update_status(agent_id, ticker, "Analýza sentimentu komodity")
            sentiment_analysis[ticker] = analyze_commodity_sentiment(ticker, end_date, api_key, agent_id)
            continue
        progress.update_status(agent_id, ticker, "Načítání insider obchodů")

        # Získání insider obchodů
        insider_trades = get_insider_trades(
            ticker=ticker,
            end_date=end_date,
            limit=1000,
            api_key=api_key,
        )

        progress.update_status(agent_id, ticker, "Analýza obchodních vzorců")

        # Získání signálů z insider obchodů
        transaction_shares = pd.Series([t.transaction_shares for t in insider_trades]).dropna()
        insider_signals = np.where(transaction_shares < 0, "bearish", "bullish").tolist()

        progress.update_status(agent_id, ticker, "Načítání firemních zpráv")

        # Získání firemních zpráv
        company_news = get_company_news(ticker, end_date, limit=100, api_key=api_key)

        # Získání sentimentu z firemních zpráv
        sentiment = pd.Series([n.sentiment for n in company_news]).dropna()
        news_signals = np.where(
            sentiment == "negative", "bearish", np.where(sentiment == "positive", "bullish", "neutral")
        ).tolist()

        progress.update_status(agent_id, ticker, "Kombinování signálů")
        # Kombinace signálů z obou zdrojů s váhami
        insider_weight = 0.3
        news_weight = 0.7

        # Výpočet vážených počtů signálů
        bullish_signals = (
            insider_signals.count("bullish") * insider_weight + news_signals.count("bullish") * news_weight
        )
        bearish_signals = (
            insider_signals.count("bearish") * insider_weight + news_signals.count("bearish") * news_weight
        )

        if bullish_signals > bearish_signals:
            overall_signal = "bullish"
        elif bearish_signals > bullish_signals:
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"

        # Výpočet úrovně spolehlivosti na základě váženého poměru
        total_weighted_signals = len(insider_signals) * insider_weight + len(news_signals) * news_weight
        confidence = 0  # Výchozí spolehlivost když nejsou žádné signály
        if total_weighted_signals > 0:
            confidence = round((max(bullish_signals, bearish_signals) / total_weighted_signals) * 100, 2)

        # Určení typu signálu pro signal_determination
        if bullish_signals > bearish_signals:
            signal_type = "Býčí"
        elif bearish_signals > bullish_signals:
            signal_type = "Medvědí"
        else:
            signal_type = "Neutrální"

        # Vytvoření strukturovaného zdůvodnění podobného technické analýze
        reasoning = {
            "insider_trading": {
                "signal": "bullish"
                if insider_signals.count("bullish") > insider_signals.count("bearish")
                else "bearish"
                if insider_signals.count("bearish") > insider_signals.count("bullish")
                else "neutral",
                "confidence": round(
                    (
                        max(insider_signals.count("bullish"), insider_signals.count("bearish"))
                        / max(len(insider_signals), 1)
                    )
                    * 100
                ),
                "metrics": {
                    "total_trades": len(insider_signals),
                    "bullish_trades": insider_signals.count("bullish"),
                    "bearish_trades": insider_signals.count("bearish"),
                    "weight": insider_weight,
                    "weighted_bullish": round(insider_signals.count("bullish") * insider_weight, 1),
                    "weighted_bearish": round(insider_signals.count("bearish") * insider_weight, 1),
                },
            },
            "news_sentiment": {
                "signal": "bullish"
                if news_signals.count("bullish") > news_signals.count("bearish")
                else "bearish"
                if news_signals.count("bearish") > news_signals.count("bullish")
                else "neutral",
                "confidence": round(
                    (max(news_signals.count("bullish"), news_signals.count("bearish")) / max(len(news_signals), 1))
                    * 100
                ),
                "metrics": {
                    "total_articles": len(news_signals),
                    "bullish_articles": news_signals.count("bullish"),
                    "bearish_articles": news_signals.count("bearish"),
                    "neutral_articles": news_signals.count("neutral"),
                    "weight": news_weight,
                    "weighted_bullish": round(news_signals.count("bullish") * news_weight, 1),
                    "weighted_bearish": round(news_signals.count("bearish") * news_weight, 1),
                },
            },
            "combined_analysis": {
                "total_weighted_bullish": round(bullish_signals, 1),
                "total_weighted_bearish": round(bearish_signals, 1),
                "signal_determination": f"{signal_type} na základě porovnání vážených signálů",
            },
        }

        sentiment_analysis[ticker] = {
            "signal": overall_signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        progress.update_status(agent_id, ticker, "Hotovo", analysis=json.dumps(reasoning, indent=4))

    # Vytvoření zprávy o sentimentu
    message = HumanMessage(
        content=json.dumps(sentiment_analysis),
        name=agent_id,
    )

    # Výpis zdůvodnění pokud je nastaven příznak
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(sentiment_analysis, "Sentiment Analysis Agent")

    # Přidání signálu do seznamu analyst_signals
    if "analyst_signals" not in state["data"]:
        state["data"]["analyst_signals"] = {}
    state["data"]["analyst_signals"][agent_id] = sentiment_analysis

    progress.update_status(agent_id, None, "Hotovo")

    return {
        "messages": [message],
        "data": data,
    }


def analyze_commodity_sentiment(ticker: str, end_date: str, api_key: str, agent_id: str) -> Dict[str, Any]:
    """Analyzuje sentiment pro komodity na základě cenových vzorců a volatility."""
    from src.tools.api import get_prices, prices_to_df
    import pandas as pd
    
    progress.update_status(agent_id, ticker, "Načítání cenových dat komodity")
    
    # Získání cenových dat pro analýzu sentimentu
    prices = get_prices(
        ticker=ticker,
        start_date="2023-01-01",  # Delší historie pro sentiment analýzu
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
    
    # Komoditní sentiment analýza
    signals = []
    reasoning = {}
    
    progress.update_status(agent_id, ticker, "Analýza cenového momentu")
    
    # 1. Cenové momentum jako indikátor sentimentu
    returns = prices_df["close"].pct_change().dropna()
    recent_returns = returns.tail(10).mean()  # Průměrný výnos za posledních 10 dní
    
    if recent_returns > 0.02:  # Silné pozitivní momentum
        momentum_signal = "bullish"
        momentum_desc = "Silné pozitivní cenové momentum"
    elif recent_returns < -0.02:  # Silné negativní momentum
        momentum_signal = "bearish"
        momentum_desc = "Silné negativní cenové momentum"
    else:
        momentum_signal = "neutral"
        momentum_desc = "Neutrální cenové momentum"
    
    signals.append(momentum_signal)
    reasoning["price_momentum"] = {
        "signal": momentum_signal,
        "confidence": min(abs(recent_returns) * 50, 100),
        "metrics": {
            "recent_returns": f"{recent_returns:.2%}",
            "interpretation": momentum_desc
        }
    }
    
    progress.update_status(agent_id, ticker, "Analýza objemového sentimentu")
    
    # 2. Objemová analýza jako sentiment indikátor
    volume_ma = prices_df["volume"].rolling(20).mean()
    recent_volume = prices_df["volume"].tail(5).mean()
    volume_ratio = recent_volume / volume_ma.iloc[-1] if volume_ma.iloc[-1] > 0 else 1.0
    
    if volume_ratio > 1.5:  # Vysoký objem = zvýšený zájem
        volume_signal = "bullish"
        volume_desc = "Vysoký objem indikuje zvýšený zájem"
    elif volume_ratio < 0.7:  # Nízký objem = snížený zájem
        volume_signal = "bearish"
        volume_desc = "Nízký objem indikuje snížený zájem"
    else:
        volume_signal = "neutral"
        volume_desc = "Normální úroveň objemu"
    
    signals.append(volume_signal)
    reasoning["volume_sentiment"] = {
        "signal": volume_signal,
        "confidence": min(abs(volume_ratio - 1) * 100, 100),
        "metrics": {
            "volume_ratio": f"{volume_ratio:.2f}",
            "interpretation": volume_desc
        }
    }
    
    progress.update_status(agent_id, ticker, "Analýza volatilního sentimentu")
    
    # 3. Volatilita jako sentiment indikátor
    volatility = returns.std() * (252 ** 0.5)  # Anualizovaná volatilita
    recent_volatility = returns.tail(10).std() * (252 ** 0.5)
    volatility_change = (recent_volatility - volatility) / volatility if volatility > 0 else 0
    
    if volatility_change > 0.2:  # Rostoucí volatilita
        volatility_signal = "bearish"  # Rostoucí volatilita = nejistota
        volatility_desc = "Rostoucí volatilita indikuje nejistotu"
    elif volatility_change < -0.2:  # Klesající volatilita
        volatility_signal = "bullish"  # Klesající volatilita = stabilizace
        volatility_desc = "Klesající volatilita indikuje stabilizaci"
    else:
        volatility_signal = "neutral"
        volatility_desc = "Stabilní úroveň volatility"
    
    signals.append(volatility_signal)
    reasoning["volatility_sentiment"] = {
        "signal": volatility_signal,
        "confidence": min(abs(volatility_change) * 100, 100),
        "metrics": {
            "volatility_change": f"{volatility_change:.2%}",
            "current_volatility": f"{recent_volatility:.2%}",
            "interpretation": volatility_desc
        }
    }
    
    progress.update_status(agent_id, ticker, "Analýza trendového sentimentu")
    
    # 4. Trendový sentiment
    short_ma = prices_df["close"].rolling(10).mean()
    long_ma = prices_df["close"].rolling(30).mean()
    
    current_price = prices_df["close"].iloc[-1]
    trend_strength = (current_price - long_ma.iloc[-1]) / long_ma.iloc[-1] if long_ma.iloc[-1] > 0 else 0
    
    if trend_strength > 0.05:  # Silný vzestupný trend
        trend_signal = "bullish"
        trend_desc = "Silný vzestupný trend"
    elif trend_strength < -0.05:  # Silný sestupný trend
        trend_signal = "bearish"
        trend_desc = "Silný sestupný trend"
    else:
        trend_signal = "neutral"
        trend_desc = "Boční nebo slabý trend"
    
    signals.append(trend_signal)
    reasoning["trend_sentiment"] = {
        "signal": trend_signal,
        "confidence": min(abs(trend_strength) * 200, 100),
        "metrics": {
            "trend_strength": f"{trend_strength:.2%}",
            "interpretation": trend_desc
        }
    }
    
    progress.update_status(agent_id, ticker, "Výpočet finálního sentimentu")
    
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
    confidence = round(max(bullish_signals, bearish_signals) / total_signals * 100, 2)
    
    # Přidání souhrnné analýzy
    reasoning["combined_analysis"] = {
        "total_bullish": bullish_signals,
        "total_bearish": bearish_signals,
        "total_neutral": signals.count("neutral"),
        "signal_determination": f"Sentiment {overall_signal} na základě {total_signals} indikátorů"
    }
    
    progress.update_status(agent_id, ticker, "Hotovo - sentiment komodity", analysis=json.dumps(reasoning, indent=4))
    
    return {
        "signal": overall_signal,
        "confidence": confidence,
        "reasoning": reasoning,
    }
