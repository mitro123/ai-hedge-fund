"""OpenBB Platform integration for AI Hedge Fund."""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from datetime import datetime, timedelta
import logging

# Add OpenBB to Python path
openbb_path = Path(__file__).parent.parent.parent / "OpenBB" / "openbb_platform"
if openbb_path.exists():
    sys.path.insert(0, str(openbb_path))

try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError as e:
    logging.warning(f"OpenBB not available: {e}")
    OPENBB_AVAILABLE = False
    obb = None


class OpenBBDataProvider:
    """OpenBB data provider for AI Hedge Fund integration."""
    
    def __init__(self):
        """Initialize OpenBB data provider."""
        self.available = OPENBB_AVAILABLE
        if not self.available:
            logging.warning("OpenBB Platform not available. Some features will be disabled.")
    
    def is_available(self) -> bool:
        """Check if OpenBB is available."""
        return self.available
    
    def get_historical_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d",
        provider: str = "yfinance"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical price data using OpenBB.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'SPY')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval ('1m', '5m', '15m', '30m', '1h', '1d', '1W', '1M')
            provider: Data provider ('yfinance', 'alpha_vantage', 'fmp', etc.)
        
        Returns:
            DataFrame with OHLCV data or None if error
        """
        if not self.available:
            logging.error("OpenBB not available")
            return None
        
        try:
            if obb is not None:
                result = obb.equity.price.historical(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    provider=provider
                )
                return result.to_dataframe()
            return None
        except Exception as e:
            logging.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def get_company_info(
        self,
        symbol: str,
        provider: str = "yfinance"
    ) -> Optional[Dict[str, Any]]:
        """
        Get company information.
        
        Args:
            symbol: Stock symbol
            provider: Data provider
        
        Returns:
            Dictionary with company info or None if error
        """
        if not self.available:
            logging.error("OpenBB not available")
            return None
        
        try:
            # Try to get company profile/info
            if obb is not None and hasattr(obb.equity, 'profile'):
                result = obb.equity.profile(symbol=symbol, provider=provider)
                return result.to_dict() if hasattr(result, 'to_dict') else result
            else:
                logging.warning("Company profile endpoint not available")
                return None
        except Exception as e:
            logging.error(f"Error fetching company info for {symbol}: {e}")
            return None
    
    def get_financial_statements(
        self,
        symbol: str,
        statement_type: str = "income",
        period: str = "annual",
        limit: int = 5,
        provider: str = "fmp"
    ) -> Optional[pd.DataFrame]:
        """
        Get financial statements.
        
        Args:
            symbol: Stock symbol
            statement_type: Type of statement ('income', 'balance', 'cash')
            period: Period ('annual', 'quarter')
            limit: Number of periods to retrieve
            provider: Data provider
        
        Returns:
            DataFrame with financial data or None if error
        """
        if not self.available:
            logging.error("OpenBB not available")
            return None
        
        try:
            if obb is not None and hasattr(obb.equity, 'fundamental'):
                if statement_type == "income" and hasattr(obb.equity.fundamental, 'income'):
                    result = obb.equity.fundamental.income(
                        symbol=symbol,
                        period=period,
                        limit=limit,
                        provider=provider
                    )
                elif statement_type == "balance" and hasattr(obb.equity.fundamental, 'balance'):
                    result = obb.equity.fundamental.balance(
                        symbol=symbol,
                        period=period,
                        limit=limit,
                        provider=provider
                    )
                elif statement_type == "cash" and hasattr(obb.equity.fundamental, 'cash'):
                    result = obb.equity.fundamental.cash(
                        symbol=symbol,
                        period=period,
                        limit=limit,
                        provider=provider
                    )
                else:
                    logging.warning(f"Statement type {statement_type} not available")
                    return None
                
                return result.to_dataframe() if hasattr(result, 'to_dataframe') else None
            else:
                logging.warning("Fundamental data endpoints not available")
                return None
        except Exception as e:
            logging.error(f"Error fetching {statement_type} statement for {symbol}: {e}")
            return None
    
    def get_market_news(
        self,
        symbol: Optional[str] = None,
        limit: int = 10,
        provider: str = "benzinga"
    ) -> Optional[pd.DataFrame]:
        """
        Get market news.
        
        Args:
            symbol: Stock symbol (optional, for company-specific news)
            limit: Number of news items
            provider: News provider
        
        Returns:
            DataFrame with news data or None if error
        """
        if not self.available:
            logging.error("OpenBB not available")
            return None
        
        try:
            if obb is not None and hasattr(obb, 'news'):
                if symbol:
                    result = obb.news.company(
                        symbol=symbol,
                        limit=limit,
                        provider=provider
                    )
                else:
                    result = obb.news.world(
                        limit=limit,
                        provider=provider
                    )
                return result.to_dataframe() if hasattr(result, 'to_dataframe') else None
            else:
                logging.warning("News endpoints not available")
                return None
        except Exception as e:
            logging.error(f"Error fetching news: {e}")
            return None
    
    def get_economic_data(
        self,
        indicator: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        provider: str = "fred"
    ) -> Optional[pd.DataFrame]:
        """
        Get economic data.
        
        Args:
            indicator: Economic indicator (e.g., 'GDP', 'UNRATE', 'FEDFUNDS')
            start_date: Start date
            end_date: End date
            provider: Data provider
        
        Returns:
            DataFrame with economic data or None if error
        """
        if not self.available:
            logging.error("OpenBB not available")
            return None
        
        try:
            if obb is not None and hasattr(obb, 'economy'):
                result = obb.economy.fred_series(
                    symbol=indicator,
                    start_date=start_date,
                    end_date=end_date,
                    provider=provider
                )
                return result.to_dataframe() if hasattr(result, 'to_dataframe') else None
            else:
                logging.warning("Economy endpoints not available")
                return None
        except Exception as e:
            logging.error(f"Error fetching economic data for {indicator}: {e}")
            return None
    
    def get_options_data(
        self,
        symbol: str,
        expiration: Optional[str] = None,
        provider: str = "yfinance"
    ) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Get options data.
        
        Args:
            symbol: Stock symbol
            expiration: Expiration date (YYYY-MM-DD)
            provider: Data provider
        
        Returns:
            Dictionary with 'calls' and 'puts' DataFrames or None if error
        """
        if not self.available:
            logging.error("OpenBB not available")
            return None
        
        try:
            if obb is not None and hasattr(obb, 'derivatives') and hasattr(obb.derivatives, 'options'):
                result = obb.derivatives.options.chains(
                    symbol=symbol,
                    provider=provider
                )
                df = result.to_dataframe() if hasattr(result, 'to_dataframe') else None
                
                if df is not None and 'option_type' in df.columns:
                    calls = df[df['option_type'] == 'call']
                    puts = df[df['option_type'] == 'put']
                    return {'calls': calls, 'puts': puts}
                elif df is not None:
                    return {'calls': df, 'puts': df}
                else:
                    return None
            else:
                logging.warning("Options endpoints not available")
                return None
        except Exception as e:
            logging.error(f"Error fetching options data for {symbol}: {e}")
            return None
    
    def get_crypto_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d",
        provider: str = "yfinance"
    ) -> Optional[pd.DataFrame]:
        """
        Get cryptocurrency data.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            start_date: Start date
            end_date: End date
            interval: Data interval
            provider: Data provider
        
        Returns:
            DataFrame with crypto data or None if error
        """
        if not self.available:
            logging.error("OpenBB not available")
            return None
        
        try:
            if obb is not None and hasattr(obb, 'crypto'):
                result = obb.crypto.price.historical(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    provider=provider
                )
                return result.to_dataframe() if hasattr(result, 'to_dataframe') else None
            else:
                logging.warning("Crypto endpoints not available")
                return None
        except Exception as e:
            logging.error(f"Error fetching crypto data for {symbol}: {e}")
            return None
    
    def get_forex_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d",
        provider: str = "yfinance"
    ) -> Optional[pd.DataFrame]:
        """
        Get forex data.
        
        Args:
            symbol: Currency pair (e.g., 'EURUSD', 'GBPUSD')
            start_date: Start date
            end_date: End date
            interval: Data interval
            provider: Data provider
        
        Returns:
            DataFrame with forex data or None if error
        """
        if not self.available:
            logging.error("OpenBB not available")
            return None
        
        try:
            if obb is not None and hasattr(obb, 'currency'):
                result = obb.currency.price.historical(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    provider=provider
                )
                return result.to_dataframe() if hasattr(result, 'to_dataframe') else None
            else:
                logging.warning("Currency endpoints not available")
                return None
        except Exception as e:
            logging.error(f"Error fetching forex data for {symbol}: {e}")
            return None
    
    def get_commodities_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d",
        provider: str = "yfinance"
    ) -> Optional[pd.DataFrame]:
        """
        Get commodities data.
        
        Args:
            symbol: Commodity symbol (e.g., 'GC=F' for Gold, 'CL=F' for Oil, 'SI=F' for Silver)
            start_date: Start date
            end_date: End date
            interval: Data interval
            provider: Data provider
        
        Returns:
            DataFrame with commodities data or None if error
        """
        if not self.available:
            logging.error("OpenBB not available")
            return None
        
        try:
            # For commodities, we can use equity.price.historical with futures symbols
            if obb is not None:
                result = obb.equity.price.historical(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    provider=provider
                )
                return result.to_dataframe() if hasattr(result, 'to_dataframe') else None
            else:
                logging.warning("OpenBB not available for commodities")
                return None
        except Exception as e:
            logging.error(f"Error fetching commodities data for {symbol}: {e}")
            return None
    
    def get_futures_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d",
        provider: str = "yfinance"
    ) -> Optional[pd.DataFrame]:
        """
        Get futures data.
        
        Args:
            symbol: Futures symbol (e.g., 'ES=F' for S&P 500 futures)
            start_date: Start date
            end_date: End date
            interval: Data interval
            provider: Data provider
        
        Returns:
            DataFrame with futures data or None if error
        """
        if not self.available:
            logging.error("OpenBB not available")
            return None
        
        try:
            if obb is not None:
                result = obb.equity.price.historical(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    provider=provider
                )
                return result.to_dataframe() if hasattr(result, 'to_dataframe') else None
            else:
                logging.warning("OpenBB not available for futures")
                return None
        except Exception as e:
            logging.error(f"Error fetching futures data for {symbol}: {e}")
            return None


# Global instance
openbb_provider = OpenBBDataProvider()


def get_openbb_provider() -> OpenBBDataProvider:
    """Get the global OpenBB provider instance."""
    return openbb_provider


# Convenience functions for easy access
def get_stock_data(symbol: str, days: int = 30, provider: str = "yfinance") -> Optional[pd.DataFrame]:
    """Get recent stock data."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return openbb_provider.get_historical_prices(symbol, start_date, end_date, provider=provider)


def get_multiple_stocks(symbols: List[str], days: int = 30, provider: str = "yfinance") -> Dict[str, pd.DataFrame]:
    """Get data for multiple stocks."""
    results = {}
    for symbol in symbols:
        data = get_stock_data(symbol, days, provider)
        if data is not None:
            results[symbol] = data
    return results


def get_market_overview(provider: str = "yfinance") -> Dict[str, pd.DataFrame]:
    """Get overview of major market indices."""
    indices = ["SPY", "QQQ", "IWM", "DIA", "VTI"]
    return get_multiple_stocks(indices, days=5, provider=provider)


def get_forex_data_convenience(symbol: str, days: int = 30, provider: str = "yfinance") -> Optional[pd.DataFrame]:
    """Get recent forex data."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return openbb_provider.get_forex_data(symbol, start_date, end_date, provider=provider)


def get_commodities_data_convenience(symbol: str, days: int = 30, provider: str = "yfinance") -> Optional[pd.DataFrame]:
    """Get recent commodities data."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return openbb_provider.get_commodities_data(symbol, start_date, end_date, provider=provider)


def get_crypto_data_convenience(symbol: str, days: int = 30, provider: str = "yfinance") -> Optional[pd.DataFrame]:
    """Get recent crypto data."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return openbb_provider.get_crypto_data(symbol, start_date, end_date, provider=provider)


def get_multiple_forex(symbols: List[str], days: int = 30, provider: str = "yfinance") -> Dict[str, pd.DataFrame]:
    """Get data for multiple forex pairs."""
    results = {}
    for symbol in symbols:
        data = get_forex_data_convenience(symbol, days, provider)
        if data is not None:
            results[symbol] = data
    return results


def get_multiple_commodities(symbols: List[str], days: int = 30, provider: str = "yfinance") -> Dict[str, pd.DataFrame]:
    """Get data for multiple commodities."""
    results = {}
    for symbol in symbols:
        data = get_commodities_data_convenience(symbol, days, provider)
        if data is not None:
            results[symbol] = data
    return results


def get_commodities_overview(provider: str = "yfinance") -> Dict[str, pd.DataFrame]:
    """Get overview of major commodities."""
    commodities = [
        "GC=F",  # Gold
        "SI=F",  # Silver
        "CL=F",  # Crude Oil
        "NG=F",  # Natural Gas
        "HG=F",  # Copper
        "ZC=F",  # Corn
        "ZS=F",  # Soybeans
        "ZW=F"   # Wheat
    ]
    return get_multiple_commodities(commodities, days=5, provider=provider)


def get_forex_overview(provider: str = "yfinance") -> Dict[str, pd.DataFrame]:
    """Get overview of major forex pairs."""
    forex_pairs = [
        "EURUSD=X",  # EUR/USD
        "GBPUSD=X",  # GBP/USD
        "USDJPY=X",  # USD/JPY
        "USDCHF=X",  # USD/CHF
        "AUDUSD=X",  # AUD/USD
        "USDCAD=X",  # USD/CAD
        "NZDUSD=X"   # NZD/USD
    ]
    return get_multiple_forex(forex_pairs, days=5, provider=provider)
