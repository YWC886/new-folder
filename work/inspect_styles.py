# -*- coding: utf-8 -*-
"""Dump document defaults, styles, table properties, and page/section setup."""
import sys, io
from docx import Document
from docx.oxml.ns import qn

path = sys.argv[1]
out = io.open(sys.argv[2], 'w', encoding='utf-8')
def w(*a):
    print(*a, file=out)

doc = Document(path)

w("=== DOC DEFAULTS (w:docDefaults) ===")
styles_el = doc.styles.element
dd = styles_el.find(qn('w:docDefaults'))
if dd is not None:
    import lxml.etree as ET
    w(ET.tostring(dd, pretty_print=True, encoding='unicode'))

w("\n=== STYLE Normal ===")
import lxml.etree as ET
st = doc.styles['Normal']
w(ET.tostring(st.element, pretty_print=True, encoding='unicode'))

w("\n=== TABLE PROPERTIES ===")
t = doc.tables[0]
tbl = t._tbl
tblPr = tbl.find(qn('w:tblPr'))
w(ET.tostring(tblPr, pretty_print=True, encoding='unicode'))
w("\n=== GRID ===")
grid = tbl.find(qn('w:tblGrid'))
for gc in grid.findall(qn('w:gridCol')):
    w("gridCol", gc.get(qn('w:w')))

w("\n=== SECTPR ===")
sectPr = doc.sections[0]._sectPr
w(ET.tostring(sectPr, pretty_print=True, encoding='unicode'))

w("\n=== paragraph formats of a body cell (row12) ===")
c = t.rows[12].cells[0]
p = c.paragraphs[0]
w("pPr:", ET.tostring(p._p.find(qn('w:pPr')), pretty_print=True, encoding='unicode') if p._p.find(qn('w:pPr')) is not None else None)

w("\n=== content headings bold check / rPr ===")
for ri in range(12, 22):
    p = t.rows[ri].cells[0].paragraphs[0]
    w(f"row{ri}:", ET.tostring(p._p, pretty_print=True, encoding='unicode')[:1500])
out.close()
print("ok")
