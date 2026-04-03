"""
Risk Management Engine - CVaR, stress testing, position sizing, drawdown control.
This is the most critical module for survival in quantitative trading.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Risk metrics snapshot"""
    value_at_risk: float  # VaR (worst X% loss)
    conditional_var: float  # CVaR (average of worst losses)
    max_drawdown: float  # Peak-to-trough decline
    current_leverage: float  # Current leverage ratio
    concentration_risk: float  # Largest position size
    correlation_risk: float  # Average correlation of positions
    stress_test_loss: float  # Loss in worst-case scenario


class ValueAtRisk:
    """
    Value at Risk (VaR) calculation.
    
    VaR: The maximum loss with X% confidence over a time horizon.
    Example: 95% VaR = 5% means 5% of the time we lose more than this amount.
    """
    
    def __init__(self, confidence_level: float = 0.95, lookback_days: int = 252):
        """
        Args:
            confidence_level: Confidence level (0.95 = 95%)
            lookback_days: Historical lookback period (1 year = 252 trading days)
        """
        self.confidence_level = confidence_level
        self.lookback_days = lookback_days
    
    def calculate_var(self, returns: np.ndarray) -> float:
        """
        Calculate VaR using historical method.
        
        Args:
            returns: Array of historical returns (e.g., daily returns)
        
        Returns:
            VaR as percentage (e.g., 0.05 = 5% loss)
        """
        if len(returns) == 0:
            return 0.0
        
        # Percentile method: find the return at the confidence level
        alpha = 1 - self.confidence_level
        var = np.percentile(returns, alpha * 100)
        
        return max(var, -1.0)  # Cap at -100%
    
    def calculate_cvar(self, returns: np.ndarray) -> float:
        """
        Calculate Conditional VaR (CVaR) - Expected Shortfall.
        
        CVaR is more conservative than VaR:
        - VaR: The worst single day
        - CVaR: The average of the worst days (more realistic)
        
        Args:
            returns: Array of historical returns
        
        Returns:
            CVaR as percentage
        """
        if len(returns) == 0:
            return 0.0
        
        var = self.calculate_var(returns)
        
        # Average of returns worse than VaR
        worst_returns = returns[returns <= var]
        cvar = np.mean(worst_returns) if len(worst_returns) > 0 else var
        
        return max(cvar, -1.0)


class PositionSizer:
    """
    Dynamic position sizing based on:
    - Portfolio volatility
    - Position correlation
    - Risk budget
    - Sentiment signals
    """
    
    def __init__(
        self,
        max_position_size: float = 0.10,  # 10% max per position
        max_leverage: float = 2.0,
        risk_budget: float = 0.02  # 2% per trade
    ):
        self.max_position_size = max_position_size
        self.max_leverage = max_leverage
        self.risk_budget = risk_budget
    
    def calculate_kelly_position_size(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Kelly Criterion for optimal position sizing.
        
        Kelly % = (Win Rate * Avg Win - (1 - Win Rate) * Avg Loss) / Avg Win
        
        Safety: Use 0.25 * Kelly (quarter Kelly) in practice
        """
        if avg_win <= 0 or avg_loss >= 0:
            return 0.0
        
        kelly_pct = (
            (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        )
        
        # Use quarter Kelly for safety
        kelly_pct = kelly_pct * 0.25
        
        # Clip to max position size
        return np.clip(kelly_pct, 0, self.max_position_size)
    
    def calculate_volatility_adjusted_size(
        self,
        portfolio_volatility: float,
        position_volatility: float,
        target_volatility: float = 0.15  # 15% annual vol target
    ) -> float:
        """
        Adjust position size based on volatility.
        
        Higher volatility = smaller position
        """
        if portfolio_volatility <= 0:
            return self.max_position_size * 0.5
        
        # Scale position inversely with volatility
        vol_ratio = target_volatility / position_volatility
        adjusted_size = self.max_position_size * vol_ratio
        
        return np.clip(adjusted_size, 0.01, self.max_position_size)
    
    def calculate_risk_adjusted_size(
        self,
        stop_loss_pct: float,  # e.g., 0.02 for 2% stop loss
        portfolio_value: float
    ) -> float:
        """
        Size position based on risk budget.
        
        Position Size = Risk Budget / Stop Loss %
        Example: $100k portfolio, 2% risk budget, 2% stop loss
                = $2,000 / (Portfolio * 0.02) = $2,000 / $2,000 = 1 position
        """
        if portfolio_value <= 0 or stop_loss_pct <= 0:
            return 0.0
        
        max_loss_amount = portfolio_value * self.risk_budget
        position_value = max_loss_amount / stop_loss_pct
        position_size = position_value / portfolio_value
        
        return np.clip(position_size, 0, self.max_position_size)


class StressTest:
    """
    Scenario-based stress testing.
    
    Tests portfolio resilience to extreme market events.
    """
    
    # Historical scenarios
    SCENARIOS = {
        "2008_crash": {
            "market_move": -0.40,  # -40%
            "volatility_shock": 2.0,  # Vol doubles
            "correlation_shock": 0.8,  # Correlations increase to 0.8
            "description": "2008 Financial Crisis"
        },
        "volcker_rates": {
            "market_move": -0.25,
            "volatility_shock": 1.5,
            "correlation_shock": 0.7,
            "description": "Volcker Rate Hike (1979-82)"
        },
        "flash_crash": {
            "market_move": -0.10,
            "volatility_shock": 3.0,
            "duration": "1 day",
            "description": "Flash Crash (May 2010)"
        },
        "covid": {
            "market_move": -0.34,
            "volatility_shock": 2.5,
            "liquidity_shock": 0.5,
            "description": "COVID-19 Crash (Mar 2020)"
        }
    }
    
    def __init__(self):
        pass
    
    def run_scenario(
        self,
        portfolio_beta: float,
        portfolio_value: float,
        scenario_name: str = "2008_crash"
    ) -> Dict:
        """
        Run stress test scenario on portfolio.
        
        Args:
            portfolio_beta: Portfolio beta to market (e.g., 1.0)
            portfolio_value: Current portfolio value
            scenario_name: Name of scenario
        
        Returns:
            Loss estimate under scenario
        """
        if scenario_name not in self.SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.SCENARIOS[scenario_name]
        
        # Calculate loss: Market Move * Beta
        market_move = scenario["market_move"]
        portfolio_move = market_move * portfolio_beta
        portfolio_loss = portfolio_value * portfolio_move
        
        return {
            "scenario": scenario_name,
            "description": scenario["description"],
            "market_move": market_move * 100,
            "portfolio_move": portfolio_move * 100,
            "loss_amount": portfolio_loss,
            "loss_pct": portfolio_move * 100,
            "surviving": portfolio_loss > -portfolio_value  # Portfolio survives?
        }
    
    def run_all_scenarios(self, portfolio_beta: float, portfolio_value: float) -> List[Dict]:
        """Run all stress test scenarios"""
        results = []
        for scenario_name in self.SCENARIOS.keys():
            result = self.run_scenario(portfolio_beta, portfolio_value, scenario_name)
            results.append(result)
        return results


class DrawdownMonitor:
    """
    Monitor and control maximum drawdown in real-time.
    """
    
    def __init__(self, max_drawdown_limit: float = 0.15):
        """
        Args:
            max_drawdown_limit: Maximum allowed drawdown (e.g., 0.15 = 15%)
        """
        self.max_drawdown_limit = max_drawdown_limit
        self.peak_value = None
        self.peak_date = None
        self.current_drawdown = 0.0
    
    def update(self, current_value: float, current_date) -> Dict:
        """
        Update drawdown monitoring.
        
        Returns:
            Dict with current drawdown status
        """
        # Update peak
        if self.peak_value is None or current_value > self.peak_value:
            self.peak_value = current_value
            self.peak_date = current_date
        
        # Calculate current drawdown
        if self.peak_value > 0:
            self.current_drawdown = (self.peak_value - current_value) / self.peak_value
        
        return {
            "peak_value": self.peak_value,
            "peak_date": self.peak_date,
            "current_value": current_value,
            "current_drawdown": self.current_drawdown,
            "drawdown_limit": self.max_drawdown_limit,
            "exceeded_limit": self.current_drawdown > self.max_drawdown_limit,
            "buffer_remaining": max(0, self.max_drawdown_limit - self.current_drawdown)
        }


class RiskManager:
    """
    Integrated risk management system.
    
    Monitors and controls:
    - VaR / CVaR
    - Position sizing
    - Stress testing
    - Drawdown limits
    - Concentration risk
    """
    
    def __init__(
        self,
        max_drawdown: float = 0.15,
        cvar_limit: float = 0.05,
        max_position_size: float = 0.10,
        max_leverage: float = 2.0
    ):
        self.max_drawdown = max_drawdown
        self.cvar_limit = cvar_limit
        
        self.var_calculator = ValueAtRisk(confidence_level=0.95)
        self.position_sizer = PositionSizer(max_position_size, max_leverage)
        self.stress_tester = StressTest()
        self.drawdown_monitor = DrawdownMonitor(max_drawdown)
    
    def check_position_risk(
        self,
        position_size: float,
        entry_price: float,
        stop_loss_price: float,
        portfolio_value: float
    ) -> Dict:
        """
        Check if a proposed position is within risk limits.
        
        Returns:
            Risk assessment dict
        """
        max_loss = (entry_price - stop_loss_price) * position_size
        max_loss_pct = max_loss / portfolio_value if portfolio_value > 0 else 0
        
        return {
            "position_size": position_size,
            "max_loss_amount": max_loss,
            "max_loss_pct": max_loss_pct,
            "within_risk_budget": max_loss_pct <= self.cvar_limit,
            "risk_utilization": max_loss_pct / self.cvar_limit if self.cvar_limit > 0 else 0
        }
    
    def generate_report(self, returns: np.ndarray, portfolio_value: float) -> Dict:
        """Generate comprehensive risk report"""
        var = self.var_calculator.calculate_var(returns)
        cvar = self.var_calculator.calculate_cvar(returns)
        
        return {
            "value_at_risk_pct": var * 100,
            "conditional_var_pct": cvar * 100,
            "cvar_limit": self.cvar_limit * 100,
            "cvar_breach": cvar < -self.cvar_limit,
            "volatility": np.std(returns) * 100,
            "sharpe_ratio": (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0,
            "recommended_position_size": self.position_sizer.max_position_size
        }
