"""
Backtesting Engine for strategy validation.
Includes:
- Position management
- Commission & slippage
- Performance metrics calculation
- Walk-forward analysis support
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade"""
    entry_date: datetime
    exit_date: Optional[datetime] = None
    symbol: str = ""
    quantity: float = 0.0
    entry_price: float = 0.0
    exit_price: float = 0.0
    position_type: str = "long"  # long or short
    pnl: float = 0.0
    pnl_pct: float = 0.0
    
    def close(self, exit_date: datetime, exit_price: float):
        """Close the trade"""
        self.exit_date = exit_date
        self.exit_price = exit_price
        
        if self.position_type == "long":
            self.pnl = (exit_price - self.entry_price) * self.quantity
        else:  # short
            self.pnl = (self.entry_price - exit_price) * self.quantity
        
        self.pnl_pct = (self.pnl / (self.entry_price * self.quantity)) * 100
    
    def is_open(self) -> bool:
        """Check if trade is still open"""
        return self.exit_date is None


@dataclass
class PortfolioState:
    """Snapshot of portfolio state at a point in time"""
    timestamp: datetime
    cash: float = 0.0
    positions: Dict[str, float] = field(default_factory=dict)  # {symbol: quantity}
    position_prices: Dict[str, float] = field(default_factory=dict)  # {symbol: price}
    total_value: float = 0.0
    portfolio_return: float = 0.0
    portfolio_return_pct: float = 0.0


class BacktestEngine:
    """
    Main backtesting engine for strategy validation.
    
    Key features:
    - Position management (entry/exit)
    - Commission and slippage simulation
    - Drawdown tracking
    - Performance metrics (Sharpe, Sortino, etc.)
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,  # 0.1% per trade
        slippage: float = 0.0005,   # 0.05%
        cash_reserve: float = 0.05   # Keep 5% cash
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.cash_reserve = cash_reserve
        
        # Portfolio tracking
        self.cash = initial_capital
        self.positions: Dict[str, Dict] = {}  # {symbol: {quantity, entry_price}}
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.portfolio_history: List[PortfolioState] = []
        
        # Performance tracking
        self.daily_returns: List[float] = []
        self.dates: List[datetime] = []
        
        logger.info(f"BacktestEngine initialized with ${initial_capital:,.2f} capital")
    
    def calculate_portfolio_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value at current prices"""
        position_value = sum(
            self.positions[symbol]["quantity"] * prices.get(symbol, 0)
            for symbol in self.positions
            if self.positions[symbol]["quantity"] != 0
        )
        return self.cash + position_value
    
    def calculate_available_cash(self, current_prices: Dict[str, float]) -> float:
        """Calculate available cash for new positions"""
        position_value = sum(
            self.positions[symbol]["quantity"] * current_prices.get(symbol, 0)
            for symbol in self.positions
            if self.positions[symbol]["quantity"] != 0
        )
        portfolio_value = self.cash + position_value
        return portfolio_value * (1 - self.cash_reserve) - position_value
    
    def enter_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        position_type: str = "long",
        timestamp: datetime = None
    ) -> bool:
        """
        Enter a position (long or short).
        
        Returns:
            True if successful, False if insufficient cash
        """
        cost = abs(quantity) * price * (1 + self.commission) + (abs(quantity) * price * self.slippage)
        
        if self.cash < cost:
            logger.warning(
                f"Insufficient cash to enter {symbol}: need ${cost:.2f}, have ${self.cash:.2f}"
            )
            return False
        
        # Create or update position
        if symbol not in self.positions:
            self.positions[symbol] = {"quantity": 0, "entry_price": 0}
        
        # Update position
        self.positions[symbol]["quantity"] += quantity
        self.positions[symbol]["entry_price"] = price
        self.positions[symbol]["entry_date"] = timestamp or datetime.now()
        
        # Update cash
        self.cash -= cost
        
        # Record trade
        trade = Trade(
            entry_date=timestamp or datetime.now(),
            symbol=symbol,
            quantity=abs(quantity),
            entry_price=price,
            position_type=position_type
        )
        self.trades.append(trade)
        
        logger.debug(f"Entered {quantity} shares of {symbol} at ${price:.2f}")
        return True
    
    def exit_position(
        self,
        symbol: str,
        price: float,
        timestamp: datetime = None
    ) -> bool:
        """
        Exit a position completely.
        
        Returns:
            True if successful, False if no position
        """
        if symbol not in self.positions or self.positions[symbol]["quantity"] == 0:
            logger.warning(f"No position in {symbol} to exit")
            return False
        
        quantity = self.positions[symbol]["quantity"]
        proceeds = quantity * price * (1 - self.commission) - (quantity * price * self.slippage)
        
        # Update cash
        self.cash += proceeds
        
        # Close position
        self.positions[symbol]["quantity"] = 0
        
        # Record in trade history
        if self.trades:
            for trade in reversed(self.trades):
                if trade.symbol == symbol and trade.is_open():
                    trade.close(timestamp or datetime.now(), price)
                    break
        
        logger.debug(f"Exited {quantity} shares of {symbol} at ${price:.2f}")
        return True
    
    def update_position(self, symbol: str, quantity: float, price: float, timestamp: datetime = None):
        """Update position (rebalance)"""
        if symbol not in self.positions:
            self.positions[symbol] = {"quantity": 0, "entry_price": 0}
        
        current_qty = self.positions[symbol]["quantity"]
        qty_diff = quantity - current_qty
        
        if qty_diff > 0:
            self.enter_position(symbol, qty_diff, price, timestamp=timestamp)
        elif qty_diff < 0:
            self.exit_position(symbol, price, timestamp=timestamp)
    
    def run_backtest(
        self,
        data: pd.DataFrame,
        signals: pd.Series
    ) -> Dict:
        """
        Run backtest on historical data with trading signals.
        
        Args:
            data: DataFrame with OHLCV (index must be datetime)
            signals: Series with -1 (sell), 0 (hold), 1 (buy) signals
        
        Returns:
            Dictionary with performance metrics
        """
        logger.info(f"Running backtest on {len(data)} bars")
        
        self.equity_curve = [self.initial_capital]
        self.daily_returns = []
        
        prev_value = self.initial_capital
        
        for i, (date, row) in enumerate(data.iterrows()):
            signal = signals.iloc[i] if i < len(signals) else 0
            price = row['close']
            
            # Process signal
            if signal == 1:  # Buy signal
                # Calculate position size (Kelly criterion or fixed %)
                position_size = self.calculate_position_size(price)
                if position_size > 0:
                    self.enter_position("main", position_size, price, timestamp=date)
            
            elif signal == -1:  # Sell signal
                self.exit_position("main", price, timestamp=date)
            
            # Update portfolio value
            current_prices = {"main": price}
            portfolio_value = self.calculate_portfolio_value(current_prices)
            
            self.equity_curve.append(portfolio_value)
            self.portfolio_history.append(
                PortfolioState(
                    timestamp=date,
                    cash=self.cash,
                    total_value=portfolio_value,
                    portfolio_return=portfolio_value - self.initial_capital,
                    portfolio_return_pct=((portfolio_value / self.initial_capital) - 1) * 100
                )
            )
            
            # Calculate daily return
            daily_return = (portfolio_value - prev_value) / prev_value if prev_value > 0 else 0
            self.daily_returns.append(daily_return)
            
            prev_value = portfolio_value
            self.dates.append(date)
        
        logger.info(f"Backtest complete. Final portfolio value: ${self.equity_curve[-1]:,.2f}")
        
        return self.calculate_metrics()
    
    def calculate_position_size(self, current_price: float) -> float:
        """
        Calculate position size using Kelly criterion or fixed % allocation.
        
        Currently uses fixed allocation: 10% of portfolio per trade
        """
        portfolio_value = self.calculate_portfolio_value({"main": current_price})
        available = self.calculate_available_cash({"main": current_price})
        
        # Use 20% of available cash for each position
        allocation = portfolio_value * 0.20
        
        if allocation <= 0 or current_price <= 0:
            return 0.0
        
        return allocation / current_price
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if len(self.equity_curve) < 2:
            return {}
        
        equity = np.array(self.equity_curve)
        returns = np.array(self.daily_returns)
        
        # Basic metrics
        total_return = (equity[-1] - equity[0]) / equity[0]
        total_return_pct = total_return * 100
        
        # Risk metrics
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        sortino_ratio = self._calculate_sortino_ratio(returns)
        max_drawdown = self._calculate_max_drawdown(equity)
        
        # Win rate
        closed_trades = [t for t in self.trades if t.exit_price > 0]
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in closed_trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in closed_trades if t.pnl < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        metrics = {
            "total_return_pct": total_return_pct,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown_pct": max_drawdown * 100,
            "win_rate": win_rate * 100,
            "profit_factor": profit_factor,
            "num_trades": len(closed_trades),
            "avg_trade_return": np.mean([t.pnl_pct for t in closed_trades]) if closed_trades else 0,
            "final_value": equity[-1],
        }
        
        return metrics
    
    @staticmethod
    def _calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio (annualized)"""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)
        if np.std(excess_returns) == 0:
            return 0.0
        
        return np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns)
    
    @staticmethod
    def _calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside risk focus)"""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)
        downside = returns[returns < 0]
        
        if len(downside) == 0 or np.std(downside) == 0:
            return 0.0
        
        return np.sqrt(252) * np.mean(excess_returns) / np.std(downside)
    
    @staticmethod
    def _calculate_max_drawdown(equity: np.ndarray) -> float:
        """Calculate maximum drawdown as percentage"""
        if len(equity) == 0:
            return 0.0
        
        peak = equity[0]
        max_dd = 0.0
        
        for value in equity:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """Return backtest results as DataFrame"""
        return pd.DataFrame({
            "date": self.dates,
            "equity": self.equity_curve[1:],  # Skip initial capital
            "daily_return": self.daily_returns
        })
    
    def plot_results(self, save_path: Optional[str] = None):
        """Plot equity curve and drawdown"""
        try:
            import matplotlib.pyplot as plt
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
            
            # Equity curve
            ax1.plot(self.dates, self.equity_curve[1:], linewidth=2, label="Portfolio Value")
            ax1.set_title("Equity Curve")
            ax1.set_ylabel("Portfolio Value ($)")
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Drawdown
            equity = np.array(self.equity_curve)
            running_max = np.maximum.accumulate(equity)
            drawdown = (equity - running_max) / running_max
            
            ax2.fill_between(range(len(drawdown)), drawdown, alpha=0.3, label="Drawdown")
            ax2.set_title("Drawdown")
            ax2.set_ylabel("Drawdown %")
            ax2.set_xlabel("Date")
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches="tight")
                logger.info(f"Results plot saved to {save_path}")
            else:
                plt.show()
        
        except ImportError:
            logger.warning("matplotlib not installed. Cannot plot results.")
