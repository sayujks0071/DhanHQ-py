"""
Paper trading engine with realistic execution simulation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json

from ..config import Config
from ..risk.manager import RiskManager
from ..risk.monitor import RiskMonitor
from ..strategies.base import BaseStrategy
from ..broker.paper_broker import PaperBroker
from .order_manager import OrderManager

logger = logging.getLogger(__name__)


@dataclass
class PaperPosition:
    """Paper trading position."""
    symbol: str
    quantity: int
    avg_price: float
    unrealized_pnl: float
    realized_pnl: float
    margin_used: float
    entry_time: datetime


@dataclass
class PaperFill:
    """Paper trading fill."""
    timestamp: datetime
    symbol: str
    side: str
    quantity: int
    price: float
    commission: float
    slippage: float
    order_id: str


class PaperTradingEngine:
    """
    Paper trading engine with realistic execution simulation.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.risk_manager = RiskManager(config)
        self.risk_monitor = RiskMonitor(self.risk_manager)
        self.broker = PaperBroker(config)
        self.order_manager = OrderManager()
        
        # Trading state
        self.positions: Dict[str, PaperPosition] = {}
        self.fills: List[PaperFill] = []
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
        
        # State persistence
        self.state_file = "data/paper_trading_state.json"
        self._load_state()
    
    def start_trading(self, strategy: BaseStrategy, universe: List[str]):
        """Start paper trading with a strategy."""
        logger.info(f"Starting paper trading with {strategy.__class__.__name__}")
        
        # Initialize strategy
        strategy.initialize(universe, self.config)
        
        # Start market data subscription
        self._subscribe_to_market_data(universe)
        
        # Start trading loop
        self._trading_loop(strategy)
    
    def _subscribe_to_market_data(self, universe: List[str]):
        """Subscribe to market data for universe symbols."""
        logger.info(f"Subscribing to market data for {len(universe)} symbols")
        
        # This would integrate with your market data provider
        # For now, simulate subscription
        for symbol in universe:
            self.broker.subscribe_quotes(symbol)
    
    def _trading_loop(self, strategy: BaseStrategy):
        """Main trading loop."""
        logger.info("Starting trading loop")
        
        while True:
            try:
                # Get current market data
                market_data = self._get_market_data()
                
                if not market_data:
                    logger.warning("No market data available")
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
                import time
                time.sleep(1)  # 1 second update frequency
                
            except KeyboardInterrupt:
                logger.info("Trading stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                continue
    
    def _get_market_data(self) -> Dict[str, Any]:
        """Get current market data for all positions and universe."""
        # This would integrate with your market data provider
        # For now, return mock data
        market_data = {}
        
        for symbol in self.positions.keys():
            # Mock market data
            market_data[symbol] = {
                'close': 100.0 + np.random.normal(0, 1),
                'volume': 1000000,
                'bid': 99.5,
                'ask': 100.5,
                'timestamp': datetime.now()
            }
        
        return market_data
    
    def _update_positions(self, market_data: Dict[str, Any]):
        """Update positions with current market data."""
        for symbol, position in self.positions.items():
            if symbol in market_data:
                current_price = market_data[symbol]['close']
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
        current_price = market_data[symbol]['close']
        
        # Simulate execution with slippage and commission
        execution_price = self._simulate_execution(symbol, side, quantity, current_price)
        commission = self._calculate_commission(symbol, quantity, execution_price)
        
        # Check if we can execute the trade
        if not self._can_execute_trade(symbol, side, quantity, execution_price):
            logger.warning(f"Cannot execute trade: {symbol} {side} {quantity}")
            return
        
        # Execute the trade
        self._execute_trade(symbol, side, quantity, execution_price, commission)
        
        logger.info(f"Executed {side} {quantity} {symbol} at {execution_price:.2f}")
    
    def _simulate_execution(
        self, 
        symbol: str, 
        side: str, 
        quantity: int, 
        current_price: float
    ) -> float:
        """Simulate realistic execution with slippage."""
        
        # Base slippage from config
        base_slippage = self.config.slippage_bps / 10000
        
        # Volume-based slippage
        volume_factor = min(quantity / 1000, 2.0)
        
        # Time-based slippage (higher during market open/close)
        hour = datetime.now().hour
        time_factor = 1.5 if hour in [9, 15] else 1.0
        
        # Random slippage component
        random_factor = np.random.normal(1.0, 0.1)
        
        total_slippage = base_slippage * volume_factor * time_factor * random_factor
        
        if side == 'BUY':
            return current_price * (1 + total_slippage)
        else:
            return current_price * (1 - total_slippage)
    
    def _calculate_commission(self, symbol: str, quantity: int, price: float) -> float:
        """Calculate commission for a trade."""
        notional = quantity * price
        
        if 'OPT' in symbol:
            return quantity * self.config.options_commission
        else:
            return notional * self.config.equity_commission / 100
    
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
        price: float, 
        commission: float
    ):
        """Execute a trade and update positions."""
        
        # Create fill
        fill = PaperFill(
            timestamp=datetime.now(),
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            commission=commission,
            slippage=0.0,  # Would calculate actual slippage
            order_id=f"{symbol}_{side}_{datetime.now().timestamp()}"
        )
        
        # Update position
        if symbol not in self.positions:
            self.positions[symbol] = PaperPosition(
                symbol=symbol,
                quantity=0,
                avg_price=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                margin_used=0.0,
                entry_time=datetime.now()
            )
        
        position = self.positions[symbol]
        
        if side == 'BUY':
            # Add to position
            new_quantity = position.quantity + quantity
            new_avg_price = (
                (position.avg_price * position.quantity + price * quantity) 
                / new_quantity
            )
            position.quantity = new_quantity
            position.avg_price = new_avg_price
            
            # Update cash
            self.cash -= (quantity * price + commission)
            
        else:  # SELL
            # Reduce position
            position.quantity -= quantity
            
            # Calculate realized P&L
            realized_pnl = (price - position.avg_price) * quantity
            position.realized_pnl += realized_pnl
            self.total_pnl += realized_pnl
            
            # Update cash
            self.cash += (quantity * price - commission)
            
            # Remove position if quantity is zero
            if position.quantity == 0:
                del self.positions[symbol]
        
        # Store fill
        self.fills.append(fill)
        
        # Update daily P&L
        self.daily_pnl += realized_pnl if side == 'SELL' else 0
        
        # Update last trade time
        self.last_trade_time = datetime.now()
    
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
                    self._execute_trade(symbol, 'SELL', reduce_qty, position.avg_price, 0.0)
    
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
                self._execute_trade(symbol, 'SELL', position.quantity, position.avg_price, 0.0)
    
    def _reduce_leverage(self):
        """Reduce leverage by closing positions."""
        logger.info("Reducing leverage")
        
        # Close positions to reduce margin usage
        for symbol, position in self.positions.items():
            if position.quantity > 0:
                self._execute_trade(symbol, 'SELL', position.quantity, position.avg_price, 0.0)
    
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
                    'entry_time': pos.entry_time.isoformat()
                }
                for symbol, pos in self.positions.items()
            },
            'cash': self.cash,
            'margin_used': self.margin_used,
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'equity_curve': self.equity_curve,
            'max_drawdown': self.max_drawdown,
            'peak_equity': self.peak_equity
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
                self.positions[symbol] = PaperPosition(
                    symbol=symbol,
                    quantity=pos_data['quantity'],
                    avg_price=pos_data['avg_price'],
                    unrealized_pnl=pos_data['unrealized_pnl'],
                    realized_pnl=pos_data['realized_pnl'],
                    margin_used=pos_data['margin_used'],
                    entry_time=datetime.fromisoformat(pos_data['entry_time'])
                )
            
            # Restore other state
            self.cash = state.get('cash', self.config.initial_capital)
            self.margin_used = state.get('margin_used', 0.0)
            self.daily_pnl = state.get('daily_pnl', 0.0)
            self.total_pnl = state.get('total_pnl', 0.0)
            self.equity_curve = state.get('equity_curve', [])
            self.max_drawdown = state.get('max_drawdown', 0.0)
            self.peak_equity = state.get('peak_equity', self.config.initial_capital)
            
            logger.info("Loaded paper trading state from file")
            
        except FileNotFoundError:
            logger.info("No existing state file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
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
            'total_trades': len(self.fills)
        }
