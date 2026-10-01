"""
credit_score.py — the Credit Score Estimator (web layer).

Collects ten financials for three periods (net debt is derived) from a form and rates them with
the same engine index analysis uses. This module parses, converts units and
formats; it computes nothing.

The estimator and index analysis differ in exactly one place: index
analysis projects the forecast horizons from a stored velocity, while here
the user types each period in. Both then go through the identical blend,
ranking, weighting, DSCR and notch.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.data.models import User
from app.auth import get_current_user
from model_data.model_store import DEFAULT_RANGES, DEFAULT_WEIGHTS

from app.generators.credit_rating import (
    FORECAST_HORIZONS,
    PILLAR_IDS,
    build_credit_rating,
)

router = APIRouter()

# Form fields are in $ millions; the engine works in absolute currency.
MILLIONS = 1_000_000

# form field -> engine basic financial
FIELD_MAP = {
    "revenueScale": "revenue",
    "ebitda": "ebitda",
    "shortTermDebt": "short_term_debt",
    "debt": "debt",
    "totalDebt": "total_debt",
    "cashEquivalents": "cash_equivalents",
    "freeCashFlow": "free_cash_flow",
    "operatingCashFlow": "operating_cash_flow",
    "interest": "interest",
    # DSCR = (EBITDA - income tax expense) / (interest + short term debt),
    # so the engine needs this one too.
    "incomeTaxExpense": "income_tax_expense",
}

# form period -> which scenario it is. The engine's horizon keys are the
# contract; these are the names the form happens to use.
PERIOD_MAP = {
    "trailing12": "actual",
    "oneYearForward": "forecast_1y",
    "twoYearsForward": "forecast_2y",
}

# Industry weight overrides, keyed by sector. Anything absent uses the same
# defaults index analysis uses, so the two screens agree unless a sector
# deliberately disagrees.
INDUSTRY_WEIGHTS = {}


def parse_financials(financial_data):
    """
    The flat `{field}_{period}` form payload into one basic-financials dict
    per scenario.

    A blank cell is an error rather than a zero: zero revenue is a real,
    rateable input meaning the business has no sales, and silently treating
    an empty box as zero produces a confident CC.
    """
    scenarios = {scenario: {} for scenario in PERIOD_MAP.values()}

    for period, scenario in PERIOD_MAP.items():
        for form_field, basic_field in FIELD_MAP.items():
            raw = financial_data.get(f"{form_field}_{period}")
            if raw is None or raw == "":
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing value for {form_field} ({period})")
            try:
                value = float(raw)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=400,
                    detail=f"{form_field} ({period}) is not a number: {raw!r}")
            scenarios[scenario][basic_field] = value * MILLIONS

        # Net debt is derived, never entered: a typed net debt can contradict
        # the total debt and cash on the same row, and two of the six pillars
        # read it.
        scenarios[scenario]["net_debt"] = (
            scenarios[scenario]["total_debt"]
            - scenarios[scenario]["cash_equivalents"])

    return scenarios


def weights_for(sector):
    return INDUSTRY_WEIGHTS.get(sector, DEFAULT_WEIGHTS)


@router.post("/credit-score/compute")
async def compute_credit_score(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Rate a hand-entered scenario.

    Returns the same pillar rows and rating fields as
    /v0/pillar/values/historical, plus the `factors` list the existing
    results screen renders.
    """
    sector = request_data.get("sector", "Industrials")
    industry = request_data.get("industry", "General")
    financial_data = request_data.get("financialData") or {}
    if not financial_data:
        raise HTTPException(status_code=400, detail="financialData is required")

    scenarios = parse_financials(financial_data)

    result = build_credit_rating(
        actual_basic=scenarios["actual"],
        ranges=request_data.get("ranges") or DEFAULT_RANGES,
        weights=request_data.get("weights") or weights_for(sector),
        forecast_basics={h["key"]: scenarios[h["key"]]
                         for h in FORECAST_HORIZONS},
    )

    # The results screen reads `factors`; the rest of the payload matches
    # the index-analysis response so one component could render either.
    rows = {row["id"]: row for row in result["pillars"]}
    result["factors"] = [
        {
            "id": pillar_id,
            "name": rows[pillar_id]["name"],
            "weight": f"{rows[pillar_id]['weight'] * 100:.2f}%",
            "metric": rows[pillar_id]["blended_formatted_value"],
            "score": rows[pillar_id]["blended_rank"],
        }
        for pillar_id in PILLAR_IDS
    ]

    result.update({
        "sector": sector,
        "industry": industry,
        "compassRating": result["compass_rating"],
        # Exactly what the engine was handed, in absolute currency units
        # (the form collects $ millions). Returned so a result can be traced
        # back to its inputs without re-deriving the unit conversion.
        "basic_financials": {
            "actual": scenarios["actual"],
            **{h["key"]: scenarios[h["key"]] for h in FORECAST_HORIZONS},
        },
        "basic_units": "absolute currency (form values x 1,000,000)",
    })
    return result