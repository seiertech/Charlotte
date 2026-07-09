# Charlotte Alpha Runbook

This runbook is the practical operating guide for getting Charlotte Alpha to produce a first draft.

## 1. Clone the repo

```bash
git clone https://github.com/seiertech/Charlotte.git
cd Charlotte
```

## 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

## 3. Add the NIM key locally

Do not commit keys to GitHub.

Linux/macOS/Git Bash:

```bash
export NIM_API_KEY="your_new_key_here"
```

Windows PowerShell:

```powershell
$env:NIM_API_KEY="your_new_key_here"
```

## 4. Confirm foundation material

Check:

```text
foundation/Me_OS_Foundation.md
```

This must contain the real source material, not placeholder text.

## 5. Smoke test outline

```bash
python orchestrator/run.py --outline-only
```

Expected output:

```text
output/book_outline.md
output/ledger.jsonl
```

## 6. Run one chapter

```bash
python orchestrator/run.py --chapter 1
```

Expected outputs:

```text
output/chapter_plans/ch01.md
output/drafts/ch01.md
output/reviews/ch01_*.md
output/final_chapters/ch01.md
```

## 7. Run full first draft

```bash
python orchestrator/run.py
```

Expected output:

```text
output/full_first_draft.md
```

## 8. If it fails

Most likely causes:

- `NIM_API_KEY` is not set in the same terminal.
- Foundation file is still placeholder.
- NIM endpoint is temporarily unavailable.
- Context is too large for a single call.

First recovery command:

```bash
python orchestrator/run.py --chapter 1
```

This isolates the issue before running the whole book.
