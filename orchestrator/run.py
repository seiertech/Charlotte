"""Charlotte first-draft orchestrator.

Neutral execution engine for the Charlotte Book Factory.

It loads agent definitions from the repository, calls the configured model provider,
writes handoff artefacts, records the ledger, and assembles the first draft.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.ledger import Ledger
from providers.model_client import ModelClient, client_from_config


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


def extract_chapters(outline: str) -> List[Dict[str, str]]:
    chapters: List[Dict[str, str]] = []
    for line in outline.splitlines():
        match = re.match(r"^\s*(?:#+\s*)?(?:Chapter\s*)?(\d+)[\).:-]\s+(.+)$", line.strip(), flags=re.I)
        if match:
            number = int(match.group(1))
            title = match.group(2).strip()
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


def build_base_context(cfg: dict, foundation: str) -> str:
    return (
        f"# Book Title\n{cfg['book']['title']}\n\n"
        f"# Foundation Material\n{foundation}\n\n"
        f"# Handoff Contract\n{read('contracts/handoff-contract.md')}\n\n"
        f"# Workflow\n{read('workflows/first-draft-workflow.md')}\n\n"
        f"# Acceptance Gate\n{read('quality/CHAPTER_ACCEPTANCE_GATE.md')}\n"
    )


def run_outline(cfg: dict, client: ModelClient, ledger: Ledger, foundation: str) -> str:
    return call_agent(
        client=client,
        ledger=ledger,
        agent_name="outliner",
        agent_prompt=agent(cfg, "outliner"),
        task="Create the complete book outline and chapter architecture from the foundation material. Number every chapter clearly.",
        context=build_base_context(cfg, foundation),
        output_path="output/book_outline.md",
        temperature=0.1,
    )


def run_research(cfg: dict, client: ModelClient, ledger: Ledger, foundation: str, outline: str) -> str:
    return call_agent(
        client=client,
        ledger=ledger,
        agent_name="researcher",
        agent_prompt=agent(cfg, "researcher"),
        task="Create a practical research/concept pack for every planned chapter. Do not write chapter prose.",
        context=build_base_context(cfg, foundation) + f"\n\n# Book Outline\n{outline}",
        output_path="output/research_pack.md",
        temperature=0.1,
    )


def run_chapter(
    cfg: dict,
    client: ModelClient,
    ledger: Ledger,
    foundation: str,
    outline: str,
    research_pack: str,
    chapter: Dict[str, str],
    previous_summary: str,
) -> str:
    n = int(chapter["number"])
    title = chapter["title"]
    prefix = f"ch{n:02}"
    base_context = (
        build_base_context(cfg, foundation)
        + f"\n\n# Book Outline\n{outline}"
        + f"\n\n# Research Pack\n{research_pack}"
        + f"\n\n# Chapter Assignment\nChapter {n}: {title}"
        + f"\n\n# Previous Chapter Summary\n{previous_summary or 'No previous chapter.'}"
    )

    chapter_plan = call_agent(
        client,
        ledger,
        "chapter_planner",
        agent(cfg, "outliner"),
        f"Plan Chapter {n}: {title}. Produce sections, flow, examples, practice/reflection, and do-not-include-yet notes.",
        base_context,
        f"output/chapter_plans/{prefix}.md",
        temperature=0.1,
    )

    draft = call_agent(
        client,
        ledger,
        "drafter",
        agent(cfg, "drafter"),
        f"Write a complete first draft of Chapter {n}: {title} using the chapter plan and research pack. Aim for the configured chapter word target.",
        base_context + f"\n\n# Chapter Plan\n{chapter_plan}",
        f"output/drafts/{prefix}.md",
        temperature=0.1,
    )

    review_context = base_context + f"\n\n# Chapter Plan\n{chapter_plan}\n\n# Draft Chapter\n{draft}"

    review_parts: List[str] = []
    if cfg.get("workflow", {}).get("run_general_reviewer", True):
        review_parts.append(
            call_agent(
                client,
                ledger,
                "reviewer",
                agent(cfg, "reviewer"),
                f"Review Chapter {n}: {title}. Return PASS or BLOCK, a score, blocking issues, and recommended changes.",
                review_context,
                f"output/reviews/{prefix}_general.md",
                temperature=0.1,
            )
        )

    if cfg.get("workflow", {}).get("run_personas", True):
        for persona_path in cfg.get("personas", []):
            persona_prompt = read(persona_path)
            persona_name = Path(persona_path).stem
            review = call_agent(
                client,
                ledger,
                f"persona_{persona_name}",
                persona_prompt,
                f"Review Chapter {n}: {title} from your persona. Return PASS or BLOCK with blocking issues only.",
                review_context,
                f"output/reviews/{prefix}_{persona_name}.md",
                temperature=0.1,
            )
            review_parts.append(f"# Persona: {persona_name}\n\n{review}")

    if cfg.get("workflow", {}).get("run_continuity_warden", True):
        review_parts.append(
            call_agent(
                client,
                ledger,
                "warden_continuity",
                agent(cfg, "warden_continuity"),
                f"Review continuity for Chapter {n}: {title}.",
                review_context,
                f"output/reviews/{prefix}_continuity.md",
                temperature=0.1,
            )
        )

    if cfg.get("workflow", {}).get("run_safety_warden", True):
        review_parts.append(
            call_agent(
                client,
                ledger,
                "warden_safety",
                agent(cfg, "warden_safety"),
                f"Review safety for Chapter {n}: {title}.",
                review_context,
                f"output/reviews/{prefix}_safety.md",
                temperature=0.1,
            )
        )

    if cfg.get("workflow", {}).get("run_voice_warden", True):
        review_parts.append(
            call_agent(
                client,
                ledger,
                "warden_voice",
                agent(cfg, "warden_voice"),
                f"Review voice for Chapter {n}: {title}.",
                review_context,
                f"output/reviews/{prefix}_voice.md",
                temperature=0.1,
            )
        )

    combined_review = "\n\n---\n\n".join(review_parts)
    write(f"output/reviews/{prefix}_combined.md", combined_review)
    blocked = contains_block(combined_review)
    ledger.append("chapter_review_complete", {"chapter": n, "title": title, "blocked": blocked})

    final = call_agent(
        client,
        ledger,
        "editor",
        agent(cfg, "editor"),
        f"Edit Chapter {n}: {title}. Apply review notes and produce the final chapter. If review notes contain BLOCK, explicitly resolve the blockers before finalising.",
        review_context + f"\n\n# Combined Review Notes\n{combined_review}",
        f"output/final_chapters/{prefix}.md",
        temperature=0.1,
    )
    ledger.append("chapter_complete", {"chapter": n, "title": title, "blocked_before_edit": blocked, "output_path": f"output/final_chapters/{prefix}.md"})
    return final


def assemble(cfg: dict, chapters: List[Dict[str, str]]) -> None:
    parts = [f"# {cfg['book']['title']}\n"]
    for chapter in chapters:
        n = int(chapter["number"])
        path = f"output/final_chapters/ch{n:02}.md"
        parts.append(read(path))
    write(cfg["book"].get("output_file", "output/full_first_draft.md"), "\n\n---\n\n".join(parts))


def write_status(cfg: dict, chapters: List[Dict[str, str]]) -> None:
    lines = ["# Charlotte Status", "", f"Book: {cfg['book']['title']}", "", "## Chapters"]
    for chapter in chapters:
        n = int(chapter["number"])
        path = ROOT / f"output/final_chapters/ch{n:02}.md"
        marker = "DONE" if path.exists() else "PENDING"
        lines.append(f"- Chapter {n}: {chapter['title']} — {marker}")
    write("output/status.md", "\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outline-only", action="store_true", help="Generate only output/book_outline.md")
    parser.add_argument("--chapter", type=int, help="Generate only one chapter by number")
    parser.add_argument("--assemble-only", action="store_true", help="Assemble existing final_chapters into full draft")
    args = parser.parse_args()

    cfg = load_config()
    ensure_dirs()
    ledger = Ledger(ROOT)
    client = client_from_config(cfg)

    foundation_path = cfg["book"]["foundation_file"]
    foundation = read(foundation_path)
    if not foundation.strip():
        raise SystemExit(f"Missing foundation material: {foundation_path}")
    if is_placeholder_foundation(foundation):
        raise SystemExit(f"Foundation material appears to be placeholder text. Replace {foundation_path} before running Charlotte.")

    if args.assemble_only:
        outline = read("output/book_outline.md")
        chapters = extract_chapters(outline)
        assemble(cfg, chapters)
        write_status(cfg, chapters)
        print(f"Assembled {cfg['book'].get('output_file', 'output/full_first_draft.md')}")
        return

    ledger.append("run_start", {"book": cfg["book"]["title"], "provider": cfg.get("provider", {}).get("type")})
    outline = run_outline(cfg, client, ledger, foundation)
    chapters = extract_chapters(outline)

    if args.outline_only:
        write_status(cfg, chapters)
        print("Wrote output/book_outline.md")
        return

    research_pack = run_research(cfg, client, ledger, foundation, outline)

    previous_summary = ""
    selected = [c for c in chapters if not args.chapter or int(c["number"]) == args.chapter]
    for chapter in selected:
        final = run_chapter(cfg, client, ledger, foundation, outline, research_pack, chapter, previous_summary)
        previous_summary = final[:1200]

    if not args.chapter:
        assemble(cfg, chapters)
        write_status(cfg, chapters)
        ledger.append("run_complete", {"output_file": cfg['book'].get('output_file', 'output/full_first_draft.md')})
        print(f"Wrote {cfg['book'].get('output_file', 'output/full_first_draft.md')}")
    else:
        write_status(cfg, chapters)
        ledger.append("chapter_run_complete", {"chapter": args.chapter})
        print(f"Wrote chapter {args.chapter}")


if __name__ == "__main__":
    main()
