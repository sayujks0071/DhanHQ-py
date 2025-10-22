"""
Real-time risk monitoring and alerting.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

from .manager import RiskManager, RiskMetrics
from .limits import RiskLevel

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Alert type enumeration."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class RiskAlert:
    """Risk alert data structure."""
    timestamp: datetime
    alert_type: AlertType
    category: str
    message: str
    value: float
    threshold: float
    severity: int  # 1-5, higher is more severe


class RiskMonitor:
    """
    Real-time risk monitoring and alerting system.
    """
    
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.alerts: List[RiskAlert] = []
        self.alert_callbacks: List[Callable[[RiskAlert], None]] = []
        
        # Alert thresholds
        self.alert_thresholds = {
            'portfolio_value': {'warning': 0.8, 'critical': 0.9},
            'daily_pnl': {'warning': -0.02, 'critical': -0.05},
            'drawdown': {'warning': 0.05, 'critical': 0.1},
            'margin_usage': {'warning': 0.7, 'critical': 0.9},
            'delta_exposure': {'warning': 0.8, 'critical': 0.95},
            'gamma_exposure': {'warning': 0.8, 'critical': 0.95},
            'theta_exposure': {'warning': 0.8, 'critical': 0.95},
            'vega_exposure': {'warning': 0.8, 'critical': 0.95}
        }
    
    def monitor_risk(
        self,
        positions: Dict[str, Any],
        cash: float,
        margin_used: float,
        market_data: Optional[Dict[str, Any]] = None
    ) -> List[RiskAlert]:
        """
        Monitor risk metrics and generate alerts.
        
        Returns:
            List of new alerts generated
        """
        new_alerts = []
        
        # Calculate current risk metrics
        risk_metrics = self.risk_manager._calculate_risk_metrics(
            positions, cash, margin_used, market_data
        )
        
        # Check each risk metric
        alerts = self._check_portfolio_alerts(risk_metrics)
        new_alerts.extend(alerts)
        
        alerts = self._check_greeks_alerts(risk_metrics)
        new_alerts.extend(alerts)
        
        alerts = self._check_margin_alerts(risk_metrics)
        new_alerts.extend(alerts)
        
        alerts = self._check_position_alerts(positions, risk_metrics)
        new_alerts.extend(alerts)
        
        alerts = self._check_sector_alerts(risk_metrics)
        new_alerts.extend(alerts)
        
        # Store alerts
        self.alerts.extend(new_alerts)
        
        # Trigger callbacks
        for alert in new_alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
        
        # Clean up old alerts (keep last 1000)
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        return new_alerts
    
    def _check_portfolio_alerts(self, risk_metrics: RiskMetrics) -> List[RiskAlert]:
        """Check portfolio-level alerts."""
        alerts = []
        
        # Portfolio value alerts
        if risk_metrics.portfolio_value < self.risk_manager.config.initial_capital * 0.8:
            alerts.append(RiskAlert(
                timestamp=datetime.now(),
                alert_type=AlertType.WARNING,
                category='portfolio_value',
                message=f"Portfolio value below 80% of initial capital: {risk_metrics.portfolio_value:.2f}",
                value=risk_metrics.portfolio_value,
                threshold=self.risk_manager.config.initial_capital * 0.8,
                severity=3
            ))
        
        # Daily P&L alerts
        if risk_metrics.daily_pnl < -self.risk_manager.config.initial_capital * 0.02:
            alerts.append(RiskAlert(
                timestamp=datetime.now(),
                alert_type=AlertType.WARNING,
                category='daily_pnl',
                message=f"Daily loss exceeds 2%: {risk_metrics.daily_pnl:.2f}",
                value=risk_metrics.daily_pnl,
                threshold=-self.risk_manager.config.initial_capital * 0.02,
                severity=3
            ))
        
        # Drawdown alerts
        if risk_metrics.current_drawdown > 0.05:
            alerts.append(RiskAlert(
                timestamp=datetime.now(),
                alert_type=AlertType.WARNING,
                category='drawdown',
                message=f"Current drawdown exceeds 5%: {risk_metrics.current_drawdown:.2%}",
                value=risk_metrics.current_drawdown,
                threshold=0.05,
                severity=4
            ))
        
        return alerts
    
    def _check_greeks_alerts(self, risk_metrics: RiskMetrics) -> List[RiskAlert]:
        """Check Greeks exposure alerts."""
        alerts = []
        
        # Delta exposure
        if abs(risk_metrics.total_delta) > self.risk_manager.limits.max_delta_exposure * 0.8:
            alerts.append(RiskAlert(
                timestamp=datetime.now(),
                alert_type=AlertType.WARNING,
                category='delta_exposure',
                message=f"Delta exposure approaching limit: {risk_metrics.total_delta:.2f}",
                value=abs(risk_metrics.total_delta),
                threshold=self.risk_manager.limits.max_delta_exposure * 0.8,
                severity=3
            ))
        
        # Gamma exposure
        if abs(risk_metrics.total_gamma) > self.risk_manager.limits.max_gamma_exposure * 0.8:
            alerts.append(RiskAlert(
                timestamp=datetime.now(),
                alert_type=AlertType.WARNING,
                category='gamma_exposure',
                message=f"Gamma exposure approaching limit: {risk_metrics.total_gamma:.2f}",
                value=abs(risk_metrics.total_gamma),
                threshold=self.risk_manager.limits.max_gamma_exposure * 0.8,
                severity=3
            ))
        
        # Theta exposure
        if abs(risk_metrics.total_theta) > self.risk_manager.limits.max_theta_exposure * 0.8:
            alerts.append(RiskAlert(
                timestamp=datetime.now(),
                alert_type=AlertType.WARNING,
                category='theta_exposure',
                message=f"Theta exposure approaching limit: {risk_metrics.total_theta:.2f}",
                value=abs(risk_metrics.total_theta),
                threshold=self.risk_manager.limits.max_theta_exposure * 0.8,
                severity=3
            ))
        
        # Vega exposure
        if abs(risk_metrics.total_vega) > self.risk_manager.limits.max_vega_exposure * 0.8:
            alerts.append(RiskAlert(
                timestamp=datetime.now(),
                alert_type=AlertType.WARNING,
                category='vega_exposure',
                message=f"Vega exposure approaching limit: {risk_metrics.total_vega:.2f}",
                value=abs(risk_metrics.total_vega),
                threshold=self.risk_manager.limits.max_vega_exposure * 0.8,
                severity=3
            ))
        
        return alerts
    
    def _check_margin_alerts(self, risk_metrics: RiskMetrics) -> List[RiskAlert]:
        """Check margin usage alerts."""
        alerts = []
        
        margin_usage = risk_metrics.margin_used / self.risk_manager.config.initial_capital
        
        if margin_usage > 0.7:
            alerts.append(RiskAlert(
                timestamp=datetime.now(),
                alert_type=AlertType.WARNING,
                category='margin_usage',
                message=f"Margin usage high: {margin_usage:.2%}",
                value=margin_usage,
                threshold=0.7,
                severity=3
            ))
        
        if margin_usage > 0.9:
            alerts.append(RiskAlert(
                timestamp=datetime.now(),
                alert_type=AlertType.CRITICAL,
                category='margin_usage',
                message=f"Margin usage critical: {margin_usage:.2%}",
                value=margin_usage,
                threshold=0.9,
                severity=5
            ))
        
        return alerts
    
    def _check_position_alerts(
        self, 
        positions: Dict[str, Any], 
        risk_metrics: RiskMetrics
    ) -> List[RiskAlert]:
        """Check position-specific alerts."""
        alerts = []
        
        # Position count
        if risk_metrics.position_count > self.risk_manager.limits.max_concurrent_positions * 0.8:
            alerts.append(RiskAlert(
                timestamp=datetime.now(),
                alert_type=AlertType.WARNING,
                category='position_count',
                message=f"Position count approaching limit: {risk_metrics.position_count}",
                value=risk_metrics.position_count,
                threshold=self.risk_manager.limits.max_concurrent_positions * 0.8,
                severity=2
            ))
        
        # Individual position sizes
        for symbol, position in positions.items():
            position_value = abs(position.quantity * position.avg_price)
            if position_value > self.risk_manager.limits.max_position_size * 0.8:
                alerts.append(RiskAlert(
                    timestamp=datetime.now(),
                    alert_type=AlertType.WARNING,
                    category='position_size',
                    message=f"Position size approaching limit for {symbol}: {position_value:.2f}",
                    value=position_value,
                    threshold=self.risk_manager.limits.max_position_size * 0.8,
                    severity=3
                ))
        
        return alerts
    
    def _check_sector_alerts(self, risk_metrics: RiskMetrics) -> List[RiskAlert]:
        """Check sector exposure alerts."""
        alerts = []
        
        for sector, exposure in risk_metrics.sector_exposures.items():
            sector_pct = exposure / risk_metrics.portfolio_value
            if sector_pct > self.risk_manager.limits.max_sector_exposure * 0.8:
                alerts.append(RiskAlert(
                    timestamp=datetime.now(),
                    alert_type=AlertType.WARNING,
                    category='sector_exposure',
                    message=f"Sector exposure approaching limit for {sector}: {sector_pct:.2%}",
                    value=sector_pct,
                    threshold=self.risk_manager.limits.max_sector_exposure * 0.8,
                    severity=3
                ))
        
        return alerts
    
    def add_alert_callback(self, callback: Callable[[RiskAlert], None]):
        """Add alert callback function."""
        self.alert_callbacks.append(callback)
    
    def get_alerts(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        alert_type: Optional[AlertType] = None,
        category: Optional[str] = None
    ) -> List[RiskAlert]:
        """Get filtered alerts."""
        filtered_alerts = self.alerts
        
        if start_time:
            filtered_alerts = [a for a in filtered_alerts if a.timestamp >= start_time]
        
        if end_time:
            filtered_alerts = [a for a in filtered_alerts if a.timestamp <= end_time]
        
        if alert_type:
            filtered_alerts = [a for a in filtered_alerts if a.alert_type == alert_type]
        
        if category:
            filtered_alerts = [a for a in filtered_alerts if a.category == category]
        
        return filtered_alerts
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        if not self.alerts:
            return {}
        
        # Count by type
        type_counts = {}
        for alert in self.alerts:
            type_counts[alert.alert_type.value] = type_counts.get(alert.alert_type.value, 0) + 1
        
        # Count by category
        category_counts = {}
        for alert in self.alerts:
            category_counts[alert.category] = category_counts.get(alert.category, 0) + 1
        
        # Recent alerts (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_alerts = [a for a in self.alerts if a.timestamp >= recent_cutoff]
        
        return {
            'total_alerts': len(self.alerts),
            'recent_alerts': len(recent_alerts),
            'type_counts': type_counts,
            'category_counts': category_counts,
            'highest_severity': max([a.severity for a in self.alerts]) if self.alerts else 0
        }
    
    def clear_alerts(self, older_than: Optional[datetime] = None):
        """Clear alerts, optionally only those older than specified time."""
        if older_than:
            self.alerts = [a for a in self.alerts if a.timestamp > older_than]
        else:
            self.alerts = []
    
    def export_alerts(self, filename: str):
        """Export alerts to CSV file."""
        if not self.alerts:
            return
        
        df = pd.DataFrame([
            {
                'timestamp': alert.timestamp,
                'alert_type': alert.alert_type.value,
                'category': alert.category,
                'message': alert.message,
                'value': alert.value,
                'threshold': alert.threshold,
                'severity': alert.severity
            }
            for alert in self.alerts
        ])
        
        df.to_csv(filename, index=False)
        logger.info(f"Exported {len(self.alerts)} alerts to {filename}")
