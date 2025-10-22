"""
Historical candle data management for the Liquid F&O Trading System.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from ..config import config
from ..utils.timezone import ISTTimezone


class TimeFrame(Enum):
    """Timeframe enumeration."""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    DAILY = "1d"


@dataclass
class Candle:
    """Candle data structure."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    open_interest: Optional[int] = None
    vwap: Optional[float] = None


class CandleDataManager:
    """Historical candle data manager."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache: Dict[str, Dict[str, pd.DataFrame]] = {}
        self.cache_ttl = 300  # 5 minutes
        
    def get_candles(self, security_id: str, timeframe: TimeFrame, 
                   start_date: date, end_date: date, 
                   broker_adapter) -> pd.DataFrame:
        """Get historical candles for a security."""
        try:
            cache_key = f"{security_id}_{timeframe.value}_{start_date}_{end_date}"
            
            # Check cache first
            if self._is_cached(cache_key):
                self.logger.debug(f"Returning cached data for {security_id}")
                return self.cache[security_id][cache_key]
            
            # Fetch from broker
            self.logger.info(f"Fetching candles for {security_id} {timeframe.value}")
            candles_data = broker_adapter.get_historical_data(
                security_id, timeframe.value, start_date, end_date
            )
            
            # Convert to DataFrame
            df = self._process_candles_data(candles_data, timeframe)
            
            # Cache the data
            self._cache_data(security_id, cache_key, df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to get candles for {security_id}: {e}")
            raise
    
    def _process_candles_data(self, data: List[Dict], timeframe: TimeFrame) -> pd.DataFrame:
        """Process raw candles data into DataFrame."""
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Ensure proper column types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Add open interest if available
        if 'open_interest' in df.columns:
            df['open_interest'] = pd.to_numeric(df['open_interest'], errors='coerce')
        
        # Add VWAP if not present
        if 'vwap' not in df.columns:
            df['vwap'] = self._calculate_vwap(df)
        
        # Sort by timestamp
        df.sort_index(inplace=True)
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='last')]
        
        return df
    
    def _calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price."""
        if 'volume' not in df.columns:
            return pd.Series(index=df.index, dtype=float)
        
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        
        return vwap
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if data is cached and not expired."""
        for security_id, cache in self.cache.items():
            if cache_key in cache:
                # Check TTL (simplified - in production, use proper TTL)
                return True
        return False
    
    def _cache_data(self, security_id: str, cache_key: str, df: pd.DataFrame) -> None:
        """Cache DataFrame data."""
        if security_id not in self.cache:
            self.cache[security_id] = {}
        
        self.cache[security_id][cache_key] = df.copy()
    
    def get_latest_candle(self, security_id: str, timeframe: TimeFrame, 
                         broker_adapter) -> Optional[Candle]:
        """Get latest candle for a security."""
        try:
            end_date = ISTTimezone.now().date()
            start_date = end_date - timedelta(days=1)
            
            df = self.get_candles(security_id, timeframe, start_date, end_date, broker_adapter)
            
            if df.empty:
                return None
            
            latest = df.iloc[-1]
            
            return Candle(
                timestamp=df.index[-1],
                open=float(latest['open']),
                high=float(latest['high']),
                low=float(latest['low']),
                close=float(latest['close']),
                volume=int(latest['volume']),
                open_interest=int(latest.get('open_interest', 0)) if pd.notna(latest.get('open_interest')) else None,
                vwap=float(latest.get('vwap', 0)) if pd.notna(latest.get('vwap')) else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get latest candle for {security_id}: {e}")
            return None
    
    def get_intraday_candles(self, security_id: str, timeframe: TimeFrame, 
                           broker_adapter) -> pd.DataFrame:
        """Get intraday candles for today."""
        try:
            today = ISTTimezone.now().date()
            return self.get_candles(security_id, timeframe, today, today, broker_adapter)
            
        except Exception as e:
            self.logger.error(f"Failed to get intraday candles for {security_id}: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for candles."""
        if df.empty:
            return df
        
        # Simple Moving Averages
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_10'] = df['close'].rolling(window=10).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        df['ema_5'] = df['close'].ewm(span=5).mean()
        df['ema_10'] = df['close'].ewm(span=10).mean()
        df['ema_20'] = df['close'].ewm(span=20).mean()
        df['ema_50'] = df['close'].ewm(span=50).mean()
        
        # Bollinger Bands
        bb_period = 20
        bb_std = 2
        df['bb_middle'] = df['close'].rolling(window=bb_period).mean()
        bb_std_dev = df['close'].rolling(window=bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std_dev * bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std_dev * bb_std)
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'])
        
        # ATR
        df['atr'] = self._calculate_atr(df)
        
        # MACD
        macd_data = self._calculate_macd(df['close'])
        df['macd'] = macd_data['macd']
        df['macd_signal'] = macd_data['signal']
        df['macd_histogram'] = macd_data['histogram']
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def _calculate_macd(self, prices: pd.Series, 
                       fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_histogram = macd - macd_signal
        
        return {
            'macd': macd,
            'signal': macd_signal,
            'histogram': macd_histogram
        }
    
    def get_volatility(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate historical volatility."""
        returns = df['close'].pct_change()
        volatility = returns.rolling(window=period).std() * np.sqrt(252)  # Annualized
        
        return volatility
    
    def get_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Tuple[pd.Series, pd.Series]:
        """Calculate support and resistance levels."""
        # Simple support/resistance based on local minima/maxima
        highs = df['high'].rolling(window=window, center=True).max()
        lows = df['low'].rolling(window=window, center=True).min()
        
        resistance = highs.where(df['high'] == highs)
        support = lows.where(df['low'] == lows)
        
        return support, resistance
    
    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, bool]:
        """Detect common candlestick patterns."""
        if df.empty or len(df) < 3:
            return {}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]
        
        patterns = {}
        
        # Doji
        body_size = abs(latest['close'] - latest['open'])
        total_range = latest['high'] - latest['low']
        patterns['doji'] = body_size < (total_range * 0.1)
        
        # Hammer
        lower_shadow = latest['open'] - latest['low']
        upper_shadow = latest['high'] - latest['close']
        body_size = abs(latest['close'] - latest['open'])
        patterns['hammer'] = (lower_shadow > 2 * body_size and 
                              upper_shadow < body_size and 
                              latest['close'] > latest['open'])
        
        # Shooting Star
        patterns['shooting_star'] = (upper_shadow > 2 * body_size and 
                                   lower_shadow < body_size and 
                                   latest['close'] < latest['open'])
        
        # Engulfing
        patterns['bullish_engulfing'] = (prev['close'] < prev['open'] and 
                                        latest['close'] > latest['open'] and 
                                        latest['open'] < prev['close'] and 
                                        latest['close'] > prev['open'])
        
        patterns['bearish_engulfing'] = (prev['close'] > prev['open'] and 
                                        latest['close'] < latest['open'] and 
                                        latest['open'] > prev['close'] and 
                                        latest['close'] < prev['open'])
        
        return patterns
    
    def get_market_regime(self, df: pd.DataFrame) -> str:
        """Determine market regime based on volatility and trend."""
        if df.empty or len(df) < 50:
            return "unknown"
        
        # Calculate volatility
        returns = df['close'].pct_change()
        volatility = returns.rolling(window=20).std().iloc[-1]
        
        # Calculate trend strength
        sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
        sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        trend_strength = abs(current_price - sma_20) / sma_20
        
        # Classify regime
        if volatility > 0.03:  # High volatility
            if trend_strength > 0.02:  # Strong trend
                return "trending_high_vol"
            else:
                return "ranging_high_vol"
        else:  # Low volatility
            if trend_strength > 0.02:  # Strong trend
                return "trending_low_vol"
            else:
                return "ranging_low_vol"
    
    def clear_cache(self, security_id: Optional[str] = None) -> None:
        """Clear cache for a specific security or all securities."""
        if security_id:
            if security_id in self.cache:
                del self.cache[security_id]
        else:
            self.cache.clear()
        
        self.logger.info(f"Cleared cache for {security_id or 'all securities'}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        total_cached = sum(len(cache) for cache in self.cache.values())
        securities_cached = len(self.cache)
        
        return {
            'securities_cached': securities_cached,
            'total_datasets': total_cached,
            'cache_size_mb': 0  # Would need to calculate actual size
        }
