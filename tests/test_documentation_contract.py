"""Guard SHIT's repository-level documentation and fresh-session navigation."""
import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
CONTROL_DOCS = (
    "AGENTS.md",
    "docs/README.md",
    "project/ROADMAP.md",
    "project/goals/README.md",
)


class DocumentationContractTests(unittest.TestCase):
    def test_repository_control_documents_exist(self):
        required = (
            "AGENTS.md",
            "docs/README.md",
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

    def test_agent_entry_point_requires_documentation_rules(self):
        source = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("DOCUMENTATION_RULES.md", source)
        self.assertIn("NEXT_WORK.md", source)
        self.assertIn("LOOSE_ENDS.md", source)
        self.assertIn("same session", source.lower())

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
# Scope: Required control documents, per-goal roadmaps, navigation coverage and
#        local links from the main fresh-session entry points.
# Run: python -m unittest tests.test_documentation_contract -v
# Related: AGENTS.md, docs/README.md, project/DOCUMENTATION_RULES.md,
#          project/ROADMAP.md, and project/goals/*.
# -----------------------------------------------------------------------------
