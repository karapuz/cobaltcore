"""Tests for the temporal entity store.  Run: python -m pytest test_entity_store.py -q"""

import json
import os
import tempfile
from datetime import date

import pytest

from entity import entity_store as entities
from entity.entity_store import (
    AmbiguousResolution,
    AttributeNotFound,
    EntityNotFound,
    EntityStore,
    OverlappingIntervals,
    isin_from_cusip,
)

STORE = entities.get_store()


def uid(ticker, as_of=None):
    return entities.resolve_one("exchange_ticker", ticker, as_of)


# ---------------------------------------------------------------- core query

def test_djia_has_thirty_components():
    assert len(STORE.list_entities(djia_only=True)) == 30


def test_attribute_as_of_date():
    apple = uid("AAPL")
    assert STORE.get_value(apple, "corporate_name", "2006-12-31") == "Apple Computer, Inc."
    assert STORE.get_value(apple, "corporate_name", "2010-01-01") == "Apple Inc."


def test_interval_is_half_open_at_the_boundary():
    """On the change date the NEW value applies, not the old one."""
    apple = uid("AAPL")
    assert STORE.get_value(apple, "corporate_name", "2007-01-08") == "Apple Computer, Inc."
    assert STORE.get_value(apple, "corporate_name", "2007-01-09") == "Apple Inc."


def test_cik_is_zero_padded_ten_digits():
    assert STORE.get_value(uid("AAPL"), "cik") == "0000320193"
    assert STORE.get_value(uid("AXP"), "cik") == "0000004962"


def test_unknown_entity_and_attribute_raise():
    with pytest.raises(EntityNotFound):
        STORE.get_value("not-a-uuid", "corporate_name")
    with pytest.raises(AttributeNotFound):
        STORE.get_value(uid("AAPL"), "favourite_colour")


def test_licensed_attribute_is_modeled_but_empty():
    """CUSIP is declared, has no value, and does NOT raise."""
    assert "cusip" in STORE.attributes
    assert STORE.get_value(uid("AAPL"), "cusip") is None


# ------------------------------------------------------------ identity churn

def test_one_entity_survives_rename_and_reticker():
    """The Facebook/Meta case: same UUID before and after both changes."""
    then = uid("FB", "2019-01-01")
    now = uid("META")
    assert then == now

    assert STORE.get_value(then, "corporate_name", "2019-01-01") == "Facebook, Inc."
    assert STORE.get_value(then, "corporate_name", "2026-01-01") == "Meta Platforms, Inc."


def test_ticker_change_lags_name_change():
    """Renamed 2021-10-28, reticker 2022-06-09 — the gap is real, not a bug."""
    meta = uid("META")
    assert STORE.get_value(meta, "corporate_name", "2022-01-01") == "Meta Platforms, Inc."
    assert STORE.get_value(meta, "exchange_ticker", "2022-01-01") == "FB"


def test_retired_ticker_resolves_to_nothing_today():
    assert STORE.resolve("exchange_ticker", "FB") == []


def test_uuid_is_deterministic_across_rebuilds():
    """Rebuilding the file must not renumber entities."""
    assert uid("AAPL") == EntityStore().resolve("exchange_ticker", "AAPL")[0]


def test_module_level_functions_share_one_store():
    """Callers in-process get the same loaded object, not a re-parse."""
    assert entities.get_store() is entities.get_store()
    assert len(entities.get_store()) == 31


def test_resolve_one_raises_instead_of_guessing():
    with pytest.raises(EntityNotFound):
        entities.resolve_one("exchange_ticker", "FB")          # retired today
    with pytest.raises(EntityNotFound):
        entities.resolve_one("exchange_ticker", "NOPE")


def test_resolve_one_rejects_ambiguity():
    """A reused ticker must raise, never silently pick the first match."""
    store = EntityStore()
    store._index[("exchange_ticker", "DUP")] = [
        ("e1", date.min, date.max), ("e2", date.min, date.max)]
    with pytest.raises(AmbiguousResolution):
        store.resolve_one("exchange_ticker", "DUP")


def test_history_hides_internal_fields():
    for rec in entities.history(uid("AAPL"), "corporate_name"):
        assert not any(k.startswith("_") for k in rec)


# ---------------------------------------------------------------- validation

def test_overlapping_intervals_are_rejected_at_load():
    doc = {
        "schema_version": 1,
        "attributes": ["corporate_name"],
        "entities": [{
            "entity_id": "e1",
            "display_name": "Overlapping Co",
            "attributes": {"corporate_name": [
                {"value": "Old", "valid_from": None, "valid_to": "2020-01-01"},
                {"value": "New", "valid_from": "2019-01-01", "valid_to": None},
            ]},
        }],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(doc, fh)
        path = fh.name
    with pytest.raises(OverlappingIntervals):
        EntityStore(path)


# ---------------------------------------------------------------------- ISIN

@pytest.mark.parametrize("cusip,isin", [
    ("037833100", "US0378331005"),   # Apple
    ("594918104", "US5949181045"),   # Microsoft
    ("478160104", "US4781601046"),   # Johnson & Johnson
])
def test_isin_check_digit(cusip, isin):
    assert isin_from_cusip(cusip) == isin


def test_isin_rejects_bad_length():
    with pytest.raises(ValueError):
        isin_from_cusip("0378331")


# ------------------------------------------------------- data layout errors

def test_missing_index_file_raises_rather_than_returning_empty():
    """An absent indices.json must not present as 'there are no indices'."""
    import shutil
    with tempfile.TemporaryDirectory() as meta:
        shutil.copy(STORE.path, os.path.join(meta, "entity.json"))
        with pytest.raises(FileNotFoundError) as exc:
            EntityStore(os.path.join(meta, "entity.json"),
                        os.path.join(meta, "index.json"))
        assert "index.json" in str(exc.value)


def test_missing_entity_file_raises_with_the_expected_location():
    with tempfile.TemporaryDirectory() as meta:
        with pytest.raises(FileNotFoundError) as exc:
            EntityStore(os.path.join(meta, "entity.json"))
        assert "entity.json" in str(exc.value)