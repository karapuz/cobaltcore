import rating.conf.const as const
import rating.util.access as access
import rating.tweak.context as twkcx
import rating.tweak.tweak_const as tweak_const
import rating.conf.pallete_conf as pallete_conf
import rating.conf.report_run_env as report_run_env
import rating.model.version_repo.comp_r_20260819.rating_model_engine as rating_model_engine
import os

past_periods = 10
env_name = os.getenv("ENV_DATA_NAME")
pallette = "STEEL_BLUE"


def getdata(symbol, year, attributes) -> dict:
    tweaks_ = {
        tweak_const.TRANSCRIPT_ROOT: "/tmp/transcript", 
        tweak_const.TRANSCRIPT_DATE: env_name,
        tweak_const.TRANSCRIPT_APP: "prod_20260819",
    }
    date_tag = access.get_date_tag(year=year)
    tweaks = report_run_env.get_prod_run_conf(env_name, symbol, printout=True)
    tweaks.update(pallete_conf.get_pallette(pallette))
    tweaks.update(tweaks_)
    tweaks[tweak_const.ENV_TWEAK] = const.PROD_MODE
    tweaks[tweak_const.PEERS_TWEAK] = []
    tweaks[tweak_const.PEERS_MAP_TWEAK] = {}
    tweaks[tweak_const.PAST_PERIODS_TWEAK] = past_periods
    with twkcx.Tweaks(**tweaks):
        dk = access.SymbolDataKeeper(symbol, debug=False)
        ebitda : float          = rating_model_engine.compute_ebitda(dk=dk, date_tag=date_tag)
        revenue: float          = dk.get_val("REVENUE", date_tag) # type: ignore
        free_cash_flow: float   = dk.get_val("FREE_CASH_FLOW", date_tag) # type: ignore
        total_debt: float       = dk.get_val("TOTAL_DEBT", date_tag) # type: ignore
        cash_eq: float          = dk.get_val("CASH_AND_EQ", date_tag) # type: ignore
        interest: float         = dk.get_val("INTEREST", date_tag) # type: ignore

        short_term_debt: float  = dk.get_val("SHORT_TERM_DEBT", date_tag) # type: ignore
        op_cash_flow: float     = dk.get_val("OPERATING_CASH_FLOW", date_tag) # type: ignore

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

