"""Charlotte Draft-3 conveyor.

Reveal order + rules come from foundation/DRAFT3_DIRECTIVES.md (Decisions A–E).
Pipeline per chapter: Researcher(119B) -> Architect(119B) -> Drafter(675B) -> Editor(119B).
Chapters written to output/draft3/chNN.md and committed one at a time.

Usage:
    python3 orchestrator/conveyor_v3.py 1 1     # one chapter
    python3 orchestrator/conveyor_v3.py 1 12    # a range
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml
from providers.model_client import client_from_config, ModelClient

MAX_RETRIES = 5
RETRY_BACKOFF = [30, 60, 90, 120, 180]
INTER_CHAPTER_PAUSE = 20
WORD_TARGET = 2200  # Draft 3 chapters carry mechanism + failure modes; toolkit/worked/hard longer

# The locked Draft-3 reveal order (from DRAFT3_DIRECTIVES.md)
CHAPTERS = [
    (0,  "A Note Before We Start",                 "intro"),
    (1,  "The Doorway — You Are a System",         "doorway"),
    (2,  "Body",                                   "layer"),
    (3,  "Wiring",                                 "layer"),
    (4,  "Habit",                                  "layer"),
    (5,  "Room",                                   "layer"),
    (6,  "Story",                                  "layer"),
    (7,  "The Method Made Whole",                  "method"),
    (8,  "The Toolkit",                            "toolkit"),
    (9,  "Worked Situations",                      "worked"),
    (10, "The Hard Cases",                         "hardcases"),
    (11, "Belief, Then Faith",                     "finale"),
    (12, "Watching It Change — The Growth Map",    "growth"),
]

LAYER_GRAMMAR = {
    "Body":   "weight, thinness, blur, temperature (never psychological)",
    "Wiring": "speed, gear-slip, reaction-before-decision (never slow)",
    "Habit":  "groove, automaticity, sleepwalking (never effortful)",
    "Room":   "temperature, volume, pull, weather (never solitary)",
    "Story":  "narration, the uninvited sentence, the coat (never sensory)",
}


def read(path: str) -> str:
    p = ROOT / path
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write(path: str, content: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def call(client: ModelClient, system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    for attempt in range(MAX_RETRIES + 1):
        try:
            return client.complete(messages, temperature=temperature).content
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES:
                w = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"    429 — waiting {w}s (retry {attempt+1})"); time.sleep(w)
            else:
                raise
        except Exception as e:
            if attempt < MAX_RETRIES:
                w = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"    {type(e).__name__} — waiting {w}s (retry {attempt+1})"); time.sleep(w)
            else:
                raise
    return ""


def git_commit(n: int, title: str) -> None:
    subprocess.run(["git", "add", f"output/draft3/ch{n:02}.md", "output/status_v3.md"],
                   cwd=ROOT, check=True, capture_output=True)
    r = subprocess.run(["git", "commit", "-m", f"Draft 3 — Chapter {n:02}: {title[:55]}"],
                       cwd=ROOT, capture_output=True, text=True)
    print("    committed" if r.returncode == 0 else "    (nothing to commit)")


def drafter_task(n: int, title: str, kind: str) -> str:
    """Chapter-type-specific instruction, all Decision-E compliant."""
    base = (f"Write Chapter {n}: '{title}' for Draft 3. Follow DRAFT3_DIRECTIVES exactly: "
            f"plain layer names (Body/Wiring/Habit/Room/Story); banned words (chest, clench, shoulders, "
            f"'lands like a stone', 'why can't I just'); POV division (third person demonstrates, "
            f"second person applies, 'I' only for argument). ")
    if kind == "intro":
        return (base + "This is the reader-facing INTRODUCTION in the author's warm FIRST-PERSON voice. "
                "PRESERVE this placeholder EXACTLY and do NOT invent a personal story: "
                "'> [Author's note — to be written in your own true words.]'. "
                "Install two convictions only — you are a system; everything is cause and effect — plus relief, "
                "and how to read the book. No layers, no model. ~900 words.")
    if kind == "doorway":
        return (base + "This is THE DOORWAY. It contains the ONE full scene of the whole book (your best 500 words) "
                "AND the five-cause proof: FIVE DISTINCT people (vary age/gender/situation) all snapping at 3pm, "
                "five different causes (Body=slept five hours; Wiring=reaction before decision; Habit=worn groove, "
                "third time this week; Room=walked into a room already tense; Story='I'm the one who holds everything "
                "together, so I'm the one allowed to break'), each with a DIFFERENT body. Third person for the five, "
                "then pivot to second person: 'Which one was yours?' Do NOT name the five layers yet — call them "
                "'five places it could be coming from'. ~1400 words.")
    if kind == "layer":
        g = LAYER_GRAMMAR.get(title, "")
        return (base + f"This is the '{title}' layer chapter. Sensory grammar for {title}: {g}. "
                "Structure: recognition (micro-scene as evidence, NOT an overture) -> what this layer is -> "
                "MECHANISM (why it constrains the layers above it; what actually fails) -> a 'Commonly mistaken for' "
                "section -> a 'Notice this in you' practice (notice->trace->try->watch->adjust, ending 'One line for "
                "the picture of yourself: ...'). Currencies appear ONLY as 'what is it costing you'. ~2200 words.")
    if kind == "method":
        return (base + "Teach the whole method: the two questions 'which layer, which currency', the sequencing rule "
                "(work from the body up), and the self-check across all five layers. Include a 'Notice this in you'. ~2000 words.")
    if kind == "toolkit":
        return (base + "A CLEAN reference of the tools (few, named), each: what it's for / when / how (steps) / what it "
                "feels like / its edge (when to reach for a person). No repetitive per-tool scenes. End with a layer->tool "
                "chooser. ~2600 words.")
    if kind == "worked":
        return (base + "Reader-aligned worked situations (generic 'when you...' framings, NOT named-character stories), "
                "each walked through with the tools by name, including the honest stumble-and-adjust. ~2600 words.")
    if kind == "hardcases":
        return (base + "The hard cases, addressed directly to the reader: the person who diagnosed correctly and still "
                "won't move; and the reader whose lowest layer is not fixable (chronic illness, poverty, a marriage they "
                "can't leave). Honest, not tidy. This earns trust. ~1800 words.")
    if kind == "finale":
        return (base + "The volition finale. Answer the reader's real last-page question: 'I understand — and I still "
                "won't do it. Why?' Distinguish Belief (map; corrected by evidence) from Faith (compass; restored by "
                "meaning), agnostic of religion. This is the emotional climax. ~2000 words.")
    if kind == "growth":
        return (base + "Watching the system change + the Growth Map. Pay off the Doorway: the reader's own accumulating "
                "self-portrait from the practices, traced over time. End the book with the closer about reaching for a "
                "person. ~1600 words.")
    return base


def main() -> None:
    cfg = yaml.safe_load(read("config.yaml"))
    cfg["provider"]["timeout_seconds"] = 600
    big = client_from_config(cfg)  # 675B prose
    scfg = dict(cfg); scfg["provider"] = cfg.get("reviewer_provider", cfg["provider"])
    small = client_from_config(scfg)  # 119B support

    foundation = read("foundation/Me_OS_Foundation.md")
    directives = read("foundation/DRAFT3_DIRECTIVES.md")
    researcher_p = read(cfg["agents"]["researcher"])
    architect_p = read(cfg["agents"]["chapter_architect"])
    drafter_p = read(cfg["agents"]["drafter"])
    editor_p = read(cfg["agents"]["editor"])

    start = int(sys.argv[1]) if len(sys.argv) >= 2 else 0
    end = int(sys.argv[2]) if len(sys.argv) >= 3 else 12
    selected = [c for c in CHAPTERS if start <= c[0] <= end]

    state_path = ROOT / "output/book_state_v3.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}

    print(f"=== DRAFT 3 CONVEYOR — chapters {start}-{end} ({len(selected)}) | prose=675B ===")
    (ROOT / "output/draft3").mkdir(parents=True, exist_ok=True)

    for idx, (n, title, kind) in enumerate(selected):
        print(f"\nch{n:02}: {title}  [{kind}]")
        # prior context: summaries of earlier draft-3 chapters
        prior = "\n".join(f"- Ch{k}: {v.get('title')} — {v.get('summary','')[:220]}"
                          for k, v in sorted(state.items(), key=lambda kv: int(kv[0])) if int(k) < n)
        base_ctx = (f"# Book: THE SYSTEM OF YOU\n\n# DRAFT 3 DIRECTIVES (obey exactly)\n{directives}\n\n"
                    f"# Foundation (model + voice; renamed per directives)\n{foundation}\n\n"
                    f"# Earlier Draft-3 chapters (continuity)\n{prior or 'none yet'}\n")

        if kind == "intro":
            # Intro: single author-voice call, preserve placeholder (no research/architect needed)
            print("    [drafter/intro 675B]...", end=" ", flush=True)
            final = call(big, drafter_p, drafter_task(n, title, kind) + "\n\n" + base_ctx, temperature=0.5)
            print("done")
        else:
            print("    [1/4 researcher]...", end=" ", flush=True)
            research = call(small, researcher_p,
                f"Focused research/concept pack for Chapter {n}: '{title}' ({kind}). Concrete examples from varied "
                f"life domains; name what must NOT be revealed yet; no prose.\n\n{base_ctx}", 0.1)
            write(f"output/draft3/_research_ch{n:02}.md", research); print("done")

            print("    [2/4 architect]...", end=" ", flush=True)
            plan = call(small, architect_p,
                f"Plan Chapter {n}: '{title}' ({kind}) per the directives and the drafter task below. "
                f"Sections, opening beat (recognition), mechanism/commonly-mistaken-for where relevant, closing pull, "
                f"and the 'Notice this in you' practice.\n\nDRAFTER TASK:\n{drafter_task(n,title,kind)}\n\n"
                f"{base_ctx}\n\n# Research\n{research}", 0.2)
            write(f"output/draft3/_plan_ch{n:02}.md", plan); print("done")

            print("    [3/4 drafter 675B]...", end=" ", flush=True)
            draft = call(big, drafter_p, drafter_task(n, title, kind) +
                f"\n\n{base_ctx}\n\n# Chapter Plan\n{plan}\n\n# Research\n{research}", 0.4)
            print("done")

            print("    [4/4 editor]...", end=" ", flush=True)
            final = call(small, editor_p,
                f"Edit Chapter {n}: '{title}'. Smooth flow and rhythm; keep every scene, example, and the practice; "
                f"enforce banned-word removal (chest/clench/shoulders); do not add new concepts.\n\n"
                f"# Draft\n{draft}\n\n# Plan\n{plan}", 0.2)
            print("done")

        final = re.sub(r'^\s*```markdown\s*\n', '', final); final = re.sub(r'\n```\s*$', '\n', final)
        write(f"output/draft3/ch{n:02}.md", final)
        wc = len(re.findall(r"\b\w+\b", final))
        print(f"    ✓ {wc} words")

        state[str(n)] = {"title": title, "kind": kind, "words": wc, "summary": final[:800]}
        state_path.write_text(json.dumps(state, indent=2))

        # status file
        lines = ["# Charlotte Draft 3 — Status", ""]
        for cn, ct, ck in CHAPTERS:
            done = (ROOT / f"output/draft3/ch{cn:02}.md").exists()
            w = state.get(str(cn), {}).get("words", "")
            lines.append(f"- Ch{cn}: {ct} — {'DONE ('+str(w)+'w)' if done else 'pending'}")
        write("output/status_v3.md", "\n".join(lines) + "\n")

        git_commit(n, title)
        if idx < len(selected) - 1:
            time.sleep(INTER_CHAPTER_PAUSE)

    print("\n=== batch complete ===")


if __name__ == "__main__":
    main()
