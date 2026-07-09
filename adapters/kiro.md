# Kiro Adapter

Charlotte is not a Kiro-specific repository.

Kiro should treat this repo as a neutral agent workflow repository.

## What Kiro should read first

```text
README.md
AGENTS.md
workflows/first-draft-workflow.md
contracts/handoff-contract.md
config.yaml
```

## Kiro instruction

Use the repository contracts and workflow as the source of truth.

Do not create a parallel `.kiro` architecture unless explicitly requested.

Do not move the core workflow into Kiro-specific specs.

Do not overwrite `foundation/Me_OS_Foundation.md`.

Generated manuscript content must go into `output/`.

## Kiro prompt

```text
You are operating inside the Charlotte repository.

Charlotte is an agent-agnostic Book Factory. Do not convert it into a Kiro-specific project.

Read:
- README.md
- AGENTS.md
- workflows/first-draft-workflow.md
- contracts/handoff-contract.md
- config.yaml

Goal:
Execute the neutral first-draft workflow and produce output/full_first_draft.md.

Rules:
- Preserve the agent sequence.
- Preserve handoff artefacts.
- Use repository files, not hidden chat memory.
- Do not overwrite foundation/Me_OS_Foundation.md.
- Keep generated content under output/.
```
