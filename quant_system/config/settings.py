"""
Global configuration management for the quantitative trading system.
Handles environment variables, API keys, and system parameters.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    """Global application settings"""
    
    # ==================== Basic Info ====================
    APP_NAME: str = "AI-Driven Quantitative Trading System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # ==================== Paths ====================
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    # ==================== Database ====================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://quant_user:quant_password_secure@localhost:5432/quant_trading"
    )
    DATABASE_ECHO: bool = DEBUG
    
    # ==================== Redis / Cache ====================
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TTL: int = 3600  # seconds
    
    # ==================== Kafka / Streaming ====================
    KAFKA_BROKER: str = os.getenv("KAFKA_BROKER", "localhost:9092")
    KAFKA_TOPICS: dict = {
        "market_prices": "market-prices",
        "order_book": "order-book",
        "news": "news-events",
        "signals": "trading-signals",
        "executions": "trade-executions",
    }
    
    # ==================== API Keys (Secure) ====================
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    ALPHA_VANTAGE_KEY: str = os.getenv("ALPHA_VANTAGE_KEY", "")
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"
    
    # ==================== Trading Parameters ====================
    INITIAL_CAPITAL: float = float(os.getenv("INITIAL_CAPITAL", 100000))
    
    # Risk limits
    MAX_LEVERAGE: float = 2.0
    MAX_DRAWDOWN: float = 0.15  # 15% max drawdown
    MAX_POSITION_SIZE: float = 0.1  # 10% per position
    MIN_POSITION_SIZE: float = 0.01  # 1% min position
    
    # CVaR parameters
    CVAR_CONFIDENCE_LEVEL: float = 0.95  # 95% confidence
    VAR_LOOKBACK_DAYS: int = 252  # 1 year of trading days
    
    # ==================== Data Fetching ====================
    DATA_SOURCE: str = os.getenv("DATA_SOURCE", "yfinance")  # yfinance, alpha_vantage
    FETCH_BATCH_SIZE: int = 100  # symbols per request
    CACHE_DATA: bool = True
    
    # Supported symbols/markets
    SUPPORTED_SYMBOLS: list = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "META", "NVDA", "JPM", "V", "JNJ",
        # Add more as needed
    ]
    
    # ==================== Backtesting ====================
    BACKTEST_COMMISSION: float = 0.001  # 0.1% per trade
    BACKTEST_SLIPPAGE: float = 0.0005   # 0.05% slippage
    BACKTEST_CASH_BAR: float = 0.05  # Keep 5% cash buffer
    
    # ==================== Strategy ====================
    REBALANCE_FREQUENCY: str = "daily"  # daily, weekly, monthly
    POSITION_HOLDING_PERIOD: int = 5  # days
    
    # Factor model weights
    FACTOR_WEIGHTS: dict = {
        "momentum": 0.30,
        "value": 0.25,
        "volatility": 0.20,
        "sentiment": 0.15,
        "technicals": 0.10,
    }
    
    # ==================== Technical Analysis ====================
    TA_INDICATORS: dict = {
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        
        "bb_period": 20,
        "bb_std": 2,
        
        "sma_fast": 20,
        "sma_slow": 50,
    }
    
    # ==================== AI/NLP ====================
    SENTIMENT_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CONTEXT_WINDOW: int = 5  # days of news to consider
    
    # ==================== Execution ====================
    EXECUTION_MODE: str = os.getenv("EXECUTION_MODE", "paper")  # paper or live
    ORDER_TYPE: str = "limit"  # limit or market
    ORDER_TIMEOUT: int = 300  # seconds
    
    # Broker settings
    ALPACA_API_KEY: Optional[str] = os.getenv("ALPACA_API_KEY")
    ALPACA_SECRET_KEY: Optional[str] = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"  # paper trading
    
    IB_ACCOUNT: Optional[str] = os.getenv("IB_ACCOUNT")
    IB_PORT: int = 7497
    
    # ==================== Logging ====================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ==================== Server ====================
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", 8000))
    API_RELOAD: bool = DEBUG
    
    # ==================== Frontend ====================
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # ==================== Monitoring ====================
    ENABLE_PROMETHEUS: bool = True
    PROMETHEUS_PORT: int = 8001
    
    @classmethod
    def validate(cls) -> None:
        """Validate critical configuration"""
        if not cls.OPENAI_API_KEY and cls.DEBUG:
            print("⚠️  WARNING: OPENAI_API_KEY not set. AI features will be limited.")
        
        # Ensure data directory exists
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Configuration loaded: {cls.APP_NAME} v{cls.APP_VERSION}")
        print(f"   Database: {cls.DATABASE_URL.split('/')[-1]}")
        print(f"   Mode: {'DEBUG' if cls.DEBUG else 'PRODUCTION'}")
        print(f"   Execution: {cls.EXECUTION_MODE.upper()}")

# Create global settings instance
settings = Settings()
