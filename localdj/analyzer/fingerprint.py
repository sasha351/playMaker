"""Acoustic fingerprinting via chromaprint / pyacoustid."""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def compute_fingerprint(path: Path | str) -> Optional[str]:
    """Compute the acoustic fingerprint of a file using chromaprint.

    Returns the raw fingerprint string, or None on failure.
    """
    try:
        import acoustid  # type: ignore[import]
        duration, fingerprint = acoustid.fingerprint_file(str(path))
        return fingerprint
    except Exception:  # noqa: BLE001
        return None


def fingerprint_similarity(fp1: str, fp2: str) -> float:
    """Compute a similarity score [0, 1] between two fingerprint strings.

    Uses bitwise Hamming similarity on the compressed fingerprint bytes.
    1.0 = identical, 0.0 = completely different.
    """
    if fp1 == fp2:
        return 1.0
    try:
        import base64
        b1 = base64.b64decode(fp1 + "==")
        b2 = base64.b64decode(fp2 + "==")
        min_len = min(len(b1), len(b2))
        if min_len == 0:
            return 0.0
        # Matching bits out of total bits in the shorter string
        total = min_len * 8
        same_bits = sum(bin(~(a ^ b) & 0xFF).count("1") for a, b in zip(b1[:min_len], b2[:min_len]))
        return same_bits / total
    except Exception:  # noqa: BLE001
        return 0.0
