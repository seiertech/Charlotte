"""Export a Charlotte manuscript (.md) to PDF and DOCX — the .md is never modified.

Usage:
    python3 orchestrator/export_formats.py output/full_second_draft.md
    # -> output/full_second_draft.pdf  +  output/full_second_draft.docx
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import markdown as md_lib
from xhtml2pdf import pisa
from htmldocx import HtmlToDocx
import docx
from docx.shared import Pt


CSS = """
@page { size: A5; margin: 2cm 1.8cm; }
body { font-family: Georgia, "Times New Roman", serif; font-size: 11pt; line-height: 1.5; color: #1a1a1a; }
h1 { font-size: 20pt; margin-top: 0; page-break-before: always; }
h1.first { page-break-before: avoid; }
h2 { font-size: 14pt; margin-top: 1.2em; }
h3 { font-size: 12pt; margin-top: 1em; }
h4 { font-size: 11pt; font-weight: bold; }
p  { margin: 0.5em 0; }
blockquote { color: #444; border-left: 3px solid #bbb; margin: 0.8em 0; padding: 0.2em 0.9em; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 9.5pt; }
th, td { border: 1px solid #999; padding: 4px 6px; text-align: left; vertical-align: top; }
th { background: #f0f0f0; font-weight: bold; }
hr { border: 0; border-top: 1px solid #ccc; margin: 1.2em 0; }
em { font-style: italic; } strong { font-weight: bold; }
"""


def md_to_html(md_text: str) -> str:
    body = md_lib.markdown(
        md_text,
        extensions=["tables", "extra", "sane_lists", "nl2br"],
    )
    # page-break before each chapter <h1>, except the first (title)
    first = [True]
    def mark(m):
        if first[0]:
            first[0] = False
            return '<h1 class="first"' + m.group(1) + '>'
        return '<h1' + m.group(1) + '>'
    body = re.sub(r'<h1([^>]*)>', mark, body)
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"


def make_pdf(html: str, out_path: Path) -> None:
    with out_path.open("wb") as fh:
        result = pisa.CreatePDF(html, dest=fh, encoding="utf-8")
    if result.err:
        raise RuntimeError(f"PDF generation reported {result.err} errors")


def make_docx(html: str, out_path: Path) -> None:
    doc = docx.Document()
    # base body font
    style = doc.styles["Normal"]
    style.font.name = "Georgia"
    style.font.size = Pt(11)
    HtmlToDocx().add_html_to_document(html, doc)
    doc.save(str(out_path))


def main() -> None:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "output/full_second_draft.md")
    if not src.exists():
        raise SystemExit(f"Source not found: {src}")

    md_text = src.read_text(encoding="utf-8")
    html = md_to_html(md_text)

    pdf_path = src.with_suffix(".pdf")
    docx_path = src.with_suffix(".docx")

    make_pdf(html, pdf_path)
    print(f"PDF  -> {pdf_path}  ({pdf_path.stat().st_size // 1024} KB)")

    make_docx(html, docx_path)
    print(f"DOCX -> {docx_path}  ({docx_path.stat().st_size // 1024} KB)")

    print(f"Source .md left untouched: {src}")


if __name__ == "__main__":
    main()
