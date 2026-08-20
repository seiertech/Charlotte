# Author Actions — Draft 4

This is your single checklist of every place in Draft 4 that needs your own
voice or a decision from you. Each item marks a spot where the pipeline
inserted an `[AUTHOR VOICE]` placeholder and a `[NOTE TO AUTHOR]` brief.

The surrounding chapter text is already written and complete — these are the
personal, first-person moments only you can supply. Drop your words in place of
the `[AUTHOR VOICE]` / `[NOTE TO AUTHOR]` lines in each chapter file, then
rebuild the DOCX (`python3 orchestrator/make_docx.py`).

---

## Checklist

| # | Chapter | Type | What to write | Length |
|---|---------|------|---------------|--------|
| 1 | ch00 — A Note Before We Start | Author's real intro | Already supplied in your own words (foundation/author_note.md). Review it reads the way you want as the book's opening. | — |
| 2 | ch03 — Wiring | VOICE_MOMENT | A personal experience of reacting before thinking — your own wiring catching you. | 50–100 words |
| 3 | ch08 — The Toolkit | VOICE_MOMENT | How you discovered you'd been working on the wrong layer — the personal origin of the sequencing insight. | 100–150 words |
| 4 | ch10 — When the Layer Won't Move | VOICE_MOMENT | A personal moment of recognising the difference between trusting what you've proven and having faith to keep going when proof is absent. A time you kept a habit or relationship alive not for immediate results but because you believed in the longer arc. | 100–200 words |
| 5 | ch11 — Belief, Then Faith | VOICE_MOMENT | Your own growth map — what changed in you from applying this. The book's emotional close. | 150–300 words |
| 6 | ch13 — A Note Before You Go | PERSONAL_STORY | Close the book in your own voice. What you most want the reader to carry out the door — and, if you're willing, where you are now with your own system, on your own ongoing journey. The last thing they hear from you. | 150–300 words |

---

## How to fill them in

1. Open the chapter file under `output/draft4/` (e.g. `output/draft4/ch11.md`).
2. Find the `[AUTHOR VOICE]` line and the `[NOTE TO AUTHOR: ...]` brief below it.
3. Replace both lines with your passage.
4. When all are done, rebuild the final files:
   ```
   python3 orchestrator/make_docx.py
   ```
   This regenerates `output/full_fourth_draft.docx` and `output/full_fourth_draft.md`.

## Note on faith vs. trust (ch09 / ch10 / ch11)

Per your instruction, the manuscript keeps faith as faith — it does not convert
your belief language into secular terms. It does, however, make an explicit
point about the difference between **trust** (confidence earned from proven
evidence) and **faith** (continuing when proof is absent), then proceeds on
faith. Items 4 and 5 above are where your personal voice on this lands.
