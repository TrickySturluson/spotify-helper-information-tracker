#!/usr/bin/env python3
"""Preview or safely rebuild only the derived canonical Library index.

Default mode is read-only. Applying a rebuild requires both --apply and
--repair-index, creates a timestamped backup, verifies alias preservation,
uses atomic JSON replacement, and rolls back if the post-repair health check fails.

Run: python scripts/music/library_maintenance.py [--json]
Apply: python scripts/music/library_maintenance.py --apply --repair-index
No provider requests or Spotify playlist writes are performed.
"""
import argparse
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.music.library_health import inspect_library
    from scripts.music.music_library import MusicLibrary, read_json, write_json
except ModuleNotFoundError:
    # Direct script execution puts scripts/music, not the repository root, on sys.path.
    from library_health import inspect_library
    from music_library import MusicLibrary, read_json, write_json

ALIAS_MAPS = ("spotify_ids", "recording_mbids", "isrcs", "source_track_ids")


def _build_expected_index(root):
    """Rebuild the derived index in a temporary directory over read-only record links."""
    root = Path(root)
    with tempfile.TemporaryDirectory(prefix="shit-library-index-preview-") as temp:
        target = Path(temp)
        for name in ("songs", "artists", "albums"):
            source = root / name
            if source.exists():
                (target / name).symlink_to(source, target_is_directory=True)
        # Empty index forces the existing canonical index builder to scan records.
        library = MusicLibrary(target)
        generated = read_json(target / "library_index.json")
        if not isinstance(generated, dict):
            raise RuntimeError("Could not build a valid preview index from canonical records.")
        return generated


def _subset_preserved(old, new):
    """Return missing derived keys; any loss blocks an automatic rebuild."""
    missing = {}
    if not isinstance(old, dict):
        return {"unreadable_existing_index": ["existing index is not a JSON object"]}
    for collection in ("songs", "artists", "albums"):
        old_rows = old.get(collection, old.get("recordings", {}) if collection == "songs" else {})
        new_rows = new.get(collection, {})
        if isinstance(old_rows, dict):
            lost = sorted(set(old_rows) - set(new_rows if isinstance(new_rows, dict) else {}))
            if lost:
                missing[collection] = lost[:25]
    for name in ALIAS_MAPS:
        old_rows, new_rows = old.get(name, {}), new.get(name, {})
        if isinstance(old_rows, dict):
            lost = sorted(set(old_rows) - set(new_rows if isinstance(new_rows, dict) else {}))
            if lost:
                missing[name] = lost[:25]
    old_candidates = old.get("name_candidates", {})
    new_candidates = new.get("name_candidates", {})
    if isinstance(old_candidates, dict) and isinstance(new_candidates, dict):
        lost = []
        for alias, targets in old_candidates.items():
            rebuilt = new_candidates.get(alias, [])
            if isinstance(targets, list) and not set(targets).issubset(set(rebuilt if isinstance(rebuilt, list) else [])):
                lost.append(alias)
        if lost:
            missing["name_candidates"] = lost[:25]
    return missing


def plan_maintenance(root):
    """Return a no-write, no-network plan for the safe derived-index repair."""
    root = Path(root)
    health = inspect_library(root)
    index_path = root / "library_index.json"
    old_index = read_json(index_path)
    try:
        expected = _build_expected_index(root)
        build_error = None
    except Exception as error:
        expected, build_error = None, f"{type(error).__name__}: {error}"
    if expected is None:
        missing = {"build": [build_error or "preview failed"]}
    elif not index_path.exists():
        missing = {}
    elif old_index is None:
        missing = {"unreadable_existing_index": ["existing index is present but is not valid JSON"]}
    else:
        missing = _subset_preserved(old_index, expected)

    errors = health.get("errors", [])
    findings = list(errors) + list(health.get("warnings", []))
    def index_related(message):
        value = str(message).casefold()
        return (
            value.startswith(("library index", "songs index", "artists index", "albums index"))
            or " alias " in value
            or "name candidate alias" in value
            or "canonical songs record is not referenced by the index" in value
            or "canonical artists record is not referenced by the index" in value
            or "canonical albums record is not referenced by the index" in value
        )
    non_index_findings = [item for item in findings if not index_related(item)]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "preview",
        "root": str(root),
        "health_ok": health.get("ok", False),
        "health_errors": len(errors),
        "health_warnings": len(health.get("warnings", [])),
        "repair_type": "derived_index_rebuild",
        "repair_needed": bool(findings or missing) and not non_index_findings,
        "safe_to_rebuild": bool(expected is not None and not missing and not non_index_findings),
        "blocking_record_findings": non_index_findings[:25],
        "aliases_or_records_that_would_be_lost": missing,
        "current_counts": health.get("counts", {}),
        "proposed_counts": {
            name: len(expected.get(name, {})) for name in ("songs", "artists", "albums")
        } if expected else {},
        "provider_requests": 0,
        "spotify_playlist_writes": 0,
        "_proposed_index": expected,
    }


def maintain(root, apply=False, repair_index=False):
    report = plan_maintenance(root)
    proposed = report.pop("_proposed_index", None)
    report["mode"] = "apply" if apply else "preview"
    report["changed"] = False
    report["backup_path"] = None
    if not apply:
        return report
    if not repair_index:
        report["error"] = "Applying maintenance requires explicit --repair-index."
        return report
    if not report["repair_needed"]:
        report["message"] = "No health findings require an index rebuild."
        return report
    if not report["safe_to_rebuild"] or not isinstance(proposed, dict):
        report["error"] = "Index rebuild refused: canonical records contain non-index errors or existing aliases would be lost."
        return report

    root = Path(root)
    index_path = root / "library_index.json"
    backup_root = root.parent / (
        "library.backup-maintenance-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    )
    backup_root.mkdir(parents=True, exist_ok=False)
    backup_path = backup_root / "library_index.json"
    existed = index_path.is_file()
    if existed:
        shutil.copy2(index_path, backup_path)
        report["backup_path"] = str(backup_path)

    try:
        write_json(index_path, proposed)
        after = inspect_library(root)
        if after.get("errors") or after.get("warnings"):
            if existed:
                shutil.copy2(backup_path, index_path.with_suffix(".rollback.tmp"))
                index_path.with_suffix(".rollback.tmp").replace(index_path)
            else:
                index_path.unlink(missing_ok=True)
            report["error"] = "Post-repair health check failed; original index restored."
            report["post_repair_errors"] = after["errors"][:25]
            return report
        report["changed"] = True
        report["post_repair_health_ok"] = True
        report["post_repair_counts"] = after.get("counts", {})
        return report
    except Exception as error:
        if existed and backup_path.exists():
            shutil.copy2(backup_path, index_path.with_suffix(".rollback.tmp"))
            index_path.with_suffix(".rollback.tmp").replace(index_path)
        elif not existed:
            index_path.unlink(missing_ok=True)
        report["error"] = f"{type(error).__name__}: {error}; rollback attempted."
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2] / "assistant_data/music/library")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--repair-index", action="store_true")
    args = parser.parse_args(argv)
    if args.repair_index and not args.apply:
        parser.error("--repair-index requires --apply")
    report = maintain(args.root, apply=args.apply, repair_index=args.repair_index)
    report.pop("aliases_or_records_that_would_be_lost", None) if args.json is False else None
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not report.get("error") else 2


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Safe, explicit maintenance for deterministic derived Library index damage.
# Default: Read-only preview; no network requests or playlist writes.
# Apply: Requires --apply --repair-index, alias-preservation proof, timestamped backup,
#        atomic replacement, and post-repair health validation with rollback on failure.
# Scope: Rebuilds library_index.json only; never edits song/artist/album evidence or identities.
# Related: library_health.py, music_library.py, library_cli.py.
