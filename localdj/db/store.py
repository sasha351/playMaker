"""SQLite CRUD and query layer."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from localdj.db.schema import SCHEMA_SQL


class TrackStore:
    """Manages track persistence in a SQLite database."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._apply_schema()

    def _apply_schema(self) -> None:
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------
    # Track CRUD
    # ------------------------------------------------------------------

    def upsert_track(self, data: dict[str, Any]) -> int:
        """Insert or update a track row. Returns the row id."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "path")
        sql = (
            f"INSERT INTO tracks ({columns}) VALUES ({placeholders}) "
            f"ON CONFLICT(path) DO UPDATE SET {updates}"
        )
        self._conn.execute(sql, list(data.values()))
        self._conn.commit()
        # Retrieve the id of the upserted row
        row = self._conn.execute("SELECT id FROM tracks WHERE path=?", (data["path"],)).fetchone()
        return row["id"]

    def get_track(self, path: str) -> Optional[sqlite3.Row]:
        return self._conn.execute("SELECT * FROM tracks WHERE path=?", (path,)).fetchone()

    def get_track_by_id(self, track_id: int) -> Optional[sqlite3.Row]:
        return self._conn.execute("SELECT * FROM tracks WHERE id=?", (track_id,)).fetchone()

    def all_tracks(self, include_missing: bool = False) -> list[sqlite3.Row]:
        if include_missing:
            return self._conn.execute("SELECT * FROM tracks").fetchall()
        return self._conn.execute(
            "SELECT * FROM tracks WHERE status='ok'"
        ).fetchall()

    def query_by_bpm_range(self, bpm_min: float, bpm_max: float) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM tracks WHERE status='ok' AND bpm >= ? AND bpm <= ?",
            (bpm_min, bpm_max),
        ).fetchall()

    def query_by_genre(self, genre: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM tracks WHERE status='ok' AND LOWER(genre) LIKE ?",
            (f"%{genre.lower()}%",),
        ).fetchall()

    def mark_missing(self, path: str) -> None:
        self._conn.execute(
            "UPDATE tracks SET status='missing' WHERE path=?", (path,)
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Playlist runs
    # ------------------------------------------------------------------

    def save_run(
        self,
        mode: str,
        preset: Optional[str],
        weights: dict[str, float],
        quality_score: float,
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO playlist_runs (mode, preset, weights_json, quality_score) VALUES (?,?,?,?)",
            (mode, preset, json.dumps(weights), quality_score),
        )
        self._conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_runs(self, limit: int = 50) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT * FROM playlist_runs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()

    # ------------------------------------------------------------------
    # Ratings / A-B
    # ------------------------------------------------------------------

    def save_rating(self, run_id: int, rating: int, notes: str = "") -> None:
        self._conn.execute(
            "INSERT INTO ratings (run_id, rating, notes) VALUES (?,?,?)",
            (run_id, rating, notes),
        )
        self._conn.commit()

    def save_ab_result(self, run_id_a: int, run_id_b: int, winner: str) -> None:
        self._conn.execute(
            "INSERT INTO ab_results (run_id_a, run_id_b, winner) VALUES (?,?,?)",
            (run_id_a, run_id_b, winner),
        )
        self._conn.commit()

    def get_ratings(self, limit: int = 50) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT r.*, p.mode, p.preset, p.quality_score FROM ratings r "
            "JOIN playlist_runs p ON r.run_id = p.id "
            "ORDER BY r.created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
