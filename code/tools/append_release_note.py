"""在 Word 成果报告末尾追加「结题材料包核对」小节（v0.1，幂等：已有则跳过）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "pylibs"))
from docx import Document  # noqa: E402

DOCX = ROOT / "data" / "exports" / "项目成果报告_20261121.docx"
HEADING = "结题材料包核对（37 项）"


def main() -> int:
    if not DOCX.is_file():
        print(f"错误：报告不存在：{DOCX}")
        return 2
    doc = Document(str(DOCX))
    if any(p.text.strip().startswith(HEADING) for p in doc.paragraphs):
        print("已存在该小节，跳过")
        return 0
    doc.add_heading(HEADING, level=1)
    doc.add_paragraph(
        "依据 docs/规划/结题材料总目录_v0.1.md，对申报材料、规划过程、软件数据、论文成果四类共 37 项"
        "交付物做存在性与文件大小核对：全部存在、缺失 0。清单见 data/exports/结题材料包清单_20261121.csv"
        "（并已同步到工作簿 sheet「11_结题材料包清单」）。"
    )
    doc.add_paragraph(
        "注意：该核对只证明文件在位与可复现，不证明实验结论；所有 SIM/REFERENCE/PLANNING 结果仍需按"
        "数据边界声明使用，实测结论待 M0.4 采集链路与砝码标定完成后替换。"
    )
    doc.save(str(DOCX))
    print(f"已追加小节 → {DOCX}（段落 {len(doc.paragraphs)}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
