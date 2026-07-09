# Manuscript Acceptance Gate

The assembled first draft is accepted for human review only when it passes these book-level checks. This gate runs after every chapter has passed the Chapter Acceptance Gate and the manuscript is assembled.

## Required artefacts

```text
output/full_first_draft.md
output/book_outline.md
output/reviews/manuscript_review.md
output/reviews/pacing_review.md
output/status.md
```

## Book-level quality checks

- The central thesis is delivered from opening to close.
- No chapter contradicts an earlier chapter.
- Terminology is consistent across the whole book.
- Reveal order holds: no chapter teaches a later chapter's idea early.
- No two chapters are redundant.
- Every idea promised in the outline is delivered.
- Pacing holds at book scale: the middle does not sag, the ending is not rushed.
- The calm mentor voice is consistent from first chapter to last.
- Every chapter ends with a meaningful transition into the next.
- The book lands: the final chapter gives the reader somewhere to stand.

## Automatic block conditions

Block the manuscript if:

```text
output/reviews/manuscript_review.md   contains  status: BLOCK
output/reviews/pacing_review.md        contains  status: ADJUST (unresolved)
```

or if any chapter is still marked BLOCKED in output/status.md.

## Human review note

For Alpha, the orchestrator writes the manuscript review and pacing review artefacts but does not automatically stop distribution. A human must read the full draft and clear the gate before the manuscript leaves the repository.
