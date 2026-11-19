# -*- coding: utf-8 -*-
"""`code/selection/gp_match.py`（选型 v0.3）测试。"""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (HERE, ROOT / "code" / "processing", ROOT / "code" / "selection"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import gp_match  # noqa: E402
import match_propulsion  # noqa: E402

VOLTAGES = (10.0, 20.0)
THROTTLES = (25.0, 50.0, 75.0, 100.0)


def toy_runs() -> list[dict]:
    runs: list[dict] = []
    for voltage in VOLTAGES:
        for throttle in THROTTLES:
            runs.append(
                {
                    "run_id": f"TOY_{voltage:g}V_{throttle:g}pct",
                    "source": "SIM",
                    "combo": "TOY10",
                    "voltage_set_v": voltage,
                    "throttle_set_pct": throttle,
                    "thrust_N": 0.2 * voltage * throttle / 100.0,
                    "eta_sys": 0.15 + 0.6 * throttle / 100.0 - 0.05 * voltage / 20.0,
                    "eta_em": 0.55,
                    "fm": 0.5,
                    "rpm": 4000.0,
                    "current_a": voltage * throttle / 200.0,
                    "u_eta_sys_k2": 0.01,
                    "prop_diameter_m": 0.2544,
                }
            )
    return runs


def write_runs_csv(path: Path) -> None:
    fieldnames = list(match_propulsion.INPUT_FIELDS)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for run in toy_runs():
            writer.writerow(
                {
                    "run_id": run["run_id"],
                    "source": run["source"],
                    "combo": run["combo"],
                    "voltage_set_v": run["voltage_set_v"],
                    "throttle_set_pct": run["throttle_set_pct"],
                    "thrust_N_mean": run["thrust_N"],
                    "eta_sys_mean": run["eta_sys"],
                    "eta_em_mean": run["eta_em"],
                    "fm_mean": run["fm"],
                    "rpm_mean": run["rpm"],
                    "current_a_mean": run["current_a"],
                    "u_eta_sys_k2": run["u_eta_sys_k2"],
                    "prop_diameter_m": run["prop_diameter_m"],
                }
            )


class FitTests(unittest.TestCase):
    def test_fit_models_returns_gps_and_loocv(self) -> None:
        models = gp_match.fit_models(toy_runs())
        self.assertIn("thrust", models)
        self.assertIn("eta", models)
        self.assertIn("current_a", models["extra"])
        self.assertGreater(models["loocv"]["thrust"]["length_scale"], 0.0)
        self.assertLess(models["loocv"]["eta"]["rmse"], 0.05)
        self.assertGreaterEqual(models["loocv"]["thrust"]["n"], len(toy_runs()))

    def test_fit_models_requires_min_points(self) -> None:
        with self.assertRaises(ValueError):
            gp_match.fit_models(toy_runs()[:2])

    def test_local_u_is_conservative_max_of_neighbours(self) -> None:
        runs = toy_runs()
        for run in runs:
            run["u_eta_sys_k2"] = round(run["throttle_set_pct"] / 1000.0, 5)
        u = gp_match._local_u(runs, 20.0, 30.0)
        self.assertIsNotNone(u)
        self.assertAlmostEqual(u, 0.05, places=6)


class MatchTests(unittest.TestCase):
    def test_match_hits_required_thrust(self) -> None:
        results = gp_match.match_gp(toy_runs(), thrust_required_n=3.0, thrust_tolerance=0.1)
        self.assertTrue(results)
        self.assertAlmostEqual(results[0]["thrust_N"], 3.0, delta=0.15)
        self.assertEqual(results[0]["matched_by"], "gp")
        self.assertGreater(results[0]["gp_std_eta"], 0.0)
        self.assertLess(results[0]["eta_sys_conservative"], results[0]["eta_sys"])

    def test_match_voltage_filter(self) -> None:
        results = gp_match.match_gp(toy_runs(), thrust_required_n=3.0, thrust_tolerance=0.1, voltages=[20.0])
        self.assertTrue(results)
        self.assertTrue(all(entry["voltage_set_v"] == 20.0 for entry in results))
        with self.assertRaises(ValueError):
            gp_match.match_gp(toy_runs(), thrust_required_n=3.0, thrust_tolerance=0.1, voltages=[10.0])

    def test_match_source_filter(self) -> None:
        with self.assertRaises(ValueError):
            gp_match.match_gp(toy_runs(), thrust_required_n=3.0, thrust_tolerance=0.1, source="MEASURED")

    def test_match_max_u_filter(self) -> None:
        with self.assertRaises(ValueError):
            gp_match.match_gp(toy_runs(), thrust_required_n=3.0, thrust_tolerance=0.1, max_u_k2=0.001)

    def test_match_no_candidates_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            gp_match.match_gp(toy_runs(), thrust_required_n=100.0, thrust_tolerance=0.1)
        self.assertIn("GP 未找到", str(ctx.exception))

    def test_match_invalid_arguments(self) -> None:
        with self.assertRaises(ValueError):
            gp_match.match_gp(toy_runs(), thrust_required_n=0.0)
        with self.assertRaises(ValueError):
            gp_match.match_gp(toy_runs(), thrust_required_n=1.0, thrust_tolerance=1.5)
        with self.assertRaises(ValueError):
            gp_match.match_gp(toy_runs(), thrust_required_n=1.0, objective="nope")

    def test_ranking_by_eta(self) -> None:
        results = gp_match.match_gp(toy_runs(), thrust_required_n=1.5, thrust_tolerance=0.2, objective="eta_sys")
        self.assertGreaterEqual(len(results), 2)
        eta_values = [entry["eta_sys"] for entry in results]
        self.assertEqual(eta_values, sorted(eta_values, reverse=True))
        self.assertEqual([entry["rank"] for entry in results], list(range(1, len(results) + 1)))

    def test_balanced_objective_sets_score(self) -> None:
        results = gp_match.match_gp(
            toy_runs(), thrust_required_n=1.5, thrust_tolerance=0.2, objective="balanced"
        )
        self.assertTrue(results)
        scores = [entry["score"] for entry in results]
        self.assertEqual(scores, sorted(scores, reverse=True))


class OutputTests(unittest.TestCase):
    def test_write_report_fields(self) -> None:
        results = gp_match.match_gp(toy_runs(), thrust_required_n=3.0, thrust_tolerance=0.1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.csv"
            gp_match.write_report(results, path)
            with path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, gp_match.GP_OUTPUT_FIELDS)
                rows = list(reader)
            self.assertEqual(len(rows), len(results))
            self.assertTrue(rows[0]["data_note"].startswith("GP 连续匹配"))

    def test_plot_gp_selection_png_and_overwrite_protection(self) -> None:
        runs = toy_runs()
        results = gp_match.match_gp(runs, thrust_required_n=3.0, thrust_tolerance=0.1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "selection.png"
            gp_match.plot_gp_selection(runs, results, path, thrust_required_n=3.0, thrust_tolerance=0.1)
            self.assertGreater(path.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                gp_match.plot_gp_selection(runs, results, path, thrust_required_n=3.0, thrust_tolerance=0.1)

    def test_main_end_to_end_and_error_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runs_csv = tmp_path / "runs.csv"
            write_runs_csv(runs_csv)
            out_csv = tmp_path / "selection.csv"
            out_png = tmp_path / "selection.png"
            code = gp_match.main(
                [
                    "--input",
                    str(runs_csv),
                    "--thrust",
                    "3.0",
                    "--tolerance",
                    "0.1",
                    "--output",
                    str(out_csv),
                    "--figure",
                    str(out_png),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue(out_csv.exists())
            self.assertTrue(out_png.exists())
            # 输出已存在且未 --overwrite → exit 2
            self.assertEqual(
                gp_match.main(
                    ["--input", str(runs_csv), "--thrust", "3.0", "--output", str(out_csv), "--figure", str(out_png)]
                ),
                2,
            )
            # 无候选 → exit 2
            self.assertEqual(
                gp_match.main(
                    ["--input", str(runs_csv), "--thrust", "100", "--output", str(tmp_path / "x.csv")]
                ),
                2,
            )


    def test_main_require_measured_rejects_sim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runs_csv = tmp_path / "runs.csv"
            write_runs_csv(runs_csv)
            code = gp_match.main(
                [
                    "--input",
                    str(runs_csv),
                    "--thrust",
                    "3.0",
                    "--require-measured",
                    "--output",
                    str(tmp_path / "selection.csv"),
                    "--figure",
                    str(tmp_path / "selection.png"),
                ]
            )
            self.assertEqual(code, 2)
            self.assertFalse((tmp_path / "selection.csv").exists())


if __name__ == "__main__":
    unittest.main()
