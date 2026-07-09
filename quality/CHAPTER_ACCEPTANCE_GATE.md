# Chapter Acceptance Gate

A Charlotte chapter is accepted only when it passes these checks.

## Required artefacts

For Chapter XX:

```text
output/chapter_plans/chXX.md
output/drafts/chXX.md
output/reviews/chXX_combined.md
output/final_chapters/chXX.md
```

## Minimum quality checks

- One clear chapter idea.
- Strong opening.
- Clear reader benefit.
- No filler sections.
- No contradiction with earlier chapters.
- No concepts revealed too early.
- Voice remains calm, human, and direct.
- Safety concerns are either resolved or explicitly flagged.
- Chapter ends with a meaningful transition.

## Automatic block conditions

Block the chapter if any review says:

```text
status: BLOCK
```

or contains:

```text
BLOCK
```

## Human review note

For Alpha, the orchestrator writes review artefacts but does not yet automatically stop on all block conditions. Human review remains required before publication.
