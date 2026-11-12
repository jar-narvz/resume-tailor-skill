# PROGRESS.md

## Current state

Steps 1–3 are done: implemented by Codex, reviewed and verified by Claude
on 2026-11-12, including the by-hand Claude app check for step 3 (a
Project chat tailored with no setup and reported `"library":
"/mnt/project"`). Next: step 4 (automated tests and CI), which needs
planning detail first.

## Log

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
