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
date. It can't add a position, move sections, or change the header.

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
