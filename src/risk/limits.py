"""
Risk limits configuration and validation.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PositionLimit:
    """Position-specific risk limits."""
    symbol: str
    max_quantity: int
    max_value: float
    max_delta: float
    max_gamma: float
    max_theta: float
    max_vega: float


@dataclass
class SectorLimit:
    """Sector-specific risk limits."""
    sector: str
    max_exposure: float
    max_delta: float
    max_gamma: float
    max_theta: float
    max_vega: float


@dataclass
class UnderlyingLimit:
    """Underlying-specific risk limits."""
    underlying: str
    max_exposure: float
    max_delta: float
    max_gamma: float
    max_theta: float
    max_vega: float


class RiskLimitsValidator:
    """Validates risk limits configuration."""
    
    def __init__(self):
        self.required_limits = [
            'max_position_size',
            'max_portfolio_value',
            'max_daily_loss',
            'max_drawdown',
            'max_delta_exposure',
            'max_gamma_exposure',
            'max_theta_exposure',
            'max_vega_exposure',
            'max_margin_usage',
            'max_concurrent_positions',
            'max_sector_exposure',
            'max_underlying_exposure'
        ]
    
    def validate_limits(self, limits_config: Dict[str, Any]) -> List[str]:
        """
        Validate risk limits configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required limits
        for limit in self.required_limits:
            if limit not in limits_config:
                errors.append(f"Missing required limit: {limit}")
            elif not isinstance(limits_config[limit], (int, float)):
                errors.append(f"Invalid type for limit {limit}: {type(limits_config[limit])}")
            elif limits_config[limit] <= 0:
                errors.append(f"Invalid value for limit {limit}: {limits_config[limit]}")
        
        # Check logical consistency
        if 'max_position_size' in limits_config and 'max_portfolio_value' in limits_config:
            if limits_config['max_position_size'] > limits_config['max_portfolio_value']:
                errors.append("max_position_size cannot be greater than max_portfolio_value")
        
        if 'max_daily_loss' in limits_config and 'max_portfolio_value' in limits_config:
            if limits_config['max_daily_loss'] > limits_config['max_portfolio_value']:
                errors.append("max_daily_loss cannot be greater than max_portfolio_value")
        
        if 'max_drawdown' in limits_config:
            if limits_config['max_drawdown'] > 1.0:
                errors.append("max_drawdown cannot be greater than 100%")
        
        if 'max_margin_usage' in limits_config:
            if limits_config['max_margin_usage'] > 1.0:
                errors.append("max_margin_usage cannot be greater than 100%")
        
        return errors
    
    def validate_position_limits(self, position_limits: List[PositionLimit]) -> List[str]:
        """Validate position-specific limits."""
        errors = []
        
        for limit in position_limits:
            if limit.max_quantity <= 0:
                errors.append(f"Invalid max_quantity for {limit.symbol}: {limit.max_quantity}")
            
            if limit.max_value <= 0:
                errors.append(f"Invalid max_value for {limit.symbol}: {limit.max_value}")
            
            if abs(limit.max_delta) > 1.0:
                errors.append(f"Invalid max_delta for {limit.symbol}: {limit.max_delta}")
        
        return errors
    
    def validate_sector_limits(self, sector_limits: List[SectorLimit]) -> List[str]:
        """Validate sector-specific limits."""
        errors = []
        
        for limit in sector_limits:
            if limit.max_exposure <= 0 or limit.max_exposure > 1.0:
                errors.append(f"Invalid max_exposure for sector {limit.sector}: {limit.max_exposure}")
        
        return errors
    
    def validate_underlying_limits(self, underlying_limits: List[UnderlyingLimit]) -> List[str]:
        """Validate underlying-specific limits."""
        errors = []
        
        for limit in underlying_limits:
            if limit.max_exposure <= 0 or limit.max_exposure > 1.0:
                errors.append(f"Invalid max_exposure for underlying {limit.underlying}: {limit.max_exposure}")
        
        return errors


class DynamicRiskLimits:
    """Dynamic risk limits that adjust based on market conditions."""
    
    def __init__(self, base_limits: Dict[str, Any]):
        self.base_limits = base_limits
        self.current_limits = base_limits.copy()
    
    def update_limits(self, market_conditions: Dict[str, Any]):
        """Update limits based on market conditions."""
        
        # Volatility adjustment
        if 'volatility' in market_conditions:
            vol = market_conditions['volatility']
            if vol > 0.3:  # High volatility
                self.current_limits['max_position_size'] *= 0.5
                self.current_limits['max_delta_exposure'] *= 0.7
                self.current_limits['max_gamma_exposure'] *= 0.5
            elif vol < 0.15:  # Low volatility
                self.current_limits['max_position_size'] *= 1.2
                self.current_limits['max_delta_exposure'] *= 1.1
        
        # Market regime adjustment
        if 'market_regime' in market_conditions:
            regime = market_conditions['market_regime']
            if regime == 'bear':
                self.current_limits['max_daily_loss'] *= 0.5
                self.current_limits['max_drawdown'] *= 0.7
            elif regime == 'bull':
                self.current_limits['max_position_size'] *= 1.1
                self.current_limits['max_delta_exposure'] *= 1.1
        
        # Time-based adjustment
        if 'time_to_expiry' in market_conditions:
            tte = market_conditions['time_to_expiry']
            if tte < 7:  # Less than 1 week to expiry
                self.current_limits['max_theta_exposure'] *= 0.5
                self.current_limits['max_gamma_exposure'] *= 0.7
    
    def get_current_limits(self) -> Dict[str, Any]:
        """Get current risk limits."""
        return self.current_limits.copy()
    
    def reset_to_base(self):
        """Reset to base limits."""
        self.current_limits = self.base_limits.copy()


class RiskLimitsManager:
    """Manages risk limits configuration and validation."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validator = RiskLimitsValidator()
        self.dynamic_limits = DynamicRiskLimits(config)
        
        # Validate initial configuration
        errors = self.validator.validate_limits(config)
        if errors:
            raise ValueError(f"Invalid risk limits configuration: {errors}")
    
    def get_limits(self, market_conditions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get current risk limits, optionally adjusted for market conditions."""
        if market_conditions:
            self.dynamic_limits.update_limits(market_conditions)
        
        return self.dynamic_limits.get_current_limits()
    
    def reset_limits(self):
        """Reset limits to base configuration."""
        self.dynamic_limits.reset_to_base()
    
    def update_position_limits(self, position_limits: List[PositionLimit]):
        """Update position-specific limits."""
        errors = self.validator.validate_position_limits(position_limits)
        if errors:
            raise ValueError(f"Invalid position limits: {errors}")
        
        # Store position limits (implementation would depend on your storage)
        pass
    
    def update_sector_limits(self, sector_limits: List[SectorLimit]):
        """Update sector-specific limits."""
        errors = self.validator.validate_sector_limits(sector_limits)
        if errors:
            raise ValueError(f"Invalid sector limits: {errors}")
        
        # Store sector limits (implementation would depend on your storage)
        pass
    
    def update_underlying_limits(self, underlying_limits: List[UnderlyingLimit]):
        """Update underlying-specific limits."""
        errors = self.validator.validate_underlying_limits(underlying_limits)
        if errors:
            raise ValueError(f"Invalid underlying limits: {errors}")
        
        # Store underlying limits (implementation would depend on your storage)
        pass
