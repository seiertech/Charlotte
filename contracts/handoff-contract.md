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


## Rewrite Stage

Stage outputs for the editorial rewrite pipeline (Draft 3 → Draft 4):

| Stage | Producing Agent | Consuming Agent(s) | Output Path |
|-------|----------------|--------------------|--------------------|
| Model Bible | Bible Generator | Rewrite Agent, Continuity Auditor, Editorial Gate | `foundation/model_bible.md` |
| Character Bible | Bible Generator | Rewrite Agent, Continuity Auditor, Editorial Gate | `foundation/character_bible.md` |
| Chapter Rewrite | Rewrite Agent | Evidence Agent | `output/draft4/chXX_raw.md` |
| Evidenced Chapter | Evidence Agent | Artifact Scrubber | `output/draft4/chXX_evidenced.md` |
| Evidence Log | Evidence Agent | Editorial Gate, Author Action Log | `output/draft4/chXX_evidence_log.md` |
| Scrubbed Chapter | Artifact Scrubber | Continuity Auditor | `output/draft4/chXX_scrubbed.md` |
| Continuity Report | Continuity Auditor | Rewrite Agent (on BLOCK) | `output/reviews/chXX_continuity_d4.md` |
| Editorial Report | Editorial Gate | Rewrite Agent (on BLOCK) | `output/reviews/chXX_editorial_d4.md` |
| Final D4 Chapter | Pipeline | Assembler | `output/draft4/chXX.md` |
| Assembled Draft 4 | Assembler | Book-level Editorial Gate | `output/full_fourth_draft.md` |
| Author Action Log | Pipeline (post-assembly) | Author | `output/author_actions.md` |
| Draft 4 State | Pipeline | Resume logic | `output/draft4_state.json` |
| Draft 4 Status | Pipeline | Human review | `output/status_d4.md` |

### Rewrite stage package fields

```yaml
book_id: charlotte
stage: rewrite
chapter_number: <int>
input_files: [...]
output_file: <path>
status: PENDING | IN_PROGRESS | COMPLETE | FAILED | WAITING_HUMAN
next_agent: <agent_name>
```
