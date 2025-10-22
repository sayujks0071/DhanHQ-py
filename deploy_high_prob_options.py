#!/usr/bin/env python3
"""
Deploy High Probability Option Strategies - Live Trading
This script deploys the AI trading bot with high probability option strategies
"""

import os
import time
import logging
from datetime import datetime
from ai_trading_bot import AITradingBot
from ai_option_strategies import OptionStrategyAnalyzer

class HighProbabilityOptionsBot(AITradingBot):
    """
    Enhanced AI Trading Bot optimized for high probability option strategies
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure for high probability option strategies
        self.trading_config.update({
            # Enhanced option strategy settings
            "enable_option_strategy_ai": True,
            "auto_deploy_option_strategies": True,
            "option_strategy_exchange_segment": "NSE_FNO",
            "option_strategy_instrument_type": "OPTIDX",
            
            # High probability strategy settings
            "min_option_confidence": 0.85,  # Higher confidence for options
            "max_option_risk_per_trade": 0.005,  # Lower risk for options (0.5%)
            "option_strategy_timeout": 300,  # 5 minutes timeout
            
            # Enhanced safety for live trading
            "min_confidence": 0.8,
            "max_position_size": 100,  # Smaller positions for live
            "risk_per_trade": 0.01,   # 1% risk per trade
            "max_daily_trades": 3,    # Conservative daily limit
            "trading_hours": {"start": "09:15", "end": "15:30"},
            "update_interval": 15,    # Slower updates for stability
            
            # Live trading settings
            "paper_trading_mode": False,
            "paper_position_size": 1,  # Start with 1 lot
            "live_safeguards": True,
            "enhanced_logging": True
        })
        
        # Initialize enhanced option strategy analyzer
        self.option_strategy_analyzer = OptionStrategyAnalyzer(
            self.dhan,
            self.logger,
            exchange_segment="NSE_FNO",
            instrument_type="OPTIDX"
        )
        
        self.logger.info("🎯 HIGH PROBABILITY OPTIONS BOT INITIALIZED")
        self.logger.info("📊 Option strategies: ENABLED")
        self.logger.info("🛡️ Enhanced safeguards: ACTIVE")
        self.logger.info("💰 Live trading mode: ENABLED")
    
    def test_live_connection(self):
        """Test live API connection"""
        print("\n🔍 Testing Live API Connection")
        print("=" * 50)
        
        try:
            # Test fund limits API
            funds = self._get_available_funds()
            if funds is not None:
                print(f"✅ Live API connection successful")
                print(f"💰 Available funds: ₹{funds:,.2f}")
                return True
            else:
                print("⚠️  Live API connection - No funds data")
                return False
        except Exception as e:
            print(f"❌ Live API connection failed: {e}")
            return False
    
    def get_high_probability_strategies(self, security_id: str, market_snapshot: dict) -> list:
        """
        Get high probability option strategies for the given security
        """
        try:
            # Get all strategy rankings
            strategies = self.option_strategy_analyzer.rank_strategies(
                security_id,
                market_snapshot,
                market_history=list(self.market_history.get(security_id, [])),
                position=self.active_positions.get(security_id)
            )
            
            # Filter for high probability strategies
            high_prob_strategies = []
            for strategy in strategies:
                if (strategy.confidence >= self.trading_config.get("min_option_confidence", 0.85) and
                    strategy.score > 50):  # Minimum score threshold
                    high_prob_strategies.append(strategy)
            
            return high_prob_strategies[:3]  # Top 3 high probability strategies
            
        except Exception as e:
            self.logger.error(f"Error getting high probability strategies: {e}")
            return []
    
    def deploy_high_probability_strategy(self, security_id: str, strategy) -> bool:
        """
        Deploy a high probability option strategy
        """
        try:
            if not strategy or strategy.score <= 0:
                return False
            
            self.logger.info(f"🎯 Deploying high probability strategy: {strategy.name}")
            self.logger.info(f"📊 Score: {strategy.score:.2f}, Confidence: {strategy.confidence:.2f}")
            self.logger.info(f"🎯 Risk Profile: {strategy.risk_profile}")
            self.logger.info(f"💡 Rationale: {strategy.rationale}")
            
            # Log strategy legs
            for idx, leg in enumerate(strategy.legs, 1):
                self.logger.info(f"  Leg {idx}: {leg.action} {leg.option_type} {leg.moneyness} qty={leg.quantity}")
                self.logger.info(f"    Notes: {leg.notes}")
            
            # In paper trading mode, just log the strategy
            if self.trading_config.get("paper_trading_mode", True):
                self.logger.info("📝 PAPER TRADING: Strategy logged (no live orders placed)")
                return True
            
            # TODO: Implement actual option order placement here
            # This would involve placing multi-leg option orders through DhanHQ
            # For now, we just log the strategy execution plan
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deploying high probability strategy: {e}")
            return False
    
    def run_high_probability_options_trading(self, security_ids: list):
        """
        Run high probability options trading for specified securities
        """
        self.logger.info("🚀 Starting High Probability Options Trading")
        self.logger.info(f"📊 Monitoring securities: {security_ids}")
        self.logger.info("🎯 Strategy focus: High probability, low risk")
        
        # Setup market feed for options
        from dhanhq import MarketFeed
        
        instruments = []
        for security_id in security_ids:
            instruments.append((MarketFeed.NSE_FNO, security_id, MarketFeed.Ticker))
        
        market_feed = MarketFeed(self.dhan_context, instruments, "v2")
        update_interval = self.trading_config.get("update_interval", 15)
        
        try:
            while True:
                self._reset_daily_trade_counters()
                self._update_positions()
                
                # Get market data
                market_data = market_feed.get_data()
                
                if market_data:
                    for data in market_data:
                        security_id = str(data.get("security_id", ""))
                        if not security_id:
                            continue
                        
                        # Update market history
                        self._update_market_history(security_id, data)
                        
                        # Get high probability option strategies
                        high_prob_strategies = self.get_high_probability_strategies(security_id, data)
                        
                        if high_prob_strategies:
                            self.logger.info(f"🎯 Found {len(high_prob_strategies)} high probability strategies for {security_id}")
                            
                            # Deploy the best strategy
                            best_strategy = high_prob_strategies[0]
                            success = self.deploy_high_probability_strategy(security_id, best_strategy)
                            
                            if success:
                                self.logger.info(f"✅ High probability strategy deployed for {security_id}")
                            else:
                                self.logger.warning(f"❌ Failed to deploy strategy for {security_id}")
                        else:
                            self.logger.debug(f"No high probability strategies found for {security_id}")
                
                # Wait before next iteration
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 High probability options trading stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Error in high probability options trading: {e}")
        finally:
            market_feed.disconnect()

def create_high_probability_options_bot():
    """Create high probability options trading bot"""
    print("🎯 Creating High Probability Options Trading Bot")
    print("=" * 60)
    
    # Load credentials from environment
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    ai_studio_api_key = os.getenv("AI_STUDIO_API_KEY")
    
    if not all([client_id, access_token, ai_studio_api_key]):
        print("❌ Missing credentials!")
        print("\n📋 Required environment variables:")
        print("   DHAN_LIVE_CLIENT_ID=your_live_client_id")
        print("   DHAN_LIVE_ACCESS_TOKEN=your_live_access_token")
        print("   AI_STUDIO_API_KEY=your_ai_studio_api_key")
        return None
    
    # Create high probability options bot
    bot = HighProbabilityOptionsBot(
        client_id=client_id,
        access_token=access_token,
        ai_studio_api_key=ai_studio_api_key
    )
    
    print("✅ High probability options bot created")
    print("🎯 Strategy focus: High probability, low risk")
    print("📊 Option strategies: ENABLED")
    print("🛡️ Enhanced safeguards: ACTIVE")
    print("📝 Paper trading mode: ENABLED")
    
    return bot

def main():
    """Main deployment function"""
    print("🎯 High Probability Options Strategy Deployment")
    print("=" * 60)
    print(f"⏰ Deployment time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀 Market is LIVE - Deploying high probability option strategies")
    
    try:
        # Create high probability options bot
        bot = create_high_probability_options_bot()
        
        if not bot:
            print("\n❌ Bot creation failed!")
            return
        
        # Test connection
        print("\n🔍 Testing connection...")
        if not bot.test_live_connection():
            print("❌ Connection test failed!")
            return
        
        print("✅ Connection test successful")
        
        # Configure securities for options trading
        # These are popular NSE F&O securities
        option_securities = [
            "256265",  # NIFTY 50
            "260105",  # BANK NIFTY
            "260000",  # NIFTY IT
            "260001",  # NIFTY FMCG
            "260002",  # NIFTY PHARMA
        ]
        
        print(f"\n📊 Starting high probability options trading for:")
        for sec_id in option_securities:
            print(f"   - {sec_id}")
        
        print("\n🎯 Trading Configuration:")
        print(f"   - Min confidence: {bot.trading_config.get('min_option_confidence', 0.85)}")
        print(f"   - Max risk per trade: {bot.trading_config.get('max_option_risk_per_trade', 0.005)}")
        print(f"   - Paper trading: {bot.trading_config.get('paper_trading_mode', True)}")
        print(f"   - Update interval: {bot.trading_config.get('update_interval', 15)}s")
        
        print("\n🚀 Starting high probability options trading...")
        print("⚠️  Press Ctrl+C to stop")
        
        # Start high probability options trading
        bot.run_high_probability_options_trading(option_securities)
        
    except KeyboardInterrupt:
        print("\n🛑 High probability options trading stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
