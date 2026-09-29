"""
Data Ingestion and Caching Engine for Indian Equities (NSE/BSE).
Fetches historical daily OHLCV and fundamental metrics using yfinance with disk-caching.
"""

import os
import json
import time
import logging
from typing import Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
import yfinance as yf

from backend.config import BENCHMARK_TICKER, DEFAULT_NSE_STOCKS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)
DATA_CACHE_DIR = os.path.join(CACHE_DIR, "data")
INFO_CACHE_DIR = os.path.join(CACHE_DIR, "info")
os.makedirs(DATA_CACHE_DIR, exist_ok=True)
os.makedirs(INFO_CACHE_DIR, exist_ok=True)

# Cache expiry in seconds (e.g. 4 hours during market days, or 12 hours)
CACHE_EXPIRY_SECONDS = 14400


def clean_ticker_symbol(symbol: str) -> str:
    """Normalize Indian stock symbol to include .NS suffix if not provided."""
    s = symbol.strip().upper()
    if not (s.startswith("^") or s.endswith(".NS") or s.endswith(".BO")):
        s = f"{s}.NS"
    return s


def fetch_historical_ohlcv(
    symbol: str, 
    period: str = "5y", 
    interval: str = "1d",
    force_refresh: bool = False
) -> pd.DataFrame:
    """
    Fetch historical OHLCV data from yfinance with disk caching.
    Ensures single-level columns and datetime index.
    """
    clean_sym = clean_ticker_symbol(symbol)
    safe_name = clean_sym.replace("^", "INDEX_").replace(".", "_")
    cache_file = os.path.join(DATA_CACHE_DIR, f"{safe_name}_{period}_{interval}.joblib")

    # Check cache freshness
    if not force_refresh and os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        if (time.time() - mtime) < CACHE_EXPIRY_SECONDS:
            try:
                import joblib
                df = joblib.load(cache_file)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"Failed to read cache for {clean_sym}: {e}")

    logger.info(f"Ingesting OHLCV data for {clean_sym} (period={period})...")
    raw_df = None
    for attempt in range(2):
        try:
            # Try ticker history first or download
            t = yf.Ticker(clean_sym)
            raw_df = t.history(period=period, interval=interval, auto_adjust=True)
            if raw_df is None or raw_df.empty:
                raw_df = yf.download(clean_sym, period=period, interval=interval, progress=False, auto_adjust=True)
            if raw_df is not None and not raw_df.empty and len(raw_df) > 10:
                break
        except Exception as e:
            if attempt == 0:
                time.sleep(0.5)
            else:
                logger.warning(f"Fetch attempt {attempt+1} failed for {clean_sym}: {e}")

    if raw_df is None or raw_df.empty:
        # Fallback to cache if available
        if os.path.exists(cache_file):
            logger.info(f"Using cache fallback for {clean_sym}")
            import joblib
            return joblib.load(cache_file)
        raise ValueError(f"No OHLCV data returned for symbol {clean_sym}")

    try:
        # Flatten multi-index columns if present
        if isinstance(raw_df.columns, pd.MultiIndex):
            raw_df.columns = raw_df.columns.get_level_values(0)

        # Standardize column names
        cols = {c: c.capitalize() for c in raw_df.columns}
        raw_df = raw_df.rename(columns=cols)

        # Ensure required columns exist
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        for rc in required_cols:
            if rc not in raw_df.columns:
                raise ValueError(f"Missing required price column {rc} in data for {clean_sym}")

        # Sort and clean index
        raw_df = raw_df.sort_index()
        raw_df = raw_df[~raw_df.index.duplicated(keep="last")]
        raw_df = raw_df.dropna(subset=["Close"])

        # Compute turnover in INR Crores (1 Crore = 10,000,000 INR)
        raw_df["Turnover_Cr"] = (raw_df["Close"] * raw_df["Volume"]) / 1e7

        # Save to joblib cache
        try:
            import joblib
            joblib.dump(raw_df, cache_file)
        except Exception as e:
            logger.warning(f"Could not write cache for {clean_sym}: {e}")

        return raw_df

    except Exception as e:
        logger.error(f"Error processing data for {clean_sym}: {e}")
        if os.path.exists(cache_file):
            import joblib
            return joblib.load(cache_file)
        raise



def fetch_benchmark_data(period: str = "5y") -> pd.DataFrame:
    """Fetch Nifty 50 benchmark data for regime detection and beta calculation."""
    try:
        return fetch_historical_ohlcv(BENCHMARK_TICKER, period=period)
    except Exception as e:
        logger.warning(f"Benchmark fetch failed ({e}). Proceeding without market regime sync.")
        return pd.DataFrame()


def fetch_ticker_fundamentals(symbol: str) -> Dict[str, Any]:
    """
    Fetch fundamental metrics, market cap, and valuation filters.
    Caches info to JSON to minimize yfinance API overhead.
    """
    clean_sym = clean_ticker_symbol(symbol)
    safe_name = clean_sym.replace("^", "INDEX_").replace(".", "_")
    cache_file = os.path.join(INFO_CACHE_DIR, f"{safe_name}.json")

    # Read from cache if recent
    if os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        if (time.time() - mtime) < (CACHE_EXPIRY_SECONDS * 2):
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass

    result: Dict[str, Any] = {
        "symbol": clean_sym,
        "name": clean_sym,
        "sector": "N/A",
        "industry": "N/A",
        "pe_ratio": None,
        "forward_pe": None,
        "peg_ratio": None,
        "market_cap_cr": None,
        "pb_ratio": None,
        "roe": None,
        "debt_to_equity": None,
        "week_52_high": None,
        "week_52_low": None,
        "dividend_yield": None,
        "currency": "INR"
    }

    # Match predefined sector/name if in default universe
    for s in DEFAULT_NSE_STOCKS:
        if s["symbol"] == clean_sym:
            result["name"] = s["name"]
            result["sector"] = s["sector"]
            break

    try:
        t = yf.Ticker(clean_sym)
        info = t.info or {}

        if info:
            result["name"] = info.get("shortName") or info.get("longName") or result["name"]
            result["sector"] = info.get("sector") or result["sector"]
            result["industry"] = info.get("industry") or result["industry"]
            result["pe_ratio"] = info.get("trailingPE")
            result["forward_pe"] = info.get("forwardPE")
            result["peg_ratio"] = info.get("pegRatio")
            
            raw_mc = info.get("marketCap")
            if raw_mc:
                result["market_cap_cr"] = round(raw_mc / 1e7, 2)
                
            result["pb_ratio"] = info.get("priceToBook")
            result["roe"] = info.get("returnOnEquity")
            result["debt_to_equity"] = info.get("debtToEquity")
            result["week_52_high"] = info.get("fiftyTwoWeekHigh")
            result["week_52_low"] = info.get("fiftyTwoWeekLow")
            result["dividend_yield"] = info.get("dividendYield")

        # Cache valid result
        with open(cache_file, "w") as f:
            json.dump(result, f, indent=2)

    except Exception as e:
        logger.warning(f"Could not fetch fundamentals for {clean_sym}: {e}")

    return result
