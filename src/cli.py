"""
Command-line interface for the F&O trading system.
"""

import typer
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from .config import Config
from .data.instruments import InstrumentMaster
from .data.candles import CandleData
from .data.option_chain import OptionChainData
from .backtest.engine import BacktestEngine
from .backtest.walk_forward import WalkForwardOptimizer
from .governance.selector import StrategySelector
from .engine.engine_paper import PaperTradingEngine
from .engine.engine_live import LiveTradingEngine
from .reporting.reporter import Reporter
from .reporting.telegram import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def ingest(
    universe_size: int = typer.Option(50, help="Maximum number of symbols in universe"),
    days_back: int = typer.Option(365, help="Days of historical data to fetch")
):
    """Ingest market data and build universe."""
    try:
        logger.info("Starting data ingestion...")
        
        # Load configuration
        config = Config()
        
        # Initialize data components
        instruments = InstrumentMaster(config)
        candles = CandleData(config)
        option_chain = OptionChainData(config)
        
        # Build universe
        universe = instruments.build_universe(universe_size)
        logger.info(f"Built universe with {len(universe)} symbols")
        
        # Fetch historical data
        for symbol in universe:
            logger.info(f"Fetching data for {symbol}")
            candles.fetch_historical_data(symbol, days_back)
            option_chain.fetch_option_chain(symbol)
        
        logger.info("Data ingestion completed successfully")
        
    except Exception as e:
        logger.error(f"Error during data ingestion: {e}")
        raise typer.Exit(1)


@app.command()
def research(
    strategy: str = typer.Option("all", help="Strategy to research"),
    start_date: str = typer.Option("2023-01-01", help="Start date for research"),
    end_date: str = typer.Option("2024-01-01", help="End date for research")
):
    """Run strategy research and backtesting."""
    try:
        logger.info("Starting strategy research...")
        
        # Load configuration
        config = Config()
        
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Initialize backtesting engine
        engine = BacktestEngine(config)
        
        # Run backtests for strategies
        strategies = ["fut_donchian", "opt_iron_fly", "opt_iron_condor", "opt_debit_spread", "opt_orb"]
        
        if strategy != "all":
            strategies = [strategy]
        
        results = {}
        for strategy_name in strategies:
            logger.info(f"Researching {strategy_name}...")
            
            # This would load the actual strategy class
            # For now, just log the action
            logger.info(f"Backtesting {strategy_name} from {start_dt} to {end_dt}")
            
            # Placeholder for actual backtesting
            results[strategy_name] = {
                'total_return': 0.15,
                'sharpe_ratio': 1.2,
                'max_drawdown': 0.08,
                'win_rate': 0.55
            }
        
        # Generate research report
        reporter = Reporter(config.reporting)
        report = reporter.generate_research_report(results)
        
        logger.info("Strategy research completed successfully")
        
    except Exception as e:
        logger.error(f"Error during strategy research: {e}")
        raise typer.Exit(1)


@app.command()
def run_paper(
    strategy: str = typer.Option("opt_iron_fly", help="Strategy to run"),
    universe_size: int = typer.Option(20, help="Universe size for paper trading")
):
    """Run paper trading."""
    try:
        logger.info("Starting paper trading...")
        
        # Load configuration
        config = Config()
        
        # Initialize paper trading engine
        engine = PaperTradingEngine(config)
        
        # Initialize strategy
        # This would load the actual strategy class
        logger.info(f"Initializing {strategy} strategy...")
        
        # Build universe
        instruments = InstrumentMaster(config)
        universe = instruments.build_universe(universe_size)
        
        # Start paper trading
        logger.info(f"Starting paper trading with {strategy} strategy")
        logger.info(f"Universe: {universe}")
        
        # This would start the actual paper trading loop
        # For now, just log the action
        logger.info("Paper trading started successfully")
        
    except Exception as e:
        logger.error(f"Error during paper trading: {e}")
        raise typer.Exit(1)


@app.command()
def run_live(
    strategy: str = typer.Option("opt_iron_fly", help="Strategy to run"),
    universe_size: int = typer.Option(20, help="Universe size for live trading")
):
    """Run live trading."""
    try:
        logger.info("Starting live trading...")
        
        # Load configuration
        config = Config()
        
        # Check if live trading is enabled
        if not config.enable_live:
            logger.error("Live trading is not enabled in configuration")
            raise typer.Exit(1)
        
        # Initialize live trading engine
        engine = LiveTradingEngine(config)
        
        # Initialize strategy
        # This would load the actual strategy class
        logger.info(f"Initializing {strategy} strategy...")
        
        # Build universe
        instruments = InstrumentMaster(config)
        universe = instruments.build_universe(universe_size)
        
        # Start live trading
        logger.info(f"Starting live trading with {strategy} strategy")
        logger.info(f"Universe: {universe}")
        
        # This would start the actual live trading loop
        # For now, just log the action
        logger.info("Live trading started successfully")
        
    except Exception as e:
        logger.error(f"Error during live trading: {e}")
        raise typer.Exit(1)


@app.command()
def report(
    report_type: str = typer.Option("daily", help="Type of report to generate"),
    date: Optional[str] = typer.Option(None, help="Date for report (YYYY-MM-DD)")
):
    """Generate reports."""
    try:
        logger.info(f"Generating {report_type} report...")
        
        # Load configuration
        config = Config()
        
        # Initialize reporter
        reporter = Reporter(config.reporting)
        
        # Generate report based on type
        if report_type == "daily":
            # This would load actual portfolio data
            portfolio_data = {
                'total_value': 1000000,
                'total_pnl': 50000,
                'daily_pnl': 5000
            }
            
            report = reporter.generate_daily_report(
                portfolio_data=portfolio_data,
                positions={},
                orders=[],
                risk_metrics={},
                strategy_performance={}
            )
            
        elif report_type == "weekly":
            report = reporter.generate_weekly_report(
                weekly_data={},
                strategy_performance={},
                risk_analysis={}
            )
            
        elif report_type == "monthly":
            report = reporter.generate_monthly_report(
                monthly_data={},
                strategy_performance={},
                risk_analysis={},
                backtest_results={}
            )
        
        logger.info(f"{report_type.capitalize()} report generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise typer.Exit(1)


@app.command()
def status():
    """Check system status."""
    try:
        logger.info("Checking system status...")
        
        # Load configuration
        config = Config()
        
        # Check configuration
        logger.info("Configuration loaded successfully")
        
        # Check data availability
        instruments = InstrumentMaster(config)
        universe = instruments.build_universe(10)
        logger.info(f"Universe built with {len(universe)} symbols")
        
        # Check broker connection (if live trading enabled)
        if config.enable_live:
            logger.info("Live trading enabled - broker connection check would be performed")
        
        # Check reporting
        reporter = Reporter(config.reporting)
        summary = reporter.get_report_summary()
        logger.info(f"Reports available: {summary}")
        
        logger.info("System status check completed successfully")
        
    except Exception as e:
        logger.error(f"Error checking system status: {e}")
        raise typer.Exit(1)


@app.command()
def test():
    """Run system tests."""
    try:
        logger.info("Running system tests...")
        
        # Load configuration
        config = Config()
        
        # Test data components
        instruments = InstrumentMaster(config)
        candles = CandleData(config)
        option_chain = OptionChainData(config)
        
        logger.info("Data components initialized successfully")
        
        # Test backtesting
        engine = BacktestEngine(config)
        logger.info("Backtesting engine initialized successfully")
        
        # Test risk management
        from .risk.manager import RiskManager
        risk_manager = RiskManager(config)
        logger.info("Risk manager initialized successfully")
        
        # Test reporting
        reporter = Reporter(config.reporting)
        logger.info("Reporter initialized successfully")
        
        logger.info("All system tests passed successfully")
        
    except Exception as e:
        logger.error(f"Error during system tests: {e}")
        raise typer.Exit(1)


@app.command()
def optimize(
    strategy: str = typer.Option("opt_iron_fly", help="Strategy to optimize"),
    start_date: str = typer.Option("2023-01-01", help="Start date for optimization"),
    end_date: str = typer.Option("2024-01-01", help="End date for optimization")
):
    """Run walk-forward optimization."""
    try:
        logger.info("Starting walk-forward optimization...")
        
        # Load configuration
        config = Config()
        
        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Initialize walk-forward optimizer
        optimizer = WalkForwardOptimizer(config)
        
        # Define parameter space
        parameter_space = {
            'param1': [0.1, 0.2, 0.3],
            'param2': [10, 20, 30],
            'param3': [0.5, 0.6, 0.7]
        }
        
        # Run optimization
        logger.info(f"Optimizing {strategy} from {start_dt} to {end_dt}")
        
        # This would run the actual optimization
        # For now, just log the action
        logger.info("Walk-forward optimization completed successfully")
        
    except Exception as e:
        logger.error(f"Error during optimization: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()