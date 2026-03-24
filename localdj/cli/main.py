"""LocalDJ CLI — base command is `dj`."""
from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

console = Console()

_DEFAULT_DB = Path.home() / ".localdj" / "library.db"


def _get_db(db_path: str | None) -> "TrackStore":  # noqa: F821
    from localdj.db.store import TrackStore
    return TrackStore(Path(db_path) if db_path else _DEFAULT_DB)


@click.group()
@click.version_option(package_name="localdj")
def cli() -> None:
    """LocalDJ — smart local-first playlist generator."""


# -- scan ----------------------------------------------------------------------

@cli.command()
@click.argument("root", type=click.Path(exists=True, file_okay=False))
@click.option("--db", default=None, help="Path to SQLite database.")
@click.option("--json", "as_json", is_flag=True, help="Output summary as JSON.")
@click.option("--no-analyze", is_flag=True, help="Skip audio analysis (metadata only).")
def scan(root: str, db: Optional[str], as_json: bool, no_analyze: bool) -> None:
    """Scan a music library ROOT directory."""
    from localdj.scanner.library import scan_library, LibraryNotFoundError
    from localdj.analyzer.metadata import extract_metadata

    store = _get_db(db)
    root_path = Path(root)

    try:
        files = list(scan_library(root_path))
    except LibraryNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    new_count = 0
    updated_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        disable=as_json,
    ) as progress:
        task = progress.add_task("Scanning...", total=len(files))
        for af in files:
            existing = store.get_track(str(af.path))
            if existing and existing["mtime"] == af.mtime:
                progress.advance(task)
                continue

            meta = extract_metadata(af.path)
            data = {
                "path": str(af.path),
                "size": af.size,
                "mtime": af.mtime,
                "title": meta.title,
                "artist": meta.artist,
                "album": meta.album,
                "genre": meta.genre,
                "year": meta.year,
                "track_number": meta.track_number,
                "bpm": meta.bpm,
                "duration": meta.duration,
            }
            if existing:
                updated_count += 1
            else:
                new_count += 1
            store.upsert_track(data)
            progress.advance(task)

    total = len(files)
    if as_json:
        import json
        click.echo(json.dumps({"total": total, "new": new_count, "updated": updated_count}))
    else:
        console.print(
            f"[green]Scan complete.[/green] "
            f"{total} files | {new_count} new | {updated_count} updated"
        )


# -- generate ------------------------------------------------------------------

@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["energy-curve", "vibe", "cluster"]),
    default="energy-curve",
    show_default=True,
)
@click.option("--preset", default=None, help="Vibe preset name (for --mode vibe).")
@click.option("--seed-artist", "seed_artist", default=None, help="Seed artist (for --mode cluster).")
@click.option("--length", default=20, show_default=True, help="Max number of tracks.")
@click.option(
    "--shape",
    type=click.Choice(["ascending", "descending", "arc"]),
    default="arc",
    show_default=True,
    help="Energy curve shape (for --mode energy-curve).",
)
@click.option("--output", "-o", default="~/playlists", help="Output directory.", show_default=True)
@click.option("--relative", is_flag=True, help="Use relative paths in M3U8.")
@click.option("--no-interactive", is_flag=True, help="Suppress interactive prompts.")
@click.option("--db", default=None, help="Path to SQLite database.")
@click.option("--bpm-min", "bpm_min", default=None, type=float, help="Minimum BPM filter.")
@click.option("--bpm-max", "bpm_max", default=None, type=float, help="Maximum BPM filter.")
@click.option("--verbose", is_flag=True, help="Print per-track detail.")
@click.option("--quiet", is_flag=True, help="Suppress all output except errors.")
def generate(
    mode: str,
    preset: Optional[str],
    seed_artist: Optional[str],
    length: int,
    shape: str,
    output: str,
    relative: bool,
    no_interactive: bool,
    db: Optional[str],
    bpm_min: Optional[float],
    bpm_max: Optional[float],
    verbose: bool,
    quiet: bool,
) -> None:
    """Generate a smart playlist."""
    from localdj.engine.energy_curve import build_energy_curve_playlist, CurveShape
    from localdj.engine.vibe_presets import apply_preset, BUILTIN_PRESETS, VibePreset
    from localdj.engine.clustering import cluster_by_artist
    from localdj.exporter.m3u8 import write_m3u8
    from localdj.tuner.scorer import score_playlist
    from localdj.tuner.profiles import default_weights

    store = _get_db(db)
    all_tracks = [dict(t) for t in store.all_tracks()]

    if not all_tracks:
        if not quiet:
            console.print("[yellow]No tracks in library. Run `dj scan <path>` first.[/yellow]")
        sys.exit(1)

    # Apply BPM filter
    if bpm_min is not None:
        all_tracks = [t for t in all_tracks if t.get("bpm") and t["bpm"] >= bpm_min]
    if bpm_max is not None:
        all_tracks = [t for t in all_tracks if t.get("bpm") and t["bpm"] <= bpm_max]

    # Build playlist
    if mode == "energy-curve":
        curve_shape = CurveShape(shape)
        playlist = build_energy_curve_playlist(all_tracks, shape=curve_shape, length=length)
    elif mode == "vibe":
        preset_name = preset or "chill_sunday"
        if preset_name in BUILTIN_PRESETS:
            vibe = BUILTIN_PRESETS[preset_name]
        else:
            vibe = VibePreset(name=preset_name)
        playlist = apply_preset(all_tracks, vibe, max_tracks=length)
    else:  # cluster
        artists = [a.strip() for a in (seed_artist or "").split(",") if a.strip()]
        playlist = cluster_by_artist(all_tracks, artists, max_tracks=length)

    if not playlist:
        if not quiet:
            console.print("[yellow]No tracks matched the criteria.[/yellow]")
        sys.exit(1)

    # Score
    weights = default_weights()
    score = score_playlist(playlist, weights=weights)
    run_id = store.save_run(mode, preset, weights, score.overall)

    # Export
    output_dir = Path(output).expanduser()
    datestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    preset_part = f"_{preset}" if preset else ""
    filename = f"{mode.replace('-', '_')}{preset_part}_{datestamp}.m3u8"
    out_path = output_dir / filename

    write_m3u8(playlist, out_path, absolute_paths=not relative)

    if not quiet:
        console.print(f"[green]Playlist saved:[/green] {out_path}")
        console.print(
            f"  {len(playlist)} tracks · quality score: {score.overall:.2f}"
        )

    if verbose:
        table = Table(title="Playlist", show_lines=True)
        table.add_column("#", style="dim")
        table.add_column("Title")
        table.add_column("Artist")
        table.add_column("BPM", justify="right")
        table.add_column("Energy", justify="right")
        for i, t in enumerate(playlist, 1):
            table.add_row(
                str(i),
                t.get("title") or Path(t["path"]).stem,
                t.get("artist") or "",
                f"{t.get('bpm') or 0:.0f}",
                f"{t.get('energy_score') or 0:.2f}",
            )
        console.print(table)


# -- tune ----------------------------------------------------------------------

@cli.command()
@click.option("--dump-weights", is_flag=True, help="Print current weights as JSON.")
@click.option("--apply", "apply_file", default=None, type=click.Path(), help="Apply a suggestions TOML file.")
@click.option("--db", default=None, help="Path to SQLite database.")
def tune(dump_weights: bool, apply_file: Optional[str], db: Optional[str]) -> None:
    """View or adjust playlist generation weights."""
    from localdj.tuner.profiles import default_weights, load_profile, save_profile

    weights = default_weights()

    if dump_weights:
        import json
        click.echo(json.dumps(weights, indent=2))
        return

    if apply_file:
        import tomllib
        with open(apply_file, "rb") as fh:
            data = tomllib.load(fh)
        suggested = data.get("suggested_weights", {})
        if suggested:
            save_profile("active", suggested)
            console.print("[green]Weights applied from suggestion file.[/green]")
        else:
            console.print("[yellow]No suggested_weights found in file.[/yellow]")
        return

    console.print("[bold]Current weights:[/bold]")
    for k, v in weights.items():
        console.print(f"  {k}: {v:.4f}")


# -- history -------------------------------------------------------------------

@cli.command()
@click.option("--last", default=10, show_default=True, help="Number of recent runs to show.")
@click.option("--db", default=None, help="Path to SQLite database.")
def history(last: int, db: Optional[str]) -> None:
    """Show recent playlist generation history."""
    store = _get_db(db)
    runs = store.get_runs(limit=last)
    if not runs:
        console.print("No history yet.")
        return
    table = Table(title="Recent Runs", show_lines=True)
    table.add_column("ID", style="dim")
    table.add_column("Created")
    table.add_column("Mode")
    table.add_column("Preset")
    table.add_column("Quality", justify="right")
    for run in runs:
        table.add_row(
            str(run["id"]),
            str(run["created_at"]),
            run["mode"] or "",
            run["preset"] or "",
            f"{run['quality_score']:.2f}" if run["quality_score"] is not None else "-",
        )
    console.print(table)


# -- ab-compare ----------------------------------------------------------------

@cli.command("ab-compare")
@click.option("--config-a", "config_a", required=True, type=click.Path(exists=True))
@click.option("--config-b", "config_b", required=True, type=click.Path(exists=True))
@click.option("--db", default=None, help="Path to SQLite database.")
def ab_compare(config_a: str, config_b: str, db: Optional[str]) -> None:
    """Run an A/B comparison between two config files."""
    console.print("[bold]A/B comparison is available in interactive mode.[/bold]")
    console.print(f"Config A: {config_a}")
    console.print(f"Config B: {config_b}")
    console.print("Use `dj tune` to review and apply results.")
