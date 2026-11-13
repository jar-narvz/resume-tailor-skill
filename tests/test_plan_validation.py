"""Plan skills drawn from selected bullets must match whole tokens."""

import json
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



class ResolvePlanTests(unittest.TestCase):
    """General plan validation keeps the example inventory intact."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = Path(self.temp.name) / "library"
        shutil.copytree(ROOT / "examples", self.library)

    def resolve_plan(self, **changes):
        return resolve({"variant": "swe", **changes}, str(self.library))

    def assert_rejected(self, message, **changes):
        _, fails, _ = self.resolve_plan(**changes)
        self.assertTrue(any(message in fail for fail in fails), fails)

    def test_unknown_variant(self):
        self.assert_rejected("unknown variant 'missing'", variant="missing")

    def test_unknown_graduation(self):
        self.assert_rejected("unknown graduation 'May 2030'", graduation="May 2030")

    def test_unknown_bullet(self):
        self.assert_rejected("bullet id 'missing-1' is not in bullets.md or archive.md",
                             experience={"acme": ["missing-1"]})

    def test_bullets_from_another_slot_or_project(self):
        self.assert_rejected("experience/acme: 'northwind-1' belongs to 'northwind', not here",
                             experience={"acme": ["northwind-1"]})
        self.assert_rejected("proj-chat: 'kv-1' belongs to 'proj-kv', not here",
                             projects=[{"id": "proj-chat", "bullets": ["kv-1"]}])

    def test_duplicate_project_bullet(self):
        self.assert_rejected("proj-chat: the same bullet is used twice",
                             projects=[{"id": "proj-chat", "bullets": ["chat-1", "chat-1"]}])

    def test_unknown_reframe_source(self):
        self.assert_rejected("reframe_of 'missing-1' is not in bullets.md or archive.md",
                             experience={"acme": [{"reframe_of": "missing-1", "text": "Built service"}]})

    def test_reframe_source_from_wrong_slot(self):
        self.assert_rejected("reframe_of 'northwind-1' belongs to 'northwind', not here",
                             experience={"acme": [{"reframe_of": "northwind-1", "text": "Train models"}]})

    def test_reframe_rules_are_enforced_by_resolve(self):
        from library import load_library
        original = load_library(str(self.library))["bullets"]["acme-1"]["text"]
        cases = [
            (original.replace("Built", "Led", 1), "words not in the original bullet: led"),
            (original.replace("3 hours to 25 minutes", "25 hours to 3 minutes"), "numbers changed:"),
        ]
        for text, problem in cases:
            with self.subTest(text=text):
                self.assert_rejected("experience/acme: reframe of acme-1 rejected — " + problem,
                                     experience={"acme": [{"reframe_of": "acme-1", "text": text}]})

    def test_invalid_bullet_entry(self):
        for entry in (42, None, {"text": "Invented text"}):
            with self.subTest(entry=entry):
                self.assert_rejected("bullet entry must be an id string or {reframe_of, text}",
                                     experience={"acme": [entry]})

    def test_unknown_project(self):
        self.assert_rejected("project 'proj-missing' is not in bullets.md",
                             projects=[{"id": "proj-missing"}])

    def test_unknown_experience_override(self):
        self.assert_rejected("experience slot 'missing' is not in variant 'swe'",
                             experience={"missing": ["acme-1"]})

    def test_empty_experience_override(self):
        self.assert_rejected("experience/acme: no bullets left; every position needs at least one",
                             experience={"acme": []})

    def test_skill_outside_inventory(self):
        self.assert_rejected("skill 'Kubernetes' (Tools) is not in skills.md",
                             skills=[{"label": "Tools", "items": ["Kubernetes"]}])

    def test_skill_from_unselected_bullet_is_rejected(self):
        # Grad-CAM appears in plant-3, which isn't selected here, and in no inventory.
        self.assert_rejected("skill 'Grad-CAM' (Tools) is not in skills.md",
                             projects=[{"id": "proj-chat", "bullets": ["chat-1"]}],
                             skills=[{"label": "Tools", "items": ["Grad-CAM"]}])

    def test_skill_from_another_variants_defaults(self):
        profile_path = self.library / "profile.yaml"
        profile = yaml.safe_load(profile_path.read_text())
        profile["variants"]["ml"]["default_skills"]["Tools"] = ["TensorFlow"]
        profile_path.write_text(yaml.safe_dump(profile, sort_keys=False))
        skills = [{"label": "Tools", "items": ["TensorFlow"]}]
        resolved, fails, warns = self.resolve_plan(skills=skills)
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])
        self.assertEqual(resolved["skills"], skills)
        self.assertEqual(resolved["archive_used"], [])

    def test_inner_parenthesized_inventory_skill(self):
        # Exclude proj-kv so Raft must come from Consensus (Raft), not a bullet.
        skills = [{"label": "Concepts", "items": ["Raft"]}]
        resolved, fails, warns = self.resolve_plan(
            projects=[{"id": "proj-chat", "bullets": ["chat-1"]}], skills=skills)
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])
        self.assertEqual(resolved["skills"], skills)
        self.assertEqual(resolved["archive_used"], [])

    def test_archive_only_skill_is_reported_exactly(self):
        skills = [{"label": "Tools", "items": ["Tableau"]}]
        resolved, fails, warns = self.resolve_plan(skills=skills)
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])
        self.assertEqual(resolved["skills"], skills)
        self.assertEqual(resolved["archive_used"], ["Tableau"])

    def test_unchanged_sample_plan(self):
        plan = json.loads((self.library / "sample-plan.json").read_text())
        resolved, fails, warns = resolve(plan, str(self.library))
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])
        self.assertEqual(resolved["reframes"], 1)


if __name__ == "__main__":
    unittest.main()
