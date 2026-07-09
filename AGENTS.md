# Charlotte Agent Operating Model

Charlotte is agent-agnostic.

These agents are role definitions, not bindings to any specific AI tool.

Any executor may run them:

- Kiro
- Codex
- Claude Code
- Cursor
- GitHub Actions
- n8n
- Local Python runner
- Future agent platform

## Core agent sequence

1. Outliner
2. Researcher
3. Drafter
4. Persona Reviewers
5. Continuity Warden
6. Safety Warden
7. Voice Warden
8. Editor
9. Assembler

## Rule

Agents communicate through files and contracts, not hidden chat memory.

Each agent must read the declared inputs, produce the declared output, and hand off to the next stage through the repository structure.

## Source of truth

The book source of truth is:

```text
foundation/Me_OS_Foundation.md
```

## Generated content

Generated content must remain under:

```text
output/
```

## Do not

- Do not bind the workflow to Kiro.
- Do not assume a specific model provider.
- Do not collapse all roles into one prompt.
- Do not overwrite foundation material.
- Do not store critical workflow state only in chat.
