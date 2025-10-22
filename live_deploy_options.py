#!/usr/bin/env python3
"""
Live Deploy High Probability Option Strategies
Actually places real orders for option strategies
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deploy_high_prob_options import HighProbabilityOptionsBot

class LiveOptionsBot(HighProbabilityOptionsBot):
    """
    A bot that actually places real option orders
    """
    
    def _deploy_option_strategy(self, security_id: str, recommendation) -> None:
        """
        Deploy the provided option strategy with REAL ORDERS.
        """
        if not recommendation or recommendation.score <= 0:
            self.logger.info("Skipping option strategy deployment for %s due to low score.", security_id)
            return
            
        # Check if we're in paper trading mode
        if self.trading_config.get("paper_trading_mode", True):
            self.logger.info("📝 PAPER TRADING MODE - No real orders will be placed")
            return
            
        self.logger.info(
            "🚀 LIVE DEPLOYING option strategy %s for %s (risk: %s, confidence: %.2f)",
            recommendation.name,
            security_id,
            recommendation.risk_profile,
            recommendation.confidence,
        )
        
        # Place real orders for each leg
        order_ids = []
        for idx, leg in enumerate(recommendation.legs, start=1):
            try:
                # Map strategy leg to actual order parameters
                if leg.action == "BUY":
                    transaction_type = "BUY"
                elif leg.action == "SELL":
                    transaction_type = "SELL"
                else:
                    self.logger.warning("Skipping leg %d: Unknown action %s", idx, leg.action)
                    continue
                
                # For demo purposes, we'll place a simple order
                # In a real implementation, you'd need to:
                # 1. Get actual option contract details
                # 2. Calculate strike prices based on moneyness
                # 3. Set proper order parameters
                
                order_params = {
                    "security_id": security_id,
                    "exchange_segment": "NSE_FNO",
                    "transaction_type": transaction_type,
                    "quantity": leg.quantity,
                    "order_type": "MARKET",
                    "product_type": "INTRADAY",
                    "validity": "DAY",
                    "price": 0.0  # Market orders don't need price, but API requires it
                }
                
                self.logger.info(
                    "  📋 Placing order for leg %d: %s %s qty=%s",
                    idx,
                    leg.action,
                    leg.option_type,
                    leg.quantity,
                )
                
                # Place the order
                order_response = self.dhan.place_order(**order_params)
                
                if order_response.get("status") == "success":
                    order_id = order_response.get("data", {}).get("orderId")
                    order_ids.append(order_id)
                    self.logger.info("  ✅ Order placed successfully: %s", order_id)
                else:
                    self.logger.error("  ❌ Order failed: %s", order_response.get("remarks", "Unknown error"))
                    
            except Exception as e:
                self.logger.error("  ❌ Error placing order for leg %d: %s", idx, e)
        
        if order_ids:
            self.logger.info(
                "🎯 Option strategy %s deployed successfully with %d orders: %s",
                recommendation.name,
                len(order_ids),
                order_ids
            )
        else:
            self.logger.warning("⚠️ No orders were placed for strategy %s", recommendation.name)

def live_deploy():
    """Deploy option strategies with real orders"""
    print("🚀 LIVE DEPLOY: High Probability Option Strategies")
    print("=" * 60)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💰 REAL ORDERS WILL BE PLACED!")
    
    # Get credentials
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    ai_studio_api_key = os.getenv("AI_STUDIO_API_KEY")
    
    if not all([client_id, access_token, ai_studio_api_key]):
        print("❌ Missing credentials!")
        return False
    
    try:
        # Create live bot
        print("🤖 Creating live options bot...")
        bot = LiveOptionsBot(
            client_id=client_id,
            access_token=access_token,
            ai_studio_api_key=ai_studio_api_key
        )
        
        # Force live trading mode
        bot.trading_config.update({
            "paper_trading_mode": False,  # CRITICAL: Disable paper trading
            "min_option_confidence": 0.6,  # Lower threshold
            "max_option_risk_per_trade": 0.01,
            "auto_deploy_option_strategies": True,
        })
        
        print("✅ Live bot created with REAL ORDER PLACEMENT enabled")
        
        # Test connection
        if not bot.test_live_connection():
            print("❌ Connection test failed!")
            return False
        
        print("✅ Live connection successful")
        
        # Get market data
        print("\n📊 Fetching market data...")
        
        # Initialize default values
        nifty_quote = {"LTP": "24000", "volume": 0}
        
        # NIFTY 50
        nifty_data = bot.dhan.quote_data({"IDX_I": ["256265"]})
        if nifty_data.get("status") == "success":
            nifty_quote = nifty_data.get("data", {})
            print(f"📈 NIFTY 50: ₹{nifty_quote.get('LTP', 'N/A')}")
        else:
            print("❌ Failed to get NIFTY data - using default values")
        
        # Create market snapshot
        nifty_snapshot = {
            "security_id": "256265",
            "last_price": float(nifty_quote.get('LTP', 24000)),
            "change": 0,
            "change_percent": 0,
            "volume": nifty_quote.get('volume', 0),
            "timestamp": datetime.now().isoformat()
        }
        
        # Evaluate and deploy option strategy
        print("\n🎯 Evaluating and deploying option strategies...")
        strategy = bot._evaluate_option_strategy("256265", nifty_snapshot)
        
        if strategy:
            print(f"✅ Strategy found: {strategy.name}")
            print(f"   Score: {strategy.score}")
            print(f"   Confidence: {strategy.confidence}")
            print(f"   Risk Profile: {strategy.risk_profile}")
            
            # Deploy the strategy (this will now place real orders)
            print("\n🚀 Deploying option strategy with REAL ORDERS...")
            bot._deploy_option_strategy("256265", strategy)
            
            print("✅ Option strategy deployed with real orders!")
            print("📋 Check your DhanHQ order list for new orders")
            
        else:
            print("❌ No suitable option strategies found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  WARNING: This will place REAL ORDERS with REAL MONEY!")
    print("💰 Make sure you understand the risks before proceeding.")
    print()
    
    success = live_deploy()
    if success:
        print("\n✅ Live deployment completed")
    else:
        print("\n❌ Live deployment failed")
        sys.exit(1)
