"""BPM detection module."""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def detect_bpm(path: Path | str, *, sr: int = 22050) -> Optional[float]:
    """Detect BPM of an audio file using librosa.

    Falls back to None if librosa is not installed or detection fails.

    Args:
        path: Path to the audio file.
        sr: Sample rate for loading the audio.

    Returns:
        Estimated BPM, or None if detection fails.
    """
    try:
        import librosa  # type: ignore[import]
        import numpy as np

        y, sample_rate = librosa.load(str(path), sr=sr, mono=True)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sample_rate)
        # librosa >= 0.10 returns a 1-element array
        bpm_value = float(np.atleast_1d(tempo)[0])
        return bpm_value if bpm_value > 0 else None
    except Exception:  # noqa: BLE001
        return None
