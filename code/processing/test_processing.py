# -*- coding: utf-8 -*-
r"""compute_efficiency.py 的回归测试：用合成 CSV + 合成标定验证公式、标记与文件保护。

运行：
    py -3.12 -m unittest discover -s code\processing -p "test_*.py" -v
"""
from __future__ import annotations

import csv
import json
import math
import tempfile
import unittest
from pathlib import Path

from compute_efficiency import (
    DEFAULT_AIR_DENSITY,
    OUTPUT_FIELDS,
    RAW_FIELDS,
    air_density_from_conditions,
    compute_efficiency,
    load_calibration,
)

AMBIENT_C = 24.0
PRESSURE_KPA = 96.0
PROP_DIAMETER_M = 0.4572


def expected_air_density() -> float:
    return PRESSURE_KPA * 1000.0 / (287.05 * (AMBIENT_C + 273.15))


def write_raw_csv(path: Path, rows: int = 1000, sample_rate: float = 1000.0) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
        writer.writeheader()
        for index in range(rows):
            device_ms = int(round(index * 1000.0 / sample_rate))
            writer.writerow(
                {
                    "host_ts": f"2026-11-19T20:00:{index % 60:02d}.{index % 1000:03d}+08:00",
                    "elapsed_s": f"{index / sample_rate:.6f}",
                    "seq": str(index),
                    "device_time_ms": str(device_ms),
                    "thrust_raw": "28000.000",
                    "torque_raw": "17000.000",
                    "rpm": "6000.000",
                    "voltage_v": "22.20000",
                    "current_a": "8.00000",
                    "motor_temp_c": "35.000",
                    "ambient_temp_c": f"{AMBIENT_C:.3f}",
                    "humidity_pct": "45.000",
                    "pressure_kpa": f"{PRESSURE_KPA:.3f}",
                }
            )


def write_ramp_then_steady_csv(path: Path, ramp_rows: int = 400, steady_rows: int = 600, sample_rate: float = 1000.0) -> None:
    """前 ramp_rows 行推力线性爬升，之后恒定（用于验证稳态自动识别跳过斜坡）。"""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
        writer.writeheader()
        for index in range(ramp_rows + steady_rows):
            thrust = 20000.0 + 8000.0 * index / max(1, ramp_rows - 1) if index < ramp_rows else 28000.0
            writer.writerow(
                {
                    "host_ts": f"2026-11-19T20:00:00.{index % 1000:03d}+08:00",
                    "elapsed_s": f"{index / sample_rate:.6f}",
                    "seq": str(index),
                    "device_time_ms": str(int(round(index * 1000.0 / sample_rate))),
                    "thrust_raw": f"{thrust:.3f}",
                    "torque_raw": "17000.000",
                    "rpm": "6000.000",
                    "voltage_v": "22.20000",
                    "current_a": "8.00000",
                    "motor_temp_c": "35.000",
                    "ambient_temp_c": f"{AMBIENT_C:.3f}",
                    "humidity_pct": "45.000",
                    "pressure_kpa": f"{PRESSURE_KPA:.3f}",
                }
            )


def write_alternating_csv(path: Path, rows: int = 1000, sample_rate: float = 1000.0) -> None:
    """推力高低交替（无稳态段），用于验证自动识别回退行为。"""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
        writer.writeheader()
        for index in range(rows):
            writer.writerow(
                {
                    "host_ts": f"2026-11-19T20:00:00.{index % 1000:03d}+08:00",
                    "elapsed_s": f"{index / sample_rate:.6f}",
                    "seq": str(index),
                    "device_time_ms": str(int(round(index * 1000.0 / sample_rate))),
                    "thrust_raw": "32000" if index % 2 == 0 else "24000",
                    "torque_raw": "17000.000",
                    "rpm": "6000.000",
                    "voltage_v": "22.20000",
                    "current_a": "8.00000",
                    "motor_temp_c": "35.000",
                    "ambient_temp_c": f"{AMBIENT_C:.3f}",
                    "humidity_pct": "45.000",
                    "pressure_kpa": f"{PRESSURE_KPA:.3f}",
                }
            )


def write_calibration(path: Path, simulated: bool = True, include_torque: bool = True) -> None:
    data = {
        "schema_version": "0.1",
        "simulated": simulated,
        "source": "unittest 合成标定",
        "thrust": {"k": 0.00035, "b": 0.0},
        "propeller": {"diameter_m": PROP_DIAMETER_M},
    }
    if include_torque:
        data["torque"] = {"k": 0.1 / 17000.0, "b": 0.0}
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class ComputeEfficiencyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.csv_path = self.root / "20261119_SIM_TEST_R1.csv"
        self.calib_path = self.root / "calib.json"
        write_raw_csv(self.csv_path)
        write_calibration(self.calib_path)
        self.out_csv = self.root / "out" / "processed.csv"
        self.out_json = self.root / "out" / "efficiency.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_pipeline(self, **kwargs) -> dict:
        params = dict(output_csv=self.out_csv, summary_json=self.out_json, window_s=1.0)
        params.update(kwargs)
        return compute_efficiency(self.csv_path, self.calib_path, **params)

    def test_thrust_torque_and_efficiencies(self) -> None:
        summary = self.run_pipeline()
        window = summary["window"]
        self.assertAlmostEqual(window["thrust_N"]["mean"], 9.8, places=6)
        self.assertAlmostEqual(window["torque_Nm"]["mean"], 0.1, places=9)
        self.assertAlmostEqual(window["rpm"]["mean"], 6000.0, places=6)

        omega = 2.0 * math.pi * 6000.0 / 60.0
        p_shaft = 0.1 * omega
        p_elec = 22.2 * 8.0
        rho = expected_air_density()
        area = math.pi * PROP_DIAMETER_M**2 / 4.0
        p_ideal = 9.8**1.5 / math.sqrt(2.0 * rho * area)
        self.assertAlmostEqual(window["p_shaft_w"]["mean"], p_shaft, places=6)
        self.assertAlmostEqual(window["p_elec_w"]["mean"], p_elec, places=6)
        self.assertAlmostEqual(window["eta_em"]["mean"], p_shaft / p_elec, places=9)
        self.assertAlmostEqual(window["fm"]["mean"], p_ideal / p_shaft, places=9)
        self.assertAlmostEqual(window["eta_sys"]["mean"], p_ideal / p_elec, places=9)
        self.assertGreater(window["eta_sys"]["mean"], 0.2)
        self.assertLess(window["eta_sys"]["mean"], 0.35)

    def test_simulated_flag_and_outputs(self) -> None:
        summary = self.run_pipeline()
        self.assertTrue(summary["simulated"])
        self.assertIn("模拟数据", summary["data_notice"])
        self.assertTrue(self.out_csv.exists())
        self.assertTrue(self.out_json.exists())
        self.assertIn("eta_sys", summary["window"])

        with self.out_csv.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(reader.fieldnames, OUTPUT_FIELDS)
            rows = list(reader)
        self.assertEqual(len(rows), 1000)
        self.assertAlmostEqual(float(rows[-1]["thrust_N"]), 9.8, places=6)

    def test_air_density_formula(self) -> None:
        rho = air_density_from_conditions(20.0, 101.325)
        self.assertAlmostEqual(rho, 1.2041, places=3)
        self.assertGreater(air_density_from_conditions(40.0, 101.325), 1.05)
        with self.assertRaises(ValueError):
            air_density_from_conditions(-300.0, 101.325)
        with self.assertRaises(ValueError):
            air_density_from_conditions(20.0, 0.0)

    def test_default_density_when_no_env_channel(self) -> None:
        path = self.root / "no_env.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
            writer.writeheader()
            writer.writerow(
                {
                    "host_ts": "2026-11-19T20:00:00+08:00",
                    "elapsed_s": "0.000",
                    "seq": "0",
                    "device_time_ms": "0",
                    "thrust_raw": "28000",
                    "torque_raw": "17000",
                    "rpm": "6000",
                    "voltage_v": "22.2",
                    "current_a": "8.0",
                    "motor_temp_c": "35",
                    "ambient_temp_c": "",
                    "humidity_pct": "",
                    "pressure_kpa": "",
                }
            )
            writer.writerow(
                {
                    "host_ts": "2026-11-19T20:00:01+08:00",
                    "elapsed_s": "1.000",
                    "seq": "1",
                    "device_time_ms": "1000",
                    "thrust_raw": "28000",
                    "torque_raw": "17000",
                    "rpm": "6000",
                    "voltage_v": "22.2",
                    "current_a": "8.0",
                    "motor_temp_c": "35",
                    "ambient_temp_c": "",
                    "humidity_pct": "",
                    "pressure_kpa": "",
                }
            )
        summary = compute_efficiency(path, self.calib_path, window_s=2.0, output_csv=self.root / "p.csv", summary_json=self.root / "s.json")
        self.assertAlmostEqual(summary["assumptions"]["air_density_kg_m3"], DEFAULT_AIR_DENSITY, places=9)

    def test_missing_torque_calibration_rejected(self) -> None:
        bad_calib = self.root / "bad_calib.json"
        write_calibration(bad_calib, include_torque=False)
        with self.assertRaises(ValueError):
            compute_efficiency(self.csv_path, bad_calib, window_s=1.0, output_csv=self.root / "a.csv", summary_json=self.root / "a.json")

    def test_missing_pipeline_channel_rejected(self) -> None:
        bad_csv = self.root / "missing_thrust.csv"
        with bad_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
            writer.writeheader()
            writer.writerow(
                {
                    "host_ts": "2026-11-19T20:00:00+08:00",
                    "elapsed_s": "0.000",
                    "seq": "0",
                    "device_time_ms": "0",
                    "thrust_raw": "",
                    "torque_raw": "17000",
                    "rpm": "6000",
                    "voltage_v": "22.2",
                    "current_a": "8.0",
                    "motor_temp_c": "35",
                    "ambient_temp_c": "24",
                    "humidity_pct": "45",
                    "pressure_kpa": "96",
                }
            )
        with self.assertRaises(ValueError):
            compute_efficiency(bad_csv, self.calib_path, window_s=1.0, output_csv=self.root / "b.csv", summary_json=self.root / "b.json")

    def test_outputs_not_overwritten_by_default(self) -> None:
        self.run_pipeline()
        with self.assertRaises(FileExistsError):
            self.run_pipeline()
        summary = self.run_pipeline(overwrite=True)
        self.assertIn("processed_csv", summary["_outputs"])

    def test_load_calibration_units(self) -> None:
        calib = load_calibration(self.calib_path)
        self.assertEqual(calib["thrust"]["k"], 0.00035)
        self.assertAlmostEqual(calib["diameter_m"], PROP_DIAMETER_M)
        self.assertTrue(calib["simulated"])

    def test_auto_steady_detection_skips_ramp(self) -> None:
        path = self.root / "ramp.csv"
        write_ramp_then_steady_csv(path, ramp_rows=400, steady_rows=600)
        summary = compute_efficiency(
            path,
            self.calib_path,
            window_s=1.0,
            steady_mode="auto",
            steady_window_s=0.3,
            steady_threshold=0.01,
            output_csv=self.root / "ramp_processed.csv",
            summary_json=self.root / "ramp_efficiency.json",
        )
        window = summary["window"]
        self.assertEqual(window["mode"], "auto")
        detection = window["detection"]
        self.assertTrue(detection["applied"])
        self.assertGreaterEqual(detection["start_s"], 0.35)
        self.assertAlmostEqual(detection["duration_s"], 0.3, delta=0.05)
        self.assertAlmostEqual(window["thrust_N"]["mean"], 9.8, places=6)

    def test_auto_steady_falls_back_on_no_signal(self) -> None:
        path = self.root / "alternating.csv"
        write_alternating_csv(path)
        summary = compute_efficiency(
            path,
            self.calib_path,
            window_s=1.0,
            steady_mode="auto",
            steady_window_s=0.05,
            steady_threshold=0.001,
            output_csv=self.root / "alt_processed.csv",
            summary_json=self.root / "alt_efficiency.json",
        )
        detection = summary["window"]["detection"]
        self.assertFalse(detection["applied"])
        self.assertTrue(any("回退" in warning for warning in summary["warnings"]))

    def test_steady_last_mode_metadata(self) -> None:
        summary = self.run_pipeline()
        window = summary["window"]
        self.assertEqual(window["mode"], "last")
        self.assertAlmostEqual(window["requested_window_s"], 1.0, places=6)
        self.assertAlmostEqual(window["window_s"], 1.0, delta=0.002)
        self.assertIsNotNone(window["start_s"])
        self.assertGreaterEqual(window["end_s"], window["start_s"])

    def test_uncertainty_block(self) -> None:
        summary = self.run_pipeline()
        uncertainty = summary["uncertainty"]
        expected_eta_em = 2.0 * math.sqrt(0.005**2 + 0.001**2 + 0.001**2 + 0.005**2)
        expected_fm = 2.0 * math.sqrt((1.5 * 0.0065) ** 2 + 0.005**2 + 0.001**2 + (0.5 * 0.005) ** 2)
        expected_eta_sys = 2.0 * math.sqrt((1.5 * 0.0065) ** 2 + (0.5 * 0.005) ** 2 + 0.001**2 + 0.005**2)
        self.assertAlmostEqual(uncertainty["U_rel_eta_em_k2"], expected_eta_em, delta=1e-9)
        self.assertAlmostEqual(uncertainty["U_rel_fm_k2"], expected_fm, delta=1e-9)
        self.assertAlmostEqual(uncertainty["U_rel_eta_sys_k2"], expected_eta_sys, delta=1e-9)
        self.assertAlmostEqual(uncertainty["U_rel_eta_sys_k2"], 0.022565, delta=2e-5)
        self.assertIn("note", uncertainty)


if __name__ == "__main__":
    unittest.main()
