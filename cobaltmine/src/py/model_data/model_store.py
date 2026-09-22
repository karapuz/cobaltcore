"""
Per-entity model inputs — in-process library.

Three things are stored per entity, each with its own independent revision
history: projection velocity, pillar weights, and pillar ranges
(breakpoints). All three live in one file per entity:

    data/model_data/v0/{ENTITY_UUID}.json

    from model_data import model_store as model

    model.get(entity_id, "weights")                     # latest, or defaults
    model.update(entity_id, "weights", {"fcf_debt": 0.30})
    model.set_component(entity_id, "ranges", full_map)
    model.reset(entity_id, "velocity")

Components are versioned separately on purpose: editing a weight should not
invalidate the velocity revision that a rating was produced under, and the
audit answer to "what produced this number" is a triple of revisions, not
one. An entity with no file uses the defaults for all three and is not
written to disk — absence means "never customised", which is different from
"explicitly reset to defaults".
"""

import copy
import json
import os
import tempfile
import threading
from datetime import datetime, timezone

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("COMPASS_DATA_DIR",
                          os.path.join(_PROJECT_ROOT, "data"))
MODEL_VERSION = "v0"
MODEL_DIR = os.environ.get(
    "COMPASS_MODEL_DIR",
    os.path.join(DATA_DIR, "model_data", MODEL_VERSION))

SCHEMA_VERSION = 2

PILLAR_IDS = (
    "revenue_scale", "ebitda_margin", "fcf_debt",
    "td_ebitda", "nd_ebitda", "ebitda_interest",
)

# True = higher is better. Ranges must run best-to-worst, so the direction
# decides whether breakpoints descend or ascend.
PILLAR_DIRECTION = {
    "revenue_scale": True,
    "ebitda_margin": True,
    "fcf_debt": True,
    "td_ebitda": False,
    "nd_ebitda": False,
    "ebitda_interest": True,
}

RANGE_BREAKPOINTS = 8   # eight cut points produce nine rating buckets

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

# 6 pillars with weights summing to 100%
DEFAULT_RANGES = {
    "revenue_scale":    [60.0, 30.0, 15.0,  4.0,  1.0,  0.1,  0.02],
    "ebitda_margin":    [ 0.5,  0.4,  0.3,  0.2,  0.15, 0.10, 0.05],
    "fcf_debt":         [ 0.45, 0.35, 0.25, 0.15, 0.08, 0.0, -0.08],
    "td_ebitda":        [ 0.5,  1.0,  2.0,  3.5,  5.0,  7.0,  9.5],
    "nd_ebitda":        [ 0.0,  0.5,  1.5,  3.0,  4.5,  6.8,  9.3],
    "ebitda_interest":  [50.0, 30.0, 15.0,  7.0,  4.0,  1.5,  1.0],
}


# Weights sum to 100%
DEFAULT_WEIGHTS = {
    "revenue_scale":    0.15,
    "ebitda_margin":    0.15,
    "fcf_debt":         0.20,
    "td_ebitda":        0.20,
    "nd_ebitda":        0.15,
    "ebitda_interest":  0.15,
}

PILLAR_DIRECTION = {
    "revenue_scale": True,      # higher = better
    "ebitda_margin": True,      # higher = better
    "fcf_debt": True,           # higher = better
    "td_ebitda": False,         # lower = better
    "nd_ebitda": False,         # lower = better
    "ebitda_interest": True,    # higher = better
}

PILLAR_NAMES = {
    "revenue_scale": "Revenue Scale",
    "ebitda_margin": "EBITDA Margin",
    "fcf_debt": "Free Cash Flow / Debt",
    "td_ebitda": "Total Debt / EBITDA",
    "nd_ebitda": "Net Debt / EBITDA",
    "ebitda_interest": "EBITDA / Interest",
}

# Numeric rank to letter rating (0 = best, 8 = worst)
RANK_TO_RATING = {
    0: "AAA",
    1: "AA+",
    2: "AA",
    3: "AA-",
    4: "A+",
    5: "A",
    6: "A-",
    7: "BBB+",
    8: "BBB",
}

# Ordered rating scale for notch adjustments
RATING_ORDER = [
    "AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
    "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
    "B+", "B", "B-", "CCC+", "CCC", "CCC-", "CC", "C", "D"
]

RATING_SCALE = [
    ("AAA",   0.0,  1.5),
    ("AA+",   1.5,  2.5),
    ("AA",    2.5,  3.5),
    ("AA-",   3.5,  4.5),
    ("A+",    4.5,  5.5),
    ("A",     5.5,  6.5),
    ("A-",    6.5,  7.5),
    ("BBB+",  7.5,  8.5),
    ("BBB",   8.5,  9.5),
    ("BBB-",  9.5, 10.5),
    ("BB+",  10.5, 11.5),
    ("BB",   11.5, 12.5),
    ("BB-",  12.5, 13.5),
    ("B+",   13.5, 14.5),
    ("B",    14.5, 15.5),
    ("B-",   15.5, 16.5),
    ("CCC+", 16.5, 17.5),
    ("CCC",  17.5, 18.5),
    ("CCC-", 18.5, 19.5),
    ("CC",   19.5, 20.5),
]

"""
AAA:    1
AA+:    2
AA:     3
AA-:    4
A+:     5
A:      6
A-:     7
BBB+:   8
BBB:    9
BBB-:   10
BB+:    11
BB:     12
BB-:    13
B+:     14
B:      15
B-:     16
CCC+:   17
CCC:    18
CCC-:   19
CC:     20

Revenue
>$60
$30.0 - 60.0
$15.0 - 30.0
$4.0 - 15.0
$1.0 - 4.0
$0.1 - 1.0
$0.02 - 0.1
<$0.02

EBITDA Margin (%)
>50%
40%–50%
30%–40%
20%–30%
15%–20%
10%–15%
5%–10%
<5%

"FCF / Total Debt (%)
>45%
35%–45%
25%–35%
15%–25%
8%–15%
0%–8%
(8%)–0%
<(8%)

Total Debt / EBITDA (x)
<0.5x
0.5x–1.0x
1.0x–2.0x
2.0x–3.5x
3.5x–5.0x
5.0x–7.0x
7.0x –9.5x
>9.5x

Net Debt / EBITDA (x)
<0.0x
0.0x–0.5x
0.5x–1.5x
1.5x–3.0x
3.0x–4.5x
4.5x–6.8x
6.8x–9.3x
>9.3x

EBITDA / Interest Coverage
>50.0x
30.0x – 50.0x
15.0x – 30.0x
7.0x – 15.0x
4.0x –7.0x
1.5x – 4.0x
1.0x – 1.5x
<1.0x
"""


VELOCITY_FIELDS = frozenset(DEFAULT_VELOCITY)

# Guard rails on hand-entered velocity. Outside this band it is almost
# always a typo (1.5 entered as 15, or a percentage entered as 5).
MIN_VELOCITY = 0.5
MAX_VELOCITY = 2.0

WEIGHT_SUM_TOLERANCE = 1e-6


class InvalidModelInput(ValueError):
    pass


class UnknownComponent(KeyError):
    pass


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidModelInput(f"{label}: expected a number, got {value!r}")
    return float(value)


# --------------------------------------------------------------- validators

def validate_velocity(velocity, partial=False):
    if not isinstance(velocity, dict):
        raise InvalidModelInput("velocity must be a mapping")

    unknown = set(velocity) - VELOCITY_FIELDS
    if unknown:
        raise InvalidModelInput(
            f"unknown velocity field(s): {sorted(unknown)}; "
            f"known: {sorted(VELOCITY_FIELDS)}")
    if not partial:
        missing = VELOCITY_FIELDS - set(velocity)
        if missing:
            raise InvalidModelInput(f"missing velocity field(s): {sorted(missing)}")

    cleaned = {}
    for field, value in velocity.items():
        number = _number(value, field)
        if not MIN_VELOCITY <= number <= MAX_VELOCITY:
            raise InvalidModelInput(
                f"{field}: velocity {number} outside [{MIN_VELOCITY}, "
                f"{MAX_VELOCITY}] — a multiplier, not a percentage")
        cleaned[field] = number
    return cleaned


def validate_weights(weights, partial=False):
    """
    Weights are fractions that must sum to 1.0.

    The sum is only checked on a complete mapping: a partial update is
    merged against the stored weights first, and the merged result is what
    gets checked. A lone weight cannot be judged on its own.
    """
    if not isinstance(weights, dict):
        raise InvalidModelInput("weights must be a mapping")

    unknown = set(weights) - set(PILLAR_IDS)
    if unknown:
        raise InvalidModelInput(
            f"unknown pillar(s): {sorted(unknown)}; known: {list(PILLAR_IDS)}")
    if not partial:
        missing = set(PILLAR_IDS) - set(weights)
        if missing:
            raise InvalidModelInput(f"missing pillar weight(s): {sorted(missing)}")

    cleaned = {}
    for pillar, value in weights.items():
        number = _number(value, pillar)
        if not 0.0 <= number <= 1.0:
            raise InvalidModelInput(
                f"{pillar}: weight {number} outside [0, 1] — a fraction, "
                f"not a percentage")
        cleaned[pillar] = number

    if not partial:
        total = sum(cleaned.values())
        if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
            raise InvalidModelInput(
                f"weights must sum to 1.0, got {total:.6f}")
    return cleaned


def validate_ranges(ranges, partial=False):
    """
    Ranges are 8 breakpoints per pillar, ordered best rating to worst.

    Monotonicity is enforced in the pillar's own direction: a
    higher-is-better pillar descends, a lower-is-better pillar ascends. An
    out-of-order breakpoint silently creates an unreachable rating bucket,
    which is far worse than a rejected edit.
    """
    if not isinstance(ranges, dict):
        raise InvalidModelInput("ranges must be a mapping")

    unknown = set(ranges) - set(PILLAR_IDS)
    if unknown:
        raise InvalidModelInput(
            f"unknown pillar(s): {sorted(unknown)}; known: {list(PILLAR_IDS)}")
    if not partial:
        missing = set(PILLAR_IDS) - set(ranges)
        if missing:
            raise InvalidModelInput(f"missing pillar range(s): {sorted(missing)}")

    cleaned = {}
    for pillar, breakpoints in ranges.items():
        if not isinstance(breakpoints, (list, tuple)):
            raise InvalidModelInput(f"{pillar}: ranges must be a list")
        if len(breakpoints) != RANGE_BREAKPOINTS:
            raise InvalidModelInput(
                f"{pillar}: expected {RANGE_BREAKPOINTS} breakpoints, "
                f"got {len(breakpoints)}")

        values = [_number(v, f"{pillar}[{i}]") for i, v in enumerate(breakpoints)]
        increasing = PILLAR_DIRECTION[pillar]
        for i, (a, b) in enumerate(zip(values, values[1:])):
            # best-to-worst: descending when higher is better
            if increasing and b >= a:
                raise InvalidModelInput(
                    f"{pillar}: breakpoints must strictly descend (higher is "
                    f"better); position {i + 1} ({b}) is not below {a}")
            if not increasing and b <= a:
                raise InvalidModelInput(
                    f"{pillar}: breakpoints must strictly ascend (lower is "
                    f"better); position {i + 1} ({b}) is not above {a}")
        cleaned[pillar] = values
    return cleaned


COMPONENTS = {
    "velocity": {"default": DEFAULT_VELOCITY, "validate": validate_velocity},
    "weights": {"default": DEFAULT_WEIGHTS, "validate": validate_weights},
    "ranges": {"default": DEFAULT_RANGES, "validate": validate_ranges},
}


def _component(name):
    try:
        return COMPONENTS[name]
    except KeyError:
        raise UnknownComponent(
            f"unknown component {name!r}; known: {sorted(COMPONENTS)}")


def _safe_name(entity_id):
    """entity_id becomes a filename, so it must not contain path syntax."""
    if not entity_id or os.sep in str(entity_id) or ".." in str(entity_id):
        raise InvalidModelInput(f"unsafe entity_id {entity_id!r}")
    return f"{entity_id}.json"


def _migrate_revision(revision, component):
    """
    schema 1 stored a revision's payload under the component's own name
    ("velocity"); schema 2 uses "value" for every component.
    """
    if "value" in revision:
        return revision
    if component in revision:
        migrated = dict(revision)
        migrated["value"] = migrated.pop(component)
        return migrated
    raise InvalidModelInput(
        f"revision {revision.get('revision')} of {component} has no value; "
        f"keys present: {sorted(revision)}")


def _migrate(doc, entity_id):
    """
    schema 1 held velocity revisions at the top level, with the mapping
    under a "velocity" key rather than "value".
    """
    if doc.get("schema_version", 1) >= SCHEMA_VERSION:
        return doc
    revisions = [_migrate_revision(r, "velocity")
                 for r in doc.get("revisions", [])]
    return {
        "schema_version": SCHEMA_VERSION,
        "entity_id": doc.get("entity_id", entity_id),
        "model_version": doc.get("model_version", MODEL_VERSION),
        "components": {"velocity": {"revisions": revisions}},
    }


class ModelStore:
    """
    One JSON file per entity. Reads go to disk and are cached on (mtime,
    size), so a file changed by another process or edited by hand is picked
    up on the next call. "Use the latest" has to include edits this process
    did not make.
    """

    def __init__(self, directory=MODEL_DIR):
        self.directory = directory
        self._lock = threading.Lock()
        self._cache = {}

    def path_for(self, entity_id):
        return os.path.join(self.directory, _safe_name(entity_id))

    # ----------------------------------------------------------------- read

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
            doc = _migrate(json.load(fh), entity_id)
        self._cache[entity_id] = (stamp, doc)
        return doc

    def get_record(self, entity_id, component):
        """Latest revision of one component, or the synthetic default record."""
        spec = _component(component)
        doc = self._read_document(entity_id)
        revisions = ((doc or {}).get("components", {})
                     .get(component, {}).get("revisions", []))
        if not revisions:
            return {
                "entity_id": entity_id,
                "component": component,
                "value": copy.deepcopy(spec["default"]),
                "revision": 0,
                "is_default": True,
                "updated_at": None,
                "actor": None,
                "note": "defaults; never customised",
            }
        latest = revisions[-1]
        if "value" not in latest:
            raise InvalidModelInput(
                f"{self.path_for(entity_id)}: revision "
                f"{latest.get('revision')} of {component} has no 'value' key "
                f"(keys: {sorted(latest)}) — the file predates schema "
                f"{SCHEMA_VERSION} and did not migrate")
        return {
            "entity_id": entity_id,
            "component": component,
            "value": latest["value"],
            "revision": latest["revision"],
            "is_default": False,
            "updated_at": latest.get("updated_at"),
            "actor": latest.get("actor"),
            "note": latest.get("note"),
        }

    def get(self, entity_id, component):
        return self.get_record(entity_id, component)["value"]

    def get_all(self, entity_id):
        """Every component's live value plus its revision, in one read."""
        return {name: self.get_record(entity_id, name) for name in COMPONENTS}

    def history(self, entity_id, component):
        _component(component)
        doc = self._read_document(entity_id)
        if not doc:
            return []
        return list(doc.get("components", {})
                    .get(component, {}).get("revisions", []))

    def is_customised(self, entity_id, component=None):
        doc = self._read_document(entity_id)
        if doc is None:
            return False
        if component is None:
            return True
        return bool(doc.get("components", {})
                    .get(component, {}).get("revisions"))

    # ---------------------------------------------------------------- write

    def set_component(self, entity_id, component, value, actor=None, note=None):
        """Persist a complete value as a new revision of one component."""
        cleaned = _component(component)["validate"](value)
        return self._append(entity_id, component, cleaned, actor, note)

    def update(self, entity_id, component, partial, actor=None, note=None):
        """
        Merge a partial value over the current one and persist it.

        The merged result is validated, not the fragment — which is what
        makes a partial weight edit checkable against the sum-to-1 rule.
        """
        spec = _component(component)
        changes = spec["validate"](partial, partial=True)
        if not changes:
            raise InvalidModelInput("no fields to update")
        merged = copy.deepcopy(self.get(entity_id, component))
        merged.update(changes)
        return self._append(entity_id, component,
                            spec["validate"](merged), actor, note)

    def reset(self, entity_id, component, actor=None, note=None):
        """
        Record an explicit return to the defaults.

        Appends rather than deleting: "was customised, then reverted" is a
        different fact from "never touched".
        """
        spec = _component(component)
        return self._append(entity_id, component,
                            copy.deepcopy(spec["default"]), actor,
                            note or "reset to defaults")

    def _append(self, entity_id, component, value, actor, note):
        path = self.path_for(entity_id)
        with self._lock:
            doc = self._read_document(entity_id) or {
                "schema_version": SCHEMA_VERSION,
                "entity_id": entity_id,
                "model_version": MODEL_VERSION,
                "components": {},
            }
            components = dict(doc.get("components", {}))
            revisions = list(components.get(component, {}).get("revisions", []))
            revisions.append({
                "revision": len(revisions) + 1,
                "value": value,
                "updated_at": _now(),
                "actor": actor,
                "note": note,
            })
            components[component] = {"revisions": revisions}
            self._write_atomic(path, dict(doc, components=components))
            self._cache.pop(entity_id, None)
        return self.get_record(entity_id, component)

    def _write_atomic(self, path, doc):
        """
        Temp file in the same directory, then rename. A half-written model
        file is a corrupt input that fails every later run; rename is atomic
        on POSIX, so a crash mid-write leaves the previous revision intact.
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
        if not os.path.isdir(self.directory):
            return []
        return sorted(name[:-5] for name in os.listdir(self.directory)
                      if name.endswith(".json"))


# ------------------------------------------------------------ shared store

_shared = None
_shared_lock = threading.Lock()


def get_store(directory=MODEL_DIR):
    global _shared
    if _shared is None:
        with _shared_lock:
            if _shared is None:
                _shared = ModelStore(directory)
    return _shared


def get(entity_id, component):
    return get_store().get(entity_id, component)


def get_record(entity_id, component):
    return get_store().get_record(entity_id, component)


def get_all(entity_id):
    return get_store().get_all(entity_id)


def set_component(entity_id, component, value, actor=None, note=None):
    return get_store().set_component(entity_id, component, value, actor, note)


def update(entity_id, component, partial, actor=None, note=None):
    return get_store().update(entity_id, component, partial, actor, note)


def reset(entity_id, component, actor=None, note=None):
    return get_store().reset(entity_id, component, actor, note)


def history(entity_id, component):
    return get_store().history(entity_id, component)


def is_customised(entity_id, component=None):
    return get_store().is_customised(entity_id, component)


def list_customised():
    return get_store().list_customised()
