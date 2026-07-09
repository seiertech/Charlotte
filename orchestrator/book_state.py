"""Book state ledger for Charlotte.

Tracks cross-chapter continuity so the pipeline never depends on chat memory:
- chapter summaries (for context windowing)
- terms introduced (so later chapters stay consistent and do not redefine)
- examples/practices used (so the Example Curator can catch repeats)
- open flags raised by wardens (so nothing is silently dropped)

State is persisted to output/book_state.json so runs can resume after a crash.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class ChapterRecord:
    number: int
    title: str
    summary: str = ""
    introduced_terms: List[str] = field(default_factory=list)
    examples_used: List[str] = field(default_factory=list)
    open_flags: List[str] = field(default_factory=list)
    word_count: int = 0
    revisions: int = 0
    blocked: bool = False
    final_path: str = ""


@dataclass
class BookState:
    chapters: List[ChapterRecord] = field(default_factory=list)

    # ----- lookups -------------------------------------------------------
    def get(self, number: int) -> Optional[ChapterRecord]:
        for ch in self.chapters:
            if ch.number == number:
                return ch
        return None

    def upsert_chapter(self, record: ChapterRecord) -> None:
        for idx, ch in enumerate(self.chapters):
            if ch.number == record.number:
                self.chapters[idx] = record
                break
        else:
            self.chapters.append(record)
        self.chapters.sort(key=lambda c: c.number)

    def is_complete(self, number: int) -> bool:
        ch = self.get(number)
        return bool(ch and ch.final_path and not ch.blocked)

    # ----- aggregate views for prompts ----------------------------------
    def known_terms(self) -> List[str]:
        terms: List[str] = []
        for ch in self.chapters:
            terms.extend(ch.introduced_terms)
        return terms

    def used_examples(self) -> List[str]:
        used: List[str] = []
        for ch in self.chapters:
            used.extend(ch.examples_used)
        return used

    def previous_summary(self, number: int) -> str:
        """Summary of the chapter immediately before `number`."""
        prev = [c for c in self.chapters if c.number < number and c.summary]
        if not prev:
            return "No previous chapter."
        last = max(prev, key=lambda c: c.number)
        return f"Chapter {last.number}: {last.title}\n{last.summary}"

    def windowed_context(self, number: int, window: int) -> str:
        """Full summaries for the last `window` chapters, plus terms/examples so far.

        Keeps the prompt bounded on long books instead of appending every prior chapter.
        """
        prior = sorted((c for c in self.chapters if c.number < number and c.summary), key=lambda c: c.number)
        recent = prior[-window:] if window > 0 else prior
        lines = ["# Book State"]
        if recent:
            lines.append("\n## Recent chapter summaries")
            for ch in recent:
                lines.append(f"- Chapter {ch.number}: {ch.title} — {ch.summary}")
        terms = self.known_terms()
        if terms:
            lines.append("\n## Terms already introduced (keep consistent, do not redefine)")
            lines.append(", ".join(sorted(set(terms))))
        examples = self.used_examples()
        if examples:
            lines.append("\n## Examples/practices already used (do not repeat)")
            lines.append("; ".join(examples[-40:]))
        open_flags = [f"Ch{c.number}: {flag}" for c in self.chapters for flag in c.open_flags]
        if open_flags:
            lines.append("\n## Open flags from earlier chapters")
            for flag in open_flags:
                lines.append(f"- {flag}")
        return "\n".join(lines)

    def as_context(self) -> str:
        if not self.chapters:
            return "No previous chapters yet."
        lines = ["# Book State Ledger"]
        for ch in self.chapters:
            lines.append(f"- Chapter {ch.number}: {ch.title} — {ch.summary}")
        return "\n".join(lines)

    # ----- persistence ---------------------------------------------------
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"chapters": [asdict(c) for c in self.chapters]}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "BookState":
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        chapters = [ChapterRecord(**c) for c in data.get("chapters", [])]
        return cls(chapters=chapters)
