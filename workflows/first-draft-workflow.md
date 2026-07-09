# Charlotte First Draft Workflow

This is the neutral first-draft workflow. It is not tied to Kiro or any other tool.

## Goal

Produce:

```text
output/full_first_draft.md
```

from:

```text
foundation/Me_OS_Foundation.md
```

## Workflow

```text
1. Read foundation material
2. Run Outliner
3. Run Researcher
4. For each chapter:
   4.1 Plan chapter
   4.2 Draft chapter
   4.3 Run persona reviewers
   4.4 Run continuity warden
   4.5 Run safety warden
   4.6 Run voice warden
   4.7 Edit chapter
   4.8 Save final chapter
5. Assemble final chapters
6. Produce full first draft
```

## Quality gate

A chapter can move to final only when:

- Persona review has no blocking issues
- Continuity review has no blocking issues
- Safety review has no blocking issues
- Voice review has no blocking issues

## Revision rule

If a review blocks the chapter:

```text
Drafter → Reviewer → Editor
```

Repeat up to the configured maximum revision count in `config.yaml`.

## Tool rule

Any AI tool may execute this workflow, provided it preserves the handoff contract.
