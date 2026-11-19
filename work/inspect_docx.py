# -*- coding: utf-8 -*-
"""Dump the structure of the application-form docx: sections, paragraphs, tables, cells."""
import sys, io
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

path = sys.argv[1]
out = io.open(sys.argv[2], 'w', encoding='utf-8')
def w(*a):
    print(*a, file=out)

doc = Document(path)

w("=== SECTIONS ===")
for i, s in enumerate(doc.sections):
    w(i, "page", s.page_width, s.page_height, "margins", s.left_margin, s.right_margin, s.top_margin, s.bottom_margin)

w("\n=== BODY ELEMENTS ===")
body = doc.element.body
tbl_idx = 0
par_idx = 0
for child in body.iterchildren():
    tag = child.tag.split('}')[-1]
    if tag == 'p':
        p = Paragraph(child, doc)
        txt = p.text
        style = p.style.name if p.style is not None else ''
        w(f"[P{par_idx}] style={style!r} text={txt!r}")
        par_idx += 1
    elif tag == 'tbl':
        t = Table(child, doc)
        w(f"[TABLE {tbl_idx}] rows={len(t.rows)} cols={len(t.columns)}")
        for ri, row in enumerate(t.rows):
            cells = []
            seen = set()
            for ci, cell in enumerate(row.cells):
                key = id(cell._tc)
                if key in seen:
                    continue
                seen.add(key)
                span = 1
                try:
                    span = cell.grid_span
                except Exception:
                    pass
                cells.append((ci, span, cell.text.replace('\n', '\\n')))
            w(f"  row{ri}: {cells}")
        tbl_idx += 1
    else:
        w(f"[{tag}]")

w("\n=== PARAGRAPH COUNT ===", len(doc.paragraphs), "TABLES", len(doc.tables))
out.close()
print("written")
