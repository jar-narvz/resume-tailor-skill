"""Validate libraries and the zip installed by Claude app users."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[1]


class LibraryToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.library = self.root / "library"
        shutil.copytree(ROOT / "examples", self.library)

    def run_script(self, name, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts" / name), *map(str, args)],
                              capture_output=True, text=True)

    def assert_invalid(self, message):
        result = self.run_script("validate_library.py", self.library)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(message, result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_examples_validate(self):
        result = self.run_script("validate_library.py", self.library)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout,
                         f"ok: {self.library} has 24 bullets, 3 projects, 2 variants\n")

    def test_duplicate_bullet_id_is_rejected(self):
        with (self.library / "bullets.md").open("a") as bullets:
            bullets.write("\n## Duplicate\n\n### acme-1\nBuilt another service.\n")
        self.assert_invalid("bullet id 'acme-1' appears twice")

    def test_missing_default_bullet_is_rejected(self):
        profile_path = self.library / "profile.yaml"
        profile = yaml.safe_load(profile_path.read_text())
        profile["variants"]["swe"]["experience"][0]["default_bullets"] = ["acme-999"]
        profile_path.write_text(yaml.safe_dump(profile, sort_keys=False))
        self.assert_invalid("default bullet 'acme-999' for slot 'acme' is not in bullets.md")

    def test_empty_bullet_is_rejected(self):
        with (self.library / "bullets.md").open("a") as bullets:
            bullets.write("\n## Empty\n\n### acme-999\n")
        self.assert_invalid("bullet 'acme-999' has no text")

    def test_public_package_layout_and_extracted_validation(self):
        out = self.root / "packages"
        result = self.run_script("package_skill.py", "--no-library", "--out", out)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        zip_path = out / "resume-tailor.zip"
        self.assertEqual(result.stdout.strip(), str(zip_path))
        extracted = self.root / "extracted"
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            self.assertTrue(names)
            self.assertTrue(all(name.startswith("resume-tailor/") for name in names), names)
            self.assertIn("resume-tailor/SKILL.md", names)
            for directory in ("scripts", "assets", "references", "examples"):
                self.assertTrue(any(name.startswith(f"resume-tailor/{directory}/") for name in names),
                                directory)
            self.assertFalse(any(name.startswith("resume-tailor/user/") for name in names))
            archive.extractall(extracted)
        skill = extracted / "resume-tailor"
        validation = subprocess.run(
            [sys.executable, str(skill / "scripts/build_resume.py"),
             "--library", str(skill / "examples"), "validate", str(skill / "examples/sample-plan.json")],
            cwd=skill, capture_output=True, text=True,
        )
        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
        self.assertEqual(json.loads(validation.stdout), {"ok": True, "fails": [], "warns": []})

    def test_invalid_personal_library_cannot_be_packaged(self):
        with (self.library / "bullets.md").open("a") as bullets:
            bullets.write("\n## Empty\n\n### acme-999\n")
        out = self.root / "packages"
        result = self.run_script("package_skill.py", "--library", self.library, "--out", out)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("library has problems; fix them before packaging", result.stderr)
        self.assertIn("bullet 'acme-999' has no text", result.stderr)
        self.assertEqual(list(out.glob("*.zip")), [])


if __name__ == "__main__":
    unittest.main()
