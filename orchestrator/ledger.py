"""Artefact ledger for Charlotte.

Records workflow events so execution state lives in the repo, not chat memory.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class Ledger:
    def __init__(self, root: Path, path: str = "output/ledger.jsonl") -> None:
        self.root = root
        self.path = root / path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, payload: Dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **payload,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
