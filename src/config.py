"""
Configuration management for the Liquid F&O Trading System.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, time
import yaml
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = "sqlite:///data/trading.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class RedisConfig(BaseModel):
    """Redis configuration."""
    url: str = "redis://localhost:6379/0"
    max_connections: int = 10


class MarketHoursConfig(BaseModel):
    """Market hours configuration."""
    pre_open: str = "09:00"
    open: str = "09:15"
    close: str = "15:30"
    timezone: str = "Asia/Kolkata"
    
    @validator('pre_open', 'open', 'close')
    def validate_time_format(cls, v):
        try:
            time.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid time format: {v}")


class RiskConfig(BaseModel):
    """Risk management configuration."""
    max_daily_dd: float = 0.02
    max_per_trade_risk: float = 0.005
    max_concurrent_positions: int = 8
    margin_buffer_pct: float = 0.15
    hedge_min_delta: float = 0.20
    
    # Greek caps per underlying
    max_delta: float = 0.8
    max_vega: float = 3.0
    max_gamma: float = 0.5
    
    # Portfolio level caps
    max_portfolio_delta: float = 5.0
    max_portfolio_vega: float = 15.0
    max_portfolio_gamma: float = 10.0


class UniverseConfig(BaseModel):
    """Universe configuration."""
    max_instruments: int = 150
    min_turnover_30d: int = 100_000_000  # 100 Cr
    min_oi: int = 1_000_000  # 10 Lakh
    max_spread_bps: int = 5
    min_lot_value: int = 100_000  # 1 Lakh
    max_lot_value: int = 15_000_000  # 1.5 Cr
    min_price: int = 50
    exclude_stocks: List[str] = Field(default_factory=list)


class OptionsConfig(BaseModel):
    """Options configuration."""
    expiry_days: int = 7
    strike_steps: int = 5
    min_oi: int = 1000
    min_volume: int = 500
    iv_smoothing: float = 0.5
    roll_time: str = "14:45"
    avoid_last_30min: bool = True


class CostsConfig(BaseModel):
    """Transaction costs configuration."""
    futures_bps: int = 4
    options_abs: int = 40  # INR per lot
    statutory_bps: float = 0.1
    stt_bps: float = 0.05
    stamp_duty_bps: float = 0.003


class SlippageConfig(BaseModel):
    """Slippage configuration."""
    futures_bps: int = 3
    options_abs: float = 0.35  # INR per option leg


class DashboardConfig(BaseModel):
    """Dashboard configuration."""
    host: str = "localhost"
    port: int = 8787
    auth_token: str = "your_auth_token_here"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8787"]


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    file: str = "logs/trading.log"
    max_size: str = "10MB"
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class Settings(BaseSettings):
    """Main application settings."""
    
    # DhanHQ API
    dhan_client_id: str = Field(..., env="DHAN_CLIENT_ID")
    dhan_access_token: str = Field(..., env="DHAN_ACCESS_TOKEN")
    
    # Trading mode
    enable_live: bool = Field(False, env="ENABLE_LIVE")
    enable_options: bool = Field(True, env="ENABLE_OPTIONS")
    disable_equity: bool = Field(True, env="DISABLE_EQUITY")
    
    # Universe
    universe_max: int = Field(150, env="UNIVERSE_MAX")
    
    # Risk management
    risk_max_daily_dd: float = Field(0.02, env="RISK_MAX_DAILY_DD")
    risk_per_trade: float = Field(0.005, env="RISK_PER_TRADE")
    max_concurrent_pos: int = Field(8, env="MAX_CONCURRENT_POS")
    
    # Transaction costs
    slippage_fut_bps: int = Field(3, env="SLIPPAGE_FUT_BPS")
    slippage_opt_abs: float = Field(0.35, env="SLIPPAGE_OPT_ABS")
    txn_cost_fut_bps: int = Field(4, env="TXN_COST_FUT_BPS")
    txn_cost_opt_abs: int = Field(40, env="TXN_COST_OPT_ABS")
    
    # Margin and risk
    margin_buffer_pct: float = Field(0.15, env="MARGIN_BUFFER_PCT")
    hedge_min_delta_abs: float = Field(0.20, env="HEDGE_MIN_DELTA_ABS")
    iv_smoothing: float = Field(0.5, env="IV_SMOOTHING")
    
    # Notifications
    notify_telegram_bot_token: Optional[str] = Field(None, env="NOTIFY_TELEGRAM_BOT_TOKEN")
    notify_telegram_chat_id: Optional[str] = Field(None, env="NOTIFY_TELEGRAM_CHAT_ID")
    
    # Dashboard
    dashboard_port: int = Field(8787, env="DASHBOARD_PORT")
    dashboard_host: str = Field("localhost", env="DASHBOARD_HOST")
    
    # Database
    database_url: str = Field("sqlite:///data/trading.db", env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/trading.log", env="LOG_FILE")
    
    # Market hours
    market_open: str = Field("09:15", env="MARKET_OPEN")
    market_close: str = Field("15:30", env="MARKET_CLOSE")
    pre_open_start: str = Field("09:00", env="PRE_OPEN_START")
    
    # Strategy
    default_strategy_timeframe: str = Field("5m", env="DEFAULT_STRATEGY_TIMEFRAME")
    max_strategy_parallel: int = Field(5, env="MAX_STRATEGY_PARALLEL")
    
    # Backtesting
    backtest_start_date: str = Field("2023-01-01", env="BACKTEST_START_DATE")
    backtest_end_date: str = Field("2024-01-01", env="BACKTEST_END_DATE")
    walk_forward_window: int = Field(252, env="WALK_FORWARD_WINDOW")
    walk_forward_step: int = Field(63, env="WALK_FORWARD_STEP")
    
    # Options
    options_expiry_days: int = Field(7, env="OPTIONS_EXPIRY_DAYS")
    options_strike_steps: int = Field(5, env="OPTIONS_STRIKE_STEPS")
    options_min_oi: int = Field(1000, env="OPTIONS_MIN_OI")
    options_min_volume: int = Field(500, env="OPTIONS_MIN_VOLUME")
    
    # Event blackouts
    event_blackout_dates: str = Field("", env="EVENT_BLACKOUT_DATES")
    
    # Kill switch
    kill_switch_enabled: bool = Field(True, env="KILL_SWITCH_ENABLED")
    kill_switch_daily_loss_pct: float = Field(0.05, env="KILL_SWITCH_DAILY_LOSS_PCT")
    kill_switch_max_positions: int = Field(10, env="KILL_SWITCH_MAX_POSITIONS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class Config:
    """Main configuration class."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration."""
        self.config_file = config_file or "config.yaml"
        self.settings = Settings()
        self._load_yaml_config()
    
    def _load_yaml_config(self) -> None:
        """Load YAML configuration file."""
        config_path = Path(self.config_file)
        if not config_path.exists():
            return
        
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
        
        # Update settings with YAML config
        if yaml_config:
            self._update_settings_from_yaml(yaml_config)
    
    def _update_settings_from_yaml(self, yaml_config: Dict[str, Any]) -> None:
        """Update settings from YAML configuration."""
        # This would merge YAML config with environment variables
        # For now, we'll use environment variables as primary
        pass
    
    @property
    def is_live_trading_enabled(self) -> bool:
        """Check if live trading is enabled."""
        return self.settings.enable_live
    
    @property
    def is_options_enabled(self) -> bool:
        """Check if options trading is enabled."""
        return self.settings.enable_options
    
    @property
    def is_equity_disabled(self) -> bool:
        """Check if equity trading is disabled."""
        return self.settings.disable_equity
    
    def get_market_hours(self) -> MarketHoursConfig:
        """Get market hours configuration."""
        return MarketHoursConfig(
            pre_open=self.settings.pre_open_start,
            open=self.settings.market_open,
            close=self.settings.market_close,
            timezone="Asia/Kolkata"
        )
    
    def get_risk_config(self) -> RiskConfig:
        """Get risk management configuration."""
        return RiskConfig(
            max_daily_dd=self.settings.risk_max_daily_dd,
            max_per_trade_risk=self.settings.risk_per_trade,
            max_concurrent_positions=self.settings.max_concurrent_pos,
            margin_buffer_pct=self.settings.margin_buffer_pct,
            hedge_min_delta=self.settings.hedge_min_delta_abs
        )
    
    def get_universe_config(self) -> UniverseConfig:
        """Get universe configuration."""
        return UniverseConfig(
            max_instruments=self.settings.universe_max
        )
    
    def get_options_config(self) -> OptionsConfig:
        """Get options configuration."""
        return OptionsConfig(
            expiry_days=self.settings.options_expiry_days,
            strike_steps=self.settings.options_strike_steps,
            min_oi=self.settings.options_min_oi,
            min_volume=self.settings.options_min_volume,
            iv_smoothing=self.settings.iv_smoothing
        )
    
    def get_costs_config(self) -> CostsConfig:
        """Get transaction costs configuration."""
        return CostsConfig(
            futures_bps=self.settings.txn_cost_fut_bps,
            options_abs=self.settings.txn_cost_opt_abs
        )
    
    def get_slippage_config(self) -> SlippageConfig:
        """Get slippage configuration."""
        return SlippageConfig(
            futures_bps=self.settings.slippage_fut_bps,
            options_abs=self.settings.slippage_opt_abs
        )
    
    def get_dashboard_config(self) -> DashboardConfig:
        """Get dashboard configuration."""
        return DashboardConfig(
            host=self.settings.dashboard_host,
            port=self.settings.dashboard_port
        )
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration."""
        return DatabaseConfig(url=self.settings.database_url)
    
    def get_redis_config(self) -> RedisConfig:
        """Get Redis configuration."""
        return RedisConfig(url=self.settings.redis_url)
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        return LoggingConfig(
            level=self.settings.log_level,
            file=self.settings.log_file
        )
    
    def get_event_blackout_dates(self) -> List[datetime]:
        """Get event blackout dates."""
        if not self.settings.event_blackout_dates:
            return []
        
        dates = []
        for date_str in self.settings.event_blackout_dates.split(','):
            try:
                date = datetime.strptime(date_str.strip(), '%Y-%m-%d')
                dates.append(date)
            except ValueError:
                continue
        
        return dates


# Global configuration instance
config = Config()
