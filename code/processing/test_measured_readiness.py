"""`measured_readiness` 测试（v0.1，M0.4 门禁）。"""

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
import measured_readiness as mr  # noqa: E402

SIM_RAW = PROJECT_ROOT / "data" / "raw" / "20261117_SIM_22V2_50pct_R1.csv"
SIM_CALIB = PROJECT_ROOT / "data" / "metadata" / "calib_SIM_DEMO.json"


def _valid_calibration() -> dict:
    return {
        "schema_version": "0.1",
        "simulated": False,
        "source": "测试用真实读数（双人砝码标定）",
        "thrust": {"k": 0.00035, "b": 0.0},
        "torque": {"k": 5.882352941176471e-06, "b": 0.0},
        "propeller": {"diameter_m": 0.4572},
    }


def _valid_meta() -> dict:
    return {
        "schema_version": "0.1",
        "run_id": "TEST_MEASURED",
        "status": "ok",
        "mode": "serial",
        "simulated": False,
        "rows_written": 3,
        "csv_file": "TEST_MEASURED.csv",
        "test": {"operator": "张三、李四", "prop_diameter_m": 0.4572},
    }


def _write_raw_csv(path: Path, rows: int = 3) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(ce.RAW_FIELDS))
        writer.writeheader()
        for i in range(rows):
            row = {field: "" for field in ce.RAW_FIELDS}
            row.update(
                {
                    "host_ts": f"2026-11-20T10:00:0{i}+08:00",
                    "elapsed_s": f"{i / 1000.0:.3f}",
                    "seq": i,
                    "device_time_ms": i,
                    "thrust_raw": 28000,
                    "torque_raw": 17000,
                    "rpm": 6000,
                    "voltage_v": 22.2,
                    "current_a": 8.0,
                }
            )
            writer.writerow(row)


def _prepare(tmp: str, *, calibration: dict | None = None, meta: dict | None = None) -> tuple[Path, Path]:
    root = Path(tmp)
    raw = root / "TEST_MEASURED.csv"
    _write_raw_csv(raw)
    calib = root / "calib.json"
    calib.write_text(json.dumps(calibration or _valid_calibration(), ensure_ascii=False), encoding="utf-8")
    meta_path = raw.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta or _valid_meta(), ensure_ascii=False), encoding="utf-8")
    return raw, calib


class ReadinessTests(unittest.TestCase):
    def test_sim_inputs_rejected(self) -> None:
        report = mr.assess(SIM_RAW, SIM_CALIB)
        self.assertFalse(report["ready"])
        joined = " ".join(report["errors"])
        self.assertIn("simulated:false", joined)
        self.assertIn("SIM", joined)

    def test_valid_fixture_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw, calib = _prepare(tmp)
            report = mr.assess(raw, calib)
        self.assertTrue(report["ready"], msg=report["errors"])
        self.assertEqual(report["facts"]["rows"], 3)
        self.assertAlmostEqual(report["facts"]["diameter_m"], 0.4572)

    def test_missing_meta_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw, calib = _prepare(tmp)
            raw.with_suffix(".meta.json").unlink()
            report = mr.assess(raw, calib)
        self.assertFalse(report["ready"])
        self.assertTrue(any("缺少 meta" in item for item in report["errors"]))

    def test_calibration_without_simulated_flag_rejected(self) -> None:
        calibration = _valid_calibration()
        calibration.pop("simulated")
        with tempfile.TemporaryDirectory() as tmp:
            raw, calib = _prepare(tmp, calibration=calibration)
            report = mr.assess(raw, calib)
        self.assertFalse(report["ready"])
        self.assertTrue(any("simulated" in item for item in report["errors"]))

    def test_calibration_zero_k_rejected(self) -> None:
        calibration = _valid_calibration()
        calibration["thrust"]["k"] = 0.0
        with tempfile.TemporaryDirectory() as tmp:
            raw, calib = _prepare(tmp, calibration=calibration)
            report = mr.assess(raw, calib)
        self.assertFalse(report["ready"])
        self.assertTrue(any("thrust.k" in item for item in report["errors"]))

    def test_meta_mode_simulate_rejected(self) -> None:
        meta = _valid_meta()
        meta["mode"] = "simulate"
        with tempfile.TemporaryDirectory() as tmp:
            raw, calib = _prepare(tmp, meta=meta)
            report = mr.assess(raw, calib)
        self.assertFalse(report["ready"])
        self.assertTrue(any("serial" in item for item in report["errors"]))

    def test_missing_required_channel_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw, calib = _prepare(tmp)
            with raw.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            for row in rows:
                row["current_a"] = ""
            with raw.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(ce.RAW_FIELDS))
                writer.writeheader()
                writer.writerows(rows)
            report = mr.assess(raw, calib)
        self.assertFalse(report["ready"])
        self.assertTrue(any("current_a" in item for item in report["errors"]))

    def test_missing_diameter_rejected(self) -> None:
        calibration = _valid_calibration()
        calibration.pop("propeller")
        meta = _valid_meta()
        meta["test"].pop("prop_diameter_m")
        with tempfile.TemporaryDirectory() as tmp:
            raw, calib = _prepare(tmp, calibration=calibration, meta=meta)
            report = mr.assess(raw, calib)
        self.assertFalse(report["ready"])
        self.assertTrue(any("桨径" in item for item in report["errors"]))

    def test_cli_exit_codes_and_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw, calib = _prepare(tmp)
            out = Path(tmp) / "report.json"
            code = mr.main(["--input", str(raw), "--calib", str(calib), "--json", "--output", str(out)])
            self.assertEqual(code, 0)
            report = json.loads(out.read_text(encoding="utf-8"))
        self.assertTrue(report["ready"])
        self.assertEqual(mr.main(["--input", str(SIM_RAW), "--calib", str(SIM_CALIB), "--json"]), 1)

    def test_missing_input_files_not_ready(self) -> None:
        report = mr.assess(PROJECT_ROOT / "no_such.csv", PROJECT_ROOT / "no_such.json")
        self.assertFalse(report["ready"])
        self.assertGreaterEqual(len(report["errors"]), 2)


if __name__ == "__main__":
    unittest.main()
