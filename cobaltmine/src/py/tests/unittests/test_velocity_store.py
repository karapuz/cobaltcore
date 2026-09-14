"""Tests for the per-entity velocity store.  Run: python -m pytest test_velocity_store.py -q"""

import json
import os
import tempfile

import pytest

from model_data.velocity_store import (
    DEFAULT_VELOCITY,
    InvalidVelocity,
    VelocityStore,
    validate,
)

UID = "11ef028b-08db-5625-b3f5-ea8b87ac96b0"   # Apple
OTHER = "c51dab33-e003-5c1d-9216-e86c64bdc386"  # NVIDIA


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as directory:
        yield VelocityStore(directory)


# ------------------------------------------------------------------ reading

def test_uncustomised_entity_gets_defaults(store):
    record = store.get_record(UID)
    assert record["velocity"] == DEFAULT_VELOCITY
    assert record["is_default"] is True
    assert record["revision"] == 0
    assert not store.is_customised(UID)


def test_velocity_is_per_entity(store):
    store.update(UID, {"revenue": 1.10})
    assert store.get(UID)["revenue"] == 1.10
    assert store.get(OTHER)["revenue"] == DEFAULT_VELOCITY["revenue"]


# ------------------------------------------------------------- persistence

def test_every_edit_is_persisted_immediately(store):
    store.update(UID, {"revenue": 1.05})
    path = os.path.join(store.directory, f"{UID}.json")
    assert os.path.exists(path), "edit must hit disk before the call returns"
    with open(path) as fh:
        assert json.load(fh)["revisions"][-1]["velocity"]["revenue"] == 1.05


def test_file_is_named_for_the_entity_uuid(store):
    store.update(UID, {"ebitda": 1.04})
    assert store.list_customised() == [UID]


def test_edits_append_revisions_rather_than_overwrite(store):
    store.update(UID, {"revenue": 1.05}, actor="ilya", note="first")
    store.update(UID, {"revenue": 1.06}, actor="ilya", note="second")
    revisions = store.history(UID)
    assert [r["revision"] for r in revisions] == [1, 2]
    assert [r["velocity"]["revenue"] for r in revisions] == [1.05, 1.06]
    assert revisions[-1]["actor"] == "ilya"


def test_latest_revision_is_the_one_used(store):
    for value in (1.04, 1.07, 1.02):
        store.update(UID, {"revenue": value})
    assert store.get(UID)["revenue"] == 1.02
    assert store.get_record(UID)["revision"] == 3


def test_partial_update_leaves_other_fields_alone(store):
    store.update(UID, {"revenue": 1.09})
    velocity = store.get(UID)
    assert velocity["revenue"] == 1.09
    assert velocity["ebitda"] == DEFAULT_VELOCITY["ebitda"]
    assert set(velocity) == set(DEFAULT_VELOCITY)


def test_external_edit_is_picked_up(store):
    """Another process writing the file must not be served stale."""
    store.update(UID, {"revenue": 1.05})
    assert store.get(UID)["revenue"] == 1.05

    path = os.path.join(store.directory, f"{UID}.json")
    with open(path) as fh:
        doc = json.load(fh)
    doc["revisions"].append({
        "revision": 2, "velocity": dict(DEFAULT_VELOCITY, revenue=1.20),
        "updated_at": "2026-09-14T00:00:00+00:00", "actor": "someone-else",
        "note": "out of band",
    })
    with open(path, "w") as fh:
        json.dump(doc, fh)

    assert store.get(UID)["revenue"] == 1.20


def test_reset_records_a_revision_rather_than_deleting(store):
    store.update(UID, {"revenue": 1.15})
    record = store.reset(UID)
    assert record["velocity"] == DEFAULT_VELOCITY
    assert record["is_default"] is False, "reverted is not the same as never set"
    assert len(store.history(UID)) == 2


# -------------------------------------------------------------- validation

def test_unknown_field_is_rejected_not_dropped(store):
    with pytest.raises(InvalidVelocity) as exc:
        store.update(UID, {"revenu": 1.05})
    assert "revenu" in str(exc.value)
    assert not store.is_customised(UID)


@pytest.mark.parametrize("bad", [15, 0, -1, 5])
def test_out_of_band_values_are_rejected(store, bad):
    """A percentage or a typo must not be accepted as a multiplier."""
    with pytest.raises(InvalidVelocity):
        store.update(UID, {"revenue": bad})


def test_non_numeric_is_rejected(store):
    with pytest.raises(InvalidVelocity):
        store.update(UID, {"revenue": "1.05"})
    with pytest.raises(InvalidVelocity):
        store.update(UID, {"revenue": True})


def test_full_set_requires_every_field(store):
    with pytest.raises(InvalidVelocity) as exc:
        store.set(UID, {"revenue": 1.05})
    assert "missing" in str(exc.value)


def test_validate_accepts_the_defaults():
    assert validate(DEFAULT_VELOCITY) == DEFAULT_VELOCITY


def test_entity_id_cannot_escape_the_directory(store):
    with pytest.raises(InvalidVelocity):
        store.update("../../etc/passwd", {"revenue": 1.05})