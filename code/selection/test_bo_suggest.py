"""`code/selection/bo_suggest.py` 测试（补测策略对比，Round 19）。"""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, PROJECT_ROOT / "code" / "processing"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np  # noqa: E402

import bo_suggest as bo  # noqa: E402
import gp_surface as gp  # noqa: E402
import match_propulsion as mp  # noqa: E402

VOLTAGES = (18.0, 24.0)
THROTTLES = (25.0, 50.0, 75.0, 100.0)


def toy_runs() -> list[dict]:
    runs = []
    for voltage in VOLTAGES:
        for throttle in THROTTLES:
            eta = 0.18 + 0.32 * (throttle / 100.0) - 0.03 * ((voltage - 21.0) / 5.0) ** 2
            runs.append(
                {
                    "run_id": f"toy_{voltage:g}_{throttle:g}",
                    "source": "SIM",
                    "combo": "TOY",
                    "voltage_set_v": voltage,
                    "throttle_set_pct": throttle,
                    "thrust_N_mean": 0.2 * voltage * throttle / 100.0,
                    "eta_sys_mean": eta,
                    "eta_em_mean": eta / 0.75,
                    "fm_mean": eta / 0.75,
                    "rpm_mean": 3000.0 + 30.0 * throttle,
                    "current_a_mean": 1.0 + 0.05 * throttle,
                    "u_eta_sys_k2": 0.02,
                    "prop_diameter_m": 0.2544,
                }
            )
    return runs


def toy_csv(path: Path) -> Path:
    runs = toy_runs()
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(mp.INPUT_FIELDS))
        writer.writeheader()
        writer.writerows(runs)
    return path


class FitTests(unittest.TestCase):
    def test_fit_eta(self) -> None:
        fitted = bo.fit_eta(toy_runs())
        self.assertEqual(len(fitted["gpfit"].y), len(toy_runs()))
        self.assertGreater(fitted["length_scale"], 0)
        self.assertIn("loocv_rmse", fitted["loocv"])

    def test_expected_improvement_non_negative(self) -> None:
        fitted = bo.fit_eta(toy_runs())
        grid = [{"voltage_set_v": v, "throttle_set_pct": t} for v in (20.0, 21.0) for t in (40.0, 60.0)]
        values = bo.expected_improvement(fitted["gpfit"], gp.features_of(grid), best=0.4)
        self.assertTrue(np.all(values >= 0.0))
        self.assertTrue(np.all(np.isfinite(values)))


class SuggestTests(unittest.TestCase):
    def test_sigma_suggestions_respect_distance(self) -> None:
        rows = bo.suggest(toy_runs(), n=3, strategy="sigma", min_distance=0.15, voltage_points=9, throttle_points=21)
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["strategy"] for row in rows}, {"sigma"})
        for row in rows:
            self.assertGreaterEqual(row["min_distance"], 0.15 - 1e-6)
            self.assertGreaterEqual(row["voltage_set_v"], min(VOLTAGES))
            self.assertLessEqual(row["voltage_set_v"], max(VOLTAGES))
            self.assertGreaterEqual(row["throttle_set_pct"], min(THROTTLES))
            self.assertLessEqual(row["throttle_set_pct"], max(THROTTLES))

    def test_ei_suggestions(self) -> None:
        rows = bo.suggest(toy_runs(), n=2, strategy="ei", min_distance=0.15, voltage_points=9, throttle_points=21)
        self.assertEqual(len(rows), 2)
        self.assertEqual({row["strategy"] for row in rows}, {"ei"})

    def test_random_deterministic_seed(self) -> None:
        first = bo.suggest(toy_runs(), n=2, strategy="random", seed=7)
        second = bo.suggest(toy_runs(), n=2, strategy="random", seed=7)
        self.assertEqual(first, second)

    def test_distance_limit_may_shorten(self) -> None:
        # 过大的最小距离可能让候选全部不满足：允许返回 0..n 个（不应抛错）
        rows = bo.suggest(toy_runs(), n=5, strategy="sigma", min_distance=0.5, voltage_points=9, throttle_points=21)
        self.assertLessEqual(len(rows), 5)
        self.assertIsInstance(rows, list)

    def test_invalid_suggest_inputs(self) -> None:
        with self.assertRaises(ValueError):
            bo.suggest(toy_runs(), strategy="bogus")
        with self.assertRaises(ValueError):
            bo.suggest([], strategy="sigma")
        with self.assertRaises(ValueError):
            bo.suggest(toy_runs(), n=0, strategy="sigma")


class SimulationTests(unittest.TestCase):
    def test_simulate_strategy_metrics(self) -> None:
        result = bo.simulate_strategy(toy_runs(), strategy="sigma", n=2, rounds=2, holdout=2)
        self.assertEqual(result["strategy"], "sigma")
        self.assertEqual(len(result["grid_rmse"]), 2)
        self.assertTrue(all(np.isfinite(result["grid_rmse"])))
        self.assertTrue(all(np.isfinite(result["holdout_rmse"])))

    def test_none_baseline(self) -> None:
        result = bo.simulate_strategy(toy_runs(), strategy="none", n=2, rounds=2, holdout=2)
        self.assertEqual(result["strategy"], "none")

    def test_invalid_simulation_inputs(self) -> None:
        with self.assertRaises(ValueError):
            bo.simulate_strategy(toy_runs(), strategy="bogus", rounds=1, holdout=2)
        with self.assertRaises(ValueError):
            bo.simulate_strategy(toy_runs(), strategy="sigma", rounds=0, holdout=2)

    def test_run_comparison_columns(self) -> None:
        rows = bo.run_comparison(toy_runs(), rounds=2, n=2, holdout=2)
        self.assertEqual([row["strategy"] for row in rows], ["none", "sigma", "ei", "random"])
        for row in rows:
            self.assertEqual(set(row.keys()), set(bo.METRIC_FIELDS))


class OutputTests(unittest.TestCase):
    def test_write_csv_and_overwrite_protection(self) -> None:
        rows = bo.run_comparison(toy_runs(), rounds=2, n=2, holdout=2)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "metrics.csv"
            bo.write_csv(rows, out, fields=bo.METRIC_FIELDS)
            text = out.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(",".join(bo.METRIC_FIELDS)))
            with self.assertRaises(FileExistsError):
                bo.write_csv(rows, out, fields=bo.METRIC_FIELDS)

    def test_plot_and_overwrite_protection(self) -> None:
        rows = bo.run_comparison(toy_runs(), rounds=2, n=2, holdout=2)
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "metrics.png"
            bo.plot_summary(rows, png)
            self.assertGreater(png.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                bo.plot_summary(rows, png)


class CliTests(unittest.TestCase):
    def test_main_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_csv = toy_csv(Path(tmp) / "runs.csv")
            output = Path(tmp) / "metrics.csv"
            figure = Path(tmp) / "metrics.png"
            code = bo.main(
                [
                    "--input",
                    str(runs_csv),
                    "--rounds",
                    "1",
                    "--n",
                    "2",
                    "--holdout",
                    "2",
                    "--output",
                    str(output),
                    "--figure",
                    str(figure),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            self.assertTrue(figure.exists())

    def test_main_rejects_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs_csv = toy_csv(Path(tmp) / "runs.csv")
            output = Path(tmp) / "metrics.csv"
            output.write_text("exists", encoding="utf-8")
            code = bo.main(["--input", str(runs_csv), "--rounds", "1", "--output", str(output), "--figure", str(Path(tmp) / "x.png")])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
