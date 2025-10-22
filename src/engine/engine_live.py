"""
Live trading engine with real order execution.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json
import time

from ..config import Config
from ..risk.manager import RiskManager
from ..risk.monitor import RiskMonitor
from ..strategies.base import BaseStrategy
from ..broker.dhan_adapter import DhanAdapter
from .order_manager import OrderManager

logger = logging.getLogger(__name__)


@dataclass
class LivePosition:
    """Live trading position."""
    symbol: str
    quantity: int
    avg_price: float
    unrealized_pnl: float
    realized_pnl: float
    margin_used: float
    entry_time: datetime
    order_id: str


@dataclass
class LiveFill:
    """Live trading fill."""
    timestamp: datetime
    symbol: str
    side: str
    quantity: int
    price: float
    commission: float
    order_id: str
    fill_id: str


class LiveTradingEngine:
    """
    Live trading engine with real order execution.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.risk_manager = RiskManager(config)
        self.risk_monitor = RiskMonitor(self.risk_manager)
        self.broker = DhanAdapter(config)
        self.order_manager = OrderManager()
        
        # Trading state
        self.positions: Dict[str, LivePosition] = {}
        self.fills: List[LiveFill] = []
        self.cash = config.initial_capital
        self.margin_used = 0.0
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        
        # Performance tracking
        self.equity_curve = []
        self.daily_returns = []
        self.max_drawdown = 0.0
        self.peak_equity = config.initial_capital
        
        # Risk tracking
        self.daily_loss = 0.0
        self.consecutive_losses = 0
        self.last_trade_time = None
        
        # Trading controls
        self.trading_enabled = False
        self.kill_switch = False
        self.emergency_stop = False
        
        # State persistence
        self.state_file = "data/live_trading_state.json"
        self._load_state()
        
        # Initialize broker connection
        self._initialize_broker()
    
    def _initialize_broker(self):
        """Initialize broker connection."""
        try:
            # Test broker connection
            if not self.broker.test_connection():
                raise Exception("Failed to connect to broker")
            
            logger.info("Broker connection established")
            
            # Get account information
            account_info = self.broker.get_account_info()
            self.cash = account_info.get('available_cash', self.config.initial_capital)
            
            logger.info(f"Account cash: {self.cash}")
            
        except Exception as e:
            logger.error(f"Failed to initialize broker: {e}")
            raise
    
    def start_trading(self, strategy: BaseStrategy, universe: List[str]):
        """Start live trading with a strategy."""
        
        # Pre-flight checks
        if not self._pre_flight_checks():
            logger.error("Pre-flight checks failed")
            return
        
        logger.info(f"Starting live trading with {strategy.__class__.__name__}")
        
        # Initialize strategy
        strategy.initialize(universe, self.config)
        
        # Start market data subscription
        self._subscribe_to_market_data(universe)
        
        # Enable trading
        self.trading_enabled = True
        
        # Start trading loop
        self._trading_loop(strategy)
    
    def _pre_flight_checks(self) -> bool:
        """Perform pre-flight checks before live trading."""
        logger.info("Performing pre-flight checks...")
        
        checks = [
            self._check_broker_connection(),
            self._check_account_status(),
            self._check_market_hours(),
            self._check_risk_limits(),
            self._check_emergency_stop()
        ]
        
        all_passed = all(checks)
        
        if all_passed:
            logger.info("All pre-flight checks passed")
        else:
            logger.error("Some pre-flight checks failed")
        
        return all_passed
    
    def _check_broker_connection(self) -> bool:
        """Check broker connection."""
        try:
            return self.broker.test_connection()
        except Exception as e:
            logger.error(f"Broker connection check failed: {e}")
            return False
    
    def _check_account_status(self) -> bool:
        """Check account status."""
        try:
            account_info = self.broker.get_account_info()
            return account_info.get('status') == 'active'
        except Exception as e:
            logger.error(f"Account status check failed: {e}")
            return False
    
    def _check_market_hours(self) -> bool:
        """Check if market is open."""
        now = datetime.now()
        market_open = now.hour >= 9 and now.hour < 15
        return market_open
    
    def _check_risk_limits(self) -> bool:
        """Check if risk limits are within bounds."""
        try:
            is_safe, violations = self.risk_manager.check_limits(
                self.positions, self.cash, self.margin_used
            )
            return is_safe
        except Exception as e:
            logger.error(f"Risk limits check failed: {e}")
            return False
    
    def _check_emergency_stop(self) -> bool:
        """Check if emergency stop is active."""
        return not self.emergency_stop
    
    def _subscribe_to_market_data(self, universe: List[str]):
        """Subscribe to market data for universe symbols."""
        logger.info(f"Subscribing to market data for {len(universe)} symbols")
        
        try:
            for symbol in universe:
                self.broker.subscribe_quotes(symbol)
            logger.info("Market data subscription successful")
        except Exception as e:
            logger.error(f"Failed to subscribe to market data: {e}")
            raise
    
    def _trading_loop(self, strategy: BaseStrategy):
        """Main trading loop."""
        logger.info("Starting live trading loop")
        
        while self.trading_enabled and not self.kill_switch:
            try:
                # Check emergency stop
                if self.emergency_stop:
                    logger.warning("Emergency stop activated")
                    break
                
                # Get current market data
                market_data = self._get_market_data()
                
                if not market_data:
                    logger.warning("No market data available")
                    time.sleep(1)
                    continue
                
                # Update positions with current prices
                self._update_positions(market_data)
                
                # Generate strategy signals
                signals = strategy.generate_signals(
                    datetime.now(),
                    market_data,
                    self.positions
                )
                
                # Process signals
                for signal in signals:
                    if self.trading_enabled and not self.kill_switch:
                        self._process_signal(signal, market_data)
                
                # Check risk limits
                is_safe, violations = self.risk_manager.check_limits(
                    self.positions, self.cash, self.margin_used, market_data
                )
                
                if not is_safe:
                    logger.warning(f"Risk limits violated: {violations}")
                    self._handle_risk_violations(violations)
                
                # Monitor risk and generate alerts
                alerts = self.risk_monitor.monitor_risk(
                    self.positions, self.cash, self.margin_used, market_data
                )
                
                if alerts:
                    logger.info(f"Generated {len(alerts)} risk alerts")
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Save state
                self._save_state()
                
                # Sleep until next update
                time.sleep(1)  # 1 second update frequency
                
            except KeyboardInterrupt:
                logger.info("Trading stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(5)  # Wait before retrying
                continue
        
        logger.info("Trading loop ended")
    
    def _get_market_data(self) -> Dict[str, Any]:
        """Get current market data for all positions and universe."""
        try:
            # Get quotes for all positions
            symbols = list(self.positions.keys())
            if not symbols:
                return {}
            
            quotes = self.broker.get_quotes(symbols)
            return quotes
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return {}
    
    def _update_positions(self, market_data: Dict[str, Any]):
        """Update positions with current market data."""
        for symbol, position in self.positions.items():
            if symbol in market_data:
                current_price = market_data[symbol].get('close', position.avg_price)
                position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
    
    def _process_signal(self, signal: Dict[str, Any], market_data: Dict[str, Any]):
        """Process a trading signal."""
        symbol = signal['symbol']
        side = signal['side']
        quantity = signal['quantity']
        
        if symbol not in market_data:
            logger.warning(f"No market data for {symbol}")
            return
        
        # Get current market price
        current_price = market_data[symbol].get('close', 0)
        
        if current_price == 0:
            logger.warning(f"Invalid price for {symbol}")
            return
        
        # Check if we can execute the trade
        if not self._can_execute_trade(symbol, side, quantity, current_price):
            logger.warning(f"Cannot execute trade: {symbol} {side} {quantity}")
            return
        
        # Execute the trade
        try:
            self._execute_trade(symbol, side, quantity, current_price)
            logger.info(f"Executed {side} {quantity} {symbol} at {current_price:.2f}")
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
    
    def _can_execute_trade(
        self, 
        symbol: str, 
        side: str, 
        quantity: int, 
        price: float
    ) -> bool:
        """Check if we can execute a trade."""
        
        if side == 'BUY':
            # Check if we have enough cash
            required_cash = quantity * price
            return self.cash >= required_cash
        else:
            # Check if we have the position
            if symbol in self.positions:
                return self.positions[symbol].quantity >= quantity
            return False
    
    def _execute_trade(
        self, 
        symbol: str, 
        side: str, 
        quantity: int, 
        price: float
    ):
        """Execute a trade and update positions."""
        
        try:
            # Place order with broker
            order_result = self.broker.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_type='MARKET'
            )
            
            if not order_result.get('success', False):
                logger.error(f"Order failed: {order_result}")
                return
            
            order_id = order_result.get('order_id')
            
            # Wait for fill (simplified - in practice you'd monitor order status)
            time.sleep(1)
            
            # Get fill details
            fill_price = price  # Simplified - would get actual fill price
            commission = self._calculate_commission(symbol, quantity, fill_price)
            
            # Create fill
            fill = LiveFill(
                timestamp=datetime.now(),
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=fill_price,
                commission=commission,
                order_id=order_id,
                fill_id=f"{order_id}_{datetime.now().timestamp()}"
            )
            
            # Update position
            if symbol not in self.positions:
                self.positions[symbol] = LivePosition(
                    symbol=symbol,
                    quantity=0,
                    avg_price=0.0,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    margin_used=0.0,
                    entry_time=datetime.now(),
                    order_id=order_id
                )
            
            position = self.positions[symbol]
            
            if side == 'BUY':
                # Add to position
                new_quantity = position.quantity + quantity
                new_avg_price = (
                    (position.avg_price * position.quantity + fill_price * quantity) 
                    / new_quantity
                )
                position.quantity = new_quantity
                position.avg_price = new_avg_price
                
                # Update cash
                self.cash -= (quantity * fill_price + commission)
                
            else:  # SELL
                # Reduce position
                position.quantity -= quantity
                
                # Calculate realized P&L
                realized_pnl = (fill_price - position.avg_price) * quantity
                position.realized_pnl += realized_pnl
                self.total_pnl += realized_pnl
                
                # Update cash
                self.cash += (quantity * fill_price - commission)
                
                # Remove position if quantity is zero
                if position.quantity == 0:
                    del self.positions[symbol]
            
            # Store fill
            self.fills.append(fill)
            
            # Update daily P&L
            self.daily_pnl += realized_pnl if side == 'SELL' else 0
            
            # Update last trade time
            self.last_trade_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            raise
    
    def _calculate_commission(self, symbol: str, quantity: int, price: float) -> float:
        """Calculate commission for a trade."""
        notional = quantity * price
        
        if 'OPT' in symbol:
            return quantity * self.config.options_commission
        else:
            return notional * self.config.equity_commission / 100
    
    def _handle_risk_violations(self, violations: List[str]):
        """Handle risk limit violations."""
        logger.warning(f"Handling risk violations: {violations}")
        
        # Implement risk response strategies
        for violation in violations:
            if "Daily loss" in violation:
                self._reduce_position_sizes()
            elif "Drawdown" in violation:
                self._close_risky_positions()
            elif "Margin" in violation:
                self._reduce_leverage()
            elif "Greeks" in violation:
                self._hedge_exposures()
    
    def _reduce_position_sizes(self):
        """Reduce position sizes to manage risk."""
        logger.info("Reducing position sizes")
        
        for symbol, position in self.positions.items():
            if position.quantity > 0:
                # Reduce position by 50%
                reduce_qty = position.quantity // 2
                if reduce_qty > 0:
                    try:
                        self._execute_trade(symbol, 'SELL', reduce_qty, position.avg_price)
                    except Exception as e:
                        logger.error(f"Failed to reduce position {symbol}: {e}")
    
    def _close_risky_positions(self):
        """Close positions with highest risk."""
        logger.info("Closing risky positions")
        
        # Sort positions by risk (simplified - would use proper risk metrics)
        risky_positions = sorted(
            self.positions.items(),
            key=lambda x: abs(x[1].unrealized_pnl),
            reverse=True
        )
        
        # Close top 3 riskiest positions
        for symbol, position in risky_positions[:3]:
            if position.quantity > 0:
                try:
                    self._execute_trade(symbol, 'SELL', position.quantity, position.avg_price)
                except Exception as e:
                    logger.error(f"Failed to close position {symbol}: {e}")
    
    def _reduce_leverage(self):
        """Reduce leverage by closing positions."""
        logger.info("Reducing leverage")
        
        # Close positions to reduce margin usage
        for symbol, position in self.positions.items():
            if position.quantity > 0:
                try:
                    self._execute_trade(symbol, 'SELL', position.quantity, position.avg_price)
                except Exception as e:
                    logger.error(f"Failed to close position {symbol}: {e}")
    
    def _hedge_exposures(self):
        """Hedge Greek exposures."""
        logger.info("Hedging exposures")
        
        # This would implement proper hedging strategies
        # For now, just log the action
        pass
    
    def _update_performance_metrics(self):
        """Update performance metrics."""
        # Calculate total portfolio value
        total_value = self.cash
        for position in self.positions.values():
            total_value += position.quantity * position.avg_price + position.unrealized_pnl
        
        self.equity_curve.append(total_value)
        
        # Update peak equity and drawdown
        if total_value > self.peak_equity:
            self.peak_equity = total_value
        
        current_drawdown = (self.peak_equity - total_value) / self.peak_equity
        self.max_drawdown = max(self.max_drawdown, current_drawdown)
        
        # Update daily returns
        if len(self.equity_curve) > 1:
            daily_return = (total_value - self.equity_curve[-2]) / self.equity_curve[-2]
            self.daily_returns.append(daily_return)
    
    def _save_state(self):
        """Save trading state to file."""
        state = {
            'positions': {
                symbol: {
                    'quantity': pos.quantity,
                    'avg_price': pos.avg_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'realized_pnl': pos.realized_pnl,
                    'margin_used': pos.margin_used,
                    'entry_time': pos.entry_time.isoformat(),
                    'order_id': pos.order_id
                }
                for symbol, pos in self.positions.items()
            },
            'cash': self.cash,
            'margin_used': self.margin_used,
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'equity_curve': self.equity_curve,
            'max_drawdown': self.max_drawdown,
            'peak_equity': self.peak_equity,
            'trading_enabled': self.trading_enabled,
            'kill_switch': self.kill_switch,
            'emergency_stop': self.emergency_stop
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _load_state(self):
        """Load trading state from file."""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # Restore positions
            self.positions = {}
            for symbol, pos_data in state.get('positions', {}).items():
                self.positions[symbol] = LivePosition(
                    symbol=symbol,
                    quantity=pos_data['quantity'],
                    avg_price=pos_data['avg_price'],
                    unrealized_pnl=pos_data['unrealized_pnl'],
                    realized_pnl=pos_data['realized_pnl'],
                    margin_used=pos_data['margin_used'],
                    entry_time=datetime.fromisoformat(pos_data['entry_time']),
                    order_id=pos_data['order_id']
                )
            
            # Restore other state
            self.cash = state.get('cash', self.config.initial_capital)
            self.margin_used = state.get('margin_used', 0.0)
            self.daily_pnl = state.get('daily_pnl', 0.0)
            self.total_pnl = state.get('total_pnl', 0.0)
            self.equity_curve = state.get('equity_curve', [])
            self.max_drawdown = state.get('max_drawdown', 0.0)
            self.peak_equity = state.get('peak_equity', self.config.initial_capital)
            self.trading_enabled = state.get('trading_enabled', False)
            self.kill_switch = state.get('kill_switch', False)
            self.emergency_stop = state.get('emergency_stop', False)
            
            logger.info("Loaded live trading state from file")
            
        except FileNotFoundError:
            logger.info("No existing state file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def stop_trading(self):
        """Stop trading."""
        logger.info("Stopping trading")
        self.trading_enabled = False
    
    def activate_kill_switch(self):
        """Activate kill switch to stop all trading."""
        logger.warning("Kill switch activated")
        self.kill_switch = True
        self.trading_enabled = False
    
    def activate_emergency_stop(self):
        """Activate emergency stop."""
        logger.warning("Emergency stop activated")
        self.emergency_stop = True
        self.trading_enabled = False
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.equity_curve:
            return {}
        
        total_return = (self.equity_curve[-1] - self.equity_curve[0]) / self.equity_curve[0]
        volatility = np.std(self.daily_returns) * np.sqrt(252) if self.daily_returns else 0
        sharpe_ratio = total_return / volatility if volatility > 0 else 0
        
        return {
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'total_pnl': self.total_pnl,
            'current_equity': self.equity_curve[-1] if self.equity_curve else self.config.initial_capital,
            'position_count': len(self.positions),
            'total_trades': len(self.fills),
            'trading_enabled': self.trading_enabled,
            'kill_switch': self.kill_switch,
            'emergency_stop': self.emergency_stop
        }
