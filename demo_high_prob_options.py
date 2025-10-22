#!/usr/bin/env python3
"""
Demo High Probability Option Strategies
Demonstrates the high probability option strategies without live credentials
"""

import time
import random
from datetime import datetime
from ai_option_strategies import OptionStrategyAnalyzer, StrategyRecommendation

class DemoHighProbabilityOptions:
    """Demo high probability options trading system"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.option_analyzer = OptionStrategyAnalyzer(None, self.logger)
        self.strategies_deployed = 0
        self.total_score = 0
        
    def _setup_logger(self):
        """Setup demo logger"""
        import logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)
    
    def generate_demo_market_data(self, security_id: str) -> dict:
        """Generate realistic demo market data"""
        base_prices = {
            "256265": 19500,  # NIFTY 50
            "260105": 45000,  # BANK NIFTY
            "260000": 35000,  # NIFTY IT
            "260001": 25000,  # NIFTY FMCG
            "260002": 18000,  # NIFTY PHARMA
        }
        
        base_price = base_prices.get(security_id, 20000)
        
        # Generate realistic price movement
        change_pct = random.uniform(-0.02, 0.02)  # ±2% movement
        current_price = base_price * (1 + change_pct)
        
        return {
            "security_id": security_id,
            "last_price": round(current_price, 2),
            "open": round(base_price, 2),
            "high": round(current_price * 1.01, 2),
            "low": round(current_price * 0.99, 2),
            "volume": random.randint(100000, 500000),
            "change": round(current_price - base_price, 2),
            "change_percent": round(change_pct * 100, 2)
        }
    
    def demo_high_probability_strategies(self, security_id: str, market_data: dict):
        """Demo high probability strategy evaluation"""
        try:
            # Create mock historical data
            history = []
            for i in range(20):
                hist_data = self.generate_demo_market_data(security_id)
                history.append(hist_data)
            
            # Get strategy recommendations
            strategies = self.option_analyzer.rank_strategies(
                security_id,
                market_data,
                market_history=history
            )
            
            # Filter high probability strategies (confidence > 0.8)
            high_prob_strategies = [
                s for s in strategies 
                if s.confidence >= 0.8 and s.score > 50
            ]
            
            if high_prob_strategies:
                self.logger.info(f"🎯 Found {len(high_prob_strategies)} high probability strategies for {security_id}")
                
                for i, strategy in enumerate(high_prob_strategies[:3], 1):
                    self.logger.info(f"  Strategy {i}: {strategy.name}")
                    self.logger.info(f"    Score: {strategy.score:.2f}")
                    self.logger.info(f"    Confidence: {strategy.confidence:.2f}")
                    self.logger.info(f"    Risk: {strategy.risk_profile}")
                    self.logger.info(f"    Rationale: {strategy.rationale}")
                    
                    # Log strategy legs
                    for j, leg in enumerate(strategy.legs, 1):
                        self.logger.info(f"      Leg {j}: {leg.action} {leg.option_type} {leg.moneyness} qty={leg.quantity}")
                    
                    self.strategies_deployed += 1
                    self.total_score += strategy.score
                    
                    self.logger.info(f"✅ High probability strategy deployed: {strategy.name}")
                    self.logger.info("📝 PAPER TRADING: Strategy logged (no live orders placed)")
                    self.logger.info("-" * 60)
            else:
                self.logger.info(f"📊 No high probability strategies found for {security_id}")
                
        except Exception as e:
            self.logger.error(f"❌ Error evaluating strategies for {security_id}: {e}")
    
    def run_demo_trading(self):
        """Run demo high probability options trading"""
        print("🎯 DEMO: High Probability Option Strategies")
        print("=" * 60)
        print(f"⏰ Demo started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📊 Simulating live market conditions")
        print("🎯 Strategy focus: High probability, low risk")
        print()
        
        # Demo securities
        securities = [
            "256265",  # NIFTY 50
            "260105",  # BANK NIFTY
            "260000",  # NIFTY IT
        ]
        
        try:
            for cycle in range(5):  # Run 5 cycles
                print(f"\n🔄 Trading Cycle {cycle + 1}/5")
                print("=" * 40)
                
                for security_id in securities:
                    # Generate market data
                    market_data = self.generate_demo_market_data(security_id)
                    
                    print(f"\n📊 Market Data for {security_id}:")
                    print(f"   Price: ₹{market_data['last_price']:,.2f}")
                    print(f"   Change: {market_data['change_percent']:+.2f}%")
                    print(f"   Volume: {market_data['volume']:,}")
                    
                    # Evaluate high probability strategies
                    self.demo_high_probability_strategies(security_id, market_data)
                
                # Wait between cycles
                if cycle < 4:
                    print(f"\n⏳ Waiting 10 seconds before next cycle...")
                    time.sleep(10)
            
            # Summary
            print(f"\n📈 DEMO SUMMARY")
            print("=" * 40)
            print(f"✅ Strategies deployed: {self.strategies_deployed}")
            print(f"📊 Average score: {self.total_score / max(self.strategies_deployed, 1):.2f}")
            print(f"🎯 High probability strategies: ACTIVE")
            print(f"🛡️ Safety features: ENABLED")
            print(f"📝 Paper trading mode: ACTIVE")
            
        except KeyboardInterrupt:
            print("\n🛑 Demo stopped by user")
        except Exception as e:
            print(f"❌ Demo error: {e}")

def main():
    """Main demo function"""
    demo = DemoHighProbabilityOptions()
    demo.run_demo_trading()

if __name__ == "__main__":
    main()
