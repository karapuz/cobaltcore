"""
Temporal entity store — in-process library.

Answers: given an entity UUID, a date, and an attribute name, what was the
value of that attribute on that date?

    from entity import entity_store as entities

    uid = entities.resolve_one("exchange_ticker", "META")
    entities.get_value(uid, "corporate_name", "2019-01-01")   # Facebook, Inc.
    entities.get_value(uid, "cik")                            # 0001326801

The module-level functions run against a lazily-loaded shared store, which is
what callers in this process should use. Construct EntityStore(path) directly
only for tests, or to hold a second data file open at the same time.

Intervals are half-open: a record applies to dates d where
valid_from <= d < valid_to. null valid_from means unbounded past, null
valid_to means still in effect. Half-open matters — on a change date the NEW
value applies, and exactly one record can match any given date.
"""

import json
import os
import threading
from bisect import bisect_right
from datetime import date

# This module lives at <root>/entity/entity_store.py and its data under
# <root>/data/. Resolve from the project root rather than the module
# directory — entity/ and data/ are siblings, not nested, so a plain
# __file__-relative path would have to walk upward and would break the first
# time this module moves.
#
# The two files do not sit together: entity records are under data/meta/,
# index membership directly under data/.
#
#   data/meta/entity.json   corporate entities and their attributes
#   data/index.json         index membership
#
# COMPASS_DATA_DIR relocates both at once — point it at a dated snapshot to
# reproduce a past rating run against the identity data as it stood then.
# COMPASS_ENTITY_FILE and COMPASS_INDEX_FILE override either file on its own.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("COMPASS_DATA_DIR",
                          os.path.join(_PROJECT_ROOT, "data"))
DEFAULT_PATH = os.environ.get(
    "COMPASS_ENTITY_FILE", os.path.join(DATA_DIR, "meta", "entity.json"))
DEFAULT_INDEX_PATH = os.environ.get(
    "COMPASS_INDEX_FILE", os.path.join(DATA_DIR, "index.json"))


class EntityNotFound(KeyError):
    pass


class AttributeNotFound(KeyError):
    pass


class IndexNotFound(KeyError):
    pass


class AmbiguousResolution(LookupError):
    """A value matched more than one entity on the requested date."""


class OverlappingIntervals(ValueError):
    """Two records for one attribute claim the same date."""


def _as_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _validate(entities):
    """Reject overlapping intervals at load. A store that can return two
    answers for one date is worse than one that fails loudly."""
    problems = []
    for entity_id, entity in entities.items():
        for attribute, records in entity["attributes"].items():
            for earlier, later in zip(records, records[1:]):
                if later["_from"] < earlier["_to"]:
                    problems.append(
                        f"{entity_id}/{attribute}: "
                        f"[{earlier['_from']},{earlier['_to']}) overlaps "
                        f"[{later['_from']},{later['_to']})")
    if problems:
        raise OverlappingIntervals("; ".join(problems))


class EntityStore:
    """
    Effectively immutable once loaded. Reads are lock-free; reload() builds a
    whole new index and swaps it in under a lock, so a concurrent reader sees
    either the old data or the new data, never a half-built index.
    """

    def __init__(self, path=DEFAULT_PATH, index_path=DEFAULT_INDEX_PATH):
        self.path = path
        self.index_path = index_path
        self._write_lock = threading.Lock()
        self._install(self._build(path), self._build_indices(index_path))

    # ------------------------------------------------------------- loading

    @staticmethod
    def _build(path):
        try:
            with open(path) as fh:
                doc = json.load(fh)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"entity data not found at {path}. Expected "
                f"<root>/data/meta/entity.json, or set COMPASS_DATA_DIR / "
                f"COMPASS_ENTITY_FILE.")

        entities = {}
        for raw in doc["entities"]:
            attributes = {}
            for attribute, records in raw["attributes"].items():
                # Sorted by start date so lookup is a binary search, and so
                # overlap validation only compares neighbours.
                attributes[attribute] = sorted(
                    (dict(r,
                          _from=_as_date(r.get("valid_from")) or date.min,
                          _to=_as_date(r.get("valid_to")) or date.max)
                     for r in records),
                    key=lambda r: r["_from"])
            entities[raw["entity_id"]] = dict(raw, attributes=attributes)

        _validate(entities)

        # (attribute, value) -> [(entity_id, from, to), ...] so reverse
        # lookup doesn't scan every entity on every call.
        index = {}
        for entity_id, entity in entities.items():
            for attribute, records in entity["attributes"].items():
                for rec in records:
                    index.setdefault((attribute, rec["value"]), []).append(
                        (entity_id, rec["_from"], rec["_to"]))

        return {
            "schema_version": doc.get("schema_version"),
            "attributes": doc.get("attributes", []),
            "entities": entities,
            "index": index,
        }

    @staticmethod
    def _build_indices(index_path):
        """
        Index membership: (entity, index) pairs with validity intervals.

        A missing file raises. Returning {} here instead would surface as an
        empty index picker in the UI with no error anywhere — a data-layout
        problem disguised as "there are no indices".
        """
        try:
            with open(index_path) as fh:
                doc = json.load(fh)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"index membership data not found at {index_path}. Expected "
                f"<root>/data/index.json — note it does NOT sit beside "
                f"entity.json, which is under data/meta/. Set COMPASS_DATA_DIR "
                f"/ COMPASS_INDEX_FILE to relocate. Regenerate both with: "
                f"python build_entities.py")

        indices = {}
        for raw in doc["indices"]:
            members = [
                dict(m,
                     _from=_as_date(m.get("valid_from")) or date.min,
                     _to=_as_date(m.get("valid_to")) or date.max)
                for m in raw["members"]
            ]
            indices[raw["index_id"]] = dict(raw, members=members)
        return indices

    def _install(self, built, indices):
        self.schema_version = built["schema_version"]
        self.attributes = built["attributes"]
        self._entities = built["entities"]
        self._index = built["index"]
        self._indices = indices

    def reload(self):
        """Re-read both files. Builds first and swaps second, so a failed
        parse leaves the currently loaded data intact."""
        built = self._build(self.path)
        indices = self._build_indices(self.index_path)
        with self._write_lock:
            self._install(built, indices)

    # --------------------------------------------------------------- query

    def _records(self, entity_id, attribute):
        entity = self._entities.get(entity_id)
        if entity is None:
            raise EntityNotFound(entity_id)
        records = entity["attributes"].get(attribute)
        if records is None:
            raise AttributeNotFound(attribute)
        return records

    def get_attribute(self, entity_id, attribute, as_of=None):
        """
        Full record (value + provenance + interval) in effect on `as_of`, or
        None if the attribute is modeled but has no value on that date.

        Raises EntityNotFound / AttributeNotFound for unknown keys — an
        unknown attribute name is a caller bug, an empty interval is data.
        """
        records = self._records(entity_id, attribute)
        when = _as_date(as_of) or date.today()

        # Rightmost record starting at or before `when`. Intervals never
        # overlap, so it is the only candidate.
        position = bisect_right([r["_from"] for r in records], when) - 1
        if position < 0:
            return None
        rec = records[position]
        if when >= rec["_to"]:
            return None

        out = {k: v for k, v in rec.items() if not k.startswith("_")}
        out.update(attribute=attribute, entity_id=entity_id,
                   as_of=when.isoformat())
        return out

    def get_value(self, entity_id, attribute, as_of=None):
        """Just the value, or None."""
        rec = self.get_attribute(entity_id, attribute, as_of)
        return rec["value"] if rec else None

    def snapshot(self, entity_id, as_of=None):
        """Every attribute of one entity as of a date."""
        entity = self._entities.get(entity_id)
        if entity is None:
            raise EntityNotFound(entity_id)
        when = _as_date(as_of) or date.today()
        return {
            "entity_id": entity_id,
            "as_of": when.isoformat(),
            "attributes": {a: self.get_value(entity_id, a, when)
                           for a in entity["attributes"]},
        }

    def history(self, entity_id, attribute):
        """Every record for one attribute, oldest first."""
        return [{k: v for k, v in r.items() if not k.startswith("_")}
                for r in self._records(entity_id, attribute)]

    def resolve(self, attribute, value, as_of=None):
        """
        Reverse lookup: which entities held this attribute value on this date?

        This is what the UUID buys you — resolve("exchange_ticker", "FB",
        "2019-01-01") and resolve("exchange_ticker", "META") are the same
        entity. Returns a list; empty means nothing held that value then.
        """
        when = _as_date(as_of) or date.today()
        return [entity_id
                for entity_id, start, end in self._index.get((attribute, value), ())
                if start <= when < end]

    def resolve_one(self, attribute, value, as_of=None):
        """
        resolve() for callers that need exactly one answer — the common case
        when turning a ticker into an entity id.

        Raises EntityNotFound if nothing matched, AmbiguousResolution if
        several did. Tickers get reused after delisting, so the ambiguous
        case is real and should never be silently first-wins.
        """
        hits = self.resolve(attribute, value, as_of)
        if not hits:
            raise EntityNotFound(
                f"no entity with {attribute}={value!r} on {as_of or 'today'}")
        if len(hits) > 1:
            raise AmbiguousResolution(
                f"{attribute}={value!r} matched {len(hits)} entities: {hits}")
        return hits[0]

    # --------------------------------------------------------- index membership

    def list_indices(self):
        """Every index this layer knows about."""
        return [{"index_id": i["index_id"], "name": i["name"],
                 "complete": i.get("complete", False),
                 "member_count": len(i["members"])}
                for i in self._indices.values()]

    def index_members(self, index_id, as_of=None):
        """
        Entity ids that were components of `index_id` on `as_of`.

        Returns entity ids, not tickers — the caller resolves whatever
        attributes it needs at the same date, so a company that was renamed
        or retickered still lines up with its own history.
        """
        index = self._indices.get(index_id)
        if index is None:
            raise IndexNotFound(index_id)
        when = _as_date(as_of) or date.today()
        return [m["entity_id"] for m in index["members"]
                if m["_from"] <= when < m["_to"]]

    def index_components(self, index_id, as_of=None):
        """
        index_members() with each entity's name and ticker resolved as of the
        same date, which is what a constituent picker needs.
        """
        when = _as_date(as_of) or date.today()
        return [
            {"entity_id": entity_id,
             "ticker": self.get_value(entity_id, "exchange_ticker", when),
             "name": self.get_value(entity_id, "corporate_name", when)}
            for entity_id in self.index_members(index_id, when)
        ]

    def index_metadata(self, index_id):
        index = self._indices.get(index_id)
        if index is None:
            raise IndexNotFound(index_id)
        return {"index_id": index["index_id"], "name": index["name"],
                "complete": index.get("complete", False),
                "membership_dates_loaded": index.get("membership_dates_loaded", False)}

    def list_entities(self, djia_only=False):
        return [{"entity_id": e["entity_id"],
                 "display_name": e["display_name"],
                 "in_djia": e.get("in_djia", False)}
                for e in self._entities.values()
                if not djia_only or e.get("in_djia")]

    def __contains__(self, entity_id):
        return entity_id in self._entities

    def __len__(self):
        return len(self._entities)


# ------------------------------------------------------------ shared store

_shared = None
_shared_lock = threading.Lock()


def get_store(path=DEFAULT_PATH):
    """The process-wide store, loaded on first use."""
    global _shared
    if _shared is None:
        with _shared_lock:
            if _shared is None:
                _shared = EntityStore(path)
    return _shared


def reload():
    """Re-read the entity file in place."""
    get_store().reload()


def get_attribute(entity_id, attribute, as_of=None):
    return get_store().get_attribute(entity_id, attribute, as_of)


def get_value(entity_id, attribute, as_of=None):
    return get_store().get_value(entity_id, attribute, as_of)


def snapshot(entity_id, as_of=None):
    return get_store().snapshot(entity_id, as_of)


def history(entity_id, attribute):
    return get_store().history(entity_id, attribute)


def resolve(attribute, value, as_of=None):
    return get_store().resolve(attribute, value, as_of)


def resolve_one(attribute, value, as_of=None):
    return get_store().resolve_one(attribute, value, as_of)


def list_entities(djia_only=False):
    return get_store().list_entities(djia_only=djia_only)


def list_indices():
    return get_store().list_indices()


def index_members(index_id, as_of=None):
    return get_store().index_members(index_id, as_of)


def index_components(index_id, as_of=None):
    return get_store().index_components(index_id, as_of)


def index_metadata(index_id):
    return get_store().index_metadata(index_id)


def isin_from_cusip(cusip, country="US"):
    """
    Derive an ISIN from a 9-character CUSIP.

    Provided so ISIN never has to be stored or kept in sync — it is a pure
    function of the CUSIP. Check digit is the ISO 6166 mod-10 (Luhn) over the
    letter-expanded body.
    """
    if len(cusip) != 9:
        raise ValueError("CUSIP must be 9 characters")
    body = country.upper() + cusip.upper()
    digits = "".join(str(ord(c) - 55) if c.isalpha() else c for c in body)

    total, double = 0, True
    for char in reversed(digits):
        value = int(char)
        if double:
            value *= 2
            if value > 9:
                value -= 9
        total += value
        double = not double
    return body + str((10 - total % 10) % 10)