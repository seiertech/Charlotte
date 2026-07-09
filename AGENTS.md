# Charlotte Agent Operating Model

Charlotte is agent-agnostic.

These agents are role definitions, not bindings to any specific AI tool.

Any executor may run them:

- Kiro
- Codex
- Claude Code
- Cursor
- GitHub Actions
- n8n
- Local Python runner
- Future agent platform

## Agent roster

### Structure and content
1. **Outliner** — turns the foundation into a numbered chapter plan for the whole book.
2. **Researcher** — builds a concept/research pack per chapter for the Drafter.
3. **Chapter Architect** — designs the structure of a single chapter before drafting.
4. **Drafter** — writes one complete chapter from the plan and research.
5. **Revision Agent** — rewrites a chapter to resolve blocking review notes.
6. **Editor** — polishes the accepted chapter without re-architecting it.
7. **Transition Agent** — tunes chapter openings and closings for narrative pull.
8. **Assembler** — stitches final chapters into the full draft (handled by the orchestrator).

### Reviewers and guardians
9. **General Reviewer** — is the chapter good enough to proceed.
10. **Thesis Guardian** — does the chapter serve the book's central argument.
11. **Example Curator** — are examples concrete, varied, and not repeated.
12. **Continuity Warden** — sequence, reveal order, terminology.
13. **Safety Warden** — responsible handling of vulnerable/emotional material.
14. **Voice Warden** — calm mentor voice and readability.
15. **Persona Reviewers** — skeptic, overwhelmed, young reader, elder, literal, vulnerable.

### Book-level
16. **Pacing Agent** — arc and rhythm across the whole book.
17. **Manuscript Reviewer** — final book-level review after assembly.

## Core chapter sequence

```text
Chapter Architect
  -> Drafter
  -> Review pass (General, Thesis, Example Curator, Personas, Continuity, Safety, Voice)
  -> Revision loop on BLOCK (Revision Agent, up to max_revisions)
  -> Editor
  -> Transition Agent
  -> Book state checkpoint
```

## Book-level sequence

```text
Assemble final chapters
  -> Pacing Agent
  -> Manuscript Reviewer
  -> Manuscript Acceptance Gate (human)
```

## Rule

Agents communicate through files and contracts, not hidden chat memory.

Each agent must read the declared inputs, produce the declared output, and hand
off to the next stage through the repository structure. Cross-chapter continuity
lives in `output/book_state.json`.

## Source of truth

The book source of truth is:

```text
foundation/Me_OS_Foundation.md
```

## Generated content

Generated content must remain under:

```text
output/
```

## Do not

- Do not bind the workflow to Kiro.
- Do not assume a specific model provider.
- Do not collapse all roles into one prompt.
- Do not overwrite foundation material.
- Do not store critical workflow state only in chat.
