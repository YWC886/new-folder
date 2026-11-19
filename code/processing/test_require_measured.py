"""`compute_efficiency --require-measured` 守门测试（v0.5，D035/D036）。"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import compute_efficiency as ce  # noqa: E402

SIM_RAW = PROJECT_ROOT / "data" / "raw" / "20261117_SIM_22V2_50pct_R1.csv"
SIM_CALIB = PROJECT_ROOT / "data" / "metadata" / "calib_SIM_DEMO.json"


def _calibration() -> dict:
    return {
        "schema_version": "0.1",
        "simulated": False,
        "source": "测试用读数（双人砝码标定）",
        "thrust": {"k": 0.00035, "b": 0.0},
        "torque": {"k": 5.882352941176471e-06, "b": 0.0},
        "propeller": {"diameter_m": 0.4572},
    }


def _meta() -> dict:
    return {
        "schema_version": "0.1",
        "run_id": "TEST_MEASURED",
        "status": "ok",
        "mode": "serial",
        "simulated": False,
        "rows_written": 600,
        "csv_file": "TEST_MEASURED.csv",
        "test": {"operator": "张三、李四", "prop_diameter_m": 0.4572},
    }


def _write_fixture(root: Path) -> tuple[Path, Path]:
    raw = root / "TEST_MEASURED.csv"
    with raw.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(ce.RAW_FIELDS))
        writer.writeheader()
        for i in range(600):
            row = {field: "" for field in ce.RAW_FIELDS}
            row.update(
                {
                    "host_ts": f"2026-11-20T10:00:{i // 1000:02d}+08:00",
                    "elapsed_s": f"{i / 1000.0:.6f}",
                    "seq": i,
                    "device_time_ms": i,
                    "thrust_raw": 28000,
                    "torque_raw": 17000,
                    "rpm": 6000,
                    "voltage_v": 22.2,
                    "current_a": 8.0,
                    "motor_temp_c": 35.0,
                    "ambient_temp_c": 24.0,
                    "humidity_pct": 45.0,
                    "pressure_kpa": 96.0,
                }
            )
            writer.writerow(row)
    calib = root / "calib.json"
    calib.write_text(json.dumps(_calibration(), ensure_ascii=False), encoding="utf-8")
    raw.with_suffix(".meta.json").write_text(json.dumps(_meta(), ensure_ascii=False), encoding="utf-8")
    return raw, calib


class RequireMeasuredTests(unittest.TestCase):
    def test_sim_input_refused(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            ce.compute_efficiency(
                SIM_RAW,
                SIM_CALIB,
                window_s=1.0,
                output_csv=None,
                summary_json=None,
                require_measured=True,
            )
        self.assertIn("MEASURED 守门拒绝", str(ctx.exception))

    def test_measured_fixture_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, calib = _write_fixture(root)
            summary = ce.compute_efficiency(
                raw,
                calib,
                window_s=0.5,
                output_csv=root / "out.csv",
                summary_json=root / "out.json",
                require_measured=True,
            )
        self.assertFalse(summary["simulated"])
        self.assertIn("uncertainty", summary)
        self.assertAlmostEqual(summary["window"]["thrust_N"]["mean"], 9.8, places=6)

    def test_sim_input_allowed_without_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = ce.compute_efficiency(
                SIM_RAW,
                SIM_CALIB,
                window_s=1.0,
                output_csv=root / "out.csv",
                summary_json=root / "out.json",
                require_measured=False,
            )
        self.assertTrue(summary["simulated"])

    def test_calibration_simulated_true_refused(self) -> None:
        calibration = _calibration()
        calibration["simulated"] = True
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw, _ = _write_fixture(root)
            calib = root / "calib_sim.json"
            calib.write_text(json.dumps(calibration, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                ce.compute_efficiency(
                    raw,
                    calib,
                    window_s=0.5,
                    output_csv=root / "out.csv",
                    summary_json=root / "out.json",
                    require_measured=True,
                )
        self.assertIn("标定 simulated 必须为 false", str(ctx.exception))

    def test_cli_parser_flag_wired(self) -> None:
        args = ce.build_parser().parse_args(
            ["--input", "a.csv", "--calib", "b.json", "--require-measured"]
        )
        self.assertTrue(args.require_measured)
        args_default = ce.build_parser().parse_args(["--input", "a.csv", "--calib", "b.json"])
        self.assertFalse(args_default.require_measured)


if __name__ == "__main__":
    unittest.main()
