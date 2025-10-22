"""
Comprehensive reporting system.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class ReportData:
    """Report data structure."""
    timestamp: datetime
    portfolio_value: float
    total_pnl: float
    daily_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    positions: Dict[str, Any]
    orders: List[Dict[str, Any]]
    risk_metrics: Dict[str, Any]
    strategy_performance: Dict[str, Any]


class Reporter:
    """
    Comprehensive reporting system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.reports_dir = config.get('reports_dir', 'reports')
        self.logs_dir = config.get('logs_dir', 'logs')
        
        # Create directories if they don't exist
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Report templates
        self.daily_report_template = self._load_template('daily_report.md')
        self.weekly_report_template = self._load_template('weekly_report.md')
        self.monthly_report_template = self._load_template('monthly_report.md')
    
    def generate_daily_report(
        self,
        portfolio_data: Dict[str, Any],
        positions: Dict[str, Any],
        orders: List[Dict[str, Any]],
        risk_metrics: Dict[str, Any],
        strategy_performance: Dict[str, Any]
    ) -> str:
        """
        Generate daily report.
        
        Args:
            portfolio_data: Portfolio data
            positions: Current positions
            orders: Today's orders
            risk_metrics: Risk metrics
            strategy_performance: Strategy performance
            
        Returns:
            Report content
        """
        try:
            # Prepare report data
            report_data = ReportData(
                timestamp=datetime.now(),
                portfolio_value=portfolio_data.get('total_value', 0.0),
                total_pnl=portfolio_data.get('total_pnl', 0.0),
                daily_pnl=portfolio_data.get('daily_pnl', 0.0),
                unrealized_pnl=portfolio_data.get('unrealized_pnl', 0.0),
                realized_pnl=portfolio_data.get('realized_pnl', 0.0),
                positions=positions,
                orders=orders,
                risk_metrics=risk_metrics,
                strategy_performance=strategy_performance
            )
            
            # Generate report content
            content = self._format_daily_report(report_data)
            
            # Save report
            filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = os.path.join(self.reports_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            logger.info(f"Daily report generated: {filepath}")
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return f"Error generating daily report: {e}"
    
    def generate_weekly_report(
        self,
        weekly_data: Dict[str, Any],
        strategy_performance: Dict[str, Any],
        risk_analysis: Dict[str, Any]
    ) -> str:
        """
        Generate weekly report.
        
        Args:
            weekly_data: Weekly portfolio data
            strategy_performance: Strategy performance
            risk_analysis: Risk analysis
            
        Returns:
            Report content
        """
        try:
            # Generate report content
            content = self._format_weekly_report(weekly_data, strategy_performance, risk_analysis)
            
            # Save report
            filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = os.path.join(self.reports_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            logger.info(f"Weekly report generated: {filepath}")
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return f"Error generating weekly report: {e}"
    
    def generate_monthly_report(
        self,
        monthly_data: Dict[str, Any],
        strategy_performance: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> str:
        """
        Generate monthly report.
        
        Args:
            monthly_data: Monthly portfolio data
            strategy_performance: Strategy performance
            risk_analysis: Risk analysis
            backtest_results: Backtest results
            
        Returns:
            Report content
        """
        try:
            # Generate report content
            content = self._format_monthly_report(
                monthly_data, strategy_performance, risk_analysis, backtest_results
            )
            
            # Save report
            filename = f"monthly_report_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = os.path.join(self.reports_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            logger.info(f"Monthly report generated: {filepath}")
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating monthly report: {e}")
            return f"Error generating monthly report: {e}"
    
    def _format_daily_report(self, data: ReportData) -> str:
        """Format daily report."""
        content = f"""
# Daily Trading Report - {data.timestamp.strftime('%Y-%m-%d')}

## Portfolio Summary
- **Total Value**: ₹{data.portfolio_value:,.2f}
- **Total P&L**: ₹{data.total_pnl:,.2f}
- **Daily P&L**: ₹{data.daily_pnl:,.2f}
- **Unrealized P&L**: ₹{data.unrealized_pnl:,.2f}
- **Realized P&L**: ₹{data.realized_pnl:,.2f}

## Positions ({len(data.positions)})
"""
        
        if data.positions:
            content += "| Symbol | Quantity | Avg Price | Current Price | P&L |\n"
            content += "|--------|----------|-----------|---------------|-----|\n"
            
            for symbol, position in data.positions.items():
                current_price = position.get('current_price', position.get('avg_price', 0))
                pnl = (current_price - position.get('avg_price', 0)) * position.get('quantity', 0)
                content += f"| {symbol} | {position.get('quantity', 0)} | ₹{position.get('avg_price', 0):.2f} | ₹{current_price:.2f} | ₹{pnl:.2f} |\n"
        else:
            content += "No positions\n"
        
        content += f"""
## Orders ({len(data.orders)})
"""
        
        if data.orders:
            content += "| Time | Symbol | Side | Quantity | Price | Status |\n"
            content += "|------|--------|------|----------|-------|--------|\n"
            
            for order in data.orders:
                content += f"| {order.get('timestamp', '')} | {order.get('symbol', '')} | {order.get('side', '')} | {order.get('quantity', 0)} | ₹{order.get('price', 0):.2f} | {order.get('status', '')} |\n"
        else:
            content += "No orders today\n"
        
        content += f"""
## Risk Metrics
- **Delta Exposure**: {data.risk_metrics.get('total_delta', 0):.2f}
- **Gamma Exposure**: {data.risk_metrics.get('total_gamma', 0):.2f}
- **Theta Exposure**: {data.risk_metrics.get('total_theta', 0):.2f}
- **Vega Exposure**: {data.risk_metrics.get('total_vega', 0):.2f}
- **Margin Used**: ₹{data.risk_metrics.get('margin_used', 0):,.2f}
- **Current Drawdown**: {data.risk_metrics.get('current_drawdown', 0):.2%}
- **Max Drawdown**: {data.risk_metrics.get('max_drawdown', 0):.2%}

## Strategy Performance
"""
        
        for strategy, performance in data.strategy_performance.items():
            content += f"""
### {strategy}
- **P&L**: ₹{performance.get('pnl', 0):,.2f}
- **Return**: {performance.get('return', 0):.2%}
- **Sharpe**: {performance.get('sharpe', 0):.2f}
- **Max DD**: {performance.get('max_drawdown', 0):.2%}
"""
        
        content += f"""
---
*Report generated at {data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def _format_weekly_report(
        self,
        weekly_data: Dict[str, Any],
        strategy_performance: Dict[str, Any],
        risk_analysis: Dict[str, Any]
    ) -> str:
        """Format weekly report."""
        content = f"""
# Weekly Trading Report - {datetime.now().strftime('%Y-%m-%d')}

## Weekly Summary
- **Total Return**: {weekly_data.get('total_return', 0):.2%}
- **Weekly P&L**: ₹{weekly_data.get('weekly_pnl', 0):,.2f}
- **Volatility**: {weekly_data.get('volatility', 0):.2%}
- **Sharpe Ratio**: {weekly_data.get('sharpe_ratio', 0):.2f}
- **Max Drawdown**: {weekly_data.get('max_drawdown', 0):.2%}

## Strategy Performance
"""
        
        for strategy, performance in strategy_performance.items():
            content += f"""
### {strategy}
- **Weekly Return**: {performance.get('weekly_return', 0):.2%}
- **P&L**: ₹{performance.get('pnl', 0):,.2f}
- **Trades**: {performance.get('trades', 0)}
- **Win Rate**: {performance.get('win_rate', 0):.2%}
- **Sharpe**: {performance.get('sharpe', 0):.2f}
"""
        
        content += f"""
## Risk Analysis
- **Portfolio VaR (95%)**: {risk_analysis.get('var_95', 0):.2%}
- **Portfolio CVaR (95%)**: {risk_analysis.get('cvar_95', 0):.2%}
- **Beta**: {risk_analysis.get('beta', 0):.2f}
- **Correlation**: {risk_analysis.get('correlation', 0):.2f}

---
*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def _format_monthly_report(
        self,
        monthly_data: Dict[str, Any],
        strategy_performance: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        backtest_results: Dict[str, Any]
    ) -> str:
        """Format monthly report."""
        content = f"""
# Monthly Trading Report - {datetime.now().strftime('%Y-%m-%d')}

## Monthly Summary
- **Total Return**: {monthly_data.get('total_return', 0):.2%}
- **Monthly P&L**: ₹{monthly_data.get('monthly_pnl', 0):,.2f}
- **Volatility**: {monthly_data.get('volatility', 0):.2%}
- **Sharpe Ratio**: {monthly_data.get('sharpe_ratio', 0):.2f}
- **Max Drawdown**: {monthly_data.get('max_drawdown', 0):.2%}
- **Calmar Ratio**: {monthly_data.get('calmar_ratio', 0):.2f}

## Strategy Performance
"""
        
        for strategy, performance in strategy_performance.items():
            content += f"""
### {strategy}
- **Monthly Return**: {performance.get('monthly_return', 0):.2%}
- **P&L**: ₹{performance.get('pnl', 0):,.2f}
- **Trades**: {performance.get('trades', 0)}
- **Win Rate**: {performance.get('win_rate', 0):.2%}
- **Sharpe**: {performance.get('sharpe', 0):.2f}
- **Max DD**: {performance.get('max_drawdown', 0):.2%}
"""
        
        content += f"""
## Risk Analysis
- **Portfolio VaR (95%)**: {risk_analysis.get('var_95', 0):.2%}
- **Portfolio CVaR (95%)**: {risk_analysis.get('cvar_95', 0):.2%}
- **Beta**: {risk_analysis.get('beta', 0):.2f}
- **Correlation**: {risk_analysis.get('correlation', 0):.2f}

## Backtest Results
- **Total Return**: {backtest_results.get('total_return', 0):.2%}
- **Annualized Return**: {backtest_results.get('annualized_return', 0):.2%}
- **Volatility**: {backtest_results.get('volatility', 0):.2%}
- **Sharpe Ratio**: {backtest_results.get('sharpe_ratio', 0):.2f}
- **Max Drawdown**: {backtest_results.get('max_drawdown', 0):.2%}
- **Total Trades**: {backtest_results.get('total_trades', 0)}
- **Win Rate**: {backtest_results.get('win_rate', 0):.2%}
- **Profit Factor**: {backtest_results.get('profit_factor', 0):.2f}

---
*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def _load_template(self, template_name: str) -> str:
        """Load report template."""
        template_path = os.path.join('templates', template_name)
        try:
            with open(template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return ""
    
    def export_portfolio_data(
        self,
        portfolio_data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export portfolio data to CSV."""
        if filename is None:
            filename = f"portfolio_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = os.path.join(self.reports_dir, filename)
        
        # Convert to DataFrame and export
        df = pd.DataFrame([portfolio_data])
        df.to_csv(filepath, index=False)
        
        logger.info(f"Portfolio data exported: {filepath}")
        return filepath
    
    def export_strategy_performance(
        self,
        strategy_performance: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export strategy performance to CSV."""
        if filename is None:
            filename = f"strategy_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = os.path.join(self.reports_dir, filename)
        
        # Convert to DataFrame and export
        df = pd.DataFrame(strategy_performance)
        df.to_csv(filepath, index=False)
        
        logger.info(f"Strategy performance exported: {filepath}")
        return filepath
    
    def get_report_summary(self) -> Dict[str, Any]:
        """Get report summary."""
        try:
            # Count reports
            daily_reports = len([f for f in os.listdir(self.reports_dir) if f.startswith('daily_report_')])
            weekly_reports = len([f for f in os.listdir(self.reports_dir) if f.startswith('weekly_report_')])
            monthly_reports = len([f for f in os.listdir(self.reports_dir) if f.startswith('monthly_report_')])
            
            return {
                'daily_reports': daily_reports,
                'weekly_reports': weekly_reports,
                'monthly_reports': monthly_reports,
                'total_reports': daily_reports + weekly_reports + monthly_reports,
                'reports_dir': self.reports_dir
            }
            
        except Exception as e:
            logger.error(f"Error getting report summary: {e}")
            return {}
