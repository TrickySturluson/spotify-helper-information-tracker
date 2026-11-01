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
