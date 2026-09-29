"""
Quantitative Feature Engineering Engine for Indian Equities.
Calculates technical indicators, momentum oscillators, trend/volatility metrics,
volume signals, market regime features, and directional classification targets.
"""

from typing import Tuple, List, Optional
import pandas as pd
import numpy as np

from backend.config import MODEL_PARAMS


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI) using Wilder's smoothing."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def calculate_stochastic(
    high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator %K and %D."""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    stoch_k = 100.0 * ((close - lowest_low) / (highest_high - lowest_low + 1e-10))
    stoch_d = stoch_k.rolling(window=d_period).mean()
    return stoch_k, stoch_d


def calculate_macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD Line, Signal Line, and Histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return atr


def calculate_bollinger_bands(
    series: pd.Series, period: int = 20, num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands (Upper, Middle, Lower, %B, Bandwidth)."""
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    pct_b = (series - lower) / (upper - lower + 1e-10)
    bandwidth = (upper - lower) / (middle + 1e-10)
    return upper, middle, lower, pct_b, bandwidth


def calculate_supertrend(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10, multiplier: float = 3.0
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Supertrend indicator.
    Returns:
        supertrend: Price level of supertrend
        direction: +1 for Bullish, -1 for Bearish
    """
    atr = calculate_atr(high, low, close, period=period)
    hl2 = (high + low) / 2.0

    basic_upper = hl2 + (multiplier * atr)
    basic_lower = hl2 - (multiplier * atr)

    n = len(close)
    final_upper = np.zeros(n)
    final_lower = np.zeros(n)
    supertrend = np.zeros(n)
    direction = np.zeros(n)

    close_arr = close.values
    basic_upper_arr = np.nan_to_num(basic_upper.values, nan=close_arr[0])
    basic_lower_arr = np.nan_to_num(basic_lower.values, nan=close_arr[0])

    final_upper[0] = basic_upper_arr[0]
    final_lower[0] = basic_lower_arr[0]
    direction[0] = 1
    supertrend[0] = final_lower[0]

    for i in range(1, n):
        # Final Upper Band
        if basic_upper_arr[i] < final_upper[i - 1] or close_arr[i - 1] > final_upper[i - 1]:
            final_upper[i] = basic_upper_arr[i]
        else:
            final_upper[i] = final_upper[i - 1]

        # Final Lower Band
        if basic_lower_arr[i] > final_lower[i - 1] or close_arr[i - 1] < final_lower[i - 1]:
            final_lower[i] = basic_lower_arr[i]
        else:
            final_lower[i] = final_lower[i - 1]

        # Supertrend and Direction
        if direction[i - 1] == 1:
            if close_arr[i] < final_lower[i]:
                direction[i] = -1
            else:
                direction[i] = 1
        else:
            if close_arr[i] > final_upper[i]:
                direction[i] = 1
            else:
                direction[i] = -1

        supertrend[i] = final_lower[i] if direction[i] == 1 else final_upper[i]

    return pd.Series(supertrend, index=close.index), pd.Series(direction, index=close.index)


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate On-Balance Volume (OBV)."""
    direction = np.sign(close.diff()).fillna(0)
    obv = (direction * volume).cumsum()
    return obv


def engineer_features(
    df: pd.DataFrame, 
    benchmark_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Transform raw OHLCV DataFrame into full quantitative feature matrix.
    Adds momentum, trend, volatility, volume, market regime features, and directional classification targets.
    """
    data = df.copy()

    # 1. Moving Averages
    data["EMA_20"] = data["Close"].ewm(span=20, adjust=False).mean()
    data["EMA_50"] = data["Close"].ewm(span=50, adjust=False).mean()
    data["EMA_200"] = data["Close"].ewm(span=200, adjust=False).mean()
    data["SMA_20"] = data["Close"].rolling(window=20).mean()

    # Trend ratios
    data["Price_to_EMA20"] = data["Close"] / (data["EMA_20"] + 1e-10) - 1.0
    data["Price_to_EMA50"] = data["Close"] / (data["EMA_50"] + 1e-10) - 1.0
    data["Price_to_EMA200"] = data["Close"] / (data["EMA_200"] + 1e-10) - 1.0
    data["EMA20_to_EMA50"] = data["EMA_20"] / (data["EMA_50"] + 1e-10) - 1.0
    data["EMA50_to_EMA200"] = data["EMA_50"] / (data["EMA_200"] + 1e-10) - 1.0

    # Trend slope (5-day slope of 50 EMA)
    data["EMA50_Slope"] = data["EMA_50"].pct_change(5)

    # 2. Momentum Indicators
    data["RSI_14"] = calculate_rsi(data["Close"], period=14)
    data["Stoch_K"], data["Stoch_D"] = calculate_stochastic(data["High"], data["Low"], data["Close"])
    data["MACD"], data["MACD_Signal"], data["MACD_Hist"] = calculate_macd(data["Close"])

    # 3. Volatility Indicators
    data["ATR_14"] = calculate_atr(data["High"], data["Low"], data["Close"], period=14)
    data["ATR_Pct"] = data["ATR_14"] / (data["Close"] + 1e-10)
    (
        data["BB_Upper"],
        data["BB_Middle"],
        data["BB_Lower"],
        data["BB_PctB"],
        data["BB_Bandwidth"],
    ) = calculate_bollinger_bands(data["Close"], period=20, num_std=2.0)

    # 4. Supertrend
    data["Supertrend"], data["Supertrend_Dir"] = calculate_supertrend(
        data["High"], data["Low"], data["Close"], period=10, multiplier=3.0
    )

    # 5. Volume Signals
    data["Vol_SMA20"] = data["Volume"].rolling(window=20).mean()
    data["Vol_Ratio"] = data["Volume"] / (data["Vol_SMA20"] + 1e-10)
    data["OBV"] = calculate_obv(data["Close"], data["Volume"])
    data["OBV_Slope"] = data["OBV"].pct_change(10).replace([np.inf, -np.inf], 0.0).fillna(0.0)

    # Turnover check (in INR Crores)
    if "Turnover_Cr" not in data.columns:
        data["Turnover_Cr"] = (data["Close"] * data["Volume"]) / 1e7
    data["Avg_Turnover_20D_Cr"] = data["Turnover_Cr"].rolling(window=20).mean()

    # 6. Returns & Price Action
    data["Return_1D"] = data["Close"].pct_change(1)
    data["Return_5D"] = data["Close"].pct_change(5)
    data["Return_10D"] = data["Close"].pct_change(10)
    data["Return_20D"] = data["Close"].pct_change(20)

    # High / Low Range Ratio
    data["HL_Range_Pct"] = (data["High"] - data["Low"]) / (data["Close"] + 1e-10)

    # 7. Market Regime / Relative Strength (using Nifty 50 if available)
    if benchmark_df is not None and not benchmark_df.empty:
        bench_close = benchmark_df["Close"].reindex(data.index).ffill()
        data["Nifty_Return_20D"] = bench_close.pct_change(20)
        data["Nifty_EMA50"] = bench_close.ewm(span=50, adjust=False).mean()
        data["Nifty_Bullish_Regime"] = (bench_close > data["Nifty_EMA50"]).astype(float)
        data["Relative_Strength_20D"] = data["Return_20D"] - data["Nifty_Return_20D"].fillna(0.0)
    else:
        data["Nifty_Bullish_Regime"] = 1.0
        data["Relative_Strength_20D"] = data["Return_20D"]

    # 8. Directional ML Target (Triple-Barrier Classification)
    # Target = 1 if max forward high in next N days >= profit_target_pct AND min forward low > stop_loss_limit_pct
    horizon = MODEL_PARAMS["holding_horizon_days"]
    target_profit = MODEL_PARAMS["profit_target_pct"]
    stop_limit = MODEL_PARAMS["stop_loss_limit_pct"]

    # Compute forward max high and min low over the next `horizon` sessions
    # Using rolling windows on reversed series or shifting forward
    indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=horizon)
    forward_max_high = data["High"].rolling(window=indexer).max()
    forward_min_low = data["Low"].rolling(window=indexer).min()
    forward_close = data["Close"].shift(-horizon)

    max_upside = (forward_max_high - data["Close"]) / data["Close"]
    max_downside = (forward_min_low - data["Close"]) / data["Close"]
    forward_return = (forward_close - data["Close"]) / data["Close"]

    data["Forward_Return"] = forward_return
    data["Max_Upside"] = max_upside
    data["Max_Downside"] = max_downside

    # Directional Target label
    target_condition = (max_upside >= target_profit) & (max_downside > stop_limit)
    data["Target"] = target_condition.astype(int)

    # Clean initial warm-up rows (e.g. 200 EMA needs ~200 days)
    # We do not dropna on Target yet because the latest rows are needed for live inference!
    return data


def get_feature_columns() -> List[str]:
    """Returns the standardized list of tabular features used by the ML model."""
    return [
        "Price_to_EMA20",
        "Price_to_EMA50",
        "Price_to_EMA200",
        "EMA20_to_EMA50",
        "EMA50_to_EMA200",
        "EMA50_Slope",
        "RSI_14",
        "Stoch_K",
        "Stoch_D",
        "MACD",
        "MACD_Signal",
        "MACD_Hist",
        "ATR_Pct",
        "BB_PctB",
        "BB_Bandwidth",
        "Supertrend_Dir",
        "Vol_Ratio",
        "OBV_Slope",
        "Return_1D",
        "Return_5D",
        "Return_10D",
        "Return_20D",
        "HL_Range_Pct",
        "Relative_Strength_20D",
        "Nifty_Bullish_Regime"
    ]
