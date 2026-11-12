# PLAN.md

Source of truth for remaining work. Only Claude edits this file. Status
lives in PROGRESS.md.

## Where the project is

The skill works end to end in Claude Code and the Claude app (paid and
free accounts): setup, polish with approval, packaging, and tailoring were
tested by hand on 2026-11-12. What's left before publishing: one gap in
the data model, one output bug, automated tests, and the public release.

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

The tailored `.tex` starts with the master template's comment
("master_swe.tex … Don't edit this file"), which is wrong for a file
users receive. Replace it with one line naming the company, role and
build date. Verify: sample build's `.tex` first line no longer mentions
`master_` or "Don't edit"; output PDF unchanged.

### Step 3 — Automated tests and CI

pytest suite: reframe rules (number changed, new word stem, >3 words
added, allowed verb swap), plan validation (unknown ID, wrong slot, skill
not in inventory, `add_experience` failures), and an end-to-end sample
build (one page, no fails, every bullet recoverable from the PDF text).
GitHub Actions installs TeX Live + poppler and runs it; README gets the
badge. Details to be planned when step 2 is done.

### Step 4 — Publish

README pass (mention tests), repo description and topics, make public,
optional v1.0 release with the zip attached.

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
