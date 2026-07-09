"""Charlotte lean conveyor — 4 calls per chapter, maximum speed.

Pipeline: Researcher → Architect → Drafter(675B) → Editor(119B)

No reviewers, no wardens, no personas, no revision loop on the first draft.
Those belong in a quality pass over the completed manuscript, not per-chapter gating.

Usage:
    python3 orchestrator/conveyor.py            # all pending chapters
    python3 orchestrator/conveyor.py 2 15       # chapters 2 to 15
    python3 orchestrator/conveyor.py 5 5        # chapter 5 only
"""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml
from orchestrator.book_state import BookState, ChapterRecord
from orchestrator.ledger import Ledger
from providers.model_client import ModelClient, client_from_config

# Retry settings for 429
MAX_RETRIES = 5
RETRY_BACKOFF = [30, 60, 90, 120, 180]

# Pause between chapters (seconds)
INTER_CHAPTER_PAUSE = 30


def read(path: str) -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write(path: str, content: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def load_config() -> dict:
    return yaml.safe_load(read("config.yaml"))


def call(client: ModelClient, system_prompt: str, user_prompt: str) -> str:
    """Call with retry on 429/timeout."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.complete(messages, temperature=0.15)
            return resp.content
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"    ⚠ 429 — waiting {wait}s (retry {attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"    ⚠ {type(e).__name__} — waiting {wait}s (retry {attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
            else:
                raise
    return ""


def git_commit_chapter(n: int, title: str) -> None:
    subprocess.run(["git", "add", f"output/final_chapters/ch{n:02}.md", "output/status.md"],
                   cwd=ROOT, check=True, capture_output=True)
    result = subprocess.run(["git", "commit", "-m", f"Chapter {n:02}: {title[:60]}"],
                           cwd=ROOT, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"    → committed")
    else:
        print(f"    → already up to date")


def extract_chapters(outline: str) -> list:
    import re
    chapters = []
    seen = set()
    for line in outline.splitlines():
        clean = line.strip().lstrip("#*>-•\t ").strip()
        match = re.match(r"^Chapter\s+(\d+)\s*[\).:\-–—]?\s*(.+)$", clean, re.I)
        if match:
            number = int(match.group(1))
            if number not in seen:
                seen.add(number)
                title = match.group(2).strip().strip("*_# ").strip()
                if title:
                    chapters.append({"number": number, "title": title})
    return chapters


def main() -> None:
    cfg = load_config()

    # Build clients
    cfg["provider"]["timeout_seconds"] = 600
    big_client = client_from_config(cfg)  # 675B for drafter

    small_cfg = dict(cfg)
    small_cfg["provider"] = cfg.get("reviewer_provider", cfg["provider"])
    small_client = client_from_config(small_cfg)  # 119B for researcher/architect/editor

    # Load state
    state = BookState.load(ROOT / "output/book_state.json")
    ledger = Ledger(ROOT)
    foundation = read(cfg["book"]["foundation_file"])
    outline = read("output/book_outline.md")
    if not outline.strip():
        raise SystemExit("No outline found — run --outline-only first")

    chapters = extract_chapters(outline)
    word_target = cfg.get("workflow", {}).get("chapter_word_target", 1400)

    # Load agent prompts
    researcher_prompt = read(cfg["agents"]["researcher"])
    architect_prompt = read(cfg["agents"]["chapter_architect"])
    drafter_prompt = read(cfg["agents"]["drafter"])
    editor_prompt = read(cfg["agents"]["editor"])

    # Seed state
    for c in chapters:
        n = int(c["number"])
        if not state.get(n):
            state.upsert_chapter(ChapterRecord(number=n, title=str(c["title"])))
    state.save(ROOT / "output/book_state.json")

    # Parse args
    if len(sys.argv) >= 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    elif len(sys.argv) == 2:
        start, end = int(sys.argv[1]), int(sys.argv[1])
    else:
        start, end = 0, 9999

    selected = [c for c in chapters if start <= int(c["number"]) <= end]

    print(f"\n{'='*50}")
    print(f"  CHARLOTTE LEAN CONVEYOR")
    print(f"  Pipeline: Researcher → Architect → Drafter(675B) → Editor")
    print(f"  4 calls per chapter | {word_target} word target")
    print(f"  Chapters: {start}–{end} ({len(selected)} to run)")
    print(f"{'='*50}")

    (ROOT / "output/final_chapters").mkdir(parents=True, exist_ok=True)

    for idx, chapter in enumerate(selected):
        n = int(chapter["number"])
        title = str(chapter["title"])
        final_path = ROOT / f"output/final_chapters/ch{n:02}.md"

        print(f"\n  ch{n:02}: {title}")

        # Context for all calls
        base_ctx = (
            f"# Book: {cfg['book']['title']}\n\n"
            f"# Foundation Material\n{foundation}\n\n"
            f"# Book Outline\n{outline}\n\n"
            f"# Previous chapters context\n{state.windowed_context(n, 3)}\n"
        )

        # 1. RESEARCHER (119B)
        print(f"    [1/4] researcher...", end=" ", flush=True)
        research = call(small_client, researcher_prompt,
            f"Create a focused research/concept pack for Chapter {n}: '{title}'. "
            f"Provide concrete grounded examples from varied life domains. "
            f"Name what must NOT be revealed yet. Do not write prose.\n\n{base_ctx}")
        write(f"output/research_ch{n:02}.md", research)
        print("done")

        # 2. ARCHITECT (119B)
        print(f"    [2/4] architect...", end=" ", flush=True)
        plan = call(small_client, architect_prompt,
            f"Plan Chapter {n}: '{title}'. Design the scene structure, opening beat, "
            f"grounded examples (2-3 varied life domains), closing pull, and 'Notice this in you' practice. "
            f"Target ~{word_target} words.\n\n{base_ctx}\n\n# Research Pack\n{research}")
        write(f"output/chapter_plans/ch{n:02}.md", plan)
        print("done")

        # 3. DRAFTER (675B) — the money call
        print(f"    [3/4] drafter (675B)...", end=" ", flush=True)
        draft = call(big_client, drafter_prompt,
            f"Write Chapter {n}: '{title}'. "
            f"Build full scenes with named people, physical sensations, varied life domains. "
            f"Target {word_target} words. Recognition before instruction. "
            f"Do NOT restate the foundation — expand it into lived moments.\n\n"
            f"{base_ctx}\n\n# Chapter Plan\n{plan}\n\n# Research Pack\n{research}")
        print("done")

        # 4. EDITOR (119B)
        print(f"    [4/4] editor...", end=" ", flush=True)
        final = call(small_client, editor_prompt,
            f"Edit Chapter {n}: '{title}'. Smooth flow, fix rhythm, ensure transitions work. "
            f"Do not add new concepts. Do not remove scenes or examples. Keep the weight.\n\n"
            f"# Draft to edit\n{draft}\n\n# Chapter Plan\n{plan}")
        write(f"output/final_chapters/ch{n:02}.md", final)
        print("done")

        # Word count
        import re
        wc = len(re.findall(r"\b\w+\b", final))
        print(f"    ✓ {wc} words")

        # Update state
        rec = state.get(n) or ChapterRecord(number=n, title=title)
        rec.summary = final[:800]
        rec.word_count = wc
        rec.final_path = f"output/final_chapters/ch{n:02}.md"
        rec.blocked = False
        state.upsert_chapter(rec)
        state.save(ROOT / "output/book_state.json")

        # Write status
        lines = ["# Charlotte Status", "", f"Book: {cfg['book']['title']}", "", "## Chapters"]
        for c in chapters:
            cn = int(c["number"])
            cp = ROOT / f"output/final_chapters/ch{cn:02}.md"
            r = state.get(cn)
            marker = "DONE" if cp.exists() else "PENDING"
            extra = f" ({r.word_count} words)" if r and cp.exists() else ""
            lines.append(f"- Chapter {cn}: {c['title']} — {marker}{extra}")
        write("output/status.md", "\n".join(lines) + "\n")

        # Commit
        git_commit_chapter(n, title)

        # Log
        ledger.append("chapter_complete_lean", {"chapter": n, "title": title, "words": wc})

        # Pause (not after last)
        if idx < len(selected) - 1:
            print(f"    ⏸ {INTER_CHAPTER_PAUSE}s pause...")
            time.sleep(INTER_CHAPTER_PAUSE)

    print(f"\n{'='*50}")
    print(f"  CONVEYOR COMPLETE")
    done = sorted(p.name for p in (ROOT / "output/final_chapters").glob("ch*.md"))
    print(f"  {len(done)} chapters: {done}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
