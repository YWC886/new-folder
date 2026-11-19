"""`code/tools` 测试：软著源代码页生成器 + 复现包清单生成器。"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import build_manifest as bm  # noqa: E402
import source_pages as sp  # noqa: E402


class SourcePagesTests(unittest.TestCase):
    def _fake_tree(self, root: Path) -> None:
        for name, content in {
            "acquisition/a.py": "print('a')\n" * 30,
            "processing/b.py": "print('b')\n" * 40,
            "simulation/c.py": "print('c')\n" * 7,
        }.items():
            path = root / "code" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def test_collect_sources_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fake_tree(root)
            files = sp.collect_sources(root, dirs=("acquisition", "processing", "simulation"))
        self.assertEqual([f.rel_path for f in files], [f"code/{p}" for p in sorted(["acquisition/a.py", "processing/b.py", "simulation/c.py"])])

    def test_render_pages_pagination(self) -> None:
        files = [sp.SourceFile("a.py", tuple(f"line{i}" for i in range(1, 61)))]
        pages = sp.render_pages(files, lines_per_page=50, software_name="测试软件", version="V1.0")
        self.assertEqual(pages.total_files, 1)
        self.assertEqual(pages.total_lines, 60)
        self.assertEqual(pages.total_pages, 2)
        self.assertIn("第 1 页 / 共 2 页", pages.pages[0])
        self.assertIn("第 2 页 / 共 2 页", pages.pages[1])
        self.assertIn("000001", pages.pages[0])
        self.assertIn("line60", pages.pages[1])

    def test_render_pages_rejects_bad_input(self) -> None:
        with self.assertRaises(ValueError):
            sp.render_pages([], lines_per_page=50)
        with self.assertRaises(ValueError):
            sp.render_pages([sp.SourceFile("a.py", ("x",))], lines_per_page=5)

    def test_manifest_fields(self) -> None:
        files = [sp.SourceFile("a.py", ("print(1)", "print(2)"))]
        pages = sp.render_pages(files, lines_per_page=50)
        manifest = sp.to_manifest(pages, generated_at="2026-11-19T00:00:00+08:00")
        self.assertEqual(manifest["total_files"], 1)
        self.assertEqual(manifest["total_lines"], 2)
        self.assertEqual(manifest["total_pages"], 1)
        self.assertIn("前 30 页", manifest["note"])
        self.assertEqual(len(manifest["files"][0]["sha256"]), 64)

    def test_write_outputs_and_overwrite(self) -> None:
        files = [sp.SourceFile("a.py", ("print(1)",))]
        pages = sp.render_pages(files)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "build"
            outputs = sp.write_outputs(pages, out)
            self.assertTrue(Path(outputs["source_pages"]).exists())
            self.assertTrue(Path(outputs["manifest"]).exists())
            data = json.loads(Path(outputs["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(data["total_files"], 1)
            with self.assertRaises(FileExistsError):
                sp.write_outputs(pages, out)
            sp.write_outputs(pages, out, overwrite=True)

    def test_collect_real_repo(self) -> None:
        files = sp.collect_sources(PROJECT_ROOT)
        self.assertGreaterEqual(len(files), 10)
        self.assertTrue(any(f.rel_path.startswith("code/processing/") for f in files))


class ManifestTests(unittest.TestCase):
    def test_sha256_matches_hashlib(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.txt"
            payload = "内容 abc\n"
            path.write_bytes(payload.encode("utf-8"))
            expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            self.assertEqual(bm.sha256_of(path), expected)

    def test_collect_files_categories_and_exclusions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "code").mkdir()
            (root / "code" / "x.py").write_text("print(1)\n", encoding="utf-8")
            (root / "code" / "fig.png").write_bytes(b"png")
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("# doc\n", encoding="utf-8")
            (root / "README.md").write_text("# root\n", encoding="utf-8")
            rows = bm.collect_files(root)
        rels = {row["rel_path"] for row in rows}
        self.assertIn("code/x.py", rels)
        self.assertIn("docs/a.md", rels)
        self.assertIn("README.md", rels)
        self.assertNotIn("code/fig.png", rels)
        self.assertTrue(all(row["size_bytes"] > 0 for row in rows))
        self.assertTrue(all(len(row["sha256"]) == 64 for row in rows))

    def test_write_manifest_and_overwrite(self) -> None:
        rows = [{"category": "code", "rel_path": "code/x.py", "size_bytes": 8, "sha256": "0" * 64}]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "manifest.csv"
            bm.write_manifest(rows, out)
            text = out.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(",".join(bm.MANIFEST_FIELDS)))
            self.assertIn("code/x.py", text)
            with self.assertRaises(FileExistsError):
                bm.write_manifest(rows, out)

    def test_collect_real_repo(self) -> None:
        rows = bm.collect_files(PROJECT_ROOT)
        categories = {row["category"] for row in rows}
        self.assertIn("code", categories)
        self.assertIn("docs", categories)
        self.assertTrue(any(row["rel_path"].endswith(".py") for row in rows))
        self.assertFalse(any(row["rel_path"].startswith("work/") for row in rows))


if __name__ == "__main__":
    unittest.main()
