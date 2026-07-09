# First Draft Workflow Requirements

The system shall generate a complete first draft manuscript from the supplied foundation file and agent workflow.

## Inputs

- foundation/Me_OS_Foundation.md
- config.yaml
- agents/*.md
- agents/personas/*.md

## Outputs

- output/book_outline.md
- output/research_pack.md
- output/chapter_plans/
- output/drafts/
- output/reviews/
- output/final_chapters/
- output/full_first_draft.md

## Workflow

1. Generate the book outline.
2. Generate the research and concept pack.
3. Plan each chapter.
4. Draft each chapter.
5. Run persona review loop.
6. Run continuity review.
7. Run safety review.
8. Run voice review.
9. Edit chapter.
10. Assemble the full first draft.

## Success condition

The repository can produce output/full_first_draft.md from the existing foundation material.
