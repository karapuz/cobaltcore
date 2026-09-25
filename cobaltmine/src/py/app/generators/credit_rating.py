"""
credit_rating.py — the rating engine.

Pure computation. Given financials, ranges, weights and a velocity, it
produces a rating. It knows nothing about HTTP, routers, authentication,
entity UUIDs, effective dates, or where any of its inputs came from.

    from credit_rating import build_credit_rating

    result = build_credit_rating(
        actual_basic=financials,   # nine basic figures
        ranges=ranges,             # breakpoints per pillar
        weights=weights,           # pillar weights, summing to 1.0
        velocity=velocity,         # per-year growth multipliers
    )

HOW THE SCORE IS BUILT

    actual financials ──┐
    1Y forecast ────────┼── weighted blend (55/35/10) ──> blended financials
    2Y forecast ────────┘                                        │
                                                                 v
                                                      pillar ratios computed
                                                                 │
                                                                 v
                                                      ranked against ranges
                                                                 │
                                                                 v
                                                    weighted -> base score

Values are blended, not rankings. Ranks are coarse integer buckets, so
averaging them throws away everything that happens inside a bucket and
produces step changes at the edges. Blending the underlying figures first
and ranking once keeps the arithmetic continuous.

The actual and forecast pillars are still computed and returned, because
the UI shows them as columns — but they do not feed the score.
"""

from model_data.model_store import (
    RATING_ORDER,
    BREAKPOINT_TO_RATING,
    RATING_SCALE,
    PILLAR_DIRECTION,
    PILLAR_NAMES,
    DEFAULT_RANGES,
    DEFAULT_WEIGHTS,
    DEFAULT_VELOCITY,
)

# Pillars, in display order.
PILLAR_IDS = (
    "revenue_scale",
    "ebitda_margin",
    "fcf_debt",
    "td_ebitda",
    "nd_ebitda",
    "ebitda_interest",
)

# The nine figures every calculation starts from.
BASIC_FIELDS = (
    "revenue", "ebitda", "free_cash_flow", "debt", "total_debt",
    "net_debt", "interest", "operating_cash_flow", "short_term_debt",
)

# Basic financials arrive in absolute currency units. The revenue_scale
# breakpoints are expressed in billions, so revenue is divided by this
# before it is ranked. Every other pillar is a unitless ratio.
REVENUE_SCALE_DIVISOR = 1_000_000_000

FORECAST_HORIZONS = [
    {"key": "forecast_1y", "label": "1Y FORECAST", "years": 1},
    {"key": "forecast_2y", "label": "2Y FORECAST", "years": 2},
]

# How much each horizon contributes to the blended financials.
# "actual" is the PILLAR column. Must sum to 1.0.
SCORE_BLEND = {
    "actual": 0.55,
    "forecast_1y": 0.35,
    "forecast_2y": 0.10,
}

assert abs(sum(SCORE_BLEND.values()) - 1.0) < 1e-9, "SCORE_BLEND must sum to 1.0"
assert set(SCORE_BLEND) == {"actual"} | {h["key"] for h in FORECAST_HORIZONS}, \
    "SCORE_BLEND and FORECAST_HORIZONS disagree"


class InvalidFinancials(ValueError):
    """A basic financial is missing or not a number."""


# ─────────────────────────────────────
# Ranking primitives
# ─────────────────────────────────────

def calculate_rank(value, breakpoints, is_increasing):
    """
    Numeric rank, 0 = best. With 8 breakpoints the range is 0..8.

    Breakpoints run best to worst: descending for a higher-is-better
    pillar, ascending for a lower-is-better one.
    This should be translated to BREAKPOINT_TO_RATING, and then back to ranking 
    """
    def breakpoint_to_rank(index):
        if index == len(BREAKPOINT_TO_RATING):
            return BREAKPOINT_TO_RATING[index-1][1]
        return BREAKPOINT_TO_RATING[index][1]
    
    if is_increasing:
        for i, bp in enumerate(breakpoints):
            if value >= bp:
                return breakpoint_to_rank(i)
    else:
        for i, bp in enumerate(breakpoints):
            if value <= bp:
                return breakpoint_to_rank(i)
    return breakpoint_to_rank(len(breakpoints))


def rank_to_rating(numeric_rank):
    """
    Letter rating for a pillar rank.

    Ranks come from BREAKPOINT_TO_RATING and are points on the RATING_SCALE
    axis (0, 3, 6, 9, ...), not positions in a list. So this resolves
    through score_to_rating, the same function the final rating uses.
    Resolving through RANK_TO_RATING instead treated the rank as a list
    index, which returned a letter one notch worse for every breakpoint
    below AAA and disagreed with the overall rating for the same number.

    Fractional ranks are still rejected. The guard exists to catch a caller
    averaging ranks, which is the thing this engine avoids by blending
    values instead — score_to_rating alone would silently accept one.
    """
    if numeric_rank is None:
        return None
    if numeric_rank != int(numeric_rank):
        raise ValueError(
            f"rank_to_rating expects an integer rank, got {numeric_rank!r}; "
            f"blend values, not ranks")
    return score_to_rating(int(numeric_rank))


def score_to_rating(score):
    """
    Letter rating for a position on the RATING_SCALE axis.

    This is the single source of truth for turning a number into a letter.
    Pillar ranks and the weighted base score live on the same axis, so both
    resolve through here.
    """
    if score < RATING_SCALE[0][1]:
        return RATING_SCALE[0][0]          # at or below the best band
    for rating, low, high in RATING_SCALE:
        if low <= score < high:
            return rating
    return RATING_SCALE[-1][0]             # beyond the worst band


def apply_notch(rating, notch):
    """Positive notch moves the rating down, negative moves it up."""
    if notch == 0:
        return rating
    try:
        idx = RATING_ORDER.index(rating)
    except ValueError:
        return rating
    return RATING_ORDER[max(0, min(len(RATING_ORDER) - 1, idx + notch))]


def get_range_display(rank, breakpoints, is_increasing):
    """Human-readable band for a rank."""
    if rank is None:
        return "n/a"
    if is_increasing:
        if rank == 0:
            return f"≥{breakpoints[0]}"
        if rank < len(breakpoints):
            return f"{breakpoints[rank]}-{breakpoints[rank - 1]}"
        return f"<{breakpoints[-1]}"
    if rank == 0:
        return f"≤{breakpoints[0]}"
    if rank < len(breakpoints):
        return f"{breakpoints[rank - 1]}-{breakpoints[rank]}"
    return f">{breakpoints[-1]}"


def format_pillar_value(pillar_id, value):
    """
    Display string for a pillar value.

    revenue_scale is already in billions by the time it reaches a Pillar
    (see REVENUE_SCALE_DIVISOR), so nothing is divided here.
    """
    if value is None:
        return "n/a"
    if pillar_id == "revenue_scale":
        return f"${value:.1f}B"
    if pillar_id in ("ebitda_margin", "fcf_debt"):
        return f"{value * 100:.1f}%"
    return f"{value:.2f}x"


# ─────────────────────────────────────
# Pillar
# ─────────────────────────────────────

class Pillar:
    """
    One pillar of one scenario — actual, a forecast horizon, or the blend.

    `value` is None when the ratio is undefined (a zero denominator). In
    that case `numeric_rank` must be supplied explicitly, because the
    caller is the only thing that knows whether "undefined" means best
    (no debt) or worst (no earnings).
    """

    __slots__ = ("_pillar_id", "_value", "_breakpoints", "_is_increasing",
                 "_numeric_rank", "_rating", "_formatted_value",
                 "_range_display")

    def __init__(self, pillar_id, value, breakpoints, numeric_rank=None):
        if pillar_id not in PILLAR_DIRECTION:
            raise KeyError(f"unknown pillar id {pillar_id!r}")
        if value is None and numeric_rank is None:
            raise ValueError(
                f"{pillar_id}: value is None so numeric_rank must be given")

        self._pillar_id = pillar_id
        self._value = value
        self._breakpoints = list(breakpoints)
        self._is_increasing = PILLAR_DIRECTION[pillar_id]

        # Assigned on every path — the draft only set it inside the
        # `if numeric_rank is None` branch, so any explicitly-ranked
        # pillar raised AttributeError on the next line.
        if numeric_rank is None:
            self._numeric_rank = calculate_rank(
                value, self._breakpoints, self._is_increasing)
        else:
            self._numeric_rank = numeric_rank

        self._rating = rank_to_rating(self._numeric_rank)
        # No trailing comma. The draft had one, making this a 1-tuple that
        # then rendered as ("$394.3B",) everywhere it was displayed.
        self._formatted_value = format_pillar_value(pillar_id, value)
        self._range_display = get_range_display(
            self._numeric_rank, self._breakpoints, self._is_increasing)

    @property
    def pillar_id(self):
        return self._pillar_id

    @property
    def name(self):
        return PILLAR_NAMES[self._pillar_id]

    def get_pillar_id(self):
        return self._pillar_id

    def get_actual_value(self):
        return self._value

    def get_actual_numeric_rank(self):
        return self._numeric_rank

    def get_actual_rating(self):
        return self._rating

    def get_breakpoints(self):
        return self._breakpoints

    def get_is_increasing(self):
        return self._is_increasing

    def get_formatted_value(self):
        return self._formatted_value

    def get_range_display(self):
        return self._range_display

    def __eq__(self, other):
        if not isinstance(other, Pillar):
            return NotImplemented
        return (self._pillar_id == other._pillar_id
                and self._value == other._value
                and self._numeric_rank == other._numeric_rank)

    def __repr__(self):
        return (f"Pillar({self._pillar_id}, value={self._value!r}, "
                f"rank={self._numeric_rank}, rating={self._rating})")

    __str__ = __repr__


# ─────────────────────────────────────
# Pillar construction
# ─────────────────────────────────────

# Ranks live on the RATING_SCALE axis, not in breakpoint-index space.
# Deriving these from BREAKPOINT_TO_RATING keeps them correct if the scale
# is ever rewidened — returning 0 and len(breakpoints) put a zero-revenue
# issuer at rank 7, which reads as A- rather than the worst grade.
BEST_RANK = BREAKPOINT_TO_RATING[min(BREAKPOINT_TO_RATING)][1]
WORST_RANK = BREAKPOINT_TO_RATING[max(BREAKPOINT_TO_RATING)][1]


def _best_rank():
    return BEST_RANK


def _worst_rank(breakpoints=None):
    return WORST_RANK


def validate_basic(basic):
    """Every basic field present and numeric. Missing data must not score."""
    if not isinstance(basic, dict):
        raise InvalidFinancials("basic financials must be a mapping")
    missing = [f for f in BASIC_FIELDS if f not in basic]
    if missing:
        raise InvalidFinancials(f"missing basic financial(s): {sorted(missing)}")
    for field in BASIC_FIELDS:
        value = basic[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidFinancials(
                f"{field}: expected a number, got {value!r}")
    return basic


def calculate_pillar_values(basic, basic_ranges=None) -> dict:
    """
    Six Pillars from one set of basic financials.

    Every zero-denominator case is decided explicitly rather than falling
    back to 0, because a ratio of 0 is a real, poor value while an
    undefined ratio can mean either the best case (no debt) or the worst
    (no earnings), and those must not collapse together.
    """
    validate_basic(basic)
    ranges = basic_ranges or DEFAULT_RANGES

    fcf = basic["free_cash_flow"]
    debt = basic["debt"]
    ebitda = basic["ebitda"]
    revenue = basic["revenue"]
    net_debt = basic["net_debt"]
    interest = basic["interest"]
    total_debt = basic["total_debt"]

    pillars = {}

    pillars["revenue_scale"] = Pillar(
        "revenue_scale",
        revenue / REVENUE_SCALE_DIVISOR,
        ranges["revenue_scale"])

    bps = ranges["ebitda_margin"]
    if revenue <= 0:
        pillars["ebitda_margin"] = Pillar(
            "ebitda_margin", None, bps, numeric_rank=_worst_rank(bps))
    else:
        pillars["ebitda_margin"] = Pillar(
            "ebitda_margin", ebitda / revenue, bps)

    # fcf_debt — no debt is favourable, but no debt alongside negative free
    # cash flow is not, so the two are separated.
    bps = ranges["fcf_debt"]
    if debt == 0:
        rank = _best_rank() if fcf > 0 else _worst_rank(bps)
        pillars["fcf_debt"] = Pillar("fcf_debt", None, bps, numeric_rank=rank)
    else:
        pillars["fcf_debt"] = Pillar("fcf_debt", fcf / debt, bps)

    # td_ebitda / nd_ebitda — lower is better. No earnings with no debt is
    # unlevered; no earnings with debt is the worst case.
    for pillar_id, debt_figure in (("td_ebitda", total_debt),
                                   ("nd_ebitda", net_debt)):
        bps = ranges[pillar_id]
        if ebitda == 0:
            rank = _best_rank() if debt_figure <= 0 else _worst_rank(bps)
            pillars[pillar_id] = Pillar(pillar_id, None, bps, numeric_rank=rank)
        else:
            pillars[pillar_id] = Pillar(pillar_id, debt_figure / ebitda, bps)

    # ebitda_interest — no interest expense with positive earnings is
    # infinite coverage
    bps = ranges["ebitda_interest"]
    if interest == 0:
        rank = _best_rank() if ebitda > 0 else _worst_rank(bps)
        pillars["ebitda_interest"] = Pillar(
            "ebitda_interest", None, bps, numeric_rank=rank)
    else:
        pillars["ebitda_interest"] = Pillar(
            "ebitda_interest", ebitda / interest, bps)

    return pillars


# ─────────────────────────────────────
# Forecasting and blending
# ─────────────────────────────────────

def build_forecast(actual_basic, years=1, velocity=None):
    """Project the basic financials `years` ahead, compounding the velocity."""
    velocity = velocity or DEFAULT_VELOCITY
    return {
        key: value * (velocity[key] ** years)
        for key, value in actual_basic.items()
    }


def blend_basics(actual_basic, velocity=None, blend=None, horizons=None):
    """
    One set of financials weighted across actual and every forecast horizon.

        blended[f] = 0.55*actual[f] + 0.35*forecast1y[f] + 0.10*forecast2y[f]

    This is where the 55/35/10 is applied. Ranking happens once, afterwards,
    on the result.
    """
    velocity = velocity or DEFAULT_VELOCITY
    blend = blend or SCORE_BLEND
    horizons = horizons or FORECAST_HORIZONS

    blended = {field: value * blend["actual"]
               for field, value in actual_basic.items()}

    for horizon in horizons:
        weight = blend[horizon["key"]]
        forecast = build_forecast(actual_basic, horizon["years"], velocity)
        for field, value in forecast.items():
            blended[field] += value * weight

    return blended


# ─────────────────────────────────────
# DSCR
# ─────────────────────────────────────

def calculate_dscr(basic):
    """Operating Cash Flow / (Short Term Debt + Debt)."""
    denominator = basic["short_term_debt"] + basic["debt"]
    if denominator == 0:
        return 0
    return basic["operating_cash_flow"] / denominator


def calculate_dscr_notch(dscr_value):
    """DSCR ≥ 1.8 improves by a notch, DSCR < 1.0 worsens by one."""
    if dscr_value >= 1.8:
        return -1, "DSCR ≥ 1.8"
    if dscr_value < 1.0:
        return 1, "DSCR < 1.0"
    return 0, "1.0 ≤ DSCR < 1.8"


# ─────────────────────────────────────
# Top level
# ─────────────────────────────────────

def build_credit_rating(actual_basic, ranges=None, weights=None, velocity=None):
    """
    Full rating for one set of financials. Pure: same inputs, same output.

    Returns the pillar rows the UI renders, the DSCR block, the base score
    and the final rating. Identity — entity id, ticker, corporate name,
    effective date — is the caller's business and is not added here.
    """
    validate_basic(actual_basic)
    ranges = ranges or DEFAULT_RANGES
    weights = weights or DEFAULT_WEIGHTS
    velocity = velocity or DEFAULT_VELOCITY

    actual_pillars = calculate_pillar_values(actual_basic, ranges)

    forecast_pillars = {}
    forecast_basics = {}
    for horizon in FORECAST_HORIZONS:
        forecast_basic = build_forecast(
            actual_basic, horizon["years"], velocity)
        forecast_basics[horizon["key"]] = forecast_basic
        forecast_pillars[horizon["key"]] = calculate_pillar_values(
            forecast_basic, ranges)

    # The score path: blend the figures, then rank once.
    blended_basic = blend_basics(actual_basic, velocity)
    blended_pillars = calculate_pillar_values(blended_basic, ranges)

    dscr_value = calculate_dscr(actual_basic)
    dscr_notch, dscr_reason = calculate_dscr_notch(dscr_value)

    rows = []
    base_score = 0.0
    total_weight = 0.0

    for pillar_id in PILLAR_IDS:
        actual = actual_pillars[pillar_id]
        blended = blended_pillars[pillar_id]
        weight = weights.get(pillar_id, DEFAULT_WEIGHTS[pillar_id])
        total_weight += weight

        row = {
            "name": actual.name,
            "id": pillar_id,
            "value": actual.get_actual_value(),
            "formatted_value": actual.get_formatted_value(),
            "numeric_rank": actual.get_actual_numeric_rank(),
            "rank": actual.get_actual_rating(),
            "range_display": actual.get_range_display(),
            "range_breakpoints": actual.get_breakpoints(),
            "weight": weight,
            "is_increasing": actual.get_is_increasing(),
        }

        for horizon in FORECAST_HORIZONS:
            key = horizon["key"]
            forecast = forecast_pillars[key][pillar_id]
            row[f"{key}_value"] = forecast.get_actual_value()
            row[f"{key}_formatted_value"] = forecast.get_formatted_value()
            row[f"{key}_numeric_rank"] = forecast.get_actual_numeric_rank()
            row[f"{key}_rank"] = forecast.get_actual_rating()

        row["blended_value"] = blended.get_actual_value()
        row["blended_formatted_value"] = blended.get_formatted_value()
        row["blended_numeric_rank"] = blended.get_actual_numeric_rank()
        row["blended_rank"] = blended.get_actual_rating()
        row["score_contribution"] = blended.get_actual_numeric_rank() * weight

        base_score += row["score_contribution"]
        rows.append(row)

    base_rating = score_to_rating(base_score)
    compass_rating = apply_notch(base_rating, dscr_notch)

    return {
        "pillars": rows,
        "velocity": velocity,
        "forecast_horizons": FORECAST_HORIZONS,
        "score_blend": SCORE_BLEND,
        "blended_basic": blended_basic,
        "total_weight": total_weight,
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