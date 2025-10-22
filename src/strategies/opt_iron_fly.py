"""
Iron Butterfly Options Strategy.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import logging

from ..config import config
from ..utils.timezone import ISTTimezone
from ..options.greeks import GreeksCalculator
from ..options.iv import IVCalculator


@dataclass
class IronFlySignal:
    """Iron Butterfly signal."""
    signal_type: str  # 'ENTER', 'EXIT', 'HOLD'
    strategy_legs: List[Dict]
    max_profit: float
    max_loss: float
    breakeven_points: Tuple[float, float]
    confidence: float
    timestamp: datetime
    rationale: str


class IronFlyStrategy:
    """Iron Butterfly Options Strategy."""
    
    def __init__(self, delta_hedge: bool = True, iv_rank_min: float = 0.3, 
                 wing_size_atr: float = 1.5):
        self.logger = logging.getLogger(__name__)
        self.delta_hedge = delta_hedge
        self.iv_rank_min = iv_rank_min
        self.wing_size_atr = wing_size_atr
        
        # Strategy components
        self.greeks_calc = GreeksCalculator()
        self.iv_calc = IVCalculator()
        
        # Strategy state
        self.position = None
        self.entry_time = None
        self.entry_price = None
        self.strategy_legs = []
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        
    def generate_signal(self, option_chain_data: Dict, 
                       current_price: float, atr: float) -> Optional[IronFlySignal]:
        """Generate Iron Butterfly signal."""
        try:
            # Check IV rank
            if not self._check_iv_rank(option_chain_data):
                return IronFlySignal(
                    signal_type='HOLD',
                    strategy_legs=[],
                    max_profit=0.0,
                    max_loss=0.0,
                    breakeven_points=(0.0, 0.0),
                    confidence=0.0,
                    timestamp=ISTTimezone.now(),
                    rationale="IV rank too low"
                )
            
            # Find ATM strike
            atm_strike = self._find_atm_strike(option_chain_data, current_price)
            if not atm_strike:
                return None
            
            # Calculate wing strikes
            wing_strikes = self._calculate_wing_strikes(atm_strike, atr)
            
            # Build strategy legs
            strategy_legs = self._build_strategy_legs(atm_strike, wing_strikes)
            
            # Calculate strategy metrics
            max_profit, max_loss, breakeven_points = self._calculate_strategy_metrics(
                strategy_legs, current_price
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                option_chain_data, current_price, max_profit, max_loss
            )
            
            return IronFlySignal(
                signal_type='ENTER',
                strategy_legs=strategy_legs,
                max_profit=max_profit,
                max_loss=max_loss,
                breakeven_points=breakeven_points,
                confidence=confidence,
                timestamp=ISTTimezone.now(),
                rationale=f"Iron Butterfly at {atm_strike} with wings at {wing_strikes}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate Iron Fly signal: {e}")
            return None
    
    def _check_iv_rank(self, option_chain_data: Dict) -> bool:
        """Check if IV rank meets minimum requirement."""
        try:
            # Get historical IV data (simplified)
            current_iv = option_chain_data.get('current_iv', 0.3)
            historical_ivs = option_chain_data.get('historical_ivs', [])
            
            if not historical_ivs:
                return True  # Assume OK if no historical data
            
            # Calculate IV rank
            iv_rank = self.iv_calc.calculate_iv_rank(current_iv, historical_ivs)
            
            return iv_rank >= self.iv_rank_min
            
        except Exception as e:
            self.logger.warning(f"Failed to check IV rank: {e}")
            return True
    
    def _find_atm_strike(self, option_chain_data: Dict, current_price: float) -> Optional[float]:
        """Find ATM strike price."""
        try:
            calls = option_chain_data.get('calls', [])
            puts = option_chain_data.get('puts', [])
            
            # Find closest strike to current price
            all_strikes = []
            for call in calls:
                if call.get('strike_price'):
                    all_strikes.append(call['strike_price'])
            for put in puts:
                if put.get('strike_price'):
                    all_strikes.append(put['strike_price'])
            
            if not all_strikes:
                return None
            
            # Find closest strike
            atm_strike = min(all_strikes, key=lambda x: abs(x - current_price))
            return atm_strike
            
        except Exception as e:
            self.logger.warning(f"Failed to find ATM strike: {e}")
            return None
    
    def _calculate_wing_strikes(self, atm_strike: float, atr: float) -> Tuple[float, float]:
        """Calculate wing strikes based on ATR."""
        try:
            wing_distance = atr * self.wing_size_atr
            
            # Round to nearest strike interval (assuming 50 point intervals for NIFTY)
            strike_interval = 50
            wing_distance = round(wing_distance / strike_interval) * strike_interval
            
            lower_wing = atm_strike - wing_distance
            upper_wing = atm_strike + wing_distance
            
            return lower_wing, upper_wing
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate wing strikes: {e}")
            return atm_strike - 100, atm_strike + 100
    
    def _build_strategy_legs(self, atm_strike: float, 
                           wing_strikes: Tuple[float, float]) -> List[Dict]:
        """Build Iron Butterfly strategy legs."""
        lower_wing, upper_wing = wing_strikes
        
        legs = [
            # Sell ATM call
            {
                'action': 'SELL',
                'option_type': 'CALL',
                'strike_price': atm_strike,
                'quantity': 1,
                'premium': 0.0  # Will be filled by market data
            },
            # Sell ATM put
            {
                'action': 'SELL',
                'option_type': 'PUT',
                'strike_price': atm_strike,
                'quantity': 1,
                'premium': 0.0  # Will be filled by market data
            },
            # Buy lower wing call
            {
                'action': 'BUY',
                'option_type': 'CALL',
                'strike_price': lower_wing,
                'quantity': 1,
                'premium': 0.0  # Will be filled by market data
            },
            # Buy upper wing call
            {
                'action': 'BUY',
                'option_type': 'CALL',
                'strike_price': upper_wing,
                'quantity': 1,
                'premium': 0.0  # Will be filled by market data
            }
        ]
        
        return legs
    
    def _calculate_strategy_metrics(self, strategy_legs: List[Dict], 
                                  current_price: float) -> Tuple[float, float, Tuple[float, float]]:
        """Calculate strategy profit/loss metrics."""
        try:
            # Simplified calculation - in practice, would use actual option prices
            max_profit = 0.0  # Premium received
            max_loss = 0.0    # Wing width minus premium
            
            # Calculate breakeven points
            breakeven_lower = current_price - max_profit
            breakeven_upper = current_price + max_profit
            
            return max_profit, max_loss, (breakeven_lower, breakeven_upper)
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate strategy metrics: {e}")
            return 0.0, 0.0, (0.0, 0.0)
    
    def _calculate_confidence(self, option_chain_data: Dict, current_price: float, 
                            max_profit: float, max_loss: float) -> float:
        """Calculate signal confidence."""
        try:
            # Base confidence on risk-reward ratio
            if max_loss <= 0:
                return 0.0
            
            risk_reward_ratio = max_profit / max_loss
            confidence = min(1.0, risk_reward_ratio / 2.0)
            
            # Adjust for IV rank
            current_iv = option_chain_data.get('current_iv', 0.3)
            historical_ivs = option_chain_data.get('historical_ivs', [])
            
            if historical_ivs:
                iv_rank = self.iv_calc.calculate_iv_rank(current_iv, historical_ivs)
                confidence *= iv_rank
            
            return max(0.0, confidence)
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate confidence: {e}")
            return 0.0
    
    def update_position(self, current_price: float, option_chain_data: Dict) -> Dict:
        """Update position status and check exit conditions."""
        if not self.position:
            return {'action': 'HOLD', 'reason': 'No position'}
        
        try:
            # Check time-based exit (e.g., 7 days before expiry)
            if self.entry_time:
                days_held = (ISTTimezone.now() - self.entry_time).days
                if days_held >= 7:  # Exit 7 days before expiry
                    return self._close_position('TIME_EXIT', current_price)
            
            # Check profit target (50% of max profit)
            current_pnl = self._calculate_current_pnl(current_price)
            if current_pnl >= self.max_profit * 0.5:
                return self._close_position('PROFIT_TARGET', current_price)
            
            # Check stop loss (80% of max loss)
            if current_pnl <= -self.max_loss * 0.8:
                return self._close_position('STOP_LOSS', current_price)
            
            return {'action': 'HOLD', 'reason': 'Position maintained'}
            
        except Exception as e:
            self.logger.error(f"Failed to update position: {e}")
            return {'action': 'HOLD', 'reason': 'Error updating position'}
    
    def _calculate_current_pnl(self, current_price: float) -> float:
        """Calculate current P&L for the position."""
        try:
            # Simplified calculation - in practice, would use actual option prices
            # and Greeks for accurate P&L calculation
            
            if not self.strategy_legs:
                return 0.0
            
            # This is a placeholder - real implementation would calculate
            # P&L based on current option prices and position
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate current P&L: {e}")
            return 0.0
    
    def _close_position(self, reason: str, current_price: float) -> Dict:
        """Close current position."""
        try:
            if not self.position:
                return {'action': 'HOLD', 'reason': 'No position to close'}
            
            # Calculate final P&L
            final_pnl = self._calculate_current_pnl(current_price)
            
            # Update performance metrics
            self.total_trades += 1
            if final_pnl > 0:
                self.winning_trades += 1
            self.total_pnl += final_pnl
            
            # Reset position
            self.position = None
            self.entry_time = None
            self.entry_price = None
            self.strategy_legs = []
            
            return {
                'action': 'CLOSE',
                'reason': reason,
                'pnl': final_pnl,
                'exit_price': current_price
            }
            
        except Exception as e:
            self.logger.error(f"Failed to close position: {e}")
            return {'action': 'HOLD', 'reason': 'Error closing position'}
    
    def enter_position(self, signal: IronFlySignal) -> Dict:
        """Enter position based on signal."""
        try:
            if signal.signal_type != 'ENTER':
                return {'action': 'HOLD', 'reason': 'No entry signal'}
            
            # Set position
            self.position = 'IRON_FLY'
            self.entry_time = signal.timestamp
            self.entry_price = signal.entry_price if hasattr(signal, 'entry_price') else 0.0
            self.strategy_legs = signal.strategy_legs
            self.max_profit = signal.max_profit
            self.max_loss = signal.max_loss
            
            return {
                'action': 'ENTER',
                'position': self.position,
                'strategy_legs': len(self.strategy_legs),
                'max_profit': self.max_profit,
                'max_loss': self.max_loss,
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
        self.strategy_legs = []
        
        self.logger.info("Iron Fly strategy reset")
    
    def get_strategy_info(self) -> Dict:
        """Get strategy information."""
        return {
            'name': 'Iron Butterfly',
            'type': 'Options',
            'delta_hedge': self.delta_hedge,
            'iv_rank_min': self.iv_rank_min,
            'wing_size_atr': self.wing_size_atr,
            'current_position': self.position,
            'strategy_legs': len(self.strategy_legs),
            'max_profit': getattr(self, 'max_profit', 0.0),
            'max_loss': getattr(self, 'max_loss', 0.0)
        }
