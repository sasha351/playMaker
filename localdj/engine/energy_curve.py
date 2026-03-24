"""Energy curve playlist mode — arrange tracks by energy arc."""
from __future__ import annotations

import sqlite3
from enum import Enum
from typing import Any


class CurveShape(str, Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"
    ARC = "arc"  # build → peak → wind-down


def build_energy_curve_playlist(
    tracks: list[sqlite3.Row | dict[str, Any]],
    shape: CurveShape = CurveShape.ARC,
    length: int = 20,
) -> list[dict[str, Any]]:
    """Sort tracks to follow an energy curve.

    Args:
        tracks: Pool of candidate tracks (rows from DB or plain dicts).
        shape: Desired curve shape.
        length: Maximum playlist length (number of tracks).

    Returns:
        Ordered list of track dicts.
    """
    def _to_dict(t: Any) -> dict[str, Any]:
        if isinstance(t, dict):
            return t
        return dict(t)

    pool = [_to_dict(t) for t in tracks if _to_dict(t).get("energy_score") is not None]
    pool.sort(key=lambda t: t["energy_score"])

    if not pool:
        return []

    pool = pool[:length]

    if shape == CurveShape.ASCENDING:
        return pool
    elif shape == CurveShape.DESCENDING:
        return list(reversed(pool))
    else:  # ARC
        mid = len(pool) // 2
        ascending = pool[:mid]
        descending = list(reversed(pool[mid:]))
        return ascending + descending
