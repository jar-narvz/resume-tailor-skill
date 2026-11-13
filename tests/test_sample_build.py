"""Exercise the public CLI with real sample and overflowing resumes."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import support

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_resume import resolve
from library import norm


class SampleBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.library = self.root / "library"
        shutil.copytree(ROOT / "examples", self.library)
        self.plan_path = self.library / "sample-plan.json"
        self.out = self.root / "out"

    def build(self):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_resume.py"), "--library", str(self.library),
             "build", str(self.plan_path), str(self.out)], capture_output=True, text=True,
        )

    @support.requires_tex
    def test_sample_plan_builds_and_all_resolved_bullets_extract(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["pages"], 1)
        self.assertEqual(summary["fails"], [])
        self.assertEqual(summary["bullets_used"], 19)
        resolved, fails, _ = resolve(json.loads(self.plan_path.read_text()), str(self.library))
        self.assertEqual(fails, [])
        extracted = subprocess.run(["pdftotext", "-layout", summary["pdf"], "-"],
                                   capture_output=True, text=True)
        self.assertEqual(extracted.returncode, 0, extracted.stderr)
        bullets = [b for p in resolved["projects"] for b in p["bullets"]]
        bullets += [b for slot in resolved["slots"].values() for b in slot]
        self.assertEqual(len(bullets), 19)
        for bullet in bullets:
            with self.subTest(bullet_id=bullet["id"]):
                self.assertIn(norm(bullet["text"]), norm(extracted.stdout))

    @support.requires_tex
    def test_overflow_exits_one_and_keeps_tex(self):
        plan = json.loads(self.plan_path.read_text())
        # Extra experience and project/archive bullets overflow by a wide margin across TeX installs.
        plan["add_experience"] = ["harbor"]
        for project in plan["projects"]:
            if project["id"] == "proj-plant":
                project["bullets"] = ["plant-2", "plant-1", "plant-4", "plant-3"]
            elif project["id"] == "proj-chat":
                project["bullets"] += ["chat-a1"]
        plan["experience"]["acme"] += ["acme-a1"]
        self.plan_path.write_text(json.dumps(plan))
        result = self.build()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        summary = json.loads(result.stdout)
        self.assertGreaterEqual(summary["pages"], 2)
        self.assertTrue(any("pages; cut the weakest bullet" in fail for fail in summary["fails"]),
                        summary["fails"])
        self.assertTrue((self.out / "tailored.tex").is_file())
        self.assertIn("Data Analyst Intern", (self.out / "tailored.tex").read_text())
        self.assertTrue(Path(summary["tex"]).is_file())


if __name__ == "__main__":
    unittest.main()
