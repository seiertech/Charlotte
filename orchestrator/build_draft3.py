"""Assemble the final Draft 3: clean intro, build the two appendices (Toolkit +
Troubleshooting) in the original clean format with the NEW layer names, and stitch
the whole manuscript into output/full_third_draft.md.

Toolkit + Troubleshooting are APPENDICES (per author instruction), covered the same
way as the original foundation (clean 12-tool reference + the layer tables).
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D3 = ROOT / "output/draft3"

# old computing layer labels -> new plain names (for the ported appendices)
LAYER_RENAMES = [
    ("Layer 1 — The body *(Hardware)*", "Body *(the body you run on)*"),
    ("Layer 2 — The part that runs without you noticing *(Operating System)*", "Wiring *(the part that runs before you decide)*"),
    ("Layer 3 — Habits & skills *(Software)*", "Habit *(the worn-in paths)*"),
    ("Layer 4 — The people *(Network)*", "Room *(the people around you)*"),
    ("Layer 5 — The story of who you are *(Identity)*", "Story *(who you understand yourself to be)*"),
]


def clean(t: str) -> str:
    t = t.strip()
    t = re.sub(r'^```(?:markdown)?\s*\n', '', t)
    t = re.sub(r'\n```\s*$', '', t).strip()
    # drop a leading model preamble line like "Here's Chapter 0 ... verbatim."
    lines = t.split('\n')
    if lines and re.match(r"^\s*Here[’']?s\b", lines[0]):
        cut = 0
        for i, l in enumerate(lines):
            if l.strip() == '---':
                cut = i + 1
                break
        lines = lines[cut:]
        t = '\n'.join(lines).strip()
    return t


def strip_leading_title(t: str) -> str:
    lines = t.split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and (lines[0].lstrip().startswith('#') or
                  (lines[0].strip().startswith('**') and lines[0].strip().endswith('**'))):
        lines.pop(0)
    return '\n'.join(lines).strip()


# ---- 1) Build Appendix A — The Toolkit (from the clean Draft-2 toolkit) ----
tk = (ROOT / "output/final_chapters/ch13.md").read_text(encoding="utf-8")
tk = clean(tk)
tk = strip_leading_title(tk)
# drop the trailing chapter-transition ("next we walk six problems...")
tk = re.split(r"\nA tool is only useful once", tk)[0].strip()
# new layer names in the chooser
tk = tk.replace("**Habits stuck?**", "**Habit stuck?**")
tk = tk.replace("**People drifting or clashing?**", "**Room — people drifting or clashing?**")
tk = tk.replace("Hidden machine", "Wiring")
appendix_a = "# Appendix A — The Toolkit\n\n*The tools themselves — few, named, and yours to keep. Every \"first move\" in the book points to one of these.*\n\n" + tk
(D3 / "appendix_a_toolkit.md").write_text(appendix_a, encoding="utf-8")

# ---- 2) Build Appendix B — Troubleshooting Reference (renamed layers) ----
ts = (ROOT / "output/final_chapters/troubleshooting_reference.md").read_text(encoding="utf-8")
ts = clean(ts)
ts = strip_leading_title(ts)
for old, new in LAYER_RENAMES:
    ts = ts.replace(f"### {old}", f"### {new}")
appendix_b = "# Appendix B — The Troubleshooting Reference\n\n" + ts
(D3 / "appendix_b_troubleshooting.md").write_text(appendix_b, encoding="utf-8")

# ---- 3) Clean the intro in place (strip preamble) ----
intro = clean((D3 / "ch00.md").read_text(encoding="utf-8"))
(D3 / "ch00.md").write_text(intro, encoding="utf-8")

# ---- 4) Assemble the final manuscript ----
# (skip ch08 — the verbose toolkit chapter; the Toolkit is now Appendix A)
FLOW = [
    ("ch00.md", None,        "A Note Before We Start"),               # Introduction
    ("ch01.md", 1,  "The Doorway — You Are a System"),
    ("ch02.md", 2,  "Body"),
    ("ch03.md", 3,  "Wiring"),
    ("ch04.md", 4,  "Habit"),
    ("ch05.md", 5,  "Room"),
    ("ch06.md", 6,  "Story"),
    ("ch07.md", 7,  "The Method Made Whole"),
    ("ch09.md", 8,  "Worked Situations"),
    ("ch10.md", 9,  "The Hard Cases"),
    ("ch11.md", 10, "Belief, Then Faith"),
    ("ch12.md", 11, "Watching It Change — The Growth Map"),
]

parts = ["# THE SYSTEM OF YOU\n### The Manual You Were Never Given\n\n"
         "*Understanding how you actually work — and what you actually need to run at your best.*\n\n"
         "**— Draft 3 —**\n"]

for fname, num, title in FLOW:
    body = strip_leading_title(clean((D3 / fname).read_text(encoding="utf-8")))
    header = f"# {title}" if num is None else f"# Chapter {num} — {title}"
    parts.append(f"{header}\n\n{body}")

# appendices
parts.append((D3 / "appendix_a_toolkit.md").read_text(encoding="utf-8").strip())
parts.append((D3 / "appendix_b_troubleshooting.md").read_text(encoding="utf-8").strip())

manuscript = "\n\n---\n\n".join(parts)
(ROOT / "output/full_third_draft.md").write_text(manuscript, encoding="utf-8")

wc = len(re.findall(r"\b\w+\b", manuscript))
print(f"Assembled output/full_third_draft.md — {wc:,} words, {len(FLOW)} chapters + 2 appendices")
