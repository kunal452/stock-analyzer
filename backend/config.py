"""
Configuration and constants for Indian Stock Market Analyzer & Prediction System.
Focuses on National Stock Exchange (NSE) equities, benchmark indices, and quantitative parameters.
"""

from typing import List, Dict, Any

# Benchmark & Macro Indices
BENCHMARK_TICKER = "^NSEI"      # Nifty 50
BANK_NIFTY_TICKER = "^NSEBANK"  # Nifty Bank
VIX_TICKER = "^INDIAVIX"        # India VIX

# Market Hours & Scheduling (IST: UTC+5:30)
MARKET_SCHEDULE = {
    "timezone": "Asia/Kolkata",
    "market_open_hour": 9,
    "market_open_minute": 15,
    "market_close_hour": 15,
    "market_close_minute": 30,
    "daily_scan_hour": 15,
    "daily_scan_minute": 45,  # Run daily scan at 15:45 IST after market settlement
    "trading_days": [0, 1, 2, 3, 4]  # Monday (0) to Friday (4)
}

# Comprehensive Universe of High-Liquidity Indian Equities (NSE .NS suffix)
# Spans Nifty 50, Nifty Next 50, Midcap 100, PSU leaders, Defense, and High-Volume Retail Equities
DEFAULT_NSE_STOCKS: List[Dict[str, str]] = [
    # --- NIFTY 50 MEGA CAPS & BLUE CHIPS ---
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy & Conglomerate", "category": "mega_cap"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "Information Technology", "category": "mega_cap"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Banking & Financial Services", "category": "mega_cap"},
    {"symbol": "INFY.NS", "name": "Infosys", "sector": "Information Technology", "category": "mega_cap"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Banking & Financial Services", "category": "mega_cap"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "Telecommunications", "category": "mega_cap"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Public Sector Banking", "category": "mega_cap"},
    {"symbol": "LICI.NS", "name": "Life Insurance Corp of India", "sector": "Insurance & Financials", "category": "mega_cap"},
    {"symbol": "ITC.NS", "name": "ITC Limited", "sector": "FMCG", "category": "large_cap"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "sector": "FMCG", "category": "large_cap"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "sector": "Engineering & Construction", "category": "large_cap"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "sector": "NBFC / Financials", "category": "large_cap"},
    {"symbol": "HCLTECH.NS", "name": "HCL Technologies", "sector": "Information Technology", "category": "large_cap"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki India", "sector": "Automobile", "category": "large_cap"},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharmaceutical", "sector": "Pharmaceuticals", "category": "large_cap"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises", "sector": "Conglomerate & Mining", "category": "large_cap"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "sector": "Banking & Financial Services", "category": "large_cap"},
    {"symbol": "TITAN.NS", "name": "Titan Company", "sector": "Consumer Goods & Luxury", "category": "large_cap"},
    {"symbol": "ONGC.NS", "name": "Oil and Natural Gas Corp", "sector": "Energy & Oil", "category": "large_cap"},
    {"symbol": "TMPV.NS", "name": "Tata Motors (Passenger Vehicles)", "sector": "Automobile", "category": "large_cap"},
    {"symbol": "NTPC.NS", "name": "NTPC Limited", "sector": "Power & Energy", "category": "large_cap"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank", "sector": "Banking & Financial Services", "category": "large_cap"},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports and SEZ", "sector": "Infrastructure & Logistics", "category": "large_cap"},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corp of India", "sector": "Power Transmission", "category": "large_cap"},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra", "sector": "Automobile", "category": "large_cap"},
    {"symbol": "COALINDIA.NS", "name": "Coal India", "sector": "Metals & Mining", "category": "large_cap"},
    {"symbol": "BAJAJFINSV.NS", "name": "Bajaj Finserv", "sector": "Financial Services", "category": "large_cap"},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel", "sector": "Metals & Mining", "category": "large_cap"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints", "sector": "Consumer Goods & Paints", "category": "large_cap"},
    {"symbol": "ULTRACEMCO.NS", "name": "UltraTech Cement", "sector": "Cement & Building Materials", "category": "large_cap"},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel", "sector": "Metals & Mining", "category": "large_cap"},
    {"symbol": "WIPRO.NS", "name": "Wipro Limited", "sector": "Information Technology", "category": "large_cap"},
    {"symbol": "GRASIM.NS", "name": "Grasim Industries", "sector": "Textiles & Chemicals", "category": "large_cap"},
    {"symbol": "CIPLA.NS", "name": "Cipla Limited", "sector": "Pharmaceuticals", "category": "large_cap"},
    {"symbol": "TECHM.NS", "name": "Tech Mahindra", "sector": "Information Technology", "category": "large_cap"},
    {"symbol": "HDFCLIFE.NS", "name": "HDFC Life Insurance", "sector": "Insurance & Financials", "category": "large_cap"},
    {"symbol": "SBILIFE.NS", "name": "SBI Life Insurance", "sector": "Insurance & Financials", "category": "large_cap"},
    {"symbol": "DRREDDY.NS", "name": "Dr. Reddy's Laboratories", "sector": "Pharmaceuticals", "category": "large_cap"},
    {"symbol": "BRITANNIA.NS", "name": "Britannia Industries", "sector": "FMCG", "category": "large_cap"},
    {"symbol": "INDUSINDBK.NS", "name": "IndusInd Bank", "sector": "Banking & Financial Services", "category": "large_cap"},
    {"symbol": "NESTLEIND.NS", "name": "Nestle India", "sector": "FMCG", "category": "large_cap"},
    {"symbol": "BPCL.NS", "name": "Bharat Petroleum Corp", "sector": "Energy & Refineries", "category": "large_cap"},
    {"symbol": "EICHERMOT.NS", "name": "Eicher Motors", "sector": "Automobile", "category": "large_cap"},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals", "sector": "Healthcare", "category": "large_cap"},
    {"symbol": "DIVISLAB.NS", "name": "Divi's Laboratories", "sector": "Pharmaceuticals", "category": "large_cap"},
    {"symbol": "HEROMOTOCO.NS", "name": "Hero MotoCorp", "sector": "Automobile", "category": "large_cap"},
    {"symbol": "HINDALCO.NS", "name": "Hindalco Industries", "sector": "Metals & Mining", "category": "large_cap"},
    {"symbol": "COFORGE.NS", "name": "Coforge Limited", "sector": "Information Technology", "category": "large_cap"},
    {"symbol": "SHRIRAMFIN.NS", "name": "Shriram Finance", "sector": "NBFC / Financials", "category": "large_cap"},
    {"symbol": "TRENT.NS", "name": "Trent Limited", "sector": "Retail / Consumer", "category": "large_cap"},
    {"symbol": "BEL.NS", "name": "Bharat Electronics", "sector": "Defense Electronics", "category": "large_cap"},

    # --- DEFENSE, AEROSPACE & PSU GIANTS ---
    {"symbol": "HAL.NS", "name": "Hindustan Aeronautics", "sector": "Defense & Aerospace", "category": "defense_psu"},
    {"symbol": "BDL.NS", "name": "Bharat Dynamics", "sector": "Defense & Missiles", "category": "defense_psu"},
    {"symbol": "MAZDOCK.NS", "name": "Mazagon Dock Shipbuilders", "sector": "Defense & Shipbuilding", "category": "defense_psu"},
    {"symbol": "COCHINSHIP.NS", "name": "Cochin Shipyard", "sector": "Defense & Shipbuilding", "category": "defense_psu"},
    {"symbol": "BHEL.NS", "name": "Bharat Heavy Electricals", "sector": "Heavy Electrical Equipment", "category": "defense_psu"},
    {"symbol": "IRFC.NS", "name": "Indian Railway Finance Corp", "sector": "Railways & Financials", "category": "defense_psu"},
    {"symbol": "RVNL.NS", "name": "Rail Vikas Nigam", "sector": "Railways & Infrastructure", "category": "defense_psu"},
    {"symbol": "IRCON.NS", "name": "Ircon International", "sector": "Railways & Construction", "category": "defense_psu"},
    {"symbol": "PFC.NS", "name": "Power Finance Corporation", "sector": "Power Financing / NBFC", "category": "defense_psu"},
    {"symbol": "RECLTD.NS", "name": "REC Limited", "sector": "Power Financing / NBFC", "category": "defense_psu"},
    {"symbol": "GAIL.NS", "name": "GAIL India", "sector": "Natural Gas & Utilities", "category": "defense_psu"},
    {"symbol": "IOC.NS", "name": "Indian Oil Corporation", "sector": "Energy & Refineries", "category": "defense_psu"},
    {"symbol": "NMDC.NS", "name": "NMDC Limited", "sector": "Mining & Minerals", "category": "defense_psu"},
    {"symbol": "SAIL.NS", "name": "Steel Authority of India", "sector": "Metals & Mining", "category": "defense_psu"},
    {"symbol": "NHPC.NS", "name": "NHPC Limited", "sector": "Hydro Power & Utilities", "category": "defense_psu"},
    {"symbol": "SJVN.NS", "name": "SJVN Limited", "sector": "Renewable & Hydro Power", "category": "defense_psu"},

    # --- HIGH GROWTH MIDCAPS & MOMENTUM LEADERS ---
    {"symbol": "ZOMATO.NS", "name": "Zomato Limited", "sector": "Consumer Tech / Internet", "category": "mid_cap"},
    {"symbol": "JIOFIN.NS", "name": "Jio Financial Services", "sector": "NBFC & Fintech", "category": "large_cap"},
    {"symbol": "SUZLON.NS", "name": "Suzlon Energy", "sector": "Renewable Energy / Wind", "category": "mid_cap"},
    {"symbol": "TATAPOWER.NS", "name": "Tata Power Company", "sector": "Power & Renewable Energy", "category": "large_cap"},
    {"symbol": "DLF.NS", "name": "DLF Limited", "sector": "Real Estate & Construction", "category": "large_cap"},
    {"symbol": "SIEMENS.NS", "name": "Siemens Limited", "sector": "Capital Goods & Tech", "category": "large_cap"},
    {"symbol": "ABB.NS", "name": "ABB India", "sector": "Industrial Tech & Robotics", "category": "large_cap"},
    {"symbol": "CGPOWER.NS", "name": "CG Power and Industrial Solutions", "sector": "Electrical Equipment", "category": "mid_cap"},
    {"symbol": "POLYCAB.NS", "name": "Polycab India", "sector": "Cables & Electricals", "category": "mid_cap"},
    {"symbol": "DIXON.NS", "name": "Dixon Technologies", "sector": "Electronics Manufacturing", "category": "mid_cap"},
    {"symbol": "PERSISTENT.NS", "name": "Persistent Systems", "sector": "Information Technology", "category": "mid_cap"},
    {"symbol": "COFORGE.NS", "name": "Coforge Limited", "sector": "Information Technology", "category": "mid_cap"},
    {"symbol": "KPITTECH.NS", "name": "KPIT Technologies", "sector": "Automotive Software / Tech", "category": "mid_cap"},
    {"symbol": "TATAELXSI.NS", "name": "Tata Elxsi", "sector": "Design & Technology", "category": "mid_cap"},
    {"symbol": "BHARATFORG.NS", "name": "Bharat Forge", "sector": "Forging & Defense", "category": "mid_cap"},
    {"symbol": "CUMMINSIND.NS", "name": "Cummins India", "sector": "Engines & Industrial Machinery", "category": "mid_cap"},
    {"symbol": "ASHOKLEY.NS", "name": "Ashok Leyland", "sector": "Commercial Vehicles", "category": "mid_cap"},
    {"symbol": "TVSMOTOR.NS", "name": "TVS Motor Company", "sector": "Automobile & Two Wheelers", "category": "mid_cap"},
    {"symbol": "ASTRAL.NS", "name": "Astral Limited", "sector": "Building Materials & Pipes", "category": "mid_cap"},
    {"symbol": "SUPREMEIND.NS", "name": "Supreme Industries", "sector": "Plastics & Piping", "category": "mid_cap"},
    {"symbol": "TORNTPOWER.NS", "name": "Torrent Power", "sector": "Power Generation & Distribution", "category": "mid_cap"},
    {"symbol": "TORNTPHARM.NS", "name": "Torrent Pharmaceuticals", "sector": "Pharmaceuticals", "category": "mid_cap"},
    {"symbol": "LUPIN.NS", "name": "Lupin Limited", "sector": "Pharmaceuticals", "category": "mid_cap"},
    {"symbol": "AUROPHARMA.NS", "name": "Aurobindo Pharma", "sector": "Pharmaceuticals", "category": "mid_cap"},
    {"symbol": "ALKEM.NS", "name": "Alkem Laboratories", "sector": "Pharmaceuticals", "category": "mid_cap"},
    {"symbol": "MANAPPURAM.NS", "name": "Manappuram Finance", "sector": "Gold Loans & NBFC", "category": "mid_cap"},
    {"symbol": "MUTHOOTFIN.NS", "name": "Muthoot Finance", "sector": "Gold Loans & NBFC", "category": "mid_cap"},
    {"symbol": "CHOLAFIN.NS", "name": "Cholamandalam Investment", "sector": "Vehicle Finance / NBFC", "category": "mid_cap"},
    {"symbol": "FEDERALBNK.NS", "name": "Federal Bank", "sector": "Banking & Financial Services", "category": "mid_cap"},
    {"symbol": "IDFCFIRSTB.NS", "name": "IDFC First Bank", "sector": "Banking & Financial Services", "category": "mid_cap"},
    {"symbol": "AUBANK.NS", "name": "AU Small Finance Bank", "sector": "Small Finance Banking", "category": "mid_cap"},
    {"symbol": "INDHOTEL.NS", "name": "The Indian Hotels Co (Taj)", "sector": "Hospitality & Tourism", "category": "mid_cap"},
    {"symbol": "JUBLFOOD.NS", "name": "Jubilant FoodWorks", "sector": "Quick Service Restaurants", "category": "mid_cap"},
    {"symbol": "PAGEIND.NS", "name": "Page Industries (Jockey)", "sector": "Apparel & Textiles", "category": "mid_cap"},
    {"symbol": "GODREJCP.NS", "name": "Godrej Consumer Products", "sector": "FMCG", "category": "large_cap"},
    {"symbol": "DABUR.NS", "name": "Dabur India", "sector": "FMCG & Ayurvedic", "category": "large_cap"},
    {"symbol": "MARICO.NS", "name": "Marico Limited", "sector": "FMCG", "category": "large_cap"},
    {"symbol": "COLPAL.NS", "name": "Colgate-Palmolive India", "sector": "FMCG", "category": "large_cap"},
    {"symbol": "TATACONSUM.NS", "name": "Tata Consumer Products", "sector": "FMCG & Beverages", "category": "large_cap"},
    {"symbol": "VBL.NS", "name": "Varun Beverages", "sector": "Beverages & FMCG", "category": "large_cap"},
    {"symbol": "BOSCHLTD.NS", "name": "Bosch Limited", "sector": "Auto Ancillary", "category": "large_cap"},
    {"symbol": "MRF.NS", "name": "MRF Limited", "sector": "Tyres & Rubber", "category": "large_cap"},
    {"symbol": "BALKRISIND.NS", "name": "Balkrishna Industries", "sector": "Tyres & Off-Highway", "category": "mid_cap"},
    {"symbol": "APOLLOTYRE.NS", "name": "Apollo Tyres", "sector": "Tyres & Rubber", "category": "mid_cap"},

    # --- CAPITAL MARKETS, FINTECH & EXCHANGES ---
    {"symbol": "BSE.NS", "name": "BSE Limited", "sector": "Stock Exchange", "category": "capital_markets"},
    {"symbol": "CDSL.NS", "name": "Central Depository Services", "sector": "Depository & Fintech", "category": "capital_markets"},
    {"symbol": "ANGELONE.NS", "name": "Angel One Limited", "sector": "Discount Brokerage / Fintech", "category": "capital_markets"},
    {"symbol": "MOTILALOFS.NS", "name": "Motilal Oswal Financial", "sector": "Broking & Wealth Management", "category": "capital_markets"},
    {"symbol": "MCX.NS", "name": "Multi Commodity Exchange", "sector": "Commodities Exchange", "category": "capital_markets"},
    {"symbol": "KFINTECH.NS", "name": "KFin Technologies", "sector": "RTA & Capital Markets Tech", "category": "capital_markets"},
    {"symbol": "CAMS.NS", "name": "Computer Age Management Services", "sector": "Mutual Fund Services", "category": "capital_markets"},

    # --- SPECIALTY CHEMICALS & MATERIALS ---
    {"symbol": "DEEPAKNTR.NS", "name": "Deepak Nitrite", "sector": "Specialty Chemicals", "category": "mid_cap"},
    {"symbol": "TATACHEM.NS", "name": "Tata Chemicals", "sector": "Inorganic & Basic Chemicals", "category": "mid_cap"},
    {"symbol": "PIIND.NS", "name": "PI Industries", "sector": "Agrochemicals & Fine Chem", "category": "mid_cap"},
    {"symbol": "SRF.NS", "name": "SRF Limited", "sector": "Specialty Chemicals & Fluorine", "category": "mid_cap"},
    {"symbol": "GUJGASLTD.NS", "name": "Gujarat Gas Limited", "sector": "City Gas Distribution", "category": "mid_cap"},
    {"symbol": "IGL.NS", "name": "Indraprastha Gas Limited", "sector": "City Gas Distribution", "category": "mid_cap"},
    {"symbol": "MGL.NS", "name": "Mahanagar Gas Limited", "sector": "City Gas Distribution", "category": "mid_cap"},
    {"symbol": "PETRONET.NS", "name": "Petronet LNG", "sector": "Oil & Gas Logistics", "category": "mid_cap"},
    {"symbol": "VEDL.NS", "name": "Vedanta Limited", "sector": "Metals & Natural Resources", "category": "large_cap"},
    {"symbol": "NATIONALUM.NS", "name": "National Aluminium Co (NALCO)", "sector": "Aluminium & Mining", "category": "mid_cap"},
    {"symbol": "HINDZINC.NS", "name": "Hindustan Zinc", "sector": "Zinc & Silver Mining", "category": "large_cap"},

    # --- INFRASTRUCTURE, REALTY & CEMENT ---
    {"symbol": "GMRINFRA.NS", "name": "GMR Airports Infrastructure", "sector": "Airports & Infrastructure", "category": "mid_cap"},
    {"symbol": "GODREJPROP.NS", "name": "Godrej Properties", "sector": "Real Estate", "category": "mid_cap"},
    {"symbol": "OBEROIRLTY.NS", "name": "Oberoi Realty", "sector": "Real Estate", "category": "mid_cap"},
    {"symbol": "PRESTIGE.NS", "name": "Prestige Estates Projects", "sector": "Real Estate", "category": "mid_cap"},
    {"symbol": "AMBUJACEM.NS", "name": "Ambuja Cements", "sector": "Cement & Building Materials", "category": "large_cap"},
    {"symbol": "ACC.NS", "name": "ACC Limited", "sector": "Cement", "category": "large_cap"},
    {"symbol": "SHREECEM.NS", "name": "Shree Cement", "sector": "Cement", "category": "large_cap"},
    {"symbol": "DALBHARAT.NS", "name": "Dalmia Bharat", "sector": "Cement", "category": "mid_cap"},

    # --- NEW AGE TECH, RETAIL & TELECOM ---
    {"symbol": "PAYTM.NS", "name": "One97 Communications (Paytm)", "sector": "Fintech & Payments", "category": "mid_cap"},
    {"symbol": "NYKAA.NS", "name": "FSN E-Commerce (Nykaa)", "sector": "E-Commerce & Beauty", "category": "mid_cap"},
    {"symbol": "POLICYBZR.NS", "name": "PB Fintech (PolicyBazaar)", "sector": "Insurtech / Fintech", "category": "mid_cap"},
    {"symbol": "DELHIVERY.NS", "name": "Delhivery Limited", "sector": "Logistics & Supply Chain", "category": "mid_cap"},
    {"symbol": "MAPMYINDIA.NS", "name": "CE Info Systems (MapmyIndia)", "sector": "Geospatial & Tech", "category": "mid_cap"},
    {"symbol": "IDEA.NS", "name": "Vodafone Idea", "sector": "Telecommunications", "category": "mid_cap"},
    {"symbol": "INDUSTOWER.NS", "name": "Indus Towers", "sector": "Telecom Infrastructure", "category": "large_cap"},
    {"symbol": "TATATECH.NS", "name": "Tata Technologies", "sector": "Engineering R&D Services", "category": "mid_cap"},
]

# Universe Presets for Targeted Screening
UNIVERSE_PRESETS: Dict[str, Dict[str, Any]] = {
    "nifty50": {
        "name": "Nifty 50 Top Bluechips",
        "description": "50 high-capitalization benchmark Indian equities with maximum institutional backing and deep liquidity.",
        "symbols": [s["symbol"] for s in DEFAULT_NSE_STOCKS[:50]]
    },
    "nifty100": {
        "name": "Nifty 100 Large & Midcaps",
        "description": "Top 100 bluechip and established large-cap compounders across all key sectors.",
        "symbols": [s["symbol"] for s in DEFAULT_NSE_STOCKS[:100]]
    },
    "midcaps": {
        "name": "High-Growth Midcaps & Smallcaps",
        "description": "Rapidly compounding mid-market leaders in defense, electronics, fintech, and renewable energy.",
        "symbols": [s["symbol"] for s in DEFAULT_NSE_STOCKS if s.get("category") in ["mid_cap", "capital_markets"]]
    },
    "defense_psu": {
        "name": "Defense, Railways & PSU Leaders",
        "description": "Government-backed strategic defense manufacturers, railway infrastructure, and power giants.",
        "symbols": [s["symbol"] for s in DEFAULT_NSE_STOCKS if s.get("category") == "defense_psu" or "Defense" in s.get("sector", "") or "Railways" in s.get("sector", "")]
    },
    "banking_finance": {
        "name": "Banking & Financial Services",
        "description": "Private banks, PSU banks, NBFCs, insurance, and market infrastructure institutions.",
        "symbols": [s["symbol"] for s in DEFAULT_NSE_STOCKS if "Banking" in s.get("sector", "") or "Financial" in s.get("sector", "") or "NBFC" in s.get("sector", "") or "Insurance" in s.get("sector", "")]
    },
    "all": {
        "name": "Full 130+ NSE Market Universe",
        "description": "Comprehensive scan across all curated sectors and market caps.",
        "symbols": [s["symbol"] for s in DEFAULT_NSE_STOCKS]
    }
}

# Quantitative & ML Modeling Parameters
MODEL_PARAMS = {
    # Target definition (Triple barrier / fixed horizon classification)
    "holding_horizon_days": 10,       # Look ahead 10 trading sessions
    "profit_target_pct": 0.04,        # 4.0% upside threshold for positive label
    "stop_loss_limit_pct": -0.025,    # Max allowed drawdown (-2.5%) during holding window
    
    # Validation scheme
    "train_test_split_ratio": 0.80,   # Chronological 80/20 train/test split (no lookahead bias)
    
    # LightGBM Classifier Parameters
    "n_estimators": 120,
    "learning_rate": 0.03,
    "max_depth": 4,
    "num_leaves": 15,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 20,
    "random_state": 42
}

# Rule Engine & Screening Safety Thresholds
SCREENER_THRESHOLDS = {
    "min_turnover_cr": 8.0,           # Minimum daily turnover of ₹8 Crore
    "min_model_confidence": 0.58,      # Minimum ML probability to consider as Buy (58%)
    "strong_buy_confidence": 0.68,    # High conviction threshold (68%)
    "trend_filter_strict": True,       # Price must be above 50 EMA and 200 EMA
    "atr_stop_loss_multiplier": 1.5,   # ATR multiple below entry for dynamic stop loss
    "target_risk_reward_ratio": 1.8,   # Minimum target reward-to-risk ratio
    "default_capital": 100000.0,       # Default risk calculation portfolio base (₹1,00,000)
    "max_risk_per_trade_pct": 0.015    # Risk 1.5% of capital per trade setup
}

# Investment Advisor Categorization Rules
ADVISOR_CONFIG = {
    # Long-term Compounder criteria
    "compounder": {
        "min_roe": 14.0,              # ROE >= 14%
        "max_pe": 80.0,               # P/E reasonable (or N/A for high growth)
        "max_debt_to_equity": 1.8,    # Conservative balance sheet
        "min_holding_months": 6,
        "expected_upside_min": 15.0,  # +15% to +35% upside
        "expected_upside_max": 35.0,
    },
    # High-Conviction Swing criteria
    "swing": {
        "min_ml_confidence": 0.62,
        "min_volume_ratio": 1.10,
        "holding_days_min": 7,
        "holding_days_max": 25,
        "expected_upside_min": 5.0,
        "expected_upside_max": 12.0
    },
    # Value Dip criteria
    "dip_buy": {
        "min_rsi": 32.0,
        "max_rsi": 50.0,
        "proximity_to_50ema_pct": 3.0,  # Within 3% of 50 EMA
        "holding_months": 3
    }
}
