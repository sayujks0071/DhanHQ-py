"""
Debit Spread options strategy implementation.
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
class DebitSpreadParams:
    """Debit Spread strategy parameters."""
    underlying: str
    expiry: datetime
    long_strike: float
    short_strike: float
    option_type: str  # 'CALL' or 'PUT'
    max_risk: float
    target_profit: float
    stop_loss: float
    days_to_expiry: int
    min_pop: float = 0.3
    max_pop: float = 0.7
    iv_rank_threshold: float = 0.5


class DebitSpreadStrategy(BaseStrategy):
    """
    Debit Spread options strategy.
    
    This strategy involves:
    1. Buying a higher-priced option
    2. Selling a lower-priced option of the same type
    3. Both options have the same expiry
    4. Profit when the spread widens
    """
    
    def __init__(self, params: DebitSpreadParams):
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
        
        logger.info(f"Debit Spread initialized for {self.params.underlying}")
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
        """Check if we have an active Debit Spread position."""
        # Look for Debit Spread legs in positions
        debit_spread_legs = 0
        for symbol, position in current_positions.items():
            if self._is_debit_spread_leg(symbol):
                debit_spread_legs += 1
        
        return debit_spread_legs >= 2  # Debit Spread has 2 legs
    
    def _is_debit_spread_leg(self, symbol: str) -> bool:
        """Check if a symbol is part of our Debit Spread."""
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
        
        # Create Debit Spread entry signals
        signals.extend(self._create_debit_spread_entry())
        
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
        
        # For call spreads, check if underlying is above long strike
        # For put spreads, check if underlying is below long strike
        if self.params.option_type == 'CALL':
            return current_price > self.params.long_strike
        else:  # PUT
            return current_price < self.params.long_strike
    
    def _create_debit_spread_entry(self) -> List[Dict[str, Any]]:
        """Create Debit Spread entry signals."""
        signals = []
        
        # Create 2 legs for Debit Spread
        legs = [
            # Long option (higher strike for calls, lower strike for puts)
            {
                'symbol': f"{self.params.underlying}_{self.params.option_type}_{self.params.long_strike}_{self.params.expiry.strftime('%Y%m%d')}",
                'side': 'BUY',
                'quantity': 1,
                'leg_type': 'long'
            },
            # Short option (lower strike for calls, higher strike for puts)
            {
                'symbol': f"{self.params.underlying}_{self.params.option_type}_{self.params.short_strike}_{self.params.expiry.strftime('%Y%m%d')}",
                'side': 'SELL',
                'quantity': 1,
                'leg_type': 'short'
            }
        ]
        
        for leg in legs:
            signals.append({
                'symbol': leg['symbol'],
                'side': leg['side'],
                'quantity': leg['quantity'],
                'strategy': 'debit_spread',
                'leg_type': leg['leg_type'],
                'underlying': self.params.underlying,
                'expiry': self.params.expiry,
                'option_type': self.params.option_type,
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
        legs = ['long', 'short']
        
        for leg_type in legs:
            signals.append({
                'symbol': f"{self.params.underlying}_{self.params.option_type}_{leg_type.upper()}_{self.params.expiry.strftime('%Y%m%d')}",
                'side': 'CLOSE',  # This would need to be handled by the order manager
                'quantity': 1,
                'strategy': 'debit_spread',
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
            if self._is_debit_spread_leg(symbol):
                total_pnl += position.unrealized_pnl
        
        return total_pnl
    
    def _calculate_max_profit(self) -> float:
        """Calculate maximum profit of the Debit Spread."""
        # Max profit = difference between strikes - net debit
        # This would be calculated based on option prices
        # For now, return placeholder
        return 50.0
    
    def _calculate_max_loss(self) -> float:
        """Calculate maximum loss of the Debit Spread."""
        # Max loss = net debit paid
        # This would be calculated based on option prices
        # For now, return placeholder
        return 100.0
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get strategy information."""
        return {
            'strategy_name': 'Debit Spread',
            'underlying': self.params.underlying,
            'expiry': self.params.expiry,
            'option_type': self.params.option_type,
            'long_strike': self.params.long_strike,
            'short_strike': self.params.short_strike,
            'max_profit': self.max_profit,
            'max_loss': self.max_loss,
            'target_profit': self.params.target_profit,
            'stop_loss': self.params.stop_loss,
            'days_to_expiry': self.params.days_to_expiry
        }
