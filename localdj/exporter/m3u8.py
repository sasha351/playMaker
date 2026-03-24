"""M3U8 playlist file writer."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def write_m3u8(
    tracks: list[dict[str, Any]],
    output_path: Path | str,
    *,
    absolute_paths: bool = True,
    include_extinfo: bool = True,
) -> Path:
    """Write tracks to an M3U8 playlist file.

    Args:
        tracks: List of track dicts with at least 'path'. Optional fields:
                'title', 'artist', 'duration' (seconds).
        output_path: Destination .m3u8 file path.
        absolute_paths: Use absolute paths when True; relative to output dir when False.
        include_extinfo: Prepend #EXTINF lines when True.

    Returns:
        The resolved output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_dir = output_path.parent

    lines: list[str] = ["#EXTM3U"]

    for track in tracks:
        track_path = Path(track["path"])
        if absolute_paths:
            file_ref = str(track_path.resolve())
        else:
            try:
                file_ref = str(track_path.resolve().relative_to(output_dir.resolve()))
            except ValueError:
                file_ref = str(track_path.resolve())

        if include_extinfo:
            duration = int(track.get("duration") or -1)
            artist = track.get("artist") or ""
            title = track.get("title") or track_path.stem
            lines.append(f"#EXTINF:{duration},{artist} - {title}")

        lines.append(file_ref)

    content = "\n".join(lines) + "\n"
    output_path.write_text(content, encoding="utf-8")
    return output_path
