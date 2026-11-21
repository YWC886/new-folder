"""export_office 测试（5 项）。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import export_office as eo  # noqa: E402


class WorkbookTests(unittest.TestCase):
    def test_build_workbook_has_expected_sheets(self) -> None:
        from openpyxl import load_workbook

        with tempfile.TemporaryDirectory() as tmp:
            out = eo.build_workbook(Path(tmp) / "book.xlsx")
            wb = load_workbook(out)
            expected = {
                "00_说明",
                "01_效率地图_runs",
                "02_效率地图_grid",
                "03_GP平滑代理_v0.4",
                "04_选型Pareto_v0.4",
                "05_补测建议_v0.4",
                "06_UIUC逐桨对标",
                "07_逐桨先验_v0.3",
                "08_试验排程_v0.2",
                "09_测试与材料",
            }
            self.assertTrue(expected.issubset(set(wb.sheetnames)), wb.sheetnames)
            self.assertGreaterEqual(wb["01_效率地图_runs"].max_row, 3)
            header = [c.value for c in wb["01_效率地图_runs"][2]]
            self.assertIn("eta_sys_mean", header)

    def test_workbook_overwrite_protection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "book.xlsx"
            eo.build_workbook(out)
            with self.assertRaises(FileExistsError):
                eo.build_workbook(out)


class ReportTests(unittest.TestCase):
    def test_build_report_structure(self) -> None:
        from docx import Document

        with tempfile.TemporaryDirectory() as tmp:
            out = eo.build_report(Path(tmp) / "report.docx")
            doc = Document(out)
            text = "\n".join(p.text for p in doc.paragraphs)
            for keyword in ("数据边界声明", "项目成果概览", "效率地图", "选型匹配", "验证与复现", "下一步"):
                self.assertIn(keyword, text)
            self.assertGreaterEqual(len(doc.tables), 2)
            self.assertGreaterEqual(len(doc.inline_shapes), 3)
            self.assertTrue(out.stat().st_size > 100_000)

    def test_report_overwrite_protection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "report.docx"
            eo.build_report(out)
            with self.assertRaises(FileExistsError):
                eo.build_report(out)


class CliTests(unittest.TestCase):
    def test_main_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = eo.main(["--out-dir", tmp, "--workbook", "w.xlsx", "--report", "r.docx"])
            self.assertEqual(code, 0)
            self.assertTrue((Path(tmp) / "w.xlsx").exists())
            self.assertTrue((Path(tmp) / "r.docx").exists())
            again = eo.main(["--out-dir", tmp, "--workbook", "w.xlsx", "--report", "r.docx"])
            self.assertEqual(again, 2)


if __name__ == "__main__":
    unittest.main()
