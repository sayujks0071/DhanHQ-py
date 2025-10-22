#!/usr/bin/env python3
"""
Check Current Orders and Positions
View your current order status and positions
"""

import os
from dhanhq import DhanContext, dhanhq

def check_orders_and_positions():
    """Check current orders and positions"""
    print("📊 Checking Current Orders and Positions")
    print("=" * 50)
    
    # Get credentials
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    
    if not all([client_id, access_token]):
        print("❌ Missing credentials!")
        return
    
    try:
        # Initialize DhanHQ
        dhan_context = DhanContext(client_id, access_token)
        dhan = dhanhq(dhan_context)
        
        print("🔍 Fetching current orders...")
        orders = dhan.get_order_list()
        
        if orders.get("status") == "success":
            order_data = orders.get("data", [])
            print(f"📋 Total orders today: {len(order_data)}")
            
            if order_data:
                print("\n📊 Current Orders:")
                for i, order in enumerate(order_data, 1):
                    print(f"  {i}. Order ID: {order.get('orderId', 'N/A')}")
                    print(f"     Symbol: {order.get('tradingSymbol', 'N/A')}")
                    print(f"     Type: {order.get('transactionType', 'N/A')} {order.get('orderType', 'N/A')}")
                    print(f"     Quantity: {order.get('quantity', 'N/A')}")
                    print(f"     Price: ₹{order.get('price', 'N/A')}")
                    print(f"     Status: {order.get('orderStatus', 'N/A')}")
                    print(f"     Time: {order.get('createTime', 'N/A')}")
                    print()
            else:
                print("📋 No orders found")
        else:
            print("❌ Failed to fetch orders")
        
        print("\n🔍 Fetching current positions...")
        positions = dhan.get_positions()
        
        if positions.get("status") == "success":
            position_data = positions.get("data", [])
            print(f"📊 Total positions: {len(position_data)}")
            
            if position_data:
                print("\n📈 Current Positions:")
                for i, position in enumerate(position_data, 1):
                    print(f"  {i}. Symbol: {position.get('tradingSymbol', 'N/A')}")
                    print(f"     Net Qty: {position.get('netQty', 'N/A')}")
                    print(f"     Avg Price: ₹{position.get('buyAvg', 'N/A')}")
                    print(f"     P&L: ₹{position.get('unrealizedProfit', 'N/A')}")
                    print(f"     Segment: {position.get('exchangeSegment', 'N/A')}")
                    print()
            else:
                print("📊 No open positions")
        else:
            print("❌ Failed to fetch positions")
        
        print("\n🔍 Fetching available funds...")
        funds = dhan.get_fund_limits()
        
        if funds.get("status") == "success":
            fund_data = funds.get("data", {})
            print(f"💰 Available Balance: ₹{fund_data.get('availabelBalance', 'N/A'):,.2f}")
            print(f"💰 Withdrawable Balance: ₹{fund_data.get('withdrawableBalance', 'N/A'):,.2f}")
            print(f"💰 Utilized Amount: ₹{fund_data.get('utilizedAmount', 'N/A'):,.2f}")
        else:
            print("❌ Failed to fetch funds")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_orders_and_positions()
