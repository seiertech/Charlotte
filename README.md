# Charlotte

Charlotte is an agent-agnostic Book Factory repository.

It is designed to hold the book foundation, agent role definitions, handoff contracts, workflows, and generated manuscript outputs in a structure that any AI coding environment or agent runner can use.

Kiro can access and operate this repo, but Charlotte is not a Kiro-specific project.

## Principle

The repository owns the process.
The tool only executes it.

This means Charlotte should be usable by:

- Kiro
- Codex
- Claude Code
- Cursor
- GitHub Actions
- n8n
- A local Python runner
- Any future agent system

## Repository model

```text
Charlotte/
├── agents/              # Role definitions and persona reviewers
├── contracts/           # Input/output handoff contracts
├── workflows/           # Tool-agnostic workflow definitions
├── orchestrator/        # Optional local runner
├── foundation/          # Source truth for the book
├── output/              # Generated manuscript artefacts
├── adapters/            # Optional tool-specific instructions
├── config.yaml          # Neutral workflow configuration
├── AGENTS.md            # Agent operating model
└── README.md
```

## Core workflow

```text
Foundation
→ Outliner
→ Researcher
→ Drafter
→ Persona Reviewers
→ Continuity Warden
→ Safety Warden
→ Voice Warden
→ Editor
→ Assembler
→ First Draft
```

## Important

`foundation/Me_OS_Foundation.md` is the source of truth for the book.

Generated content must go into `output/`.

Tool-specific files belong in `adapters/`, not in the core workflow.

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

## Using with Kiro

Open the GitHub repo in Kiro and point Kiro at:

```text
AGENTS.md
workflows/first-draft-workflow.md
contracts/handoff-contract.md
config.yaml
```

Kiro should execute the neutral repo workflow. It should not become the owner of the architecture.
