"""Tests for the per-entity model store.  Run: python -m pytest test_model_store.py -q"""

import json
import os
import tempfile

import pytest

from model_data.model_store import (
    DEFAULT_RANGES,
    DEFAULT_VELOCITY,
    DEFAULT_WEIGHTS,
    InvalidModelInput,
    ModelStore,
    UnknownComponent,
    validate_ranges,
    validate_velocity,
    validate_weights,
)

UID = "11ef028b-08db-5625-b3f5-ea8b87ac96b0"   # Apple
OTHER = "c51dab33-e003-5c1d-9216-e86c64bdc386"  # NVIDIA


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as directory:
        yield ModelStore(directory)


# ------------------------------------------------------------------ reading

def test_uncustomised_entity_gets_defaults(store):
    record = store.get_record(UID, "velocity")
    assert record["value"] == DEFAULT_VELOCITY
    assert record["is_default"] is True
    assert record["revision"] == 0
    assert not store.is_customised(UID, "velocity")


def test_velocity_is_per_entity(store):
    store.update(UID, "velocity", {"revenue": 1.10})
    assert store.get(UID, "velocity")["revenue"] == 1.10
    assert store.get(OTHER, "velocity")["revenue"] == DEFAULT_VELOCITY["revenue"]


# ------------------------------------------------------------- persistence

def test_every_edit_is_persisted_immediately(store):
    store.update(UID, "velocity", {"revenue": 1.05})
    path = os.path.join(store.directory, f"{UID}.json")
    assert os.path.exists(path), "edit must hit disk before the call returns"
    with open(path) as fh:
        doc = json.load(fh)
    assert doc["components"]["velocity"]["revisions"][-1]["value"]["revenue"] == 1.05


def test_file_is_named_for_the_entity_uuid(store):
    store.update(UID, "velocity", {"ebitda": 1.04})
    assert store.list_customised() == [UID]


def test_edits_append_revisions_rather_than_overwrite(store):
    store.update(UID, "velocity", {"revenue": 1.05}, actor="ilya", note="first")
    store.update(UID, "velocity", {"revenue": 1.06}, actor="ilya", note="second")
    revisions = store.history(UID, "velocity")
    assert [r["revision"] for r in revisions] == [1, 2]
    assert [r["value"]["revenue"] for r in revisions] == [1.05, 1.06]
    assert revisions[-1]["actor"] == "ilya"


def test_latest_revision_is_the_one_used(store):
    for value in (1.04, 1.07, 1.02):
        store.update(UID, "velocity", {"revenue": value})
    assert store.get(UID, "velocity")["revenue"] == 1.02
    assert store.get_record(UID, "velocity")["revision"] == 3


def test_partial_update_leaves_other_fields_alone(store):
    store.update(UID, "velocity", {"revenue": 1.09})
    velocity = store.get(UID, "velocity")
    assert velocity["revenue"] == 1.09
    assert velocity["ebitda"] == DEFAULT_VELOCITY["ebitda"]
    assert set(velocity) == set(DEFAULT_VELOCITY)


def test_external_edit_is_picked_up(store):
    """Another process writing the file must not be served stale."""
    store.update(UID, "velocity", {"revenue": 1.05})
    assert store.get(UID, "velocity")["revenue"] == 1.05

    path = os.path.join(store.directory, f"{UID}.json")
    with open(path) as fh:
        doc = json.load(fh)
    doc["components"]["velocity"]["revisions"].append({
        "revision": 2, "value": dict(DEFAULT_VELOCITY, revenue=1.20),
        "updated_at": "2026-09-14T00:00:00+00:00", "actor": "someone-else",
        "note": "out of band",
    })
    with open(path, "w") as fh:
        json.dump(doc, fh)

    assert store.get(UID, "velocity")["revenue"] == 1.20


def test_reset_records_a_revision_rather_than_deleting(store):
    store.update(UID, "velocity", {"revenue": 1.15})
    record = store.reset(UID, "velocity")
    assert record["value"] == DEFAULT_VELOCITY
    assert record["is_default"] is False, "reverted is not the same as never set"
    assert len(store.history(UID, "velocity")) == 2


# -------------------------------------------------------------- validation

def test_unknown_field_is_rejected_not_dropped(store):
    with pytest.raises(InvalidModelInput) as exc:
        store.update(UID, "velocity", {"revenu": 1.05})
    assert "revenu" in str(exc.value)
    assert not store.is_customised(UID, "velocity")


@pytest.mark.parametrize("bad", [15, 0, -1, 5])
def test_out_of_band_values_are_rejected(store, bad):
    """A percentage or a typo must not be accepted as a multiplier."""
    with pytest.raises(InvalidModelInput):
        store.update(UID, "velocity", {"revenue": bad})


def test_non_numeric_is_rejected(store):
    with pytest.raises(InvalidModelInput):
        store.update(UID, "velocity", {"revenue": "1.05"})
    with pytest.raises(InvalidModelInput):
        store.update(UID, "velocity", {"revenue": True})


def test_full_set_requires_every_field(store):
    with pytest.raises(InvalidModelInput) as exc:
        store.set_component(UID, "velocity", {"revenue": 1.05})
    assert "missing" in str(exc.value)


def test_validate_accepts_the_defaults():
    assert validate_velocity(DEFAULT_VELOCITY) == DEFAULT_VELOCITY
    assert validate_weights(DEFAULT_WEIGHTS) == DEFAULT_WEIGHTS
    assert validate_ranges(DEFAULT_RANGES) == DEFAULT_RANGES


def test_entity_id_cannot_escape_the_directory(store):
    with pytest.raises(InvalidModelInput):
        store.update("../../etc/passwd", "velocity", {"revenue": 1.05})


# --------------------------------------------------- weights and ranges

def test_components_version_independently(store):
    store.update(UID, "velocity", {"revenue": 1.05})
    store.update(UID, "weights", {"fcf_debt": 0.25, "td_ebitda": 0.15})
    assert store.get_record(UID, "velocity")["revision"] == 1
    assert store.get_record(UID, "weights")["revision"] == 1
    assert store.get_record(UID, "ranges")["is_default"] is True

    store.update(UID, "weights", {"fcf_debt": 0.20, "td_ebitda": 0.20})
    assert store.get_record(UID, "weights")["revision"] == 2
    assert store.get_record(UID, "velocity")["revision"] == 1, "unrelated bump"


def test_all_components_share_one_file(store):
    store.update(UID, "weights", {"fcf_debt": 0.25, "td_ebitda": 0.15})
    store.update(UID, "ranges", {"ebitda_margin": [0.4, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.02]})
    assert store.list_customised() == [UID]
    with open(store.path_for(UID)) as fh:
        doc = json.load(fh)
    assert set(doc["components"]) == {"weights", "ranges"}


def test_weights_must_sum_to_one(store):
    with pytest.raises(InvalidModelInput) as exc:
        store.update(UID, "weights", {"fcf_debt": 0.30})   # merged sum = 1.10
    assert "sum to 1.0" in str(exc.value)
    assert not store.is_customised(UID, "weights")


def test_partial_weight_edit_that_rebalances_is_accepted(store):
    record = store.update(UID, "weights", {"fcf_debt": 0.25, "td_ebitda": 0.15})
    assert record["value"]["fcf_debt"] == 0.25
    assert abs(sum(record["value"].values()) - 1.0) < 1e-9


def test_weight_rejects_percentage(store):
    with pytest.raises(InvalidModelInput):
        store.update(UID, "weights", {"fcf_debt": 20})


def test_ranges_must_run_best_to_worst(store):
    """A non-monotonic breakpoint would create an unreachable bucket."""
    with pytest.raises(InvalidModelInput) as exc:
        store.update(UID, "ranges",
                     {"ebitda_margin": [0.35, 0.30, 0.31, 0.20, 0.15, 0.10, 0.05, 0.02]})
    assert "descend" in str(exc.value)


def test_ranges_direction_is_per_pillar(store):
    """td_ebitda is lower-is-better, so its breakpoints must ascend."""
    store.update(UID, "ranges", {"td_ebitda": [0.8, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]})
    with pytest.raises(InvalidModelInput) as exc:
        store.update(UID, "ranges", {"td_ebitda": [8, 7, 6, 5, 4, 3, 2, 1]})
    assert "ascend" in str(exc.value)


def test_ranges_need_exactly_eight_breakpoints(store):
    with pytest.raises(InvalidModelInput) as exc:
        store.update(UID, "ranges", {"ebitda_margin": [0.3, 0.2, 0.1]})
    assert "8 breakpoints" in str(exc.value)


def test_unknown_component_raises(store):
    with pytest.raises(UnknownComponent):
        store.get(UID, "wieghts")


def test_get_all_returns_every_component(store):
    store.update(UID, "weights", {"fcf_debt": 0.25, "td_ebitda": 0.15})
    everything = store.get_all(UID)
    assert set(everything) == {"velocity", "weights", "ranges"}
    assert everything["weights"]["revision"] == 1
    assert everything["velocity"]["is_default"] is True


def test_schema_1_velocity_file_is_migrated(store):
    """Files written before weights/ranges existed must still load."""
    os.makedirs(store.directory, exist_ok=True)
    legacy = {
        "schema_version": 1, "entity_id": UID, "model_version": "v0",
        # The real schema-1 shape: payload under "velocity", no "value" key.
        "revisions": [{"revision": 1,
                       "velocity": dict(DEFAULT_VELOCITY, revenue=1.07),
                       "updated_at": "2026-09-01T00:00:00+00:00",
                       "actor": "ilya", "note": "legacy"}],
    }
    with open(store.path_for(UID), "w") as fh:
        json.dump(legacy, fh)
    assert store.get(UID, "velocity")["revenue"] == 1.07
    assert store.get_record(UID, "weights")["is_default"] is True


def test_migrated_file_survives_a_later_edit(store):
    """After migration, a new revision must append to the legacy history."""
    os.makedirs(store.directory, exist_ok=True)
    legacy = {
        "schema_version": 1, "entity_id": UID, "model_version": "v0",
        "revisions": [{"revision": 1, "velocity": dict(DEFAULT_VELOCITY, revenue=1.07),
                       "updated_at": "2026-09-01T00:00:00+00:00",
                       "actor": "ilya", "note": "legacy"}],
    }
    with open(store.path_for(UID), "w") as fh:
        json.dump(legacy, fh)

    record = store.update(UID, "velocity", {"revenue": 1.09})
    assert record["revision"] == 2
    assert store.get(UID, "velocity")["revenue"] == 1.09
    with open(store.path_for(UID)) as fh:
        doc = json.load(fh)
    assert doc["schema_version"] == 2
    assert all("value" in r for r in doc["components"]["velocity"]["revisions"])


def test_legacy_file_migrates_for_every_entity_in_the_directory(store):
    """Regression: get_all() walks all three components over a legacy file."""
    os.makedirs(store.directory, exist_ok=True)
    legacy = {
        "schema_version": 1, "entity_id": OTHER, "model_version": "v0",
        "revisions": [{"revision": 1, "velocity": dict(DEFAULT_VELOCITY),
                       "updated_at": "2026-09-01T00:00:00+00:00",
                       "actor": None, "note": None}],
    }
    with open(store.path_for(OTHER), "w") as fh:
        json.dump(legacy, fh)

    everything = store.get_all(OTHER)
    assert everything["velocity"]["revision"] == 1
    assert everything["weights"]["is_default"] is True
    assert everything["ranges"]["is_default"] is True