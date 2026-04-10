# 🤖 AI-Driven Multi-Market Quantitative Trading System

> **A production-ready, end-to-end intelligent quantitative investment system combining event-driven AI analysis, statistical factor models, portfolio optimization, and real-time execution.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📊 Project Overview

**One-line definition:**
> A system that **understands markets with AI**, **validates strategies with statistics**, and **executes trades with precision**.

### Key Features
- ✅ **Event-Driven Architecture**: Real-time market event streaming (Kafka/Redis)
- ✅ **AI Intelligence Layer**: NLP sentiment analysis, LLM-powered reasoning, structured event extraction
- ✅ **Statistical Rigor**: Factor models, portfolio optimization (mean-variance, risk parity)
- ✅ **Risk Management**: CVaR, stress testing, dynamic position sizing
- ✅ **Backtesting Engine**: Walk-forward analysis, out-of-sample validation
- ✅ **Execution System**: Paper trading, limit orders, partial fills, order book simulation
- ✅ **Dashboard**: Real-time portfolio visualization with AI explanations

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Data Layer                       │
│  Tick-level prices + Order book + News + Macro     │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│            Event Streaming Layer                    │
│     Kafka/Redis: Real-time event pipeline          │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│               AI Intelligence Layer                 │
│  NLP + LLM + Event Extraction + Agent Decision     │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│            Strategy Generation Layer                │
│  Factor Models + TA Indicators + Portfolio Opt     │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│           Risk Management Engine                    │
│   CVaR + Stress Tests + Position Sizing            │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│      Research & Evaluation Layer                    │
│   Walk-forward Backtest + Metrics + Validation     │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│            Execution Layer                          │
│  Paper Trading + Order Management + Broker API     │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│          Dashboard & Reporting                      │
│    React UI + TradingView Charts + PnL Monitor     │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
quant_trading_system/
│
├── README.md                          # This file
├── ARCHITECTURE.md                    # Detailed architecture doc
├── INTERVIEW_GUIDE.md                 # System design interview script
│
├── requirements.txt                   # Python dependencies
├── requirements-dev.txt               # Development dependencies
├── docker-compose.yml                 # Multi-service docker setup
├── .dockerignore
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── settings.py                    # Global configuration
│   ├── api_keys.py                    # API key management (use env vars)
│   └── logging.py                     # Logging configuration
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/                          # 📊 Data Layer
│   │   ├── __init__.py
│   │   ├── fetchers.py                # Data acquisition (yfinance, API)
│   │   ├── normalizer.py              # Data normalization pipeline
│   │   ├── database.py                # Local storage (SQLite/PostgreSQL)
│   │   └── validators.py              # Data quality checks
│   │
│   ├── streaming/                     # ⚡ Event Streaming Layer
│   │   ├── __init__.py
│   │   ├── event_producer.py          # Event generation
│   │   ├── event_consumer.py          # Event processing
│   │   ├── event_types.py             # Event schema definitions
│   │   └── queue_manager.py           # Kafka/Redis management
│   │
│   ├── ai/                            # 🤖 AI Intelligence Layer
│   │   ├── __init__.py
│   │   ├── nlp_sentiment.py           # NLP sentiment analysis
│   │   ├── event_extractor.py         # Structured event extraction
│   │   ├── llm_reasoning.py           # LLM-based decision making
│   │   ├── agent.py                   # Agent framework
│   │   └── embeddings.py              # Text embeddings
│   │
│   ├── strategy/                      # 📈 Strategy Generation Layer
│   │   ├── __init__.py
│   │   ├── technical_indicators.py    # TA indicators (RSI, MACD, etc)
│   │   ├── factor_model.py            # Multi-factor model
│   │   ├── portfolio_optimizer.py     # Mean-variance, risk parity
│   │   ├── signal_generator.py        # Buy/sell signal logic
│   │   └── base_strategy.py           # Abstract strategy class
│   │
│   ├── risk/                          # ⚠️ Risk Management Layer
│   │   ├── __init__.py
│   │   ├── cvar_calculator.py         # Conditional Value at Risk
│   │   ├── stress_test.py             # Stress testing scenarios
│   │   ├── position_sizer.py          # Dynamic position sizing
│   │   └── risk_monitor.py            # Real-time risk tracking
│   │
│   ├── backtesting/                   # 🧪 Research & Evaluation Layer
│   │   ├── __init__.py
│   │   ├── backtest_engine.py         # Core backtest logic
│   │   ├── walk_forward.py            # Walk-forward analysis
│   │   ├── metrics.py                 # Performance metrics
│   │   └── validator.py               # Out-of-sample validation
│   │
│   ├── execution/                     # 💰 Execution Layer
│   │   ├── __init__.py
│   │   ├── paper_trading.py           # Simulated trading
│   │   ├── order_manager.py           # Order lifecycle
│   │   ├── broker_api.py              # Broker integrations
│   │   └── trade_simulator.py         # Order book simulation
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                  # Logging utilities
│       ├── decorators.py              # Caching, timing decorators
│       └── helpers.py                 # General utilities
│
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_data_fetcher.py
│   │   ├── test_strategy.py
│   │   └── test_risk_engine.py
│   ├── integration/
│   │   └── test_end_to_end.py
│   └── fixtures.py                    # Test data fixtures
│
├── notebooks/
│   ├── 01_data_exploration.ipynb      # EDA
│   ├── 02_factor_analysis.ipynb       # Factor investigation
│   └── 03_strategy_backtest.ipynb     # Strategy development
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── PortfolioChart.jsx
│   │   │   ├── RiskPanel.jsx
│   │   │   └── AIExplainer.jsx
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── index.css
│   ├── package.json
│   └── .env.example
│
├── scripts/
│   ├── download_data.py               # Fetch historical data
│   ├── run_backtest.py                # Execute backtest
│   ├── deploy.sh                      # Deployment script
│   └── health_check.py                # System health check
│
├── docs/
│   ├── ARCHITECTURE.md                # Detailed architecture
│   ├── API.md                         # API documentation
│   ├── SETUP.md                       # Setup instructions
│   └── TROUBLESHOOTING.md             # Common issues
│
└── .github/
    └── workflows/
        ├── tests.yml                  # CI/CD pipeline
        └── deploy.yml                 # Auto-deployment
```

---

## 🛠️ Tech Stack

### Backend
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data** | yfinance, Alpha Vantage, PostgreSQL | Market data acquisition & storage |
| **Streaming** | Redis Streams / Kafka | Real-time event pipeline |
| **AI** | OpenAI GPT-4, HuggingFace, spaCy | NLP, LLM reasoning, embeddings |
| **Strategy** | Pandas, NumPy, scikit-learn | Data processing, factor models |
| **Risk** | SciPy, cvxpy | Statistical calculations, optimization |
| **Backtesting** | Backtrader, Zipline | Strategy validation |
| **API Server** | FastAPI | REST API for execution & monitoring |

### Frontend
- **React 18** with TypeScript
- **TradingView Lightweight Charts** for OHLCV visualization
- **Recharts** for performance metrics
- **Tailwind CSS** for styling
- **Vite** for bundling

### DevOps
- **Docker & Docker Compose** for containerization
- **GitHub Actions** for CI/CD
- **PostgreSQL** for data persistence
- **Redis** for caching & streaming

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.9+
Docker & Docker Compose
Node.js 16+ (for frontend)
```

### 1. Clone & Setup
```bash
git clone https://github.com/yourname/quant-trading-system.git
cd quant-trading-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run with Docker
```bash
docker-compose up -d
```

### 4. Download Data & Run Backtest
```bash
python scripts/download_data.py --symbol AAPL --start 2023-01-01
python scripts/run_backtest.py --strategy momentum --date-range 2023
```

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

## 📊 MVP Walkthrough

### Step 1: Fetch Data
```python
from src.data.fetchers import YahooFinanceFetcher

fetcher = YahooFinanceFetcher()
data = fetcher.fetch('AAPL', start='2023-01-01', end='2024-01-01')
```

### Step 2: Generate Signals
```python
from src.strategy.technical_indicators import RSI, MACD
from src.strategy.signal_generator import SignalGenerator

signals = SignalGenerator()
signals.add_indicator(RSI(period=14))
signals.add_indicator(MACD())
buy_sell = signals.generate('AAPL', data)
```

### Step 3: Backtest
```python
from src.backtesting.backtest_engine import BacktestEngine

engine = BacktestEngine(initial_capital=100000)
results = engine.run(data, signals)
print(results.metrics())
```

### Step 4: Visualize
Dashboard automatically available at `http://localhost:3000`

---

## 🎯 Core Concepts (100-Score Differentiators)

### 1. **Event-Driven Finance**
Markets are **event streams**, not time series.
```
PriceEvent → NewsEvent → VolumeSpikeEvent → OrderBookEvent
     ↓           ↓            ↓                 ↓
   AI learns sequence patterns → generates decisions
```

### 2. **AI ≠ Prediction**
AI doesn't predict prices; it **interprets market reactions**.
```
NewsEvent: "Apple beats earnings"
AI: {sentiment: positive, probability: 85%, expected_impact: 2-3%}
```

### 3. **Statistics > Deep Learning**
AI explains, statistics earn returns.
```
AI: "Bullish sentiment on earnings"
Statistics: "But momentum factor is oversold" 
Risk: "But correlation is high; reduce position to 2%"
```

### 4. **Portfolio > Single Stock**
Single-stock prediction is overfit. Correct approach: optimize the **whole portfolio**.
```
Position = f(volatility, correlation, sentiment, technicals)
→ Dynamic rebalancing
```

### 5. **Risk First**
You can make money with a mediocre strategy, but you can't survive bad risk management.
```
CVaR: 95% confidence worst loss = 5% account
Stress test: If market crashes 20%, account loss = 8% (acceptable)
```

---

## 📈 Performance Metrics

The system tracks:
- **Sharpe Ratio** (risk-adjusted returns)
- **Sortino Ratio** (downside risk focus)
- **Max Drawdown** (worst peak-to-trough)
- **Win Rate** (% winning trades)
- **Profit Factor** (gross profit / gross loss)
- **Calmar Ratio** (return / max drawdown)

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=src tests/
```

---

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Deep dive into each layer
- **[INTERVIEW_GUIDE.md](./INTERVIEW_GUIDE.md)** - System design presentation
- **[API.md](./docs/API.md)** - API endpoints reference
- **[SETUP.md](./docs/SETUP.md)** - Installation & configuration guide

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⭐ Citation

If you use this system for research or education, please cite:

```bibtex
@software{quant_trading_system_2024,
  author = {Your Name},
  title = {AI-Driven Quantitative Trading System},
  year = {2024},
  url = {https://github.com/yourname/quant-trading-system}
}
```

---

## 📞 Support

- 📧 Email: your.email@example.com
- 💬 Discussions: GitHub Discussions
- 🐛 Issues: GitHub Issues
- 📖 Wiki: Check our Wiki for FAQs

---

## 🙏 Acknowledgments

- Inspired by real-world quant hedge fund systems
- Built with production-grade best practices
- Suitable for interviews, education, and research

---

**Made with ❤️ for quants, AI engineers, and fintech enthusiasts**
