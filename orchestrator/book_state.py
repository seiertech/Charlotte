"""Minimal book state ledger for Charlotte.

Kiro can expand this into richer continuity tracking later.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ChapterRecord:
    number: int
    title: str
    summary: str
    introduced_terms: List[str] = field(default_factory=list)
    open_flags: List[str] = field(default_factory=list)


@dataclass
class BookState:
    chapters: List[ChapterRecord] = field(default_factory=list)

    def add_chapter(self, number: int, title: str, summary: str) -> None:
        self.chapters.append(ChapterRecord(number=number, title=title, summary=summary))

    def as_context(self) -> str:
        if not self.chapters:
            return "No previous chapters yet."
        lines = ["# Book State Ledger"]
        for ch in self.chapters:
            lines.append(f"- Chapter {ch.number}: {ch.title} — {ch.summary}")
        return "\n".join(lines)
