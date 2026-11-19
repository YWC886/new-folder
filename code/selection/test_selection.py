# -*- coding: utf-8 -*-
"""selection/match_propulsion.py 的回归测试：读入、筛选、排序、Pareto、报告与图件。"""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from match_propulsion import (
    INPUT_FIELDS,
    OUTPUT_FIELDS,
    load_runs,
    main,
    match,
    pareto_front,
    plot_selection,
    write_report,
)


def make_run(
    *,
    run_id: str,
    thrust: float,
    eta_sys: float,
    voltage: float = 22.2,
    throttle: float = 100.0,
    combo: str = "SIM10x4.5",
    source: str = "SIM",
    eta_em: float = 0.6,
    fm: float = 0.7,
) -> dict:
    return {
        "run_id": run_id,
        "source": source,
        "combo": combo,
        "voltage_set_v": voltage,
        "throttle_set_pct": throttle,
        "thrust_N": thrust,
        "eta_sys": eta_sys,
        "eta_em": eta_em,
        "fm": fm,
        "rpm": 6000.0,
        "current_a": 8.0,
        "u_eta_sys_k2": 0.0226,
        "prop_diameter_m": 0.2544,
    }


class LoadRunsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_csv(self, rows: list[dict], fields: list[str] = INPUT_FIELDS) -> Path:
        path = self.root / "runs.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_load_runs_parses_numbers(self) -> None:
        row = {field: "" for field in INPUT_FIELDS}
        row.update(
            {
                "run_id": "r1",
                "source": "SIM",
                "combo": "C1",
                "voltage_set_v": "22.2",
                "throttle_set_pct": "75",
                "thrust_N_mean": "6.053",
                "eta_sys_mean": "0.4827",
                "eta_em_mean": "0.7",
                "fm_mean": "0.69",
                "rpm_mean": "9500.5",
                "current_a_mean": "12.0",
                "u_eta_sys_k2": "0.0226",
                "prop_diameter_m": "0.2544",
            }
        )
        path = self.write_csv([row])
        runs = load_runs(path)
        self.assertEqual(len(runs), 1)
        self.assertAlmostEqual(runs[0]["thrust_N"], 6.053)
        self.assertAlmostEqual(runs[0]["eta_sys"], 0.4827)
        self.assertAlmostEqual(runs[0]["prop_diameter_m"], 0.2544)

    def test_load_runs_missing_columns_rejected(self) -> None:
        path = self.write_csv([{"run_id": "r1"}], fields=["run_id"])
        with self.assertRaises(ValueError):
            load_runs(path)

    def test_load_runs_skips_rows_without_numbers(self) -> None:
        row = {field: "" for field in INPUT_FIELDS}
        row.update({"run_id": "r1", "source": "SIM", "combo": "C1", "thrust_N_mean": "", "eta_sys_mean": ""})
        path = self.write_csv([row])
        with self.assertRaises(ValueError):
            load_runs(path)


class MatchTest(unittest.TestCase):
    def test_filters_by_tolerance(self) -> None:
        runs = [
            make_run(run_id="a", thrust=4.4, eta_sys=0.20, voltage=20.0),
            make_run(run_id="b", thrust=4.6, eta_sys=0.30, voltage=21.0),
            make_run(run_id="c", thrust=5.4, eta_sys=0.40, voltage=22.0),
            make_run(run_id="d", thrust=5.6, eta_sys=0.50, voltage=23.0),
        ]
        results = match(runs, thrust_required_n=5.0, thrust_tolerance=0.1)
        ids = [entry["run_id"] for entry in results]
        self.assertEqual(ids, ["c", "b"])

    def test_ranks_by_efficiency_and_dedupes_combo_voltage(self) -> None:
        runs = [
            make_run(run_id="low", thrust=5.0, eta_sys=0.40, throttle=90.0),
            make_run(run_id="high", thrust=5.2, eta_sys=0.45, throttle=85.0),
            make_run(run_id="other-voltage", thrust=5.0, eta_sys=0.43, voltage=29.6, throttle=60.0),
        ]
        results = match(runs, thrust_required_n=5.0, thrust_tolerance=0.1, interpolate=False)
        self.assertEqual([entry["run_id"] for entry in results], ["high", "other-voltage"])
        self.assertEqual([entry["rank"] for entry in results], [1, 2])
        self.assertAlmostEqual(results[0]["thrust_margin_N"], 0.2, places=9)

    def test_respects_max_throttle_and_voltage_filter(self) -> None:
        runs = [
            make_run(run_id="a", thrust=5.0, eta_sys=0.40, voltage=22.2, throttle=95.0),
            make_run(run_id="b", thrust=5.0, eta_sys=0.45, voltage=29.6, throttle=85.0),
        ]
        results = match(runs, thrust_required_n=5.0, max_throttle_pct=90.0, voltages=[29.6])
        self.assertEqual([entry["run_id"] for entry in results], ["b"])

    def test_source_filter(self) -> None:
        runs = [
            make_run(run_id="sim", thrust=5.0, eta_sys=0.40, source="SIM"),
            make_run(run_id="measured", thrust=5.0, eta_sys=0.30, source="MEASURED"),
        ]
        results = match(runs, thrust_required_n=5.0, source="MEASURED")
        self.assertEqual([entry["run_id"] for entry in results], ["measured"])

    def test_no_candidates_raises(self) -> None:
        runs = [make_run(run_id="a", thrust=2.0, eta_sys=0.3)]
        with self.assertRaises(ValueError):
            match(runs, thrust_required_n=10.0)

    def test_top_n_truncation(self) -> None:
        runs = [
            make_run(run_id=f"r{index}", thrust=5.0, eta_sys=0.3 + index * 0.01, voltage=20.0 + index)
            for index in range(6)
        ]
        results = match(runs, thrust_required_n=5.0, top_n=3)
        self.assertEqual(len(results), 3)
        self.assertAlmostEqual(results[0]["eta_sys"], 0.35)


class MatchV02Test(unittest.TestCase):
    """v0.2 新增：油门插值、多目标排序、不确定度过滤与保守效率。"""

    def test_interpolation_exact_thrust(self) -> None:
        runs = [
            make_run(run_id="p20", thrust=2.0, eta_sys=0.30, throttle=20.0),
            make_run(run_id="p40", thrust=4.0, eta_sys=0.40, throttle=40.0),
        ]
        results = match(runs, thrust_required_n=3.0, thrust_tolerance=0.01)
        self.assertEqual(len(results), 1)
        entry = results[0]
        self.assertEqual(entry["matched_by"], "interp")
        self.assertAlmostEqual(entry["thrust_N"], 3.0)
        self.assertAlmostEqual(entry["throttle_set_pct"], 30.0)
        self.assertAlmostEqual(entry["eta_sys"], 0.35)
        self.assertAlmostEqual(entry["thrust_margin_N"], 0.0)
        self.assertEqual(entry["run_id"], "interp:p20~p40")

    def test_interpolation_falls_back_to_grid(self) -> None:
        runs = [
            make_run(run_id="p2", thrust=2.0, eta_sys=0.30, throttle=20.0),
            make_run(run_id="p4", thrust=4.0, eta_sys=0.40, throttle=40.0),
        ]
        results = match(runs, thrust_required_n=6.0, thrust_tolerance=0.5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["matched_by"], "grid")
        self.assertEqual(results[0]["run_id"], "p4")

    def test_interpolation_skipped_when_throttle_over_limit(self) -> None:
        runs = [
            make_run(run_id="p20", thrust=2.0, eta_sys=0.30, throttle=20.0),
            make_run(run_id="p40", thrust=4.0, eta_sys=0.40, throttle=40.0),
        ]
        results = match(runs, thrust_required_n=3.0, thrust_tolerance=0.5, max_throttle_pct=25.0)
        self.assertEqual(results[0]["matched_by"], "grid")
        self.assertEqual(results[0]["run_id"], "p20")

    def test_max_u_filter(self) -> None:
        runs = [
            make_run(run_id="noisy", thrust=5.0, eta_sys=0.45, voltage=22.2),
            make_run(run_id="clean", thrust=5.0, eta_sys=0.40, voltage=29.6),
        ]
        runs[0]["u_eta_sys_k2"] = 0.05
        runs[1]["u_eta_sys_k2"] = 0.01
        results = match(runs, thrust_required_n=5.0, thrust_tolerance=0.1, max_u_k2=0.02)
        self.assertEqual([entry["run_id"] for entry in results], ["clean"])

    def test_objective_current_vs_eta(self) -> None:
        runs = [
            make_run(run_id="fast", thrust=5.0, eta_sys=0.45, voltage=22.2),
            make_run(run_id="economy", thrust=5.0, eta_sys=0.40, voltage=29.6),
        ]
        runs[0]["current_a"] = 12.0
        runs[1]["current_a"] = 8.0
        eta_first = match(runs, thrust_required_n=5.0, objective="eta_sys")[0]
        current_first = match(runs, thrust_required_n=5.0, objective="current")[0]
        self.assertEqual(eta_first["run_id"], "fast")
        self.assertEqual(current_first["run_id"], "economy")

    def test_balanced_score_and_conservative_eta(self) -> None:
        runs = [
            make_run(run_id="a", thrust=5.0, eta_sys=0.45, voltage=22.2),
            make_run(run_id="b", thrust=5.0, eta_sys=0.40, voltage=29.6),
        ]
        runs[0]["u_eta_sys_k2"] = 0.01
        runs[1]["u_eta_sys_k2"] = 0.02
        results = match(runs, thrust_required_n=5.0, objective="balanced")
        scores = [entry["score"] for entry in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        for entry in results:
            self.assertGreaterEqual(entry["score"], 0.0)
            self.assertLessEqual(entry["score"], 1.0)
            self.assertAlmostEqual(
                entry["eta_sys_conservative"],
                entry["eta_sys"] - entry["u_eta_sys_k2"],
                places=9,
            )


class ParetoAndReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_pareto_front(self) -> None:
        runs = [
            make_run(run_id="a", thrust=1.0, eta_sys=0.2),
            make_run(run_id="b", thrust=1.5, eta_sys=0.35),
            make_run(run_id="c", thrust=2.0, eta_sys=0.30),
            make_run(run_id="d", thrust=3.0, eta_sys=0.25),
        ]
        front = pareto_front(runs)
        self.assertEqual([entry["run_id"] for entry in front], ["a", "b"])

    def test_write_report_fields(self) -> None:
        results = match(
            [make_run(run_id="a", thrust=5.0, eta_sys=0.4)],
            thrust_required_n=5.0,
        )
        path = write_report(results, self.root / "out" / "selection.csv")
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0].keys(), set(OUTPUT_FIELDS))
        self.assertEqual(rows[0]["run_id"], "a")
        self.assertEqual(rows[0]["rank"], "1")

    def test_plot_creates_png_and_protects_overwrite(self) -> None:
        runs = [
            make_run(run_id="a", thrust=4.0, eta_sys=0.2),
            make_run(run_id="b", thrust=5.0, eta_sys=0.4),
        ]
        results = match(runs, thrust_required_n=5.0, thrust_tolerance=0.2)
        png = plot_selection(runs, results, self.root / "figures" / "sel.png", thrust_required_n=5.0, thrust_tolerance=0.2)
        self.assertTrue(png.exists())
        self.assertGreater(png.stat().st_size, 1000)
        with self.assertRaises(FileExistsError):
            plot_selection(runs, results, png, thrust_required_n=5.0, thrust_tolerance=0.2)

    def test_main_end_to_end(self) -> None:
        rows = []
        for voltage in (22.2, 29.6):
            for throttle in (50.0, 75.0):
                row = {field: "" for field in INPUT_FIELDS}
                row.update(
                    {
                        "run_id": f"r-{voltage}-{throttle}",
                        "source": "SIM",
                        "combo": "C1",
                        "voltage_set_v": str(voltage),
                        "throttle_set_pct": str(throttle),
                        "thrust_N_mean": str(voltage * throttle / 1000.0),
                        "eta_sys_mean": "0.3" if throttle == 50.0 else "0.5",
                        "eta_em_mean": "0.6",
                        "fm_mean": "0.7",
                        "rpm_mean": "8000",
                        "current_a_mean": "10",
                        "u_eta_sys_k2": "0.0226",
                        "prop_diameter_m": "0.2544",
                    }
                )
                rows.append(row)
        input_path = self.root / "runs.csv"
        with input_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=INPUT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

        exit_code = main(
            [
                "--input",
                str(input_path),
                "--thrust",
                "1.7",
                "--tolerance",
                "0.2",
                "--output",
                str(self.root / "out" / "selection.csv"),
                "--figure",
                str(self.root / "out" / "selection.png"),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue((self.root / "out" / "selection.csv").exists())
        self.assertTrue((self.root / "out" / "selection.png").exists())

    def test_main_no_candidates_exit_code_2(self) -> None:
        rows = [
            {
                **{field: "" for field in INPUT_FIELDS},
                **{
                    "run_id": "r1",
                    "source": "SIM",
                    "combo": "C1",
                    "voltage_set_v": "22.2",
                    "throttle_set_pct": "50",
                    "thrust_N_mean": "1.0",
                    "eta_sys_mean": "0.2",
                    "rpm_mean": "4000",
                    "current_a_mean": "2",
                    "prop_diameter_m": "0.2544",
                },
            }
        ]
        input_path = self.root / "runs.csv"
        with input_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=INPUT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        exit_code = main(
            [
                "--input",
                str(input_path),
                "--thrust",
                "10",
                "--output",
                str(self.root / "out.csv"),
                "--figure",
                str(self.root / "fig.png"),
            ]
        )
        self.assertEqual(exit_code, 2)


    def test_main_require_measured_rejects_sim(self) -> None:
        rows = [
            {
                **{field: "" for field in INPUT_FIELDS},
                **{
                    "run_id": "sim-1",
                    "source": "SIM",
                    "combo": "C1",
                    "voltage_set_v": "22.2",
                    "throttle_set_pct": "50",
                    "thrust_N_mean": "5.0",
                    "eta_sys_mean": "0.3",
                    "rpm_mean": "8000",
                    "current_a_mean": "10",
                    "prop_diameter_m": "0.2544",
                },
            }
        ]
        input_path = self.root / "runs.csv"
        with input_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=INPUT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        exit_code = main(
            [
                "--input",
                str(input_path),
                "--thrust",
                "5",
                "--require-measured",
                "--output",
                str(self.root / "out.csv"),
                "--figure",
                str(self.root / "fig.png"),
            ]
        )
        self.assertEqual(exit_code, 2)
        self.assertFalse((self.root / "out.csv").exists())

    def test_main_require_measured_accepts_measured(self) -> None:
        rows = []
        for voltage in (22.2, 29.6):
            for throttle in (50.0, 75.0):
                row = {field: "" for field in INPUT_FIELDS}
                row.update(
                    {
                        "run_id": f"m-{voltage}-{throttle}",
                        "source": "MEASURED",
                        "combo": "C1",
                        "voltage_set_v": str(voltage),
                        "throttle_set_pct": str(throttle),
                        "thrust_N_mean": str(voltage * throttle / 1000.0),
                        "eta_sys_mean": "0.3" if throttle == 50.0 else "0.5",
                        "eta_em_mean": "0.6",
                        "fm_mean": "0.7",
                        "rpm_mean": "8000",
                        "current_a_mean": "10",
                        "u_eta_sys_k2": "0.0226",
                        "prop_diameter_m": "0.2544",
                    }
                )
                rows.append(row)
        input_path = self.root / "runs.csv"
        with input_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=INPUT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        exit_code = main(
            [
                "--input",
                str(input_path),
                "--thrust",
                "1.7",
                "--tolerance",
                "0.2",
                "--require-measured",
                "--output",
                str(self.root / "out" / "selection.csv"),
                "--figure",
                str(self.root / "out" / "selection.png"),
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue((self.root / "out" / "selection.csv").exists())


if __name__ == "__main__":
    unittest.main()
