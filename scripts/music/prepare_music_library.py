#!/usr/bin/env python3
"""Prepare the canonical SHIT music library: migrate, enrich, merge, and audit.

Default mode is a read-only preflight. Pass --execute to perform provider lookups
and write the library. Every provider stage is bounded and checkpointed by its
existing implementation; rerunning resumes from cached state.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PYTHON = sys.executable

# Conservative one-run defaults. Existing script settings can be overridden
# explicitly in the caller's environment.
SAFE_LIMITS = {
    "MUSIC_METADATA_LOOKUPS_PER_RUN": "120",
    "MUSIC_PROFILE_LOOKUPS_PER_RUN": "100",
    "TRACK_PROFILE_LOOKUPS_PER_RUN": "200",
    "ALBUM_PROFILE_LOOKUPS_PER_RUN": "100",
    "MUSICBRAINZ_LOOKUPS_PER_RUN": "300",
    "MUSICBRAINZ_ID_LOOKUPS_PER_RUN": "200",
    "DISCOGS_LOOKUPS_PER_RUN": "30",
    "GETSONGBPM_LOOKUPS_PER_RUN": "100",
    "ACOUSTICBRAINZ_MAX_BATCHES": "20",
    "TRACK_PROFILE_RECENT_WINDOW_DAYS": "90",
    "TRACK_PROFILE_RECENT_TOP_N": "200",
    "TRACK_PROFILE_PRIORITY_PLAYLISTS": "4diIlnF8BlgoJrwUfejf49",
}


def command(*parts):
    return [PYTHON, *map(str, parts)]


def run(label, args, env=None):
    print(f"\n=== {label} ===", flush=True)
    merged = os.environ.copy()
    merged.update(env or {})
    completed = subprocess.run(args, cwd=ROOT, env=merged, check=False)
    if completed.returncode:
        raise SystemExit(f"{label} stopped with exit code {completed.returncode}; fix the issue and rerun (checkpoints are retained).")


def build_plan():
    # Resolve exact recording IDs before AcousticBrainz; run track/album/artist
    # lookups only after the offline migration has captured the full catalogue.
    return [
        ("Resolve exact MusicBrainz recording IDs", command("compat/enrich_musicbrainz_recording_ids.py"), {"MUSICBRAINZ_ID_LOOKUPS_PER_RUN": SAFE_LIMITS["MUSICBRAINZ_ID_LOOKUPS_PER_RUN"]}),
        ("Fill unresolved durations from MusicBrainz", command("compat/enrich_musicbrainz_durations.py"), {"MUSICBRAINZ_LOOKUPS_PER_RUN": SAFE_LIMITS["MUSICBRAINZ_LOOKUPS_PER_RUN"]}),
        ("Enrich scrobbled track durations and rebuild catalogue", command("compat/build_music_metadata.py"), {"LASTFM_API_KEY": os.environ.get("LASTFM_API_KEY", ""), "MUSIC_METADATA_LOOKUPS_PER_RUN": SAFE_LIMITS["MUSIC_METADATA_LOOKUPS_PER_RUN"]}),
        ("Build artist genre, mood, and theme profiles", command("compat/build_music_profiles.py"), {"LASTFM_API_KEY": os.environ.get("LASTFM_API_KEY", ""), "MUSIC_PROFILE_LOOKUPS_PER_RUN": SAFE_LIMITS["MUSIC_PROFILE_LOOKUPS_PER_RUN"]}),
        ("Enrich recording-level Last.fm and MusicBrainz tags", command("compat/build_track_profiles.py"), {"LASTFM_API_KEY": os.environ.get("LASTFM_API_KEY", ""), "TRACK_PROFILE_LOOKUPS_PER_RUN": SAFE_LIMITS["TRACK_PROFILE_LOOKUPS_PER_RUN"], "TRACK_PROFILE_RECENT_WINDOW_DAYS": SAFE_LIMITS["TRACK_PROFILE_RECENT_WINDOW_DAYS"], "TRACK_PROFILE_RECENT_TOP_N": SAFE_LIMITS["TRACK_PROFILE_RECENT_TOP_N"], "TRACK_PROFILE_PRIORITY_PLAYLISTS": SAFE_LIMITS["TRACK_PROFILE_PRIORITY_PLAYLISTS"]}),
        ("Enrich album tracklists, summaries, artwork, and release tags", command("compat/build_album_profiles.py"), {"LASTFM_API_KEY": os.environ.get("LASTFM_API_KEY", ""), "ALBUM_PROFILE_LOOKUPS_PER_RUN": SAFE_LIMITS["ALBUM_PROFILE_LOOKUPS_PER_RUN"], "TRACK_PROFILE_PRIORITY_PLAYLISTS": SAFE_LIMITS["TRACK_PROFILE_PRIORITY_PLAYLISTS"]}),
        ("Add optional exact-match Discogs release context", command("compat/enrich_discogs.py"), {"DISCOGS_LOOKUPS_PER_RUN": SAFE_LIMITS["DISCOGS_LOOKUPS_PER_RUN"]}),
        ("Enrich acoustic measurements from historical AcousticBrainz submissions", command("compat/enrich_acousticbrainz.py"), {"ACOUSTICBRAINZ_MAX_BATCHES": SAFE_LIMITS["ACOUSTICBRAINZ_MAX_BATCHES"]}),
        ("Add optional exact-match GetSongBPM fallback", command("compat/enrich_getsongbpm.py"), {"GETSONGBPM_LOOKUPS_PER_RUN": SAFE_LIMITS["GETSONGBPM_LOOKUPS_PER_RUN"]}),
        ("Rebuild final duration metadata and merge into canonical library", command("compat/build_music_metadata.py"), {"LASTFM_API_KEY": os.environ.get("LASTFM_API_KEY", ""), "MUSIC_METADATA_LOOKUPS_PER_RUN": "0"}),
        ("Merge every enrichment export and validate the library", command("scripts/music/sync_music_library.py"), {}),
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="perform migration and bounded provider enrichment; without this flag only preflight runs")
    parser.add_argument("--yes", action="store_true", help="skip the final confirmation (requires --execute)")
    parser.add_argument("--skip-discogs", action="store_true", help="skip optional Discogs lookups")
    parser.add_argument("--skip-getsongbpm", action="store_true", help="skip optional GetSongBPM lookups")
    args = parser.parse_args(argv)
    if args.yes and not args.execute:
        parser.error("--yes requires --execute")

    if not (ROOT / "data" / "scrobbles.json").exists():
        raise SystemExit("Missing data/scrobbles.json; run the normal archive import first.")
    if not (ROOT / "assistant_data" / "music" / "track_profiles.json").exists():
        raise SystemExit("Missing track_profiles.json; build the existing metadata exports before migrating.")

    if args.execute and not os.environ.get("LASTFM_API_KEY", "").strip():
        raise SystemExit("LASTFM_API_KEY is required for the Last.fm enrichment stages. No writes or provider requests were made.")

    print("SHIT canonical library run preflight")
    print(f"Repository: {ROOT}")
    print(f"Scrobble archive: {(ROOT / 'data' / 'scrobbles.json').stat().st_size:,} bytes")
    print(f"Mode: {'EXECUTE' if args.execute else 'READ-ONLY PREFLIGHT'}")
    print("Provider caps: " + ", ".join(f"{key}={value}" for key, value in SAFE_LIMITS.items()))
    print("Optional credentials: " + ", ".join(
        f"{name}={'present' if os.environ.get(name) else 'absent (stage will skip)'}"
        for name in ("DISCOGS_USER_TOKEN", "GETSONGBPM_API_KEY")
    ))

    run("Read-only migration preview", command("shit.py", "library", "preview"))
    if not args.execute:
        print("\nPreflight complete. No provider requests or library writes were made.")
        print("Tomorrow, run: python scripts/music/prepare_music_library.py --execute")
        return 0

    if not args.yes:
        answer = input("\nThis will back up and update the canonical library, then contact metadata providers within the caps above. Continue? [y/N] ").strip().casefold()
        if answer not in {"y", "yes"}:
            print("Cancelled. No migration or provider lookups were run.")
            return 1

    run("Back up and migrate the existing catalogue", command("shit.py", "library", "migrate", "--yes"))
    for label, args_list, env in build_plan():
        if args.skip_discogs and "Discogs" in label:
            print(f"Skipping {label} by request.")
            continue
        if args.skip_getsongbpm and "GetSongBPM" in label:
            print(f"Skipping {label} by request.")
            continue
        # Missing optional credentials cause their own enrichers to skip cleanly.
        run(label, args_list, env)
        if label not in {"Resolve exact MusicBrainz recording IDs"}:
            run("Incremental canonical-library sync", command("scripts/music/sync_music_library.py"))
    run("Final canonical-library integrity audit", command("shit.py", "library", "audit"))
    run("Final canonical-library status", command("shit.py", "library", "status"))
    print("\nSHIT library preparation complete. Provider checkpoints are retained for future continuation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: One controlled entry point for the offline migration followed by missing-data enrichment.
# Default: Read-only preflight and migration preview; no API calls or writes.
# Execute: python scripts/music/prepare_music_library.py --execute
# Safety: Bounded per-provider batches, checkpoint/resume through existing caches, one
#         provider process at a time, automatic migration backup, no Spotify playlist writes.
# Optional stages: Discogs and GetSongBPM run only when their credentials are configured.
# Identity: Exact/verified MusicBrainz matches only; unresolved recordings stay unresolved.
# Related: scripts/music/sync_music_library.py; scripts/music/migrate_full_music_library.py.
