"""
Instrument master data management for the Liquid F&O Trading System.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import logging
from dataclasses import dataclass
from enum import Enum

from ..config import config
from ..utils.timezone import ISTTimezone


class InstrumentType(Enum):
    """Instrument type enumeration."""
    EQUITY = "EQUITY"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    INDEX = "INDEX"


class ExchangeSegment(Enum):
    """Exchange segment enumeration."""
    NSE_EQ = "NSE_EQ"
    NSE_FNO = "NSE_FNO"
    BSE_EQ = "BSE_EQ"
    BSE_FNO = "BSE_FNO"
    MCX_COMM = "MCX_COMM"
    IDX_I = "IDX_I"


@dataclass
class Instrument:
    """Instrument data structure."""
    symbol: str
    security_id: str
    instrument_type: InstrumentType
    exchange_segment: ExchangeSegment
    lot_size: int
    tick_size: float
    strike_price: Optional[float] = None
    expiry_date: Optional[date] = None
    option_type: Optional[str] = None  # CALL or PUT
    underlying: Optional[str] = None
    is_active: bool = True
    last_updated: Optional[datetime] = None


class InstrumentMaster:
    """Instrument master data manager."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.instruments: Dict[str, Instrument] = {}
        self.universe_config = config.get_universe_config()
        
    def load_instruments(self, broker_adapter) -> None:
        """Load instruments from broker."""
        try:
            self.logger.info("Loading instrument master data...")
            
            # Get instruments from broker
            instruments_data = broker_adapter.get_instruments()
            
            for instrument_data in instruments_data:
                instrument = self._parse_instrument(instrument_data)
                if instrument:
                    self.instruments[instrument.security_id] = instrument
            
            self.logger.info(f"Loaded {len(self.instruments)} instruments")
            
        except Exception as e:
            self.logger.error(f"Failed to load instruments: {e}")
            raise
    
    def _parse_instrument(self, data: Dict) -> Optional[Instrument]:
        """Parse instrument data from broker response."""
        try:
            return Instrument(
                symbol=data.get('symbol', ''),
                security_id=str(data.get('security_id', '')),
                instrument_type=InstrumentType(data.get('instrument_type', 'EQUITY')),
                exchange_segment=ExchangeSegment(data.get('exchange_segment', 'NSE_EQ')),
                lot_size=int(data.get('lot_size', 1)),
                tick_size=float(data.get('tick_size', 0.05)),
                strike_price=data.get('strike_price'),
                expiry_date=self._parse_date(data.get('expiry_date')),
                option_type=data.get('option_type'),
                underlying=data.get('underlying'),
                is_active=data.get('is_active', True),
                last_updated=ISTTimezone.now()
            )
        except Exception as e:
            self.logger.warning(f"Failed to parse instrument {data}: {e}")
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    def get_instrument(self, security_id: str) -> Optional[Instrument]:
        """Get instrument by security ID."""
        return self.instruments.get(security_id)
    
    def get_futures(self, underlying: str) -> List[Instrument]:
        """Get all futures for an underlying."""
        return [
            inst for inst in self.instruments.values()
            if (inst.instrument_type == InstrumentType.FUTURE and 
                inst.underlying == underlying and 
                inst.is_active)
        ]
    
    def get_options(self, underlying: str, expiry_date: Optional[date] = None) -> List[Instrument]:
        """Get options for an underlying, optionally filtered by expiry."""
        options = [
            inst for inst in self.instruments.values()
            if (inst.instrument_type == InstrumentType.OPTION and 
                inst.underlying == underlying and 
                inst.is_active)
        ]
        
        if expiry_date:
            options = [opt for opt in options if opt.expiry_date == expiry_date]
        
        return options
    
    def get_option_chain(self, underlying: str, expiry_date: date) -> Dict[str, List[Instrument]]:
        """Get option chain for underlying and expiry."""
        options = self.get_options(underlying, expiry_date)
        
        chain = {
            'calls': [],
            'puts': []
        }
        
        for option in options:
            if option.option_type == 'CALL':
                chain['calls'].append(option)
            elif option.option_type == 'PUT':
                chain['puts'].append(option)
        
        # Sort by strike price
        chain['calls'].sort(key=lambda x: x.strike_price or 0)
        chain['puts'].sort(key=lambda x: x.strike_price or 0)
        
        return chain
    
    def get_liquid_universe(self, broker_adapter) -> List[str]:
        """Get liquid F&O universe based on criteria."""
        try:
            self.logger.info("Building liquid F&O universe...")
            
            # Get turnover and OI data
            turnover_data = broker_adapter.get_turnover_data()
            oi_data = broker_adapter.get_oi_data()
            
            liquid_instruments = []
            
            for security_id, instrument in self.instruments.items():
                if not self._is_fno_eligible(instrument):
                    continue
                
                # Check turnover criteria
                turnover = turnover_data.get(security_id, 0)
                if turnover < self.universe_config.min_turnover_30d:
                    continue
                
                # Check OI criteria
                oi = oi_data.get(security_id, 0)
                if oi < self.universe_config.min_oi:
                    continue
                
                # Check lot value
                lot_value = instrument.lot_size * self._get_current_price(security_id, broker_adapter)
                if (lot_value < self.universe_config.min_lot_value or 
                    lot_value > self.universe_config.max_lot_value):
                    continue
                
                # Check price
                current_price = self._get_current_price(security_id, broker_adapter)
                if current_price < self.universe_config.min_price:
                    continue
                
                # Check spread
                if not self._check_spread(security_id, broker_adapter):
                    continue
                
                liquid_instruments.append(security_id)
            
            # Sort by turnover and take top N
            liquid_instruments.sort(
                key=lambda x: turnover_data.get(x, 0), 
                reverse=True
            )
            
            universe = liquid_instruments[:self.universe_config.max_instruments]
            
            self.logger.info(f"Built universe with {len(universe)} instruments")
            return universe
            
        except Exception as e:
            self.logger.error(f"Failed to build liquid universe: {e}")
            raise
    
    def _is_fno_eligible(self, instrument: Instrument) -> bool:
        """Check if instrument is F&O eligible."""
        return (
            instrument.exchange_segment in [ExchangeSegment.NSE_FNO, ExchangeSegment.BSE_FNO] and
            instrument.instrument_type in [InstrumentType.FUTURE, InstrumentType.OPTION] and
            instrument.is_active
        )
    
    def _get_current_price(self, security_id: str, broker_adapter) -> float:
        """Get current price for instrument."""
        try:
            quote = broker_adapter.get_quote(security_id)
            return float(quote.get('ltp', 0))
        except:
            return 0.0
    
    def _check_spread(self, security_id: str, broker_adapter) -> bool:
        """Check if spread is within acceptable limits."""
        try:
            quote = broker_adapter.get_quote(security_id)
            bid = float(quote.get('bid', 0))
            ask = float(quote.get('ask', 0))
            
            if bid == 0 or ask == 0:
                return False
            
            spread_bps = ((ask - bid) / bid) * 10000
            return spread_bps <= self.universe_config.max_spread_bps
            
        except:
            return False
    
    def get_atm_strikes(self, underlying: str, expiry_date: date, 
                       current_price: float) -> Tuple[float, float]:
        """Get ATM call and put strikes."""
        chain = self.get_option_chain(underlying, expiry_date)
        
        if not chain['calls'] or not chain['puts']:
            return None, None
        
        # Find ATM strikes
        call_strikes = [opt.strike_price for opt in chain['calls'] if opt.strike_price]
        put_strikes = [opt.strike_price for opt in chain['puts'] if opt.strike_price]
        
        # Find closest strikes to current price
        atm_call = min(call_strikes, key=lambda x: abs(x - current_price))
        atm_put = min(put_strikes, key=lambda x: abs(x - current_price))
        
        return atm_call, atm_put
    
    def get_strike_range(self, underlying: str, expiry_date: date, 
                        current_price: float, range_pct: float = 0.1) -> List[float]:
        """Get strikes within range of current price."""
        chain = self.get_option_chain(underlying, expiry_date)
        
        all_strikes = []
        for opt in chain['calls'] + chain['puts']:
            if opt.strike_price:
                all_strikes.append(opt.strike_price)
        
        all_strikes = sorted(set(all_strikes))
        
        min_price = current_price * (1 - range_pct)
        max_price = current_price * (1 + range_pct)
        
        return [strike for strike in all_strikes 
                if min_price <= strike <= max_price]
    
    def get_expiry_dates(self, underlying: str) -> List[date]:
        """Get all expiry dates for an underlying."""
        options = self.get_options(underlying)
        expiry_dates = set()
        
        for opt in options:
            if opt.expiry_date:
                expiry_dates.add(opt.expiry_date)
        
        return sorted(expiry_dates)
    
    def get_weekly_expiries(self, underlying: str) -> List[date]:
        """Get weekly expiry dates for an underlying."""
        all_expiries = self.get_expiry_dates(underlying)
        
        # Filter for weekly expiries (typically Thursday)
        weekly_expiries = []
        for expiry in all_expiries:
            if expiry.weekday() == 3:  # Thursday
                weekly_expiries.append(expiry)
        
        return sorted(weekly_expiries)
    
    def get_monthly_expiries(self, underlying: str) -> List[date]:
        """Get monthly expiry dates for an underlying."""
        all_expiries = self.get_expiry_dates(underlying)
        
        # Group by month and get last Thursday of each month
        monthly_expiries = []
        current_month = None
        current_expiry = None
        
        for expiry in sorted(all_expiries):
            if expiry.weekday() == 3:  # Thursday
                if current_month != expiry.month:
                    if current_expiry:
                        monthly_expiries.append(current_expiry)
                    current_month = expiry.month
                current_expiry = expiry
        
        if current_expiry:
            monthly_expiries.append(current_expiry)
        
        return monthly_expiries
    
    def update_instrument(self, security_id: str, updates: Dict) -> None:
        """Update instrument data."""
        if security_id in self.instruments:
            instrument = self.instruments[security_id]
            for key, value in updates.items():
                if hasattr(instrument, key):
                    setattr(instrument, key, value)
            instrument.last_updated = ISTTimezone.now()
    
    def get_universe_summary(self) -> Dict:
        """Get summary of current universe."""
        total = len(self.instruments)
        futures = len([i for i in self.instruments.values() 
                      if i.instrument_type == InstrumentType.FUTURE])
        options = len([i for i in self.instruments.values() 
                      if i.instrument_type == InstrumentType.OPTION])
        active = len([i for i in self.instruments.values() if i.is_active])
        
        return {
            'total_instruments': total,
            'futures': futures,
            'options': options,
            'active': active,
            'last_updated': ISTTimezone.now()
        }
