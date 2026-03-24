"""SQLite schema definitions."""
from __future__ import annotations

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS tracks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    path            TEXT NOT NULL UNIQUE,
    size            INTEGER,
    mtime           REAL,
    title           TEXT,
    artist          TEXT,
    album           TEXT,
    genre           TEXT,
    year            INTEGER,
    track_number    INTEGER,
    bpm             REAL,
    duration        REAL,
    energy_score    REAL,
    rms             REAL,
    spectral_centroid REAL,
    zero_crossing_rate REAL,
    fingerprint     TEXT,
    duplicate_of    INTEGER REFERENCES tracks(id),
    status          TEXT DEFAULT 'ok' CHECK(status IN ('ok', 'missing', 'quarantined')),
    analyzed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS playlist_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode            TEXT,
    preset          TEXT,
    weights_json    TEXT,
    quality_score   REAL
);

CREATE TABLE IF NOT EXISTS ratings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER REFERENCES playlist_runs(id),
    rating          INTEGER CHECK(rating BETWEEN 1 AND 5),
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ab_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id_a        INTEGER REFERENCES playlist_runs(id),
    run_id_b        INTEGER REFERENCES playlist_runs(id),
    winner          TEXT CHECK(winner IN ('A', 'B', 'tie')),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
