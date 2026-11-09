"""Regression checks for the scheduled Spotify authentication health workflow."""

import ast
from pathlib import Path
import re
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "spotify-auth-health-check.yml"
WORKFLOW = WORKFLOW_PATH.read_text(encoding="utf-8")


def embedded_health_script():
    match = re.search(
        r"(?ms)^          python - <<'PY'\n(?P<script>.*?)^          PY$",
        WORKFLOW,
    )
    if not match:
        raise AssertionError("Could not locate the embedded auth-health Python script.")
    return textwrap.dedent(match.group("script"))


class SpotifyAuthHealthWorkflowTests(unittest.TestCase):
    def test_embedded_python_script_is_syntactically_valid(self):
        ast.parse(embedded_health_script())

    def test_workflow_is_scheduled_and_manually_recoverable(self):
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertIn('cron: "0 9 * * *"', WORKFLOW)
        self.assertIn('if [ "$EVENT_NAME" = "schedule" ]; then', WORKFLOW)
        self.assertIn('echo "skip=false" >> "$GITHUB_OUTPUT"', WORKFLOW)

    def test_schedule_uses_previous_run_status_and_fails_closed(self):
        self.assertIn("gh run list --workflow spotify-auth-health-check.yml", WORKFLOW)
        self.assertIn('gh run view "$previous_run"', WORKFLOW)
        self.assertIn("AUTH_HEALTH_STATUS=pending", WORKFLOW)
        self.assertIn("Scheduled checks are paused", WORKFLOW)
        self.assertIn("refusing to contact Spotify", WORKFLOW)

    def test_retry_after_deadline_is_preserved_and_honored(self):
        script = embedded_health_script()
        self.assertIn("def retry_state(header):", script)
        self.assertIn("parsedate_to_datetime", script)
        self.assertIn("rate_limited_until:", script)
        self.assertIn("AUTH_HEALTH_RETRY_AFTER=", script)
        self.assertIn('date +%s', WORKFLOW)

    def test_invalid_grant_is_a_manual_reauthorization_blocker(self):
        script = embedded_health_script()
        self.assertIn('report("reauthorization_required"', script)
        self.assertIn("The same credential will not be retried", script)
        self.assertIn("reauthorization_required", WORKFLOW)

    def test_provider_failures_are_distinct_and_redacted(self):
        script = embedded_health_script()
        for status in (
            "rate_limited",
            "provider_unavailable",
            "configuration_error",
            "scope_or_identity_error",
            "identity_error",
            "secret_persistence_failed",
            "provider_error",
            "healthy",
        ):
            self.assertIn(status, script)
        self.assertIn("exc.read(4096)", script)
        self.assertNotIn("print(token_body)", script)
        self.assertNotIn("print(me_body)", script)
        self.assertNotIn("error_description", script)

    def test_rotated_secret_is_persisted_only_after_account_verification(self):
        script = embedded_health_script()
        verify = script.index("if me_status != 200:")
        persist = script.index('rotated = token_data.get("refresh_token")')
        self.assertLess(verify, persist)
        self.assertIn('"SPOTIFY_REFRESH_TOKEN"', script)
        self.assertIn("::add-mask::", script)

    def test_workflow_token_permissions_remain_read_only_for_repository_data(self):
        permissions = WORKFLOW.split("permissions:", 1)[1].split("\n\n", 1)[0]
        self.assertIn("contents: read", permissions)
        self.assertIn("actions: read", permissions)
        self.assertNotIn("contents: write", permissions)
        self.assertNotIn("variables:", permissions)
        self.assertNotIn("issues: write", permissions)

    def test_health_check_has_no_playlist_or_library_write_path(self):
        workflow = WORKFLOW.lower()
        self.assertNotIn("api.spotify.com/v1/playlists", workflow)
        self.assertNotIn("playlist-modify", workflow)
        self.assertNotIn("assistant_data/", workflow)
        self.assertIn("never modifies playlists, library data, or repository contents", workflow)


if __name__ == "__main__":
    unittest.main()

# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Protect the Spotify auth-health workflow's schedule/latch behavior,
#          retry-after handling, status classification, token redaction, and
#          read-only playlist boundary.
# Inputs: Reads the maintained GitHub Actions YAML and extracts its embedded
#         Python refresh/verification script for syntax and contract checks.
# Outputs: Unit-test assertions only; no provider requests or repository writes.
# Safety: Does not load credentials, contact Spotify, or modify workflow state.
# -----------------------------------------------------------------------------
