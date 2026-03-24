"""Recursive library scanner with format detection."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

SUPPORTED_EXTENSIONS = frozenset({
    ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav", ".alac",
})


class LibraryNotFoundError(FileNotFoundError):
    """Raised when the library root directory does not exist."""


@dataclass
class AudioFile:
    """Represents a discovered audio file."""
    path: Path
    extension: str = field(init=False)
    size: int = field(init=False)
    mtime: float = field(init=False)

    def __post_init__(self) -> None:
        self.extension = self.path.suffix.lower()
        stat = self.path.stat()
        self.size = stat.st_size
        self.mtime = stat.st_mtime


def scan_library(root: Path | str, *, follow_symlinks: bool = True) -> Iterator[AudioFile]:
    """Recursively scan *root* for audio files.

    Args:
        root: Directory to scan.
        follow_symlinks: Whether to follow symlinks (default True).

    Yields:
        AudioFile instances for each discovered audio file.

    Raises:
        LibraryNotFoundError: If *root* does not exist.
    """
    root = Path(root)
    if not root.exists():
        raise LibraryNotFoundError(f"Library root not found: {root}")

    seen: set[Path] = set()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        # Avoid infinite symlink loops
        real_dir = Path(dirpath).resolve()
        if real_dir in seen:
            dirnames.clear()
            continue
        seen.add(real_dir)

        for filename in filenames:
            filepath = Path(dirpath) / filename
            if filepath.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    yield AudioFile(path=filepath)
                except OSError:
                    continue
