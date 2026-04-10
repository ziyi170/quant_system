"""
Technical indicators for signal generation.
Implements: RSI, MACD, Bollinger Bands, SMA, EMA, etc.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class Indicator(ABC):
    """Abstract base class for all indicators"""
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicator values"""
        pass
    
    @abstractmethod
    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """Generate buy/sell signals based on indicator"""
        pass


class RSI(Indicator):
    """
    Relative Strength Index
    
    Momentum oscillator (0-100):
    - < 30: Oversold (potential buy)
    - > 70: Overbought (potential sell)
    """
    
    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI"""
        prices = df['close'].astype(float)
        
        # Calculate deltas
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        # Calculate RS and RSI
        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        df['rsi'] = rsi
        return df
    
    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals:
        1: Buy (oversold)
        -1: Sell (overbought)
        0: Neutral
        """
        df = self.calculate(df)
        signal = pd.Series(0, index=df.index)
        signal[df['rsi'] < self.oversold] = 1   # Buy
        signal[df['rsi'] > self.overbought] = -1  # Sell
        return signal


class MACD(Indicator):
    """
    Moving Average Convergence Divergence
    
    Trend-following momentum indicator
    - MACD line: 12-day EMA - 26-day EMA
    - Signal line: 9-day EMA of MACD
    - Histogram: MACD - Signal
    """
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD"""
        prices = df['close'].astype(float)
        
        # Calculate EMAs
        ema_fast = prices.ewm(span=self.fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow, adjust=False).mean()
        
        # MACD line
        df['macd'] = ema_fast - ema_slow
        
        # Signal line
        df['macd_signal'] = df['macd'].ewm(span=self.signal, adjust=False).mean()
        
        # Histogram
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on MACD crossovers:
        1: Buy (MACD crosses above signal)
        -1: Sell (MACD crosses below signal)
        0: Neutral
        """
        df = self.calculate(df)
        
        signal = pd.Series(0, index=df.index)
        
        # Detect crossovers
        macd_above_signal = df['macd'] > df['macd_signal']
        prev_macd_above = macd_above_signal.shift(1)
        
        # Bullish crossover (MACD crosses above signal)
        signal[macd_above_signal & ~prev_macd_above] = 1
        
        # Bearish crossover (MACD crosses below signal)
        signal[~macd_above_signal & prev_macd_above] = -1
        
        return signal


class BollingerBands(Indicator):
    """
    Bollinger Bands
    
    Volatility indicator with upper/lower bands ±2 std from SMA
    """
    
    def __init__(self, period: int = 20, num_std: float = 2.0):
        self.period = period
        self.num_std = num_std
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        prices = df['close'].astype(float)
        
        # Middle band (SMA)
        df['bb_middle'] = prices.rolling(window=self.period).mean()
        
        # Standard deviation
        std = prices.rolling(window=self.period).std()
        
        # Upper and lower bands
        df['bb_upper'] = df['bb_middle'] + (std * self.num_std)
        df['bb_lower'] = df['bb_middle'] - (std * self.num_std)
        
        # Percentage B: where price is relative to bands
        df['bb_pct'] = (prices - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
        
        return df
    
    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals:
        1: Buy (price touches lower band = oversold)
        -1: Sell (price touches upper band = overbought)
        0: Neutral
        """
        df = self.calculate(df)
        prices = df['close'].astype(float)
        
        signal = pd.Series(0, index=df.index)
        
        # Near lower band (oversold)
        signal[prices <= df['bb_lower'] * 1.01] = 1
        
        # Near upper band (overbought)
        signal[prices >= df['bb_upper'] * 0.99] = -1
        
        return signal


class SimpleMovingAverage(Indicator):
    """Simple Moving Average"""
    
    def __init__(self, period: int = 20):
        self.period = period
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate SMA"""
        df[f'sma_{self.period}'] = df['close'].rolling(window=self.period).mean()
        return df
    
    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on price vs SMA:
        1: Buy (price > SMA)
        -1: Sell (price < SMA)
        0: Neutral
        """
        df = self.calculate(df)
        prices = df['close'].astype(float)
        sma = df[f'sma_{self.period}']
        
        signal = pd.Series(0, index=df.index)
        signal[prices > sma * 1.01] = 1   # Buy if above
        signal[prices < sma * 0.99] = -1  # Sell if below
        
        return signal


class ExponentialMovingAverage(Indicator):
    """Exponential Moving Average"""
    
    def __init__(self, period: int = 12):
        self.period = period
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA"""
        df[f'ema_{self.period}'] = df['close'].ewm(span=self.period, adjust=False).mean()
        return df
    
    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """Generate signals based on price vs EMA"""
        df = self.calculate(df)
        prices = df['close'].astype(float)
        ema = df[f'ema_{self.period}']
        
        signal = pd.Series(0, index=df.index)
        signal[prices > ema * 1.01] = 1
        signal[prices < ema * 0.99] = -1
        
        return signal


class ADX(Indicator):
    """
    Average Directional Index
    
    Measures trend strength (not direction)
    - ADX > 25: Strong trend
    - ADX < 20: Weak trend
    """
    
    def __init__(self, period: int = 14):
        self.period = period
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ADX"""
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        close = df['close'].astype(float)
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.period).mean()
        
        # Directional Movement
        up_move = high.diff()
        down_move = -low.diff()
        
        pos_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
        neg_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
        
        pos_di = 100 * (pos_dm.rolling(window=self.period).mean() / atr)
        neg_di = 100 * (neg_dm.rolling(window=self.period).mean() / atr)
        
        # ADX
        dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di + 1e-10)
        df['adx'] = dx.rolling(window=self.period).mean()
        df['+DI'] = pos_di
        df['-DI'] = neg_di
        
        return df
    
    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on trend strength and direction
        """
        df = self.calculate(df)
        
        signal = pd.Series(0, index=df.index)
        
        # Strong uptrend
        signal[(df['adx'] > 25) & (df['+DI'] > df['-DI'])] = 1
        
        # Strong downtrend
        signal[(df['adx'] > 25) & (df['-DI'] > df['+DI'])] = -1
        
        return signal


class StochasticOscillator(Indicator):
    """
    Stochastic Oscillator
    
    Compares closing price to price range
    """
    
    def __init__(self, period: int = 14, smooth: int = 3):
        self.period = period
        self.smooth = smooth
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Stochastic Oscillator"""
        low_min = df['low'].rolling(window=self.period).min()
        high_max = df['high'].rolling(window=self.period).max()
        
        k = 100 * ((df['close'] - low_min) / (high_max - low_min + 1e-10))
        df['stoch_k'] = k.rolling(window=self.smooth).mean()
        df['stoch_d'] = df['stoch_k'].rolling(window=self.smooth).mean()
        
        return df
    
    def get_signal(self, df: pd.DataFrame) -> pd.Series:
        """Generate signals"""
        df = self.calculate(df)
        
        signal = pd.Series(0, index=df.index)
        signal[df['stoch_k'] < 20] = 1      # Oversold
        signal[df['stoch_k'] > 80] = -1     # Overbought
        
        return signal


# Composite indicator combining multiple indicators
class CompositeIndicator:
    """Combine multiple indicators for robust signals"""
    
    def __init__(self, indicators: list, weights: Optional[dict] = None):
        """
        Args:
            indicators: List of Indicator instances
            weights: Dictionary of indicator names to weights (default: equal)
        """
        self.indicators = indicators
        self.weights = weights or {i.__class__.__name__: 1.0/len(indicators) for i in indicators}
    
    def get_composite_signal(self, df: pd.DataFrame) -> pd.Series:
        """Combine signals from all indicators"""
        combined_signal = pd.Series(0.0, index=df.index)
        
        for indicator in self.indicators:
            signal = indicator.get_signal(df)
            weight = self.weights.get(indicator.__class__.__name__, 1.0)
            combined_signal += signal * weight
        
        # Convert to {-1, 0, 1}
        result = pd.Series(0, index=df.index)
        result[combined_signal > 0.3] = 1
        result[combined_signal < -0.3] = -1
        
        return result


# Convenience function
def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all standard indicators"""
    indicators = [
        RSI(),
        MACD(),
        BollingerBands(),
        SimpleMovingAverage(20),
        SimpleMovingAverage(50),
        ExponentialMovingAverage(12),
        ADX(),
        StochasticOscillator()
    ]
    
    for indicator in indicators:
        df = indicator.calculate(df)
    
    return df
