"""
Margin calculations for options strategies in the Liquid F&O Trading System.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import date
import logging

from ..config import config


@dataclass
class MarginRequirement:
    """Margin requirement data structure."""
    span_margin: float
    exposure_margin: float
    total_margin: float
    available_margin: float
    margin_utilization: float


@dataclass
class StrategyMargin:
    """Strategy margin data structure."""
    strategy_name: str
    total_margin: float
    max_loss: float
    margin_ratio: float
    risk_reward_ratio: float


class MarginCalculator:
    """Options strategy margin calculator."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = config.get_risk_config()
        
        # Margin rates (simplified - in practice, these would be dynamic)
        self.margin_rates = {
            'naked_call': 0.15,  # 15% of underlying value
            'naked_put': 0.15,   # 15% of underlying value
            'covered_call': 0.0, # No additional margin for covered calls
            'cash_secured_put': 0.0,  # No additional margin for cash secured puts
            'spread': 0.05,      # 5% of spread width
            'straddle': 0.20,    # 20% of underlying value
            'strangle': 0.20,    # 20% of underlying value
            'iron_condor': 0.10, # 10% of spread width
            'iron_butterfly': 0.10,  # 10% of spread width
            'calendar': 0.05,    # 5% of underlying value
        }
    
    def calculate_strategy_margin(self, strategy_legs: List[Dict], 
                                underlying_price: float) -> StrategyMargin:
        """Calculate margin requirement for a strategy."""
        try:
            strategy_type = self._identify_strategy_type(strategy_legs)
            total_margin = 0
            max_loss = 0
            
            if strategy_type == 'naked_call':
                total_margin = self._calculate_naked_call_margin(strategy_legs, underlying_price)
                max_loss = self._calculate_naked_call_max_loss(strategy_legs, underlying_price)
            
            elif strategy_type == 'naked_put':
                total_margin = self._calculate_naked_put_margin(strategy_legs, underlying_price)
                max_loss = self._calculate_naked_put_max_loss(strategy_legs, underlying_price)
            
            elif strategy_type == 'spread':
                total_margin = self._calculate_spread_margin(strategy_legs, underlying_price)
                max_loss = self._calculate_spread_max_loss(strategy_legs, underlying_price)
            
            elif strategy_type == 'straddle':
                total_margin = self._calculate_straddle_margin(strategy_legs, underlying_price)
                max_loss = self._calculate_straddle_max_loss(strategy_legs, underlying_price)
            
            elif strategy_type == 'iron_condor':
                total_margin = self._calculate_iron_condor_margin(strategy_legs, underlying_price)
                max_loss = self._calculate_iron_condor_max_loss(strategy_legs, underlying_price)
            
            else:
                # Generic calculation
                total_margin = self._calculate_generic_margin(strategy_legs, underlying_price)
                max_loss = self._calculate_generic_max_loss(strategy_legs, underlying_price)
            
            margin_ratio = total_margin / underlying_price if underlying_price > 0 else 0
            risk_reward_ratio = max_loss / total_margin if total_margin > 0 else 0
            
            return StrategyMargin(
                strategy_name=strategy_type,
                total_margin=total_margin,
                max_loss=max_loss,
                margin_ratio=margin_ratio,
                risk_reward_ratio=risk_reward_ratio
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate strategy margin: {e}")
            return StrategyMargin(
                strategy_name='unknown',
                total_margin=0,
                max_loss=0,
                margin_ratio=0,
                risk_reward_ratio=0
            )
    
    def _identify_strategy_type(self, strategy_legs: List[Dict]) -> str:
        """Identify the type of options strategy."""
        if not strategy_legs:
            return 'unknown'
        
        # Count calls and puts
        call_count = sum(1 for leg in strategy_legs if leg.get('option_type') == 'CALL')
        put_count = sum(1 for leg in strategy_legs if leg.get('option_type') == 'PUT')
        
        # Count buy and sell positions
        buy_count = sum(1 for leg in strategy_legs if leg.get('action') == 'BUY')
        sell_count = sum(1 for leg in strategy_legs if leg.get('action') == 'SELL')
        
        # Identify strategy type
        if len(strategy_legs) == 1:
            leg = strategy_legs[0]
            if leg.get('action') == 'SELL':
                if leg.get('option_type') == 'CALL':
                    return 'naked_call'
                else:
                    return 'naked_put'
            else:
                return 'long_option'
        
        elif len(strategy_legs) == 2:
            if call_count == 1 and put_count == 1:
                return 'straddle'
            elif call_count == 2 or put_count == 2:
                return 'spread'
            else:
                return 'two_leg_strategy'
        
        elif len(strategy_legs) == 4:
            if call_count == 2 and put_count == 2:
                return 'iron_condor'
            else:
                return 'four_leg_strategy'
        
        else:
            return 'complex_strategy'
    
    def _calculate_naked_call_margin(self, strategy_legs: List[Dict], 
                                   underlying_price: float) -> float:
        """Calculate margin for naked call."""
        total_margin = 0
        
        for leg in strategy_legs:
            if (leg.get('action') == 'SELL' and 
                leg.get('option_type') == 'CALL'):
                
                strike_price = leg.get('strike_price', 0)
                quantity = leg.get('quantity', 0)
                
                # Naked call margin = max(20% of underlying - OTM amount, 10% of underlying)
                otm_amount = max(0, underlying_price - strike_price)
                margin_per_unit = max(
                    0.20 * underlying_price - otm_amount,
                    0.10 * underlying_price
                )
                
                total_margin += margin_per_unit * quantity
        
        return total_margin
    
    def _calculate_naked_put_margin(self, strategy_legs: List[Dict], 
                                   underlying_price: float) -> float:
        """Calculate margin for naked put."""
        total_margin = 0
        
        for leg in strategy_legs:
            if (leg.get('action') == 'SELL' and 
                leg.get('option_type') == 'PUT'):
                
                strike_price = leg.get('strike_price', 0)
                quantity = leg.get('quantity', 0)
                
                # Naked put margin = max(20% of underlying - OTM amount, 10% of strike)
                otm_amount = max(0, strike_price - underlying_price)
                margin_per_unit = max(
                    0.20 * underlying_price - otm_amount,
                    0.10 * strike_price
                )
                
                total_margin += margin_per_unit * quantity
        
        return total_margin
    
    def _calculate_spread_margin(self, strategy_legs: List[Dict], 
                               underlying_price: float) -> float:
        """Calculate margin for spread strategies."""
        # For spreads, margin is typically the difference between strikes
        call_strikes = [leg.get('strike_price', 0) for leg in strategy_legs 
                       if leg.get('option_type') == 'CALL']
        put_strikes = [leg.get('strike_price', 0) for leg in strategy_legs 
                      if leg.get('option_type') == 'PUT']
        
        total_margin = 0
        
        if call_strikes and len(call_strikes) == 2:
            # Call spread
            spread_width = abs(call_strikes[1] - call_strikes[0])
            total_margin += spread_width
        
        if put_strikes and len(put_strikes) == 2:
            # Put spread
            spread_width = abs(put_strikes[1] - put_strikes[0])
            total_margin += spread_width
        
        return total_margin
    
    def _calculate_straddle_margin(self, strategy_legs: List[Dict], 
                                 underlying_price: float) -> float:
        """Calculate margin for straddle strategies."""
        # Straddle margin is typically 20% of underlying value
        return 0.20 * underlying_price
    
    def _calculate_iron_condor_margin(self, strategy_legs: List[Dict], 
                                    underlying_price: float) -> float:
        """Calculate margin for iron condor strategies."""
        # Iron condor margin is the width of the spread
        call_strikes = sorted([leg.get('strike_price', 0) for leg in strategy_legs 
                             if leg.get('option_type') == 'CALL'])
        put_strikes = sorted([leg.get('strike_price', 0) for leg in strategy_legs 
                            if leg.get('option_type') == 'PUT'])
        
        total_margin = 0
        
        if len(call_strikes) == 2:
            total_margin += call_strikes[1] - call_strikes[0]
        
        if len(put_strikes) == 2:
            total_margin += put_strikes[1] - put_strikes[0]
        
        return total_margin
    
    def _calculate_generic_margin(self, strategy_legs: List[Dict], 
                                underlying_price: float) -> float:
        """Calculate margin for generic strategies."""
        total_margin = 0
        
        for leg in strategy_legs:
            if leg.get('action') == 'SELL':
                strike_price = leg.get('strike_price', 0)
                quantity = leg.get('quantity', 0)
                
                # Generic margin calculation
                margin_per_unit = 0.15 * underlying_price  # 15% of underlying
                total_margin += margin_per_unit * quantity
        
        return total_margin
    
    def _calculate_naked_call_max_loss(self, strategy_legs: List[Dict], 
                                     underlying_price: float) -> float:
        """Calculate maximum loss for naked call."""
        max_loss = 0
        
        for leg in strategy_legs:
            if (leg.get('action') == 'SELL' and 
                leg.get('option_type') == 'CALL'):
                
                strike_price = leg.get('strike_price', 0)
                quantity = leg.get('quantity', 0)
                
                # Max loss is unlimited for naked calls
                # Use a reasonable estimate (e.g., 3x underlying price)
                max_loss += 3 * underlying_price * quantity
        
        return max_loss
    
    def _calculate_naked_put_max_loss(self, strategy_legs: List[Dict], 
                                    underlying_price: float) -> float:
        """Calculate maximum loss for naked put."""
        max_loss = 0
        
        for leg in strategy_legs:
            if (leg.get('action') == 'SELL' and 
                leg.get('option_type') == 'PUT'):
                
                strike_price = leg.get('strike_price', 0)
                quantity = leg.get('quantity', 0)
                
                # Max loss is strike price (if underlying goes to zero)
                max_loss += strike_price * quantity
        
        return max_loss
    
    def _calculate_spread_max_loss(self, strategy_legs: List[Dict], 
                                 underlying_price: float) -> float:
        """Calculate maximum loss for spread strategies."""
        # For spreads, max loss is typically the width of the spread
        return self._calculate_spread_margin(strategy_legs, underlying_price)
    
    def _calculate_straddle_max_loss(self, strategy_legs: List[Dict], 
                                   underlying_price: float) -> float:
        """Calculate maximum loss for straddle strategies."""
        # For long straddles, max loss is the premium paid
        # For short straddles, max loss is unlimited
        return underlying_price  # Simplified estimate
    
    def _calculate_iron_condor_max_loss(self, strategy_legs: List[Dict], 
                                      underlying_price: float) -> float:
        """Calculate maximum loss for iron condor strategies."""
        # Max loss is the width of the spread minus premium received
        return self._calculate_iron_condor_margin(strategy_legs, underlying_price)
    
    def _calculate_generic_max_loss(self, strategy_legs: List[Dict], 
                                  underlying_price: float) -> float:
        """Calculate maximum loss for generic strategies."""
        # Simplified calculation
        return self._calculate_generic_margin(strategy_legs, underlying_price)
    
    def calculate_portfolio_margin(self, strategies: List[StrategyMargin]) -> MarginRequirement:
        """Calculate portfolio-level margin requirements."""
        try:
            total_margin = sum(strategy.total_margin for strategy in strategies)
            max_loss = sum(strategy.max_loss for strategy in strategies)
            
            # Get available margin from config
            available_margin = 1000000  # Simplified - would come from broker
            
            margin_utilization = total_margin / available_margin if available_margin > 0 else 0
            
            return MarginRequirement(
                span_margin=total_margin * 0.7,  # 70% span margin
                exposure_margin=total_margin * 0.3,  # 30% exposure margin
                total_margin=total_margin,
                available_margin=available_margin,
                margin_utilization=margin_utilization
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate portfolio margin: {e}")
            return MarginRequirement(0, 0, 0, 0, 0)
    
    def check_margin_requirements(self, strategies: List[StrategyMargin], 
                                available_margin: float) -> Dict[str, bool]:
        """Check if margin requirements are met."""
        try:
            total_margin = sum(strategy.total_margin for strategy in strategies)
            
            # Check if total margin exceeds available margin
            margin_ok = total_margin <= available_margin
            
            # Check individual strategy margins
            strategy_checks = {}
            for strategy in strategies:
                strategy_checks[strategy.strategy_name] = (
                    strategy.total_margin <= available_margin * 0.1  # Max 10% per strategy
                )
            
            return {
                'overall_margin_ok': margin_ok,
                'total_margin': total_margin,
                'available_margin': available_margin,
                'margin_utilization': total_margin / available_margin if available_margin > 0 else 0,
                'strategy_checks': strategy_checks
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check margin requirements: {e}")
            return {'overall_margin_ok': False}
    
    def optimize_margin_usage(self, strategies: List[StrategyMargin], 
                            available_margin: float) -> List[StrategyMargin]:
        """Optimize margin usage by adjusting strategy sizes."""
        try:
            # Sort strategies by risk-reward ratio
            sorted_strategies = sorted(strategies, 
                                     key=lambda s: s.risk_reward_ratio, 
                                     reverse=True)
            
            optimized_strategies = []
            remaining_margin = available_margin
            
            for strategy in sorted_strategies:
                if strategy.total_margin <= remaining_margin:
                    optimized_strategies.append(strategy)
                    remaining_margin -= strategy.total_margin
                else:
                    # Scale down strategy to fit available margin
                    scale_factor = remaining_margin / strategy.total_margin
                    scaled_strategy = StrategyMargin(
                        strategy_name=strategy.strategy_name,
                        total_margin=strategy.total_margin * scale_factor,
                        max_loss=strategy.max_loss * scale_factor,
                        margin_ratio=strategy.margin_ratio,
                        risk_reward_ratio=strategy.risk_reward_ratio
                    )
                    optimized_strategies.append(scaled_strategy)
                    break
            
            return optimized_strategies
            
        except Exception as e:
            self.logger.error(f"Failed to optimize margin usage: {e}")
            return strategies
