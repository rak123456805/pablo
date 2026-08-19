"""
reference.py — loads reference.json once at module import time and exposes
typed constants.  All validation code imports from here; never hardcodes.
"""
from __future__ import annotations

import json
from pathlib import Path

_REF_PATH = Path(__file__).parent.parent / "reference.json"
if not _REF_PATH.exists():
    _REF_PATH = Path(__file__).parent.parent.parent / "reference.json"

with open(_REF_PATH, encoding="utf-8") as _f:
    _RAW: dict = json.load(_f)

# ── Allowed values ────────────────────────────────────────────────────────────
SECTIONS: frozenset[str] = frozenset(_RAW["sections"])
CATEGORIES: frozenset[str] = frozenset(_RAW["categories"])
LANGUAGES: frozenset[str] = frozenset(_RAW["languages"])

# ── Artwork specs ─────────────────────────────────────────────────────────────
ARTWORK_SPECS: dict[str, dict] = _RAW["artwork_specs"]
# e.g. ARTWORK_SPECS["poster"] = {"aspect": "2:3", "target_px": [600, 900], "max_kb": 200}

ARTWORK_KINDS: frozenset[str] = frozenset(ARTWORK_SPECS.keys())

# ── Conventions ───────────────────────────────────────────────────────────────
SEASON_ZERO_MEANING: str = _RAW["conventions"]["season_zero"]
CONTENT_GROUP_MEANING: str = _RAW["conventions"]["content_group"]

# ── Derived helpers ───────────────────────────────────────────────────────────

def artwork_aspect_ratio(kind: str) -> tuple[int, int]:
    """Return (width_parts, height_parts) for the given artwork kind."""
    aspect_str = ARTWORK_SPECS[kind]["aspect"]
    w, h = aspect_str.split(":")
    return int(w), int(h)


def artwork_max_bytes(kind: str) -> int:
    return ARTWORK_SPECS[kind]["max_kb"] * 1024


def artwork_target_px(kind: str) -> tuple[int, int]:
    w, h = ARTWORK_SPECS[kind]["target_px"]
    return int(w), int(h)
