"""PDF checks reject broken output without needing a TeX installation."""

import argparse
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_resume import FILL_MIN, check_pdf, cmd_build


class CheckPdfTests(unittest.TestCase):
    def setUp(self):
        self.resolved = {
            "name": "Alex Rivera", "email": "alex@example.com", "graduation": "May 2027",
            "projects": [{"bullets": [{"id": "chat-1", "text": "Built a real time chat app."}]}],
            "slots": {"acme": [{"id": "acme-1", "text": "Wrote a Python inventory service."}]},
        }
        self.text = ("Alex Rivera alex@example.com EDUCATION May 2027\n"
                     "Built a real time chat app.\nWrote a Python inventory service.\n")

    def check(self, *, pages=1, embedded="yes", text=None, bottom=756, log=""):
        outputs = {
            "pdfinfo": f"Pages: {pages}\n",
            "bbox": f'<page width="612" height="792"><word yMax="{bottom}">end</word></page>',
            "pdffonts": ("name type encoding emb sub uni object ID\n"
                         "-----------------------------------------\n"
                         f"Termes CID Type 0C Identity-H {embedded} yes yes 4 0\n"),
            "text": self.text if text is None else text,
        }

        def run(command, **kwargs):
            if command[0] == "pdftotext":
                key = "bbox" if "-bbox" in command else "text"
            else:
                key = command[0]
            return subprocess.CompletedProcess(command, 0, stdout=outputs[key], stderr="")

        with patch("build_resume.subprocess.run", side_effect=run):
            return check_pdf("unused.pdf", self.resolved, log)

    def test_clean_pdf(self):
        self.assertEqual(self.check(), ([], [], {
            "pages": 1, "page_fill_pct": 100.0, "bullets_used": 2}))

    def test_two_pages_are_rejected(self):
        fails, warns, info = self.check(pages=2)
        self.assertEqual(fails, ["resume is 2 pages; cut the weakest bullet for this posting and rebuild"])
        self.assertEqual(warns, [])
        self.assertEqual(info["pages"], 2)

    def test_unembedded_font_is_rejected(self):
        fails, _, _ = self.check(embedded="no")
        self.assertEqual(fails, ["fonts not embedded (viewers will substitute them): ['Termes']"])

    def test_unexpected_character_is_rejected(self):
        fails, _, _ = self.check(text=self.text + "\ufffd")
        self.assertEqual(fails, ["PDF text layer has unexpected characters ['\ufffd']; ATS parsers will misread them"])

    def test_required_text_is_checked(self):
        for required in ("Alex Rivera", "alex@example.com", "May 2027", "EDUCATION"):
            with self.subTest(required=required):
                fails, _, _ = self.check(text=self.text.replace(required, ""))
                self.assertEqual(fails, [f"extracted text is missing {required!r}"])

    def test_missing_project_and_experience_bullets_are_rejected(self):
        for bullet_id, text in (("chat-1", "Built a real time chat app."),
                                ("acme-1", "Wrote a Python inventory service.")):
            with self.subTest(bullet_id=bullet_id):
                fails, _, _ = self.check(text=self.text.replace(text, ""))
                self.assertEqual(fails, [f"bullets not recoverable from PDF text (ATS risk): {[bullet_id]}"])

    def test_sparse_page_warns(self):
        fails, warns, info = self.check(bottom=396)
        self.assertEqual(fails, [])
        self.assertEqual(info["page_fill_pct"], 50.0)
        self.assertLess(info["page_fill_pct"], FILL_MIN)
        self.assertEqual(warns, ["page is only 50.0% full, too sparse to stretch evenly; "
                                 "add a bullet or project back and rebuild"])

    def test_overfull_lines_warn(self):
        fails, warns, _ = self.check(log="Overfull \\hbox\nOverfull \\hbox")
        self.assertEqual(fails, [])
        self.assertEqual(warns, ["2 overfull line(s) in LaTeX log; text may run into the margin"])

    def test_invalid_plan_stops_before_compiling(self):
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp) / "library"
            shutil.copytree(ROOT / "examples", library)
            out = Path(temp) / "out"
            args = argparse.Namespace(variant="missing", graduation=None, plan=None,
                                      library=str(library), outdir=str(out), no_fill=False)
            stdout = io.StringIO()
            with patch("build_resume.compile_pdf") as compile_pdf, redirect_stdout(stdout):
                self.assertEqual(cmd_build(args), 1)
            compile_pdf.assert_not_called()
            self.assertEqual(json.loads(stdout.getvalue())["fails"],
                             ["unknown variant 'missing'; profile.yaml has ['ml', 'swe']"])
            self.assertFalse((out / "tailored.tex").exists())


if __name__ == "__main__":
    unittest.main()
