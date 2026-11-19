# -*- coding: utf-8 -*-
"""校验生成的“已填写”docx：结构、内容、字数、留空项。"""
import io
import zipfile

from docx import Document

DST = r'D:\下载\创新\附件3：大学生创新创业训练计划项目申报表（创新训练项目）_已填写_大一新生版.docx'
OUT = r'D:\下载\创新\work\verify_report.txt'
out = io.open(OUT, 'w', encoding='utf-8')


def W(*a):
    print(*a, file=out)


W('== zip integrity ==')
z = zipfile.ZipFile(DST)
W('testzip:', z.testzip())

doc = Document(DST)
T = doc.tables[0]


def uniq(row):
    res = []
    for c in row.cells:
        if all(c._tc is not x._tc for x in res):
            res.append(c)
    return res


W('\n== cover paragraphs P0-P20 ==')
for i, p in enumerate(doc.paragraphs[:21]):
    W(i, repr(p.text), '|', p.alignment, '|', p.style.name)

W('\n== header rows 0-3 / 10 / 22-27 ==')
for ri in (0, 1, 2, 3, 10, 22, 23, 24, 25, 26, 27):
    row = T.rows[ri]
    W('row%d:' % ri, ' | '.join(repr(c.text) for c in uniq(row)))
rc11 = uniq(T.rows[11])
W('row11 cells:', len(rc11), '|', repr(rc11[2].text)[:120], '... len=', len(rc11[2].text))

W('\n== sections char count ==')
ROWS = {'一': 12, '二': 13, '三': 14, '四': 15, '五': 16, '六': 17, '七': 18, '八': 19, '九': 20, '十一': 28}
for key, ri in ROWS.items():
    cell = uniq(T.rows[ri])[0]
    texts = [p.text for p in cell.paragraphs]
    body = ''.join(texts[1:])
    W(key, 'paras=', len(texts), 'chars=', len(body), 'head=', repr(texts[0][:24]))
    W('   last=', repr(texts[-1][:50]))

W('\n== personal info blank check ==')
for ri in range(4, 10):
    row = T.rows[ri]
    W('row%d:' % ri, [repr(c.text) for c in uniq(row)])

W('\n== forbidden strings ==')
alltext = '\n'.join(p.text for p in doc.paragraphs)
for row in T.rows:
    for c in uniq(row):
        alltext += '\n' + c.text
for bad in ('待补充', '待调研', '待核实', 'TODO', 'xxx'):
    W(bad, '->', alltext.count(bad))

W('\n== overall ==')
W('total chars:', len(alltext))
W('paragraph count:', len(doc.paragraphs))
W('table rows:', len(T.rows))
out.close()
print('ok')
