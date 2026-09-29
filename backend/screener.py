"""
Quantitative Screener and Multi-Factor Ranking Engine for Indian Equities.
Applies rule-based safety screens (Trend Filter, Liquidity, ATR Risk-Reward),
ranks buy candidates using ML conviction and quantitative factors,
and generates structured investment advisory recommendations.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from backend.config import DEFAULT_NSE_STOCKS, UNIVERSE_PRESETS, SCREENER_THRESHOLDS
from backend.data_engine import fetch_historical_ohlcv, fetch_ticker_fundamentals, fetch_benchmark_data
from backend.feature_engineering import engineer_features
from backend.ml_engine import predict_latest_setup
from backend.advisor import generate_investment_suggestions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_trade_plan(
    current_close: float,
    atr_val: float,
    capital: float = SCREENER_THRESHOLDS["default_capital"],
    risk_pct: float = SCREENER_THRESHOLDS["max_risk_per_trade_pct"],
    atr_multiplier: float = SCREENER_THRESHOLDS["atr_stop_loss_multiplier"],
    min_rr_ratio: float = SCREENER_THRESHOLDS["target_risk_reward_ratio"]
) -> Dict[str, Any]:
    """
    Calculate dynamic entry, ATR stop-loss, profit targets, risk-reward ratio,
    and portfolio position sizing according to professional risk management rules.
    """
    entry_price = round(current_close, 2)
    # Stop loss placed at 1.5 * ATR below entry (min 1.5% distance)
    stop_distance = max(atr_val * atr_multiplier, entry_price * 0.015)
    stop_loss = round(max(0.01, entry_price - stop_distance), 2)
    stop_pct = round(((entry_price - stop_loss) / entry_price) * 100, 2)

    # Targets: Target 1 at 1.5x risk, Target 2 at 2.5x risk
    target_1 = round(entry_price + (stop_distance * 1.5), 2)
    target_1_pct = round(((target_1 - entry_price) / entry_price) * 100, 2)

    target_2 = round(entry_price + (stop_distance * 2.5), 2)
    target_2_pct = round(((target_2 - entry_price) / entry_price) * 100, 2)

    # Risk to Reward
    risk_amount_per_share = entry_price - stop_loss
    reward_amount_per_share = target_1 - entry_price
    rr_ratio = round(reward_amount_per_share / max(0.01, risk_amount_per_share), 2)

    # Position Sizing
    max_risk_rupees = capital * risk_pct  # e.g. 1.5% of ₹1,00,000 = ₹1,500
    shares_to_buy = int(max_risk_rupees / max(0.1, risk_amount_per_share)) if risk_amount_per_share > 0 else 0
    trade_capital_required = round(shares_to_buy * entry_price, 2)

    return {
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "stop_loss_pct": stop_pct,
        "target_1": target_1,
        "target_1_pct": target_1_pct,
        "target_2": target_2,
        "target_2_pct": target_2_pct,
        "risk_reward_ratio": f"1 : {rr_ratio}",
        "risk_reward_numeric": rr_ratio,
        "risk_per_share": round(risk_amount_per_share, 2),
        "position_sizing": {
            "account_capital": capital,
            "max_risk_rupees": round(max_risk_rupees, 2),
            "recommended_shares": shares_to_buy,
            "trade_capital_required": trade_capital_required,
            "capital_allocation_pct": round((trade_capital_required / capital) * 100, 2) if capital > 0 else 0.0
        }
    }


def evaluate_single_stock(
    symbol: str, 
    benchmark_df: Optional[pd.DataFrame] = None
) -> Optional[Dict[str, Any]]:
    """
    Evaluate single stock through full quantitative pipeline:
    OHLCV -> Features -> Model Prediction -> Fundamentals -> Safety Filters -> Trade Plan.
    """
    try:
        raw_df = fetch_historical_ohlcv(symbol, period="5y")
        if raw_df is None or len(raw_df) < 220:
            logger.warning(f"Skipping {symbol}: Insufficient price bars.")
            return None

        features_df = engineer_features(raw_df, benchmark_df=benchmark_df)
        pred_result = predict_latest_setup(features_df, symbol)
        fundamentals = fetch_ticker_fundamentals(symbol)

        latest_row = features_df.iloc[-1]
        close = float(latest_row["Close"])
        ema_20 = float(latest_row["EMA_20"])
        ema_50 = float(latest_row["EMA_50"])
        ema_200 = float(latest_row["EMA_200"])
        atr_14 = float(latest_row["ATR_14"])
        rsi_14 = float(latest_row["RSI_14"])
        vol_ratio = float(latest_row["Vol_Ratio"])
        turnover_cr = float(latest_row["Avg_Turnover_20D_Cr"])
        supertrend_dir = int(latest_row["Supertrend_Dir"])

        # Safety Rules Screen
        # 1. Trend Filter: Price > 50 EMA and Price > 200 EMA
        pass_trend = bool(close > ema_50 and close > ema_200)
        
        # 2. Liquidity Check: 20-day Average Daily Turnover >= min_turnover_cr
        min_turnover = SCREENER_THRESHOLDS["min_turnover_cr"]
        pass_liquidity = bool(turnover_cr >= min_turnover)

        # 3. Model Confidence Check: Probability >= min_model_confidence
        min_conf = SCREENER_THRESHOLDS["min_model_confidence"]
        ml_prob = pred_result["buy_probability"]
        pass_confidence = bool(ml_prob >= min_conf)

        # 4. Momentum check: RSI not extremely overbought (> 78) and Supertrend bullish (+1)
        pass_momentum = bool(rsi_14 < 78 and supertrend_dir == 1)

        # Overall Safety Screen Pass
        is_safe_buy_candidate = bool(pass_trend and pass_liquidity and pass_confidence)

        # Trade Plan Calculation
        trade_plan = generate_trade_plan(close, atr_14)

        # Multi-factor Composite Score (0 to 100)
        # Factor 1: ML Probability (40 pts)
        score_ml = ml_prob * 40.0
        # Factor 2: Trend Alignment (30 pts: Above 20, 50, 200 EMAs and 50 > 200)
        score_trend = 0.0
        if close > ema_20: score_trend += 8.0
        if close > ema_50: score_trend += 10.0
        if close > ema_200: score_trend += 12.0
        # Factor 3: Volume & Momentum (20 pts)
        score_mom = 0.0
        if 45 <= rsi_14 <= 68: score_mom += 10.0
        elif 35 <= rsi_14 < 45: score_mom += 5.0
        if vol_ratio >= 1.2: score_mom += 10.0
        elif vol_ratio >= 1.0: score_mom += 6.0
        # Factor 4: Liquidity / Cap Quality (10 pts)
        score_liq = min(10.0, (turnover_cr / 50.0) * 10.0)

        composite_score = round(score_ml + score_trend + score_mom + score_liq, 1)

        # Company Name
        company_name = fundamentals.get("name") or symbol

        return {
            "symbol": symbol,
            "company_name": company_name,
            "sector": fundamentals.get("sector", "N/A"),
            "current_price": round(close, 2),
            "day_change_pct": round(float(latest_row["Return_1D"]) * 100, 2),
            "ml_probability": round(ml_prob, 4),
            "ml_probability_pct": round(ml_prob * 100, 2),
            "conviction": pred_result["conviction"],
            "signal_color": pred_result["signal_color"],
            "composite_score": composite_score,
            "filters": {
                "trend_filter": pass_trend,
                "liquidity_filter": pass_liquidity,
                "confidence_filter": pass_confidence,
                "momentum_filter": pass_momentum,
                "all_passed": is_safe_buy_candidate
            },
            "technical_indicators": {
                "rsi_14": round(rsi_14, 2),
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "ema_200": round(ema_200, 2),
                "atr_14": round(atr_14, 2),
                "vol_ratio": round(vol_ratio, 2),
                "turnover_cr": round(turnover_cr, 2),
                "supertrend": round(float(latest_row["Supertrend"]), 2),
                "supertrend_dir": "BULLISH" if supertrend_dir == 1 else "BEARISH",
                "macd": round(float(latest_row["MACD"]), 2),
                "macd_signal": round(float(latest_row["MACD_Signal"]), 2),
                "macd_hist": round(float(latest_row["MACD_Hist"]), 2)
            },
            "trade_plan": trade_plan,
            "fundamentals": fundamentals,
            "driving_features": pred_result["driving_features"],
            "model_diagnostics": pred_result["model_metrics"]
        }

    except Exception as e:
        logger.error(f"Error evaluating stock {symbol}: {e}", exc_info=False)
        return None


def run_full_screener(
    custom_symbols: Optional[List[str]] = None,
    universe_preset: str = "nifty50",
    limit_top_k: int = 10,
    user_capital: float = SCREENER_THRESHOLDS["default_capital"],
    max_workers: int = 6
) -> Dict[str, Any]:
    """
    Run quantitative multi-factor screener across Indian equities basket with multi-threaded parallel execution.
    Ranks candidates by composite quantitative score and generates tailored investment suggestions.
    """
    # Determine symbols to scan
    if custom_symbols and len(custom_symbols) > 0:
        symbols_to_scan = custom_symbols
        preset_info = {"name": "Custom Watchlist", "description": f"Custom selection of {len(symbols_to_scan)} stocks"}
    elif universe_preset in UNIVERSE_PRESETS:
        preset_data = UNIVERSE_PRESETS[universe_preset]
        symbols_to_scan = preset_data["symbols"]
        preset_info = {"name": preset_data["name"], "description": preset_data["description"]}
    else:
        # Default to Nifty 50 for fast snappy screening
        preset_data = UNIVERSE_PRESETS["nifty50"]
        symbols_to_scan = preset_data["symbols"]
        preset_info = {"name": preset_data["name"], "description": preset_data["description"]}

    logger.info(f"Running quantitative screener across {len(symbols_to_scan)} tickers in parallel (workers={max_workers})...")

    benchmark_df = fetch_benchmark_data(period="2y")
    evaluated_stocks: List[Dict[str, Any]] = []

    # Parallel evaluation with controlled concurrency to prevent rate limits
    import time
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sym = {}
        for sym in symbols_to_scan:
            future_to_sym[executor.submit(evaluate_single_stock, sym, benchmark_df)] = sym
            time.sleep(0.06)

        for future in as_completed(future_to_sym):
            sym = future_to_sym[future]
            try:
                res = future.result()
                if res is not None:
                    evaluated_stocks.append(res)
            except Exception as e:
                logger.warning(f"Error evaluating {sym} in parallel screener: {e}")


    # Sort all by composite score descending
    evaluated_stocks.sort(key=lambda x: x["composite_score"], reverse=True)

    # Top Buy Recommendations: Must pass all safety filters or have high ML confidence
    top_buys = [s for s in evaluated_stocks if s["filters"]["all_passed"]][:limit_top_k]
    
    # Fallback if fewer than 3 stocks pass all strict filters
    if len(top_buys) < 3:
        top_buys = [s for s in evaluated_stocks if s["filters"]["trend_filter"] and s["ml_probability"] >= 0.50][:limit_top_k]

    # Generate actionable investment recommendations
    investment_suggestions = generate_investment_suggestions(evaluated_stocks, user_capital=user_capital)

    return {
        "universe_preset": universe_preset,
        "preset_info": preset_info,
        "total_scanned": len(symbols_to_scan),
        "total_valid": len(evaluated_stocks),
        "top_buy_candidates": top_buys,
        "investment_suggestions": investment_suggestions,
        "all_screened_stocks": evaluated_stocks,
        "market_regime": {
            "benchmark": "^NSEI",
            "status": "BULLISH" if (not benchmark_df.empty and benchmark_df["Close"].iloc[-1] > benchmark_df["Close"].ewm(span=50).mean().iloc[-1]) else "NEUTRAL / SIDEWAYS"
        }
    }
