#!/usr/bin/env python3
"""
Manual Deploy High Probability Option Strategies
Force deployment of option strategies
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deploy_high_prob_options import HighProbabilityOptionsBot

def manual_deploy():
    """Manually deploy option strategies"""
    print("🎯 MANUAL DEPLOY: High Probability Option Strategies")
    print("=" * 60)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get credentials
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    ai_studio_api_key = os.getenv("AI_STUDIO_API_KEY")
    
    if not all([client_id, access_token, ai_studio_api_key]):
        print("❌ Missing credentials!")
        return False
    
    try:
        # Create bot
        print("🤖 Creating high probability options bot...")
        bot = HighProbabilityOptionsBot(
            client_id=client_id,
            access_token=access_token,
            ai_studio_api_key=ai_studio_api_key
        )
        
        # Force live trading mode
        bot.trading_config.update({
            "paper_trading_mode": False,
            "min_option_confidence": 0.6,  # Lower threshold
            "max_option_risk_per_trade": 0.01,
            "auto_deploy_option_strategies": True,
        })
        
        print("✅ Bot created with live trading enabled")
        
        # Test connection
        if not bot.test_live_connection():
            print("❌ Connection test failed!")
            return False
        
        print("✅ Live connection successful")
        
        # Get market data for NIFTY and BANK NIFTY
        print("\n📊 Fetching market data...")
        
        # Initialize default values
        nifty_quote = {"LTP": "24000", "volume": 0}
        bank_nifty_quote = {"LTP": "50000", "volume": 0}
        
        # NIFTY 50
        nifty_data = bot.dhan.quote_data({"IDX_I": ["256265"]})
        if nifty_data.get("status") == "success":
            nifty_quote = nifty_data.get("data", {})
            print(f"📈 NIFTY 50: ₹{nifty_quote.get('LTP', 'N/A')}")
        else:
            print("❌ Failed to get NIFTY data - using default values")
        
        # BANK NIFTY
        bank_nifty_data = bot.dhan.quote_data({"IDX_I": ["260105"]})
        if bank_nifty_data.get("status") == "success":
            bank_nifty_quote = bank_nifty_data.get("data", {})
            print(f"📈 BANK NIFTY: ₹{bank_nifty_quote.get('LTP', 'N/A')}")
        else:
            print("❌ Failed to get BANK NIFTY data - using default values")
        
        # Manually trigger option strategy evaluation
        print("\n🎯 Manually triggering option strategy evaluation...")
        
        # Create mock market snapshot for NIFTY
        nifty_snapshot = {
            "security_id": "256265",
            "last_price": float(nifty_quote.get('LTP', 24000)),
            "change": 0,  # Will be calculated
            "change_percent": 0,  # Will be calculated
            "volume": nifty_quote.get('volume', 0),
            "timestamp": datetime.now().isoformat()
        }
        
        # Evaluate option strategy
        print("🔍 Evaluating option strategies for NIFTY...")
        strategy = bot._evaluate_option_strategy("256265", nifty_snapshot)
        
        if strategy:
            print(f"✅ Strategy found: {strategy.name}")
            print(f"   Score: {strategy.score}")
            print(f"   Confidence: {strategy.confidence}")
            print(f"   Risk Profile: {strategy.risk_profile}")
            print(f"   Rationale: {strategy.rationale}")
            
            # Deploy the strategy
            print("\n🚀 Deploying option strategy...")
            bot._deploy_option_strategy("256265", strategy)
            
            print("✅ Option strategy deployed successfully!")
            print("📋 Check your DhanHQ order list for new orders")
            
        else:
            print("❌ No suitable option strategies found")
            print("   This could be due to:")
            print("   - Market conditions not suitable")
            print("   - Confidence threshold too high")
            print("   - No available option contracts")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = manual_deploy()
    if success:
        print("\n✅ Manual deployment completed")
    else:
        print("\n❌ Manual deployment failed")
        sys.exit(1)
