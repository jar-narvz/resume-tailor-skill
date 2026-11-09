# resume-tailor

A Claude skill that tailors your resume to a job posting and hands back a
one-page PDF. It only picks and reorders bullets from your own library, so
a tailored resume can never claim more than you wrote.

![The same made-up candidate's base resume (left) and the version tailored to a backend posting (right)](docs/before-after.png)

*Left: the example candidate's base resume. Right: tailored to
[a backend posting](examples/sample-posting.md) with
[this plan](examples/sample-plan.json). The distributed-systems project
moved to the top, the posting's stack leads each skills line, and one
bullet was reordered to put PostgreSQL first. No new words were added.*

## Install

**Claude app (claude.ai, desktop, mobile).** Skills need code execution
turned on in your settings.

```bash
git clone https://github.com/jar-narvz/resume-tailor-skill
cd resume-tailor-skill
python3 scripts/package_skill.py --no-library --out .
```

Upload the `resume-tailor.zip` it creates as a skill in Claude's settings.

**Claude Code.**

```bash
git clone https://github.com/jar-narvz/resume-tailor-skill ~/.claude/skills/resume-tailor
pip install pyyaml pikepdf
```

## First run: setup

Start a chat and say something like *"set up my resume"*, or just share a
job posting. With no library yet, the skill runs setup first
([references/setup.md](references/setup.md)):

1. It asks for your current resume (PDF, .docx, Google Doc, or pasted
   text) and any older versions.
2. It copies every bullet **word for word** into a library, with older
   wordings and old resumes' content kept in an archive.
3. It asks up to four questions: which base resumes ("variants") you want,
   what each shows by default, the font, and your graduation date.
4. It builds each base resume and shows you the PDFs to check.
5. **Claude Code:** your library is saved in `user/` inside the skill
   folder, and you're done. **Claude app:** the workspace resets between
   chats, so it packages a copy of the skill with your library inside and
   asks you to upload that zip in place of the public one.

Your library never leaves your machine or your Claude account, and
`user/` is in `.gitignore`.

## Usage

- Paste a job link: *"https://job-boards.greenhouse.io/acme/jobs/123"*
- Paste the description: *"Tailor my resume to this: …"*
- Name the role: *"Tailor my resume for the Globex backend intern role"*
- Ask for a cover letter: *"…and write a cover letter, a recruiter at the
  career fair referred me."*
- Add to your library: *"Add a bullet: I cut our CI time from 20 to 8
  minutes by caching Docker layers."*

Each run returns the PDF and its `.tex`, a short summary (which base, what
changed, what the posting asks for that you don't have), and a
comma-separated keyword list to paste into the application's skills field.

## Requirements

- **xelatex** (TeX Live or MacTeX) and **poppler** (`pdfinfo`,
  `pdffonts`, `pdftotext`)
- **Python 3** with `pyyaml` and `pikepdf`

The Claude app's code environment already has these. On a Mac for Claude
Code:

```bash
brew install --cask mactex-no-gui
brew install poppler
pip install pyyaml pikepdf
```

On Debian or Ubuntu: `sudo apt install texlive-xetex fonts-texgyre poppler-utils`.

Try it without setting anything up (uses the made-up example library):

```bash
python3 scripts/validate_library.py examples
python3 scripts/build_resume.py --library examples build examples/sample-plan.json out
```

## How it works

```
profile.yaml ─┐
bullets.md   ─┼─> plan.json ─> build_resume.py ─> xelatex ─> checks ─> PDF + .tex
skills.md    ─┤   (Claude       (validate, compose)          (1 page, fonts,
archive.md   ─┘    writes it)                                 text layer, fill)
```

Your library is four plain-text files:

| File | Holds |
|---|---|
| `profile.yaml` | Header, education, font, and your **variants**: base resumes with a section order, experience entries, and default bullets, projects and skills |
| `bullets.md` | Every bullet, each with a stable ID (`acme-3`) |
| `skills.md` | Every skill you can speak to |
| `archive.md` | Content from older resumes, usable but never a default |

For each posting Claude reads the job description, picks the closest
variant, and writes a small **plan**: which projects in which order, which
bullets by ID, and the skills lines. `build_resume.py` validates the plan
against the library, fills the variant's template, compiles it with
xelatex, and checks the PDF. Any check that fails stops the build; Claude
fixes the plan and rebuilds rather than delivering a broken resume. See
[examples/](examples/) for a complete library, posting, plan and output.

## Design decisions

**Library-only bullets.** A plan can name bullets by ID or reframe one,
nothing else. AI-written resume bullets tend to drift toward whatever the
posting asks for, and you're the one who has to answer for every line in
an interview. Tailoring is mostly choosing and ordering anyway.
I built this for my own internship search, where I apply to a lot of
roles. I had already cut C++, REST APIs and Tableau from my resume when I
couldn't back them up in an interview, and I wanted tailoring that could
never quietly add claims like those back.

**Verbatim validation.** A reframe may reorder clauses, swap the leading
verb from a short list, or trim. The build rejects any word whose stem
isn't in the original, any changed number, and any growth over three
words ([reframe-rules.md](references/reframe-rules.md)). Skills face the
same check against your inventory. A rule enforced in code holds up
better than an instruction the model might forget.

**The fill check.** A one-page resume that stops halfway looks thin. When
the content ends at 93–97% of the page, the build stretches the vertical
spacing evenly to the bottom margin. Below 93% it asks for more content
instead, because big gaps look like padding.

**An ATS-safe text layer.** Applicant tracking systems read the PDF's
text, not its picture. The class turns off ligatures (so "fi" doesn't
extract as one glyph), writes a real space character for every visible
space (some parsers glue words otherwise), and embeds every font. The
build checks that each bullet can be recovered from the extracted text.
It also fixes a Times New Roman quirk: the font shares one glyph between
`;` and the Greek question mark (U+037E), and XeTeX labels it as the Greek
character, so every semicolon would reach the ATS as a stray symbol. The
build relabels it in the PDF.
I tested the output by checking each PDF's extracted text and by running
it through Affinda's resume parser. That caught two problems this layout
now avoids. In some parsers, words ran together because the PDF had no real
space characters. And Affinda filed a job title that started with a term
label as a certification instead of a job, so keep labels like that at the
end of a title, in parentheses.

**TeX Gyre Termes instead of bundled fonts.** Times New Roman's license
doesn't allow redistributing the font files, so the default is TeX Gyre
Termes, a free Times clone that ships with TeX Live. On the author's own
resumes it produced the same line breaks and page fill as Times New Roman.
Set `font: times-system` to use Times New Roman installed on your
computer.

**Profile-driven templates.** Header, education and section order live in
`profile.yaml`, and each variant's template is rendered from it on every
build. One edit to your phone number or dates updates every variant, and
there's no hand-maintained LaTeX to get out of sync.

## Limitations

- **One layout.** A single-column, Times-style resume. Changing the look
  means editing `assets/resume.cls`.
- **LaTeX required.** The build needs xelatex, which is a large install
  outside the Claude app.
- **US-letter, one page,** and English-language section names.
- **One school's graduation date is checked.** Additional schools render
  fine but aren't checked.
- **The optional Google Doc sync is manual.** Claude compares the doc
  with your library and shows you the differences; you confirm each
  addition.

## License

[MIT](LICENSE) © 2026 Jared Narvaez
