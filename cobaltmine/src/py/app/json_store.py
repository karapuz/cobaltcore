import json
import os
import threading
from typing import List, Optional

# ─────────────────────────────────────
# Resolve path to data/credit_ratings.json
# relative to the project root (backend/)
# ─────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "credit_ratings.json")

# Lock to prevent concurrent read/write conflicts
_lock = threading.Lock()


def _read_file() -> dict:
    """Read and parse the JSON file. Returns empty structure if file missing."""
    if not os.path.exists(DATA_FILE):
        return {"users": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _write_file(data: dict) -> None:
    """Write data back to JSON file with formatting."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_credit_ratings(user_id: int) -> List[dict]:
    """
    Fetch all credit ratings for a given user.
    Returns an empty list if user has no records.
    """
    with _lock:
        data = _read_file()
        return data.get("users", {}).get(str(user_id), [])


def get_credit_rating_by_id(user_id: int, computation_id: str) -> Optional[dict]:
    """
    Fetch a single credit rating by computation_id for a given user.
    Returns None if not found.
    """
    ratings = get_credit_ratings(user_id)
    for rating in ratings:
        if rating["id"] == computation_id:
            return rating
    return None


def add_credit_rating(user_id: int, rating: dict) -> dict:
    """
    Add a new credit rating for a user.
    Raises ValueError if computation_id already exists for that user.
    """
    with _lock:
        data = _read_file()
        user_key = str(user_id)

        # Initialize user list if not present
        if user_key not in data["users"]:
            data["users"][user_key] = []

        # Check for duplicate computation_id
        for existing in data["users"][user_key]:
            if existing["id"] == rating["id"]:
                raise ValueError(f"Computation ID '{rating['id']}' already exists")

        data["users"][user_key].append(rating)
        _write_file(data)
        return rating


def update_credit_rating(user_id: int, computation_id: str, updated_fields: dict) -> Optional[dict]:
    """
    Update an existing credit rating by computation_id.
    Only updates fields that are present in updated_fields.
    Returns the updated rating, or None if not found.
    """
    with _lock:
        data = _read_file()
        user_key = str(user_id)
        ratings = data.get("users", {}).get(user_key, [])

        for i, rating in enumerate(ratings):
            if rating["id"] == computation_id:
                ratings[i].update(updated_fields)
                _write_file(data)
                return ratings[i]

        return None


def delete_credit_rating(user_id: int, computation_id: str) -> bool:
    """
    Delete a credit rating by computation_id for a given user.
    Returns True if deleted, False if not found.
    """
    with _lock:
        data = _read_file()
        user_key = str(user_id)
        ratings = data.get("users", {}).get(user_key, [])

        for i, rating in enumerate(ratings):
            if rating["id"] == computation_id:
                ratings.pop(i)
                _write_file(data)
                return True

        return False


def seed_user_data(user_id: int) -> None:
    """
    Seeds demo credit rating data for a new user if they have no records.
    Called automatically after signup.
    """
    with _lock:
        data = _read_file()
        user_key = str(user_id)

        # Only seed if the user has no data yet
        if user_key in data["users"] and len(data["users"][user_key]) > 0:
            return

        # Copy demo data from user "1" if available, otherwise use defaults
        demo_source = data.get("users", {}).get("1", [])
        if not demo_source:
            demo_source = []

        # Deep copy and assign new IDs based on user
        import copy
        seeded = copy.deepcopy(demo_source)
        data["users"][user_key] = seeded
        _write_file(data)
