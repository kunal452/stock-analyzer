# Indian Stock Market Analyzer & Prediction System 📈🇮🇳

An institutional-grade quantitative trading pipeline, feature engineering engine, and machine learning directional prediction system built for **Indian Equities (NSE/BSE)**.

Features **automated daily market updates**, **real-time dynamic company search & discovery**, and an **actionable investment advisory engine** that suggests specific companies to invest in with custom position sizing and plain-English investment theses.

---

## ⭐ Key Highlights & Features

1. **Daily Automated Market Updates**:
   - Background scheduler automatically tracks Indian market trading hours (09:15 – 15:30 IST).
   - Automatically executes a full end-of-day quantitative scan at **15:45 IST** after market settlement.
   - Caches and archives daily top picks to disk so results load instantaneously.
   - One-click **"Run Daily Scan Now"** button for immediate on-demand updates.

2. **Broad Universe & Dynamic Company Search**:
   - Scans 140+ top liquid Indian equities across Nifty 50, Nifty Next 50, Midcaps, Defense, Railways, PSUs, Banking, and IT.
   - Real-time search autocomplete lets users search **ANY company** by name or symbol (e.g., Tata, Zomato, Reliance, Suzlon, BHEL, IRFC).
   - Preset selectors: *Nifty 50 Bluechips*, *Nifty 100*, *High-Growth Midcaps*, *Defense & PSU*, *Banking & Financials*, or *Full Market Basket*.

3. **Intelligent Investment Recommendations**:
   - Directly answers: **"Which companies should I invest in today?"**
   - Categorized into:
     - 🏆 **Long-Term Compounders (6–12 Months)**: High ROE, sustainable debt, above 200 EMA.
     - 🚀 **High-Conviction Swing Trades (1–4 Weeks)**: Machine learning probability ≥ 60%, Supertrend bullish, volume expansion.
     - 💎 **Value Dip Buys (1–3 Months)**: High-quality companies pulling back near 50/200 EMA support.
   - Detailed trade setup: Entry zone, Target 1 (+% gain), Target 2, Dynamic ATR Stop-Loss (-% risk), and Risk-to-Reward ratio (≥ 1:1.8).
   - **Portfolio Base Customizer**: Enter your capital (e.g. ₹50,000, ₹1,00,000, ₹5,00,000) and get exact recommended shares and investment amounts!

---

## 🏗️ System Architecture

```text
[ NSE / BSE Data Pipeline ]
        │ (yfinance / NSE tickers e.g. RELIANCE.NS, TCS.NS, Nifty 50 Benchmark)
        ▼
[ Feature Engineering Engine ]
        ├── Technical Indicators (RSI, Stochastic, MACD, EMAs 20/50/200, Supertrend, ATR, Bollinger Bands)
        ├── Volume Signals (20-day Volume SMA ratio, On-Balance Volume slope, Turnover in ₹ Crores)
        ├── Market Regime (Nifty 50 50-day EMA trend, 20-day relative strength)
        └── Fundamental Valuation (P/E, Market Cap, 52-Week High/Low range, ROE)
        ▼
[ Predictive Core & Labeling ]
        ├── Target: Triple-Barrier Labeling (Max upside ≥ +4.0% & Max drawdown > -2.5% in 10 sessions)
        ├── Model: LightGBM Gradient Boosted Decision Trees with Calibrated Probabilities
        └── Validation: Strict Walk-Forward Chronological Split (No random shuffling or future leakage)
        ▼
[ Stock Screener & Ranking Rule Engine ]
        ├── Trend Safety: Price > 50-Day and 200-Day EMA (Confirmed Uptrend)
        ├── Liquidity Check: Average 20-day daily turnover ≥ ₹10–20 Crore
        ├── Model Conviction: LightGBM probability ≥ 60%
        └── Dynamic Trade Plan: Entry, Stop-Loss (1.5x ATR), Targets (+5% to +10%), Risk:Reward (≥ 1:1.5)
        ▼
[ Interactive Dashboard & Analytics ]
        ├── Live Top Buy Recommendations & Filter Matrix
        ├── Deep Dive Candlestick Charts with TradingView Lightweight Charts
        ├── Interactive Strategy Backtester (Equity Curve, Win Rate, Profit Factor, Drawdown)
        └── Model Diagnostics & Feature Importance
```

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure Python 3.10+ is installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Interactive Dashboard
```bash
python run.py
```
This automatically starts the FastAPI application at `http://localhost:8000` and opens the dashboard in your default browser.

### 4. Run CLI Quick Evaluation
You can also run instant quantitative evaluations from your terminal:
```bash
# Evaluate TCS
python run.py --symbol TCS.NS

# Evaluate Reliance
python run.py --symbol RELIANCE.NS

# Evaluate Tata Motors
python run.py --symbol TATAMOTORS.NS
```

---

## 📊 Core Quantitative Modules

### 1. Triple-Barrier Target Formulation (`backend/feature_engineering.py`)
Direct next-day close regression is plagued by non-stationary market noise. We frame the problem as **directional probability classification** over a 10-day holding horizon:

$$\text{Target} = \begin{cases} 1 & \text{if } \max_{t \in [1, 10]} \left(\frac{\text{High}_t - \text{Close}_0}{\text{Close}_0}\right) \ge 4.0\% \quad \text{and} \quad \min_{t \in [1, 10]} \left(\frac{\text{Low}_t - \text{Close}_0}{\text{Close}_0}\right) > -2.5\% \\ 0 & \text{otherwise} \end{cases}$$

This ensures that stocks labeled as "Buy" would not have hit an early stop-loss before reaching their upside target.

### 2. Walk-Forward Chronological Validation (`backend/ml_engine.py`)
Random shuffling in financial time series causes severe future lookahead bias. The model enforces **expanding/walk-forward time-series splits** (past 80% train, subsequent 20% out-of-sample test), measuring real-world precision, recall, and ROC-AUC.

### 3. Safety Screening Rules (`backend/screener.py`)
Before receiving a Buy recommendation, candidate stocks must pass:
1. **Trend Filter**: `Close > EMA_50` and `Close > EMA_200`
2. **Liquidity Filter**: 20-day Average Daily Turnover $\ge \text{₹}10\text{ Crore}$
3. **Model Conviction**: Output probability $\ge 60\%$
4. **Risk-Reward Threshold**: Dynamic Target to Stop-Loss ratio $\ge 1.50$

### 4. Dynamic Trade Plan & Position Sizing
- **Entry Price**: Current market close or breakout level.
- **Dynamic Stop-Loss**: $\text{Entry} - (1.5 \times \text{ATR}_{14})$
- **Target 1**: $\text{Entry} + (1.5 \times \text{Stop Distance})$ (~5% to 7% upside)
- **Target 2**: $\text{Entry} + (2.5 \times \text{Stop Distance})$ (~8% to 12% runner)
- **Position Sizing**: Calculated for ₹1,00,000 portfolio base risking max 1.5% (₹1,500).

---

## 🌐 REST API Endpoints

- `GET /api/universe`: Get list of supported NSE stocks and benchmark indices.
- `GET /api/market-overview`: Latest Nifty 50, Bank Nifty, and macro regime status.
- `GET /api/screener`: Run quantitative multi-factor screener and rank candidates.
- `GET /api/analyze/{symbol}`: Full deep dive with OHLCV candlestick series, indicators, ML probability, trade setup, and fundamentals.
- `POST /api/train/{symbol}`: Trigger Walk-Forward model retraining and diagnostics.
- `GET /api/backtest/{symbol}`: Run historical strategy backtest with custom capital and probability thresholds.
- `GET /docs`: Interactive Swagger API documentation.
