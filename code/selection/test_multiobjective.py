# -*- coding: utf-8 -*-
"""`code/selection/multiobjective.py`（选型 v0.4）测试。"""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (HERE, ROOT / "code" / "processing"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import match_propulsion  # noqa: E402
import multiobjective as mo  # noqa: E402

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


class ParetoTests(unittest.TestCase):
    def test_pareto_basic_properties(self) -> None:
        result = mo.run_pareto(toy_runs(), thrust_required_n=1.5, thrust_tolerance=0.2, voltage_points=9, throttle_points=21)
        self.assertGreater(result["n_candidates"], 0)
        front = result["front"]
        self.assertGreater(len(front), 0)
        self.assertEqual(result["n_front"], len(front))
        for entry in front:
            self.assertLessEqual(abs(entry["thrust_margin_N"]), 1.5 * 0.2 + 1e-9)
            self.assertGreater(entry["gp_std_eta"], 0.0)
            self.assertLessEqual(entry["eta_sys_conservative"], entry["eta_sys"] + 1e-12)
            self.assertIn("is_knee", entry)
        self.assertEqual(sum(1 for entry in front if entry["is_knee"]), 1)

    def test_front_is_non_dominated_and_sorted(self) -> None:
        result = mo.run_pareto(toy_runs(), thrust_required_n=1.5, thrust_tolerance=0.2, voltage_points=9, throttle_points=21)
        front = result["front"]
        for i, first in enumerate(front):
            for j, second in enumerate(front):
                if i == j:
                    continue
                self.assertFalse(mo.dominates(first, second), f"front[{i}] dominates front[{j}]")
        cons = [entry["eta_sys_conservative"] for entry in front]
        self.assertEqual(cons, sorted(cons, reverse=True))
        self.assertEqual([entry["rank"] for entry in front], list(range(1, len(front) + 1)))
        self.assertTrue(all(entry["data_note"] == mo.DATA_NOTE_PARETO for entry in front))

    def test_no_candidates_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            mo.run_pareto(toy_runs(), thrust_required_n=100.0, thrust_tolerance=0.1)
        self.assertIn("GP 未找到", str(ctx.exception))

    def test_invalid_arguments(self) -> None:
        with self.assertRaises(ValueError):
            mo.run_pareto(toy_runs(), thrust_required_n=0.0)
        with self.assertRaises(ValueError):
            mo.run_pareto(toy_runs(), thrust_required_n=1.0, thrust_tolerance=1.5)
        with self.assertRaises(ValueError):
            mo.candidate_grid(toy_runs(), voltage_points=1)

    def test_csv_and_plot_outputs(self) -> None:
        result = mo.run_pareto(toy_runs(), thrust_required_n=1.5, thrust_tolerance=0.2, voltage_points=9, throttle_points=21)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = mo.write_csv(result["front"], tmp_path / "pareto.csv", fields=mo.PARETO_FIELDS)
            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, mo.PARETO_FIELDS)
                self.assertEqual(len(list(reader)), len(result["front"]))
            with self.assertRaises(FileExistsError):
                mo.write_csv(result["front"], csv_path, fields=mo.PARETO_FIELDS)
            png_path = mo.plot_pareto(
                result["candidates"],
                result["front"],
                tmp_path / "pareto.png",
                thrust_required_n=1.5,
                thrust_tolerance=0.2,
            )
            self.assertGreater(png_path.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                mo.plot_pareto(
                    result["candidates"],
                    result["front"],
                    png_path,
                    thrust_required_n=1.5,
                    thrust_tolerance=0.2,
                )


class SuggestionTests(unittest.TestCase):
    def test_suggestions_bounded_and_distinct(self) -> None:
        suggestions = mo.suggest_measurements(toy_runs(), n=3, min_distance=0.15, voltage_points=9, throttle_points=21)
        self.assertEqual(len(suggestions), 3)
        for entry in suggestions:
            self.assertGreaterEqual(entry["throttle_set_pct"], 25.0 - 1e-9)
            self.assertLessEqual(entry["throttle_set_pct"], 100.0 + 1e-9)
            self.assertGreater(entry["gp_std_eta"], 0.0)
            self.assertGreaterEqual(entry["min_distance"], 0.15 - 1e-9)
        self.assertEqual([entry["rank"] for entry in suggestions], [1, 2, 3])
        self.assertTrue(all(entry["data_note"] == mo.DATA_NOTE_SUGGEST for entry in suggestions))

    def test_suggestion_csv_and_plot(self) -> None:
        runs = toy_runs()
        suggestions = mo.suggest_measurements(runs, n=2, min_distance=0.2, voltage_points=9, throttle_points=21)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = mo.write_csv(suggestions, tmp_path / "suggest.csv", fields=mo.SUGGEST_FIELDS)
            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, mo.SUGGEST_FIELDS)
                self.assertEqual(len(list(reader)), 2)
            png_path = mo.plot_suggestions(runs, suggestions, tmp_path / "suggest.png")
            self.assertGreater(png_path.stat().st_size, 10_000)


class CliTests(unittest.TestCase):
    def test_main_pareto_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runs_csv = tmp_path / "runs.csv"
            write_runs_csv(runs_csv)
            out_csv = tmp_path / "pareto.csv"
            out_png = tmp_path / "pareto.png"
            code = mo.main(
                [
                    "--input",
                    str(runs_csv),
                    "--thrust",
                    "1.5",
                    "--tolerance",
                    "0.2",
                    "--voltage-points",
                    "9",
                    "--throttle-points",
                    "21",
                    "--output",
                    str(out_csv),
                    "--figure",
                    str(out_png),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue(out_csv.exists())
            self.assertTrue(out_png.exists())
            self.assertEqual(
                mo.main(
                    [
                        "--input",
                        str(runs_csv),
                        "--thrust",
                        "1.5",
                        "--voltage-points",
                        "9",
                        "--throttle-points",
                        "21",
                        "--output",
                        str(out_csv),
                        "--figure",
                        str(out_png),
                    ]
                ),
                2,
            )
            self.assertEqual(
                mo.main(["--input", str(runs_csv), "--thrust", "100", "--output", str(tmp_path / "x.csv")]),
                2,
            )

    def test_main_suggest_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runs_csv = tmp_path / "runs.csv"
            write_runs_csv(runs_csv)
            out_csv = tmp_path / "suggest.csv"
            out_png = tmp_path / "suggest.png"
            code = mo.main(
                [
                    "--input",
                    str(runs_csv),
                    "--suggest",
                    "--n",
                    "3",
                    "--min-distance",
                    "0.15",
                    "--voltage-points",
                    "9",
                    "--throttle-points",
                    "21",
                    "--output",
                    str(out_csv),
                    "--figure",
                    str(out_png),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue(out_csv.exists())
            self.assertTrue(out_png.exists())


if __name__ == "__main__":
    unittest.main()
