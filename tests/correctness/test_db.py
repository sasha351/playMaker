"""Correctness tests for the SQLite store."""
from __future__ import annotations

from pathlib import Path

import pytest

from localdj.db.store import TrackStore


@pytest.fixture()
def store(tmp_path: Path) -> TrackStore:
    return TrackStore(tmp_path / "test.db")


def test_schema_migrations(store: TrackStore) -> None:
    cur = store._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    tables = {row[0] for row in cur.fetchall()}
    assert "tracks" in tables
    assert "playlist_runs" in tables
    assert "ratings" in tables
    assert "ab_results" in tables


def test_insert_and_retrieve_track(store: TrackStore) -> None:
    store.upsert_track({"path": "/music/track.mp3", "title": "Test", "artist": "Tester"})
    row = store.get_track("/music/track.mp3")
    assert row is not None
    assert row["title"] == "Test"
    assert row["artist"] == "Tester"


def test_update_existing_track(store: TrackStore) -> None:
    store.upsert_track({"path": "/music/track.mp3", "title": "Old"})
    store.upsert_track({"path": "/music/track.mp3", "title": "New"})
    row = store.get_track("/music/track.mp3")
    assert row["title"] == "New"
    count = store._conn.execute(
        "SELECT COUNT(*) FROM tracks WHERE path='/music/track.mp3'"
    ).fetchone()[0]
    assert count == 1


def test_query_by_bpm_range(store: TrackStore) -> None:
    store.upsert_track({"path": "/music/slow.mp3", "bpm": 80.0})
    store.upsert_track({"path": "/music/fast.mp3", "bpm": 140.0})
    result = store.query_by_bpm_range(70, 100)
    assert len(result) == 1
    assert result[0]["path"] == "/music/slow.mp3"


def test_query_by_genre(store: TrackStore) -> None:
    store.upsert_track({"path": "/music/jazz.mp3", "genre": "Jazz"})
    store.upsert_track({"path": "/music/rock.mp3", "genre": "Rock"})
    result = store.query_by_genre("jazz")
    assert len(result) == 1
    assert result[0]["path"] == "/music/jazz.mp3"


def test_feedback_table(store: TrackStore) -> None:
    run_id = store.save_run("energy-curve", None, {}, 0.75)
    store.save_rating(run_id, 4, "Great!")
    ratings = store.get_ratings()
    assert len(ratings) >= 1
    assert ratings[0]["rating"] == 4
