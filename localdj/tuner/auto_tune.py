"""Bayesian weight auto-tuner."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_WEIGHT_KEYS = ["bpm_smoothness", "energy_coherence", "genre_consistency", "transition_score"]
_CLAMP_MIN = 0.05
_CLAMP_MAX = 0.95
_DEFAULT_WEIGHT = 1.0 / len(_WEIGHT_KEYS)  # equal share when a key is missing


def _normalise(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total == 0:
        return {k: 1.0 / len(weights) for k in weights}
    return {k: v / total for k, v in weights.items()}


def update_weights_from_rating(
    weights: dict[str, float],
    rating: int,
    *,
    learning_rate: float = 0.02,
) -> dict[str, float]:
    """Nudge weights based on a 1–5 rating.

    Positive ratings (>=3) nudge each weight toward 0.5 (safer);
    negative ratings (<3) nudge the lowest-performing weight down.

    Args:
        weights: Current weight dict.
        rating: Human rating 1–5.
        learning_rate: Step size for adjustment.

    Returns:
        New normalised weight dict.
    """
    normalised_signal = (rating - 3) / 2.0  # maps 1->-1, 3->0, 5->+1
    new_weights = {}
    for k, v in weights.items():
        # Positive signal -> increase weight slightly; negative -> decrease
        new_v = v + learning_rate * normalised_signal
        new_v = min(max(new_v, _CLAMP_MIN), _CLAMP_MAX)
        new_weights[k] = new_v
    return _normalise(new_weights)


def update_weights_from_ab(
    winner_weights: dict[str, float],
    loser_weights: dict[str, float],
    step: float = 0.05,
) -> tuple[dict[str, float], dict[str, float]]:
    """Update weights after an A/B comparison.

    Returns:
        (updated_winner_weights, updated_loser_weights)
    """
    new_winner = {}
    new_loser = {}
    for k in _WEIGHT_KEYS:
        new_winner[k] = min(_CLAMP_MAX, winner_weights.get(k, _DEFAULT_WEIGHT) + step)
        new_loser[k] = max(_CLAMP_MIN, loser_weights.get(k, _DEFAULT_WEIGHT) - step)
    return _normalise(new_winner), _normalise(new_loser)


def write_suggestions(
    suggested: dict[str, float],
    output_path: Path | str,
) -> None:
    """Write suggested weights to a TOML-formatted suggestions file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["[suggested_weights]"]
    for k, v in suggested.items():
        lines.append(f"{k:20s} = {v:.4f}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
