# Reframe rules

A reframe is the one way a tailored resume's wording can differ from the
library. It exists so the posting's key term can move into the first half
of a line a recruiter skims. It is not a rewrite.

## Allowed

- **Reorder clauses** of the original bullet so the posting's technology
  or concept comes first.
- **Swap the leading verb** for another from this list: Built, Designed,
  Developed, Engineered, Implemented, Created, Wrote, Led, Managed,
  Maintained (and their present-tense forms for current roles).
- **Drop a clause** to save a line, as long as what remains is still true
  on its own.
- Small connectors (and, the, with, using, via, across, ...) to stitch the
  reordered clauses together.

## Not allowed (the build rejects these)

- Any word whose stem isn't already in the original bullet, apart from the
  verb list and connectors above. That rules out new technologies, new
  mechanisms, and new scope words ("distributed", "production",
  "scalable") in one check.
- Changing, adding, or removing a number. Every metric (40+, 92%, 3 hours,
  1,000 trials) is a real measurement.
- Growing the bullet by more than three words.

## Why this is strict

The user has to defend every line in an interview. A reframe that slips in
a posting's buzzword is exactly the failure this skill exists to prevent.
If a posting keyword isn't in any of their bullets, say it's a gap in the
summary instead. That's more useful to them than hiding it.

If the user says in conversation that they did something that isn't in
the library, offer to add it to `bullets.md` as a new ID before using it
(see "Maintaining the library" in SKILL.md). Don't slip it into a reframe.

## Example

Original `acme-1`:
> Built a Python service that batches inventory updates from 40+
> warehouses into PostgreSQL, cutting nightly sync time from 3 hours to
> 25 minutes.

Valid reframe for a posting that leads with PostgreSQL:
> Built a Python service that batches inventory updates into PostgreSQL
> from 40+ warehouses, cutting nightly sync time from 3 hours to 25 minutes.

Rejected: "Built a scalable distributed Python service that ...", because
"scalable" and "distributed" aren't in the original.
