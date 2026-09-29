"""
Dynamic Company Search & Autocomplete Engine for Indian Equities & Global Tickers.
Searches local curated universe and queries live Yahoo Finance Search API for real-time ticker resolution.
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from backend.config import DEFAULT_NSE_STOCKS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Search session with browser-like headers
SEARCH_SESSION = requests.Session()
SEARCH_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
})


def search_companies(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Search Indian stocks by symbol or company name.
    1. First performs fast fuzzy/token matching against our curated 130+ NSE stocks.
    2. Then supplements with live Yahoo Finance Search API for broader market discovery.
    """
    if not query or len(query.strip()) < 1:
        # Return popular large-caps by default
        return [
            {
                "symbol": s["symbol"],
                "name": s["name"],
                "sector": s["sector"],
                "exchange": "NSE",
                "is_curated": True
            }
            for s in DEFAULT_NSE_STOCKS[:limit]
        ]

    q = query.strip().upper()
    q_lower = query.strip().lower()
    results: List[Dict[str, Any]] = []
    seen_symbols = set()

    # 1. Search in Curated NSE Universe
    for stock in DEFAULT_NSE_STOCKS:
        sym = stock["symbol"].upper()
        clean_sym = sym.replace(".NS", "")
        name = stock["name"]
        name_lower = name.lower()
        sector = stock.get("sector", "")
        sector_lower = sector.lower()

        # Score priority: Exact symbol prefix > Name contains > Sector contains
        match = False
        priority = 0

        if clean_sym == q or sym == q:
            match = True
            priority = 100
        elif clean_sym.startswith(q) or sym.startswith(q):
            match = True
            priority = 80
        elif q in clean_sym:
            match = True
            priority = 60
        elif q_lower in name_lower:
            match = True
            priority = 50
        elif any(tok in name_lower for tok in q_lower.split()):
            match = True
            priority = 30
        elif q_lower in sector_lower:
            match = True
            priority = 20

        if match and sym not in seen_symbols:
            seen_symbols.add(sym)
            results.append({
                "symbol": stock["symbol"],
                "clean_symbol": clean_sym,
                "name": name,
                "sector": sector,
                "exchange": "NSE",
                "is_curated": True,
                "priority": priority
            })

    # Sort curated matches by priority descending
    results.sort(key=lambda x: x["priority"], reverse=True)

    # 2. If results are fewer than limit or user searched specific ticker, query Yahoo Finance API
    if len(results) < limit:
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={requests.utils.quote(query)}&quotesCount=10&newsCount=0&enableFuzzyQuery=false"
            resp = SEARCH_SESSION.get(url, timeout=3.5)
            if resp.status_code == 200:
                data = resp.json()
                quotes = data.get("quotes", [])
                for q_item in quotes:
                    raw_sym = q_item.get("symbol", "").upper()
                    if not raw_sym or raw_sym in seen_symbols:
                        continue

                    # Prioritize Indian equities (.NS or .BO)
                    exch = q_item.get("exchange", "")
                    short_name = q_item.get("shortname") or q_item.get("longname") or raw_sym
                    sector = q_item.get("sector", "N/A")

                    # If symbol doesn't have suffix and looks like an Indian equity on NSE
                    if exch in ["NSI", "NSE", "BOM", "BSE"]:
                        if not (raw_sym.endswith(".NS") or raw_sym.endswith(".BO")):
                            raw_sym = f"{raw_sym}.NS"

                    if raw_sym not in seen_symbols:
                        seen_symbols.add(raw_sym)
                        results.append({
                            "symbol": raw_sym,
                            "clean_symbol": raw_sym.replace(".NS", "").replace(".BO", ""),
                            "name": short_name,
                            "sector": sector,
                            "exchange": exch or "NSE",
                            "is_curated": False,
                            "priority": 10 if (".NS" in raw_sym or ".BO" in raw_sym) else 5
                        })
        except Exception as e:
            logger.debug(f"Live search fallback failed: {e}")

    # Final sort & cleanup
    results.sort(key=lambda x: x["priority"], reverse=True)
    for r in results:
        r.pop("priority", None)

    return results[:limit]
