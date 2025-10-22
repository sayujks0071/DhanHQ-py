"""
Comprehensive risk management system.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from ..config import Config
from ..options.greeks import GreeksCalculator

logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """Risk limits configuration."""
    max_position_size: float
    max_portfolio_value: float
    max_daily_loss: float
    max_drawdown: float
    max_delta_exposure: float
    max_gamma_exposure: float
    max_theta_exposure: float
    max_vega_exposure: float
    max_margin_usage: float
    max_concurrent_positions: int
    max_sector_exposure: float
    max_underlying_exposure: float


@dataclass
class RiskMetrics:
    """Current risk metrics."""
    portfolio_value: float
    total_delta: float
    total_gamma: float
    total_theta: float
    total_vega: float
    margin_used: float
    margin_available: float
    daily_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    current_drawdown: float
    max_drawdown: float
    position_count: int
    sector_exposures: Dict[str, float]
    underlying_exposures: Dict[str, float]


class RiskManager:
    """
    Comprehensive risk management system for F&O trading.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.greeks_calc = GreeksCalculator()
        
        # Risk limits from config
        self.limits = RiskLimits(
            max_position_size=config.max_position_size,
            max_portfolio_value=config.max_portfolio_value,
            max_daily_loss=config.max_daily_loss,
            max_drawdown=config.max_drawdown,
            max_delta_exposure=config.max_delta_exposure,
            max_gamma_exposure=config.max_gamma_exposure,
            max_theta_exposure=config.max_theta_exposure,
            max_vega_exposure=config.max_vega_exposure,
            max_margin_usage=config.max_margin_usage,
            max_concurrent_positions=config.max_concurrent_positions,
            max_sector_exposure=config.max_sector_exposure,
            max_underlying_exposure=config.max_underlying_exposure
        )
        
        # Risk tracking
        self.daily_pnl_history = []
        self.peak_portfolio_value = config.initial_capital
        self.max_drawdown_observed = 0.0
        
    def check_limits(
        self,
        positions: Dict[str, Any],
        cash: float,
        margin_used: float,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Check all risk limits and return status with violations.
        
        Returns:
            (is_safe, violations): Tuple of safety status and list of violations
        """
        violations = []
        
        # Calculate current risk metrics
        risk_metrics = self._calculate_risk_metrics(positions, cash, margin_used, market_data)
        
        # Check individual limits
        if not self._check_position_size_limits(positions, risk_metrics):
            violations.append("Position size limits exceeded")
        
        if not self._check_portfolio_limits(risk_metrics):
            violations.append("Portfolio limits exceeded")
        
        if not self._check_daily_loss_limits(risk_metrics):
            violations.append("Daily loss limits exceeded")
        
        if not self._check_drawdown_limits(risk_metrics):
            violations.append("Drawdown limits exceeded")
        
        if not self._check_greeks_limits(risk_metrics):
            violations.append("Greeks limits exceeded")
        
        if not self._check_margin_limits(risk_metrics):
            violations.append("Margin limits exceeded")
        
        if not self._check_position_count_limits(risk_metrics):
            violations.append("Position count limits exceeded")
        
        if not self._check_sector_exposure_limits(risk_metrics):
            violations.append("Sector exposure limits exceeded")
        
        if not self._check_underlying_exposure_limits(risk_metrics):
            violations.append("Underlying exposure limits exceeded")
        
        is_safe = len(violations) == 0
        
        if not is_safe:
            logger.warning(f"Risk limit violations: {violations}")
        
        return is_safe, violations
    
    def _calculate_risk_metrics(
        self,
        positions: Dict[str, Any],
        cash: float,
        margin_used: float,
        market_data: Optional[Dict[str, Any]] = None
    ) -> RiskMetrics:
        """Calculate comprehensive risk metrics."""
        
        # Calculate portfolio value
        portfolio_value = cash
        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0
        unrealized_pnl = 0.0
        sector_exposures = {}
        underlying_exposures = {}
        
        for symbol, position in positions.items():
            if market_data and symbol in market_data:
                current_price = market_data[symbol].get('close', 0)
                position_value = position.quantity * current_price
                portfolio_value += position_value
                
                # Calculate unrealized P&L
                unrealized_pnl += (current_price - position.avg_price) * position.quantity
                
                # Calculate Greeks (simplified)
                if 'OPT' in symbol:
                    # Options Greeks calculation
                    greeks = self._calculate_position_greeks(symbol, position, market_data[symbol])
                    total_delta += greeks['delta'] * position.quantity
                    total_gamma += greeks['gamma'] * position.quantity
                    total_theta += greeks['theta'] * position.quantity
                    total_vega += greeks['vega'] * position.quantity
                
                # Calculate sector and underlying exposures
                sector = self._get_sector(symbol)
                underlying = self._get_underlying(symbol)
                
                if sector:
                    sector_exposures[sector] = sector_exposures.get(sector, 0) + position_value
                if underlying:
                    underlying_exposures[underlying] = underlying_exposures.get(underlying, 0) + position_value
        
        # Calculate daily P&L
        daily_pnl = self._calculate_daily_pnl()
        
        # Calculate drawdown
        current_drawdown, max_drawdown = self._calculate_drawdown(portfolio_value)
        
        return RiskMetrics(
            portfolio_value=portfolio_value,
            total_delta=total_delta,
            total_gamma=total_gamma,
            total_theta=total_theta,
            total_vega=total_vega,
            margin_used=margin_used,
            margin_available=self.config.initial_capital - margin_used,
            daily_pnl=daily_pnl,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=0.0,  # Would track from fills
            current_drawdown=current_drawdown,
            max_drawdown=max_drawdown,
            position_count=len(positions),
            sector_exposures=sector_exposures,
            underlying_exposures=underlying_exposures
        )
    
    def _calculate_position_greeks(
        self, 
        symbol: str, 
        position: Any, 
        market_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate Greeks for a position."""
        # This would integrate with your options engine
        # For now, return placeholder values
        return {
            'delta': 0.0,
            'gamma': 0.0,
            'theta': 0.0,
            'vega': 0.0
        }
    
    def _get_sector(self, symbol: str) -> Optional[str]:
        """Get sector for a symbol."""
        # This would integrate with your instrument master
        # For now, return placeholder
        return None
    
    def _get_underlying(self, symbol: str) -> Optional[str]:
        """Get underlying for a symbol."""
        # This would integrate with your instrument master
        # For now, return placeholder
        return None
    
    def _calculate_daily_pnl(self) -> float:
        """Calculate daily P&L."""
        if not self.daily_pnl_history:
            return 0.0
        
        # Return today's P&L (simplified)
        return self.daily_pnl_history[-1] if self.daily_pnl_history else 0.0
    
    def _calculate_drawdown(self, current_value: float) -> Tuple[float, float]:
        """Calculate current and maximum drawdown."""
        if current_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_value
        
        current_drawdown = (self.peak_portfolio_value - current_value) / self.peak_portfolio_value
        self.max_drawdown_observed = max(self.max_drawdown_observed, current_drawdown)
        
        return current_drawdown, self.max_drawdown_observed
    
    def _check_position_size_limits(
        self, 
        positions: Dict[str, Any], 
        risk_metrics: RiskMetrics
    ) -> bool:
        """Check position size limits."""
        for symbol, position in positions.items():
            position_value = abs(position.quantity * position.avg_price)
            if position_value > self.limits.max_position_size:
                return False
        return True
    
    def _check_portfolio_limits(self, risk_metrics: RiskMetrics) -> bool:
        """Check portfolio-level limits."""
        if risk_metrics.portfolio_value > self.limits.max_portfolio_value:
            return False
        return True
    
    def _check_daily_loss_limits(self, risk_metrics: RiskMetrics) -> bool:
        """Check daily loss limits."""
        if risk_metrics.daily_pnl < -self.limits.max_daily_loss:
            return False
        return True
    
    def _check_drawdown_limits(self, risk_metrics: RiskMetrics) -> bool:
        """Check drawdown limits."""
        if risk_metrics.current_drawdown > self.limits.max_drawdown:
            return False
        return True
    
    def _check_greeks_limits(self, risk_metrics: RiskMetrics) -> bool:
        """Check Greeks exposure limits."""
        if abs(risk_metrics.total_delta) > self.limits.max_delta_exposure:
            return False
        if abs(risk_metrics.total_gamma) > self.limits.max_gamma_exposure:
            return False
        if abs(risk_metrics.total_theta) > self.limits.max_theta_exposure:
            return False
        if abs(risk_metrics.total_vega) > self.limits.max_vega_exposure:
            return False
        return True
    
    def _check_margin_limits(self, risk_metrics: RiskMetrics) -> bool:
        """Check margin usage limits."""
        margin_usage = risk_metrics.margin_used / self.config.initial_capital
        if margin_usage > self.limits.max_margin_usage:
            return False
        return True
    
    def _check_position_count_limits(self, risk_metrics: RiskMetrics) -> bool:
        """Check position count limits."""
        if risk_metrics.position_count > self.limits.max_concurrent_positions:
            return False
        return True
    
    def _check_sector_exposure_limits(self, risk_metrics: RiskMetrics) -> bool:
        """Check sector exposure limits."""
        for sector, exposure in risk_metrics.sector_exposures.items():
            sector_pct = exposure / risk_metrics.portfolio_value
            if sector_pct > self.limits.max_sector_exposure:
                return False
        return True
    
    def _check_underlying_exposure_limits(self, risk_metrics: RiskMetrics) -> bool:
        """Check underlying exposure limits."""
        for underlying, exposure in risk_metrics.underlying_exposures.items():
            underlying_pct = exposure / risk_metrics.portfolio_value
            if underlying_pct > self.limits.max_underlying_exposure:
                return False
        return True
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L history."""
        self.daily_pnl_history.append(pnl)
        
        # Keep only last 30 days
        if len(self.daily_pnl_history) > 30:
            self.daily_pnl_history = self.daily_pnl_history[-30:]
    
    def get_risk_summary(self, risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """Get comprehensive risk summary."""
        return {
            'portfolio_value': risk_metrics.portfolio_value,
            'total_delta': risk_metrics.total_delta,
            'total_gamma': risk_metrics.total_gamma,
            'total_theta': risk_metrics.total_theta,
            'total_vega': risk_metrics.total_vega,
            'margin_usage': risk_metrics.margin_used / self.config.initial_capital,
            'current_drawdown': risk_metrics.current_drawdown,
            'max_drawdown': risk_metrics.max_drawdown,
            'position_count': risk_metrics.position_count,
            'daily_pnl': risk_metrics.daily_pnl,
            'unrealized_pnl': risk_metrics.unrealized_pnl
        }
    
    def should_stop_trading(self, risk_metrics: RiskMetrics) -> bool:
        """Determine if trading should be stopped due to risk."""
        # Stop if any critical limits are breached
        critical_violations = [
            risk_metrics.current_drawdown > self.limits.max_drawdown,
            risk_metrics.daily_pnl < -self.limits.max_daily_loss,
            risk_metrics.margin_used / self.config.initial_capital > self.limits.max_margin_usage
        ]
        
        return any(critical_violations)
