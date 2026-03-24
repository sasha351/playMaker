"""Audio accuracy tests for BPM detection."""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import pytest

pytest.importorskip("librosa")

from localdj.analyzer.bpm import detect_bpm


def _make_click_track(path: Path, bpm: float, sr: int = 22050, duration: float = 4.0) -> Path:
    """Create a WAV file with a click track at the given BPM."""
    n_samples = int(sr * duration)
    interval = sr * 60.0 / bpm
    samples = [0.0] * n_samples
    click_len = int(sr * 0.01)
    pos = 0.0
    while pos < n_samples:
        for k in range(click_len):
            idx = int(pos) + k
            if idx < n_samples:
                samples[idx] = math.sin(2 * math.pi * 1000 * k / sr)
        pos += interval

    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        for s in samples:
            wf.writeframes(struct.pack("<h", int(s * 32767)))
    return path


@pytest.mark.accuracy
def test_bpm_known_120(tmp_path: Path) -> None:
    audio = _make_click_track(tmp_path / "click_120.wav", 120.0)
    bpm = detect_bpm(audio)
    assert bpm is not None
    assert abs(bpm - 120.0) <= 4 or abs(bpm - 60.0) <= 4


@pytest.mark.accuracy
def test_bpm_known_90(tmp_path: Path) -> None:
    audio = _make_click_track(tmp_path / "click_90.wav", 90.0)
    bpm = detect_bpm(audio)
    assert bpm is not None
    assert abs(bpm - 90.0) <= 4 or abs(bpm - 45.0) <= 4


@pytest.mark.accuracy
def test_bpm_no_clear_beat(silent_wav_file: Path) -> None:
    bpm = detect_bpm(silent_wav_file)
    assert bpm is None or isinstance(bpm, float)
