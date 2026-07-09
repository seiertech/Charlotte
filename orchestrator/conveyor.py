"""Charlotte conveyor — runs chapters one at a time with smart model routing.

Model routing:
  - 675B (mistral-large-3): Drafter only — the actual chapter prose
  - 119B (mistral-small-4): Everything else (researcher, architect, all reviewers,
    wardens, personas, editor, revision, transition)

This keeps 675B call count to exactly 1-2 per chapter, well under rate limits.
Every chapter is committed to git immediately after completion.

Usage:
    python3 orchestrator/conveyor.py            # all pending chapters
    python3 orchestrator/conveyor.py 5 15       # chapters 5 to 15 inclusive
    python3 orchestrator/conveyor.py 7 7        # chapter 7 only
"""

from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import orchestrator.run as R
from orchestrator.book_state import BookState, ChapterRecord
from orchestrator.ledger import Ledger
from providers.model_client import ModelClient, client_from_config, OpenAICompatibleClient

# Only these agent names get routed to the big model
BIG_MODEL_AGENTS = {"drafter"}

# How long to pause between chapters (seconds) — gives rate limit time to breathe
INTER_CHAPTER_PAUSE = 90

# Retry settings for 429 / timeouts
MAX_RETRIES = 4
RETRY_BACKOFF = [60, 120, 180, 300]  # seconds to wait before each retry


def make_clients(cfg: dict) -> tuple[ModelClient, ModelClient]:
    """Return (big_client [675B], small_client [119B])."""
    big = client_from_config(cfg)                          # uses cfg["provider"] = 675B
    small_cfg = dict(cfg)
    small_cfg["provider"] = cfg.get("reviewer_provider", cfg["provider"])
    small = client_from_config(small_cfg)                  # uses reviewer_provider = 119B
    return big, small


def call_with_retry(client: ModelClient, messages: list, temperature: float) -> object:
    """Call client.complete with automatic retry on 429 / timeout."""
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return client.complete(messages, temperature=temperature)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"  ⚠ 429 rate limit — waiting {wait}s before retry {attempt + 1}/{MAX_RETRIES}...")
                time.sleep(wait)
                last_exc = e
            else:
                raise
        except Exception as e:
            wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
            print(f"  ⚠ {type(e).__name__} — waiting {wait}s before retry {attempt + 1}/{MAX_RETRIES}...")
            time.sleep(wait)
            last_exc = e
    raise last_exc


def patched_call_agent(big: ModelClient, small: ModelClient):
    """Return a version of R.call_agent that routes by agent name."""
    original = R.call_agent

    def _call(client, ledger, agent_name, agent_prompt, task, context, output_path, temperature=0.4):
        # Route: drafter → big model; everything else → small model
        chosen = big if agent_name in BIG_MODEL_AGENTS else small

        messages = [
            {"role": "system", "content": agent_prompt},
            {
                "role": "user",
                "content": (
                    f"# Task\n\n{task}\n\n"
                    f"# Repository Context\n\n{context}\n\n"
                    f"# Required Output\n\nWrite the complete artefact for `{output_path}` in Markdown."
                ),
            },
        ]
        response = call_with_retry(chosen, messages, temperature)
        R.write(output_path, response.content)
        ledger.append(
            "agent_output",
            {
                "agent": agent_name,
                "output_path": output_path,
                "provider": response.provider,
                "model": response.model,
            },
        )
        return response.content

    return _call


def git_commit_chapter(n: int, title: str) -> None:
    path = f"output/final_chapters/ch{n:02}.md"
    subprocess.run(["git", "add", path, "output/status.md"], cwd=ROOT, check=True)
    msg = f"Chapter {n:02}: {title[:60]}"
    result = subprocess.run(
        ["git", "commit", "-m", msg], cwd=ROOT, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  → committed: {msg}")
    else:
        print(f"  → already up to date (nothing new to commit)")


def run_one_chapter(cfg, big, small, ledger, foundation, outline, chapter, state):
    """Run the full pipeline for one chapter with dual-model routing."""
    n = int(chapter["number"])
    title = str(chapter["title"])

    print(f"\n{'='*60}")
    print(f"  ch{n:02}: {title}")
    print(f"  prose=675B  |  reviews=119B")
    print(f"{'='*60}")

    # Patch call_agent for the duration of this chapter
    original = R.call_agent
    R.call_agent = patched_call_agent(big, small)

    try:
        # Per-chapter research note (small model — short output)
        research = R.call_agent(
            small, ledger, "researcher", R.agent(cfg, "researcher"),
            f"Create a focused research/concept pack for Chapter {n} only: '{title}'. "
            f"Do not write chapter prose. Respect the reveal order. "
            f"Provide concrete examples from varied life domains.",
            R.build_base_context(cfg, foundation) + f"\n\n# Book Outline\n{outline}",
            f"output/research_ch{n:02}.md",
            temperature=0.1,
        )

        final = R.run_chapter(
            cfg, big, ledger, foundation, outline, research, chapter, state
        )
    finally:
        R.call_agent = original  # always restore

    return final


def main() -> None:
    cfg = R.load_config()
    cfg["provider"]["timeout_seconds"] = 600
    cfg["workflow"]["max_revisions"] = 1

    big, small = make_clients(cfg)
    ledger = Ledger(ROOT)
    state = BookState.load(ROOT / "output/book_state.json")

    foundation = R.read(cfg["book"]["foundation_file"])
    outline = R.read("output/book_outline.md")
    if not outline.strip():
        raise SystemExit("output/book_outline.md is missing — run --outline-only first")

    chapters = R.extract_chapters(outline)

    # Seed state with all chapter titles for transition agent
    for c in chapters:
        n = int(c["number"])
        if not state.get(n):
            state.upsert_chapter(ChapterRecord(number=n, title=str(c["title"])))
    state.save(ROOT / "output/book_state.json")

    # Parse range args
    if len(sys.argv) >= 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    elif len(sys.argv) == 2:
        start, end = int(sys.argv[1]), int(sys.argv[1])
    else:
        start, end = 0, 9999

    selected = [c for c in chapters if start <= int(c["number"]) <= end]
    print(f"\nCharlotte Conveyor")
    print(f"  Prose  (675B): {cfg['provider']['model']}")
    print(f"  Review (119B): {cfg.get('reviewer_provider', cfg['provider'])['model']}")
    print(f"  Chapters: {start}–{end}  ({len(selected)} to run)")
    print(f"  Word target: {cfg['workflow']['chapter_word_target']}")
    print(f"  Inter-chapter pause: {INTER_CHAPTER_PAUSE}s")

    R.ensure_dirs()

    for idx, chapter in enumerate(selected):
        n = int(chapter["number"])
        title = str(chapter["title"])
        final_path = ROOT / f"output/final_chapters/ch{n:02}.md"

        # Skip if already complete
        if final_path.exists() and final_path.stat().st_size > 500:
            rec = state.get(n)
            if rec and not rec.blocked:
                print(f"\n  ch{n:02} — skipping (already complete, {final_path.stat().st_size // 1000}KB)")
                continue

        final = run_one_chapter(cfg, big, small, ledger, foundation, outline, chapter, state)
        wc = R.word_count(final)
        print(f"\n  ✓ ch{n:02} complete — {wc} words")

        R.write_status(cfg, chapters, state)
        git_commit_chapter(n, title)

        # Pause between chapters — not after the last one
        if idx < len(selected) - 1:
            remaining = len(selected) - idx - 1
            print(f"  ⏸  pausing {INTER_CHAPTER_PAUSE}s before next chapter ({remaining} remaining)...")
            time.sleep(INTER_CHAPTER_PAUSE)

    print(f"\n{'='*60}")
    print("=== Conveyor complete ===")
    done = sorted(p.name for p in (ROOT / "output/final_chapters").glob("ch*.md"))
    print(f"Chapters in output/final_chapters/ ({len(done)} total): {done}")


if __name__ == "__main__":
    main()
