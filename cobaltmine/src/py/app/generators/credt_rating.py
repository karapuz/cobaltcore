from pprint import pprint as pp
from model_data import model_store as model

# ─────────────────────────────────────
# Corporate identity
# ─────────────────────────────────────
#
# Index membership, entity names and tickers all come from the
# meta layer (entity.entity_store, backed by data/meta).
# Nothing about corporate
# identity is hardcoded here. Entities are addressed by UUID; a ticker is
# just one time-varying attribute of an entity, resolved at the effective
# date of the request.

from model_data.model_store import (
    RATING_ORDER, RANK_TO_RATING, RATING_SCALE, PILLAR_DIRECTION, 
    PILLAR_NAMES, DEFAULT_RANGES, DEFAULT_WEIGHTS
)


# ─────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────

class Pillar:
    def __init__(self, pillar_id, actual_value, breakpoints, actual_numeric_rank=None):
        self._pillar_id = pillar_id
        self._actual_value = actual_value
        self._breakpoints = breakpoints

        self._is_increasing = PILLAR_DIRECTION[self._pillar_id]

        if actual_numeric_rank is None:
            self._actual_numeric_rank = calculate_rank(
                self._actual_value, 
                self._breakpoints, 
                self._is_increasing)
        self._actual_rating = rank_to_rating(self._actual_numeric_rank)
        self._formatted_value = format_pillar_value(self._pillar_id, self._actual_value),
        self._range_display = get_range_display(self._actual_numeric_rank, self._breakpoints, self._is_increasing)

    def get_actual_numeric_rank(self):
        return self._actual_numeric_rank

    def get_actual_value(self):
        return self._actual_value

    def get_breakpoints(self):
        return self._breakpoints

    def get_is_increasing(self):
        return self._is_increasing

    def get_actual_rating(self):
        return self._actual_rating

    def get_formatted_value(self):
        return self._formatted_value

    def get_range_display(self):
        return self._range_display

    def _repr(self):
        return f"Pillar({self._pillar_id}, {self._actual_value}, {self._actual_rating})"

    __repr__ = _repr
    __str__ = _repr

def calculate_pillar_values(basic, basic_ranges) -> dict[str, Pillar]:
    """
    Calculate pillar values from basic financials
    """
    fcf         = basic["free_cash_flow"]
    debt        = basic["debt"]
    ebitda      = basic["ebitda"]
    revenue     = basic["revenue"]
    net_debt    = basic["net_debt"]
    interest    = basic["interest"]
    total_debt  = basic["total_debt"]

    # revenue_scale
    revenue_scale = Pillar("revenue_scale", revenue, basic_ranges["revenue_scale"])

    # ebitda_margin
    best = 0
    worst = len(basic_ranges["ebitda_margin"])

    # 0 - the best, len[x] - the worst
    if revenue <= 0:
        ebitda_margin = Pillar(
            "ebitda_margin", ebitda, basic_ranges["ebitda_margin"], actual_numeric_rank=worst)
    else:
        ebitda_margin = Pillar(
            "ebitda_margin", ebitda, basic_ranges["ebitda_margin"])


    # fcf_debt
    # 0 - the best, len[x] - the worst
    if debt == 0:
        if fcf <= 0:
            fcf_debt = Pillar(
                "fcf_debt", None, basic_ranges["fcf_debt"], actual_numeric_rank=worst)
        else:
            fcf_debt = Pillar(
                "fcf_debt", None, basic_ranges["fcf_debt"], actual_numeric_rank=best)
    else:
        fcf_debt = Pillar(
                "fcf_debt", fcf / debt, basic_ranges["fcf_debt"])


    # td_ebitda
    # 0 - the best, len[x] - the worst
    if ebitda == 0:
        if total_debt == 0:
            td_ebitda = Pillar(
                "td_ebitda", None, basic_ranges["td_ebitda"], actual_numeric_rank=best)
        else:
            td_ebitda = Pillar(
                "td_ebitda", None, basic_ranges["td_ebitda"], actual_numeric_rank=worst)
    else:
        td_ebitda = Pillar(
            "td_ebitda", total_debt / ebitda, basic_ranges["td_ebitda"])

    # nd_ebitda
    # 0 - the best, len[x] - the worst
    if ebitda == 0:
        if net_debt == 0:
            nd_ebitda = Pillar(
                "nd_ebitda", None, basic_ranges["nd_ebitda"], actual_numeric_rank=best)
        else:
            nd_ebitda = Pillar(
                "nd_ebitda", None, basic_ranges["nd_ebitda"], actual_numeric_rank=worst)
    else:
        nd_ebitda = Pillar(
            "nd_ebitda", net_debt / ebitda, basic_ranges["nd_ebitda"])

    # nd_ebitda
    # 0 - the best, len[x] - the worst
    if interest == 0:
        if ebitda == 0:
            ebitda_interest = Pillar(
                "nd_ebitda", None, basic_ranges["ebitda_interest"], actual_numeric_rank=best)
        else:
            ebitda_interest = Pillar(
                "nd_ebitda", None, basic_ranges["ebitda_interest"], actual_numeric_rank=worst)
    else:
        ebitda_interest = Pillar(
            "nd_ebitda", ebitda / interest, basic_ranges["ebitda_interest"])

    # "revenue_scale": Pillar("revenue_scale", revenue),
    # "ebitda_margin": ebitda / revenue if revenue else 0,
    # "fcf_debt": fcf / debt if debt else 0,
    # "td_ebitda": total_debt / ebitda if ebitda else 0,
    # "nd_ebitda": net_debt / ebitda if ebitda else 0,
    # "ebitda_interest": ebitda / interest if interest else 0,

    ret = {
        "revenue_scale"     : revenue_scale,
        "ebitda_margin"     : ebitda_margin,
        "fcf_debt"          : fcf_debt,
        "td_ebitda"         : td_ebitda,
        "nd_ebitda"         : nd_ebitda,
        "ebitda_interest"   : ebitda_interest,
    }
    
    return ret

def calculate_dscr(basic):
    """
    Calculate Debt Service Coverage Ratio.
    DSCR = Operating Cash Flow / (Short Term Debt + Debt)
    """
    ocf = basic["operating_cash_flow"]
    std = basic["short_term_debt"]
    debt = basic["debt"]
    
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
    if numeric_rank not in RANK_TO_RATING:
        print(f"rank_to_rating: numeric_rank={numeric_rank} not in RANK_TO_RATING")
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
        value = value/1000000000
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


# Projection velocity is per entity and editable; see
# model_data/velocity_store.py. Entities that have never been customised
# fall back to velocity_store.DEFAULT_VELOCITY, which holds the values this
# module used to hardcode.

# Forecast horizons emitted on every pillar. Add an entry here and both the
# API payload and the CSV export pick it up; only the table columns in
# TickerAnalysis.js need a matching change.
FORECAST_HORIZONS = [
    {"key": "forecast_1y", "label": "1Y FORECAST", "years": 1},
    {"key": "forecast_2y", "label": "2Y FORECAST", "years": 2},
]

# How much each horizon contributes to a pillar's blended rank before the
# pillar weights are applied. "actual" is the PILLAR column. Must sum to 1.0.
SCORE_BLEND = {
    "actual": 0.55,
    "forecast_1y": 0.35,
    "forecast_2y": 0.10,
}

assert abs(sum(SCORE_BLEND.values()) - 1.0) < 1e-9, "SCORE_BLEND must sum to 1.0"


def build_forecast(actual_basic: dict, years: int = 1, velocity: dict = None): # type: ignore
    """
    Project basic financials `years` ahead by compounding the per-year
    velocity. `velocity` is the entity's stored mapping; defaults are used
    when it is omitted.
    """
    velocity = velocity or model.DEFAULT_VELOCITY
    return {
        key: value * (velocity[key] ** years)
        for key, value in actual_basic.items()
    }


def act_build_pillar_response(ranges, actual_basic, velocity, weights):    
    actual_pillar_values = calculate_pillar_values(actual_basic, basic_ranges=ranges)

    # One set of pillar values per forecast horizon, keyed by horizon key.
    forecast_pillar_values = {
        h["key"]: calculate_pillar_values(
                    build_forecast(
                        actual_basic, h["years"], velocity), 
                    basic_ranges=ranges)
        for h in FORECAST_HORIZONS
    }
    print("forecast_pillar_values->")
    pp(forecast_pillar_values)

    # Calculate DSCR and notch from actual values
    dscr_value = calculate_dscr(actual_basic)
    dscr_notch, dscr_reason = calculate_dscr_notch(dscr_value)
    
    pillars = []
    base_score = 0
    
    pillar_ids = [
        "revenue_scale", 
        "ebitda_margin", 
        "fcf_debt", 
        "td_ebitda", 
        "nd_ebitda", 
        "ebitda_interest"
    ]

    blended_values = {}
    actual_keys = actual_basic.keys()
    for actual_key in actual_keys:
        blended_values[actual_keys] = actual_basic[actual_key] * SCORE_BLEND["actual"]
    for h in FORECAST_HORIZONS:
        key = h["key"]
        for actual_key in actual_keys:
            blended_values[actual_keys] += actual_basic[actual_key] * SCORE_BLEND[key] * velocity[actual_key]


    for pillar_id in pillar_ids:
        pillar_obj = actual_pillar_values[pillar_id]
        for h in FORECAST_HORIZONS:
            key = h["key"]
            forecast_obj = forecast_pillar_values[key][pillar_id]
            blended_numeric_value += forecast_obj.get_actual_value() * SCORE_BLEND[key]
        blended_values[pillar_id] = blended_numeric_value

    blended_objs = calculate_pillar_values(blended_values, basic_ranges=ranges)

    for pillar_id in pillar_ids:
        pillar_obj      = actual_pillar_values[pillar_id]
        weight          = weights.get(pillar_id, DEFAULT_WEIGHTS[pillar_id])
                
        pillar = {
            "name": PILLAR_NAMES[pillar_id],
            "id": pillar_id,
            "value": pillar_obj.get_actual_value(),
            "formatted_value": pillar_obj.get_formatted_value(),
            "numeric_rank": pillar_obj.get_actual_numeric_rank(),
            "rank": pillar_obj.get_actual_rating(),
            "range_display": pillar_obj.get_range_display(),
            "range_breakpoints": pillar_obj.get_breakpoints(),
            "weight": weight,
            "is_increasing": pillar_obj.get_is_increasing(),
        }

        for h in FORECAST_HORIZONS:
            key = h["key"]
            forecast_obj = forecast_pillar_values[key][pillar_id]
            pillar[f"{key}_value"] = forecast_obj.get_actual_value()
            pillar[f"{key}_formatted_value"] = forecast_obj.get_formatted_value()
            pillar[f"{key}_numeric_rank"] = forecast_obj.get_actual_numeric_rank()
            pillar[f"{key}_rank"] = forecast_obj.get_actual_rating()

        blended_obj = blended_objs[pillar_id]
        pillar["blended_numeric_rank"] = blended_obj.get_actual_numeric_rank()
        pillar["blended_rank"] = blended_obj.get_actual_rating()
        pillar["score_contribution"] = pillar["blended_numeric_rank"] * weight

        base_score += pillar["score_contribution"]

        pillars.append(pillar)
    
    # Base rating before notch
    base_rating = score_to_rating(base_score)
    
    # Final rating after notch
    compass_rating = apply_notch(base_rating, dscr_notch)
    
    return {
        # "entity_id": entity_id,
        # "ticker_symbol": ticker_id,
        # "corporate_name": (entities.get_value(entity_id, "corporate_name", as_of)
        #                    if entity_id else None),
        # "as_of": as_of,
        "pillars": pillars,
        "velocity": velocity,
        # "velocity_revision": velocity_record["revision"],
        # "velocity_is_default": velocity_record["is_default"],
        # "weights_revision": records["weights"]["revision"],
        # "weights_is_default": records["weights"]["is_default"],
        # "ranges_revision": records["ranges"]["revision"],
        # "ranges_is_default": records["ranges"]["is_default"],
        # "forecast_horizons": FORECAST_HORIZONS,
        # "score_blend": SCORE_BLEND,
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
