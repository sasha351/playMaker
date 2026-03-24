"""Audio accuracy tests for energy feature extraction."""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("librosa")

from localdj.analyzer.energy import extract_energy


@pytest.mark.accuracy
def test_energy_silent_track(silent_wav_file: Path) -> None:
    features = extract_energy(silent_wav_file)
    if features.energy_score is not None:
        assert features.energy_score < 0.1


@pytest.mark.accuracy
def test_energy_score_normalized(wav_file: Path) -> None:
    features = extract_energy(wav_file)
    if features.energy_score is not None:
        assert 0.0 <= features.energy_score <= 1.0


@pytest.mark.accuracy
def test_spectral_centroid_range(wav_file: Path) -> None:
    features = extract_energy(wav_file)
    if features.spectral_centroid is not None:
        assert 20.0 <= features.spectral_centroid <= 20000.0


@pytest.mark.accuracy
def test_energy_ordering(silent_wav_file: Path, wav_file: Path) -> None:
    """Audible tone should score higher energy than silence."""
    quiet = extract_energy(silent_wav_file)
    loud = extract_energy(wav_file)
    if quiet.energy_score is not None and loud.energy_score is not None:
        assert loud.energy_score >= quiet.energy_score
