"""Prerequisites shared by tests that compile and inspect real PDFs."""

from functools import wraps
import importlib
import os
import shutil


def requires_tex(test):
    """Skip missing local tools, or fail when CI requires the full build suite."""
    @wraps(test)
    def checked(self, *args, **kwargs):
        missing = [tool for tool in ("xelatex", "pdfinfo", "pdffonts", "pdftotext")
                   if shutil.which(tool) is None]
        try:
            importlib.import_module("pikepdf")
        except ImportError:
            missing.append("pikepdf")
        if missing:
            message = "PDF build prerequisites missing: " + ", ".join(missing)
            if os.environ.get("RESUME_TAILOR_REQUIRE_TEX") == "1":
                self.fail(message)
            self.skipTest(message)
        return test(self, *args, **kwargs)
    return checked
