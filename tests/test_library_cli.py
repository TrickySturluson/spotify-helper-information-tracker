"""Regression tests for the native SHIT library command interface."""
import json

from scripts.music.library_cli import audit, build_parser, status


def test_library_cli_parses_safe_and_write_commands(tmp_path):
    parser = build_parser()
    assert parser.parse_args(["library", "status", "--root", str(tmp_path)]).action == "status"
    assert parser.parse_args(["library", "preview", "--root", str(tmp_path)]).action == "preview"
    migrate = parser.parse_args(["library", "migrate", "--yes", "--root", str(tmp_path)])
    assert migrate.action == "migrate"
    assert migrate.yes is True
    assert parser.parse_args(["library", "audit", "--root", str(tmp_path)]).action == "audit"
    prepare = parser.parse_args(["library", "prepare", "--execute", "--skip-discogs"])
    assert prepare.action == "prepare" and prepare.execute and prepare.skip_discogs
    assert parser.parse_args(["library", "sync"]).action == "sync"
    freshness = parser.parse_args(["library", "freshness", "--limit", "7", "--market", "US", "--include-unknown-age"])
    assert freshness.action == "freshness" and freshness.limit == 7 and freshness.market == "US" and freshness.include_unknown_age
    duration_preview = parser.parse_args(["library", "duration-evidence", "--json"])
    assert duration_preview.action == "duration-evidence" and duration_preview.json
    duration_apply = parser.parse_args(["library", "duration-evidence", "--apply", "--yes"])
    assert duration_apply.action == "duration-evidence" and duration_apply.apply and duration_apply.yes
    assert parser.parse_args(["migration", "status"]).action == "status"
    assert parser.parse_args(["migration", "run", "--yes"]).action == "run"
    assert parser.parse_args(["migration", "resume", "--yes"]).action == "resume"

# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Regression tests for the native SHIT library command interface.
# Scope: Safe command parsing, aliases, status reporting, and audit behavior.
# Run: python -m unittest tests.test_library_cli -v
# Related: scripts/music/library_cli.py and shit.py.
# -----------------------------------------------------------------------------


def test_library_cli_status_reports_empty_library(tmp_path, capsys):
    status(tmp_path)
    result = json.loads(capsys.readouterr().out)
    assert result["indexed_songs"] == 0
    assert result["indexed_artists"] == 0
    assert result["indexed_albums"] == 0


def test_library_cli_audit_accepts_empty_library(tmp_path, capsys):
    assert audit(tmp_path) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True
