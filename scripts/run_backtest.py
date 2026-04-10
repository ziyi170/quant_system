#!/usr/bin/env python
"""
Complete working backtest example.

This script demonstrates the full workflow:
1. Fetch historical data
2. Calculate technical indicators
3. Generate trading signals
4. Run backtest
5. Display results

Usage:
    python scripts/run_backtest.py --symbol AAPL --start 2023-01-01 --end 2024-01-01
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import argparse

import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.fetchers import YahooFinanceFetcher
from src.strategy.technical_indicators import RSI, MACD, BollingerBands, SimpleMovingAverage, CompositeIndicator
from src.backtesting.backtest_engine import BacktestEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_momentum_strategy(df: pd.DataFrame) -> pd.Series:
    """
    Momentum strategy: Buy on RSI oversold + MACD bullish crossover
    """
    logger.info("Generating momentum signals...")
    
    # Initialize indicators
    rsi = RSI(period=14, overbought=70, oversold=30)
    macd = MACD()
    
    # Get signals
    rsi_signal = rsi.get_signal(df.copy())
    macd_signal = macd.get_signal(df.copy())
    
    # Combine: Buy if both indicators align
    combined_signal = pd.Series(0, index=df.index)
    
    # Buy: RSI oversold AND MACD bullish
    buy_signal = (rsi_signal == 1) & (macd_signal >= 0)
    combined_signal[buy_signal] = 1
    
    # Sell: RSI overbought OR MACD bearish
    sell_signal = (rsi_signal == -1) | (macd_signal < 0)
    combined_signal[sell_signal] = -1
    
    return combined_signal


def run_mean_reversion_strategy(df: pd.DataFrame) -> pd.Series:
    """
    Mean reversion strategy: Buy when price touches lower Bollinger Band
    """
    logger.info("Generating mean reversion signals...")
    
    bb = BollingerBands(period=20, num_std=2.0)
    return bb.get_signal(df.copy())


def run_trend_following_strategy(df: pd.DataFrame) -> pd.Series:
    """
    Trend following: Buy when price > 50-day SMA
    """
    logger.info("Generating trend following signals...")
    
    sma_fast = SimpleMovingAverage(period=20)
    sma_slow = SimpleMovingAverage(period=50)
    
    df = sma_fast.calculate(df.copy())
    df = sma_slow.calculate(df.copy())
    
    signal = pd.Series(0, index=df.index)
    
    # Buy: SMA20 > SMA50 (uptrend)
    signal[df['sma_20'] > df['sma_50']] = 1
    
    # Sell: SMA20 < SMA50 (downtrend)
    signal[df['sma_20'] < df['sma_50']] = -1
    
    return signal


def print_metrics(metrics: dict, strategy_name: str):
    """Pretty print backtest metrics"""
    print(f"\n{'='*60}")
    print(f"📊 {strategy_name} - Backtest Results")
    print(f"{'='*60}\n")
    
    print(f"💰 Returns:")
    print(f"   Total Return:        {metrics.get('total_return_pct', 0):.2f}%")
    
    print(f"\n📈 Risk-Adjusted Returns:")
    print(f"   Sharpe Ratio:        {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"   Sortino Ratio:       {metrics.get('sortino_ratio', 0):.2f}")
    print(f"   Max Drawdown:        {metrics.get('max_drawdown_pct', 0):.2f}%")
    
    print(f"\n🎯 Trade Statistics:")
    print(f"   Total Trades:        {metrics.get('num_trades', 0):.0f}")
    print(f"   Win Rate:            {metrics.get('win_rate', 0):.2f}%")
    print(f"   Profit Factor:       {metrics.get('profit_factor', 0):.2f}")
    print(f"   Avg Trade Return:    {metrics.get('avg_trade_return', 0):.2f}%")
    
    print(f"\n💵 Final Portfolio Value: ${metrics.get('final_value', 0):,.2f}")
    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run backtesting on a trading strategy"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="AAPL",
        help="Stock symbol (default: AAPL)"
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date (YYYY-MM-DD), default: 1 year ago"
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD), default: today"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["momentum", "mean_reversion", "trend_following", "all"],
        default="momentum",
        help="Strategy to run (default: momentum)"
    )
    parser.add_argument(
        "--initial-capital",
        type=float,
        default=100000,
        help="Initial capital (default: 100000)"
    )
    
    args = parser.parse_args()
    
    # Set date range
    end_date = args.end or datetime.now().strftime("%Y-%m-%d")
    start_date = args.start or (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    logger.info(f"\n🚀 Starting backtest for {args.symbol}")
    logger.info(f"   Period: {start_date} to {end_date}")
    logger.info(f"   Initial Capital: ${args.initial_capital:,.2f}\n")
    
    # ==================== Step 1: Fetch Data ====================
    logger.info(f"📥 Fetching data for {args.symbol}...")
    fetcher = YahooFinanceFetcher()
    
    try:
        df = fetcher.fetch(args.symbol, start_date, end_date)
        logger.info(f"✅ Fetched {len(df)} bars of data\n")
    except Exception as e:
        logger.error(f"❌ Failed to fetch data: {e}")
        return 1
    
    # ==================== Step 2: Run Strategies ====================
    strategies = {
        "Momentum": run_momentum_strategy,
        "Mean Reversion": run_mean_reversion_strategy,
        "Trend Following": run_trend_following_strategy,
    }
    
    strategies_to_run = strategies if args.strategy == "all" else {args.strategy.title(): strategies[args.strategy.title()]}
    
    results = {}
    
    for strategy_name, strategy_func in strategies_to_run.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Running {strategy_name} Strategy")
        logger.info(f"{'='*60}\n")
        
        # Generate signals
        signals = strategy_func(df.copy())
        
        # Run backtest
        engine = BacktestEngine(
            initial_capital=args.initial_capital,
            commission=0.001,
            slippage=0.0005
        )
        
        metrics = engine.run_backtest(df, signals)
        results[strategy_name] = {
            "metrics": metrics,
            "engine": engine,
            "signals": signals
        }
        
        # Print results
        print_metrics(metrics, strategy_name)
    
    # ==================== Step 3: Compare Strategies ====================
    if len(results) > 1:
        print(f"\n{'='*60}")
        print("📊 Strategy Comparison")
        print(f"{'='*60}\n")
        
        comparison_df = pd.DataFrame({
            name: result["metrics"] 
            for name, result in results.items()
        }).T
        
        print(comparison_df[["total_return_pct", "sharpe_ratio", "max_drawdown_pct", "win_rate"]].to_string())
        print()
    
    # ==================== Step 4: Export Results ====================
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    for strategy_name, result in results.items():
        # Save metrics
        metrics_df = pd.DataFrame([result["metrics"]])
        metrics_path = output_dir / f"metrics_{strategy_name.lower().replace(' ', '_')}.csv"
        metrics_df.to_csv(metrics_path, index=False)
        logger.info(f"Metrics saved to {metrics_path}")
        
        # Save equity curve
        results_df = result["engine"].get_results_dataframe()
        equity_path = output_dir / f"equity_{strategy_name.lower().replace(' ', '_')}.csv"
        results_df.to_csv(equity_path, index=False)
        logger.info(f"Equity curve saved to {equity_path}")
    
    logger.info(f"\n✅ Backtest complete!\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
