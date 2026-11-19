"""软著材料生成器 v0.1：把 `code/` 源码拼接为带页码的源代码页 + 清单 JSON。

用途：软件著作权登记通常要求提交源代码前/后各 30 页（每页 ≥50 行）。
本工具生成连续编写的「源代码页」文本与清单（文件、行数、页数、SHA256），
便于人工挑选前 30 页 + 后 30 页后打印/转 PDF。

用法：
    py -3.12 code\\tools\\source_pages.py --out-dir docs\\softcopyright\\build --overwrite
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIRS = ("acquisition", "processing", "simulation", "selection", "reference", "tools")
DEFAULT_NAME = "多旋翼动力系统效率地图构建与匹配优化软件"
DEFAULT_VERSION = "V1.0"
LINES_PER_PAGE = 50


@dataclass(frozen=True)
class SourceFile:
    rel_path: str
    lines: tuple[str, ...]

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def sha256(self) -> str:
        data = "\n".join(self.lines).encode("utf-8")
        return hashlib.sha256(data).hexdigest()


@dataclass
class SourcePages:
    software_name: str
    version: str
    lines_per_page: int
    files: list[SourceFile] = field(default_factory=list)
    pages: list[str] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def total_lines(self) -> int:
        return sum(f.line_count for f in self.files)

    @property
    def total_pages(self) -> int:
        return len(self.pages)


def collect_sources(root: Path | str = PROJECT_ROOT, dirs: tuple[str, ...] = SOURCE_DIRS) -> list[SourceFile]:
    """收集 code/<dir>/*.py 源文件，按路径排序；跳过 __pycache__。"""
    root = Path(root)
    files: list[SourceFile] = []
    for name in dirs:
        directory = root / "code" / name
        if not directory.is_dir():
            raise FileNotFoundError(f"源码目录不存在：{directory}")
        for path in sorted(directory.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8")
            files.append(SourceFile(rel_path=rel, lines=tuple(text.splitlines())))
    if not files:
        raise ValueError("未找到任何 .py 源文件")
    return files


def render_pages(
    files: list[SourceFile],
    *,
    software_name: str = DEFAULT_NAME,
    version: str = DEFAULT_VERSION,
    lines_per_page: int = LINES_PER_PAGE,
) -> SourcePages:
    """把源文件按连续行号切成每页 lines_per_page 行的源代码页。"""
    if lines_per_page < 10:
        raise ValueError("lines_per_page 必须 >= 10")
    if not files:
        raise ValueError("files 不能为空")

    result = SourcePages(software_name=software_name, version=version, lines_per_page=lines_per_page)
    # 先展平为 (文件, 行) 序列，再分页
    flat: list[tuple[str, int, str]] = []
    for source in files:
        result.files.append(source)
        for index, line in enumerate(source.lines, start=1):
            flat.append((source.rel_path, index, line))

    total_pages = (len(flat) + lines_per_page - 1) // lines_per_page
    for page_index in range(total_pages):
        chunk = flat[page_index * lines_per_page : (page_index + 1) * lines_per_page]
        body: list[str] = [
            f"软件名称：{software_name}    版本：{version}",
            f"第 {page_index + 1} 页 / 共 {total_pages} 页",
            "-" * 78,
        ]
        current_file = ""
        for display_no, (rel_path, line_no, line) in enumerate(chunk, start=page_index * lines_per_page + 1):
            if rel_path != current_file:
                body.append(f"/* ---- {rel_path} ---- */")
                current_file = rel_path
            body.append(f"{display_no:06d}  {line}")
        body.append("-" * 78)
        result.pages.append("\n".join(body))
    return result


def to_manifest(pages: SourcePages, *, generated_at: str | None = None) -> dict:
    return {
        "software_name": pages.software_name,
        "version": pages.version,
        "lines_per_page": pages.lines_per_page,
        "total_files": len(pages.files),
        "total_lines": pages.total_lines,
        "total_pages": pages.total_pages,
        "generated_at": generated_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        "files": [
            {"rel_path": f.rel_path, "lines": f.line_count, "sha256": f.sha256}
            for f in pages.files
        ],
        "note": "软著提交通常取前 30 页 + 后 30 页（不足 60 页交全部）；SIM/REFERENCE 数据不参与本清单",
    }


def write_outputs(pages: SourcePages, out_dir: Path | str, *, overwrite: bool = False) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    source_txt = out_dir / f"源代码页_{pages.version}.txt"
    manifest_json = out_dir / f"源代码清单_{pages.version}.json"
    software_txt = out_dir / f"源文件目录_{pages.version}.txt"

    for path in (source_txt, manifest_json, software_txt):
        if path.exists() and not overwrite:
            raise FileExistsError(f"输出已存在：{path}（加 --overwrite 覆盖）")

    source_txt.write_text(
        ("\n\n" + "=" * 78 + "\n").join(pages.pages) + "\n", encoding="utf-8"
    )
    manifest = to_manifest(pages)
    manifest_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    software_txt.write_text(
        "\n".join(f"{f.rel_path}  {f.line_count} 行  sha256={f.sha256[:12]}…" for f in pages.files) + "\n",
        encoding="utf-8",
    )
    return {
        "source_pages": source_txt,
        "manifest": manifest_json,
        "file_list": software_txt,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="软著源代码页生成器（v0.1）")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="仓库根目录")
    parser.add_argument("--out-dir", type=Path, default=Path("docs/softcopyright/build"))
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--lines-per-page", type=int, default=LINES_PER_PAGE)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        files = collect_sources(args.root)
        pages = render_pages(
            files,
            software_name=args.name,
            version=args.version,
            lines_per_page=args.lines_per_page,
        )
        outputs = write_outputs(pages, args.out_dir, overwrite=args.overwrite)
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"错误：{exc}")
        return 2

    print(f"软件：{pages.software_name} {pages.version}")
    print(f"源文件 {pages.total_files} 个，合计 {pages.total_lines} 行 → {pages.total_pages} 页（每页 {pages.lines_per_page} 行）")
    print(f"源代码页：{outputs['source_pages']}")
    print(f"清单 JSON：{outputs['manifest']}")
    print(f"文件目录：{outputs['file_list']}")
    print("提示：软著提交一般取前 30 页 + 后 30 页（总页数不足 60 页则交全部）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
