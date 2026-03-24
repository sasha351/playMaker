"""Quality scoring for generated playlists."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PlaylistScore:
    """Quality scores for a generated playlist."""
    bpm_smoothness: float = 0.0       # 1 - normalised avg BPM delta
    energy_coherence: float = 0.0     # Pearson r of energy vs expected curve
    genre_consistency: float = 0.0    # % tracks matching dominant genre
    transition_score: float = 0.0     # Composite transition quality
    overall: float = 0.0              # Weighted sum


def score_playlist(
    tracks: list[dict[str, Any]],
    *,
    weights: dict[str, float] | None = None,
    expected_curve: list[float] | None = None,
) -> PlaylistScore:
    """Compute quality scores for a playlist.

    Args:
        tracks: Ordered list of track dicts.
        weights: Scoring weight overrides.
        expected_curve: Expected energy values (for coherence metric).

    Returns:
        PlaylistScore with individual and overall scores.
    """
    if weights is None:
        weights = {
            "bpm_smoothness": 0.35,
            "energy_coherence": 0.35,
            "genre_consistency": 0.20,
            "transition_score": 0.10,
        }

    score = PlaylistScore()
    n = len(tracks)
    if n == 0:
        return score

    # BPM smoothness
    bpms = [t.get("bpm") for t in tracks if t.get("bpm") is not None]
    if len(bpms) >= 2:
        deltas = [abs(bpms[i + 1] - bpms[i]) for i in range(len(bpms) - 1)]
        avg_delta = sum(deltas) / len(deltas)
        score.bpm_smoothness = max(0.0, 1.0 - avg_delta / 60.0)
    else:
        score.bpm_smoothness = 1.0

    # Energy coherence
    energies = [t.get("energy_score") for t in tracks if t.get("energy_score") is not None]
    if len(energies) >= 2 and expected_curve is not None and len(expected_curve) >= 2:
        try:
            import numpy as np
            e_arr = np.array(energies[: len(expected_curve)])
            c_arr = np.array(expected_curve[: len(e_arr)])
            correlation = float(np.corrcoef(e_arr, c_arr)[0, 1])
            score.energy_coherence = max(0.0, correlation)
        except Exception:  # noqa: BLE001
            score.energy_coherence = 0.5
    else:
        score.energy_coherence = 0.5  # neutral when no expected curve

    # Genre consistency
    genres = [t.get("genre") for t in tracks if t.get("genre")]
    if genres:
        dominant = max(set(genres), key=genres.count)
        score.genre_consistency = genres.count(dominant) / len(genres)
    else:
        score.genre_consistency = 0.5

    # Transition score: penalise large BPM + energy jumps
    if n >= 2:
        transition_scores = []
        for i in range(n - 1):
            bpm_a = tracks[i].get("bpm") or 0
            bpm_b = tracks[i + 1].get("bpm") or 0
            e_a = tracks[i].get("energy_score") or 0
            e_b = tracks[i + 1].get("energy_score") or 0
            bpm_penalty = min(abs(bpm_b - bpm_a) / 60.0, 1.0)
            energy_penalty = abs(e_b - e_a)
            transition_scores.append(1.0 - (bpm_penalty * 0.6 + energy_penalty * 0.4))
        score.transition_score = max(0.0, sum(transition_scores) / len(transition_scores))
    else:
        score.transition_score = 1.0

    # Overall weighted sum
    score.overall = (
        weights.get("bpm_smoothness", 0.35) * score.bpm_smoothness
        + weights.get("energy_coherence", 0.35) * score.energy_coherence
        + weights.get("genre_consistency", 0.20) * score.genre_consistency
        + weights.get("transition_score", 0.10) * score.transition_score
    )
    score.overall = min(max(score.overall, 0.0), 1.0)
    return score
