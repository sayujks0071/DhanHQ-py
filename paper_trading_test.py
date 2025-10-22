#!/usr/bin/env python3
"""
Paper Trading Test for Enhanced AI Trading Bot
This script simulates trading behavior with curated market snapshots
"""

import json
import time
import random
from datetime import datetime, time as dt_time
from typing import Dict, List

from ai_trading_bot import AITradingBot, TradeRecommendation

class PaperTradingBot(AITradingBot):
    """
    Paper trading version that simulates orders without real execution
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paper_mode = True
        self.simulated_orders = []
        self.simulated_positions = {}
        self.simulated_funds = 100000.0  # Start with 1 lakh
        self.trade_log = []
        
    def _get_available_funds(self) -> float:
        """Override to return simulated funds"""
        return self.simulated_funds
    
    def _update_positions(self):
        """Override to use simulated positions"""
        # In paper mode, we maintain our own position tracking
        pass
    
    def execute_trade(self, recommendation: TradeRecommendation, security_id: str, 
                     market_snapshot: Dict, quantity: int) -> bool:
        """
        Simulate trade execution for paper trading
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
                "new_position": new_position,
                "stop_loss": recommendation.stop_loss,
                "take_profit": recommendation.take_profit
            }
            
            self.simulated_orders.append(trade_record)
            self.trade_log.append(trade_record)
            
            self.logger.info(
                "PAPER TRADE %s: %s shares of %s at ₹%.2f | Value: ₹%.2f | "
                "Confidence: %.2f | Funds: ₹%.2f | Position: %s",
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
                self.logger.info("Stop loss: ₹%.2f", recommendation.stop_loss)
            if recommendation.take_profit:
                self.logger.info("Take profit: ₹%.2f", recommendation.take_profit)
            
            self._record_trade(security_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Error in paper trade execution: {e}")
            return False
    
    def get_paper_trading_summary(self) -> Dict:
        """Get summary of paper trading results"""
        total_trades = len(self.simulated_orders)
        buy_trades = len([t for t in self.simulated_orders if t["action"] == "BUY"])
        sell_trades = len([t for t in self.simulated_orders if t["action"] == "SELL"])
        
        total_buy_value = sum(t["value"] for t in self.simulated_orders if t["action"] == "BUY")
        total_sell_value = sum(t["value"] for t in self.simulated_orders if t["action"] == "SELL")
        
        # Calculate portfolio value (simplified - using current prices)
        portfolio_value = sum(
            pos * 1000 for pos in self.simulated_positions.values()  # Assuming current price = 1000
        )
        
        return {
            "total_trades": total_trades,
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "total_buy_value": total_buy_value,
            "total_sell_value": total_sell_value,
            "net_investment": total_buy_value - total_sell_value,
            "remaining_funds": self.simulated_funds,
            "portfolio_value": portfolio_value,
            "total_value": self.simulated_funds + portfolio_value,
            "current_positions": dict(self.simulated_positions),
            "trade_log": self.trade_log
        }

def create_curated_market_snapshots(security_ids: List[str], num_snapshots: int = 10) -> List[List[Dict]]:
    """Create curated market snapshots for testing"""
    snapshots = []
    base_prices = {"1333": 1500, "11536": 2500, "288": 3500}  # HDFC, Reliance, TCS
    
    for i in range(num_snapshots):
        snapshot = []
        for security_id in security_ids:
            base_price = base_prices.get(security_id, 1000)
            
            # Create realistic price movements
            if i == 0:
                # Initial snapshot
                price = base_price
            else:
                # Add some trend and volatility
                trend = random.uniform(-0.02, 0.02)  # ±2% trend
                volatility = random.uniform(-0.01, 0.01)  # ±1% volatility
                price = base_price * (1 + trend + volatility)
            
            snapshot.append({
                "security_id": security_id,
                "symbol": f"STOCK_{security_id}",
                "last_price": round(price, 2),
                "volume": random.randint(1000, 10000),
                "high": round(price * 1.02, 2),
                "low": round(price * 0.98, 2),
                "open": round(price * 0.99, 2),
                "change": round(price - base_price, 2),
                "change_percent": round(((price - base_price) / base_price) * 100, 2)
            })
        
        snapshots.append(snapshot)
    
    return snapshots

def run_paper_trading_simulation():
    """Run paper trading simulation with curated market data"""
    print("📊 Starting Paper Trading Simulation")
    print("=" * 60)
    
    # Initialize paper trading bot
    bot = PaperTradingBot(
        client_id="paper_client",
        access_token="paper_token",
        ai_studio_api_key="paper_key"
    )
    
    # Configure for paper trading
    bot.trading_config.update({
        "min_confidence": 0.6,  # Lower threshold for testing
        "max_position_size": 100,
        "risk_per_trade": 0.01,  # 1% risk per trade
        "max_daily_trades": 8,
        "update_interval": 1,
        "trading_hours": {"start": "09:15", "end": "15:30"}
    })
    
    print(f"💰 Starting funds: ₹{bot.simulated_funds:,.2f}")
    print(f"⚙️  Configuration: {json.dumps(bot.trading_config, indent=2)}")
    print()
    
    # Test securities
    securities = ["1333", "11536", "288"]  # HDFC, Reliance, TCS
    
    # Create curated market snapshots
    market_snapshots = create_curated_market_snapshots(securities, 10)
    
    print("🔄 Running paper trading simulation...")
    print("-" * 60)
    
    try:
        for i, snapshot in enumerate(market_snapshots):
            print(f"\n📊 Market Snapshot {i + 1}/10")
            
            for market_data in snapshot:
                security_id = str(market_data.get("security_id", ""))
                if not security_id:
                    continue
                
                # Update market history
                bot._update_market_history(security_id, market_data)
                
                # Simulate AI analysis with varying confidence
                confidence = 0.5 + (i * 0.05) + random.uniform(-0.1, 0.1)
                confidence = max(0.0, min(1.0, confidence))
                
                # Create mock AI response
                mock_ai_response = {
                    "candidates": [{
                        "content": {
                            "parts": [{
                                "text": json.dumps({
                                    "action": "BUY" if confidence > 0.7 else "HOLD",
                                    "confidence": confidence,
                                    "quantity": random.randint(5, 20),
                                    "reasoning": f"Paper trading analysis - confidence: {confidence:.2f}",
                                    "stop_loss": market_data["last_price"] * 0.95,
                                    "take_profit": market_data["last_price"] * 1.10
                                })
                            }]
                        }
                    }]
                }
                
                # Parse and normalize recommendation
                parsed = bot._parse_ai_response(mock_ai_response)
                recommendation = bot._normalize_recommendation(parsed)
                
                # Determine quantity
                quantity = bot._determine_order_quantity(recommendation, security_id, market_data)
                
                # Check if should execute
                if bot._should_execute_trade(recommendation, security_id, quantity):
                    executed = bot.execute_trade(recommendation, security_id, market_data, quantity)
                    if executed:
                        print(f"✅ Paper trade executed: {recommendation.action} {quantity} shares of {security_id}")
                    else:
                        print(f"❌ Paper trade failed: {recommendation.action} {quantity} shares of {security_id}")
                else:
                    print(f"⏸️  Paper trade skipped: {recommendation.action} {quantity} shares of {security_id}")
            
            # Brief pause between snapshots
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n🛑 Paper trading simulation stopped by user")
    except Exception as e:
        print(f"\n❌ Paper trading simulation error: {e}")
    
    # Generate comprehensive summary
    print("\n" + "=" * 60)
    print("📊 PAPER TRADING SUMMARY")
    print("=" * 60)
    
    summary = bot.get_paper_trading_summary()
    
    print(f"💰 Remaining Funds: ₹{summary['remaining_funds']:,.2f}")
    print(f"📈 Portfolio Value: ₹{summary['portfolio_value']:,.2f}")
    print(f"💎 Total Value: ₹{summary['total_value']:,.2f}")
    print(f"📊 Total Trades: {summary['total_trades']}")
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
        print(f"  {trade['timestamp']}: {trade['action']} {trade['quantity']} shares of {trade['security_id']} at ₹{trade['price']:.2f} (Confidence: {trade['confidence']:.2f})")
    
    print("\n🎉 Paper trading simulation completed!")
    print("\n📋 Next Steps:")
    print("1. Review the paper trading results above")
    print("2. Analyze the AI decision patterns and confidence levels")
    print("3. Adjust TRADING_CONFIG parameters if needed")
    print("4. Test with real market data during trading hours")
    print("5. Consider live deployment with proper credentials")

if __name__ == "__main__":
    run_paper_trading_simulation()



