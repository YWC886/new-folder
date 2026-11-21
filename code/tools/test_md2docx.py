"""md2docx 测试（4 项）。"""

from __future__ import annotations

import base64
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import md2docx  # noqa: E402

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class ConvertTests(unittest.TestCase):
    def test_headings_table_list(self) -> None:
        from docx import Document

        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "a.md"
            md.write_text(
                "# 标题\n\n## 小节\n\n普通段落 **加粗** 与 `代码`。\n\n- 列表一\n- 列表二\n\n"
                "| 列A | 列B |\n|---|---|\n| 1 | 2 |\n",
                encoding="utf-8",
            )
            out = md2docx.convert(md, Path(tmp) / "a.docx")
            doc = Document(out)
            texts = [p.text for p in doc.paragraphs]
            self.assertIn("标题", texts)
            self.assertIn("小节", texts)
            self.assertTrue(any("普通段落" in t for t in texts))
            self.assertEqual(len(doc.tables), 1)
            self.assertEqual(doc.tables[0].cell(1, 1).text, "2")

    def test_image_embedding(self) -> None:
        from docx import Document

        with tempfile.TemporaryDirectory() as tmp:
            fig = Path(tmp) / "fig.png"
            fig.write_bytes(PNG_1PX)
            md = Path(tmp) / "b.md"
            md.write_text("# 图测试\n\n![图 1 示例](fig.png)\n", encoding="utf-8")
            md2docx.convert(md, Path(tmp) / "b.docx")
            doc = Document(Path(tmp) / "b.docx")
            self.assertEqual(len(doc.inline_shapes), 1)
            self.assertTrue(any("图 1 示例" in p.text for p in doc.paragraphs))

    def test_overwrite_protection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "c.md"
            md.write_text("# t\n", encoding="utf-8")
            out = Path(tmp) / "c.docx"
            md2docx.convert(md, out)
            with self.assertRaises(FileExistsError):
                md2docx.convert(md, out)
            md2docx.convert(md, out, overwrite=True)

    def test_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "d.md"
            md.write_text("# t\n\n正文\n", encoding="utf-8")
            out = Path(tmp) / "d.docx"
            self.assertEqual(md2docx.main(["--input", str(md), "--output", str(out)]), 0)
            self.assertTrue(out.exists())
            self.assertEqual(md2docx.main(["--input", str(Path(tmp) / "no.md"), "--output", str(out)]), 2)


if __name__ == "__main__":
    unittest.main()
