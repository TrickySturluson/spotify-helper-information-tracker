#!/usr/bin/env python3
"""Plan/apply narrowly scoped, evidence-backed repairs to canonical song records."""
import argparse
import copy
import hashlib
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "assistant_data" / "music" / "library"
DEFAULT_MUSIC_ROOT = REPO_ROOT / "assistant_data" / "music"
sys.path.insert(0, str(REPO_ROOT))

from scripts.music.music_evidence import track_metadata_confidence


def _read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, f"{type(error).__name__}: {error}"


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".maintainer-tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def _spotify_snapshot_duration_source(record):
    context = record.get("listening_context")
    return (
        isinstance(context, dict)
        and context.get("source") == "Spotify reference-library snapshot"
        and bool(record.get("playlist_sources"))
    )


def plan_maintenance(root=DEFAULT_ROOT):
    """Read-only plan. Only propose provenance/confidence repairs with explicit evidence."""
    root = Path(root)
    actions = []
    errors = []
    counts = Counter()
    for path in sorted((root / "songs").rglob("song.json")):
        record, problem = _read(path)
        if problem or not isinstance(record, dict):
            errors.append({"path": str(path), "error": problem or "record is not an object"})
            continue
        counts["songs_scanned"] += 1
        evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
        metadata = evidence.get("track_metadata") if isinstance(evidence.get("track_metadata"), dict) else {}
        if metadata.get("duration_ms") is None and metadata.get("duration") is None:
            continue
        counts["songs_with_duration"] += 1
        duration_source = metadata.get("duration_source")
        proposed_source = None
        if not duration_source:
            counts["duration_source_missing"] += 1
            if _spotify_snapshot_duration_source(record):
                proposed_source = "spotify_reference_library_snapshot"
                actions.append({
                    "song_id": record.get("id"),
                    "path": str(path.relative_to(root)),
                    "action": "add_duration_provenance",
                    "duration_source": proposed_source,
                    "duration_provider": "spotify",
                    "reason": "Explicit Spotify reference-library snapshot context and playlist membership.",
                })
                counts["safe_spotify_provenance_repairs"] += 1
            else:
                counts["unresolved_duration_provenance"] += 1
        metadata_for_confidence = dict(metadata)
        if proposed_source:
            metadata_for_confidence["duration_source"] = proposed_source
            metadata_for_confidence["duration_provider"] = "spotify"
        recomputed = track_metadata_confidence(metadata_for_confidence).get("duration")
        confidence = record.get("confidence") if isinstance(record.get("confidence"), dict) else {}
        stored_metadata = confidence.get("metadata") if isinstance(confidence.get("metadata"), dict) else {}
        stored = stored_metadata.get("duration")
        if stored is None and recomputed is not None:
            actions.append({
                "song_id": record.get("id"),
                "path": str(path.relative_to(root)),
                "action": "fill_missing_duration_confidence",
                "value": recomputed,
                "reason": "Derived from existing duration evidence and its source family; no metadata value is changed.",
            })
            counts["missing_duration_confidence"] += 1
        elif stored is not None and recomputed is not None and stored != recomputed:
            counts["existing_duration_confidence_conflicts"] += 1

    by_song = Counter(action["song_id"] for action in actions)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "plan",
        "read_only": True,
        "ok": not errors,
        "counts": dict(counts),
        "action_count": len(actions),
        "multi_action_song_count": sum(1 for count in by_song.values() if count > 1),
        "action_examples": actions[:30],
        "errors": errors,
        "guardrails": [
            "Never change duration values or track identities.",
            "Only add Spotify duration provenance when the record explicitly names a Spotify reference-library snapshot and playlist membership.",
            "Only fill a missing duration confidence value; never overwrite an existing confidence value.",
            "Ambiguous or unsupported provenance remains unresolved.",
            "No provider requests or Spotify playlist writes.",
        ],
    }


def apply_maintenance(root=DEFAULT_ROOT, music_root=DEFAULT_MUSIC_ROOT):
    """Apply only safe planned repairs after backing up each affected song file."""
    root, music_root = Path(root), Path(music_root)
    plan = plan_maintenance(root)
    all_actions = []
    for path in sorted((root / "songs").rglob("song.json")):
        record, problem = _read(path)
        if problem or not isinstance(record, dict):
            continue
        evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
        metadata = evidence.get("track_metadata") if isinstance(evidence.get("track_metadata"), dict) else {}
        if metadata.get("duration_ms") is None and metadata.get("duration") is None:
            continue
        source_missing = not metadata.get("duration_source")
        proposed_source = "spotify_reference_library_snapshot" if source_missing and _spotify_snapshot_duration_source(record) else None
        meta_for_confidence = dict(metadata)
        if proposed_source:
            meta_for_confidence["duration_source"] = proposed_source
            meta_for_confidence["duration_provider"] = "spotify"
        recomputed = track_metadata_confidence(meta_for_confidence).get("duration")
        confidence = record.get("confidence") if isinstance(record.get("confidence"), dict) else {}
        stored_metadata = confidence.get("metadata") if isinstance(confidence.get("metadata"), dict) else {}
        actions = []
        if proposed_source:
            actions.append("add_duration_provenance")
        if stored_metadata.get("duration") is None and recomputed is not None:
            actions.append("fill_missing_duration_confidence")
        if actions:
            all_actions.append((path, actions, proposed_source))

    if not all_actions:
        return {
            "mode": "apply", "updated_records": 0, "actions_applied": 0,
            "backup_path": None, "journal_path": None,
            "remaining_plan": plan["counts"], "remaining_action_count": 0,
            "ok": plan["ok"], "errors": plan["errors"],
        }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    backup_root = root.with_name(root.name + ".backup-maintenance-" + timestamp)
    journal_path = music_root / "maintenance" / "repair_journal.jsonl"
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    updated_records = actions_applied = 0
    with journal_path.open("a", encoding="utf-8") as journal:
        for path, actions, proposed_source in all_actions:
            record, problem = _read(path)
            if problem or not isinstance(record, dict):
                continue
            before_hash = _hash(path)
            relative = path.relative_to(root)
            backup_path = backup_root / relative
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_path)

            evidence = record.setdefault("evidence", {})
            metadata = evidence.setdefault("track_metadata", {})
            confidence = record.setdefault("confidence", {})
            stored_metadata = confidence.setdefault("metadata", {})
            applied = []
            if "add_duration_provenance" in actions and not metadata.get("duration_source") and proposed_source:
                metadata["duration_source"] = proposed_source
                metadata["duration_provider"] = "spotify"
                applied.append("add_duration_provenance")
            if "fill_missing_duration_confidence" in actions and stored_metadata.get("duration") is None:
                current = track_metadata_confidence(metadata).get("duration")
                if current is not None:
                    stored_metadata["duration"] = current
                    applied.append("fill_missing_duration_confidence")
            if not applied:
                backup_path.unlink(missing_ok=True)
                continue

            _atomic_json(path, record)
            after_hash = _hash(path)
            row = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "song_id": record.get("id"),
                "record_path": str(relative),
                "actions": applied,
                "backup_path": str(backup_path),
                "before_sha256": before_hash,
                "after_sha256": after_hash,
            }
            journal.write(json.dumps(row, ensure_ascii=False) + "\n")
            journal.flush()
            updated_records += 1
            actions_applied += len(applied)

    remaining = plan_maintenance(root)
    return {
        "mode": "apply",
        "updated_records": updated_records,
        "actions_applied": actions_applied,
        "backup_path": str(backup_root),
        "journal_path": str(journal_path),
        "remaining_plan": remaining["counts"],
        "remaining_action_count": remaining["action_count"],
        "ok": remaining["ok"],
        "errors": remaining["errors"],
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--music-root", type=Path, default=DEFAULT_MUSIC_ROOT)
    parser.add_argument("--apply", action="store_true", help="apply safe repairs; default is plan-only")
    parser.add_argument("--yes", action="store_true", help="confirm writes when using --apply")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    if args.apply and not args.yes:
        parser.error("--apply also requires --yes.")
    report = apply_maintenance(args.root, args.music_root) if args.apply else plan_maintenance(args.root)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("SHIT Library maintainer")
        print(f"Mode: {report['mode']}")
        if report["mode"] == "plan":
            print(f"Songs scanned: {report['counts'].get('songs_scanned', 0):,}")
            print(f"Safe Spotify provenance repairs: {report['counts'].get('safe_spotify_provenance_repairs', 0):,}")
            print(f"Missing duration confidence: {report['counts'].get('missing_duration_confidence', 0):,}")
            print(f"Unresolved provenance: {report['counts'].get('unresolved_duration_provenance', 0):,}")
            print(f"Existing confidence conflicts (not changed): {report['counts'].get('existing_duration_confidence_conflicts', 0):,}")
        else:
            print(f"Updated records: {report['updated_records']:,}")
            print(f"Actions applied: {report['actions_applied']:,}")
            print(f"Backup: {report['backup_path']}")
            print(f"Journal: {report['journal_path']}")
    return 0 if report.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Safe, deterministic maintenance of derived duration provenance/confidence fields.
# Modes: Read-only plan by default; --apply --yes writes only explicit repairs.
# Safety: No provider calls, no identity/duration changes, no confidence overwrites; backs up changed song files.
# Audit: Every applied change is journaled with before/after SHA-256 and backup path.
# Related: scripts/music/music_evidence.py, scripts/music/library_confidence_audit.py, project/goals/library-health-maintenance/.
