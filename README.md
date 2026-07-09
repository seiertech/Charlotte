# Charlotte

Charlotte is an agent-agnostic Book Factory repository.

It holds the book foundation, agent role definitions, handoff contracts, workflows, provider adapters, and generated manuscript outputs in a structure that any AI coding environment or agent runner can use.

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
├── providers/           # Model execution adapters
├── orchestrator/        # Local runner
├── foundation/          # Source truth for the book
├── output/              # Generated manuscript artefacts
├── quality/             # Acceptance gates
├── runbooks/            # Practical run instructions
├── adapters/            # Optional tool-specific instructions
├── config.yaml          # Neutral workflow and provider configuration
├── AGENTS.md            # Agent operating model
└── README.md
```

## Core workflow

```text
Foundation
→ Outliner
→ Researcher
→ Chapter Planner
→ Drafter
→ General Reviewer
→ Persona Reviewers
→ Continuity Warden
→ Safety Warden
→ Voice Warden
→ Editor
→ Assembler
→ First Draft
```

## Current execution status

Charlotte Alpha now has a neutral execution engine.

The engine:

- Loads `config.yaml`
- Loads the agent role files
- Calls the configured provider
- Writes each agent output into `output/`
- Records execution events into `output/ledger.jsonl`
- Writes `output/status.md`
- Assembles `output/full_first_draft.md`
- Stops if the foundation file still contains placeholder text

## Current NIM configuration

Charlotte is configured for NVIDIA NIM:

```yaml
provider:
  type: "nim"
  protocol: "openai_compatible"
  base_url: "https://integrate.api.nvidia.com/v1"
  model: "mistralai/mistral-small-4-119b-2603"
  api_key_env: "NIM_API_KEY"
```

Runtime defaults:

```yaml
runtime_defaults:
  max_tokens: 16384
  temperature: 0.1
  top_p: 1.0
  reasoning_effort: "high"
  tool_choice: "auto"
```

Do not commit secrets.

## Add the NIM key locally

Linux/macOS/Git Bash:

```bash
export NIM_API_KEY="your_new_key_here"
```

Windows PowerShell:

```powershell
$env:NIM_API_KEY="your_new_key_here"
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

## Run full first draft

```bash
python orchestrator/run.py
```

This writes:

```text
output/full_first_draft.md
```

## Recommended first run

Run one chapter first:

```bash
python orchestrator/run.py --chapter 1
```

Then inspect:

```text
output/final_chapters/ch01.md
output/reviews/ch01_combined.md
output/status.md
output/ledger.jsonl
```

If Chapter 1 is acceptable, run the full draft.

## Using with Kiro

Open the GitHub repo in Kiro and point Kiro at:

```text
AGENTS.md
workflows/first-draft-workflow.md
contracts/handoff-contract.md
adapters/kiro.md
runbooks/ALPHA_RUNBOOK.md
config.yaml
```

Kiro should execute the neutral repo workflow. It should not become the owner of the architecture.
