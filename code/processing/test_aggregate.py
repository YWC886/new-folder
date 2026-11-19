# -*- coding: utf-8 -*-
"""aggregate_efficiency.py 的回归测试：展平、分组统计、去重、坏文件、覆盖保护。"""
from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from aggregate_efficiency import GRID_FIELDS, RUN_FIELDS, aggregate, flatten_summary, load_summaries


def make_summary(
    run_id: str = "20261119_SIM_22V2_50pct_R1",
    combo: str = "DEMO",
    voltage: float = 22.2,
    throttle: float = 50.0,
    eta_em: float = 0.35,
    fm: float = 0.80,
    eta_sys: float = 0.28,
    simulated: bool = True,
    include_uncertainty: bool = False,
    mode: str = "simulate",
) -> dict:
    return {
        "schema_version": "0.2",
        "simulated": simulated,
        "data_notice": "模拟数据：仅用于软件联调与流程验证，不是实验结果",
        "rows": 5000,
        "window": {
            "mode": "last",
            "window_s": 3.0,
            "samples": 3001,
            **{
                name: {"count": 3001, "mean": value, "std": 0.0, "min": value, "max": value, "relative_std": 0.0}
                for name, value in {
                    "thrust_N": 9.8,
                    "torque_Nm": 0.1,
                    "rpm": 6000.0,
                    "voltage_v": voltage,
                    "current_a": 8.0,
                    "p_shaft_w": 62.8,
                    "p_elec_w": 177.5,
                    "eta_em": eta_em,
                    "fm": fm,
                    "eta_sys": eta_sys,
                }.items()
            },
        },
        "conditions": {
            "run_id": run_id,
            "mode": mode,
            "combo": combo,
            "repeat": "R1",
            "motor": "未填写",
            "esc": "未填写",
            "prop": "未填写",
            "voltage_set_v": voltage,
            "throttle_set_pct": throttle,
            "prop_diameter_m": 0.4572,
            "operator": "unittest",
        },
        "assumptions": {"air_density_kg_m3": 1.125, "air_density_source": "实测环境温压估算"},
        "calibration_source": "unittest 合成标定",
        "uncertainty": (
            {
                "method": "first_order_relative",
                "U_rel_eta_em_k2": 0.0144222051,
                "U_rel_fm_k2": 0.0225665682,
                "U_rel_eta_sys_k2": 0.0225665682,
            }
            if include_uncertainty
            else {}
        ),
        "warnings": [],
    }


class AggregateEfficiencyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "runs.csv"
        self.grid = self.root / "grid.csv"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_summary(self, name: str, **kwargs) -> Path:
        path = self.root / f"{name}_efficiency.json"
        path.write_text(json.dumps(make_summary(**kwargs), ensure_ascii=False), encoding="utf-8")
        return path

    def test_aggregate_writes_runs_and_grid(self) -> None:
        paths = [
            self.write_summary("a", eta_em=0.35, fm=0.80, eta_sys=0.28),
            self.write_summary("b", run_id="20261119_SIM_22V2_50pct_R2", eta_em=0.37, fm=0.82, eta_sys=0.30),
            self.write_summary("c", run_id="20261119_SIM_14V8_30pct_R1", voltage=14.8, throttle=30.0, eta_em=0.30, fm=0.75, eta_sys=0.20),
        ]
        result = aggregate(paths, self.out, self.grid)
        self.assertEqual(len(result["rows"]), 3)
        self.assertEqual(len(result["grid"]), 2)
        self.assertEqual(result["sources"], ["SIM"])

        with self.out.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0].keys(), set(RUN_FIELDS))
        self.assertEqual(len(rows), 3)

        with self.grid.open(encoding="utf-8", newline="") as handle:
            grid = list(csv.DictReader(handle))
        self.assertEqual(grid[0].keys(), set(GRID_FIELDS))
        two_runs = [row for row in grid if row["runs"] == "2"]
        self.assertEqual(len(two_runs), 1)
        entry = two_runs[0]
        self.assertEqual(entry["source"], "SIM")
        self.assertAlmostEqual(float(entry["eta_sys_mean"]), 0.29, places=9)
        self.assertAlmostEqual(float(entry["eta_sys_std"]), 0.0141421356, places=8)
        single = [row for row in grid if row["runs"] == "1"][0]
        self.assertEqual(float(single["eta_sys_std"]), 0.0)

    def test_duplicate_run_id_deduplicated(self) -> None:
        first = self.write_summary("a")
        duplicate = self.write_summary("b")  # 相同 run_id
        third = self.write_summary("c", run_id="20261119_SIM_OTHER_R1")
        result = aggregate([first, duplicate, third], self.out, self.grid)
        self.assertEqual(len(result["rows"]), 2)
        self.assertTrue(any("重复 run_id" in warning for warning in result["warnings"]))

    def test_bad_json_skipped_with_warning(self) -> None:
        bad = self.root / "bad_efficiency.json"
        bad.write_text("{not json", encoding="utf-8")
        good = self.write_summary("good")
        result = aggregate([bad, good], self.out, self.grid)
        self.assertEqual(len(result["rows"]), 1)
        self.assertTrue(any("跳过" in warning for warning in result["warnings"]))

    def test_all_invalid_raises(self) -> None:
        bad = self.root / "bad_efficiency.json"
        bad.write_text("{not json", encoding="utf-8")
        with self.assertRaises(ValueError):
            aggregate([bad], self.out, self.grid)

    def test_overwrite_protection(self) -> None:
        paths = [self.write_summary("a")]
        aggregate(paths, self.out, self.grid)
        with self.assertRaises(FileExistsError):
            aggregate(paths, self.out, self.grid)
        result = aggregate(paths, self.out, self.grid, overwrite=True)
        self.assertEqual(len(result["rows"]), 1)

    def test_require_measured_rejects_sim_inputs(self) -> None:
        paths = [self.write_summary("a")]
        with self.assertRaises(ValueError) as ctx:
            aggregate(paths, self.out, self.grid, require_measured=True)
        self.assertIn("MEASURED 守门拒绝", str(ctx.exception))
        self.assertIn("来源不是 MEASURED", str(ctx.exception))
        self.assertFalse(self.out.exists())

    def test_require_measured_accepts_measured_inputs(self) -> None:
        paths = [
            self.write_summary("m1", simulated=False, mode="serial", voltage=14.8, throttle=30.0),
            self.write_summary(
                "m2", run_id="20261119_M0p4_14V8_30pct_R2", simulated=False, mode="serial", voltage=14.8, throttle=30.0, eta_sys=0.20
            ),
        ]
        result = aggregate(paths, self.out, self.grid, require_measured=True)
        self.assertEqual(result["sources"], ["MEASURED"])
        self.assertEqual(len(result["rows"]), 2)
        self.assertTrue(self.out.exists())

    def test_require_measured_default_off_keeps_sim(self) -> None:
        paths = [self.write_summary("a")]
        result = aggregate(paths, self.out, self.grid)
        self.assertEqual(result["sources"], ["SIM"])

    def test_require_measured_rejects_non_serial_mode(self) -> None:
        paths = [self.write_summary("m", simulated=False, mode="bench")]

        with self.assertRaises(ValueError) as ctx:
            aggregate(paths, self.out, self.grid, require_measured=True)
        self.assertIn("mode 不是 'serial'", str(ctx.exception))

    def test_flatten_marks_measured_and_keeps_conditions(self) -> None:
        path = self.write_summary("m", simulated=False, voltage=14.8, throttle=30.0)
        rows, warnings = load_summaries([path])
        self.assertEqual(warnings, [])
        self.assertEqual(rows[0]["source"], "MEASURED")
        self.assertEqual(float(rows[0]["voltage_set_v"]), 14.8)
        self.assertEqual(float(rows[0]["throttle_set_pct"]), 30.0)
        self.assertEqual(rows[0]["combo"], "DEMO")

    def test_flatten_rejects_missing_window(self) -> None:
        with self.assertRaises(ValueError):
            flatten_summary({"conditions": {}}, Path("x.json"))

    def test_uncertainty_and_steady_mode_propagated(self) -> None:
        first = self.write_summary("u1", include_uncertainty=True)
        second = self.write_summary("u2", run_id="20261119_SIM_22V2_50pct_R2", include_uncertainty=True, eta_sys=0.30)
        aggregate([first, second], self.out, self.grid)

        with self.out.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["steady_mode"], "last")
        self.assertAlmostEqual(float(rows[0]["u_eta_sys_k2"]), 0.0225665682, places=10)
        self.assertEqual(rows[0].keys(), set(RUN_FIELDS))

        with self.grid.open(encoding="utf-8", newline="") as handle:
            grid = list(csv.DictReader(handle))
        single_group = [row for row in grid if row["runs"] == "2"][0]
        self.assertAlmostEqual(float(single_group["u_eta_sys_k2_max"]), 0.0225665682, places=10)
        self.assertEqual(single_group.keys(), set(GRID_FIELDS))


if __name__ == "__main__":
    unittest.main()
