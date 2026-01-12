"""State management for CV apply operations."""

from datetime import datetime
from typing import Any

from .utils import read_json, write_json, strip_markers


def read_state(path: str) -> dict[str, Any]:
    """Read state file or return empty state if file doesn't exist."""
    import os
    import json

    if not os.path.exists(path):
        return {"docs": {}}
    try:
        data = read_json(path)
    except (json.JSONDecodeError, OSError):
        return {"docs": {}}
    if not isinstance(data, dict):
        return {"docs": {}}
    if "docs" not in data or not isinstance(data["docs"], dict):
        data["docs"] = {}
    return data


def write_state(path: str, state: dict[str, Any]) -> None:
    """Write state to file."""
    write_json(path, state)


def update_state(
    *,
    state_path: str,
    doc: str,
    doc_url: str | None,
    doc_id: str | None,
    data_path: str,
    replacements: dict[str, str],
) -> None:
    """
    Update state with document application information.

    Args:
        state_path: Path to state file
        doc: Document name
        doc_url: Document URL
        doc_id: Document ID
        data_path: Path to source data file
        replacements: Applied replacements
    """
    state = read_state(state_path)
    state["docs"][doc] = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "doc_url": doc_url,
        "doc_id": doc_id,
        "data_path": data_path,
        "replacements": replacements,
        "cleaned_replacements": {k: strip_markers(v) for k, v in replacements.items()},
    }
    write_state(state_path, state)


def invert_replacements(replacements: dict[str, str]) -> tuple[dict[str, str], list[str], int]:
    """
    Invert replacements dictionary for reverse lookup.

    Args:
        replacements: Dictionary mapping keys to values

    Returns:
        Tuple of (inverted_dict, collisions, skipped_count)
    """
    inverted: dict[str, str] = {}
    collisions: list[str] = []
    skipped = 0
    for key, value in replacements.items():
        if not value:
            skipped += 1
            continue
        if value in inverted and inverted[value] != key:
            collisions.append(value)
            continue
        inverted[value] = key
    return inverted, collisions, skipped
