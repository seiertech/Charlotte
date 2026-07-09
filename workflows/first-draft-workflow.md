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
2. Run Outliner            -> output/book_outline.md
3. Run Researcher          -> output/research_pack.md
4. For each chapter:
   4.1 Chapter Architect    -> plan the chapter structure
   4.2 Drafter              -> write the first draft
   4.3 Review pass (all enabled reviewers run together):
        - General Reviewer
        - Thesis Guardian
        - Example Curator
        - Persona Reviewers (skeptic, overwhelmed, young reader, elder, literal, vulnerable)
        - Continuity Warden
        - Safety Warden
        - Voice Warden
   4.4 Revision loop: if any review returns BLOCK,
       Revision Agent rewrites -> re-review.
       Repeat up to workflow.max_revisions.
   4.5 Editor               -> final chapter polish
   4.6 Transition Agent     -> fix opening/closing pull
   4.7 Validate word count against workflow.chapter_word_target
   4.8 Record chapter in book state and checkpoint
5. Assemble final chapters -> output/full_first_draft.md
6. Book-level review:
   - Pacing Agent           -> output/reviews/pacing_review.md
   - Manuscript Reviewer    -> output/reviews/manuscript_review.md
7. Write status            -> output/status.md
```

## Chapter quality gate

A chapter can move to final only when its review pass has no unresolved
blocking issues from:

- General Reviewer
- Thesis Guardian
- Persona reviewers
- Continuity, Safety, and Voice wardens

If revisions are exhausted while still BLOCK, the chapter is marked BLOCKED
in `output/status.md` and flagged in the book state for human review.

## Revision rule

If any review blocks the chapter:

```text
Revision Agent -> re-review
```

Repeat up to `workflow.max_revisions` in `config.yaml`. Safety blocks must
always be resolved and are never deferred.

## Manuscript gate

After assembly, the book must clear `quality/MANUSCRIPT_ACCEPTANCE_GATE.md`
before a human accepts the draft.

## Resume

Runs are resumable. Completed chapters (recorded in `output/book_state.json`
with a final artefact) are skipped unless `--no-resume` is passed or
`workflow.resume` is false.

## Tool rule

Any AI tool may execute this workflow, provided it preserves the handoff contract.
