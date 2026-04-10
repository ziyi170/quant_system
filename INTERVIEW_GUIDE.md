# 🎯 System Design Interview Guide - AI Quantitative Trading System

## Overview (1 min)

**One-liner:**
> An end-to-end intelligent quantitative trading system that processes real-time market data, uses AI to interpret events, validates strategies through rigorous backtesting, and manages risk dynamically.

**Key differentiator:**
> It's not about predicting prices—it's about **understanding market reactions to events** and **automating disciplined execution** with strict risk controls.

---

## System Architecture Deep Dive (5 min)

### High-Level Flow
```
Market Data → Event Extraction → AI Reasoning → Strategy → Risk Engine → Execution
     ↓              ↓                  ↓           ↓          ↓            ↓
  Real-time    News + Prices    Sentiment +    Signals +   Position   Orders +
   OHLCV       → Microstructure   LLM Insight   Portfolio  Sizing      Fills
```

### Layer-by-Layer Breakdown

#### 1. **Data Layer** (Real-time Market Data)
**Problem:** Markets are event streams, not just price feeds.

**Solution:**
- **Tick-level data**: Every price change (not just OHLCV)
- **Order book depth**: Bid-ask spread, volume imbalance signals
- **Corporate actions**: Stock splits, dividends (affects price adjustment)
- **Alternative data**: News, sentiment, macro indicators

**Tech:**
```
yfinance → PostgreSQL (historical)
WebSocket → Redis Streams (real-time)
```

**Why this design:**
- PostgreSQL handles 10M+ rows efficiently
- Redis for sub-second latency on streaming data
- Separation: cold data (DB) vs hot data (cache)

---

#### 2. **Event Streaming Layer** (Critical Infrastructure)
**Problem:** Coupling market data directly to strategy causes brittleness.

**Solution:** Event-driven architecture with topic separation
```
Raw Data → Event Producer → Kafka Topics → Event Consumers → Processors
           
           Topics:
           - market-prices (ticks)
           - order-book (depth changes)
           - news-events (sentiment)
           - signals (trading signals)
```

**Key design choice:**
- Use **Kafka** for guaranteed delivery, ordering, replay capability
- Fallback: **Redis Streams** for simpler setup
- Enable backtesting: replay historical events

**Interview talking points:**
- "Kafka gives us event ordering per partition"
- "We can replay market data for strategy validation"
- "Decouples data producers from consumers"

---

#### 3. **AI Intelligence Layer** (Why this matters)
**Problem:** Raw market data is noise. AI extracts meaning.

**Three components:**

**a) NLP Sentiment Analysis**
```
News: "Apple beats earnings by 10%"
      ↓
sentiment_model (DistilBERT)
      ↓
{sentiment: 0.95, label: "POSITIVE"}
```

**b) Structured Event Extraction** ⭐ Key differentiator
```
News: "Fed raises rates 25bps"
      ↓
LLM (GPT-4)
      ↓
{
  event_type: "RATE_HIKE",
  magnitude: 25,
  expected_impact: {
    fixed_income: "NEGATIVE",
    usd: "POSITIVE",
    equity: "MIXED"
  }
}
```

**c) LLM Reasoning**
```
Market State + Historical Context
      ↓
GPT-4: "Bond yields rising, creating headwind for growth stocks.
        But tech with strong earnings could outperform."
      ↓
Decision: { bias: "LONG_VALUE", confidence: 0.73 }
```

**Why this design:**
- Don't predict, **interpret**
- LLM helps with context (vs pure statistics)
- Sentiment is input to factor model, not sole decision

**Cost optimization:**
- Use cheaper models (DistilBERT) for routine tasks
- Reserve GPT-4 for complex reasoning
- Cache LLM outputs (same news → same analysis)

---

#### 4. **Strategy Generation Layer** (The Quantitative Core)
**Problem:** Single predictors overfit. Correct approach: **portfolio optimization**.

**Components:**

**a) Technical Indicators** (TA)
```python
RSI(14) → Oversold signal
MACD → Momentum confirmation
Bollinger Bands → Volatility adjustment
```

**b) Factor Model** (Multi-factor)
```
Return = α + β₁×Momentum + β₂×Value + β₃×Volatility + β₄×Sentiment + ε

Weights (from optimization):
- Momentum: 30%
- Value: 25%
- Volatility: 20%
- Sentiment (AI): 15%
- Technicals: 10%
```

**c) Portfolio Optimization**
```
Maximize: Sharpe Ratio = (Return - Rf) / Volatility

Subject to:
- Max leverage: 2x
- Position limit: 10% per stock
- Sector limits
- Correlation constraints
```

**Tech: cvxpy**
```python
cvxpy.Problem(
    cvxpy.Maximize(sharpe_ratio),
    constraints=[leverage <= 2, position <= 0.1, ...]
)
```

**Why this design:**
- **"Portfolio > individual predictions"**
- Optimization naturally handles correlations
- Diversification reduces drawdowns

---

#### 5. **Risk Management Engine** (Most Critical)
**Principle: Survival > Returns**

**Three layers:**

**a) Position Sizing** (Dynamic)
```
position_size = f(
    portfolio_volatility,
    position_correlation,
    sentiment_signal,
    technical_indicator
)

→ Position in AAPL today: 3%, tomorrow: 2% (volatility increased)
```

**b) Value at Risk (CVaR)**
```
At 95% confidence:
- VaR: 5% (worst 5% of days)
- CVaR: 6.2% (average of worst 5%)

Set: Max position = CVaR / 2
```

**c) Stress Testing**
```
Scenarios:
- Market crash 20% (2008)
- Interest rate shock +200bps (Volcker era)
- Liquidity crisis (gaps in bid-ask)
- Correlation breakdown (crisis mode)

→ Simulation: if scenario hits, account loss < 15%?
```

**Live risk monitoring:**
```
Every minute:
- Calculate portfolio Greeks (delta, vega, rho)
- Monitor concentration risk
- Alert if approaching limits
```

**Interview talking points:**
- "CVaR is more conservative than VaR"
- "Stress testing catches black swans VaR misses"
- "Risk is managed before positions are taken"

---

#### 6. **Research & Evaluation Layer** (Validation)
**Problem: How do we know strategy works? (Not just luck)**

**Walk-Forward Analysis** ⭐ Most robust test
```
Divide history into periods:

[Training] [Test]
[  2020  ] [2021]  → Train model on 2020, test on 2021
           [Training] [Test]
           [  2021  ] [2022]  → Train on 2021, test on 2022
                      [Training] [Test]
                      [  2022  ] [2023]
```

**Why walk-forward?**
- Prevents look-ahead bias
- Parameter reoptimization captures regime changes
- Out-of-sample test is gold standard

**Metrics We Calculate:**
```
Sharpe Ratio = (Return - Rf) / Volatility
- Penalizes both upside and downside
- Standard in portfolio management

Sortino Ratio = (Return - Rf) / Downside Volatility
- Only penalizes losses (more realistic)
- Better than Sharpe for traders

Max Drawdown = Peak-to-Trough decline
- Psychological impact of losses
- Tells us: worst day, how long to recover?

Win Rate = % of profitable trades
- 50% win rate with 2:1 profit/loss ratio = 📈
- 70% win rate with 0.5:1 ratio = 📉

Profit Factor = Gross Profit / Gross Loss
- > 2.0 is considered robust
```

**Code:**
```python
engine = BacktestEngine(initial_capital=100000)
metrics = engine.run_backtest(historical_data, signals)

# Metrics: {
#   "sharpe_ratio": 1.45,
#   "max_drawdown": 0.12,
#   "win_rate": 0.62,
#   "profit_factor": 2.31
# }
```

---

#### 7. **Execution Layer** (The Bridge to Reality)
**Problem: Backtesting != Live Trading**

**Three execution modes:**

**a) Paper Trading (Simulated)**
```
- No real money
- Realistic commission (0.1%)
- Slippage simulation (0.05%)
- Order fills at next bar (not instant)
- Good for testing before going live
```

**b) Live Trading (via Broker API)**
```python
broker = AlpacaAPI()  # or Interactive Brokers

order = broker.place_order(
    symbol="AAPL",
    qty=100,
    side="BUY",
    type="LIMIT",
    limit_price=150.50,
    time_in_force="DAY"
)
```

**c) Order Management**
```
Types:
- LIMIT: Execute only at target price
- MARKET: Execute immediately (market risk)
- PARTIAL FILL: Handle situations where only part fills

→ Tracking orders until execution or cancellation
```

---

## Data Flow Example: "Breaking News" Scenario

```
[Real-time feed]
CNBC: "Apple beats Q4 earnings, raises guidance"

[Event Streaming]
news_event = {
  ticker: "AAPL",
  title: "...",
  source: "CNBC",
  timestamp: 2024-01-23 14:32:00
}
→ Kafka topic: news-events

[AI Processing]
NLP: sentiment = 0.92 (STRONG POSITIVE)
LLM: {
  event: "POSITIVE_EARNINGS_SURPRISE",
  impact: "SHORT_TERM_BULLISH",
  confidence: 0.85
}

[Strategy]
Factor Model + MACD signal:
  → Score = +0.68 (strong buy signal)

[Risk Engine]
Current allocation to tech: 25%
Adding 2% AAPL = 27% total (within 30% limit)
Position size: 100 shares (= 2% portfolio)

[Execution]
Place limit order: 100 AAPL @ $150.00

[Monitoring]
- Track fill status
- Monitor AAPL if gaps up → market order
- Set stop loss @ $148.00
```

---

## Scalability Questions & Answers

### Q: How do we handle 1000 symbols?

**A:** 
```
Current: Fetches daily
Scale to: Real-time intraday

Data layer:
- Kafka partitions by symbol (1000 partitions)
- Each partition has 1 consumer (parallel processing)
- Redis cache for hot symbols

Strategy:
- Factor model runs per symbol
- Optimization batches updates (hourly)

→ Latency: < 100ms from event to decision
```

### Q: How do we prevent overfitting?

**A:**
```
1. Walk-forward analysis (not train/test split)
2. Out-of-sample testing on held-out periods
3. Parameter sensitivity testing:
   - Does strategy break if RSI period = 15 vs 14?
   - Sharpe = 1.5, confident in signal
   - Sharpe = 1.1, might be luck

4. Constraints:
   - Max positions: limits curve-fitting to specific stocks
   - Factor weights: regularization prevents overweighting

5. Live validation:
   - Forward test on recent data (not in model)
   - Kill strategy if live Sharpe < 0.8
```

### Q: How do we handle market gaps (overnight)?

**A:**
```
Pre-market logic:
1. Calculate overnight sentiment change
2. Check macro announcements (Fed, jobs report)
3. Adjust position size down if volatility spike expected
4. Set wider stop losses

→ Opens at 9:30am:
   - Check actual gap vs predicted
   - Rebalance positions
   - May exit if gap too large
```

### Q: What if our LLM (ChatGPT) goes down?

**A:**
```
1. Cache layer:
   - Redis: "Apple earnings" → cached sentiment (24h TTL)
   - 99% of market repetitive (same stocks, similar events)

2. Fallback:
   - Use simpler NLP model (DistilBERT) if LLM unavailable
   - 70% accuracy vs 85%, but 100% uptime

3. Circuit breaker:
   - If LLM latency > 5s: use cache or skip sentiment
   - Don't wait for perfect data; trade with what we have
```

---

## System Design Trade-offs

| Aspect | Choice | Why |
|--------|--------|-----|
| **Kafka vs Redis** | Kafka | Event ordering & replay for backtesting |
| **PostgreSQL vs NoSQL** | PostgreSQL | ACID + time-series queries (OHLCV) |
| **Real-time vs Batch** | Hybrid | Real-time signals, batch factor updates |
| **Single Factor vs Multi-Factor** | Multi-factor | Diversification, lower drawdown |
| **Manual vs Automated Risk** | Automated | Emotions in crisis, machines don't panic |
| **Paper vs Live** | Paper first | Test, validate, then live after 6 months |

---

## Key Metrics to Watch (Interviewer wants to hear these)

1. **Sharpe Ratio > 1.0** = Decent risk-adjusted returns
2. **Max Drawdown < 15%** = Survivable
3. **Win Rate > 55%** = More wins than losses
4. **Walk-forward validated** = Not just lucky
5. **Profit Factor > 2.0** = Gross profit 2x gross loss

---

## Potential Follow-up Questions

### Q: How do you handle transaction costs?
```
A: Model them explicitly:
- Commission: 0.1% per trade
- Slippage: 0.05% (worst-case execution)
- Market impact: 0.02% (large orders move price)

→ Strategy must beat these costs to be profitable
   (Dead zone: strategies with < 1% annual return won't work)
```

### Q: How do you manage multiple assets?
```
A: Correlation-aware portfolio optimization:
- AAPL and MSFT: high correlation (tech)
- AAPL and XLE (energy): low correlation
- Optimize for max Sharpe across basket
- Constraints: max 10% per stock, 30% per sector
```

### Q: What about latency requirements?
```
A: Latency budget (100ms):
- Data fetch: 10ms
- AI/LLM processing: 50ms
- Strategy calculation: 20ms
- Order placement: 20ms

→ Use async/parallel where possible
→ Pre-compute factors if time-sensitive
```

### Q: How do you test reliability?
```
A: Three-pronged approach:
1. Unit tests: Each component (indicator, risk engine)
2. Integration tests: Full pipeline with real data
3. Chaos engineering: Kill Kafka, test fallbacks

→ Must have 99.9% uptime (allow 43 sec downtime/month)
```

---

## Conclusion (30 seconds)

"This system embodies modern quantitative trading principles:
1. **Event-driven** - Markets are event streams
2. **Statistically rigorous** - Walk-forward validation
3. **Risk-first** - Survival before returns
4. **AI-enhanced** - Interpretation, not prediction
5. **Scaled for production** - Handles thousands of symbols

The key insight: **automation removes emotion**, and **discipline beats genius**."

---

## Recommended Follow-up Reading
- "A Century of Evidence on Trend-Following Investing" (AQR)
- "The Intelligent Investor" - Graham & Dodd (principles)
- "Advances in Active Portfolio Management" - Grinold & Kahn
