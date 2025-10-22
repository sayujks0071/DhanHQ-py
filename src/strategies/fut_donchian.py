"""
Donchian Breakout Strategy for Futures Trading.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from ..config import config
from ..utils.timezone import ISTTimezone


@dataclass
class DonchianSignal:
    """Donchian breakout signal."""
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    timestamp: datetime
    rationale: str


class DonchianBreakoutStrategy:
    """Donchian Breakout Strategy for futures trading."""
    
    def __init__(self, lookback_period: int = 20, atr_multiplier: float = 2.0, 
                 time_stop_days: int = 5):
        self.logger = logging.getLogger(__name__)
        self.lookback_period = lookback_period
        self.atr_multiplier = atr_multiplier
        self.time_stop_days = time_stop_days
        
        # Strategy state
        self.position = None
        self.entry_time = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        
    def generate_signal(self, price_data: pd.DataFrame, 
                       current_price: float) -> Optional[DonchianSignal]:
        """Generate trading signal based on Donchian breakout."""
        try:
            if len(price_data) < self.lookback_period:
                return None
            
            # Calculate Donchian channels
            high_channel = price_data['high'].rolling(window=self.lookback_period).max()
            low_channel = price_data['low'].rolling(window=self.lookback_period).min()
            
            # Get current values
            current_high_channel = high_channel.iloc[-1]
            current_low_channel = low_channel.iloc[-1]
            
            # Calculate ATR for stop loss
            atr = self._calculate_atr(price_data)
            
            # Generate signal
            signal = self._evaluate_breakout(
                current_price, current_high_channel, current_low_channel, atr
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Failed to generate Donchian signal: {e}")
            return None
    
    def _calculate_atr(self, price_data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range."""
        try:
            high = price_data['high']
            low = price_data['low']
            close = price_data['close']
            
            # Calculate True Range
            tr1 = high - low
            tr2 = np.abs(high - close.shift(1))
            tr3 = np.abs(low - close.shift(1))
            
            true_range = np.maximum(tr1, np.maximum(tr2, tr3))
            atr = true_range.rolling(window=period).mean().iloc[-1]
            
            return atr if not np.isnan(atr) else 0.0
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate ATR: {e}")
            return 0.0
    
    def _evaluate_breakout(self, current_price: float, high_channel: float, 
                          low_channel: float, atr: float) -> Optional[DonchianSignal]:
        """Evaluate breakout conditions."""
        try:
            # Check for breakout above high channel
            if current_price > high_channel:
                stop_loss = current_price - (atr * self.atr_multiplier)
                take_profit = current_price + (atr * self.atr_multiplier * 2)
                
                confidence = self._calculate_confidence(current_price, high_channel, atr)
                
                return DonchianSignal(
                    signal_type='BUY',
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=confidence,
                    timestamp=ISTTimezone.now(),
                    rationale=f"Breakout above Donchian high channel at {high_channel:.2f}"
                )
            
            # Check for breakout below low channel
            elif current_price < low_channel:
                stop_loss = current_price + (atr * self.atr_multiplier)
                take_profit = current_price - (atr * self.atr_multiplier * 2)
                
                confidence = self._calculate_confidence(current_price, low_channel, atr)
                
                return DonchianSignal(
                    signal_type='SELL',
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=confidence,
                    timestamp=ISTTimezone.now(),
                    rationale=f"Breakout below Donchian low channel at {low_channel:.2f}"
                )
            
            # No breakout
            return DonchianSignal(
                signal_type='HOLD',
                entry_price=current_price,
                stop_loss=0.0,
                take_profit=0.0,
                confidence=0.0,
                timestamp=ISTTimezone.now(),
                rationale="No breakout detected"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate breakout: {e}")
            return None
    
    def _calculate_confidence(self, current_price: float, channel_price: float, 
                            atr: float) -> float:
        """Calculate signal confidence."""
        try:
            # Base confidence on breakout strength
            breakout_strength = abs(current_price - channel_price) / atr
            
            # Normalize to 0-1 range
            confidence = min(1.0, breakout_strength / 2.0)
            
            return max(0.0, confidence)
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate confidence: {e}")
            return 0.0
    
    def update_position(self, current_price: float, timestamp: datetime) -> Dict:
        """Update position status and check exit conditions."""
        if not self.position:
            return {'action': 'HOLD', 'reason': 'No position'}
        
        try:
            # Check time stop
            if self.entry_time:
                time_elapsed = timestamp - self.entry_time
                if time_elapsed.days >= self.time_stop_days:
                    return self._close_position('TIME_STOP', current_price)
            
            # Check stop loss
            if self.position == 'LONG' and current_price <= self.stop_loss:
                return self._close_position('STOP_LOSS', current_price)
            elif self.position == 'SHORT' and current_price >= self.stop_loss:
                return self._close_position('STOP_LOSS', current_price)
            
            # Check take profit
            if self.position == 'LONG' and current_price >= self.take_profit:
                return self._close_position('TAKE_PROFIT', current_price)
            elif self.position == 'SHORT' and current_price <= self.take_profit:
                return self._close_position('TAKE_PROFIT', current_price)
            
            return {'action': 'HOLD', 'reason': 'Position maintained'}
            
        except Exception as e:
            self.logger.error(f"Failed to update position: {e}")
            return {'action': 'HOLD', 'reason': 'Error updating position'}
    
    def _close_position(self, reason: str, current_price: float) -> Dict:
        """Close current position."""
        try:
            if not self.position:
                return {'action': 'HOLD', 'reason': 'No position to close'}
            
            # Calculate P&L
            if self.position == 'LONG':
                pnl = current_price - self.entry_price
            else:  # SHORT
                pnl = self.entry_price - current_price
            
            # Update performance metrics
            self.total_trades += 1
            if pnl > 0:
                self.winning_trades += 1
            self.total_pnl += pnl
            
            # Reset position
            self.position = None
            self.entry_time = None
            self.entry_price = None
            self.stop_loss = None
            self.take_profit = None
            
            return {
                'action': 'CLOSE',
                'reason': reason,
                'pnl': pnl,
                'exit_price': current_price
            }
            
        except Exception as e:
            self.logger.error(f"Failed to close position: {e}")
            return {'action': 'HOLD', 'reason': 'Error closing position'}
    
    def enter_position(self, signal: DonchianSignal) -> Dict:
        """Enter position based on signal."""
        try:
            if signal.signal_type == 'HOLD':
                return {'action': 'HOLD', 'reason': 'No signal'}
            
            # Set position
            self.position = 'LONG' if signal.signal_type == 'BUY' else 'SHORT'
            self.entry_time = signal.timestamp
            self.entry_price = signal.entry_price
            self.stop_loss = signal.stop_loss
            self.take_profit = signal.take_profit
            
            return {
                'action': 'ENTER',
                'position': self.position,
                'entry_price': self.entry_price,
                'stop_loss': self.stop_loss,
                'take_profit': self.take_profit,
                'confidence': signal.confidence
            }
            
        except Exception as e:
            self.logger.error(f"Failed to enter position: {e}")
            return {'action': 'HOLD', 'reason': 'Error entering position'}
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get strategy performance metrics."""
        try:
            if self.total_trades == 0:
                return {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_pnl': 0.0,
                    'profit_factor': 0.0
                }
            
            win_rate = self.winning_trades / self.total_trades
            avg_pnl = self.total_pnl / self.total_trades
            
            # Calculate profit factor (simplified)
            profit_factor = 1.0  # Would need to track wins/losses separately
            
            return {
                'total_trades': self.total_trades,
                'win_rate': win_rate,
                'total_pnl': self.total_pnl,
                'avg_pnl': avg_pnl,
                'profit_factor': profit_factor
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    def reset_strategy(self) -> None:
        """Reset strategy state."""
        self.position = None
        self.entry_time = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        
        self.logger.info("Strategy reset")
    
    def get_strategy_info(self) -> Dict:
        """Get strategy information."""
        return {
            'name': 'Donchian Breakout',
            'type': 'Futures',
            'lookback_period': self.lookback_period,
            'atr_multiplier': self.atr_multiplier,
            'time_stop_days': self.time_stop_days,
            'current_position': self.position,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit
        }
