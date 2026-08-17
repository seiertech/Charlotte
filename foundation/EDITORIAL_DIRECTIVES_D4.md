# EDITORIAL DIRECTIVES — DRAFT 4

*Governing rules for the editorial rewrite pipeline. This document supersedes `DRAFT3_DIRECTIVES.md` on any topic it addresses explicitly. Where this document is silent, DRAFT3_DIRECTIVES remains in force. Every agent in the Draft 4 pipeline SHALL read and enforce this file.*

---

## 1. Character Consolidation Rules

Draft 3 suffered from character proliferation: interchangeable one-off names appearing once and vanishing. Draft 4 consolidates to a **fixed cast of 4–5 recurring characters** defined in `foundation/character_bible.md`.

### Rules

1. **All named characters must come from the Character Bible.** No agent may introduce a new named character. The cast is closed after Bible creation.
2. **One-off Draft 3 characters are mapped to the fixed cast.** When a Draft 3 chapter uses a character not in the Bible, the Rewrite Agent SHALL replace that character with the Bible character assigned to the same primary layer, preserving the narrative function (the *what happens*), while changing the *who*.
3. **Unnamed background figures** (e.g., "the barista," "a fellow commuter") are permitted for incidental interaction only. Maximum **2 unnamed figures per chapter**. They SHALL NOT carry dialogue exceeding one sentence.
4. **No character may dominate more than 40%** of all chapter-level appearances (one appearance = present in a chapter, regardless of scene count within it).
5. **Every character must have a distinct physical signature** (defined in the Character Bible) that appears on *every* appearance. This is how the reader recognises them without re-introduction.
6. **The five-cause proof** (Ch01 Doorway) uses the fixed cast — five characters, one symptom, five layer-causes. The characters are NOT new one-off figures; they are the recurring cast demonstrating the thesis.

---

## 2. Repetition-Reduction Targets

Both editors identified pervasive repetition: restated explanations, duplicated paragraph-level content across chapters, and the same metaphors recurring without development.

### Rules

1. **De-duplicate across chapters.** If a concept (e.g., "the layers stack") is fully explained in one chapter, subsequent chapters SHALL reference it briefly (one sentence max) rather than re-explain.
2. **Cut restated paragraphs.** Any paragraph whose content duplicates an earlier paragraph within the same chapter or within the preceding chapter SHALL be removed or condensed to a single bridging sentence.
3. **Retire overused phrases.** The following are BANNED (hard fail — earn one back per chapter only by writing something better first): `chest`, `clench`, `clenched`, `shoulders`, `lands like a stone`, `why can't I just`, `the words swim`. Each character has a *different* physical signature; no universal body language.
4. **Metaphor development, not repetition.** A metaphor may recur ONLY if it is *developed* (extended, complicated, or subverted). Exact repetition of a metaphorical framing across chapters is cut.
5. **Net effect:** despite expansion, individual passages are tighter. Repetition cuts fund the space for new mechanism/failure-mode content.

---

## 3. Production-Artifact Definitions

Draft 3 contains residual production artifacts from the pipeline process. These must be detected and removed before publication.

### Defined Artifact Patterns

| # | Pattern | Description | Action |
|---|---------|-------------|--------|
| 1 | `EDITOR FLAG` | Literal string (any case) used as internal review marker | REMOVE |
| 2 | `[Author's note]` | Placeholder for author-supplied content | REMOVE (except in Introduction — preserve and route to Author Gate) |
| 3 | `## <phrase> purpose:` | Outline-style header describing a section's structural purpose | REMOVE |
| 4 | Chapter misnumbering | Any chapter number reference that doesn't match the sequential position in the TOC | CORRECT to match TOC |
| 5 | Internal YAML/code blocks | Fenced blocks containing workflow keys (`status:`, `assignee:`, `draft_notes:`) rather than reader-facing example content | REMOVE |
| 6 | `<!-- ... -->` HTML comments | Internal pipeline comments not intended for readers | REMOVE |
| 7 | `TODO`, `FIXME`, `HACK` | Developer-style task markers | REMOVE or resolve |

### Rules

1. The Artifact Scrubber SHALL scan every chapter for ALL patterns above.
2. Any artifact found SHALL be removed and logged (type, location, snippet, action).
3. Exception: `[Author's note]` in the Introduction chapter is preserved and routed to the Author Gate for human resolution.
4. A chapter that passes the Artifact Scrubber SHALL contain ZERO instances of the above patterns (except the preserved Introduction case).
5. If zero artifacts are found, the scrubber produces the chapter unchanged with a log stating "0 artifacts found."

---

## 4. Author-Presence Insertion Points

The editors converged: the book's credibility depends on the author's presence — not as a character, but as the mind and person behind the system. Draft 3 has almost none. Draft 4 inserts the author at **7 defined points** using `[AUTHOR VOICE]` markers with accompanying `[NOTE TO AUTHOR]` instructions.

### Insertion Points

| # | Chapter | Location | Type | What Is Needed |
|---|---------|----------|------|----------------|
| 1 | Ch00 — Introduction | Opening section ("How it's helped me") | PERSONAL_STORY | The credibility anchor: where this model came from, one real before-and-after, who you've watched it help. 200–500 words. |
| 2 | Ch01 — The Doorway | After the five-cause proof, before the "you" turn | VOICE_MOMENT | A brief personal moment of recognising the system in yourself — the first time you saw the layers. 50–100 words. |
| 3 | Ch03 — Wiring | Within the "reactions before thought" section | VOICE_MOMENT | A personal experience of reacting before thinking — your own wiring catching you. 50–100 words. |
| 4 | Ch07 — The Method Made Whole | After presenting the full two-question method | VOICE_MOMENT | A moment the method worked (or honestly failed) for you — real, not polished. 100–200 words. |
| 5 | Ch08 — Worked Situations | Opening or between situations | VOICE_MOMENT | How you discovered you'd been working on the wrong layer — the personal origin of the sequencing insight. 100–150 words. |
| 6 | Ch10 — Belief, Then Faith | Within the faith section, after the trust/faith distinction | VOICE_MOMENT | What you hold to when proof isn't there — your own relationship to faith (agnostic of religion). 100–200 words. |
| 7 | Ch11 — Growth Map | Closing section | VOICE_MOMENT | The author's own growth map — what changed in you from applying this. The book's emotional close. 150–300 words. |

### Rules

1. At each insertion point, the Rewrite Agent SHALL insert an `[AUTHOR VOICE]` marker.
2. Immediately below each marker, the Rewrite Agent SHALL insert a `[NOTE TO AUTHOR: <CATEGORY> — <explanation>]` block specifying what is needed, why it matters at this point, and a suggested word count.
3. The Rewrite Agent SHALL NOT fabricate autobiographical content, personal opinions, or first-person experiences on the author's behalf.
4. Categories: `PERSONAL_STORY` (for the major Ch00 piece), `VOICE_MOMENT` (for all other insertion points).

---

## 5. Sourcing Requirements

Both editors flagged unsourced claims as a credibility risk. Draft 4 must have a credible evidentiary spine without becoming a textbook.

### Rules

1. **Every psychological, neurological, behavioural, or health-related claim** that is stated as fact (not clearly positioned as the author's model) SHALL have either:
   - A lightweight inline reference to an established, well-known source (e.g., endnote format: "Sapolsky, 2004"), OR
   - A qualifying phrase that honestly positions it as synthesis (e.g., "in my model…", "as a practical rule…", "what the research suggests, broadly…")
2. **The Evidence Agent** runs after the Rewrite Agent and before the Artifact Scrubber. It is responsible for inserting sources and qualifiers.
3. **Non-fabrication rule (absolute).** No agent SHALL invent citations, fabricate study names, attribute claims to specific researchers without verification, or generate fictitious publication details. References must be to established, well-known findings only.
4. **Unfixable claims** — where a claim cannot be sourced or qualified without fundamentally changing its meaning — SHALL be flagged with: `[NOTE TO AUTHOR: SOURCE_NEEDED — <specific claim text>]`.
5. **Evidence log** — the Evidence Agent produces a per-chapter log listing: claims found, action taken (sourced / qualified / flagged), and reference or qualifier added.
6. **Tone.** References are light — endnotes preferred, never mid-sentence academic parentheticals. The mentor voice does not read like a paper.

---

## 6. Layer-Boundary Clarifications

Draft 3's layers sometimes blur into each other. Draft 4 enforces crisp boundaries using the Model Bible as the single source of truth.

### Rules

1. **Every layer reference SHALL use the exact name from the Model Bible:** Body, Wiring, Habit, Room, Story. No synonyms, no ad-hoc variants, no computing terms (except one-time optional gloss per chapter).
2. **Every currency reference SHALL use the exact name from the Model Bible:** Charge, Fuel, Pressure. Same rule.
3. **The Wiring-vs-Story boundary** is the most common confusion. The Model Bible provides a discrimination test (at least 2 yes/no criteria). The Rewrite Agent SHALL apply this test when a Draft 3 passage ambiguously mixes the two.
4. **Each layer gets its own sensory grammar** (enforced by the Rewrite Agent and Continuity Auditor):
   | Layer | Permitted register | Forbidden |
   |-------|-------------------|-----------|
   | Body | weight, thinness, blur, temperature | anything psychological |
   | Wiring | speed, gear-slip, reaction-before-decision | anything slow |
   | Habit | groove, automaticity, sleepwalking | anything effortful |
   | Room | temperature, volume, pull, weather | anything solitary |
   | Story | narration, the uninvited sentence, the coat | anything sensory |
5. **Commonly mistaken for** — each layer chapter SHALL include a section explaining which OTHER layer this one is most often confused with and how to tell the difference.
6. **Diagnostic sequence.** The recommended evaluation order is always: Body → Wiring → Habit → Room → Story (bottom-up). This is the Model Bible's preferred sequence and SHALL be consistent across all chapters.

---

## 7. Taxonomy-Reframing Guidance

### General Reframing

The taxonomy in Draft 3 is presented as a classification system. Draft 4 reframes it as a **diagnostic tool** — something the reader *uses*, not something they *memorise*. The shift:
- FROM: "Here are five layers. Learn them."
- TO: "Here is a way to find where your problem lives. Use it."

### Rules

1. **The five-cause proof (Ch01)** is the reframing device. Before any layer is taught individually, the reader sees *one symptom with five different causes* — proving the taxonomy's value through demonstration, not assertion.
2. **Each layer chapter** opens with recognition ("you've felt this"), moves to mechanism ("here's why"), includes failure modes ("commonly mistaken for"), and closes with a practice ("notice this in you"). Not: definition → examples → exercise.
3. **Currencies are the cost-axis only.** They do NOT receive their own chapter. They appear as the "what's it costing you" dimension of the two-question diagnostic and in the Troubleshooting Reference's "Costing you" column. Never as a standalone framework.
4. **Scene rationing.** ONE full scene in the entire book — in the Doorway (Ch01), the best 500 words in the manuscript. Everywhere else: micro-scenes of 1–3 sentences used as *evidence mid-argument*, never as overtures.
5. **POV division of labour.** Third person demonstrates (the taxonomy). Second person applies (the turn to the reader). First person argues (the author's reasoning). No passage violates this division without justification.

### Chapter 9 — Constraint Taxonomy Rewrite

Chapter 9 (The Hard Cases) currently treats all constraints as equivalent. Draft 4 SHALL restructure the constraint taxonomy into **5 distinct categories**, each with different implications for the reader:

| # | Category | Definition | Example | Appropriate Response |
|---|----------|------------|---------|---------------------|
| 1 | **Immutable constraint** | A condition that will not change regardless of action | Genetic condition, permanent disability, irreversible loss | Adaptation and integration. The system works around it. |
| 2 | **Currently constrained** | A condition that is fixed *now* but may change with time or treatment | Chronic illness in active phase, grief in acute stage, recovery from surgery | Patience and management now; reassess as condition evolves. |
| 3 | **Externally imposed constraint** | A barrier created by systems, structures, or other people — not by the reader's own wiring | Poverty, systemic discrimination, caregiving obligations imposed by circumstance | Challenge the system, seek structural change, access support. NOT "adapt internally." |
| 4 | **Changeable-but-costly constraint** | A situation that *could* change but at significant personal cost | A marriage that could end, a career that could shift, a location that could change | Honest cost-benefit assessment. The book's job is to name the cost clearly, not to decide for the reader. |
| 5 | **Unsafe situation** | A situation where the reader is at risk of harm | Abuse (physical, emotional, financial), active danger, coercive control | **Exit, boundary, or safety plan.** The answer is NEVER adaptation. Tool 12 (The Brave Phone Call) applies immediately. |

#### Chapter 9 Enforcement Rules

1. The Rewrite Agent SHALL apply all 5 categories when rewriting Chapter 9, with clear examples and distinct guidance for each.
2. The chapter SHALL include an explicit statement: the book's "adapt around the constraint" advice applies ONLY to categories 1 (immutable) and 2 (currently constrained).
3. For category 3 (externally imposed): the chapter SHALL state clearly that the honest answer may be to challenge the external system, not to adapt internally.
4. For category 5 (unsafe): the chapter SHALL state that adaptation is NEVER appropriate and direct the reader to exit, boundary, or professional help.
5. The Continuity Auditor SHALL verify that all 5 categories appear in Chapter 9 and match these definitions.

### Chapter 10 — Faith/Trust Distinction

Chapter 10 (Belief, Then Faith) retains **"faith"** as the primary term. The Rewrite Agent SHALL insert a paragraph (100–200 words) distinguishing faith from trust within the first 500 words of the chapter body (after any opening scene or micro-scene).

The paragraph SHALL:
- (a) Acknowledge that "faith" carries religious and metaphysical connotations for many readers.
- (b) Distinguish faith from trust: trust implies evidence-based confidence in something already partially proven; faith operates precisely where evidence runs out.
- (c) State clearly that this book uses "faith" to mean the capacity to act without proof, to hold direction when the data isn't in yet — agnostic of religion.
- (d) Position the terminology as a deliberate choice, not an oversight or carelessness — the word was chosen because no weaker word captures the function.

---

## Per-Chapter Word Count Targets — Draft 4

The Rewrite Agent and Editorial Gate use this table instead of a flat percentage reduction. Draft 4 **expands** the manuscript from ~25,000 words to 33,000–37,000 words by simultaneously cutting repetition AND adding substantive new content (mechanism explanations, failure modes, hard cases, counterexamples).

| Chapter | Title | D3 Word Count | D4 Target Min | D4 Target Max | Notes |
|---------|-------|---------------|---------------|---------------|-------|
| Ch00 | Introduction (A Note Before We Start) | 920 | 1,000 | 1,400 | Expansion: author note adds bulk |
| Ch01 | The Doorway — You Are a System | 1,450 | 2,200 | 2,800 | Expansion: five-cause proof + mechanism |
| Ch02 | Body | 2,100 | 2,600 | 3,200 | Add failure modes ("commonly mistaken for") |
| Ch03 | Wiring | 2,200 | 2,800 | 3,400 | Add hard cases, counterexamples |
| Ch04 | Habit | 1,800 | 2,400 | 3,000 | Expansion: model limitations |
| Ch05 | Room | 2,300 | 2,600 | 3,200 | Light expansion + de-duplication |
| Ch06 | Story | 2,100 | 2,600 | 3,200 | Add failure modes |
| Ch07 | The Method Made Whole | 2,400 | 2,800 | 3,400 | Add mechanism depth |
| Ch08 | Worked Situations | 1,900 | 2,400 | 3,000 | Expansion: counterexamples |
| Ch09 | The Hard Cases | 2,200 | 3,000 | 3,600 | Significant expansion: constraint taxonomy (5 categories) |
| Ch10 | Belief, Then Faith | 1,800 | 2,400 | 2,800 | Faith/trust distinction paragraph + depth |
| Ch11 | Growth Map (Watching It Change) | 2,100 | 2,600 | 3,200 | Add hard cases |
| Ch12 | Appendix (Toolkit + Troubleshooting) | 1,700 | 2,200 | 2,800 | Closing expansion |
| **Total** | | **~25,000** | **~33,600** | **~37,000** | |

### Word Count Rules

1. The Editorial Gate per-chapter check SHALL validate each chapter's word count against this table. This **supersedes** the previous flat 15–25% reduction check.
2. The Editorial Gate book-level check SHALL verify that the total assembled manuscript falls within **33,000–37,000 words**.
3. If a chapter cannot reach its minimum target without padding, the Rewrite Agent SHALL log the shortfall with justification. The Editorial Gate may still BLOCK.
4. Word count is calculated as whitespace-separated tokens in the chapter body text, excluding the rewrite log, YAML front-matter, and any appended metadata.

---

## Content Expansion Guidance

Draft 4 expands by approximately 10,000 words of new substantive content. This section defines what types of new content are **permitted** and what is **forbidden**.

### Permitted New Content

| Type | Description | Where |
|------|-------------|-------|
| **Mechanism explanations** | Why lower layers constrain higher ones; what actually fails at the boundaries; why Story-work can't fix a Body problem | Each layer chapter (Ch02–Ch06) + Ch07 |
| **Failure modes** | Each layer's "commonly mistaken for" — the diagnosis error and its consequences | Each layer chapter (Ch02–Ch06) |
| **Hard cases** | The lowest layer that won't move; the reader who diagnosed correctly and still can't shift it | Ch09 primarily, references in Ch07 and Ch11 |
| **Counterexamples** | When the model doesn't apply cleanly; honest edge cases | Ch03, Ch04, Ch08 |
| **Model limitations** | What this framework can't do; what it isn't designed for; where it breaks | Ch04, Ch07, Ch09 |

### Forbidden New Content

| Type | Reason |
|------|--------|
| New concepts outside the Model Bible | The taxonomy is CLOSED at 5 layers + 3 currencies |
| New tools beyond the 12 in the Toolkit | The toolkit is CLOSED; additions require author decision |
| Content that contradicts the Foundation | `Me_OS_Foundation.md` remains the source of truth for the model itself |
| Fabricated research or unsourced claims stated as fact | See Sourcing Requirements (§5) |
| Clinical advice, diagnoses, or treatment recommendations | The book is explicitly not a clinical resource |
| Content that contradicts DRAFT3_DIRECTIVES on topics not addressed here | DRAFT3_DIRECTIVES remains in force for anything this document doesn't supersede |

---

## Directive Hierarchy

When this document and `DRAFT3_DIRECTIVES.md` address the same topic with different instructions:

1. **This document (EDITORIAL_DIRECTIVES_D4) wins.**
2. The conflict SHALL be logged in the rewrite log with both instructions and the resolution.
3. Where DRAFT3_DIRECTIVES addresses a topic NOT covered here, DRAFT3_DIRECTIVES remains in force.
4. Where neither document addresses a topic, `foundation/Me_OS_Foundation.md` is the source of truth.

---

## `[NOTE TO AUTHOR]` Marker Format

All points in the manuscript requiring human author input SHALL use a consistent marker format:

```
[NOTE TO AUTHOR: <CATEGORY> — <explanation>]
```

Where `<CATEGORY>` is one of:
- **PERSONAL_STORY** — Major autobiographical content (Ch00 credibility anchor)
- **VOICE_MOMENT** — Brief personal anecdote or reflection (insertion points §4)
- **SOURCE_NEEDED** — A claim the Evidence Agent could not source or qualify
- **DECISION_NEEDED** — A point requiring an author decision (naming, structural choice, etc.)

### Rules

1. Every `[NOTE TO AUTHOR]` marker SHALL include the category AND a clear explanation of what is needed.
2. All markers are consolidated post-assembly into `output/author_actions.md` — the author's single checklist.
3. No agent SHALL resolve a `[NOTE TO AUTHOR]` marker by generating content on the author's behalf.

---

*EDITORIAL DIRECTIVES — DRAFT 4 · v1.0*
