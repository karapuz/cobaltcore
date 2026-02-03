import json
import os
import copy
import threading
from typing import List, Optional

# ─────────────────────────────────────
# Resolve paths to data files
# relative to the project root (backend/)
# ─────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_FILE = os.path.join(BASE_DIR, "data", "credit_ratings.json")
SCENARIOS_FILE = os.path.join(BASE_DIR, "data", "scenarios.json")

# Separate locks for each file to avoid blocking unrelated operations
_portfolio_lock = threading.Lock()
_scenarios_lock = threading.Lock()


# ─────────────────────────────────────
# Generic file helpers
# ─────────────────────────────────────
def _read_file(filepath: str) -> dict:
    """Read and parse a JSON file. Returns empty structure if file missing."""
    if not os.path.exists(filepath):
        return {"users": {}}
    with open(filepath, "r") as f:
        return json.load(f)


def _write_file(filepath: str, data: dict) -> None:
    """Write data back to a JSON file with formatting."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


# ─────────────────────────────────────
# Portfolio (credit_ratings.json)
# ─────────────────────────────────────
def get_credit_ratings(user_id: int) -> List[dict]:
    """Fetch all credit ratings for a given user."""
    with _portfolio_lock:
        data = _read_file(PORTFOLIO_FILE)
        return data.get("users", {}).get(str(user_id), [])


def get_credit_rating_by_id(user_id: int, computation_id: str) -> Optional[dict]:
    """Fetch a single credit rating by computation_id."""
    ratings = get_credit_ratings(user_id)
    for rating in ratings:
        if rating["id"] == computation_id:
            return rating
    return None


def add_credit_rating(user_id: int, rating: dict) -> dict:
    """Add a new credit rating. Raises ValueError on duplicate ID."""
    with _portfolio_lock:
        data = _read_file(PORTFOLIO_FILE)
        user_key = str(user_id)

        if user_key not in data["users"]:
            data["users"][user_key] = []

        for existing in data["users"][user_key]:
            if existing["id"] == rating["id"]:
                raise ValueError(f"Computation ID '{rating['id']}' already exists")

        data["users"][user_key].append(rating)
        _write_file(PORTFOLIO_FILE, data)
        return rating


def update_credit_rating(user_id: int, computation_id: str, updated_fields: dict) -> Optional[dict]:
    """Update an existing credit rating. Returns updated record or None."""
    with _portfolio_lock:
        data = _read_file(PORTFOLIO_FILE)
        user_key = str(user_id)
        ratings = data.get("users", {}).get(user_key, [])

        for i, rating in enumerate(ratings):
            if rating["id"] == computation_id:
                ratings[i].update(updated_fields)
                _write_file(PORTFOLIO_FILE, data)
                return ratings[i]

        return None


def delete_credit_rating(user_id: int, computation_id: str) -> bool:
    """Delete a credit rating. Returns True if deleted, False if not found."""
    with _portfolio_lock:
        data = _read_file(PORTFOLIO_FILE)
        user_key = str(user_id)
        ratings = data.get("users", {}).get(user_key, [])

        for i, rating in enumerate(ratings):
            if rating["id"] == computation_id:
                ratings.pop(i)
                _write_file(PORTFOLIO_FILE, data)
                return True

        return False


def seed_portfolio_data(user_id: int) -> None:
    """Seeds demo portfolio data for a new user if they have no records."""
    with _portfolio_lock:
        data = _read_file(PORTFOLIO_FILE)
        user_key = str(user_id)

        if user_key in data["users"] and len(data["users"][user_key]) > 0:
            return

        demo_source = data.get("users", {}).get("1", [])
        data["users"][user_key] = copy.deepcopy(demo_source)
        _write_file(PORTFOLIO_FILE, data)


# ─────────────────────────────────────
# Scenarios (scenarios.json)
# ─────────────────────────────────────
def get_scenarios(user_id: int) -> List[dict]:
    """Fetch all scenarios for a given user."""
    with _scenarios_lock:
        data = _read_file(SCENARIOS_FILE)
        return data.get("users", {}).get(str(user_id), [])


def get_scenario_by_id(user_id: int, computation_id: str) -> Optional[dict]:
    """Fetch a single scenario by computation_id."""
    scenarios = get_scenarios(user_id)
    for scenario in scenarios:
        if scenario["id"] == computation_id:
            return scenario
    return None


def update_scenario(user_id: int, computation_id: str, updated_fields: dict) -> Optional[dict]:
    """
    Update an existing scenario by computation_id.
    Only updates fields present in updated_fields.
    Returns updated record or None if not found.
    """
    with _scenarios_lock:
        data = _read_file(SCENARIOS_FILE)
        user_key = str(user_id)
        scenarios = data.get("users", {}).get(user_key, [])

        for i, scenario in enumerate(scenarios):
            if scenario["id"] == computation_id:
                scenarios[i].update(updated_fields)
                _write_file(SCENARIOS_FILE, data)
                return scenarios[i]

        return


def seed_scenarios_data(user_id: int) -> None:
    """Seeds demo scenario data for a new user if they have no records."""
    with _scenarios_lock:
        data = _read_file(SCENARIOS_FILE)
        user_key = str(user_id)

        if user_key in data["users"] and len(data["users"][user_key]) > 0:
            return

        demo_source = data.get("users", {}).get("1", [])
        data["users"][user_key] = copy.deepcopy(demo_source)
        _write_file(SCENARIOS_FILE, data)
