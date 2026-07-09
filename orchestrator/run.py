"""Charlotte first-draft orchestrator.

Neutral execution engine for the Charlotte Book Factory.

It loads agent definitions from the repository, calls the configured model provider,
writes handoff artefacts, records the ledger, tracks cross-chapter continuity in a
persisted book state, runs a bounded revision loop on blocking reviews, and assembles
the first draft with a book-level pacing and manuscript review.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.ledger import Ledger
from orchestrator.book_state import BookState, ChapterRecord
from providers.model_client import ModelClient, client_from_config

BOOK_STATE_PATH = ROOT / "output/book_state.json"


# --------------------------------------------------------------------------
# IO helpers
# --------------------------------------------------------------------------
def read(path: str) -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write(path: str, content: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def load_config() -> dict:
    return yaml.safe_load(read("config.yaml"))


def ensure_dirs() -> None:
    for path in [
        "output",
        "output/chapter_plans",
        "output/drafts",
        "output/reviews",
        "output/final_chapters",
        "output/handoffs",
    ]:
        (ROOT / path).mkdir(parents=True, exist_ok=True)


def agent(cfg: dict, name: str) -> str:
    path = cfg["agents"][name]
    content = read(path)
    if not content.strip():
        raise FileNotFoundError(f"Missing agent file for {name}: {path}")
    return content


def is_placeholder_foundation(foundation: str) -> bool:
    lowered = foundation.lower()
    return "replace this placeholder" in lowered or "foundation file used by charlotte" in lowered


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


# --------------------------------------------------------------------------
# Model call
# --------------------------------------------------------------------------
def call_agent(
    client: ModelClient,
    ledger: Ledger,
    agent_name: str,
    agent_prompt: str,
    task: str,
    context: str,
    output_path: str,
    temperature: float = 0.4,
) -> str:
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
    response = client.complete(messages, temperature=temperature)
    write(output_path, response.content)
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


# --------------------------------------------------------------------------
# Parsing helpers
# --------------------------------------------------------------------------
def extract_chapters(outline: str) -> List[Dict[str, object]]:
    chapters: List[Dict[str, object]] = []
    seen = set()
    for line in outline.splitlines():
        match = re.match(r"^\s*(?:#+\s*)?(?:Chapter\s*)?(\d+)[\).:-]\s+(.+)$", line.strip(), flags=re.I)
        if match:
            number = int(match.group(1))
            if number in seen:
                continue
            seen.add(number)
            title = match.group(2).strip().strip("*_# ")
            chapters.append({"number": number, "title": title})

    if not chapters:
        fallback_titles = [
            "You Are a System",
            "Cause and Effect in You",
            "The Body Speaks First",
            "The Currencies You Spend",
            "The Operating System Underneath",
            "Identity and the Roles You Carry",
            "Habits as Repeated Routes",
            "Burnout as System Debt",
            "Changing Without Fighting Yourself",
            "Tools That Help, and Where They Stop",
            "Relationships as Shared Systems",
            "Faith, Meaning, and the Longer Road",
            "Watching the System Change",
            "The Manual You Keep Writing",
        ]
        chapters = [{"number": idx, "title": title} for idx, title in enumerate(fallback_titles, start=1)]
    return chapters


def contains_block(review_text: str) -> bool:
    return bool(re.search(r"\bBLOCK\b", review_text, flags=re.I))


def summarise(text: str, limit: int = 900) -> str:
    """Cheap extractive summary: strip the revision log, keep the head."""
    body = re.split(r"```yaml\s*\nrevision_log", text, maxsplit=1)[0]
    body = body.strip()
    return body[:limit]


# --------------------------------------------------------------------------
# Context builders
# --------------------------------------------------------------------------
def build_base_context(cfg: dict, foundation: str) -> str:
    return (
        f"# Book Title\n{cfg['book']['title']}\n\n"
        f"# Foundation Material\n{foundation}\n\n"
        f"# Handoff Contract\n{read('contracts/handoff-contract.md')}\n\n"
        f"# Workflow\n{read('workflows/first-draft-workflow.md')}\n\n"
        f"# Acceptance Gate\n{read('quality/CHAPTER_ACCEPTANCE_GATE.md')}\n"
    )


# --------------------------------------------------------------------------
# Stages
# --------------------------------------------------------------------------
def run_outline(cfg: dict, client: ModelClient, ledger: Ledger, foundation: str) -> str:
    return call_agent(
        client, ledger, "outliner", agent(cfg, "outliner"),
        "Create the complete book outline and chapter architecture from the foundation material. Number every chapter clearly (e.g. 'Chapter 1: Title').",
        build_base_context(cfg, foundation),
        "output/book_outline.md",
        temperature=0.1,
    )


def run_research(cfg: dict, client: ModelClient, ledger: Ledger, foundation: str, outline: str) -> str:
    return call_agent(
        client, ledger, "researcher", agent(cfg, "researcher"),
        "Create a practical research/concept pack for every planned chapter. Do not write chapter prose.",
        build_base_context(cfg, foundation) + f"\n\n# Book Outline\n{outline}",
        "output/research_pack.md",
        temperature=0.1,
    )


def review_chapter(
    cfg: dict, client: ModelClient, ledger: Ledger,
    n: int, title: str, prefix: str, review_context: str, pass_label: str,
) -> Tuple[str, bool]:
    """Run all enabled review stages. Returns (combined_review, blocked)."""
    wf = cfg.get("workflow", {})
    parts: List[str] = []

    def add(flag: str, name: str, agent_key: str, task: str, suffix: str) -> None:
        if wf.get(flag, True):
            parts.append(call_agent(
                client, ledger, name, agent(cfg, agent_key), task, review_context,
                f"output/reviews/{prefix}_{suffix}{pass_label}.md", temperature=0.1,
            ))

    add("run_general_reviewer", "reviewer", "reviewer",
        f"Review Chapter {n}: {title}. Return PASS or BLOCK, a score, blocking issues, and recommended changes.", "general")
    add("run_thesis_guardian", "thesis_guardian", "thesis_guardian",
        f"Guard the thesis for Chapter {n}: {title}. Confirm it advances the book's central argument.", "thesis")
    add("run_example_curator", "example_curator", "example_curator",
        f"Curate examples/practices for Chapter {n}: {title}. Flag missing anchors and repeats from earlier chapters.", "examples")

    if wf.get("run_personas", True):
        for persona_path in cfg.get("personas", []):
            persona_name = Path(persona_path).stem
            review = call_agent(
                client, ledger, f"persona_{persona_name}", read(persona_path),
                f"Review Chapter {n}: {title} from your persona. Return PASS or BLOCK with blocking issues only.",
                review_context, f"output/reviews/{prefix}_{persona_name}{pass_label}.md", temperature=0.1,
            )
            parts.append(f"# Persona: {persona_name}\n\n{review}")

    add("run_continuity_warden", "warden_continuity", "warden_continuity",
        f"Review continuity for Chapter {n}: {title}.", "continuity")
    add("run_safety_warden", "warden_safety", "warden_safety",
        f"Review safety for Chapter {n}: {title}.", "safety")
    add("run_voice_warden", "warden_voice", "warden_voice",
        f"Review voice for Chapter {n}: {title}.", "voice")

    combined = "\n\n---\n\n".join(parts)
    write(f"output/reviews/{prefix}_combined{pass_label}.md", combined)
    return combined, contains_block(combined)


def run_chapter(
    cfg: dict, client: ModelClient, ledger: Ledger,
    foundation: str, outline: str, research_pack: str,
    chapter: Dict[str, object], state: BookState,
) -> str:
    wf = cfg.get("workflow", {})
    n = int(chapter["number"])
    title = str(chapter["title"])
    prefix = f"ch{n:02}"
    window = int(wf.get("context_window_chapters", 3))
    max_revisions = int(wf.get("max_revisions", 3))
    word_target = int(wf.get("chapter_word_target", 3500))
    tolerance = float(wf.get("word_count_tolerance", 0.4))

    base_context = (
        build_base_context(cfg, foundation)
        + f"\n\n# Book Outline\n{outline}"
        + f"\n\n# Research Pack\n{research_pack}"
        + f"\n\n# Chapter Assignment\nChapter {n}: {title}"
        + f"\n\n# Previous Chapter Summary\n{state.previous_summary(n)}"
        + f"\n\n{state.windowed_context(n, window)}"
    )

    # 1. Architect the chapter (dedicated planner, not the outliner)
    chapter_plan = call_agent(
        client, ledger, "chapter_architect", agent(cfg, "chapter_architect"),
        f"Plan Chapter {n}: {title}. Produce the structural chapter plan: one idea, section flow, opening/closing beats, required practices/examples, terms introduced, and do-not-reveal-yet notes. Target ~{word_target} words.",
        base_context, f"output/chapter_plans/{prefix}.md", temperature=0.1,
    )

    # 2. First draft
    draft = call_agent(
        client, ledger, "drafter", agent(cfg, "drafter"),
        f"Write a complete first draft of Chapter {n}: {title} using the chapter plan and research pack. Aim for ~{word_target} words.",
        base_context + f"\n\n# Chapter Plan\n{chapter_plan}",
        f"output/drafts/{prefix}.md", temperature=0.1,
    )

    # 3. Revision loop: review -> if BLOCK, revise -> re-review, up to max_revisions
    current = draft
    revisions = 0
    blocked = True
    combined_review = ""
    while revisions <= max_revisions:
        pass_label = "" if revisions == 0 else f"_r{revisions}"
        review_context = base_context + f"\n\n# Chapter Plan\n{chapter_plan}\n\n# Chapter Under Review\n{current}"
        combined_review, blocked = review_chapter(cfg, client, ledger, n, title, prefix, review_context, pass_label)
        ledger.append("chapter_review", {"chapter": n, "title": title, "pass": revisions, "blocked": blocked})

        if not blocked:
            break
        if revisions >= max_revisions:
            ledger.append("chapter_revision_exhausted", {"chapter": n, "title": title, "revisions": revisions})
            break

        revisions += 1
        current = call_agent(
            client, ledger, "revision_agent", agent(cfg, "revision_agent"),
            f"Revise Chapter {n}: {title}. Resolve every blocking issue in the combined review. Keep what passed.",
            review_context + f"\n\n# Combined Review Notes\n{combined_review}",
            f"output/drafts/{prefix}_r{revisions}.md", temperature=0.2,
        )

    # 4. Editor polish
    edit_context = (
        base_context
        + f"\n\n# Chapter Plan\n{chapter_plan}"
        + f"\n\n# Chapter To Edit\n{current}"
        + f"\n\n# Combined Review Notes\n{combined_review}"
    )
    final = call_agent(
        client, ledger, "editor", agent(cfg, "editor"),
        f"Edit Chapter {n}: {title}. Apply outstanding review notes, smooth flow, and produce the final chapter. Do not add new concepts or remove safety caveats.",
        edit_context, f"output/final_chapters/{prefix}.md", temperature=0.1,
    )

    # 5. Transition polish (openings/closings)
    if wf.get("run_transition_agent", True):
        next_ch = state.get(n + 1)
        next_hint = f"Chapter {n + 1}: {next_ch.title}" if next_ch else "Next chapter (see outline)."
        transition = call_agent(
            client, ledger, "transition_agent", agent(cfg, "transition_agent"),
            f"Check the opening and closing of Chapter {n}: {title}. If ADJUST, provide replacement opening/closing paragraphs only.",
            base_context + f"\n\n# Final Chapter\n{final}\n\n# Next Chapter\n{next_hint}",
            f"output/reviews/{prefix}_transition.md", temperature=0.2,
        )
        ledger.append("chapter_transition", {"chapter": n, "adjust": "ADJUST" in transition.upper()})

    # 6. Validate word count
    wc = word_count(final)
    lo = int(word_target * (1 - tolerance))
    hi = int(word_target * (1 + tolerance))
    within = lo <= wc <= hi
    if not within:
        ledger.append("chapter_word_count_flag", {"chapter": n, "words": wc, "target": word_target, "range": [lo, hi]})

    # 7. Record state and persist (checkpoint)
    record = state.get(n) or ChapterRecord(number=n, title=title)
    record.title = title
    record.summary = summarise(final)
    record.word_count = wc
    record.revisions = revisions
    record.blocked = blocked
    record.final_path = f"output/final_chapters/{prefix}.md"
    if blocked:
        record.open_flags.append(f"exhausted {max_revisions} revisions still BLOCK")
    state.upsert_chapter(record)
    state.save(BOOK_STATE_PATH)

    ledger.append("chapter_complete", {
        "chapter": n, "title": title, "revisions": revisions,
        "blocked": blocked, "words": wc, "within_target": within,
        "output_path": record.final_path,
    })
    return final


def assemble(cfg: dict, chapters: List[Dict[str, object]]) -> str:
    parts = [f"# {cfg['book']['title']}\n"]
    for chapter in chapters:
        n = int(chapter["number"])
        parts.append(read(f"output/final_chapters/ch{n:02}.md"))
    manuscript = "\n\n---\n\n".join(parts)
    write(cfg["book"].get("output_file", "output/full_first_draft.md"), manuscript)
    return manuscript


def run_book_level_reviews(cfg: dict, client: ModelClient, ledger: Ledger, foundation: str, outline: str, manuscript: str, state: BookState) -> None:
    wf = cfg.get("workflow", {})
    book_context = (
        f"# Book Title\n{cfg['book']['title']}\n\n"
        f"# Book Outline\n{outline}\n\n"
        f"# Foundation Material\n{foundation}\n\n"
        f"{state.as_context()}\n"
    )
    if wf.get("run_pacing_agent", True):
        call_agent(
            client, ledger, "pacing_agent", agent(cfg, "pacing_agent"),
            "Review the pacing of the whole book across its full arc. Return PASS or ADJUST with specific issues.",
            book_context, "output/reviews/pacing_review.md", temperature=0.1,
        )
    if wf.get("run_manuscript_reviewer", True):
        call_agent(
            client, ledger, "manuscript_reviewer", agent(cfg, "manuscript_reviewer"),
            "Review the assembled first draft as a whole book. Return PASS or BLOCK with book-level issues.",
            book_context + f"\n\n# Assembled Draft\n{manuscript[:60000]}",
            "output/reviews/manuscript_review.md", temperature=0.1,
        )


def write_status(cfg: dict, chapters: List[Dict[str, object]], state: BookState) -> None:
    lines = ["# Charlotte Status", "", f"Book: {cfg['book']['title']}", "", "## Chapters"]
    for chapter in chapters:
        n = int(chapter["number"])
        rec = state.get(n)
        path = ROOT / f"output/final_chapters/ch{n:02}.md"
        if rec and rec.blocked:
            marker = "BLOCKED"
        elif path.exists():
            marker = "DONE"
        else:
            marker = "PENDING"
        extra = f" ({rec.word_count} words, {rec.revisions} revisions)" if rec and path.exists() else ""
        lines.append(f"- Chapter {n}: {chapter['title']} — {marker}{extra}")
    write("output/status.md", "\n".join(lines) + "\n")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outline-only", action="store_true", help="Generate only output/book_outline.md")
    parser.add_argument("--chapter", type=int, help="Generate only one chapter by number")
    parser.add_argument("--assemble-only", action="store_true", help="Assemble existing final_chapters into full draft")
    parser.add_argument("--no-resume", action="store_true", help="Ignore existing final chapters and regenerate")
    args = parser.parse_args()

    cfg = load_config()
    ensure_dirs()
    ledger = Ledger(ROOT)
    client = client_from_config(cfg)
    state = BookState.load(BOOK_STATE_PATH)
    resume = cfg.get("workflow", {}).get("resume", True) and not args.no_resume

    foundation_path = cfg["book"]["foundation_file"]
    foundation = read(foundation_path)
    if not foundation.strip():
        raise SystemExit(f"Missing foundation material: {foundation_path}")
    if is_placeholder_foundation(foundation):
        raise SystemExit(f"Foundation material appears to be placeholder text. Replace {foundation_path} before running Charlotte.")

    if args.assemble_only:
        outline = read("output/book_outline.md")
        chapters = extract_chapters(outline)
        for ch in chapters:
            n = int(ch["number"])
            if not state.get(n):
                state.upsert_chapter(ChapterRecord(number=n, title=str(ch["title"]), final_path=f"output/final_chapters/ch{n:02}.md"))
        manuscript = assemble(cfg, chapters)
        run_book_level_reviews(cfg, client, ledger, foundation, outline, manuscript, state)
        write_status(cfg, chapters, state)
        state.save(BOOK_STATE_PATH)
        print(f"Assembled {cfg['book'].get('output_file', 'output/full_first_draft.md')}")
        return

    ledger.append("run_start", {"book": cfg["book"]["title"], "provider": cfg.get("provider", {}).get("type"), "resume": resume})
    outline = run_outline(cfg, client, ledger, foundation)
    chapters = extract_chapters(outline)

    # seed state with titles so transition agent knows the next chapter
    for ch in chapters:
        n = int(ch["number"])
        if not state.get(n):
            state.upsert_chapter(ChapterRecord(number=n, title=str(ch["title"])))
    state.save(BOOK_STATE_PATH)

    if args.outline_only:
        write_status(cfg, chapters, state)
        print("Wrote output/book_outline.md")
        return

    research_pack = run_research(cfg, client, ledger, foundation, outline)

    selected = [c for c in chapters if not args.chapter or int(c["number"]) == args.chapter]
    for chapter in selected:
        n = int(chapter["number"])
        if resume and state.is_complete(n) and (ROOT / f"output/final_chapters/ch{n:02}.md").exists():
            ledger.append("chapter_skipped_resume", {"chapter": n})
            print(f"Skipping chapter {n} (already complete, resume on)")
            continue
        run_chapter(cfg, client, ledger, foundation, outline, research_pack, chapter, state)

    if not args.chapter:
        manuscript = assemble(cfg, chapters)
        run_book_level_reviews(cfg, client, ledger, foundation, outline, manuscript, state)
        write_status(cfg, chapters, state)
        state.save(BOOK_STATE_PATH)
        ledger.append("run_complete", {"output_file": cfg['book'].get('output_file', 'output/full_first_draft.md')})
        print(f"Wrote {cfg['book'].get('output_file', 'output/full_first_draft.md')}")
    else:
        write_status(cfg, chapters, state)
        ledger.append("chapter_run_complete", {"chapter": args.chapter})
        print(f"Wrote chapter {args.chapter}")


if __name__ == "__main__":
    main()
