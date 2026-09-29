"""
Backtesting Engine for Indian Equities Quantitative Strategy.
Simulates historical trade execution with realistic ATR stop-loss, profit targets,
max holding horizons, equity curve tracking, and performance statistics.
"""

import logging
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from backend.data_engine import fetch_historical_ohlcv, fetch_benchmark_data
from backend.feature_engineering import engineer_features, get_feature_columns
from backend.ml_engine import train_time_series_model
from backend.config import MODEL_PARAMS, SCREENER_THRESHOLDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_strategy_backtest(
    symbol: str, 
    start_capital: float = 100000.0,
    prob_threshold: float = 0.58
) -> Dict[str, Any]:
    """
    Simulates the quantitative ML strategy over historical test period.
    """
    raw_df = fetch_historical_ohlcv(symbol, period="5y")
    benchmark_df = fetch_benchmark_data(period="5y")
    features_df = engineer_features(raw_df, benchmark_df=benchmark_df)

    feature_cols = get_feature_columns()
    valid_df = features_df.dropna(subset=feature_cols + ["Target"]).copy()

    if len(valid_df) < 300:
        raise ValueError(f"Insufficient history for backtest on {symbol}. Need >= 300 bars.")

    # Train model on first 60% of data, backtest on remaining 40% (out-of-sample simulation)
    split_idx = int(len(valid_df) * 0.60)
    train_df = valid_df.iloc[:split_idx]
    test_df = valid_df.iloc[split_idx:].copy()

    model, metrics = train_time_series_model(valid_df, symbol)

    # Predict probabilities for the test partition
    X_test = test_df[feature_cols]
    test_df["ML_Prob"] = model.predict_proba(X_test)[:, 1]

    # Trading variables
    capital = start_capital
    equity_curve: List[Dict[str, Any]] = []
    trade_log: List[Dict[str, Any]] = []

    in_trade = False
    entry_price = 0.0
    entry_date = None
    stop_loss = 0.0
    target_price = 0.0
    days_in_trade = 0
    shares = 0
    trade_capital = 0.0

    n_bars = len(test_df)
    test_dates = test_df.index
    closes = test_df["Close"].values
    highs = test_df["High"].values
    lows = test_df["Low"].values
    ema50s = test_df["EMA_50"].values
    ema200s = test_df["EMA_200"].values
    atrs = test_df["ATR_14"].values
    probs = test_df["ML_Prob"].values

    buy_and_hold_start_price = closes[0]

    for i in range(n_bars):
        current_date_str = str(test_dates[i].strftime("%Y-%m-%d") if hasattr(test_dates[i], "strftime") else test_dates[i])
        current_close = closes[i]
        current_high = highs[i]
        current_low = lows[i]

        if in_trade:
            days_in_trade += 1
            exit_reason = None
            exit_price = current_close

            # Check Stop Loss hit
            if current_low <= stop_loss:
                exit_price = stop_loss
                exit_reason = "Stop-Loss Hit"
            # Check Target reached
            elif current_high >= target_price:
                exit_price = target_price
                exit_reason = "Profit Target Reached"
            # Check Time Horizon expiration (10 trading days)
            elif days_in_trade >= MODEL_PARAMS["holding_horizon_days"]:
                exit_price = current_close
                exit_reason = "Horizon Expired (10D)"

            if exit_reason is not None:
                pnl = (exit_price - entry_price) * shares
                trade_return_pct = ((exit_price - entry_price) / entry_price) * 100
                capital += pnl

                trade_log.append({
                    "entry_date": entry_date,
                    "exit_date": current_date_str,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "shares": shares,
                    "pnl_rupees": round(pnl, 2),
                    "return_pct": round(trade_return_pct, 2),
                    "exit_reason": exit_reason,
                    "holding_days": days_in_trade
                })

                in_trade = False
                days_in_trade = 0
                shares = 0

        # Check for new entry signal (if not already in trade)
        if not in_trade and i < n_bars - 1:
            prob = probs[i]
            # Safety rules: Prob >= threshold, Price > EMA 50, Price > EMA 200
            if prob >= prob_threshold and current_close > ema50s[i] and current_close > ema200s[i]:
                atr = atrs[i]
                stop_dist = max(atr * 1.5, current_close * 0.015)
                
                entry_price = current_close
                entry_date = current_date_str
                stop_loss = round(entry_price - stop_dist, 2)
                target_price = round(entry_price + (stop_dist * 2.0), 2)

                # Position sizing (risk 1.5% of current equity)
                risk_rupees = capital * 0.015
                risk_per_share = max(1.0, entry_price - stop_loss)
                shares = max(1, int(risk_rupees / risk_per_share))
                trade_capital = shares * entry_price

                # Ensure we have enough capital
                if trade_capital > capital * 0.95:
                    shares = max(1, int((capital * 0.95) / entry_price))
                    trade_capital = shares * entry_price

                in_trade = True
                days_in_trade = 0

        # Record Daily Equity
        unrealized_pnl = (current_close - entry_price) * shares if in_trade else 0.0
        current_equity = capital + unrealized_pnl
        bnh_equity = start_capital * (current_close / buy_and_hold_start_price)

        equity_curve.append({
            "date": current_date_str,
            "strategy_equity": round(current_equity, 2),
            "benchmark_equity": round(bnh_equity, 2),
            "in_trade": in_trade
        })

    # Performance Statistics
    total_trades = len(trade_log)
    winning_trades = [t for t in trade_log if t["pnl_rupees"] > 0]
    losing_trades = [t for t in trade_log if t["pnl_rupees"] <= 0]

    win_rate_pct = round((len(winning_trades) / total_trades * 100), 2) if total_trades > 0 else 0.0
    gross_profits = sum(t["pnl_rupees"] for t in winning_trades)
    gross_losses = abs(sum(t["pnl_rupees"] for t in losing_trades))
    profit_factor = round(gross_profits / max(1.0, gross_losses), 2) if gross_losses > 0 else (99.0 if gross_profits > 0 else 0.0)

    final_strategy_equity = equity_curve[-1]["strategy_equity"] if equity_curve else start_capital
    strategy_return_pct = round(((final_strategy_equity - start_capital) / start_capital) * 100, 2)

    final_bnh_equity = equity_curve[-1]["benchmark_equity"] if equity_curve else start_capital
    bnh_return_pct = round(((final_bnh_equity - start_capital) / start_capital) * 100, 2)

    # Max Drawdown
    equity_series = pd.Series([e["strategy_equity"] for e in equity_curve])
    peak = equity_series.cummax()
    drawdown = (equity_series - peak) / peak
    max_drawdown_pct = round(abs(float(drawdown.min())) * 100, 2) if not drawdown.empty else 0.0

    # Sharpe Ratio proxy
    daily_returns = equity_series.pct_change().dropna()
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe_ratio = round(float((daily_returns.mean() / daily_returns.std()) * np.sqrt(252)), 2)
    else:
        sharpe_ratio = 0.0

    return {
        "symbol": symbol,
        "start_capital": start_capital,
        "final_capital": round(final_strategy_equity, 2),
        "strategy_return_pct": strategy_return_pct,
        "buy_and_hold_return_pct": bnh_return_pct,
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate_pct": win_rate_pct,
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_drawdown_pct,
        "sharpe_ratio": sharpe_ratio,
        "equity_curve": equity_curve[-120:],  # Return recent 120 trading sessions for fast snappy visualization
        "recent_trades": trade_log[-20:]      # Return last 20 trades
    }
