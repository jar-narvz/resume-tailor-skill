# Variants

A variant is a base resume: one way of presenting the same person for a
family of roles. Most people need two (for example `swe` and `ml`); some
need one, a few need three. Every variant draws from the same bullet
library, so a project or bullet can appear on any of them.

## What a variant fixes

Defined under `variants:` in `profile.yaml`:

| Key | What it controls |
|---|---|
| `label`, `use_for` | Human-readable name and the roles it's for. Step 2 of SKILL.md reads `use_for` to pick a variant |
| `section_order` | Order of `education`, `experience`, `projects`, `skills`. A plan can't change it |
| `experience` | Which positions appear, in order, with title, dates, org, location and `default_bullets` |
| `default_projects` | Projects and their bullets, in order, when a plan doesn't name projects |
| `default_skills` | Skills lines (label → items) when a plan doesn't give skills |

Per posting, a plan can swap bullets, reorder and swap projects, rewrite
the skills lines (from the inventory), and pick an alternate graduation
date. It can append positions with `add_experience`; it can't remove or
reorder the base's positions, move sections, or change header facts.

## Adding a position for one posting

`profile.yaml` may have a top-level `extra_experience` list for positions
no variant shows by default. Each entry uses the same keys as a variant's
experience entry: `slot`, `title`, `dates`, `org`, optional `org_url` and
`location`, and `default_bullets`. Its bullets live in `bullets.md`, with
the slot as their ID prefix. Extra slots must be unique and cannot also
appear in any variant; a slot shared by several variants remains legal.
Archive bullets cannot be defaults.

A plan can use `"add_experience": ["harbor"]` to append that position, or
one shown only on another variant. Additions follow the base's positions
in list order. Lookup checks `extra_experience` first, then variants in
profile order; the first match supplies both the header and defaults.
`"experience": {"harbor": ["harbor-2"]}` overrides its bullets. Without
that override, its `default_bullets` are used. Every added position needs
at least one bullet from its own slot, and the base's effective section
order (all sections when omitted) must include experience.

`add_experience` must be a list of unique strings. Unknown slots, slots
already on the base, and an `experience` override for a slot neither on
the base nor in `add_experience` fail. Mention added positions from the
build summary's `added_experience` list when delivering the resume.

## Picking a variant (step 2)

1. Read each variant's `use_for`. Pick the one whose roles match the
   posting's title and first-listed requirements.
2. If two fit, pick the one whose `section_order` puts the posting's
   strength first (a skills-forward ML base for a research-y ML role;
   an experience-forward base for a backend role).
3. If none fits well, use the closest one and say so in the summary.
   Suggest a new variant only if the same mismatch keeps happening.

## Designing variants (setup)

- **Start from the user's real resumes.** If they already keep two
  versions, those are the two variants.
- **Differences should be about emphasis, not truth.** Variants reorder
  and select; they never hold different claims about the same work.
- **Section order is the main lever.** Put skills near the top for roles
  where keyword match matters most (ML, data, research), and experience
  first for general engineering roles.
- **Defaults should fill the page.** Aim for a default build at 95–100%
  page fill so most plans only swap content, not add it. The build's
  `page_fill_pct` tells you where it ends.
- **Every experience position needs at least one bullet** on every
  variant that shows it. A position can be left off a variant entirely.

## Alternate graduation dates

Some programs (co-ops, extra terms) change the expected graduation for a
subset of applications. List extra dates under
`education[0].alt_graduations`, and a plan picks one with
`"graduation": "<date>"`. Mention it in the summary whenever a non-default
date is used.

## Bullet IDs and slots

An experience bullet's ID prefix is its slot: `acme-3` and `acme-a1`
belong to the `acme` slot, and only fit under that position. Project
bullets belong to the project they're listed under in `bullets.md`.
Reworded bullets get a new ID next to the old one (`acme-6` replacing
`acme-2`), and the old one stays so earlier plans still build. Never put
two wordings of one bullet on a page.
