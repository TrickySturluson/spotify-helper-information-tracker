"""Regression tests for canonical-library sync and the staged run plan."""
from scripts.music.prepare_music_library import SAFE_LIMITS, build_plan
from scripts.music.sync_music_library import lyric_rows


def test_lyric_rows_accepts_list_and_track_mapping():
    assert lyric_rows([{"artist": "A", "track": "T"}, None]) == [{"artist": "A", "track": "T"}]
    assert lyric_rows({"tracks": {"x": {"artist": "A", "track": "T"}}}) == [
        {"artist": "A", "track": "T"}
    ]


def test_enrichment_plan_migrates_first_then_runs_bounded_sources():
    plan = build_plan()
    labels = [row[0] for row in plan]
    assert labels[0] == "Refresh read-only Spotify playlist snapshots"\n    assert labels[1] == "Resolve exact MusicBrainz recording IDs"
    assert labels.index("Fill unresolved durations from MusicBrainz") < labels.index(
        "Enrich scrobbled track durations and rebuild catalogue"
    )
    assert labels[-1] == "Merge every enrichment export and validate the library"
    assert SAFE_LIMITS["ACOUSTICBRAINZ_MAX_BATCHES"] == "20"
    assert SAFE_LIMITS["MUSIC_PROFILE_LOOKUPS_PER_RUN"] == "100"
    assert SAFE_LIMITS["TRACK_PROFILE_LOOKUPS_PER_RUN"] == "200"
