#!/usr/bin/env python3
"""Native SHIT command interface for the canonical per-recording music library."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.music.music_library import MusicLibrary, read_json

DEFAULT_ROOT = REPO_ROOT / "assistant_data" / "music" / "library"
MIGRATOR = REPO_ROOT / "scripts" / "music" / "migrate_full_music_library.py"


def _index(root):
    return read_json(Path(root) / "library_index.json") or {}


def status(root):
    index = _index(root)
    result = {
        "library_root": str(root),
        "indexed_songs": len(index.get("songs") or {}),
        "indexed_artists": len(index.get("artists") or {}),
        "indexed_albums": len(index.get("albums") or {}),
        "aliases": {
            "spotify_ids": len(index.get("spotify_ids") or {}),
            "recording_mbids": len(index.get("recording_mbids") or {}),
            "isrcs": len(index.get("isrcs") or {}),
            "source_track_ids": len(index.get("source_track_ids") or {}),
            "ambiguous_name_candidates": sum(
                len(rows) > 1 for rows in (index.get("name_candidates") or {}).values()
            ),
        },
    }
    report = read_json(Path(root) / "migration_report.json")
    if isinstance(report, dict):
        result["last_migration_status"] = report.get("status", "report exists")
        result["last_migration_result"] = report.get("migration_result", {})
    print(json.dumps(result, indent=2))


def audit(root):
    result = MusicLibrary(root).audit()
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 2


def run_migration(root, dry_run=False, yes=False):
    command = [sys.executable, str(MIGRATOR), "--root", str(root)]
    if dry_run:
        command.append("--dry-run")
    elif not yes:
        answer = input(
            "This will update the canonical per-recording library. "
            "A timestamped backup is created automatically. Continue? [y/N] "
        ).strip().casefold()
        if answer not in {"y", "yes"}:
            print("Migration cancelled; no library writes performed.")
            return 1
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


def build_parser():
    parser = argparse.ArgumentParser(
        prog="shit",
        description="Spotify Helper & Information Tracker — project command interface",
    )
    commands = parser.add_subparsers(dest="area", required=True)
    library = commands.add_parser("library", help="Manage the canonical per-recording music library")
    actions = library.add_subparsers(dest="action", required=True)
    for name, help_text in (
        ("status", "Show indexed catalogue counts and the last migration result"),
        ("preview", "Preview a full migration without writing files or contacting providers"),
        ("migrate", "Migrate stored profiles and accessible playlist snapshots into the library"),
        ("audit", "Validate canonical records, relations and lookup aliases"),
    ):
        sub = actions.add_parser(name, help=help_text)
        sub.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        if name == "migrate":
            sub.add_argument("--yes", action="store_true", help="Confirm the migration without an interactive prompt")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.action == "status":
        status(args.root)
        return 0
    if args.action == "audit":
        return audit(args.root)
    if args.action == "preview":
        return run_migration(args.root, dry_run=True)
    if args.action == "migrate":
        return run_migration(args.root, yes=args.yes)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

# FILE OVERVIEW
# Purpose: Native command interface for the canonical per-recording music library.
# Commands: status, preview, migrate, audit; preview is read-only and migration
# creates a timestamped backup before writing. Provider requests and playlist
# writes are not performed by the offline migration.
# Related: scripts/music/music_library.py and scripts/music/migrate_full_music_library.py.
