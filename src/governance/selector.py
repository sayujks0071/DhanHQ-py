"""
Strategy selector for choosing the best performing strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from .scorer import StrategyScorer
from .validator import StrategyValidator

logger = logging.getLogger(__name__)


@dataclass
class StrategyScore:
    """Strategy performance score."""
    strategy_name: str
    total_score: float
    return_score: float
    risk_score: float
    stability_score: float
    capacity_score: float
    greek_score: float
    suitability: str  # 'EXCELLENT', 'GOOD', 'FAIR', 'POOR'


class StrategySelector:
    """
    Strategy selector for choosing the best performing strategies.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scorer = StrategyScorer(config)
        self.validator = StrategyValidator(config)
        
        # Selection criteria
        self.min_total_score = config.get('min_total_score', 0.6)
        self.min_return_score = config.get('min_return_score', 0.5)
        self.max_risk_score = config.get('max_risk_score', 0.3)
        self.min_stability_score = config.get('min_stability_score', 0.4)
        self.min_capacity_score = config.get('min_capacity_score', 0.3)
        self.min_greek_score = config.get('min_greek_score', 0.4)
        
        # Strategy tracking
        self.strategy_scores: Dict[str, StrategyScore] = {}
        self.selected_strategies: List[str] = []
        self.rejected_strategies: List[str] = []
    
    def evaluate_strategy(
        self,
        strategy_name: str,
        backtest_results: Dict[str, Any],
        walk_forward_results: List[Dict[str, Any]],
        current_market_conditions: Dict[str, Any]
    ) -> StrategyScore:
        """
        Evaluate a strategy and return its score.
        
        Args:
            strategy_name: Name of the strategy
            backtest_results: Backtest performance metrics
            walk_forward_results: Walk-forward optimization results
            current_market_conditions: Current market conditions
            
        Returns:
            Strategy score
        """
        try:
            # Calculate individual scores
            return_score = self.scorer.calculate_return_score(backtest_results)
            risk_score = self.scorer.calculate_risk_score(backtest_results)
            stability_score = self.scorer.calculate_stability_score(walk_forward_results)
            capacity_score = self.scorer.calculate_capacity_score(backtest_results)
            greek_score = self.scorer.calculate_greek_score(backtest_results)
            
            # Calculate total score (weighted average)
            weights = self.config.get('score_weights', {
                'return': 0.3,
                'risk': 0.25,
                'stability': 0.2,
                'capacity': 0.15,
                'greek': 0.1
            })
            
            total_score = (
                return_score * weights['return'] +
                risk_score * weights['risk'] +
                stability_score * weights['stability'] +
                capacity_score * weights['capacity'] +
                greek_score * weights['greek']
            )
            
            # Determine suitability
            suitability = self._determine_suitability(total_score, return_score, risk_score)
            
            # Create strategy score
            score = StrategyScore(
                strategy_name=strategy_name,
                total_score=total_score,
                return_score=return_score,
                risk_score=risk_score,
                stability_score=stability_score,
                capacity_score=capacity_score,
                greek_score=greek_score,
                suitability=suitability
            )
            
            # Store score
            self.strategy_scores[strategy_name] = score
            
            logger.info(f"Strategy {strategy_name} scored {total_score:.3f} ({suitability})")
            
            return score
            
        except Exception as e:
            logger.error(f"Error evaluating strategy {strategy_name}: {e}")
            return StrategyScore(
                strategy_name=strategy_name,
                total_score=0.0,
                return_score=0.0,
                risk_score=1.0,
                stability_score=0.0,
                capacity_score=0.0,
                greek_score=0.0,
                suitability='POOR'
            )
    
    def select_strategies(
        self,
        available_strategies: List[str],
        max_strategies: int = 5
    ) -> List[str]:
        """
        Select the best strategies from available options.
        
        Args:
            available_strategies: List of available strategy names
            max_strategies: Maximum number of strategies to select
            
        Returns:
            List of selected strategy names
        """
        try:
            # Filter strategies that meet minimum criteria
            qualified_strategies = []
            
            for strategy_name in available_strategies:
                if strategy_name not in self.strategy_scores:
                    continue
                
                score = self.strategy_scores[strategy_name]
                
                # Check if strategy meets minimum criteria
                if self._meets_minimum_criteria(score):
                    qualified_strategies.append((strategy_name, score))
                else:
                    self.rejected_strategies.append(strategy_name)
                    logger.info(f"Strategy {strategy_name} rejected: {self._get_rejection_reason(score)}")
            
            # Sort by total score (descending)
            qualified_strategies.sort(key=lambda x: x[1].total_score, reverse=True)
            
            # Select top strategies
            selected = [strategy for strategy, score in qualified_strategies[:max_strategies]]
            self.selected_strategies = selected
            
            logger.info(f"Selected {len(selected)} strategies: {selected}")
            
            return selected
            
        except Exception as e:
            logger.error(f"Error selecting strategies: {e}")
            return []
    
    def validate_strategy_deployment(
        self,
        strategy_name: str,
        current_positions: Dict[str, Any],
        market_data: Dict[str, Any],
        risk_metrics: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate if a strategy can be deployed safely.
        
        Args:
            strategy_name: Name of the strategy
            current_positions: Current portfolio positions
            market_data: Current market data
            risk_metrics: Current risk metrics
            
        Returns:
            (is_valid, violations): Tuple of validation status and violations
        """
        try:
            violations = []
            
            # Check if strategy is selected
            if strategy_name not in self.selected_strategies:
                violations.append("Strategy not selected for deployment")
            
            # Check if strategy meets current market conditions
            if not self._check_market_conditions(strategy_name, market_data):
                violations.append("Strategy not suitable for current market conditions")
            
            # Check if strategy meets risk limits
            if not self._check_risk_limits(strategy_name, risk_metrics):
                violations.append("Strategy exceeds risk limits")
            
            # Check if strategy has sufficient capacity
            if not self._check_capacity(strategy_name, current_positions):
                violations.append("Strategy exceeds capacity limits")
            
            # Check if strategy meets Greek limits
            if not self._check_greek_limits(strategy_name, risk_metrics):
                violations.append("Strategy exceeds Greek limits")
            
            is_valid = len(violations) == 0
            
            if not is_valid:
                logger.warning(f"Strategy {strategy_name} validation failed: {violations}")
            
            return is_valid, violations
            
        except Exception as e:
            logger.error(f"Error validating strategy deployment: {e}")
            return False, [f"Validation error: {e}"]
    
    def _determine_suitability(
        self,
        total_score: float,
        return_score: float,
        risk_score: float
    ) -> str:
        """Determine strategy suitability based on scores."""
        if total_score >= 0.8 and return_score >= 0.7 and risk_score <= 0.2:
            return 'EXCELLENT'
        elif total_score >= 0.6 and return_score >= 0.5 and risk_score <= 0.3:
            return 'GOOD'
        elif total_score >= 0.4 and return_score >= 0.3 and risk_score <= 0.4:
            return 'FAIR'
        else:
            return 'POOR'
    
    def _meets_minimum_criteria(self, score: StrategyScore) -> bool:
        """Check if strategy meets minimum criteria."""
        return (
            score.total_score >= self.min_total_score and
            score.return_score >= self.min_return_score and
            score.risk_score <= self.max_risk_score and
            score.stability_score >= self.min_stability_score and
            score.capacity_score >= self.min_capacity_score and
            score.greek_score >= self.min_greek_score
        )
    
    def _get_rejection_reason(self, score: StrategyScore) -> str:
        """Get reason for strategy rejection."""
        reasons = []
        
        if score.total_score < self.min_total_score:
            reasons.append(f"Total score {score.total_score:.3f} < {self.min_total_score}")
        if score.return_score < self.min_return_score:
            reasons.append(f"Return score {score.return_score:.3f} < {self.min_return_score}")
        if score.risk_score > self.max_risk_score:
            reasons.append(f"Risk score {score.risk_score:.3f} > {self.max_risk_score}")
        if score.stability_score < self.min_stability_score:
            reasons.append(f"Stability score {score.stability_score:.3f} < {self.min_stability_score}")
        if score.capacity_score < self.min_capacity_score:
            reasons.append(f"Capacity score {score.capacity_score:.3f} < {self.min_capacity_score}")
        if score.greek_score < self.min_greek_score:
            reasons.append(f"Greek score {score.greek_score:.3f} < {self.min_greek_score}")
        
        return "; ".join(reasons)
    
    def _check_market_conditions(
        self,
        strategy_name: str,
        market_data: Dict[str, Any]
    ) -> bool:
        """Check if strategy is suitable for current market conditions."""
        # This would implement market condition checks
        # For now, return True as placeholder
        return True
    
    def _check_risk_limits(
        self,
        strategy_name: str,
        risk_metrics: Dict[str, Any]
    ) -> bool:
        """Check if strategy meets risk limits."""
        # This would implement risk limit checks
        # For now, return True as placeholder
        return True
    
    def _check_capacity(
        self,
        strategy_name: str,
        current_positions: Dict[str, Any]
    ) -> bool:
        """Check if strategy has sufficient capacity."""
        # This would implement capacity checks
        # For now, return True as placeholder
        return True
    
    def _check_greek_limits(
        self,
        strategy_name: str,
        risk_metrics: Dict[str, Any]
    ) -> bool:
        """Check if strategy meets Greek limits."""
        # This would implement Greek limit checks
        # For now, return True as placeholder
        return True
    
    def get_strategy_rankings(self) -> List[Dict[str, Any]]:
        """Get strategy rankings."""
        rankings = []
        
        for strategy_name, score in self.strategy_scores.items():
            rankings.append({
                'strategy_name': strategy_name,
                'total_score': score.total_score,
                'return_score': score.return_score,
                'risk_score': score.risk_score,
                'stability_score': score.stability_score,
                'capacity_score': score.capacity_score,
                'greek_score': score.greek_score,
                'suitability': score.suitability,
                'selected': strategy_name in self.selected_strategies
            })
        
        # Sort by total score
        rankings.sort(key=lambda x: x['total_score'], reverse=True)
        
        return rankings
    
    def get_selection_summary(self) -> Dict[str, Any]:
        """Get selection summary."""
        return {
            'total_strategies_evaluated': len(self.strategy_scores),
            'selected_strategies': len(self.selected_strategies),
            'rejected_strategies': len(self.rejected_strategies),
            'selection_rate': len(self.selected_strategies) / len(self.strategy_scores) if self.strategy_scores else 0,
            'average_score': np.mean([score.total_score for score in self.strategy_scores.values()]) if self.strategy_scores else 0,
            'selected_strategies_list': self.selected_strategies,
            'rejected_strategies_list': self.rejected_strategies
        }
