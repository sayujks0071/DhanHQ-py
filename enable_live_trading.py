#!/usr/bin/env python3
"""
Enable Live Trading for High Probability Option Strategies
Switch from paper trading to live trading mode
"""

import os
import sys
from datetime import datetime
from deploy_high_prob_options import HighProbabilityOptionsBot

def enable_live_trading():
    """Enable live trading mode"""
    print("🚀 ENABLING LIVE TRADING MODE")
    print("=" * 50)
    print("⚠️  WARNING: This will place REAL ORDERS with REAL MONEY!")
    print("💰 Available funds will be used for actual trading")
    print()
    
    # Get credentials
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    ai_studio_api_key = os.getenv("AI_STUDIO_API_KEY")
    
    if not all([client_id, access_token, ai_studio_api_key]):
        print("❌ Missing credentials!")
        return False
    
    try:
        # Create bot with live trading enabled
        print("🤖 Creating live trading bot...")
        bot = HighProbabilityOptionsBot(
            client_id=client_id,
            access_token=access_token,
            ai_studio_api_key=ai_studio_api_key
        )
        
        # DISABLE paper trading mode
        bot.trading_config.update({
            "paper_trading_mode": False,  # DISABLE paper trading
            "min_option_confidence": 0.85,  # High confidence required
            "max_option_risk_per_trade": 0.01,  # 1% risk per trade
            "update_interval": 15,  # Slower updates for live trading
            "max_daily_trades": 3,  # Conservative daily limit
            "live_safeguards": True,  # Enhanced safety
            "enhanced_logging": True,  # Full logging
        })
        
        print("✅ Live trading mode ENABLED")
        print("⚠️  Paper trading mode DISABLED")
        print("💰 Real money trading ACTIVE")
        print()
        
        # Test connection
        print("🔍 Testing live connection...")
        if not bot.test_live_connection():
            print("❌ Connection test failed!")
            return False
        
        print("✅ Live connection successful")
        
        # Configure securities for live options trading
        option_securities = [
            "256265",  # NIFTY 50
            "260105",  # BANK NIFTY
        ]
        
        print(f"\n📊 Live trading configuration:")
        print(f"   - Paper trading: {bot.trading_config.get('paper_trading_mode', False)}")
        print(f"   - Min confidence: {bot.trading_config.get('min_option_confidence', 0.85)}")
        print(f"   - Max risk: {bot.trading_config.get('max_option_risk_per_trade', 0.01)}")
        print(f"   - Daily trades: {bot.trading_config.get('max_daily_trades', 3)}")
        print(f"   - Update interval: {bot.trading_config.get('update_interval', 15)}s")
        
        print(f"\n🎯 Monitoring live option securities:")
        for sec_id in option_securities:
            print(f"   - {sec_id}")
        
        print("\n🚨 LIVE TRADING WARNINGS:")
        print("   ⚠️  Real money will be used")
        print("   ⚠️  Orders will appear in your order list")
        print("   ⚠️  Positions will affect your demat balance")
        print("   ⚠️  Market risk applies")
        
        print("\n🚀 Starting LIVE high probability options trading...")
        print("⚠️  Press Ctrl+C to stop")
        
        # Start live trading
        bot.run_high_probability_options_trading(option_securities)
        
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Live trading stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("🎯 Enable Live Trading for High Probability Option Strategies")
    print("=" * 70)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Confirm with user
    print("⚠️  IMPORTANT: This will enable REAL MONEY TRADING!")
    print("💰 Your available funds will be used for actual option strategies")
    print("📊 Orders will appear in your DhanHQ order list")
    print()
    
    response = input("Are you sure you want to enable live trading? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Live trading not enabled")
        return
    
    success = enable_live_trading()
    if success:
        print("\n✅ Live trading deployment completed")
    else:
        print("\n❌ Live trading deployment failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
