"""
index_analysis.py — the web layer.

Routes, identity resolution and persistence. Every number in the response
is produced by credit_rating, which this module calls and never
duplicates. Nothing here computes a ratio, a rank or a rating.

    HTTP request
        -> resolve the entity and its ticker as of a date   (entity_store)
        -> fetch financials                                 (compass_access)
        -> load weights / ranges / velocity                 (model_store)
        -> build_credit_rating(...)                         (credit_rating)
        -> attach identity and revision metadata
        -> HTTP response
"""

from fastapi import APIRouter, Depends, HTTPException

from app.data.models import User
from app.auth import get_current_user
from entity import entity_store as entities
from model_data import model_store as model
import app.data.compass_access as compass_access

from app.generators.credit_rating import BASIC_FIELDS, build_credit_rating

router = APIRouter()

# The financial year to fetch. Until compass_access can serve a year
# derived from `as_of`, the identity half of the request is as-of aware
# and the financials half is not — a 2019 effective date resolves the
# 2019 ticker and then scores it with these figures.
DATA_YEAR = "2025"


# ─────────────────────────────────────
# Data access
# ─────────────────────────────────────

def fetch_basic_financials(symbol, year=DATA_YEAR):
    """
    The nine basic figures for one ticker symbol.

    Raises HTTPException rather than returning a partial dict: a missing
    figure that reaches the engine as a zero produces a plausible and
    wrong rating, which is worse than an error.
    """
    basic = compass_access.getdata(
        symbol=symbol, year=year)

    if not basic:
        raise HTTPException(
            status_code=404,
            detail=f"No financials available for {symbol} in {year}")

    missing = [field for field in BASIC_FIELDS
               if basic.get(field) is None]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=(f"Incomplete financials for {symbol} in {year}; "
                    f"missing: {sorted(missing)}"))

    return basic


def resolve_ticker(entity_id, as_of=None):
    """Entity UUID -> (ticker symbol, corporate name) as of a date."""
    try:
        symbol = entities.get_value(entity_id, "exchange_ticker", as_of)
        name = entities.get_value(entity_id, "corporate_name", as_of)
    except entities.EntityNotFound:
        raise HTTPException(status_code=404,
                            detail=f"Unknown entity {entity_id}")
    if symbol is None:
        raise HTTPException(
            status_code=404,
            detail=f"Entity {entity_id} had no exchange ticker on {as_of or 'today'}")
    return symbol, name


# ─────────────────────────────────────
# Response assembly
# ─────────────────────────────────────

def build_pillar_response(entity_id, as_of=None):
    """
    The engine's result plus the identity and revision metadata the UI
    needs. Model inputs are read at request time so the latest persisted
    revision is what scores this request.
    """
    symbol, name = resolve_ticker(entity_id, as_of)
    actual_basic = fetch_basic_financials(symbol)
    records = model.get_all(entity_id)

    result = build_credit_rating(
        actual_basic=actual_basic,
        ranges=records["ranges"]["value"],
        weights=records["weights"]["value"],
        velocity=records["velocity"]["value"],
    )

    result.update({
        "entity_id": entity_id,
        "ticker_symbol": symbol,
        "corporate_name": name,
        "as_of": as_of,
        "data_year": DATA_YEAR,
        "velocity_revision": records["velocity"]["revision"],
        "velocity_is_default": records["velocity"]["is_default"],
        "weights_revision": records["weights"]["revision"],
        "weights_is_default": records["weights"]["is_default"],
        "ranges_revision": records["ranges"]["revision"],
        "ranges_is_default": records["ranges"]["is_default"],
    })
    return result


# ─────────────────────────────────────
# Routes
# ─────────────────────────────────────

@router.get("/v0/index/name/historical")
async def get_indices(
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Available indices, from the meta layer."""
    return {"indices": [
        {"index_id": i["index_id"], "index_name": i["name"],
         "complete": i["complete"]}
        for i in entities.list_indices()
    ]}


@router.get("/v0/index/value/historical")
async def get_index_tickers(
    index_id: str,
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """
    Components of an index as of a date.

    ticker_id is the entity UUID — the stable handle every downstream call
    uses. ticker_symbol and ticker_name are attributes resolved at
    `effective_date`, so a past date returns the ticker the company
    actually traded under then.
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
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Pillar values for one entity. ticker_id is an entity UUID."""
    return build_pillar_response(ticker_id, as_of=effective_date)


@router.post("/v0/pillar/recalculate")
async def recalculate_pillars(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Persist any supplied model inputs, then recompute.

    Weights, ranges and velocity are each written as their own revision
    before the response is built. None of them is a preview: the stored
    value is what every later run for this entity will use.
    """
    entity_id = request_data.get("ticker_id")
    if not entity_id:
        raise HTTPException(status_code=400,
                            detail="ticker_id (entity UUID) is required")

    actor = getattr(current_user, "username", None)
    for component in ("weights", "ranges", "velocity"):
        supplied = request_data.get(component)
        if not supplied:
            continue
        try:
            model.update(entity_id, component, supplied, actor=actor,
                         note=request_data.get("note") or "edited via recalculate")
        except (model.InvalidModelInput, model.UnknownComponent) as exc:
            raise HTTPException(status_code=400, detail=f"{component}: {exc}")

    # Read back from the store rather than the request body, so the
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
    over. The merged result is validated, which is what lets a single
    weight be checked against the sum-to-1 rule.
    """
    entity_id = request_data.get("ticker_id")
    if not entity_id:
        raise HTTPException(status_code=400,
                            detail="ticker_id (entity UUID) is required")
    value = request_data.get("value") or request_data.get(component)
    if not value:
        raise HTTPException(status_code=400,
                            detail=f"{component} value is required")
    try:
        return model.update(entity_id, component, value, actor=
                            getattr(current_user, "username", None),
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