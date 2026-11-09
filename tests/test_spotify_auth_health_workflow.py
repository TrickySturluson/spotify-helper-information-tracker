"""Regression checks for the broker-backed Spotify authentication health workflow."""

import ast
from pathlib import Path
import re
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github" / "workflows" / "spotify-auth-health-check.yml").read_text(encoding="utf-8")


def embedded_health_script():
    match = re.search(
        r"(?ms)^          python - <<'PY'\n(?P<script>.*?)^          PY$",
        WORKFLOW,
    )
    if not match:
        raise AssertionError("Could not locate the embedded broker health-check script.")
    return textwrap.dedent(match.group("script"))


class SpotifyAuthHealthWorkflowTests(unittest.TestCase):
    def test_embedded_python_script_is_syntactically_valid(self):
        ast.parse(embedded_health_script())

    def test_workflow_is_scheduled_and_manually_recoverable(self):
        self.assertIn("workflow_dispatch:", WORKFLOW)
        self.assertIn("SPOTIFY_AUTH_STATE_REF: auth-state-anchor", WORKFLOW)
        self.assertIn("if: github.ref == 'refs/heads/main'", WORKFLOW)
        self.assertIn('cron: "0 9 * * *"', WORKFLOW)
        self.assertIn('if [ "$EVENT_NAME" = "schedule" ]; then', WORKFLOW)
        self.assertIn('echo "skip=false" >> "$GITHUB_OUTPUT"', WORKFLOW)

    def test_oidc_is_the_only_authentication_path(self):
        permissions = WORKFLOW.split("permissions:", 1)[1].split("\n\n", 1)[0]
        self.assertIn("id-token: write", permissions)
        self.assertIn("contents: read", permissions)
        self.assertIn("statuses: write", permissions)
        self.assertIn("scripts.spotify.broker_access_token", WORKFLOW)
        self.assertIn("SHIT_AUTH_BROKER_URL: ${{ vars.BROKER_BASE_URL }}", WORKFLOW)
        self.assertNotIn("secrets.SPOTIFY_REFRESH_TOKEN", WORKFLOW)
        self.assertNotIn("SPOTIFY_CLIENT_SECRET", WORKFLOW)
        self.assertNotIn("accounts.spotify.com/api/token", WORKFLOW)
        self.assertNotIn("gh secret set", WORKFLOW)

    def test_schedule_latch_and_retry_after_are_preserved(self):
        self.assertIn('gh api "repos/$GITHUB_REPOSITORY/commits/$AUTH_STATE_SHA/status"', WORKFLOW)
        self.assertIn("context=spotify-auth-health", WORKFLOW)
        self.assertIn("state=pending", WORKFLOW)
        self.assertIn("Scheduled checks are paused", WORKFLOW)
        self.assertIn("refusing to contact Spotify", WORKFLOW)
        self.assertIn("def retry_state(header):", WORKFLOW)
        self.assertIn("parsedate_to_datetime", WORKFLOW)
        self.assertIn("rate_limited_until:", WORKFLOW)
        self.assertIn("86400", WORKFLOW)
        self.assertIn("retry_state(exc.retry_after)", WORKFLOW)

    def test_health_check_is_read_only_and_has_no_legacy_fallback(self):
        workflow = WORKFLOW.lower()
        self.assertNotIn("api.spotify.com/v1/playlists", workflow)
        self.assertNotIn("playlist-modify", workflow)
        self.assertNotIn("assistant_data/", workflow)
        self.assertIn("never modifies playlists, library data, or repository contents", workflow)
        self.assertNotIn("legacy refresh-token fallback", workflow)


if __name__ == "__main__":
    unittest.main()

# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Protect the broker-backed Spotify auth-health workflow's OIDC-only
#          access, commit-status latch, Retry-After handling, and read-only boundary.
# Inputs: Reads the maintained GitHub Actions YAML and checks credential boundaries.
# Outputs: Unit-test assertions only; no provider requests or repository writes.
# Safety: Does not load credentials, contact Spotify, or modify workflow state.
# -----------------------------------------------------------------------------
