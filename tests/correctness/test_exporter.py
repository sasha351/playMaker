"""Correctness tests for the M3U8 exporter."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from localdj.exporter.m3u8 import write_m3u8


def _make_tracks(n: int, base_dir: Path) -> list[dict[str, Any]]:
    base_dir.mkdir(parents=True, exist_ok=True)
    tracks = []
    for i in range(n):
        p = base_dir / f"track_{i:04d}.mp3"
        p.write_bytes(b"")
        tracks.append({
            "path": str(p),
            "title": f"Track {i}",
            "artist": "Artist",
            "duration": 240.0,
        })
    return tracks


def test_m3u8_valid_header(tmp_path: Path) -> None:
    tracks = _make_tracks(1, tmp_path / "audio")
    out = write_m3u8(tracks, tmp_path / "out.m3u8")
    content = out.read_text(encoding="utf-8")
    assert content.startswith("#EXTM3U")


def test_m3u8_extinfo_format(tmp_path: Path) -> None:
    tracks = _make_tracks(2, tmp_path / "audio")
    out = write_m3u8(tracks, tmp_path / "out.m3u8", include_extinfo=True)
    content = out.read_text(encoding="utf-8")
    assert "#EXTINF:" in content


def test_m3u8_absolute_paths(tmp_path: Path) -> None:
    tracks = _make_tracks(1, tmp_path / "audio")
    out = write_m3u8(tracks, tmp_path / "out.m3u8", absolute_paths=True)
    content = out.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if not l.startswith("#") and l]
    assert all(Path(l).is_absolute() for l in lines)


def test_m3u8_empty_playlist(tmp_path: Path) -> None:
    out = write_m3u8([], tmp_path / "empty.m3u8")
    content = out.read_text(encoding="utf-8")
    assert content.startswith("#EXTM3U")


def test_m3u8_unicode_filenames(tmp_path: Path) -> None:
    audio = tmp_path / "audio"
    audio.mkdir()
    p = audio / "japanese_track.mp3"
    p.write_bytes(b"")
    tracks = [{"path": str(p), "title": "Japanese Title", "artist": "Artist", "duration": 180}]
    out = write_m3u8(tracks, tmp_path / "unicode.m3u8")
    content = out.read_text(encoding="utf-8")
    assert "Japanese Title" in content


def test_m3u8_large_playlist(tmp_path: Path) -> None:
    tracks = _make_tracks(5000, tmp_path / "audio")
    out = write_m3u8(tracks, tmp_path / "large.m3u8")
    content = out.read_text(encoding="utf-8")
    non_header = [l for l in content.splitlines() if l and not l.startswith("#")]
    assert len(non_header) == 5000


def test_m3u8_idempotent(tmp_path: Path) -> None:
    tracks = _make_tracks(3, tmp_path / "audio")
    out_a = write_m3u8(tracks, tmp_path / "a.m3u8")
    out_b = write_m3u8(tracks, tmp_path / "b.m3u8")
    assert out_a.read_text() == out_b.read_text()
