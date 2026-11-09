# Cover letter layout and rules

## Layout (fixed by the template; don't change per posting)

1. **Name** (bold), then a bold contact line from `profile.yaml` (a plain
   location is left off; set `letter: false` on a contact to skip it)
2. Date (Month Day, Year)
3. Addressee block: hiring manager's name and title if the posting or a
   contact gives one, else "Hiring Team"; company; street address only if
   you can confirm it from the company's own site, otherwise just
   City, State. Never guess an address.
4. Salutation ending in a colon: "Dear Ms. Last Name:" when a name is
   known, else "Dear <Company> Hiring Team:"
5. Body paragraphs (below)
6. **Sincerely,** / italic signature / bold typed name

## Body: 3 or 4 paragraphs, 250–450 words, one page

- **Opening.** The exact role title, how they found it (only if known: a
  referral, a career-fair recruiter, a job board; name the person if it's
  a referral), school/major/year, and one sentence on what qualifies them
  most.
- **Why me (2nd).** Connect the posting's needs to their background. Don't
  restate the resume: pick ONE project or accomplishment and expand on it
  with the detail a bullet can't hold.
- **Why this company (3rd, optional).** Tie their real interests and
  experience to something specific about this company (product, mission,
  a named team from the posting). Skip it rather than write generic praise.
- **Closing.** Restate interest, ask for an interview, thank the reader,
  give phone and email.

## Integrity rules (same spirit as reframe-rules.md)

- Every factual claim must trace to the library (`bullets.md`,
  `archive.md`) or something the user has said in conversation. Expanding
  a bullet means explaining it in prose, not adding metrics, tools, or
  outcomes it doesn't contain.
- Don't claim feelings or stories they haven't stated ("the hardest part
  was...", "I've used your product for years"). Statements of interest in
  the company's work are fine; say in the summary which sentences are
  theirs to check.
- Never address a gap by implying experience. If the posting stresses
  something they lack, leave it out, or frame it as something they're
  ready to learn only if they ask for that.

## letter.json

```json
{
  "company": "Acme",
  "role": "Software Engineer Intern",
  "date": "November 8, 2026",
  "addressee": ["Hiring Team", "Acme", "San Jose, CA"],
  "salutation": "Dear Acme Hiring Team:",
  "paragraphs": ["Opening ...", "Why me ...", "Why Acme (optional) ...", "Closing ..."]
}
```

`date` is optional and defaults to today.
