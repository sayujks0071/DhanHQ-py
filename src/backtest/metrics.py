"""
Comprehensive backtesting metrics calculation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestMetrics:
    """Container for backtest performance metrics."""
    
    # Return metrics
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_duration: int
    var_95: float
    cvar_95: float
    
    # Trade metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # Options-specific metrics
    theta_harvest: float
    vega_exposure: float
    gamma_exposure: float
    delta_exposure: float
    
    # Regime analysis
    bull_market_return: float
    bear_market_return: float
    high_vol_return: float
    low_vol_return: float


class MetricsCalculator:
    """Calculate comprehensive backtest metrics."""
    
    def __init__(self):
        self.risk_free_rate = 0.06  # 6% risk-free rate for India
    
    def calculate_metrics(
        self,
        equity_curve: pd.Series,
        fills: List[Dict[str, Any]],
        positions: Dict[str, Any],
        benchmark_return: Optional[float] = None
    ) -> BacktestMetrics:
        """
        Calculate comprehensive backtest metrics.
        
        Args:
            equity_curve: Portfolio equity over time
            fills: List of trade fills
            positions: Current positions
            benchmark_return: Benchmark annualized return for comparison
        """
        returns = equity_curve.pct_change().dropna()
        
        # Basic return metrics
        total_return = (equity_curve.iloc[-1] - equity_curve.iloc[0]) / equity_curve.iloc[0]
        annualized_return = self._calculate_annualized_return(returns)
        volatility = returns.std() * np.sqrt(252)
        
        # Risk-adjusted metrics
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        sortino_ratio = self._calculate_sortino_ratio(returns)
        calmar_ratio = self._calculate_calmar_ratio(annualized_return, equity_curve)
        
        # Risk metrics
        max_dd, max_dd_duration = self._calculate_max_drawdown(equity_curve)
        var_95, cvar_95 = self._calculate_var_cvar(returns)
        
        # Trade metrics
        trade_metrics = self._calculate_trade_metrics(fills)
        
        # Options-specific metrics
        options_metrics = self._calculate_options_metrics(positions)
        
        # Regime analysis
        regime_metrics = self._calculate_regime_metrics(returns, equity_curve)
        
        return BacktestMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_dd,
            max_drawdown_duration=max_dd_duration,
            var_95=var_95,
            cvar_95=cvar_95,
            **trade_metrics,
            **options_metrics,
            **regime_metrics
        )
    
    def _calculate_annualized_return(self, returns: pd.Series) -> float:
        """Calculate annualized return."""
        if len(returns) == 0:
            return 0.0
        
        total_days = len(returns)
        years = total_days / 252
        return (1 + returns.mean()) ** 252 - 1 if years > 0 else 0.0
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio."""
        if returns.std() == 0:
            return 0.0
        
        excess_return = returns.mean() - self.risk_free_rate / 252
        return excess_return / returns.std() * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio (downside deviation)."""
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        excess_return = returns.mean() - self.risk_free_rate / 252
        downside_std = downside_returns.std() * np.sqrt(252)
        return excess_return / downside_std
    
    def _calculate_calmar_ratio(self, annualized_return: float, equity_curve: pd.Series) -> float:
        """Calculate Calmar ratio (return / max drawdown)."""
        max_dd, _ = self._calculate_max_drawdown(equity_curve)
        if max_dd == 0:
            return 0.0
        return annualized_return / abs(max_dd)
    
    def _calculate_max_drawdown(self, equity_curve: pd.Series) -> tuple[float, int]:
        """Calculate maximum drawdown and duration."""
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        
        max_dd = drawdown.min()
        
        # Calculate max drawdown duration
        in_drawdown = drawdown < 0
        drawdown_periods = []
        current_period = 0
        
        for is_dd in in_drawdown:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                    current_period = 0
        
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        max_dd_duration = max(drawdown_periods) if drawdown_periods else 0
        
        return max_dd, max_dd_duration
    
    def _calculate_var_cvar(self, returns: pd.Series) -> tuple[float, float]:
        """Calculate Value at Risk (VaR) and Conditional VaR (CVaR) at 95% confidence."""
        if len(returns) == 0:
            return 0.0, 0.0
        
        var_95 = np.percentile(returns, 5)  # 5th percentile for 95% VaR
        cvar_95 = returns[returns <= var_95].mean()  # Expected value below VaR
        
        return var_95, cvar_95
    
    def _calculate_trade_metrics(self, fills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trade-level metrics."""
        if not fills:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0
            }
        
        # Group fills by trade (simplified - would need proper trade matching)
        trades = self._group_fills_by_trade(fills)
        
        total_trades = len(trades)
        winning_trades = sum(1 for trade in trades if trade['pnl'] > 0)
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        wins = [trade['pnl'] for trade in trades if trade['pnl'] > 0]
        losses = [trade['pnl'] for trade in trades if trade['pnl'] < 0]
        
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        
        total_wins = sum(wins) if wins else 0.0
        total_losses = abs(sum(losses)) if losses else 0.0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }
    
    def _group_fills_by_trade(self, fills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group fills by trade and calculate P&L."""
        # Simplified implementation - would need proper trade matching logic
        trades = []
        
        # For now, assume each fill is a complete trade
        for fill in fills:
            trades.append({
                'symbol': fill.get('symbol', ''),
                'pnl': fill.get('pnl', 0.0),
                'entry_time': fill.get('timestamp'),
                'exit_time': fill.get('timestamp')
            })
        
        return trades
    
    def _calculate_options_metrics(self, positions: Dict[str, Any]) -> Dict[str, float]:
        """Calculate options-specific metrics."""
        # This would integrate with your options engine
        # For now, return placeholder values
        return {
            'theta_harvest': 0.0,
            'vega_exposure': 0.0,
            'gamma_exposure': 0.0,
            'delta_exposure': 0.0
        }
    
    def _calculate_regime_metrics(
        self, 
        returns: pd.Series, 
        equity_curve: pd.Series
    ) -> Dict[str, float]:
        """Calculate performance in different market regimes."""
        # Simplified regime analysis
        # In practice, you'd use more sophisticated regime detection
        
        # Bull vs Bear (simplified using rolling returns)
        rolling_returns = returns.rolling(20).mean()
        bull_periods = rolling_returns > 0
        bear_periods = rolling_returns < 0
        
        bull_return = returns[bull_periods].mean() * 252 if bull_periods.any() else 0.0
        bear_return = returns[bear_periods].mean() * 252 if bear_periods.any() else 0.0
        
        # High vs Low volatility
        rolling_vol = returns.rolling(20).std()
        vol_median = rolling_vol.median()
        high_vol_periods = rolling_vol > vol_median
        low_vol_periods = rolling_vol <= vol_median
        
        high_vol_return = returns[high_vol_periods].mean() * 252 if high_vol_periods.any() else 0.0
        low_vol_return = returns[low_vol_periods].mean() * 252 if low_vol_periods.any() else 0.0
        
        return {
            'bull_market_return': bull_return,
            'bear_market_return': bear_return,
            'high_vol_return': high_vol_return,
            'low_vol_return': low_vol_return
        }
    
    def generate_report(self, metrics: BacktestMetrics) -> str:
        """Generate a comprehensive backtest report."""
        report = f"""
# Backtest Performance Report

## Return Metrics
- Total Return: {metrics.total_return:.2%}
- Annualized Return: {metrics.annualized_return:.2%}
- Volatility: {metrics.volatility:.2%}
- Sharpe Ratio: {metrics.sharpe_ratio:.2f}
- Sortino Ratio: {metrics.sortino_ratio:.2f}
- Calmar Ratio: {metrics.calmar_ratio:.2f}

## Risk Metrics
- Maximum Drawdown: {metrics.max_drawdown:.2%}
- Max DD Duration: {metrics.max_drawdown_duration} days
- VaR (95%): {metrics.var_95:.2%}
- CVaR (95%): {metrics.cvar_95:.2%}

## Trade Metrics
- Total Trades: {metrics.total_trades}
- Win Rate: {metrics.win_rate:.2%}
- Average Win: {metrics.avg_win:.2f}
- Average Loss: {metrics.avg_loss:.2f}
- Profit Factor: {metrics.profit_factor:.2f}

## Options Metrics
- Theta Harvest: {metrics.theta_harvest:.2f}
- Vega Exposure: {metrics.vega_exposure:.2f}
- Gamma Exposure: {metrics.gamma_exposure:.2f}
- Delta Exposure: {metrics.delta_exposure:.2f}

## Regime Analysis
- Bull Market Return: {metrics.bull_market_return:.2%}
- Bear Market Return: {metrics.bear_market_return:.2%}
- High Vol Return: {metrics.high_vol_return:.2%}
- Low Vol Return: {metrics.low_vol_return:.2%}
"""
        return report
