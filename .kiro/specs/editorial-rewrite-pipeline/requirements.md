# Requirements Document

## Introduction

This document specifies requirements for a new stage in the Charlotte Book Factory pipeline: the **Editorial Rewrite Pipeline**. This stage sits after the first-draft workflow and takes the completed Draft 3 manuscript plus consolidated professional editorial feedback as inputs, producing a rewritten Draft 4 as output.

The editorial rewrite pipeline is not a rebuild of Charlotte. It is the next stage of the writing process — the same agent-agnostic, file-driven, contract-based system gains a new workflow that applies structured editorial directives to an existing draft.

Two independent professional editors reviewed Draft 3 and converged on the same core issues: character proliferation, repetition, production artifacts, missing author presence, unsourced claims, fuzzy layer boundaries, and rigid taxonomy framing. This pipeline operationalizes that feedback.

Beyond correcting those issues, the pipeline also expands the manuscript by approximately 10,000 words of new substantive content (mechanism explanations, failure modes, hard cases, counterexamples) to bring Draft 4 to the ~35,000-word depth the editors recommended. A dedicated Evidence Agent provides a credible evidentiary spine by inserting lightweight source references and qualifying phrases for unsourced claims. Chapter 9's constraint taxonomy receives a targeted restructuring to distinguish between genuinely immutable constraints, externally imposed barriers, changeable-but-costly situations, and unsafe scenarios. Finally, all points in the manuscript requiring human author input are marked with searchable `[NOTE TO AUTHOR]` references, giving the author a single pattern to locate every required contribution.

## Glossary

- **Pipeline**: A defined sequence of agent stages that transforms inputs into outputs, following the Charlotte handoff contract.
- **Draft_3**: The completed first-draft manuscript produced by the existing first-draft-workflow (13 chapters, ~27k words, stored in `output/full_third_draft.md`).
- **Draft_4**: The rewritten manuscript produced by this pipeline, incorporating all editorial feedback.
- **Model_Bible**: A reference document that locks definitions, boundaries, diagnostic tests, inclusions/exclusions, and common confusions for all 5 layers (Body, Wiring, Habit, Room, Story) and 3 currencies (Charge, Fuel, Pressure).
- **Character_Bible**: A reference document defining the fixed cast of 4–5 recurring characters with stable identities, occupations, situations, layer-assignments, and chapter-appearance maps.
- **Editorial_Directives_D4**: A consolidated directive document encoding all editorial feedback as actionable rewrite rules for Draft 4 agents.
- **Rewrite_Agent**: An agent that takes a Draft 3 chapter plus reference bibles and editorial directives and produces a rewritten Draft 4 chapter.
- **Artifact_Scrubber**: An agent or pass that detects and removes production artifacts (EDITOR FLAGs, outline headers, placeholder author notes, chapter misnumbering, internal instructions).
- **Continuity_Auditor**: An agent that verifies character consistency, layer-name consistency, and cross-chapter continuity against the Model Bible and Character Bible.
- **Editorial_Gate**: A quality gate specific to the editorial rewrite that checks compliance with the consolidated editorial directives.
- **Author_Gate**: A blocking checkpoint that halts pipeline progress until a human-supplied author contribution is provided.
- **Foundation**: The source-of-truth document for the book (`foundation/Me_OS_Foundation.md`).
- **DRAFT3_DIRECTIVES**: The existing locked editorial decisions for Draft 3 (`foundation/DRAFT3_DIRECTIVES.md`) which remain in force unless explicitly superseded by Editorial_Directives_D4.
- **Evidence_Agent**: An agent that scans rewritten chapters for unsourced claims and inserts lightweight source references, qualifying phrases, or flags for author review.
- **Author_Action_Log**: A consolidated list of all `[NOTE TO AUTHOR]` markers across the manuscript, produced after assembly to give the author a single checklist of required human contributions.

## Requirements

### Requirement 1: Editorial Directives Document

**User Story:** As the book author, I want the consolidated editorial feedback encoded as a structured directives document, so that every agent in the rewrite pipeline applies the same rules consistently.

#### Acceptance Criteria

1. IF the `foundation/EDITORIAL_DIRECTIVES_D4.md` file does not exist when a rewrite stage is initiated, THEN THE Pipeline SHALL halt execution and produce an error message indicating the required directives file is missing.
2. WHEN the Editorial_Directives_D4 file is present, THE Pipeline SHALL parse its directives and apply them as the governing rules for all Draft 4 rewrite operations, overriding any prior draft directives on the same topic.
3. WHERE a directive in Editorial_Directives_D4 addresses the same topic as a directive in DRAFT3_DIRECTIVES with a different instruction, THE Pipeline SHALL follow Editorial_Directives_D4.
4. WHERE a directive in DRAFT3_DIRECTIVES addresses a topic not covered by any directive in Editorial_Directives_D4, THE Pipeline SHALL continue to enforce the DRAFT3_DIRECTIVES rule.
5. THE Editorial_Directives_D4 SHALL contain a named section for each of the following categories: character consolidation rules, repetition-reduction targets, production-artifact definitions, author-presence insertion points, sourcing requirements, layer-boundary clarifications, and taxonomy-reframing guidance.
6. IF the Editorial_Directives_D4 file is present but missing one or more of the required sections defined in criterion 5, THEN THE Pipeline SHALL halt execution and produce an error message identifying which sections are absent.

### Requirement 2: Model Bible Creation

**User Story:** As the book author, I want a Model Bible that locks down crisp definitions for the five-layer taxonomy and three currencies, so that the rewrite produces consistent terminology and boundaries throughout.

#### Acceptance Criteria

1. WHEN the editorial rewrite pipeline begins, THE Pipeline SHALL produce a `foundation/model_bible.md` before any chapter rewriting starts.
2. THE Model_Bible SHALL define each of the 5 layers (Body, Wiring, Habit, Room, Story) with: a one-sentence definition (maximum 30 words), a list of what is included, a list of what is excluded, a diagnostic test phrased as a yes/no question the reader can apply to classify a phenomenon into that layer, and a "commonly confused with" section distinguishing it from each adjacent layer.
3. THE Model_Bible SHALL define each of the 3 currencies (Charge, Fuel, Pressure) with: a one-sentence definition (maximum 30 words), a description of how it manifests in each of the 5 layers, and a comparison statement explaining how it differs operationally from each of the other two currencies.
4. THE Model_Bible SHALL present the taxonomy as a preferred diagnostic sequence with feedback loops by specifying a recommended evaluation order across layers and identifying, for each layer, which other layers can feed back into it and under what conditions.
5. THE Model_Bible SHALL resolve the Wiring-vs-Story boundary overlap by providing a discrimination test consisting of at least two differentiating criteria, each phrased as a yes/no question, that assigns a given phenomenon to either Wiring or Story with no overlapping classification.
6. WHEN a Rewrite_Agent processes any chapter, THE Rewrite_Agent SHALL use only the layer names, currency names, and definitions from the Model_Bible for all taxonomy-related terminology in the rewritten output.
7. IF a Rewrite_Agent encounters a term or concept in a source chapter that does not match any Model_Bible definition, THEN THE Rewrite_Agent SHALL flag the term for author review and map it to the nearest Model_Bible entry before proceeding with the rewrite.

### Requirement 3: Character Bible Creation

**User Story:** As the book author, I want a Character Bible that defines a fixed cast of recurring characters, so that the rewrite replaces the proliferation of interchangeable characters with a stable, memorable cast.

#### Acceptance Criteria

1. WHEN the editorial rewrite pipeline begins, THE Pipeline SHALL produce a `foundation/character_bible.md` before any chapter rewriting starts.
2. THE Character_Bible SHALL define between 4 and 5 recurring characters, each with: a name, age, occupation, life situation, primary layer association, secondary layer association if applicable, a physical signature consisting of one concrete sensory detail that distinguishes the character on every appearance, and a one-sentence "what they carry" summary describing the character's core emotional burden or unresolved tension.
3. THE Character_Bible SHALL include a chapter-appearance map listing each character and the chapter numbers in which they appear, indicating whether each appearance is primary (drives the chapter's narrative) or secondary (supports another character's narrative).
4. THE Character_Bible SHALL ensure that no single character dominates more than 40% of all chapter-level appearances across the book, where one appearance is counted per chapter in which the character is present regardless of how many scenes they occupy within that chapter.
5. THE Character_Bible SHALL assign at least one character to each of the 5 layers as their primary demonstration vehicle.
6. WHEN a Rewrite_Agent processes a chapter, THE Rewrite_Agent SHALL draw named characters only from the Character_Bible and SHALL NOT introduce new named or one-off characters for the "five-cause proof" device.
7. IF a chapter's narrative requires a human presence outside the defined cast, THEN THE Rewrite_Agent SHALL use unnamed, role-described background figures (e.g., "the barista," "a fellow commuter") limited to a maximum of 2 per chapter, and these figures SHALL NOT carry dialogue exceeding one sentence.

### Requirement 4: Rewrite Agent

**User Story:** As the book author, I want a rewrite agent that systematically transforms each Draft 3 chapter into a Draft 4 chapter applying all editorial directives, so that the rewrite is consistent and traceable.

#### Acceptance Criteria

1. THE Rewrite_Agent SHALL accept as inputs: the Draft 3 chapter, the Model Bible, the Character Bible, the Editorial_Directives_D4, the DRAFT3_DIRECTIVES, the Foundation, and the preceding chapter's Draft 4 output (for continuity); IF the chapter is the first in the manuscript, THEN THE Rewrite_Agent SHALL proceed without a preceding Draft 4 input and use the Foundation alone for continuity context.
2. WHEN rewriting a chapter, THE Rewrite_Agent SHALL replace any character not present in the Character Bible's fixed cast with the corresponding fixed-cast character as mapped in the Character Bible, preserving the original narrative function of the replaced character.
3. WHEN rewriting a chapter, THE Rewrite_Agent SHALL remove all production artifacts including EDITOR FLAG markers, outline headers, placeholder text (any bracketed or annotated text indicating incomplete content), and misnumbered references.
4. WHEN rewriting a chapter, THE Rewrite_Agent SHALL replace all layer names and currency terms with the exact terms defined in the Model Bible, applying no synonyms or paraphrases.
5. WHEN rewriting a chapter, THE Rewrite_Agent SHALL reduce prose by 15–25% compared to the Draft 3 chapter word count, targeting de-duplication and removal of restated material; IF the chapter cannot be reduced by at least 15% without removing non-duplicated substantive content, THEN THE Rewrite_Agent SHALL reduce as much as possible and log the shortfall with justification in the rewrite log.
6. WHEN rewriting a chapter, THE Rewrite_Agent SHALL vary exercises so that no more than 2 consecutive chapters use the same exercise format (where exercise format means the structural type such as reflection prompt, scenario walkthrough, fill-in worksheet, or guided visualization).
7. IF a scientific or psychological claim appears in the chapter text without a qualifying phrase (e.g., hedging language indicating study limitations or generalizability) or a source reference, THEN THE Rewrite_Agent SHALL either add a qualifying phrase or insert a lightweight source reference adjacent to the claim.
8. THE Rewrite_Agent SHALL produce a rewrite log appended to the end of each chapter output listing: changes made mapped to the specific editorial directive that prompted each change, word count before and after rewrite, fixed-cast characters used in the chapter, and any unresolved issues where directives conflicted or could not be fully applied.
9. IF the Editorial_Directives_D4 and the DRAFT3_DIRECTIVES conflict on a specific instruction, THEN THE Rewrite_Agent SHALL prioritize the Editorial_Directives_D4 and log the conflict and resolution in the rewrite log.

### Requirement 5: Artifact Scrubber Pass

**User Story:** As the book author, I want a dedicated pass that detects and removes all production artifacts from the manuscript, so that no internal workflow markers appear in the reader-facing text.

#### Acceptance Criteria

1. WHEN a chapter has been rewritten, THE Artifact_Scrubber SHALL scan the output for the following production artifacts: literal strings `EDITOR FLAG` and `[Author's note]`, outline-style headers matching the pattern `## <phrase> purpose:`, chapter numbers that do not match the sequential position of the chapter in the manuscript table of contents, and any YAML front-matter blocks or fenced code blocks whose content contains workflow keys (e.g., `status:`, `assignee:`, `draft_notes:`) rather than reader-facing example code.
2. IF a production artifact is detected, THEN THE Artifact_Scrubber SHALL remove it from the chapter text and append an entry to the artifact removal log containing: the artifact type, the line number where it was found, a snippet of up to 120 characters of the removed content, and the action taken (removed or preserved).
3. IF an `[Author's note]` placeholder is detected in the Introduction chapter, THEN THE Artifact_Scrubber SHALL preserve the placeholder in the chapter text and add an entry to the removal log with the action recorded as "preserved – routed to Author_Gate for review."
4. WHEN the scan is complete, THE Artifact_Scrubber SHALL produce a chapter containing zero instances of the artifact patterns defined in criterion 1 (except those explicitly preserved per criterion 3), paired with the artifact removal log.
5. IF the Artifact_Scrubber detects no production artifacts during the scan, THEN THE Artifact_Scrubber SHALL output the chapter unchanged and produce an artifact removal log stating that zero artifacts were found.

### Requirement 6: Continuity Auditor

**User Story:** As the book author, I want a continuity check that verifies the rewritten chapters use consistent characters, terminology, and layer names against the bibles, so that the book reads as a unified work.

#### Acceptance Criteria

1. WHEN a rewritten chapter is produced, THE Continuity_Auditor SHALL verify that every character referenced by canonical name or listed alias (as defined in the Character Bible) appears as an entry in the Character Bible.
2. WHEN a rewritten chapter is produced, THE Continuity_Auditor SHALL verify that every layer name and currency name is a case-sensitive exact match to an entry in the Model Bible.
3. WHEN a rewritten chapter is produced, THE Continuity_Auditor SHALL verify that character details (occupation, situation, physical signature) stated in the chapter do not contradict the corresponding fields in that character's Character Bible entry.
4. WHEN a rewritten chapter is produced, THE Continuity_Auditor SHALL verify that no character or named concept appears before its designated first-appearance chapter as specified in the Character Bible chapter-appearance map and the reveal order.
5. IF one or more continuity violations are found, THEN THE Continuity_Auditor SHALL return a BLOCK status accompanied by a list where each entry identifies the violation type, the offending text, the chapter location, and the expected value from the relevant bible.
6. IF no continuity violations are found, THEN THE Continuity_Auditor SHALL return a PASS status indicating the chapter is consistent with all bibles.

### Requirement 7: Editorial Compliance Gate

**User Story:** As the book author, I want a quality gate that specifically checks whether each chapter complies with the editorial directives, so that editorial feedback is verifiably addressed.

#### Acceptance Criteria

1. WHEN a rewritten chapter is submitted for approval, THE Editorial_Gate SHALL check each of the following and report a per-check pass or fail result: (a) character cast compliance — only characters listed in the Character Bible appear, (b) artifact-free status — no placeholder text, inline comments, revision marks, or TODO annotations remain, (c) word count reduction is between 15% and 25% relative to the same chapter's Draft 3 word count, (d) layer terminology matches the terms defined in the Model Bible with no synonyms or ad-hoc variants, (e) exercise variety — no more than 2 consecutive exercises use the same format, and (f) every factual claim that cites statistics, dates, named studies, or attributed quotes includes at least one source reference.
2. IF any single check in criterion 1 fails, THEN THE Editorial_Gate SHALL return a BLOCK status that lists each failing check by name and includes the location within the chapter (section or paragraph identifier) where the violation occurs.
3. IF all checks in criterion 1 pass, THEN THE Editorial_Gate SHALL return a PASS status for that chapter.
4. THE Editorial_Gate SHALL be a separate gate from the existing Chapter_Acceptance_Gate — both gates must independently pass before a chapter is marked as approved, and they may execute in any order.
5. WHEN the full manuscript is assembled, THE Editorial_Gate SHALL run a book-level check confirming: (a) total manuscript word count is between 15% and 25% lower than the total Draft 3 word count, (b) each character from the fixed cast appears with the frequency distribution specified in the Character Bible, and (c) no placeholder text, inline comments, revision marks, or TODO annotations remain in any chapter.

### Requirement 8: Author Gate for Human Prerequisites

**User Story:** As the book author, I want the pipeline to halt at defined points where human-written content is required, so that the system never fabricates personal author material.

#### Acceptance Criteria

1. WHEN the Introduction chapter is queued for rewrite, THE Author_Gate SHALL check whether a human-supplied author note exists in the designated file (`foundation/author_note.md`).
2. IF the author note file does not exist, is empty, or contains fewer than 50 words of non-boilerplate content (e.g., content that is not exclusively template prompts such as "Insert your note here" or "TODO"), THEN THE Author_Gate SHALL block the Introduction chapter rewrite and mark it as WAITING_HUMAN in the pipeline status.
3. WHEN the pipeline stage is re-executed and the author note file contains 50 or more words of non-boilerplate content, THE Author_Gate SHALL unblock the Introduction chapter for rewriting.
4. THE Pipeline SHALL allow all other chapters to proceed independently of the Author_Gate — only the Introduction is blocked.
5. THE Pipeline SHALL define 6–8 author-presence insertion points across the book in Editorial_Directives_D4, specifying the chapter and location within each chapter where author voice is required.
6. WHEN a chapter undergoing rewrite contains an author-presence insertion point, THE Rewrite_Agent SHALL insert an `[AUTHOR VOICE]` marker at that location with a one-sentence contextual prompt describing what personal content is expected, rather than generating autobiographical anecdotes, personal opinions, or first-person experiences on the author's behalf.
7. IF the Author_Gate blocks the Introduction chapter, THEN THE Pipeline SHALL log the block event in the pipeline status with the reason and the path to the missing or insufficient file, and SHALL continue processing all non-blocked chapters.

### Requirement 9: Rewrite Workflow Definition

**User Story:** As any Charlotte executor (Kiro, Codex, local runner, etc.), I want a workflow definition file for the editorial rewrite pipeline, so that the stage can be orchestrated like the existing first-draft-workflow.

#### Acceptance Criteria

1. THE Pipeline SHALL define its workflow in `workflows/editorial-rewrite-workflow.md` following the same structural conventions as `workflows/first-draft-workflow.md`, including: stage listing with ordering, per-stage input/output declarations, agent assignments, and trigger/exit conditions for each stage.
2. THE workflow SHALL specify the sequence: Bible Creation (Model Bible, Character Bible) → Chapter Rewrite Loop (Rewrite Agent → Artifact Scrubber → Continuity Auditor → Editorial Gate → Revision loop on BLOCK) → Assembly → Book-level Editorial Gate.
3. THE workflow SHALL specify that Draft 3 chapters in `output/draft3/` or `output/final_chapters/` are the input, not the foundation alone.
4. WHEN the workflow is re-run, IF a chapter has a passing Editorial Gate verdict recorded in the pipeline state file, THEN THE workflow SHALL skip that chapter and proceed to the next unfinished chapter.
5. THE workflow SHALL specify a maximum revision count for the rewrite revision loop, with the value read from `config.yaml` and defaulting to 3 if not configured.
6. IF a chapter's revision count reaches the configured maximum and the Editorial Gate still returns BLOCK, THEN THE workflow SHALL halt the chapter rewrite loop for that chapter, record it as failed in the pipeline state, and continue to the next chapter.
7. THE workflow SHALL define the output location for Draft 4 chapters as `output/draft4/chXX.md` and the assembled manuscript as `output/full_fourth_draft.md`.

### Requirement 10: Handoff Contract Extension

**User Story:** As any Charlotte agent, I want the handoff contract updated to cover the new rewrite stage outputs, so that agents can discover and consume each other's work through the standard contract mechanism.

#### Acceptance Criteria

1. THE contracts/handoff-contract.md SHALL be extended with a dedicated rewrite stage section that lists all stage outputs for the editorial rewrite pipeline.
2. THE handoff contract SHALL include one entry for each of the following artifacts: Model Bible, Character Bible, Rewrite Agent chapter outputs, Artifact Scrubber outputs, Continuity Auditor reports, Editorial Gate reports, and assembled Draft 4, where each entry specifies the producing agent, the consuming agent(s), and the artifact file-path pattern.
3. THE handoff contract SHALL specify the following package fields for every rewrite stage entry: book_id, stage (value: "rewrite"), chapter_number, input_files, output_file, status, and next_agent.
4. THE handoff contract SHALL define the valid status values for the rewrite stage as: PENDING, IN_PROGRESS, COMPLETE, FAILED, and WAITING_HUMAN.

### Requirement 11: Configuration Extension

**User Story:** As an operator running the Charlotte pipeline, I want config.yaml updated with settings for the editorial rewrite stage, so that I can control model, revision limits, and feature flags for the new pipeline.

#### Acceptance Criteria

1. THE config.yaml SHALL include an `editorial_rewrite` section containing the following keys with their default values: `max_revisions` (integer, default: 3, valid range: 1 to 10), `word_reduction_target_min` (float, default: 0.15, valid range: 0.0 to 1.0), `word_reduction_target_max` (float, default: 0.25, valid range: 0.0 to 1.0, must be greater than `word_reduction_target_min`), `run_artifact_scrubber` (boolean, default: true), `run_continuity_auditor` (boolean, default: true), `run_editorial_gate` (boolean, default: true), and `resume` (boolean, default: false).
2. THE config.yaml SHALL include an `editorial_rewrite.agents` mapping containing keys `rewrite_agent`, `artifact_scrubber`, and `continuity_auditor`, each holding a file path string referencing the corresponding agent definition file.
3. THE config.yaml SHALL provide a distinct `book.output_file` entry for the editorial rewrite stage (Draft 4) that is separate from the Draft 3 `book.output_file` entry, so that running the editorial rewrite stage does not overwrite Draft 3 output.
4. IF a required key is missing from the `editorial_rewrite` section when the pipeline loads the configuration, THEN THE system SHALL halt startup and report an error message indicating which key is missing.

### Requirement 12: New Agent Role Definitions

**User Story:** As the Charlotte system, I want agent role definition files for the new rewrite-stage agents, so that any executor can load and run them following Charlotte's agent-agnostic conventions.

#### Acceptance Criteria

1. THE Pipeline SHALL include an agent definition at `agents/rewrite_agent.md` specifying: role, mission, an Inputs section explicitly listing all consumed files (Draft 3 chapter, Model Bible, Character Bible, Editorial_Directives_D4, DRAFT3_DIRECTIVES, Foundation, preceding Draft 4 chapter), an Output section defining the chapter output followed by a rewrite log appended at the end containing changes per directive, word count before/after, characters used, and unresolved issues, and a Rules section referencing Model Bible and Character Bible as authoritative terminology and character sources.
2. THE Pipeline SHALL include an agent definition at `agents/artifact_scrubber.md` specifying: role, mission, an Inputs section listing the rewritten chapter file, a pattern list enumerating at minimum the 5 artifact types defined in Requirement 5 (EDITOR FLAG, Author's note placeholders, outline-style headers, chapter misnumbering, internal-only YAML/code blocks), actions per pattern (remove or preserve-and-flag), and an Output section defining a clean chapter plus an artifact removal log listing each artifact found and action taken.
3. THE Pipeline SHALL include an agent definition at `agents/continuity_auditor.md` specifying: role, mission, an Inputs section listing the rewritten chapter, Model Bible, and Character Bible, a checks section enumerating at minimum character-existence verification, layer/currency name matching, and character-detail consistency, BLOCK/PASS criteria stating that any continuity violation results in BLOCK with the specific violation listed, and an Output section defining a status report with status field and violation list.
4. THE agent definitions SHALL each use the heading structure of existing Charlotte agents: a level-1 heading with the agent name in the format `# AGENT: <NAME>`, followed by level-2 headings for Role, Mission, Inputs, Output (or Outputs), and Rules sections.
5. WHEN a new agent definition references input or output files, THE agent definition SHALL use the same file path conventions as existing Charlotte agents (paths relative to the repository root).

### Requirement 13: Pipeline State and Resumability

**User Story:** As an operator, I want the editorial rewrite pipeline to track its own state and support resuming interrupted runs, so that partial progress is not lost.

#### Acceptance Criteria

1. THE Pipeline SHALL maintain state in `output/draft4_state.json` recording each chapter's current status as one of: "pending", "rewriting", "rewritten", "editorial_pass", "blocked", or "waiting_human_input", and SHALL update this file within 5 seconds of any chapter changing status.
2. WHEN the pipeline is re-run with resume enabled, THE Pipeline SHALL skip chapters that have a status of "editorial_pass" in the state file and SHALL proceed to process only chapters with status "pending", "rewriting", or "rewritten".
3. IF the state file is missing when the pipeline is started with resume enabled, THEN THE Pipeline SHALL treat all chapters as "pending" and begin processing from the start.
4. IF the state file is present but unparseable, THEN THE Pipeline SHALL halt execution and produce an error message indicating the state file is corrupted, without overwriting the existing file.
5. WHEN a chapter is blocked, THE Pipeline SHALL record the block reason (maximum 500 characters) and the name of the blocking agent in the state file, and SHALL set that chapter's status to "blocked".
6. WHEN a chapter completes processing or becomes blocked, THE Pipeline SHALL write a status file at `output/status_d4.md` listing: total chapter count, count of chapters in each status category, and for each blocked chapter the block reason and blocking agent.


### Requirement 14: Word Count Expansion Target

**User Story:** As the book author, I want Draft 4 to expand the manuscript to approximately 35,000 words by adding substantive new content (mechanism explanations, failure modes, hard cases, counterexamples), so that the book reaches the depth editors recommended.

#### Acceptance Criteria

1. THE Rewrite_Agent SHALL target a total manuscript word count of 33,000–37,000 words for Draft 4 (up from Draft 3's ~25,000 words).
2. WHEN rewriting a chapter, THE Rewrite_Agent SHALL simultaneously cut repetitive/duplicated prose AND add new substantive content, resulting in a net word count increase per chapter.
3. THE new content added SHALL be limited to: mechanism explanations (why lower layers constrain higher ones), failure modes (each layer's "commonly mistaken for"), hard cases (the lowest layer that won't move), counterexamples (when the model doesn't apply cleanly), and model limitations.
4. THE Rewrite_Agent SHALL NOT add new content that introduces concepts outside the Model Bible taxonomy or contradicts the Foundation.
5. THE Editorial_Gate book-level check SHALL verify that the assembled Draft 4 manuscript word count falls within 33,000–37,000 words.
6. THE Editorial_Gate per-chapter check for word count SHALL be updated: instead of requiring 15–25% reduction, it SHALL verify that the chapter's word count is within the range specified in a per-chapter target table in Editorial_Directives_D4.

### Requirement 15: Evidentiary Spine Agent

**User Story:** As the book author, I want a dedicated agent that researches and inserts lightweight source references for psychological, neurological, and behavioural claims, so that the book has a credible evidentiary foundation without becoming a textbook.

#### Acceptance Criteria

1. THE Pipeline SHALL include a new agent defined at `agents/evidence_agent.md` that runs after the Rewrite Agent and before the Artifact Scrubber in the chapter pipeline.
2. THE Evidence_Agent SHALL scan the rewritten chapter for claims that are psychological, neurological, behavioural, or health-related in nature and currently lack a source reference or qualifying phrase.
3. FOR each unsourced claim identified, THE Evidence_Agent SHALL either: (a) insert a lightweight inline reference to an established, well-known source (e.g., "research consistently shows…" with an endnote), or (b) add a qualifying phrase that honestly positions the claim as the author's synthesis rather than established fact (e.g., "in my model…" or "as a practical rule…").
4. THE Evidence_Agent SHALL NOT invent citations, fabricate study names, or attribute claims to specific researchers without verification.
5. WHERE a claim cannot be sourced or qualified without fundamentally changing its meaning, THE Evidence_Agent SHALL insert a `[NOTE TO AUTHOR: This claim needs a source or reframing — <specific claim text>]` marker.
6. THE Evidence_Agent SHALL produce an evidence log listing: claims found, action taken per claim (sourced / qualified / flagged for author), and the reference or qualifier added.
7. THE Evidence_Agent output SHALL be stored at `output/draft4/chXX_evidenced.md` and passed to the Artifact Scrubber as its input (replacing the raw rewrite output in the pipeline sequence).

### Requirement 16: Chapter 9 Constraint Taxonomy Rewrite

**User Story:** As the book author, I want Chapter 9 (The Hard Cases) rewritten with a more sophisticated constraint taxonomy that distinguishes between types of "immovable" situations, so that the book doesn't inadvertently tell readers to accept situations they should challenge or leave.

#### Acceptance Criteria

1. THE Editorial_Directives_D4 SHALL include a Chapter 9 specific directive instructing the Rewrite Agent to restructure the constraint taxonomy into at minimum these categories: immutable constraint (e.g., genetic condition, permanent disability), currently constrained (e.g., chronic illness in active phase), externally imposed constraint (e.g., poverty, systemic barriers), changeable-but-costly constraint (e.g., a marriage that could end but at significant cost), and unsafe situation (e.g., abuse, where the answer is exit, not adaptation).
2. WHEN rewriting Chapter 9, THE Rewrite_Agent SHALL apply the constraint taxonomy from criterion 1, explicitly distinguishing between situations where internal adaptation is appropriate and situations where the honest answer is to challenge, change, or leave the external circumstance.
3. WHEN rewriting Chapter 9, THE Rewrite_Agent SHALL include a clear statement that the book's "adapt around the constraint" advice applies ONLY to genuinely immutable or currently-constrained situations, and SHALL NOT apply it to unsafe situations or externally-imposed constraints that can be challenged.
4. THE Continuity_Auditor SHALL verify that Chapter 9's constraint categories match those defined in the Editorial_Directives_D4 Chapter 9 directive.

### Requirement 17: Faith/Trust Terminology Handling

**User Story:** As the book author, I want the Belief/Faith chapter to explicitly acknowledge and address the terminology choice of "faith" over "trust," so that readers understand the intentional, non-religious usage.

#### Acceptance Criteria

1. THE Editorial_Directives_D4 SHALL include a directive for Chapter 10 (Belief, Then Faith) instructing the Rewrite Agent to retain "faith" as the primary term.
2. WHEN rewriting Chapter 10, THE Rewrite_Agent SHALL insert a paragraph (100–200 words) that: (a) acknowledges "faith" carries religious and metaphysical connotations for many readers, (b) distinguishes it from "trust" — explaining that trust typically implies evidence-based confidence while faith operates precisely where evidence runs out, (c) states clearly that the book uses "faith" to mean the capacity to act without proof, agnostic of religion, and (d) positions the terminology as a deliberate choice, not an oversight.
3. THE inserted paragraph SHALL appear early in Chapter 10, within the first 500 words of the chapter body (after any opening scene), before the main argument unfolds.

### Requirement 18: Author Reference Markers at All Human-Dependent Points

**User Story:** As the book author, I want every point in the manuscript where my personal input is needed to be clearly marked with a searchable reference explaining what's required, so that I can find all human-dependent sections by searching for a single marker pattern.

#### Acceptance Criteria

1. WHEREVER the pipeline inserts an `[AUTHOR VOICE]` marker, THE Rewrite_Agent SHALL also insert immediately below it a `[NOTE TO AUTHOR: <explanation>]` block containing: what personal content is needed, why it matters at this point in the book, and a suggested length (in words).
2. WHERE the Author_Gate blocks the Introduction chapter, THE Pipeline SHALL insert in the Introduction text a `[NOTE TO AUTHOR: PERSONAL_STORY — Your personal story is the credibility anchor for the entire book. Write 200–500 words about: where this model came from, one real before-and-after, and who you've watched it help. Without this, no publisher will take the book seriously.]` marker.
3. WHERE the Evidence_Agent flags a claim it cannot source, THE marker `[NOTE TO AUTHOR: ...]` SHALL include the specific claim text and a suggestion for what type of source would satisfy it (personal experience, general research reference, or reframing as synthesis).
4. ALL `[NOTE TO AUTHOR: ...]` markers SHALL follow a consistent format: `[NOTE TO AUTHOR: <category> — <explanation>]` where category is one of: PERSONAL_STORY, VOICE_MOMENT, SOURCE_NEEDED, DECISION_NEEDED.
5. THE Pipeline SHALL produce a consolidated `output/author_actions.md` file listing every `[NOTE TO AUTHOR]` marker across the entire manuscript with: chapter, location, category, and the full explanation text.
