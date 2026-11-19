"""双节点热网络 v0.4 测试。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import transient_thermal as tt  # noqa: E402
import two_node_thermal as tn  # noqa: E402

AMBIENT = 24.0


class TwoNodeTests(unittest.TestCase):
    def test_steady_state_matches_single_node(self) -> None:
        profile = tn.duty_profile(5.0, 1.0, heat_s=1500.0)
        rows = tn.simulate_two_node(
            voltage_v=22.2, throttle_fn=profile, duration_s=1500.0, dt_s=1.0
        )
        last_heat = [r for r in rows if r["throttle"] > 0.0][-1]
        single = tt.simulate_transient(
            voltage_v=22.2,
            throttle_fn=profile,
            duration_s=1500.0,
            dt_s=1.0,
            thermal=tt.ThermalParams(thermal_capacitance_j_per_k=45.0),
        )
        # 绕组稳态温度等于"总热阻 2.5 K/W"的单节点结果
        self.assertAlmostEqual(
            last_heat["winding_temp_c"], single[-1]["motor_temp_c"], delta=0.5
        )
        # 定子稳态温度 = 环境 + 热流 × R_sa（双节点分配）
        thermal = tn.TwoNodeParams()
        expected_stator = AMBIENT + last_heat["heat_w"] * thermal.stator_to_ambient_r_k_per_w
        self.assertAlmostEqual(last_heat["stator_temp_c"], expected_stator, delta=0.5)
        self.assertGreater(last_heat["winding_temp_c"], AMBIENT + 40.0)

    def test_winding_hotter_than_stator_during_heating(self) -> None:
        profile = tn.duty_profile(2.0, 1.0, heat_s=120.0)
        rows = tn.simulate_two_node(voltage_v=22.2, throttle_fn=profile, duration_s=120.0, dt_s=0.5)
        mid = [r for r in rows if 60.0 <= r["t_s"] <= 100.0]
        self.assertTrue(mid)
        for row in mid:
            self.assertGreater(row["winding_temp_c"], row["stator_temp_c"])
            self.assertGreater(row["stator_temp_c"], AMBIENT)

    def test_cooling_returns_toward_ambient(self) -> None:
        profile = tn.duty_profile(2.0, 1.0, heat_s=120.0)
        rows = tn.simulate_two_node(voltage_v=22.2, throttle_fn=profile, duration_s=420.0, dt_s=0.5)
        heat = [r for r in rows if r["t_s"] <= 120.0]
        cool = [r for r in rows if r["t_s"] > 120.0]
        peak = max(r["winding_temp_c"] for r in heat)
        self.assertGreater(peak, 60.0)
        # 冷却段整体单调下降（允许极小的数值抖动）
        prev = peak
        for row in cool[::20]:
            self.assertLessEqual(row["winding_temp_c"], prev + 1e-6)
            prev = row["winding_temp_c"]
        self.assertLess(cool[-1]["winding_temp_c"], 30.0)
        self.assertLess(cool[-1]["stator_temp_c"], 30.0)

    def test_energy_balance_at_steady_state(self) -> None:
        profile = tn.duty_profile(5.0, 1.0, heat_s=1500.0)
        rows = tn.simulate_two_node(voltage_v=22.2, throttle_fn=profile, duration_s=1500.0, dt_s=1.0)
        last = [r for r in rows if r["throttle"] > 0.0][-1]
        thermal = tn.TwoNodeParams()
        q_ws = (last["winding_temp_c"] - last["stator_temp_c"]) / thermal.winding_to_stator_r_k_per_w
        q_sa = (last["stator_temp_c"] - AMBIENT) / thermal.stator_to_ambient_r_k_per_w
        self.assertAlmostEqual(q_ws / last["heat_w"], 1.0, delta=0.02)
        self.assertAlmostEqual(q_sa / last["heat_w"], 1.0, delta=0.02)
        # 总热阻/热容与 v0.3 一致
        self.assertAlmostEqual(thermal.total_resistance_k_per_w, 2.5, delta=1e-9)
        self.assertAlmostEqual(thermal.total_capacitance_j_per_k, 45.0, delta=1e-9)

    def test_invalid_parameters(self) -> None:
        profile = tn.duty_profile(1.0, 1.0, 10.0)
        base = {"throttle_fn": profile, "duration_s": 10.0}
        with self.assertRaises(ValueError):
            tn.simulate_two_node(
                voltage_v=22.2,
                **base,
                thermal=tn.TwoNodeParams(winding_capacitance_j_per_k=0.0),
            )
        with self.assertRaises(ValueError):
            tn.simulate_two_node(
                voltage_v=22.2,
                **base,
                thermal=tn.TwoNodeParams(winding_to_stator_r_k_per_w=0.0),
            )
        with self.assertRaises(ValueError):
            tn.simulate_two_node(voltage_v=22.2, **base, dt_s=0.0)
        with self.assertRaises(ValueError):
            tn.simulate_two_node(voltage_v=0.0, **base)
        with self.assertRaises(ValueError):
            tn.duty_profile(1.0, 1.0, heat_s=0.0)
        with self.assertRaises(ValueError):
            tn.duty_profile(1.0, 0.0, heat_s=10.0)

    def test_csv_and_plot_outputs(self) -> None:
        profile = tn.duty_profile(1.0, 1.0, heat_s=5.0)
        rows = tn.simulate_two_node(voltage_v=22.2, throttle_fn=profile, duration_s=10.0, dt_s=1.0)
        self.assertEqual(len(rows), 11)
        self.assertEqual(list(rows[0].keys()), tn.FIELDS)
        self.assertTrue(all(r["data_notice"] == tn.DATA_NOTICE for r in rows))
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "out.csv"
            tn.write_csv(rows, csv_path)
            text = csv_path.read_text(encoding="utf-8")
            self.assertEqual(text.splitlines()[0].split(","), tn.FIELDS)
            self.assertEqual(len(text.strip().splitlines()), 12)
            with self.assertRaises(FileExistsError):
                tn.write_csv(rows, csv_path)
            png = Path(tmp) / "out.png"
            ref = [r["winding_temp_c"] for r in rows]
            tn.plot_two_node(rows, png, single_node=ref)
            self.assertGreater(png.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                tn.plot_two_node(rows, png, overwrite=False)

    def test_duty_profile(self) -> None:
        profile = tn.duty_profile(10.0, 0.8, heat_s=40.0)
        self.assertAlmostEqual(profile(0.0), 0.0)
        self.assertAlmostEqual(profile(5.0), 0.4)
        self.assertAlmostEqual(profile(20.0), 0.8)
        self.assertAlmostEqual(profile(40.0), 0.0)

    def test_main_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo.csv"
            png = Path(tmp) / "demo.png"
            argv = [
                "--voltage",
                "22.2",
                "--heat-s",
                "12",
                "--cool-s",
                "8",
                "--dt",
                "1.0",
                "--output",
                str(out),
                "--figure",
                str(png),
            ]
            code = tn.main(argv)
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())
            self.assertGreater(png.stat().st_size, 10_000)
            # 无 --overwrite 时再次运行应拒绝
            self.assertEqual(tn.main(argv), 2)
            self.assertEqual(tn.main(argv + ["--overwrite"]), 0)


if __name__ == "__main__":
    unittest.main()
