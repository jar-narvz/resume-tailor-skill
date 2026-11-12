"""Shared loaders for the resume library: profile.yaml, bullets.md,
archive.md and skills.md, plus LaTeX escaping.

A library is a folder holding those files (archive.md is optional).
The skill prefers the Claude Project library over `user/` inside the
skill folder, then falls back to `examples/` with a warning.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.normpath(os.path.join(HERE, ".."))
ASSETS = os.path.join(SKILL_DIR, "assets")
TEMPLATES = os.path.join(SKILL_DIR, "templates")
USER_DIR = os.path.join(SKILL_DIR, "user")
EXAMPLES_DIR = os.path.join(SKILL_DIR, "examples")
PROJECT_DIR = "/mnt/project"

FONTS = ("termes", "times-system")
SECTIONS = ("education", "experience", "projects", "skills")


def find_library(explicit=None, quiet=False):
    """Return explicit > Project > user/ > examples/; warn on shadowing or demo use."""
    if explicit:
        if not os.path.exists(os.path.join(explicit, "profile.yaml")):
            raise SystemExit(f"no profile.yaml in {explicit}")
        return explicit
    project = os.environ.get("RESUME_TAILOR_PROJECT_DIR", PROJECT_DIR)
    if os.path.exists(os.path.join(project, "profile.yaml")):
        missing = [name for name in ("bullets.md", "skills.md")
                   if not os.path.isfile(os.path.join(project, name))]
        if missing:
            raise SystemExit(f"incomplete Project library in {project}: missing "
                             f"{', '.join(missing)}. Add them to the Project's Context.")
        if not quiet and os.path.exists(os.path.join(USER_DIR, "profile.yaml")):
            print(f"WARNING: using Project library {project} instead of {USER_DIR}; "
                  "both have profile.yaml.", file=sys.stderr)
        return project
    if os.path.exists(os.path.join(USER_DIR, "profile.yaml")):
        return USER_DIR
    if not quiet:
        print("WARNING: no user/profile.yaml yet, so this is using the examples/ demo "
              "library (Alex Rivera, a made-up person). Run first-time setup "
              "(references/setup.md) to build your own.", file=sys.stderr)
    return EXAMPLES_DIR


# ------------------------------------------------------------------ profile

def load_profile(library):
    import yaml
    path = os.path.join(library, "profile.yaml")
    with open(path, encoding="utf-8") as f:
        p = yaml.safe_load(f) or {}
    edu = p.get("education")
    if isinstance(edu, dict):  # allow a single school without a list
        p["education"] = [edu]
    p.setdefault("font", "termes")
    p.setdefault("contact", [])
    p.setdefault("variants", {})
    return p


def email_of(profile):
    for c in profile.get("contact", []):
        if "@" in str(c.get("label", "")):
            return str(c["label"])
    return None


def graduations(profile):
    """(default, [all allowed]) graduation strings from the first school."""
    edu = (profile.get("education") or [{}])[0]
    g = str(edu.get("graduation", "")).strip()
    alts = [str(x) for x in edu.get("alt_graduations") or []]
    return g, [g] + [a for a in alts if a != g]


# ------------------------------------------------------------------ escaping

TEX_ESC = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
           "\\": r"\textbackslash{}"}


def esc(s):
    """Escape LaTeX specials in plain text from the library."""
    s = "".join(TEX_ESC.get(ch, ch) for ch in str(s))
    s = s.replace("’", "'")
    # number ranges like 5-10% or 16-20 read better with an en dash
    return re.sub(r"(?<=\d)-(?=\d)", "--", s)


def esc_text(s):
    """Escape profile text that may already use LaTeX dashes (`--`)."""
    s = "".join(TEX_ESC.get(ch, ch) for ch in str(s))
    return s.replace("’", "'").replace("–", "--").replace("—", "---")


def esc_url(u):
    return str(u).replace("\\", "").replace("%", r"\%").replace("#", r"\#").replace("{", "").replace("}", "")


# ------------------------------------------------------------------ bullets

def group_of(bullet_id):
    """Experience slot a bullet belongs to: its ID minus the trailing number
    (acme-3 -> acme, acme-a2 -> acme, acme-3s -> acme)."""
    return re.sub(r"-a?\d+[a-z]?$", "", bullet_id)


def parse_bullets(path):
    """Return (bullets, projects, groups).

    bullets:  id -> {"text", "group"}
    projects: pid -> {"title", "tech", "term", "bullets": [ids], optional link/demo/context}
    groups:   slot -> [ids]  (experience positions, keyed by id prefix)
    """
    bullets, projects, groups = {}, {}, {}
    cur_project = None
    cur_id = None
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for n, line in enumerate(lines, 1):
        if line.startswith("## "):
            cur_project = None
            cur_id = None
            continue
        m = re.match(r"^### project:(\S+)\s+[—-]+\s+(.*?)\s*(\[[^\]]*\])?\s*$", line)
        if m:
            pid, rest = m.group(1), m.group(2)
            term = ""
            if "," in rest:
                rest, term = rest.rsplit(",", 1)
            rest, term = rest.strip(), term.strip()
            tm = re.match(r"^(.*)\(([^()]*)\)\s*$", rest)
            title, tech = (tm.group(1).strip(), tm.group(2).strip()) if tm else (rest, "")
            if pid in projects:
                raise SystemExit(f"{path}:{n}: project id {pid!r} appears twice")
            projects[pid] = {"title": title, "tech": tech, "term": term, "bullets": []}
            cur_project, cur_id = pid, None
            continue
        km = re.match(r"^(link|demo|context):\s*(.+?)\s*$", line)
        if km and cur_project and cur_id is None:
            projects[cur_project][km.group(1)] = km.group(2)
            continue
        m = re.match(r"^### (\S+)(\s+\[[^\]]*\])?\s*$", line)
        if m:
            cur_id = m.group(1)
            if cur_id in bullets:
                raise SystemExit(f"{path}:{n}: bullet id {cur_id!r} appears twice")
            group = cur_project or group_of(cur_id)
            bullets[cur_id] = {"text": "", "group": group}
            if cur_project:
                projects[cur_project]["bullets"].append(cur_id)
            else:
                groups.setdefault(group, []).append(cur_id)
            continue
        if cur_id and line.strip():
            b = bullets[cur_id]
            b["text"] = (b["text"] + " " + line.strip()).strip()
        elif cur_id and not line.strip() and bullets[cur_id]["text"]:
            cur_id = None
    return bullets, projects, groups


def parse_archive(path, bullets, projects, groups):
    """Merge archive.md into the parsed library. Archive bullets are allowed
    in a plan but never used as defaults. Returns (skills lines, archive ids)."""
    skills, archive_ids = [], []
    if not os.path.exists(path):
        return skills, archive_ids
    cur_project, cur_id = None, None
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        m = re.match(r"^@skills (.+?):\s*(.+)$", line)
        if m:
            skills.append({"label": m.group(1).strip(), "items": split_items(m.group(2))})
            continue
        if line.startswith("## "):
            cur_project, cur_id = None, None
            continue
        m = re.match(r"^### project\+:(\S+)\s*$", line)
        if m:
            cur_project, cur_id = m.group(1), None
            if cur_project not in projects:
                raise SystemExit(f"archive.md: project+:{cur_project} is not in bullets.md")
            projects[cur_project].setdefault("archive", [])
            continue
        m = re.match(r"^### (\S+)(\s+\[[^\]]*\])?\s*$", line)
        if m:
            cur_id = m.group(1)
            if cur_id in bullets:
                raise SystemExit(f"archive.md: id {cur_id!r} already exists in bullets.md")
            group = cur_project or group_of(cur_id)
            bullets[cur_id] = {"text": "", "group": group, "archive": True}
            archive_ids.append(cur_id)
            if cur_project:
                projects[cur_project]["archive"].append(cur_id)
            else:
                groups.setdefault(group, []).append(cur_id)
            continue
        if cur_id and line.strip():
            b = bullets[cur_id]
            b["text"] = (b["text"] + " " + line.strip()).strip()
        elif cur_id and not line.strip() and bullets[cur_id]["text"]:
            cur_id = None
    return skills, archive_ids


def parse_skills(path):
    """skills.md: `## Category` then `- item` lines. Returns [{label, items}]."""
    out = []
    if not os.path.exists(path):
        return out
    cur = None
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            if line.startswith("## "):
                cur = {"label": line[3:].strip(), "items": []}
                out.append(cur)
            elif cur is not None and re.match(r"^\s*[-*]\s+\S", line):
                cur["items"].append(re.sub(r"^\s*[-*]\s+", "", line).strip())
    return out


def split_items(s):
    """Split a skills line on top-level commas (keeps 'RL (A, B)' together)."""
    items, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            items.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        items.append(cur.strip())
    return items


def norm(s):
    return re.sub(r"[^a-z0-9+#]", "", str(s).lower())


def load_library(library):
    """Everything a build needs. Returns a dict."""
    profile = load_profile(library)
    bullets, projects, groups = parse_bullets(os.path.join(library, "bullets.md"))
    archive_skills, archive_ids = parse_archive(os.path.join(library, "archive.md"),
                                                bullets, projects, groups)
    skills_md = parse_skills(os.path.join(library, "skills.md"))
    return {"profile": profile, "bullets": bullets, "projects": projects, "groups": groups,
            "archive_skills": archive_skills, "archive_ids": archive_ids, "skills_md": skills_md}
