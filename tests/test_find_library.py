"""Project library lookup and builds use isolated temporary directories."""

from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import library


class FindLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.user = self.root / "user"
        self.examples = self.root / "examples"
        for path in (self.project, self.user, self.examples):
            path.mkdir()
        self.env = patch.dict(os.environ, {"RESUME_TAILOR_PROJECT_DIR": str(self.project)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.paths = patch.multiple(library, USER_DIR=str(self.user), EXAMPLES_DIR=str(self.examples))
        self.paths.start()
        self.addCleanup(self.paths.stop)

    def populate(self, path):
        for name in ("profile.yaml", "bullets.md", "skills.md", "archive.md"):
            shutil.copyfile(ROOT / "examples" / name, path / name)

    def test_project_wins_and_warns_when_user_also_exists(self):
        self.populate(self.project)
        self.populate(self.user)
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(library.find_library(), str(self.project))
        self.assertEqual(len(stderr.getvalue().splitlines()), 1)
        self.assertIn("WARNING", stderr.getvalue())
        self.assertIn(str(self.project), stderr.getvalue())
        self.assertIn(str(self.user), stderr.getvalue())

    def test_project_without_user_needs_no_warning_or_archive(self):
        self.populate(self.project)
        (self.project / "archive.md").unlink()
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(library.find_library(), str(self.project))
        self.assertEqual(stderr.getvalue(), "")

    def test_user_used_when_project_has_no_profile(self):
        self.populate(self.user)
        (self.project / "bullets.md").write_text("unrelated", encoding="utf-8")
        self.assertEqual(library.find_library(), str(self.user))

    def test_explicit_wins_over_both_even_if_project_incomplete(self):
        self.populate(self.user)
        self.populate(self.examples)
        self.populate(self.project)
        for incomplete in (False, True):
            with self.subTest(incomplete=incomplete):
                if incomplete:
                    (self.project / "bullets.md").unlink()
                stderr = io.StringIO()
                with redirect_stderr(stderr):
                    self.assertEqual(library.find_library(str(self.examples)), str(self.examples))
                self.assertEqual(stderr.getvalue(), "")

    def test_missing_explicit_profile_does_not_fall_back(self):
        self.populate(self.project)
        with self.assertRaisesRegex(SystemExit, f"no profile.yaml in {self.user}"):
            library.find_library(str(self.user))

    def test_examples_fallback_warns(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(library.find_library(), str(self.examples))
        self.assertIn("WARNING", stderr.getvalue())
        self.assertIn("examples/ demo library", stderr.getvalue())

    def test_quiet_suppresses_warnings(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(library.find_library(quiet=True), str(self.examples))
            self.populate(self.project)
            self.populate(self.user)
            self.assertEqual(library.find_library(quiet=True), str(self.project))
        self.assertEqual(stderr.getvalue(), "")

    def test_incomplete_project_names_missing_files_without_fallback(self):
        self.populate(self.user)
        for missing in (("bullets.md",), ("skills.md",), ("bullets.md", "skills.md")):
            with self.subTest(missing=missing):
                self.populate(self.project)
                for name in missing:
                    (self.project / name).unlink()
                with self.assertRaises(SystemExit) as error:
                    library.find_library(quiet=True)
                message = str(error.exception)
                self.assertIn(str(self.project), message)
                self.assertIn(", ".join(missing), message)
                self.assertIn("Project's Context", message)

    def test_incomplete_project_cli_exits_cleanly(self):
        (self.project / "profile.yaml").touch()
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_resume.py"), "build",
             str(ROOT / "examples/sample-plan.json"), str(self.root / "out")],
            env=os.environ.copy(), capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("missing bullets.md, skills.md", result.stderr)
        self.assertIn("Project's Context", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.root / "out").exists())

    @unittest.skipUnless(shutil.which("xelatex"), "xelatex is not on PATH")
    def test_build_from_read_only_project(self):
        self.populate(self.project)
        original = {path.name: path.read_bytes() for path in self.project.iterdir()}
        try:
            for path in self.project.iterdir():
                path.chmod(0o444)
            self.project.chmod(0o555)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_resume.py"), "build",
                 str(ROOT / "examples/sample-plan.json"), str(self.root / "out")],
                env=os.environ.copy(), capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["library"], str(self.project))
            self.assertEqual(summary["fails"], [])
            self.assertEqual(summary["pages"], 1)
            self.assertEqual(summary["bullets_used"], 19)
            self.assertEqual(
                {path.name: path.read_bytes() for path in self.project.iterdir()}, original,
            )
        finally:
            self.project.chmod(0o755)
            for path in self.project.iterdir():
                path.chmod(0o644)


if __name__ == "__main__":
    unittest.main()
