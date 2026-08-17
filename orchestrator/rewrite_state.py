"""Rewrite pipeline state tracking for Charlotte.

Tracks per-chapter progress through the editorial rewrite pipeline:
- chapter status (pending → rewriting → rewritten → editorial_pass / blocked / waiting_human_input)
- revision counts and block reasons
- word counts (D3 source vs D4 output)
- character usage per chapter

State is persisted to output/draft4_state.json so runs can resume after a crash.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


VALID_STATUSES = (
    "pending",
    "rewriting",
    "rewritten",
    "editorial_pass",
    "blocked",
    "waiting_human_input",
)


@dataclass
class RewriteChapterRecord:
    number: int
    title: str
    status: str = "pending"  # one of VALID_STATUSES
    revision_count: int = 0
    block_reason: str = ""
    blocking_agent: str = ""
    d3_word_count: int = 0
    d4_word_count: int = 0
    characters_used: List[str] = field(default_factory=list)
    output_path: str = ""


@dataclass
class RewriteState:
    chapters: List[RewriteChapterRecord] = field(default_factory=list)

    # ----- lookups -------------------------------------------------------
    def get(self, number: int) -> Optional[RewriteChapterRecord]:
        """Return the chapter record for the given number, or None if not found."""
        for ch in self.chapters:
            if ch.number == number:
                return ch
        return None

    def upsert(self, record: RewriteChapterRecord) -> None:
        """Update an existing chapter record or add a new one."""
        for idx, ch in enumerate(self.chapters):
            if ch.number == record.number:
                self.chapters[idx] = record
                break
        else:
            self.chapters.append(record)
        self.chapters.sort(key=lambda c: c.number)

    def is_editorial_pass(self, number: int) -> bool:
        """Return True if the chapter has passed editorial review."""
        ch = self.get(number)
        return ch is not None and ch.status == "editorial_pass"

    def summary_status(self) -> Dict[str, int]:
        """Return counts per status category."""
        counts: Dict[str, int] = {}
        for ch in self.chapters:
            counts[ch.status] = counts.get(ch.status, 0) + 1
        return counts

    # ----- persistence ---------------------------------------------------
    def save(self, path: Path) -> None:
        """Write state to JSON immediately."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"chapters": [asdict(c) for c in self.chapters]}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "RewriteState":
        """Load state from JSON file.

        If the file is missing, return an empty state (all chapters treated as pending).
        If the file is corrupted/unparseable, raise a clear error WITHOUT overwriting.
        """
        if not path.exists():
            return cls()
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RuntimeError(
                f"Cannot read state file at {path}: {exc}"
            ) from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"State file at {path} is corrupted (invalid JSON): {exc}. "
                f"The file has NOT been overwritten — resolve manually."
            ) from exc
        if not isinstance(data, dict) or "chapters" not in data:
            raise RuntimeError(
                f"State file at {path} is corrupted (missing 'chapters' key). "
                f"The file has NOT been overwritten — resolve manually."
            )
        chapters = [
            RewriteChapterRecord(**ch) for ch in data["chapters"]
        ]
        return cls(chapters=chapters)
