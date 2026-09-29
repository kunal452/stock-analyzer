"""
Indian Stock Market Analyzer & Prediction System - Runner Script.
Supports launching the interactive web application, running direct CLI evaluations,
or executing automated daily scans with investment recommendations.
"""

import sys
import argparse
import webbrowser
import uvicorn

# Configure UTF-8 encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.app import app

def run_server(host="127.0.0.1", port=8000, reload=False, open_browser=True):
    print("\n" + "=" * 66)
    print(" [*] Starting Indian Stock Market Analyzer & Prediction System")
    print(f" Server URL: http://{host}:{port}")
    print(f" Interactive Dashboard: http://localhost:{port}")
    print(f" Daily Recommendations: http://localhost:{port}/api/daily-recommendations")
    print(f" OpenAPI Documentation: http://localhost:{port}/docs")
    print("=" * 66 + "\n")
    
    if open_browser:
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            pass

    uvicorn.run("backend.app:app", host=host, port=port, reload=reload)

def run_cli_analysis(symbol: str):
    from backend.screener import evaluate_single_stock
    from backend.data_engine import fetch_benchmark_data

    print(f"\nRunning quantitative evaluation for {symbol}...")
    bench_df = fetch_benchmark_data(period="2y")
    res = evaluate_single_stock(symbol, benchmark_df=bench_df)

    if not res:
        print(f"Failed to analyze symbol {symbol}")
        return

    plan = res["trade_plan"]
    print("\n" + "=" * 55)
    print(f" Ticker: {res['symbol']} ({res['company_name']})")
    print(f" Sector: {res['sector']}")
    print(f" Current Price: Rs. {res['current_price']} ({res['day_change_pct']}%)")
    print(f" ML Conviction: {res['conviction']} ({res['ml_probability_pct']}%)")
    print(f" Composite Quant Score: {res['composite_score']} / 100")
    print("-" * 55)
    print(" Safety Screen:")
    print(f"   - Trend Filter (Price > 50 & 200 EMA): {'PASS [OK]' if res['filters']['trend_filter'] else 'FAIL [X]'}")
    print(f"   - Liquidity Filter (Turnover >= Rs 8 Cr): {'PASS [OK]' if res['filters']['liquidity_filter'] else 'FAIL [X]'}")
    print(f"   - Model Confidence (>= 58%): {'PASS [OK]' if res['filters']['confidence_filter'] else 'FAIL [X]'}")
    print("-" * 55)
    print(" Actionable Trade Setup:")
    print(f"   - Recommended Entry: Rs. {plan['entry_price']}")
    print(f"   - Dynamic Stop-Loss: Rs. {plan['stop_loss']} (-{plan['stop_loss_pct']}%)")
    print(f"   - Target 1 (+5-8%): Rs. {plan['target_1']} (+{plan['target_1_pct']}%)")
    print(f"   - Target 2 (Runner): Rs. {plan['target_2']} (+{plan['target_2_pct']}%)")
    print(f"   - Risk-to-Reward: {plan['risk_reward_ratio']}")
    print(f"   - Position Sizing (Rs. 1,00,000 Portfolio): Buy {plan['position_sizing']['recommended_shares']} shares (Total Rs. {plan['position_sizing']['trade_capital_required']})")
    print("=" * 55 + "\n")

def run_cli_daily_scan(universe: str = "nifty50"):
    from backend.scheduler import daily_manager
    print("\n" + "=" * 55)
    print(f" Executing Daily Market Scan for Universe: {universe.upper()}")
    print("=" * 55 + "\n")
    results = daily_manager.run_daily_update(universe=universe, force=True)
    suggestions = results.get("investment_suggestions", {})
    top_picks = suggestions.get("top_overall_recommendations", [])
    
    print(f"\nDate: {results['scan_date']} | Updated: {results['updated_at']}")
    print(f"Total Companies Scanned: {results['total_scanned']} | Valid Analyzed: {results['total_valid']}")
    print(f"Market Regime: {results['market_regime']['status']}")
    print("\n[*] TOP INVESTMENT RECOMMENDATIONS FOR TODAY:")
    print("-" * 86)
    for i, p in enumerate(top_picks, 1):
        print(f" {i}. {p['symbol']} ({p['company_name']}) - {p['action']}")
        print(f"    Horizon: {p['horizon']} | Category: {p['category']}")
        print(f"    CMP: Rs. {p['current_price']} | Entry Zone: {p['entry_zone']}")
        print(f"    Target: Rs. {p['target_price']} ({p['target_pct']}) | Stop-Loss: Rs. {p['stop_loss']} ({p['stop_loss_pct']})")
        print(f"    ML Conviction: {p['ml_probability_pct']}% | Risk-Reward: {p['risk_reward']}")
        print(f"    Suggested Allocation: Rs. {p['suggested_allocation']['capital_allocated']:,} ({p['suggested_allocation']['shares_to_buy']} shares)")
        print("-" * 86)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indian Stock Market Analyzer & Prediction System")
    parser.add_argument("--host", default="127.0.0.1", help="Server host IP")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--symbol", type=str, help="Run direct CLI evaluation for a specific symbol (e.g. TCS.NS, RELIANCE.NS)")
    parser.add_argument("--daily-update", action="store_true", help="Execute daily automated scan and print top investment picks")
    parser.add_argument("--universe", default="nifty50", help="Universe preset for daily update (nifty50, nifty100, midcaps, defense_psu, all)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser on startup")

    args = parser.parse_args()

    if args.symbol:
        run_cli_analysis(args.symbol)
    elif args.daily_update:
        run_cli_daily_scan(universe=args.universe)
    else:
        run_server(host=args.host, port=args.port, open_browser=not args.no_browser)
