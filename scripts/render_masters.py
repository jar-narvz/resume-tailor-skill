#!/usr/bin/env python3
"""Render profile.yaml into one master_<variant>.tex per variant.

A master is the fixed part of a resume: header, education, section order,
experience entries, and the default bullets, projects and skills (as
`%%BULLETS slot: ids%%` slots and `% @skills` / `% @projects` comment lines
that build_resume.py fills). The build renders masters in memory on every
run, so writing them to disk is only for reading or debugging.

Usage
  render_masters.py [LIBRARY] [OUTDIR]

LIBRARY defaults to user/ (falling back to examples/); OUTDIR defaults to
LIBRARY/masters/.
"""

import os
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from library import (FONTS, SECTIONS, TEMPLATES, esc_text, esc_url, find_library,  # noqa: E402
                     graduations, load_profile)


def contact_line(profile, sep=r"\rSep{}", letter=False):
    """The " | " contact line. For a cover letter (letter=True) entries with
    `letter: false` are skipped, and so is a plain location (no url, no digits)."""
    parts = []
    for c in profile.get("contact", []):
        if letter and (c.get("letter") is False or
                       (c.get("letter") is None and not c.get("url")
                        and not any(ch.isdigit() for ch in str(c.get("label", ""))))):
            continue
        label = esc_text(c.get("label", ""))
        url = c.get("url")
        parts.append(f"\\href{{{esc_url(url)}}}{{{label}}}" if url else label)
    return sep.join(parts)


def education_tex(profile, graduation=None):
    out = []
    default_grad, _ = graduations(profile)
    for i, e in enumerate(profile.get("education") or []):
        grad = graduation if (i == 0 and graduation) else str(e.get("graduation", ""))
        prefix = e.get("graduation_prefix", "Expected Graduation:" if i == 0 else "")
        right = (esc_text(prefix) + r"\rS" if prefix else "") + f"\\textbf{{{esc_text(grad)}}}" if grad else ""
        out.append(f"\\rSchool{{{esc_text(e.get('school', ''))}}}{{{right}}}")
        if e.get("degree"):
            out.append(f"\\rDegree{{{esc_text(e['degree'])}}}")
        if e.get("coursework"):
            out.append(r"\textbf{Relevant Coursework:}\rS " + esc_text(", ".join(e["coursework"])) + r"\par")
    return "\n".join(out)


def dates(s):
    # a real space after the en dash so parsers don't glue "2026--August"
    return esc_text(s).replace(" -- ", r" --\rS ")


def experience_tex(variant):
    out = []
    for x in variant.get("experience") or []:
        org = esc_text(x.get("org", ""))
        if x.get("org_url"):
            org = f"\\href{{{esc_url(x['org_url'])}}}{{{org}}}"
        out.append(f"\\rTitle{{{esc_text(x.get('title', ''))}}}{{{dates(x.get('dates', ''))}}}")
        out.append(f"\\rAt{{{org}}}{{{esc_text(x.get('location', ''))}}}")
        out.append(f"%%BULLETS {x['slot']}: {' '.join(x.get('default_bullets') or [])}%%")
    return "\n".join(out)


def render(profile, vid, graduation=None):
    """Return the master .tex source for one variant."""
    variants = profile.get("variants") or {}
    if vid not in variants:
        raise SystemExit(f"unknown variant {vid!r}; profile.yaml has {sorted(variants)}")
    v = variants[vid]
    font = profile.get("font", "termes")
    if font not in FONTS:
        raise SystemExit(f"font {font!r} must be one of {FONTS}")

    defaults = []
    for label, items in (v.get("default_skills") or {}).items():
        defaults.append(f"% @skills {label}: {', '.join(str(i) for i in items)}")
    for pid, ids in (v.get("default_projects") or {}).items():
        defaults.append(f"% @projects {pid}: {' '.join(ids or [])}")

    body = {
        "education": education_tex(profile, graduation),
        "experience": experience_tex(v),
        "projects": "%%PROJECTS%%",
        "skills": "%%SKILLS%%",
    }
    order = v.get("section_order") or list(SECTIONS)
    sections = []
    for s in order:
        if s not in body:
            raise SystemExit(f"variant {vid}: unknown section {s!r}; use {SECTIONS}")
        if s == "experience" and not v.get("experience"):
            continue
        sections.append(f"\\section{{{s.capitalize()}}}\n{body[s]}\n")

    name = esc_text(profile.get("name", ""))
    with open(os.path.join(TEMPLATES, "master.tex.tmpl"), encoding="utf-8") as f:
        tmpl = string.Template(f.read())
    return tmpl.substitute(variant=vid, defaults="\n".join(defaults), font=font,
                           title=f"{name} Resume", author=name, name=name,
                           contact=contact_line(profile), sections="\n".join(sections))


def main():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    library = find_library(args[0] if args else None)
    outdir = args[1] if len(args) > 1 else os.path.join(library, "masters")
    profile = load_profile(library)
    os.makedirs(outdir, exist_ok=True)
    for vid in profile.get("variants") or {}:
        path = os.path.join(outdir, f"master_{vid}.tex")
        with open(path, "w", encoding="utf-8") as f:
            f.write(render(profile, vid))
        print(path)


if __name__ == "__main__":
    main()
