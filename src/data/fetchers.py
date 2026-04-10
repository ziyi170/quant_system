"""
Data fetchers for acquiring real-time and historical market data.
Supports multiple sources: yfinance, Alpha Vantage, etc.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
import yfinance as yf
from requests import Session

logger = logging.getLogger(__name__)


class DataFetcher(ABC):
    """Abstract base class for data fetchers"""
    
    @abstractmethod
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch OHLCV data"""
        pass
    
    @abstractmethod
    def fetch_intraday(
        self,
        symbol: str,
        interval: str = "1min"
    ) -> pd.DataFrame:
        """Fetch intraday tick data"""
        pass


class YahooFinanceFetcher(DataFetcher):
    """
    Yahoo Finance data fetcher (free, no API key needed).
    
    Returns DataFrame with columns:
    - Open, High, Low, Close: OHLC prices
    - Volume: Trading volume
    - Adj Close: Adjusted closing price
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("/tmp/market_data")
        self.cache_dir.mkdir(exist_ok=True)
        self.session = Session()
    
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Interval (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            logger.info(f"Fetching {symbol} data from {start_date} to {end_date}")
            
            ticker = yf.Ticker(symbol, session=self.session)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=False,  # Keep unadjusted prices
                prepost=False       # Exclude pre/post market
            )
            
            # Rename columns for consistency
            df.columns = df.columns.str.lower()
            
            # Remove rows with missing data
            df = df.dropna()
            
            # Ensure index is datetime
            df.index = pd.to_datetime(df.index)
            
            # Remove timezone info if present
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            logger.info(f"✅ Fetched {len(df)} rows for {symbol}")
            
            return df
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch {symbol}: {e}")
            raise
    
    def fetch_intraday(
        self,
        symbol: str,
        interval: str = "1m",
        days: int = 5
    ) -> pd.DataFrame:
        """
        Fetch intraday tick data (limited to last ~30 days by Yahoo Finance).
        
        Args:
            symbol: Stock symbol
            interval: Interval (1m, 5m, 15m, 1h, 1d)
            days: Number of days to fetch
        
        Returns:
            DataFrame with intraday OHLCV
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.fetch(
            symbol,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            interval=interval
        )
    
    def fetch_batch(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols"""
        data = {}
        for symbol in symbols:
            try:
                data[symbol] = self.fetch(symbol, start_date, end_date)
            except Exception as e:
                logger.warning(f"Skipped {symbol}: {e}")
                continue
        return data


class AlphaVantageFetcher(DataFetcher):
    """
    Alpha Vantage data fetcher (requires free API key).
    
    More reliable for certain data types but has rate limits.
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    CALL_LIMIT = 5  # requests per minute
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = Session()
        self._last_call_time = None
    
    def _rate_limit(self):
        """Enforce rate limiting (5 requests/minute)"""
        if self._last_call_time:
            elapsed = (datetime.now() - self._last_call_time).total_seconds()
            if elapsed < 12:  # 60 / 5 = 12 seconds
                import time
                time.sleep(12 - elapsed)
        self._last_call_time = datetime.now()
    
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch data from Alpha Vantage.
        
        Supports: TIME_SERIES_DAILY, TIME_SERIES_WEEKLY, TIME_SERIES_MONTHLY
        """
        self._rate_limit()
        
        # Map interval to Alpha Vantage function
        if interval in ["1d", "daily"]:
            function = "TIME_SERIES_DAILY_ADJUSTED"
            key_name = "Time Series (Daily)"
        elif interval in ["1wk", "weekly"]:
            function = "TIME_SERIES_WEEKLY_ADJUSTED"
            key_name = "Time Series (Weekly)"
        else:
            raise ValueError(f"Unsupported interval: {interval}")
        
        try:
            params = {
                "function": function,
                "symbol": symbol,
                "apikey": self.api_key,
                "outputsize": "full"  # Get full history
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "Error Message" in data:
                raise ValueError(f"API Error: {data['Error Message']}")
            
            if key_name not in data:
                raise ValueError(f"No data for {symbol}")
            
            # Parse time series
            df = pd.DataFrame.from_dict(data[key_name], orient="index")
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Rename columns
            column_mapping = {
                "1. open": "open",
                "2. high": "high",
                "3. low": "low",
                "4. close": "close",
                "5. adjusted close": "adj close",
                "6. volume": "volume",
            }
            df = df.rename(columns=column_mapping)
            
            # Convert to numeric
            for col in ["open", "high", "low", "close", "adj close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Filter by date range
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            
            logger.info(f"✅ Fetched {len(df)} rows for {symbol}")
            return df
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch {symbol}: {e}")
            raise
    
    def fetch_intraday(
        self,
        symbol: str,
        interval: str = "5min"
    ) -> pd.DataFrame:
        """
        Fetch intraday data.
        
        Supported intervals: 1min, 5min, 15min, 30min, 60min
        """
        self._rate_limit()
        
        try:
            params = {
                "function": f"TIME_SERIES_INTRADAY",
                "symbol": symbol,
                "interval": interval,
                "apikey": self.api_key,
                "outputsize": "full"
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            key_name = f"Time Series ({interval})"
            if key_name not in data:
                raise ValueError(f"No intraday data for {symbol}")
            
            df = pd.DataFrame.from_dict(data[key_name], orient="index")
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # Rename columns
            column_mapping = {
                "1. open": "open",
                "2. high": "high",
                "3. low": "low",
                "4. close": "close",
                "5. volume": "volume",
            }
            df = df.rename(columns=column_mapping)
            
            # Convert to numeric
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            logger.info(f"✅ Fetched {len(df)} intraday rows for {symbol}")
            return df
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch intraday {symbol}: {e}")
            raise


class DataCache:
    """Simple file-based cache for market data"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_path(self, symbol: str, start_date: str, end_date: str) -> Path:
        """Generate cache file path"""
        return self.cache_dir / f"{symbol}_{start_date}_{end_date}.parquet"
    
    def get(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Retrieve cached data"""
        path = self._get_path(symbol, start_date, end_date)
        if path.exists():
            try:
                return pd.read_parquet(path)
            except Exception as e:
                logger.warning(f"Failed to read cache for {symbol}: {e}")
        return None
    
    def set(self, symbol: str, start_date: str, end_date: str, df: pd.DataFrame):
        """Cache data"""
        try:
            path = self._get_path(symbol, start_date, end_date)
            df.to_parquet(path)
            logger.debug(f"Cached {symbol} data")
        except Exception as e:
            logger.warning(f"Failed to cache {symbol}: {e}")


# Export functions
def get_data(
    symbol: str,
    start_date: str,
    end_date: str,
    source: str = "yfinance",
    use_cache: bool = True,
    cache_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Convenience function to fetch market data.
    
    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        source: Data source (yfinance or alpha_vantage)
        use_cache: Whether to use caching
        cache_dir: Cache directory
    
    Returns:
        DataFrame with OHLCV data
    """
    cache = DataCache(cache_dir or Path("/tmp/market_data")) if use_cache else None
    
    # Try cache first
    if cache:
        cached = cache.get(symbol, start_date, end_date)
        if cached is not None:
            logger.info(f"Using cached data for {symbol}")
            return cached
    
    # Fetch from source
    if source == "yfinance":
        fetcher = YahooFinanceFetcher()
    elif source == "alpha_vantage":
        from config.settings import settings
        fetcher = AlphaVantageFetcher(settings.ALPHA_VANTAGE_KEY)
    else:
        raise ValueError(f"Unknown source: {source}")
    
    df = fetcher.fetch(symbol, start_date, end_date)
    
    # Cache result
    if cache:
        cache.set(symbol, start_date, end_date, df)
    
    return df
