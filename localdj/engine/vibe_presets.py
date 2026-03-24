"""Vibe preset definitions and filter engine."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class VibePreset:
    """Defines the filtering parameters for a named vibe preset."""
    name: str
    bpm_min: Optional[float] = None
    bpm_max: Optional[float] = None
    energy_min: Optional[float] = None
    energy_max: Optional[float] = None
    genre_bias: list[str] = field(default_factory=list)


BUILTIN_PRESETS: dict[str, VibePreset] = {
    "chill_sunday": VibePreset(
        name="chill_sunday",
        bpm_min=60, bpm_max=95,
        energy_max=0.5,
        genre_bias=["ambient", "indie", "folk", "jazz"],
    ),
    "morning_fuel": VibePreset(
        name="morning_fuel",
        bpm_min=118, bpm_max=160,
        energy_min=0.6,
        genre_bias=["pop", "rock", "electronic", "hip-hop"],
    ),
    "late_night_drive": VibePreset(
        name="late_night_drive",
        bpm_min=85, bpm_max=120,
        energy_min=0.3, energy_max=0.7,
        genre_bias=["electronic", "synthwave", "ambient"],
    ),
}


def apply_preset(
    tracks: list[sqlite3.Row | dict[str, Any]],
    preset: VibePreset,
    max_tracks: int = 50,
) -> list[dict[str, Any]]:
    """Filter a track pool by the given preset parameters.

    Args:
        tracks: Pool of candidate tracks.
        preset: Vibe preset to apply.
        max_tracks: Maximum number of tracks to return.

    Returns:
        Filtered track list, genre-biased tracks first.
    """
    def _to_dict(t: Any) -> dict[str, Any]:
        return t if isinstance(t, dict) else dict(t)

    result: list[dict[str, Any]] = []
    for row in tracks:
        t = _to_dict(row)
        bpm = t.get("bpm")
        energy = t.get("energy_score")

        if preset.bpm_min is not None and bpm is not None and bpm < preset.bpm_min:
            continue
        if preset.bpm_max is not None and bpm is not None and bpm > preset.bpm_max:
            continue
        if preset.energy_min is not None and energy is not None and energy < preset.energy_min:
            continue
        if preset.energy_max is not None and energy is not None and energy > preset.energy_max:
            continue
        result.append(t)

    # Sort: genre-biased tracks first
    if preset.genre_bias:
        def _genre_rank(t: dict[str, Any]) -> int:
            genre = (t.get("genre") or "").lower()
            for i, g in enumerate(preset.genre_bias):
                if g.lower() in genre:
                    return i
            return len(preset.genre_bias)

        result.sort(key=_genre_rank)

    return result[:max_tracks]
