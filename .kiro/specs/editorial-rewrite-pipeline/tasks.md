# Implementation Plan: Editorial Rewrite Pipeline

## Overview

This plan implements the editorial rewrite pipeline as an additive extension to the Charlotte Book Factory. The pipeline transforms Draft 3 (~25k words) into Draft 4 (~35k words) by applying consolidated editorial feedback through a sequence of agents (Rewrite Agent → Evidence Agent → Artifact Scrubber → Continuity Auditor → Editorial Gate), governed by a Model Bible and Character Bible, with full resumability and state tracking.

Key changes from the original plan: the pipeline now **expands** the manuscript by ~10,000 words (targeting 33k–37k total) using per-chapter word count targets instead of a flat 15–25% reduction. A new Evidence Agent provides a credible evidentiary spine. Chapter 9 receives a restructured constraint taxonomy (5 categories). Chapter 10 gets a faith/trust distinction paragraph. All human-dependent points are marked with `[NOTE TO AUTHOR: <CATEGORY> — <explanation>]` markers, consolidated into `output/author_actions.md` after assembly.

The implementation follows the existing Charlotte conventions: file-driven, agent-agnostic, contract-based, with markdown agent definitions, YAML configuration, and a Python orchestrator.

## Tasks

- [ ] 1. Create foundation documents and editorial directives template
  - [ ] 1.1 Create `foundation/EDITORIAL_DIRECTIVES_D4.md` with all required sections
    - Create the editorial directives document with the 7 required named sections: Character Consolidation Rules, Repetition-Reduction Targets, Production-Artifact Definitions, Author-Presence Insertion Points (6–8 across book), Sourcing Requirements, Layer-Boundary Clarifications, and Taxonomy-Reframing Guidance
    - Include the **per-chapter word count target table** specifying D3 word count, D4 target min, and D4 target max for each of the 13 chapters (total target: 33,000–37,000 words)
    - Include the **Chapter 9 specific directive** for constraint taxonomy rewrite with 5 categories: immutable constraint, currently constrained, externally imposed constraint, changeable-but-costly constraint, and unsafe situation
    - Include the **Chapter 10 specific directive** instructing the Rewrite Agent to retain "faith" as the primary term and insert a faith/trust distinction paragraph (100–200 words) within the first 500 words of the chapter body
    - The Author-Presence Insertion Points section must define 6–8 insertion points specifying chapter and location
    - _Requirements: 1.1, 1.2, 1.5, 1.6, 8.5, 14.6, 16.1, 17.1_

  - [ ] 1.2 Create `foundation/model_bible.md` with the full taxonomy structure
    - Define each of the 5 layers (Body, Wiring, Habit, Room, Story) with: one-sentence definition (max 30 words), includes list, excludes list, diagnostic test (yes/no question), and "commonly confused with" section for each adjacent layer
    - Define each of the 3 currencies (Charge, Fuel, Pressure) with: one-sentence definition (max 30 words), manifestation per layer, and comparison statement vs each other currency
    - Include the diagnostic sequence with recommended evaluation order and feedback loops
    - Include the Wiring-vs-Story discrimination test with at least two differentiating yes/no criteria
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 1.3 Create `foundation/character_bible.md` with fixed cast and appearance map
    - Define 4–5 recurring characters each with: name, age, occupation, life situation, primary layer, secondary layer (if applicable), physical signature (one sensory detail), and "what they carry" sentence
    - Include a chapter-appearance map (13 chapters) with P (primary) / S (secondary) / — (absent) indicators
    - Ensure no single character exceeds 40% of chapter-level appearances
    - Assign at least one character to each of the 5 layers as their primary demonstration vehicle
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 2. Create agent definition files
  - [ ] 2.1 Create `agents/rewrite_agent.md` agent definition
    - Use Charlotte's standard heading structure: `# AGENT: REWRITE AGENT` with ## Role, ## Mission, ## Inputs, ## Output, ## Rules sections
    - Inputs section must list: Draft 3 chapter, Model Bible, Character Bible, Editorial_Directives_D4, DRAFT3_DIRECTIVES, Foundation, preceding Draft 4 chapter (or Foundation alone for Ch0)
    - Output section must define: rewritten chapter followed by rewrite log with changes per directive, word count before/after, characters used, and unresolved issues
    - Rules section must reference Model Bible and Character Bible as authoritative sources, specify **per-chapter word count targets from ED4 table** (replacing flat 15–25% reduction), exercise variety constraint (no more than 2 consecutive same format), character replacement rules, sourcing requirements, and `[NOTE TO AUTHOR]` marker format
    - Rules section must include: Chapter 9 constraint taxonomy application (5 categories), Chapter 10 faith/trust paragraph insertion (100–200 words within first 500 words), and new content limited to mechanism explanations, failure modes, hard cases, counterexamples, and model limitations
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 12.1, 12.4, 12.5, 14.2, 14.3, 14.4, 16.2, 16.3, 17.2, 17.3, 18.1_

  - [ ] 2.2 Create `agents/evidence_agent.md` agent definition
    - Use Charlotte's standard heading structure: `# AGENT: EVIDENCE AGENT` with ## Role, ## Mission, ## Inputs, ## Output, ## Rules sections
    - Role: Scan rewritten chapters for unsourced psychological, neurological, behavioural, and health-related claims; insert source references or qualifying phrases; flag unfixable claims
    - Inputs section: rewritten chapter from Rewrite Agent (`output/draft4/chXX_raw.md`)
    - Processing: identify unsourced claims → insert lightweight inline reference to established source OR add qualifying phrase OR flag with `[NOTE TO AUTHOR: SOURCE_NEEDED — <specific claim text>]` marker
    - Output section: evidenced chapter at `output/draft4/chXX_evidenced.md` + evidence log listing claims found, action per claim (sourced / qualified / flagged for author), and reference or qualifier added
    - Rules: SHALL NOT invent citations, fabricate study names, or attribute claims to specific researchers without verification; references must be to established, well-known findings only
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 12.4, 12.5, 18.3_

  - [ ] 2.3 Create `agents/artifact_scrubber.md` agent definition
    - Use Charlotte's standard heading structure: `# AGENT: ARTIFACT SCRUBBER`
    - Inputs section: evidenced chapter file (output of Evidence Agent, replacing raw rewrite)
    - Include pattern list enumerating 5 artifact types: EDITOR FLAG, [Author's note] placeholders, outline-style headers (`## <phrase> purpose:`), chapter misnumbering, internal YAML/code blocks with workflow keys
    - Define actions per pattern: remove (general) or preserve-and-flag ([Author's note] in Introduction → route to Author_Gate)
    - Output section: clean chapter + artifact removal log (type, line number, snippet up to 120 chars, action taken)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 12.2, 12.4, 12.5_

  - [ ] 2.4 Create `agents/continuity_auditor.md` agent definition
    - Use Charlotte's standard heading structure: `# AGENT: CONTINUITY AUDITOR`
    - Inputs section: rewritten chapter, Model Bible, Character Bible
    - Checks section enumerating: character-existence verification, layer/currency name matching (case-sensitive exact match), character-detail consistency, reveal-order compliance (no premature appearances)
    - Additional check for Chapter 9: verify constraint categories match those defined in Editorial_Directives_D4 Chapter 9 directive (5 categories)
    - BLOCK/PASS criteria: any continuity violation → BLOCK with violation type, offending text, chapter location, expected value
    - Output section: status report with status field and violation list
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 12.3, 12.4, 12.5, 16.4_

  - [ ] 2.5 Create `agents/editorial_gate.md` agent definition
    - Use Charlotte's standard heading structure: `# AGENT: EDITORIAL GATE`
    - Per-chapter checks: (a) character cast compliance, (b) artifact-free status, (c) **word count within per-chapter target range from ED4 table** (supersedes flat 15–25% reduction), (d) layer terminology matches Model Bible, (e) exercise variety, (f) factual claims have source references
    - Book-level checks: **total word count within 33,000–37,000** (supersedes flat 15–25% total reduction), character frequency per Bible, no residual placeholders
    - Output: PASS or BLOCK with per-check details and chapter locations of violations
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 14.5, 14.6_

- [ ] 3. Checkpoint – Ensure foundation documents and agent definitions are complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement Rewrite State module
  - [ ] 4.1 Create `orchestrator/rewrite_state.py` with `RewriteChapterRecord` and `RewriteState` dataclasses
    - Implement `RewriteChapterRecord` dataclass with fields: number, title, status (string enum: "pending" | "rewriting" | "rewritten" | "editorial_pass" | "blocked" | "waiting_human_input"), revision_count, block_reason, blocking_agent, d3_word_count, d4_word_count, characters_used (list), output_path
    - Implement `RewriteState` dataclass with chapters list and methods: `get(number)`, `upsert(record)`, `is_editorial_pass(number)`, `save(path)`, `load(path)` (classmethod), `summary_status()` (returns counts per status category)
    - State persists to `output/draft4_state.json`; `save()` writes immediately (within 5 seconds of any status change)
    - Handle corrupted state file: raise clear error without overwriting the file
    - Handle missing state file on resume: treat all chapters as "pending"
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [ ]* 4.2 Write property test for RewriteState (Property 9: State File Reflects All Transitions)
    - **Property 9: State File Reflects All Transitions**
    - **Validates: Requirements 13.1, 13.5**
    - Use Hypothesis to generate sequences of status changes; verify state file is updated after each transition
    - Also test round-trip serialization (save → load produces identical state)

  - [ ]* 4.3 Write unit tests for RewriteState
    - Test `load()` with missing file returns all-pending state
    - Test `load()` with corrupted JSON raises clear error
    - Test `upsert()` updates existing chapter and adds new ones
    - Test `summary_status()` returns correct counts
    - Test `is_editorial_pass()` returns correct boolean
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [ ] 5. Implement Author Gate logic
  - [ ] 5.1 Implement `check_author_gate()` function in `orchestrator/rewrite_conveyor.py`
    - Function signature: `def check_author_gate(chapter_number: int) -> Tuple[bool, str]`
    - Only blocks chapter 0 (Introduction); all other chapters return `(False, "")`
    - Check `foundation/author_note.md`: must exist, contain ≥ 50 words of non-boilerplate content
    - Boilerplate patterns to detect: "Insert your note here", "TODO", "Replace this", and similar template prompts
    - Return `(True, reason)` if blocked, `(False, "")` if unblocked
    - When blocked: log block event with reason and file path in pipeline status; insert `[NOTE TO AUTHOR: PERSONAL_STORY — ...]` marker in Introduction text
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.7, 18.2_

  - [ ]* 5.2 Write property test for Author Gate (Property 7: Author Gate Blocking Condition)
    - **Property 7: Author Gate Blocking Condition**
    - **Validates: Requirements 8.1, 8.2, 8.3**
    - Use Hypothesis to generate `author_note.md` content of varying length and boilerplate ratios
    - Verify: gate blocks iff file missing OR < 50 non-boilerplate words

- [ ] 6. Implement prerequisite validation and config parsing
  - [ ] 6.1 Implement `validate_prerequisites()` in `orchestrator/rewrite_conveyor.py`
    - Check `foundation/EDITORIAL_DIRECTIVES_D4.md` exists; halt with named error if missing
    - Parse directives file and verify all 7 required sections are present; halt identifying absent sections if any missing
    - Verify per-chapter word count target table is present in ED4
    - Check `foundation/model_bible.md` and `foundation/character_bible.md` exist
    - Check Draft 3 chapters exist in `output/draft3/` or `output/final_chapters/`
    - _Requirements: 1.1, 1.6, 9.3, 14.6_

  - [ ] 6.2 Implement config loading and validation for `editorial_rewrite` section
    - Parse `editorial_rewrite` section from `config.yaml` with all required keys
    - Validate ranges: `max_revisions` (1–10), `word_reduction_target_min` (0.0–1.0), `word_reduction_target_max` (0.0–1.0, must be > min)
    - Validate `editorial_rewrite.agents` mapping includes `rewrite_agent`, `artifact_scrubber`, `continuity_auditor`, and `evidence_agent` keys pointing to agent definition files
    - Halt with error naming the missing key if any required key absent
    - _Requirements: 11.1, 11.2, 11.4_

  - [ ]* 6.3 Write unit tests for prerequisite validation and config parsing
    - Test missing directives file → halt with error
    - Test directives file missing sections → halt identifying absent sections
    - Test missing config keys → halt naming key
    - Test missing `evidence_agent` in agents mapping → halt with error
    - Test invalid ranges → appropriate error
    - _Requirements: 1.1, 1.6, 11.4_

- [ ] 7. Checkpoint – Ensure state management, author gate, and validation are solid
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement the Rewrite Conveyor orchestrator
  - [ ] 8.1 Implement `generate_model_bible()` and `generate_character_bible()` in `orchestrator/rewrite_conveyor.py`
    - `generate_model_bible()` takes config, ModelClient, Ledger; reads Foundation + DRAFT3_DIRECTIVES + ED4; produces `foundation/model_bible.md`
    - `generate_character_bible()` takes config, ModelClient, Ledger; reads Foundation + Model Bible + ED4; produces `foundation/character_bible.md`
    - Both called before any chapter rewriting begins
    - _Requirements: 2.1, 3.1, 9.2_

  - [ ] 8.2 Implement `run_rewrite_chapter()` orchestrating the chapter rewrite loop
    - Accept inputs: config, client, ledger, chapter dict, state, model_bible, character_bible, directives_d4, directives_d3, foundation, prev_d4
    - Pipeline per chapter: Rewrite Agent → **Evidence Agent** → Artifact Scrubber → Continuity Auditor → Editorial Gate
    - Revision loop on BLOCK (either auditor or gate), capped at `max_revisions` from config (default 3)
    - Track revision_count in state; if exhausted mark chapter "blocked" with reason and blocking agent
    - Update state file after each status transition
    - _Requirements: 4.1, 5.1, 6.1, 7.1, 9.2, 9.5, 9.6, 13.1, 13.5, 15.1, 15.7_

  - [ ] 8.3 Implement `main()` entry point with CLI args and full pipeline orchestration
    - CLI arguments: `--chapter N`, `--bibles-only`, `--assemble-only`, `--no-resume`
    - Load config, validate prerequisites, generate bibles (if needed)
    - Chapter loop: check author gate → run_rewrite_chapter for each chapter
    - Resume logic: skip chapters with `editorial_pass` status if `resume: true` and no `--no-resume` flag
    - Allow all chapters to proceed independently of Author Gate (only Introduction blocked)
    - _Requirements: 8.4, 9.2, 9.4, 13.2_

  - [ ] 8.4 Implement `assemble_draft4()`, author action log generation, and `run_book_level_editorial_gate()`
    - `assemble_draft4()`: stitch all passing chapters into `output/full_fourth_draft.md`
    - **Generate `output/author_actions.md`**: scan assembled manuscript for all `[NOTE TO AUTHOR: ...]` markers; produce consolidated table with chapter, location, category, and explanation for each marker; include summary counts by category
    - `run_book_level_editorial_gate()`: check **total word count within 33,000–37,000** (supersedes old 15–25% reduction), character frequency per Bible, no residual placeholders
    - Write status file at `output/status_d4.md` with chapter counts per status and blocked/waiting details
    - _Requirements: 7.5, 9.2, 9.7, 13.6, 14.5, 18.5_

  - [ ]* 8.5 Write property test for revision loop termination (Property 10: Revision Loop Termination)
    - **Property 10: Revision Loop Termination**
    - **Validates: Requirements 9.5, 9.6**
    - Use Hypothesis to generate chapter runs with BLOCK verdicts; verify loop stops at max_revisions and chapter is marked "blocked"

  - [ ]* 8.6 Write property test for resume skip behavior (Property 8: Resume Skips Passing Chapters)
    - **Property 8: Resume Skips Passing Chapters**
    - **Validates: Requirements 9.4, 13.2**
    - Use Hypothesis to generate state files with various status values; verify only non-"editorial_pass" chapters are processed

- [ ] 9. Implement directive hierarchy, Evidence Agent, and agent invocation logic
  - [ ] 9.1 Implement directive parsing and conflict resolution logic
    - Parse both `EDITORIAL_DIRECTIVES_D4` and `DRAFT3_DIRECTIVES` into structured directive sets
    - For conflicting topics: ED4 wins and conflict is logged in rewrite log
    - For topics only in DRAFT3_DIRECTIVES: continue to enforce
    - Parse per-chapter word count target table from ED4 into structured lookup
    - Pass merged directive context to Rewrite Agent prompts
    - _Requirements: 1.2, 1.3, 1.4, 4.9, 14.6_

  - [ ]* 9.2 Write property test for directive hierarchy (Property 1: Directive Hierarchy Resolution)
    - **Property 1: Directive Hierarchy Resolution**
    - **Validates: Requirements 1.3, 4.9**
    - Use Hypothesis to generate chapter text with conflicting directive terms; verify output matches ED4 instruction

  - [ ] 9.3 Implement Rewrite Agent invocation with all inputs and rewrite log generation
    - Build prompt for ModelClient with all declared inputs (Draft 3 chapter, Model Bible, Character Bible, ED4, DRAFT3_DIRECTIVES, Foundation, preceding D4)
    - Parse agent output to extract rewritten chapter and rewrite log
    - Rewrite log must contain: changes per directive, word count before/after, characters used, and unresolved issues
    - Handle `[AUTHOR VOICE]` marker insertion at author-presence insertion points with accompanying `[NOTE TO AUTHOR: VOICE_MOMENT — ...]` markers
    - For Chapter 9: instruct agent to apply constraint taxonomy (5 categories) and include clear statement about when adaptation advice applies vs. when to challenge/leave
    - For Chapter 10: instruct agent to insert faith/trust distinction paragraph (100–200 words) within first 500 words
    - Output stored at `output/draft4/chXX_raw.md`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 8.6, 14.2, 14.3, 14.4, 16.2, 16.3, 17.2, 17.3, 18.1_

  - [ ] 9.4 Implement Evidence Agent invocation and evidence log generation
    - Invoke Evidence Agent with rewritten chapter (`output/draft4/chXX_raw.md`)
    - Parse output for evidenced chapter and evidence log
    - Evidence log must list: claims found, action per claim (sourced / qualified / flagged for author), reference or qualifier added
    - For claims that cannot be sourced or qualified: insert `[NOTE TO AUTHOR: SOURCE_NEEDED — <specific claim text>]` marker
    - Output stored at `output/draft4/chXX_evidenced.md`; passed to Artifact Scrubber as input
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 18.3_

  - [ ] 9.5 Implement Artifact Scrubber invocation and log generation
    - Invoke scrubber agent with evidenced chapter text (from Evidence Agent output)
    - Parse output for clean chapter and artifact removal log
    - Handle special case: preserve `[Author's note]` in Introduction chapter (route to Author_Gate)
    - Log each artifact: type, line number, snippet (up to 120 chars), action taken
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 9.6 Implement Continuity Auditor invocation
    - Invoke auditor agent with chapter, Model Bible, Character Bible
    - Parse PASS/BLOCK response with violation list
    - On BLOCK: extract violation type, offending text, chapter location, expected value
    - For Chapter 9: verify constraint categories match ED4 directive (5 categories)
    - Feed violations back to Rewrite Agent on revision loop
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 16.4_

  - [ ] 9.7 Implement Editorial Gate invocation (per-chapter)
    - Invoke gate with chapter and reference documents
    - Check all 6 criteria: character cast, artifact-free, **word count within per-chapter target range from ED4 table**, layer terminology, exercise variety, sourced claims
    - On BLOCK: return failing check names and chapter locations of violations
    - Gate is separate from existing Chapter Acceptance Gate; both must independently pass
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 14.6_

- [ ] 10. Checkpoint – Ensure orchestrator and agent invocations work end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Create workflow definition and extend contracts/config
  - [ ] 11.1 Create `workflows/editorial-rewrite-workflow.md`
    - Follow structural conventions of `workflows/first-draft-workflow.md`: Goal, Workflow sequence, quality gate rules, revision rule, resume rule, tool rule
    - Specify sequence: Bible Creation → Chapter Rewrite Loop (Rewrite Agent → **Evidence Agent** → Artifact Scrubber → Continuity Auditor → Editorial Gate → Revision on BLOCK) → Assembly → **Author Action Log generation** → Book-level Editorial Gate
    - Declare inputs: Draft 3 chapters in `output/draft3/` or `output/final_chapters/`
    - Declare outputs: `output/draft4/chXX.md` per chapter, `output/full_fourth_draft.md` assembled, `output/author_actions.md` consolidated author markers
    - Specify resume rule: skip chapters with passing Editorial Gate verdict
    - Specify max revision count from config (default 3); halt chapter loop at max with BLOCK → mark failed
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 15.1, 18.5_

  - [ ] 11.2 Extend `contracts/handoff-contract.md` with rewrite stage section
    - Add a "## Rewrite Stage" section listing all new stage outputs
    - Include entries for: Model Bible, Character Bible, Rewrite Agent chapter outputs, **Evidence Agent outputs (evidenced chapter + evidence log)**, Artifact Scrubber outputs, Continuity Auditor reports, Editorial Gate reports, assembled Draft 4, **Author Action Log**
    - Each entry specifies: producing agent, consuming agent(s), output file-path pattern
    - **Evidence Agent entries**: producing agent = Evidence Agent, consuming agent = Artifact Scrubber, path = `output/draft4/chXX_evidenced.md`; evidence log consumed by Editorial Gate and Author Action Log
    - Define package fields for rewrite entries: book_id, stage ("rewrite"), chapter_number, input_files, output_file, status (PENDING | IN_PROGRESS | COMPLETE | FAILED | WAITING_HUMAN), next_agent
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 15.7_

  - [ ] 11.3 Extend `config.yaml` with `editorial_rewrite` section and `output_file_d4`
    - Add `editorial_rewrite` section with keys: `max_revisions` (3), `word_reduction_target_min` (0.15), `word_reduction_target_max` (0.25), `run_artifact_scrubber` (true), `run_continuity_auditor` (true), `run_editorial_gate` (true), `resume` (false)
    - Add `editorial_rewrite.agents` mapping: `rewrite_agent`, `artifact_scrubber`, `continuity_auditor`, **`evidence_agent`** — all pointing to respective agent definition files
    - Add `book.output_file_d4: "output/full_fourth_draft.md"` separate from the Draft 3 entry
    - _Requirements: 11.1, 11.2, 11.3_

- [ ] 12. Implement word count, evidence, author marker, and remaining property tests
  - [ ]* 12.1 Write property test for character cast closure (Property 2: Character Cast Closure)
    - **Property 2: Character Cast Closure**
    - **Validates: Requirements 3.6, 4.2, 6.1**
    - Use Hypothesis to generate chapter text with character names; verify all named characters ∈ Character Bible set

  - [ ]* 12.2 Write property test for layer terminology consistency (Property 3: Layer Terminology Consistency)
    - **Property 3: Layer Terminology Consistency**
    - **Validates: Requirements 2.6, 4.4, 6.2**
    - Use Hypothesis to generate text with layer/currency references; verify case-sensitive exact match to Model Bible entries

  - [ ]* 12.3 Write property test for per-chapter word count compliance (Property 4: Per-Chapter Word Count Compliance)
    - **Property 4: Per-Chapter Word Count Compliance**
    - **Validates: Requirements 14.6, 7.1c (superseded)**
    - Use Hypothesis to generate chapters of varying length per chapter number; verify output word count falls within the per-chapter target range from ED4 table (NOT the old flat 15–25% reduction formula)

  - [ ]* 12.4 Write property test for artifact-free output (Property 5: Artifact-Free Output)
    - **Property 5: Artifact-Free Output**
    - **Validates: Requirements 5.1, 5.4, 7.1b**
    - Use Hypothesis to generate chapters with randomly inserted artifacts; verify scrubber removes all (except preserved [Author's note] in Introduction)

  - [ ]* 12.5 Write property test for continuity auditor idempotence (Property 6: Continuity Auditor Round-Trip)
    - **Property 6: Continuity Auditor Round-Trip**
    - **Validates: Requirements 6.5, 6.6**
    - Use Hypothesis to generate chapters that pass the auditor; verify re-running produces PASS again

  - [ ]* 12.6 Write property test for word count expansion (Property 11: Word Count Expansion)
    - **Property 11: Word Count Expansion**
    - **Validates: Requirements 14.1, 14.5**
    - Use Hypothesis to generate full draft assemblies with varying chapter lengths; verify total assembled word count within 33,000–37,000

  - [ ]* 12.7 Write property test for evidence agent non-fabrication (Property 12: Evidence Agent Non-Fabrication)
    - **Property 12: Evidence Agent Non-Fabrication**
    - **Validates: Requirements 15.3, 15.4**
    - Use Hypothesis to generate chapters with unsourced claims; verify inserted references are from well-known sources (validate against allowlist of established findings); verify no fabricated citations

  - [ ]* 12.8 Write property test for constraint taxonomy completeness (Property 13: Constraint Taxonomy Completeness)
    - **Property 13: Constraint Taxonomy Completeness**
    - **Validates: Requirements 16.1, 16.4**
    - Use Hypothesis to generate Ch9 rewrites with random constraint examples; verify all 5 categories present in output

  - [ ]* 12.9 Write property test for author marker consistency (Property 14: Author Marker Consistency)
    - **Property 14: Author Marker Consistency**
    - **Validates: Requirements 18.4**
    - Use Hypothesis to generate `[NOTE TO AUTHOR]` markers with random categories/explanations; verify format compliance: `[NOTE TO AUTHOR: <CATEGORY> — <explanation>]` where CATEGORY ∈ {PERSONAL_STORY, VOICE_MOMENT, SOURCE_NEEDED, DECISION_NEEDED}

- [ ] 13. Write integration tests with MockModelClient
  - [ ]* 13.1 Write integration tests for the full chapter pipeline
    - Test full chapter pipeline with MockModelClient: rewrite → **evidence** → scrub → audit → gate
    - Test resume behaviour across simulated runs (skip editorial_pass chapters)
    - Test assembly of passing chapters into full manuscript
    - Test error paths: missing files, corrupted state, exhausted revisions
    - Test Author Gate blocking Introduction while other chapters proceed
    - _Requirements: 4.1, 5.1, 6.1, 7.1, 8.4, 9.4, 13.2, 15.1_

  - [ ]* 13.2 Write tests for Evidence Agent (`tests/test_evidence_agent.py`)
    - Test that unsourced claims are identified and actioned (sourced, qualified, or flagged)
    - Test that no fabricated citations are generated (validate against allowlist)
    - Test evidence log format and completeness
    - Test `[NOTE TO AUTHOR: SOURCE_NEEDED — ...]` marker format for unfixable claims
    - _Requirements: 15.2, 15.3, 15.4, 15.5, 15.6_

  - [ ]* 13.3 Write tests for author markers (`tests/test_author_markers.py`)
    - Test `[NOTE TO AUTHOR: <CATEGORY> — <explanation>]` format consistency across all marker types
    - Test consolidated `output/author_actions.md` generation: chapter, location, category, explanation for each marker
    - Test that all 4 categories are valid: PERSONAL_STORY, VOICE_MOMENT, SOURCE_NEEDED, DECISION_NEEDED
    - Test that Author Gate blocking inserts correct PERSONAL_STORY marker in Introduction
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

  - [ ]* 13.4 Write tests for per-chapter word count targets (`tests/test_word_count.py`)
    - Test per-chapter target table parsing from ED4
    - Test Editorial Gate per-chapter word count check validates against ED4 table (not flat reduction)
    - Test book-level check validates total within 33,000–37,000
    - Test chapters with word count outside target range trigger BLOCK
    - _Requirements: 14.1, 14.5, 14.6_

- [ ] 14. Final checkpoint – Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document (14 properties total)
- Unit tests validate specific examples and edge cases
- All tests use `MockModelClient` — no live model calls in automated testing
- The implementation language is Python, matching the existing Charlotte orchestrator
- Agent definition files are markdown (not code), following Charlotte's agent-agnostic conventions
- Foundation documents (Model Bible, Character Bible) are also markdown reference files consumed by agents at runtime
- The pipeline now EXPANDS the manuscript (~25k → 33k–37k) rather than reducing it; per-chapter targets replace the flat 15–25% reduction
- Evidence Agent is a NEW pipeline stage between Rewrite Agent and Artifact Scrubber
- Chapter 9 constraint taxonomy (5 categories) and Chapter 10 faith/trust paragraph are encoded in ED4 and applied by the Rewrite Agent
- `[NOTE TO AUTHOR]` markers follow format `[NOTE TO AUTHOR: <CATEGORY> — <explanation>]` and are consolidated in `output/author_actions.md`
- New test files: `test_evidence_agent.py`, `test_author_markers.py`, `test_word_count.py`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3", "2.4", "2.5"] },
    { "id": 2, "tasks": ["4.1", "5.1", "6.1", "6.2"] },
    { "id": 3, "tasks": ["4.2", "4.3", "5.2", "6.3"] },
    { "id": 4, "tasks": ["8.1", "8.2", "9.1"] },
    { "id": 5, "tasks": ["8.3", "9.3", "9.4", "9.5", "9.6", "9.7"] },
    { "id": 6, "tasks": ["8.4", "8.5", "8.6", "9.2"] },
    { "id": 7, "tasks": ["11.1", "11.2", "11.3"] },
    { "id": 8, "tasks": ["12.1", "12.2", "12.3", "12.4", "12.5", "12.6", "12.7", "12.8", "12.9"] },
    { "id": 9, "tasks": ["13.1", "13.2", "13.3", "13.4"] }
  ]
}
```
