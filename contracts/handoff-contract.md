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

## Stage outputs

| Stage | Output |
|---|---|
| Outliner | output/book_outline.md |
| Researcher | output/research_pack.md |
| Chapter Planner | output/chapter_plans/chXX.md |
| Drafter | output/drafts/chXX.md |
| Persona Reviewers | output/reviews/chXX_personas.md |
| Continuity Warden | output/reviews/chXX_continuity.md |
| Safety Warden | output/reviews/chXX_safety.md |
| Voice Warden | output/reviews/chXX_voice.md |
| Editor | output/final_chapters/chXX.md |
| Assembler | output/full_first_draft.md |
