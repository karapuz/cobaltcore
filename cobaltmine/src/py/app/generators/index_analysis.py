import copy

from fastapi import APIRouter, Depends, HTTPException

from app.data.models import User
from app.auth import get_current_user
from entity import entity_store as entities
from model_data import model_store as model
import app.data.compass_access as compass_access

router = APIRouter()

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

# Financials are still keyed by ticker symbol. Only 13 of the 30 DJIA
# entities have them; the rest raise 404 rather than silently scoring
# another company's balance sheet.

from model_data.model_store import (
    RATING_ORDER, RANK_TO_RATING, RATING_SCALE, PILLAR_DIRECTION, 
    PILLAR_NAMES, DEFAULT_RANGES, DEFAULT_WEIGHTS
)


# ─────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────

def calculate_pillar_values(basic):
    """Calculate pillar values from basic financials"""
    fcf         = basic["free_cash_flow"]
    debt        = basic["debt"]
    ebitda      = basic["ebitda"]
    revenue     = basic["revenue"]
    net_debt    = basic["net_debt"]
    interest    = basic["interest"]
    total_debt  = basic["total_debt"]
    
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

def build_pillar_response(entity_id, weights=None, ranges=None, as_of=None):
    """
    Pillar response for one entity as of a date.

    `entity_id` is a UUID from the meta layer. The ticker is
    resolved at `as_of` and used only to find the financials.
    """
    try:
        ticker_id = entities.get_value(entity_id, "exchange_ticker", as_of)
    except entities.EntityNotFound:
        raise HTTPException(status_code=404,
                            detail=f"Unknown entity {entity_id}")
    if ticker_id is None:
        raise HTTPException(
            status_code=404,
            detail=f"Entity {entity_id} had no exchange ticker on {as_of or 'today'}")

    # if ticker_id not in MOCK_BASIC_VALUES:
    #     raise HTTPException(
    #         status_code=404,
    #         detail=(f"No financials loaded for {ticker_id} "
    #                 f"({entities.get_value(entity_id, 'corporate_name', as_of)})"))    
    return _build_pillar_response(ticker_id, entity_id, weights, ranges, as_of)


def _build_pillar_response(ticker_id, entity_id=None, weights=None,
                           ranges=None, as_of=None):
    # Read the velocity at build time, never at import, so the latest
    # persisted revision is the one that scores this request.
    # All three model inputs are per entity and persisted. Read them at
    # build time, never at import, so the latest revision is what scores
    # this request. A request-supplied weights/ranges has already been
    # persisted by the caller, so there is one source of truth either way.
    if entity_id:
        records = model.get_all(entity_id)
    else:
        records = {name: {"value": copy.deepcopy(spec["default"]),
                          "revision": 0, "is_default": True}
                   for name, spec in model.COMPONENTS.items()}

    # import pdb; pdb.set_trace()
    velocity_record = records["velocity"]
    velocity = velocity_record["value"]
    weights = weights or records["weights"]["value"]
    ranges = ranges or records["ranges"]["value"]
    """Build full pillar response for a ticker"""

    attributes = [
        "revenue", "ebitda", "free_cash_flow", "debt", "total_debt", "net_debt", "interest", 
        "operating_cash_flow", "short_term_debt"
    ]

    actual_basic = compass_access.getdata(symbol=ticker_id, year="2025", attributes=attributes)
    print(f"actual_basic = {actual_basic}")
    actual_pillar_values = calculate_pillar_values(actual_basic)

    # One set of pillar values per forecast horizon, keyed by horizon key.
    forecast_pillar_values = {
        h["key"]: calculate_pillar_values(
            build_forecast(actual_basic, h["years"], velocity))
        for h in FORECAST_HORIZONS
    }
    
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
        
        pillar = {
            "name": PILLAR_NAMES[pillar_id],
            "id": pillar_id,
            "value": actual_value,
            "formatted_value": format_pillar_value(pillar_id, actual_value),
            "numeric_rank": actual_numeric_rank,
            "rank": actual_rating,
            "range_display": get_range_display(actual_numeric_rank, breakpoints, is_increasing),
            "range_breakpoints": breakpoints,
            "weight": weight,
            "is_increasing": is_increasing,
        }

        for h in FORECAST_HORIZONS:
            key = h["key"]
            forecast_value = forecast_pillar_values[key][pillar_id]
            forecast_numeric_rank = calculate_rank(forecast_value, breakpoints, is_increasing)
            pillar[f"{key}_value"] = forecast_value
            pillar[f"{key}_formatted_value"] = format_pillar_value(pillar_id, forecast_value)
            pillar[f"{key}_numeric_rank"] = forecast_numeric_rank
            pillar[f"{key}_rank"] = rank_to_rating(forecast_numeric_rank)

        # Blend the three horizons into one rank for this pillar, then weight it.
        blended_numeric_rank = actual_numeric_rank * SCORE_BLEND["actual"]
        for h in FORECAST_HORIZONS:
            blended_numeric_rank += (
                pillar[f"{h['key']}_numeric_rank"] * SCORE_BLEND[h["key"]]
            )

        pillar["blended_numeric_rank"] = blended_numeric_rank
        pillar["blended_rank"] = rank_to_rating(round(blended_numeric_rank))
        pillar["score_contribution"] = blended_numeric_rank * weight

        base_score += pillar["score_contribution"]

        pillars.append(pillar)
    
    # Base rating before notch
    base_rating = score_to_rating(base_score)
    
    # Final rating after notch
    compass_rating = apply_notch(base_rating, dscr_notch)
    
    return {
        "entity_id": entity_id,
        "ticker_symbol": ticker_id,
        "corporate_name": (entities.get_value(entity_id, "corporate_name", as_of)
                           if entity_id else None),
        "as_of": as_of,
        "pillars": pillars,
        "velocity": velocity,
        "velocity_revision": velocity_record["revision"],
        "velocity_is_default": velocity_record["is_default"],
        "weights_revision": records["weights"]["revision"],
        "weights_is_default": records["weights"]["is_default"],
        "ranges_revision": records["ranges"]["revision"],
        "ranges_is_default": records["ranges"]["is_default"],
        "forecast_horizons": FORECAST_HORIZONS,
        "score_blend": SCORE_BLEND,
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
    effective_date: str = None, # type: ignore
    current_user: User = Depends(get_current_user)
):
    """Available indices, from the meta_information layer."""
    return {"indices": [
        {"index_id": i["index_id"], "index_name": i["name"],
         "complete": i["complete"]}
        for i in entities.list_indices()
    ]}


@router.get("/v0/index/value/historical")
async def get_index_tickers(
    index_id: str,
    effective_date: str = None, # type: ignore
    current_user: User = Depends(get_current_user)
):
    """
    Components of an index as of a date.

    ticker_id is the entity UUID — the stable handle every downstream call
    uses. ticker_symbol and ticker_name are that entity's attributes
    resolved at `effective_date`, so a past date returns the name and ticker
    the company had then.
    """
    try:
        components = entities.index_components(index_id, effective_date)
        meta = entities.index_metadata(index_id)
    except entities.IndexNotFound:
        raise HTTPException(status_code=404, detail=f"Unknown index {index_id}")

    return {
        "index_id": index_id,
        "as_of": effective_date,
        "complete": meta["complete"],
        "membership_dates_loaded": meta["membership_dates_loaded"],
        "tickers": [
            {"ticker_id": c["entity_id"],
             "ticker_symbol": c["ticker"],
             "ticker_name": c["name"]}
            for c in components
        ],
    }


@router.get("/v0/pillar/values/historical")
async def get_pillar_values(
    ticker_id: str,
    effective_date: str = None, # type: ignore
    current_user: User = Depends(get_current_user)
):
    """Pillar values for one entity. ticker_id is an entity UUID."""
    return build_pillar_response(ticker_id, as_of=effective_date)


@router.post("/v0/pillar/recalculate")
async def recalculate_pillars(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Recalculate pillars with custom weights and ranges."""
    entity_id = request_data.get("ticker_id")
    if not entity_id:
        raise HTTPException(status_code=400, detail="ticker_id (entity UUID) is required")

    # Weights, ranges and velocity sent with a recalculate are edits, so
    # each is persisted as its own revision before the response is built.
    # None of them is a preview: the stored value is what every later run
    # for this entity will use.
    actor = getattr(current_user, "username", None)
    for component in ("weights", "ranges", "velocity"):
        supplied = request_data.get(component)
        if not supplied:
            continue
        try:
            model.update(entity_id, component, supplied, actor=actor,
                         note=request_data.get("note") or "edited via recalculate")
        except (model.InvalidModelInput, model.UnknownComponent) as exc:
            raise HTTPException(status_code=400,
                                detail=f"{component}: {exc}")

    # Read back from the store rather than using the request body, so the
    # response always reflects what was actually persisted.
    return build_pillar_response(
        entity_id, as_of=request_data.get("effective_date"))


@router.get("/v0/model/{component}")
async def get_model_component(
    component: str,
    ticker_id: str,
    current_user: User = Depends(get_current_user)
):
    """Live value and revision of one model component for an entity."""
    try:
        return model.get_record(ticker_id, component)
    except model.UnknownComponent as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/v0/model/{component}/history")
async def get_model_history(
    component: str,
    ticker_id: str,
    current_user: User = Depends(get_current_user)
):
    """Every revision ever persisted for one component."""
    try:
        return {"ticker_id": ticker_id, "component": component,
                "revisions": model.history(ticker_id, component)}
    except model.UnknownComponent as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.put("/v0/model/{component}")
async def put_model_component(
    component: str,
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Persist a new revision of one component.

    Accepts a partial mapping — only the keys sent change, the rest carry
    over from the revision in effect. The merged result is validated, which
    is what lets a single weight be checked against the sum-to-1 rule.
    """
    entity_id = request_data.get("ticker_id")
    if not entity_id:
        raise HTTPException(status_code=400, detail="ticker_id (entity UUID) is required")
    value = request_data.get("value") or request_data.get(component)
    if not value:
        raise HTTPException(status_code=400, detail=f"{component} value is required")
    try:
        return model.update(entity_id, component, value,
                            actor=getattr(current_user, "username", None),
                            note=request_data.get("note"))
    except model.UnknownComponent as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except model.InvalidModelInput as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/v0/model/{component}")
async def reset_model_component(
    component: str,
    ticker_id: str,
    current_user: User = Depends(get_current_user)
):
    """Record an explicit return to the default value for one component."""
    try:
        return model.reset(ticker_id, component,
                           actor=getattr(current_user, "username", None))
    except model.UnknownComponent as exc:
        raise HTTPException(status_code=404, detail=str(exc))