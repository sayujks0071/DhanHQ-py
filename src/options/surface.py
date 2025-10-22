"""
IV Surface management for the Liquid F&O Trading System.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import logging
from dataclasses import dataclass
from scipy.interpolate import griddata, RBFInterpolator
from scipy.optimize import minimize

from .iv import IVCalculator, IVSurface


@dataclass
class SurfacePoint:
    """IV Surface point data structure."""
    strike: float
    expiry: float
    iv: float
    moneyness: float
    time_to_expiry: float


class IVSurfaceManager:
    """IV Surface management and interpolation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.iv_calc = IVCalculator()
        self.surface_cache: Dict[str, IVSurface] = {}
        
    def build_surface(self, option_chain_data: Dict, 
                     risk_free_rate: float = 0.06) -> Optional[IVSurface]:
        """Build IV surface from option chain data."""
        try:
            surface = self.iv_calc.calculate_iv_surface(option_chain_data, risk_free_rate)
            
            if surface:
                # Smooth the surface
                surface = self.iv_calc.smooth_iv_surface(surface)
                
                # Cache the surface
                cache_key = f"{option_chain_data.get('underlying', 'unknown')}_{datetime.now().strftime('%Y%m%d')}"
                self.surface_cache[cache_key] = surface
            
            return surface
            
        except Exception as e:
            self.logger.error(f"Failed to build IV surface: {e}")
            return None
    
    def interpolate_iv(self, surface: IVSurface, strike: float, 
                      time_to_expiry: float) -> Optional[float]:
        """Interpolate IV for given strike and time to expiry."""
        if surface is None or surface.iv_matrix.size == 0:
            return None
        
        try:
            # Find closest points for interpolation
            strike_idx = self._find_closest_index(surface.strikes, strike)
            expiry_idx = self._find_closest_index(surface.expiries, time_to_expiry)
            
            # Simple bilinear interpolation
            if (0 <= strike_idx < len(surface.strikes) and 
                0 <= expiry_idx < len(surface.expiries)):
                
                iv = surface.iv_matrix[expiry_idx, strike_idx]
                
                if not np.isnan(iv):
                    return iv
            
            # If exact match not found, use interpolation
            return self._interpolate_bilinear(surface, strike, time_to_expiry)
            
        except Exception as e:
            self.logger.warning(f"Failed to interpolate IV: {e}")
            return None
    
    def _find_closest_index(self, array: List[float], value: float) -> int:
        """Find index of closest value in array."""
        return min(range(len(array)), key=lambda i: abs(array[i] - value))
    
    def _interpolate_bilinear(self, surface: IVSurface, strike: float, 
                            time_to_expiry: float) -> Optional[float]:
        """Bilinear interpolation for IV surface."""
        try:
            # Get valid data points
            valid_data = []
            for i, expiry in enumerate(surface.expiries):
                for j, strike_price in enumerate(surface.strikes):
                    iv = surface.iv_matrix[i, j]
                    if not np.isnan(iv):
                        valid_data.append((strike_price, expiry, iv))
            
            if len(valid_data) < 4:
                return None
            
            # Use scipy's griddata for interpolation
            points = np.array([(d[0], d[1]) for d in valid_data])
            values = np.array([d[2] for d in valid_data])
            
            interpolated = griddata(points, values, (strike, time_to_expiry), 
                                 method='linear', fill_value=np.nan)
            
            return float(interpolated) if not np.isnan(interpolated) else None
            
        except Exception as e:
            self.logger.warning(f"Failed bilinear interpolation: {e}")
            return None
    
    def calculate_surface_metrics(self, surface: IVSurface) -> Dict[str, float]:
        """Calculate surface metrics."""
        if surface is None or surface.iv_matrix.size == 0:
            return {}
        
        try:
            # Remove NaN values for calculations
            valid_ivs = surface.iv_matrix[~np.isnan(surface.iv_matrix)]
            
            if len(valid_ivs) == 0:
                return {}
            
            metrics = {
                'mean_iv': np.mean(valid_ivs),
                'median_iv': np.median(valid_ivs),
                'std_iv': np.std(valid_ivs),
                'min_iv': np.min(valid_ivs),
                'max_iv': np.max(valid_ivs),
                'iv_range': np.max(valid_ivs) - np.min(valid_ivs)
            }
            
            # Calculate skew metrics
            skew_metrics = self.iv_calc.calculate_iv_skew(surface)
            metrics.update(skew_metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate surface metrics: {e}")
            return {}
    
    def find_arbitrage_opportunities(self, surface: IVSurface, 
                                    tolerance: float = 0.05) -> List[Dict]:
        """Find potential arbitrage opportunities in IV surface."""
        if surface is None or surface.iv_matrix.size == 0:
            return []
        
        opportunities = []
        
        try:
            # Check for calendar spread arbitrage
            calendar_arb = self._find_calendar_arbitrage(surface, tolerance)
            opportunities.extend(calendar_arb)
            
            # Check for butterfly arbitrage
            butterfly_arb = self._find_butterfly_arbitrage(surface, tolerance)
            opportunities.extend(butterfly_arb)
            
            # Check for vertical spread arbitrage
            vertical_arb = self._find_vertical_arbitrage(surface, tolerance)
            opportunities.extend(vertical_arb)
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Failed to find arbitrage opportunities: {e}")
            return []
    
    def _find_calendar_arbitrage(self, surface: IVSurface, 
                               tolerance: float) -> List[Dict]:
        """Find calendar spread arbitrage opportunities."""
        opportunities = []
        
        try:
            # Check for calendar spreads with different expiries
            # This is simplified - in practice, you'd have multiple expiries
            if len(surface.expiries) < 2:
                return opportunities
            
            for i, strike in enumerate(surface.strikes):
                for j in range(len(surface.expiries) - 1):
                    short_iv = surface.iv_matrix[j, i]
                    long_iv = surface.iv_matrix[j + 1, i]
                    
                    if (not np.isnan(short_iv) and not np.isnan(long_iv) and 
                        short_iv > long_iv + tolerance):
                        
                        opportunities.append({
                            'type': 'calendar_spread',
                            'strike': strike,
                            'short_expiry': surface.expiries[j],
                            'long_expiry': surface.expiries[j + 1],
                            'short_iv': short_iv,
                            'long_iv': long_iv,
                            'arbitrage_amount': short_iv - long_iv
                        })
            
            return opportunities
            
        except Exception as e:
            self.logger.warning(f"Failed to find calendar arbitrage: {e}")
            return []
    
    def _find_butterfly_arbitrage(self, surface: IVSurface, 
                                tolerance: float) -> List[Dict]:
        """Find butterfly spread arbitrage opportunities."""
        opportunities = []
        
        try:
            # Check for butterfly spreads
            for i in range(1, len(surface.strikes) - 1):
                wing1_iv = surface.iv_matrix[0, i - 1]
                body_iv = surface.iv_matrix[0, i]
                wing2_iv = surface.iv_matrix[0, i + 1]
                
                if (not np.isnan(wing1_iv) and not np.isnan(body_iv) and 
                    not np.isnan(wing2_iv)):
                    
                    # Check butterfly condition
                    butterfly_iv = (wing1_iv + wing2_iv) / 2
                    
                    if body_iv > butterfly_iv + tolerance:
                        opportunities.append({
                            'type': 'butterfly_spread',
                            'strikes': [surface.strikes[i - 1], surface.strikes[i], surface.strikes[i + 1]],
                            'body_iv': body_iv,
                            'wing_iv': butterfly_iv,
                            'arbitrage_amount': body_iv - butterfly_iv
                        })
            
            return opportunities
            
        except Exception as e:
            self.logger.warning(f"Failed to find butterfly arbitrage: {e}")
            return []
    
    def _find_vertical_arbitrage(self, surface: IVSurface, 
                               tolerance: float) -> List[Dict]:
        """Find vertical spread arbitrage opportunities."""
        opportunities = []
        
        try:
            # Check for vertical spreads
            for i in range(len(surface.strikes) - 1):
                strike1_iv = surface.iv_matrix[0, i]
                strike2_iv = surface.iv_matrix[0, i + 1]
                
                if (not np.isnan(strike1_iv) and not np.isnan(strike2_iv)):
                    
                    # Check vertical spread condition
                    if strike1_iv > strike2_iv + tolerance:
                        opportunities.append({
                            'type': 'vertical_spread',
                            'strikes': [surface.strikes[i], surface.strikes[i + 1]],
                            'higher_strike_iv': strike1_iv,
                            'lower_strike_iv': strike2_iv,
                            'arbitrage_amount': strike1_iv - strike2_iv
                        })
            
            return opportunities
            
        except Exception as e:
            self.logger.warning(f"Failed to find vertical arbitrage: {e}")
            return []
    
    def calculate_surface_curvature(self, surface: IVSurface) -> Dict[str, float]:
        """Calculate surface curvature metrics."""
        if surface is None or surface.iv_matrix.size == 0:
            return {}
        
        try:
            # Calculate curvature along strike dimension
            strike_curvature = []
            for i in range(surface.iv_matrix.shape[0]):
                row = surface.iv_matrix[i, :]
                valid_indices = ~np.isnan(row)
                
                if np.sum(valid_indices) >= 3:
                    valid_row = row[valid_indices]
                    valid_strikes = [surface.strikes[j] for j in range(len(surface.strikes)) if valid_indices[j]]
                    
                    # Calculate second derivative
                    if len(valid_row) >= 3:
                        curvature = np.gradient(np.gradient(valid_row, valid_strikes), valid_strikes)
                        strike_curvature.extend(curvature)
            
            # Calculate curvature along time dimension
            time_curvature = []
            for j in range(surface.iv_matrix.shape[1]):
                col = surface.iv_matrix[:, j]
                valid_indices = ~np.isnan(col)
                
                if np.sum(valid_indices) >= 3:
                    valid_col = col[valid_indices]
                    valid_expiries = [surface.expiries[i] for i in range(len(surface.expiries)) if valid_indices[i]]
                    
                    # Calculate second derivative
                    if len(valid_col) >= 3:
                        curvature = np.gradient(np.gradient(valid_col, valid_expiries), valid_expiries)
                        time_curvature.extend(curvature)
            
            return {
                'mean_strike_curvature': np.mean(strike_curvature) if strike_curvature else 0,
                'std_strike_curvature': np.std(strike_curvature) if strike_curvature else 0,
                'mean_time_curvature': np.mean(time_curvature) if time_curvature else 0,
                'std_time_curvature': np.std(time_curvature) if time_curvature else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate surface curvature: {e}")
            return {}
    
    def optimize_surface_fit(self, surface: IVSurface, 
                           method: str = 'rbf') -> Optional[IVSurface]:
        """Optimize surface fit using advanced interpolation."""
        if surface is None or surface.iv_matrix.size == 0:
            return None
        
        try:
            # Get valid data points
            valid_points = []
            valid_values = []
            
            for i, expiry in enumerate(surface.expiries):
                for j, strike in enumerate(surface.strikes):
                    iv = surface.iv_matrix[i, j]
                    if not np.isnan(iv):
                        valid_points.append([strike, expiry])
                        valid_values.append(iv)
            
            if len(valid_points) < 4:
                return surface
            
            valid_points = np.array(valid_points)
            valid_values = np.array(valid_values)
            
            # Create new surface with optimized fit
            if method == 'rbf':
                # Use RBF interpolation
                rbf = RBFInterpolator(valid_points, valid_values, 
                                    kernel='thin_plate_spline', smoothing=0.1)
                
                # Generate new surface
                new_matrix = np.zeros_like(surface.iv_matrix)
                for i, expiry in enumerate(surface.expiries):
                    for j, strike in enumerate(surface.strikes):
                        new_matrix[i, j] = rbf([[strike, expiry]])[0]
                
                return IVSurface(
                    strikes=surface.strikes,
                    expiries=surface.expiries,
                    iv_matrix=new_matrix,
                    spot_price=surface.spot_price,
                    risk_free_rate=surface.risk_free_rate,
                    timestamp=surface.timestamp
                )
            
            return surface
            
        except Exception as e:
            self.logger.error(f"Failed to optimize surface fit: {e}")
            return surface
    
    def export_surface_data(self, surface: IVSurface, 
                          format: str = 'csv') -> Optional[str]:
        """Export surface data to file."""
        if surface is None:
            return None
        
        try:
            if format.lower() == 'csv':
                # Create DataFrame
                data = []
                for i, expiry in enumerate(surface.expiries):
                    for j, strike in enumerate(surface.strikes):
                        data.append({
                            'strike': strike,
                            'expiry': expiry,
                            'iv': surface.iv_matrix[i, j],
                            'moneyness': strike / surface.spot_price,
                            'time_to_expiry': expiry
                        })
                
                df = pd.DataFrame(data)
                return df.to_csv(index=False)
            
            elif format.lower() == 'json':
                import json
                return json.dumps({
                    'strikes': surface.strikes,
                    'expiries': surface.expiries,
                    'iv_matrix': surface.iv_matrix.tolist(),
                    'spot_price': surface.spot_price,
                    'risk_free_rate': surface.risk_free_rate,
                    'timestamp': surface.timestamp
                })
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to export surface data: {e}")
            return None
    
    def clear_cache(self) -> None:
        """Clear surface cache."""
        self.surface_cache.clear()
        self.logger.info("Cleared IV surface cache")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'cached_surfaces': len(self.surface_cache),
            'cache_keys': list(self.surface_cache.keys())
        }
