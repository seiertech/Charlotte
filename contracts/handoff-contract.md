# Charlotte Handoff Contract

This contract defines how agents pass work to each other.

## Standard package

Every agent handoff should include:

```yaml
book_id: charlotte
stage:
chapter_number:
chapter_title:
input_files:
output_file:
status: draft|review|blocked|approved
summary:
open_questions:
blocking_issues:
next_agent:
```

## Required rule

No agent should depend only on conversation memory.

Every important decision, draft, review, or output must be written to the repo.
Cross-chapter continuity (summaries, introduced terms, examples used, open flags)
is persisted to `output/book_state.json` so runs can resume without chat memory.

## Stage outputs

| Stage | Output |
|---|---|
| Outliner | output/book_outline.md |
| Researcher | output/research_pack.md |
| Chapter Architect | output/chapter_plans/chXX.md |
| Drafter | output/drafts/chXX.md |
| Revision Agent | output/drafts/chXX_rN.md |
| General Reviewer | output/reviews/chXX_general.md |
| Thesis Guardian | output/reviews/chXX_thesis.md |
| Example Curator | output/reviews/chXX_examples.md |
| Persona Reviewers | output/reviews/chXX_<persona>.md |
| Continuity Warden | output/reviews/chXX_continuity.md |
| Safety Warden | output/reviews/chXX_safety.md |
| Voice Warden | output/reviews/chXX_voice.md |
| Combined review | output/reviews/chXX_combined.md |
| Editor | output/final_chapters/chXX.md |
| Transition Agent | output/reviews/chXX_transition.md |
| Assembler | output/full_first_draft.md |
| Pacing Agent | output/reviews/pacing_review.md |
| Manuscript Reviewer | output/reviews/manuscript_review.md |
| Book state | output/book_state.json |
| Status | output/status.md |
| Ledger | output/ledger.jsonl |

## Revision passes

Re-review artefacts from the revision loop are suffixed with the pass number,
e.g. `output/reviews/chXX_general_r1.md`, so each attempt is auditable.
