"""Artist/acoustic similarity clustering."""
from __future__ import annotations

import sqlite3
from typing import Any

from localdj.analyzer.fingerprint import fingerprint_similarity


def cluster_by_artist(
    tracks: list[sqlite3.Row | dict[str, Any]],
    seed_artists: list[str],
    max_tracks: int = 50,
) -> list[dict[str, Any]]:
    """Return tracks clustered around the seed artists.

    Exact artist matches come first, then all other tracks ordered by
    artist-name similarity (simple substring match).

    Args:
        tracks: Pool of candidate tracks.
        seed_artists: Artist names to seed the cluster.
        max_tracks: Maximum number of tracks to return.

    Returns:
        Ordered list of track dicts, seed-artist tracks prioritised.
    """
    def _to_dict(t: Any) -> dict[str, Any]:
        return t if isinstance(t, dict) else dict(t)

    seeds_lower = [s.lower() for s in seed_artists]

    def _rank(t: dict[str, Any]) -> int:
        artist = (t.get("artist") or "").lower()
        for i, s in enumerate(seeds_lower):
            if s in artist or artist in s:
                return i
        return len(seeds_lower)

    pool = [_to_dict(t) for t in tracks]
    pool.sort(key=_rank)
    return pool[:max_tracks]


def cluster_by_fingerprint(
    tracks: list[dict[str, Any]],
    seed_fingerprint: str,
    min_similarity: float = 0.4,
    max_tracks: int = 50,
) -> list[dict[str, Any]]:
    """Return tracks acoustically similar to a seed fingerprint.

    Args:
        tracks: Pool of candidate tracks (must have 'fingerprint' field).
        seed_fingerprint: Reference fingerprint string.
        min_similarity: Minimum similarity score to include a track.
        max_tracks: Maximum number of tracks to return.

    Returns:
        Tracks sorted by descending similarity.
    """
    scored: list[tuple[float, dict[str, Any]]] = []
    for t in tracks:
        fp = t.get("fingerprint")
        if not fp:
            continue
        score = fingerprint_similarity(seed_fingerprint, fp)
        if score >= min_similarity:
            scored.append((score, t))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:max_tracks]]
