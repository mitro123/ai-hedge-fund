import datetime
import os
import time

import pandas as pd
import requests

from src.data.cache import get_cache
from src.data.models import (
    CompanyFactsResponse,
    CompanyNews,
    CompanyNewsResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    InsiderTrade,
    InsiderTradeResponse,
    LineItem,
    LineItemResponse,
    Price,
    PriceResponse,
)
from src.exceptions import APIError, APIKeyError, APIRateLimitError, APIResponseError, DataFetchError

# Global cache instance
_cache = get_cache()


def _make_api_request(
    url: str, headers: dict, method: str = "GET", json_data: dict | None = None, max_retries: int = 3
) -> requests.Response:
    """
    Make an API request with rate limiting handling and moderate backoff.

    Args:
        url: The URL to request
        headers: Headers to include in the request
        method: HTTP method (GET or POST)
        json_data: JSON data for POST requests
        max_retries: Maximum number of retries (default: 3)

    Returns:
        requests.Response: The response object

    Raises:
        APIRateLimitError: If rate limit is exceeded after all retries
        APIResponseError: If the request fails with a non-429 error
        APIError: For other API-related errors
    """
    last_response = None

    for attempt in range(max_retries + 1):  # +1 for initial attempt
        try:
            if method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json_data)
            else:
                response = requests.get(url, headers=headers)

            last_response = response

            if response.status_code == 429 and attempt < max_retries:
                # Linear backoff: 60s, 90s, 120s, 150s...
                delay = 60 + (30 * attempt)
                print(
                    f"Rate limited (429). Attempt {attempt + 1}/{max_retries + 1}. Waiting {delay}s before retrying..."
                )
                time.sleep(delay)
                continue
            elif response.status_code == 429:
                # Final 429 after all retries
                raise APIRateLimitError(
                    retry_after=60, message=f"API rate limit exceeded after {max_retries + 1} attempts"
                )

            # Return the response (success or other errors)
            return response

        except requests.RequestException as e:
            if attempt == max_retries:
                raise APIError(
                    message=f"Network error after {max_retries + 1} attempts: {str(e)}",
                    error_code="NETWORK_ERROR",
                    details={"url": url, "attempt": attempt + 1},
                    original_exception=e,
                )
            # Continue to next attempt for network errors
            time.sleep(5)  # Short delay before retry

    # This should never be reached, but just in case
    if last_response:
        return last_response
    else:
        raise APIError(
            message="Failed to make API request - no response received", error_code="NO_RESPONSE", details={"url": url}
        )


def get_prices(ticker: str, start_date: str, end_date: str, api_key: str | None = None) -> list[Price]:
    """
    Fetch price data from cache or API.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: Optional API key, will use environment variable if not provided

    Returns:
        List of Price objects

    Raises:
        APIKeyError: If API key is missing
        DataFetchError: If data cannot be fetched
        APIResponseError: If API returns an error
    """
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{start_date}_{end_date}"

    # Check cache first - simple exact match
    if cached_data := _cache.get_prices(cache_key):
        return [Price(**price) for price in cached_data]

    # Validate API key
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if not financial_api_key:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")

    # If not in cache, fetch from API
    headers = {"X-API-KEY": financial_api_key}
    url = f"https://api.financialdatasets.ai/prices/?ticker={ticker}&interval=day&interval_multiplier=1&start_date={start_date}&end_date={end_date}"

    try:
        response = _make_api_request(url, headers)
        if response.status_code != 200:
            raise APIResponseError(response.status_code, response.text, url)

        # Parse response with Pydantic model
        price_response = PriceResponse(**response.json())
        prices = price_response.prices

        if not prices:
            return []

        # Cache the results using the comprehensive cache key
        _cache.set_prices(cache_key, [p.model_dump() for p in prices])
        return prices

    except (APIError, APIKeyError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise DataFetchError(ticker, "price", f"Unexpected error: {str(e)}")


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    api_key: str | None = None,
) -> list[FinancialMetrics]:
    """
    Fetch financial metrics from cache or API.

    Args:
        ticker: Stock ticker symbol
        end_date: End date in YYYY-MM-DD format
        period: Period type (ttm, annual, quarterly)
        limit: Maximum number of records to fetch
        api_key: Optional API key, will use environment variable if not provided

    Returns:
        List of FinancialMetrics objects

    Raises:
        APIKeyError: If API key is missing
        DataFetchError: If data cannot be fetched
        APIResponseError: If API returns an error
    """
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{period}_{end_date}_{limit}"

    # Check cache first - simple exact match
    if cached_data := _cache.get_financial_metrics(cache_key):
        return [FinancialMetrics(**metric) for metric in cached_data]

    # Validate API key
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if not financial_api_key:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")

    # If not in cache, fetch from API
    headers = {"X-API-KEY": financial_api_key}
    url = f"https://api.financialdatasets.ai/financial-metrics/?ticker={ticker}&report_period_lte={end_date}&limit={limit}&period={period}"

    try:
        response = _make_api_request(url, headers)
        if response.status_code != 200:
            raise APIResponseError(response.status_code, response.text, url)

        # Parse response with Pydantic model
        metrics_response = FinancialMetricsResponse(**response.json())
        financial_metrics = metrics_response.financial_metrics

        if not financial_metrics:
            return []

        # Cache the results as dicts using the comprehensive cache key
        _cache.set_financial_metrics(cache_key, [m.model_dump() for m in financial_metrics])
        return financial_metrics

    except (APIError, APIKeyError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise DataFetchError(ticker, "financial_metrics", f"Unexpected error: {str(e)}")


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    api_key: str | None = None,
) -> list[LineItem]:
    """
    Search for specific line items in financial statements.

    Args:
        ticker: Stock ticker symbol
        line_items: List of line item names to search for
        end_date: End date in YYYY-MM-DD format
        period: Period type (ttm, annual, quarterly)
        limit: Maximum number of records to fetch
        api_key: Optional API key, will use environment variable if not provided

    Returns:
        List of LineItem objects

    Raises:
        APIKeyError: If API key is missing
        DataFetchError: If data cannot be fetched
        APIResponseError: If API returns an error
    """
    # Validate API key
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if not financial_api_key:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")

    headers = {"X-API-KEY": financial_api_key}
    url = "https://api.financialdatasets.ai/financials/search/line-items"

    body = {
        "tickers": [ticker],
        "line_items": line_items,
        "end_date": end_date,
        "period": period,
        "limit": limit,
    }

    try:
        response = _make_api_request(url, headers, method="POST", json_data=body)
        if response.status_code != 200:
            raise APIResponseError(response.status_code, response.text, url)

        data = response.json()
        response_model = LineItemResponse(**data)
        search_results = response_model.search_results

        if not search_results:
            return []

        return search_results[:limit]

    except (APIError, APIKeyError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise DataFetchError(ticker, "line_items", f"Unexpected error: {str(e)}")


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str | None = None,
) -> list[InsiderTrade]:
    """
    Fetch insider trades from cache or API.

    Args:
        ticker: Stock ticker symbol
        end_date: End date in YYYY-MM-DD format
        start_date: Optional start date in YYYY-MM-DD format
        limit: Maximum number of records to fetch
        api_key: Optional API key, will use environment variable if not provided

    Returns:
        List of InsiderTrade objects

    Raises:
        APIKeyError: If API key is missing
        DataFetchError: If data cannot be fetched
        APIResponseError: If API returns an error
    """
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"

    # Check cache first - simple exact match
    if cached_data := _cache.get_insider_trades(cache_key):
        return [InsiderTrade(**trade) for trade in cached_data]

    # Validate API key
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if not financial_api_key:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")

    headers = {"X-API-KEY": financial_api_key}
    all_trades = []
    current_end_date = end_date

    try:
        while True:
            url = f"https://api.financialdatasets.ai/insider-trades/?ticker={ticker}&filing_date_lte={current_end_date}"
            if start_date:
                url += f"&filing_date_gte={start_date}"
            url += f"&limit={limit}"

            response = _make_api_request(url, headers)
            if response.status_code != 200:
                raise APIResponseError(response.status_code, response.text, url)

            data = response.json()
            response_model = InsiderTradeResponse(**data)
            insider_trades = response_model.insider_trades

            if not insider_trades:
                break

            all_trades.extend(insider_trades)

            # Only continue pagination if we have a start_date and got a full page
            if not start_date or len(insider_trades) < limit:
                break

            # Update end_date to the oldest filing date from current batch for next iteration
            current_end_date = min(trade.filing_date for trade in insider_trades).split("T")[0]

            # If we've reached or passed the start_date, we can stop
            if current_end_date <= start_date:
                break

        if not all_trades:
            return []

        # Cache the results using the comprehensive cache key
        _cache.set_insider_trades(cache_key, [trade.model_dump() for trade in all_trades])
        return all_trades

    except (APIError, APIKeyError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise DataFetchError(ticker, "insider_trades", f"Unexpected error: {str(e)}")


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str | None = None,
) -> list[CompanyNews]:
    """
    Fetch company news from cache or API.

    Args:
        ticker: Stock ticker symbol
        end_date: End date in YYYY-MM-DD format
        start_date: Optional start date in YYYY-MM-DD format
        limit: Maximum number of records to fetch
        api_key: Optional API key, will use environment variable if not provided

    Returns:
        List of CompanyNews objects

    Raises:
        APIKeyError: If API key is missing
        DataFetchError: If data cannot be fetched
        APIResponseError: If API returns an error
    """
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"

    # Check cache first - simple exact match
    if cached_data := _cache.get_company_news(cache_key):
        return [CompanyNews(**news) for news in cached_data]

    # Validate API key
    financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
    if not financial_api_key:
        raise APIKeyError("FINANCIAL_DATASETS_API_KEY")

    headers = {"X-API-KEY": financial_api_key}
    all_news = []
    current_end_date = end_date

    try:
        while True:
            url = f"https://api.financialdatasets.ai/news/?ticker={ticker}&end_date={current_end_date}"
            if start_date:
                url += f"&start_date={start_date}"
            url += f"&limit={limit}"

            response = _make_api_request(url, headers)
            if response.status_code != 200:
                raise APIResponseError(response.status_code, response.text, url)

            data = response.json()
            response_model = CompanyNewsResponse(**data)
            company_news = response_model.news

            if not company_news:
                break

            all_news.extend(company_news)

            # Only continue pagination if we have a start_date and got a full page
            if not start_date or len(company_news) < limit:
                break

            # Update end_date to the oldest date from current batch for next iteration
            current_end_date = min(news.date for news in company_news).split("T")[0]

            # If we've reached or passed the start_date, we can stop
            if current_end_date <= start_date:
                break

        if not all_news:
            return []

        # Cache the results using the comprehensive cache key
        _cache.set_company_news(cache_key, [news.model_dump() for news in all_news])
        return all_news

    except (APIError, APIKeyError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise DataFetchError(ticker, "company_news", f"Unexpected error: {str(e)}")


def get_market_cap(
    ticker: str,
    end_date: str,
    api_key: str | None = None,
) -> float | None:
    """
    Fetch market cap from the API.

    Args:
        ticker: Stock ticker symbol
        end_date: End date in YYYY-MM-DD format
        api_key: Optional API key, will use environment variable if not provided

    Returns:
        Market cap value or None if not available

    Raises:
        APIKeyError: If API key is missing
        DataFetchError: If data cannot be fetched
        APIResponseError: If API returns an error
    """
    try:
        # Check if end_date is today
        if end_date == datetime.datetime.now().strftime("%Y-%m-%d"):
            # Validate API key
            financial_api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
            if not financial_api_key:
                raise APIKeyError("FINANCIAL_DATASETS_API_KEY")

            # Get the market cap from company facts API
            headers = {"X-API-KEY": financial_api_key}
            url = f"https://api.financialdatasets.ai/company/facts/?ticker={ticker}"

            response = _make_api_request(url, headers)
            if response.status_code != 200:
                raise APIResponseError(response.status_code, response.text, url)

            data = response.json()
            response_model = CompanyFactsResponse(**data)
            return response_model.company_facts.market_cap

        # For historical dates, use financial metrics
        financial_metrics = get_financial_metrics(ticker, end_date, api_key=api_key)
        if not financial_metrics:
            return None

        market_cap = financial_metrics[0].market_cap

        if not market_cap:
            return None

        return market_cap

    except (APIError, APIKeyError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise DataFetchError(ticker, "market_cap", f"Unexpected error: {str(e)}")


def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


# Update the get_price_data function to use the new functions
def get_price_data(ticker: str, start_date: str, end_date: str, api_key: str | None = None) -> pd.DataFrame:
    prices = get_prices(ticker, start_date, end_date, api_key=api_key)
    return prices_to_df(prices)
