#!/usr/bin/env python3
"""
Main bot runner script for the F&O trading system.
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import Config
from src.engine.engine_paper import PaperTradingEngine
from src.engine.engine_live import LiveTradingEngine
from src.reporting.telegram import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot class."""
    
    def __init__(self):
        self.config = Config()
        self.running = False
        self.engine = None
        self.telegram = TelegramNotifier(self.config.reporting)
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def start(self, mode: str = "paper", strategy: str = "opt_iron_fly"):
        """Start the trading bot."""
        try:
            logger.info(f"Starting trading bot in {mode} mode with {strategy} strategy")
            
            # Send startup notification
            if self.telegram.enabled:
                self.telegram.send_startup_alert()
            
            # Initialize trading engine
            if mode == "paper":
                self.engine = PaperTradingEngine(self.config)
            elif mode == "live":
                if not self.config.enable_live:
                    logger.error("Live trading is not enabled in configuration")
                    return
                self.engine = LiveTradingEngine(self.config)
            else:
                logger.error(f"Invalid mode: {mode}")
                return
            
            # Build universe
            from src.data.instruments import InstrumentMaster
            instruments = InstrumentMaster(self.config)
            universe = instruments.build_universe(20)
            
            logger.info(f"Built universe with {len(universe)} symbols: {universe}")
            
            # Initialize strategy
            strategy_class = self._load_strategy(strategy)
            if not strategy_class:
                logger.error(f"Failed to load strategy: {strategy}")
                return
            
            # Start trading
            self.running = True
            self.engine.start_trading(strategy_class, universe)
            
        except Exception as e:
            logger.error(f"Error starting trading bot: {e}")
            if self.telegram.enabled:
                self.telegram.send_error_alert(str(e), "Bot Startup")
    
    def stop(self):
        """Stop the trading bot."""
        logger.info("Stopping trading bot...")
        self.running = False
        
        if self.engine:
            if hasattr(self.engine, 'stop_trading'):
                self.engine.stop_trading()
        
        # Send shutdown notification
        if self.telegram.enabled:
            self.telegram.send_shutdown_alert()
        
        logger.info("Trading bot stopped")
    
    def _load_strategy(self, strategy_name: str):
        """Load strategy class."""
        try:
            if strategy_name == "fut_donchian":
                from src.strategies.fut_donchian import DonchianBreakoutStrategy
                return DonchianBreakoutStrategy
            elif strategy_name == "opt_iron_fly":
                from src.strategies.opt_iron_fly import IronFlyStrategy
                return IronFlyStrategy
            elif strategy_name == "opt_iron_condor":
                from src.strategies.opt_iron_condor import IronCondorStrategy
                return IronCondorStrategy
            elif strategy_name == "opt_debit_spread":
                from src.strategies.opt_debit_spread import DebitSpreadStrategy
                return DebitSpreadStrategy
            elif strategy_name == "opt_orb":
                from src.strategies.opt_orb import ORBStrategy
                return ORBStrategy
            else:
                logger.error(f"Unknown strategy: {strategy_name}")
                return None
        except Exception as e:
            logger.error(f"Error loading strategy {strategy_name}: {e}")
            return None


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="F&O Trading Bot")
    parser.add_argument("--mode", choices=["paper", "live"], default="paper", help="Trading mode")
    parser.add_argument("--strategy", default="opt_iron_fly", help="Trading strategy")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # Initialize bot
    bot = TradingBot()
    
    try:
        # Start bot
        bot.start(args.mode, args.strategy)
        
        # Keep running
        while bot.running:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        bot.stop()


if __name__ == "__main__":
    main()
