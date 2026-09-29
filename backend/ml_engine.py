"""
Machine Learning & Predictive Engine for Indian Equities.
Trains and evaluates gradient boosting classifiers with strict Walk-Forward time-series validation.
Provides directional probabilities, feature importances, and model diagnostics.
"""

import os
import joblib
import logging
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

from backend.config import MODEL_PARAMS
from backend.feature_engineering import get_feature_columns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
MODEL_CACHE_DIR = os.path.join(CACHE_DIR, "models")
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

# In-memory model cache for fast API responses
_LOADED_MODELS: Dict[str, Any] = {}
_MODEL_METRICS_CACHE: Dict[str, Dict[str, Any]] = {}


def train_time_series_model(
    df: pd.DataFrame, 
    symbol: str, 
    retrain: bool = False
) -> Tuple[LGBMClassifier, Dict[str, Any]]:
    """
    Train LightGBM Classifier using strict chronological time-series split.
    Guarantees no future leakage (random shuffling strictly disallowed).
    """
    clean_sym = symbol.replace("^", "INDEX_").replace(".", "_")
    model_path = os.path.join(MODEL_CACHE_DIR, f"{clean_sym}_lgbm.joblib")
    metrics_path = os.path.join(MODEL_CACHE_DIR, f"{clean_sym}_metrics.joblib")

    # Return cached if valid and not forcing retrain
    if not retrain and clean_sym in _LOADED_MODELS and clean_sym in _MODEL_METRICS_CACHE:
        return _LOADED_MODELS[clean_sym], _MODEL_METRICS_CACHE[clean_sym]

    if not retrain and os.path.exists(model_path) and os.path.exists(metrics_path):
        try:
            model = joblib.load(model_path)
            metrics = joblib.load(metrics_path)
            _LOADED_MODELS[clean_sym] = model
            _MODEL_METRICS_CACHE[clean_sym] = metrics
            return model, metrics
        except Exception as e:
            logger.warning(f"Could not load cached model for {clean_sym}: {e}")

    feature_cols = get_feature_columns()

    # Drop rows that don't have valid features and labels
    # Warm-up period (first ~200 rows) or the last `holding_horizon_days` (where target is NaN)
    valid_data = df.dropna(subset=feature_cols + ["Target"]).copy()

    if len(valid_data) < 250:
        raise ValueError(f"Insufficient training samples for {symbol}: {len(valid_data)} rows. Need >= 250 rows.")

    X = valid_data[feature_cols]
    y = valid_data["Target"].astype(int)

    # Walk-Forward Chronological Split (80% train, 20% test)
    split_ratio = MODEL_PARAMS.get("train_test_split_ratio", 0.80)
    split_idx = int(len(valid_data) * split_ratio)

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # Class balance adjustment
    pos_count = (y_train == 1).sum()
    neg_count = (y_train == 0).sum()
    scale_pos_weight = (neg_count / max(1, pos_count)) if pos_count > 0 else 1.0

    model = LGBMClassifier(
        n_estimators=MODEL_PARAMS["n_estimators"],
        learning_rate=MODEL_PARAMS["learning_rate"],
        max_depth=MODEL_PARAMS["max_depth"],
        num_leaves=MODEL_PARAMS["num_leaves"],
        subsample=MODEL_PARAMS["subsample"],
        colsample_bytree=MODEL_PARAMS["colsample_bytree"],
        min_child_samples=MODEL_PARAMS["min_child_samples"],
        scale_pos_weight=scale_pos_weight,
        random_state=MODEL_PARAMS["random_state"],
        verbose=-1
    )

    model.fit(X_train, y_train)

    # Evaluate on out-of-sample Test Data
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_test, y_prob)
    except Exception:
        auc = 0.50

    cm = confusion_matrix(y_test, y_pred).tolist()

    # Feature Importance ranking
    raw_importances = model.feature_importances_
    total_imp = np.sum(raw_importances) + 1e-10
    feature_importance_list = [
        {"feature": feat, "importance": round(float(imp / total_imp * 100), 2)}
        for feat, imp in zip(feature_cols, raw_importances)
    ]
    feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)

    metrics_result = {
        "symbol": symbol,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "base_rate_pct": round(float((y_test == 1).mean() * 100), 2),
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(auc), 4),
        "confusion_matrix": cm,
        "feature_importances": feature_importance_list
    }

    # Persist
    try:
        joblib.dump(model, model_path)
        joblib.dump(metrics_result, metrics_path)
    except Exception as e:
        logger.warning(f"Failed to persist model cache: {e}")

    _LOADED_MODELS[clean_sym] = model
    _MODEL_METRICS_CACHE[clean_sym] = metrics_result

    return model, metrics_result


def predict_latest_setup(
    df: pd.DataFrame, 
    symbol: str, 
    model: Optional[LGBMClassifier] = None,
    metrics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate directional probability and conviction signal for the most recent session.
    """
    feature_cols = get_feature_columns()

    # Find the latest row with all features calculated
    sub_df = df.dropna(subset=feature_cols)
    if sub_df.empty:
        raise ValueError(f"No valid feature row available for inference on {symbol}")

    latest_row = sub_df.iloc[[-1]]
    latest_date = str(latest_row.index[-1].strftime("%Y-%m-%d") if hasattr(latest_row.index[-1], "strftime") else latest_row.index[-1])
    current_close = float(latest_row["Close"].values[0])

    if model is None or metrics is None:
        model, metrics = train_time_series_model(df, symbol)

    X_latest = latest_row[feature_cols]
    prob_class1 = float(model.predict_proba(X_latest)[0][1])

    # Categorize Conviction
    if prob_class1 >= 0.70:
        conviction = "STRONG BUY"
        signal_color = "#10b981"  # Emerald
    elif prob_class1 >= 0.60:
        conviction = "BUY"
        signal_color = "#34d399"  # Light Emerald
    elif prob_class1 >= 0.45:
        conviction = "NEUTRAL / ACCUMULATE"
        signal_color = "#f59e0b"  # Amber
    else:
        conviction = "AVOID / BEARISH"
        signal_color = "#ef4444"  # Rose Red

    # Latest individual feature values for explanation
    latest_feature_values = []
    top_feats = metrics.get("feature_importances", [])[:7]
    for item in top_feats:
        fname = item["feature"]
        fval = float(latest_row[fname].values[0])
        latest_feature_values.append({
            "feature": fname,
            "importance_pct": item["importance"],
            "current_value": round(fval, 3)
        })

    return {
        "symbol": symbol,
        "as_of_date": latest_date,
        "close_price": round(current_close, 2),
        "buy_probability": round(prob_class1, 4),
        "buy_probability_pct": round(prob_class1 * 100, 2),
        "conviction": conviction,
        "signal_color": signal_color,
        "model_metrics": metrics,
        "driving_features": latest_feature_values
    }
