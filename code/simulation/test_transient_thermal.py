"""transient_thermal v0.3 测试（SIM）。"""

from __future__ import annotations

import csv
import math
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import propulsion_model as pm  # noqa: E402
import transient_thermal as tt  # noqa: E402


class TransientThermalTests(unittest.TestCase):
    def test_steady_state_converges_to_v02(self) -> None:
        """长时间恒油门后温度应接近 v0.2 稳态解。"""
        model = pm.ModelParams()
        pack = pm.PackModel(cells=6)
        fn = tt.ramp_profile(0.0, 1.0)
        rows = tt.simulate_transient(
            model, pack, voltage_v=22.2, throttle_fn=fn, duration_s=900.0, dt_s=1.0
        )
        steady = pm.solve_operating_point(model, 22.2, 1.0, pack=pack)
        self.assertAlmostEqual(rows[-1]["motor_temp_c"], steady["motor_temp_c"], delta=1.0)

    def test_temperature_monotonic_while_heating(self) -> None:
        rows = tt.simulate_transient(voltage_v=22.2, throttle_fn=tt.ramp_profile(0.0, 1.0), duration_s=120.0, dt_s=1.0)
        temps = [r["motor_temp_c"] for r in rows]
        self.assertGreater(temps[-1], temps[0])
        for a, b in zip(temps, temps[1:]):
            self.assertGreaterEqual(b, a - 1e-9)

    def test_time_constant_order_of_magnitude(self) -> None:
        """一阶系统：温升达到 63.2% 的时间应接近 R_th·C_th。"""
        pack = pm.PackModel(cells=6)
        thermal = tt.ThermalParams(thermal_capacitance_j_per_k=45.0)
        tau = pack.motor_thermal_resistance_k_per_w * thermal.thermal_capacitance_j_per_k
        rows = tt.simulate_transient(
            pack=pack,
            thermal=thermal,
            voltage_v=22.2,
            throttle_fn=tt.ramp_profile(0.0, 1.0),
            duration_s=600.0,
            dt_s=1.0,
        )
        t0, t_end = rows[0]["motor_temp_c"], rows[-1]["motor_temp_c"]
        target = t0 + 0.632 * (t_end - t0)
        hit = next(r["t_s"] for r in rows if r["motor_temp_c"] >= target)
        self.assertGreater(hit, 0.7 * tau)
        self.assertLess(hit, 1.4 * tau)

    def test_invalid_inputs(self) -> None:
        fn = tt.ramp_profile(0.0, 1.0)
        with self.assertRaises(ValueError):
            tt.simulate_transient(voltage_v=0.0, throttle_fn=fn)
        with self.assertRaises(ValueError):
            tt.simulate_transient(voltage_v=22.2, throttle_fn=fn, duration_s=0.0)
        with self.assertRaises(ValueError):
            tt.simulate_transient(voltage_v=22.2, throttle_fn=fn, dt_s=0.0)
        with self.assertRaises(ValueError):
            tt.simulate_transient(
                voltage_v=22.2, throttle_fn=fn, thermal=tt.ThermalParams(thermal_capacitance_j_per_k=0.0)
            )
        with self.assertRaises(ValueError):
            tt.ramp_profile(0.0, 0.0)
        with self.assertRaises(ValueError):
            tt.ramp_profile(-1.0, 0.5)

    def test_csv_and_figure_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = tmp_path / "t.csv"
            png_path = tmp_path / "t.png"
            rows = tt.simulate_transient(voltage_v=22.2, throttle_fn=tt.ramp_profile(1.0, 0.8), duration_s=20.0, dt_s=1.0)
            tt.write_csv(rows, csv_path)
            self.assertTrue(csv_path.exists())
            with csv_path.open(encoding="utf-8") as fh:
                reader = list(csv.DictReader(fh))
            self.assertEqual(len(reader), len(rows))
            self.assertEqual(list(reader[0].keys()), tt.FIELDS)
            with self.assertRaises(FileExistsError):
                tt.write_csv(rows, csv_path)
            tt.plot_transient(rows, png_path)
            self.assertGreater(png_path.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                tt.plot_transient(rows, png_path)

    def test_data_notice_present(self) -> None:
        rows = tt.simulate_transient(voltage_v=22.2, throttle_fn=tt.ramp_profile(0.0, 1.0), duration_s=5.0, dt_s=1.0)
        self.assertTrue(all(r["data_notice"] == tt.DATA_NOTICE for r in rows))
        self.assertIn("仿真", tt.DATA_NOTICE)
        self.assertIn("不是实验结果", tt.DATA_NOTICE)


if __name__ == "__main__":
    unittest.main()
