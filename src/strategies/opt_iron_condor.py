"""
Iron Condor options strategy implementation.
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
class IronCondorParams:
    """Iron Condor strategy parameters."""
    underlying: str
    expiry: datetime
    short_strike_1: float  # Lower short strike
    short_strike_2: float  # Upper short strike
    long_strike_1: float   # Lower long strike
    long_strike_2: float    # Upper long strike
    max_risk: float
    target_profit: float
    stop_loss: float
    days_to_expiry: int
    iv_rank_threshold: float = 0.5
    min_pop: float = 0.3  # Minimum probability of profit
    max_pop: float = 0.7  # Maximum probability of profit


class IronCondorStrategy(BaseStrategy):
    """
    Iron Condor options strategy.
    
    This strategy involves:
    1. Selling a put spread (lower strikes)
    2. Selling a call spread (upper strikes)
    3. Both spreads are out-of-the-money
    4. Profit when underlying stays between the short strikes
    """
    
    def __init__(self, params: IronCondorParams):
        self.params = params
        self.positions = {}
        self.entry_time = None
        self.entry_price = None
        self.max_profit = None
        self.max_loss = None
        
    def initialize(self, universe: List[str], config: Any):
        """Initialize the strategy."""
        self.universe = universe
        self.config = config
        
        # Calculate max profit and loss
        self.max_profit = self._calculate_max_profit()
        self.max_loss = self._calculate_max_loss()
        
        logger.info(f"Iron Condor initialized for {self.params.underlying}")
        logger.info(f"Max profit: {self.max_profit}, Max loss: {self.max_loss}")
    
    def generate_signals(
        self,
        timestamp: datetime,
        market_data: Dict[str, Any],
        current_positions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate trading signals."""
        signals = []
        
        # Check if we already have a position
        if self._has_position(current_positions):
            # Manage existing position
            signals.extend(self._manage_position(timestamp, market_data, current_positions))
        else:
            # Look for new entry opportunities
            signals.extend(self._look_for_entry(timestamp, market_data))
        
        return signals
    
    def _has_position(self, current_positions: Dict[str, Any]) -> bool:
        """Check if we have an active Iron Condor position."""
        # Look for Iron Condor legs in positions
        iron_condor_legs = 0
        for symbol, position in current_positions.items():
            if self._is_iron_condor_leg(symbol):
                iron_condor_legs += 1
        
        return iron_condor_legs >= 4  # Iron Condor has 4 legs
    
    def _is_iron_condor_leg(self, symbol: str) -> bool:
        """Check if a symbol is part of our Iron Condor."""
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
        
        # Check if we're in market hours
        if not self._is_market_hours(timestamp):
            return signals
        
        # Check if we have enough time to expiry
        if not self._check_time_to_expiry():
            return signals
        
        # Check IV rank
        if not self._check_iv_rank(market_data):
            return signals
        
        # Check probability of profit
        if not self._check_pop(market_data):
            return signals
        
        # Check if underlying is in suitable range
        if not self._check_underlying_range(market_data):
            return signals
        
        # Create Iron Condor entry signals
        signals.extend(self._create_iron_condor_entry())
        
        return signals
    
    def _manage_position(
        self,
        timestamp: datetime,
        market_data: Dict[str, Any],
        current_positions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Manage existing position."""
        signals = []
        
        # Check for profit target
        if self._check_profit_target(current_positions):
            signals.extend(self._close_position())
            return signals
        
        # Check for stop loss
        if self._check_stop_loss(current_positions):
            signals.extend(self._close_position())
            return signals
        
        # Check for time-based exit
        if self._check_time_exit():
            signals.extend(self._close_position())
            return signals
        
        # Check for roll opportunity
        if self._check_roll_opportunity(market_data):
            signals.extend(self._roll_position())
        
        return signals
    
    def _check_market_hours(self, timestamp: datetime) -> bool:
        """Check if we're in market hours."""
        hour = timestamp.hour
        return 9 <= hour < 15  # 9 AM to 3 PM IST
    
    def _check_time_to_expiry(self) -> bool:
        """Check if we have enough time to expiry."""
        days_to_expiry = (self.params.expiry - datetime.now()).days
        return days_to_expiry >= self.params.days_to_expiry
    
    def _check_iv_rank(self, market_data: Dict[str, Any]) -> bool:
        """Check if IV rank is suitable."""
        # This would need to be implemented based on your IV calculation
        # For now, return True as placeholder
        return True
    
    def _check_pop(self, market_data: Dict[str, Any]) -> bool:
        """Check if probability of profit is suitable."""
        # This would need to be implemented based on your POP calculation
        # For now, return True as placeholder
        return True
    
    def _check_underlying_range(self, market_data: Dict[str, Any]) -> bool:
        """Check if underlying is in suitable range."""
        if self.params.underlying not in market_data:
            return False
        
        current_price = market_data[self.params.underlying]['close']
        
        # Check if underlying is between the short strikes
        return (self.params.short_strike_1 < current_price < self.params.short_strike_2)
    
    def _create_iron_condor_entry(self) -> List[Dict[str, Any]]:
        """Create Iron Condor entry signals."""
        signals = []
        
        # Create 4 legs for Iron Condor
        legs = [
            # Long put (lower long strike)
            {
                'symbol': f"{self.params.underlying}_PUT_{self.params.long_strike_1}_{self.params.expiry.strftime('%Y%m%d')}",
                'side': 'BUY',
                'quantity': 1,
                'leg_type': 'long_put'
            },
            # Short put (lower short strike)
            {
                'symbol': f"{self.params.underlying}_PUT_{self.params.short_strike_1}_{self.params.expiry.strftime('%Y%m%d')}",
                'side': 'SELL',
                'quantity': 1,
                'leg_type': 'short_put'
            },
            # Short call (upper short strike)
            {
                'symbol': f"{self.params.underlying}_CALL_{self.params.short_strike_2}_{self.params.expiry.strftime('%Y%m%d')}",
                'side': 'SELL',
                'quantity': 1,
                'leg_type': 'short_call'
            },
            # Long call (upper long strike)
            {
                'symbol': f"{self.params.underlying}_CALL_{self.params.long_strike_2}_{self.params.expiry.strftime('%Y%m%d')}",
                'side': 'BUY',
                'quantity': 1,
                'leg_type': 'long_call'
            }
        ]
        
        for leg in legs:
            signals.append({
                'symbol': leg['symbol'],
                'side': leg['side'],
                'quantity': leg['quantity'],
                'strategy': 'iron_condor',
                'leg_type': leg['leg_type'],
                'underlying': self.params.underlying,
                'expiry': self.params.expiry,
                'max_risk': self.max_loss,
                'target_profit': self.max_profit
            })
        
        return signals
    
    def _check_profit_target(self, current_positions: Dict[str, Any]) -> bool:
        """Check if profit target is reached."""
        # Calculate current P&L
        current_pnl = self._calculate_current_pnl(current_positions)
        
        # Check if we've reached profit target
        profit_target = self.max_profit * self.params.target_profit
        return current_pnl >= profit_target
    
    def _check_stop_loss(self, current_positions: Dict[str, Any]) -> bool:
        """Check if stop loss is hit."""
        # Calculate current P&L
        current_pnl = self._calculate_current_pnl(current_positions)
        
        # Check if we've hit stop loss
        stop_loss_amount = self.max_loss * self.params.stop_loss
        return current_pnl <= -stop_loss_amount
    
    def _check_time_exit(self) -> bool:
        """Check if we should exit based on time."""
        days_to_expiry = (self.params.expiry - datetime.now()).days
        return days_to_expiry <= 7  # Exit 7 days before expiry
    
    def _check_roll_opportunity(self, market_data: Dict[str, Any]) -> bool:
        """Check if we should roll the position."""
        # This would implement roll logic based on market conditions
        # For now, return False as placeholder
        return False
    
    def _close_position(self) -> List[Dict[str, Any]]:
        """Close the entire position."""
        signals = []
        
        # Create closing signals for all legs
        legs = ['long_put', 'short_put', 'short_call', 'long_call']
        
        for leg_type in legs:
            signals.append({
                'symbol': f"{self.params.underlying}_{leg_type.upper()}_{self.params.expiry.strftime('%Y%m%d')}",
                'side': 'CLOSE',  # This would need to be handled by the order manager
                'quantity': 1,
                'strategy': 'iron_condor',
                'action': 'close',
                'leg_type': leg_type
            })
        
        return signals
    
    def _roll_position(self) -> List[Dict[str, Any]]:
        """Roll the position to a new expiry."""
        signals = []
        
        # This would implement roll logic
        # For now, return empty list as placeholder
        return signals
    
    def _calculate_current_pnl(self, current_positions: Dict[str, Any]) -> float:
        """Calculate current P&L of the position."""
        total_pnl = 0.0
        
        for symbol, position in current_positions.items():
            if self._is_iron_condor_leg(symbol):
                total_pnl += position.unrealized_pnl
        
        return total_pnl
    
    def _calculate_max_profit(self) -> float:
        """Calculate maximum profit of the Iron Condor."""
        # Max profit = net credit received
        # This would be calculated based on option prices
        # For now, return placeholder
        return 100.0
    
    def _calculate_max_loss(self) -> float:
        """Calculate maximum loss of the Iron Condor."""
        # Max loss = difference between strikes - net credit
        # This would be calculated based on option prices
        # For now, return placeholder
        return 200.0
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information."""
        return {
            'strategy_name': 'Iron Condor',
            'underlying': self.params.underlying,
            'expiry': self.params.expiry,
            'short_strikes': [self.params.short_strike_1, self.params.short_strike_2],
            'long_strikes': [self.params.long_strike_1, self.params.long_strike_2],
            'max_profit': self.max_profit,
            'max_loss': self.max_loss,
            'target_profit': self.params.target_profit,
            'stop_loss': self.params.stop_loss,
            'days_to_expiry': self.params.days_to_expiry
        }
