# Charlotte

Charlotte is a Kiro-ready Book Factory for generating a complete first draft from supplied foundation material.

## Current status

This repository has been seeded with:

- Kiro steering files
- First-draft workflow spec
- Agent prompts
- Persona reviewers
- A simple Python orchestrator
- Config file
- Output folder
- Foundation placeholder

## Important

`foundation/Me_OS_Foundation.md` is currently a placeholder. Replace it with the full foundation text from the source draft package before running a real manuscript generation.

## Setup

```bash
pip install -r requirements.txt
```

## Run outline only

```bash
python orchestrator/run.py --outline-only
```

## Run one chapter

```bash
python orchestrator/run.py --chapter 1
```

## Run full first draft scaffold

```bash
python orchestrator/run.py
```

This writes:

```text
output/full_first_draft.md
```

## Kiro usage

Open this repository in Kiro and use:

```text
.kiro/steering/book-factory.md
.kiro/specs/first-draft-workflow/requirements.md
.kiro/specs/first-draft-workflow/tasks.md
```

Primary Kiro prompt:

```text
Review this repository as the Charlotte Book Factory.

Goal:
Make the shortest path to generating a complete first draft at output/full_first_draft.md.

Instructions:
1. Inspect the repository.
2. Confirm the agent workflow.
3. Confirm orchestrator/run.py creates the required output folders.
4. Replace the deterministic scaffold with real model calls only where needed.
5. Preserve the agent handoff model.
6. Do not overwrite foundation/Me_OS_Foundation.md.
7. Keep generated manuscript content inside output/.
8. Run one chapter test before full manuscript generation.

Success condition:
The repository can generate output/full_first_draft.md from the foundation file.
```
