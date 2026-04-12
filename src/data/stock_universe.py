"""
Stock Universe - Complete investable universe across all market caps and sectors.
Includes mega-caps, mid-caps, small-caps, and potential unicorns.
"""

# ============================================================
# FULL INVESTMENT UNIVERSE
# Categorized by role in portfolio
# ============================================================

# CORE HOLDINGS - Large cap, proven businesses, anchor portfolio
CORE = {
    # Tech Giants
    "AAPL": "Tech/Consumer Electronics",
    "MSFT": "Tech/Cloud & Enterprise",
    "GOOG": "Tech/Search & AI",
    "AMZN": "Tech/E-commerce & Cloud",
    "META": "Tech/Social & Metaverse",

    # Finance Leaders
    "JPM": "Finance/Banking",
    "V": "Finance/Payments",
    "MA": "Finance/Payments",
    "BRK-B": "Finance/Conglomerate",

    # Healthcare Leaders
    "UNH": "Healthcare/Insurance",
    "JNJ": "Healthcare/Diversified",
    "LLY": "Healthcare/Pharma (GLP-1)",
    "ABBV": "Healthcare/Biotech",

    # Consumer Staples
    "WMT": "Consumer/Retail",
    "COST": "Consumer/Wholesale",
    "PG": "Consumer/Staples",
    "KO": "Consumer/Beverages",
}

# GROWTH ENGINES - High revenue growth, market leaders in expanding TAMs
GROWTH = {
    "NVDA": "AI/GPU Leader",
    "AMD": "AI/CPU & GPU",
    "AVGO": "Semiconductors/Networking",
    "CRM": "Enterprise/SaaS CRM",
    "NFLX": "Streaming/Entertainment",
    "ADBE": "Creative/SaaS",
    "NOW": "Enterprise/IT Workflow",
    "PANW": "Cybersecurity",
    "SNOW": "Data/Cloud Analytics",
    "UBER": "Mobility/Delivery",
    "ABNB": "Travel/Platform",
    "SHOP": "E-commerce/Platform",
}

# UNICORN HUNTERS - Smaller companies with massive growth potential
# High risk, high reward. < $100B market cap, high revenue growth
UNICORNS = {
    "PLTR": "AI/Government & Enterprise Data",
    "COIN": "Crypto/Exchange",
    "SQ": "Fintech/Payments & Banking",
    "DDOG": "Cloud/Observability",
    "NET": "Cloud/Edge Network & Security",
    "CRWD": "Cybersecurity/Endpoint",
    "ZS": "Cybersecurity/Zero Trust",
    "MNDY": "SaaS/Work Management",
    "TTD": "AdTech/Programmatic",
    "RBLX": "Gaming/Metaverse Platform",
    "DUOL": "EdTech/Language Learning",
    "CELH": "Consumer/Beverages",
    "HIMS": "Healthcare/Telehealth DTC",
    "AFRM": "Fintech/Buy Now Pay Later",
    "SOFI": "Fintech/Digital Banking",
    "IONQ": "Quantum Computing",
    "SMCI": "AI/Server Infrastructure",
    "ARM": "Semiconductors/IP Licensing",
    "MSTR": "Bitcoin/Treasury",
    "HOOD": "Fintech/Retail Brokerage",
}

# CYCLICAL & VALUE - Benefit from economic expansion
CYCLICAL = {
    "CAT": "Industrial/Machinery",
    "BA": "Aerospace/Defense",
    "GS": "Finance/Investment Banking",
    "XOM": "Energy/Oil & Gas",
    "CVX": "Energy/Oil & Gas",
    "HD": "Consumer/Home Improvement",
    "NKE": "Consumer/Apparel",
    "MCD": "Consumer/Restaurants",
    "DIS": "Media/Entertainment",
}

# DEFENSIVE - Protect in downturns, dividend payers
DEFENSIVE = {
    "NEE": "Utilities/Renewable Energy",
    "PFE": "Healthcare/Pharma",
    "MRK": "Healthcare/Pharma",
    "T": "Telecom",
    "VZ": "Telecom",
    "GLD": "Gold ETF",
}

# SPECIAL SITUATIONS
SPECIAL = {
    "TSLA": "EV/Energy/AI Robotics",
    "INTC": "Semiconductors/Turnaround",
    "SNAP": "Social/AR Platform",
    "ROKU": "Streaming/CTV Platform",
}


def get_full_universe():
    """Get the complete stock universe with categories."""
    universe = {}
    for category, stocks in [
        ("core", CORE), ("growth", GROWTH), ("unicorn", UNICORNS),
        ("cyclical", CYCLICAL), ("defensive", DEFENSIVE), ("special", SPECIAL),
    ]:
        for ticker, description in stocks.items():
            universe[ticker] = {"description": description, "category": category}
    return universe


def get_universe_tickers():
    """Get all ticker symbols."""
    u = get_full_universe()
    return list(u.keys())


def get_category_tickers(category: str):
    """Get tickers for a specific category."""
    u = get_full_universe()
    return [t for t, info in u.items() if info["category"] == category]
