"""
Greeks calculations for the Liquid F&O Trading System.
"""

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, date
import logging

from ..utils.timezone import ISTTimezone


@dataclass
class Greeks:
    """Greeks data structure."""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


class GreeksCalculator:
    """Black-Scholes Greeks calculator."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_greeks(self, spot_price: float, strike_price: float, 
                       time_to_expiry: float, risk_free_rate: float, 
                       volatility: float, option_type: str) -> Greeks:
        """
        Calculate all Greeks for an option.
        
        Args:
            spot_price: Current spot price
            strike_price: Option strike price
            time_to_expiry: Time to expiry in years
            risk_free_rate: Risk-free interest rate
            volatility: Implied volatility
            option_type: 'CALL' or 'PUT'
        """
        try:
            # Calculate d1 and d2
            d1, d2 = self._calculate_d1_d2(
                spot_price, strike_price, time_to_expiry, 
                risk_free_rate, volatility
            )
            
            # Calculate Greeks
            delta = self._calculate_delta(spot_price, strike_price, 
                                        time_to_expiry, risk_free_rate, 
                                        volatility, option_type, d1)
            
            gamma = self._calculate_gamma(spot_price, strike_price, 
                                        time_to_expiry, risk_free_rate, 
                                        volatility, d1)
            
            theta = self._calculate_theta(spot_price, strike_price, 
                                        time_to_expiry, risk_free_rate, 
                                        volatility, option_type, d1, d2)
            
            vega = self._calculate_vega(spot_price, strike_price, 
                                      time_to_expiry, risk_free_rate, 
                                      volatility, d1)
            
            rho = self._calculate_rho(spot_price, strike_price, 
                                    time_to_expiry, risk_free_rate, 
                                    volatility, option_type, d1, d2)
            
            return Greeks(
                delta=delta,
                gamma=gamma,
                theta=theta,
                vega=vega,
                rho=rho
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate Greeks: {e}")
            return Greeks(0, 0, 0, 0, 0)
    
    def _calculate_d1_d2(self, spot_price: float, strike_price: float, 
                        time_to_expiry: float, risk_free_rate: float, 
                        volatility: float) -> Tuple[float, float]:
        """Calculate d1 and d2 for Black-Scholes formula."""
        if time_to_expiry <= 0:
            return 0, 0
        
        d1 = (np.log(spot_price / strike_price) + 
              (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / \
             (volatility * np.sqrt(time_to_expiry))
        
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        return d1, d2
    
    def _calculate_delta(self, spot_price: float, strike_price: float, 
                        time_to_expiry: float, risk_free_rate: float, 
                        volatility: float, option_type: str, d1: float) -> float:
        """Calculate option delta."""
        if option_type.upper() == 'CALL':
            return np.exp(-risk_free_rate * time_to_expiry) * self._normal_cdf(d1)
        else:  # PUT
            return -np.exp(-risk_free_rate * time_to_expiry) * self._normal_cdf(-d1)
    
    def _calculate_gamma(self, spot_price: float, strike_price: float, 
                        time_to_expiry: float, risk_free_rate: float, 
                        volatility: float, d1: float) -> float:
        """Calculate option gamma."""
        return (np.exp(-risk_free_rate * time_to_expiry) * 
                self._normal_pdf(d1)) / (spot_price * volatility * np.sqrt(time_to_expiry))
    
    def _calculate_theta(self, spot_price: float, strike_price: float, 
                        time_to_expiry: float, risk_free_rate: float, 
                        volatility: float, option_type: str, 
                        d1: float, d2: float) -> float:
        """Calculate option theta (per day)."""
        if time_to_expiry <= 0:
            return 0
        
        term1 = -spot_price * self._normal_pdf(d1) * volatility / (2 * np.sqrt(time_to_expiry))
        
        if option_type.upper() == 'CALL':
            term2 = -risk_free_rate * strike_price * np.exp(-risk_free_rate * time_to_expiry) * \
                   self._normal_cdf(d2)
        else:  # PUT
            term2 = risk_free_rate * strike_price * np.exp(-risk_free_rate * time_to_expiry) * \
                   self._normal_cdf(-d2)
        
        return (term1 + term2) / 365  # Convert to per day
    
    def _calculate_vega(self, spot_price: float, strike_price: float, 
                       time_to_expiry: float, risk_free_rate: float, 
                       volatility: float, d1: float) -> float:
        """Calculate option vega."""
        return spot_price * np.exp(-risk_free_rate * time_to_expiry) * \
               self._normal_pdf(d1) * np.sqrt(time_to_expiry) / 100  # Per 1% vol change
    
    def _calculate_rho(self, spot_price: float, strike_price: float, 
                      time_to_expiry: float, risk_free_rate: float, 
                      volatility: float, option_type: str, 
                      d1: float, d2: float) -> float:
        """Calculate option rho."""
        if option_type.upper() == 'CALL':
            return strike_price * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * \
                   self._normal_cdf(d2) / 100  # Per 1% rate change
        else:  # PUT
            return -strike_price * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * \
                   self._normal_cdf(-d2) / 100  # Per 1% rate change
    
    def _normal_cdf(self, x: float) -> float:
        """Cumulative distribution function of standard normal distribution."""
        return 0.5 * (1 + np.sign(x) * np.sqrt(1 - np.exp(-2 * x**2 / np.pi)))
    
    def _normal_pdf(self, x: float) -> float:
        """Probability density function of standard normal distribution."""
        return np.exp(-0.5 * x**2) / np.sqrt(2 * np.pi)
    
    def calculate_portfolio_greeks(self, positions: list) -> Dict[str, float]:
        """Calculate portfolio-level Greeks."""
        total_delta = 0
        total_gamma = 0
        total_theta = 0
        total_vega = 0
        total_rho = 0
        
        for position in positions:
            if not hasattr(position, 'greeks') or not position.greeks:
                continue
            
            # Multiply by position size and direction
            multiplier = position.quantity * (1 if position.side == 'BUY' else -1)
            
            total_delta += position.greeks.delta * multiplier
            total_gamma += position.greeks.gamma * multiplier
            total_theta += position.greeks.theta * multiplier
            total_vega += position.greeks.vega * multiplier
            total_rho += position.greeks.rho * multiplier
        
        return {
            'delta': total_delta,
            'gamma': total_gamma,
            'theta': total_theta,
            'vega': total_vega,
            'rho': total_rho
        }
    
    def calculate_delta_hedge_ratio(self, spot_price: float, strike_price: float, 
                                   time_to_expiry: float, risk_free_rate: float, 
                                   volatility: float, option_type: str) -> float:
        """Calculate delta hedge ratio for options."""
        greeks = self.calculate_greeks(
            spot_price, strike_price, time_to_expiry, 
            risk_free_rate, volatility, option_type
        )
        
        return abs(greeks.delta)
    
    def calculate_gamma_exposure(self, spot_price: float, strike_price: float, 
                               time_to_expiry: float, risk_free_rate: float, 
                               volatility: float, position_size: int) -> float:
        """Calculate gamma exposure for a position."""
        greeks = self.calculate_greeks(
            spot_price, strike_price, time_to_expiry, 
            risk_free_rate, volatility, 'CALL'  # Gamma is same for calls and puts
        )
        
        return greeks.gamma * position_size * spot_price
    
    def calculate_theta_decay(self, spot_price: float, strike_price: float, 
                           time_to_expiry: float, risk_free_rate: float, 
                           volatility: float, option_type: str, 
                           days: int = 1) -> float:
        """Calculate theta decay for specified number of days."""
        greeks = self.calculate_greeks(
            spot_price, strike_price, time_to_expiry, 
            risk_free_rate, volatility, option_type
        )
        
        return greeks.theta * days
    
    def calculate_vega_exposure(self, spot_price: float, strike_price: float, 
                             time_to_expiry: float, risk_free_rate: float, 
                             volatility: float, position_size: int, 
                             vol_change: float = 1.0) -> float:
        """Calculate vega exposure for a position."""
        greeks = self.calculate_greeks(
            spot_price, strike_price, time_to_expiry, 
            risk_free_rate, volatility, 'CALL'  # Vega is same for calls and puts
        )
        
        return greeks.vega * position_size * vol_change
    
    def calculate_breakeven_points(self, spot_price: float, strike_price: float, 
                                time_to_expiry: float, risk_free_rate: float, 
                                volatility: float, option_type: str, 
                                premium: float) -> Tuple[float, float]:
        """Calculate breakeven points for an option."""
        # For calls: breakeven = strike + premium
        # For puts: breakeven = strike - premium
        
        if option_type.upper() == 'CALL':
            breakeven = strike_price + premium
            return breakeven, None
        else:  # PUT
            breakeven = strike_price - premium
            return None, breakeven
    
    def calculate_probability_itm(self, spot_price: float, strike_price: float, 
                                time_to_expiry: float, risk_free_rate: float, 
                                volatility: float, option_type: str) -> float:
        """Calculate probability of finishing in the money."""
        d1, d2 = self._calculate_d1_d2(
            spot_price, strike_price, time_to_expiry, 
            risk_free_rate, volatility
        )
        
        if option_type.upper() == 'CALL':
            return self._normal_cdf(d2)
        else:  # PUT
            return self._normal_cdf(-d2)
    
    def calculate_probability_otm(self, spot_price: float, strike_price: float, 
                                time_to_expiry: float, risk_free_rate: float, 
                                volatility: float, option_type: str) -> float:
        """Calculate probability of finishing out of the money."""
        return 1 - self.calculate_probability_itm(
            spot_price, strike_price, time_to_expiry, 
            risk_free_rate, volatility, option_type
        )
    
    def calculate_expected_value(self, spot_price: float, strike_price: float, 
                               time_to_expiry: float, risk_free_rate: float, 
                               volatility: float, option_type: str) -> float:
        """Calculate expected value of option at expiry."""
        # This is a simplified calculation
        # In practice, you'd use Monte Carlo or other methods
        
        prob_itm = self.calculate_probability_itm(
            spot_price, strike_price, time_to_expiry, 
            risk_free_rate, volatility, option_type
        )
        
        if option_type.upper() == 'CALL':
            expected_payoff = max(0, spot_price - strike_price) * prob_itm
        else:  # PUT
            expected_payoff = max(0, strike_price - spot_price) * prob_itm
        
        return expected_payoff * np.exp(-risk_free_rate * time_to_expiry)
    
    def calculate_risk_metrics(self, positions: list, 
                             spot_prices: Dict[str, float]) -> Dict[str, float]:
        """Calculate portfolio risk metrics."""
        portfolio_greeks = self.calculate_portfolio_greeks(positions)
        
        # Calculate risk metrics
        risk_metrics = {
            'delta_exposure': portfolio_greeks['delta'],
            'gamma_exposure': portfolio_greeks['gamma'],
            'theta_exposure': portfolio_greeks['theta'],
            'vega_exposure': portfolio_greeks['vega'],
            'rho_exposure': portfolio_greeks['rho']
        }
        
        # Calculate dollar delta
        total_dollar_delta = 0
        for position in positions:
            if hasattr(position, 'underlying') and position.underlying in spot_prices:
                spot_price = spot_prices[position.underlying]
                if hasattr(position, 'greeks') and position.greeks:
                    dollar_delta = position.greeks.delta * position.quantity * spot_price
                    total_dollar_delta += dollar_delta * (1 if position.side == 'BUY' else -1)
        
        risk_metrics['dollar_delta'] = total_dollar_delta
        
        return risk_metrics
