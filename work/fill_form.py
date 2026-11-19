# -*- coding: utf-8 -*-
"""把 proposal_content_v2.py（按 2026 级大一新生条件改写）的内容写入大创申报表模板，输出“已填写”docx。

留空项（需用户本人提供）：项目负责人、团队成员（姓名/学号/学院/电话）、
申报日期、十一栏签名与日期。模板本身不作原地修改。
"""
import os
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

WORK = r'D:\下载\创新'
sys.path.insert(0, os.path.join(WORK, 'work'))
import proposal_content_v2 as C  # noqa: E402

SRC = os.path.join(WORK, '附件3：大学生创新创业训练计划项目申报表（创新训练项目）.docx')
DST = os.path.join(WORK, '附件3：大学生创新创业训练计划项目申报表（创新训练项目）_已填写_大一新生版.docx')

BODY = 12.0   # 小四
REF = 10.5    # 五号
LINE = 1.5    # 1.5 倍行距

doc = Document(SRC)
T = doc.tables[0]

# 正文各栏内容较长：解除 11-20 行的“行内禁止跨页”限制，让内容连续排版，
# 避免每栏另起一页造成的整页空白（预算表、导师意见等短行保留 cantSplit）
for _ri in range(11, 21):
    _trPr = T.rows[_ri]._tr.trPr
    if _trPr is not None:
        for _cs in _trPr.findall(qn('w:cantSplit')):
            _trPr.remove(_cs)


# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------
def set_run_font(r, size, bold=False, ea='宋体', latin='Times New Roman'):
    """统一设置中西文字体、字号、加粗。"""
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.name = latin
    rPr = r._r.get_or_add_rPr()
    rf = rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rPr.insert(0, rf)
    rf.set(qn('w:ascii'), latin)
    rf.set(qn('w:hAnsi'), latin)
    rf.set(qn('w:eastAsia'), ea)
    rf.set(qn('w:cs'), latin)
    rf.set(qn('w:hint'), 'eastAsia')
    szcs = rPr.find(qn('w:szCs'))
    if szcs is None:
        szcs = OxmlElement('w:szCs')
        rPr.append(szcs)
    szcs.set(qn('w:val'), str(int(round(size * 2))))


def clear_runs(p):
    for r in list(p.runs):
        r._r.getparent().remove(r._r)


def set_ind(p, first_chars=0, size=BODY):
    """设置首行缩进（字符数），并清除模板残留的左右/悬挂缩进。"""
    pf = p.paragraph_format
    pf.first_line_indent = Pt(size * first_chars / 100.0)
    ind = p._p.get_or_add_pPr().get_or_add_ind()
    for a in ('left', 'leftChars', 'hanging', 'hangingChars', 'start', 'startChars', 'end', 'endChars'):
        if ind.get(qn('w:' + a)) is not None:
            del ind.attrib[qn('w:' + a)]
    if first_chars:
        ind.set(qn('w:firstLineChars'), str(first_chars))
    else:
        pf.left_indent = Pt(0)


def uniq_cells(row):
    out = []
    for c in row.cells:
        if all(c._tc is not x._tc for x in out):
            out.append(c)
    return out


def row_cells(ri):
    return uniq_cells(T.rows[ri])


def set_cell_par(cell, text, size=BODY, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER,
                 first_chars=0, line=LINE):
    """覆盖单元格第一个段落的内容，删除多余空段。"""
    p = cell.paragraphs[0]
    clear_runs(p)
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = line
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    set_ind(p, first_chars, size)
    r = p.add_run(text)
    set_run_font(r, size, bold)
    for extra in list(cell.paragraphs[1:]):
        extra._p.getparent().remove(extra._p)


def new_par_after(anchor_el, text, size=BODY, bold=False, first_chars=200,
                  line=LINE, align=WD_ALIGN_PARAGRAPH.JUSTIFY, before=0.0,
                  keep_next=False):
    """在 anchor_el 后插入一个新段落，返回新段落的 XML 元素（供继续插入）。"""
    p = doc.add_paragraph()
    anchor_el.addnext(p._p)          # 从文档尾部移动到目标位置
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = line
    pf.space_before = Pt(before)
    pf.space_after = Pt(0)
    pf.keep_with_next = keep_next
    set_ind(p, first_chars, size)
    r = p.add_run(text)
    set_run_font(r, size, bold)
    return p._p


# --------------------------------------------------------------------------
# 1. 表头信息
# --------------------------------------------------------------------------
set_cell_par(row_cells(0)[1], C.PROJECT_NAME)                       # 项目名称
set_cell_par(row_cells(1)[1], C.PROJECT_TYPE_CELL)                  # 项目类型（勾选创新训练项目）
set_cell_par(row_cells(2)[1], C.RED_TRAVEL_CELL)                    # 青年红色筑梦之旅
set_cell_par(row_cells(3)[1], C.PROJECT_PERIOD_CELL)                # 项目实施时间

rc10 = row_cells(10)                                                # 指导教师：姓名 / 研究方向
set_cell_par(rc10[2], C.ADVISOR)
set_cell_par(rc10[4], C.ADVISOR_RESEARCH)

rc11 = row_cells(11)                                                # 主要成果
set_cell_par(rc11[2], C.ADVISOR_ACHIEVEMENTS, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             first_chars=200, line=LINE)

# --------------------------------------------------------------------------
# 2. 封面
# --------------------------------------------------------------------------
paras = doc.paragraphs
P9 = paras[9]       # 项 目 名 称：
P12 = paras[12]     # 指 导 教 师：

# 清空 P9 的下划线空格，项目名称另起一行（名称过长，放不进下划线空格）
for r in P9.runs:
    if r.text.strip() == '' and len(r.text) >= 3:
        r.text = ''

# P12 下划线空格内填写导师姓名（保留 run 的下划线格式）
for r in P12.runs:
    if r.text.strip() == '' and len(r.text) >= 3:
        r.text = C.ADVISOR
        break

p = doc.add_paragraph()
P9._p.addnext(p._p)
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
pf = p.paragraph_format
pf.line_spacing = 1.4
pf.space_before = Pt(0)
pf.space_after = Pt(0)
set_ind(p, 0, 16)
r = p.add_run(C.PROJECT_NAME)
set_run_font(r, 16, True)

# --------------------------------------------------------------------------
# 3. 正文各栏（插在栏目标题段之后）
# --------------------------------------------------------------------------
ROW = {'一': 12, '二': 13, '三': 14, '四': 15, '五': 16,
       '六': 17, '七': 18, '八': 19, '九': 20, '十一': 28}

for key, items in C.SECTIONS.items():
    paras_in_cell = row_cells(ROW[key])[0].paragraphs
    anchor = paras_in_cell[1] if key == '八' else paras_in_cell[0]
    cur = anchor._p
    for kind, val in items:
        if kind == 'refs':
            for ref in val:
                cur = new_par_after(cur, ref, size=REF, bold=False, first_chars=0,
                                    line=1.25, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        elif kind == 'h':
            cur = new_par_after(cur, val, size=BODY, bold=True, first_chars=200,
                                line=LINE, before=3, keep_next=True)
        else:
            cur = new_par_after(cur, val, size=BODY, bold=False, first_chars=200,
                                line=LINE)

# 清理各栏末尾残留的模板占位空段（如“五”栏标题后的空段），“十一”栏签名区不受影响
for key in C.SECTIONS:
    cell = row_cells(ROW[key])[0]
    while len(cell.paragraphs) > 2 and cell.paragraphs[-1].text.strip() == '':
        last = cell.paragraphs[-1]
        last._p.getparent().remove(last._p)

# --------------------------------------------------------------------------
# 4. 经费预算表
# --------------------------------------------------------------------------
for i, (item, amount, usage) in enumerate(C.BUDGET_ROWS):
    cells = row_cells(23 + i)
    set_cell_par(cells[0], item, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell_par(cells[1], amount, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell_par(cells[2], usage, align=WD_ALIGN_PARAGRAPH.LEFT)

cells27 = row_cells(27)
set_cell_par(cells27[1], '10000 元', align=WD_ALIGN_PARAGRAPH.RIGHT)

# 清理模板作者元数据（原模板作者为学校老师），标题改为项目名称
cp = doc.core_properties
cp.author = ''
cp.last_modified_by = ''
cp.title = C.PROJECT_NAME
cp.subject = '大学生创新创业训练计划项目申报表（创新训练项目）'
cp.comments = ''

doc.save(DST)
print('saved:', DST)
