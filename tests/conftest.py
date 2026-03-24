"""Shared test fixtures."""
from __future__ import annotations

import struct
import wave
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_audio_dir(tmp_path: Path) -> Path:
    """Return a temporary directory suitable for audio file fixtures."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    return audio_dir


def _create_minimal_wav(path: Path, duration_s: float = 0.5, sr: int = 44100) -> Path:
    """Write a minimal valid WAV file (sine wave)."""
    import math
    n_samples = int(sr * duration_s)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        for i in range(n_samples):
            sample = int(32767 * math.sin(2 * math.pi * 440 * i / sr))
            wf.writeframes(struct.pack("<h", sample))
    return path


@pytest.fixture()
def wav_file(tmp_path: Path) -> Path:
    """A minimal valid WAV file."""
    return _create_minimal_wav(tmp_path / "test.wav")


@pytest.fixture()
def silent_wav_file(tmp_path: Path) -> Path:
    """A silent (zero-amplitude) WAV file."""
    path = tmp_path / "silent.wav"
    n_samples = 22050
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(b"\x00\x00" * n_samples)
    return path
