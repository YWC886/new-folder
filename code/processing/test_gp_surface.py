"""`code/processing/gp_surface.py` 测试：GP 平滑、LOOCV、网格输出与图件。"""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, PROJECT_ROOT / "work" / "pylibs"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np  # noqa: E402

import gp_surface as gp  # noqa: E402


def toy_rows() -> list[dict]:
    rows: list[dict] = []
    voltages = (12.0, 16.0, 20.0, 24.0)
    throttles = (25.0, 50.0, 75.0, 100.0)
    for voltage in voltages:
        for throttle in throttles:
            eta = 0.55 - 0.35 * ((voltage - 18.0) / 12.0) ** 2 - 0.25 * ((throttle - 62.5) / 37.5) ** 2
            rows.append(
                {
                    "voltage_set_v": voltage,
                    "throttle_set_pct": throttle,
                    "eta_sys": eta,
                    "run_id": f"toy_{voltage:g}_{throttle:g}",
                    "source": "SIM",
                }
            )
    return rows


def write_runs_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("run_id", "source", "voltage_set_v", "throttle_set_pct", "eta_sys"))
        writer.writeheader()
        writer.writerows(rows)


class LoadRunsTests(unittest.TestCase):
    def test_load_and_features(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runs.csv"
            write_runs_csv(path, toy_rows())
            runs = gp.load_runs(path)
            features = gp.features_of(runs)
        self.assertEqual(len(runs), 16)
        self.assertEqual(features.shape, (16, 2))
        self.assertAlmostEqual(features[0][0], 12.0 / gp.VOLTAGE_SCALE)
        self.assertAlmostEqual(features[0][1], 25.0 / gp.THROTTLE_SCALE)
        self.assertEqual(runs[0]["source"], "SIM")

    def test_load_aggregate_style_eta_sys_mean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runs.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=("run_id", "source", "voltage_set_v", "throttle_set_pct", "eta_sys_mean"),
                )
                writer.writeheader()
                for row in toy_rows():
                    writer.writerow(
                        {
                            "run_id": row["run_id"],
                            "source": row["source"],
                            "voltage_set_v": row["voltage_set_v"],
                            "throttle_set_pct": row["throttle_set_pct"],
                            "eta_sys_mean": row["eta_sys"],
                        }
                    )
            runs = gp.load_runs(path)
        self.assertEqual(len(runs), 16)
        self.assertAlmostEqual(runs[0]["eta_sys"], toy_rows()[0]["eta_sys"])

    def test_missing_column_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("voltage_set_v,throttle_set_pct\n22.2,50\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                gp.load_runs(path)

    def test_too_few_points_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "few.csv"
            write_runs_csv(path, toy_rows()[:2])
            with self.assertRaises(ValueError):
                gp.load_runs(path)

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            gp.load_runs(Path("/nonexistent/runs.csv"))


class GPFitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runs = toy_rows()
        self.x = gp.features_of(self.runs)
        self.y = np.asarray([row["eta_sys"] for row in self.runs], dtype=float)

    def test_interpolates_training_points(self) -> None:
        fit = gp.GPFit(self.x, self.y, length_scale=0.3, noise_var=1e-10)
        mean, _ = fit.predict(self.x)
        self.assertLess(float(np.max(np.abs(mean - self.y))), 1e-4)

    def test_choose_length_scale_and_metrics(self) -> None:
        result = gp.choose_length_scale(self.x, self.y)
        self.assertIn(result["length_scale"], gp.LENGTH_SCALES)
        self.assertGreaterEqual(result["n"], 16)
        self.assertLess(result["loocv_rmse"], 0.02)
        self.assertGreater(result["r2"], 0.98)
        # 确定性：再次调用结果一致
        again = gp.choose_length_scale(self.x, self.y)
        self.assertEqual(result["length_scale"], again["length_scale"])
        self.assertAlmostEqual(result["loocv_rmse"], again["loocv_rmse"])

    def test_loocv_close_to_training_values(self) -> None:
        fit = gp.GPFit(self.x, self.y, length_scale=0.3)
        loo_mean, loo_var = fit.loocv()
        self.assertEqual(loo_mean.shape, self.y.shape)
        self.assertTrue(np.all(loo_var > 0))
        self.assertLess(float(np.sqrt(np.mean((self.y - loo_mean) ** 2))), 0.02)

    def test_invalid_length_scale_raises(self) -> None:
        with self.assertRaises(ValueError):
            gp.rbf_kernel(self.x, self.x, length_scale=0.0)
        with self.assertRaises(ValueError):
            gp.regression_metrics(np.zeros(3), np.zeros(4))

    def test_predict_grid_shape(self) -> None:
        fit = gp.GPFit(self.x, self.y, length_scale=0.3)
        rows = gp.predict_grid(fit, [12.0, 18.0], [25.0, 50.0, 75.0])
        self.assertEqual(len(rows), 6)
        self.assertEqual(tuple(rows[0].keys()), gp.GRID_FIELDS)
        self.assertTrue(all(row["eta_std"] > 0 for row in rows))
        self.assertIn("不是实验结果", rows[0]["data_note"])

    def test_write_csv_and_overwrite(self) -> None:
        fit = gp.GPFit(self.x, self.y, length_scale=0.3)
        rows = gp.predict_grid(fit, [12.0, 18.0], [25.0, 50.0])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "grid.csv"
            gp.write_csv(rows, out)
            text = out.read_text(encoding="utf-8")
            self.assertEqual(len(text.strip().splitlines()), len(rows) + 1)
            self.assertIn("eta_pred", text.splitlines()[0])
            with self.assertRaises(FileExistsError):
                gp.write_csv(rows, out)
            gp.write_csv(rows, out, overwrite=True)

    def test_plot_surface_outputs_png(self) -> None:
        fit = gp.GPFit(self.x, self.y, length_scale=0.3)
        rows = gp.predict_grid(fit, list(range(12, 25)), list(range(25, 101, 25)))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "surface.png"
            gp.plot_surface(self.runs, rows, out)
            self.assertGreater(out.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                gp.plot_surface(self.runs, rows, out)
            gp.plot_surface(self.runs, rows, out, overwrite=True)


if __name__ == "__main__":
    unittest.main()
