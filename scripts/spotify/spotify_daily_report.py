#!/usr/bin/env python3
"""Read-only Tricky Daily quality report from explicitly observed feedback.

Last.fm scrobbles and Spotify playback-tracker sessions remain separate signals.
Unknown coverage is reported as unknown, never converted to zero engagement.
"""
import argparse
import json
from pathlib import Path

DEFAULT_DATA = Path("assistant_data/spotify/daily_feedback.json")


def build_report(payload, candidates=None):
    if not isinstance(payload, dict) or not isinstance(payload.get("tracks"), dict):
        raise ValueError("Daily feedback must contain a tracks object.")
    tracks = payload["tracks"]
    liked_observed = liked_positive = 0
    playback_observed = playback_positive = playback_sessions = 0
    lastfm_observed = lastfm_scrobbles = 0
    removal_events = curator_rotations = explicit_removals = 0
    additions = 0

    for row in tracks.values():
        if not isinstance(row, dict):
            continue
        additions += len(row.get("additions") or [])
        liked_rows = row.get("liked_observations") or []
        if liked_rows:
            liked_observed += 1
            if liked_rows[-1].get("liked") is True:
                liked_positive += 1

        playback_rows = row.get("playback_observations") or []
        if playback_rows:
            playback_observed += 1
            plays = sum(max(0, int(item.get("plays") or 0)) for item in playback_rows)
            playback_sessions += plays
            if plays:
                playback_positive += 1

        if "lastfm_post_add_scrobbles" in row:
            lastfm_observed += 1
            lastfm_scrobbles += max(0, int(row.get("lastfm_post_add_scrobbles") or 0))

        for event in row.get("removal_events") or []:
            removal_events += 1
            if event.get("reason") == "curator_rotation":
                curator_rotations += 1
            else:
                explicit_removals += 1

    def rate(numerator, denominator):
        return round(numerator / denominator, 4) if denominator else None

    coverage = payload.get("coverage") or {}
    mix_summary = {}
    daily_candidate_tracks = set()
    for candidate in candidates or []:
        if not isinstance(candidate, dict):
            continue
        uri = candidate.get("spotify_uri") or (
            "spotify:track:" + str(candidate.get("spotify_id"))
            if candidate.get("spotify_id") else None
        )
        for event in candidate.get("discovery_evidence") or []:
            context = event.get("context") or {}
            if context.get("playlist_id") != "4yUVHSMQySfWeEowfIMcx7":
                continue
            recommendation = event.get("recommendation") or {}
            tier = recommendation.get("daily_mix_bucket") or recommendation.get("tier") or "unclassified"
            summary = mix_summary.setdefault(tier, {"surfaced_events": 0, "unique_tracks": set(), "tracks_with_feedback": set()})
            summary["surfaced_events"] += 1
            if uri:
                summary["unique_tracks"].add(uri)
                if uri in tracks:
                    summary["tracks_with_feedback"].add(uri)
                daily_candidate_tracks.add(uri)
    mix_summary = {
        tier: {
            "surfaced_events": values["surfaced_events"],
            "unique_tracks": len(values["unique_tracks"]),
            "tracks_with_feedback": len(values["tracks_with_feedback"]),
        }
        for tier, values in sorted(mix_summary.items())
    }
    return {
        "playlist_id": "4yUVHSMQySfWeEowfIMcx7",
        "track_count": len(tracks),
        "addition_events": additions,
        "discovery_mix": {
            "surfaced_tracks": len(daily_candidate_tracks),
            "by_tier": mix_summary,
            "source": "Daily-scoped discovery evidence with stored recommendation metadata",
        },
        "liked": {
            "observed_tracks": liked_observed,
            "currently_liked_tracks": liked_positive,
            "positive_rate_among_observed": rate(liked_positive, liked_observed),
            "coverage": coverage.get("liked_songs", "unknown"),
        },
        "spotify_playback_tracker": {
            "observed_tracks": playback_observed,
            "tracks_with_plays": playback_positive,
            "total_sessions": playback_sessions,
            "positive_rate_among_observed": rate(playback_positive, playback_observed),
            "coverage": coverage.get("playback_tracker", "unknown"),
            "coverage_detail": coverage.get("playback_tracker_detail"),
        },
        "lastfm_scrobbles": {
            "observed_tracks": lastfm_observed,
            "post_add_scrobbles": lastfm_scrobbles,
            "coverage": coverage.get("lastfm", "unknown"),
        },
        "removals": {
            "total_events": removal_events,
            "neutral_curator_rotations": curator_rotations,
            "other_removals": explicit_removals,
        },
        "interpretation": {
            "liked_rate_denominator": "tracks with an observed liked status only",
            "playback_rate_denominator": "tracks with playback observations only",
            "missing_observations": "unknown, not zero",
            "listening_sources": "Last.fm scrobbles and Spotify playback tracker are reported separately",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--candidates", type=Path,
        default=Path("assistant_data/recommendations/discovery_candidates.json"),
    )
    args = parser.parse_args()
    if not args.input.is_file():
        payload = {"version": 1, "tracks": {}, "coverage": {}}
    else:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    candidates = []
    if args.candidates.is_file():
        candidate_payload = json.loads(args.candidates.read_text(encoding="utf-8"))
        candidates = candidate_payload.get("tracks", []) if isinstance(candidate_payload, dict) else candidate_payload
    report = build_report(payload, candidates)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Read-only quality and feedback coverage report for Tricky Daily.
# Inputs: assistant_data/spotify/daily_feedback.json.
# Evidence: Likes, Spotify playback sessions, and Last.fm scrobbles are kept separate.
# Safety: Never calls Spotify or modifies playlists, feedback, or manager state.
# Run: python scripts/spotify/spotify_daily_report.py [--input PATH] [--output PATH].
# -----------------------------------------------------------------------------
