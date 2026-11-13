"""Plan skills drawn from selected bullets must match whole tokens."""

from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_resume import resolve


class PlanValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = Path(self.temp.name) / "library"
        shutil.copytree(ROOT / "examples", self.library)
        # Remove inventory sources so these cases exercise only bullet matching.
        (self.library / "skills.md").write_text("# Skills\n")
        (self.library / "archive.md").write_text("# Archive\n")
        profile_path = self.library / "profile.yaml"
        profile = yaml.safe_load(profile_path.read_text())
        for variant in profile["variants"].values():
            variant["default_skills"] = {}
        profile_path.write_text(yaml.safe_dump(profile, sort_keys=False))

    def test_skill_substring_is_rejected(self):
        _, fails, warns = resolve({"variant": "swe", "skills": [
            {"label": "Tools", "items": ["Script"]}]}, str(self.library))
        self.assertEqual(fails, ["skill 'Script' (Tools) is not in skills.md, archive.md, "
                                 "a variant's default_skills, or a bullet on this resume — only list "
                                 "what the user can speak to"])
        self.assertEqual(warns, [])

    def test_short_skill_from_bullet_word_is_rejected(self):
        # "in" is a whole word in the selected bullets, but a 1-2 character
        # item must come from a skills list, not from prose.
        for item in ["In", "A"]:
            with self.subTest(item=item):
                _, fails, _ = resolve({"variant": "swe", "skills": [
                    {"label": "Tools", "items": [item]}]}, str(self.library))
                self.assertEqual(len(fails), 1, fails)
                self.assertIn(f"skill {item!r}", fails[0])

    def test_punctuated_skill_from_selected_bullet_is_allowed(self):
        resolved, fails, warns = resolve({"variant": "swe", "skills": [
            {"label": "Tools", "items": ["Node.js"]}]}, str(self.library))
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])
        self.assertEqual(resolved["skills"], [{"label": "Tools", "items": ["Node.js"]}])


if __name__ == "__main__":
    unittest.main()
