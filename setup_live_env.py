#!/usr/bin/env python3
"""
Setup Live Environment for High Probability Option Strategies
Quick setup script for live trading deployment
"""

import os
import sys

def setup_live_environment():
    """Setup live trading environment"""
    print("🔧 Setting up Live Trading Environment")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = ".env"
    if not os.path.exists(env_file):
        print("📝 Creating .env file...")
        with open(env_file, "w") as f:
            f.write("# Live Trading Credentials\n")
            f.write("DHAN_LIVE_CLIENT_ID=your_live_client_id_here\n")
            f.write("DHAN_LIVE_ACCESS_TOKEN=your_live_access_token_here\n")
            f.write("AI_STUDIO_API_KEY=your_ai_studio_api_key_here\n")
        print("✅ .env file created")
    else:
        print("✅ .env file already exists")
    
    # Check required packages
    print("\n📦 Checking required packages...")
    try:
        import requests
        print("✅ requests package available")
    except ImportError:
        print("❌ requests package missing - install with: pip install requests")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv package available")
    except ImportError:
        print("❌ python-dotenv package missing - install with: pip install python-dotenv")
    
    # Check DhanHQ package
    try:
        from dhanhq import DhanContext, dhanhq
        print("✅ DhanHQ package available")
    except ImportError:
        print("❌ DhanHQ package missing - install with: pip install dhanhq")
    
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your live credentials")
    print("2. Run: python quick_deploy_options.py")
    print("3. Monitor the high probability option strategies")
    
    print("\n🎯 High Probability Option Strategies Available:")
    print("   - Bull Call Spread (Bullish)")
    print("   - Bear Put Spread (Bearish)")
    print("   - Iron Condor (Neutral)")
    print("   - Bull Put Spread (Income)")
    print("   - Bear Call Spread (Income)")
    print("   - Iron Butterfly (Range-bound)")
    print("   - Long Straddle (Volatility)")
    print("   - Long Strangle (Volatility)")
    
    print("\n🛡️ Safety Features:")
    print("   - Paper trading mode enabled")
    print("   - High confidence thresholds (85%+)")
    print("   - Low risk per trade (0.5%)")
    print("   - Enhanced logging and monitoring")
    print("   - Real-time strategy evaluation")

if __name__ == "__main__":
    setup_live_environment()
