# PROGRESS.md

## Current state

Step 1 (plan can add an older position) is done: implemented by Codex,
reviewed and verified by Claude on 2026-11-12. Next: step 2 (clean header
in the tailored .tex), then step 3 (library in a Claude Project; the
`/mnt/project` test passed by hand on 2026-11-12).
Setup, polish-with-approval, packaging and tailoring were tested by hand
in the Claude app on 2026-11-12.

## Log

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
