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

# Mock basic values per ticker (in billions)
MOCK_BASIC_VALUES = {
    "AAPL": {
        "actual": {"revenue": 394.3, "ebitda": 130.5, "free_cash_flow": 99.6, "debt": 111.1, "total_debt": 111.1, "net_debt": 49.0, "interest": 3.9, "operating_cash_flow": 110.5, "short_term_debt": 15.0},
        "projected": {"revenue": 420.0, "ebitda": 142.0, "free_cash_flow": 108.0, "debt": 105.0, "total_debt": 105.0, "net_debt": 40.0, "interest": 3.5, "operating_cash_flow": 118.0, "short_term_debt": 12.0},
    },
    "MSFT": {
        "actual": {"revenue": 211.9, "ebitda": 98.1, "free_cash_flow": 59.5, "debt": 78.4, "total_debt": 78.4, "net_debt": -28.0, "interest": 2.1, "operating_cash_flow": 87.7, "short_term_debt": 5.0},
        "projected": {"revenue": 245.0, "ebitda": 115.0, "free_cash_flow": 72.0, "debt": 70.0, "total_debt": 70.0, "net_debt": -45.0, "interest": 1.8, "operating_cash_flow": 102.0, "short_term_debt": 4.0},
    },
    "JPM": {
        "actual": {"revenue": 154.8, "ebitda": 65.2, "free_cash_flow": 35.0, "debt": 450.0, "total_debt": 450.0, "net_debt": 350.0, "interest": 18.5, "operating_cash_flow": 45.0, "short_term_debt": 50.0},
        "projected": {"revenue": 165.0, "ebitda": 70.0, "free_cash_flow": 38.0, "debt": 430.0, "total_debt": 430.0, "net_debt": 320.0, "interest": 17.0, "operating_cash_flow": 50.0, "short_term_debt": 45.0},
    },
    "V": {
        "actual": {"revenue": 32.7, "ebitda": 21.3, "free_cash_flow": 18.5, "debt": 20.5, "total_debt": 20.5, "net_debt": 5.2, "interest": 0.6, "operating_cash_flow": 19.8, "short_term_debt": 3.0},
        "projected": {"revenue": 36.0, "ebitda": 24.0, "free_cash_flow": 21.0, "debt": 18.0, "total_debt": 18.0, "net_debt": 2.0, "interest": 0.5, "operating_cash_flow": 22.5, "short_term_debt": 2.5},
    },
    "JNJ": {
        "actual": {"revenue": 85.2, "ebitda": 28.5, "free_cash_flow": 17.8, "debt": 35.5, "total_debt": 35.5, "net_debt": 12.3, "interest": 0.9, "operating_cash_flow": 22.1, "short_term_debt": 5.5},
        "projected": {"revenue": 88.0, "ebitda": 30.0, "free_cash_flow": 19.0, "debt": 32.0, "total_debt": 32.0, "net_debt": 8.0, "interest": 0.8, "operating_cash_flow": 24.0, "short_term_debt": 5.0},
    },
    "WMT": {
        "actual": {"revenue": 611.3, "ebitda": 36.2, "free_cash_flow": 12.5, "debt": 55.8, "total_debt": 55.8, "net_debt": 42.1, "interest": 2.1, "operating_cash_flow": 28.8, "short_term_debt": 8.2},
        "projected": {"revenue": 640.0, "ebitda": 40.0, "free_cash_flow": 15.0, "debt": 50.0, "total_debt": 50.0, "net_debt": 35.0, "interest": 1.8, "operating_cash_flow": 32.0, "short_term_debt": 7.0},
    },
    "PG": {
        "actual": {"revenue": 82.0, "ebitda": 20.5, "free_cash_flow": 14.2, "debt": 33.1, "total_debt": 33.1, "net_debt": 22.5, "interest": 0.8, "operating_cash_flow": 17.5, "short_term_debt": 4.8},
        "projected": {"revenue": 86.0, "ebitda": 22.0, "free_cash_flow": 15.5, "debt": 30.0, "total_debt": 30.0, "net_debt": 18.0, "interest": 0.7, "operating_cash_flow": 19.0, "short_term_debt": 4.0},
    },
    "UNH": {
        "actual": {"revenue": 324.2, "ebitda": 32.8, "free_cash_flow": 22.1, "debt": 58.2, "total_debt": 58.2, "net_debt": 35.6, "interest": 2.8, "operating_cash_flow": 28.5, "short_term_debt": 6.5},
        "projected": {"revenue": 355.0, "ebitda": 36.0, "free_cash_flow": 25.0, "debt": 55.0, "total_debt": 55.0, "net_debt": 30.0, "interest": 2.5, "operating_cash_flow": 32.0, "short_term_debt": 6.0},
    },
    "HD": {
        "actual": {"revenue": 152.7, "ebitda": 24.8, "free_cash_flow": 14.5, "debt": 42.5, "total_debt": 42.5, "net_debt": 38.2, "interest": 1.8, "operating_cash_flow": 18.2, "short_term_debt": 2.8},
        "projected": {"revenue": 160.0, "ebitda": 27.0, "free_cash_flow": 16.0, "debt": 40.0, "total_debt": 40.0, "net_debt": 34.0, "interest": 1.6, "operating_cash_flow": 20.0, "short_term_debt": 2.5},
    },
    "CVX": {
        "actual": {"revenue": 200.5, "ebitda": 45.2, "free_cash_flow": 21.5, "debt": 25.8, "total_debt": 25.8, "net_debt": 8.5, "interest": 0.7, "operating_cash_flow": 35.2, "short_term_debt": 3.2},
        "projected": {"revenue": 195.0, "ebitda": 42.0, "free_cash_flow": 20.0, "debt": 22.0, "total_debt": 22.0, "net_debt": 5.0, "interest": 0.6, "operating_cash_flow": 33.0, "short_term_debt": 3.0},
    },
    "AMZN": {
        "actual": {"revenue": 574.8, "ebitda": 85.5, "free_cash_flow": 32.2, "debt": 67.2, "total_debt": 67.2, "net_debt": -18.5, "interest": 2.1, "operating_cash_flow": 84.5, "short_term_debt": 8.5},
        "projected": {"revenue": 650.0, "ebitda": 105.0, "free_cash_flow": 45.0, "debt": 60.0, "total_debt": 60.0, "net_debt": -40.0, "interest": 1.8, "operating_cash_flow": 100.0, "short_term_debt": 7.0},
    },
    "NVDA": {
        "actual": {"revenue": 60.9, "ebitda": 33.8, "free_cash_flow": 27.2, "debt": 11.2, "total_debt": 11.2, "net_debt": -15.8, "interest": 0.3, "operating_cash_flow": 28.5, "short_term_debt": 1.2},
        "projected": {"revenue": 95.0, "ebitda": 55.0, "free_cash_flow": 48.0, "debt": 10.0, "total_debt": 10.0, "net_debt": -35.0, "interest": 0.2, "operating_cash_flow": 52.0, "short_term_debt": 1.0},
    },
    "GOOGL": {
        "actual": {"revenue": 307.4, "ebitda": 97.5, "free_cash_flow": 60.2, "debt": 28.5, "total_debt": 28.5, "net_debt": -90.5, "interest": 0.5, "operating_cash_flow": 91.5, "short_term_debt": 3.5},
        "projected": {"revenue": 340.0, "ebitda": 110.0, "free_cash_flow": 70.0, "debt": 25.0, "total_debt": 25.0, "net_debt": -110.0, "interest": 0.4, "operating_cash_flow": 105.0, "short_term_debt": 3.0},
    },
    "META": {
        "actual": {"revenue": 134.9, "ebitda": 52.5, "free_cash_flow": 43.0, "debt": 18.4, "total_debt": 18.4, "net_debt": -23.5, "interest": 0.4, "operating_cash_flow": 71.1, "short_term_debt": 2.1},
        "projected": {"revenue": 160.0, "ebitda": 65.0, "free_cash_flow": 55.0, "debt": 15.0, "total_debt": 15.0, "net_debt": -40.0, "interest": 0.3, "operating_cash_flow": 85.0, "short_term_debt": 1.8},
    },
}

# ─────────────────────────────────────
# Configuration
# ─────────────────────────────────────

# 6 pillars with weights summing to 100%
DEFAULT_RANGES = {
    "revenue_scale": [100, 50, 25, 12.5, 6, 3, 1.5, 1],
    "ebitda_margin": [0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05, 0.02],
    "fcf_debt": [1.0, 0.5, 0.3, 0.2, 0.15, 0.10, 0.05, 0.02],
    "td_ebitda": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
    "nd_ebitda": [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
    "ebitda_interest": [15, 10, 8, 6, 4, 3, 2, 1.5],
}

# Weights sum to 100%
DEFAULT_WEIGHTS = {
    "revenue_scale": 0.15,
    "ebitda_margin": 0.15,
    "fcf_debt": 0.20,
    "td_ebitda": 0.20,
    "nd_ebitda": 0.15,
    "ebitda_interest": 0.15,
}

PILLAR_DIRECTION = {
    "revenue_scale": True,      # higher = better
    "ebitda_margin": True,      # higher = better
    "fcf_debt": True,           # higher = better
    "td_ebitda": False,         # lower = better
    "nd_ebitda": False,         # lower = better
    "ebitda_interest": True,    # higher = better
}

PILLAR_NAMES = {
    "revenue_scale": "Revenue Scale",
    "ebitda_margin": "EBITDA Margin",
    "fcf_debt": "Free Cash Flow / Debt",
    "td_ebitda": "Total Debt / EBITDA",
    "nd_ebitda": "Net Debt / EBITDA",
    "ebitda_interest": "EBITDA / Interest",
}

# Numeric rank to letter rating (0 = best, 8 = worst)
RANK_TO_RATING = {
    0: "AAA",
    1: "AA+",
    2: "AA",
    3: "AA-",
    4: "A+",
    5: "A",
    6: "A-",
    7: "BBB+",
    8: "BBB",
}

# Ordered rating scale for notch adjustments
RATING_ORDER = [
    "AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
    "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
    "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"
]

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
    
    return {
        "revenue_scale": revenue,
        "ebitda_margin": ebitda / revenue if revenue else 0,
        "fcf_debt": fcf / debt if debt else 0,
        "td_ebitda": total_debt / ebitda if ebitda else 0,
        "nd_ebitda": net_debt / ebitda if ebitda else 0,
        "ebitda_interest": ebitda / interest if interest else 0,
    }


def calculate_dscr(basic):
    """
    Calculate Debt Service Coverage Ratio.
    DSCR = Operating Cash Flow / (Short Term Debt + Debt)
    """
    ocf = basic.get("operating_cash_flow", 0)
    std = basic.get("short_term_debt", 0)
    debt = basic.get("debt", 0)
    
    denominator = std + debt
    if denominator == 0:
        return 0
    return ocf / denominator


def calculate_dscr_notch(dscr_value):
    """
    Calculate DSCR notch adjustment.
    - DSCR >= 1.8: notch = -1 (improves rating by 1)
    - DSCR < 1.0:  notch = +1 (worsens rating by 1)
    - Otherwise:   notch = 0 (no change)
    """
    if dscr_value >= 1.8:
        return -1, "DSCR ≥ 1.8"
    elif dscr_value < 1.0:
        return 1, "DSCR < 1.0"
    else:
        return 0, "1.0 ≤ DSCR < 1.8"


def apply_notch(rating, notch):
    """
    Apply notch adjustment to a rating.
    Positive notch moves down (worse), negative notch moves up (better).
    """
    if notch == 0:
        return rating
    
    try:
        idx = RATING_ORDER.index(rating)
    except ValueError:
        return rating
    
    new_idx = idx + notch
    new_idx = max(0, min(len(RATING_ORDER) - 1, new_idx))
    return RATING_ORDER[new_idx]


def calculate_rank(value, breakpoints, is_increasing):
    """Calculate numeric rank (0 = best, 8 = worst)"""
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


def rank_to_rating(numeric_rank):
    """Convert numeric rank to letter rating"""
    if numeric_rank < 0:
        return "AAA"
    if numeric_rank > 8:
        return "BBB-"
    return RANK_TO_RATING.get(numeric_rank, "BBB")


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
    """Convert numeric score to letter rating"""
    for rating, low, high in RATING_SCALE:
        if low <= score < high:
            return rating
    return "CC"


def build_pillar_response(ticker_id, weights=None, ranges=None):
    """Build full pillar response for a ticker"""
    weights = weights or DEFAULT_WEIGHTS
    ranges = ranges or DEFAULT_RANGES
    
    ticker_data = MOCK_BASIC_VALUES.get(ticker_id, MOCK_BASIC_VALUES["AAPL"])
    actual_basic = ticker_data.get("actual", ticker_data)
    projected_basic = ticker_data.get("projected", actual_basic)
    
    actual_pillar_values = calculate_pillar_values(actual_basic)
    projected_pillar_values = calculate_pillar_values(projected_basic)
    
    # Calculate DSCR and notch from actual values
    dscr_value = calculate_dscr(actual_basic)
    dscr_notch, dscr_reason = calculate_dscr_notch(dscr_value)
    
    pillars = []
    base_score = 0
    
    pillar_ids = ["revenue_scale", "ebitda_margin", "fcf_debt", "td_ebitda", "nd_ebitda", "ebitda_interest"]
    
    for pillar_id in pillar_ids:
        actual_value = actual_pillar_values[pillar_id]
        is_increasing = PILLAR_DIRECTION[pillar_id]
        breakpoints = ranges.get(pillar_id, DEFAULT_RANGES[pillar_id])
        weight = weights.get(pillar_id, DEFAULT_WEIGHTS[pillar_id])
        
        actual_numeric_rank = calculate_rank(actual_value, breakpoints, is_increasing)
        actual_rating = rank_to_rating(actual_numeric_rank)
        base_score += actual_numeric_rank * weight
        
        projected_value = projected_pillar_values[pillar_id]
        projected_numeric_rank = calculate_rank(projected_value, breakpoints, is_increasing)
        projected_rating = rank_to_rating(projected_numeric_rank)
        
        pillars.append({
            "name": PILLAR_NAMES[pillar_id],
            "id": pillar_id,
            "value": actual_value,
            "formatted_value": format_pillar_value(pillar_id, actual_value),
            "numeric_rank": actual_numeric_rank,
            "rank": actual_rating,
            "range_display": get_range_display(actual_numeric_rank, breakpoints, is_increasing),
            "range_breakpoints": breakpoints,
            "projected_value": projected_value,
            "projected_formatted_value": format_pillar_value(pillar_id, projected_value),
            "projected_numeric_rank": projected_numeric_rank,
            "projected_rank": projected_rating,
            "weight": weight,
            "is_increasing": is_increasing,
        })
    
    # Base rating before notch
    base_rating = score_to_rating(base_score)
    
    # Final rating after notch
    compass_rating = apply_notch(base_rating, dscr_notch)
    
    return {
        "pillars": pillars,
        "dscr": {
            "value": dscr_value,
            "formatted_value": f"{dscr_value:.2f}x",
            "notch": dscr_notch,
            "notch_reason": dscr_reason,
        },
        "base_score": base_score,
        "base_rating": base_rating,
        "compass_rating": compass_rating,
    }

# ─────────────────────────────────────
# Endpoints
# ─────────────────────────────────────

@router.get("/v0/index/name/historical")
async def get_indices(
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get list of available indices"""
    return {"indices": MOCK_INDICES}


@router.get("/v0/index/value/historical")
async def get_index_tickers(
    index_id: str,
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get tickers for a specific index"""
    tickers = MOCK_TICKERS.get(index_id, [])
    return {"tickers": tickers}


@router.get("/v0/pillar/values/historical")
async def get_pillar_values(
    ticker_id: str,
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get pillar values for a specific ticker"""
    return build_pillar_response(ticker_id)


@router.post("/v0/pillar/recalculate")
async def recalculate_pillars(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Recalculate pillars with custom weights and ranges"""
    ticker_id = request_data.get("ticker_id", "AAPL")
    weights = request_data.get("weights")
    ranges = request_data.get("ranges")
    return build_pillar_response(ticker_id, weights, ranges)