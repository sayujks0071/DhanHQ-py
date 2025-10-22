"""
Telegram notification system.
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Telegram notification system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bot_token = config.get('telegram_bot_token')
        self.chat_id = config.get('telegram_chat_id')
        self.enabled = config.get('telegram_enabled', False)
        
        if self.enabled and not self.bot_token:
            logger.warning("Telegram enabled but bot token not provided")
            self.enabled = False
        
        if self.enabled and not self.chat_id:
            logger.warning("Telegram enabled but chat ID not provided")
            self.enabled = False
    
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        Send a message to Telegram.
        
        Args:
            message: Message to send
            parse_mode: Message parse mode
            
        Returns:
            Success status
        """
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_trade_alert(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        strategy: str
    ) -> bool:
        """
        Send trade alert.
        
        Args:
            symbol: Symbol traded
            side: Buy/Sell
            quantity: Quantity
            price: Price
            strategy: Strategy name
            
        Returns:
            Success status
        """
        message = f"""
🚀 *Trade Alert*
📊 *Symbol*: {symbol}
📈 *Side*: {side}
📦 *Quantity*: {quantity}
💰 *Price*: ₹{price:.2f}
🎯 *Strategy*: {strategy}
⏰ *Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(message)
    
    def send_pnl_alert(
        self,
        daily_pnl: float,
        total_pnl: float,
        portfolio_value: float
    ) -> bool:
        """
        Send P&L alert.
        
        Args:
            daily_pnl: Daily P&L
            total_pnl: Total P&L
            portfolio_value: Portfolio value
            
        Returns:
            Success status
        """
        emoji = "📈" if daily_pnl >= 0 else "📉"
        
        message = f"""
{emoji} *P&L Update*
💰 *Daily P&L*: ₹{daily_pnl:,.2f}
📊 *Total P&L*: ₹{total_pnl:,.2f}
💼 *Portfolio Value*: ₹{portfolio_value:,.2f}
⏰ *Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(message)
    
    def send_risk_alert(
        self,
        risk_metrics: Dict[str, Any],
        violations: List[str]
    ) -> bool:
        """
        Send risk alert.
        
        Args:
            risk_metrics: Risk metrics
            violations: Risk violations
            
        Returns:
            Success status
        """
        message = f"""
⚠️ *Risk Alert*
🚨 *Violations*: {len(violations)}
📊 *Delta*: {risk_metrics.get('total_delta', 0):.2f}
📈 *Gamma*: {risk_metrics.get('total_gamma', 0):.2f}
⏰ *Theta*: {risk_metrics.get('total_theta', 0):.2f}
📉 *Vega*: {risk_metrics.get('total_vega', 0):.2f}
💼 *Margin Used*: ₹{risk_metrics.get('margin_used', 0):,.2f}
📉 *Drawdown*: {risk_metrics.get('current_drawdown', 0):.2%}
⏰ *Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*Violations:*
"""
        
        for violation in violations:
            message += f"• {violation}\n"
        
        return self.send_message(message)
    
    def send_strategy_alert(
        self,
        strategy_name: str,
        action: str,
        reason: str
    ) -> bool:
        """
        Send strategy alert.
        
        Args:
            strategy_name: Strategy name
            action: Action taken
            reason: Reason for action
            
        Returns:
            Success status
        """
        emoji = "✅" if action == "STARTED" else "⏹️" if action == "STOPPED" else "⚠️"
        
        message = f"""
{emoji} *Strategy Alert*
🎯 *Strategy*: {strategy_name}
🔄 *Action*: {action}
📝 *Reason*: {reason}
⏰ *Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(message)
    
    def send_daily_summary(
        self,
        portfolio_value: float,
        daily_pnl: float,
        total_pnl: float,
        position_count: int,
        trade_count: int
    ) -> bool:
        """
        Send daily summary.
        
        Args:
            portfolio_value: Portfolio value
            daily_pnl: Daily P&L
            total_pnl: Total P&L
            position_count: Number of positions
            trade_count: Number of trades
            
        Returns:
            Success status
        """
        emoji = "📈" if daily_pnl >= 0 else "📉"
        
        message = f"""
{emoji} *Daily Summary*
💼 *Portfolio Value*: ₹{portfolio_value:,.2f}
💰 *Daily P&L*: ₹{daily_pnl:,.2f}
📊 *Total P&L*: ₹{total_pnl:,.2f}
📦 *Positions*: {position_count}
🔄 *Trades*: {trade_count}
⏰ *Date*: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        return self.send_message(message)
    
    def send_error_alert(
        self,
        error_message: str,
        component: str
    ) -> bool:
        """
        Send error alert.
        
        Args:
            error_message: Error message
            component: Component that failed
            
        Returns:
            Success status
        """
        message = f"""
🚨 *Error Alert*
⚠️ *Component*: {component}
📝 *Error*: {error_message}
⏰ *Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(message)
    
    def send_startup_alert(self) -> bool:
        """Send startup alert."""
        message = f"""
🚀 *Trading Bot Started*
⏰ *Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔄 *Status*: Online
"""
        
        return self.send_message(message)
    
    def send_shutdown_alert(self) -> bool:
        """Send shutdown alert."""
        message = f"""
⏹️ *Trading Bot Stopped*
⏰ *Time*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔄 *Status*: Offline
"""
        
        return self.send_message(message)
    
    def test_connection(self) -> bool:
        """Test Telegram connection."""
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url)
            
            if response.status_code == 200:
                logger.info("Telegram connection test successful")
                return True
            else:
                logger.error(f"Telegram connection test failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing Telegram connection: {e}")
            return False
