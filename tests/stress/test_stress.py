"""Stress tests for the LocalDJ pipeline."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from localdj.scanner.library import scan_library
from localdj.db.store import TrackStore


@pytest.mark.slow
@pytest.mark.stress
def test_scan_10k_tracks(tmp_path: Path) -> None:
    for i in range(10_000):
        (tmp_path / f"track_{i:05d}.mp3").write_bytes(b"")
    start = time.monotonic()
    result = list(scan_library(tmp_path))
    elapsed = time.monotonic() - start
    assert len(result) == 10_000
    assert elapsed < 10.0


@pytest.mark.slow
@pytest.mark.stress
def test_db_10k_inserts(tmp_path: Path) -> None:
    store = TrackStore(tmp_path / "stress.db")
    start = time.monotonic()
    for i in range(10_000):
        store.upsert_track({"path": f"/music/track_{i:05d}.mp3", "title": f"Track {i}"})
    elapsed = time.monotonic() - start
    assert elapsed < 10.0
    all_tracks = store.all_tracks()
    assert len(all_tracks) == 10_000


@pytest.mark.slow
@pytest.mark.stress
def test_playlist_gen_10k_library(tmp_path: Path) -> None:
    from localdj.engine.energy_curve import build_energy_curve_playlist
    import random
    rng = random.Random(1)
    tracks = [
        {"path": f"/music/t{i}.mp3", "energy_score": rng.uniform(0, 1), "bpm": rng.uniform(80, 160)}
        for i in range(10_000)
    ]
    start = time.monotonic()
    playlist = build_energy_curve_playlist(tracks, length=50)
    elapsed = time.monotonic() - start
    assert len(playlist) == 50
    assert elapsed < 2.0
