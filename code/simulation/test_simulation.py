# -*- coding: utf-8 -*-
r"""仿真模块测试：物理模型量级/单调性 + 仿真战役闭环 + 覆盖保护。

运行：
    py -3.12 -m unittest discover -s code\simulation -p "test_*.py" -v
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _sub in ("processing", "simulation"):
    _path = ROOT / "code" / _sub
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import simulate_campaign as sc  # noqa: E402
import sensitivity_pack_model as spm  # noqa: E402
from compute_efficiency import air_density_from_conditions  # noqa: E402
from propulsion_model import ModelParams, PackModel, air_density, solve_operating_point  # noqa: E402


class ModelTests(unittest.TestCase):
    """物理模型的量级与单调性自检（不宣称任何实测精度）。"""

    def setUp(self) -> None:
        self.params = ModelParams()

    def test_operating_point_ranges(self) -> None:
        point = solve_operating_point(self.params, 22.2, 1.0)
        self.assertGreater(point["rpm"], 6000.0)
        self.assertLess(point["rpm"], 12000.0)
        self.assertGreater(point["thrust_n"], 5.0)
        self.assertLess(point["thrust_n"], 20.0)
        for key in ("eta_em", "fm", "eta_sys"):
            self.assertGreater(point[key], 0.0)
            self.assertLess(point[key], 1.0)
        self.assertTrue(math.isclose(point["eta_sys"], point["fm"] * point["eta_em"], rel_tol=1e-9))

    def test_thrust_and_rpm_monotonic_with_throttle(self) -> None:
        points = [solve_operating_point(self.params, 22.2, throttle) for throttle in (0.2, 0.4, 0.6, 0.8, 1.0)]
        for previous, current in zip(points, points[1:]):
            self.assertGreater(current["rpm"], previous["rpm"])
            self.assertGreater(current["thrust_n"], previous["thrust_n"])

    def test_torque_balance(self) -> None:
        point = solve_operating_point(self.params, 22.2, 0.6)
        motor_torque = self.params.kt * point["current_a"]
        expected = point["torque_nm"] + self.params.kt * self.params.no_load_current_a
        self.assertAlmostEqual(motor_torque, expected, delta=1e-3 * max(expected, 1e-9))

    def test_rpm_below_no_load_bound(self) -> None:
        for voltage in (11.1, 22.2, 29.6):
            point = solve_operating_point(self.params, voltage, 1.0)
            bound = 60.0 * voltage / (self.params.ke * 2.0 * math.pi)
            self.assertLess(point["rpm"], bound)

    def test_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            solve_operating_point(self.params, 0.0, 0.5)
        with self.assertRaises(ValueError):
            solve_operating_point(self.params, -1.0, 0.5)
        with self.assertRaises(ValueError):
            solve_operating_point(self.params, 22.2, 0.0)
        with self.assertRaises(ValueError):
            solve_operating_point(self.params, 22.2, 1.1)

    def test_air_density_matches_processing_formula(self) -> None:
        self.assertTrue(
            math.isclose(
                air_density(24.0, 96.0),
                air_density_from_conditions(24.0, 96.0),
                rel_tol=1e-12,
            )
        )


class CampaignTests(unittest.TestCase):
    """仿真战役闭环（临时目录，不污染 data/）。"""

    def test_campaign_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            result = sc.run_campaign(
                [11.1],
                [25, 100],
                repeats=1,
                duration_s=0.8,
                sample_rate=1000.0,
                window_s=0.4,
                raw_dir=work / "raw",
                processed_dir=work / "processed",
                metadata_dir=work / "metadata",
                figures_dir=work / "figures",
                make_plot=False,
                base_seed=7,
            )
            self.assertEqual(len(result["rows"]), 2)
            self.assertTrue(result["runs_csv"].exists())
            self.assertTrue(result["grid_csv"].exists())
            self.assertTrue(result["summary_csv"].exists())
            self.assertTrue(result["calibration"].exists())
            self.assertIsNone(result["figure"])

            with (work / "metadata" / "20261119_SIM_11.1V_25pct_R1_efficiency.json").open(encoding="utf-8") as handle:
                summary = json.load(handle)
            self.assertTrue(summary["simulated"])
            with (work / "raw" / "20261119_SIM_11.1V_25pct_R1.meta.json").open(encoding="utf-8") as handle:
                meta = json.load(handle)
            self.assertTrue(meta["simulated"])
            self.assertEqual(meta["mode"], "simulate")

            thrust_row = next(row for row in result["rows"] if row["throttle_set_pct"] == 100)
            self.assertLess(abs(thrust_row["thrust_rel_err"]), 0.01)
            self.assertLess(abs(thrust_row["rpm_rel_err"]), 0.01)
            self.assertLess(abs(thrust_row["eta_sys_rel_err"]), 0.02)

    def test_campaign_refuses_overwrite_and_force_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            kwargs = dict(
                duration_s=0.6,
                sample_rate=1000.0,
                window_s=0.3,
                raw_dir=work / "raw",
                processed_dir=work / "processed",
                metadata_dir=work / "metadata",
                figures_dir=work / "figures",
                make_plot=False,
            )
            sc.run_campaign([11.1], [50], base_seed=3, **kwargs)
            with self.assertRaises(FileExistsError):
                sc.run_campaign([11.1], [50], base_seed=3, **kwargs)
            result = sc.run_campaign([11.1], [50], base_seed=4, force=True, **kwargs)
            self.assertEqual(len(result["rows"]), 1)

    def test_calibration_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calib = Path(tmp) / "calib.json"
            bad = sc.build_calibration(ModelParams(), "2026-11-19T00:00:00+08:00")
            bad["thrust"]["k"] = 0.00099
            calib.parent.mkdir(parents=True, exist_ok=True)
            with calib.open("w", encoding="utf-8") as handle:
                json.dump(bad, handle, ensure_ascii=False)
            with self.assertRaises(ValueError):
                sc.ensure_calibration(calib, ModelParams())


class PackModelTests(unittest.TestCase):
    """v0.2 电池内阻压降 + 电机温升反馈的物理自检（非实测精度）。"""

    def setUp(self) -> None:
        self.params = ModelParams()

    def test_pack_voltage_drops_below_open_circuit(self) -> None:
        pack = PackModel(cells=6)
        point = solve_operating_point(self.params, 22.2, 1.0, pack=pack)
        self.assertLess(point["bus_voltage_v"], 22.2)
        self.assertGreater(point["voltage_sag_v"], 0.0)
        self.assertGreater(point["battery_current_a"], 0.0)
        self.assertTrue(
            math.isclose(
                point["battery_current_a"],
                point["p_elec_w"] / point["bus_voltage_v"],
                rel_tol=1e-7,
            )
        )

    def test_sag_and_temperature_monotonic_with_throttle(self) -> None:
        pack = PackModel(cells=6)
        points = [solve_operating_point(self.params, 22.2, throttle, pack=pack) for throttle in (0.25, 0.5, 0.75, 1.0)]
        for previous, current in zip(points, points[1:]):
            self.assertGreater(current["voltage_sag_v"], previous["voltage_sag_v"])
            self.assertGreater(current["motor_temp_c"], previous["motor_temp_c"])
            self.assertGreater(current["winding_resistance_ohm"], self.params.resistance_ohm)

    def test_pack_efficiency_not_above_ideal(self) -> None:
        pack = PackModel(cells=6)
        for throttle in (0.25, 0.5, 0.75, 1.0):
            ideal = solve_operating_point(self.params, 22.2, throttle)
            packed = solve_operating_point(self.params, 22.2, throttle, pack=pack)
            self.assertLess(packed["eta_sys"], ideal["eta_sys"])
            self.assertLess(packed["bus_voltage_v"], ideal["voltage_v"])
            self.assertGreater(packed["motor_temp_c"], self.params.ambient_temp_c)

    def test_pack_disabled_equals_v01(self) -> None:
        ideal = solve_operating_point(self.params, 22.2, 0.5)
        self.assertEqual(ideal["voltage_v"], 22.2)
        self.assertNotIn("bus_voltage_v", ideal)

    def test_pack_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            solve_operating_point(self.params, 22.2, 0.5, pack=PackModel(cells=0))
        with self.assertRaises(ValueError):
            solve_operating_point(self.params, 22.2, 0.5, pack=PackModel(cell_internal_resistance_ohm=-0.01))

    def test_sensitivity_matrix_and_outputs(self) -> None:
        rows = spm.build_rows()
        self.assertEqual(len(rows), len(spm.VOLTAGES) * len(spm.THROTTLES))
        for row in rows:
            self.assertLess(row["eta_sys_pack"], row["eta_sys_ideal"])
            self.assertGreaterEqual(row["delta_eta_sys"], -0.05)
            self.assertTrue(0.0 < row["sag_pct_of_oc"] < 15.0)
        self.assertEqual(spm.cells_for_voltage(22.2), 6)
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            csv_path = spm.write_csv(rows, work / "sensitivity.csv")
            self.assertTrue(csv_path.exists())
            from plot_efficiency_map import read_runs  # noqa: E402

            self.assertEqual(len(read_runs(csv_path)), len(rows))
            png = spm.plot_impact(rows, work / "impact.png")
            self.assertTrue(png.exists())
            self.assertGreater(png.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                spm.plot_impact(rows, work / "impact.png")


if __name__ == "__main__":
    unittest.main()
