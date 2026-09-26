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
past_periods = 10
env_name: str = str(os.getenv("ENV_DATA_NAME"))
pallette = "STEEL_BLUE"

QS = ["Q1", "Q2", "Q3", "Q4"]
attributes = [
    "REVENUE",
    "FREE_CASH_FLOW",
    "TOTAL_DEBT",
    "CASH_AND_EQ",
    "INTEREST",
    "SHORT_TERM_DEBT",
    "OPERATING_CASH_FLOW"
]

def getdata(symbol, year, ttm:bool=True) -> dict:
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
        dk = access.SymbolDataKeeper(symbol, debug=False)
        if not ttm:
            year_int = int(year)
            found_y = None
            for y in [year_int+2, year_int+1, year_int]:
                if found_y:
                    break
                ttm_vals = defaultdict(float)
                date_tag = access.get_date_tag(year=y)
                found_y = date_tag
                for attr in attributes:
                    val = dk.get_val(attr, date_tag=date_tag, throw=False)
                    if isinstance(val, rating_const.WRAPPED_VALUE):
                        print(f"getdata: skipping {attr} for {date_tag}")
                        found_y = None
                        break
                    ttm_vals[attr] = val
            print(f"getdata: found {found_y}")
            ebitda : float = rating_model_engine.compute_ebitda(dk=dk, date_tag=found_y)
            ttm_vals["EBITDA"] = ebitda
        else:
            found_q = {}
            year_int = int(year)
            for q in QS:
                for y in [year_int+2, year_int+1, year_int]:
                    q_vals = defaultdict(float)
                    if q not in found_q or not found_q[q]:
                        date_tag = access.get_date_tag(year=y, period=q)                        
                        for attr in attributes:
                            val = dk.get_val(attr, date_tag=date_tag, throw=False)
                            found_q[q] = True
                            if isinstance(val, rating_const.WRAPPED_VALUE):
                                print(f"getdata: skipping {attr} for {date_tag}")
                                found_q[q] = False
                                break
                            q_vals[attr] += val
                        if found_q[q]:
                            print(f"getdata: found {y}-{q}")
                            for attr in attributes:
                                ttm_vals[attr] += q_vals[attr]
                                print(f"{y}{q} {attr} - {q_vals[attr]} --> {ttm_vals[attr]}")
                            ebitda : float = rating_model_engine.compute_ebitda(dk=dk, date_tag=date_tag)
                            ttm_vals["EBITDA"] += ebitda

        ebitda : float          = ttm_vals["EBITDA"]
        revenue: float          = ttm_vals["REVENUE"]
        free_cash_flow: float   = ttm_vals["FREE_CASH_FLOW"]
        total_debt: float       = ttm_vals["TOTAL_DEBT"]
        cash_eq: float          = ttm_vals["CASH_AND_EQ"]
        interest: float         = ttm_vals["INTEREST"]
        short_term_debt: float  = ttm_vals["SHORT_TERM_DEBT"]
        op_cash_flow: float     = ttm_vals["OPERATING_CASH_FLOW"]
        net_debt = total_debt - cash_eq
        return {
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

