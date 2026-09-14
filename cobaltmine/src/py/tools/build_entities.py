#!/usr/bin/env python3
"""
Build ./data/meta/entity.json — the temporal attribute store for
corporations — and ./data/index.json.

    python build_entities.py

Entity UUIDs are generated deterministically (uuid5 over the SEC CIK) so that
rebuilding the file never renumbers anything. The UUID is the permanent key:
once minted it does NOT change, even if every attribute of the entity does.
That is the whole point — Facebook and Meta are one entity with one UUID and
two names.

Provenance is recorded per record. `source` is where the value came from and
`verified` is whether it came from a machine-readable authoritative feed.
Records with verified=false were entered by hand and should be checked against
filings before anyone relies on them.
"""

import argparse
import json
import uuid
from datetime import date

# Stable namespace for Compass entity UUIDs. Never change this value —
# changing it renumbers every entity in the system.
COMPASS_NAMESPACE = uuid.UUID("6f2d4f1e-9c3b-5a8d-b7e4-1c0a2d5f8b93")

SEC = "sec:company_tickers.json@2026-09-12"
SA = "stockanalysis.com/list/dow-jones-stocks@2026-09-05"
MANUAL = "manual:corporate-action"

# (ticker, legal name [SA], cik [SEC], sec registrant name [SEC])
DJIA = [
    ("NVDA",  "NVIDIA Corporation",                           1045810, "NVIDIA CORP"),
    ("AAPL",  "Apple Inc.",                                    320193, "Apple Inc."),
    ("GOOGL", "Alphabet Inc.",                                1652044, "Alphabet Inc."),
    ("MSFT",  "Microsoft Corporation",                         789019, "MICROSOFT CORP"),
    ("AMZN",  "Amazon.com, Inc.",                             1018724, "AMAZON COM INC"),
    ("JPM",   "JPMorgan Chase & Co.",                           19617, "JPMORGAN CHASE & CO"),
    ("WMT",   "Walmart Inc.",                                  104169, "Walmart Inc."),
    ("V",     "Visa Inc.",                                    1403161, "VISA INC."),
    ("JNJ",   "Johnson & Johnson",                             200406, "JOHNSON & JOHNSON"),
    ("CSCO",  "Cisco Systems, Inc.",                           858877, "CISCO SYSTEMS, INC."),
    ("CVX",   "Chevron Corporation",                            93410, "CHEVRON CORP"),
    ("KO",    "The Coca-Cola Company",                          21344, "COCA COLA CO"),
    ("CAT",   "Caterpillar Inc.",                               18230, "CATERPILLAR INC"),
    ("MRK",   "Merck & Co., Inc.",                             310158, "Merck & Co., Inc."),
    ("UNH",   "UnitedHealth Group Incorporated",               731766, "UNITEDHEALTH GROUP INC"),
    ("PG",    "The Procter & Gamble Company",                   80424, "PROCTER & GAMBLE Co"),
    ("HD",    "The Home Depot, Inc.",                          354950, "HOME DEPOT, INC."),
    ("GS",    "The Goldman Sachs Group, Inc.",                 886982, "GOLDMAN SACHS GROUP INC"),
    ("AMGN",  "Amgen Inc.",                                    318154, "AMGEN INC"),
    ("AXP",   "American Express Company",                        4962, "AMERICAN EXPRESS CO"),
    ("IBM",   "International Business Machines Corporation",    51143, "INTERNATIONAL BUSINESS MACHINES CORP"),
    ("CRM",   "Salesforce, Inc.",                              1108524, "Salesforce, Inc."),
    ("MCD",   "McDonald's Corporation",                          63908, "MCDONALDS CORP"),
    ("DIS",   "The Walt Disney Company",                       1744489, "Walt Disney Co"),
    ("BA",    "The Boeing Company",                              12927, "BOEING CO"),
    ("MMM",   "3M Company",                                      66740, "3M CO"),
    ("SHW",   "The Sherwin-Williams Company",                    89800, "SHERWIN WILLIAMS CO"),
    ("TRV",   "The Travelers Companies, Inc.",                   86312, "TRAVELERS COMPANIES, INC."),
    ("HON",   "Honeywell International Inc.",                   773840, "HONEYWELL INTERNATIONAL INC"),
    ("NKE",   "NIKE, Inc.",                                     320187, "NIKE, Inc."),
]

# Not a DJIA component. Included because it is the canonical demonstration of
# why entities need UUIDs: one company, two names, two tickers.
EXTRA = [
    ("META", "Meta Platforms, Inc.", 1326801, "Meta Platforms, Inc."),
]

# Superseded attribute values. valid_to on the historical record must equal
# valid_from on the record that replaced it.
# ticker -> attribute -> [(value, valid_from, valid_to)]
HISTORY = {
    "AAPL":  {"corporate_name": [("Apple Computer, Inc.", None, "2007-01-09")]},
    "GOOGL": {"corporate_name": [("Google Inc.", None, "2015-10-02")]},
    "MMM":   {"corporate_name": [("Minnesota Mining and Manufacturing Company", None, "2002-06-01")]},
    "CVX":   {"corporate_name": [("ChevronTexaco Corporation", "2001-10-09", "2005-05-09")]},
    "CRM":   {"corporate_name": [("salesforce.com, inc.", None, "2022-04-04")]},
    "META":  {
        "corporate_name":  [("Facebook, Inc.", None, "2021-10-28")],
        "exchange_ticker": [("FB", None, "2022-06-09")],
    },
}
# valid_from for the CURRENT record of an attribute that has history.
CURRENT_SINCE = {
    ("AAPL", "corporate_name"):  "2007-01-09",
    ("GOOGL", "corporate_name"): "2015-10-02",
    ("MMM", "corporate_name"):   "2002-06-01",
    ("CVX", "corporate_name"):   "2005-05-09",
    ("CRM", "corporate_name"):   "2022-04-04",
    ("META", "corporate_name"):  "2021-10-28",
    ("META", "exchange_ticker"): "2022-06-09",
}

ATTRIBUTES = [
    "corporate_name",
    "exchange_ticker",
    "cusip",
    "isin",
    "cik",
    "sec_registrant_name",
]


def entity_uuid(cik: int) -> str:
    """Deterministic, stable entity id. Same CIK always yields the same UUID."""
    return str(uuid.uuid5(COMPASS_NAMESPACE, f"cik:{cik:010d}"))


def record(value, valid_from=None, valid_to=None, source=SEC, verified=True):
    return {
        "value": value,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "source": source,
        "verified": verified,
    }


def build_entity(ticker, legal_name, cik, sec_name, in_djia):
    hist = HISTORY.get(ticker, {})
    attrs = {}

    def with_history(attr, current_record):
        records = [
            record(v, vf, vt, source=MANUAL, verified=False)
            for v, vf, vt in hist.get(attr, [])
        ]
        current_record["valid_from"] = CURRENT_SINCE.get((ticker, attr))
        records.append(current_record)
        return records

    attrs["corporate_name"] = with_history(
        "corporate_name", record(legal_name, source=SA))
    attrs["exchange_ticker"] = with_history(
        "exchange_ticker", record(ticker, source=SA))
    attrs["cik"] = [record(f"{cik:010d}", source=SEC)]
    attrs["sec_registrant_name"] = [record(sec_name, source=SEC)]

    # CUSIP is licensed data from CUSIP Global Services and is not in any
    # free authoritative feed. ISIN for a US issue is derived from CUSIP
    # (see entity_store.isin_from_cusip). Both are modeled and left empty
    # rather than populated with guesses.
    attrs["cusip"] = []
    attrs["isin"] = []

    return {
        "entity_id": entity_uuid(cik),
        "display_name": legal_name,
        "in_djia": in_djia,
        "attributes": attrs,
    }


# Index membership is a relationship (entity <-> index) over time, not a
# single-valued attribute, so it lives in its own file. An entity belongs to
# several indices at once; an attribute cannot.
#
# Per-constituent join dates are NOT loaded — every membership below carries
# valid_from=null, meaning "a member as far as this snapshot knows". Queries
# for a past date will therefore return today's membership, which is wrong
# for anything before 2026-09-05. Load real join/leave dates before using
# as_of for historical index work.
INDICES = [
    {
        "index_id": "DJIA",
        "name": "Dow Jones Industrial Average",
        "complete": True,
        "members": [row[0] for row in DJIA],
        "source": SA,
    },
    {
        "index_id": "SPX",
        "name": "S&P 500",
        "complete": False,
        "members": ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL"],
        "source": MANUAL,
    },
    {
        "index_id": "NDX",
        "name": "NASDAQ 100",
        "complete": False,
        "members": ["AAPL", "MSFT", "NVDA", "META"],
        "source": MANUAL,
    },
]


def build_indices(by_ticker):
    out = []
    for index in INDICES:
        members = []
        for ticker in index["members"]:
            members.append({
                "entity_id": by_ticker[ticker],
                "valid_from": None,
                "valid_to": None,
                "source": index["source"],
                "verified": index["source"] != MANUAL,
            })
        out.append({
            "index_id": index["index_id"],
            "name": index["name"],
            "complete": index["complete"],
            "membership_dates_loaded": False,
            "members": members,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./data/meta/entity.json")
    ap.add_argument("--indices-out", default="./data/index.json")
    args = ap.parse_args()

    entities = [build_entity(*row, in_djia=True) for row in DJIA]
    entities += [build_entity(*row, in_djia=False) for row in EXTRA]

    doc = {
        "schema_version": 1,
        "generated": date.today().isoformat(),
        "namespace": str(COMPASS_NAMESPACE),
        "attributes": ATTRIBUTES,
        "interval_semantics": (
            "Half-open [valid_from, valid_to). null valid_from = unbounded "
            "past; null valid_to = currently in effect."
        ),
        "entities": entities,
    }

    with open(args.out, "w") as fh:
        json.dump(doc, fh, indent=2)
    print(f"wrote {args.out}: {len(entities)} entities")

    by_ticker = {}
    for row, entity in zip(DJIA + EXTRA, entities):
        by_ticker[row[0]] = entity["entity_id"]

    index_doc = {
        "schema_version": 1,
        "generated": date.today().isoformat(),
        "interval_semantics": (
            "Half-open [valid_from, valid_to). null valid_from = membership "
            "start not loaded; null valid_to = currently a member."
        ),
        "indices": build_indices(by_ticker),
    }
    with open(args.indices_out, "w") as fh:
        json.dump(index_doc, fh, indent=2)
    counts = ", ".join(f"{i['index_id']}={len(i['members'])}"
                       for i in index_doc["indices"])
    print(f"wrote {args.indices_out}: {counts}")


if __name__ == "__main__":
    main()