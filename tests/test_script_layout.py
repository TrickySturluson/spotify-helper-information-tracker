"""Guard the responsibility-based implementation and compatibility layout."""
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    "analytics": (
        "audit_project.py", "build_advanced_analytics.py", "build_assistant_data.py",
        "build_listening_time_summary.py", "build_music_analytics.py",
        "build_playback_analytics.py", "build_stats.py",
    ),
    "music": (
        "audio_analysis.py", "build_music_metadata.py", "build_music_profiles.py",
        "build_track_profiles.py", "enrich_acousticbrainz.py", "enrich_discogs.py", "enrich_getsongbpm.py",
        "enrich_musicbrainz_durations.py", "enrich_musicbrainz_recording_ids.py",
        "enrich_recommendation_lyrics.py", "lyrics_library.py", "mood_inference.py",
    ),
    "spotify": (
        "playlist_intelligence.py", "playlist_metadata.py", "spotify_daily_feedback.py",
        "spotify_daily_playlist.py", "spotify_discovery.py", "spotify_playback_tracker.py",
        "spotify_playlist_cloud.py", "spotify_playlist_manager.py",
        "spotify_playlist_sequencer.py", "spotify_reference_library.py",
        "track_playlist_removals.py",
    ),
    "lastfm": ("update_lastfm.py",),
}


class ScriptLayoutTests(unittest.TestCase):
    def test_every_implementation_has_a_compatibility_entry_point(self):
        for group, filenames in GROUPS.items():
            for filename in filenames:
                with self.subTest(group=group, filename=filename):
                    implementation = ROOT / "scripts" / group / filename
                    shim = ROOT / "compat" / filename
                    self.assertTrue(implementation.is_file())
                    self.assertTrue(shim.is_file())
                    source = shim.read_text(encoding="utf-8")
                    self.assertIn(f'"scripts" / "{group}" / "{filename}"', source)
                    self.assertIn("__file__ = str(_ROOT", source)

    def test_each_script_group_is_a_python_package(self):
        for group in GROUPS:
            with self.subTest(group=group):
                self.assertTrue((ROOT / "scripts" / group / "__init__.py").is_file())

    def test_root_contains_only_the_python_import_bootstrap(self):
        root_python = {path.name for path in ROOT.glob("*.py")}
        self.assertEqual(root_python, {"sitecustomize.py", "shit.py"})

    def test_compatibility_directory_is_on_import_path(self):
        import sys
        self.assertIn(str(ROOT / "compat"), sys.path)


    def test_maintained_python_and_workflow_files_have_bottom_overviews(self):
        candidates = []
        for directory in ("scripts", "compat", "tests", ".github/workflows"):
            base = ROOT / directory
            if base.exists():
                suffixes = {".py"} if directory != ".github/workflows" else {".yml", ".yaml"}
                candidates.extend(path for path in base.rglob("*") if path.is_file() and path.suffix in suffixes)
        for path in sorted(candidates):
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                source = path.read_text(encoding="utf-8")
                self.assertIn("FILE OVERVIEW", source)
                self.assertIn("FILE OVERVIEW", source[-1500:])

    def test_implementation_overviews_are_specific_not_generic_templates(self):
        generic_phrases = (
            "Uses the canonical archives and/or generated project data",
            "consult this module's configuration and command options for exact paths",
            "tests/ contains regression coverage",
            "docs/ contains extended guides",
            "See docs/ for longer operational and data-contract guides",
            "Purpose: Implementation module scripts/",
        )
        implementations = sorted((ROOT / "scripts").rglob("*.py"))
        self.assertTrue(implementations, "No maintained implementation modules were found")
        for path in implementations:
            if path.name == "__init__.py":
                continue
            source = path.read_text(encoding="utf-8")
            marker = source.rfind("FILE OVERVIEW")
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertGreaterEqual(marker, 0, "Missing FILE OVERVIEW")
                overview = source[marker:]
                self.assertIn("Purpose:", overview, "Overview must state the module's purpose")
                for phrase in generic_phrases:
                    self.assertNotIn(phrase, overview, f"Generic overview boilerplate: {phrase}")

    def test_compatibility_overviews_name_the_maintained_implementation(self):
        wrappers = sorted(path for path in (ROOT / "compat").glob("*.py") if path.name != "__init__.py")
        for path in wrappers:
            source = path.read_text(encoding="utf-8")
            marker = source.rfind("FILE OVERVIEW")
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertGreaterEqual(marker, 0, "Missing FILE OVERVIEW")
                self.assertIn("scripts/", source[marker:], "Compatibility overview must name its maintained implementation")

    def test_repository_gitignore_has_a_file_overview(self):
        source = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("FILE OVERVIEW", source)
        self.assertIn("FILE OVERVIEW", source[-1500:])


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Guard the responsibility-based implementation and compatibility layout.
# Scope: Regression checks for the behavior named by this test module.
# Run: python -m unittest tests.test_script_layout -v (from the repository root).
# Related: Implementation lives under scripts/; longer behavior notes live in docs/.
# -----------------------------------------------------------------------------
