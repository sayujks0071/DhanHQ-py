#!/usr/bin/env python3
"""
Simple Live Deploy - Place a basic order to test the system
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deploy_high_prob_options import HighProbabilityOptionsBot

def simple_live_deploy():
    """Deploy a simple order to test the system"""
    print("🚀 SIMPLE LIVE DEPLOY: Test Order Placement")
    print("=" * 60)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💰 PLACING A TEST ORDER")
    
    # Get credentials
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    ai_studio_api_key = os.getenv("AI_STUDIO_API_KEY")
    
    if not all([client_id, access_token, ai_studio_api_key]):
        print("❌ Missing credentials!")
        return False
    
    try:
        # Create bot
        print("🤖 Creating bot...")
        bot = HighProbabilityOptionsBot(
            client_id=client_id,
            access_token=access_token,
            ai_studio_api_key=ai_studio_api_key
        )
        
        print("✅ Bot created successfully")
        
        # Test connection
        if not bot.test_live_connection():
            print("❌ Connection test failed!")
            return False
        
        print("✅ Live connection successful")
        
        # Place a simple test order (buy 1 share of a liquid stock)
        print("\n📋 Placing a simple test order...")
        
        # Use a liquid stock like HDFC Bank (security ID: 1333)
        test_order_params = {
            "security_id": "1333",  # HDFC Bank
            "exchange_segment": "NSE_EQ",
            "transaction_type": "BUY",
            "quantity": 1,
            "order_type": "MARKET",
            "product_type": "CNC",
            "validity": "DAY",
            "price": 0.0  # Market order
        }
        
        print(f"📊 Order details:")
        print(f"   Symbol: HDFC Bank (1333)")
        print(f"   Action: BUY")
        print(f"   Quantity: 1")
        print(f"   Type: Market Order")
        
        # Place the order
        order_response = bot.dhan.place_order(**test_order_params)
        
        if order_response.get("status") == "success":
            order_id = order_response.get("data", {}).get("orderId")
            print(f"✅ Test order placed successfully!")
            print(f"📋 Order ID: {order_id}")
            print(f"📊 Check your DhanHQ order list for this order")
            
            # Check orders to confirm
            print("\n🔍 Checking order status...")
            orders = bot.dhan.get_order_list()
            if orders.get("status") == "success":
                order_data = orders.get("data", [])
                print(f"📋 Total orders today: {len(order_data)}")
                
                # Find our order
                for order in order_data:
                    if order.get("orderId") == order_id:
                        print(f"✅ Found our order:")
                        print(f"   Order ID: {order.get('orderId')}")
                        print(f"   Symbol: {order.get('tradingSymbol')}")
                        print(f"   Type: {order.get('transactionType')} {order.get('orderType')}")
                        print(f"   Quantity: {order.get('quantity')}")
                        print(f"   Status: {order.get('orderStatus')}")
                        print(f"   Time: {order.get('createTime')}")
                        break
            else:
                print("❌ Failed to fetch order list")
            
        else:
            print(f"❌ Test order failed: {order_response.get('remarks', 'Unknown error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 This will place a simple test order to verify the system works")
    print("💰 Order: Buy 1 share of HDFC Bank (Market Order)")
    print()
    
    success = simple_live_deploy()
    if success:
        print("\n✅ Simple live deployment completed successfully!")
        print("🎯 The system is working - you can now see orders in your DhanHQ order list")
    else:
        print("\n❌ Simple live deployment failed")
        sys.exit(1)
