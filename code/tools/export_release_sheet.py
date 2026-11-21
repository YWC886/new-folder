"""把结题材料包核对清单并入成果 Excel（追加/刷新「11_结题材料包清单」工作表）。

v0.1（2026-11-21）：读取 release_package.py 生成的 CSV，追加到现有工作簿；
不修改其他工作表；重复运行为刷新该页。
用法：py -3.12 code/tools/export_release_sheet.py [--workbook data/exports/项目成果总览_20261121.xlsx]
      [--csv data/exports/结题材料包清单_20261121.csv]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "pylibs"))
from openpyxl import load_workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402

SHEET = "11_结题材料包清单"
BANNER = "结题材料包核对（只读清单）：存在性/大小检查，内容真实性以各文件与 README 为准；非实验结果。"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workbook", default="data/exports/项目成果总览_20261121.xlsx")
    ap.add_argument("--csv", default="data/exports/结题材料包清单_20261121.csv")
    args = ap.parse_args(argv)
    wb_path = ROOT / args.workbook
    csv_path = ROOT / args.csv
    if not wb_path.is_file():
        print(f"错误：工作簿不存在：{wb_path}")
        return 2
    if not csv_path.is_file():
        print(f"错误：清单 CSV 不存在（先运行 release_package.py）：{csv_path}")
        return 2

    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    wb = load_workbook(wb_path)
    if SHEET in wb.sheetnames:
        del wb[SHEET]
    ws = wb.create_sheet(SHEET)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=4)
    c = ws.cell(row=1, column=1, value=BANNER)
    c.font = Font(bold=True, color="B00020")
    c.alignment = Alignment(wrap_text=True)
    ws.row_dimensions[1].height = 30
    header = ["类别", "相对路径", "存在", "大小(字节)"]
    for j, h in enumerate(header, 1):
        cell = ws.cell(row=3, column=j, value=h)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DDEBF7")
    for i, r in enumerate(rows, 4):
        ws.cell(row=i, column=1, value=r["category"])
        ws.cell(row=i, column=2, value=r["rel_path"])
        ws.cell(row=i, column=3, value=r["exists"])
        ws.cell(row=i, column=4, value=int(r["size_bytes"]))
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 70
    ws.column_dimensions["C"].width = 8
    ws.column_dimensions["D"].width = 14
    ws.freeze_panes = "A4"
    wb.save(wb_path)
    n_missing = sum(1 for r in rows if r["exists"] != "Y")
    print(f"已写入「{SHEET}」：{len(rows)} 项，缺失 {n_missing} 项 → {wb_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
