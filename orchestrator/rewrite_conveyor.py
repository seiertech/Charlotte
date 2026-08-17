"""Charlotte editorial rewrite conveyor.

Orchestrator for the editorial rewrite pipeline (Draft 3 → Draft 4).
Equivalent to run.py for the first-draft workflow.

Pipeline sequence:
  Bible Creation (Model Bible, Character Bible)
  → Chapter Rewrite Loop:
      Rewrite Agent → Evidence Agent → Artifact Scrubber
      → Continuity Auditor → Editorial Gate → Revision on BLOCK
  → Assembly
  → Author Action Log
  → Book-level Editorial Gate

Usage:
    python orchestrator/rewrite_conveyor.py                  # full pipeline
    python orchestrator/rewrite_conveyor.py --chapter 3      # single chapter
    python orchestrator/rewrite_conveyor.py --bibles-only    # generate bibles and stop
    python orchestrator/rewrite_conveyor.py --assemble-only  # assemble passing chapters
    python orchestrator/rewrite_conveyor.py --no-resume      # ignore state, reprocess all
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.ledger import Ledger
from orchestrator.rewrite_state import RewriteState, RewriteChapterRecord
from orchestrator.author_gate import check_author_gate
from orchestrator.rewrite_validation import (
    validate_prerequisites,
    load_rewrite_config,
    PipelineError,
)
from providers.model_client import ModelClient, client_from_config


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
STATE_PATH = ROOT / "output" / "draft4_state.json"
STATUS_PATH = ROOT / "output" / "status_d4.md"
DRAFT4_DIR = ROOT / "output" / "draft4"
MANUSCRIPT_PATH = ROOT / "output" / "full_fourth_draft.md"
AUTHOR_ACTIONS_PATH = ROOT / "output" / "author_actions.md"

# Retry settings (same pattern as conveyor.py)
MAX_RETRIES = 5
RETRY_BACKOFF = [30, 60, 90, 120, 180]

# Pause between chapters (seconds)
INTER_CHAPTER_PAUSE = 5


# --------------------------------------------------------------------------
# IO helpers
# --------------------------------------------------------------------------
def read(path: str) -> str:
    """Read a file relative to ROOT, returning empty string if missing."""
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write(path: str, content: str) -> None:
    """Write content to a file relative to ROOT, creating dirs as needed."""
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def load_config() -> dict:
    """Load config.yaml from project root."""
    return yaml.safe_load(read("config.yaml"))


def ensure_dirs() -> None:
    """Ensure all output directories exist."""
    for path in [
        "output",
        "output/draft4",
        "output/reviews",
    ]:
        (ROOT / path).mkdir(parents=True, exist_ok=True)


def word_count(text: str) -> int:
    """Count words in text."""
    return len(re.findall(r"\b\w+\b", text))


def agent_prompt(cfg: dict, agent_key: str) -> str:
    """Load an agent definition file from the editorial_rewrite.agents config."""
    er_agents = cfg.get("editorial_rewrite", {}).get("agents", {})
    path = er_agents.get(agent_key, "")
    if not path:
        raise PipelineError(f"No agent path configured for '{agent_key}'")
    content = read(path)
    if not content.strip():
        raise PipelineError(f"Agent definition file empty or missing: {path}")
    return content


# --------------------------------------------------------------------------
# Model call with retry
# --------------------------------------------------------------------------
def call_agent(
    client: ModelClient,
    ledger: Ledger,
    agent_name: str,
    system_prompt: str,
    task: str,
    context: str,
    output_path: Optional[str] = None,
    temperature: float = 0.15,
) -> str:
    """Call a model with system prompt and user task+context. Retry on API errors.

    If output_path is provided, writes the response to that file.
    Records the invocation in the ledger with timestamp and duration.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"# Task\n\n{task}\n\n"
                f"# Context\n\n{context}"
            ),
        },
    ]

    start_time = time.time()
    response_content = ""

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.complete(messages, temperature=temperature)
            response_content = resp.content
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"    ⚠ 429 — waiting {wait}s (retry {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"    ⚠ {type(e).__name__} — waiting {wait}s (retry {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
            else:
                raise

    duration = time.time() - start_time

    if output_path:
        write(output_path, response_content)

    ledger.append(
        "rewrite_agent_call",
        {
            "agent": agent_name,
            "output_path": output_path or "",
            "duration_seconds": round(duration, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return response_content


# --------------------------------------------------------------------------
# Chapter discovery
# --------------------------------------------------------------------------
def discover_draft3_chapters(cfg: dict) -> List[Dict[str, object]]:
    """Discover Draft 3 chapters from output/draft3/ or output/final_chapters/.

    Returns list of dicts with 'number', 'title', 'path' keys.
    """
    # Prefer output/draft3/ but fall back to output/final_chapters/
    draft3_dir = ROOT / "output" / "draft3"
    final_dir = ROOT / "output" / "final_chapters"

    source_dir = draft3_dir if draft3_dir.exists() and list(draft3_dir.glob("ch*.md")) else final_dir

    chapters: List[Dict[str, object]] = []
    if source_dir.exists():
        for path in sorted(source_dir.glob("ch*.md")):
            match = re.match(r"ch(\d+)\.md", path.name)
            if match:
                number = int(match.group(1))
                # Extract title from first heading or use default
                content = path.read_text(encoding="utf-8")
                title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else f"Chapter {number}"
                chapters.append({
                    "number": number,
                    "title": title,
                    "path": str(path.relative_to(ROOT)),
                })

    return chapters


# --------------------------------------------------------------------------
# Task 8.1: Bible Generation
# --------------------------------------------------------------------------
def generate_model_bible(cfg: dict, client: ModelClient, ledger: Ledger) -> str:
    """Produce foundation/model_bible.md from Foundation + DRAFT3_DIRECTIVES + ED4.

    The Model Bible locks definitions, boundaries, diagnostic tests, inclusions/exclusions,
    and common confusions for all 5 layers and 3 currencies.
    """
    foundation = read(cfg["book"]["foundation_file"])
    draft3_directives = read("foundation/DRAFT3_DIRECTIVES.md")
    ed4_directives = read("foundation/EDITORIAL_DIRECTIVES_D4.md")

    system_prompt = (
        "You are the Bible Generator for the Charlotte Book Factory. "
        "Your task is to produce a comprehensive Model Bible that locks down "
        "definitions for the five-layer taxonomy and three currencies used in the book.\n\n"
        "The Model Bible must include for each of the 5 layers (Body, Wiring, Habit, Room, Story):\n"
        "- A one-sentence definition (maximum 30 words)\n"
        "- A list of what is included\n"
        "- A list of what is excluded\n"
        "- A diagnostic test (yes/no question)\n"
        "- A 'commonly confused with' section for each adjacent layer\n\n"
        "For each of the 3 currencies (Charge, Fuel, Pressure):\n"
        "- A one-sentence definition (maximum 30 words)\n"
        "- How it manifests in each of the 5 layers\n"
        "- Comparison statement vs each other currency\n\n"
        "Also include:\n"
        "- A diagnostic sequence with recommended evaluation order and feedback loops\n"
        "- A Wiring-vs-Story discrimination test with at least two yes/no criteria\n"
    )

    context = (
        f"# Foundation Material\n\n{foundation}\n\n"
        f"# DRAFT3_DIRECTIVES\n\n{draft3_directives}\n\n"
        f"# EDITORIAL_DIRECTIVES_D4\n\n{ed4_directives}\n"
    )

    task = (
        "Generate the complete Model Bible for 'THE SYSTEM OF YOU'. "
        "Output as a Markdown document suitable for foundation/model_bible.md. "
        "Follow the exact structure specified in the system prompt."
    )

    print("  Generating Model Bible...")
    content = call_agent(
        client, ledger, "bible_generator", system_prompt,
        task, context, "foundation/model_bible.md", temperature=0.1,
    )
    print("    ✓ Model Bible written to foundation/model_bible.md")
    return content


def generate_character_bible(cfg: dict, client: ModelClient, ledger: Ledger) -> str:
    """Produce foundation/character_bible.md from Foundation + Model Bible + ED4.

    The Character Bible defines the fixed cast of 4-5 recurring characters with
    stable identities, chapter-appearance maps, and distribution constraints.
    """
    foundation = read(cfg["book"]["foundation_file"])
    model_bible = read("foundation/model_bible.md")
    ed4_directives = read("foundation/EDITORIAL_DIRECTIVES_D4.md")

    system_prompt = (
        "You are the Bible Generator for the Charlotte Book Factory. "
        "Your task is to produce a Character Bible that defines a fixed cast of "
        "4-5 recurring characters for the book.\n\n"
        "Each character must have:\n"
        "- Name, age, occupation, life situation\n"
        "- Primary layer association\n"
        "- Secondary layer association (if applicable)\n"
        "- Physical signature (one concrete sensory detail)\n"
        "- 'What they carry' (one sentence describing core emotional burden)\n\n"
        "The Character Bible must also include:\n"
        "- A chapter-appearance map (13 chapters) with P/S/— indicators\n"
        "- No single character may exceed 40% of chapter-level appearances\n"
        "- At least one character assigned to each of the 5 layers as primary vehicle\n"
    )

    context = (
        f"# Foundation Material\n\n{foundation}\n\n"
        f"# Model Bible\n\n{model_bible}\n\n"
        f"# EDITORIAL_DIRECTIVES_D4\n\n{ed4_directives}\n"
    )

    task = (
        "Generate the complete Character Bible for 'THE SYSTEM OF YOU'. "
        "Output as a Markdown document suitable for foundation/character_bible.md. "
        "Follow the exact structure specified in the system prompt. "
        "Ensure the chapter-appearance map covers all 13 chapters and respects "
        "the 40% cap per character."
    )

    print("  Generating Character Bible...")
    content = call_agent(
        client, ledger, "bible_generator", system_prompt,
        task, context, "foundation/character_bible.md", temperature=0.1,
    )
    print("    ✓ Character Bible written to foundation/character_bible.md")
    return content


# --------------------------------------------------------------------------
# Task 8.2: Chapter Rewrite Loop
# --------------------------------------------------------------------------
def run_rewrite_chapter(
    cfg: dict,
    client: ModelClient,
    ledger: Ledger,
    chapter: Dict,
    state: RewriteState,
    model_bible: str,
    character_bible: str,
    directives_d4: str,
    directives_d3: str,
    foundation: str,
    prev_d4: str,
) -> str:
    """Run full chapter pipeline: rewrite → evidence → scrub → audit → gate → revision loop.

    Updates state after each status transition. On BLOCK from auditor or gate,
    loops back to Rewrite Agent up to max_revisions times.

    Returns the final chapter content (or empty string if blocked/failed).
    """
    er_cfg = cfg.get("editorial_rewrite", {})
    max_revisions = int(er_cfg.get("max_revisions", 3))
    run_scrubber = er_cfg.get("run_artifact_scrubber", True)
    run_auditor = er_cfg.get("run_continuity_auditor", True)
    run_gate = er_cfg.get("run_editorial_gate", True)

    n = int(chapter["number"])
    title = str(chapter["title"])
    prefix = f"ch{n:02}"
    d3_path = str(chapter.get("path", ""))
    d3_content = read(d3_path) if d3_path else ""
    d3_wc = word_count(d3_content)

    # Update state to rewriting
    record = state.get(n) or RewriteChapterRecord(number=n, title=title)
    record.title = title
    record.status = "rewriting"
    record.d3_word_count = d3_wc
    state.upsert(record)
    state.save(STATE_PATH)

    print(f"\n  ch{n:02}: {title}")
    print(f"    D3 source: {d3_path} ({d3_wc} words)")

    # Build shared context for all agents in this chapter
    base_context = (
        f"# Book Title: {cfg['book']['title']}\n\n"
        f"# Foundation Material\n{foundation}\n\n"
        f"# Model Bible\n{model_bible}\n\n"
        f"# Character Bible\n{character_bible}\n\n"
        f"# EDITORIAL_DIRECTIVES_D4\n{directives_d4}\n\n"
        f"# DRAFT3_DIRECTIVES\n{directives_d3}\n\n"
        f"# Preceding Draft 4 Chapter\n{prev_d4 or '(First chapter — no preceding D4.)'}\n\n"
        f"# Draft 3 Chapter to Rewrite\n{d3_content}\n"
    )

    revision = 0
    current_chapter = ""
    block_reason = ""
    blocking_agent = ""

    while revision <= max_revisions:
        # --- Stage 1: Rewrite Agent ---
        print(f"    [{revision}/{max_revisions}] Rewrite Agent...", end=" ", flush=True)
        rewrite_task = (
            f"Rewrite Chapter {n}: '{title}' from Draft 3 to Draft 4. "
            f"Apply all editorial directives. Replace characters not in Character Bible. "
            f"Remove production artifacts. Use exact Model Bible terminology. "
            f"Cut repetitive prose and add new substantive content (mechanism explanations, "
            f"failure modes, hard cases, counterexamples). "
            f"Append a rewrite log at the end with: changes per directive, "
            f"word count before/after, characters used, unresolved issues."
        )

        if revision > 0 and block_reason:
            rewrite_task += (
                f"\n\nPREVIOUS REVISION BLOCKED by {blocking_agent}:\n{block_reason}\n"
                f"Resolve these issues while preserving what passed."
            )

        rewrite_prompt = agent_prompt(cfg, "rewrite_agent")
        current_chapter = call_agent(
            client, ledger, "rewrite_agent", rewrite_prompt,
            rewrite_task, base_context,
            f"output/draft4/{prefix}_raw.md", temperature=0.15,
        )
        print("done")

        # --- Stage 2: Evidence Agent ---
        print(f"    [{revision}/{max_revisions}] Evidence Agent...", end=" ", flush=True)
        evidence_prompt = agent_prompt(cfg, "evidence_agent")
        evidence_task = (
            f"Scan Chapter {n}: '{title}' for unsourced psychological, neurological, "
            f"behavioural, and health-related claims. For each: insert a source reference, "
            f"add a qualifying phrase, or flag with [NOTE TO AUTHOR: SOURCE_NEEDED — ...]. "
            f"Do NOT invent citations or fabricate study names. "
            f"Produce the evidenced chapter followed by an evidence log."
        )
        evidence_context = (
            f"# Chapter to Process\n{current_chapter}\n\n"
            f"# Model Bible\n{model_bible}\n"
        )
        current_chapter = call_agent(
            client, ledger, "evidence_agent", evidence_prompt,
            evidence_task, evidence_context,
            f"output/draft4/{prefix}_evidenced.md", temperature=0.1,
        )
        print("done")

        # --- Stage 3: Artifact Scrubber ---
        if run_scrubber:
            print(f"    [{revision}/{max_revisions}] Artifact Scrubber...", end=" ", flush=True)
            scrubber_prompt = agent_prompt(cfg, "artifact_scrubber")
            scrubber_task = (
                f"Scan Chapter {n}: '{title}' for production artifacts. "
                f"Remove: EDITOR FLAG, outline headers (## <phrase> purpose:), "
                f"chapter misnumbering, internal YAML/code blocks with workflow keys. "
                f"For [Author's note] in Introduction (Ch0): preserve and route to Author_Gate. "
                f"Produce the clean chapter followed by an artifact removal log."
            )
            scrubber_context = f"# Chapter to Process\n{current_chapter}\n"
            current_chapter = call_agent(
                client, ledger, "artifact_scrubber", scrubber_prompt,
                scrubber_task, scrubber_context,
                f"output/draft4/{prefix}_scrubbed.md", temperature=0.1,
            )
            print("done")

        # --- Stage 4: Continuity Auditor ---
        audit_blocked = False
        if run_auditor:
            print(f"    [{revision}/{max_revisions}] Continuity Auditor...", end=" ", flush=True)
            auditor_prompt = agent_prompt(cfg, "continuity_auditor")
            auditor_task = (
                f"Verify Chapter {n}: '{title}' for continuity against bibles. "
                f"Check: character existence, layer/currency name matching (case-sensitive), "
                f"character-detail consistency, reveal-order compliance. "
                f"Return PASS or BLOCK with a violation list."
            )
            auditor_context = (
                f"# Chapter Under Review\n{current_chapter}\n\n"
                f"# Model Bible\n{model_bible}\n\n"
                f"# Character Bible\n{character_bible}\n"
            )
            audit_result = call_agent(
                client, ledger, "continuity_auditor", auditor_prompt,
                auditor_task, auditor_context,
                f"output/reviews/{prefix}_continuity_d4.md", temperature=0.1,
            )
            audit_blocked = _contains_block(audit_result)
            if audit_blocked:
                block_reason = _extract_block_reason(audit_result)
                blocking_agent = "continuity_auditor"
                print("BLOCK")
            else:
                print("PASS")

        # --- Stage 5: Editorial Gate ---
        gate_blocked = False
        if run_gate and not audit_blocked:
            print(f"    [{revision}/{max_revisions}] Editorial Gate...", end=" ", flush=True)
            gate_prompt = (
                "You are the Editorial Gate for the Charlotte Book Factory. "
                "Check the chapter against per-chapter requirements:\n"
                "(a) character cast compliance — only Character Bible characters\n"
                "(b) artifact-free status — no placeholders, TODOs, revision marks\n"
                "(c) word count within per-chapter target range from ED4 table\n"
                "(d) layer terminology matches Model Bible (case-sensitive)\n"
                "(e) exercise variety — no more than 2 consecutive same-format\n"
                "(f) factual claims have source references\n\n"
                "Return PASS if all checks pass. Return BLOCK listing each failing check "
                "with the location within the chapter."
            )
            gate_task = (
                f"Run Editorial Gate checks on Chapter {n}: '{title}'. "
                f"Draft 3 word count: {d3_wc}. Verify all 6 criteria."
            )
            gate_context = (
                f"# Chapter Under Review\n{current_chapter}\n\n"
                f"# Model Bible\n{model_bible}\n\n"
                f"# Character Bible\n{character_bible}\n\n"
                f"# EDITORIAL_DIRECTIVES_D4 (for word count targets)\n{directives_d4}\n"
            )
            gate_result = call_agent(
                client, ledger, "editorial_gate", gate_prompt,
                gate_task, gate_context,
                f"output/reviews/{prefix}_editorial_d4.md", temperature=0.1,
            )
            gate_blocked = _contains_block(gate_result)
            if gate_blocked:
                block_reason = _extract_block_reason(gate_result)
                blocking_agent = "editorial_gate"
                print("BLOCK")
            else:
                print("PASS")

        # --- Decision: pass or loop ---
        if not audit_blocked and not gate_blocked:
            # Chapter passed all gates
            d4_wc = word_count(current_chapter)
            write(f"output/draft4/{prefix}.md", current_chapter)

            record.status = "editorial_pass"
            record.revision_count = revision
            record.d4_word_count = d4_wc
            record.block_reason = ""
            record.blocking_agent = ""
            record.output_path = f"output/draft4/{prefix}.md"
            state.upsert(record)
            state.save(STATE_PATH)

            print(f"    ✓ PASS — {d4_wc} words (D3: {d3_wc})")
            ledger.append("rewrite_chapter_pass", {
                "chapter": n, "title": title, "revisions": revision,
                "d3_words": d3_wc, "d4_words": d4_wc,
            })
            return current_chapter

        # BLOCK path — check revision budget
        revision += 1
        if revision > max_revisions:
            # Exhausted revisions
            record.status = "blocked"
            record.revision_count = max_revisions
            record.block_reason = block_reason[:500]
            record.blocking_agent = blocking_agent
            state.upsert(record)
            state.save(STATE_PATH)

            print(f"    ✗ BLOCKED after {max_revisions} revisions by {blocking_agent}")
            ledger.append("rewrite_chapter_blocked", {
                "chapter": n, "title": title, "revisions": max_revisions,
                "blocking_agent": blocking_agent, "reason": block_reason[:500],
            })
            return ""

        # Update state for next revision
        record.status = "rewriting"
        record.revision_count = revision
        state.upsert(record)
        state.save(STATE_PATH)
        print(f"    ↻ Revising (attempt {revision}/{max_revisions})...")

    return ""


def _contains_block(text: str) -> bool:
    """Check if review text contains a BLOCK verdict."""
    return bool(re.search(r"\bBLOCK\b", text, flags=re.IGNORECASE))


def _extract_block_reason(text: str) -> str:
    """Extract the reason from a BLOCK verdict (text after BLOCK marker)."""
    match = re.search(r"\bBLOCK\b[:\s]*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        reason = match.group(1).strip()
        return reason[:500]
    return text[:500]


# --------------------------------------------------------------------------
# Task 8.4: Assembly and Book-Level Gate
# --------------------------------------------------------------------------
def assemble_draft4(cfg: dict, state: RewriteState) -> str:
    """Stitch all passing chapters into output/full_fourth_draft.md.

    Only includes chapters with status 'editorial_pass'.
    Returns the assembled manuscript content.
    """
    parts: List[str] = [f"# {cfg['book']['title']} — Draft 4\n"]
    assembled_count = 0

    for record in sorted(state.chapters, key=lambda c: c.number):
        if record.status == "editorial_pass" and record.output_path:
            content = read(record.output_path)
            if content.strip():
                parts.append(content)
                assembled_count += 1

    manuscript = "\n\n---\n\n".join(parts)
    output_path = cfg["book"].get("output_file_d4", "output/full_fourth_draft.md")
    write(output_path, manuscript)

    wc = word_count(manuscript)
    print(f"\n  Assembly: {assembled_count} chapters → {output_path} ({wc} words)")
    return manuscript


def generate_author_action_log(manuscript_path: str, output_path: str) -> None:
    """Scan manuscript for [NOTE TO AUTHOR] markers, produce consolidated table.

    Reads the manuscript, finds all [NOTE TO AUTHOR: CATEGORY — explanation] markers,
    and produces a consolidated Markdown table at output_path.
    """
    manuscript = read(manuscript_path)
    if not manuscript.strip():
        write(output_path, "# Author Action Log — Draft 4\n\nNo manuscript content found.\n")
        return

    # Find all [NOTE TO AUTHOR: ...] markers
    pattern = re.compile(
        r"\[NOTE TO AUTHOR:\s*([A-Z_]+)\s*[—–-]\s*(.+?)\]",
        re.IGNORECASE,
    )

    entries: List[Dict[str, str]] = []
    current_chapter = "Unknown"
    current_section = ""

    for line_num, line in enumerate(manuscript.splitlines(), 1):
        # Track current chapter from headings
        ch_match = re.match(r"^#\s+(?:Chapter\s+)?(\d+|[A-Z])", line, re.IGNORECASE)
        if ch_match:
            current_chapter = f"Ch{ch_match.group(1).zfill(2)}"
        # Track section headings
        sec_match = re.match(r"^##\s+(.+)$", line)
        if sec_match:
            current_section = sec_match.group(1).strip()

        for match in pattern.finditer(line):
            category = match.group(1).upper()
            explanation = match.group(2).strip()
            entries.append({
                "chapter": current_chapter,
                "location": current_section or f"Line {line_num}",
                "category": category,
                "explanation": explanation,
            })

    # Build output
    lines = [
        "# Author Action Log — Draft 4",
        "",
        "All points in the manuscript requiring human author input. "
        "Search for `[NOTE TO AUTHOR` to locate each in context.",
        "",
    ]

    if entries:
        lines.append("| # | Chapter | Location | Category | Explanation |")
        lines.append("|---|---------|----------|----------|-------------|")
        for idx, entry in enumerate(entries, 1):
            lines.append(
                f"| {idx} | {entry['chapter']} | {entry['location']} | "
                f"{entry['category']} | {entry['explanation']} |"
            )

        # Summary by category
        category_counts: Dict[str, int] = {}
        for entry in entries:
            cat = entry["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        lines.append("")
        lines.append(f"**Total markers:** {len(entries)}")
        summary_parts = [f"{cat}: {count}" for cat, count in sorted(category_counts.items())]
        lines.append(f"**By category:** {', '.join(summary_parts)}")
    else:
        lines.append("No `[NOTE TO AUTHOR]` markers found in the manuscript.")

    write(output_path, "\n".join(lines) + "\n")
    print(f"    ✓ Author Action Log: {len(entries)} markers → {output_path}")


def run_book_level_editorial_gate(
    cfg: dict, client: ModelClient, ledger: Ledger, manuscript: str
) -> str:
    """Book-level: total 33k-37k, character frequency, no residual placeholders.

    Runs after assembly to verify the entire manuscript meets book-level criteria.
    Returns the gate result (PASS or BLOCK with details).
    """
    model_bible = read("foundation/model_bible.md")
    character_bible = read("foundation/character_bible.md")
    directives_d4 = read("foundation/EDITORIAL_DIRECTIVES_D4.md")

    wc = word_count(manuscript)
    print(f"\n  Book-level Editorial Gate (manuscript: {wc} words)...")

    system_prompt = (
        "You are the Book-Level Editorial Gate for the Charlotte Book Factory. "
        "You verify the entire assembled Draft 4 manuscript meets these criteria:\n\n"
        "1. Total word count within 33,000–37,000 words\n"
        "2. Character frequency distribution matches Character Bible specifications\n"
        "   (no character > 40% of appearances)\n"
        "3. No residual placeholders, TODO markers, EDITOR FLAGs, or production artifacts\n"
        "   (Exception: [NOTE TO AUTHOR] markers are allowed — they are deliberate)\n\n"
        "Return PASS if all checks pass.\n"
        "Return BLOCK with specific details for each failing check.\n"
    )

    task = (
        f"Run book-level Editorial Gate checks on the assembled Draft 4 manuscript. "
        f"Current total word count: {wc}."
    )

    # Pass truncated manuscript for very long texts
    manuscript_excerpt = manuscript[:80000] if len(manuscript) > 80000 else manuscript
    context = (
        f"# Assembled Manuscript (total word count: {wc})\n\n{manuscript_excerpt}\n\n"
        f"# Character Bible\n{character_bible}\n\n"
        f"# Model Bible\n{model_bible}\n"
    )

    result = call_agent(
        client, ledger, "editorial_gate_book_level", system_prompt,
        task, context, "output/reviews/book_level_editorial_gate_d4.md",
        temperature=0.1,
    )

    if _contains_block(result):
        print(f"    ✗ Book-level gate: BLOCK")
    else:
        print(f"    ✓ Book-level gate: PASS")

    return result


# --------------------------------------------------------------------------
# Status file generation
# --------------------------------------------------------------------------
def write_status(cfg: dict, state: RewriteState) -> None:
    """Write output/status_d4.md with chapter counts per status and blocked details."""
    counts = state.summary_status()
    total = len(state.chapters)

    lines = [
        "# Charlotte Draft 4 — Status",
        "",
        "## Summary",
        f"- Total chapters: {total}",
    ]
    for status_name in [
        "editorial_pass", "rewriting", "rewritten", "pending", "blocked", "waiting_human_input"
    ]:
        if status_name in counts:
            lines.append(f"- {status_name}: {counts[status_name]}")

    # Blocked chapters
    blocked = [c for c in state.chapters if c.status == "blocked"]
    if blocked:
        lines.append("")
        lines.append("## Blocked Chapters")
        for ch in blocked:
            lines.append(
                f"- Ch{ch.number:02}: {ch.title} — BLOCKED by {ch.blocking_agent} "
                f"({ch.block_reason[:100]})"
            )

    # Waiting human input
    waiting = [c for c in state.chapters if c.status == "waiting_human_input"]
    if waiting:
        lines.append("")
        lines.append("## Waiting Human Input")
        for ch in waiting:
            lines.append(
                f"- Ch{ch.number:02}: {ch.title} — WAITING ({ch.block_reason[:100]})"
            )

    write("output/status_d4.md", "\n".join(lines) + "\n")


# --------------------------------------------------------------------------
# Task 8.3: Main Entry Point
# --------------------------------------------------------------------------
def main() -> None:
    """Entry point. Parse CLI args, load config, run pipeline."""
    parser = argparse.ArgumentParser(
        description="Charlotte editorial rewrite pipeline (Draft 3 → Draft 4)"
    )
    parser.add_argument(
        "--chapter", type=int, default=None,
        help="Process only chapter N"
    )
    parser.add_argument(
        "--bibles-only", action="store_true",
        help="Generate Model Bible and Character Bible, then stop"
    )
    parser.add_argument(
        "--assemble-only", action="store_true",
        help="Assemble existing draft4 chapters into full manuscript"
    )
    parser.add_argument(
        "--no-resume", action="store_true",
        help="Ignore state file, reprocess all chapters"
    )
    args = parser.parse_args()

    # Load configuration
    cfg = load_config()
    ensure_dirs()

    # Validate editorial_rewrite config section
    try:
        er_cfg = load_rewrite_config(str(ROOT / "config.yaml"))
    except PipelineError as e:
        raise SystemExit(f"Configuration error: {e}")

    # Merge into main config for convenience
    cfg["editorial_rewrite"] = er_cfg

    # Initialize infrastructure
    ledger = Ledger(ROOT, path="output/ledger_d4.jsonl")
    client = client_from_config(cfg)
    state = RewriteState.load(STATE_PATH)
    resume = er_cfg.get("resume", False) and not args.no_resume

    print(f"\n{'=' * 60}")
    print(f"  CHARLOTTE EDITORIAL REWRITE PIPELINE")
    print(f"  Draft 3 → Draft 4")
    print(f"  Resume: {'on' if resume else 'off'}")
    if args.chapter is not None:
        print(f"  Mode: single chapter ({args.chapter})")
    elif args.bibles_only:
        print(f"  Mode: bibles-only")
    elif args.assemble_only:
        print(f"  Mode: assemble-only")
    else:
        print(f"  Mode: full pipeline")
    print(f"{'=' * 60}")

    ledger.append("rewrite_pipeline_start", {
        "book": cfg["book"]["title"],
        "resume": resume,
        "chapter": args.chapter,
        "mode": "bibles_only" if args.bibles_only else (
            "assemble_only" if args.assemble_only else (
                f"chapter_{args.chapter}" if args.chapter is not None else "full"
            )
        ),
    })

    # --- Assemble-only mode ---
    if args.assemble_only:
        manuscript = assemble_draft4(cfg, state)
        generate_author_action_log(
            cfg["book"].get("output_file_d4", "output/full_fourth_draft.md"),
            "output/author_actions.md",
        )
        run_book_level_editorial_gate(cfg, client, ledger, manuscript)
        write_status(cfg, state)
        print(f"\n  Done. Assembled manuscript at {cfg['book'].get('output_file_d4')}")
        return

    # --- Validate prerequisites ---
    try:
        validate_prerequisites(cfg, str(ROOT))
    except PipelineError as e:
        raise SystemExit(f"Prerequisite validation failed: {e}")

    # --- Bible generation ---
    # Only regenerate if files don't exist or --no-resume
    model_bible_path = ROOT / "foundation" / "model_bible.md"
    char_bible_path = ROOT / "foundation" / "character_bible.md"

    if not model_bible_path.exists() or args.no_resume:
        model_bible = generate_model_bible(cfg, client, ledger)
    else:
        model_bible = read("foundation/model_bible.md")
        print("  Model Bible: using existing file")

    if not char_bible_path.exists() or args.no_resume:
        character_bible = generate_character_bible(cfg, client, ledger)
    else:
        character_bible = read("foundation/character_bible.md")
        print("  Character Bible: using existing file")

    if args.bibles_only:
        print(f"\n  Done. Bibles generated (--bibles-only mode).")
        return

    # --- Load all reference documents ---
    foundation = read(cfg["book"]["foundation_file"])
    directives_d4 = read("foundation/EDITORIAL_DIRECTIVES_D4.md")
    directives_d3 = read("foundation/DRAFT3_DIRECTIVES.md")

    # --- Discover chapters ---
    chapters = discover_draft3_chapters(cfg)
    if not chapters:
        raise SystemExit("No Draft 3 chapters found. Run first-draft pipeline first.")

    # Seed state with all chapters
    for ch in chapters:
        n = int(ch["number"])
        if not state.get(n):
            record = RewriteChapterRecord(number=n, title=str(ch["title"]))
            state.upsert(record)
    state.save(STATE_PATH)

    # Filter to requested chapter if specified
    if args.chapter is not None:
        chapters = [c for c in chapters if int(c["number"]) == args.chapter]
        if not chapters:
            raise SystemExit(f"Chapter {args.chapter} not found in Draft 3.")

    print(f"\n  Chapters to process: {len(chapters)}")

    # --- Chapter rewrite loop ---
    prev_d4 = ""
    for idx, chapter in enumerate(chapters):
        n = int(chapter["number"])
        title = str(chapter["title"])

        # Resume: skip editorial_pass chapters
        if resume and state.is_editorial_pass(n):
            # Load existing D4 for continuity with next chapter
            existing = state.get(n)
            if existing and existing.output_path:
                prev_d4 = read(existing.output_path)
            print(f"\n  ch{n:02}: {title} — skipped (editorial_pass, resume on)")
            ledger.append("rewrite_chapter_skipped", {"chapter": n, "reason": "resume"})
            continue

        # Author Gate: only blocks Introduction (ch00)
        blocked, reason = check_author_gate(n, str(ROOT / "foundation"))
        if blocked:
            record = state.get(n) or RewriteChapterRecord(number=n, title=title)
            record.status = "waiting_human_input"
            record.block_reason = reason
            record.blocking_agent = "author_gate"
            state.upsert(record)
            state.save(STATE_PATH)
            print(f"\n  ch{n:02}: {title} — WAITING_HUMAN (Author Gate)")
            print(f"    Reason: {reason[:100]}")
            ledger.append("rewrite_chapter_author_gate", {
                "chapter": n, "title": title, "reason": reason[:200],
            })
            continue

        # Run the full chapter pipeline
        result = run_rewrite_chapter(
            cfg, client, ledger, chapter, state,
            model_bible, character_bible,
            directives_d4, directives_d3, foundation, prev_d4,
        )

        # Update prev_d4 for next chapter's continuity context
        if result:
            prev_d4 = result

        # Inter-chapter pause (not after last)
        if idx < len(chapters) - 1:
            time.sleep(INTER_CHAPTER_PAUSE)

    # --- Assembly (only in full pipeline mode) ---
    if args.chapter is None:
        manuscript = assemble_draft4(cfg, state)
        generate_author_action_log(
            cfg["book"].get("output_file_d4", "output/full_fourth_draft.md"),
            "output/author_actions.md",
        )
        run_book_level_editorial_gate(cfg, client, ledger, manuscript)

    # --- Write status ---
    write_status(cfg, state)
    state.save(STATE_PATH)

    ledger.append("rewrite_pipeline_complete", {
        "summary": state.summary_status(),
    })

    print(f"\n{'=' * 60}")
    print(f"  EDITORIAL REWRITE PIPELINE COMPLETE")
    print(f"  Status: {state.summary_status()}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
