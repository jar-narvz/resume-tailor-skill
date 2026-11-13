"""Reframes preserve claims while allowing small wording changes."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_resume import check_reframe, numbers
from library import load_library


class ReframeTests(unittest.TestCase):
    def test_rejected_reframes(self):
        cases = [
            ("Built a service", "Led a service", "words not in the original bullet: led"),
            ("Built a service", "Managed a service", "words not in the original bullet: managed"),
            ("Built a service", "Built a developed service", "words not in the original bullet: developed"),
            ("Cut sync from 3 hours to 25 minutes", "Cut sync from 25 hours to 3 minutes", "numbers changed:"),
            ("Built 6 REST endpoints", "Built 7 REST endpoints", "numbers changed:"),
            ("Built a service", "Built 3 services", "numbers changed:"),
            ("Built 6 REST endpoints", "Built 6 endpoints", "numbers changed:"),
            ("Built a service", "Built a scalable service", "words not in the original bullet: scalable"),
            ("Built a service", "Built a service with the and for", "reframe is longer than the original by more than 3 words"),
        ]
        for original, text, message in cases:
            with self.subTest(text=text):
                self.assertTrue(any(message in p for p in check_reframe(original, text)),
                                check_reframe(original, text))

    def test_allowed_reframes(self):
        cases = [
            ("Built a service", "Developed a service"),
            ("Led a service", "Built a service"),
            ("Led a service", "Led a service"),
            ("Led a service", "Managed a service"),
            ("Managed a service", "Lead a service"),
            ("Built a service", "Engineer a service"),
            ("Built a service with tests", "Built a service"),
            ("Developed services", "Develop service"),
            ("Built service", "Built a service with the"),
        ]
        for original, text in cases:
            with self.subTest(text=text):
                self.assertEqual(check_reframe(original, text), [])

    def test_unchanged_bullet_and_numbered_clause_reorder(self):
        original = "Built 6 endpoints and wrote 3 tests"
        self.assertEqual(check_reframe(original, original), [])
        self.assertEqual(check_reframe(original, "Wrote 3 tests and built 6 endpoints"), [])

    def test_removed_or_repeated_number_is_rejected(self):
        for text in ("Built endpoints", "Built 6 endpoints and 6 endpoints"):
            with self.subTest(text=text):
                self.assertTrue(any("numbers changed:" in problem
                                    for problem in check_reframe("Built 6 endpoints", text)))

    def test_sample_clause_reorder(self):
        plan = json.loads((ROOT / "examples/sample-plan.json").read_text())
        reframe = plan["experience"]["acme"][0]
        original = load_library(str(ROOT / "examples"))["bullets"][reframe["reframe_of"]]["text"]
        self.assertEqual(check_reframe(original, reframe["text"]), [])

    def test_number_pairs_include_next_word_and_preserve_duplicates(self):
        self.assertEqual(numbers("3 hours, 25 minutes; 3 hours; 92% coverage; 40+ warehouses; 6"),
                         [("25", "minutes"), ("3", "hours"), ("3", "hours"),
                          ("40+", "warehouses"), ("6", ""), ("92%", "coverage")])


if __name__ == "__main__":
    unittest.main()
