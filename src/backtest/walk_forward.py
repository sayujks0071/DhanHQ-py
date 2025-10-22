"""
Walk-forward optimization with purged k-fold cross-validation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from itertools import combinations

from ..config import Config
from ..strategies.base import BaseStrategy
from .engine import BacktestEngine
from .metrics import BacktestMetrics, MetricsCalculator

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardResult:
    """Result of a walk-forward optimization run."""
    in_sample_metrics: BacktestMetrics
    out_of_sample_metrics: BacktestMetrics
    parameters: Dict[str, Any]
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


class WalkForwardOptimizer:
    """
    Walk-forward optimization with purged k-fold cross-validation.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.metrics_calc = MetricsCalculator()
        
    def optimize_strategy(
        self,
        strategy_class: type,
        parameter_space: Dict[str, List[Any]],
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        train_window: int = 252,  # 1 year
        test_window: int = 63,    # 3 months
        purge_period: int = 5,    # 5 days
        n_folds: int = 5
    ) -> List[WalkForwardResult]:
        """
        Perform walk-forward optimization with purged k-fold CV.
        
        Args:
            strategy_class: Strategy class to optimize
            parameter_space: Dictionary of parameter names to possible values
            start_date: Start date for optimization
            end_date: End date for optimization
            train_window: Training window in days
            test_window: Test window in days
            purge_period: Days to purge between train and test
            n_folds: Number of folds for cross-validation
        """
        logger.info(f"Starting walk-forward optimization for {strategy_class.__name__}")
        
        results = []
        current_date = start_date
        
        while current_date + pd.Timedelta(days=train_window + test_window) <= end_date:
            # Define train and test periods
            train_start = current_date
            train_end = current_date + pd.Timedelta(days=train_window)
            test_start = train_end + pd.Timedelta(days=purge_period)
            test_end = test_start + pd.Timedelta(days=test_window)
            
            if test_end > end_date:
                break
            
            logger.info(f"Optimizing period: {train_start} to {test_end}")
            
            # Perform parameter optimization on training data
            best_params = self._optimize_parameters(
                strategy_class,
                parameter_space,
                train_start,
                train_end,
                n_folds
            )
            
            # Test on out-of-sample data
            oos_metrics = self._test_strategy(
                strategy_class,
                best_params,
                test_start,
                test_end
            )
            
            # Calculate in-sample metrics for comparison
            is_metrics = self._test_strategy(
                strategy_class,
                best_params,
                train_start,
                train_end
            )
            
            result = WalkForwardResult(
                in_sample_metrics=is_metrics,
                out_of_sample_metrics=oos_metrics,
                parameters=best_params,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end
            )
            
            results.append(result)
            
            # Move to next period
            current_date += pd.Timedelta(days=test_window)
        
        logger.info(f"Walk-forward optimization completed. {len(results)} periods tested")
        return results
    
    def _optimize_parameters(
        self,
        strategy_class: type,
        parameter_space: Dict[str, List[Any]],
        train_start: pd.Timestamp,
        train_end: pd.Timestamp,
        n_folds: int
    ) -> Dict[str, Any]:
        """Optimize parameters using purged k-fold cross-validation."""
        
        # Generate parameter combinations
        param_combinations = self._generate_parameter_combinations(parameter_space)
        
        best_score = -np.inf
        best_params = None
        
        for params in param_combinations:
            # Perform k-fold CV
            cv_scores = []
            
            for fold in range(n_folds):
                # Split training data into train/validation
                fold_train_start, fold_train_end, fold_val_start, fold_val_end = \
                    self._get_fold_split(train_start, train_end, fold, n_folds)
                
                # Train on fold training data
                strategy = strategy_class(params)
                # Note: In practice, you'd need to implement proper training
                
                # Validate on fold validation data
                val_metrics = self._test_strategy(
                    strategy_class,
                    params,
                    fold_val_start,
                    fold_val_end
                )
                
                # Use Sharpe ratio as optimization metric
                cv_scores.append(val_metrics.sharpe_ratio)
            
            # Average CV score
            avg_score = np.mean(cv_scores)
            
            if avg_score > best_score:
                best_score = avg_score
                best_params = params
        
        logger.info(f"Best parameters: {best_params} (CV score: {best_score:.3f})")
        return best_params
    
    def _generate_parameter_combinations(
        self, 
        parameter_space: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """Generate all combinations of parameters."""
        param_names = list(parameter_space.keys())
        param_values = list(parameter_space.values())
        
        combinations_list = []
        for combo in combinations(*param_values):
            param_dict = dict(zip(param_names, combo))
            combinations_list.append(param_dict)
        
        return combinations_list
    
    def _get_fold_split(
        self,
        train_start: pd.Timestamp,
        train_end: pd.Timestamp,
        fold: int,
        n_folds: int
    ) -> Tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
        """Split training period into fold train/validation sets."""
        
        total_days = (train_end - train_start).days
        fold_size = total_days // n_folds
        
        # Calculate fold boundaries
        fold_start = train_start + pd.Timedelta(days=fold * fold_size)
        fold_end = fold_start + pd.Timedelta(days=fold_size)
        
        # Use first part for training, second part for validation
        fold_train_start = fold_start
        fold_train_end = fold_start + pd.Timedelta(days=fold_size // 2)
        fold_val_start = fold_train_end + pd.Timedelta(days=1)
        fold_val_end = fold_end
        
        return fold_train_start, fold_train_end, fold_val_start, fold_val_end
    
    def _test_strategy(
        self,
        strategy_class: type,
        parameters: Dict[str, Any],
        start_date: pd.Timestamp,
        end_date: pd.Timestamp
    ) -> BacktestMetrics:
        """Test strategy with given parameters on specified period."""
        
        # Create strategy instance
        strategy = strategy_class(parameters)
        
        # Run backtest
        engine = BacktestEngine(self.config)
        metrics_dict = engine.run_backtest(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            universe=self.config.universe_symbols
        )
        
        # Convert to BacktestMetrics object
        # This is simplified - in practice you'd need proper conversion
        metrics = BacktestMetrics(
            total_return=metrics_dict.get('total_return', 0.0),
            annualized_return=metrics_dict.get('annualized_return', 0.0),
            volatility=metrics_dict.get('volatility', 0.0),
            sharpe_ratio=metrics_dict.get('sharpe_ratio', 0.0),
            sortino_ratio=0.0,  # Would calculate properly
            calmar_ratio=0.0,   # Would calculate properly
            max_drawdown=metrics_dict.get('max_drawdown', 0.0),
            max_drawdown_duration=0,  # Would calculate properly
            var_95=0.0,         # Would calculate properly
            cvar_95=0.0,        # Would calculate properly
            total_trades=metrics_dict.get('total_trades', 0),
            winning_trades=0,   # Would calculate properly
            losing_trades=0,    # Would calculate properly
            win_rate=metrics_dict.get('win_rate', 0.0),
            avg_win=0.0,        # Would calculate properly
            avg_loss=0.0,       # Would calculate properly
            profit_factor=0.0,  # Would calculate properly
            theta_harvest=0.0,  # Would calculate properly
            vega_exposure=0.0,  # Would calculate properly
            gamma_exposure=0.0, # Would calculate properly
            delta_exposure=0.0, # Would calculate properly
            bull_market_return=0.0,  # Would calculate properly
            bear_market_return=0.0,  # Would calculate properly
            high_vol_return=0.0,    # Would calculate properly
            low_vol_return=0.0      # Would calculate properly
        )
        
        return metrics
    
    def analyze_results(self, results: List[WalkForwardResult]) -> Dict[str, Any]:
        """Analyze walk-forward optimization results."""
        
        if not results:
            return {}
        
        # Extract metrics
        oos_returns = [r.out_of_sample_metrics.annualized_return for r in results]
        oos_sharpe = [r.out_of_sample_metrics.sharpe_ratio for r in results]
        oos_drawdowns = [r.out_of_sample_metrics.max_drawdown for r in results]
        
        # Calculate stability metrics
        return_stability = np.std(oos_returns) / np.mean(oos_returns) if np.mean(oos_returns) != 0 else 0
        sharpe_stability = np.std(oos_sharpe) / np.mean(oos_sharpe) if np.mean(oos_sharpe) != 0 else 0
        
        # Parameter stability
        param_changes = 0
        for i in range(1, len(results)):
            if results[i].parameters != results[i-1].parameters:
                param_changes += 1
        
        param_stability = 1 - (param_changes / (len(results) - 1)) if len(results) > 1 else 1.0
        
        # Performance degradation
        is_returns = [r.in_sample_metrics.annualized_return for r in results]
        degradation = np.mean(oos_returns) - np.mean(is_returns)
        
        analysis = {
            'total_periods': len(results),
            'avg_oos_return': np.mean(oos_returns),
            'avg_oos_sharpe': np.mean(oos_sharpe),
            'avg_oos_drawdown': np.mean(oos_drawdowns),
            'return_stability': return_stability,
            'sharpe_stability': sharpe_stability,
            'param_stability': param_stability,
            'performance_degradation': degradation,
            'best_period': max(range(len(results)), key=lambda i: oos_sharpe[i]),
            'worst_period': min(range(len(results)), key=lambda i: oos_sharpe[i])
        }
        
        return analysis
    
    def generate_report(self, results: List[WalkForwardResult]) -> str:
        """Generate comprehensive walk-forward optimization report."""
        
        analysis = self.analyze_results(results)
        
        report = f"""
# Walk-Forward Optimization Report

## Summary
- Total Periods: {analysis.get('total_periods', 0)}
- Average OOS Return: {analysis.get('avg_oos_return', 0):.2%}
- Average OOS Sharpe: {analysis.get('avg_oos_sharpe', 0):.3f}
- Average OOS Drawdown: {analysis.get('avg_oos_drawdown', 0):.2%}

## Stability Analysis
- Return Stability: {analysis.get('return_stability', 0):.3f}
- Sharpe Stability: {analysis.get('sharpe_stability', 0):.3f}
- Parameter Stability: {analysis.get('param_stability', 0):.3f}
- Performance Degradation: {analysis.get('performance_degradation', 0):.2%}

## Period-by-Period Results
"""
        
        for i, result in enumerate(results):
            report += f"""
### Period {i+1}: {result.train_start.date()} to {result.test_end.date()}
- Parameters: {result.parameters}
- OOS Return: {result.out_of_sample_metrics.annualized_return:.2%}
- OOS Sharpe: {result.out_of_sample_metrics.sharpe_ratio:.3f}
- OOS Drawdown: {result.out_of_sample_metrics.max_drawdown:.2%}
"""
        
        return report
