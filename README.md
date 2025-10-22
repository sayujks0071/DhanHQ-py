# Liquid F&O Trading System

A production-grade Indian F&O algorithmic trading system with options engine and live web dashboard for monitoring.

## 🚀 Features

- **Liquid F&O Universe**: Top 150 F&O instruments by turnover and OI
- **Options Engine**: Complete Greeks calculations, IV surface, and risk arrays
- **Trading Strategies**: 
  - Futures: Donchian Breakout, Trend-ADX
  - Options: Iron Butterfly, Iron Condor, Debit Spreads, ORB Options
- **Risk Management**: Comprehensive risk controls and Greek caps
- **Backtesting**: Walk-forward optimization with purged K-fold
- **Live Dashboard**: Real-time monitoring with WebSocket updates
- **Paper Trading**: Safe testing environment
- **Live Trading**: Production-ready with safety checks

## 📋 Requirements

- Python 3.11+
- Redis (for caching)
- DhanHQ API credentials
- Static IP addresses (for live trading)

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd liquid-fo-trading
```

2. **Install dependencies**
```bash
pip install -e .
```

3. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Install Redis** (for caching)
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with your credentials:

```bash
# DhanHQ API Credentials
DHAN_CLIENT_ID=your_client_id_here
DHAN_ACCESS_TOKEN=your_access_token_here

# Trading Mode
ENABLE_LIVE=false
ENABLE_OPTIONS=true
DISABLE_EQUITY=true

# Risk Management
RISK_MAX_DAILY_DD=0.02
RISK_PER_TRADE=0.005
MAX_CONCURRENT_POS=8

# Dashboard
DASHBOARD_PORT=8787
```

### Static IP Setup

For live trading, you need to set static IP addresses:

```bash
python setup_static_ip.py
```

## 🚀 Quick Start

### 1. Development Setup
```bash
make dev-setup
```

### 2. Data Ingestion
```bash
make ingest
# or
python -m src.cli ingest
```

### 3. Strategy Research
```bash
make research
# or
python -m src.cli research
```

### 4. Paper Trading
```bash
make run-paper
# or
python -m src.cli run-paper
```

### 5. Live Trading (Production)
```bash
make run-live
# or
python -m src.cli run-live
```

## 📊 Available Commands

### Data Management
- `make ingest` - Build F&O universe and cache historical data
- `make research` - Run walk-forward optimization and strategy ranking

### Trading
- `make run-paper` - Start paper trading engine with dashboard
- `make run-live` - Start live trading engine (requires ENABLE_LIVE=true)

### Reporting
- `make report` - Generate EOD report

### System
- `make test` - Run system tests
- `make status` - Show system status
- `make clean` - Clean build artifacts

## 🎯 Trading Strategies

### Futures Strategies

#### Donchian Breakout
- **Description**: Breakout strategy using Donchian channels
- **Parameters**: Lookback period (20), ATR multiplier (2.0), Time stop (5 days)
- **Risk**: Moderate
- **Best for**: Trending markets

#### Trend-ADX
- **Description**: Trend following with ADX filter
- **Parameters**: ADX period (14), ADX threshold (25), Trend period (20)
- **Risk**: Moderate
- **Best for**: Strong trending markets

### Options Strategies

#### Iron Butterfly
- **Description**: Neutral strategy with limited risk
- **Parameters**: Delta hedge (true), IV rank min (0.3), Wing size ATR (1.5)
- **Risk**: Low
- **Best for**: Low volatility, range-bound markets

#### Iron Condor
- **Description**: Income strategy with defined risk
- **Parameters**: Target POP (0.7), IV rank min (0.4), Wing size ATR (2.0)
- **Risk**: Low
- **Best for**: High volatility, range-bound markets

#### Debit Spread
- **Description**: Directional strategy with limited risk
- **Parameters**: Follow futures (true), Max width (200), Min width (50)
- **Risk**: Moderate
- **Best for**: Directional moves with limited capital

#### ORB Options
- **Description**: Intraday breakout strategy
- **Parameters**: Breakout time (09:30), Time stop (120 min), Profit lock (50%)
- **Risk**: High
- **Best for**: Intraday volatility

## 🛡️ Risk Management

### Position Limits
- **Max concurrent positions**: 8
- **Max daily drawdown**: 2%
- **Max risk per trade**: 0.5%

### Greek Caps (per underlying)
- **Max Delta**: 0.8 lots
- **Max Vega**: 3.0 lots equivalent
- **Max Gamma**: 0.5 (proportional to notional)

### Portfolio Caps
- **Max Portfolio Delta**: 5.0
- **Max Portfolio Vega**: 15.0
- **Max Portfolio Gamma**: 10.0

## 📈 Dashboard

The live dashboard provides real-time monitoring:

- **Live P&L & Drawdown**: Current portfolio performance
- **Positions**: Active positions with Greeks
- **Orders**: Pending and filled orders
- **Risk Metrics**: Portfolio-level risk exposure
- **Strategy Status**: Individual strategy performance
- **Market Data**: Real-time quotes and option chains

Access at: `http://localhost:8787`

## 🧪 Backtesting

### Walk-Forward Optimization
- **Window**: 252 days (1 year)
- **Step**: 63 days (3 months)
- **Purged K-Fold**: Prevents look-ahead bias

### Metrics
- **CAGR**: Compound Annual Growth Rate
- **Sharpe Ratio**: Risk-adjusted returns
- **Sortino Ratio**: Downside risk-adjusted returns
- **Max Drawdown**: Maximum peak-to-trough decline
- **Calmar Ratio**: CAGR / Max Drawdown
- **Profit Factor**: Gross profit / Gross loss
- **Hit Rate**: Percentage of winning trades

## 🔒 Safety Features

### Pre-Live Checks
- Environment variables validation
- API connection testing
- Market hours verification
- Fund availability check
- Risk parameter validation

### Live Trading Safeguards
- Kill switch for emergency stops
- Daily loss limits
- Position size limits
- Greek exposure caps
- Event blackout periods

### Event Blackouts
- RBI Policy Meetings
- Union Budget
- Major Index Rebalances
- Earnings Heavyweights

## 📁 Project Structure

```
src/
├── config.py              # Configuration management
├── utils/
│   └── timezone.py        # IST timezone utilities
├── data/
│   ├── instruments.py     # Instrument master data
│   ├── candles.py         # Historical candle data
│   ├── option_chain.py    # Option chain data
│   └── cache.py          # Redis caching layer
├── options/
│   ├── greeks.py          # Greeks calculations
│   ├── iv.py              # Implied volatility
│   ├── surface.py         # IV surface management
│   ├── margin.py          # Margin calculations
│   └── risk_arrays.py     # Risk arrays
├── strategies/
│   ├── fut_donchian.py    # Donchian breakout
│   ├── opt_iron_fly.py    # Iron butterfly
│   └── ...                # Other strategies
├── backtest/
│   ├── engine.py          # Backtesting engine
│   ├── costs.py           # Transaction costs
│   └── metrics.py         # Performance metrics
├── risk/
│   ├── limits.py          # Risk limits
│   ├── sizing.py          # Position sizing
│   └── dd_guard.py        # Drawdown protection
├── engine/
│   ├── engine_paper.py    # Paper trading engine
│   └── engine_live.py     # Live trading engine
├── monitoring/
│   ├── server.py          # Dashboard server
│   └── ws.py              # WebSocket handler
└── cli.py                 # Command line interface
```

## 🚨 Risk Disclaimer

**IMPORTANT**: This system is for educational and research purposes. Trading involves substantial risk of loss. Past performance does not guarantee future results. Always:

1. **Test thoroughly** in paper trading mode
2. **Start with small positions** in live trading
3. **Monitor closely** during live trading
4. **Have stop-losses** in place
5. **Never risk more** than you can afford to lose

## 📞 Support

For issues and questions:
1. Check the logs in `logs/trading.log`
2. Run `make test` to verify system health
3. Check `make status` for system status
4. Review configuration in `.env` file

## 📄 License

MIT License - see LICENSE file for details.

## 🔄 Updates

- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Added options engine and Greeks calculations
- **v1.2.0**: Enhanced risk management and dashboard
- **v1.3.0**: Added walk-forward optimization and strategy ranking

---

**Happy Trading! 📈**