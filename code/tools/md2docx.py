"""Markdown → Word（.docx）转换工具（v0.1，通用子集）。

支持：标题（# / ## / ###）、段落、无序/有序列表、引用块、表格、图片行
（`![说明](相对路径)`）、水平线；中文排版（微软雅黑、首行缩进）。
图片路径相对 Markdown 文件所在目录解析。

用法：
    py -3.12 code\\tools\\md2docx.py --input a.md --output a.docx [--title 标题] [--overwrite]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "work" / "pylibs"))

from docx import Document  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

BODY_FONT = "Microsoft YaHei"
MONO_FONT = "Consolas"


def _style_font(style, *, size_pt: float, bold: bool = False, color=None) -> None:
    style.font.name = BODY_FONT
    style.font.size = Pt(size_pt)
    style.font.bold = bold
    style._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    if color is not None:
        style.font.color.rgb = RGBColor(*color)


def _setup(document: Document) -> None:
    normal = document.styles["Normal"]
    _style_font(normal, size_pt=10.5)
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 1.35
    for name, size in (("Heading 1", 16), ("Heading 2", 13.5), ("Heading 3", 11.5)):
        style = document.styles[name]
        _style_font(style, size_pt=size, bold=True, color=(0x1F, 0x3B, 0x57))
        style.paragraph_format.space_before = Pt(10)
        style.paragraph_format.space_after = Pt(4)


def _add_rich(paragraph, text: str) -> None:
    """处理 **粗体** 与 `代码` 两种行内标记。"""
    parts = []
    buf = ""
    i = 0
    while i < len(text):
        if text.startswith("**", i):
            if buf:
                parts.append((buf, False, False))
                buf = ""
            j = text.find("**", i + 2)
            if j < 0:
                buf += text[i:]
                break
            parts.append((text[i + 2 : j], True, False))
            i = j + 2
            continue
        if text[i] == "`":
            if buf:
                parts.append((buf, False, False))
                buf = ""
            j = text.find("`", i + 1)
            if j < 0:
                buf += text[i:]
                break
            parts.append((text[i + 1 : j], False, True))
            i = j + 1
            continue
        buf += text[i]
        i += 1
    if buf:
        parts.append((buf, False, False))
    for chunk, bold, code in parts:
        run = paragraph.add_run(chunk)
        run.bold = bold
        if code:
            run.font.name = MONO_FONT
            run.font.size = Pt(9.5)


def _split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _is_table_sep(cells: list[str]) -> bool:
    return all(cell and set(cell) <= set("-: ") for cell in cells)


def convert(md_path: Path, output: Path, title: str | None = None, *, overwrite: bool = False) -> Path:
    if not md_path.is_file():
        raise FileNotFoundError(f"Markdown 文件不存在：{md_path}")
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output}（加 --overwrite 覆盖）")
    lines = md_path.read_text(encoding="utf-8").splitlines()
    doc = Document()
    _setup(doc)
    if title:
        doc.add_heading(title, level=0)

    i = 0
    n = len(lines)
    in_list = False
    while i < n:
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            in_list = False
            i += 1
            continue
        if stripped.startswith("<!--"):
            while i < n and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        if stripped.startswith("!["):
            # ![说明](路径)
            try:
                label = stripped[2 : stripped.index("]")]
                target = stripped[stripped.index("(") + 1 : stripped.index(")")]
            except ValueError:
                i += 1
                continue
            img = (md_path.parent / target).resolve()
            if img.is_file():
                doc.add_picture(str(img), width=Cm(15.0))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap = doc.add_paragraph(label)
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                cap.paragraph_format.space_before = Pt(2)
                for run in cap.runs:
                    run.font.size = Pt(9)
                    run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            i += 1
            continue
        if stripped.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(_split_table_row(lines[i]))
                i += 1
            rows = [r for r in rows if not _is_table_sep(r)]
            if rows:
                cols = max(len(r) for r in rows)
                table = doc.add_table(rows=len(rows), cols=cols)
                table.style = "Table Grid"
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                for r_idx, row in enumerate(rows):
                    for c_idx in range(cols):
                        cell = table.cell(r_idx, c_idx)
                        cell.text = ""
                        para = cell.paragraphs[0]
                        text = row[c_idx] if c_idx < len(row) else ""
                        _add_rich(para, text)
                        for run in para.runs:
                            run.font.size = Pt(9)
                            if r_idx == 0:
                                run.bold = True
            in_list = False
            continue
        if stripped.startswith("```"):
            block = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Cm(0.5)
            run = para.add_run("\n".join(block))
            run.font.name = MONO_FONT
            run.font.size = Pt(9)
            continue
        if stripped.startswith(">"):
            text = stripped.lstrip(">").strip()
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Cm(0.6)
            para.paragraph_format.space_after = Pt(4)
            _add_rich(para, text)
            for run in para.runs:
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
            for run in para.runs:
                run.italic = True
            i += 1
            continue
        if stripped.startswith("---") and set(stripped) <= set("-"):
            doc.add_paragraph("")
            i += 1
            continue
        heading = None
        for level, prefix in ((1, "### "), (0, "## "), (0, "# ")):
            if stripped.startswith(prefix):
                heading = (3 if level == 1 else (2 if prefix == "## " else 1), stripped[len(prefix):])
                break
        if heading:
            doc.add_heading(heading[1], level=heading[0])
            in_list = False
            i += 1
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            para = doc.add_paragraph(style="List Bullet")
            _add_rich(para, stripped[2:])
            in_list = True
            i += 1
            continue
        if stripped[:2].isdigit() and stripped[2:4] in (". ", ") "):
            para = doc.add_paragraph(style="List Number")
            _add_rich(para, stripped[3:].strip())
            in_list = True
            i += 1
            continue
        para = doc.add_paragraph()
        para.paragraph_format.first_line_indent = Cm(0.74)
        _add_rich(para, stripped)
        in_list = False
        i += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output))
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Markdown → Word（.docx）转换")
    parser.add_argument("--input", required=True, help="输入 .md 文件")
    parser.add_argument("--output", required=True, help="输出 .docx 文件")
    parser.add_argument("--title", default=None, help="可选：文档封面标题")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已存在的输出文件")
    args = parser.parse_args(argv)
    try:
        out = convert(Path(args.input), Path(args.output), title=args.title, overwrite=args.overwrite)
    except FileNotFoundError as exc:
        print(f"错误：{exc}")
        return 2
    except FileExistsError as exc:
        print(f"错误：{exc}")
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"转换失败：{exc}")
        return 1
    print(f"已生成：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
