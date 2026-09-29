"""
Integration test script for Indian Stock Market Analyzer & Prediction System.
Validates data ingestion, feature calculation, model training, trade planning, and backtesting.
"""

import sys
import logging
from backend.data_engine import fetch_historical_ohlcv, fetch_benchmark_data, fetch_ticker_fundamentals
from backend.feature_engineering import engineer_features, get_feature_columns
from backend.ml_engine import train_time_series_model, predict_latest_setup
from backend.screener import evaluate_single_stock, generate_trade_plan
from backend.backtest_engine import run_strategy_backtest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def test_pipeline():
    symbol = "TCS.NS"
    print(f"\n=======================================================")
    print(f" Testing Quantitative Pipeline for {symbol}")
    print(f"=======================================================\n")

    # 1. Ingestion
    print("1. Ingesting historical OHLCV data...")
    df = fetch_historical_ohlcv(symbol, period="3y")
    print(f"   [SUCCESS] Fetched {len(df)} daily bars from {df.index[0].date()} to {df.index[-1].date()}")
    print(f"   Latest Close: Rs. {df['Close'].iloc[-1]:.2f}, Volume: {df['Volume'].iloc[-1]:,}")

    # 2. Benchmark data
    print("\n2. Fetching Nifty 50 benchmark data...")
    bench_df = fetch_benchmark_data(period="3y")
    print(f"   [SUCCESS] Nifty 50 bars: {len(bench_df)}, Latest Close: {bench_df['Close'].iloc[-1]:.2f}")

    # 3. Feature Engineering
    print("\n3. Calculating Technical Indicators and Triple-Barrier Labels...")
    features_df = engineer_features(df, benchmark_df=bench_df)
    feat_cols = get_feature_columns()
    print(f"   [SUCCESS] Generated {len(feat_cols)} features: {feat_cols[:6]}...")
    print(f"   Latest RSI(14): {features_df['RSI_14'].iloc[-1]:.2f}")
    print(f"   Latest EMA(50): {features_df['EMA_50'].iloc[-1]:.2f}")
    print(f"   Latest Supertrend: {features_df['Supertrend'].iloc[-1]:.2f} (Dir: {features_df['Supertrend_Dir'].iloc[-1]})")

    # 4. ML Model Training & Walk-Forward Validation
    print("\n4. Training LightGBM Classifier with Chronological Time-Series Split...")
    model, metrics = train_time_series_model(features_df, symbol, retrain=True)
    print(f"   [SUCCESS] Model Trained!")
    print(f"   Train samples: {metrics['train_samples']}, Test samples: {metrics['test_samples']}")
    print(f"   Test Accuracy: {metrics['accuracy']:.2%}")
    print(f"   Test Precision: {metrics['precision']:.2%}")
    print(f"   Test ROC-AUC: {metrics['roc_auc']:.3f}")
    print(f"   Top 3 Predictive Features:")
    for feat in metrics["feature_importances"][:3]:
        print(f"     - {feat['feature']}: {feat['importance']}% importance")

    # 5. Live Inference & Trade Planning
    print("\n5. Running Live Inference & Trade Plan Generation...")
    prediction = predict_latest_setup(features_df, symbol, model=model, metrics=metrics)
    print(f"   ML Buy Probability: {prediction['buy_probability_pct']:.1f}% ({prediction['conviction']})")

    evaluation = evaluate_single_stock(symbol, benchmark_df=bench_df)
    plan = evaluation["trade_plan"]
    print(f"\n   Trade Setup for {symbol}:")
    print(f"   Entry: Rs. {plan['entry_price']}")
    print(f"   Dynamic Stop-Loss: Rs. {plan['stop_loss']} (-{plan['stop_loss_pct']}%)")
    print(f"   Target 1 (+5% to +8%): Rs. {plan['target_1']} (+{plan['target_1_pct']}%)")
    print(f"   Risk-to-Reward: {plan['risk_reward_ratio']}")
    print(f"   Position Sizing (Rs. 1,00,000 Portfolio): Buy {plan['position_sizing']['recommended_shares']} shares (Total Rs. {plan['position_sizing']['trade_capital_required']})")

    # 6. Backtest Simulation
    print("\n6. Running Historical Strategy Backtest...")
    bt_result = run_strategy_backtest(symbol, start_capital=100000.0)
    print(f"   Total Trades: {bt_result['total_trades']}")
    print(f"   Win Rate: {bt_result['win_rate_pct']:.1f}%")
    print(f"   Profit Factor: {bt_result['profit_factor']}")
    print(f"   Strategy Net Return: {bt_result['strategy_return_pct']:.1f}%")
    print(f"   Max Drawdown: {bt_result['max_drawdown_pct']:.1f}%")

    print("\n=======================================================")
    print(" ALL TESTS PASSED SUCCESSFULLY! Quantitative Engine is Ready.")
    print("=======================================================\n")

if __name__ == "__main__":
    test_pipeline()
