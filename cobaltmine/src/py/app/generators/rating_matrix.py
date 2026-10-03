"""
rating_matrix.py — ratings for many entities across many years.

A table where the rows are index components and the columns are financial
years. Each cell is one full run of the rating engine, so a cell here and
the ticker analysis screen for the same entity and year agree by
construction.

    GET /v0/ratings/matrix?index_id=DJIA&start_year=2021&end_year=2025
    GET /v0/ratings/matrix?index_id=DJIA&start_year=2021&end_year=2025
            &ticker_id=<uuid>&ticker_id=<uuid>

Built on index_analysis rather than beside it: entity resolution, the
financials fetch and the response assembly are all reused, and the only
change needed there was threading a `year` through build_pillar_response.

Cells fail independently. A company with no filings for one year leaves
that cell with an error and the rest of the table still renders — a single
missing year should not blank a five-year view.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.data.models import User
from app.auth import get_current_user
from entity import entity_store as entities
import app.data.compass_access as compass_access

from app.generators.index_analysis import (
    DATA_YEAR,
    build_pillar_response,
    resolve_ticker,
)

router = APIRouter()

# One cell is one engine run plus one upstream fetch, so the table is
# priced in round trips. 150 keeps the worst case (30 DJIA names x 5 years)
# inside a normal request.
MAX_CELLS = 150

# Guards against a typo like start_year=201 turning into a 1800-cell table.
EARLIEST_YEAR = 1990
LATEST_YEAR = int(DATA_YEAR) + 1


def parse_year_range(start_year, end_year):
    """Inclusive range, validated. Returns a list of year strings."""
    if start_year is None and end_year is None:
        return [DATA_YEAR]
    if start_year is None:
        start_year = end_year
    if end_year is None:
        end_year = start_year

    if start_year > end_year:
        raise HTTPException(
            status_code=400,
            detail=f"start_year {start_year} is after end_year {end_year}")
    if start_year < EARLIEST_YEAR or end_year > LATEST_YEAR:
        raise HTTPException(
            status_code=400,
            detail=f"years must be between {EARLIEST_YEAR} and {LATEST_YEAR}")

    return [str(year) for year in range(start_year, end_year + 1)]


def resolve_entities(index_id, ticker_ids, as_of):
    """
    The rows of the table.

    `ticker_id` narrows an index to a subset; without it the whole index is
    used. Either way every row is checked against the meta layer, so an
    unknown id fails here rather than as a confusing empty row.
    """
    if ticker_ids:
        rows = []
        for entity_id in ticker_ids:
            symbol, name = resolve_ticker(entity_id, as_of)
            rows.append({"entity_id": entity_id, "ticker": symbol, "name": name})
        return rows

    if not index_id:
        raise HTTPException(
            status_code=400,
            detail="Provide index_id, or one or more ticker_id values")

    try:
        components = entities.index_components(index_id, as_of)
    except entities.IndexNotFound:
        raise HTTPException(status_code=404, detail=f"Unknown index {index_id}")

    return [{"entity_id": c["entity_id"], "ticker": c["ticker"], "name": c["name"]}
            for c in components]


def summarise(result):
    """The part of a full rating that belongs in a table cell."""
    return {
        # When these differ, the cell is showing another year's filings.
        "data_year": result.get("data_year"),
        "requested_year": result.get("requested_year"),
        "compass_rating": result["compass_rating"],
        "base_rating": result["base_rating"],
        "base_score": result["base_score"],
        "dscr": result["dscr"]["formatted_value"],
        "dscr_value": result["dscr"]["value"],
        "dscr_notch": result["dscr"]["notch"],
        "dscr_notch_reason": result["dscr"]["notch_reason"],
        "pillar_ranks": {row["id"]: row["blended_numeric_rank"]
                         for row in result["pillars"]},
    }


@router.get("/v0/ratings/matrix")
async def get_rating_matrix(
    index_id: str = None,
    ticker_id: list[str] = Query(default=None),
    start_year: int = None,
    end_year: int = None,
    effective_date: str = None,
    include_pillars: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Ratings for every selected entity in every selected year.

    `effective_date` resolves index membership and corporate identity, the
    same way the index screens do; `start_year`/`end_year` select the
    financial years. The two are independent: a 2019 effective date with a
    2021-2025 year range gives the 2019 constituents rated on later
    filings.
    """
    years = parse_year_range(start_year, end_year)
    rows = resolve_entities(index_id, ticker_id, effective_date)

    if len(rows) * len(years) > MAX_CELLS:
        raise HTTPException(
            status_code=400,
            detail=(f"{len(rows)} entities x {len(years)} years exceeds the "
                    f"{MAX_CELLS}-cell limit; narrow with ticker_id or a "
                    f"shorter year range"))

    cells = {}
    rated = 0
    failed = 0

    # One SymbolDataKeeper per symbol for the whole table, rather than one
    # per cell. A five-year column asks for the same symbol five times.
    with compass_access.symbol_session():
        for row in rows:
            entity_id = row["entity_id"]
            cells[entity_id] = {}
            for year in years:
                try:
                    # ttm=False: annual filings for that year. The whole point
                    # of this service is that each column is a distinct fiscal
                    # year, which a trailing-twelve-month window would defeat.
                    result = build_pillar_response(
                        entity_id, as_of=effective_date, year=year, ttm=False)
                except HTTPException as exc:
                    # Usually "no financials for this year". Recorded per cell so
                    # one gap does not lose the rest of the table.
                    cells[entity_id][year] = {"error": exc.detail,
                                              "status": exc.status_code}
                    failed += 1
                    continue
                except Exception as exc:  # noqa: BLE001
                    # Anything the data layer or engine raises. Caught per cell
                    # for the same reason: a 150-cell request should not be lost
                    # to one upstream fault, and the message names the cell.
                    cells[entity_id][year] = {
                        "error": f"{type(exc).__name__}: {exc}",
                        "status": 500,
                    }
                    failed += 1
                    continue

                cell = summarise(result)
                if include_pillars:
                    cell["pillars"] = result["pillars"]
                cells[entity_id][year] = cell
                rated += 1

    return {
        "index_id": index_id,
        "as_of": effective_date,
        "years": years,
        "entities": rows,
        "cells": cells,
        "rated": rated,
        "failed": failed,
    }


@router.get("/v0/ratings/matrix/flat")
async def get_rating_matrix_flat(
    index_id: str = None,
    ticker_id: list[str] = Query(default=None),
    start_year: int = None,
    end_year: int = None,
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """
    The same table as one row per (entity, year), for CSV and spreadsheets.

    Failed cells are included with their error rather than dropped, so the
    row count always equals entities x years and a gap is visible instead
    of inferred.
    """
    matrix = await get_rating_matrix(
        index_id=index_id, ticker_id=ticker_id, start_year=start_year,
        end_year=end_year, effective_date=effective_date,
        include_pillars=False, current_user=current_user)

    flat = []
    for entity in matrix["entities"]:
        for year in matrix["years"]:
            cell = matrix["cells"][entity["entity_id"]][year]
            flat.append({
                "entity_id": entity["entity_id"],
                "ticker": entity["ticker"],
                "name": entity["name"],
                "year": year,
                **cell,
            })

    return {"years": matrix["years"], "rated": matrix["rated"],
            "failed": matrix["failed"], "rows": flat}