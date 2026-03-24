# LocalDJ Architecture

## Module Overview

```
localdj/
├── scanner/    Recursive filesystem walker; yields AudioFile objects
├── analyzer/   Feature extraction (metadata, BPM, energy, fingerprint)
├── db/         SQLite persistence layer (schema + CRUD)
├── engine/     Playlist generation algorithms
├── exporter/   Output formats (M3U8)
├── tuner/      Quality scoring and weight auto-tuning
└── cli/        Click-based command-line interface
```

## Data Flow

```
dj scan <root>
   └─► scan_library()  ──► AudioFile(path, size, mtime)
          └─► extract_metadata()  ──► TrackMetadata
                 └─► TrackStore.upsert_track()  ──► SQLite tracks table

dj generate
   └─► TrackStore.all_tracks()  ──► track pool
          └─► [engine mode]
                 energy-curve  ──► build_energy_curve_playlist()
                 vibe          ──► apply_preset()
                 cluster       ──► cluster_by_artist()
          └─► score_playlist()  ──► PlaylistScore
          └─► TrackStore.save_run()
          └─► write_m3u8()  ──► playlist.m3u8
```

## Database Schema

### tracks
Core table storing one row per audio file.

| Column             | Type    | Description                    |
|--------------------|---------|--------------------------------|
| id                 | INTEGER | Primary key                    |
| path               | TEXT    | Unique file path               |
| size               | INTEGER | File size in bytes             |
| mtime              | REAL    | Last-modified timestamp        |
| title/artist/album | TEXT    | ID3 tags                       |
| bpm                | REAL    | Detected beats per minute      |
| energy_score       | REAL    | Composite energy [0, 1]        |
| fingerprint        | TEXT    | Chromaprint fingerprint        |
| status             | TEXT    | ok / missing / quarantined     |

### playlist_runs
Each call to `dj generate` logs a run with mode, preset, weights, and quality score.

### ratings
Human 1–5 star ratings linked to playlist runs.

### ab_results
Pairwise A/B comparison results (winner = A/B/tie).
