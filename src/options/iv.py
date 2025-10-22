"""
Implied Volatility calculations for the Liquid F&O Trading System.
"""

import numpy as np
from scipy.optimize import brentq
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

from .greeks import GreeksCalculator


@dataclass
class IVSurface:
    """Implied Volatility Surface data structure."""
    strikes: List[float]
    expiries: List[float]
    iv_matrix: np.ndarray
    spot_price: float
    risk_free_rate: float
    timestamp: str


class IVCalculator:
    """Implied Volatility calculator using Black-Scholes."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.greeks_calc = GreeksCalculator()
        self.max_iterations = 100
        self.tolerance = 1e-6
    
    def calculate_iv(self, spot_price: float, strike_price: float, 
                    time_to_expiry: float, risk_free_rate: float, 
                    market_price: float, option_type: str) -> Optional[float]:
        """
        Calculate implied volatility using Brent's method.
        
        Args:
            spot_price: Current spot price
            strike_price: Option strike price
            time_to_expiry: Time to expiry in years
            risk_free_rate: Risk-free interest rate
            market_price: Market price of the option
            option_type: 'CALL' or 'PUT'
        """
        try:
            # Check for edge cases
            if (market_price <= 0 or time_to_expiry <= 0 or 
                spot_price <= 0 or strike_price <= 0):
                return None
            
            # Define the objective function
            def objective(vol):
                theoretical_price = self._black_scholes_price(
                    spot_price, strike_price, time_to_expiry, 
                    risk_free_rate, vol, option_type
                )
                return theoretical_price - market_price
            
            # Find IV using Brent's method
            # IV typically ranges from 0.01 to 5.0 (1% to 500%)
            iv = brentq(objective, 0.01, 5.0, xtol=self.tolerance, maxiter=self.max_iterations)
            
            return iv
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate IV: {e}")
            return None
    
    def _black_scholes_price(self, spot_price: float, strike_price: float, 
                           time_to_expiry: float, risk_free_rate: float, 
                           volatility: float, option_type: str) -> float:
        """Calculate Black-Scholes option price."""
        if time_to_expiry <= 0:
            # At expiry, option value is intrinsic value
            if option_type.upper() == 'CALL':
                return max(0, spot_price - strike_price)
            else:  # PUT
                return max(0, strike_price - spot_price)
        
        # Calculate d1 and d2
        d1 = (np.log(spot_price / strike_price) + 
              (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / \
             (volatility * np.sqrt(time_to_expiry))
        
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        # Calculate option price
        if option_type.upper() == 'CALL':
            price = (spot_price * self._normal_cdf(d1) - 
                    strike_price * np.exp(-risk_free_rate * time_to_expiry) * 
                    self._normal_cdf(d2))
        else:  # PUT
            price = (strike_price * np.exp(-risk_free_rate * time_to_expiry) * 
                    self._normal_cdf(-d2) - spot_price * self._normal_cdf(-d1))
        
        return max(0, price)  # Ensure non-negative price
    
    def _normal_cdf(self, x: float) -> float:
        """Cumulative distribution function of standard normal distribution."""
        return 0.5 * (1 + np.sign(x) * np.sqrt(1 - np.exp(-2 * x**2 / np.pi)))
    
    def calculate_iv_surface(self, option_chain_data: Dict, 
                           risk_free_rate: float = 0.06) -> IVSurface:
        """Calculate IV surface from option chain data."""
        try:
            spot_price = option_chain_data.get('current_price', 0)
            calls = option_chain_data.get('calls', [])
            puts = option_chain_data.get('puts', [])
            
            if not calls and not puts:
                return None
            
            # Extract strikes and expiries
            strikes = set()
            expiries = set()
            
            for call in calls:
                if call.get('strike_price') and call.get('last_price', 0) > 0:
                    strikes.add(call['strike_price'])
            
            for put in puts:
                if put.get('strike_price') and put.get('last_price', 0) > 0:
                    strikes.add(put['strike_price'])
            
            strikes = sorted(strikes)
            expiries = [1.0]  # Simplified - single expiry
            
            # Calculate IV matrix
            iv_matrix = np.zeros((len(expiries), len(strikes)))
            
            for i, expiry in enumerate(expiries):
                for j, strike in enumerate(strikes):
                    # Find corresponding option data
                    call_data = next((c for c in calls 
                                    if c.get('strike_price') == strike), None)
                    put_data = next((p for p in puts 
                                   if p.get('strike_price') == strike), None)
                    
                    # Calculate IV for call and put, then average
                    call_iv = None
                    put_iv = None
                    
                    if call_data and call_data.get('last_price', 0) > 0:
                        call_iv = self.calculate_iv(
                            spot_price, strike, expiry, risk_free_rate,
                            call_data['last_price'], 'CALL'
                        )
                    
                    if put_data and put_data.get('last_price', 0) > 0:
                        put_iv = self.calculate_iv(
                            spot_price, strike, expiry, risk_free_rate,
                            put_data['last_price'], 'PUT'
                        )
                    
                    # Average the IVs if both available
                    if call_iv and put_iv:
                        iv_matrix[i, j] = (call_iv + put_iv) / 2
                    elif call_iv:
                        iv_matrix[i, j] = call_iv
                    elif put_iv:
                        iv_matrix[i, j] = put_iv
                    else:
                        iv_matrix[i, j] = np.nan
            
            return IVSurface(
                strikes=strikes,
                expiries=expiries,
                iv_matrix=iv_matrix,
                spot_price=spot_price,
                risk_free_rate=risk_free_rate,
                timestamp=str(np.datetime64('now'))
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate IV surface: {e}")
            return None
    
    def calculate_iv_rank(self, current_iv: float, historical_ivs: List[float]) -> float:
        """Calculate IV rank (percentile of current IV in historical range)."""
        if not historical_ivs or len(historical_ivs) < 2:
            return 0.5  # Default to 50th percentile
        
        historical_ivs = [iv for iv in historical_ivs if iv > 0]
        
        if not historical_ivs:
            return 0.5
        
        # Calculate percentile
        rank = sum(1 for iv in historical_ivs if iv <= current_iv) / len(historical_ivs)
        return rank
    
    def calculate_iv_percentile(self, current_iv: float, historical_ivs: List[float], 
                              period: int = 252) -> float:
        """Calculate IV percentile over specified period."""
        if not historical_ivs or len(historical_ivs) < period:
            return 0.5
        
        # Take last N days
        recent_ivs = historical_ivs[-period:]
        recent_ivs = [iv for iv in recent_ivs if iv > 0]
        
        if not recent_ivs:
            return 0.5
        
        # Calculate percentile
        percentile = sum(1 for iv in recent_ivs if iv <= current_iv) / len(recent_ivs)
        return percentile
    
    def calculate_iv_skew(self, iv_surface: IVSurface) -> Dict[str, float]:
        """Calculate IV skew metrics."""
        if iv_surface is None or iv_surface.iv_matrix.size == 0:
            return {}
        
        try:
            # Get ATM strike (closest to spot price)
            atm_idx = min(range(len(iv_surface.strikes)), 
                         key=lambda i: abs(iv_surface.strikes[i] - iv_surface.spot_price))
            
            atm_iv = iv_surface.iv_matrix[0, atm_idx]
            
            # Calculate skew metrics
            skew_metrics = {
                'atm_iv': atm_iv,
                'iv_skew': 0.0,
                'put_skew': 0.0,
                'call_skew': 0.0
            }
            
            # Put skew (OTM puts vs ATM)
            otm_put_indices = [i for i in range(len(iv_surface.strikes)) 
                             if iv_surface.strikes[i] < iv_surface.spot_price * 0.95]
            if otm_put_indices:
                otm_put_idx = min(otm_put_indices, 
                                key=lambda i: abs(iv_surface.strikes[i] - iv_surface.spot_price * 0.9))
                otm_put_iv = iv_surface.iv_matrix[0, otm_put_idx]
                skew_metrics['put_skew'] = otm_put_iv - atm_iv
            
            # Call skew (OTM calls vs ATM)
            otm_call_indices = [i for i in range(len(iv_surface.strikes)) 
                              if iv_surface.strikes[i] > iv_surface.spot_price * 1.05]
            if otm_call_indices:
                otm_call_idx = min(otm_call_indices, 
                                 key=lambda i: abs(iv_surface.strikes[i] - iv_surface.spot_price * 1.1))
                otm_call_iv = iv_surface.iv_matrix[0, otm_call_idx]
                skew_metrics['call_skew'] = otm_call_iv - atm_iv
            
            # Overall skew
            skew_metrics['iv_skew'] = skew_metrics['call_skew'] - skew_metrics['put_skew']
            
            return skew_metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate IV skew: {e}")
            return {}
    
    def smooth_iv_surface(self, iv_surface: IVSurface, 
                          smoothing_factor: float = 0.5) -> IVSurface:
        """Smooth IV surface using exponential moving average."""
        if iv_surface is None:
            return None
        
        try:
            # Apply smoothing to IV matrix
            smoothed_matrix = iv_surface.iv_matrix.copy()
            
            # Simple smoothing - replace NaN values with interpolated values
            for i in range(smoothed_matrix.shape[0]):
                row = smoothed_matrix[i, :]
                valid_indices = ~np.isnan(row)
                
                if np.any(valid_indices):
                    # Interpolate missing values
                    valid_values = row[valid_indices]
                    valid_positions = np.where(valid_indices)[0]
                    
                    if len(valid_values) > 1:
                        # Linear interpolation
                        smoothed_row = np.interp(
                            range(len(row)), 
                            valid_positions, 
                            valid_values
                        )
                        smoothed_matrix[i, :] = smoothed_row
            
            return IVSurface(
                strikes=iv_surface.strikes,
                expiries=iv_surface.expiries,
                iv_matrix=smoothed_matrix,
                spot_price=iv_surface.spot_price,
                risk_free_rate=iv_surface.risk_free_rate,
                timestamp=iv_surface.timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Failed to smooth IV surface: {e}")
            return iv_surface
    
    def calculate_iv_term_structure(self, option_chain_data: Dict, 
                                   risk_free_rate: float = 0.06) -> Dict[str, float]:
        """Calculate IV term structure."""
        try:
            # This is a simplified implementation
            # In practice, you'd have multiple expiries
            
            spot_price = option_chain_data.get('current_price', 0)
            calls = option_chain_data.get('calls', [])
            puts = option_chain_data.get('puts', [])
            
            # Find ATM options
            atm_calls = [c for c in calls if abs(c.get('strike_price', 0) - spot_price) < spot_price * 0.02]
            atm_puts = [p for p in puts if abs(p.get('strike_price', 0) - spot_price) < spot_price * 0.02]
            
            term_structure = {}
            
            # Calculate IV for ATM options
            if atm_calls and atm_calls[0].get('last_price', 0) > 0:
                call_iv = self.calculate_iv(
                    spot_price, atm_calls[0]['strike_price'], 1.0, 
                    risk_free_rate, atm_calls[0]['last_price'], 'CALL'
                )
                if call_iv:
                    term_structure['near_term_iv'] = call_iv
            
            if atm_puts and atm_puts[0].get('last_price', 0) > 0:
                put_iv = self.calculate_iv(
                    spot_price, atm_puts[0]['strike_price'], 1.0, 
                    risk_free_rate, atm_puts[0]['last_price'], 'PUT'
                )
                if put_iv:
                    term_structure['near_term_iv'] = put_iv
            
            return term_structure
            
        except Exception as e:
            self.logger.error(f"Failed to calculate IV term structure: {e}")
            return {}
    
    def calculate_iv_forecast(self, historical_ivs: List[float], 
                            forecast_days: int = 30) -> Dict[str, float]:
        """Calculate IV forecast using historical data."""
        if not historical_ivs or len(historical_ivs) < 30:
            return {}
        
        try:
            # Simple moving average forecast
            recent_ivs = historical_ivs[-30:]  # Last 30 days
            avg_iv = np.mean(recent_ivs)
            
            # Calculate volatility of IV
            iv_volatility = np.std(recent_ivs)
            
            # Simple forecast
            forecast = {
                'forecast_iv': avg_iv,
                'iv_volatility': iv_volatility,
                'confidence_interval_lower': avg_iv - 1.96 * iv_volatility,
                'confidence_interval_upper': avg_iv + 1.96 * iv_volatility
            }
            
            return forecast
            
        except Exception as e:
            self.logger.error(f"Failed to calculate IV forecast: {e}")
            return {}
