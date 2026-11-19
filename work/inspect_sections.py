# -*- coding: utf-8 -*-
import sys, io, re
from docx import Document
from docx.oxml.ns import qn

path = sys.argv[1]
out = io.open(sys.argv[2], 'w', encoding='utf-8')
w = lambda *a: print(*a, file=out)
doc = Document(path)
t = doc.tables[0]

def uniq_cells(row):
    res = []
    for c in row.cells:
        if all(c._tc is not x._tc for x in res):
            res.append(c)
    return res

def tini(s):
    return re.sub(r' xmlns:[a-zA-Z0-9]+="[^"]*"', '', s)

w("=== SECTIONS 12-21, 28 paragraphs ===")
for ri in list(range(12, 22)) + [28]:
    row = t.rows[ri]
    cells = uniq_cells(row)
    w(f"--- row{ri} (uniq cells={len(cells)}) ---")
    for k, c in enumerate(cells):
        for pi, p in enumerate(c.paragraphs):
            w(f"  cell{k} para{pi}: {p.text!r} align={p.alignment}")
w("\n=== row heights (trHeight) ===")
for ri, row in enumerate(t.rows):
    tr = row._tr
    trPr = tr.find(qn('w:trPr'))
    h = None
    if trPr is not None:
        he = trPr.find(qn('w:trHeight'))
        if he is not None:
            h = (he.get(qn('w:val')), he.get(qn('w:hRule')))
    w(f"row{ri}: height={h}")
out.close()
print('ok')
