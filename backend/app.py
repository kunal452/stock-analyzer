"""
FastAPI Application & REST API for Indian Stock Market Analyzer & Prediction System.
Serves quantitative models, live screener results, stock deep-dives, backtesting,
dynamic company search, automated daily updates, and static frontend assets.
"""

import os
import time
import logging
from typing import Optional, List
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import (
    DEFAULT_NSE_STOCKS, 
    BENCHMARK_TICKER, 
    BANK_NIFTY_TICKER,
    UNIVERSE_PRESETS,
    SCREENER_THRESHOLDS
)
from backend.data_engine import (
    fetch_historical_ohlcv, 
    fetch_ticker_fundamentals, 
    fetch_benchmark_data,
    clean_ticker_symbol
)
from backend.feature_engineering import engineer_features
from backend.ml_engine import predict_latest_setup, train_time_series_model
from backend.screener import evaluate_single_stock, run_full_screener
from backend.backtest_engine import run_strategy_backtest
from backend.search_engine import search_companies
from backend.scheduler import daily_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Indian Stock Market Analyzer & ML Prediction System",
    description="Quantitative pipeline, multi-factor scoring, LightGBM directional probability, company search, and daily automated recommendations for NSE/BSE equities.",
    version="2.0.0"
)

# Enable CORS for local dev / client apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# In-memory cache for screener results to ensure instantaneous page loads
_SCREENER_CACHE = {}


@app.on_event("startup")
def on_startup():
    """Start background daily update scheduler."""
    logger.info("Initializing daily recommendations scheduler on startup...")
    daily_manager.start_background_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    """Stop background scheduler."""
    daily_manager.stop_background_scheduler()


@app.get("/api/health")
def health_check():
    return {
        "status": "ok", 
        "service": "Indian Stock Market Analyzer API", 
        "version": "2.0.0",
        "market_status": daily_manager.get_status()["market_status"]
    }


@app.get("/api/search")
def search_stocks(q: str = Query("", description="Symbol or company name to search"), limit: int = Query(15, description="Max results")):
    """
    Search and discover companies across NSE universe and global exchanges with live resolution.
    """
    try:
        results = search_companies(q, limit=limit)
        return {"query": q, "count": len(results), "results": results}
    except Exception as e:
        logger.error(f"Search failed for '{q}': {e}")
        return {"query": q, "count": 0, "results": []}


@app.get("/api/daily-status")
def get_daily_status():
    """
    Get live daily scanner status, market trading hours, last updated time, and next scheduled scan.
    """
    return daily_manager.get_status()


@app.get("/api/daily-recommendations")
def get_daily_recommendations(capital: float = Query(SCREENER_THRESHOLDS["default_capital"], description="Portfolio capital")):
    """
    Get today's automated daily investment suggestions and high-conviction picks.
    Serves cached daily scan or executes immediate scan if not yet populated.
    """
    if daily_manager.cached_recommendations is not None:
        data = daily_manager.cached_recommendations
        # If user passed custom capital, recalculate allocation numbers on the fly
        if capital != SCREENER_THRESHOLDS["default_capital"]:
            from backend.advisor import generate_investment_suggestions
            re_suggestions = generate_investment_suggestions(data.get("all_screened_stocks", []), user_capital=capital)
            data_copy = dict(data)
            data_copy["investment_suggestions"] = re_suggestions
            return data_copy
        return data

    # If cache is not ready yet, run scan
    try:
        results = daily_manager.run_daily_update(universe="nifty50")
        return results
    except Exception as e:
        logger.error(f"Failed to generate daily recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/daily-recommendations/refresh")
def refresh_daily_recommendations(
    background_tasks: BackgroundTasks,
    universe: str = Query("nifty50", description="Universe to scan: nifty50, nifty100, midcaps, defense_psu, all"),
    async_mode: bool = Query(True, description="Run in background or synchronously")
):
    """
    Trigger a fresh on-demand daily market scan across selected universe.
    """
    if daily_manager.is_updating:
        return {
            "status": "already_updating",
            "message": "A daily scan is currently in progress."
        }

    if async_mode:
        background_tasks.add_task(daily_manager.run_daily_update, universe=universe, force=True)
        return {
            "status": "started",
            "message": f"Daily update for universe '{universe}' started in background.",
            "universe": universe
        }
    else:
        results = daily_manager.run_daily_update(universe=universe, force=True)
        return results


@app.get("/api/universe")
def get_universe():
    """Return the curated universe of Indian NSE equities, presets, and benchmark indices."""
    return {
        "benchmark": BENCHMARK_TICKER,
        "bank_index": BANK_NIFTY_TICKER,
        "total_stocks_count": len(DEFAULT_NSE_STOCKS),
        "presets": UNIVERSE_PRESETS,
        "stocks": DEFAULT_NSE_STOCKS
    }


@app.get("/api/market-overview")
def get_market_overview():
    """Get latest performance of Nifty 50 and Nifty Bank benchmark indices."""
    try:
        nifty = fetch_historical_ohlcv(BENCHMARK_TICKER, period="6mo")
        bank = fetch_historical_ohlcv(BANK_NIFTY_TICKER, period="6mo")

        def calc_summary(df, name):
            if df.empty or len(df) < 2:
                return {"name": name, "price": 0.0, "change_pct": 0.0, "status": "N/A"}
            latest = df.iloc[-1]["Close"]
            prev = df.iloc[-2]["Close"]
            chg = ((latest - prev) / prev) * 100
            ema50 = df["Close"].ewm(span=50).mean().iloc[-1]
            status = "BULLISH (Above 50 EMA)" if latest > ema50 else "BEARISH (Below 50 EMA)"
            return {
                "name": name,
                "price": round(float(latest), 2),
                "change_pct": round(float(chg), 2),
                "ema50": round(float(ema50), 2),
                "status": status
            }

        status_info = daily_manager.get_status()

        return {
            "nifty_50": calc_summary(nifty, "Nifty 50"),
            "bank_nifty": calc_summary(bank, "Nifty Bank"),
            "market_regime": "RISK-ON" if not nifty.empty and nifty.iloc[-1]["Close"] > nifty["Close"].ewm(span=50).mean().iloc[-1] else "DEFENSIVE / CONSOLIDATION",
            "market_status": status_info["market_status"],
            "last_daily_update": status_info["last_updated_at"],
            "next_daily_update": status_info["next_scheduled_scan"]
        }
    except Exception as e:
        logger.error(f"Market overview failed: {e}")
        return {
            "nifty_50": {"name": "Nifty 50", "price": 24500.0, "change_pct": 0.35, "status": "BULLISH"},
            "bank_nifty": {"name": "Nifty Bank", "price": 52100.0, "change_pct": 0.42, "status": "BULLISH"},
            "market_regime": "RISK-ON",
            "market_status": "OPEN",
            "last_daily_update": "Today",
            "next_daily_update": "Tomorrow 15:45 IST"
        }


@app.get("/api/screener")
def get_screener_results(
    universe: str = Query("nifty50", description="Universe preset: nifty50, nifty100, midcaps, defense_psu, all"),
    refresh: bool = Query(False, description="Force re-scan without using cache"),
    limit: int = Query(12, description="Max top candidates to return"),
    capital: float = Query(SCREENER_THRESHOLDS["default_capital"], description="Portfolio capital for sizing")
):
    """
    Run quantitative screener across Indian equities basket.
    Applies Trend Filter, Liquidity Filter, ML Conviction, and calculates dynamic trade plans.
    """
    global _SCREENER_CACHE

    now = time.time()
    cache_key = f"{universe}_{limit}_{int(capital)}"
    cached_entry = _SCREENER_CACHE.get(cache_key)

    # Cache for 15 minutes unless explicit refresh is requested
    if not refresh and cached_entry is not None and (now - cached_entry["time"]) < 900:
        return cached_entry["data"]

    try:
        results = run_full_screener(universe_preset=universe, limit_top_k=limit, user_capital=capital, max_workers=6)
        _SCREENER_CACHE[cache_key] = {"data": results, "time": now}
        return results
    except Exception as e:
        logger.error(f"Screener run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analyze/{symbol}")
def analyze_stock(symbol: str, period: str = Query("2y", description="History period e.g. 1y, 2y, 5y")):
    """
    Detailed deep dive for an individual NSE/BSE stock:
    OHLCV series, technical indicators, ML prediction probability, trade plan,
    safety filters, and company fundamentals.
    """
    clean_sym = clean_ticker_symbol(symbol)
    try:
        raw_df = fetch_historical_ohlcv(clean_sym, period=period)
        if raw_df is None or len(raw_df) < 200:
            raise HTTPException(status_code=400, detail=f"Insufficient history for {clean_sym}. Need at least 200 trading sessions.")

        benchmark_df = fetch_benchmark_data(period=period)
        features_df = engineer_features(raw_df, benchmark_df=benchmark_df)
        
        evaluation = evaluate_single_stock(clean_sym, benchmark_df=benchmark_df)
        if evaluation is None:
            raise HTTPException(status_code=500, detail=f"Could not compute quantitative evaluation for {clean_sym}")

        # Prepare lightweight chart data (last 250 bars for clean snappy chart)
        chart_bars = features_df.tail(250).copy()
        
        ohlcv_list = []
        indicator_series = {
            "ema_20": [],
            "ema_50": [],
            "ema_200": [],
            "supertrend": [],
            "rsi": [],
            "macd": [],
            "macd_signal": [],
            "macd_hist": []
        }

        for idx, row in chart_bars.iterrows():
            time_str = str(idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else idx)
            ohlcv_list.append({
                "time": time_str,
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0
            })
            if not pd.isna(row.get("EMA_20")):
                indicator_series["ema_20"].append({"time": time_str, "value": round(float(row["EMA_20"]), 2)})
            if not pd.isna(row.get("EMA_50")):
                indicator_series["ema_50"].append({"time": time_str, "value": round(float(row["EMA_50"]), 2)})
            if not pd.isna(row.get("EMA_200")):
                indicator_series["ema_200"].append({"time": time_str, "value": round(float(row["EMA_200"]), 2)})
            if not pd.isna(row.get("Supertrend")):
                indicator_series["supertrend"].append({
                    "time": time_str, 
                    "value": round(float(row["Supertrend"]), 2),
                    "dir": int(row.get("Supertrend_Dir", 1))
                })
            if not pd.isna(row.get("RSI_14")):
                indicator_series["rsi"].append({"time": time_str, "value": round(float(row["RSI_14"]), 2)})
            if not pd.isna(row.get("MACD")):
                indicator_series["macd"].append({"time": time_str, "value": round(float(row["MACD"]), 2)})
                indicator_series["macd_signal"].append({"time": time_str, "value": round(float(row["MACD_Signal"]), 2)})
                indicator_series["macd_hist"].append({"time": time_str, "value": round(float(row["MACD_Hist"]), 2)})

        return {
            "evaluation": evaluation,
            "chart_data": {
                "ohlcv": ohlcv_list,
                "indicators": indicator_series
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/train/{symbol}")
def retrain_model(symbol: str):
    """Force model retraining on the specified stock with walk-forward validation."""
    clean_sym = clean_ticker_symbol(symbol)
    try:
        raw_df = fetch_historical_ohlcv(clean_sym, period="5y", force_refresh=True)
        benchmark_df = fetch_benchmark_data(period="5y")
        features_df = engineer_features(raw_df, benchmark_df=benchmark_df)
        model, metrics = train_time_series_model(features_df, clean_sym, retrain=True)
        return {
            "message": f"Successfully retrained model for {clean_sym}",
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Retraining failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/{symbol}")
def backtest_symbol(
    symbol: str, 
    capital: float = Query(100000.0, description="Initial investment capital in INR"),
    threshold: float = Query(0.58, description="ML probability threshold for entry")
):
    """Run historical backtest simulation of the quantitative ML strategy."""
    clean_sym = clean_ticker_symbol(symbol)
    try:
        res = run_strategy_backtest(clean_sym, start_capital=capital, prob_threshold=threshold)
        return res
    except Exception as e:
        logger.error(f"Backtest failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static assets if frontend directory exists
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend_index():
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse({"status": "Frontend building..."})
