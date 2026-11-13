"""Plan additions preserve position facts, slot ownership, and default builds."""

import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import support

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_resume import compose, resolve
from library import load_library
from validate_library import check


class AddExperienceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = Path(self.temp.name) / "library"
        shutil.copytree(ROOT / "examples", self.library)
        self.profile = yaml.safe_load((self.library / "profile.yaml").read_text())
        # Supply a controlled pool even before the example has been updated.
        self.profile["extra_experience"] = [{
            "slot": "harbor", "title": "Data Analyst Intern",
            "dates": "June 2025 -- August 2025", "org": "Harbor Analytics",
            "org_url": "https://example.com/harbor", "location": "Oakland, CA",
            "default_bullets": ["harbor-1", "harbor-2"],
        }]
        bullets = self.library / "bullets.md"
        if "### harbor-1 " not in bullets.read_text():
            with bullets.open("a") as f:
                f.write("\n## Experience\n\n### harbor-1  [sql]\n"
                        "Built SQL reports for the operations team.\n\n"
                        "### harbor-2  [python]\n"
                        "Wrote Python checks for missing records.\n")
        self.save_profile()

    def save_profile(self):
        (self.library / "profile.yaml").write_text(yaml.safe_dump(self.profile, sort_keys=False))

    def resolve_plan(self, **changes):
        self.save_profile()
        return resolve({"variant": "swe", "add_experience": ["harbor"], **changes}, str(self.library))

    def assert_rejected(self, message, **changes):
        _, fails, _ = self.resolve_plan(**changes)
        self.assertTrue(any(message in f for f in fails), fails)

    def test_default_bullets_and_headers_are_appended_without_mutation(self):
        self.save_profile()
        lib = load_library(str(self.library))
        original = copy.deepcopy(lib["profile"])
        with patch("build_resume.load_library", return_value=lib):
            r, fails, warns = self.resolve_plan()
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])
        self.assertEqual(list(r["slots"]), ["acme", "northwind", "harbor"])
        self.assertEqual([b["id"] for b in r["slots"]["harbor"]], ["harbor-1", "harbor-2"])
        self.assertEqual(r["added_experience"], ["harbor"])
        tex = compose(r)
        self.assertIn("Data Analyst Intern", tex)
        self.assertIn("Harbor Analytics", tex)
        self.assertIn("https://example.com/harbor", tex)
        self.assertIn("Oakland, CA", tex)
        self.assertIn("June 2025", tex)
        self.assertLess(tex.index("Undergraduate Research Assistant"), tex.index("Data Analyst Intern"))
        self.assertEqual(lib["profile"], original)

    def test_explicit_override(self):
        r, fails, _ = self.resolve_plan(experience={"harbor": ["harbor-2"]})
        self.assertEqual(fails, [])
        self.assertEqual([b["id"] for b in r["slots"]["harbor"]], ["harbor-2"])

    def test_empty_override_fails(self):
        self.assert_rejected("no bullets", experience={"harbor": []})

    def test_added_position_without_defaults_fails(self):
        self.profile["extra_experience"][0]["default_bullets"] = []
        self.assert_rejected("no bullets")

    def test_wrong_slot_bullet_fails(self):
        self.assert_rejected("not here", experience={"harbor": ["acme-1"]})

    def test_malformed_additions_fail(self):
        for value in (["harbor", "harbor"], "harbor", None, {}, [1], [["harbor"]]):
            with self.subTest(value=value):
                self.assert_rejected("unique strings", add_experience=value)

    def test_unknown_slot_fails(self):
        self.assert_rejected("unknown", add_experience=["typo"])

    def test_existing_slot_fails(self):
        self.assert_rejected("already", add_experience=["acme"])

    def test_unrequested_override_fails(self):
        self.assert_rejected("not in variant", add_experience=[], experience={"harbor": ["harbor-1"]})

    def test_first_other_variant_supplies_header_and_defaults(self):
        first = copy.deepcopy(self.profile["extra_experience"][0])
        first["default_bullets"] = ["harbor-2"]
        second = {**first, "title": "Later Title", "default_bullets": ["harbor-1"]}
        self.profile["extra_experience"] = []
        self.profile["variants"]["ml"]["experience"].append(first)
        self.profile["variants"]["later"] = {**self.profile["variants"]["ml"], "experience": [second]}
        r, fails, _ = self.resolve_plan()
        self.assertEqual(fails, [])
        self.assertEqual([b["id"] for b in r["slots"]["harbor"]], ["harbor-2"])
        self.assertIn("Data Analyst Intern", compose(r))
        self.assertNotIn("Later Title", compose(r))

    def test_pool_precedes_other_variants_and_preserves_list_order(self):
        other = {**self.profile["extra_experience"][0], "title": "Other Title",
                 "default_bullets": ["harbor-2"]}
        self.profile["variants"]["ml"]["experience"].append(other)
        # northwind becomes an addition from the other variant.
        self.profile["variants"]["swe"]["experience"].pop()
        r, fails, _ = self.resolve_plan(add_experience=["harbor", "northwind"])
        self.assertEqual(fails, [])
        self.assertEqual(list(r["slots"]), ["acme", "harbor", "northwind"])
        self.assertIn("Data Analyst Intern", compose(r))
        self.assertNotIn("Other Title", compose(r))
        self.assertEqual([b["id"] for b in r["slots"]["harbor"]], ["harbor-1", "harbor-2"])

    def test_empty_experience_and_omitted_section_order_render(self):
        self.profile["variants"]["swe"]["experience"] = []
        for omitted in (False, True):
            with self.subTest(omitted_section_order=omitted):
                if omitted:
                    del self.profile["variants"]["swe"]["section_order"]
                r, fails, _ = self.resolve_plan()
                self.assertEqual(fails, [])
                self.assertIn(r"\section{Experience}", compose(r))
                self.assertIn("Data Analyst Intern", compose(r))

    def test_section_order_without_experience_fails(self):
        self.profile["variants"]["swe"]["section_order"] = ["education", "projects", "skills"]
        self.assert_rejected("section_order")

    def test_library_without_pool_keeps_defaults(self):
        del self.profile["extra_experience"]
        self.save_profile()
        r, fails, _ = resolve({"variant": "swe"}, str(self.library))
        self.assertEqual(fails, [])
        self.assertEqual(list(r["slots"]), ["acme", "northwind"])
        self.assertEqual(r["added_experience"], [])
        self.assertNotIn("Data Analyst Intern", compose(r))

    def test_build_failures_exit_cleanly(self):
        cases = [({"add_experience": v}, "unique strings")
                 for v in ("harbor", None, {}, ["harbor", "harbor"], [1], [["harbor"]])]
        cases += [({"add_experience": ["typo"]}, "unknown"),
                  ({"add_experience": ["acme"]}, "already"),
                  ({"experience": {"harbor": []}}, "no bullets"),
                  ({"experience": {"harbor": ["acme-1"]}}, "not here"),
                  ({"add_experience": [], "experience": {"harbor": ["harbor-1"]}}, "not in variant")]
        for changes, message in cases:
            with self.subTest(changes=changes):
                self.assert_build_rejected(changes, message)
        self.profile["variants"]["swe"]["section_order"] = ["education", "projects", "skills"]
        self.save_profile()
        self.assert_build_rejected({}, "section_order")

    def assert_build_rejected(self, changes, message):
        plan = Path(self.temp.name) / "plan.json"
        plan.write_text(json.dumps({"variant": "swe", "add_experience": ["harbor"], **changes}))
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/build_resume.py"),
                               "--library", str(self.library), "build", str(plan),
                               str(Path(self.temp.name) / "out")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertTrue(any(message in f for f in json.loads(proc.stdout)["fails"]), proc.stdout)

    def test_validator_rejects_invalid_extra_entries(self):
        original = copy.deepcopy(self.profile)
        cases = [
            ("duplicate", lambda p: p["extra_experience"].append(copy.deepcopy(p["extra_experience"][0]))),
            ("variant", lambda p: p["extra_experience"].append(copy.deepcopy(p["variants"]["swe"]["experience"][0]))),
            ("missing 'title'", lambda p: p["extra_experience"][0].pop("title")),
            ("no default_bullets", lambda p: p["extra_experience"][0].pop("default_bullets")),
            ("not in bullets.md", lambda p: p["extra_experience"][0].update(default_bullets=["harbor-missing"])),
            ("not slot", lambda p: p["extra_experience"][0].update(default_bullets=["acme-1"])),
            ("archive", lambda p: p["extra_experience"][0].update(default_bullets=["harbor-a1"])),
        ]
        with (self.library / "archive.md").open("a") as f:
            f.write("\n## Experience\n\n### harbor-a1  [sql]\nWrote archived SQL reports.\n")
        for message, mutate in cases:
            with self.subTest(message=message):
                self.profile = copy.deepcopy(original)
                mutate(self.profile)
                self.save_profile()
                problems = check(str(self.library))
                self.assertTrue(any(message in p for p in problems), problems)

    def test_example_library_passes_validator(self):
        self.assertEqual(check(str(ROOT / "examples")), [])

    @support.requires_tex
    def test_example_addition_end_to_end(self):
        plan = Path(self.temp.name) / "plan.json"
        plan.write_text(json.dumps({"variant": "swe", "add_experience": ["harbor"],
                                    "projects": [{"id": "proj-kv"}, {"id": "proj-chat"}]}))
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/build_resume.py"),
                               "--library", str(ROOT / "examples"), "build", str(plan),
                               str(Path(self.temp.name) / "out")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        summary = json.loads(proc.stdout)
        self.assertEqual(summary["fails"], [])
        self.assertEqual(summary["pages"], 1)
        self.assertEqual(summary["added_experience"], ["harbor"])
        text = subprocess.check_output(["pdftotext", summary["pdf"], "-"], text=True)
        flat = re.sub(r"\s+", " ", text)
        self.assertIn("Data Analyst Intern", flat)
        bullets = load_library(str(ROOT / "examples"))["bullets"]
        for bid in ("harbor-1", "harbor-2"):
            self.assertIn(bullets[bid]["text"], flat)


if __name__ == "__main__":
    unittest.main()
