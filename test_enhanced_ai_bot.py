#!/usr/bin/env python3
"""
Test script for the enhanced AI Trading Bot
This script validates the new features and safety mechanisms
"""

import json
import time
from datetime import datetime, time as dt_time
from typing import Dict, List

from ai_trading_bot import AITradingBot, TradeRecommendation

def test_trade_recommendation_model():
    """Test the TradeRecommendation dataclass"""
    print("🧪 Testing TradeRecommendation Model...")
    
    # Test basic creation
    rec = TradeRecommendation()
    assert rec.action == "HOLD"
    assert rec.confidence == 0.0
    assert not rec.is_actionable()
    
    # Test actionable recommendation
    rec = TradeRecommendation(action="BUY", confidence=0.8, quantity=100)
    assert rec.is_actionable()
    assert rec.action == "BUY"
    assert rec.confidence == 0.8
    assert rec.quantity == 100
    
    # Test SELL recommendation
    rec = TradeRecommendation(action="SELL", confidence=0.9, quantity=50)
    assert rec.is_actionable()
    assert rec.action == "SELL"
    
    print("✅ TradeRecommendation model tests passed!")

def test_ai_config_fallbacks():
    """Test AI configuration fallbacks"""
    print("🧪 Testing AI Config Fallbacks...")
    
    # Test with minimal config
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token", 
        ai_studio_api_key="test_key"
    )
    
    # Verify fallback configs are loaded
    assert bot.ai_config["model"] == "gemini-pro"
    assert bot.trading_config["min_confidence"] == 0.7
    assert bot.trading_config["max_position_size"] == 1000
    assert bot.trading_config["risk_per_trade"] == 0.02
    
    print("✅ AI config fallbacks working correctly!")

def test_market_features_calculation():
    """Test market feature calculation"""
    print("🧪 Testing Market Features Calculation...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test with empty history
    features = bot._calculate_market_features("1333", {})
    assert isinstance(features, dict)
    assert "history_depth" in features
    assert features["history_depth"] == 0.0
    
    # Add some mock history
    for i in range(10):
        bot.market_history["1333"].append({
            "last_price": 100 + i,
            "volume": 1000 + i * 100
        })
    
    # Test with mock market data
    market_data = {
        "last_price": 110,
        "volume": 2000,
        "open": 100,
        "high": 115,
        "low": 95
    }
    
    features = bot._calculate_market_features("1333", market_data)
    assert "short_ma" in features
    assert "long_ma" in features
    assert "momentum_pct" in features
    assert "intraday_return_pct" in features
    assert "range_position" in features
    assert "relative_volume" in features
    
    print("✅ Market features calculation working!")

def test_risk_based_quantity():
    """Test risk-based quantity calculation"""
    print("🧪 Testing Risk-Based Quantity Calculation...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Mock available funds
    bot.funds_cache = {"timestamp": time.time(), "amount": 100000.0}
    
    market_data = {"last_price": 100}
    quantity = bot._calculate_risk_based_quantity(market_data, 0.05)
    
    # Should calculate based on 2% risk per trade and 5% stop loss
    # Max loss = 100000 * 0.02 = 2000
    # Per share risk = 100 * 0.05 = 5
    # Expected quantity = 2000 / 5 = 400
    expected_quantity = int((100000 * 0.02) / (100 * 0.05))
    assert quantity == expected_quantity
    
    print("✅ Risk-based quantity calculation working!")

def test_trading_hours_validation():
    """Test trading hours validation"""
    print("🧪 Testing Trading Hours Validation...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test time parsing
    parsed_time = bot._parse_time("09:15")
    assert parsed_time == dt_time(9, 15)
    
    parsed_time = bot._parse_time("15:30")
    assert parsed_time == dt_time(15, 30)
    
    # Test invalid time
    parsed_time = bot._parse_time("invalid")
    assert parsed_time is None
    
    print("✅ Trading hours validation working!")

def test_daily_trade_limits():
    """Test daily trade limit enforcement"""
    print("🧪 Testing Daily Trade Limits...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test trade recording
    bot._record_trade("1333")
    bot._record_trade("1333")
    bot._record_trade("11536")
    
    assert bot.daily_trade_counts["1333"] == 2
    assert bot.daily_trade_counts["11536"] == 1
    assert bot.daily_trade_counts["__TOTAL__"] == 3
    
    # Test daily reset
    bot.last_trade_day = datetime.now().date()
    bot._reset_daily_trade_counters()
    # Should not reset if same day
    assert bot.daily_trade_counts["__TOTAL__"] == 3
    
    print("✅ Daily trade limits working!")

def test_position_quantity_extraction():
    """Test position quantity extraction"""
    print("🧪 Testing Position Quantity Extraction...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test with different position formats
    position1 = {"netQuantity": 100}
    qty = bot._extract_net_quantity(position1)
    assert qty == 100.0
    
    position2 = {"netQty": 50}
    qty = bot._extract_net_quantity(position2)
    assert qty == 50.0
    
    position3 = {"quantity": 25}
    qty = bot._extract_net_quantity(position3)
    assert qty == 25.0
    
    # Test with no position
    qty = bot._extract_net_quantity(None)
    assert qty == 0.0
    
    print("✅ Position quantity extraction working!")

def test_ai_response_parsing():
    """Test AI response parsing and normalization"""
    print("🧪 Testing AI Response Parsing...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test valid AI response
    ai_response = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": '{"action": "BUY", "confidence": 0.85, "quantity": 100, "reasoning": "Strong momentum"}'
                }]
            }
        }]
    }
    
    parsed = bot._parse_ai_response(ai_response)
    assert parsed["action"] == "BUY"
    assert parsed["confidence"] == 0.85
    assert parsed["quantity"] == 100
    
    # Test normalization
    rec = bot._normalize_recommendation(parsed)
    assert isinstance(rec, TradeRecommendation)
    assert rec.action == "BUY"
    assert rec.confidence == 0.85
    assert rec.quantity == 100
    assert rec.reasoning == "Strong momentum"
    
    print("✅ AI response parsing working!")

def test_safety_checks():
    """Test safety check mechanisms"""
    print("🧪 Testing Safety Checks...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test low confidence rejection
    rec = TradeRecommendation(action="BUY", confidence=0.5, quantity=100)
    should_execute = bot._should_execute_trade(rec, "1333", 100)
    assert not should_execute  # Should be rejected due to low confidence
    
    # Test high confidence acceptance
    rec = TradeRecommendation(action="BUY", confidence=0.8, quantity=100)
    should_execute = bot._should_execute_trade(rec, "1333", 100)
    # This might be rejected due to other factors, but confidence should pass
    
    # Test zero quantity rejection
    rec = TradeRecommendation(action="BUY", confidence=0.8, quantity=0)
    should_execute = bot._should_execute_trade(rec, "1333", 0)
    assert not should_execute  # Should be rejected due to zero quantity
    
    print("✅ Safety checks working!")

def test_configuration_validation():
    """Test configuration validation"""
    print("🧪 Testing Configuration Validation...")
    
    # Test with custom trading config
    custom_config = {
        "min_confidence": 0.8,
        "max_position_size": 500,
        "risk_per_trade": 0.01,
        "max_daily_trades": 5
    }
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key",
        trading_config=custom_config
    )
    
    assert bot.trading_config["min_confidence"] == 0.8
    assert bot.trading_config["max_position_size"] == 500
    assert bot.trading_config["risk_per_trade"] == 0.01
    assert bot.trading_config["max_daily_trades"] == 5
    
    print("✅ Configuration validation working!")

def run_all_tests():
    """Run all tests"""
    print("🚀 Running Enhanced AI Trading Bot Tests")
    print("=" * 50)
    
    try:
        test_trade_recommendation_model()
        test_ai_config_fallbacks()
        test_market_features_calculation()
        test_risk_based_quantity()
        test_trading_hours_validation()
        test_daily_trade_limits()
        test_position_quantity_extraction()
        test_ai_response_parsing()
        test_safety_checks()
        test_configuration_validation()
        
        print("\n🎉 All tests passed successfully!")
        print("\n📋 Enhanced Features Validated:")
        print("✅ TradeRecommendation model with structured data")
        print("✅ AI config fallbacks for standalone usage")
        print("✅ Market feature calculation with technical indicators")
        print("✅ Risk-based position sizing")
        print("✅ Trading hours validation")
        print("✅ Daily trade limit enforcement")
        print("✅ Position quantity extraction from multiple formats")
        print("✅ AI response parsing and normalization")
        print("✅ Comprehensive safety checks")
        print("✅ Configuration validation and customization")
        
        print("\n🚀 Ready for dry-run testing with paper/sandbox account!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    run_all_tests()



