#!/usr/bin/env python3
"""Read-only Tricky Daily quality report from explicitly observed feedback.

Last.fm scrobbles and Spotify playback-tracker sessions remain separate signals.
Unknown coverage is reported as unknown, never converted to zero engagement.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

DEFAULT_DATA = Path("assistant_data/spotify/daily_feedback.json")


def _rows(value):
    """Return only mapping-shaped rows from an optional evidence collection."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _count(value):
    """Parse a non-negative integer without letting malformed evidence abort a report."""
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def build_report(payload, candidates=None):
    if not isinstance(payload, dict) or not isinstance(payload.get("tracks"), dict):
        raise ValueError("Daily feedback must contain a tracks object.")
    tracks = payload["tracks"]
    liked_observed = liked_positive = 0
    post_add_like_observed = post_add_like_positive = 0
    playback_observed = playback_positive = playback_sessions = 0
    lastfm_observed = lastfm_scrobbles = 0
    removal_events = curator_rotations = explicit_removals = 0
    additions = 0

    for row in tracks.values():
        if not isinstance(row, dict):
            continue
        addition_rows = _rows(row.get("additions"))
        additions += len(addition_rows)
        liked_rows = _rows(row.get("liked_observations"))
        if liked_rows and isinstance(liked_rows[-1].get("liked"), bool):
            liked_observed += 1
            if liked_rows[-1]["liked"]:
                liked_positive += 1
        # A post-add save is only measurable when the latest addition recorded
        # an explicit not-liked baseline and a later liked observation exists.
        if addition_rows and liked_rows:
            latest_add = addition_rows[-1]
            latest_like = liked_rows[-1]
            if latest_add.get("liked_at_add") is False:
                try:
                    added_at = datetime.fromisoformat(str(latest_add["at"]).replace("Z", "+00:00"))
                    observed_at = datetime.fromisoformat(str(latest_like["at"]).replace("Z", "+00:00"))
                    if observed_at >= added_at and isinstance(latest_like.get("liked"), bool):
                        post_add_like_observed += 1
                        if latest_like["liked"]:
                            post_add_like_positive += 1
                except (KeyError, TypeError, ValueError):
                    pass

        playback_raw = row.get("playback_observations")
        playback_rows = _rows(playback_raw)
        if playback_rows:
            playback_observed += 1
            plays = sum(_count(item.get("plays")) for item in playback_rows)
            playback_sessions += plays
            if plays:
                playback_positive += 1

        if "lastfm_post_add_scrobbles" in row:
            lastfm_observed += 1
            lastfm_scrobbles += _count(row.get("lastfm_post_add_scrobbles"))

        for event in _rows(row.get("removal_events")):
            removal_events += 1
            if event.get("reason") == "curator_rotation":
                curator_rotations += 1
            else:
                explicit_removals += 1

    def rate(numerator, denominator):
        return round(numerator / denominator, 4) if denominator else None

    coverage = payload.get("coverage")
    if not isinstance(coverage, dict):
        coverage = {}
    mix_summary = {}
    daily_candidate_tracks = set()
    for candidate in candidates or []:
        if not isinstance(candidate, dict):
            continue
        uri = candidate.get("spotify_uri") or (
            "spotify:track:" + str(candidate.get("spotify_id"))
            if candidate.get("spotify_id") else None
        )
        for event in _rows(candidate.get("discovery_evidence")):
            context = event.get("context")
            if not isinstance(context, dict) or context.get("playlist_id") != "4yUVHSMQySfWeEowfIMcx7":
                continue
            recommendation = event.get("recommendation")
            if not isinstance(recommendation, dict):
                recommendation = {}
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
        "liked_after_add": {
            "observed_tracks": post_add_like_observed,
            "tracks_saved_after_add": post_add_like_positive,
            "save_rate_among_tracks_with_unliked_baseline": rate(
                post_add_like_positive, post_add_like_observed
            ),
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
