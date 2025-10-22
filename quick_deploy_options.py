#!/usr/bin/env python3
"""
Quick Deploy High Probability Option Strategies
Immediate deployment script for live market
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deploy_high_prob_options import HighProbabilityOptionsBot

def quick_deploy():
    """Quick deployment for immediate live trading"""
    print("🚀 QUICK DEPLOY: High Probability Option Strategies")
    print("=" * 60)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Market is LIVE - Deploying immediately")
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    ai_studio_api_key = os.getenv("AI_STUDIO_API_KEY")
    
    if not all([client_id, access_token, ai_studio_api_key]):
        print("❌ Missing credentials!")
        print("\n📋 Set these environment variables:")
        print("   export DHAN_LIVE_CLIENT_ID='your_client_id'")
        print("   export DHAN_LIVE_ACCESS_TOKEN='your_access_token'")
        print("   export AI_STUDIO_API_KEY='your_ai_key'")
        return False
    
    try:
        # Create bot with live credentials
        print("🤖 Creating high probability options bot...")
        bot = HighProbabilityOptionsBot(
            client_id=client_id,
            access_token=access_token,
            ai_studio_api_key=ai_studio_api_key
        )
        
        print("✅ Bot created successfully")
        
        # Test connection
        print("🔍 Testing live connection...")
        if not bot.test_live_connection():
            print("❌ Connection test failed!")
            return False
        
        print("✅ Live connection successful")
        
        # Configure for immediate deployment
        bot.trading_config.update({
            "paper_trading_mode": False,  # Live trading enabled
            "min_option_confidence": 0.8,  # Slightly lower for more opportunities
            "max_option_risk_per_trade": 0.01,  # 1% risk
            "update_interval": 10,  # Faster updates
            "max_daily_trades": 5,  # Allow more trades
        })
        
        # Popular NSE F&O securities for options
        option_securities = [
            "256265",  # NIFTY 50
            "260105",  # BANK NIFTY
        ]
        
        print(f"\n📊 Monitoring option securities:")
        for sec_id in option_securities:
            print(f"   - {sec_id}")
        
        print("\n🎯 Configuration:")
        print(f"   - Paper trading: {bot.trading_config.get('paper_trading_mode', True)}")
        print(f"   - Min confidence: {bot.trading_config.get('min_option_confidence', 0.8)}")
        print(f"   - Max risk: {bot.trading_config.get('max_option_risk_per_trade', 0.01)}")
        print(f"   - Update interval: {bot.trading_config.get('update_interval', 10)}s")
        
        print("\n🚀 Starting high probability options trading...")
        print("⚠️  Press Ctrl+C to stop")
        print("💰 LIVE TRADING mode - Real orders will be placed")
        
        # Start trading
        bot.run_high_probability_options_trading(option_securities)
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Trading stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = quick_deploy()
    if success:
        print("\n✅ High probability options deployment completed")
    else:
        print("\n❌ Deployment failed")
        sys.exit(1)
