#!/usr/bin/env python3
"""Zip the skill together with a personal library, for upload to the Claude app.

The Claude app resets its workspace between chats, so a library written
during setup only survives if it ships inside the skill itself. This makes
resume-tailor-<name>.zip with one top-level folder, resume-tailor/, holding
SKILL.md, the scripts, assets, templates, references, the examples, and the
library as user/.

Usage
  package_skill.py [--library DIR] [--out DIR]
  package_skill.py --no-library [--out DIR]     the public skill, no user/ (for first install)

--library defaults to user/ in the skill folder; --out defaults to the
current directory. Prints the path of the zip.
"""

import argparse
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from library import SKILL_DIR, USER_DIR, load_profile  # noqa: E402

SKILL_NAME = "resume-tailor"  # must match `name:` in SKILL.md
INCLUDE = ["SKILL.md", "LICENSE", "assets", "templates", "scripts", "references", "examples"]
EXCLUDE_DIRS = {"__pycache__", "resume-work", "letter-work", ".git", "masters"}
EXCLUDE_FILES = {os.path.join("examples", "sample-output.pdf")}
LIBRARY_FILES = ["profile.yaml", "bullets.md", "skills.md", "archive.md"]
MAX_BYTES = 8 * 1024 * 1024  # skill uploads must stay small; this is a conservative cap


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "user"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library", default=USER_DIR)
    ap.add_argument("--out", default=".")
    ap.add_argument("--no-library", action="store_true", help="package the public skill without user/")
    args = ap.parse_args()
    if args.no_library:
        args.library = None
    else:
        check_library(args.library)
    name = load_profile(args.library).get("name", "user") if args.library else None
    os.makedirs(args.out, exist_ok=True)
    zpath = os.path.join(args.out, f"{SKILL_NAME}-{slug(name)}.zip" if name else f"{SKILL_NAME}.zip")
    write_zip(zpath, args.library)
    print(zpath)


def check_library(library):
    missing = [f for f in LIBRARY_FILES[:3] if not os.path.exists(os.path.join(library, f))]
    if missing:
        sys.exit(f"{library} is missing {missing}; run setup first (references/setup.md)")
    from validate_library import check
    problems = check(library)
    if problems:
        sys.exit("library has problems; fix them before packaging:\n  " + "\n  ".join(problems))


def write_zip(zpath, library):
    total = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for top in INCLUDE:
            src = os.path.join(SKILL_DIR, top)
            if os.path.isfile(src):
                z.write(src, os.path.join(SKILL_NAME, top))
                total += os.path.getsize(src)
                continue
            for root, dirs, files in os.walk(src):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, SKILL_DIR)
                    if rel in EXCLUDE_FILES or f.endswith(".pyc"):
                        continue
                    z.write(full, os.path.join(SKILL_NAME, rel))
                    total += os.path.getsize(full)
        for f in (LIBRARY_FILES if library else []):
            full = os.path.join(library, f)
            if os.path.exists(full):
                z.write(full, os.path.join(SKILL_NAME, "user", f))
                total += os.path.getsize(full)
    if total > MAX_BYTES:
        print(f"WARNING: {total // 1024} KB uncompressed; skill uploads may reject large bundles", file=sys.stderr)


if __name__ == "__main__":
    main()
