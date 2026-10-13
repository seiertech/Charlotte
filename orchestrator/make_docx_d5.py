#!/usr/bin/env python3
"""
make_docx_d5.py

Build output/full_fifth_draft.docx from the single reader-facing manuscript
output/full_fifth_draft.md.

Unlike make_docx.py (which assembles the fourth draft from per-chapter draft4/
files), this reads the finished fifth-draft markdown as-is, so the dedication,
the "A Toolkit for You" back matter, and the "Notes" endnotes are all included
exactly as written. It reuses the same lightweight markdown->docx rendering and
book typography.

Run: PYTHONPATH=/tmp/pylibs python3 orchestrator/make_docx_d5.py
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTPUT_DIR = os.path.join(ROOT, "output")
MD_PATH = os.path.join(OUTPUT_DIR, "full_fifth_draft.md")
DOCX_PATH = os.path.join(OUTPUT_DIR, "full_fifth_draft.docx")

BOOK_TITLE = "THE SYSTEM OF YOU"
BOOK_SUBTITLE = "The Manual You Were Never Given"

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BODY_FONT = "Georgia"
BODY_SIZE = Pt(11)

# Front/back-matter H1s that should NOT force the "Chapter" treatment but still
# start on a fresh page.
SUPERSCRIPT_RE = re.compile(r"\^(\d+)\^")
INLINE_RE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|_[^_]+?_)")


def configure_document_styles(document):
    normal = document.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = BODY_SIZE
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:ascii"), BODY_FONT)
    rfonts.set(qn("w:hAnsi"), BODY_FONT)
    pf = normal.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(10)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = 1.25
    for name, before, after in (
        ("Heading 1", 0, 18),
        ("Heading 2", 18, 8),
        ("Heading 3", 14, 6),
        ("Heading 4", 12, 4),
    ):
        try:
            st = document.styles[name]
        except KeyError:
            continue
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True


def _add_run(paragraph, text, bold, italic, superscript=False):
    if text == "":
        return
    run = paragraph.add_run(text)
    if bold:
        run.bold = True
    if italic:
        run.italic = True
    if superscript:
        run.font.superscript = True


def _add_text_with_superscripts(paragraph, text, bold, italic):
    """Render ^N^ endnote markers as true superscripts."""
    pos = 0
    for m in SUPERSCRIPT_RE.finditer(text):
        if m.start() > pos:
            _add_run(paragraph, text[pos:m.start()], bold, italic)
        _add_run(paragraph, m.group(1), bold, italic, superscript=True)
        pos = m.end()
    if pos < len(text):
        _add_run(paragraph, text[pos:], bold, italic)


def add_inline_runs(paragraph, text, base_bold=False, base_italic=False):
    if text == "":
        return
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            _add_text_with_superscripts(paragraph, text[pos:m.start()], base_bold, base_italic)
        token = m.group(0)
        if token.startswith("**") and token.endswith("**"):
            _add_text_with_superscripts(paragraph, token[2:-2], True, base_italic)
        elif token.startswith("*") and token.endswith("*"):
            _add_text_with_superscripts(paragraph, token[1:-1], base_bold, True)
        elif token.startswith("_") and token.endswith("_"):
            _add_text_with_superscripts(paragraph, token[1:-1], base_bold, True)
        else:
            _add_text_with_superscripts(paragraph, token, base_bold, base_italic)
        pos = m.end()
    if pos < len(text):
        _add_text_with_superscripts(paragraph, text[pos:], base_bold, base_italic)


def _list_number_match(line):
    m = re.match(r"^\s*\d+[.)]\s+(.*)$", line)
    return m.group(1) if m else None


def _split_table_row(stripped):
    inner = stripped.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip() for c in inner.split("|")]


def _is_table_separator(stripped):
    body = stripped.strip("|").replace("|", "").replace(":", "").strip()
    return "-" in stripped and set(body) <= {"-", " "}


def _flush_table(document, rows):
    if not rows:
        return
    ncols = max(len(r) for r in rows)
    table = document.add_table(rows=0, cols=ncols)
    try:
        table.style = "Light Grid Accent 1"
    except KeyError:
        try:
            table.style = "Table Grid"
        except KeyError:
            pass
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_i, row in enumerate(rows):
        cells = table.add_row().cells
        for c_i in range(ncols):
            text = row[c_i] if c_i < len(row) else ""
            cell = cells[c_i]
            cell.text = ""
            add_inline_runs(cell.paragraphs[0], text, base_bold=(r_i == 0))


def build_title_page(document):
    spacer = document.add_paragraph()
    spacer.paragraph_format.space_before = Pt(120)
    title = document.add_paragraph(style="Title")
    title.add_run(BOOK_TITLE)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    try:
        sub = document.add_paragraph(style="Subtitle")
    except KeyError:
        sub = document.add_paragraph(style="Heading 2")
    srun = sub.add_run(BOOK_SUBTITLE)
    srun.italic = True
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.space_before = Pt(12)


def render(document, md_text):
    lines = md_text.split("\n")
    table_buf = []
    first_h1_done = False
    # The manuscript's own title line (# THE SYSTEM OF YOU) is handled by the
    # title page, so skip the very first H1 + its subtitle line.
    skip_title_block = True

    def flush():
        _flush_table(document, table_buf)
        table_buf.clear()

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("|"):
            if _is_table_separator(stripped):
                continue
            table_buf.append(_split_table_row(stripped))
            continue
        elif table_buf:
            flush()

        if stripped == "---" or (set(stripped) == {"-"} and len(stripped) >= 3):
            continue
        if stripped == "":
            continue

        # Skip the manuscript's own title line + subtitle (title page covers it)
        if skip_title_block:
            if stripped == "# " + BOOK_TITLE or stripped.lstrip("# ").strip().upper() == BOOK_TITLE:
                continue
            if stripped.strip("*") == BOOK_SUBTITLE:
                continue

        if stripped.startswith("####"):
            add_inline_runs(document.add_paragraph(style="Heading 4"), stripped[4:].strip())
            continue
        if stripped.startswith("###"):
            add_inline_runs(document.add_paragraph(style="Heading 3"), stripped[3:].strip())
            continue
        if stripped.startswith("##"):
            add_inline_runs(document.add_paragraph(style="Heading 2"), stripped[2:].strip())
            continue
        if stripped.startswith("#"):
            text = stripped[1:].strip()
            skip_title_block = False
            if first_h1_done:
                document.add_page_break()
            first_h1_done = True
            add_inline_runs(document.add_paragraph(style="Heading 1"), text)
            continue

        if stripped.startswith(">"):
            qtext = stripped[1:].strip()
            if qtext == "":
                continue
            p = document.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.right_indent = Inches(0.5)
            add_inline_runs(p, qtext, base_italic=True)
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            add_inline_runs(document.add_paragraph(style="List Bullet"), stripped[2:].strip())
            continue

        num_text = _list_number_match(line)
        if num_text is not None:
            add_inline_runs(document.add_paragraph(style="List Number"), num_text)
            continue

        if stripped.startswith("**") and stripped.endswith("**") and stripped.count("**") == 2:
            add_inline_runs(document.add_paragraph(), stripped)
            continue

        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_inline_runs(p, stripped)

    if table_buf:
        flush()


def main():
    with open(MD_PATH, "r", encoding="utf-8") as fh:
        md = fh.read()
    document = Document()
    configure_document_styles(document)
    build_title_page(document)
    document.add_page_break()
    render(document, md)
    document.save(DOCX_PATH)
    size = os.path.getsize(DOCX_PATH)
    words = len(re.findall(r"\S+", md))
    print("BUILD COMPLETE")
    print("DOCX : {}".format(DOCX_PATH))
    print("size : {:,} bytes".format(size))
    print("words: {:,}".format(words))


if __name__ == "__main__":
    main()
