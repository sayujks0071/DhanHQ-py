"""
Opening Range Breakout (ORB) options strategy implementation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from .base import BaseStrategy

logger = logging.getLogger(__name__)


@dataclass
class ORBParams:
    """ORB strategy parameters."""
    underlying: str
    option_type: str  # 'CALL' or 'PUT'
    expiry: datetime
    orb_period: int = 15  # Opening range period in minutes
    breakout_threshold: float = 0.5  # Breakout threshold in percentage
    stop_loss: float = 0.3  # Stop loss in percentage
    target_profit: float = 1.0  # Target profit in percentage
    max_risk: float = 1000.0
    min_volume: int = 1000000  # Minimum volume requirement
    min_oi: int = 1000  # Minimum open interest requirement


class ORBStrategy(BaseStrategy):
    """
    Opening Range Breakout (ORB) options strategy.
    
    This strategy involves:
    1. Identifying the opening range (first N minutes of trading)
    2. Waiting for a breakout above/below the range
    3. Entering a position in the direction of the breakout
    4. Managing the position with stop loss and target profit
    """
    
    def __init__(self, params: ORBParams):
        self.params = params
        self.positions = {}
        self.entry_time = None
        self.entry_price = None
        self.opening_range_high = None
        self.opening_range_low = None
        self.opening_range_established = False
        self.breakout_direction = None
        self.breakout_price = None
        
    def initialize(self, universe: List[str], config: Any):
        """Initialize the strategy."""
        self.universe = universe
        self.config = config
        
        logger.info(f"ORB strategy initialized for {self.params.underlying}")
        logger.info(f"ORB period: {self.params.orb_period} minutes")
        logger.info(f"Breakout threshold: {self.params.breakout_threshold}%")
    
    def generate_signals(
        self,
        timestamp: datetime,
        market_data: Dict[str, Any],
        current_positions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate trading signals."""
        signals = []
        
        # Check if we're in market hours
        if not self._is_market_hours(timestamp):
            return signals
        
        # Check if we already have a position
        if self._has_position(current_positions):
            # Manage existing position
            signals.extend(self._manage_position(timestamp, market_data, current_positions))
        else:
            # Look for new entry opportunities
            signals.extend(self._look_for_entry(timestamp, market_data))
        
        return signals
    
    def _has_position(self, current_positions: Dict[str, Any]) -> bool:
        """Check if we have an active ORB position."""
        # Look for ORB position
        for symbol, position in current_positions.items():
            if self._is_orb_position(symbol):
                return True
        return False
    
    def _is_orb_position(self, symbol: str) -> bool:
        """Check if a symbol is part of our ORB position."""
        # This would need to be implemented based on your symbol naming convention
        # For now, return False as placeholder
        return False
    
    def _look_for_entry(
        self, 
        timestamp: datetime, 
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Look for entry opportunities."""
        signals = []
        
        if self.params.underlying not in market_data:
            return signals
        
        current_price = market_data[self.params.underlying]['close']
        
        # Check if we're in the opening range period
        if self._is_opening_range_period(timestamp):
            # Establish opening range
            self._update_opening_range(current_price)
        else:
            # Check for breakout
            if self._check_breakout(current_price):
                signals.extend(self._create_orb_entry())
        
        return signals
    
    def _manage_position(
        self,
        timestamp: datetime,
        market_data: Dict[str, Any],
        current_positions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Manage existing position."""
        signals = []
        
        if self.params.underlying not in market_data:
            return signals
        
        current_price = market_data[self.params.underlying]['close']
        
        # Check for profit target
        if self._check_profit_target(current_price):
            signals.extend(self._close_position())
            return signals
        
        # Check for stop loss
        if self._check_stop_loss(current_price):
            signals.extend(self._close_position())
            return signals
        
        # Check for time-based exit
        if self._check_time_exit(timestamp):
            signals.extend(self._close_position())
            return signals
        
        return signals
    
    def _is_market_hours(self, timestamp: datetime) -> bool:
        """Check if we're in market hours."""
        hour = timestamp.hour
        minute = timestamp.minute
        return 9 <= hour < 15 or (hour == 9 and minute >= 15)  # 9:15 AM to 3 PM IST
    
    def _is_opening_range_period(self, timestamp: datetime) -> bool:
        """Check if we're in the opening range period."""
        market_open = timestamp.replace(hour=9, minute=15, second=0, microsecond=0)
        orb_end = market_open + timedelta(minutes=self.params.orb_period)
        
        return market_open <= timestamp <= orb_end
    
    def _update_opening_range(self, current_price: float):
        """Update the opening range."""
        if not self.opening_range_established:
            self.opening_range_high = current_price
            self.opening_range_low = current_price
            self.opening_range_established = True
        else:
            self.opening_range_high = max(self.opening_range_high, current_price)
            self.opening_range_low = min(self.opening_range_low, current_price)
    
    def _check_breakout(self, current_price: float) -> bool:
        """Check if there's a breakout."""
        if not self.opening_range_established:
            return False
        
        # Calculate breakout thresholds
        range_size = self.opening_range_high - self.opening_range_low
        breakout_threshold = range_size * self.params.breakout_threshold / 100
        
        # Check for upward breakout
        if current_price > self.opening_range_high + breakout_threshold:
            self.breakout_direction = 'UP'
            self.breakout_price = current_price
            return True
        
        # Check for downward breakout
        if current_price < self.opening_range_low - breakout_threshold:
            self.breakout_direction = 'DOWN'
            self.breakout_price = current_price
            return True
        
        return False
    
    def _create_orb_entry(self) -> List[Dict[str, Any]]:
        """Create ORB entry signals."""
        signals = []
        
        # Determine option type based on breakout direction
        if self.breakout_direction == 'UP':
            option_type = 'CALL'
        else:  # DOWN
            option_type = 'PUT'
        
        # Find suitable strike price
        strike_price = self._find_suitable_strike(option_type)
        
        if strike_price is None:
            return signals
        
        # Create option symbol
        option_symbol = f"{self.params.underlying}_{option_type}_{strike_price}_{self.params.expiry.strftime('%Y%m%d')}"
        
        # Create entry signal
        signals.append({
            'symbol': option_symbol,
            'side': 'BUY',
            'quantity': 1,
            'strategy': 'orb',
            'underlying': self.params.underlying,
            'option_type': option_type,
            'strike_price': strike_price,
            'expiry': self.params.expiry,
            'breakout_direction': self.breakout_direction,
            'breakout_price': self.breakout_price,
            'opening_range_high': self.opening_range_high,
            'opening_range_low': self.opening_range_low
        })
        
        return signals
    
    def _find_suitable_strike(self, option_type: str) -> Optional[float]:
        """Find suitable strike price for the option."""
        # This would need to be implemented based on your option chain data
        # For now, return placeholder
        if option_type == 'CALL':
            return self.opening_range_high * 1.02  # 2% above opening range high
        else:  # PUT
            return self.opening_range_low * 0.98  # 2% below opening range low
    
    def _check_profit_target(self, current_price: float) -> bool:
        """Check if profit target is reached."""
        if not self.breakout_price:
            return False
        
        # Calculate profit percentage
        if self.breakout_direction == 'UP':
            profit_pct = (current_price - self.breakout_price) / self.breakout_price * 100
        else:  # DOWN
            profit_pct = (self.breakout_price - current_price) / self.breakout_price * 100
        
        return profit_pct >= self.params.target_profit
    
    def _check_stop_loss(self, current_price: float) -> bool:
        """Check if stop loss is hit."""
        if not self.breakout_price:
            return False
        
        # Calculate loss percentage
        if self.breakout_direction == 'UP':
            loss_pct = (self.breakout_price - current_price) / self.breakout_price * 100
        else:  # DOWN
            loss_pct = (current_price - self.breakout_price) / self.breakout_price * 100
        
        return loss_pct >= self.params.stop_loss
    
    def _check_time_exit(self, timestamp: datetime) -> bool:
        """Check if we should exit based on time."""
        # Exit at market close
        return timestamp.hour >= 15
    
    def _close_position(self) -> List[Dict[str, Any]]:
        """Close the position."""
        signals = []
        
        # Create closing signal
        signals.append({
            'symbol': f"{self.params.underlying}_{self.params.option_type}_CLOSE",
            'side': 'SELL',
            'quantity': 1,
            'strategy': 'orb',
            'action': 'close'
        })
        
        return signals
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information."""
        return {
            'strategy_name': 'Opening Range Breakout',
            'underlying': self.params.underlying,
            'option_type': self.params.option_type,
            'expiry': self.params.expiry,
            'orb_period': self.params.orb_period,
            'breakout_threshold': self.params.breakout_threshold,
            'stop_loss': self.params.stop_loss,
            'target_profit': self.params.target_profit,
            'opening_range_high': self.opening_range_high,
            'opening_range_low': self.opening_range_low,
            'breakout_direction': self.breakout_direction,
            'breakout_price': self.breakout_price
        }
