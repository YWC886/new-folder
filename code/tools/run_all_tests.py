# -*- coding: utf-8 -*-
"""一键运行全部子项目测试（六套合跑），以退出码表示成败。

用法：
    py -3.12 code\\tools\\run_all_tests.py
    py -3.12 code\\tools\\run_all_tests.py --root D:\\下载\\创新 --pattern "test_*.py"
"""
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIRS = ("acquisition", "processing", "simulation", "selection", "reference", "tools")


def discover_dirs(root: Path, dirs: tuple[str, ...] = DEFAULT_DIRS) -> list[Path]:
    """返回 root/code 下存在且需要运行的测试目录。"""
    code_dir = root / "code"
    found = [code_dir / name for name in dirs if (code_dir / name).is_dir()]
    if not found:
        raise FileNotFoundError(f"未找到任何测试目录：{code_dir}")
    return found


def run_dir(directory: Path, pattern: str = "test_*.py") -> unittest.TestResult:
    """运行一个目录下的测试，返回 TestResult。"""
    loader = unittest.TestLoader()
    suite = loader.discover(str(directory), pattern=pattern)
    runner = unittest.TextTestRunner(verbosity=1, stream=sys.stderr)
    return runner.run(suite)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="一键运行全部子项目测试（六套合跑）")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="项目根目录")
    parser.add_argument("--pattern", default="test_*.py", help="测试文件匹配模式")
    args = parser.parse_args(argv)

    try:
        dirs = discover_dirs(args.root)
    except FileNotFoundError as exc:
        print(f"错误：{exc}")
        return 2

    total = 0
    failed_dirs: list[str] = []
    for directory in dirs:
        result = run_dir(directory, args.pattern)
        total += result.testsRun
        ok = result.wasSuccessful() and result.testsRun > 0
        if not ok:
            failed_dirs.append(directory.name)
        print(f"[{'OK' if ok else 'FAIL'}] {directory.name}: {result.testsRun} tests")

    print()
    print(f"总计：{total} 项测试；{len(dirs) - len(failed_dirs)}/{len(dirs)} 套通过")
    if failed_dirs:
        print("失败套件：" + "、".join(failed_dirs))
    return 0 if not failed_dirs and total > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
