# -*- coding: utf-8 -*-
import sys, io
sys.path.insert(0, r'D:\下载\创新\work\pylibs')
import lxml.etree as ET
from docx import Document
from docx.oxml.ns import qn

path = sys.argv[1]
out = io.open(sys.argv[2], 'w', encoding='utf-8')
w = lambda *a: print(*a, file=out)
doc = Document(path)

w("=== COVER PARAGRAPHS P9-P13 ===")
for i in range(9, 14):
    p = doc.paragraphs[i]
    w(f"P{i} text={p.text!r} align={p.alignment}")
    pPr = p._p.find(qn('w:pPr'))
    w(" pPr:", ET.tostring(pPr, pretty_print=True, encoding='unicode').replace(' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"', '') if pPr is not None else None)
    for ri, r in enumerate(p.runs):
        w(f"  run{ri} {r.text!r} sz={r.font.size} bold={r.font.bold} name={r.font.name}")
        rPr = r._r.find(qn('w:rPr'))
        if rPr is not None:
            w("   rPr:", ET.tostring(rPr, encoding='unicode').replace(' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"', ''))

t = doc.tables[0]
w("\n=== ROW1/ROW2/ROW3/ROW0 cells text/runs ===")
for ri in (0, 1, 2, 3):
    row = t.rows[ri]
    seen = []
    for ci, c in enumerate(row.cells):
        if all(c._tc is not x._tc for x in seen):
            seen.append(c)
    w(f"row{ri}:")
    for c in seen:
        for pi, p in enumerate(c.paragraphs):
            w(f"  cell para{pi}: {p.text!r} align={p.alignment}")
            for r in p.runs:
                w(f"    run {r.text!r} sz={r.font.size} bold={r.font.bold}")

w("\n=== ROW 10/11 cells ===")
for ri in (10, 11, 27):
    row = t.rows[ri]
    w(f"row{ri}:")
    seen = []
    for ci, c in enumerate(row.cells):
        if all(c._tc is not x._tc for x in seen):
            seen.append(c)
    for k, c in enumerate(seen):
        for pi, p in enumerate(c.paragraphs):
            w(f"  cell{k} para{pi}: {p.text!r} style={p.style.name} align={p.alignment}")
            pPr = p._p.find(qn('w:pPr'))
            if pPr is not None:
                w("     pPr:", ET.tostring(pPr, encoding='unicode').replace(' xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"', ''))
            for r in p.runs:
                w(f"     run {r.text!r} sz={r.font.size} bold={r.font.bold} name={r.font.name}")

w("\n=== HEADERS/FOOTERS ===")
for si, s in enumerate(doc.sections):
    for part_name in ('header', 'first_page_header', 'even_page_header', 'footer', 'first_page_footer'):
        try:
            part = getattr(s, part_name)
        except Exception:
            continue
        if part is None:
            continue
        txt = ' | '.join(p.text for p in part.paragraphs if p.text.strip())
        w(part_name, '=', repr(txt))
out.close()
print('ok')
