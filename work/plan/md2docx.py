# -*- coding: utf-8 -*-
"""把规划用的 Markdown 转成中文排版规范的 docx（标题/正文/表格/图片/代码块）。

用法：
    python md2docx.py <input.md> <output.docx> [--title "文档标题"]
"""
import os
import re
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

PAGE_WIDTH = 21.0 - 2.4 - 2.2   # cm，A4 减去左右边距

BODY_FONT_EA = '宋体'
HEAD_FONT_EA = '微软雅黑'
LATIN_FONT = 'Times New Roman'
BODY_SIZE = 11.0     # pt
TABLE_SIZE = 9.0
CODE_SIZE = 9.0


def set_cn_font(run, ea=BODY_FONT_EA, latin=LATIN_FONT, size=BODY_SIZE,
                bold=None, color=None):
    run.font.size = Pt(size)
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rpr.insert(0, rf)
    rf.set(qn('w:ascii'), latin)
    rf.set(qn('w:hAnsi'), latin)
    rf.set(qn('w:eastAsia'), ea)
    rf.set(qn('w:cs'), latin)
    rf.set(qn('w:hint'), 'eastAsia')
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


INLINE_RE = re.compile(r'(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))')


def add_inline(par, text, size=BODY_SIZE, ea=BODY_FONT_EA, bold=False):
    for piece in INLINE_RE.split(text):
        if not piece:
            continue
        if piece.startswith('**') and piece.endswith('**'):
            run = par.add_run(piece[2:-2])
            set_cn_font(run, ea=ea, size=size, bold=True)
        elif piece.startswith('`') and piece.endswith('`'):
            run = par.add_run(piece[1:-1])
            set_cn_font(run, ea='Consolas', latin='Consolas', size=size)
        elif piece.startswith('[') and '](' in piece:
            label = piece[1:piece.index(']')]
            url = piece[piece.index('](') + 2:-1]
            run = par.add_run(label)
            set_cn_font(run, ea=ea, size=size, bold=bold)
            run2 = par.add_run(f'（{url}）')
            set_cn_font(run2, ea=ea, size=size - 0.5, color=(0x33, 0x66, 0x99))
        else:
            run = par.add_run(piece)
            set_cn_font(run, ea=ea, size=size, bold=bold)


def setup_page(doc):
    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.4)
    sec.bottom_margin = Cm(2.2)
    sec.left_margin = Cm(2.4)
    sec.right_margin = Cm(2.2)


def body_par_format(par, space_before=0, space_after=3, line=1.4, indent=None):
    pf = par.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if indent is not None:
        pf.first_line_indent = Pt(indent)


def add_heading(doc, text, level):
    par = doc.add_paragraph()
    if level == 1:
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        body_par_format(par, 6, 10, 1.3)
        add_inline(par, text, size=20, ea=HEAD_FONT_EA, bold=True)
    elif level == 2:
        body_par_format(par, 10, 5, 1.3)
        add_inline(par, text, size=14, ea=HEAD_FONT_EA, bold=True)
    elif level == 3:
        body_par_format(par, 6, 3, 1.3)
        add_inline(par, text, size=12, ea=HEAD_FONT_EA, bold=True)
    else:
        body_par_format(par, 4, 2, 1.3)
        add_inline(par, text, size=11, ea=HEAD_FONT_EA, bold=True)
    return par


def add_bullet(doc, text, ordered=False, level=0):
    par = doc.add_paragraph()
    body_par_format(par, 0, 2, 1.35)
    par.paragraph_format.left_indent = Cm(0.75 + 0.6 * level)
    par.paragraph_format.first_line_indent = Cm(-0.45)
    prefix = '- ' if not ordered else ''
    add_inline(par, prefix + text)
    return par


def add_code(doc, lines):
    par = doc.add_paragraph()
    body_par_format(par, 2, 2, 1.1)
    par.paragraph_format.left_indent = Cm(0.5)
    run = par.add_run('\n'.join(lines))
    set_cn_font(run, ea='Consolas', latin='Consolas', size=CODE_SIZE)
    shade = OxmlElement('w:shd')
    shade.set(qn('w:val'), 'clear')
    shade.set(qn('w:color'), 'F2F2F2')
    shade.set(qn('w:fill'), 'F2F2F2')
    par._p.get_or_add_pPr().append(shade)


def add_table(doc, rows):
    if not rows:
        return
    ncol = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=ncol)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for i, row in enumerate(rows):
        for j in range(ncol):
            cell = table.cell(i, j)
            text = row[j] if j < len(row) else ''
            par = cell.paragraphs[0]
            body_par_format(par, 0, 0, 1.15)
            if i == 0:
                par.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_inline(par, text, size=TABLE_SIZE, bold=True)
            else:
                add_inline(par, text, size=TABLE_SIZE)
    # 表头底色
    for j in range(ncol):
        tcPr = table.cell(0, j)._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'D9E2F3')
        shd.set(qn('w:fill'), 'D9E2F3')
        tcPr.append(shd)
    doc.add_paragraph()


def split_table_row(line):
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c.strip() for c in s.split('|')]


def is_table_sep(line):
    s = line.strip().strip('|')
    return bool(re.fullmatch(r'[\s:\-|]+', s)) and '-' in s


def convert(md_path, docx_path, title=None):
    with open(md_path, encoding='utf-8') as f:
        lines = f.read().splitlines()

    doc = Document()
    setup_page(doc)
    # 默认正文样式
    normal = doc.styles['Normal']
    normal.font.name = LATIN_FONT
    normal.font.size = Pt(BODY_SIZE)
    normal.element.rPr.rFonts.set(qn('w:eastAsia'), BODY_FONT_EA)

    i = 0
    first_h1 = True
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # 代码块
        if stripped.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i])
                i += 1
            i += 1
            add_code(doc, code)
            continue

        # 图片
        m = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', stripped)
        if m:
            alt, src = m.group(1), m.group(2)
            src = src.replace('\\', '/')
            if not os.path.isabs(src):
                src = os.path.normpath(os.path.join(os.path.dirname(md_path), src))
            if os.path.exists(src):
                par = doc.add_paragraph()
                par.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = par.add_run()
                run.add_picture(src, width=Cm(min(PAGE_WIDTH - 0.5, 15.2)))
                cap = doc.add_paragraph()
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                body_par_format(cap, 0, 6, 1.2)
                add_inline(cap, alt, size=9)
            i += 1
            continue

        # 表格
        if stripped.startswith('|') and '|' in stripped:
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                if not is_table_sep(lines[i]):
                    rows.append(split_table_row(lines[i]))
                i += 1
            if rows:
                add_table(doc, rows)
            continue

        # 标题
        m = re.match(r'^(#{1,4})\s+(.*)$', stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1 and first_h1 and title:
                text = title
                first_h1 = False
            add_heading(doc, text, level)
            i += 1
            continue

        # 分隔线
        if re.fullmatch(r'-{3,}|\*{3,}', stripped):
            par = doc.add_paragraph()
            body_par_format(par, 4, 4, 1.0)
            run = par.add_run()
            pPr = par._p.get_or_add_pPr()
            pbdr = OxmlElement('w:pBdr')
            bottom = OxmlElement('w:bottom')
            bottom.set(qn('w:val'), 'single')
            bottom.set(qn('w:sz'), '6')
            bottom.set(qn('w:space'), '1')
            bottom.set(qn('w:color'), '999999')
            pbdr.append(bottom)
            pPr.append(pbdr)
            i += 1
            continue

        # 引用块
        if stripped.startswith('>'):
            text = stripped[1:].strip()
            par = doc.add_paragraph()
            body_par_format(par, 0, 2, 1.35, indent=None)
            par.paragraph_format.left_indent = Cm(0.6)
            add_inline(par, text, size=BODY_SIZE - 0.5)
            i += 1
            continue

        # 列表
        m = re.match(r'^(\s*)[-*+]\s+(.*)$', line)
        if m:
            level = len(m.group(1)) // 2
            add_bullet(doc, m.group(2).strip(), ordered=False, level=level)
            i += 1
            continue
        m = re.match(r'^(\s*)(\d+)[.、)]\s+(.*)$', line)
        if m:
            level = len(m.group(1)) // 2
            add_bullet(doc, f'{m.group(2)}. {m.group(3).strip()}', ordered=True, level=level)
            i += 1
            continue

        # 普通段落（支持软换行合并）
        par = doc.add_paragraph()
        body_par_format(par, 0, 3, 1.45, indent=24)  # 首行缩进 2 字符
        par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_inline(par, stripped)
        i += 1

    doc.save(docx_path)
    print('saved:', docx_path)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    md_path, docx_path = argv[1], argv[2]
    title = argv[3] if len(argv) > 3 else None
    convert(md_path, docx_path, title)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
