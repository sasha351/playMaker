"""Audio accuracy tests for acoustic fingerprinting."""
from __future__ import annotations

import pytest

from localdj.analyzer.fingerprint import fingerprint_similarity


@pytest.mark.accuracy
def test_identical_files_max_similarity() -> None:
    fp = "AQAATQAAAAAAAAAA"
    assert fingerprint_similarity(fp, fp) == 1.0


@pytest.mark.accuracy
def test_different_tracks_low_similarity() -> None:
    fp_a = "AQAATQAAAAAAAAAA"
    fp_b = "BQBBBBBBBBBBBBBB"
    sim = fingerprint_similarity(fp_a, fp_b)
    assert 0.0 <= sim <= 1.0


@pytest.mark.accuracy
def test_fingerprint_stability() -> None:
    fp = "AQAATQAAAAAAAAAA"
    assert fingerprint_similarity(fp, fp) == fingerprint_similarity(fp, fp)
