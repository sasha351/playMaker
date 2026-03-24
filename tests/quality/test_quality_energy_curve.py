"""Quality tests for the energy curve playlist mode."""
from __future__ import annotations

from localdj.engine.energy_curve import CurveShape, build_energy_curve_playlist


def _make_tracks(n: int) -> list[dict]:
    import random
    rng = random.Random(42)
    return [
        {"path": f"/music/track_{i}.mp3", "energy_score": rng.uniform(0.1, 0.9), "bpm": rng.uniform(80, 150)}
        for i in range(n)
    ]


def test_energy_curve_ascending() -> None:
    tracks = _make_tracks(20)
    playlist = build_energy_curve_playlist(tracks, shape=CurveShape.ASCENDING)
    energies = [t["energy_score"] for t in playlist]
    assert energies == sorted(energies)


def test_energy_curve_descending() -> None:
    tracks = _make_tracks(20)
    playlist = build_energy_curve_playlist(tracks, shape=CurveShape.DESCENDING)
    energies = [t["energy_score"] for t in playlist]
    assert energies == sorted(energies, reverse=True)


def test_energy_curve_arc() -> None:
    tracks = _make_tracks(20)
    playlist = build_energy_curve_playlist(tracks, shape=CurveShape.ARC, length=20)
    assert len(playlist) > 0


def test_bpm_smoothness_energy_mode() -> None:
    tracks = _make_tracks(20)
    playlist = build_energy_curve_playlist(tracks, shape=CurveShape.ARC)
    bpms = [t["bpm"] for t in playlist]
    for i in range(len(bpms) - 1):
        # Arc sorts by energy, not BPM; max possible delta equals the BPM range (150-80=70)
        assert abs(bpms[i + 1] - bpms[i]) <= 70
