# First-time setup

Run this when there is no `user/profile.yaml` in the skill folder, or when
the user asks to set up, rebuild, or import their resume. The goal is a
personal library (`profile.yaml`, `bullets.md`, `skills.md`, `archive.md`)
that every later tailoring run draws from. It takes one conversation.

Work in the user's words. Setup copies; it never improves, embellishes, or
"punches up" a bullet. Whatever goes into the library is what the build
will let onto a resume, so a padded bullet here becomes a padded resume
everywhere.

## Where the library goes

- **Claude Code** (the skill folder is writable): write to
  `<SKILL_DIR>/user/`. Files persist, so setup is done once.
- **Claude app** (the skill folder is read-only and the workspace resets
  between chats): write to `resume-work/user/` in the working directory,
  pass `--library resume-work/user` to every script during setup, and
  finish with step 6 (package and re-upload).

Test which applies by checking whether `<SKILL_DIR>` is writable
(`test -w <SKILL_DIR> && echo writable`).

## 1. Collect source material

Ask once for everything they have. This first message asks only for
files; the step 3 questions wait until you've read them, since the resume
answers most of them.

- Their current resume: PDF, .docx, a Google Doc link, or pasted text.
- Any older or alternate resumes (a data-science version, last year's
  version, a LinkedIn PDF export). These fill the archive.

Read every file fully. For a Google Doc, use the Drive connector if it's
connected; otherwise ask them to download it as PDF or paste it.

Memory and past chats can help here, but only to find things: a resume
doc they mentioned, an older version, a job or project to ask about.
They hold summaries, not the user's exact wording, so:

- Copy bullet text word for word from an actual resume (file, doc, or
  pasted text), never from memory or a past chat.
- Anything you only found in memory or a past chat (a job, a date, a
  skill) goes into the library only after the user confirms it.

## 2. Extract

From all sources, pull out:

- **Header:** name and each contact item (email, phone, links, city), in
  the order the current resume shows them.
- **Education:** school, degree line, expected graduation, coursework.
- **Experience:** each position's title, org, dates, location, and every
  bullet **verbatim**.
- **Projects:** title, tech, term, any repo or demo link, and every bullet
  verbatim.
- **Skills:** every item on any skills line, grouped by the categories
  they used.

Merge across sources:

- The same bullet in two resumes is one ID.
- A different wording of the same bullet is a **separate ID** (the newest
  wording gets the lower number and goes into defaults; the older one
  stays available).
- Bullets, projects and skills that appear only on older resumes go to
  `archive.md`, not `bullets.md`.

Don't fix grammar, add metrics, or merge two bullets into one. If a bullet
has an obvious typo, keep it and mention it in step 5 so they can decide.

## 3. Ask at most four questions

Ask together, in one message, only what you can't infer:

1. **Variants.** Suggest one or two based on their bullets (e.g. "software
   engineering" and "ML/data") with a one-line `use_for` each. If their
   sources already contain two versions, propose those.
2. **Defaults per variant.** Propose which bullets and projects each base
   shows, starting from their current resume; ask only if it's unclear.
3. **Font.** `termes` (free Times clone, the default) or `times-system`
   (Times New Roman installed on their computer). In the Claude app, skip
   this question and use `termes`: its environment doesn't have Times New
   Roman, so `times-system` can't build there.
4. **Graduation date(s)**, if the resume doesn't show one or they apply to
   programs that shift it (these go in `alt_graduations`).

If the person isn't around to answer, take the defaults (variants as
suggested, current resume's content as defaults, `termes`) and say so.

## 4. Write the library

Follow the formats in `examples/` exactly (Alex Rivera is the model):

- `profile.yaml`: header, education, font, variants. Copy the structure
  of `examples/profile.yaml`; `drive_masters: []` unless they want Drive
  checks (see SKILL.md, optional Drive sync).
- `bullets.md`: one `## Position` per job; one `### project:<id> — Title
  (Tech), Term  [variants]` per project with optional `link:`, `demo:` and
  `context:` lines; one `### <id>  [tags]` per bullet with the text on the
  next line. Experience bullet IDs are `<slot>-<n>`, where `<slot>` is a
  short lowercase name for the position (`acme-1`), and the same slot name
  goes in `profile.yaml`.
- `skills.md`: `## Category` headings with `- item` lines. Include every
  item on every source resume's skills lines, plus the languages and tools
  its bullets and project headers name (Go, PyTorch), so a variant's
  default skills can list them.
- `archive.md`: older material, `-a<n>` IDs, and `@skills Label: a, b`
  lines for skills only older resumes list.

Then check and render:

```bash
python3 <SKILL_DIR>/scripts/validate_library.py <LIBRARY>
python3 <SKILL_DIR>/scripts/render_masters.py <LIBRARY>
```

Fix everything the validator reports before going on.

## 5. Build each base and show it

For each variant:

```bash
python3 <SKILL_DIR>/scripts/build_resume.py --library <LIBRARY> build --variant <v> resume-work/base-<v>
```

Each build must pass (one page, fonts embedded, no fails). If a base
warns that the page is under ~93% full, add default bullets from
`bullets.md`; if none are left, leave it short and say so. Never move
archive content into a variant's defaults to fill space; a short honest
page is fine. If it spills to two pages, remove the weakest default.

Then send the PDFs with a short summary of the library:

- the variants you made and what each is for (if their sources had two
  versions and you made one variant, say why);
- what went to `archive.md` (older positions, projects, skills), so they
  know it's available when a posting fits;
- any typos you kept.

Ask them to check the PDFs against their real resume: every bullet theirs
and word for word, dates and links right. Apply their corrections to the
library (corrections to wording replace the bullet text in place during
setup only; after setup, rewording always means a new ID).

## 6. Make it stick

Do this as soon as they confirm the bases, before any tailoring, even if
setup started from a tailoring request. In the Claude app, a library that
isn't packaged is gone when the chat ends.

- **Claude Code:** the files are already in `<SKILL_DIR>/user/`. Done.
  Suggest committing nothing from `user/` to any public repo
  (`.gitignore` already excludes it).
- **Claude app:** package the skill with their library inside it:

  ```bash
  python3 <SKILL_DIR>/scripts/package_skill.py --library resume-work/user --out resume-work
  ```

  Send them the zip it prints, and tell them: in Claude, open the skills
  settings, upload this zip as a skill, and turn off (or delete) the
  public `resume-tailor` skill so the two don't both trigger. From then
  on their library loads automatically in every chat.

## 7. Later edits

When the user says "add this bullet", "I also know Docker", or "I started
a new job":

- Draft the new entry with a **fresh ID** (next number for that prefix)
  and show it to them. Never edit or delete an existing ID; a reworded
  bullet is a new ID next to the old one.
- A new skill goes in `skills.md`. A new position needs a slot in each
  variant that should show it, plus its `## Position` section.
- Run `validate_library.py`, rebuild a base to confirm, and in the Claude
  app re-run `package_skill.py` and have them upload the new zip
  (replacing the old one).
