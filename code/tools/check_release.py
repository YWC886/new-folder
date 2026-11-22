# -*- coding: utf-8 -*-
"""提交前一致性检查（release preflight）。

检查三件事：
1. 六套测试是否全部通过（复用 `run_all_tests`）；
2. 复现包清单 `data/processed/release_manifest_v0.1.csv` 是否与工作区一致（存在性 + SHA256）；
3. 软著源代码页清单 `docs/softcopyright/build/源代码清单_V1.0.json` 是否仍与代码一致
   （文件集合、行数、SHA256 新鲜度）。

用法：
    py -3.12 code\\tools\\check_release.py
    py -3.12 code\\tools\\check_release.py --skip-tests --json
退出码：0 = 全部检查通过；1 = 有失败项；2 = 参数/路径错误。
"""
from __future__ import annotations

import sys as _sys

for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import run_all_tests as rat  # noqa: E402
import source_pages as sp  # noqa: E402

DEFAULT_MANIFEST = Path("data/processed/release_manifest_v0.1.csv")
DEFAULT_BUILD_DIR = Path("docs/softcopyright/build")
SOURCE_MANIFEST_NAME = "源代码清单_V1.0.json"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_sha256_of(path: Path) -> str:
    """与 `source_pages.SourceFile.sha256` 一致的规范哈希（按行以 \\n 连接）。"""
    data = "\n".join(path.read_text(encoding="utf-8").splitlines()).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_manifest(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"清单不存在：{path}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def verify_manifest(root: Path, rows: list[dict[str, str]]) -> dict[str, object]:
    missing: list[str] = []
    mismatch: list[str] = []
    for row in rows:
        path = root / row["rel_path"]
        if not path.is_file():
            missing.append(row["rel_path"])
        elif sha256_of(path) != row["sha256"]:
            mismatch.append(row["rel_path"])
    return {
        "ok": bool(rows) and not missing and not mismatch,
        "files": len(rows),
        "missing": missing,
        "mismatch": mismatch,
    }


def check_source_pages(root: Path, build_dir: Path) -> dict[str, object]:
    manifest_path = build_dir / SOURCE_MANIFEST_NAME
    if not manifest_path.is_file():
        return {"ok": False, "error": f"源代码清单不存在（先运行 source_pages.py）：{manifest_path}"}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = data.get("files", [])
    stale: list[str] = []
    for entry in entries:
        path = root / entry["rel_path"]
        if not path.is_file() or source_sha256_of(path) != entry["sha256"]:
            stale.append(entry["rel_path"])
    try:
        dirs = tuple(name for name in sp.SOURCE_DIRS if (root / "code" / name).is_dir())
        current = sp.collect_sources(root, dirs=dirs) if dirs else []
    except (FileNotFoundError, ValueError):
        current = []
    current_paths = {item.rel_path for item in current}
    listed_paths = {entry["rel_path"] for entry in entries}
    return {
        "ok": bool(entries) and not stale and current_paths == listed_paths,
        "files": len(entries),
        "lines": data.get("total_lines"),
        "pages": data.get("total_pages"),
        "stale": stale,
        "extra_in_code": sorted(current_paths - listed_paths),
        "missing_in_code": sorted(listed_paths - current_paths),
    }


def check_tests(root: Path, pattern: str = "test_*.py") -> dict[str, object]:
    dirs = rat.discover_dirs(root)
    total = 0
    failed: list[str] = []
    for directory in dirs:
        result = rat.run_dir(directory, pattern)
        total += result.testsRun
        if not (result.wasSuccessful() and result.testsRun > 0):
            failed.append(directory.name)
    return {"ok": not failed and total > 0, "total": total, "dirs": len(dirs), "failed": failed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="提交前一致性检查（测试 + 清单 + 源代码页）")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试（只查清单/源代码页）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 汇总")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    report: dict[str, object] = {}

    if args.skip_tests:
        report["tests"] = {"ok": True, "skipped": True}
    else:
        report["tests"] = check_tests(root)
        print(f"[{'OK' if report['tests']['ok'] else 'FAIL'}] 测试：{report['tests']['total']} 项，失败套件 {report['tests']['failed']}")

    manifest_path = (root / args.manifest) if not args.manifest.is_absolute() else args.manifest
    try:
        rows = load_manifest(manifest_path)
        report["manifest"] = verify_manifest(root, rows)
        print(
            f"[{'OK' if report['manifest']['ok'] else 'FAIL'}] 复现包清单：{report['manifest']['files']} 文件，"
            f"缺失 {len(report['manifest']['missing'])}，SHA 不一致 {len(report['manifest']['mismatch'])}"
        )
    except FileNotFoundError as exc:
        report["manifest"] = {"ok": False, "error": str(exc)}
        print(f"[FAIL] 复现包清单：{exc}")

    build_dir = (root / args.build_dir) if not args.build_dir.is_absolute() else args.build_dir
    report["source_pages"] = check_source_pages(root, build_dir)
    sp_report = report["source_pages"]
    if "error" in sp_report:
        print(f"[FAIL] 源代码页：{sp_report['error']}")
    else:
        print(
            f"[{'OK' if sp_report['ok'] else 'FAIL'}] 源代码页：{sp_report['files']} 文件 / "
            f"{sp_report['lines']} 行 / {sp_report['pages']} 页，过期 {len(sp_report['stale'])}，"
            f"代码有而清单无 {len(sp_report['extra_in_code'])}"
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    all_ok = all(bool(report[key].get("ok")) for key in report)
    print(f"\n结论：{'全部通过' if all_ok else '存在失败项'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
