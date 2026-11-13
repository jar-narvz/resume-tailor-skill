# PLAN.md

Source of truth for remaining work. Only Claude edits this file. Status
lives in PROGRESS.md.

## Where the project is

The skill works end to end in Claude Code and the Claude app (paid and
free accounts): setup, polish with approval, packaging, and tailoring were
tested by hand on 2026-11-12. Steps 1-3 are done. What's left before
publishing: three loopholes in the claim checks (step 4), automated tests
and CI (step 5), and the public release (step 6).

## Steps

### Step 1 — Let a plan add an older position

**Need.** A posting sometimes calls for a job that the chosen base resume
doesn't show (a data internship for a data role, when the user keeps one
software variant). Today a plan can't add a position, so setup has to
either make a whole variant for it or drop the job. In testing, setup
dropped a real internship from the library for this reason.

**Design.**

- **Position pool.** A new optional top-level `extra_experience:` list in
  `profile.yaml`, same keys as a variant's experience entry (`slot`,
  `title`, `dates`, `org`, `org_url`, `location`, `default_bullets`).
  These positions are on no variant by default. Their bullets live in
  `bullets.md` like any other experience bullets (ID prefix = slot).
  *Why a separate list instead of "any variant's positions":* one place
  for the header facts of a position no variant shows, and the validator
  can keep slots unique.
- **Plan key `add_experience`:** a list of slots from `extra_experience`
  *or from another variant's experience*, added after the variant's own
  positions, in list order. Bullets come from the existing `experience`
  override (`"experience": {"harbor": ["harbor-2"]}`) or else the entry's
  `default_bullets`. *Why a separate key instead of letting `experience`
  name any slot:* the current "slot not in variant" failure catches typos;
  adding a position should be a deliberate act the summary can report.
  Lookup: `extra_experience` first, then variants in profile order; the
  first matching entry supplies both the header and the default bullets.
- **Rendering.** Build a *copy* of the chosen variant with the added
  entries appended to its `experience` list, and render the master from
  that copy, so headers and bullet placeholders exist for the added
  positions. Never mutate the loaded profile (other variants' defaults are
  read from it). If the variant's experience list was empty, the added
  positions still render an Experience section.
- **Build fails** (exit 1, clear message, no traceback) on:
  `add_experience` that isn't a list of unique strings; an unknown slot;
  a slot the variant already shows; a variant whose effective section
  order (omitted `section_order` = all sections) has no `experience`; an
  added position left with no bullets; a bullet from another slot; and,
  unchanged, an `experience` override naming a slot that's neither in the
  variant nor in `add_experience`.
- **Summary** gains `"added_experience": [slots]`, and SKILL.md tells
  Claude to mention any added position in its summary, as it does for
  archive items.
- **Validator** checks `extra_experience` entries like variant entries
  (required keys, default bullets exist and belong to the slot), counts
  their slots as known (so their bullet prefixes are legal), and fails on
  a duplicate slot within `extra_experience` or one that's also a slot in
  any variant. The same slot in several variants stays legal, as now.
  Archive bullets stay forbidden as defaults, including here.
- **Docs:** plan shape in `build_resume.py`'s docstring and SKILL.md;
  `references/variants.md` (currently says a plan can't add a position);
  `references/setup.md` step 2 (an old-only position goes in
  `extra_experience`, replacing "a whole position can't be archived");
  README Limitations (drop "Old positions need a variant").
- **Example:** add one `extra_experience` position with two bullets to
  the Alex Rivera library (`examples/profile.yaml`, `examples/bullets.md`).
  Default builds must not change.

**Non-goals.** Reordering positions within the section; a plan removing
one of the variant's positions; a plan editing a title or dates; changes
to `archive.md` parsing.

**Files.** `tests/test_add_experience.py` (new), `scripts/build_resume.py`, `scripts/render_masters.py` (only
if needed to render the extra entries), `scripts/validate_library.py`,
`examples/profile.yaml`, `examples/bullets.md`, `SKILL.md`,
`references/variants.md`, `references/setup.md`, `README.md`.

**Tests.** `tests/test_add_experience.py`, stdlib `unittest` (no new
dependency; pytest runs unittest tests, so step 3 can adopt it as is).
Libraries for negative cases are built in temp dirs from a copy of
`examples/`. Cover:

- plan validation (`resolve()`, no LaTeX): added position with default
  bullets; with an explicit `experience` override; empty override
  (fails); wrong-slot bullet (fails); duplicate / non-list / non-string
  `add_experience` (fail); unknown slot (fails); slot already in the
  variant (fails); override for an extra slot not in `add_experience`
  (fails); adding a slot that two other variants define (uses the first);
  a variant with no experience entries renders the added position; a
  variant whose `section_order` lacks experience (fails); a library with
  no `extra_experience` (unchanged behavior).
- validator: duplicate extra slot, extra slot also in a variant, missing
  required key, missing default bullet, wrong-slot default, archive bullet
  as default (each fails); the example library passes.
- one end-to-end build (skip if `xelatex` isn't on PATH): variant `swe`,
  add the example's extra position, projects limited to `proj-kv` and
  `proj-chat` so it fits one page; assert `"fails": []`, `"pages": 1`,
  `"added_experience"` lists the slot, and `pdftotext` output contains the
  position's title and both bullets.

**Verify.**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_library.py examples
for v in swe ml; do python3 scripts/build_resume.py --library examples build --variant $v out/after-$v >/dev/null; diff out/baseline-$v/tailored.tex out/after-$v/tailored.tex && echo "$v unchanged"; done
python3 scripts/build_resume.py --library examples build examples/sample-plan.json out/v1
```
Expected: all tests pass; validator `ok`; `swe unchanged` and `ml
unchanged` (baselines in `out/baseline-*` were built before the change);
sample build `"fails": []`, `"pages": 1`, `"bullets_used": 19`.

### Step 2 — Clean header in the tailored .tex

**Need.** The tailored `.tex` users receive starts with the master
template's comment ("master_swe.tex … Don't edit this file"). It names the
wrong file, and editing a delivered `.tex` is fine.

**Design.** `compose()` in `build_resume.py` drops the master's leading
`%` comment lines and starts the file with one line:
`% <Name> resume, tailored for <Company> (<Role>), built <YYYY-MM-DD> by resume-tailor`,
or for `build --variant` (no company): `% <Name> resume, <variant> base, built <YYYY-MM-DD> by resume-tailor`.
Masters written by `render_masters.py` keep their current header (they
are masters). Only comments change, so the PDF text is identical.

- `resolve()` carries the plan's `company` and `role` into the resolved
  dict; `compose()` builds the line from it. Both are optional: company
  and role → "tailored for Acme (Intern)"; one of them → "tailored for
  Acme" / "tailored for Intern"; neither (or `--variant`) → the base line.
- Collapse all whitespace (including CR/LF) in interpolated values to
  single spaces, so the header is always exactly one comment line.
- The date comes from a parameter defaulting to today, so tests can pin
  it.

**Files.** `scripts/build_resume.py`, `tests/test_tex_header.py` (new).

**Verify.**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_resume.py --library examples build examples/sample-plan.json out/v2
head -2 out/v2/tailored.tex
for v in swe ml; do python3 scripts/build_resume.py --library examples build --variant $v out/after2-$v >/dev/null; diff <(grep -v '^%' out/baseline-$v/tailored.tex) <(grep -v '^%' out/after2-$v/tailored.tex) && echo "$v body unchanged"; done
pdftotext out/v2/tailored.pdf - | diff out/baseline-sample/text.txt - && echo "sample text unchanged"
```
Expected: tests pass (new: all four company/role combinations and the
variant line with a pinned date, CR/LF collapsed, no `master_` or "Don't
edit"); `head` shows the new line naming Globex Logistics; `swe body
unchanged`, `ml body unchanged`, `sample text unchanged` (baseline in
`out/baseline-sample/text.txt`, built before the change); sample build
`"fails": []`, `"pages": 1`, `"bullets_used": 19`.

### Step 3 — Keep the library in a Claude Project (app alternative to the zip)

**Need.** In the Claude app, every library change means re-uploading the
whole skill zip. Users who tailor in one place want to update their
library by replacing a file.

**Evidence (2026-11-12, free account).** Four library files added to a
Project's Context appear in every chat in that Project as real, read-only
files in `/mnt/project/` (flat, original names, byte sizes identical to
the source files). The installed skill sits at
`/mnt/skills/plugins/resume-tailor`. Chat uploads go to
`/mnt/user-data/uploads` and don't persist.

**Design.**

- **Lookup in code, not just instructions.** `library.find_library()`
  becomes: explicit `--library` > `/mnt/project` (if it has
  `profile.yaml`) > `user/` in the skill folder > `examples/` (warning).
  *Why code:* every script then finds the Project library with no flag,
  the same way it finds `user/`, and the JSON summary's `"library"` shows
  which one was used. *Why the Project first:* opening a chat inside that
  Project is a deliberate, per-chat choice, and its files are the ones the
  user edits. If both exist, print a one-line warning naming both. The
  Project path is a module constant overridable by an environment
  variable (`RESUME_TAILOR_PROJECT_DIR`) so tests can point it at a temp
  dir.
- **Incomplete Project library.** If the Project dir has `profile.yaml`
  but is missing `bullets.md` or `skills.md` (`archive.md` is optional),
  stop with a clear error naming the missing files and saying to add them
  to the Project's Context. Never fall back to another library or mix
  sources silently.
- **One library path everywhere in SKILL.md.** Define `LIBRARY` once
  (`/mnt/project` when it has `profile.yaml`, else `SKILL_DIR/user`) and
  use it for every file the instructions read (profile, bullets, skills,
  archive), so Claude picks IDs from the same files the build uses.
- **SKILL.md setup gate** checks both places (`user/profile.yaml` or
  `/mnt/project/profile.yaml`) before deciding setup is needed.
- **Setup step 7 (Claude app)** offers both: (a) **Project**: send the four
  files to download and say "add these to your Project's Context, then
  tailor in chats inside that Project"; (b) **zip**: as now, works in every
  chat. One line each on the trade-off; recommend the Project if they
  tailor in one place.
- **Step 8 (later edits), Project users:** `/mnt/project` is read-only,
  so copy it to `resume-work/user/`, edit there, run
  `validate_library.py resume-work/user` and a base build with
  `--library resume-work/user`, then send only the changed file(s) to
  replace in Context. Zip users get a new zip, as now.
- **README:** "Where your library lives" gets the Project option and the
  trade-off; Limitations line updated.

**Non-goals.** Writing to `/mnt/project` (it's read-only); syncing a
Project library with a zip library; Project instructions text.

**Files.** `scripts/library.py`, `tests/test_find_library.py` (new),
`SKILL.md`, `references/setup.md`, `README.md`.

**Verify.**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_resume.py --library examples build examples/sample-plan.json out/v3
```
Expected: all tests pass, including new ones for: lookup order (Project
dir used when it has `profile.yaml`; `user/` when it doesn't; explicit
`--library` wins over both; warning when both exist; `examples/` fallback
with its warning); an incomplete Project dir fails with the missing file
names; a build from a read-only Project dir (temp dir with write
permission removed) succeeds and reports it as `"library"`. Sample build
unchanged (`"fails": []`, `"pages": 1`, `"bullets_used": 19`).
Then by hand in the Claude app: in the test Project, a new chat tailors
to a posting without running setup, and the summary's `"library"` is
`/mnt/project`.

### Step 4 — Close three loopholes in the claim checks

**Need.** While planning tests, Codex found three ways a plan can make a
claim the user never wrote, and all three pass the build today
(reproduced 2026-11-12):

1. `check_reframe("Built a service", "Led a service")` returns no
   problems. "Led" claims leadership the original didn't. The swap list
   includes Led/Managed, and a listed verb is allowed anywhere in the
   text, not only as the first word.
2. `"... from 3 hours to 25 minutes"` → `"... from 25 hours to 3
   minutes"` passes, because `numbers()` compares sorted lists, so the
   same numbers attached to different things look unchanged.
3. Listing the skill `Script` passes when a bullet on the page says
   `TypeScript`. `norm()` removes spaces and punctuation, so the
   "appears in a bullet on this resume" check is a substring match with
   no word boundaries.

**Design.**

- **Verb swap: first word only, and no promotion.** A word from the swap
  list that isn't in the original is allowed only as the reframe's first
  word. The free swap set is the build verbs (built, designed, developed,
  engineered, implemented, created, wrote, maintained, plus their present
  forms). Led/lead/managed/manage count as swaps only if the original
  already has a leadership stem (led, lead, manag-). *Why:* swapping
  "Built" for "Developed" is wording; swapping it for "Led" is a new claim
  about the role.
- **Numbers keep their meaning.** Compare numbers as `(number, next
  word)` pairs (next word = the token right after the number, or empty at
  the end), as a sorted list. *Why pairs and not exact order:* reordering
  clauses legitimately moves numbers ("into PostgreSQL from 40+
  warehouses"), but the word after a number is what it measures, so a
  swap like "25 hours" breaks the pairing. Side effect: trimming the word
  right after a number ("6 REST endpoints" → "6 endpoints") is now
  rejected. That's a safe failure, because Claude can use the original
  bullet instead, and the rules doc will say so.
- **Skills from bullets match whole words.** The "appears in a bullet on
  this resume" check matches the skill's tokens as a contiguous run of
  whole tokens in the selected bullets (lowercase, split on anything
  other than letters, digits, `+` and `#`). So "Node.js" matches
  "Node.js" and "REST APIs" matches "REST APIs", but "Script" doesn't
  match "TypeScript". The inventory check (`skills.md`, archive, variant
  defaults) is unchanged.
- **Docs:** `references/reframe-rules.md` (verb rule, number rule,
  trimming next to a number), plus one phrase each in `SKILL.md:78` and
  the README "Verbatim validation" paragraph if their wording no longer
  matches.

**Tests** (in a new `tests/test_reframe.py`, plus a skill case in a new
`tests/test_plan_validation.py`, so step 5 extends these files):

- Rejected: Built→Led, Built→Managed, a swap-list verb inserted mid-text,
  a number/unit swap, a changed number, an added number, a new stem, and
  growth over 3 words.
- Allowed: Built→Developed as the first word, Led→Built, Led kept when
  the original says Led, clause reorder (the sample plan's `acme-1`
  reframe), a trim, a plural/tense change, and exactly 3 added connectors.
- Skills: `Script` with only a TypeScript bullet on the page fails;
  `Node.js` taken from a selected bullet passes.

**Non-goals.** Fixing false rejections from the simple stemmer (`Used
services` → `Use service` is rejected); those fail safe. Changing the
PDF bullet-recovery check (it checks the first five words of text the
build composed itself, so a plan can't truncate a bullet through it).

**Files.** `scripts/build_resume.py`, `references/reframe-rules.md`,
`SKILL.md`, `README.md`, `tests/test_reframe.py` (new),
`tests/test_plan_validation.py` (new).

**Verify.**

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_resume.py --library examples build examples/sample-plan.json out/v4
python3 scripts/build_resume.py --library examples validate examples/sample-plan.json
```
Expected: all tests pass, including the cases above. The sample build is
unchanged: `"fails": []`, `"pages": 1`, `"bullets_used": 19`,
`"reframes": 1`. The three probes from **Need** now return problems.

### Step 5 — Automated tests and CI

**Need.** The skill's main promise ("a tailored resume can never claim
more than you wrote") is enforced in code: `check_reframe`, the plan
checks in `resolve()`, and the PDF checks in `check_pdf()`. Right now only
the newest features (older positions, the .tex header, library lookup)
have tests. A recruiter or contributor reading the repo can't see that
the core rules hold, and a future change could weaken one without anyone
noticing.

**Design.**

- **Stay on stdlib `unittest`, not pytest.** *Why:* the existing tests
  are unittest, so nothing has to be rewritten, and CI and a user's
  machine need no extra install. The old note here said pytest; this
  replaces it.
- **Extend step 4's two files and add three more, each about one rule
  set.** Library fixtures are temp copies of `examples/`, the same style
  as `test_add_experience.py`.
  - `tests/test_reframe.py` (from step 4): add any `check_reframe` cases
    step 4 didn't cover. No library and no LaTeX, so these run in
    milliseconds.
  - `tests/test_plan_validation.py` (from step 4) calls `resolve()`.
    Each case asserts that a specific message appears in `fails`:
    - unknown variant, and a graduation date not in `alt_graduations`
    - an unknown bullet ID, a bullet from another slot or project, and the
      same bullet twice in one project
    - `reframe_of` an unknown ID, `reframe_of` from the wrong slot, and a
      rejected reframe text (shows the rules are wired into the plan, not
      just the function)
    - a bullet entry that's neither a string nor `{reframe_of, text}`
    - an unknown project, and an experience override for a slot the
      variant doesn't have
    - an empty experience override ("every position needs at least one")
    - Skills, rejected: an item not in the inventory; a term that appears
      only in a bullet that isn't on the page.
    - Skills, allowed: an item in another variant's `default_skills`; the
      inner term of a parenthesized inventory item (`Raft` from
      `Consensus (Raft)`); and an archive-only skill (`Tableau`), with
      `archive_used` equal to exactly `["Tableau"]`.
    - The unchanged `examples/sample-plan.json` has no fails.
    - `add_experience` failures are already covered by
      `test_add_experience.py`, so they aren't repeated.
  - `tests/test_check_pdf.py` covers each `check_pdf` rejection with
    canned `pdfinfo` / `pdffonts` / `pdftotext` output (via
    `unittest.mock.patch` on `subprocess.run`), so no LaTeX is needed:
    2 pages, an unembedded font, an unexpected character in the text
    layer, a missing name or email, a bullet missing from the text, and
    the page fill under `FILL_MIN` warning. Plus one `cmd_build` case: a
    plan that fails validation returns 1 and never calls `compile_pdf`.
  - `tests/test_sample_build.py` runs end to end through the CLI, the
    way Claude calls it:
    - The sample plan builds with exit code 0, `"pages": 1`,
      `"fails": []`, `"bullets_used": 19`. Every **resolved** bullet
      (from `resolve()` on the same plan, so the `acme-1` reframe is
      compared as reframed) is found in the `pdftotext` output after
      `norm()`. Unselected library bullets aren't checked.
    - An overflow plan (the sample plan plus `add_experience: ["harbor"]`,
      since the sample is already at 100% fill) exits 1 with the
      "pages" fail and still writes the `.tex`. This shows the one-page
      check stops a bad build for real, not only with mocks.
    - **Layout margin (added after review).** Both real-build tests must
      pass on any reasonable TeX install, not just the author's Mac.
      Measured 2026-11-12 on TeX Live 2026: the sample's natural fill is
      94.0% (the 100.3% in the summary is after the fill stretch, which
      falls back to the unstretched PDF if stretching spills to a second
      page), so it has about 6% headroom. The overflow plan spills only 4
      lines onto page 2, which is too close. Fix: the overflow plan adds
      `harbor`, `plant-3` (the one project bullet the sample leaves
      out), and the archive alternates `acme-a1` and `chat-a1`: about 9
      more lines (24 bullets vs. 19), which puts it around 109% of the page.
      The test asserts `pages >= 2`, not an exact count. Proof: run the
      full suite inside an Ubuntu 24.04 container with the same apt
      packages as CI, and record each build's natural fill there next to
      the Mac numbers.
  - `tests/test_library_tools.py` covers the validator and the package:
    - `validate_library.py examples` exits 0, and three broken copies
      fail with their own message: a duplicate bullet ID, a variant
      default bullet that doesn't exist, and an empty bullet.
    - `package_skill.py --no-library` builds a zip whose entries all sit
      under `resume-tailor/`. It holds `SKILL.md`, `scripts/`,
      `assets/`, `references/` and `examples/`, and has no `user/`
      entries. Extracted to a temp dir, its own `build_resume.py
      validate examples/sample-plan.json` exits 0. That zip is what app
      users install, so a package missing a file is a real failure.
    - Packaging with a personal library that fails validation exits
      non-zero.
- **LaTeX tests must not skip silently in CI.** A shared helper,
  `tests/support.py`, has a `requires_tex` decorator. It checks for
  `xelatex`, `pdfinfo`, `pdffonts`, `pdftotext` and an importable
  `pikepdf`, and its skip message names whatever is missing. It skips
  locally, but fails instead when the env var
  `RESUME_TAILOR_REQUIRE_TEX=1` is set, and CI sets it. The two existing
  `skipUnless(shutil.which("xelatex"))` uses switch to the helper. *Why:*
  a green CI run that skipped every build test would prove nothing.
- **GitHub Actions**, `.github/workflows/tests.yml`:
  - Runs on push and pull_request, on `ubuntu-24.04` (pinned, not
    `ubuntu-latest`, so a runner upgrade can't silently change TeX
    versions and line breaks), with Python 3.12 via
    `actions/setup-python`.
  - Installs `texlive-xetex fonts-texgyre poppler-utils` with apt (the
    same line the README gives Debian/Ubuntu users, so CI also checks
    that instruction), then `python -m pip install pyyaml pikepdf`.
  - One diagnostic step prints `xelatex --version` and `kpsewhich
    texgyretermes-regular.otf`, so a font lookup failure is obvious in
    the log instead of buried in a LaTeX error.
  - Runs `python -m unittest discover -s tests -v` with
    `RESUME_TAILOR_REQUIRE_TEX=1`.
  - *Why apt instead of a full TeX Live image:* it's the smallest install
    that has xelatex and TeX Gyre Termes, and it's what a user would run.
- **README:**
  - A CI badge under the title.
  - "How it was tested" gets one short paragraph listing what the
    automated suite covers, and the run command. It gives no test count
    unless it's copied from a real run's output.
  - Remove "a full suite is planned."

**Non-goals.**

- Cover letter tests. There's no example letter to build from, so the
  README will say the cover letter builder is tested by hand only.
- Fixing the known early return in `add_experience` validation.
- Testing `times-system` (CI has no Times New Roman).
- Coverage reports, linting, a Python version matrix, and uploading
  PDFs as CI artifacts.

**Files.** `tests/support.py`, `tests/test_check_pdf.py`,
`tests/test_sample_build.py`, `tests/test_library_tools.py` (new);
`tests/test_reframe.py`, `tests/test_plan_validation.py` (extended);
`tests/test_add_experience.py` and `tests/test_find_library.py` (only the
skip decorator changes); `.github/workflows/tests.yml` (new);
`README.md`. No changes to `scripts/`. If a test exposes a real bug, stop
and report it rather than changing the script inside this step.

**Verify.**

```bash
RESUME_TAILOR_REQUIRE_TEX=1 python3 -m unittest discover -s tests -v
```
Expected: all tests pass with 0 skipped. Then check that the tests can
fail, without editing `scripts/`: a throwaway runner in the scratchpad
patches `build_resume.check_reframe` to return `[]` and reruns the suite
(failures in `test_reframe.py` and `test_plan_validation.py`), then
patches `build_resume.check_pdf` to return no fails (the overflow test
fails). `git diff --stat scripts/` is empty. Then, after the user
pushes: `gh run list --workflow tests.yml --commit "$(git rev-parse
HEAD)"` shows that commit's run as `completed success`, and its log
shows the same pass count with 0 skipped.

### Step 6 — Publish

**Need.** Strangers (recruiters, other students) can find the repo, trust
that it works by following the README alone, and learn nothing personal
about the author beyond what the author chose to show (name on the
license, the README's design story).

**What a first sweep found (2026-11-12).** Every version of every
tracked file in all 25 commits was searched for the author's email,
phone patterns, school, LinkedIn URLs, Google Doc IDs, local paths,
claude.ai project/chat links and secret-key patterns. Only made-up data
turned up (Alex Rivera, Jordan Lee, `(555)` numbers), plus the author's
name on the LICENSE and README copyright lines, which is intended. The
sample PDF's metadata says "Alex Rivera" and the PNG has no text chunks.
**The one real exposure: all 25 commits list the author's personal Gmail
as the author email,** which anyone can read from a public repo
(`git log`, or `.patch` on any commit URL).

**Design.**

- **6a. Commit email: the user's decision, made before anything is
  public.** Options:
  1. *(Recommended)* Rewrite the 25 commits' author and committer email
     to the GitHub noreply address (`<id>+jar-narvz@users.noreply.github.com`)
     with `git filter-repo --mailmap`, then force-push `main` once,
     while the repo is still private. *Why now:* nobody else has a
     clone, so a rewrite breaks nothing, and once the repo is public the
     email is exposed for good. The user runs the force push (the global
     rules forbid Claude doing destructive git).
  2. Keep history as is. Simplest, but the email is public.
  3. Publish a fresh repo with one squashed commit. Hides the email but
     throws away the commit history that shows how the project was built.

  With any option: set the repo's local `user.email` to the noreply
  address, and turn on GitHub's "Keep my email addresses private" and
  "Block command line pushes that expose my email" (the user changes
  these account settings).

  **Decision (2026-11-12): option 1, rewrite to noreply,** done as
  "rewrite locally, then recreate the GitHub repo" rather than a force
  push. *Why recreate:* a force push leaves the old commits reachable on
  GitHub. The repo's Activity page lists force pushes with links to the
  pre-push commit, and the old Actions run links to it too, so the old
  email stays one click away. A new repo with the same name has none of
  that. Checked first: the GitHub repo has 0 stars, forks, issues, PRs,
  releases, artifacts, caches, secrets, deployments, Pages or wiki, so
  deleting it loses only the one CI run. Locally: one branch, no tags,
  no stashes.
  Procedure (the user runs every command; Claude gives them exactly):
  1. Commit the planning docs so the tree is clean. Keep this folder
     untouched as the backup until the new repo is verified.
  2. `brew install git-filter-repo`. Make a fresh clone in a sibling
     folder (`git clone --no-local`). In that clone, run `git filter-repo`
     (no `--force` needed in a fresh clone) with:
     - `--mailmap`: one line mapping only the old email to the noreply
       address `207102629+jar-narvz@users.noreply.github.com` (confirm
       it in GitHub → Settings → Emails first);
     - `--replace-text`: replace the step 5 CI commit's short SHA and
       its run ID in every historical file version, so no file in
       history names an old SHA.
  3. Check in the rewritten clone: `git log --all --format='%ae %ce' |
     sort -u` shows only the noreply address, and the old SHA string
     appears nowhere in `git log --all -p`. Set `git config user.email`
     to the noreply address there before any new commit.
  4. Delete the GitHub repo (Settings → Danger zone; the `gh` token
     lacks `delete_repo`), recreate it **private** with the same name,
     add it as `origin` in the rewritten clone, and push `main`. The push
     starts a fresh CI run on the new SHAs.
  5. The rewritten clone becomes the working folder; the old folder
     stays as a local backup until step 6 is done.
  6. The user turns on both GitHub email-privacy settings.
  The repo stays private until 6b–6c pass.
- **6b. Privacy sweep (Claude, read-only), repeatable and recorded in
  PROGRESS.md:**
  - **Denylist from the real library.** Build a list of the author's
    real identifiers (phone, email, school, employers, project names,
    a few distinctive bullet phrases) from
    `~/.claude/skills/resume-tailor/user/`, the author's real library,
    which is outside this repo. Keep it only in the scratchpad, never
    in the repo, PLAN.md or PROGRESS.md (PROGRESS records how many terms
    and how many matches, not the terms themselves).
  - Search the denylist plus the generic patterns from the first sweep
    across every object that will be served: each unique blob from
    `git rev-list --objects --all` (via `git cat-file`, with text and
    binary blobs handled by type), every commit message, and
    author/committer metadata after 6a. Run this in the rewritten clone,
    which has no dangling objects.
  - Look inside binaries: `examples/sample-output.pdf` (docinfo, XMP,
    `strings`), `docs/before-after.png` (text/EXIF chunks), and the
    release zip. Build the zip in a clean checkout of the release commit
    (`package_skill.py` packages whatever files are in the folder, not
    just tracked ones), list its entries, reject any file that isn't
    tracked in git and any symlink, search its contents, and upload
    exactly those audited bytes.
  - GitHub side, on the recreated repo: Actions runs and logs,
    artifacts, caches, secrets, releases, issues, PRs, wiki, Pages and
    deployments. All should be empty apart from the new CI run, and
    each is recorded as checked.
  - Anything found gets removed or replaced with made-up data in a normal
    commit. If it's in history, it goes back to 6a's decision.
- **6c. Ready-for-anyone sweep:**
  - **Fresh clone, fresh environment, README only.** In a plain
    `ubuntu:24.04` container with nothing preinstalled, follow the
    README literally: the Debian/Ubuntu requirements line, the pip line,
    the clone, the "try it without setting anything up" commands, the
    full test command, and the app-user packaging command. Every command
    must work as written. (The packaging command already works on a bare
    `python:3.12-slim` with no pip packages, checked 2026-11-12.)
  - **README read as a stranger:** every relative link resolves to a
    tracked file. Install steps match the current Claude app UI
    (Settings → Capabilities, Customize → Skills). Every number traces
    to a real source (honesty rule): the 6.9 GB MacTeX size, "matched
    exactly", the line-break claim about Times New Roman, and the
    Affinda findings. Fix or drop any claim that can't be traced.
    Limitations are current. One final wording pass, which may cut but
    doesn't restructure.
  - **Claude app smoke test with the final zip.** The scripts changed
    since the last app test (steps 4–5), so upload the zip built from
    the release commit to the test account. Then, in a new chat inside
    the test Project, tailor a posting with the saved library. This
    checks the new build and Project persistence. The user uploads, and
    Claude drives the built-in browser.
  - Keep PLAN.md and PROGRESS.md public. *Why:* they show the
    plan → critique → implement → review process, which is part of what
    the portfolio demonstrates. They name only made-up candidates and the
    test account type, which the sweep confirms.
- **6d. Publish (the user runs every outward-facing command; Claude gives
  them exactly):**
  - `gh repo edit --description "…" --add-topic claude,claude-skills,resume,latex,ats,python`.
  - `gh repo edit --visibility public --accept-visibility-change-consequences`.
  - Tag `v1.0.0` on the release commit, `git push origin v1.0.0`,
    confirm with `git ls-remote --tags origin` that the tag points at
    the release SHA, then `gh release create v1.0.0 resume-tailor.zip
    --verify-tag --title "v1.0.0" --notes-file <file>`. The notes give the
    zip's SHA-256 and three short points: what it does, how to install,
    and a link to Limitations.
  - After publishing, check anonymously with `curl` (no auth; a browser
    tab may still be signed in): the repo page loads, the badge SVG says
    passing, the release asset downloads and matches its SHA-256, a
    commit's `.patch` shows only the noreply email, and the Activity page
    shows no force pushes.

**Non-goals.** CONTRIBUTING.md, issue templates, a Skills marketplace
listing, a demo video, a changelog beyond the release notes, and scrubbing
the author's name (it's intentionally on the license).

**Files.** `README.md` (wording and claims pass only) and `PROGRESS.md`.
A sweep finding outside those two files is recorded and fixed in its own
small commit, before release, only if it's a privacy leak or a README
command that fails. Anything else waits until after v1.0.0.

**Verify.**

```bash
git log --all --format='%ae %ce' | sort -u
gh repo view --json visibility,description,repositoryTopics
gh release view v1.0.0 --json assets
```
Expected: emails are only the noreply address; visibility `PUBLIC` with
the description and topics; one asset, `resume-tailor.zip`. Also
recorded: the release SHA; `git ls-remote origin` equal to local `main`
and the tag; the CI run on the release SHA `completed success`; the
anonymous download's SHA-256 equal to the audited zip's. Plus, recorded in PROGRESS.md: denylist and pattern
search over HEAD, history, messages, binaries and the zip with 0
unexpected matches; every fresh-clone command succeeded; the app smoke
test summary (`"pages": 1`, `"fails": []`); and the logged-out checks
passed.

## Review log

(Codex critiques of this plan, each accepted or rejected with a reason.)

**2026-11-12, Step 1, Codex critique (8 points).**

1. Rendering needs a copied effective variant, not just resolved slots.
   **Accepted:** `compose()` only fills placeholders the master already
   has, so additions must be rendered. Added "Rendering".
2. Empty experience list and omitted `section_order`. **Accepted:** the
   renderer skips an empty Experience section; spelled out both cases.
3. The positive build may spill to two pages. **Accepted:** the sample is
   at 100% fill; the e2e test drops one project.
4. Which entry supplies header vs. default bullets. **Accepted:** first
   match supplies both; repeated slots across variants stay legal.
5. Malformed `add_experience`. **Accepted:** list of unique strings,
   clean failures.
6. Verify must exercise overrides and the typo guard. **Accepted:** listed
   as test cases.
7. Validator needs negative checks. **Accepted:** listed as test cases.
8. Unchanged sample counts don't prove unchanged defaults. **Accepted:**
   Verify diffs both default variants' `.tex` against pre-change
   baselines.

Test framework: stdlib `unittest` rather than installing pytest now,
because pytest isn't installed and step 3 can run unittest tests
unchanged.

**2026-11-12, Steps 2 and 3, Codex critique (6 points).**

1. Step 3 later edits need a writable copy (`/mnt/project` is read-only).
   **Accepted:** step 8 copies to `resume-work/user/`, validates, and
   sends back changed files.
2. SKILL.md reads `user/...` paths directly, so Claude could pick IDs from
   a different library than the build uses. **Accepted:** one `LIBRARY`
   path used throughout.
3. A partial Project upload would crash or shadow a working library.
   **Accepted:** clear error naming missing files; no silent fallback.
4. Newlines in company/role could escape the TeX comment. **Accepted:**
   collapse whitespace.
5. Step 2 didn't say how company/role reach `compose()` or handle missing
   ones. **Accepted:** carried in the resolved dict; four combinations
   specified; date pinnable for tests.
6. Verify didn't prove unchanged PDF text or exercise Project lookup.
   **Accepted:** step 2 diffs sample PDF text against a pre-change
   baseline; step 3 tests cover fallback, incomplete and read-only
   Project dirs.

**2026-11-12, Steps 4 and 5, Codex critique (8 points).** Codex reviewed
the first draft of the test plan (then the only step 4). I reproduced
points 1 and 2 before deciding.

1. Reframe check accepts Built→Led and a number/unit swap. **Accepted**,
   reproduced: these are claim inflation, which the skill exists to
   prevent, so they get a fix step (new step 4) before tests are written
   against them. The stemmer false rejection it also found (`Used` →
   `Use`) is **rejected** as a fix: it fails safe.
2. Skill-from-bullet check is a substring match (`Script` from
   `TypeScript`); also test unselected bullets, other variants'
   defaults, parenthesized items, exact `archive_used`. **Accepted**,
   reproduced: the boundary fix goes in step 4, the rest are step 5
   cases.
3. The PDF text check must compare resolved bullets, since the sample
   reframes `acme-1`. **Accepted:** as first written, the test would
   have failed on correct output.
4. Most `check_pdf` rejections and `cmd_build`'s fail paths are
   untested. **Accepted** with mocked tool output (fast, no LaTeX). Its
   note that a bullet truncated after five words still passes recovery
   is **rejected** as a fix: the build composes that text itself, so a
   plan can't cause it.
5. Validator and package checks are too weak. **Accepted:** three
   broken-library cases, a fuller zip layout check, and validating from
   the extracted zip.
6. Ubuntu font lookup and runner drift. **Accepted:** pin
   `ubuntu-24.04` and print a `kpsewhich` diagnostic. A separate minimal
   fontspec compile is **rejected**: the sample build already does that.
7. Prerequisite helper checks too few tools. **Accepted:** check all
   four poppler/TeX tools plus `pikepdf`; use `python -m pip`.
8. Verify edited production code and `--limit 1` can pick the wrong
   run. **Accepted:** mutation runs use `mock.patch` from a scratch
   runner, cover `check_pdf` too, and the run is selected by commit SHA.


**2026-11-12, Step 6, Codex critique (8 points).** Run with web search
off after two stalled attempts.

1. Old SHAs stay discoverable after a force push, and old file versions
   name the step 5 CI commit. **Accepted, with a stronger fix:** a force
   push also leaves the repo's Activity page linking to pre-push
   commits, so 6a now recreates the GitHub repo instead of force-pushing
   to it, and `--replace-text` removes the old SHA and run ID from
   history. Making a GitHub Support garbage collection a gate is
   **rejected**: after recreation, no GitHub page refers to the old
   objects.
2. The GitHub audit is too narrow. **Accepted:** inventoried now (all
   empty apart from one CI run), and rechecked on the recreated repo.
3. The rewrite needs a fresh clone, exact mailmap and address, and a
   safe push. **Accepted:** fresh `--no-local` clone without `--force`,
   email-only mapping, address confirmed in Settings, original folder
   kept as backup. The lease and expected-SHA push advice no longer
   applies, since the new repo starts empty.
4. `git log -p` isn't every blob. **Accepted:** enumerate objects with
   `rev-list --objects --all` and `cat-file`, in the rewritten clone,
   which has no dangling objects.
5. The zip can differ from the release. **Accepted:** build it from a
   clean checkout of the release commit, reject untracked files and
   symlinks, and upload those exact audited bytes.
6. The stranger test starts with too much installed. **Accepted** for
   the environment: a plain `ubuntu:24.04` container, following the
   README. Its claim that the app packaging command needs pip packages
   is **rejected**: it ran on a bare `python:3.12-slim`. A full setup
   rerun in the app is **rejected**: setup was tested on a fresh account
   and steps 4–5 changed only build checks; the smoke test now covers a
   Project chat instead.
7. Release commands are underspecified. **Accepted:** exact
   `--description`/`--add-topic`, push and verify the tag, then
   `gh release create --verify-tag`.
8. Verify doesn't pin the release. **Accepted:** record the release SHA,
   remote ref equality, CI on that SHA, and an anonymous `curl` download
   hash. The open-ended file scope is now bounded.
