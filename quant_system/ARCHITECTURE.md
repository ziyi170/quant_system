# 🏗️ System Architecture - Complete Deep Dive

## Overview

This document provides a detailed technical breakdown of every layer in the AI quantitative trading system.

```
Market Data Input
      ↓
[DATA LAYER] → Fetch, normalize, validate
      ↓
[STREAMING LAYER] → Event production & queuing
      ↓
[AI LAYER] → NLP, LLM, event extraction
      ↓
[STRATEGY LAYER] → Factor models, optimization
      ↓
[RISK LAYER] → Position sizing, limits, controls
      ↓
[EXECUTION LAYER] → Order placement, fills
      ↓
[EVALUATION LAYER] → Backtest, metrics, analysis
      ↓
Output → Dashboard, Reports, Alerts
```

---

## 1️⃣ DATA LAYER

### Purpose
Acquire, normalize, and store market data from multiple sources.

### Components

#### 1.1 Data Fetchers
**File:** `src/data/fetchers.py`

**Supported Sources:**
- **yfinance**: Free, real-time, 1min-1mo intervals
- **Alpha Vantage**: Requires API key, more reliable intraday
- **Custom APIs**: Extensible framework for other sources

**OHLCV Data:**
```python
df = fetcher.fetch('AAPL', '2023-01-01', '2024-01-01')
# Returns: Open, High, Low, Close, Volume, Adj Close
```

**What it handles:**
- ✅ Multiple symbols in batch
- ✅ Rate limiting (Alpha Vantage: 5 req/min)
- ✅ Automatic retry on failure
- ✅ Corporate action adjustment (splits, dividends)
- ✅ Missing data handling
- ✅ Timezone normalization

#### 1.2 Data Normalization
Ensures consistency across data sources:

```python
# Normalize column names to lowercase
# Remove NaN rows
# Remove duplicates
# Ensure datetime index
# Verify data types (float64 for prices)
```

#### 1.3 Data Storage
```
Cold Storage: PostgreSQL
├── Historical OHLCV (1+ years)
├── Corporate actions
└── Reference data (symbols, sectors, etc.)

Hot Cache: Redis
├── Latest 100 bars per symbol
├── Real-time tick data
└── Aggregated indicators
```

**Schema Example:**
```sql
CREATE TABLE ohlcv (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    date DATE,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume BIGINT,
    adj_close FLOAT,
    UNIQUE(symbol, date)
);
CREATE INDEX idx_symbol_date ON ohlcv(symbol, date);
```

---

## 2️⃣ EVENT STREAMING LAYER

### Purpose
Convert raw market data into an event stream for real-time processing.

### Event Types

**PriceEvent**
```python
{
    "type": "PRICE",
    "timestamp": "2024-01-15T10:30:00Z",
    "symbol": "AAPL",
    "price": 150.25,
    "volume": 1000000,
    "bid": 150.24,
    "ask": 150.26
}
```

**NewsEvent**
```python
{
    "type": "NEWS",
    "timestamp": "2024-01-15T09:00:00Z",
    "symbol": "AAPL",
    "headline": "Apple posts record earnings",
    "source": "Bloomberg",
    "url": "...",
    "sentiment": 0.85
}
```

**MacroEvent**
```python
{
    "type": "MACRO",
    "timestamp": "2024-01-15T14:00:00Z",
    "event": "FED_RATE_DECISION",
    "value": 5.25,
    "expected": 5.25,
    "impact": "NEUTRAL"
}
```

**OrderBookEvent**
```python
{
    "type": "ORDER_BOOK",
    "timestamp": "2024-01-15T10:30:00.123Z",
    "symbol": "AAPL",
    "bid_volume": 500000,
    "ask_volume": 600000,
    "bid_ask_ratio": 0.83
}
```

### Streaming Infrastructure

**Kafka Setup** (Production)
```
kafka-broker-1 (partition 0-2)
├── market-prices topic (1000 partitions, symbol-keyed)
├── order-book topic
├── news-events topic
└── signals topic

Consumer groups:
├── ai-processor (consumes news + prices)
├── strategy-engine (consumes signals)
└── risk-monitor (consumes all events)
```

**Advantages:**
- ✅ Event ordering per partition
- ✅ Replay capability (backtest historical events)
- ✅ Parallel processing (1 partition = 1 consumer)
- ✅ Guaranteed delivery
- ✅ Failure recovery

**Redis Streams Fallback** (Simpler)
```python
# Simpler but less robust
redis.xadd('prices', {'symbol': 'AAPL', 'price': 150.25})
redis.xread(streams={'prices': '0'})  # Read all
```

---

## 3️⃣ AI INTELLIGENCE LAYER

### Purpose
Extract meaning from market data and events.

### 3.1 NLP Sentiment Analysis
**File:** `src/ai/nlp_sentiment.py`

**Pipeline:**
```
Raw News Text
    ↓
[DistilBERT] → Sentiment Classification
    ↓
{label: POSITIVE, score: 0.92}
    ↓
[Financial Keywords] → Adjustment
    ↓
Final Sentiment: -1 to +1
```

**Example:**
```python
analyzer = SentimentAnalyzer()
result = analyzer.analyze("Apple beats earnings by 20%")
# Output: {label: "POSITIVE", score: 0.95, sentiment_value: 0.95}
```

**Cost Optimization:**
- Use DistilBERT (6x faster than BERT, 97% accuracy)
- Cache results (same news = same sentiment)
- Batch process multiple headlines

### 3.2 Structured Event Extraction (LLM)
**Concept:** Convert unstructured news into actionable signals

```
Input: "Fed raises rates 25bps amid inflation concerns"

LLM Prompt:
"Extract financial event from news. Return JSON with:
- event_type: (RATE_HIKE, EARNINGS, GUIDANCE, etc.)
- magnitude: number
- affected_sectors: list
- expected_market_impact: POSITIVE/NEGATIVE/MIXED
- confidence: 0-1"

Output:
{
  "event_type": "RATE_HIKE",
  "magnitude": 25,
  "affected_sectors": ["FIXED_INCOME", "GROWTH"],
  "expected_market_impact": "MIXED",
  "confidence": 0.92
}
```

**Cost Strategy:**
- Only use GPT-4 for complex events
- Use cheaper GPT-3.5 for routine analysis
- Cache at hourly granularity

### 3.3 Agent Decision System

```
Observe Market State
    ↓
AI: "Is this a setup? Evidence?"
    ↓
Interpret: Sentiment + Technicals + Macro
    ↓
Simulate: "If I trade, what's expected outcome?"
    ↓
Decide: Action (BUY / SELL / HOLD) + Confidence
    ↓
Act: Place order if confidence > 70%
    ↓
Learn: Track outcome, update beliefs
```

---

## 4️⃣ STRATEGY LAYER

### Purpose
Generate trading signals from analyzed data.

### 4.1 Technical Indicators
**File:** `src/strategy/technical_indicators.py`

**Standard Indicators:**
```python
RSI(14)              # Momentum oscillator
MACD(12,26,9)        # Trend following
BollingerBands(20)   # Volatility bands
SMA(20,50)           # Moving averages
EMA(12)              # Exponential average
ADX(14)              # Trend strength
Stochastic(14)       # Momentum indicator
```

**Signal Generation Example:**
```python
rsi = RSI()
signal = rsi.get_signal(df)
# Returns: pd.Series with 1 (buy), 0 (hold), -1 (sell)
```

### 4.2 Factor Model
**Concept:** Predict returns using multiple factors

```
Expected Return = α + β₁×Momentum + β₂×Value + β₃×Volatility + β₄×Sentiment + ε

Where:
α = alpha (outperformance)
β₁...β₄ = factor loadings (importance weights)
Momentum = price change over past 3 months
Value = low P/E ratio
Volatility = realized volatility
Sentiment = AI sentiment score
ε = residual (model error)
```

**Estimated Model for AAPL:**
```
Return = 0.5% + 0.3×Momentum + 0.2×Value + 0.15×Volatility + 0.1×Sentiment

Interpretation:
- 30% of signal comes from momentum (last 3 months)
- 20% from valuation metrics
- 15% from realized volatility
- 10% from news sentiment
```

### 4.3 Portfolio Optimization
**Problem:** How much to allocate to each position?

**Solution:** Convex Optimization
```python
# Maximize Sharpe Ratio
# maximize: (ret_ω - rf) / sqrt(ω'Σω)
# subject to: sum(ω) = 1, ω ∈ [0, 0.1], leverage ≤ 2

import cvxpy as cp

w = cp.Variable(n)  # n assets
ret = cp.sum(w @ returns)
risk = cp.sqrt(cp.quad_form(w, cov_matrix))

problem = cp.Problem(
    cp.Maximize(ret / risk),
    [
        cp.sum(w) == 1,
        w >= 0, w <= 0.1,  # 10% max per asset
        cp.sum(w) <= 2.0   # 2x max leverage
    ]
)

problem.solve()
optimal_weights = w.value
```

---

## 5️⃣ RISK MANAGEMENT ENGINE

### Purpose
Ensure portfolio survives extreme scenarios.

### 5.1 Value at Risk (VaR) & Conditional VaR
**File:** `src/risk/risk_manager.py`

```
VaR(95%) = 5%
Interpretation: "95% of the time, our daily loss is less than 5%"
              OR "5% of the time, our daily loss exceeds 5%"

CVaR(95%) = 6.2%
Interpretation: "Average of our 5% worst days is 6.2% loss"
```

**Calculation:**
```python
var_calculator = ValueAtRisk(confidence_level=0.95)

# Using historical method (empirical percentile)
returns = np.array([...])  # Daily returns
var = var_calculator.calculate_var(returns)
cvar = var_calculator.calculate_cvar(returns)

# Set position limits based on CVaR
max_position = portfolio_value * cvar_limit / cvar
```

### 5.2 Position Sizing
**Methods:**

**a) Kelly Criterion**
```
f* = (p×b - q) / b

where:
p = win probability
b = average win / average loss ratio
q = 1 - p

Example: 60% win rate, 2:1 profit/loss ratio
f* = (0.6×2 - 0.4) / 2 = 0.4 (40%)

Use 1/4 Kelly in practice: 10% position size
```

**b) Volatility-Adjusted**
```
Position Size = TargetVol / AssetVol × BaseSize

Example:
Target portfolio vol: 15% annual
AAPL vol: 30% annual
Base position: 10%
→ Size = (15% / 30%) × 10% = 5%

Higher volatility assets = smaller positions
```

**c) Risk-Budget Sizing**
```
Position = (Portfolio × RiskBudget) / StopLoss

Example:
$100k portfolio, 2% risk budget ($2k), 3% stop loss
→ Position = $2000 / 0.03 = $66,666 (66.7% of portfolio)
→ Check: $66,666 × 3% = $2,000 ✓

This ensures exact risk control
```

### 5.3 Stress Testing
**Scenarios:**

```python
# 2008 Financial Crisis
portfolio_loss = portfolio_beta × (-40%) × portfolio_value

# Volcker Rate Hike (1979-82)
portfolio_loss = portfolio_beta × (-25%) × portfolio_value

# Flash Crash (May 2010)
portfolio_loss = portfolio_beta × (-10%) × portfolio_value (1 day)

# COVID Crash (Mar 2020)
portfolio_loss = portfolio_beta × (-34%) × portfolio_value
```

**Risk Assessment:**
```python
stress_tester = StressTest()
for scenario in stress_tester.SCENARIOS:
    loss = stress_tester.run_scenario(
        portfolio_beta=1.2,
        portfolio_value=100000,
        scenario_name=scenario
    )
    print(f"{scenario}: Loss = ${loss['loss_amount']:,.0f}")
```

### 5.4 Drawdown Monitoring
```python
drawdown_monitor = DrawdownMonitor(max_drawdown_limit=0.15)

# Update after each trade
status = drawdown_monitor.update(current_value=98500, date='2024-01-15')
# {
#   'current_drawdown': 0.015,  # 1.5%
#   'exceeded_limit': False,
#   'buffer_remaining': 0.135   # Can go down 13.5% more
# }
```

---

## 6️⃣ BACKTESTING & EVALUATION LAYER

### Purpose
Validate strategies with rigorous testing to ensure robustness.

### 6.1 Backtest Engine
**File:** `src/backtesting/backtest_engine.py`

**Architecture:**
```
Historical Data (OHLCV)
    ↓
For each bar in history:
  1. Get signal (from strategy)
  2. Calculate position size
  3. Simulate execution (commission, slippage)
  4. Track portfolio value
  5. Record trade
    ↓
Calculate metrics (Sharpe, Sortino, Drawdown, etc.)
    ↓
Output: Performance report
```

**Key Features:**
- ✅ Commission modeling (0.1% realistic)
- ✅ Slippage modeling (0.05%)
- ✅ Partial fills
- ✅ Cash management (maintain 5% reserve)
- ✅ Multi-symbol support

**Example:**
```python
engine = BacktestEngine(initial_capital=100000)
metrics = engine.run_backtest(df, signals)
# Returns: {
#   'total_return_pct': 15.2,
#   'sharpe_ratio': 1.45,
#   'max_drawdown_pct': 12.3,
#   'win_rate': 62.5,
#   'profit_factor': 2.31
# }
```

### 6.2 Walk-Forward Analysis (Most Robust)
**Concept:** Avoid look-ahead bias through out-of-sample testing

```
[Training Period] → Optimize strategy
                         ↓
                  [Test Period] → Validate
                              ↓
                  [Next Training] → Reoptimize
                              ↓
                  [Next Test] → Validate again
```

**Example:** 
```
2020: Train on Jan-Nov, Test on Dec
2021: Train on Jan-Nov, Test on Dec
2022: Train on Jan-Nov, Test on Dec
→ Average Dec performance across years
```

**Why it works:**
- Each test is truly out-of-sample
- Parameter optimization adapts to market regimes
- Catches overfitting (no look-ahead)

### 6.3 Performance Metrics

| Metric | Formula | Interpretation |
|--------|---------|-----------------|
| **Sharpe Ratio** | (Return - Rf) / σ | Excess return per unit risk (>1.0 is good) |
| **Sortino Ratio** | (Return - Rf) / σ_down | Focuses on downside risk (>1.0 is good) |
| **Max Drawdown** | Peak-to-Trough / Peak | Worst decline (-15% is typical) |
| **Win Rate** | Winning trades / Total | % of profitable trades (>55% is good) |
| **Profit Factor** | Gross Profit / Gross Loss | 2.0 means 2:1 profit-to-loss ratio |
| **Calmar Ratio** | Return / Max Drawdown | Return per unit of risk |

---

## 7️⃣ EXECUTION LAYER

### Purpose
Execute trades in paper/live environments.

### 7.1 Paper Trading
```python
engine = PaperTradingEngine(initial_capital=100000)

# Simulate trade
order = engine.place_order(
    symbol='AAPL',
    quantity=100,
    type='LIMIT',
    limit_price=150.50,
    timestamp=datetime.now()
)
# Uses next bar's OHLC for fill simulation
```

### 7.2 Live Trading (via Broker APIs)

**Alpaca API:**
```python
from alpaca_trade_api import REST, StreamConn

api = REST()
order = api.submit_order(
    symbol='AAPL',
    qty=100,
    side='buy',
    type='limit',
    limit_price=150.50,
    time_in_force='day'
)
```

**Interactive Brokers:**
```python
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

class IBWrapper(EWrapper):
    def execDetails(self, reqId, contract, execution):
        print(f"Executed {execution.shares} @ {execution.price}")
```

### 7.3 Order Management
```python
order = {
    'id': 'ORD-001',
    'symbol': 'AAPL',
    'quantity': 100,
    'side': 'BUY',
    'type': 'LIMIT',
    'limit_price': 150.50,
    'status': 'PENDING',
    'created_at': datetime.now()
}

# Possible statuses:
# PENDING → FILLED, PARTIALLY_FILLED, CANCELLED, REJECTED
```

---

## 8️⃣ SYSTEM DESIGN PATTERNS

### 8.1 Separation of Concerns
```
Data Layer ← Only fetching & storage
    ↓
Streaming Layer ← Only event production
    ↓
AI Layer ← Only interpretation
    ↓
Strategy Layer ← Only signal generation
    ↓
Risk Layer ← Only risk control
    ↓
Execution Layer ← Only order placement
```

Each layer can be tested independently.

### 8.2 Error Handling & Fallbacks
```python
try:
    sentiment = llm_model.analyze(news)
except TimeoutError:
    sentiment = cache.get(news) or nlp_fallback(news)
```

### 8.3 Monitoring & Alerting
```
Portfolio Value
    ↓ Alert if daily loss > 2%
    ↓ Alert if position > 10%
    ↓ Alert if drawdown > 15%
    ↓
Send notifications → Email, Slack, PagerDuty
```

---

## 9️⃣ SCALABILITY CONSIDERATIONS

### Data Volume
```
Current: 50 symbols, daily bars
→ 50 × 252 × 5 columns = 63k rows

Scaled: 5000 symbols, minute bars
→ 5000 × 252 × 390 × 5 columns = 2.5B rows
→ Solution: Partitioned table, columnar storage (Parquet)
```

### Processing Latency
```
Current: 100ms end-to-end (data → decision)
Target: 10ms (for HFT)

Architecture:
- Move processing to C++/Rust for hot path
- Pre-compute factors
- Cache intermediate results
- Parallel processing on GPU
```

### Fault Tolerance
```
Single point of failure → Redundancy:
- Database replication (primary + replica)
- Kafka replication (3 brokers)
- Circuit breakers (fast fail)
- Canary deployments (gradual rollout)
```

---

## 🔟 DEPLOYMENT

### Docker Compose
```yaml
services:
  postgres: Stores OHLCV & historical data
  redis: Caching & streaming
  kafka: Event streaming
  backend: FastAPI server
  frontend: React dashboard
  jupyter: For research
```

### Cloud Deployment (AWS)
```
EC2: Run backend
RDS: PostgreSQL
ElastiCache: Redis
MSK: Managed Kafka
S3: Store backtest results
CloudWatch: Monitoring
```

### Kubernetes (Production Scale)
```yaml
deployments:
  data-fetcher: Stateless, scalable
  strategy-engine: Stateless, load-balanced
  risk-monitor: Single instance (state-dependent)
  execution-service: Single instance (order state)
```

---

## Conclusion

This architecture achieves:
- ✅ **Separation of concerns** (8 independent layers)
- ✅ **Scalability** (horizontal scaling where possible)
- ✅ **Robustness** (fault tolerance, fallbacks)
- ✅ **Testability** (unit tests per layer)
- ✅ **Extensibility** (easy to add features)
- ✅ **Production-readiness** (monitoring, alerting, deployment)

**Total complexity:** ~10k LOC
**Interview value:** ⭐⭐⭐⭐⭐
