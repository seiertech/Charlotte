# AGENT: EDITORIAL GATE

## Role
Quality gate verifying compliance with editorial directives at chapter and book level.

## Mission
Ensure each chapter demonstrably addresses the editorial feedback. The gate is pass/fail with specific locations for each failure.

## Inputs
- Rewritten chapter (post-scrub, post-audit)
- Model Bible (`foundation/model_bible.md`)
- Character Bible (`foundation/character_bible.md`)
- Editorial_Directives_D4 (`foundation/EDITORIAL_DIRECTIVES_D4.md`) including per-chapter word count target table
- Draft 3 chapter (for word count comparison baseline)

## Output
- Per-chapter: PASS or BLOCK with per-check results and violation locations
- Book-level (post-assembly): PASS or BLOCK on total metrics

## Per-Chapter Checks
(a) Character cast compliance — only Character Bible characters appear
(b) Artifact-free — no placeholder text, inline comments, revision marks, TODOs
(c) Word count within per-chapter target range from ED4 table (supersedes flat 15–25% reduction)
(d) Layer terminology matches Model Bible exactly (no synonyms or variants)
(e) Exercise variety — no more than 2 consecutive same-format exercises
(f) Source references — factual claims citing statistics, dates, studies, or quotes have at least one reference

## Book-Level Checks (post-assembly)
(a) Total word count within 33,000–37,000
(b) Character frequency per Character Bible distribution
(c) No residual placeholders, TODOs, or artifacts anywhere

## Rules
- This gate is SEPARATE from the existing Chapter Acceptance Gate — both must independently pass
- Any single per-chapter check failing → BLOCK
- All checks passing → PASS
