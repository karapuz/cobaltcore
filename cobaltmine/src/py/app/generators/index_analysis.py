from fastapi import APIRouter, Depends

from app.data.models import User
from app.auth import get_current_user

router = APIRouter()

# ─────────────────────────────────────
# Mock Data
# ─────────────────────────────────────

MOCK_INDICES = [
    {"index_name": "Dow Jones Industrial Average", "index_id": "DJIA"},
    {"index_name": "S&P 500", "index_id": "SPX"},
    {"index_name": "NASDAQ 100", "index_id": "NDX"},
]

MOCK_TICKERS = {
    "DJIA": [
        {"ticker_name": "Apple Inc.", "ticker_id": "AAPL"},
        {"ticker_name": "Microsoft Corporation", "ticker_id": "MSFT"},
        {"ticker_name": "JPMorgan Chase & Co.", "ticker_id": "JPM"},
        {"ticker_name": "Visa Inc.", "ticker_id": "V"},
        {"ticker_name": "Johnson & Johnson", "ticker_id": "JNJ"},
        {"ticker_name": "Walmart Inc.", "ticker_id": "WMT"},
        {"ticker_name": "Procter & Gamble Co.", "ticker_id": "PG"},
        {"ticker_name": "UnitedHealth Group Inc.", "ticker_id": "UNH"},
        {"ticker_name": "Home Depot Inc.", "ticker_id": "HD"},
        {"ticker_name": "Chevron Corporation", "ticker_id": "CVX"},
    ],
    "SPX": [
        {"ticker_name": "Apple Inc.", "ticker_id": "AAPL"},
        {"ticker_name": "Microsoft Corporation", "ticker_id": "MSFT"},
        {"ticker_name": "Amazon.com Inc.", "ticker_id": "AMZN"},
        {"ticker_name": "NVIDIA Corporation", "ticker_id": "NVDA"},
        {"ticker_name": "Alphabet Inc.", "ticker_id": "GOOGL"},
    ],
    "NDX": [
        {"ticker_name": "Apple Inc.", "ticker_id": "AAPL"},
        {"ticker_name": "Microsoft Corporation", "ticker_id": "MSFT"},
        {"ticker_name": "NVIDIA Corporation", "ticker_id": "NVDA"},
        {"ticker_name": "Meta Platforms Inc.", "ticker_id": "META"},
    ],
}

# Mock basic values per ticker (in billions, ratios as decimals)
MOCK_BASIC_VALUES = {
    "AAPL": {"revenue": 394.3, "ebitda": 130.5, "free_cash_flow": 99.6, "debt": 111.1, "total_debt": 111.1, "net_debt": 49.0, "interest": 3.9, "operating_cash_flow": 110.5, "short_term_debt": 15.0},
    "MSFT": {"revenue": 211.9, "ebitda": 98.1, "free_cash_flow": 59.5, "debt": 78.4, "total_debt": 78.4, "net_debt": -28.0, "interest": 2.1, "operating_cash_flow": 87.7, "short_term_debt": 5.0},
    "JPM":  {"revenue": 154.8, "ebitda": 65.2, "free_cash_flow": 35.0, "debt": 450.0, "total_debt": 450.0, "net_debt": 350.0, "interest": 18.5, "operating_cash_flow": 45.0, "short_term_debt": 50.0},
    "V":    {"revenue": 32.7, "ebitda": 21.3, "free_cash_flow": 18.5, "debt": 20.5, "total_debt": 20.5, "net_debt": 5.2, "interest": 0.6, "operating_cash_flow": 19.8, "short_term_debt": 3.0},
    "JNJ":  {"revenue": 85.2, "ebitda": 28.5, "free_cash_flow": 17.8, "debt": 35.5, "total_debt": 35.5, "net_debt": 12.3, "interest": 0.9, "operating_cash_flow": 22.1, "short_term_debt": 5.5},
    "WMT":  {"revenue": 611.3, "ebitda": 36.2, "free_cash_flow": 12.5, "debt": 55.8, "total_debt": 55.8, "net_debt": 42.1, "interest": 2.1, "operating_cash_flow": 28.8, "short_term_debt": 8.2},
    "PG":   {"revenue": 82.0, "ebitda": 20.5, "free_cash_flow": 14.2, "debt": 33.1, "total_debt": 33.1, "net_debt": 22.5, "interest": 0.8, "operating_cash_flow": 17.5, "short_term_debt": 4.8},
    "UNH":  {"revenue": 324.2, "ebitda": 32.8, "free_cash_flow": 22.1, "debt": 58.2, "total_debt": 58.2, "net_debt": 35.6, "interest": 2.8, "operating_cash_flow": 28.5, "short_term_debt": 6.5},
    "HD":   {"revenue": 152.7, "ebitda": 24.8, "free_cash_flow": 14.5, "debt": 42.5, "total_debt": 42.5, "net_debt": 38.2, "interest": 1.8, "operating_cash_flow": 18.2, "short_term_debt": 2.8},
    "CVX":  {"revenue": 200.5, "ebitda": 45.2, "free_cash_flow": 21.5, "debt": 25.8, "total_debt": 25.8, "net_debt": 8.5, "interest": 0.7, "operating_cash_flow": 35.2, "short_term_debt": 3.2},
    "AMZN": {"revenue": 574.8, "ebitda": 85.5, "free_cash_flow": 32.2, "debt": 67.2, "total_debt": 67.2, "net_debt": -18.5, "interest": 2.1, "operating_cash_flow": 84.5, "short_term_debt": 8.5},
    "NVDA": {"revenue": 60.9, "ebitda": 33.8, "free_cash_flow": 27.2, "debt": 11.2, "total_debt": 11.2, "net_debt": -15.8, "interest": 0.3, "operating_cash_flow": 28.5, "short_term_debt": 1.2},
    "GOOGL": {"revenue": 307.4, "ebitda": 97.5, "free_cash_flow": 60.2, "debt": 28.5, "total_debt": 28.5, "net_debt": -90.5, "interest": 0.5, "operating_cash_flow": 91.5, "short_term_debt": 3.5},
    "META": {"revenue": 134.9, "ebitda": 52.5, "free_cash_flow": 43.0, "debt": 18.4, "total_debt": 18.4, "net_debt": -23.5, "interest": 0.4, "operating_cash_flow": 71.1, "short_term_debt": 2.1},
}

# ─────────────────────────────────────
# Configuration
# ─────────────────────────────────────

DEFAULT_RANGES = {
    "revenue_scale": [100, 50, 25, 12.5, 6, 3, 1.5, 1],
    "ebitda_margin": [0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05, 0.02],
    "fcf_debt": [1.0, 0.5, 0.3, 0.2, 0.15, 0.10, 0.05, 0.02],
    "td_ebitda": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
    "nd_ebitda": [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
    "ebitda_interest": [15, 10, 8, 6, 4, 3, 2, 1.5],
    "dscr": [3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.5],
}

DEFAULT_WEIGHTS = {
    "revenue_scale": 0.15,
    "ebitda_margin": 0.15,
    "fcf_debt": 0.15,
    "td_ebitda": 0.15,
    "nd_ebitda": 0.10,
    "ebitda_interest": 0.15,
    "dscr": 0.15,
}

# Increasing = True means higher value = better (lower rank)
PILLAR_DIRECTION = {
    "revenue_scale": True,
    "ebitda_margin": True,
    "fcf_debt": True,
    "td_ebitda": False,
    "nd_ebitda": False,
    "ebitda_interest": True,
    "dscr": True,
}

PILLAR_NAMES = {
    "revenue_scale": "Revenue Scale",
    "ebitda_margin": "EBITDA Margin",
    "fcf_debt": "Free Cash Flow / Debt",
    "td_ebitda": "Total Debt / EBITDA",
    "nd_ebitda": "Net Debt / EBITDA",
    "ebitda_interest": "EBITDA / Interest",
    "dscr": "Debt Service Coverage Ratio",
}

RATING_SCALE = [
    ("AAA",   0.0,  1.5),
    ("AA+",   1.5,  2.5),
    ("AA",    2.5,  3.5),
    ("AA-",   3.5,  4.5),
    ("A+",    4.5,  5.5),
    ("A",     5.5,  6.5),
    ("A-",    6.5,  7.5),
    ("BBB+",  7.5,  8.5),
    ("BBB",   8.5,  9.5),
    ("BBB-",  9.5, 10.5),
    ("BB+",  10.5, 11.5),
    ("BB",   11.5, 12.5),
    ("BB-",  12.5, 13.5),
    ("B+",   13.5, 14.5),
    ("B",    14.5, 15.5),
    ("B-",   15.5, 16.5),
    ("CCC+", 16.5, 17.5),
    ("CCC",  17.5, 18.5),
    ("CCC-", 18.5, 19.5),
    ("CC",   19.5, 25.0),
]

# ─────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────

def calculate_pillar_values(basic):
    """Calculate pillar values from basic financials"""
    revenue = basic.get("revenue", 0)
    ebitda = basic.get("ebitda", 0)
    fcf = basic.get("free_cash_flow", 0)
    debt = basic.get("debt", 1)
    total_debt = basic.get("total_debt", 1)
    net_debt = basic.get("net_debt", 0)
    interest = basic.get("interest", 1)
    ocf = basic.get("operating_cash_flow", 0)
    std = basic.get("short_term_debt", 0)
    
    return {
        "revenue_scale": revenue,
        "ebitda_margin": ebitda / revenue if revenue else 0,
        "fcf_debt": fcf / debt if debt else 0,
        "td_ebitda": total_debt / ebitda if ebitda else 0,
        "nd_ebitda": net_debt / ebitda if ebitda else 0,
        "ebitda_interest": ebitda / interest if interest else 0,
        "dscr": ocf / (std + debt) if (std + debt) else 0,
    }


def calculate_rank(value, breakpoints, is_increasing):
    """Calculate rank based on value and breakpoints"""
    if is_increasing:
        for i, bp in enumerate(breakpoints):
            if value >= bp:
                return i
        return len(breakpoints)
    else:
        for i, bp in enumerate(breakpoints):
            if value <= bp:
                return i
        return len(breakpoints)


def get_range_display(rank, breakpoints, is_increasing):
    """Get display string for the range"""
    if is_increasing:
        if rank == 0:
            return f"≥{breakpoints[0]}"
        elif rank < len(breakpoints):
            return f"{breakpoints[rank]}-{breakpoints[rank-1]}"
        else:
            return f"<{breakpoints[-1]}"
    else:
        if rank == 0:
            return f"≤{breakpoints[0]}"
        elif rank < len(breakpoints):
            return f"{breakpoints[rank-1]}-{breakpoints[rank]}"
        else:
            return f">{breakpoints[-1]}"


def format_pillar_value(pillar_id, value):
    """Format pillar value for display"""
    if pillar_id == "revenue_scale":
        return f"${value:.1f}B"
    elif pillar_id in ["ebitda_margin", "fcf_debt"]:
        return f"{value*100:.1f}%"
    else:
        return f"{value:.2f}x"


def score_to_rating(score):
    """Convert total score to rating"""
    for rating, low, high in RATING_SCALE:
        if low <= score < high:
            return rating
    return "CC"


def build_pillar_response(ticker_id, weights=None, ranges=None):
    """Build full pillar response for a ticker"""
    weights = weights or DEFAULT_WEIGHTS
    ranges = ranges or DEFAULT_RANGES
    
    basic = MOCK_BASIC_VALUES.get(ticker_id, MOCK_BASIC_VALUES["AAPL"])
    pillar_values = calculate_pillar_values(basic)
    
    pillars = []
    total_score = 0
    
    for pillar_id in ["revenue_scale", "ebitda_margin", "fcf_debt", "td_ebitda", "nd_ebitda", "ebitda_interest", "dscr"]:
        value = pillar_values[pillar_id]
        is_increasing = PILLAR_DIRECTION[pillar_id]
        breakpoints = ranges.get(pillar_id, DEFAULT_RANGES[pillar_id])
        weight = weights.get(pillar_id, DEFAULT_WEIGHTS[pillar_id])
        
        rank = calculate_rank(value, breakpoints, is_increasing)
        score = rank * weight
        total_score += score
        
        pillars.append({
            "name": PILLAR_NAMES[pillar_id],
            "id": pillar_id,
            "value": value,
            "formatted_value": format_pillar_value(pillar_id, value),
            "rank": rank,
            "range_display": get_range_display(rank, breakpoints, is_increasing),
            "range_breakpoints": breakpoints,
            "weight": weight,
            "is_increasing": is_increasing,
        })
    
    return {
        "pillars": pillars,
        "total_score": total_score,
        "compass_rating": score_to_rating(total_score),
    }

# ─────────────────────────────────────
# Endpoints
# ─────────────────────────────────────

@router.get("/index/name/historical")
async def get_indices(
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get list of available indices"""
    return {"indices": MOCK_INDICES}


@router.get("/index/value/historical")
async def get_index_tickers(
    index_id: str,
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get tickers for a specific index"""
    tickers = MOCK_TICKERS.get(index_id, [])
    return {"tickers": tickers}


@router.get("/pillar/values/historical")
async def get_pillar_values(
    ticker_id: str,
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get pillar values for a specific ticker"""
    return build_pillar_response(ticker_id)


@router.post("/pillar/recalculate")
async def recalculate_pillars(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Recalculate pillars with custom weights and ranges"""
    ticker_id = request_data.get("ticker_id", "AAPL")
    weights = request_data.get("weights")
    ranges = request_data.get("ranges")
    return build_pillar_response(ticker_id, weights, ranges)
