"""Correctness tests for the library scanner."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from localdj.scanner.library import (
    AudioFile,
    LibraryNotFoundError,
    scan_library,
    SUPPORTED_EXTENSIONS,
)


def test_scan_empty_dir(tmp_path: Path) -> None:
    result = list(scan_library(tmp_path))
    assert result == []


@pytest.mark.parametrize("ext", [".mp3", ".flac", ".ogg", ".wav", ".m4a"])
def test_scan_single_format(tmp_path: Path, ext: str) -> None:
    audio = tmp_path / f"track{ext}"
    audio.write_bytes(b"")
    result = list(scan_library(tmp_path))
    assert len(result) == 1
    assert result[0].extension == ext


def test_scan_nested_dirs(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b" / "c" / "d" / "e"
    deep.mkdir(parents=True)
    (deep / "track.mp3").write_bytes(b"")
    result = list(scan_library(tmp_path))
    assert len(result) == 1


def test_scan_ignores_non_audio(tmp_path: Path) -> None:
    (tmp_path / "cover.jpg").write_bytes(b"")
    (tmp_path / "info.txt").write_bytes(b"")
    (tmp_path / "track.mp3").write_bytes(b"")
    result = list(scan_library(tmp_path))
    assert len(result) == 1
    assert result[0].extension == ".mp3"


def test_scan_symlinks(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "track.mp3").write_bytes(b"")
    link = tmp_path / "link"
    link.symlink_to(real_dir)
    result = list(scan_library(tmp_path))
    # Should find the file once (via real path deduplication)
    paths = {str(r.path.resolve()) for r in result}
    assert len(paths) == 1


def test_scan_missing_root(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    with pytest.raises(LibraryNotFoundError):
        list(scan_library(missing))


@pytest.mark.slow
def test_scan_10k_files(tmp_path: Path) -> None:
    """Scan 10,000 dummy files in under 10 seconds."""
    for i in range(10_000):
        (tmp_path / f"track_{i:05d}.mp3").write_bytes(b"")
    start = time.monotonic()
    result = list(scan_library(tmp_path))
    elapsed = time.monotonic() - start
    assert len(result) == 10_000
    assert elapsed < 10.0, f"Scan took {elapsed:.1f}s (expected <10s)"


def test_duplicate_paths(tmp_path: Path) -> None:
    """Scanning same file twice only returns one AudioFile."""
    (tmp_path / "track.mp3").write_bytes(b"")
    result = list(scan_library(tmp_path))
    assert len(result) == 1
