"""Delivered TeX has a single, safe header describing the requested resume."""

from datetime import date
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_resume import compose, resolve


class TexHeaderTests(unittest.TestCase):
    def resolve_plan(self, **fields):
        resolved, fails, warns = resolve({"variant": "swe", **fields}, str(ROOT / "examples"))
        self.assertEqual(fails, [])
        self.assertEqual(warns, [])
        return resolved

    def test_default_date_and_delivered_header(self):
        tex = compose(self.resolve_plan(company="Acme", role="Intern"))
        self.assertEqual(
            tex.splitlines()[0],
            f"% Alex Rivera resume, tailored for Acme (Intern), built {date.today().isoformat()} by resume-tailor",
        )
        self.assertNotIn("master_", tex)
        self.assertNotIn("Don't edit", tex)

    def test_company_and_role_combinations_with_pinned_date(self):
        cases = [
            ({"company": "Acme", "role": "Intern"}, "tailored for Acme (Intern)"),
            ({"company": "Acme"}, "tailored for Acme"),
            ({"role": "Intern"}, "tailored for Intern"),
            ({}, "swe base"),
        ]
        for fields, description in cases:
            with self.subTest(fields=fields):
                resolved = self.resolve_plan(**fields)
                self.assertEqual(resolved["company"], fields.get("company", ""))
                self.assertEqual(resolved["role"], fields.get("role", ""))
                tex = compose(resolved, build_date=date(2025, 1, 2))
                self.assertEqual(
                    tex.splitlines()[0],
                    f"% Alex Rivera resume, {description}, built 2025-01-02 by resume-tailor",
                )
                self.assertEqual(tex.splitlines()[1], r"\documentclass[termes]{resume}")
                self.assertNotIn("master_", tex)
                self.assertNotIn("Don't edit", tex)

    def test_whitespace_collapses_in_every_interpolated_value(self):
        resolved = self.resolve_plan(company=" \tAcme\r\nCorp ", role=" Intern\n\r Engineer\t")
        resolved["name"] = " Alex\r\n Rivera\t"
        self.assertEqual(
            compose(resolved, build_date=date(2025, 1, 2)).splitlines()[0],
            "% Alex Rivera resume, tailored for Acme Corp (Intern Engineer), built 2025-01-02 by resume-tailor",
        )
        resolved.update(company="\r\n ", role="\t", variant=" swe\r\n base\t")
        self.assertEqual(
            compose(resolved, build_date=date(2025, 1, 2)).splitlines()[0],
            "% Alex Rivera resume, swe base base, built 2025-01-02 by resume-tailor",
        )

    def test_only_leading_master_comments_are_removed(self):
        resolved = self.resolve_plan()
        resolved["src"] = "% master_swe.tex\n% Don't edit\n\\documentclass{resume}\n% body comment\n"
        self.assertEqual(
            compose(resolved, build_date=date(2025, 1, 2)),
            "% Alex Rivera resume, swe base, built 2025-01-02 by resume-tailor\n"
            "\\documentclass{resume}\n% body comment\n",
        )


if __name__ == "__main__":
    unittest.main()
