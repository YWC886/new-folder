# -*- coding: utf-8 -*-
import sys, re
sys.path.insert(0, r'D:\下载\创新\work\pylibs')
import docx

doc = docx.Document(r'D:\下载\创新\附件3：大学生创新创业训练计划项目申报表（创新训练项目）.docx')
t = doc.tables[0]
for i, row in enumerate(t.rows):
    trPr = row._tr.trPr
    xml = trPr.xml if trPr is not None else ''
    cant = 'cantSplit' in xml
    m = re.search(r'w:trHeight w:val="(\d+)"', xml)
    print(i, 'cantSplit=', cant, 'h=', m.group(1) if m else None)
