"""Author Gate for Charlotte editorial rewrite pipeline.

Halts the Introduction chapter rewrite until human-supplied author content
is available in foundation/author_note.md. All other chapters pass freely.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Tuple


# Patterns indicating boilerplate/template content (case-insensitive)
BOILERPLATE_PATTERNS = [
    "insert your note here",
    "todo",
    "replace this",
    "[author's note",
    "write your",
]

REQUIRED_WORD_COUNT = 50


def _count_non_boilerplate_words(text: str) -> int:
    """Count words in text after stripping lines that are pure boilerplate."""
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        lowered = line.strip().lower()
        # Skip lines that are entirely a boilerplate pattern
        is_boilerplate = any(pattern in lowered for pattern in BOILERPLATE_PATTERNS)
        if not is_boilerplate:
            clean_lines.append(line)
    clean_text = " ".join(clean_lines)
    words = re.findall(r"\b\w+\b", clean_text)
    return len(words)


def check_author_gate(
    chapter_number: int,
    foundation_dir: str = "foundation",
) -> Tuple[bool, str]:
    """Check whether the Author Gate blocks a chapter.

    Only blocks chapter 0 (Introduction). All other chapters return (False, "").

    Checks foundation/author_note.md:
      - File must exist
      - Must contain >= 50 words of non-boilerplate content

    Returns:
        (True, reason) if blocked, (False, "") if unblocked.
    """
    if chapter_number != 0:
        return (False, "")

    author_note_path = Path(foundation_dir) / "author_note.md"

    if not author_note_path.exists():
        return (
            True,
            f"Author note file missing: {author_note_path}. "
            f"Create {author_note_path} with at least {REQUIRED_WORD_COUNT} words "
            f"of non-boilerplate content to unblock the Introduction chapter.",
        )

    try:
        content = author_note_path.read_text(encoding="utf-8")
    except OSError as exc:
        return (
            True,
            f"Cannot read author note file at {author_note_path}: {exc}",
        )

    if not content.strip():
        return (
            True,
            f"Author note file at {author_note_path} is empty. "
            f"Provide at least {REQUIRED_WORD_COUNT} words of non-boilerplate content "
            f"to unblock the Introduction chapter.",
        )

    word_count = _count_non_boilerplate_words(content)
    if word_count < REQUIRED_WORD_COUNT:
        return (
            True,
            f"Author note file at {author_note_path} contains only {word_count} words "
            f"of non-boilerplate content (minimum {REQUIRED_WORD_COUNT} required). "
            f"Add more substantive content to unblock the Introduction chapter.",
        )

    return (False, "")
