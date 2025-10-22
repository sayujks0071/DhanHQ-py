"""
Order management system for multi-leg orders and risk control.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    BRACKET = "bracket"
    OCO = "oco"  # One Cancels Other


@dataclass
class OrderLeg:
    """Order leg for multi-leg orders."""
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    leg_id: str = None
    
    def __post_init__(self):
        if self.leg_id is None:
            self.leg_id = str(uuid.uuid4())


@dataclass
class Order:
    """Order data structure."""
    order_id: str
    order_type: OrderType
    legs: List[OrderLeg]
    status: OrderStatus
    created_time: datetime
    updated_time: datetime
    filled_quantity: int = 0
    remaining_quantity: int = 0
    average_price: float = 0.0
    total_commission: float = 0.0
    parent_order_id: Optional[str] = None
    child_order_ids: List[str] = None
    
    def __post_init__(self):
        if self.child_order_ids is None:
            self.child_order_ids = []
        
        # Calculate total quantity
        self.remaining_quantity = sum(leg.quantity for leg in self.legs)
    
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED
    
    def is_active(self) -> bool:
        """Check if order is active (not filled, cancelled, or rejected)."""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]
    
    def get_fill_percentage(self) -> float:
        """Get fill percentage."""
        if self.remaining_quantity == 0:
            return 1.0
        return self.filled_quantity / (self.filled_quantity + self.remaining_quantity)


@dataclass
class Fill:
    """Fill data structure."""
    fill_id: str
    order_id: str
    leg_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    commission: float
    timestamp: datetime


class OrderManager:
    """
    Order management system for multi-leg orders and risk control.
    """
    
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.fills: List[Fill] = []
        self.order_counter = 0
        
        # Risk controls
        self.max_open_orders = 100
        self.max_order_size = 10000
        self.max_daily_orders = 1000
        
        # Order tracking
        self.daily_order_count = 0
        self.last_reset_date = datetime.now().date()
    
    def create_order(
        self,
        order_type: OrderType,
        legs: List[OrderLeg],
        parent_order_id: Optional[str] = None
    ) -> str:
        """
        Create a new order.
        
        Args:
            order_type: Type of order
            legs: List of order legs
            parent_order_id: Parent order ID for bracket orders
            
        Returns:
            Order ID
        """
        # Check risk limits
        if not self._check_order_limits():
            raise ValueError("Order limits exceeded")
        
        # Generate order ID
        order_id = f"ORD_{self.order_counter:06d}"
        self.order_counter += 1
        
        # Create order
        order = Order(
            order_id=order_id,
            order_type=order_type,
            legs=legs,
            status=OrderStatus.PENDING,
            created_time=datetime.now(),
            updated_time=datetime.now(),
            parent_order_id=parent_order_id
        )
        
        # Store order
        self.orders[order_id] = order
        
        # Update daily count
        self._update_daily_count()
        
        logger.info(f"Created order {order_id} with {len(legs)} legs")
        
        return order_id
    
    def create_bracket_order(
        self,
        entry_leg: OrderLeg,
        stop_loss_leg: OrderLeg,
        take_profit_leg: OrderLeg
    ) -> str:
        """
        Create a bracket order (entry + stop loss + take profit).
        
        Args:
            entry_leg: Entry leg
            stop_loss_leg: Stop loss leg
            take_profit_leg: Take profit leg
            
        Returns:
            Parent order ID
        """
        # Create parent order for entry
        parent_order_id = self.create_order(OrderType.MARKET, [entry_leg])
        
        # Create child orders for stop loss and take profit
        stop_order_id = self.create_order(
            OrderType.STOP,
            [stop_loss_leg],
            parent_order_id
        )
        
        take_order_id = self.create_order(
            OrderType.LIMIT,
            [take_profit_leg],
            parent_order_id
        )
        
        # Link child orders to parent
        self.orders[parent_order_id].child_order_ids = [stop_order_id, take_order_id]
        
        logger.info(f"Created bracket order {parent_order_id} with children {stop_order_id}, {take_order_id}")
        
        return parent_order_id
    
    def create_oco_order(
        self,
        leg1: OrderLeg,
        leg2: OrderLeg
    ) -> str:
        """
        Create an OCO (One Cancels Other) order.
        
        Args:
            leg1: First leg
            leg2: Second leg
            
        Returns:
            Order ID
        """
        # Create OCO order with both legs
        order_id = self.create_order(OrderType.OCO, [leg1, leg2])
        
        logger.info(f"Created OCO order {order_id}")
        
        return order_id
    
    def submit_order(self, order_id: str) -> bool:
        """
        Submit an order to the broker.
        
        Args:
            order_id: Order ID to submit
            
        Returns:
            Success status
        """
        if order_id not in self.orders:
            logger.error(f"Order {order_id} not found")
            return False
        
        order = self.orders[order_id]
        
        if order.status != OrderStatus.PENDING:
            logger.error(f"Order {order_id} is not in pending status")
            return False
        
        try:
            # Submit to broker (this would integrate with your broker)
            success = self._submit_to_broker(order)
            
            if success:
                order.status = OrderStatus.SUBMITTED
                order.updated_time = datetime.now()
                logger.info(f"Order {order_id} submitted successfully")
            else:
                order.status = OrderStatus.REJECTED
                order.updated_time = datetime.now()
                logger.error(f"Order {order_id} submission failed")
            
            return success
            
        except Exception as e:
            logger.error(f"Error submitting order {order_id}: {e}")
            order.status = OrderStatus.REJECTED
            order.updated_time = datetime.now()
            return False
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Success status
        """
        if order_id not in self.orders:
            logger.error(f"Order {order_id} not found")
            return False
        
        order = self.orders[order_id]
        
        if not order.is_active():
            logger.error(f"Order {order_id} is not active")
            return False
        
        try:
            # Cancel with broker
            success = self._cancel_with_broker(order)
            
            if success:
                order.status = OrderStatus.CANCELLED
                order.updated_time = datetime.now()
                logger.info(f"Order {order_id} cancelled successfully")
            else:
                logger.error(f"Failed to cancel order {order_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def update_order_status(self, order_id: str, status: OrderStatus):
        """Update order status."""
        if order_id in self.orders:
            self.orders[order_id].status = status
            self.orders[order_id].updated_time = datetime.now()
    
    def add_fill(
        self,
        order_id: str,
        leg_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        commission: float
    ) -> str:
        """
        Add a fill to an order.
        
        Args:
            order_id: Order ID
            leg_id: Leg ID
            symbol: Symbol
            side: Side
            quantity: Quantity filled
            price: Fill price
            commission: Commission
            
        Returns:
            Fill ID
        """
        if order_id not in self.orders:
            logger.error(f"Order {order_id} not found")
            return None
        
        # Generate fill ID
        fill_id = f"FILL_{len(self.fills):06d}"
        
        # Create fill
        fill = Fill(
            fill_id=fill_id,
            order_id=order_id,
            leg_id=leg_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            commission=commission,
            timestamp=datetime.now()
        )
        
        # Add fill
        self.fills.append(fill)
        
        # Update order
        order = self.orders[order_id]
        order.filled_quantity += quantity
        order.remaining_quantity -= quantity
        order.total_commission += commission
        
        # Update average price
        if order.filled_quantity > 0:
            order.average_price = (
                (order.average_price * (order.filled_quantity - quantity) + price * quantity) 
                / order.filled_quantity
            )
        
        # Update order status
        if order.remaining_quantity == 0:
            order.status = OrderStatus.FILLED
        else:
            order.status = OrderStatus.PARTIALLY_FILLED
        
        order.updated_time = datetime.now()
        
        logger.info(f"Added fill {fill_id} for order {order_id}")
        
        return fill_id
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)
    
    def get_active_orders(self) -> List[Order]:
        """Get all active orders."""
        return [order for order in self.orders.values() if order.is_active()]
    
    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Get orders by status."""
        return [order for order in self.orders.values() if order.status == status]
    
    def get_fills_for_order(self, order_id: str) -> List[Fill]:
        """Get fills for an order."""
        return [fill for fill in self.fills if fill.order_id == order_id]
    
    def get_order_summary(self) -> Dict[str, Any]:
        """Get order summary statistics."""
        total_orders = len(self.orders)
        active_orders = len(self.get_active_orders())
        filled_orders = len(self.get_orders_by_status(OrderStatus.FILLED))
        cancelled_orders = len(self.get_orders_by_status(OrderStatus.CANCELLED))
        rejected_orders = len(self.get_orders_by_status(OrderStatus.REJECTED))
        
        total_fills = len(self.fills)
        total_commission = sum(fill.commission for fill in self.fills)
        
        return {
            'total_orders': total_orders,
            'active_orders': active_orders,
            'filled_orders': filled_orders,
            'cancelled_orders': cancelled_orders,
            'rejected_orders': rejected_orders,
            'total_fills': total_fills,
            'total_commission': total_commission,
            'daily_order_count': self.daily_order_count
        }
    
    def _check_order_limits(self) -> bool:
        """Check if order limits are within bounds."""
        # Check max open orders
        if len(self.get_active_orders()) >= self.max_open_orders:
            logger.warning("Maximum open orders reached")
            return False
        
        # Check daily order count
        if self.daily_order_count >= self.max_daily_orders:
            logger.warning("Maximum daily orders reached")
            return False
        
        return True
    
    def _update_daily_count(self):
        """Update daily order count."""
        current_date = datetime.now().date()
        
        if current_date != self.last_reset_date:
            self.daily_order_count = 0
            self.last_reset_date = current_date
        
        self.daily_order_count += 1
    
    def _submit_to_broker(self, order: Order) -> bool:
        """Submit order to broker (placeholder)."""
        # This would integrate with your broker API
        # For now, just return True
        return True
    
    def _cancel_with_broker(self, order: Order) -> bool:
        """Cancel order with broker (placeholder)."""
        # This would integrate with your broker API
        # For now, just return True
        return True
    
    def cleanup_old_orders(self, days: int = 30):
        """Clean up old orders."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        old_orders = [
            order_id for order_id, order in self.orders.items()
            if order.created_time < cutoff_date and order.status in [
                OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED
            ]
        ]
        
        for order_id in old_orders:
            del self.orders[order_id]
        
        logger.info(f"Cleaned up {len(old_orders)} old orders")
    
    def export_orders(self, filename: str):
        """Export orders to CSV file."""
        if not self.orders:
            return
        
        orders_data = []
        for order in self.orders.values():
            orders_data.append({
                'order_id': order.order_id,
                'order_type': order.order_type.value,
                'status': order.status.value,
                'created_time': order.created_time,
                'updated_time': order.updated_time,
                'filled_quantity': order.filled_quantity,
                'remaining_quantity': order.remaining_quantity,
                'average_price': order.average_price,
                'total_commission': order.total_commission,
                'parent_order_id': order.parent_order_id
            })
        
        df = pd.DataFrame(orders_data)
        df.to_csv(filename, index=False)
        logger.info(f"Exported {len(orders_data)} orders to {filename}")
    
    def export_fills(self, filename: str):
        """Export fills to CSV file."""
        if not self.fills:
            return
        
        fills_data = []
        for fill in self.fills:
            fills_data.append({
                'fill_id': fill.fill_id,
                'order_id': fill.order_id,
                'leg_id': fill.leg_id,
                'symbol': fill.symbol,
                'side': fill.side,
                'quantity': fill.quantity,
                'price': fill.price,
                'commission': fill.commission,
                'timestamp': fill.timestamp
            })
        
        df = pd.DataFrame(fills_data)
        df.to_csv(filename, index=False)
        logger.info(f"Exported {len(fills_data)} fills to {filename}")
