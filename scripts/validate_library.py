#!/usr/bin/env python3
"""Check a resume library (profile.yaml, bullets.md, skills.md, archive.md)
before building from it.

Usage
  validate_library.py [LIBRARY]

LIBRARY defaults to user/ (falling back to examples/). Prints each problem
on its own line and exits 1 if there are any, 0 if the library is clean.

Checks
  - profile.yaml has name, a contact with an email, education with a
    school and graduation, a known font, and at least one variant
  - each variant has a valid section order, and every experience entry
    has slot, title, dates, org and at least one default bullet
  - bullet and project IDs are unique (across bullets.md and archive.md)
  - every default bullet ID exists and belongs to its slot or project
  - every default project exists in bullets.md
  - extra_experience entries have valid defaults and unique slots outside variants
  - every experience bullet's ID prefix matches a variant or extra_experience slot
  - skills.md has at least one category and no empty categories
  - every bullet has text
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from library import FONTS, SECTIONS, email_of, find_library, load_library, parse_skills  # noqa: E402


def check(library):
    problems = []
    try:
        lib = load_library(library)
    except SystemExit as e:  # duplicate IDs and similar parse errors
        return [str(e)]
    except FileNotFoundError as e:
        return [f"missing file: {e.filename}"]
    p, bullets, projects, groups = lib["profile"], lib["bullets"], lib["projects"], lib["groups"]

    # profile
    if not p.get("name"):
        problems.append("profile.yaml: 'name' is missing")
    if not email_of(p):
        problems.append("profile.yaml: no contact entry has an email address (a label containing '@')")
    for i, c in enumerate(p.get("contact") or []):
        if not isinstance(c, dict) or not c.get("label"):
            problems.append(f"profile.yaml: contact[{i}] needs a 'label'")
    edu = p.get("education") or []
    if not edu:
        problems.append("profile.yaml: 'education' is missing")
    for i, e in enumerate(edu):
        for key in ("school", "degree"):
            if not e.get(key):
                problems.append(f"profile.yaml: education[{i}] is missing '{key}'")
    if edu and not edu[0].get("graduation"):
        problems.append("profile.yaml: education[0] needs 'graduation' (the build checks for it)")
    if p.get("font") not in FONTS:
        problems.append(f"profile.yaml: font {p.get('font')!r} must be one of {list(FONTS)}")
    variants = p.get("variants") or {}
    if not variants:
        problems.append("profile.yaml: define at least one variant under 'variants'")

    def check_experience(x, where):
        for key in ("slot", "title", "dates", "org"):
            if not x.get(key):
                problems.append(f"{where} is missing '{key}'")
        slot = x.get("slot")
        ids = x.get("default_bullets") or []
        if not ids:
            problems.append(f"{where} ({slot}) has no default_bullets")
        for b in ids:
            if b not in bullets:
                problems.append(f"{where}: default bullet {b!r} for slot {slot!r} is not in bullets.md")
            elif bullets[b]["group"] != slot:
                problems.append(f"{where}: default bullet {b!r} belongs to {bullets[b]['group']!r}, "
                                f"not slot {slot!r} (an experience bullet's ID prefix must be its slot)")
            elif bullets[b].get("archive"):
                problems.append(f"{where}: {b!r} is an archive bullet; archive bullets can't be defaults")

    all_slots = set()
    for vid, v in variants.items():
        where = f"profile.yaml: variants.{vid}"
        order = v.get("section_order") or []
        bad = [s for s in order if s not in SECTIONS]
        if bad:
            problems.append(f"{where}.section_order has unknown sections {bad}; use {list(SECTIONS)}")
        for s in ("education", "projects", "skills"):
            if order and s not in order:
                problems.append(f"{where}.section_order leaves out '{s}'")
        for j, x in enumerate(v.get("experience") or []):
            all_slots.add(x.get("slot"))
            check_experience(x, f"{where}.experience[{j}]")
        for pid, ids in (v.get("default_projects") or {}).items():
            if pid not in projects:
                problems.append(f"{where}.default_projects: project {pid!r} is not in bullets.md")
                continue
            for b in ids or []:
                if b not in projects[pid]["bullets"]:
                    problems.append(f"{where}.default_projects.{pid}: bullet {b!r} is not under "
                                    f"project:{pid} in bullets.md")
        if not v.get("default_skills"):
            problems.append(f"{where} has no default_skills")
        for label, items in (v.get("default_skills") or {}).items():
            if not items:
                problems.append(f"{where}.default_skills.{label} is empty")

    extra_slots = set()
    for j, x in enumerate(p.get("extra_experience") or []):
        where = f"profile.yaml: extra_experience[{j}]"
        slot = x.get("slot")
        if slot in extra_slots:
            problems.append(f"{where}: duplicate extra_experience slot {slot!r}")
        if slot in all_slots:
            problems.append(f"{where}: slot {slot!r} is also in a variant")
        extra_slots.add(slot)
        check_experience(x, where)
    all_slots.update(extra_slots)

    # bullets
    for slot in groups:
        if slot not in all_slots:
            problems.append(f"bullets.md: experience bullets {groups[slot][:3]} have prefix {slot!r}, "
                            f"which isn't a variant or extra_experience slot (slots: {sorted(all_slots, key=str)})")
    for bid, b in bullets.items():
        if not b["text"]:
            problems.append(f"bullet {bid!r} has no text")
    for pid, pr in projects.items():
        if not pr["bullets"]:
            problems.append(f"project {pid!r} has no bullets")

    # skills
    skills_path = os.path.join(library, "skills.md")
    if not os.path.exists(skills_path):
        problems.append("skills.md is missing")
    else:
        cats = parse_skills(skills_path)
        if not cats:
            problems.append("skills.md has no '## Category' sections")
        for c in cats:
            if not c["items"]:
                problems.append(f"skills.md: category {c['label']!r} is empty")
    return problems


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    library = find_library(sys.argv[1] if len(sys.argv) > 1 else None)
    problems = check(library)
    for pr in problems:
        print(pr)
    if not problems:
        lib = load_library(library)
        print(f"ok: {library} has {len(lib['bullets'])} bullets, {len(lib['projects'])} projects, "
              f"{len(lib['profile'].get('variants') or {})} variants")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
