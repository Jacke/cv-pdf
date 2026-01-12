"""Utility functions for CV apply system."""

import json
import os
import re
from datetime import datetime
from typing import Any


def strip_markers(value: str) -> str:
    """Remove bullet markers from text while keeping contact prefixes."""
    from .constants import SKILL_BULLET_MARKER, EXP_BULLET_MARKER
    return value.replace(SKILL_BULLET_MARKER, "").replace(EXP_BULLET_MARKER, "")


def read_json(path: str) -> Any:
    """Read and parse JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, value: Any) -> None:
    """Write data to JSON file atomically."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def normalize_text(value: Any) -> str:
    """Convert any value to string representation."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def normalize_list(value: Any) -> list[Any]:
    """Ensure value is a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def format_block(lines: list[str]) -> str:
    """Format a block of text by removing leading/trailing empty lines."""
    cleaned = [line.rstrip() for line in lines]
    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    return "\n".join(cleaned)


def log_line(message: str) -> None:
    """Print a timestamped log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {message}")


def extract_placeholders(text: str) -> set[str]:
    """Extract all {{placeholder}} markers from text."""
    return set(re.findall(r"\{\{[^}]+\}\}", text))


def read_text(path: str) -> str:
    """Read text file content."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
