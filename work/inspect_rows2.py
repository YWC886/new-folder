# -*- coding: utf-8 -*-
import sys, io, re
from docx import Document
from docx.oxml.ns import qn

path = sys.argv[1]
out = io.open(sys.argv[2], 'w', encoding='utf-8')
w = lambda *a: print(*a, file=out)
doc = Document(path)

def tini(s):
    return re.sub(r' xmlns:[a-zA-Z0-9]+="[^"]*"', '', s)

w("=== COVER P9..P19 runs (compact) ===")
for i in range(9, 20):
    p = doc.paragraphs[i]
    w(f"P{i} text={p.text!r} style={p.style.name} align={p.alignment}")
    pPr = p._p.find(qn('w:pPr'))
    if pPr is not None:
        w("  pPr:", tini(pPr.xml if hasattr(pPr, 'xml') else ''))
    for ri, r in enumerate(p.runs):
        rPr = r._r.find(qn('w:rPr'))
        w(f"  run{ri} {r.text!r} sz={r.font.size} bold={r.font.bold} u={r.font.underline} name={r.font.name}")
        if rPr is not None:
            w("    rPr:", tini(rPr.xml))

t = doc.tables[0]
def uniq_cells(row):
    res = []
    for c in row.cells:
        if all(c._tc is not x._tc for x in res):
            res.append(c)
    return res

w("\n=== ROWS 0-3,10,11,22-27 cells ===")
for ri in (0, 1, 2, 3, 10, 11, 22, 23, 24, 25, 26, 27):
    row = t.rows[ri]
    w(f"row{ri}:")
    for k, c in enumerate(uniq_cells(row)):
        w(f"  cell{k}:")
        for pi, p in enumerate(c.paragraphs):
            w(f"    para{pi}: {p.text!r} style={p.style.name} align={p.alignment}")
            pPr = p._p.find(qn('w:pPr'))
            if pPr is not None:
                w("      pPr:", tini(pPr.xml))
            for r in p.runs:
                w(f"      run {r.text!r} sz={r.font.size} bold={r.font.bold} name={r.font.name}")
out.close()
print('ok')
