"""`code/reference/calibrate_uiuc.py` 测试（REFERENCE-derived priors v0.3）。"""

from __future__ import annotations

import csv
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, PROJECT_ROOT / "code" / "simulation"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import calibrate_uiuc as cal  # noqa: E402

N_REF = 100.0


def write_static(path: Path, ct0: float, a_t: float, cp0: float, a_p: float) -> None:
    lines = ["RPM    CT    CP"]
    for rpm in range(1800, 6600, 300):  # 16 点
        n = rpm / 60.0
        ratio = n / N_REF
        lines.append(f"{rpm}    {ct0 * ratio**a_t:.6f}    {cp0 * ratio**a_p:.6f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_catalog(directory: Path) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    write_static(directory / "apce_10x6_static_t0001.txt", 0.105, -0.02, 0.047, -0.035)
    write_static(directory / "apcsf_11x5_static_t0002.txt", 0.135, 0.01, 0.062, -0.010)
    return ["apce_10x6_static_t0001.txt", "apcsf_11x5_static_t0002.txt"]


class FitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        names = make_catalog(self.dir)
        self.entries = cal.catalog.load_catalog(self.dir, names)
        self.result = cal.fit_catalog(self.entries)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_recovers_exact_coefficients(self) -> None:
        prop = self.result["props"][0]
        self.assertAlmostEqual(prop["ct0"], 0.105, places=5)
        self.assertAlmostEqual(prop["aT"], -0.02, delta=1e-4)
        self.assertAlmostEqual(prop["cp0"], 0.047, places=5)
        self.assertAlmostEqual(prop["aP"], -0.035, delta=1e-4)
        self.assertGreater(prop["ct_log_r2"], 0.9999)
        self.assertGreater(prop["cp_log_r2"], 0.9999)

    def test_after_error_much_smaller_than_generic(self) -> None:
        for prop in self.result["props"]:
            self.assertLess(prop["ct_err_abs_after"], 1e-3)
            self.assertLess(prop["cp_err_abs_after"], 1e-3)
            # 至少一个通道的通用先验误差显著非零（桨型参数与通用参数不同）
            self.assertGreater(max(prop["ct_err_abs_before"], prop["cp_err_abs_before"]), 0.01)

    def test_holdout_is_finite_and_small(self) -> None:
        for prop in self.result["props"]:
            self.assertIsNotNone(prop["ct_holdout_abs"])
            self.assertLess(prop["ct_holdout_abs"], 1e-2)
            self.assertLess(prop["cp_holdout_abs"], 1e-2)

    def test_pooled_included(self) -> None:
        pooled = self.result["pooled"]
        self.assertEqual(pooled["props"], 2)
        self.assertEqual(pooled["points"], 32)
        # pooled（跨桨单一先验）通常无法同时优于通用先验；这里只校验数值合理且 C_P 有改善
        self.assertLess(pooled["ct_err_abs_after"], 0.2)
        self.assertLess(pooled["cp_err_abs_after"], pooled["cp_err_abs_before"])

    def test_insufficient_points_raise(self) -> None:
        entry = {"prop": "x", "rows": [{"n_rps": 30.0, "ct": 0.1, "cp": 0.05}]}
        with self.assertRaises(ValueError):
            cal.fit_prop(entry)


class OutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        names = make_catalog(self.dir / "uiuc")
        entries = cal.catalog.load_catalog(self.dir / "uiuc", names)
        self.result = cal.fit_catalog(entries)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_csv_fields_and_overwrite(self) -> None:
        out = self.dir / "calib.csv"
        cal.write_calibration_csv(self.result["props"], out)
        with out.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 2)
        self.assertEqual(list(rows[0].keys()), cal.CALIBRATION_FIELDS)
        with self.assertRaises(FileExistsError):
            cal.write_calibration_csv(self.result["props"], out)

    def test_priors_json_flags(self) -> None:
        out = self.dir / "priors.json"
        priors = cal.build_priors(self.result)
        cal.write_priors_json(priors, out)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(loaded["schema_version"], "0.3")
        self.assertTrue(loaded["do_not_apply"])
        self.assertIn("不是本项目实测标定", loaded["disclaimer"])
        self.assertEqual(len(loaded["props"]), 2)
        with self.assertRaises(FileExistsError):
            cal.write_priors_json(priors, out)

    def test_plot_outputs_png(self) -> None:
        out = self.dir / "calib.png"
        cal.plot_calibration(self.result, out)
        self.assertGreater(out.stat().st_size, 10_000)
        with self.assertRaises(FileExistsError):
            cal.plot_calibration(self.result, out)


class CliTests(unittest.TestCase):
    def test_main_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            names = make_catalog(base / "uiuc")
            out = base / "calib.csv"
            priors = base / "priors.json"
            figure = base / "calib.png"
            argv = [
                "--reference-dir",
                str(base / "uiuc"),
                "--files",
                *names,
                "--output",
                str(out),
                "--priors",
                str(priors),
                "--figure",
                str(figure),
            ]
            self.assertEqual(cal.main(argv), 0)
            self.assertTrue(out.exists() and priors.exists() and figure.exists())
            # 已存在且未 --overwrite → exit 2
            self.assertEqual(cal.main(argv), 2)
            self.assertEqual(cal.main(argv + ["--overwrite"]), 0)

    def test_main_missing_reference_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            code = cal.main(
                [
                    "--reference-dir",
                    str(base / "nope"),
                    "--files",
                    "apce_10x6_static_t0001.txt",
                    "--output",
                    str(base / "o.csv"),
                    "--priors",
                    str(base / "p.json"),
                    "--figure",
                    str(base / "f.png"),
                ]
            )
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
