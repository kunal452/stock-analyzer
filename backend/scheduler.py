"""
Automated Daily Update Scheduler & Recommendations Manager for Indian Equities.
Handles scheduled daily end-of-day scans, persistent daily recommendations storage,
market status tracking (IST market hours), and on-demand background refreshes.
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from backend.config import MARKET_SCHEDULE, DEFAULT_NSE_STOCKS, UNIVERSE_PRESETS
from backend.screener import run_full_screener

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)
DAILY_CACHE_FILE = os.path.join(CACHE_DIR, "daily_recommendations.json")
DAILY_HISTORY_FILE = os.path.join(CACHE_DIR, "daily_history.json")

# IST timezone definition (UTC + 5:30)
IST = timezone(timedelta(hours=5, minutes=30))


class DailyUpdateManager:
    """
    Manages automated daily scanning, caching, and state for stock recommendations.
    """
    def __init__(self):
        self.is_updating = False
        self.last_updated_at: Optional[str] = None
        self.last_updated_date: Optional[str] = None
        self.status_message = "Ready"
        self._lock = threading.Lock()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.cached_recommendations: Optional[Dict[str, Any]] = None

        # Load persisted daily data if available
        self._load_from_disk()

    def get_ist_now(self) -> datetime:
        """Get current datetime in Indian Standard Time (IST)."""
        return datetime.now(IST)

    def is_market_open(self) -> bool:
        """Check if Indian stock market (NSE/BSE) is currently in regular trading hours."""
        now = self.get_ist_now()
        # Monday is 0, Sunday is 6
        if now.weekday() not in MARKET_SCHEDULE["trading_days"]:
            return False
        
        market_open = now.replace(
            hour=MARKET_SCHEDULE["market_open_hour"], 
            minute=MARKET_SCHEDULE["market_open_minute"], 
            second=0, 
            microsecond=0
        )
        market_close = now.replace(
            hour=MARKET_SCHEDULE["market_close_hour"], 
            minute=MARKET_SCHEDULE["market_close_minute"], 
            second=0, 
            microsecond=0
        )
        return market_open <= now <= market_close

    def get_next_scheduled_scan_time(self) -> str:
        """Calculate next scheduled daily scan time (15:45 IST on next trading session)."""
        now = self.get_ist_now()
        target_today = now.replace(
            hour=MARKET_SCHEDULE["daily_scan_hour"],
            minute=MARKET_SCHEDULE["daily_scan_minute"],
            second=0,
            microsecond=0
        )

        if now.weekday() in MARKET_SCHEDULE["trading_days"] and now < target_today:
            return target_today.strftime("%Y-%m-%d 15:45 IST (Today)")

        # Otherwise find next trading day
        days_ahead = 1
        next_day = now + timedelta(days=days_ahead)
        while next_day.weekday() not in MARKET_SCHEDULE["trading_days"]:
            days_ahead += 1
            next_day = now + timedelta(days=days_ahead)

        target_next = next_day.replace(
            hour=MARKET_SCHEDULE["daily_scan_hour"],
            minute=MARKET_SCHEDULE["daily_scan_minute"],
            second=0,
            microsecond=0
        )
        day_label = "Tomorrow" if days_ahead == 1 else next_day.strftime("%A")
        return target_next.strftime(f"%Y-%m-%d 15:45 IST ({day_label})")

    def get_status(self) -> Dict[str, Any]:
        """Get live status of daily update engine and market."""
        now_ist = self.get_ist_now()
        market_live = self.is_market_open()
        market_text = "LIVE (09:15 - 15:30 IST)" if market_live else "CLOSED"

        return {
            "is_updating": self.is_updating,
            "status_message": self.status_message,
            "last_updated_at": self.last_updated_at or "Not yet run today",
            "last_updated_date": self.last_updated_date,
            "next_scheduled_scan": self.get_next_scheduled_scan_time(),
            "market_status": market_text,
            "is_market_open": market_live,
            "current_time_ist": now_ist.strftime("%Y-%m-%d %I:%M:%S %p IST"),
            "has_data": self.cached_recommendations is not None
        }

    def _load_from_disk(self):
        """Load cached daily recommendations from disk."""
        if os.path.exists(DAILY_CACHE_FILE):
            try:
                with open(DAILY_CACHE_FILE, "r") as f:
                    data = json.load(f)
                    self.cached_recommendations = data
                    self.last_updated_at = data.get("updated_at")
                    self.last_updated_date = data.get("scan_date")
                    logger.info(f"Loaded existing daily recommendations from {self.last_updated_at}")
            except Exception as e:
                logger.warning(f"Could not load daily recommendations cache: {e}")

    def _save_to_disk(self, data: Dict[str, Any]):
        """Persist recommendations to cache file and append to history."""
        try:
            with open(DAILY_CACHE_FILE, "w") as f:
                json.dump(data, f, indent=2)

            # Append summary to history log
            history_record = {
                "scan_date": data.get("scan_date"),
                "updated_at": data.get("updated_at"),
                "total_scanned": data.get("total_scanned"),
                "top_picks_count": len(data.get("top_buy_candidates", [])),
                "top_picks": [
                    {
                        "symbol": s["symbol"],
                        "name": s["company_name"],
                        "price": s["current_price"],
                        "ml_prob": s["ml_probability_pct"],
                        "conviction": s["conviction"]
                    }
                    for s in data.get("top_buy_candidates", [])[:5]
                ]
            }

            history = []
            if os.path.exists(DAILY_HISTORY_FILE):
                try:
                    with open(DAILY_HISTORY_FILE, "r") as hf:
                        history = json.load(hf)
                except Exception:
                    history = []

            # Deduplicate by scan_date
            history = [h for h in history if h.get("scan_date") != data.get("scan_date")]
            history.insert(0, history_record)
            history = history[:30]  # Keep last 30 daily scans

            with open(DAILY_HISTORY_FILE, "w") as hf:
                json.dump(history, hf, indent=2)

        except Exception as e:
            logger.error(f"Error saving daily recommendations to disk: {e}")

    def run_daily_update(self, universe: str = "nifty50", force: bool = False) -> Dict[str, Any]:
        """
        Execute full quantitative screening and generate daily investment recommendations.
        Thread-safe execution.
        """
        with self._lock:
            if self.is_updating:
                return {
                    "status": "already_running",
                    "message": "A daily scan is currently in progress."
                }
            self.is_updating = True
            self.status_message = "Scanning market universe and generating daily investment picks..."

        try:
            logger.info("Executing automated daily market scan...")
            now_ist = self.get_ist_now()
            scan_date_str = now_ist.strftime("%Y-%m-%d")
            updated_at_str = now_ist.strftime("%Y-%m-%d %I:%M %p IST")

            # Run screener across selected universe with parallel workers
            scan_results = run_full_screener(universe_preset=universe, limit_top_k=12, max_workers=6)

            payload = {
                "scan_date": scan_date_str,
                "updated_at": updated_at_str,
                "universe_preset": universe,
                "preset_info": scan_results.get("preset_info"),
                "total_scanned": scan_results["total_scanned"],
                "total_valid": scan_results["total_valid"],
                "market_regime": scan_results["market_regime"],
                "top_buy_candidates": scan_results["top_buy_candidates"],
                "investment_suggestions": scan_results["investment_suggestions"],
                "all_screened_stocks": scan_results["all_screened_stocks"],
                "next_scheduled_scan": self.get_next_scheduled_scan_time()
            }

            self.cached_recommendations = payload
            self.last_updated_at = updated_at_str
            self.last_updated_date = scan_date_str
            self.status_message = f"Daily update completed at {updated_at_str}"

            # Save to disk
            self._save_to_disk(payload)
            logger.info(f"Daily update completed successfully: {len(scan_results['top_buy_candidates'])} top candidates found.")
            return payload

        except Exception as e:
            logger.error(f"Error during daily update run: {e}", exc_info=True)
            self.status_message = f"Update failed: {str(e)}"
            raise
        finally:
            with self._lock:
                self.is_updating = False

    def start_background_scheduler(self):
        """
        Start a background daemon thread that periodically checks if daily scheduled scan is due.
        """
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return

        def _scheduler_loop():
            logger.info("Daily update background scheduler started.")
            # If no cached data exists on startup, run an initial scan in background
            if not self.cached_recommendations:
                logger.info("No existing daily recommendations found. Triggering initial startup scan...")
                try:
                    self.run_daily_update(universe="nifty50")
                except Exception as ex:
                    logger.warning(f"Startup scan encountered an issue: {ex}")

            while not self._stop_event.is_set():
                try:
                    now = self.get_ist_now()
                    today_str = now.strftime("%Y-%m-%d")

                    # Check if today is a trading day
                    if now.weekday() in MARKET_SCHEDULE["trading_days"]:
                        # If after 15:45 IST and today's scan hasn't run yet
                        is_after_close = (
                            now.hour > MARKET_SCHEDULE["daily_scan_hour"] or
                            (now.hour == MARKET_SCHEDULE["daily_scan_hour"] and now.minute >= MARKET_SCHEDULE["daily_scan_minute"])
                        )

                        if is_after_close and (self.last_updated_date != today_str) and not self.is_updating:
                            logger.info(f"Daily scan time reached (15:45 IST). Triggering automated daily scan for {today_str}...")
                            self.run_daily_update(universe="nifty50")

                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}")

                # Check every 60 seconds
                self._stop_event.wait(60.0)

        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def stop_background_scheduler(self):
        """Stop background scheduler thread."""
        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=3.0)


# Global singleton instance
daily_manager = DailyUpdateManager()
