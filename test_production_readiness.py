#!/usr/bin/env python3
"""
Test Production Readiness for Live Trading
Comprehensive checks before going live
"""

import os
import sys
from datetime import datetime, time
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_production_readiness():
    """Run comprehensive production readiness tests"""
    print("🧪 PRODUCTION READINESS TEST")
    print("=" * 50)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load environment variables
    load_dotenv()
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Environment Variables
    print("🔍 Test 1: Environment Variables")
    total_tests += 1
    
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    ai_key = os.getenv("AI_STUDIO_API_KEY")
    
    if all([client_id, access_token, ai_key]):
        print("   ✅ All required environment variables present")
        tests_passed += 1
    else:
        print("   ❌ Missing environment variables:")
        if not client_id:
            print("      - DHAN_LIVE_CLIENT_ID")
        if not access_token:
            print("      - DHAN_LIVE_ACCESS_TOKEN")
        if not ai_key:
            print("      - AI_STUDIO_API_KEY")
    
    # Test 2: API Connection
    print("\n🔍 Test 2: API Connection")
    total_tests += 1
    
    try:
        from deploy_high_prob_options import HighProbabilityOptionsBot
        
        bot = HighProbabilityOptionsBot(
            client_id=client_id,
            access_token=access_token,
            ai_studio_api_key=ai_key
        )
        
        if bot.test_live_connection():
            print("   ✅ Live API connection successful")
            tests_passed += 1
        else:
            print("   ❌ Live API connection failed")
    except Exception as e:
        print(f"   ❌ Error creating bot: {e}")
    
    # Test 3: Trading Configuration
    print("\n🔍 Test 3: Trading Configuration")
    total_tests += 1
    
    try:
        # Check if live trading is enabled
        if bot.trading_config.get("paper_trading_mode") == False:
            print("   ✅ Live trading mode enabled")
            tests_passed += 1
        else:
            print("   ⚠️ Paper trading mode still enabled")
            print("   💡 Run: python enable_live_trading.py")
    except Exception as e:
        print(f"   ❌ Error checking trading config: {e}")
    
    # Test 4: Risk Management
    print("\n🔍 Test 4: Risk Management")
    total_tests += 1
    
    try:
        risk_per_trade = bot.trading_config.get("max_option_risk_per_trade", 0)
        max_position = bot.trading_config.get("max_position_size", 0)
        daily_trades = bot.trading_config.get("max_daily_trades", 0)
        
        if risk_per_trade <= 0.02 and max_position > 0 and daily_trades > 0:
            print("   ✅ Risk management parameters configured")
            print(f"      - Max risk per trade: {risk_per_trade*100}%")
            print(f"      - Max position size: {max_position}")
            print(f"      - Max daily trades: {daily_trades}")
            tests_passed += 1
        else:
            print("   ⚠️ Risk management parameters need review")
    except Exception as e:
        print(f"   ❌ Error checking risk management: {e}")
    
    # Test 5: Market Hours
    print("\n🔍 Test 5: Market Hours Check")
    total_tests += 1
    
    try:
        current_time = datetime.now().time()
        market_start = time(9, 15)  # 9:15 AM
        market_end = time(15, 30)   # 3:30 PM
        
        if market_start <= current_time <= market_end:
            print("   ✅ Market is currently open")
            tests_passed += 1
        else:
            print("   ⚠️ Market is currently closed")
            print("   💡 Live trading will start when market opens")
    except Exception as e:
        print(f"   ❌ Error checking market hours: {e}")
    
    # Test 6: Available Funds
    print("\n🔍 Test 6: Available Funds")
    total_tests += 1
    
    try:
        funds = bot._get_available_funds()
        if funds and funds > 1000:  # Minimum 1000 for safety
            print(f"   ✅ Sufficient funds available: ₹{funds:,.2f}")
            tests_passed += 1
        else:
            print(f"   ⚠️ Low funds available: ₹{funds:,.2f}")
            print("   💡 Consider adding more funds for live trading")
    except Exception as e:
        print(f"   ❌ Error checking funds: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 PRODUCTION READINESS SUMMARY")
    print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED - READY FOR LIVE TRADING!")
        print("🚀 You can now run: python enable_live_trading.py")
        return True
    elif tests_passed >= total_tests * 0.8:
        print("⚠️ MOSTLY READY - Review failed tests")
        print("💡 Fix the issues above before going live")
        return False
    else:
        print("❌ NOT READY - Multiple issues found")
        print("🛠️ Please fix the issues above before going live")
        return False

if __name__ == "__main__":
    success = test_production_readiness()
    if not success:
        sys.exit(1)
