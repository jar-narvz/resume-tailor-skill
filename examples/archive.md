# Archive (example: Alex Rivera, a made-up person)

Bullets and skills from older resumes that aren't in `bullets.md`. The
build accepts them by ID exactly like library bullets, but never as
defaults: a plan only gets one by naming it. The summary lists every
archive item used so you can confirm it's still accurate.

Format the build parses:
- `@skills <Label>: a, b, c` adds skills you've listed before.
- `## <Position>` and `### <id>  [tags]` add experience bullets. Archive IDs
  use `-a<n>` (`acme-a1`); the prefix decides which experience slot they fit.
- `### project+:<id>` adds archive bullets to a project that's in `bullets.md`.

## Skills

@skills Frameworks & Tools: Flask, MongoDB, Tableau
@skills Concepts: Data Visualization, Agile

## Acme Corp, Software Engineering Intern (older wording)

### acme-a1  [python, backend, archive]
Wrote a Python job that syncs warehouse inventory into PostgreSQL every night.

## Projects

### project+:proj-chat

### chat-a1  [flask, mongodb, archive]
Built the first version of the chat backend in Flask with MongoDB before moving it to Node.js.
