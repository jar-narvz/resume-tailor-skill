#!/usr/bin/env python3
"""Compose, compile, and check a tailored resume from a plan.

The plan picks bullets by ID from the library's bullets.md (and archive.md);
profile.yaml supplies everything else (header, education, section order,
experience entries, defaults). Nothing on the resume can come from anywhere
except those files, which is the whole point: tailoring reorders and
selects, it never writes new claims.

Commands
  build PLAN.json OUTDIR          validate + compose + xelatex + checks
  build --variant swe OUTDIR      render a variant's defaults untouched
  validate PLAN.json              validation only (no LaTeX), fast

Options
  --library DIR  folder with profile.yaml, bullets.md, skills.md, archive.md
                 (default: user/ in the skill folder, else examples/ with a warning)

Output: prints one compact JSON summary. Exit code 1 on any FAIL; do not
deliver a resume from a failed build.

Plan shape (every key except "variant" is optional):
{
  "variant": "swe",                       (a key under variants: in profile.yaml)
  "company": "Acme", "role": "Software Engineer Intern",
  "skills":   [{"label": "Languages", "items": ["Go", "Python"]}, ...],
  "projects": [{"id": "proj-chat",
                "bullets": ["chat-1", {"reframe_of": "chat-2", "text": "..."}],
                "demo": false}, ...],
  "add_experience": ["harbor"],           (slots from the pool or another variant)
  "experience": {"acme": ["acme-3", "acme-1"]},
  "graduation": "December 2027"           (one of education[0].alt_graduations)
}
Omitted skills/projects/experience fall back to the variant's defaults.
add_experience appends positions in list order, looking in extra_experience
first, then variants in profile order. The first match supplies the header
and default bullets; experience can override those bullets by slot.
"""

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from library import (ASSETS, SECTIONS, email_of, esc, esc_text, esc_url, find_library,  # noqa: E402,F401
                     graduations, load_library, norm, split_items)
from render_masters import render  # noqa: E402

FILL_MIN = 93  # below this % of the page, add content instead of stretching spacing

# Reframes may swap the leading verb to one of these and otherwise only
# reorder / trim the original's own words. See references/reframe-rules.md.
VERB_ALLOW = {
    "built", "designed", "developed", "engineered", "implemented", "created",
    "wrote", "led", "managed", "maintained", "maintain", "manage", "lead",
    "build", "design", "develop", "implement", "create",
}
CONNECTORS = {
    "a", "an", "the", "and", "or", "to", "of", "for", "in", "on", "with", "by",
    "via", "using", "across", "over", "from", "into", "as", "that", "which",
    "while", "its", "their", "at", "per", "then", "both",
}


# ------------------------------------------------------------------ parsing

def parse_master(src):
    skills, projects = [], []
    for line in src.splitlines():
        m = re.match(r"^% @skills (.+?):\s*(.+)$", line)
        if m:
            skills.append({"label": m.group(1).strip(), "items": split_items(m.group(2))})
        m = re.match(r"^% @projects (\S+):\s*(.*)$", line)
        if m:
            projects.append({"id": m.group(1), "bullets": m.group(2).split()})
    slots = {m.group(1): m.group(2).split()
             for m in re.finditer(r"%%BULLETS (\S+):\s*([^%]*)%%", src)}
    return skills, projects, slots


# --------------------------------------------------------------- reframes

def words(s):
    return re.findall(r"[a-z0-9][a-z0-9+#'/.-]*[a-z0-9+#%]|[a-z0-9]", s.lower())


def numbers(s):
    return sorted(re.findall(r"\d[\d,.]*\+?%?", s))


def stem(w):
    w = w.strip(".'")
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[: -len(suf)]
            break
    return w[:-1] if w.endswith("e") and len(w) > 4 else w


def check_reframe(original, text):
    """Return a list of problems; empty means the reframe is allowed."""
    problems = []
    if numbers(original) != numbers(text):
        problems.append(f"numbers changed: {numbers(original)} -> {numbers(text)}")
    orig_stems = {stem(w) for w in words(original)}
    allowed = orig_stems | {stem(v) for v in VERB_ALLOW} | CONNECTORS
    new = [w for w in words(text) if stem(w) not in allowed and w not in allowed]
    if new:
        problems.append("words not in the original bullet: " + ", ".join(sorted(set(new))))
    if len(words(text)) > len(words(original)) + 3:
        problems.append("reframe is longer than the original by more than 3 words")
    return problems


# --------------------------------------------------------------- validate

def skill_inventory(lib):
    """Normalized set of every skill the user has listed anywhere."""
    lines = list(lib["skills_md"]) + list(lib["archive_skills"])
    for v in (lib["profile"].get("variants") or {}).values():
        for label, items in (v.get("default_skills") or {}).items():
            lines.append({"label": label, "items": [str(i) for i in items]})
    inventory = set()
    for line in lines:
        for item in line["items"]:
            inventory.add(norm(item))
            inner = re.search(r"\(([^()]*)\)", item)
            if inner:
                inventory.update(norm(x) for x in inner.group(1).split(","))
                inventory.add(norm(re.sub(r"\(.*\)", "", item)))
    return inventory


def resolve(plan, library):
    """Validate a plan and resolve it to concrete content. Returns (resolved, fails, warns)."""
    lib = load_library(library)
    profile, bullets, projects, groups = lib["profile"], lib["bullets"], lib["projects"], lib["groups"]
    variants = profile.get("variants") or {}
    fails, warns = [], []
    variant = plan.get("variant")
    if variant not in variants:
        return None, [f"unknown variant {variant!r}; profile.yaml has {sorted(variants)}"], []
    default_grad, allowed_grads = graduations(profile)
    graduation = plan.get("graduation") or default_grad
    if graduation not in allowed_grads:
        return None, [f"unknown graduation {graduation!r}; profile.yaml allows {allowed_grads} "
                      f"(add it to education[0].alt_graduations)"], []
    additions = plan.get("add_experience", [])
    if not isinstance(additions, list) or any(not isinstance(s, str) for s in additions) \
            or len(additions) != len(set(additions)):
        return None, ["add_experience must be a list of unique strings"], []
    base = variants[variant]
    if additions and "experience" not in (base.get("section_order") or SECTIONS):
        return None, [f"variant {variant!r}: section_order has no experience section"], []
    existing = {x.get("slot") for x in base.get("experience") or []}
    pool = list(profile.get("extra_experience") or [])
    pool += [x for v in variants.values() for x in v.get("experience") or []]
    added = []
    for slot in additions:
        if slot in existing:
            fails.append(f"add_experience: slot {slot!r} is already in variant {variant!r}")
            continue
        entry = next((x for x in pool if x.get("slot") == slot), None)
        if entry is None:
            fails.append(f"add_experience: unknown experience slot {slot!r}")
        else:
            added.append(entry)
    if fails:
        return None, fails, warns
    effective = copy.deepcopy(base)
    effective["experience"] = list(effective.get("experience") or []) + copy.deepcopy(added)
    effective_profile = {**profile, "variants": {**variants, variant: effective}}
    src = render(effective_profile, variant, graduation)
    d_skills, d_projects, d_slots = parse_master(src)
    other_defaults = [parse_master(render(profile, v))[1] for v in variants if v != variant]
    inventory = skill_inventory(lib)

    used_text = []

    def resolve_bullet(entry, allowed_ids, where):
        if isinstance(entry, str):
            if entry not in bullets:
                fails.append(f"{where}: bullet id {entry!r} is not in bullets.md or archive.md")
                return None
            if entry not in allowed_ids:
                fails.append(f"{where}: {entry!r} belongs to {bullets[entry]['group']!r}, not here")
                return None
            used_text.append(bullets[entry]["text"])
            return {"id": entry, "text": bullets[entry]["text"]}
        if isinstance(entry, dict) and "reframe_of" in entry:
            rid = entry["reframe_of"]
            if rid not in bullets:
                fails.append(f"{where}: reframe_of {rid!r} is not in bullets.md or archive.md")
                return None
            if rid not in allowed_ids:
                fails.append(f"{where}: reframe_of {rid!r} belongs to {bullets[rid]['group']!r}, not here")
                return None
            probs = check_reframe(bullets[rid]["text"], entry.get("text", ""))
            if probs:
                fails.append(f"{where}: reframe of {rid} rejected — " + "; ".join(probs))
                return None
            used_text.append(bullets[rid]["text"])
            return {"id": rid, "text": entry["text"], "reframe": True}
        fails.append(f"{where}: bullet entry must be an id string or {{reframe_of, text}}")
        return None

    # projects
    out_projects = []
    for p in plan.get("projects") or d_projects:
        pid = p.get("id")
        if pid not in projects:
            fails.append(f"project {pid!r} is not in bullets.md")
            continue
        ids = projects[pid]["bullets"]
        allowed = ids + projects[pid].get("archive", [])
        # No bullets given: use a variant's default list for this project (the
        # chosen variant's first, then any other's) so alternate wordings of
        # one bullet never both land on the page.
        default_ids = next((dp["bullets"] for dl in [d_projects] + other_defaults
                            for dp in dl if dp["id"] == pid), ids)
        chosen = [resolve_bullet(b, allowed, pid) for b in (p.get("bullets") or default_ids)]
        seen = [c["id"] for c in chosen if c]
        if len(seen) != len(set(seen)):
            fails.append(f"{pid}: the same bullet is used twice")
        info = {k: v for k, v in projects[pid].items() if k not in ("archive", "bullets")}
        if p.get("demo") is False:
            info.pop("demo", None)
        out_projects.append({**info, "id": pid, "bullets": [c for c in chosen if c]})

    # experience slots
    out_slots = {}
    overrides = plan.get("experience") or {}
    for slot in overrides:
        if slot not in d_slots:
            fails.append(f"experience slot {slot!r} is not in variant {variant!r} (slots: {sorted(d_slots)})")
    for slot, default_ids in d_slots.items():
        group_ids = groups.get(slot, [])
        entries = overrides.get(slot, default_ids)
        chosen = [resolve_bullet(b, group_ids, f"experience/{slot}") for b in entries]
        out_slots[slot] = [c for c in chosen if c]
        if not out_slots[slot]:
            fails.append(f"experience/{slot}: no bullets left; every position needs at least one")

    # skills: every item must be on one of the user's real skills lists, or
    # appear verbatim in a bullet that is on this resume.
    out_skills = plan.get("skills") or d_skills
    corpus = norm(" ".join(used_text))
    for line in out_skills:
        for item in line.get("items", []):
            n = norm(item)
            if n in inventory or (len(n) >= 3 and n in corpus):
                continue
            fails.append(f"skill {item!r} ({line.get('label')}) is not in skills.md, archive.md, "
                         f"a variant's default_skills, or a bullet on this resume — only list "
                         f"what the user can speak to")

    n_reframes = sum(1 for p in out_projects for b in p["bullets"] if b.get("reframe")) + \
        sum(1 for s in out_slots.values() for b in s if b.get("reframe"))
    used_ids = [b["id"] for p in out_projects for b in p["bullets"]] + \
        [b["id"] for s in out_slots.values() for b in s]
    archive_used = [i for i in used_ids if bullets.get(i, {}).get("archive")]
    archive_skill_items = {norm(x) for l in lib["archive_skills"] for x in l["items"]}
    current = skill_inventory({**lib, "archive_skills": []})
    archive_used += [x for l in out_skills for x in l.get("items", [])
                     if norm(x) in archive_skill_items and norm(x) not in current]
    resolved = {"variant": variant, "src": src, "skills": out_skills,
                "projects": out_projects, "slots": out_slots, "reframes": n_reframes,
                "archive_used": archive_used, "added_experience": additions, "graduation": graduation,
                "name": profile.get("name", ""), "email": email_of(profile)}
    return resolved, fails, warns


# ---------------------------------------------------------------- compose

def bullets_tex(items):
    body = "\n".join(f"  \\item {esc(b['text'])}" for b in items)
    return "\\begin{rBullets}\n" + body + "\n\\end{rBullets}"


def project_head(p):
    title, tech, term = esc(p["title"]), esc(p.get("tech", "")), esc(p.get("term", ""))
    if p.get("link"):
        shown = re.sub(r"^https?://", "", p["link"]).rstrip("/")
        head = f"\\textbf{{{title}" + (f" ({tech})" if tech else "") + "}"
        head += f"\\rSep{{}}\\href{{{esc_url(p['link'])}}}{{\\textit{{{esc(shown)}}}}}"
        if p.get("demo"):
            head += f"\\rSep{{}}\\href{{{esc_url(p['demo'])}}}{{\\textit{{live demo}}}}"
        return head + f" \\hfill \\textit{{{term}}}\\par\n"
    return f"\\rProject{{{title}}}{{{tech}}}{{{esc(p.get('context', ''))}}}{{{term}}}\n"


def compose(r):
    tex = r["src"]
    tex = "\n".join(l for l in tex.splitlines() if not l.startswith("% @"))
    skills = "\n".join(f"\\rSkill{{{esc(l['label'])}}}{{{esc(', '.join(l['items']))}}}"
                       for l in r["skills"])
    projects = "\n".join(project_head(p) + bullets_tex(p["bullets"]) for p in r["projects"])
    # keep a number and its unit on one line (1,500 m, 438 s, 10 GB)
    projects = re.sub(r"(\d) (m|s|ms|min|GB|MB|KB|B)(?=[ ,.;)])", r"\1~\2", projects)
    tex = tex.replace("%%SKILLS%%", skills).replace("%%PROJECTS%%", projects)
    for slot, items in r["slots"].items():
        tex = re.sub(r"%%BULLETS " + re.escape(slot) + r":[^%]*%%",
                     lambda _m, items=items: bullets_tex(items), tex)
    return tex + ("\n" if not tex.endswith("\n") else "")


# ------------------------------------------------------------------ build

def fix_tounicode(pdf_path):
    """Times New Roman draws ';' and U+037E (Greek question mark) with one
    glyph, and XeTeX labels it U+037E, so ATS parsers would read every
    semicolon as a Greek question mark. Relabel it as a real semicolon.
    A no-op for fonts (like TeX Gyre Termes) that keep the two apart."""
    import pikepdf
    with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
        changed = False
        for obj in pdf.objects:
            if isinstance(obj, pikepdf.Dictionary) and obj.get("/Type") == "/Font" \
                    and "/ToUnicode" in obj:
                cmap = obj.ToUnicode.read_bytes()
                fixed = re.sub(rb"<037[Ee]>", b"<003B>", cmap)
                if fixed != cmap:
                    obj.ToUnicode.write(fixed)
                    changed = True
        if changed:
            pdf.save(pdf_path)


def compile_tex(tex, cls_name, jobname, outdir):
    """Compile with xelatex in a temp dir. Returns (pdf_path, log, error)."""
    work = tempfile.mkdtemp(prefix=jobname + "-")
    # copyfile, not copy: copying the mode bits from a read-only skill folder
    # (the Claude app) would make the second compile unable to overwrite it.
    shutil.copyfile(os.path.join(ASSETS, cls_name), os.path.join(work, cls_name))
    fonts = os.path.join(ASSETS, "fonts")
    if os.path.isdir(fonts):  # optional: fonts you add yourself
        shutil.copytree(fonts, os.path.join(work, "fonts"), dirs_exist_ok=True)
    with open(os.path.join(work, jobname + ".tex"), "w", encoding="utf-8") as f:
        f.write(tex)
    proc = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-halt-on-error", jobname + ".tex"],
        cwd=work, capture_output=True, text=True, timeout=120)
    logp = os.path.join(work, jobname + ".log")
    log = open(logp, encoding="latin-1").read() if os.path.exists(logp) else proc.stdout
    pdf = os.path.join(work, jobname + ".pdf")
    if proc.returncode != 0 or not os.path.exists(pdf):
        err = [l for l in log.splitlines() if l.startswith("!")][:3]
        return None, log, "xelatex failed: " + " | ".join(err or ["see log"])
    fix_tounicode(pdf)
    shutil.copy(pdf, os.path.join(outdir, jobname + ".pdf"))
    shutil.copyfile(os.path.join(ASSETS, cls_name), os.path.join(outdir, cls_name))
    return os.path.join(outdir, jobname + ".pdf"), log, None


def compile_pdf(tex, outdir):
    return compile_tex(tex, "resume.cls", "tailored", outdir)


def check_pdf(pdf, r, log):
    fails, warns, info = [], [], {}
    meta = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", meta).group(1))
    info["pages"] = pages
    if pages != 1:
        fails.append(f"resume is {pages} pages; cut the weakest bullet for this posting and rebuild")

    # how far down the page the last line sits
    bbox = subprocess.run(["pdftotext", "-f", "1", "-l", "1", "-bbox", pdf, "-"],
                          capture_output=True, text=True).stdout
    ph = re.search(r'<page width="[\d.]+" height="([\d.]+)"', bbox)
    ymax = [float(y) for y in re.findall(r'yMax="([\d.]+)"', bbox)]
    if ph and ymax:
        info["page_fill_pct"] = round(100 * (max(ymax) - 36) / (float(ph.group(1)) - 72), 1)
        if info["page_fill_pct"] < FILL_MIN:
            warns.append(f"page is only {info['page_fill_pct']}% full, too sparse to stretch evenly; "
                         f"add a bullet or project back and rebuild")

    # Every font must be embedded: a non-embedded font is replaced by
    # whatever the viewer has.
    fonts = subprocess.run(["pdffonts", pdf], capture_output=True, text=True).stdout.splitlines()[2:]
    unembedded = [l.split()[0] for l in fonts if len(l.split()) >= 5 and l.split()[-5] == "no"]
    if unembedded:
        fails.append(f"fonts not embedded (viewers will substitute them): {unembedded}")

    text = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    flat = re.sub(r"\s+", " ", text.replace("-\n", "-"))
    odd = sorted(set(c for c in text if ord(c) > 127 and c not in "\u2013\u2014\u2019\u2018\u201c\u201d\u2022"))
    if odd:
        fails.append(f"PDF text layer has unexpected characters {odd}; ATS parsers will misread them")
    musts = [r["name"], r["graduation"], "EDUCATION"] + ([r["email"]] if r.get("email") else [])
    for must in musts:
        if must and must not in flat:
            fails.append(f"extracted text is missing {must!r}")
    all_b = [b for p in r["projects"] for b in p["bullets"]] + \
            [b for s in r["slots"].values() for b in s]
    missing = []
    for b in all_b:
        head = " ".join(b["text"].split()[:5])
        if norm(head) not in norm(flat):
            missing.append(b["id"])
    if missing:
        fails.append(f"bullets not recoverable from PDF text (ATS risk): {missing}")
    over = len(re.findall(r"Overfull \\hbox", log))
    if over:
        warns.append(f"{over} overfull line(s) in LaTeX log; text may run into the margin")
    info["bullets_used"] = len(all_b)
    return fails, warns, info


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


def cmd_build(args):
    if args.variant:
        plan = {"variant": args.variant}
        if args.graduation:
            plan["graduation"] = args.graduation
    else:
        plan = json.load(open(args.plan, encoding="utf-8"))
    os.makedirs(args.outdir, exist_ok=True)
    r, fails, warns = resolve(plan, args.library)
    summary = {"library": args.library, "variant": plan.get("variant"),
               "graduation": r["graduation"] if r else plan.get("graduation"),
               "added_experience": r["added_experience"] if r else []}
    if r is None or fails:
        summary.update(fails=fails, warns=warns)
        print(json.dumps(summary, indent=1))
        return 1
    tex = compose(r)
    tex_path = os.path.join(args.outdir, "tailored.tex")
    open(tex_path, "w", encoding="utf-8").write(tex)
    pdf, log, err = compile_pdf(tex, args.outdir)
    if err:
        summary.update(tex=tex_path, fails=[err], warns=warns)
        print(json.dumps(summary, indent=1))
        return 1
    f2, w2, info = check_pdf(pdf, r, log)
    # A one-page resume that stops a little short of the bottom margin looks
    # sparse. Recompile in fill mode so the spacing stretches evenly to the
    # bottom. Below FILL_MIN the gaps would get visibly large, so leave it
    # and let the warning prompt adding a bullet instead.
    natural = info.get("page_fill_pct", 100)
    if not args.no_fill and info.get("pages") == 1 and FILL_MIN <= natural < 97:
        filled = tex.replace("\\begin{document}", "\\begin{document}\n\\rFillPage", 1) \
                    .replace("\\end{document}", "\\rEndPage\n\\end{document}", 1)
        pdf2, log2, err2 = compile_pdf(filled, args.outdir)
        if not err2:
            f3, w3, info3 = check_pdf(pdf2, r, log2)
            if not f3 and info3.get("pages") == 1:
                tex, log, f2, w2, info = filled, log2, f3, w3, info3
                open(tex_path, "w", encoding="utf-8").write(tex)
                info["natural_fill_pct"] = natural
            else:
                compile_pdf(tex, args.outdir)  # restore unfilled PDF
    fails += f2
    warns += w2
    company, role = plan.get("company", ""), plan.get("role", "")
    base = f"{r['name']} Resume" + (f" - {company} {role}".rstrip() if company else "")
    named = safe_name(base)
    shutil.copy(pdf, os.path.join(args.outdir, named + ".pdf"))
    shutil.copy(tex_path, os.path.join(args.outdir, named + ".tex"))
    summary.update(
        pdf=os.path.join(args.outdir, named + ".pdf"),
        tex=os.path.join(args.outdir, named + ".tex"),
        pdf_kb=round(os.path.getsize(pdf) / 1024, 1),
        reframes=r["reframes"], archive_used=r["archive_used"], **info, fails=fails, warns=warns)
    print(json.dumps(summary, indent=1))
    return 1 if fails else 0


def cmd_validate(args):
    plan = json.load(open(args.plan, encoding="utf-8"))
    r, fails, warns = resolve(plan, args.library)
    print(json.dumps({"ok": not fails and r is not None, "fails": fails, "warns": warns}, indent=1))
    return 0 if (r is not None and not fails) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("plan", nargs="?")
    b.add_argument("outdir", nargs="?")
    b.add_argument("--variant")
    b.add_argument("--graduation", help="with --variant: render with this expected graduation")
    b.add_argument("--no-fill", action="store_true", help="keep natural spacing even if the page ends short")
    v = sub.add_parser("validate")
    v.add_argument("plan")
    args = ap.parse_args()
    args.library = find_library(args.library)
    if args.cmd == "build":
        if args.variant and args.plan and not args.outdir:
            args.plan, args.outdir = None, args.plan
        if not args.outdir or (not args.plan and not args.variant):
            ap.error("usage: build PLAN.json OUTDIR  |  build --variant swe OUTDIR")
    sys.exit(cmd_build(args) if args.cmd == "build" else cmd_validate(args))


if __name__ == "__main__":
    main()
