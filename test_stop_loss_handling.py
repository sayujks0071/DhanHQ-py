#!/usr/bin/env python3
"""
Focused test for stop-loss handling improvements
Tests the enhanced _calculate_risk_based_quantity with varied stop-loss types
"""

import unittest
import time
from ai_trading_bot import AITradingBot, TradeRecommendation

class TestStopLossHandling(unittest.TestCase):
    """Test suite for stop-loss handling improvements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = AITradingBot(
            client_id="test_client",
            access_token="test_token",
            ai_studio_api_key="test_key"
        )
        
        # Mock available funds
        self.bot.funds_cache = {"timestamp": time.time(), "amount": 100000.0}
    
    def test_percentage_stop_loss(self):
        """Test percentage-based stop-loss handling"""
        # Test case 1: 5% stop-loss
        market_data = {"last_price": 1600}
        stop_loss_pct = 0.05  # 5%
        quantity = self.bot._calculate_risk_based_quantity(market_data, stop_loss_pct)
        
        # Expected: (100000 * 0.02) / (1600 * 0.05) = 2000 / 80 = 25
        expected_quantity = int((100000 * 0.02) / (1600 * 0.05))
        self.assertEqual(quantity, expected_quantity)
        
        # Test case 2: 3% stop-loss (tighter)
        stop_loss_pct = 0.03  # 3%
        quantity = self.bot._calculate_risk_based_quantity(market_data, stop_loss_pct)
        
        # Expected: (100000 * 0.02) / (1600 * 0.03) = 2000 / 48 = 41
        expected_quantity = int((100000 * 0.02) / (1600 * 0.03))
        self.assertEqual(quantity, expected_quantity)
        
        # Test case 3: 1% stop-loss (very tight)
        stop_loss_pct = 0.01  # 1%
        quantity = self.bot._calculate_risk_based_quantity(market_data, stop_loss_pct)
        
        # Expected: (100000 * 0.02) / (1600 * 0.01) = 2000 / 16 = 125
        expected_quantity = int((100000 * 0.02) / (1600 * 0.01))
        self.assertEqual(quantity, expected_quantity)
    
    def test_absolute_price_stop_loss(self):
        """Test absolute price-based stop-loss handling"""
        # Test case 1: Absolute stop-loss at ₹1500 (current price ₹1600)
        market_data = {"last_price": 1600}
        stop_loss_price = 1500  # Absolute price
        quantity = self.bot._calculate_risk_based_quantity(market_data, stop_loss_price)
        
        # Expected: (100000 * 0.02) / (1600 - 1500) = 2000 / 100 = 20
        expected_quantity = int((100000 * 0.02) / (1600 - 1500))
        self.assertEqual(quantity, expected_quantity)
        
        # Test case 2: Absolute stop-loss at ₹1400 (current price ₹1600)
        stop_loss_price = 1400  # Absolute price
        quantity = self.bot._calculate_risk_based_quantity(market_data, stop_loss_price)
        
        # Expected: (100000 * 0.02) / (1600 - 1400) = 2000 / 200 = 10
        expected_quantity = int((100000 * 0.02) / (1600 - 1400))
        self.assertEqual(quantity, expected_quantity)
        
        # Test case 3: Absolute stop-loss at ₹800 (current price ₹1000)
        market_data = {"last_price": 1000}
        stop_loss_price = 800  # Absolute price
        quantity = self.bot._calculate_risk_based_quantity(market_data, stop_loss_price)
        
        # Expected: (100000 * 0.02) / (1000 - 800) = 2000 / 200 = 10
        expected_quantity = int((100000 * 0.02) / (1000 - 800))
        self.assertEqual(quantity, expected_quantity)
    
    def test_edge_cases(self):
        """Test edge cases for stop-loss handling"""
        # Test case 1: Stop-loss equal to current price (should handle gracefully)
        market_data = {"last_price": 1600}
        stop_loss_price = 1600  # Same as current price
        quantity = self.bot._calculate_risk_based_quantity(market_data, stop_loss_price)
        
        # Should handle gracefully (might return 0 or handle division by zero)
        self.assertGreaterEqual(quantity, 0)
        
        # Test case 2: Stop-loss above current price (invalid for BUY)
        stop_loss_price = 1700  # Above current price
        quantity = self.bot._calculate_risk_based_quantity(market_data, stop_loss_price)
        
        # Should handle gracefully
        self.assertGreaterEqual(quantity, 0)
        
        # Test case 3: Very small percentage stop-loss
        market_data = {"last_price": 1000}
        stop_loss_pct = 0.001  # 0.1%
        quantity = self.bot._calculate_risk_based_quantity(market_data, stop_loss_pct)
        
        # Should calculate correctly
        expected_quantity = int((100000 * 0.02) / (1000 * 0.001))
        self.assertEqual(quantity, expected_quantity)
    
    def test_different_price_levels(self):
        """Test stop-loss handling across different price levels"""
        test_cases = [
            # (price, stop_loss, expected_risk_per_share)
            (1000, 0.05, 50),    # 5% of ₹1000 = ₹50
            (2000, 0.05, 100),   # 5% of ₹2000 = ₹100
            (500, 0.05, 25),     # 5% of ₹500 = ₹25
            (1000, 800, 200),    # Absolute: ₹1000 - ₹800 = ₹200
            (2000, 1800, 200),   # Absolute: ₹2000 - ₹1800 = ₹200
            (500, 400, 100),     # Absolute: ₹500 - ₹400 = ₹100
        ]
        
        for price, stop_loss, expected_risk_per_share in test_cases:
            market_data = {"last_price": price}
            quantity = self.bot._calculate_risk_based_quantity(market_data, stop_loss)
            
            # Calculate expected quantity based on risk per share
            expected_quantity = int((100000 * 0.02) / expected_risk_per_share)
            self.assertEqual(quantity, expected_quantity, 
                           f"Failed for price {price}, stop_loss {stop_loss}")
    
    def test_integration_with_recommendation(self):
        """Test stop-loss handling integration with TradeRecommendation"""
        # Test case 1: Percentage stop-loss in recommendation
        rec = TradeRecommendation(
            action="BUY",
            confidence=0.8,
            quantity=0,  # Let bot calculate
            stop_loss=0.05  # 5% percentage
        )
        market_data = {"last_price": 1600}
        quantity = self.bot._determine_order_quantity(rec, "1333", market_data)
        
        # Should use the percentage stop-loss
        expected_quantity = int((100000 * 0.02) / (1600 * 0.05))
        self.assertEqual(quantity, expected_quantity)
        
        # Test case 2: Absolute stop-loss in recommendation
        rec = TradeRecommendation(
            action="BUY",
            confidence=0.8,
            quantity=0,  # Let bot calculate
            stop_loss=1500  # Absolute price
        )
        quantity = self.bot._determine_order_quantity(rec, "1333", market_data)
        
        # Should use the absolute stop-loss
        expected_quantity = int((100000 * 0.02) / (1600 - 1500))
        self.assertEqual(quantity, expected_quantity)

def run_stop_loss_tests():
    """Run all stop-loss handling tests"""
    print("🧪 Testing Stop-Loss Handling Improvements")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStopLossHandling)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 All stop-loss handling tests passed!")
        print("\n📋 Stop-Loss Handling Features Validated:")
        print("✅ Percentage stop-loss calculations")
        print("✅ Absolute price stop-loss calculations")
        print("✅ Edge case handling")
        print("✅ Different price level support")
        print("✅ Integration with TradeRecommendation")
        print("✅ Risk-based quantity calculation improvements")
    else:
        print("\n❌ Some tests failed. Please review the output above.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_stop_loss_tests()

