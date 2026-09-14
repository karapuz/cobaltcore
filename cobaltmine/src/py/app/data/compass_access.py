import os
import math
import statistics
import rating.conf.const as const
import rating.tweak.value as twkval
import rating.util.access as access
import rating.tweak.context as twkcx
import rating.util.csv_util as csv_util
import rating.tweak.tweak_const as tweak_const
import rating.conf.pallete_conf as pallete_conf
import rating.conf.report_run_env as report_run_env
import rating.util.transcript_util as transcript_util
import rating.research.jeff.mash_util_20260819 as mash_util_20260819
import rating.research.jeff.mash_ticker_util as mash_ticker_util

from rating.model.version_repo.comp_r_20260819 import rating_model
from rating.model.version_repo.comp_r_20260819.rating_model_engine import engine


def to_numerical_cr(ratings):
    return list(rating_model.rating_name_to_num(e) for e in ratings)


past_periods = 10
env_name = "20260609"
pallette = "STEEL_BLUE"

def mash_engine(data_keeper):
    financial_report_year = twkval.getenv(tweak_const.FINANCIAL_REPORT_YEAR_TWEAK)
    model_date_tag = access.get_date_tag(financial_report_year)

    ret = engine(
        dk=data_keeper, 
        date_tag=model_date_tag, 
        debug="") # ":P:C:V:N:R:"
    
    RATING_CLASS = ret["report"]["class"]
    RATING_VALUE = ret["report"]["value"]
    RATING_NAME  = ret["report"]["name"]

    return dict(
        RATING_CLASS=RATING_CLASS,
        RATING_VALUE=RATING_VALUE,
        RATING_NAME=RATING_NAME)


default_rating_percentage_3 = {
    "REVENUE": [.05, .1, .15, .20, .25],
    "EB_M"   : [.05, .1, .15, .20, .25],
    "FCF_TD" : [.05, .1, .15, .20, .25],
    "TD_EB"  : [.05, .1, .15, .20, .25],
    "ND_EB"  : [.05, .1, .15, .20, .25],
    "EB_INT" : [.05, .1, .15, .20, .25],
}


range_type = "DEFENSIVE_PACKAGED"
name_rating_percentage = default_rating_percentage_3

def getdata(symbol, year, attributes):
    tweaks_ = {
        tweak_const.TRANSCRIPT_ROOT: "/tmp/transcript", 
        tweak_const.TRANSCRIPT_DATE: env_name,
        tweak_const.TRANSCRIPT_APP: "mash_20260819",
        tweak_const.NOTCHE_THRESHOLDS: {
            "EBITDA": 5, "REVENUE": 5
        },
    }
    tweaks = report_run_env.get_prod_run_conf(env_name, symbol, printout=True)
    tweaks.update(pallete_conf.get_pallette(pallette))
    tweaks.update(tweaks_)
    tweaks[tweak_const.ENV_TWEAK] = const.PROD_MODE
    tweaks[tweak_const.PEERS_TWEAK] = []
    tweaks[tweak_const.PEERS_MAP_TWEAK] = {}
    tweaks[tweak_const.PAST_PERIODS_TWEAK] = past_periods
    with twkcx.Tweaks(**tweaks):
        tweaks[tweak_const.FINANCIAL_REPORT_YEAR_TWEAK] = year
        data_keeper = access.SymbolDataKeeper(symbol, debug=False)
        
    return data_keeper


