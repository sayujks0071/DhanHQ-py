"""
Strategy validation system.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Validation result."""
    is_valid: bool
    violations: List[str]
    warnings: List[str]
    score: float


class StrategyValidator:
    """
    Strategy validation system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Validation thresholds
        self.min_annual_return = config.get('min_annual_return', 0.15)
        self.max_volatility = config.get('max_volatility', 0.3)
        self.max_drawdown = config.get('max_drawdown', 0.15)
        self.min_sharpe_ratio = config.get('min_sharpe_ratio', 1.0)
        self.min_profit_factor = config.get('min_profit_factor', 1.25)
        self.min_win_rate = config.get('min_win_rate', 0.4)
        self.min_trade_count = config.get('min_trade_count', 100)
        self.max_consecutive_losses = config.get('max_consecutive_losses', 5)
        self.min_calmar_ratio = config.get('min_calmar_ratio', 1.0)
        self.max_var_95 = config.get('max_var_95', 0.05)
        self.max_cvar_95 = config.get('max_cvar_95', 0.1)
        
        # Greek limits
        self.max_delta_exposure = config.get('max_delta_exposure', 500)
        self.max_gamma_exposure = config.get('max_gamma_exposure', 100)
        self.max_theta_exposure = config.get('max_theta_exposure', 1000)
        self.max_vega_exposure = config.get('max_vega_exposure', 1000)
        
        # Capacity limits
        self.max_position_size = config.get('max_position_size', 10000)
        self.max_portfolio_value = config.get('max_portfolio_value', 1000000)
        self.max_margin_usage = config.get('max_margin_usage', 0.8)
    
    def validate_strategy(
        self,
        strategy_name: str,
        backtest_results: Dict[str, Any],
        walk_forward_results: List[Dict[str, Any]],
        current_market_conditions: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a strategy comprehensively.
        
        Args:
            strategy_name: Name of the strategy
            backtest_results: Backtest performance metrics
            walk_forward_results: Walk-forward optimization results
            current_market_conditions: Current market conditions
            
        Returns:
            Validation result
        """
        try:
            violations = []
            warnings = []
            
            # Validate backtest results
            backtest_violations, backtest_warnings = self._validate_backtest_results(backtest_results)
            violations.extend(backtest_violations)
            warnings.extend(backtest_warnings)
            
            # Validate walk-forward results
            wf_violations, wf_warnings = self._validate_walk_forward_results(walk_forward_results)
            violations.extend(wf_violations)
            warnings.extend(wf_warnings)
            
            # Validate market conditions
            market_violations, market_warnings = self._validate_market_conditions(
                strategy_name, current_market_conditions
            )
            violations.extend(market_violations)
            warnings.extend(market_warnings)
            
            # Validate Greeks
            greek_violations, greek_warnings = self._validate_greeks(backtest_results)
            violations.extend(greek_violations)
            warnings.extend(greek_warnings)
            
            # Validate capacity
            capacity_violations, capacity_warnings = self._validate_capacity(backtest_results)
            violations.extend(capacity_violations)
            warnings.extend(capacity_warnings)
            
            # Calculate validation score
            score = self._calculate_validation_score(backtest_results, walk_forward_results)
            
            # Determine if strategy is valid
            is_valid = len(violations) == 0
            
            result = ValidationResult(
                is_valid=is_valid,
                violations=violations,
                warnings=warnings,
                score=score
            )
            
            logger.info(f"Strategy {strategy_name} validation: {'PASSED' if is_valid else 'FAILED'}")
            if violations:
                logger.warning(f"Violations: {violations}")
            if warnings:
                logger.info(f"Warnings: {warnings}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating strategy {strategy_name}: {e}")
            return ValidationResult(
                is_valid=False,
                violations=[f"Validation error: {e}"],
                warnings=[],
                score=0.0
            )
    
    def _validate_backtest_results(self, backtest_results: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate backtest results."""
        violations = []
        warnings = []
        
        # Check annual return
        annual_return = backtest_results.get('annualized_return', 0.0)
        if annual_return < self.min_annual_return:
            violations.append(f"Annual return {annual_return:.2%} below minimum {self.min_annual_return:.2%}")
        elif annual_return < self.min_annual_return * 1.2:
            warnings.append(f"Annual return {annual_return:.2%} close to minimum {self.min_annual_return:.2%}")
        
        # Check volatility
        volatility = backtest_results.get('volatility', 0.0)
        if volatility > self.max_volatility:
            violations.append(f"Volatility {volatility:.2%} above maximum {self.max_volatility:.2%}")
        elif volatility > self.max_volatility * 0.9:
            warnings.append(f"Volatility {volatility:.2%} close to maximum {self.max_volatility:.2%}")
        
        # Check max drawdown
        max_drawdown = abs(backtest_results.get('max_drawdown', 0.0))
        if max_drawdown > self.max_drawdown:
            violations.append(f"Max drawdown {max_drawdown:.2%} above maximum {self.max_drawdown:.2%}")
        elif max_drawdown > self.max_drawdown * 0.9:
            warnings.append(f"Max drawdown {max_drawdown:.2%} close to maximum {self.max_drawdown:.2%}")
        
        # Check Sharpe ratio
        sharpe_ratio = backtest_results.get('sharpe_ratio', 0.0)
        if sharpe_ratio < self.min_sharpe_ratio:
            violations.append(f"Sharpe ratio {sharpe_ratio:.2f} below minimum {self.min_sharpe_ratio:.2f}")
        elif sharpe_ratio < self.min_sharpe_ratio * 1.1:
            warnings.append(f"Sharpe ratio {sharpe_ratio:.2f} close to minimum {self.min_sharpe_ratio:.2f}")
        
        # Check profit factor
        profit_factor = backtest_results.get('profit_factor', 0.0)
        if profit_factor < self.min_profit_factor:
            violations.append(f"Profit factor {profit_factor:.2f} below minimum {self.min_profit_factor:.2f}")
        elif profit_factor < self.min_profit_factor * 1.1:
            warnings.append(f"Profit factor {profit_factor:.2f} close to minimum {self.min_profit_factor:.2f}")
        
        # Check win rate
        win_rate = backtest_results.get('win_rate', 0.0)
        if win_rate < self.min_win_rate:
            violations.append(f"Win rate {win_rate:.2%} below minimum {self.min_win_rate:.2%}")
        elif win_rate < self.min_win_rate * 1.1:
            warnings.append(f"Win rate {win_rate:.2%} close to minimum {self.min_win_rate:.2%}")
        
        # Check trade count
        total_trades = backtest_results.get('total_trades', 0)
        if total_trades < self.min_trade_count:
            violations.append(f"Trade count {total_trades} below minimum {self.min_trade_count}")
        elif total_trades < self.min_trade_count * 1.2:
            warnings.append(f"Trade count {total_trades} close to minimum {self.min_trade_count}")
        
        # Check Calmar ratio
        calmar_ratio = backtest_results.get('calmar_ratio', 0.0)
        if calmar_ratio < self.min_calmar_ratio:
            violations.append(f"Calmar ratio {calmar_ratio:.2f} below minimum {self.min_calmar_ratio:.2f}")
        elif calmar_ratio < self.min_calmar_ratio * 1.1:
            warnings.append(f"Calmar ratio {calmar_ratio:.2f} close to minimum {self.min_calmar_ratio:.2f}")
        
        # Check VaR
        var_95 = abs(backtest_results.get('var_95', 0.0))
        if var_95 > self.max_var_95:
            violations.append(f"VaR 95% {var_95:.2%} above maximum {self.max_var_95:.2%}")
        elif var_95 > self.max_var_95 * 0.9:
            warnings.append(f"VaR 95% {var_95:.2%} close to maximum {self.max_var_95:.2%}")
        
        # Check CVaR
        cvar_95 = abs(backtest_results.get('cvar_95', 0.0))
        if cvar_95 > self.max_cvar_95:
            violations.append(f"CVaR 95% {cvar_95:.2%} above maximum {self.max_cvar_95:.2%}")
        elif cvar_95 > self.max_cvar_95 * 0.9:
            warnings.append(f"CVaR 95% {cvar_95:.2%} close to maximum {self.max_cvar_95:.2%}")
        
        return violations, warnings
    
    def _validate_walk_forward_results(
        self, 
        walk_forward_results: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """Validate walk-forward results."""
        violations = []
        warnings = []
        
        if not walk_forward_results:
            violations.append("No walk-forward results available")
            return violations, warnings
        
        # Check number of periods
        if len(walk_forward_results) < 5:
            violations.append(f"Insufficient walk-forward periods: {len(walk_forward_results)}")
        elif len(walk_forward_results) < 10:
            warnings.append(f"Limited walk-forward periods: {len(walk_forward_results)}")
        
        # Check consistency across periods
        returns = [result.get('annualized_return', 0.0) for result in walk_forward_results]
        sharpe_ratios = [result.get('sharpe_ratio', 0.0) for result in walk_forward_results]
        
        # Check return consistency
        return_std = np.std(returns)
        return_mean = np.mean(returns)
        if return_mean != 0:
            return_cv = return_std / abs(return_mean)
            if return_cv > 0.5:
                violations.append(f"High return variability: CV = {return_cv:.2f}")
            elif return_cv > 0.3:
                warnings.append(f"Moderate return variability: CV = {return_cv:.2f}")
        
        # Check Sharpe ratio consistency
        sharpe_std = np.std(sharpe_ratios)
        sharpe_mean = np.mean(sharpe_ratios)
        if sharpe_mean != 0:
            sharpe_cv = sharpe_std / abs(sharpe_mean)
            if sharpe_cv > 0.5:
                violations.append(f"High Sharpe ratio variability: CV = {sharpe_cv:.2f}")
            elif sharpe_cv > 0.3:
                warnings.append(f"Moderate Sharpe ratio variability: CV = {sharpe_cv:.2f}")
        
        # Check for negative periods
        negative_periods = sum(1 for r in returns if r < 0)
        negative_pct = negative_periods / len(returns)
        if negative_pct > 0.5:
            violations.append(f"Too many negative periods: {negative_pct:.2%}")
        elif negative_pct > 0.3:
            warnings.append(f"Moderate negative periods: {negative_pct:.2%}")
        
        return violations, warnings
    
    def _validate_market_conditions(
        self,
        strategy_name: str,
        market_conditions: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """Validate market conditions."""
        violations = []
        warnings = []
        
        # Check market hours
        current_hour = datetime.now().hour
        if not (9 <= current_hour < 15):
            violations.append("Outside market hours")
        
        # Check volatility regime
        volatility = market_conditions.get('volatility', 0.0)
        if volatility > 0.4:
            violations.append(f"High volatility regime: {volatility:.2%}")
        elif volatility > 0.3:
            warnings.append(f"Elevated volatility regime: {volatility:.2%}")
        
        # Check market regime
        market_regime = market_conditions.get('market_regime', 'unknown')
        if market_regime == 'bear':
            warnings.append("Bear market regime detected")
        elif market_regime == 'crisis':
            violations.append("Crisis market regime detected")
        
        # Check time to expiry for options strategies
        if 'OPT' in strategy_name:
            time_to_expiry = market_conditions.get('time_to_expiry', 30)
            if time_to_expiry < 7:
                violations.append(f"Too close to expiry: {time_to_expiry} days")
            elif time_to_expiry < 14:
                warnings.append(f"Close to expiry: {time_to_expiry} days")
        
        return violations, warnings
    
    def _validate_greeks(self, backtest_results: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate Greeks exposure."""
        violations = []
        warnings = []
        
        # Check delta exposure
        delta_exposure = abs(backtest_results.get('delta_exposure', 0.0))
        if delta_exposure > self.max_delta_exposure:
            violations.append(f"Delta exposure {delta_exposure:.0f} above maximum {self.max_delta_exposure}")
        elif delta_exposure > self.max_delta_exposure * 0.9:
            warnings.append(f"Delta exposure {delta_exposure:.0f} close to maximum {self.max_delta_exposure}")
        
        # Check gamma exposure
        gamma_exposure = abs(backtest_results.get('gamma_exposure', 0.0))
        if gamma_exposure > self.max_gamma_exposure:
            violations.append(f"Gamma exposure {gamma_exposure:.0f} above maximum {self.max_gamma_exposure}")
        elif gamma_exposure > self.max_gamma_exposure * 0.9:
            warnings.append(f"Gamma exposure {gamma_exposure:.0f} close to maximum {self.max_gamma_exposure}")
        
        # Check theta exposure
        theta_exposure = abs(backtest_results.get('theta_exposure', 0.0))
        if theta_exposure > self.max_theta_exposure:
            violations.append(f"Theta exposure {theta_exposure:.0f} above maximum {self.max_theta_exposure}")
        elif theta_exposure > self.max_theta_exposure * 0.9:
            warnings.append(f"Theta exposure {theta_exposure:.0f} close to maximum {self.max_theta_exposure}")
        
        # Check vega exposure
        vega_exposure = abs(backtest_results.get('vega_exposure', 0.0))
        if vega_exposure > self.max_vega_exposure:
            violations.append(f"Vega exposure {vega_exposure:.0f} above maximum {self.max_vega_exposure}")
        elif vega_exposure > self.max_vega_exposure * 0.9:
            warnings.append(f"Vega exposure {vega_exposure:.0f} close to maximum {self.max_vega_exposure}")
        
        return violations, warnings
    
    def _validate_capacity(self, backtest_results: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate capacity limits."""
        violations = []
        warnings = []
        
        # Check position size
        position_size = backtest_results.get('max_position_size', 0.0)
        if position_size > self.max_position_size:
            violations.append(f"Position size {position_size:.0f} above maximum {self.max_position_size}")
        elif position_size > self.max_position_size * 0.9:
            warnings.append(f"Position size {position_size:.0f} close to maximum {self.max_position_size}")
        
        # Check portfolio value
        portfolio_value = backtest_results.get('max_portfolio_value', 0.0)
        if portfolio_value > self.max_portfolio_value:
            violations.append(f"Portfolio value {portfolio_value:.0f} above maximum {self.max_portfolio_value}")
        elif portfolio_value > self.max_portfolio_value * 0.9:
            warnings.append(f"Portfolio value {portfolio_value:.0f} close to maximum {self.max_portfolio_value}")
        
        # Check margin usage
        margin_usage = backtest_results.get('margin_usage', 0.0)
        if margin_usage > self.max_margin_usage:
            violations.append(f"Margin usage {margin_usage:.2%} above maximum {self.max_margin_usage:.2%}")
        elif margin_usage > self.max_margin_usage * 0.9:
            warnings.append(f"Margin usage {margin_usage:.2%} close to maximum {self.max_margin_usage:.2%}")
        
        return violations, warnings
    
    def _calculate_validation_score(
        self,
        backtest_results: Dict[str, Any],
        walk_forward_results: List[Dict[str, Any]]
    ) -> float:
        """Calculate validation score."""
        try:
            score = 1.0
            
            # Penalize for violations
            annual_return = backtest_results.get('annualized_return', 0.0)
            if annual_return < self.min_annual_return:
                score -= 0.3
            
            volatility = backtest_results.get('volatility', 0.0)
            if volatility > self.max_volatility:
                score -= 0.2
            
            max_drawdown = abs(backtest_results.get('max_drawdown', 0.0))
            if max_drawdown > self.max_drawdown:
                score -= 0.2
            
            sharpe_ratio = backtest_results.get('sharpe_ratio', 0.0)
            if sharpe_ratio < self.min_sharpe_ratio:
                score -= 0.1
            
            profit_factor = backtest_results.get('profit_factor', 0.0)
            if profit_factor < self.min_profit_factor:
                score -= 0.1
            
            win_rate = backtest_results.get('win_rate', 0.0)
            if win_rate < self.min_win_rate:
                score -= 0.1
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating validation score: {e}")
            return 0.0
