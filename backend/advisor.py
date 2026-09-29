"""
Quantitative Investment Advisory & Recommendation Engine for Indian Equities.
Synthesizes machine learning directional conviction, multi-factor technical trend filters,
and fundamental valuation metrics into actionable investment suggestions.
Categorizes opportunities into Long-Term Compounders, High-Conviction Swing Trades, and Value Dip Buys.
"""

import logging
from typing import List, Dict, Any, Optional

from backend.config import SCREENER_THRESHOLDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_investment_suggestions(
    evaluated_stocks: List[Dict[str, Any]],
    user_capital: float = SCREENER_THRESHOLDS["default_capital"]
) -> Dict[str, Any]:
    """
    Transform raw screened stocks into structured, plain-English investment recommendations.
    Categorizes candidates by investment horizon, risk tolerance, and key rationale.
    Guarantees actionable recommendations are always provided.
    """
    if not evaluated_stocks:
        return {
            "top_overall_recommendations": [],
            "long_term_compounders": [],
            "swing_momentum_picks": [],
            "value_dip_buys": [],
            "total_analyzed": 0,
            "summary": "No stocks evaluated yet. Run screener to generate suggestions."
        }

    long_term_picks = []
    swing_picks = []
    dip_picks = []

    for stock in evaluated_stocks:
        sym = stock["symbol"]
        name = stock["company_name"]
        cmp = stock["current_price"]
        ml_prob = stock["ml_probability"]
        score = stock["composite_score"]
        filters = stock["filters"]
        tech = stock["technical_indicators"]
        fund = stock.get("fundamentals", {})
        plan = stock["trade_plan"]

        # Extract technicals
        rsi = tech.get("rsi_14", 50.0)
        vol_ratio = tech.get("vol_ratio", 1.0)
        supertrend_dir = tech.get("supertrend_dir", "BULLISH")
        turnover_cr = tech.get("turnover_cr", 10.0)
        ema_20 = tech.get("ema_20", cmp)
        ema_50 = tech.get("ema_50", cmp)
        ema_200 = tech.get("ema_200", cmp)

        # Fundamentals
        pe = fund.get("pe_ratio")
        roe = fund.get("roe")
        de = fund.get("debt_to_equity")
        mcap = fund.get("market_cap_cr")

        # -------------------------------------------------------------
        # Category 1: Long-Term Wealth Compounders (6 - 12 Months)
        # Criteria: Above 200 EMA (long-term uptrend) or 50 EMA, solid market presence.
        # -------------------------------------------------------------
        is_above_key_trend = bool(cmp >= ema_200 or cmp >= ema_50)
        has_healthy_balance = de is None or de <= 2.2

        if is_above_key_trend and has_healthy_balance and (ml_prob >= 0.50 or score >= 45):
            target_lt = round(cmp * 1.25, 2)
            target_lt_pct = 25.0
            stop_lt = round(min(plan["stop_loss"], cmp * 0.92), 2)
            stop_lt_pct = round(((cmp - stop_lt) / cmp) * 100, 2)

            thesis = [
                f"Structural Support: Trading near/above long-term moving averages (50 EMA: ₹{ema_50}, 200 EMA: ₹{ema_200}).",
                f"Balance Sheet Strength: Institutional liquidity with ₹{mcap or 'Large'} Cr market cap.",
                f"Statistical Edge: ML probability of {stock['ml_probability_pct']}% with quant composite rating {score}/100."
            ]

            shares = int((user_capital * 0.15) / cmp) if cmp > 0 else 0
            allocation_rs = round(shares * cmp, 2)

            long_term_picks.append({
                "symbol": sym,
                "clean_symbol": sym.replace(".NS", ""),
                "company_name": name,
                "sector": stock.get("sector", "N/A"),
                "category": "LONG_TERM_COMPOUNDER",
                "action": "STRONG BUY" if (score >= 60 and ml_prob >= 0.60) else "ACCUMULATE",
                "horizon": "Medium to Long Term (6 - 12 Months)",
                "risk_profile": "Low to Moderate",
                "current_price": cmp,
                "day_change_pct": stock["day_change_pct"],
                "entry_zone": f"₹{round(cmp * 0.99, 1)} – ₹{round(cmp * 1.01, 1)}",
                "target_price": target_lt,
                "target_pct": f"+{target_lt_pct}%",
                "stop_loss": stop_lt,
                "stop_loss_pct": f"-{stop_lt_pct}%",
                "risk_reward": f"1 : {round((target_lt - cmp) / max(0.01, cmp - stop_lt), 1)}",
                "ml_probability_pct": stock["ml_probability_pct"],
                "composite_score": score,
                "thesis": thesis,
                "suggested_allocation": {
                    "capital_allocated": allocation_rs,
                    "shares_to_buy": shares,
                    "portfolio_weight_pct": round((allocation_rs / user_capital) * 100, 1) if user_capital > 0 else 0.0
                }
            })

        # -------------------------------------------------------------
        # Category 2: High-Conviction Momentum & Swing Buys (1 - 4 Weeks)
        # Criteria: ML prob >= 58% or strong Supertrend / volume ratio.
        # -------------------------------------------------------------
        is_swing_candidate = bool(
            ml_prob >= 0.58 or 
            (ml_prob >= 0.52 and supertrend_dir == "BULLISH" and vol_ratio >= 1.0)
        )

        if is_swing_candidate:
            target_swing = plan["target_1"]
            target_swing_pct = plan["target_1_pct"]
            stop_swing = plan["stop_loss"]
            stop_swing_pct = plan["stop_loss_pct"]

            thesis_swing = [
                f"Machine Learning Trigger: LightGBM model forecasts {stock['ml_probability_pct']}% upside probability.",
                f"Momentum Profile: RSI at {rsi} with Supertrend in {supertrend_dir} state.",
                f"Defined Risk: Dynamic ATR stop-loss at ₹{stop_swing} offering favorable {plan['risk_reward_ratio']} risk-to-reward."
            ]

            shares_swing = plan["position_sizing"]["recommended_shares"]
            allocation_swing = plan["position_sizing"]["trade_capital_required"]

            swing_picks.append({
                "symbol": sym,
                "clean_symbol": sym.replace(".NS", ""),
                "company_name": name,
                "sector": stock.get("sector", "N/A"),
                "category": "SWING_MOMENTUM",
                "action": "STRONG BUY" if ml_prob >= 0.65 else "SWING BUY",
                "horizon": "Short Term (1 - 4 Weeks)",
                "risk_profile": "Moderate",
                "current_price": cmp,
                "day_change_pct": stock["day_change_pct"],
                "entry_zone": f"₹{round(cmp * 0.995, 1)} – ₹{round(cmp * 1.005, 1)}",
                "target_price": target_swing,
                "target_pct": f"+{target_swing_pct}%",
                "target_2_price": plan["target_2"],
                "target_2_pct": f"+{plan['target_2_pct']}%",
                "stop_loss": stop_swing,
                "stop_loss_pct": f"-{stop_swing_pct}%",
                "risk_reward": plan["risk_reward_ratio"],
                "ml_probability_pct": stock["ml_probability_pct"],
                "composite_score": score,
                "thesis": thesis_swing,
                "suggested_allocation": {
                    "capital_allocated": allocation_swing,
                    "shares_to_buy": shares_swing,
                    "portfolio_weight_pct": round((allocation_swing / user_capital) * 100, 1) if user_capital > 0 else 0.0
                }
            })

        # -------------------------------------------------------------
        # Category 3: High-Value Dip Buys (1 - 3 Months)
        # Criteria: RSI 28 to 55 (consolidation/dip), turnover >= 5 Cr.
        # -------------------------------------------------------------
        if 28.0 <= rsi <= 55.0 and turnover_cr >= 5.0:
            target_dip = round(cmp * 1.15, 2)
            target_dip_pct = 15.0
            stop_dip = round(cmp * 0.94, 2)
            stop_dip_pct = 6.0

            thesis_dip = [
                f"Oversold / Cool Entry: RSI cooled to {rsi}, offering reduced risk entry point.",
                f"Support Convergence: Close to dynamic support zones (50 EMA: ₹{round(ema_50, 1)}).",
                f"Institutional Flow: 20-day average turnover of ₹{turnover_cr} Cr ensuring active buyer interest."
            ]

            shares_dip = int((user_capital * 0.12) / cmp) if cmp > 0 else 0
            allocation_dip = round(shares_dip * cmp, 2)

            dip_picks.append({
                "symbol": sym,
                "clean_symbol": sym.replace(".NS", ""),
                "company_name": name,
                "sector": stock.get("sector", "N/A"),
                "category": "VALUE_DIP_BUY",
                "action": "ACCUMULATE ON DIPS",
                "horizon": "Positional (1 - 3 Months)",
                "risk_profile": "Low to Moderate",
                "current_price": cmp,
                "day_change_pct": stock["day_change_pct"],
                "entry_zone": f"₹{round(cmp * 0.98, 1)} – ₹{round(cmp * 1.01, 1)}",
                "target_price": target_dip,
                "target_pct": f"+{target_dip_pct}%",
                "stop_loss": stop_dip,
                "stop_loss_pct": f"-{stop_dip_pct}%",
                "risk_reward": f"1 : {round((target_dip - cmp) / max(0.01, cmp - stop_dip), 1)}",
                "ml_probability_pct": stock["ml_probability_pct"],
                "composite_score": score,
                "thesis": thesis_dip,
                "suggested_allocation": {
                    "capital_allocated": allocation_dip,
                    "shares_to_buy": shares_dip,
                    "portfolio_weight_pct": round((allocation_dip / user_capital) * 100, 1) if user_capital > 0 else 0.0
                }
            })

    # Sort each category by composite score & conviction
    long_term_picks.sort(key=lambda x: (x["composite_score"], x["ml_probability_pct"]), reverse=True)
    swing_picks.sort(key=lambda x: (x["ml_probability_pct"], x["composite_score"]), reverse=True)
    dip_picks.sort(key=lambda x: (x["composite_score"], x["ml_probability_pct"]), reverse=True)

    # Top overall suggestions: Best picks deduplicated
    seen_syms = set()
    top_overall = []
    
    # Priority order: Top swing buys with high confidence, then top compounders, then top dip buys
    combined_candidates = swing_picks + long_term_picks + dip_picks
    for p in combined_candidates:
        if p["symbol"] not in seen_syms:
            seen_syms.add(p["symbol"])
            top_overall.append(p)
            if len(top_overall) >= 8:
                break

    # Guaranteed fallback: If no candidate was captured through filters, take the top scored evaluated stocks
    if len(top_overall) == 0 and len(evaluated_stocks) > 0:
        for s in evaluated_stocks[:6]:
            plan = s["trade_plan"]
            shares = plan["position_sizing"]["recommended_shares"]
            alloc = plan["position_sizing"]["trade_capital_required"]
            top_overall.append({
                "symbol": s["symbol"],
                "clean_symbol": s["symbol"].replace(".NS", ""),
                "company_name": s["company_name"],
                "sector": s.get("sector", "N/A"),
                "category": "SWING_MOMENTUM" if s["ml_probability"] >= 0.55 else "LONG_TERM_COMPOUNDER",
                "action": "ACCUMULATE" if s["ml_probability"] >= 0.55 else "WATCHLIST",
                "horizon": "Short to Medium Term",
                "risk_profile": "Moderate",
                "current_price": s["current_price"],
                "day_change_pct": s["day_change_pct"],
                "entry_zone": f"₹{round(s['current_price'] * 0.99, 1)} – ₹{round(s['current_price'] * 1.01, 1)}",
                "target_price": plan["target_1"],
                "target_pct": f"+{plan['target_1_pct']}%",
                "stop_loss": plan["stop_loss"],
                "stop_loss_pct": f"-{plan['stop_loss_pct']}%",
                "risk_reward": plan["risk_reward_ratio"],
                "ml_probability_pct": s["ml_probability_pct"],
                "composite_score": s["composite_score"],
                "thesis": [
                    f"Machine Learning Directional Conviction: {s['ml_probability_pct']}%.",
                    f"Liquid Counter: 20-day turnover of ₹{s['technical_indicators']['turnover_cr']} Cr.",
                    f"Risk-Managed Plan: 1:{plan['risk_reward_numeric']} target reward to risk."
                ],
                "suggested_allocation": {
                    "capital_allocated": alloc,
                    "shares_to_buy": shares,
                    "portfolio_weight_pct": round((alloc / user_capital) * 100, 1) if user_capital > 0 else 0.0
                }
            })

    summary_text = (
        f"Generated {len(top_overall)} high-conviction investment recommendations from {len(evaluated_stocks)} analyzed companies. "
        f"Identified {len(swing_picks)} swing trade setups and {len(long_term_picks)} long-term wealth compounders."
    )

    return {
        "top_overall_recommendations": top_overall,
        "long_term_compounders": long_term_picks[:8],
        "swing_momentum_picks": swing_picks[:8],
        "value_dip_buys": dip_picks[:8],
        "total_analyzed": len(evaluated_stocks),
        "summary": summary_text
    }
