"""Guard SHIT's repository-level documentation and fresh-session navigation."""
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
CONTROL_DOCS = (
    "AGENTS.md",
    "docs/README.md",
    "docs/BABEL.md",
    "project/ROADMAP.md",
    "project/goals/README.md",
)


class DocumentationContractTests(unittest.TestCase):
    def test_repository_control_documents_exist(self):
        required = (
            "AGENTS.md",
            "docs/README.md",
            "docs/BABEL.md",
            "docs/REPOSITORY_FILE_INDEX.md",
            "project/DOCUMENTATION_RULES.md",
            "project/ROADMAP.md",
            "project/NEXT_WORK.md",
            "project/LOOSE_ENDS.md",
            "project/PROJECT_LOG.md",
            "compat/README.md",
            "tests/README.md",
            "data/README.md",
            "assistant_data/README.md",
            "playback_data/README.md",
            ".github/README.md",
            "scripts/README.md",
            "project/README.md",
            "docs/WORKFLOWS.md",
        )
        for relative in required:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_every_goal_has_roadmap_readme_and_action_log(self):
        goals_root = ROOT / "project" / "goals"
        goals = sorted(path for path in goals_root.iterdir() if path.is_dir())
        self.assertTrue(goals, "No goal workspaces were found")
        for goal in goals:
            for required in ("ROADMAP.md", "README.md", "ACTIONS.md"):
                with self.subTest(goal=goal.name, required=required):
                    self.assertTrue((goal / required).is_file())

    def test_every_github_actions_workflow_is_in_the_catalogue(self):
        catalogue = (ROOT / "docs" / "WORKFLOWS.md").read_text(encoding="utf-8")
        workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        self.assertTrue(workflows, "No GitHub Actions workflows were found")
        for workflow in workflows:
            with self.subTest(workflow=workflow.name):
                self.assertIn(workflow.name, catalogue)

    def test_great_migration_issue_operations_match_workflow_and_guide(self):
        workflow = (ROOT / ".github" / "workflows" / "great-migration.yml").read_text(encoding="utf-8")
        guide = (ROOT / "docs" / "GREAT_MIGRATION.md").read_text(encoding="utf-8")
        allowed_match = re.search(r"allowed\s*=\s*\{([^}]+)\}", workflow)
        self.assertIsNotNone(allowed_match, "Could not locate Great Migration operation allowlist")
        allowed = set(re.findall(r'"([a-z][a-z0-9-]*)"', allowed_match.group(1)))

        dispatch_match = re.search(
            r"workflow_dispatch:\s*(.*?)\npermissions:",
            workflow,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(dispatch_match, "Could not locate manual dispatch options")
        options_match = re.search(
            r"options:\s*((?:\s+-\s+[a-z][a-z0-9-]*\s*\n)+)",
            dispatch_match.group(1),
        )
        self.assertIsNotNone(options_match, "Could not locate manual dispatch command choices")
        dispatch_options = set(re.findall(r"^\s+-\s+([a-z][a-z0-9-]*)\s*$", options_match.group(1), re.MULTILINE))

        self.assertEqual(allowed, dispatch_options, "Issue allowlist and manual dispatch choices must stay aligned")
        for operation in sorted(allowed):
            with self.subTest(operation=operation):
                self.assertIn(f"`[SHIT LIBRARY] {operation}`", guide)

    def test_reference_library_schedule_matches_guide(self):
        workflow = (ROOT / ".github" / "workflows" / "spotify-reference-library.yml").read_text(encoding="utf-8")
        guide = (ROOT / "docs" / "RECENT_TRACK_ENRICHMENT.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn('cron: "13 6 * * *"', workflow)
        self.assertIn("scheduled daily at 06:13 UTC", guide)
        self.assertNotIn("scheduled every six hours", guide)
        self.assertIn("daily at 06:13 UTC", readme)
        self.assertNotIn("every six hours (UTC)", readme)

    def test_metadata_enrichment_budgets_match_workflow_and_guides(self):
        workflow = (ROOT / ".github" / "workflows" / "enrich-music-metadata.yml").read_text(encoding="utf-8")
        recent_guide = (ROOT / "docs" / "RECENT_TRACK_ENRICHMENT.md").read_text(encoding="utf-8")
        metadata_guide = (ROOT / "docs" / "AUTOMATED_AUDIO_METADATA.md").read_text(encoding="utf-8")

        dispatch_match = re.search(
            r"workflow_dispatch:\s*(.*?)\npermissions:",
            workflow,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(dispatch_match, "Could not locate metadata workflow dispatch inputs")

        def input_block(name):
            match = re.search(
                rf"^      {name}:\n(.*?)(?=^      [a-z_]+:|\Z)",
                dispatch_match.group(1),
                flags=re.MULTILINE | re.DOTALL,
            )
            self.assertIsNotNone(match, f"Missing workflow input: {name}")
            return match.group(1)

        def choices_and_default(name):
            block = input_block(name)
            choices = re.findall(r'^\s+-\s+"?([0-9]+)"?\s*$', block, re.MULTILINE)
            default = re.search(r'^\s+default:\s+"?([0-9]+)"?\s*$', block, re.MULTILINE)
            self.assertIsNotNone(default, f"Missing default for {name}")
            return choices, default.group(1)

        def display_choices(values):
            return "/".join(f"{int(value):,}" for value in values)

        duration_choices, duration_default = choices_and_default("musicbrainz_lookups")
        artist_choices, artist_default = choices_and_default("artist_profile_lookups")
        track_choices, track_default = choices_and_default("track_profile_lookups")

        self.assertIn("MUSICBRAINZ_LOOKUPS_PER_RUN:", workflow)
        self.assertIn("|| '300'", workflow)
        self.assertIn("MUSIC_PROFILE_LOOKUPS_PER_RUN:", workflow)
        self.assertIn("|| '100'", workflow)
        self.assertIn('MUSICBRAINZ_ID_LOOKUPS_PER_RUN: "200"', workflow)
        self.assertIn("TRACK_PROFILE_LOOKUPS_PER_RUN:", workflow)
        self.assertIn("|| '200'", workflow)
        self.assertIn('ALBUM_PROFILE_LOOKUPS_PER_RUN: "100"', workflow)

        self.assertIn(f"MusicBrainz durations {display_choices(duration_choices)} (default {int(duration_default):,})", metadata_guide)
        self.assertIn(f"artist profiles {display_choices(artist_choices)} (default {int(artist_default):,})", metadata_guide)
        self.assertIn(f"track profiles {display_choices(track_choices)} (default {int(track_default):,})", metadata_guide)
        self.assertIn("300 MusicBrainz duration lookups, 100 artist-profile lookups, 200 track-profile lookups, 200 recording-ID lookups and 100 album-profile lookups", metadata_guide)
        self.assertIn("scheduled workflow processes up to 200 track profiles per run", recent_guide)
        self.assertIn(f"Manual dispatch offers {', '.join(track_choices[:-1])}, or {track_choices[-1]} lookups (default {track_default})", recent_guide)

    def test_documentation_index_lists_every_technical_guide(self):
        docs_root = ROOT / "docs"
        index = (docs_root / "README.md").read_text(encoding="utf-8")
        guides = sorted(
            path for path in docs_root.glob("*.md")
            if path.name != "README.md"
        )
        self.assertTrue(guides, "No technical guides were found")
        for guide in guides:
            with self.subTest(guide=guide.name):
                self.assertIn(f"]({guide.name})", index)

    def test_all_markdown_local_links_resolve(self):
        ignored = {".git", ".venv", "venv", "node_modules"}
        documents = sorted(
            path for path in ROOT.rglob("*.md")
            if not any(part in ignored for part in path.parts)
        )
        self.assertTrue(documents, "No Markdown documentation was found")
        for document in documents:
            source = document.read_text(encoding="utf-8")
            targets = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", source)
            for raw_target in targets:
                target = raw_target.strip().split()[0].strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                local_path = (
                    ROOT / unquote(parsed.path)
                    if target.startswith("/")
                    else document.parent / unquote(parsed.path)
                )
                with self.subTest(document=document.relative_to(ROOT), target=target):
                    self.assertTrue(local_path.exists(), f"Broken local documentation link: {target}")

    def test_workflow_overviews_are_specific_not_generic_boilerplate(self):
        workflow_root = ROOT / ".github" / "workflows"
        generic_phrases = (
            "See the on: section above",
            "Automates the job steps declared in this workflow",
            "Keep paths, secrets, permissions, and Python versions synchronized",
        )
        workflows = sorted(workflow_root.glob("*.yml"))
        self.assertTrue(workflows, "No GitHub Actions workflows were found")
        for workflow in workflows:
            source = workflow.read_text(encoding="utf-8")
            marker = source.rfind("FILE OVERVIEW")
            self.assertGreaterEqual(marker, 0, f"{workflow.name} has no FILE OVERVIEW")
            overview = source[marker:]
            for phrase in generic_phrases:
                with self.subTest(workflow=workflow.name, phrase=phrase):
                    self.assertNotIn(phrase, overview)

    def test_workflow_catalogue_preserves_sensitive_trigger_boundaries(self):
        catalogue = (ROOT / "docs" / "WORKFLOWS.md").read_text(encoding="utf-8")
        expected = (
            "Push to main on matching enrichment paths",
            "Push to `spotify-playlist-manager` branch on matching paths",
            "Push to main on matching test-trigger/preflight paths",
            "Push on the live-cycle test-trigger path (any branch)",
            "Push on the safe-test trigger path (any branch)",
            "Push to main when this workflow file changes",
        )
        for phrase in expected:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, catalogue)

    def test_paused_goal_roadmaps_separate_documentation_and_feature_next_actions(self):
        paused_goals = (
            "great-migration",
            "library-enrichment",
            "metadata-coverage-retries",
            "discovery-recommendations",
            "listening-analytics",
            "playlist-intelligence",
            "tricky-daily",
            "playlist-sequencing",
            "library-health-maintenance",
            "metadata-freshness",
            "spotify-playability",
            "library-confidence-verification",
        )
        required_instruction = (
            "Do not run provider checks/enrichment, alter generated data, "
            "modify playlists, or implement features while the documentation-only priority is active."
        )
        for goal in paused_goals:
            with self.subTest(goal=goal):
                roadmap = (ROOT / "project" / "goals" / goal / "ROADMAP.md").read_text(encoding="utf-8")
                self.assertIn("## Next action (documentation-only priority)", roadmap)
                self.assertIn("## Next feature action after documentation pause", roadmap)
                self.assertIn(required_instruction, roadmap)

    def test_daily_force_idempotency_gap_is_documented(self):
        workflow_catalogue = (ROOT / "docs" / "WORKFLOWS.md").read_text(encoding="utf-8")
        cycle_guide = (ROOT / "docs" / "TRICKY_DAILY_CYCLE.md").read_text(encoding="utf-8")
        todo = (ROOT / "docs" / "TRICKY_DAILY_TODO.md").read_text(encoding="utf-8")
        roadmap = (ROOT / "project" / "goals" / "tricky-daily" / "ROADMAP.md").read_text(encoding="utf-8")
        schedule_test = (ROOT / "tests" / "test_spotify_daily_cycle_schedule.py").read_text(encoding="utf-8")
        cycle_source = (ROOT / "scripts" / "spotify" / "spotify_daily_cycle.py").read_text(encoding="utf-8")
        cycle_workflow = (ROOT / ".github" / "workflows" / "spotify-daily-midnight-cycle.yml").read_text(encoding="utf-8")

        self.assertIn("same-Eastern-date completion guard", workflow_catalogue)
        self.assertIn("Current `--force` bypasses both the clock gate and same-Eastern-date completion guard", workflow_catalogue)
        self.assertNotIn("Force bypasses the clock gate only", workflow_catalogue)
        self.assertIn("currently bypasses", cycle_guide)
        self.assertIn("Known P0 discrepancy", todo)
        self.assertIn("Current source discrepancy", roadmap)
        self.assertIn("Known P0 discrepancy: current --force", cycle_source)
        self.assertIn("also bypasses that completion guard", cycle_source)
        self.assertIn("intended behavior is to bypass the clock gate only", cycle_source)
        self.assertIn("exactly 60 valid unique track URIs", cycle_workflow)
        self.assertIn("current --force bypasses both the clock gate and same-date completion guard", cycle_workflow)
        self.assertIn("cycle_already_completed(config, \"2026-11-05\", force=True)", schedule_test)

    def test_completed_committed_tree_inventory_is_not_a_current_blocker(self):
        index = (ROOT / "docs" / "REPOSITORY_FILE_INDEX.md").read_text(encoding="utf-8")
        roadmap = (ROOT / "project" / "goals" / "maintainability-documentation" / "ROADMAP.md").read_text(encoding="utf-8")
        handoff = (ROOT / "project" / "NEXT_WORK.md").read_text(encoding="utf-8")

        self.assertIn("28,241", index)
        self.assertIn("27,981", index)
        self.assertIn("truncated=false", index)
        self.assertIn("This snapshot satisfies the committed-tree inventory requirement", roadmap)
        next_action = roadmap.split("## Next action", 1)[1].split("## Related records", 1)[0].lower()
        self.assertNotIn("complete the tracked-file inventory", next_action)
        self.assertIn("Complete committed-tree inventory: verified", handoff)

    def test_reference_library_snapshot_evidence_is_not_misrepresented_as_listening(self):
        source = (ROOT / "scripts" / "spotify" / "spotify_reference_library.py").read_text(encoding="utf-8")
        library_guide = (ROOT / "docs" / "PER_RECORDING_MUSIC_LIBRARY.md").read_text(encoding="utf-8")
        operations_guide = (ROOT / "docs" / "SPOTIFY_API_OPERATIONS.md").read_text(encoding="utf-8")
        workflow_catalogue = (ROOT / "docs" / "WORKFLOWS.md").read_text(encoding="utf-8")

        self.assertIn("canonical MusicLibrary", source)
        self.assertIn("not a Last.fm scrobble", source)
        self.assertIn("does **not** prove the user played, liked, saved, or listened to it", library_guide)
        self.assertIn("not Spotify playback, likes, saves, or Last.fm scrobbles", operations_guide)
        self.assertIn("canonical MusicLibrary identity/playlist-source context", workflow_catalogue)

    def test_library_resolver_index_rebuild_write_boundary_is_documented(self):
        source = (ROOT / "scripts" / "music" / "music_library.py").read_text(encoding="utf-8")
        guide = (ROOT / "docs" / "PER_RECORDING_MUSIC_LIBRARY.md").read_text(encoding="utf-8")
        health = (ROOT / "scripts" / "music" / "library_health.py").read_text(encoding="utf-8")
        sequencer = (ROOT / "scripts" / "spotify" / "spotify_playlist_sequencer.py").read_text(encoding="utf-8")
        transition_guide = (ROOT / "docs" / "TRANSITION_SCORING.md").read_text(encoding="utf-8")
        migration_guide = (ROOT / "docs" / "GREAT_MIGRATION.md").read_text(encoding="utf-8")
        legacy_migrator = (ROOT / "scripts" / "music" / "migrate_music_library.py").read_text(encoding="utf-8")
        full_migrator = (ROOT / "scripts" / "music" / "migrate_full_music_library.py").read_text(encoding="utf-8")
        migration_workflow = (ROOT / ".github" / "workflows" / "great-migration.yml").read_text(encoding="utf-8")
        credential_verifier = (ROOT / "scripts" / "music" / "verify_provider_credentials.py").read_text(encoding="utf-8")

        self.assertIn("Constructor may rebuild and write library_index.json", source)
        self.assertIn("strictly read-only structural check", guide)
        self.assertIn("never instantiates the lazy resolver", health.lower())
        self.assertIn("may rebuild/write library_index.json", sequencer)
        self.assertIn("Do not equate “no Spotify playlist writes” with “no local repository/file writes.”", transition_guide)
        self.assertIn("Resolver/index diagnostics: `audit` and `verify-catalogue`", migration_guide)
        self.assertIn("Use `health` when zero repository writes are required", migration_guide)
        self.assertIn("legacy run/resume and --recent-limit writes do not create their own backup", legacy_migrator)
        self.assertIn("timestamped sibling backup", full_migrator)
        self.assertIn("audit/verify-catalogue instantiate MusicLibrary", migration_workflow)
        self.assertIn("may rebuild library_index.json", migration_workflow)
        self.assertIn("health is the strictly read-only structural scan", migration_workflow)
        self.assertIn("verify may persist a rotated Spotify refresh token as an Actions", migration_workflow)
        self.assertIn("Verify provider credentials (may persist rotated refresh token)", migration_workflow)
        self.assertNotIn("Verify provider credentials (read-only)", migration_workflow)
        self.assertIn("SHIT_PERSIST_ROTATED_SPOTIFY_TOKEN=1", credential_verifier)
        self.assertIn("replacement Spotify refresh token may be", credential_verifier)

    def test_great_migration_previews_are_zero_write(self):
        guide = (ROOT / "docs" / "GREAT_MIGRATION.md").read_text(encoding="utf-8")
        workflow_catalogue = (ROOT / "docs" / "WORKFLOWS.md").read_text(encoding="utf-8")
        prepare_source = (ROOT / "scripts" / "music" / "prepare_music_library.py").read_text(encoding="utf-8")
        cli_source = (ROOT / "scripts" / "music" / "library_cli.py").read_text(encoding="utf-8")
        full_migrator = (ROOT / "scripts" / "music" / "migrate_full_music_library.py").read_text(encoding="utf-8")

        self.assertIn("`preview` inventories the source catalogue", guide)
        self.assertIn("`prepare-preview`", guide)
        self.assertIn("Strictly read-only Library/report operations", guide)
        self.assertIn("prepare-preview", workflow_catalogue)
        self.assertIn('command("shit.py", "library", "preview")', prepare_source)
        self.assertIn("run_migration(args.root, dry_run=True)", cli_source)

        dry_run = full_migrator.split("if args.dry_run:", 1)[1].split("backup_path = None", 1)[0]
        self.assertIn('"writes": 0', dry_run)
        self.assertNotIn("MusicLibrary(", dry_run)
        self.assertNotIn("put_catalogue", dry_run)

    def test_track_profile_builder_preserves_playlist_only_evidence_semantics(self):
        source = (ROOT / "scripts" / "music" / "build_track_profiles.py").read_text(encoding="utf-8")
        enrichment_guide = (ROOT / "docs" / "RECENT_TRACK_ENRICHMENT.md").read_text(encoding="utf-8")
        workflow_catalogue = (ROOT / "docs" / "WORKFLOWS.md").read_text(encoding="utf-8")
        library_readme = (ROOT / "assistant_data" / "music" / "library" / "README.md").read_text(encoding="utf-8")

        self.assertIn("MusicLibrary().put_catalogue(library_rows)", source)
        self.assertIn("priority_playlist_ids", source)
        self.assertIn("playlist membership is source/context evidence, not a play", enrichment_guide.lower())
        self.assertIn("playlist-only candidates are not scrobbles", workflow_catalogue)
        self.assertIn("even when they have zero scrobbles", library_readme)

    def test_agent_entry_point_requires_documentation_rules(self):
        source = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("DOCUMENTATION_RULES.md", source)
        self.assertIn("NEXT_WORK.md", source)
        self.assertIn("LOOSE_ENDS.md", source)
        self.assertIn("same session", source.lower())

    def test_documentation_system_identity_is_explicit(self):
        guide = (ROOT / "docs" / "BABEL.md").read_text(encoding="utf-8")
        self.assertIn("SHIT Documentation & Continuity", guide)
        self.assertIn("Internal codename: Babel", guide)
        for relative in (
            "README.md",
            "AGENTS.md",
            "docs/README.md",
            "project/DOCUMENTATION_RULES.md",
            "project/NEXT_WORK.md",
            "project/ROADMAP.md",
            "project/goals/maintainability-documentation/README.md",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(document=relative):
                self.assertIn("SHIT Documentation & Continuity", source)
                self.assertIn("Babel", source)

    def test_documentation_index_covers_major_repository_domains(self):
        source = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        for domain in ("project/", "scripts/", ".github/", "data/", "assistant_data/", "playback_data/"):
            with self.subTest(domain=domain):
                self.assertIn(domain, source)

    def test_control_document_local_links_resolve(self):
        for relative in CONTROL_DOCS:
            document = ROOT / relative
            source = document.read_text(encoding="utf-8")
            targets = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", source)
            for raw_target in targets:
                target = raw_target.strip().split()[0].strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                local_path = ROOT / unquote(parsed.path) if target.startswith("/") else document.parent / unquote(parsed.path)
                with self.subTest(document=relative, target=target):
                    self.assertTrue(local_path.exists(), f"Broken local documentation link: {target}")


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Prevent regressions in SHIT's repository-wide documentation contract.
# Scope: Required control documents, per-goal roadmaps, workflow operation allowlists,
#        enrichment budgets, inventory handoff consistency, Daily force/idempotency alignment, Spotify snapshot/listening-evidence boundaries and MusicLibrary index-rebuild write safety.
# Run: python -m unittest tests.test_documentation_contract -v
# Related: AGENTS.md, docs/README.md, project/DOCUMENTATION_RULES.md,
#          project/ROADMAP.md, and project/goals/*.
# -----------------------------------------------------------------------------
