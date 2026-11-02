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
PREPARER = REPO_ROOT / "scripts" / "music" / "prepare_music_library.py"
SYNCER = REPO_ROOT / "scripts" / "music" / "sync_music_library.py"
HEALTH_CHECKER = REPO_ROOT / "scripts" / "music" / "library_health.py"
CONFIDENCE_AUDIT = REPO_ROOT / "scripts" / "music" / "library_confidence_audit.py"
MAINTAINER = REPO_ROOT / "scripts" / "music" / "library_maintainer.py"


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
            "This updates the canonical library. A timestamped backup is created automatically. Continue? [y/N] "
        ).strip().casefold()
        if answer not in {"y", "yes"}:
            print("Migration cancelled; no library writes performed.")
            return 1
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


def run_preparation(args):
    if args.root != DEFAULT_ROOT:
        print("Custom --root is not supported for full preparation; use the default canonical library root.")
        return 2
    command = [sys.executable, str(PREPARER)]
    for flag in ("execute", "yes", "skip_spotify_refresh", "skip_discogs", "skip_getsongbpm"):
        if getattr(args, flag):
            command.append("--" + flag.replace("_", "-"))
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


def sync_library():
    return subprocess.run([sys.executable, str(SYNCER)], cwd=REPO_ROOT, check=False).returncode


def run_health(args):
    command = [sys.executable, str(HEALTH_CHECKER), "--root", str(args.root)]
    if args.json:
        command.append("--json")
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


def run_confidence(args):
    command = [sys.executable, str(CONFIDENCE_AUDIT), "--root", str(args.root)]
    if args.json:
        command.append("--json")
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode

def run_maintainer(args):
    if args.apply and not args.yes:
        raise SystemExit("--apply requires --yes")
    command = [
        sys.executable, str(MAINTAINER),
        "--root", str(args.root),
        "--music-root", str(DEFAULT_ROOT.parent),
    ]
    if args.apply:
        command.append("--apply")
    if args.yes:
        command.append("--yes")
    if args.json:
        command.append("--json")
    return subprocess.run(command, cwd=REPO_ROOT, check=False).returncode


def build_parser():
    parser = argparse.ArgumentParser(
        prog="shit",
        description="Spotify Helper & Information Tracker — project command interface",
    )
    commands = parser.add_subparsers(dest="area", required=True)
    library = commands.add_parser(
        "library", aliases=["migration"],
        help="Manage the canonical per-recording music library (migration is an alias)",
    )
    actions = library.add_subparsers(dest="action", required=True)
    for name, help_text in (
        ("status", "Show indexed catalogue counts and last migration result"),
        ("preview", "Preview migration without writing or contacting providers"),
        ("migrate", "Migrate stored profiles and accessible playlist snapshots"),
        ("run", "Run the Great Migration (alias for migrate)"),
        ("resume", "Resume the idempotent Great Migration"),
        ("audit", "Validate canonical records, relations and lookup aliases"),
        ("health", "Run comprehensive read-only structural and referential health checks"),
        ("confidence", "Audit identity and field-level metadata confidence without modifying records"),
        ("prepare", "Preflight or run migration plus bounded metadata enrichment"),
        ("sync", "Merge existing enrichment exports into the canonical library"),
        ("verify", "Verify configured provider credentials without changing data"),
    ):
        sub = actions.add_parser(name, help=help_text)
        sub.add_argument("--root", type=Path, default=DEFAULT_ROOT)
        if name in {"migrate", "run", "resume"}:
            sub.add_argument("--yes", action="store_true", help="Skip migration confirmation")
        if name in {"health", "confidence"}:
            sub.add_argument("--json", action="store_true", help="emit machine-readable JSON")
        if name == "prepare":
            sub.add_argument("--execute", action="store_true", help="Run migration and enrichment; default is read-only preflight")
            sub.add_argument("--yes", action="store_true", help="Skip confirmation (requires --execute)")
            sub.add_argument("--skip-spotify-refresh", action="store_true")
            sub.add_argument("--skip-discogs", action="store_true")
            sub.add_argument("--skip-getsongbpm", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.action == "status":
        status(args.root)
        return 0
    if args.action == "audit":
        return audit(args.root)
    if args.action == "health":
        return run_health(args)
    if args.action == "confidence":
        return run_confidence(args)
    if args.action == "preview":
        return run_migration(args.root, dry_run=True)
    if args.action in {"migrate", "run", "resume"}:
        return run_migration(args.root, yes=args.yes)
    if args.action == "prepare":
        if args.yes and not args.execute:
            raise SystemExit("--yes requires --execute")
        return run_preparation(args)
    if args.action == "verify":
        verifier = REPO_ROOT / "scripts" / "music" / "verify_provider_credentials.py"
        return subprocess.run([sys.executable, str(verifier)], cwd=REPO_ROOT, check=False).returncode
    if args.action == "sync":
        if args.root != DEFAULT_ROOT:
            print("Custom --root is not supported for sync; use the default canonical library root.")
            return 2
        return sync_library()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Native command interface for the canonical per-recording music library.
# Commands: status, preview, migrate, audit, health, confidence, prepare, sync, verify.
# Health is a separate read-only scan and does not instantiate the auto-rebuilding resolver.
# Prepare defaults to a read-only preflight; --execute runs migration and bounded
# provider enrichment. Sync merges existing durable exports into the canonical store.
# Offline migration creates a timestamped backup and makes no provider requests.
# Related: scripts/music/music_library.py, prepare_music_library.py, sync_music_library.py.
