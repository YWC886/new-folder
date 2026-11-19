# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r'D:\下载\创新\work\pylibs')
import docx

doc = docx.Document(r'D:\下载\创新\附件3：大学生创新创业训练计划项目申报表（创新训练项目）_已填写.docx')
t = doc.tables[0]
for ri in (26, 27):
    row = t.rows[ri]
    print('== row', ri, 'uniq cells:', len(row.cells))
    seen = []
    for ci, c in enumerate(row.cells):
        if any(c._tc is s for s in seen):
            continue
        seen.append(c._tc)
        tcPr = c._tc.tcPr
        gs = None
        if tcPr is not None:
            g = tcPr.grid_span
            gs = g
        print(f'  cell {ci} texts={[p.text for p in c.paragraphs]} gridSpan={gs}')
        for p in c.paragraphs:
            print('    para align=', p.alignment, 'xml_ind=', p._p.pPr.xml[:300] if p._p.pPr is not None else None)
