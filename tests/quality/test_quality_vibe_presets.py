"""Quality tests for vibe preset mode."""
from __future__ import annotations

from localdj.engine.vibe_presets import BUILTIN_PRESETS, apply_preset


def _make_tracks(n: int = 100) -> list[dict]:
    import random
    rng = random.Random(99)
    genres = ["ambient", "indie", "folk", "jazz", "rock", "electronic", "pop"]
    return [
        {
            "path": f"/music/track_{i}.mp3",
            "bpm": rng.uniform(55, 165),
            "energy_score": rng.uniform(0.0, 1.0),
            "genre": rng.choice(genres),
        }
        for i in range(n)
    ]


def test_chill_sunday_bpm_range() -> None:
    tracks = _make_tracks(200)
    preset = BUILTIN_PRESETS["chill_sunday"]
    playlist = apply_preset(tracks, preset)
    for t in playlist:
        if t.get("bpm") is not None:
            assert 60 <= t["bpm"] <= 95


def test_chill_sunday_energy_cap() -> None:
    tracks = _make_tracks(200)
    preset = BUILTIN_PRESETS["chill_sunday"]
    playlist = apply_preset(tracks, preset)
    for t in playlist:
        if t.get("energy_score") is not None:
            assert t["energy_score"] <= 0.5


def test_morning_fuel_bpm_floor() -> None:
    tracks = _make_tracks(200)
    preset = BUILTIN_PRESETS["morning_fuel"]
    playlist = apply_preset(tracks, preset)
    for t in playlist:
        if t.get("bpm") is not None:
            assert t["bpm"] >= 118


def test_genre_consistency_per_preset() -> None:
    tracks = _make_tracks(500)
    preset = BUILTIN_PRESETS["chill_sunday"]
    playlist = apply_preset(tracks, preset, max_tracks=50)
    if not playlist:
        return
    genres = [t.get("genre") for t in playlist if t.get("genre")]
    if not genres:
        return
    dominant = max(set(genres), key=genres.count)
    consistency = genres.count(dominant) / len(genres)
    # With chill_sunday biasing 4/7 genres, dominant share should exceed random (1/7 ~ 14%)
    assert consistency >= 0.15
