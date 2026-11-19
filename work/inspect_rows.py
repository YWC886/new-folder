# -*- coding: utf-8 -*-
"""Detailed look at rows 4-28 of the template table: heights, paragraphs, cell properties."""
import sys, io
from docx import Document
from docx.shared import Twips

path = sys.argv[1]
out = io.open(sys.argv[2], 'w', encoding='utf-8')
def w(*a):
    print(*a, file=out)

doc = Document(path)
t = doc.tables[0]
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
for ri, row in enumerate(t.rows):
    tr = row._tr
    trPr = tr.find(W + 'trPr')
    height = None
    hrule = None
    ex = None
    if trPr is not None:
        h = trPr.find(W + 'trHeight')
        if h is not None:
            height = h.get(W + 'val')
            hrule = h.get(W + 'hRule')
        ex = trPr.find(W + 'tblHeader')
    cells = row.cells
    seen = []
    for c in cells:
        if c._tc not in [x._tc for x in seen]:
            seen.append(c)
    info = []
    for c in seen:
        paras = c.paragraphs
        texts = [p.text for p in paras if p.text.strip()]
        info.append(dict(span=c.grid_span, nparas=len(paras), texts=texts))
    w(f"ROW {ri}: height={height} rule={hrule} cells={len(seen)}", info)

# also dump paragraph styles / alignments of header paragraphs
w("\n=== CELL PARAGRAPH DETAIL (row 12+) ===")
for ri in range(12, len(t.rows)):
    row = t.rows[ri]
    c = row.cells[0]
    for pi, p in enumerate(c.paragraphs):
        pf = p.paragraph_format
        w(f"row{ri} para{pi}: {p.text!r} style={p.style.name} align={p.alignment} first_line={pf.first_line_indent} line_spacing={pf.line_spacing} space_before={pf.space_before} space_after={pf.space_after}")
        for r in p.runs:
            w(f"    run {r.text!r} font={r.font.name} size={r.font.size} bold={r.font.bold}")
out.close()
print("ok")
