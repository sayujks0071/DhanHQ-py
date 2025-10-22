"""
Strategy performance scoring system.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScoreWeights:
    """Score weights configuration."""
    return_weight: float = 0.3
    risk_weight: float = 0.25
    stability_weight: float = 0.2
    capacity_weight: float = 0.15
    greek_weight: float = 0.1


class StrategyScorer:
    """
    Strategy performance scoring system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.weights = ScoreWeights(
            return_weight=config.get('return_weight', 0.3),
            risk_weight=config.get('risk_weight', 0.25),
            stability_weight=config.get('stability_weight', 0.2),
            capacity_weight=config.get('capacity_weight', 0.15),
            greek_weight=config.get('greek_weight', 0.1)
        )
        
        # Scoring thresholds
        self.min_annual_return = config.get('min_annual_return', 0.15)
        self.max_volatility = config.get('max_volatility', 0.3)
        self.max_drawdown = config.get('max_drawdown', 0.15)
        self.min_sharpe_ratio = config.get('min_sharpe_ratio', 1.0)
        self.min_profit_factor = config.get('min_profit_factor', 1.25)
        self.min_win_rate = config.get('min_win_rate', 0.4)
        
    def calculate_return_score(self, backtest_results: Dict[str, Any]) -> float:
        """
        Calculate return-based score.
        
        Args:
            backtest_results: Backtest performance metrics
            
        Returns:
            Return score (0-1)
        """
        try:
            annual_return = backtest_results.get('annualized_return', 0.0)
            total_return = backtest_results.get('total_return', 0.0)
            sharpe_ratio = backtest_results.get('sharpe_ratio', 0.0)
            
            # Calculate return score
            return_score = 0.0
            
            # Annual return component (40% weight)
            if annual_return >= self.min_annual_return:
                return_score += 0.4 * min(1.0, annual_return / (self.min_annual_return * 2))
            else:
                return_score += 0.4 * (annual_return / self.min_annual_return)
            
            # Total return component (30% weight)
            if total_return > 0:
                return_score += 0.3 * min(1.0, total_return / 0.5)  # 50% total return target
            else:
                return_score += 0.3 * max(0.0, 1 + total_return)  # Penalty for negative returns
            
            # Sharpe ratio component (30% weight)
            if sharpe_ratio >= self.min_sharpe_ratio:
                return_score += 0.3 * min(1.0, sharpe_ratio / (self.min_sharpe_ratio * 2))
            else:
                return_score += 0.3 * (sharpe_ratio / self.min_sharpe_ratio)
            
            return max(0.0, min(1.0, return_score))
            
        except Exception as e:
            logger.error(f"Error calculating return score: {e}")
            return 0.0
    
    def calculate_risk_score(self, backtest_results: Dict[str, Any]) -> float:
        """
        Calculate risk-based score (lower is better).
        
        Args:
            backtest_results: Backtest performance metrics
            
        Returns:
            Risk score (0-1, lower is better)
        """
        try:
            volatility = backtest_results.get('volatility', 0.0)
            max_drawdown = abs(backtest_results.get('max_drawdown', 0.0))
            var_95 = abs(backtest_results.get('var_95', 0.0))
            cvar_95 = abs(backtest_results.get('cvar_95', 0.0))
            
            # Calculate risk score (lower is better)
            risk_score = 0.0
            
            # Volatility component (30% weight)
            if volatility <= self.max_volatility:
                risk_score += 0.3 * (1 - volatility / self.max_volatility)
            else:
                risk_score += 0.3 * max(0.0, 1 - (volatility - self.max_volatility) / self.max_volatility)
            
            # Max drawdown component (40% weight)
            if max_drawdown <= self.max_drawdown:
                risk_score += 0.4 * (1 - max_drawdown / self.max_drawdown)
            else:
                risk_score += 0.4 * max(0.0, 1 - (max_drawdown - self.max_drawdown) / self.max_drawdown)
            
            # VaR component (15% weight)
            if var_95 <= 0.05:  # 5% VaR threshold
                risk_score += 0.15 * (1 - var_95 / 0.05)
            else:
                risk_score += 0.15 * max(0.0, 1 - (var_95 - 0.05) / 0.05)
            
            # CVaR component (15% weight)
            if cvar_95 <= 0.1:  # 10% CVaR threshold
                risk_score += 0.15 * (1 - cvar_95 / 0.1)
            else:
                risk_score += 0.15 * max(0.0, 1 - (cvar_95 - 0.1) / 0.1)
            
            return max(0.0, min(1.0, risk_score))
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 1.0  # High risk if error
    
    def calculate_stability_score(self, walk_forward_results: List[Dict[str, Any]]) -> float:
        """
        Calculate stability score based on walk-forward results.
        
        Args:
            walk_forward_results: Walk-forward optimization results
            
        Returns:
            Stability score (0-1)
        """
        try:
            if not walk_forward_results:
                return 0.0
            
            # Extract metrics
            returns = [result.get('annualized_return', 0.0) for result in walk_forward_results]
            sharpe_ratios = [result.get('sharpe_ratio', 0.0) for result in walk_forward_results]
            max_drawdowns = [abs(result.get('max_drawdown', 0.0)) for result in walk_forward_results]
            
            # Calculate stability metrics
            return_stability = 1 - (np.std(returns) / np.mean(returns)) if np.mean(returns) != 0 else 0
            sharpe_stability = 1 - (np.std(sharpe_ratios) / np.mean(sharpe_ratios)) if np.mean(sharpe_ratios) != 0 else 0
            drawdown_stability = 1 - (np.std(max_drawdowns) / np.mean(max_drawdowns)) if np.mean(max_drawdowns) != 0 else 0
            
            # Calculate overall stability score
            stability_score = (
                return_stability * 0.4 +
                sharpe_stability * 0.3 +
                drawdown_stability * 0.3
            )
            
            return max(0.0, min(1.0, stability_score))
            
        except Exception as e:
            logger.error(f"Error calculating stability score: {e}")
            return 0.0
    
    def calculate_capacity_score(self, backtest_results: Dict[str, Any]) -> float:
        """
        Calculate capacity score based on strategy capacity.
        
        Args:
            backtest_results: Backtest performance metrics
            
        Returns:
            Capacity score (0-1)
        """
        try:
            total_trades = backtest_results.get('total_trades', 0)
            win_rate = backtest_results.get('win_rate', 0.0)
            profit_factor = backtest_results.get('profit_factor', 0.0)
            avg_win = backtest_results.get('avg_win', 0.0)
            avg_loss = backtest_results.get('avg_loss', 0.0)
            
            # Calculate capacity score
            capacity_score = 0.0
            
            # Trade count component (30% weight)
            if total_trades >= 100:  # Minimum trade count
                capacity_score += 0.3 * min(1.0, total_trades / 500)  # 500 trades target
            else:
                capacity_score += 0.3 * (total_trades / 100)
            
            # Win rate component (25% weight)
            if win_rate >= self.min_win_rate:
                capacity_score += 0.25 * min(1.0, win_rate / (self.min_win_rate * 2))
            else:
                capacity_score += 0.25 * (win_rate / self.min_win_rate)
            
            # Profit factor component (25% weight)
            if profit_factor >= self.min_profit_factor:
                capacity_score += 0.25 * min(1.0, profit_factor / (self.min_profit_factor * 2))
            else:
                capacity_score += 0.25 * (profit_factor / self.min_profit_factor)
            
            # Average win/loss component (20% weight)
            if avg_loss > 0:
                win_loss_ratio = avg_win / avg_loss
                capacity_score += 0.2 * min(1.0, win_loss_ratio / 2.0)  # 2:1 win/loss target
            else:
                capacity_score += 0.2 * 0.0
            
            return max(0.0, min(1.0, capacity_score))
            
        except Exception as e:
            logger.error(f"Error calculating capacity score: {e}")
            return 0.0
    
    def calculate_greek_score(self, backtest_results: Dict[str, Any]) -> float:
        """
        Calculate Greek-based score for options strategies.
        
        Args:
            backtest_results: Backtest performance metrics
            
        Returns:
            Greek score (0-1)
        """
        try:
            theta_harvest = backtest_results.get('theta_harvest', 0.0)
            vega_exposure = abs(backtest_results.get('vega_exposure', 0.0))
            gamma_exposure = abs(backtest_results.get('gamma_exposure', 0.0))
            delta_exposure = abs(backtest_results.get('delta_exposure', 0.0))
            
            # Calculate Greek score
            greek_score = 0.0
            
            # Theta harvest component (40% weight)
            if theta_harvest > 0:
                greek_score += 0.4 * min(1.0, theta_harvest / 1000)  # 1000 theta target
            else:
                greek_score += 0.4 * 0.0
            
            # Vega exposure component (25% weight)
            if vega_exposure <= 1000:  # 1000 vega limit
                greek_score += 0.25 * (1 - vega_exposure / 1000)
            else:
                greek_score += 0.25 * 0.0
            
            # Gamma exposure component (20% weight)
            if gamma_exposure <= 100:  # 100 gamma limit
                greek_score += 0.2 * (1 - gamma_exposure / 100)
            else:
                greek_score += 0.2 * 0.0
            
            # Delta exposure component (15% weight)
            if delta_exposure <= 500:  # 500 delta limit
                greek_score += 0.15 * (1 - delta_exposure / 500)
            else:
                greek_score += 0.15 * 0.0
            
            return max(0.0, min(1.0, greek_score))
            
        except Exception as e:
            logger.error(f"Error calculating Greek score: {e}")
            return 0.0
    
    def calculate_composite_score(
        self,
        return_score: float,
        risk_score: float,
        stability_score: float,
        capacity_score: float,
        greek_score: float
    ) -> float:
        """
        Calculate composite score from individual scores.
        
        Args:
            return_score: Return score
            risk_score: Risk score
            stability_score: Stability score
            capacity_score: Capacity score
            greek_score: Greek score
            
        Returns:
            Composite score (0-1)
        """
        try:
            composite_score = (
                return_score * self.weights.return_weight +
                risk_score * self.weights.risk_weight +
                stability_score * self.weights.stability_weight +
                capacity_score * self.weights.capacity_weight +
                greek_score * self.weights.greek_weight
            )
            
            return max(0.0, min(1.0, composite_score))
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 0.0
    
    def get_score_breakdown(
        self,
        backtest_results: Dict[str, Any],
        walk_forward_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get detailed score breakdown.
        
        Args:
            backtest_results: Backtest performance metrics
            walk_forward_results: Walk-forward optimization results
            
        Returns:
            Score breakdown
        """
        try:
            return_score = self.calculate_return_score(backtest_results)
            risk_score = self.calculate_risk_score(backtest_results)
            stability_score = self.calculate_stability_score(walk_forward_results)
            capacity_score = self.calculate_capacity_score(backtest_results)
            greek_score = self.calculate_greek_score(backtest_results)
            
            composite_score = self.calculate_composite_score(
                return_score, risk_score, stability_score, capacity_score, greek_score
            )
            
            return {
                'composite_score': composite_score,
                'return_score': return_score,
                'risk_score': risk_score,
                'stability_score': stability_score,
                'capacity_score': capacity_score,
                'greek_score': greek_score,
                'weights': {
                    'return': self.weights.return_weight,
                    'risk': self.weights.risk_weight,
                    'stability': self.weights.stability_weight,
                    'capacity': self.weights.capacity_weight,
                    'greek': self.weights.greek_weight
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting score breakdown: {e}")
            return {}
