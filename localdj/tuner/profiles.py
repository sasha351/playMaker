"""Save and load named tuning profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_PROFILE_DIR = Path.home() / ".localdj" / "profiles"
_DEFAULT_WEIGHTS = {
    "bpm_smoothness": 0.35,
    "energy_coherence": 0.35,
    "genre_consistency": 0.20,
    "transition_score": 0.10,
}


def save_profile(name: str, weights: dict[str, float], profile_dir: Path | None = None) -> Path:
    """Save a named weight profile to disk."""
    dir_ = profile_dir or _DEFAULT_PROFILE_DIR
    dir_.mkdir(parents=True, exist_ok=True)
    path = dir_ / f"{name}.json"
    path.write_text(json.dumps(weights, indent=2), encoding="utf-8")
    return path


def load_profile(name: str, profile_dir: Path | None = None) -> dict[str, float]:
    """Load a named weight profile from disk.

    Returns default weights if the profile does not exist.
    """
    dir_ = profile_dir or _DEFAULT_PROFILE_DIR
    path = dir_ / f"{name}.json"
    if not path.exists():
        return dict(_DEFAULT_WEIGHTS)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_WEIGHTS)


def list_profiles(profile_dir: Path | None = None) -> list[str]:
    """Return names of all saved profiles."""
    dir_ = profile_dir or _DEFAULT_PROFILE_DIR
    if not dir_.exists():
        return []
    return [p.stem for p in dir_.glob("*.json")]


def default_weights() -> dict[str, float]:
    return dict(_DEFAULT_WEIGHTS)
