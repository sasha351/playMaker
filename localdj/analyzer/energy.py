"""Energy and mood feature extraction."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class EnergyFeatures:
    """Audio energy and mood features for a track."""
    rms: Optional[float] = None           # Root mean square energy [0, 1]
    spectral_centroid: Optional[float] = None  # Hz
    zero_crossing_rate: Optional[float] = None
    energy_score: Optional[float] = None  # Normalized composite [0, 1]


def extract_energy(
    path: Path | str,
    *,
    sr: int = 22050,
    rms_weight: float = 0.5,
    spectral_weight: float = 0.3,
    zcr_weight: float = 0.2,
) -> EnergyFeatures:
    """Extract energy features from an audio file.

    Args:
        path: Path to the audio file.
        sr: Sample rate.
        rms_weight: Weight for RMS contribution to energy_score.
        spectral_weight: Weight for spectral centroid contribution.
        zcr_weight: Weight for zero-crossing rate contribution.

    Returns:
        EnergyFeatures with populated values where computation succeeded.
    """
    features = EnergyFeatures()
    try:
        import librosa  # type: ignore[import]
        import numpy as np

        y, sample_rate = librosa.load(str(path), sr=sr, mono=True)
        if len(y) == 0:
            return features

        # RMS energy
        rms_arr = librosa.feature.rms(y=y)
        rms_mean = float(np.mean(rms_arr))
        features.rms = min(rms_mean * 10.0, 1.0)  # rough normalisation

        # Spectral centroid
        sc_arr = librosa.feature.spectral_centroid(y=y, sr=sample_rate)
        features.spectral_centroid = float(np.mean(sc_arr))

        # Zero-crossing rate
        zcr_arr = librosa.feature.zero_crossing_rate(y=y)
        features.zero_crossing_rate = float(np.mean(zcr_arr))

        # Normalised spectral centroid component (0–1 over 20–20000 Hz)
        sc_norm = min(max((features.spectral_centroid - 20.0) / 19980.0, 0.0), 1.0)

        # Normalised ZCR component (typical range 0–0.5, so scale by 2)
        zcr_norm = min(features.zero_crossing_rate * 2.0, 1.0)

        energy_score = (
            rms_weight * (features.rms or 0.0)
            + spectral_weight * sc_norm
            + zcr_weight * zcr_norm
        )
        features.energy_score = min(max(energy_score, 0.0), 1.0)

    except Exception:  # noqa: BLE001
        pass

    return features
