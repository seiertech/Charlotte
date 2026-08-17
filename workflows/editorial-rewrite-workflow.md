# Charlotte Editorial Rewrite Workflow

This is the neutral editorial rewrite workflow. It is not tied to Kiro or any other tool.

## Goal

Produce:

```text
output/full_fourth_draft.md
output/author_actions.md
output/draft4/chXX.md (per chapter)
```

from:

```text
output/draft3/ or output/final_chapters/ (Draft 3 chapters)
foundation/Me_OS_Foundation.md
foundation/DRAFT3_DIRECTIVES.md
foundation/EDITORIAL_DIRECTIVES_D4.md
```

## Workflow

```text
1. Validate prerequisites
   - EDITORIAL_DIRECTIVES_D4.md exists and contains all 7 required sections
   - Per-chapter word count target table is present
   - Model Bible and Character Bible exist (or will be generated)
   - Draft 3 chapters exist in output/draft3/ or output/final_chapters/

2. Bible Creation
   2.1 Generate Model Bible      -> foundation/model_bible.md
   2.2 Generate Character Bible  -> foundation/character_bible.md

3. Chapter Rewrite Loop (for each chapter):
   3.1 Author Gate check (Introduction only):
       - If foundation/author_note.md missing or insufficient → mark WAITING_HUMAN, skip to next
   3.2 Rewrite Agent             -> output/draft4/chXX_raw.md
       - Inputs: Draft 3 chapter, Model Bible, Character Bible,
         EDITORIAL_DIRECTIVES_D4, DRAFT3_DIRECTIVES, Foundation,
         preceding Draft 4 chapter (or Foundation alone for Ch0)
   3.3 Evidence Agent            -> output/draft4/chXX_evidenced.md
       - Scan for unsourced claims; insert references, qualifiers, or [NOTE TO AUTHOR] markers
       - Produce evidence log at output/draft4/chXX_evidence_log.md
   3.4 Artifact Scrubber         -> output/draft4/chXX_scrubbed.md
       - Remove production artifacts; preserve [Author's note] in Introduction
   3.5 Continuity Auditor        -> output/reviews/chXX_continuity_d4.md
       - Verify character, layer, and currency consistency against bibles
       - On BLOCK → enter revision loop
   3.6 Editorial Gate            -> output/reviews/chXX_editorial_d4.md
       - Per-chapter checks: character cast, artifact-free, word count within
         per-chapter target range, layer terminology, exercise variety, sourced claims
       - On BLOCK → enter revision loop
   3.7 Revision loop (on BLOCK from Auditor or Gate):
       - Feed violations back to Rewrite Agent → re-run from step 3.2
       - Repeat up to editorial_rewrite.max_revisions (default 3)
       - If max reached with BLOCK → mark chapter FAILED, continue to next
   3.8 On PASS → mark chapter editorial_pass
       - Record in state file; produce output/draft4/chXX.md

4. Assembly
   - Stitch all passing chapters -> output/full_fourth_draft.md

5. Author Action Log generation
   - Scan assembled manuscript for all [NOTE TO AUTHOR: ...] markers
   - Produce consolidated table  -> output/author_actions.md
     (chapter, location, category, explanation, summary counts by category)

6. Book-level Editorial Gate
   - Total word count within 33,000–37,000
   - Character frequency per Character Bible
   - No residual placeholders across entire manuscript

7. Write status                  -> output/status_d4.md
   - Chapter counts per status, blocked/waiting details
```

## Chapter quality gates

A chapter can move to final only when BOTH of the following pass independently:

- **Chapter Acceptance Gate** (existing) — standard quality checks
- **Editorial Gate** (new) — editorial directive compliance checks

Both gates must independently pass. They may execute in any order.

If either gate blocks the chapter, the revision loop is triggered.

## Revision rule

If the Continuity Auditor or Editorial Gate blocks the chapter:

```text
Rewrite Agent (with violation feedback) → Evidence Agent → Artifact Scrubber → Continuity Auditor → Editorial Gate
```

Repeat up to `editorial_rewrite.max_revisions` in `config.yaml` (default: 3).

If revisions are exhausted while still BLOCK, the chapter is marked FAILED
in the state file and `output/status_d4.md`, then flagged for human review.
The pipeline continues to the next chapter.

## Resume rule

Runs are resumable. Chapters with status `editorial_pass` in
`output/draft4_state.json` are skipped unless `--no-resume` is passed or
`editorial_rewrite.resume` is false.

If the state file is missing on resume, all chapters are treated as pending.

## Tool rule

Any AI tool may execute this workflow, provided it preserves the handoff contract.
