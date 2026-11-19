"""复现包清单生成器 v0.1：为交付文件生成 SHA256 清单 CSV。

用途：复现包/软著附件需要「文件—大小—SHA256」清单，便于校验完整性。
默认收录 code/、docs/、data/reference/、data/processed 中的小体量产物与
根目录说明文件；排除 work/pylibs、大体积 raw CSV 与二进制/Office 文件。

用法：
    py -3.12 code\\tools\\build_manifest.py --output data\\processed\\release_manifest_v0.1.csv --overwrite
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_FIELDS = ["category", "rel_path", "size_bytes", "sha256"]
EXCLUDED_SUFFIXES = {".png", ".docx", ".pdf", ".zip", ".pyc", ".xlsx", ".pptx"}
MAX_SIZE_BYTES = 2_000_000  # 单文件上限 2 MB（避免把大 CSV/图片塞进清单）


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root: Path | str = PROJECT_ROOT, *, max_size_bytes: int = MAX_SIZE_BYTES) -> list[dict]:
    """按类别收集复现包文件（相对路径、大小、SHA256）。"""
    root = Path(root)
    specs = [
        ("code", root / "code"),
        ("docs", root / "docs"),
        ("data_reference", root / "data" / "reference"),
        ("data_processed", root / "data" / "processed"),
        ("root", root),
    ]
    rows: list[dict] = []
    seen: set[Path] = set()
    for category, base in specs:
        if not base.exists():
            continue
        if category == "root":
            candidates = [p for p in base.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".txt"}]
        else:
            candidates = sorted(p for p in base.rglob("*") if p.is_file())
        for path in candidates:
            if path in seen or "__pycache__" in path.parts:
                continue
            if path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            if path.stat().st_size > max_size_bytes:
                continue
            seen.add(path)
            rows.append(
                {
                    "category": category,
                    "rel_path": path.relative_to(root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_of(path),
                }
            )
    rows.sort(key=lambda row: row["rel_path"])
    if not rows:
        raise ValueError("没有可收录的文件")
    return rows


def write_manifest(rows: list[dict], output: Path | str, *, overwrite: bool = False) -> Path:
    output = Path(output)
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{output}（加 --overwrite 覆盖）")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="复现包清单生成器（v0.1）")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output", type=Path, default=Path("data/processed/release_manifest_v0.1.csv"))
    parser.add_argument("--max-size", type=int, default=MAX_SIZE_BYTES)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        rows = collect_files(args.root, max_size_bytes=args.max_size)
        # 清单自身不计入（否则每次重跑文件数会漂移）
        output_rel = args.output.as_posix().lstrip("./")
        rows = [row for row in rows if row["rel_path"] != output_rel]
        output = write_manifest(rows, args.output, overwrite=args.overwrite)
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"错误：{exc}")
        return 2

    total = sum(row["size_bytes"] for row in rows)
    print(f"清单文件：{output}")
    print(f"收录 {len(rows)} 个文件，合计 {total / 1024:.1f} KiB")
    for category in sorted({row["category"] for row in rows}):
        subset = [row for row in rows if row["category"] == category]
        print(f"  {category}: {len(subset)} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
