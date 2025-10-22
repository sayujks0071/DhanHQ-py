"""
Risk arrays for options strategies in the Liquid F&O Trading System.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import logging

from .greeks import GreeksCalculator


@dataclass
class RiskArray:
    """Risk array data structure."""
    underlying_prices: List[float]
    iv_changes: List[float]
    time_decays: List[float]
    pnl_matrix: np.ndarray
    delta_matrix: np.ndarray
    gamma_matrix: np.ndarray
    theta_matrix: np.ndarray
    vega_matrix: np.ndarray


class RiskArrayCalculator:
    """Risk array calculator for options strategies."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.greeks_calc = GreeksCalculator()
        
        # Default risk array parameters
        self.price_range = 0.20  # ±20% price range
        self.iv_range = 0.50     # ±50% IV range
        self.time_range = 30     # 30 days time decay
        self.price_steps = 21    # 21 price steps
        self.iv_steps = 11       # 11 IV steps
        self.time_steps = 31     # 31 time steps
    
    def calculate_risk_array(self, strategy_legs: List[Dict], 
                           current_price: float, current_iv: float, 
                           time_to_expiry: float, risk_free_rate: float = 0.06) -> RiskArray:
        """Calculate risk array for a strategy."""
        try:
            # Generate price scenarios
            price_scenarios = self._generate_price_scenarios(current_price)
            
            # Generate IV scenarios
            iv_scenarios = self._generate_iv_scenarios(current_iv)
            
            # Generate time scenarios
            time_scenarios = self._generate_time_scenarios(time_to_expiry)
            
            # Calculate P&L matrix
            pnl_matrix = self._calculate_pnl_matrix(
                strategy_legs, price_scenarios, iv_scenarios, 
                time_scenarios, risk_free_rate
            )
            
            # Calculate Greeks matrices
            delta_matrix = self._calculate_delta_matrix(
                strategy_legs, price_scenarios, iv_scenarios, 
                time_scenarios, risk_free_rate
            )
            
            gamma_matrix = self._calculate_gamma_matrix(
                strategy_legs, price_scenarios, iv_scenarios, 
                time_scenarios, risk_free_rate
            )
            
            theta_matrix = self._calculate_theta_matrix(
                strategy_legs, price_scenarios, iv_scenarios, 
                time_scenarios, risk_free_rate
            )
            
            vega_matrix = self._calculate_vega_matrix(
                strategy_legs, price_scenarios, iv_scenarios, 
                time_scenarios, risk_free_rate
            )
            
            return RiskArray(
                underlying_prices=price_scenarios,
                iv_changes=iv_scenarios,
                time_decays=time_scenarios,
                pnl_matrix=pnl_matrix,
                delta_matrix=delta_matrix,
                gamma_matrix=gamma_matrix,
                theta_matrix=theta_matrix,
                vega_matrix=vega_matrix
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate risk array: {e}")
            return self._create_empty_risk_array()
    
    def _generate_price_scenarios(self, current_price: float) -> List[float]:
        """Generate price scenarios."""
        min_price = current_price * (1 - self.price_range)
        max_price = current_price * (1 + self.price_range)
        
        return np.linspace(min_price, max_price, self.price_steps).tolist()
    
    def _generate_iv_scenarios(self, current_iv: float) -> List[float]:
        """Generate IV scenarios."""
        min_iv = max(0.01, current_iv * (1 - self.iv_range))
        max_iv = current_iv * (1 + self.iv_range)
        
        return np.linspace(min_iv, max_iv, self.iv_steps).tolist()
    
    def _generate_time_scenarios(self, time_to_expiry: float) -> List[float]:
        """Generate time scenarios."""
        min_time = max(0.001, time_to_expiry - self.time_range / 365)
        max_time = time_to_expiry
        
        return np.linspace(max_time, min_time, self.time_steps).tolist()
    
    def _calculate_pnl_matrix(self, strategy_legs: List[Dict], 
                            price_scenarios: List[float], iv_scenarios: List[float], 
                            time_scenarios: List[float], risk_free_rate: float) -> np.ndarray:
        """Calculate P&L matrix for all scenarios."""
        pnl_matrix = np.zeros((len(price_scenarios), len(iv_scenarios), len(time_scenarios)))
        
        for i, price in enumerate(price_scenarios):
            for j, iv in enumerate(iv_scenarios):
                for k, time_to_expiry in enumerate(time_scenarios):
                    pnl = 0
                    
                    for leg in strategy_legs:
                        leg_pnl = self._calculate_leg_pnl(
                            leg, price, iv, time_to_expiry, risk_free_rate
                        )
                        pnl += leg_pnl
                    
                    pnl_matrix[i, j, k] = pnl
        
        return pnl_matrix
    
    def _calculate_leg_pnl(self, leg: Dict, price: float, iv: float, 
                          time_to_expiry: float, risk_free_rate: float) -> float:
        """Calculate P&L for a single leg."""
        try:
            strike_price = leg.get('strike_price', 0)
            option_type = leg.get('option_type', 'CALL')
            action = leg.get('action', 'BUY')
            quantity = leg.get('quantity', 0)
            premium = leg.get('premium', 0)
            
            # Calculate theoretical price
            theoretical_price = self._calculate_theoretical_price(
                price, strike_price, time_to_expiry, risk_free_rate, iv, option_type
            )
            
            # Calculate P&L
            if action == 'BUY':
                pnl = (theoretical_price - premium) * quantity
            else:  # SELL
                pnl = (premium - theoretical_price) * quantity
            
            return pnl
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate leg P&L: {e}")
            return 0
    
    def _calculate_theoretical_price(self, spot_price: float, strike_price: float, 
                                   time_to_expiry: float, risk_free_rate: float, 
                                   volatility: float, option_type: str) -> float:
        """Calculate theoretical option price using Black-Scholes."""
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
        
        return max(0, price)
    
    def _calculate_delta_matrix(self, strategy_legs: List[Dict], 
                              price_scenarios: List[float], iv_scenarios: List[float], 
                              time_scenarios: List[float], risk_free_rate: float) -> np.ndarray:
        """Calculate delta matrix for all scenarios."""
        delta_matrix = np.zeros((len(price_scenarios), len(iv_scenarios), len(time_scenarios)))
        
        for i, price in enumerate(price_scenarios):
            for j, iv in enumerate(iv_scenarios):
                for k, time_to_expiry in enumerate(time_scenarios):
                    total_delta = 0
                    
                    for leg in strategy_legs:
                        leg_delta = self._calculate_leg_delta(
                            leg, price, iv, time_to_expiry, risk_free_rate
                        )
                        total_delta += leg_delta
                    
                    delta_matrix[i, j, k] = total_delta
        
        return delta_matrix
    
    def _calculate_leg_delta(self, leg: Dict, price: float, iv: float, 
                           time_to_expiry: float, risk_free_rate: float) -> float:
        """Calculate delta for a single leg."""
        try:
            strike_price = leg.get('strike_price', 0)
            option_type = leg.get('option_type', 'CALL')
            action = leg.get('action', 'BUY')
            quantity = leg.get('quantity', 0)
            
            # Calculate Greeks
            greeks = self.greeks_calc.calculate_greeks(
                price, strike_price, time_to_expiry, risk_free_rate, iv, option_type
            )
            
            # Calculate leg delta
            leg_delta = greeks.delta * quantity
            
            if action == 'SELL':
                leg_delta = -leg_delta
            
            return leg_delta
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate leg delta: {e}")
            return 0
    
    def _calculate_gamma_matrix(self, strategy_legs: List[Dict], 
                              price_scenarios: List[float], iv_scenarios: List[float], 
                              time_scenarios: List[float], risk_free_rate: float) -> np.ndarray:
        """Calculate gamma matrix for all scenarios."""
        gamma_matrix = np.zeros((len(price_scenarios), len(iv_scenarios), len(time_scenarios)))
        
        for i, price in enumerate(price_scenarios):
            for j, iv in enumerate(iv_scenarios):
                for k, time_to_expiry in enumerate(time_scenarios):
                    total_gamma = 0
                    
                    for leg in strategy_legs:
                        leg_gamma = self._calculate_leg_gamma(
                            leg, price, iv, time_to_expiry, risk_free_rate
                        )
                        total_gamma += leg_gamma
                    
                    gamma_matrix[i, j, k] = total_gamma
        
        return gamma_matrix
    
    def _calculate_leg_gamma(self, leg: Dict, price: float, iv: float, 
                           time_to_expiry: float, risk_free_rate: float) -> float:
        """Calculate gamma for a single leg."""
        try:
            strike_price = leg.get('strike_price', 0)
            option_type = leg.get('option_type', 'CALL')
            action = leg.get('action', 'BUY')
            quantity = leg.get('quantity', 0)
            
            # Calculate Greeks
            greeks = self.greeks_calc.calculate_greeks(
                price, strike_price, time_to_expiry, risk_free_rate, iv, option_type
            )
            
            # Calculate leg gamma
            leg_gamma = greeks.gamma * quantity
            
            if action == 'SELL':
                leg_gamma = -leg_gamma
            
            return leg_gamma
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate leg gamma: {e}")
            return 0
    
    def _calculate_theta_matrix(self, strategy_legs: List[Dict], 
                              price_scenarios: List[float], iv_scenarios: List[float], 
                              time_scenarios: List[float], risk_free_rate: float) -> np.ndarray:
        """Calculate theta matrix for all scenarios."""
        theta_matrix = np.zeros((len(price_scenarios), len(iv_scenarios), len(time_scenarios)))
        
        for i, price in enumerate(price_scenarios):
            for j, iv in enumerate(iv_scenarios):
                for k, time_to_expiry in enumerate(time_scenarios):
                    total_theta = 0
                    
                    for leg in strategy_legs:
                        leg_theta = self._calculate_leg_theta(
                            leg, price, iv, time_to_expiry, risk_free_rate
                        )
                        total_theta += leg_theta
                    
                    theta_matrix[i, j, k] = total_theta
        
        return theta_matrix
    
    def _calculate_leg_theta(self, leg: Dict, price: float, iv: float, 
                           time_to_expiry: float, risk_free_rate: float) -> float:
        """Calculate theta for a single leg."""
        try:
            strike_price = leg.get('strike_price', 0)
            option_type = leg.get('option_type', 'CALL')
            action = leg.get('action', 'BUY')
            quantity = leg.get('quantity', 0)
            
            # Calculate Greeks
            greeks = self.greeks_calc.calculate_greeks(
                price, strike_price, time_to_expiry, risk_free_rate, iv, option_type
            )
            
            # Calculate leg theta
            leg_theta = greeks.theta * quantity
            
            if action == 'SELL':
                leg_theta = -leg_theta
            
            return leg_theta
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate leg theta: {e}")
            return 0
    
    def _calculate_vega_matrix(self, strategy_legs: List[Dict], 
                             price_scenarios: List[float], iv_scenarios: List[float], 
                             time_scenarios: List[float], risk_free_rate: float) -> np.ndarray:
        """Calculate vega matrix for all scenarios."""
        vega_matrix = np.zeros((len(price_scenarios), len(iv_scenarios), len(time_scenarios)))
        
        for i, price in enumerate(price_scenarios):
            for j, iv in enumerate(iv_scenarios):
                for k, time_to_expiry in enumerate(time_scenarios):
                    total_vega = 0
                    
                    for leg in strategy_legs:
                        leg_vega = self._calculate_leg_vega(
                            leg, price, iv, time_to_expiry, risk_free_rate
                        )
                        total_vega += leg_vega
                    
                    vega_matrix[i, j, k] = total_vega
        
        return vega_matrix
    
    def _calculate_leg_vega(self, leg: Dict, price: float, iv: float, 
                          time_to_expiry: float, risk_free_rate: float) -> float:
        """Calculate vega for a single leg."""
        try:
            strike_price = leg.get('strike_price', 0)
            option_type = leg.get('option_type', 'CALL')
            action = leg.get('action', 'BUY')
            quantity = leg.get('quantity', 0)
            
            # Calculate Greeks
            greeks = self.greeks_calc.calculate_greeks(
                price, strike_price, time_to_expiry, risk_free_rate, iv, option_type
            )
            
            # Calculate leg vega
            leg_vega = greeks.vega * quantity
            
            if action == 'SELL':
                leg_vega = -leg_vega
            
            return leg_vega
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate leg vega: {e}")
            return 0
    
    def _normal_cdf(self, x: float) -> float:
        """Cumulative distribution function of standard normal distribution."""
        return 0.5 * (1 + np.sign(x) * np.sqrt(1 - np.exp(-2 * x**2 / np.pi)))
    
    def _create_empty_risk_array(self) -> RiskArray:
        """Create empty risk array."""
        return RiskArray(
            underlying_prices=[],
            iv_changes=[],
            time_decays=[],
            pnl_matrix=np.array([]),
            delta_matrix=np.array([]),
            gamma_matrix=np.array([]),
            theta_matrix=np.array([]),
            vega_matrix=np.array([])
        )
    
    def calculate_risk_metrics(self, risk_array: RiskArray) -> Dict[str, float]:
        """Calculate risk metrics from risk array."""
        try:
            if risk_array.pnl_matrix.size == 0:
                return {}
            
            # Calculate various risk metrics
            max_profit = np.max(risk_array.pnl_matrix)
            max_loss = np.min(risk_array.pnl_matrix)
            profit_probability = np.sum(risk_array.pnl_matrix > 0) / risk_array.pnl_matrix.size
            
            # Calculate VaR (Value at Risk)
            pnl_flat = risk_array.pnl_matrix.flatten()
            var_95 = np.percentile(pnl_flat, 5)  # 5th percentile
            var_99 = np.percentile(pnl_flat, 1)  # 1st percentile
            
            # Calculate expected value
            expected_value = np.mean(pnl_flat)
            
            # Calculate standard deviation
            std_deviation = np.std(pnl_flat)
            
            return {
                'max_profit': max_profit,
                'max_loss': max_loss,
                'profit_probability': profit_probability,
                'var_95': var_95,
                'var_99': var_99,
                'expected_value': expected_value,
                'std_deviation': std_deviation,
                'sharpe_ratio': expected_value / std_deviation if std_deviation > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate risk metrics: {e}")
            return {}
    
    def export_risk_array(self, risk_array: RiskArray, 
                         format: str = 'csv') -> Optional[str]:
        """Export risk array to file."""
        if risk_array.pnl_matrix.size == 0:
            return None
        
        try:
            if format.lower() == 'csv':
                # Create DataFrame with all scenarios
                data = []
                for i, price in enumerate(risk_array.underlying_prices):
                    for j, iv in enumerate(risk_array.iv_changes):
                        for k, time in enumerate(risk_array.time_decays):
                            data.append({
                                'underlying_price': price,
                                'iv_change': iv,
                                'time_decay': time,
                                'pnl': risk_array.pnl_matrix[i, j, k],
                                'delta': risk_array.delta_matrix[i, j, k],
                                'gamma': risk_array.gamma_matrix[i, j, k],
                                'theta': risk_array.theta_matrix[i, j, k],
                                'vega': risk_array.vega_matrix[i, j, k]
                            })
                
                df = pd.DataFrame(data)
                return df.to_csv(index=False)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to export risk array: {e}")
            return None
