#!/usr/bin/env python3
"""
Dry-run testing script for the enhanced AI Trading Bot
This script simulates trading without executing real orders
"""

import json
import time
from datetime import datetime, time as dt_time
from typing import Dict, List

from ai_trading_bot import AITradingBot, TradeRecommendation

class DryRunAITradingBot(AITradingBot):
    """
    Dry-run version of AI Trading Bot that simulates trading without real orders
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dry_run_mode = True
        self.simulated_orders = []
        self.simulated_positions = {}
        self.simulated_funds = 100000.0  # Start with 1 lakh
        self.trade_log = []
        
    def _get_available_funds(self) -> float:
        """Override to return simulated funds"""
        return self.simulated_funds
    
    def _update_positions(self):
        """Override to use simulated positions"""
        # In dry run, we maintain our own position tracking
        pass
    
    def execute_trade(self, recommendation: TradeRecommendation, security_id: str, 
                     market_snapshot: Dict, quantity: int) -> bool:
        """
        Simulate trade execution without placing real orders
        """
        try:
            last_price = market_snapshot.get("last_price", 0)
            if not last_price:
                self.logger.warning("No price data available for simulation")
                return False
            
            # Calculate trade value
            trade_value = last_price * quantity
            
            # Check if we have enough funds for BUY
            if recommendation.action == "BUY":
                if trade_value > self.simulated_funds:
                    self.logger.warning(f"Insufficient funds for BUY: {trade_value} > {self.simulated_funds}")
                    return False
                self.simulated_funds -= trade_value
            else:  # SELL
                current_position = self.simulated_positions.get(security_id, 0)
                if quantity > current_position:
                    self.logger.warning(f"Insufficient position for SELL: {quantity} > {current_position}")
                    return False
                self.simulated_funds += trade_value
            
            # Update simulated positions
            current_position = self.simulated_positions.get(security_id, 0)
            if recommendation.action == "BUY":
                new_position = current_position + quantity
            else:  # SELL
                new_position = current_position - quantity
            
            self.simulated_positions[security_id] = new_position
            
            # Log the simulated trade
            trade_record = {
                "timestamp": datetime.now().isoformat(),
                "action": recommendation.action,
                "security_id": security_id,
                "quantity": quantity,
                "price": last_price,
                "value": trade_value,
                "confidence": recommendation.confidence,
                "reasoning": recommendation.reasoning,
                "remaining_funds": self.simulated_funds,
                "new_position": new_position
            }
            
            self.simulated_orders.append(trade_record)
            self.trade_log.append(trade_record)
            
            self.logger.info(
                "SIMULATED %s: %s shares of %s at ₹%.2f | Value: ₹%.2f | "
                "Confidence: %.2f | Remaining Funds: ₹%.2f | Position: %s",
                recommendation.action,
                quantity,
                security_id,
                last_price,
                trade_value,
                recommendation.confidence,
                self.simulated_funds,
                new_position
            )
            
            if recommendation.stop_loss:
                self.logger.info("Recommended stop loss: ₹%.2f", recommendation.stop_loss)
            if recommendation.take_profit:
                self.logger.info("Recommended take profit: ₹%.2f", recommendation.take_profit)
            
            self._record_trade(security_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Error in simulated trade execution: {e}")
            return False
    
    def get_simulation_summary(self) -> Dict:
        """Get summary of simulation results"""
        total_trades = len(self.simulated_orders)
        buy_trades = len([t for t in self.simulated_orders if t["action"] == "BUY"])
        sell_trades = len([t for t in self.simulated_orders if t["action"] == "SELL"])
        
        total_buy_value = sum(t["value"] for t in self.simulated_orders if t["action"] == "BUY")
        total_sell_value = sum(t["value"] for t in self.simulated_orders if t["action"] == "SELL")
        
        # Calculate P&L (simplified)
        net_investment = total_buy_value - total_sell_value
        current_portfolio_value = sum(
            pos * 1000 for pos in self.simulated_positions.values()  # Assuming current price = 1000
        )
        
        return {
            "total_trades": total_trades,
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "total_buy_value": total_buy_value,
            "total_sell_value": total_sell_value,
            "net_investment": net_investment,
            "remaining_funds": self.simulated_funds,
            "current_positions": dict(self.simulated_positions),
            "trade_log": self.trade_log
        }

def create_mock_market_data(security_ids: List[str]) -> List[Dict]:
    """Create mock market data for testing"""
    mock_data = []
    base_prices = {"1333": 1500, "11536": 2500, "288": 3500}  # HDFC, Reliance, TCS
    
    for security_id in security_ids:
        base_price = base_prices.get(security_id, 1000)
        # Add some random variation
        import random
        variation = random.uniform(-0.05, 0.05)  # ±5% variation
        current_price = base_price * (1 + variation)
        
        mock_data.append({
            "security_id": security_id,
            "symbol": f"STOCK_{security_id}",
            "last_price": current_price,
            "volume": random.randint(1000, 10000),
            "high": current_price * 1.02,
            "low": current_price * 0.98,
            "open": current_price * 0.99,
            "change": current_price - base_price,
            "change_percent": variation * 100
        })
    
    return mock_data

def run_dry_run_simulation():
    """Run a dry-run simulation of the AI trading bot"""
    print("🧪 Starting Dry-Run AI Trading Bot Simulation")
    print("=" * 60)
    
    # Initialize dry-run bot
    bot = DryRunAITradingBot(
        client_id="dry_run_client",
        access_token="dry_run_token",
        ai_studio_api_key="dry_run_key"
    )
    
    # Configure for simulation
    bot.trading_config.update({
        "min_confidence": 0.6,  # Lower threshold for testing
        "max_position_size": 50,
        "risk_per_trade": 0.01,  # 1% risk per trade
        "max_daily_trades": 5,
        "update_interval": 2,  # Faster updates for testing
        "trading_hours": {"start": "09:15", "end": "15:30"}
    })
    
    print(f"💰 Starting with simulated funds: ₹{bot.simulated_funds:,.2f}")
    print(f"⚙️  Configuration: {json.dumps(bot.trading_config, indent=2)}")
    print()
    
    # Test securities
    securities = ["1333", "11536", "288"]  # HDFC, Reliance, TCS
    
    print("🔄 Running simulation for 10 iterations...")
    print("-" * 60)
    
    try:
        for iteration in range(10):
            print(f"\n📊 Iteration {iteration + 1}/10")
            
            # Generate mock market data
            market_data = create_mock_market_data(securities)
            
            for data in market_data:
                security_id = str(data.get("security_id", ""))
                if not security_id:
                    continue
                
                # Update market history
                bot._update_market_history(security_id, data)
                
                # Simulate AI analysis (mock response)
                mock_ai_response = {
                    "candidates": [{
                        "content": {
                            "parts": [{
                                "text": json.dumps({
                                    "action": "BUY" if iteration % 3 == 0 else "HOLD",
                                    "confidence": 0.7 + (iteration * 0.02),
                                    "quantity": 10,
                                    "reasoning": f"Simulated analysis for iteration {iteration + 1}",
                                    "stop_loss": data["last_price"] * 0.95,
                                    "take_profit": data["last_price"] * 1.10
                                })
                            }]
                        }
                    }]
                }
                
                # Parse and normalize recommendation
                parsed = bot._parse_ai_response(mock_ai_response)
                recommendation = bot._normalize_recommendation(parsed)
                
                # Determine quantity
                quantity = bot._determine_order_quantity(recommendation, security_id, data)
                
                # Check if should execute
                if bot._should_execute_trade(recommendation, security_id, quantity):
                    executed = bot.execute_trade(recommendation, security_id, data, quantity)
                    if executed:
                        print(f"✅ Trade executed: {recommendation.action} {quantity} shares of {security_id}")
                    else:
                        print(f"❌ Trade failed: {recommendation.action} {quantity} shares of {security_id}")
                else:
                    print(f"⏸️  Trade skipped: {recommendation.action} {quantity} shares of {security_id}")
            
            # Wait between iterations
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n🛑 Simulation stopped by user")
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 SIMULATION SUMMARY")
    print("=" * 60)
    
    summary = bot.get_simulation_summary()
    
    print(f"💰 Remaining Funds: ₹{summary['remaining_funds']:,.2f}")
    print(f"📈 Total Trades: {summary['total_trades']}")
    print(f"🛒 Buy Trades: {summary['buy_trades']}")
    print(f"💸 Sell Trades: {summary['sell_trades']}")
    print(f"💵 Total Buy Value: ₹{summary['total_buy_value']:,.2f}")
    print(f"💰 Total Sell Value: ₹{summary['total_sell_value']:,.2f}")
    print(f"📊 Net Investment: ₹{summary['net_investment']:,.2f}")
    
    print(f"\n📋 Current Positions:")
    for security_id, position in summary['current_positions'].items():
        if position != 0:
            print(f"  {security_id}: {position} shares")
    
    print(f"\n📝 Trade Log:")
    for trade in summary['trade_log']:
        print(f"  {trade['timestamp']}: {trade['action']} {trade['quantity']} shares of {trade['security_id']} at ₹{trade['price']:.2f}")
    
    print("\n🎉 Dry-run simulation completed!")
    print("\n📋 Next Steps:")
    print("1. Review the simulation results above")
    print("2. Adjust TRADING_CONFIG thresholds if needed")
    print("3. Test with paper trading account")
    print("4. Monitor performance before going live")

if __name__ == "__main__":
    run_dry_run_simulation()

