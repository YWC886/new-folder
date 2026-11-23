"""结题材料包核对：按总目录检查交付物存在性与大小，生成清单 CSV。

v0.1（2026-11-21）：只读检查，不修改任何文件。
用法：py -3.12 code/tools/release_package.py [--output data/exports/结题材料包清单_20261121.csv] [--overwrite]
退出码：0 全部存在；1 有缺失；2 用法错误。
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path("data/exports/结题材料包清单_20261121.csv")

CATEGORIES = {
    "申报": [
        "docs/申报/README.md",
        "docs/申报/申报表/申报表-修改版.docx",
        "docs/申报/申报表/申报表-修改版_v3草稿.docx",
        "docs/申报/申报表/申报表-修改版_v3草稿_改动说明.md",
        "docs/申报/附件/01_项目前期基础与预研摘要.pdf",
        "docs/申报/附件/02_团队分工与实施计划.pdf",
        "docs/申报/附件/03_指导教师简介与指导条件.pdf",
        "docs/申报/附件/04_已有成果佐证.pdf",
        "docs/申报/经费预算_5000元_v0.1.md",
    ],
    "规划过程": [
        "docs/规划/申报书对比分析与优化研究路径_v0.1.docx",
        "docs/规划/结题材料总目录_v0.1.md",
        "docs/规划/答辩PPT大纲_v0.1.md",
        "docs/规划/答辩PPT骨架_v0.1.pptx",
        "docs/plan/阶段总结_StageSummary_r40.md",
        "docs/plan/阶段总结_StageSummary_r50.md",
        "docs/plan/项目待办与决策清单_TODOandDecisions_v0.1.md",
        "docs/team/task_division_3person_v0.1.md",
    ],
    "软件数据": [
        "code/acquisition/README.md",
        "code/processing/README.md",
        "code/simulation/README.md",
        "code/selection/README.md",
        "code/reference/README.md",
        "code/tools/README.md",
        "data/processed/efficiency_map_runs.csv",
        "data/processed/design_matrix_v0.2_demo.csv",
        "data/exports/项目成果总览_20261121.xlsx",
        "data/exports/项目成果报告_20261121.docx",
        "data/processed/release_manifest_v0.1.csv",
    ],
    "论文成果": [
        "docs/research/paper_method_draft_v0.1.docx",
        "docs/research/paper_method_draft_v0.1.md",
        "docs/research/literature_review_v0.1.md",
        "docs/research/references.csv",
        "docs/test/试验执行SOP_v0.1.docx",
        "docs/test/试验执行SOP_一页版_v0.1.docx",
        "docs/softcopyright/软件说明书_V1.0.md",
        "docs/softcopyright/复现包清单_V1.0.md",
        "docs/softcopyright/build/源代码页_V1.0.txt",
    ],
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="结题材料包核对（只读）")
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT))
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args(argv)
    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out

    rows = []
    missing = 0
    for cat, paths in CATEGORIES.items():
        for rel in paths:
            p = ROOT / rel
            ok = p.is_file()
            size = p.stat().st_size if ok else 0
            if not ok:
                missing += 1
            rows.append({"category": cat, "rel_path": rel, "exists": "Y" if ok else "N", "size_bytes": size})

    if out.exists() and not args.overwrite:
        print(f"错误：输出文件已存在（用 --overwrite 覆盖）：{out}")
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["category", "rel_path", "exists", "size_bytes"])
        w.writeheader()
        w.writerows(rows)

    total = len(rows)
    print(f"结题材料包：{total} 项，存在 {total - missing} 项，缺失 {missing} 项")
    for r in rows:
        if r["exists"] == "N":
            print(f"  [缺失] {r['category']} :: {r['rel_path']}")
    print(f"清单：{out}")
    print("注意：本清单只核对存在性/大小，内容真实性以各文件与 README 为准。")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
