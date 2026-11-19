"""`code/reference` 测试（解析器 + 对标 + 产物）。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, PROJECT_ROOT / "code" / "simulation"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import benchmark_uiuc as bench  # noqa: E402
import catalog_uiuc as catalog  # noqa: E402
import propulsion_model as pm  # noqa: E402
import uiuc_propdb  # noqa: E402

SAMPLE = PROJECT_ROOT / "data" / "reference" / "uiuc" / "apce_10x7_static_pg0811.txt"


class ParserTests(unittest.TestCase):
    def test_load_mirrored_sample(self) -> None:
        rows = uiuc_propdb.load_static(SAMPLE)
        self.assertEqual(len(rows), 16)
        self.assertAlmostEqual(rows[0]["rpm"], 1975.0)
        self.assertAlmostEqual(rows[0]["n_rps"], 1975.0 / 60.0)
        self.assertAlmostEqual(rows[-1]["rpm"], 6542.0)
        self.assertTrue(all(r["ct"] > 0 and r["cp"] > 0 for r in rows))

    def test_load_with_comments_and_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text(
                "# comment line\n\nRPM    CT    CP\n1000  0.10  0.05\n\n1200  0.11  0.051\n",
                encoding="utf-8",
            )
            rows = uiuc_propdb.load_static(path)
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(rows[1]["cp"], 0.051)

    def test_missing_header_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.txt"
            path.write_text("1000 0.10 0.05\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                uiuc_propdb.load_static(path)

    def test_non_numeric_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.txt"
            path.write_text("RPM CT CP\n1000 abc 0.05\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                uiuc_propdb.load_static(path)

    def test_summarize(self) -> None:
        rows = uiuc_propdb.load_static(SAMPLE)
        stats = uiuc_propdb.summarize(rows)
        self.assertEqual(stats["points"], 16)
        self.assertAlmostEqual(stats["rpm_min"], 1975.0)
        self.assertAlmostEqual(stats["rpm_max"], 6542.0)


class BenchmarkTests(unittest.TestCase):
    def test_model_coefficients_follow_model_formula(self) -> None:
        model = pm.ModelParams()
        coeffs = bench.model_coefficients(model, [6000.0])
        n = 6000.0 / 60.0
        ratio = n / model.n_ref_rev_s
        self.assertAlmostEqual(coeffs[0]["ct_model"], model.ct0 * ratio**model.reynolds_ct_exp)
        self.assertAlmostEqual(coeffs[0]["cp_model"], model.cp0 * ratio**model.reynolds_cp_exp)

    def test_benchmark_stats_reasonable(self) -> None:
        rows = uiuc_propdb.load_static(SAMPLE)
        result = bench.benchmark(rows)
        stats = result["stats"]
        self.assertEqual(stats["points"], len(rows))
        # 通用参数先验：C_T 均值误差应为个位数百分比量级，C_P 明显被低估（约 10–20%）
        self.assertGreater(stats["ct_mean_abs_rel_err"], 0.02)
        self.assertLess(stats["ct_mean_abs_rel_err"], 0.15)
        self.assertGreater(stats["cp_mean_abs_rel_err"], 0.08)
        self.assertLess(stats["cp_mean_abs_rel_err"], 0.25)
        for row in result["rows"]:
            self.assertAlmostEqual(row["ct_rel_err"], (row["ct_model"] - row["ct_ref"]) / row["ct_ref"])
            self.assertAlmostEqual(row["cp_rel_err"], (row["cp_model"] - row["cp_ref"]) / row["cp_ref"])
            self.assertIn("UIUC", row["data_note"])
            self.assertIn("不构成实验验证", row["data_note"])

    def test_write_csv_and_overwrite_protection(self) -> None:
        rows = uiuc_propdb.load_static(SAMPLE)
        result = bench.benchmark(rows)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bench.csv"
            bench.write_csv(result["rows"], out)
            text = out.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(",".join(bench.FIELDS)))
            self.assertEqual(len(text.strip().splitlines()), len(rows) + 1)
            with self.assertRaises(FileExistsError):
                bench.write_csv(result["rows"], out)

    def test_plot_outputs_png(self) -> None:
        rows = uiuc_propdb.load_static(SAMPLE)
        result = bench.benchmark(rows)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bench.png"
            bench.plot_comparison(result["rows"], out)
            self.assertGreater(out.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                bench.plot_comparison(result["rows"], out)


class PropLabelTests(unittest.TestCase):
    """文件名 → 桨标签解析（v0.2 新增）。"""

    def test_parse_default_catalog_names(self) -> None:
        expected = {
            "apce_11x7_static_kt0534.txt": ("apce_11x7", "APC-E", 11.0, 7.0),
            "apce_11x8_static_kt0517.txt": ("apce_11x8", "APC-E", 11.0, 8.0),
            "apcsf_10x7_static_kt0827.txt": ("apcsf_10x7", "APC-SF", 10.0, 7.0),
            "apcsp_9x6_static_2532rd.txt": ("apcsp_9x6", "APC-Sport", 9.0, 6.0),
            "grcp_10x6_static_rd0851.txt": ("grcp_10x6", "Graupner-CAM", 10.0, 6.0),
            "grsn_10x7_static_rd0787.txt": ("grsn_10x7", "Graupner-SN", 10.0, 7.0),
            "ance_8.5x6_static_2848cm.txt": ("ance_8.5x6", "Aeronaut-CE", 8.5, 6.0),
        }
        for name, (prop, brand_series, diameter_in, pitch_in) in expected.items():
            label = uiuc_propdb.parse_prop_label(name)
            self.assertEqual(label["file"], name)
            self.assertEqual(label["prop"], prop)
            self.assertEqual(label["brand_series"], brand_series)
            self.assertAlmostEqual(label["diameter_in"], diameter_in)
            self.assertAlmostEqual(label["pitch_in"], pitch_in)
            self.assertTrue(label["display"])
            self.assertIn(str(diameter_in).rstrip("0").rstrip("."), label["display"])

    def test_unknown_prefix_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            uiuc_propdb.parse_prop_label("foobar_10x6_static_abcd.txt")
        self.assertIn("未知品牌/系列前缀", str(ctx.exception))

    def test_malformed_name_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            uiuc_propdb.parse_prop_label("apce_10x6_prop.txt")
        self.assertIn("不符合 UIUC 静态数据命名", str(ctx.exception))


class CatalogTests(unittest.TestCase):
    """多桨型目录加载与汇总统计（v0.2 新增）。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.entries = catalog.load_catalog()
        cls.result = catalog.benchmark_catalog(cls.entries)

    def test_catalog_covers_multiple_props_and_brands(self) -> None:
        self.assertEqual(len(self.entries), 7)
        props = [entry["prop"] for entry in self.entries]
        self.assertEqual(len(set(props)), len(props))
        for entry in self.entries:
            self.assertEqual(len(entry["rows"]), 16)
            for key in ("brand", "series", "brand_series", "display"):
                self.assertTrue(entry[key], f"{entry['file']} 缺少 {key}")
        pooled = self.result["pooled"]
        self.assertEqual(pooled["props"], 7)
        self.assertEqual(pooled["points"], 112)
        self.assertEqual(pooled["brand_count"], 3)
        self.assertEqual(pooled["series_count"], 6)
        self.assertGreaterEqual(pooled["rpm_min"], 1600.0)
        self.assertLessEqual(pooled["rpm_max"], 6900.0)
        self.assertTrue(pooled["all_positive"])

    def test_per_prop_and_pooled_statistics_consistent(self) -> None:
        props = self.result["props"]
        point_rows = self.result["rows"]
        self.assertEqual(len(props), 7)
        by_prop: dict[str, list[dict]] = {}
        for row in point_rows:
            self.assertEqual(set(row), set(catalog.POINT_FIELDS))
            self.assertIn("UIUC", row["data_note"])
            self.assertIn("不构成实验验证", row["data_note"])
            by_prop.setdefault(row["prop"], []).append(row)
        for prop in props:
            self.assertEqual(set(prop), set(catalog.SUMMARY_FIELDS))
            rows = by_prop[prop["prop"]]
            self.assertEqual(len(rows), prop["points"])
            self.assertLessEqual(prop["ct_ref_min"], prop["ct_ref_mean"])
            self.assertLessEqual(prop["ct_ref_mean"], prop["ct_ref_max"])
            self.assertLessEqual(prop["cp_ref_min"], prop["cp_ref_mean"])
            self.assertLessEqual(prop["cp_ref_mean"], prop["cp_ref_max"])
            n = len(rows)
            ct_rels = [row["ct_rel_err"] for row in rows]
            cp_rels = [row["cp_rel_err"] for row in rows]
            self.assertAlmostEqual(prop["ct_rel_err_mean"], sum(ct_rels) / n, places=12)
            self.assertAlmostEqual(prop["cp_rel_err_mean"], sum(cp_rels) / n, places=12)
            self.assertAlmostEqual(
                prop["ct_rel_err_mean_abs"], sum(abs(v) for v in ct_rels) / n, places=12
            )
            self.assertAlmostEqual(
                prop["cp_rel_err_mean_abs"], sum(abs(v) for v in cp_rels) / n, places=12
            )
            self.assertAlmostEqual(
                prop["ct_rel_err_max_abs"], max(abs(v) for v in ct_rels), places=12
            )
            self.assertAlmostEqual(
                prop["cp_rel_err_max_abs"], max(abs(v) for v in cp_rels), places=12
            )
        pooled = self.result["pooled"]
        self.assertEqual(pooled["points"], sum(prop["points"] for prop in props))
        self.assertEqual(
            pooled["ct_underestimated_props"],
            sum(1 for prop in props if prop["ct_rel_err_mean"] < 0),
        )
        self.assertEqual(
            pooled["cp_underestimated_props"],
            sum(1 for prop in props if prop["cp_rel_err_mean"] < 0),
        )
        self.assertAlmostEqual(
            pooled["ct_rel_err_mean_abs"],
            sum(abs(row["ct_rel_err"]) for row in point_rows) / len(point_rows),
            places=12,
        )
        # 通用参数先验的量级：CT 约 10% 量级、CP 更大（宽区间，避免参数微调即碎）
        self.assertGreater(pooled["ct_rel_err_mean_abs"], 0.05)
        self.assertLess(pooled["ct_rel_err_mean_abs"], 0.20)
        self.assertGreater(pooled["cp_rel_err_mean_abs"], 0.10)
        self.assertLess(pooled["cp_rel_err_mean_abs"], 0.25)
        # 跨桨系统性偏差：CP 被低估的桨型不少于 CT（通用 cp0 只接近部分细薄桨）
        self.assertGreaterEqual(
            pooled["cp_underestimated_props"], pooled["ct_underestimated_props"]
        )

    def test_duplicate_prop_rejected(self) -> None:
        source = catalog.REFERENCE_DIR / "apce_11x7_static_kt0534.txt"
        text = source.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            names = ["apce_11x7_static_kt0534.txt", "apce_11x7_static_zzzz.txt"]
            for name in names:
                (Path(tmp) / name).write_text(text, encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                catalog.load_catalog(reference_dir=tmp, filenames=names)
        self.assertIn("重复", str(ctx.exception))


class CatalogOutputTests(unittest.TestCase):
    """v0.2 CSV / PNG 产物与覆盖保护。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = catalog.benchmark_catalog(catalog.load_catalog())

    def test_point_and_summary_csv_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            point_csv = Path(tmp) / "points.csv"
            summary_csv = Path(tmp) / "summary.csv"
            catalog.write_point_csv(self.result["rows"], point_csv)
            catalog.write_summary_csv(self.result["props"], summary_csv)
            point_lines = point_csv.read_text(encoding="utf-8").strip().splitlines()
            summary_lines = summary_csv.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(point_lines[0], ",".join(catalog.POINT_FIELDS))
            self.assertEqual(len(point_lines), 112 + 1)
            self.assertEqual(summary_lines[0], ",".join(catalog.SUMMARY_FIELDS))
            self.assertEqual(len(summary_lines), 7 + 1)
            with self.assertRaises(FileExistsError):
                catalog.write_point_csv(self.result["rows"], point_csv)
            with self.assertRaises(FileExistsError):
                catalog.write_summary_csv(self.result["props"], summary_csv)

    def test_figure_output_and_overwrite_protection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "catalog.png"
            catalog.plot_catalog(self.result, png)
            self.assertGreater(png.stat().st_size, 30_000)
            with self.assertRaises(FileExistsError):
                catalog.plot_catalog(self.result, png)
            catalog.plot_catalog(self.result, png, overwrite=True)
            self.assertGreater(png.stat().st_size, 30_000)

    def test_main_reports_missing_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = catalog.main(
                ["--reference-dir", tmp, "--files", "missing.txt", "--output", "x.csv"]
            )
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
