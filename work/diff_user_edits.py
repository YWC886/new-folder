# -*- coding: utf-8 -*-
"""对照 proposal_content.py，检查用户手动修改过的 docx 有哪些改动。"""
import sys, difflib
sys.path.insert(0, r'D:\下载\创新\work')
import docx
import proposal_content as C

PATH = r'D:\下载\创新\附件3：大学生创新创业训练计划项目申报表（创新训练项目）_已填写.docx'
doc = docx.Document(PATH)
T = doc.tables[0]


def uniq(row):
    out = []
    for c in row.cells:
        if all(c._tc is not x._tc for x in out):
            out.append(c)
    return out


print('===== 封面 P0-P20 =====')
for i, p in enumerate(doc.paragraphs[:21]):
    print(i, repr(p.text))

print('\n===== row0-3 / row10 / row11 / row23-27 =====')
for ri in (0, 1, 2, 3, 10, 11, 23, 24, 25, 26, 27):
    cells = uniq(T.rows[ri])
    print('row', ri, [c.text[:200] for c in cells] if len(cells) < 6 else [c.text[:120] for c in cells])

print('\n===== 申请人/团队 row4-9 =====')
for ri in range(4, 10):
    print('row', ri, [c.text for c in uniq(T.rows[ri])])

print('\n===== 各栏 diff（用户改动） =====')
ROW = {'一': 12, '二': 13, '三': 14, '四': 15, '五': 16,
       '六': 17, '七': 18, '八': 19, '九': 20, '十一': 28}
for key, items in C.SECTIONS.items():
    cell = uniq(T.rows[ROW[key]])[0]
    cur = [p.text for p in cell.paragraphs]
    # 跳过模板标题段（八为2段）
    skip = 2 if key == '八' else 1
    cur = cur[skip:]
    exp = []
    for kind, val in items:
        if kind == 'refs':
            exp.extend(val)
        else:
            exp.append(val)
    # 去掉末尾空段
    cur = [t for t in cur]
    while cur and cur[-1].strip() == '':
        cur.pop()
    if cur != exp:
        print(f'--- 栏 {key}: 现有 {len(cur)} 段 / 原稿 {len(exp)} 段 ---')
        for line in difflib.unified_diff(exp, cur, fromfile='原稿', tofile='当前', lineterm='', n=0):
            print(line)
    else:
        print(f'--- 栏 {key}: 未改动 ---')
