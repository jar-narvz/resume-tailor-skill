# PROGRESS.md

## Current state

Steps 1–5 are done. Step 5's CI passed on GitHub for commit (step 5 commit)
(run (step 5 run): `Ran 76 tests ... OK`, no skips, TeX Live 2023/Debian).
Next: step 6 (publish), which needs planning detail first.

## Log

### 2026-11-12 — Step 6 planning — Claude
- **Did:** Planned step 6 (publish), including the privacy and
  ready-for-anyone sweeps the user asked for. A first privacy scan of all
  25 commits (every file version, messages, PDF/PNG metadata, secret
  patterns, local paths) found only made-up data and the intended
  copyright name. The one exposure: every commit's author email is the
  author's personal address. Plan 6a leaves that decision to the user.
- **Changed:** PLAN.md, PROGRESS.md
- **Verify:** n/a (planning).
- **Review:** Codex critique pending. `codex exec` stalled twice (once
  on a web search, once at startup after an MCP auth error), so it was
  stopped with no output. Rerun before step 6 starts.
- **Gotchas:** Don't pipe `codex exec` into `head`: that kills it early.
  Use `-o <file>` for the final message.

### 2026-11-12 — Step 5 review — Claude
- **Did:** Reviewed Codex's step 5 diff against PLAN.md and ran Verify
  locally, including the mutation checks.
- **Changed:** PROGRESS.md only (no fixes needed).
- **Verify:** `RESUME_TAILOR_REQUIRE_TEX=1 python3 -m unittest discover
  -s tests -v` → `Ran 76 tests ... OK`, no skipped lines. Mutation runner
  in the scratchpad (`mock.patch`, no edits to `scripts/`):
  `check_reframe` disabled → 13 failures in test_plan_validation and
  test_reframe; `check_pdf` disabled → 11 failures + 1 error in
  test_check_pdf. The overflow test runs the CLI as a separate process,
  so the patch can't reach it; checked by hand instead: the overflow plan
  builds a 2-page PDF and exits 1 with the real check, and exits 0 with
  `check_pdf` patched out in a wrapper, so the test would catch it.
  `git diff scripts/` is empty. Ubuntu 24.04 container built to match
  CI (Python 3.12.3, TeX Live 2023/Debian, `kpsewhich` finds
  `/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-regular.otf`):
  `Ran 76 tests ... OK`, no skips. Natural fill there matches the Mac
  exactly: sample 94.0% (stretched 100.3%, 19 bullets, `"fails": []`),
  base swe 95.7%, base ml 93.3%. GitHub run (step 5 run) on (step 5 commit): `completed success`, `Ran 76 tests
  in 6.689s`, `OK`, no skipped lines.
- **Review:** No blocking findings. Only listed files touched; tests
  assert exact fail messages, the sample-build test compares resolved
  (reframed) bullets in full, not just their first five words, and the
  package test validates from the extracted zip. Layout margin, checked
  after review: the summary's 100.3% is the fill *after* stretching; the
  sample's natural fill is 94.0% (about 6% headroom, and a stretch that
  spills falls back to the unstretched PDF). The overflow test spilled
  only 4 lines, so Codex widened it (adds `harbor`, `plant-3`, `acme-a1`,
  `chat-a1`; asserts `pages >= 2`).
- **Gotchas:** In-process `mock.patch` doesn't reach tests that run a
  script as a subprocess; use a wrapper script for those.

### 2026-11-12 — Step 5 — Codex
- **Did:** Extended reframe and plan validation coverage; added mocked PDF
  checks, real sample/overflow CLI builds, validator failures, and public
  package layout/extracted validation tests. Added shared PDF prerequisites
  with local skips and required-mode failures, switched the two existing
  build decorators, configured Ubuntu 24.04/Python 3.12 CI, and updated the
  README badge, suite instructions, and manual-only cover letter note.
- **Changed:** tests/support.py, tests/test_check_pdf.py,
  tests/test_sample_build.py, tests/test_library_tools.py,
  tests/test_reframe.py, tests/test_plan_validation.py,
  tests/test_add_experience.py, tests/test_find_library.py,
  .github/workflows/tests.yml, README.md, PROGRESS.md.
- **Verify:** Required local command exited 0; actual final output:

  ```text
  $ RESUME_TAILOR_REQUIRE_TEX=1 python3 -m unittest discover -s tests -v
  Ran 76 tests in 8.729s

  OK
  ```

  Confirmed 0 skipped. Real sample build: pages 1, fails [], bullets_used
  19; all resolved bullet texts recovered. Overflow build exited 1 with
  the pages failure and preserved its .tex. `git diff --check` passed;
  `git diff --stat -- scripts/ PLAN.md` was empty.
- **Review:** pending Claude
- **Gotchas:** No new script bugs exposed; no tests omitted. Mutation
  checks and the GitHub run are left to Claude as requested. Current state,
  PLAN.md, and scripts/ were left unchanged. No commit or push.

### 2026-11-12 — Step 4 review — Claude
- **Did:** Reviewed Codex's step 4 diff against PLAN.md and reran Verify.
  Verb rule, number/next-word pairs, whole-token skill matching, docs and
  the listed test cases match the plan; only listed files touched.
- **Changed:** scripts/build_resume.py, tests/test_plan_validation.py,
  README.md, PROGRESS.md
- **Verify:** `Ran 39 tests ... OK`. Sample build `"fails": []`,
  `"pages": 1`, `"bullets_used": 19`, `"reframes": 1`; validate
  `"ok": true`. Base builds `--variant swe` and `ml`: `"pages": 1`,
  `"fails": []`. The three probes from PLAN.md now fail: `words not in
  the original bullet: led`, `numbers changed: [('25', 'minutes'), ('3',
  'hours')] -> [('25', 'hours'), ('3', 'minutes')]`, and `skill 'Script'
  ... is not in skills.md`.
- **Review:** Findings fixed: (1) the rewrite dropped the old
  `len(n) >= 3` guard on skills taken from bullet text, so "In", "To" and
  "A" were accepted as skills (probed); restored it with a comment and
  added `test_short_skill_from_bullet_word_is_rejected`. (2) README
  "Verbatim validation" had an over-long line and jargon ("number/next-word
  pair"); reworded in plain language. Noted, not fixed: an original with
  "lead" as a noun ("lead time") unlocks Led/Managed swaps; rare, and the
  plan defines the rule by stem.
- **Gotchas:** none.

### 2026-11-12 — Step 4 — Codex
- **Did:** Restricted new swap verbs to the first word and leadership
  swaps to originals with a leadership stem; compare sorted number/next-word
  pairs; match skills from selected bullets as contiguous whole tokens.
  Added regression coverage for the rejected and allowed reframes and
  temp-copy library tests for Script rejection and Node.js acceptance.
  Updated the reframe rules and matching skill/README wording.
- **Changed:** scripts/build_resume.py, references/reframe-rules.md,
  SKILL.md, README.md, tests/test_reframe.py (new),
  tests/test_plan_validation.py (new), PROGRESS.md.
- **Verify:** All three Step 4 commands exited 0. Actual output below
  (per-test lines and unrelated build JSON fields omitted):

  ```text
  $ python3 -m unittest discover -s tests -v
  Ran 38 tests in 5.010s

  OK
  $ python3 scripts/build_resume.py --library examples build examples/sample-plan.json out/v4
   "reframes": 1,
   "pages": 1,
   "bullets_used": 19,
   "fails": [],
  $ python3 scripts/build_resume.py --library examples validate examples/sample-plan.json
  {
   "ok": true,
   "fails": [],
   "warns": []
  }
  ```
- **Review:** pending Claude
- **Gotchas:** Trimming the word immediately after a number is now
  deliberately rejected; use the original bullet. The simple stemmer's
  existing false rejections remain outside this step's scope. No commits.

### 2026-11-12 — Steps 4–5 planning — Claude
- **Did:** Planned tests and CI, got a Codex critique (8 points), and
  reproduced its two claim loopholes: `check_reframe` accepts Built→Led
  and a number/unit swap, and the skill-from-bullet check accepts
  `Script` from `TypeScript`. These became a new fix step 4. Tests and CI
  moved to step 5, publish to step 6.
- **Changed:** PLAN.md, PROGRESS.md
- **Verify:** n/a (planning). Probes run directly against
  `scripts/build_resume.py`: all three returned no problems.
- **Review:** Codex critique recorded in PLAN.md's Review log: 8 points
  accepted, three sub-points rejected with reasons.
- **Gotchas:** `timeout` isn't on macOS. Run `codex exec` without it.

### 2026-11-12 — Step 3 review — Claude
- **Did:** Reviewed Codex's step 3 diff and reran Verify. Lookup order,
  incomplete-Project error, single `LIBRARY` in SKILL.md, and the step 8
  working copy match PLAN.md; only listed files touched (the
  `build_resume.py` diff is step 2's, still uncommitted).
- **Changed:** SKILL.md, references/setup.md
- **Verify:** 32 tests OK. Sample build `"fails": []`, `"pages": 1`,
  `"bullets_used": 19`. Extra check: Jordan's four library files in a
  read-only temp dir via `RESUME_TAILOR_PROJECT_DIR`, `build --variant
  swe` with no `--library`: `"library"` is that dir, `"pages": 1`,
  `"fails": []`.
- **Review:** Findings fixed: (1) SKILL.md and setup.md told Claude about
  `RESUME_TAILOR_PROJECT_DIR`, a test-only knob; removed from user-facing
  instructions (code keeps it). (2) Step 8 said to start from a fresh
  working copy but ran only `mkdir -p`, so a stale `archive.md` could
  survive; now `rm -rf resume-work/user` first.
- **Gotchas:** By-hand Claude app check done later the same day (Claude
  drove the built-in browser; free account): uploaded the new zip, then in
  the `tailor-resume` Project with Jordan's four files in Context, a new
  chat tailored a Tesla posting with no setup. Summary: `"library":
  "/mnt/project"`, `"pages": 1`, `"fails": []`, one warn (72% fill, all
  bullets used). Found the docs named the wrong place for skills: it's
  Customize → Skills → Add → Upload skill (same-name upload replaces in
  place), and the code-execution toggle is labeled "Create and edit
  files". Fixed in README.md, SKILL.md, references/setup.md.

### 2026-11-12 — Step 3 — Codex
- **Did:** Added lookup order explicit > Project > user > examples, with
  an environment override for the Project directory, a one-line warning
  naming both libraries when the Project shadows user/, and a clear
  incomplete-Project error naming missing files and Project Context.
  Updated SKILL.md to use one LIBRARY path for all reads and builds and
  check both profiles before setup. Documented Project vs. zip saving,
  recommending Projects for tailoring in one place; later Project edits
  use a fresh writable copy, explicit validation/builds, and delivery of
  only changed files. Added 10 stdlib unittest tests covering lookup,
  warnings, incomplete libraries, clean CLI failure, optional archive,
  and a real build from a read-only temporary Project library.
- **Changed:** scripts/library.py, tests/test_find_library.py (new),
  SKILL.md, references/setup.md, README.md, PROGRESS.md.
- **Verify:** Both automated Step 3 Verify commands exited 0. Actual
  output below; unittest's per-test `... ok` lines are abbreviated.

  ```text
  $ python3 -m unittest discover -s tests -v
  ----------------------------------------------------------------------
  Ran 32 tests in 4.829s

  OK

  $ python3 scripts/build_resume.py --library examples build examples/sample-plan.json out/v3
  {
   "library": "examples",
   "variant": "swe",
   "graduation": "May 2027",
   "added_experience": [],
   "pdf": "out/v3/Alex_Rivera_Resume_Globex_Logistics_Backend_Software_Engineer_Intern.pdf",
   "tex": "out/v3/Alex_Rivera_Resume_Globex_Logistics_Backend_Software_Engineer_Intern.tex",
   "pdf_kb": 26.4,
   "reframes": 1,
   "archive_used": [],
   "pages": 1,
   "page_fill_pct": 100.3,
   "bullets_used": 19,
   "natural_fill_pct": 94.0,
   "fails": [],
   "warns": []
  }
  ```

  Before implementation, the initial nine-test lookup suite failed with
  seven failures: missing Project selection, shadow warning, incomplete
  errors, and read-only build library selection. After implementation,
  all 32 tests passed with no skips.
- **Review:** pending Claude.
- **Gotchas:** The by-hand Claude app check is still pending: a new chat
  in the test Project must tailor without setup and report
  `"library": "/mnt/project"`. All new tests set
  RESUME_TAILOR_PROJECT_DIR to temporary directories; none access the
  real /mnt path. Read-only test permissions are restored for cleanup;
  later-edit instructions make copied files writable explicitly.
  Existing PLAN.md and Step 2 changes were left untouched. No baseline
  files were modified; the sample Verify generated only out/v3 output.
  No dependencies added, and no git commit or push run.

### 2026-11-12 — Step 2 review — Claude
- **Did:** Reviewed Codex's step 2 diff (`compose()` header, company/role
  carried in `resolve()`) and reran Verify. Matches PLAN.md; only listed
  files touched. No findings.
- **Changed:** PROGRESS.md
- **Verify:** 22 tests OK. Sample `.tex` line 1: `% Alex Rivera resume,
  tailored for Globex Logistics (Backend Software Engineer Intern), built
  2026-11-12 by resume-tailor`. `swe body unchanged`, `ml body unchanged`,
  `sample text unchanged`. Sample build `"fails": []`, `"pages": 1`,
  `"bullets_used": 19`.
- **Review:** accepted. Note: `date | None` needs Python 3.10+.
- **Gotchas:** none.

### 2026-11-12 — Step 2 — Codex
- **Did:** Carried company and role through `resolve()`. Replaced leading
  master comments in `compose()` with a single tailored or base header,
  collapsed whitespace in interpolated values, and added a pinnable build
  date defaulting to today. Added stdlib unittest coverage for all four
  company/role combinations, the variant base header, dates, CR/LF and
  other whitespace, removal of master warnings, and preservation of body
  comments. Stopped before step 3.
- **Changed:** scripts/build_resume.py, tests/test_tex_header.py (new),
  PROGRESS.md.
- **Verify:** All five Step 2 commands exited 0. Actual output below;
  unittest's per-test `... ok` lines are abbreviated.

  ```text
  $ python3 -m unittest discover -s tests -v
  ----------------------------------------------------------------------
  Ran 22 tests in 2.470s

  OK

  $ python3 scripts/build_resume.py --library examples build examples/sample-plan.json out/v2
  {
   "library": "examples",
   "variant": "swe",
   "graduation": "May 2027",
   "added_experience": [],
   "pdf": "out/v2/Alex_Rivera_Resume_Globex_Logistics_Backend_Software_Engineer_Intern.pdf",
   "tex": "out/v2/Alex_Rivera_Resume_Globex_Logistics_Backend_Software_Engineer_Intern.tex",
   "pdf_kb": 26.4,
   "reframes": 1,
   "archive_used": [],
   "pages": 1,
   "page_fill_pct": 100.3,
   "bullets_used": 19,
   "natural_fill_pct": 94.0,
   "fails": [],
   "warns": []
  }

  $ head -2 out/v2/tailored.tex
  % Alex Rivera resume, tailored for Globex Logistics (Backend Software Engineer Intern), built 2026-11-12 by resume-tailor
  \documentclass[termes]{resume}

  $ for v in swe ml; do python3 scripts/build_resume.py --library examples build --variant $v out/after2-$v >/dev/null; diff <(grep -v '^%' out/baseline-$v/tailored.tex) <(grep -v '^%' out/after2-$v/tailored.tex) && echo "$v body unchanged"; done
  swe body unchanged
  ml body unchanged

  $ pdftotext out/v2/tailored.pdf - | diff out/baseline-sample/text.txt - && echo "sample text unchanged"
  sample text unchanged
  ```

  Before implementation, the first regression test failed on the old
  `master_swe.tex` header. The expanded tests also exposed the missing
  resolved company/role fields and build-date parameter.
- **Review:** pending Claude.
- **Gotchas:** PLAN.md already had a local modification when this step
  began; it was left untouched. No baseline files were modified. Verify
  generated outputs only in out/v2 and out/after2-{swe,ml}.

### 2026-11-12 — Step 1 review — Claude
- **Did:** Reviewed Codex's step 1 diff and reran Verify. Design matches
  PLAN.md; no files outside the step's list; `render_masters.py` untouched
  as Codex noted. Fixed three small findings myself.
- **Changed:** scripts/build_resume.py, examples/bullets.md,
  tests/test_add_experience.py
- **Verify:** `unittest`: Ran 18 tests, OK. Validator: `ok: examples has 24
  bullets, 3 projects, 2 variants`. `swe unchanged`, `ml unchanged`.
  Sample build: `"fails": []`, `"pages": 1`, `"bullets_used": 19`. Extra
  plan (`add_experience: ["harbor"]`, projects kv + chat): `"fails": []`,
  `"pages": 1`, PDF text shows "Data Analyst Intern" and both bullets.
- **Review:** Findings: (1) `build_resume.py` indexed `x["slot"]`, so a
  pool entry missing `slot` crashed with a traceback instead of failing
  cleanly; now `x.get("slot")`. (2) The example's harbor bullets were thin
  ("Built SQL reports for the operations team.") for a public showcase
  library; replaced with specific made-up bullets. (3) The e2e test
  hardcoded that bullet text; it now reads it from the library. Noted, not
  changed: a failing `add_experience` returns before other plan checks run,
  so one build may report only that failure.
- **Gotchas:** none.

### 2026-11-12 — Step 1 — Codex
- **Did:** Implemented optional `extra_experience` and deliberate
  `add_experience` plan additions. Lookup uses the pool first, then variants
  in profile order; a copied effective variant renders the added headers
  and placeholders without mutating the loaded profile. Added clean plan
  failures, `added_experience` summaries, validator checks, docs, an Alex
  Rivera example position with two bullets, and 18 unittest tests including
  a real one-page PDF build. Tests cover defaults, overrides, ownership,
  ordering, empty experience, omitted section order, lookup precedence,
  profile immutability, invalid entries, and clean CLI failures.
- **Changed:** tests/test_add_experience.py (new), scripts/build_resume.py,
  scripts/validate_library.py, examples/profile.yaml, examples/bullets.md,
  SKILL.md, references/variants.md, references/setup.md, README.md,
  PROGRESS.md.
- **Verify:** All four Step 1 commands exited 0. Actual output below;
  unittest's per-test `... ok` lines are abbreviated.

  ```text
  $ python3 -m unittest discover -s tests -v
  ----------------------------------------------------------------------
  Ran 18 tests in 2.478s

  OK

  $ python3 scripts/validate_library.py examples
  ok: examples has 24 bullets, 3 projects, 2 variants

  $ for v in swe ml; do python3 scripts/build_resume.py --library examples build --variant $v out/after-$v >/dev/null; diff out/baseline-$v/tailored.tex out/after-$v/tailored.tex && echo "$v unchanged"; done
  swe unchanged
  ml unchanged

  $ python3 scripts/build_resume.py --library examples build examples/sample-plan.json out/v1
  {
   "library": "examples",
   "variant": "swe",
   "graduation": "May 2027",
   "added_experience": [],
   "pdf": "out/v1/Alex_Rivera_Resume_Globex_Logistics_Backend_Software_Engineer_Intern.pdf",
   "tex": "out/v1/Alex_Rivera_Resume_Globex_Logistics_Backend_Software_Engineer_Intern.tex",
   "pdf_kb": 26.4,
   "reframes": 1,
   "archive_used": [],
   "pages": 1,
   "page_fill_pct": 100.3,
   "bullets_used": 19,
   "natural_fill_pct": 94.0,
   "fails": [],
   "warns": []
  }
  ```

  `git diff --check` also exited 0 with no output. The initial pre-change
  test run failed on the missing addition and validator behavior; the final
  run passed with no skips.
- **Review:** pending Claude
- **Gotchas:** `scripts/render_masters.py` needed no changes: rendering the
  copied effective profile already handles an initially empty Experience
  section. `PLAN.md` and `out/baseline-swe` / `out/baseline-ml` were not
  modified. Verify generated `out/after-swe`, `out/after-ml`, and `out/v1`.
  Position reordering/removal, header edits, archive parsing, and Step 2
  remain out of scope. No dependencies added; no commit or push run.

### 2026-11-12 — Planning — Claude
- **Did:** Created PLAN.md and PROGRESS.md. Planned step 1 after a Claude
  app test showed setup dropping an older internship because a plan can't
  add a position.
- **Changed:** PLAN.md, PROGRESS.md
- **Verify:** n/a (planning)
- **Review:** pending Codex critique
- **Gotchas:** Earlier today (all by hand in the Claude app): code-execution
  and setup gates added to SKILL.md; setup asks for files first, polishes
  bullets only with approval, asks for numbers without suggesting any, and
  packages the library before tailoring.
