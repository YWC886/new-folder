# -*- coding: utf-8 -*-
"""采集链路最小回归测试；只用 Python 标准库。"""
from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from acquire import DEVICE_FIELDS, RAW_FIELDS, acquire, parse_device_line
from validate import validate_file


class DeviceLineTests(unittest.TestCase):
    def test_header_blank_and_valid_row(self) -> None:
        self.assertIsNone(parse_device_line(",".join(DEVICE_FIELDS)))
        self.assertIsNone(parse_device_line("  "))
        row = parse_device_line("0,0,28000,17000,6000,22.2,8.0,35,24,45,96")
        self.assertEqual(row["seq"], "0")
        self.assertEqual(row["thrust_raw"], "28000")

    def test_optional_channels_may_be_blank(self) -> None:
        row = parse_device_line("1,10,28001,,,,,,,,")
        self.assertEqual(row["rpm"], "")

    def test_bad_columns_and_nonfinite_values_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "列数"):
            parse_device_line("0,0,28000")
        with self.assertRaisesRegex(ValueError, "NaN"):
            parse_device_line("0,0,28000,,,NaN,,,,,")


class AcquisitionTests(unittest.TestCase):
    def test_simulation_metadata_validation_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            csv_path, metadata_path, rows = acquire(
                mode="simulate",
                output_dir=temporary,
                run_id="TEST_SIM_22V2_50pct_R1",
                duration=0.2,
                sample_rate=100,
                seed=7,
                combo="DEMO",
                voltage_set=22.2,
                throttle_set=50,
                prop_diameter_m=0.4572,
            )
            self.assertEqual(rows, 20)
            self.assertTrue(csv_path.exists())
            with metadata_path.open(encoding="utf-8") as handle:
                metadata = json.load(handle)
            self.assertTrue(metadata["simulated"])
            self.assertEqual(metadata["status"], "completed")

            report = validate_file(csv_path, window_s=0.1, min_sample_rate=99)
            self.assertEqual(report["rows"], 20)
            self.assertEqual(report["errors"], [])
            self.assertAlmostEqual(report["estimated_sample_rate_sps"], 100.0)
            self.assertTrue(report["simulated"])

            with self.assertRaises(FileExistsError):
                acquire(mode="simulate", output_dir=temporary, run_id="TEST_SIM_22V2_50pct_R1")

    def test_validator_detects_sequence_gap_and_time_reversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "broken.csv"
            with path.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
                writer.writeheader()
                for index, (seq, device_time) in enumerate(((0, 0), (2, 10), (4, 20), (1, 9))):
                    row = {name: "" for name in RAW_FIELDS}
                    row.update({
                        "host_ts": f"2026-11-17T20:00:0{index}+08:00",
                        "elapsed_s": str(index / 100),
                        "seq": str(seq),
                        "device_time_ms": str(device_time),
                        "thrust_raw": "28000",
                    })
                    writer.writerow(row)
            report = validate_file(path)
            self.assertEqual(report["status"], "fail")
            self.assertTrue(any("序号缺号" in error for error in report["errors"]))
            self.assertTrue(any("序号非严格递增" in error for error in report["errors"]))
            self.assertTrue(any("非单调" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
