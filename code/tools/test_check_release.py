# -*- coding: utf-8 -*-
"""`check_release` 提交前一致性检查测试。"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import check_release as cr  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def _manifest_row(root: Path, rel: str) -> dict[str, str]:
    return {
        "category": "docs",
        "rel_path": rel,
        "size_bytes": str((root / rel).stat().st_size),
        "sha256": cr.sha256_of(root / rel),
    }


def _build_source_manifest(root: Path, files: dict[str, str]) -> Path:
    """在 root/build 下生成源代码清单 JSON，并写入 files 对应的代码文件。"""
    entries = []
    for rel, content in files.items():
        path = root / rel
        _write(path, content)
        entries.append(
            {
                "rel_path": rel,
                "lines": len(content.splitlines()),
                "sha256": cr.source_sha256_of(path),
            }
        )
    data = {
        "software_name": "X",
        "version": "V1.0",
        "files": entries,
        "total_files": len(entries),
        "total_lines": sum(item["lines"] for item in entries),
        "total_pages": 1,
    }
    build = root / "build"
    _write(build / cr.SOURCE_MANIFEST_NAME, json.dumps(data))
    return build


class ManifestTests(unittest.TestCase):
    def test_manifest_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "a.md", "# a\n")
            _write(root / "code" / "x.py", "print(1)\n")
            rows = [_manifest_row(root, "a.md"), _manifest_row(root, "code/x.py")]
            report = cr.verify_manifest(root, rows)
        self.assertTrue(report["ok"])
        self.assertEqual(report["files"], 2)

    def test_manifest_detects_missing_and_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "a.md", "# a\n")
            rows = [_manifest_row(root, "a.md")]
            (root / "a.md").write_text("# changed\n", encoding="utf-8")
            report = cr.verify_manifest(root, rows)
            self.assertFalse(report["ok"])
            self.assertEqual(report["mismatch"], ["a.md"])
            rows2 = [dict(rows[0], rel_path="gone.md")]
            report2 = cr.verify_manifest(root, rows2)
        self.assertFalse(report2["ok"])
        self.assertEqual(report2["missing"], ["gone.md"])


class SourcePagesTests(unittest.TestCase):
    def test_source_pages_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = _build_source_manifest(
                root,
                {
                    "code/acquisition/a.py": "print(1)\n",
                    "code/processing/b.py": "print(2)\n",
                },
            )
            report = cr.check_source_pages(root, build)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["files"], 2)
        self.assertEqual(report["stale"], [])

    def test_source_pages_stale_and_extra(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            build = _build_source_manifest(root, {"code/acquisition/a.py": "print(1)\n"})
            (root / "code" / "acquisition" / "a.py").write_text("print(99)\n", encoding="utf-8")
            _write(root / "code" / "processing" / "new.py", "print(3)\n")
            report = cr.check_source_pages(root, build)
            self.assertFalse(report["ok"])
            self.assertIn("code/acquisition/a.py", report["stale"])
            self.assertIn("code/processing/new.py", report["extra_in_code"])
        self.assertEqual(report["missing_in_code"], [])

    def test_source_pages_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = cr.check_source_pages(Path(tmp), Path(tmp) / "build")
        self.assertFalse(report["ok"])
        self.assertIn("error", report)


class CliTests(unittest.TestCase):
    def _root(self, tmp: str) -> tuple[Path, Path, Path]:
        root = Path(tmp)
        build = _build_source_manifest(root, {"code/acquisition/a.py": "print(1)\n"})
        _write(root / "a.md", "# a\n")
        return root, build, root / "manifest.csv"

    def _write_manifest(self, path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["category", "rel_path", "size_bytes", "sha256"])
            writer.writeheader()
            writer.writerows(rows)

    def test_skip_tests_reports_manifest_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, build, manifest = self._root(tmp)
            self._write_manifest(manifest, [dict(_manifest_row(root, "a.md"), rel_path="missing.md")])
            code = cr.main(
                ["--root", str(root), "--manifest", str(manifest), "--build-dir", str(build), "--skip-tests"]
            )
        self.assertEqual(code, 1)

    def test_skip_tests_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, build, manifest = self._root(tmp)
            self._write_manifest(manifest, [_manifest_row(root, "a.md")])
            code = cr.main(
                ["--root", str(root), "--manifest", str(manifest), "--build-dir", str(build), "--skip-tests"]
            )
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
