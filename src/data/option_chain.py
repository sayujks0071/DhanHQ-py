"""
Option chain data management for the Liquid F&O Trading System.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import logging
from dataclasses import dataclass

from ..config import config
from ..utils.timezone import ISTTimezone


@dataclass
class OptionQuote:
    """Option quote data structure."""
    strike_price: float
    option_type: str  # CALL or PUT
    bid: float
    ask: float
    last_price: float
    volume: int
    open_interest: int
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None


@dataclass
class OptionChain:
    """Option chain data structure."""
    underlying: str
    expiry_date: date
    current_price: float
    calls: List[OptionQuote]
    puts: List[OptionQuote]
    timestamp: datetime


class OptionChainManager:
    """Option chain data manager."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache: Dict[str, OptionChain] = {}
        self.cache_ttl = 60  # 1 minute for option chain data
        
    def get_option_chain(self, underlying: str, expiry_date: date, 
                        broker_adapter) -> Optional[OptionChain]:
        """Get option chain for underlying and expiry."""
        try:
            cache_key = f"{underlying}_{expiry_date}"
            
            # Check cache first
            if self._is_cached(cache_key):
                self.logger.debug(f"Returning cached option chain for {underlying}")
                return self.cache[cache_key]
            
            # Fetch from broker
            self.logger.info(f"Fetching option chain for {underlying} {expiry_date}")
            chain_data = broker_adapter.get_option_chain(underlying, expiry_date)
            
            if not chain_data:
                return None
            
            # Process the data
            option_chain = self._process_option_chain_data(underlying, expiry_date, chain_data)
            
            # Cache the data
            self.cache[cache_key] = option_chain
            
            return option_chain
            
        except Exception as e:
            self.logger.error(f"Failed to get option chain for {underlying}: {e}")
            return None
    
    def _process_option_chain_data(self, underlying: str, expiry_date: date, 
                                 data: Dict) -> OptionChain:
        """Process raw option chain data."""
        current_price = float(data.get('current_price', 0))
        calls_data = data.get('calls', [])
        puts_data = data.get('puts', [])
        
        calls = []
        for call_data in calls_data:
            call = self._parse_option_quote(call_data, 'CALL')
            if call:
                calls.append(call)
        
        puts = []
        for put_data in puts_data:
            put = self._parse_option_quote(put_data, 'PUT')
            if put:
                puts.append(put)
        
        return OptionChain(
            underlying=underlying,
            expiry_date=expiry_date,
            current_price=current_price,
            calls=calls,
            puts=puts,
            timestamp=ISTTimezone.now()
        )
    
    def _parse_option_quote(self, data: Dict, option_type: str) -> Optional[OptionQuote]:
        """Parse option quote data."""
        try:
            return OptionQuote(
                strike_price=float(data.get('strike_price', 0)),
                option_type=option_type,
                bid=float(data.get('bid', 0)),
                ask=float(data.get('ask', 0)),
                last_price=float(data.get('last_price', 0)),
                volume=int(data.get('volume', 0)),
                open_interest=int(data.get('open_interest', 0)),
                implied_volatility=float(data.get('iv', 0)) if data.get('iv') else None,
                delta=float(data.get('delta', 0)) if data.get('delta') else None,
                gamma=float(data.get('gamma', 0)) if data.get('gamma') else None,
                theta=float(data.get('theta', 0)) if data.get('theta') else None,
                vega=float(data.get('vega', 0)) if data.get('vega') else None,
                rho=float(data.get('rho', 0)) if data.get('rho') else None
            )
        except Exception as e:
            self.logger.warning(f"Failed to parse option quote: {e}")
            return None
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if option chain is cached and not expired."""
        if cache_key in self.cache:
            chain = self.cache[cache_key]
            age = (ISTTimezone.now() - chain.timestamp).total_seconds()
            return age < self.cache_ttl
        return False
    
    def get_atm_options(self, option_chain: OptionChain) -> Tuple[OptionQuote, OptionQuote]:
        """Get ATM call and put options."""
        if not option_chain.calls or not option_chain.puts:
            return None, None
        
        current_price = option_chain.current_price
        
        # Find ATM call
        atm_call = min(option_chain.calls, 
                      key=lambda x: abs(x.strike_price - current_price))
        
        # Find ATM put
        atm_put = min(option_chain.puts, 
                     key=lambda x: abs(x.strike_price - current_price))
        
        return atm_call, atm_put
    
    def get_strike_range(self, option_chain: OptionChain, 
                        range_pct: float = 0.1) -> List[float]:
        """Get strikes within range of current price."""
        current_price = option_chain.current_price
        min_price = current_price * (1 - range_pct)
        max_price = current_price * (1 + range_pct)
        
        all_strikes = []
        for call in option_chain.calls:
            if min_price <= call.strike_price <= max_price:
                all_strikes.append(call.strike_price)
        
        return sorted(set(all_strikes))
    
    def get_liquid_options(self, option_chain: OptionChain, 
                          min_volume: int = 100, min_oi: int = 1000) -> Tuple[List[OptionQuote], List[OptionQuote]]:
        """Get liquid call and put options."""
        liquid_calls = [
            call for call in option_chain.calls
            if call.volume >= min_volume and call.open_interest >= min_oi
        ]
        
        liquid_puts = [
            put for put in option_chain.puts
            if put.volume >= min_volume and put.open_interest >= min_oi
        ]
        
        return liquid_calls, liquid_puts
    
    def calculate_iv_surface(self, option_chain: OptionChain) -> pd.DataFrame:
        """Calculate IV surface from option chain."""
        surface_data = []
        
        for call in option_chain.calls:
            if call.implied_volatility:
                surface_data.append({
                    'strike': call.strike_price,
                    'option_type': 'CALL',
                    'iv': call.implied_volatility,
                    'moneyness': call.strike_price / option_chain.current_price
                })
        
        for put in option_chain.puts:
            if put.implied_volatility:
                surface_data.append({
                    'strike': put.strike_price,
                    'option_type': 'PUT',
                    'iv': put.implied_volatility,
                    'moneyness': put.strike_price / option_chain.current_price
                })
        
        if not surface_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(surface_data)
        return df
    
    def get_iv_skew(self, option_chain: OptionChain) -> Dict[str, float]:
        """Calculate IV skew metrics."""
        calls = [call for call in option_chain.calls if call.implied_volatility]
        puts = [put for put in option_chain.puts if put.implied_volatility]
        
        if not calls or not puts:
            return {}
        
        # Sort by strike price
        calls.sort(key=lambda x: x.strike_price)
        puts.sort(key=lambda x: x.strike_price)
        
        current_price = option_chain.current_price
        
        # Find ATM options
        atm_call = min(calls, key=lambda x: abs(x.strike_price - current_price))
        atm_put = min(puts, key=lambda x: abs(x.strike_price - current_price))
        
        # Calculate skew metrics
        skew_metrics = {
            'atm_iv': (atm_call.implied_volatility + atm_put.implied_volatility) / 2,
            'call_put_skew': atm_call.implied_volatility - atm_put.implied_volatility
        }
        
        # Calculate put skew (OTM puts vs ATM)
        otm_puts = [put for put in puts if put.strike_price < current_price * 0.95]
        if otm_puts:
            otm_put = min(otm_puts, key=lambda x: abs(x.strike_price - current_price * 0.9))
            skew_metrics['put_skew'] = otm_put.implied_volatility - atm_put.implied_volatility
        
        # Calculate call skew (OTM calls vs ATM)
        otm_calls = [call for call in calls if call.strike_price > current_price * 1.05]
        if otm_calls:
            otm_call = min(otm_calls, key=lambda x: abs(x.strike_price - current_price * 1.1))
            skew_metrics['call_skew'] = otm_call.implied_volatility - atm_call.implied_volatility
        
        return skew_metrics
    
    def get_volume_profile(self, option_chain: OptionChain) -> Dict[str, List]:
        """Get volume profile for option chain."""
        call_volume = [(call.strike_price, call.volume) for call in option_chain.calls]
        put_volume = [(put.strike_price, put.volume) for put in option_chain.puts]
        
        return {
            'calls': call_volume,
            'puts': put_volume
        }
    
    def get_oi_profile(self, option_chain: OptionChain) -> Dict[str, List]:
        """Get open interest profile for option chain."""
        call_oi = [(call.strike_price, call.open_interest) for call in option_chain.calls]
        put_oi = [(put.strike_price, put.open_interest) for put in option_chain.puts]
        
        return {
            'calls': call_oi,
            'puts': put_oi
        }
    
    def find_max_pain(self, option_chain: OptionChain) -> float:
        """Calculate max pain strike price."""
        all_options = option_chain.calls + option_chain.puts
        
        # Get all unique strikes
        strikes = sorted(set(opt.strike_price for opt in all_options))
        
        max_pain = None
        min_pain = float('inf')
        
        for strike in strikes:
            pain = 0
            
            # Calculate pain for calls (sold calls lose money if price goes above strike)
            for call in option_chain.calls:
                if call.strike_price == strike:
                    if strike < option_chain.current_price:
                        pain += call.open_interest * (option_chain.current_price - strike)
            
            # Calculate pain for puts (sold puts lose money if price goes below strike)
            for put in option_chain.puts:
                if put.strike_price == strike:
                    if strike > option_chain.current_price:
                        pain += put.open_interest * (strike - option_chain.current_price)
            
            if pain < min_pain:
                min_pain = pain
                max_pain = strike
        
        return max_pain
    
    def get_greeks_summary(self, option_chain: OptionChain) -> Dict[str, float]:
        """Get portfolio Greeks summary."""
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0
        
        for call in option_chain.calls:
            if call.delta:
                total_delta += call.delta * call.open_interest
            if call.gamma:
                total_gamma += call.gamma * call.open_interest
            if call.theta:
                total_theta += call.theta * call.open_interest
            if call.vega:
                total_vega += call.vega * call.open_interest
            if call.rho:
                total_rho += call.rho * call.open_interest
        
        for put in option_chain.puts:
            if put.delta:
                total_delta += put.delta * put.open_interest
            if put.gamma:
                total_gamma += put.gamma * put.open_interest
            if put.theta:
                total_theta += put.theta * put.open_interest
            if put.vega:
                total_vega += put.vega * put.open_interest
            if put.rho:
                total_rho += put.rho * put.open_interest
        
        return {
            'total_delta': total_delta,
            'total_gamma': total_gamma,
            'total_theta': total_theta,
            'total_vega': total_vega,
            'total_rho': total_rho
        }
    
    def get_put_call_ratio(self, option_chain: OptionChain) -> float:
        """Calculate put-call ratio."""
        total_put_volume = sum(put.volume for put in option_chain.puts)
        total_call_volume = sum(call.volume for call in option_chain.calls)
        
        if total_call_volume == 0:
            return float('inf')
        
        return total_put_volume / total_call_volume
    
    def get_put_call_oi_ratio(self, option_chain: OptionChain) -> float:
        """Calculate put-call OI ratio."""
        total_put_oi = sum(put.open_interest for put in option_chain.puts)
        total_call_oi = sum(call.open_interest for call in option_chain.calls)
        
        if total_call_oi == 0:
            return float('inf')
        
        return total_put_oi / total_call_oi
    
    def clear_cache(self, underlying: Optional[str] = None) -> None:
        """Clear cache for a specific underlying or all."""
        if underlying:
            keys_to_remove = [key for key in self.cache.keys() if key.startswith(underlying)]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()
        
        self.logger.info(f"Cleared option chain cache for {underlying or 'all underlyings'}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            'cached_chains': len(self.cache),
            'cache_ttl_seconds': self.cache_ttl
        }
