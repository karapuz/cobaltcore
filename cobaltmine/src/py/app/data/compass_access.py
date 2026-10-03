import rating.conf.const as const
import rating.util.access as access
import rating.tweak.context as twkcx
import rating.tweak.tweak_const as tweak_const
import rating.conf.pallete_conf as pallete_conf
import rating.conf.report_run_env as report_run_env
import rating.model.version_repo.comp_r_20260819.rating_model_engine as rating_model_engine
import os
import rating.conf.const as rating_const

from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
import threading

past_periods = 10
env_name: str = str(os.getenv("ENV_DATA_NAME"))
pallette = "STEEL_BLUE"

CUMULATIVE = "CUMULATIVE"
PIT = "PIT"

QS = ["Q4", "Q3", "Q2", "Q1"]
attributes = {
    "REVENUE": CUMULATIVE,
    "FREE_CASH_FLOW": CUMULATIVE,
    "TOTAL_DEBT": PIT,
    "CASH_AND_EQ": PIT,
    "INTEREST": CUMULATIVE,
    "SHORT_TERM_DEBT": PIT,
    "OPERATING_CASH_FLOW": CUMULATIVE,
    "INCOME_TAX_EXPENSE": CUMULATIVE,
    "EBITDA": CUMULATIVE,
}

# ─────────────────────────────────────
# SymbolDataKeeper cache
# ─────────────────────────────────────
#
# Building a keeper is the expensive part of getdata, and the annual service
# asks for the same symbol once per year in the range — five identical
# constructions for a five-year column. Within a session the keeper is built
# once per symbol and reused.
#
# "Session" is explicit and scoped by symbol_session(). Outside one, nothing
# is cached and behaviour is exactly as before: a long-lived process-wide
# cache would serve yesterday's filings indefinitely, which is the wrong
# default for a ratings system.
#
# The cache lives in a ContextVar, so under FastAPI each request gets its
# own and concurrent requests cannot share or evict each other's keepers.

_session_cache: ContextVar = ContextVar("compass_symbol_cache", default=None)
_cache_lock = threading.Lock()


@contextmanager
def symbol_session():
    """
    Reuse SymbolDataKeeper instances for the duration of the block.

        with compass_access.symbol_session():
            for year in years:
                getdata(symbol, year, ttm=False)   # one keeper, not five

    Nests safely: an inner session reuses the outer cache rather than
    starting a second one, so a helper that opens a session does not
    discard the caller's.
    """
    existing = _session_cache.get()
    if existing is not None:
        yield existing
        return

    cache = {}
    token = _session_cache.set(cache)
    try:
        yield cache
    finally:
        # Dropped on exit. Keepers are held only as long as the work that
        # needed them.
        _session_cache.reset(token)
        cache.clear()


def get_symbol_data_keeper(symbol):
    """
    A keeper for `symbol`, from the session cache when one is open.

    Must be called inside the Tweaks context, same as a direct construction:
    a cached keeper is reused under the tweaks in force at call time, not
    the ones it was built under.
    """
    cache = _session_cache.get()
    if cache is None:
        return access.SymbolDataKeeper(symbol, debug=False)

    keeper = cache.get(symbol)
    if keeper is None:
        with _cache_lock:
            keeper = cache.get(symbol)
            if keeper is None:
                keeper = access.SymbolDataKeeper(symbol, debug=False)
                cache[symbol] = keeper
                print(f"getdata: built keeper for {symbol} ({len(cache)} cached)")
    return keeper


def getdata(symbol, year, ttm: bool = True) -> dict:
    tweaks_ = {
        tweak_const.TRANSCRIPT_ROOT: "/tmp/transcript", 
        tweak_const.TRANSCRIPT_DATE: env_name,
        tweak_const.TRANSCRIPT_APP: "prod_20260819",
    }
    tweaks = report_run_env.get_prod_run_conf(env_name, symbol, printout=True)
    tweaks.update(pallete_conf.get_pallette(pallette))
    tweaks.update(tweaks_)
    tweaks[tweak_const.ENV_TWEAK] = const.PROD_MODE
    tweaks[tweak_const.PEERS_TWEAK] = []
    tweaks[tweak_const.PEERS_MAP_TWEAK] = {}
    tweaks[tweak_const.PAST_PERIODS_TWEAK] = past_periods

    with twkcx.Tweaks(**tweaks):
        ttm_vals = defaultdict(float)
        dk = get_symbol_data_keeper(symbol)
        if not ttm:
            found_y = None
            ttm_vals = defaultdict(float)
            date_tag = access.get_date_tag(year=year)
            found_y = date_tag
            for attr, acc_type in attributes.items():
                val = dk.get_val(attr, date_tag=date_tag, throw=False)
                if isinstance(val, rating_const.WRAPPED_VALUE):
                    print(f"getdata: skipping {attr} for {date_tag}")
                    found_y = None
                    break
                ttm_vals[attr] = val
            print(f"getdata: requested {year}, found {found_y}")

            # Nothing for this year or the two after it. Returning the
            # defaultdict here hands back zeros for every figure, which rate
            # as a real company with no revenue instead of failing.
            if not found_y:
                return None
            resolved_year = year
            # ebitda : float = rating_model_engine.compute_ebitda(dk=dk, date_tag=found_y)
            # ttm_vals["EBITDA"] = ebitda
        else:
            resolved_year = int(year)
            found_q = {}
            pit_q = set()
            year_int = int(year)
            for y in [year_int+2, year_int+1, year_int]:
                for q in QS:
                    q_vals = defaultdict(float)
                    if q not in found_q or not found_q[q]:
                        date_tag = access.get_date_tag(year=y, period=q)                        
                        for attr, acc_type in attributes.items():
                            val = dk.get_val(attr, date_tag=date_tag, throw=False)
                            found_q[q] = True
                            if isinstance(val, rating_const.WRAPPED_VALUE):
                                print(f"getdata: skipping {attr} for {date_tag}")
                                found_q[q] = False
                                break
                            q_vals[attr] += val
                        if found_q[q]:
                            print(f"getdata: found {y}-{q}")
                            for attr, acc_type in attributes.items():
                                if acc_type == CUMULATIVE:
                                    ttm_vals[attr] += q_vals[attr]
                                elif acc_type == PIT and attr not in pit_q:
                                    ttm_vals[attr] = q_vals[attr]
                                    pit_q.add(attr)
                                print(f"{y}{q} {attr} - {q_vals[attr]} --> {ttm_vals[attr]}")
                            # ebitda : float = rating_model_engine.compute_ebitda(dk=dk, date_tag=date_tag)
                            # ttm_vals["EBITDA"] += ebitda

        ebitda : float          = ttm_vals["EBITDA"]
        revenue: float          = ttm_vals["REVENUE"]
        free_cash_flow: float   = ttm_vals["FREE_CASH_FLOW"]
        total_debt: float       = ttm_vals["TOTAL_DEBT"]
        cash_eq: float          = ttm_vals["CASH_AND_EQ"]
        interest: float         = ttm_vals["INTEREST"]
        short_term_debt: float  = ttm_vals["SHORT_TERM_DEBT"]
        op_cash_flow: float     = ttm_vals["OPERATING_CASH_FLOW"]
        income_tax_expense      = ttm_vals["INCOME_TAX_EXPENSE"]
        net_debt = total_debt - cash_eq
        print(f"getdata: cash_eq={cash_eq}")
        return {
            # Which year actually supplied the figures. May differ from the
            # requested year when the forward fallback fired. Callers strip
            # this before handing the dict to the rating engine.
            "_resolved_year": str(resolved_year),
            "income_tax_expense": income_tax_expense,
            "revenue": revenue, 
            "ebitda": ebitda,
            "free_cash_flow": free_cash_flow,
            "debt": total_debt,
            "total_debt": total_debt, 
            "net_debt": net_debt, 
            "interest": interest, 
            "operating_cash_flow": op_cash_flow,
            "short_term_debt": short_term_debt
        }