"""Charlotte first-draft orchestrator.

This is intentionally simple. Kiro can improve the internals later, but this file gives the repo a clear executable workflow and output contract.
"""

from pathlib import Path
import argparse
import textwrap
import yaml

ROOT = Path(__file__).resolve().parents[1]


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
    ]:
        (ROOT / path).mkdir(parents=True, exist_ok=True)


def generate_outline(foundation: str) -> str:
    # Placeholder deterministic outline. Replace with model call in Kiro/NIM integration.
    return textwrap.dedent(
        """
        # Charlotte Book Outline

        ## Proposition
        A plain-language book that helps the reader understand themselves as a system and change gently through cause and effect.

        ## Reader
        Someone who feels stuck, overwhelmed, or unable to explain why they keep repeating the same patterns.

        ## Draft Chapter Plan

        1. You Are a System
        2. Cause and Effect in You
        3. The Body Speaks First
        4. The Currencies You Spend
        5. The Operating System Underneath
        6. Identity and the Roles You Carry
        7. Habits as Repeated Routes
        8. Burnout as System Debt
        9. Changing Without Fighting Yourself
        10. Tools That Help, and Where They Stop
        11. Relationships as Shared Systems
        12. Faith, Meaning, and the Longer Road
        13. Watching the System Change
        14. The Manual You Keep Writing
        """
    ).strip()


def generate_stub_chapter(number: int, title: str, foundation: str) -> str:
    return textwrap.dedent(
        f"""
        # Chapter {number}: {title}

        This is a generated placeholder chapter for the Charlotte first-draft workflow.

        The final version should be produced by the Drafter agent using the foundation material, chapter plan, research notes, and review loop.

        ## What this chapter must do

        - Teach one idea clearly.
        - Keep the voice calm and human.
        - Build only on what has already been established.
        - Avoid revealing later concepts too early.
        - End with a gentle pull into the next chapter.

        ## Draft body placeholder

        You are not random. You are not broken beyond explanation. Something in you is organised, even if it does not yet feel kind.

        The work begins by noticing the pattern before trying to fix it.
        """
    ).strip()


def assemble(chapters: list[str], output_file: str) -> None:
    manuscript = "# THE SYSTEM OF YOU\n\n" + "\n\n---\n\n".join(chapters)
    write(output_file, manuscript)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outline-only", action="store_true")
    parser.add_argument("--chapter", type=int)
    parser.add_argument("--assemble-only", action="store_true")
    args = parser.parse_args()

    cfg = load_config()
    ensure_dirs()

    foundation_path = cfg["book"]["foundation_file"]
    output_file = cfg["book"].get("output_file", "output/full_first_draft.md")
    foundation = read(foundation_path)

    if not foundation.strip():
        raise SystemExit(f"Missing foundation material: {foundation_path}")

    outline = generate_outline(foundation)
    write("output/book_outline.md", outline)

    if args.outline_only:
        print("Wrote output/book_outline.md")
        return

    titles = [
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

    if args.chapter:
        n = args.chapter
        title = titles[n - 1]
        chapter = generate_stub_chapter(n, title, foundation)
        write(f"output/drafts/ch{n:02}.md", chapter)
        write(f"output/final_chapters/ch{n:02}.md", chapter)
        print(f"Wrote chapter {n}")
        return

    chapters = []
    for idx, title in enumerate(titles, start=1):
        chapter = generate_stub_chapter(idx, title, foundation)
        write(f"output/drafts/ch{idx:02}.md", chapter)
        write(f"output/final_chapters/ch{idx:02}.md", chapter)
        chapters.append(chapter)

    assemble(chapters, output_file)
    print(f"Wrote {output_file}")


if __name__ == "__main__":
    main()
