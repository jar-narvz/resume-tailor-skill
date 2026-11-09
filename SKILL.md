---
name: resume-tailor
description: "Tailor the user's resume to a job posting as a one-page LaTeX PDF, using only bullets from their own library. Use for a job link, pasted JD, or tailor my resume. Runs setup on first use."
---

# Tailoring a resume to a posting

People applying to many roles need speed: an application submitted in
five minutes at 70% match beats a perfect one submitted in twenty. Aim for
a handful of tool calls: read the posting, write one plan, run one build,
deliver, and summarize.

`SKILL_DIR` below means the directory this SKILL.md is in. Use literal
absolute paths in commands (shell variables don't carry between calls).

## Setup mode comes first

Before anything else, check for `SKILL_DIR/user/profile.yaml`.

- **Missing:** this user hasn't set up their library yet. Tell them in one
  line, then follow `references/setup.md` instead of tailoring. (If they
  only want to see what the skill does, you can tailor with the demo
  library in `examples/`, but say clearly that it's a made-up person.)
- **Present:** tailor as below. The scripts find `user/` on their own.
- **Asked to set up, re-import, or add content:** `references/setup.md`
  (step 7 covers later edits).

## What's in the skill

| Path | What it is |
|---|---|
| `user/profile.yaml` | Header, education, font, and the **variants** (base resumes): section order, experience entries, default bullets, projects and skills |
| `user/bullets.md` | Every bullet the user may put on a resume, each with a stable ID |
| `user/skills.md` | Every skill the user can speak to, by category |
| `user/archive.md` | Bullets and skills from older resumes. Usable by ID, never a default |
| `examples/` | The same four files for Alex Rivera, a made-up person, plus a sample posting, plan and output |
| `assets/resume.cls`, `assets/cover_letter.cls` | Layout: 10pt Times-style serif, 16pt name, 0.5in margins, embedded fonts, ATS-safe text layer |
| `scripts/build_resume.py` | Validates a plan, composes the .tex, runs xelatex, and checks the PDF |
| `scripts/build_cover_letter.py` | Same for a cover letter from a `letter.json` |
| `scripts/validate_library.py` | Checks the library's files and IDs |
| `scripts/render_masters.py` | Writes each variant's master .tex (for reading; builds render in memory) |
| `scripts/package_skill.py` | Zips the skill with the user's library for upload to the Claude app |
| `references/` | `setup.md`, `variants.md`, `reframe-rules.md`, `cover-letter.md` |

## The one rule

**Tailoring selects and reorders. It never writes new claims.** Every
bullet is a library or archive ID used verbatim, or a reframe of one,
which may only reorder clauses, swap the leading verb, or trim. Every
skill must already be in `skills.md`, `archive.md`, a variant's
`default_skills`, or a bullet on the page. The build enforces all of this
and fails loudly, on purpose. Fabricated bullets and padded skills are the
main way resume tailoring goes wrong, and the user has to defend every
line in an interview. When the posting wants something they don't have,
report it as a gap instead of working around the check. The same rule
covers the keyword list in step 6: a skill typed into an application
portal is a claim just like a resume line.

## Workflow

### 0. Optional: sync from a Google Doc master

Skip this step unless `profile.yaml` has a non-empty `drive_masters` list
(Google Doc IDs or titles the user edits as their master resume) and a
Google Drive connector is available. Then, once per run:

1. Fetch each doc's metadata. If none was modified since the library's
   files were last changed, move on.
2. If one was, read it and compare it with the library: new bullets,
   changed skills lines, a new position or project, changed dates.
3. Show the user the differences and offer to add them (new bullets get
   fresh IDs; see `references/setup.md` step 7). Don't use unconfirmed
   content in this run.

If Drive isn't connected or the call fails, say so in one line and
continue with the library as it is.

### 1. Read the posting

If they pasted the JD, use it. For a screenshot, read it directly. For a
URL, go through these in order and stop at the first that gives the real
description. A fetch has failed if it returns an empty shell, a login or
cookie wall, a "job not found" page, or under ~500 characters of body
text. Try every step before asking them to paste the JD.

1. **Fetch the URL they gave.** This works for most Greenhouse and Lever
   pages and many company pages.
2. **If that's thin, fetch the board's public JSON API.** Some boards
   build the page with JavaScript but serve the same posting as JSON:

   | Board | Posting URL looks like | Fetch this instead |
   |---|---|---|
   | Greenhouse | `job-boards.greenhouse.io/<board>/jobs/<id>` or `boards.greenhouse.io/<board>/jobs/<id>` | `https://boards-api.greenhouse.io/v1/boards/<board>/jobs/<id>` |
   | Ashby | `jobs.ashbyhq.com/<board>/<id>` | `https://api.ashbyhq.com/posting-api/job-board/<board>` (lists every open job; find the one whose `id` is `<id>`; if it's missing, the posting is closed) |
   | Workday | `<tenant>.wdN.myworkdayjobs.com/<lang>/<site>/job/<loc>/<slug>` | `https://<tenant>.wdN.myworkdayjobs.com/wday/cxs/<tenant>/<site>/job/<loc>/<slug>` (drop the `<lang>` segment) |
   | Lever | `jobs.lever.co/<company>/<id>` | `https://api.lever.co/v0/postings/<company>/<id>` |
   | SmartRecruiters | `jobs.smartrecruiters.com/<company>/<id>` | `https://api.smartrecruiters.com/v1/companies/<company>/postings/<id>` |

   A company page with only `gh_jid=<id>` is embedded Greenhouse: try the
   company name as `<board>` once, then move on.
3. **Still nothing?** Search the web for the exact title and company and
   fetch a copy of the listing (another board, LinkedIn, an aggregator).
   Say in the summary that the JD came from a copy.
4. **A browser, if this session has one.** Read only: no sign-in, forms
   or Apply. If nothing works, ask them to paste the JD.

Note only what you need:
- The 3–5 requirements stated first or repeated most
- Exact technology names and skill phrases in the posting's casing
  (`PostgreSQL`, `PyTorch`, `REST APIs`). These feed the plan and the
  keyword list in step 6.
- Whether a cover letter is required

Don't screen the user out on eligibility (graduation window, location,
"returning to school") unless they've asked you to. Just tailor.

### 2. Pick the variant and read the library

Read `user/profile.yaml` and pick the variant whose `use_for` best
matches the posting (`references/variants.md` has the tie-breakers).
Then read `user/bullets.md` end to end once; you'll pick bullets by ID
from it. Read `user/skills.md` for the skill inventory.

Only if the posting asks for something the current bullets and skills
don't cover well, read `user/archive.md` too. Use an archive item when it
clearly fits better than its current counterpart; otherwise prefer the
current wording, since it's the one the user most recently chose. Never
put two versions of the same bullet on one page.

### 3. Write the plan

Write `resume-work/plan.json` in the working directory (see
`examples/sample-plan.json` for a full one):

```json
{
  "variant": "swe",
  "company": "Globex Logistics",
  "role": "Backend Software Engineer Intern",
  "skills": [
    {"label": "Languages", "items": ["Go", "Python", "SQL", "Java"]},
    {"label": "Frameworks & Tools", "items": ["PostgreSQL", "Docker", "GitHub Actions"]},
    {"label": "Concepts", "items": ["REST APIs", "Distributed Systems", "CI/CD"]}
  ],
  "projects": [
    {"id": "proj-kv", "bullets": ["kv-1", "kv-2", "kv-3"]},
    {"id": "proj-chat"}
  ],
  "experience": {
    "acme": [{"reframe_of": "acme-1", "text": "Built a Python service that batches inventory updates into PostgreSQL from 40+ warehouses, cutting nightly sync time from 3 hours to 25 minutes."},
             "acme-2", "acme-4"]
  }
}
```

- Leave out `skills`, `projects`, or `experience` to keep the variant's
  defaults. A project with no `bullets` uses a variant's default bullets
  for it, or all its library bullets if no variant lists it.
- `projects` replaces the whole list, so include every project you want,
  in order. Any project can go on any variant.
- `"demo": false` on a project drops its "live demo" header link.
- `experience` refills a slot (the `slot` names in `profile.yaml`) with
  other bullets from the same position.
- `"graduation": "<date>"` picks one of `education[0].alt_graduations`.
- Skill items may use the posting's casing; matching ignores case and
  punctuation.

Spend effort in the order a recruiter's attention decays:
1. **Project order.** Put the best-matching project first. This is the
   highest-leverage edit and costs no space.
2. **Skills lines.** Put the posting's stack first in each line. Drop
   items that are noise for this role so the matches stand out.
3. **The leading project's first bullet.** Choose the bullet, or a
   reframe per `references/reframe-rules.md`, that puts the posting's
   core technology in the first half of the line.
4. **Everything else.** Usually leave it alone. Swap an experience bullet
   only when a sibling bullet from the same position clearly fits better.

### 4. Build

```bash
python3 /abs/path/to/SKILL_DIR/scripts/build_resume.py build resume-work/plan.json resume-work/out
```

The script validates the plan, composes the .tex, runs xelatex, and
checks the result: one page, all fonts embedded, text extractable by ATS
parsers, every bullet recoverable from the PDF text, and the name, email,
graduation date and EDUCATION heading present. It prints a short JSON
summary and exits 1 on any failure. (`--library DIR` before `build`
points it at a library other than `user/`.)

- **A validation fail** names the exact bullet, reframe, or skill. Fix the
  plan; don't fight the check. A rejected reframe usually means you added
  a word the user never wrote, so use the original bullet. A rejected
  skill means they don't list it, so it goes under gaps in the summary.
- **Two pages:** drop the weakest bullet for this posting and rebuild.
  Never touch margins, font size, or the .cls.
- **Fill the page with content first, spacing second.** If the build
  warns the page is under ~93% full, add back the next-best bullet and
  rebuild: bullets trimmed from a project already on the page, then
  sibling experience bullets, then another project. The script closes the
  last few percent itself by evenly stretching section and bullet spacing
  (`natural_fill_pct` shows where the content ended). It won't stretch
  sparse pages, because large gaps look like padding.

Don't deliver anything from a failed build.

### 5. Deliver

The build writes the named `.pdf` and `.tex` into the out directory (the
summary's `pdf` and `tex` fields). Send both to the user, PDF first, with
whatever file-delivery tool this environment has (in Claude Code, just
give the paths). The PDF is what they upload to portals.

Don't paste the PDF or .tex contents into the conversation; the files are
the delivery. Always deliver the PDF the build made. Recompiling the .tex
by hand (or in Overleaf) skips the build's text-layer fix and checks.

### 6. Summarize, then give the keywords to paste

First, three or four lines:

- Which variant you started from and why.
- The two or three most consequential changes (project order, skills
  order, any reframe).
- Anything from the archive (the summary's `archive_used`), so they can
  confirm it's still accurate. Skip this line if it's empty.
- **Gaps:** posting keywords they do **not** cover, stated plainly. These
  tell them what to prep for the interview or address in a cover letter.

Then a **Keywords to paste** list for portals' skills fields: one fenced
code block, a single comma-separated line, so the chat shows a copy
button:

```
Go, Python, PostgreSQL, SQL, REST APIs, Distributed Systems, Docker, CI/CD, GitHub Actions
```

- **Only things they actually have**: items on the tailored skills lines,
  anywhere in `skills.md` / `archive.md`, or a technology named in a
  bullet on the page. Anything they lack stays on the gaps line.
- **The posting's wording when it matches their item** ("PostgreSQL" for
  their "Postgres"), but never stretch into a different skill ("SQL" does
  not become "PostgreSQL").
- **Ordered by what the posting cares about**, roughly 10–20 items, no
  near-duplicates, no labels or line breaks inside the block.

### 7. Cover letter, only when warranted

Write one if they ask, if the application requires it, or if something
specific makes it worth it (a referral, a mission they have a real tie
to, a gap a paragraph explains better than a bullet). If you skip it, say
so in one line so they can overrule you.

Follow `references/cover-letter.md`, write `letter-work/letter.json`, and
build:

```bash
python3 /abs/path/to/SKILL_DIR/scripts/build_cover_letter.py letter-work/letter.json letter-work/out
```

It checks one page, embedded fonts, a clean text layer, and the contact
details. Deliver the named PDF and .tex the same way (PDF first). In the
summary, name any sentence that states their interest or motivation so
they can confirm it's true for them.

## Revisions

Edit `plan.json` and rerun `build`. Never hand-edit the generated `.tex`,
because the next build would silently drop the change. If the skills
change, update the keyword block to match.

## Maintaining the library

- **New experience or a reworded bullet:** draft the entry with a fresh
  ID and confirm the wording with the user, then add it per
  `references/setup.md` step 7. Don't put unconfirmed content on a resume
  in the meantime.
- **Style changes** (font, spacing, section look) belong in
  `assets/resume.cls` and are their own conversation, never part of a
  tailoring turn. After any change to it, rebuild a base and check that
  each `\href` is still its own link in the PDF.
- `build --variant <v> OUTDIR` renders a base untouched. It's a quick
  check that the pipeline works in this environment.
