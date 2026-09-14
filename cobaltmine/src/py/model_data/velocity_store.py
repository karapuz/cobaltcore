"""
Per-entity projection velocity — in-process library.

Projection velocity is the per-year multiplier applied to each basic
financial when building forecast horizons. It used to be one global table;
it is now per entity, editable, and persisted on every change.

    from model_data import velocity_store as velocities

    velocities.get(entity_id)                      # latest, or defaults
    velocities.update(entity_id, {"revenue": 1.05}, note="analyst override")
    velocities.set_velocity(entity_id, full_mapping)
    velocities.reset(entity_id)                    # back to defaults

Storage is one file per entity at:

    data/model_data/v0/{ENTITY_UUID}.json

Each file keeps the full revision history; the last revision is the live
one. A ratings engine has to be able to answer "what velocity produced this
number, and who set it", so edits append rather than overwrite.

An entity with no file uses DEFAULT_VELOCITY and is not written to disk —
absence means "never customised", which is different from "explicitly set
back to the defaults".
"""

import json
import os
import tempfile
import threading
from datetime import datetime, timezone

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("COMPASS_DATA_DIR",
                          os.path.join(_PROJECT_ROOT, "data"))
MODEL_VERSION = "v0"
VELOCITY_DIR = os.environ.get(
    "COMPASS_VELOCITY_DIR",
    os.path.join(DATA_DIR, "model_data", MODEL_VERSION))

SCHEMA_VERSION = 1

# Applied once per forecast year and compounded, so 1.0 means "flat" and
# anything at or below 0 is meaningless rather than merely aggressive.
DEFAULT_VELOCITY = {
    "revenue": 1.03,
    "ebitda": 1.02,
    "free_cash_flow": 1.0,
    "debt": 1.0,
    "total_debt": 1.0,
    "net_debt": 1.0,
    "interest": 1.01,
    "operating_cash_flow": 1.0,
    "short_term_debt": 1.0,
}

VELOCITY_FIELDS = frozenset(DEFAULT_VELOCITY)

# Guard rails on hand-entered values. A velocity outside this band is almost
# always a typo (1.5 entered as 15, or a percentage entered as 5).
MIN_VELOCITY = 0.5
MAX_VELOCITY = 2.0


class InvalidVelocity(ValueError):
    pass


def _safe_name(entity_id):
    """entity_id becomes a filename, so it must not contain path syntax."""
    if not entity_id or os.sep in str(entity_id) or ".." in str(entity_id):
        raise InvalidVelocity(f"unsafe entity_id {entity_id!r}")
    return f"{entity_id}.json"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate(velocity, partial=False):
    """
    Check a velocity mapping and return it with float values.

    Rejects unknown keys outright: silently dropping a misspelled field
    would leave the caller believing an edit took effect when it did not.
    """
    if not isinstance(velocity, dict):
        raise InvalidVelocity("velocity must be a mapping")

    unknown = set(velocity) - VELOCITY_FIELDS
    if unknown:
        raise InvalidVelocity(
            f"unknown velocity field(s): {sorted(unknown)}; "
            f"known: {sorted(VELOCITY_FIELDS)}")

    if not partial:
        missing = VELOCITY_FIELDS - set(velocity)
        if missing:
            raise InvalidVelocity(f"missing velocity field(s): {sorted(missing)}")

    cleaned = {}
    for field, value in velocity.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidVelocity(f"{field}: velocity must be a number, got {value!r}")
        value = float(value)
        if not MIN_VELOCITY <= value <= MAX_VELOCITY:
            raise InvalidVelocity(
                f"{field}: velocity {value} outside [{MIN_VELOCITY}, "
                f"{MAX_VELOCITY}] — a multiplier, not a percentage")
        cleaned[field] = value
    return cleaned


class VelocityStore:
    """
    One JSON file per entity. Reads go to disk and are cached on (mtime,
    size), so a file edited by another process or by hand is picked up on
    the next call rather than served stale from memory for the life of the
    process. Requirement is "use the latest value" — that has to include
    edits this process did not make.
    """

    def __init__(self, directory=VELOCITY_DIR):
        self.directory = directory
        self._lock = threading.Lock()
        self._cache = {}

    # ----------------------------------------------------------------- read

    def path_for(self, entity_id):
        """Where this entity's velocity file lives, per THIS store's
        directory — not the module default, or a store pointed at a
        snapshot would read one file and write another."""
        return os.path.join(self.directory, _safe_name(entity_id))

    def _read_document(self, entity_id):
        path = self.path_for(entity_id)
        try:
            stat = os.stat(path)
        except FileNotFoundError:
            self._cache.pop(entity_id, None)
            return None

        stamp = (stat.st_mtime_ns, stat.st_size)
        cached = self._cache.get(entity_id)
        if cached and cached[0] == stamp:
            return cached[1]

        with open(path) as fh:
            doc = json.load(fh)
        self._cache[entity_id] = (stamp, doc)
        return doc

    def get_record(self, entity_id):
        """
        Latest revision for this entity, or the synthetic default record.

        Always returns something — every entity has a velocity, whether or
        not anyone has edited it.
        """
        doc = self._read_document(entity_id)
        if doc is None or not doc.get("revisions"):
            return {
                "entity_id": entity_id,
                "velocity": dict(DEFAULT_VELOCITY),
                "revision": 0,
                "is_default": True,
                "updated_at": None,
                "actor": None,
                "note": "defaults; never customised",
            }
        latest = doc["revisions"][-1]
        return {
            "entity_id": entity_id,
            "velocity": latest["velocity"],
            "revision": latest["revision"],
            "is_default": False,
            "updated_at": latest.get("updated_at"),
            "actor": latest.get("actor"),
            "note": latest.get("note"),
        }

    def get(self, entity_id):
        """Just the velocity mapping in effect."""
        return self.get_record(entity_id)["velocity"]

    def history(self, entity_id):
        """Every revision, oldest first. Empty if never customised."""
        doc = self._read_document(entity_id)
        return list(doc["revisions"]) if doc else []

    def is_customised(self, entity_id):
        return self._read_document(entity_id) is not None

    # ---------------------------------------------------------------- write

    def set(self, entity_id, velocity, actor=None, note=None):
        """
        Persist a complete velocity mapping as a new revision.

        Every modification is written before this returns; there is no
        in-memory-only state to flush.
        """
        cleaned = validate(velocity)
        return self._append(entity_id, cleaned, actor, note)

    def update(self, entity_id, partial, actor=None, note=None):
        """Merge a partial mapping over the current one and persist it."""
        changes = validate(partial, partial=True)
        if not changes:
            raise InvalidVelocity("no fields to update")
        merged = dict(self.get(entity_id))
        merged.update(changes)
        return self._append(entity_id, merged, actor, note)

    def reset(self, entity_id, actor=None, note=None):
        """
        Record an explicit return to the defaults.

        Appends a revision rather than deleting the file: "was customised,
        then reverted" is different from "never touched", and a ratings
        engine should be able to tell them apart.
        """
        return self._append(entity_id, dict(DEFAULT_VELOCITY), actor,
                            note or "reset to defaults")

    def _append(self, entity_id, velocity, actor, note):
        path = self.path_for(entity_id)
        with self._lock:
            doc = self._read_document(entity_id) or {
                "schema_version": SCHEMA_VERSION,
                "entity_id": entity_id,
                "model_version": MODEL_VERSION,
                "revisions": [],
            }
            revision = {
                "revision": len(doc["revisions"]) + 1,
                "velocity": velocity,
                "updated_at": _now(),
                "actor": actor,
                "note": note,
            }
            doc = dict(doc, revisions=doc["revisions"] + [revision])
            self._write_atomic(path, doc)
            self._cache.pop(entity_id, None)   # re-stat on next read
        return self.get_record(entity_id)

    def _write_atomic(self, path, doc):
        """
        Write to a temp file in the same directory, then rename.

        A half-written velocity file would be a corrupt model input that
        fails at load time for every future run; rename is atomic on POSIX,
        so a crash mid-write leaves the previous revision intact.
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        handle, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        try:
            with os.fdopen(handle, "w") as fh:
                json.dump(doc, fh, indent=2)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    def list_customised(self):
        """Entity ids that have a velocity file."""
        if not os.path.isdir(self.directory):
            return []
        return sorted(name[:-5] for name in os.listdir(self.directory)
                      if name.endswith(".json"))


# ------------------------------------------------------------ shared store

_shared = None
_shared_lock = threading.Lock()


def get_store(directory=VELOCITY_DIR):
    global _shared
    if _shared is None:
        with _shared_lock:
            if _shared is None:
                _shared = VelocityStore(directory)
    return _shared


def get(entity_id):
    return get_store().get(entity_id)


def get_record(entity_id):
    return get_store().get_record(entity_id)


def set_velocity(entity_id, velocity, actor=None, note=None):
    """Named set_velocity, not set: a module-level `set` shadows the builtin
    for every function in this module, including validate()."""
    return get_store().set(entity_id, velocity, actor, note)


def update(entity_id, partial, actor=None, note=None):
    return get_store().update(entity_id, partial, actor, note)


def reset(entity_id, actor=None, note=None):
    return get_store().reset(entity_id, actor, note)


def history(entity_id):
    return get_store().history(entity_id)


def is_customised(entity_id):
    return get_store().is_customised(entity_id)


def list_customised():
    return get_store().list_customised()