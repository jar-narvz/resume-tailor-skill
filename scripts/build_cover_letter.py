#!/usr/bin/env python3
"""Compose, compile, and check a cover letter from a letter.json.

The header (name, contact line) and font come from profile.yaml through
templates/cover_letter.tex.tmpl; the layout comes from assets/cover_letter.cls
(see references/cover-letter.md). The JSON supplies only what changes per
posting.

Usage
  build_cover_letter.py [--library DIR] LETTER.json OUTDIR

letter.json
{
  "company": "Acme",
  "role": "Software Engineer Intern",
  "date": "October 4, 2026",                      # optional, defaults to today
  "addressee": ["Hiring Team", "Acme", "San Jose, CA"],
  "salutation": "Dear Acme Hiring Team:",
  "paragraphs": ["Opening ...", "Why me ...", "Why you (optional) ...", "Closing ..."]
}

Prints one JSON summary; exit 1 on any FAIL. Don't deliver a failed build.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import string
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_resume import compile_tex, safe_name  # noqa: E402
from library import TEMPLATES, email_of, esc, esc_text, find_library, load_profile  # noqa: E402
from render_masters import contact_line  # noqa: E402

WORDS_MIN, WORDS_MAX = 250, 450
PHONE = re.compile(r"\(?\d{3}\)?[ -]\d{3}-\d{4}")


def validate(L):
    fails, warns = [], []
    paras = L.get("paragraphs") or []
    if not 3 <= len(paras) <= 4:
        fails.append(f"{len(paras)} body paragraphs; the template wants 3 or 4 "
                     "(opening, why-me, optional why-this-company, closing)")
    if not L.get("salutation", "").rstrip().endswith(":"):
        fails.append("salutation should end with a colon, e.g. 'Dear Ms. Scott:'")
    if not L.get("addressee"):
        fails.append("addressee block is empty; use at least the company and city")
    n = len(" ".join(paras).split())
    if not WORDS_MIN <= n <= WORDS_MAX:
        warns.append(f"body is {n} words; aim for {WORDS_MIN}-{WORDS_MAX}")
    if paras and L.get("company") and L["company"].lower() not in paras[0].lower():
        warns.append("opening paragraph doesn't name the company")
    return fails, warns, n


def lesc(s):
    """esc() but keep phone numbers' hyphens (esc turns digit-digit into an en dash)."""
    keep = PHONE.findall(s)
    for i, ph in enumerate(keep):
        s = s.replace(ph, f"@@PH{i}@@", 1)
    s = esc(s)
    for i, ph in enumerate(keep):
        s = s.replace(f"@@PH{i}@@", ph)
    return s


def master(profile):
    name = esc_text(profile.get("name", ""))
    with open(os.path.join(TEMPLATES, "cover_letter.tex.tmpl"), encoding="utf-8") as f:
        tmpl = string.Template(f.read())
    return tmpl.substitute(font=profile.get("font", "termes"), title=f"{name} Cover Letter",
                           author=name, name=name, contact=contact_line(profile, r"\clSep{}", letter=True))


def compose(L, profile):
    src = master(profile)
    date = L.get("date") or datetime.date.today().strftime("%B %-d, %Y")
    block = "\\\\\n".join(lesc(x) for x in L["addressee"])
    body = "\n\n".join(lesc(p) for p in L["paragraphs"])
    return (src.replace("%%DATE%%", esc(date)).replace("%%ADDRESSEE%%", block)
               .replace("%%SALUTATION%%", esc(L["salutation"])).replace("%%BODY%%", body))


def check_pdf(pdf, L, profile):
    fails = []
    meta = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", meta).group(1))
    if pages != 1:
        fails.append(f"letter is {pages} pages; cut a sentence (usually from paragraph 2) and rebuild")
    fonts = subprocess.run(["pdffonts", pdf], capture_output=True, text=True).stdout.splitlines()[2:]
    if any(len(l.split()) >= 5 and l.split()[-5] == "no" for l in fonts):
        fails.append("fonts not embedded")
    text = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout
    flat = re.sub(r"\s+", " ", text)
    odd = sorted(set(c for c in text if ord(c) > 127 and c not in "–—’‘“”"))
    if odd:
        fails.append(f"PDF text has unexpected characters {odd}")
    for ph in PHONE.findall(" ".join(L["paragraphs"])):
        if ph not in flat:
            fails.append(f"phone number {ph!r} in the body didn't survive to the PDF text")
    musts = [profile.get("name", ""), "Sincerely", L["salutation"].split()[0]]
    if email_of(profile):
        musts.append(email_of(profile))
    for must in musts:
        if must and must not in flat:
            fails.append(f"extracted text is missing {must!r}")
    return fails, pages


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library", default=None)
    ap.add_argument("letter")
    ap.add_argument("outdir")
    args = ap.parse_args()
    profile = load_profile(find_library(args.library))
    L = json.load(open(args.letter, encoding="utf-8"))
    os.makedirs(args.outdir, exist_ok=True)
    fails, warns, n = validate(L)
    summary = {"words": n}
    if not fails:
        tex = compose(L, profile)
        pdf, _log, err = compile_tex(tex, "cover_letter.cls", "letter", args.outdir)
        if err:
            fails.append(err)
        else:
            f2, pages = check_pdf(pdf, L, profile)
            fails += f2
            summary["pages"] = pages
            name = safe_name(f"{profile.get('name', '')} Cover Letter - {L.get('company', '')} {L.get('role', '')}")
            shutil.copy(pdf, os.path.join(args.outdir, name + ".pdf"))
            open(os.path.join(args.outdir, name + ".tex"), "w", encoding="utf-8").write(tex)
            summary.update(pdf=os.path.join(args.outdir, name + ".pdf"),
                           tex=os.path.join(args.outdir, name + ".tex"))
    summary.update(fails=fails, warns=warns)
    print(json.dumps(summary, indent=1))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
