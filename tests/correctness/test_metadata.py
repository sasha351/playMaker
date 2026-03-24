"""Correctness tests for metadata extraction."""
from __future__ import annotations

from pathlib import Path

import pytest

from localdj.analyzer.metadata import TrackMetadata, extract_metadata


def test_extract_no_tags(wav_file: Path) -> None:
    meta = extract_metadata(wav_file)
    assert isinstance(meta, TrackMetadata)
    assert meta.path == wav_file


def test_extract_partial_tags(tmp_path: Path) -> None:
    """Missing fields return None, not an error."""
    audio_path = tmp_path / "noisy.mp3"
    audio_path.write_bytes(b"ID3" + b"\x00" * 100)
    meta = extract_metadata(audio_path)
    assert meta.title is None or isinstance(meta.title, str)
    assert meta.bpm is None or isinstance(meta.bpm, float)


def test_extract_corrupt_file(tmp_path: Path) -> None:
    """Gracefully skip files that cannot be decoded."""
    corrupt = tmp_path / "corrupt.mp3"
    corrupt.write_bytes(b"\xFF\xFE" * 50)
    meta = extract_metadata(corrupt)
    assert isinstance(meta, TrackMetadata)
