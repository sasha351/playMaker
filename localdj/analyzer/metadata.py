"""ID3/tag extraction via mutagen."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TrackMetadata:
    """Metadata extracted from an audio file."""
    path: Path
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    track_number: Optional[int] = None
    bpm: Optional[float] = None
    duration: Optional[float] = None  # seconds


def extract_metadata(path: Path | str) -> TrackMetadata:
    """Extract metadata tags from an audio file using mutagen.

    Args:
        path: Path to the audio file.

    Returns:
        TrackMetadata populated from available tags. Missing fields are None.
    """
    path = Path(path)
    meta = TrackMetadata(path=path)

    try:
        from mutagen import File as MutagenFile

        audio = MutagenFile(path, easy=True)
        if audio is None:
            return meta

        meta.duration = getattr(audio.info, "length", None)

        def _first(tag: str) -> Optional[str]:
            val = audio.tags.get(tag) if audio.tags else None
            if val and isinstance(val, list):
                return str(val[0]).strip() or None
            return None

        meta.title = _first("title")
        meta.artist = _first("artist")
        meta.album = _first("album")
        meta.genre = _first("genre")

        year_str = _first("date")
        if year_str:
            try:
                meta.year = int(year_str[:4])
            except (ValueError, TypeError):
                pass

        track_str = _first("tracknumber")
        if track_str:
            try:
                meta.track_number = int(track_str.split("/")[0])
            except (ValueError, TypeError):
                pass

        bpm_str = _first("bpm")
        if bpm_str:
            try:
                meta.bpm = float(bpm_str)
            except (ValueError, TypeError):
                pass

    except Exception:  # noqa: BLE001 — graceful degradation
        pass

    return meta
