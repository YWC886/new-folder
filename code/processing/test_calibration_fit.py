"""`code/processing/calibration_fit.py` 测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import calibration_fit as cf  # noqa: E402
import compute_efficiency as ce  # noqa: E402

THRUST_K = 0.00035
TORQUE_K = 5.882352941176471e-06
DIAMETER = 0.4572

THRUST_RAWS = [0, 7000, 14000, 21000, 28000, 35000]
TORQUE_RAWS = [0, 5000, 10000, 17000, 24000]


def _rows(
    *,
    thrust_raw_offsets: dict[tuple[int, int], float] | None = None,
    torque_raw_offsets: dict[tuple[int, int], float] | None = None,
    repeats: tuple[int, ...] = (1, 2),
) -> list[dict]:
    """构造标定长表行；offset 用 (重复序号, 水平序号) 指定额外 raw 偏置。"""
    thrust_raw_offsets = thrust_raw_offsets or {}
    torque_raw_offsets = torque_raw_offsets or {}
    rows: list[dict] = []
    for channel, raws, k, offsets in (
        ("thrust", THRUST_RAWS, THRUST_K, thrust_raw_offsets),
        ("torque", TORQUE_RAWS, TORQUE_K, torque_raw_offsets),
    ):
        for idx, raw in enumerate(raws):
            applied = k * raw
            for direction in ("load", "unload"):
                for repeat in repeats:
                    shift = offsets.get((repeat, idx), 0.0)
                    rows.append(
                        {
                            "channel": channel,
                            "direction": direction,
                            "repeat": repeat,
                            "applied": applied,
                            "raw": raw + shift,
                        }
                    )
    return rows


def write_readings(path: Path, rows: list[dict]) -> None:
    header = "channel,direction,repeat,applied,raw\n"
    body = "\n".join(
        f"{r['channel']},{r['direction']},{r['repeat']},{r['applied']!r},{r['raw']!r}" for r in rows
    )
    path.write_text(header + body + "\n", encoding="utf-8")


class ReadingTests(unittest.TestCase):
    def test_load_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "readings.csv"
            write_readings(path, _rows())
            rows = cf.load_readings(path)
        self.assertEqual(len(rows), (len(THRUST_RAWS) + len(TORQUE_RAWS)) * 2 * 2)
        self.assertEqual({r["channel"] for r in rows}, {"thrust", "torque"})

    def test_load_skips_comments_and_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "readings.csv"
            path.write_text(
                "# 标定读数\nchannel,direction,repeat,applied,raw\n\nthrust,load,1,0,0\nthrust,load,1,1.0,3000\n",
                encoding="utf-8",
            )
            rows = cf.load_readings(path)
        self.assertEqual(len(rows), 2)

    def test_missing_column_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("channel,direction,applied,raw\nthrust,load,0,0\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                cf.load_readings(path)
        self.assertIn("缺少必需列", str(ctx.exception))

    def test_bad_values_raise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text(
                "channel,direction,repeat,applied,raw\n"
                "thrust,load,1,0,0\n"
                "thrust,load,1,abc,3000\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                cf.load_readings(path)

    def test_bad_channel_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text(
                "channel,direction,repeat,applied,raw\nrpm,load,1,0,0\n", encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                cf.load_readings(path)


class FitTests(unittest.TestCase):
    def test_exact_fit_recovers_coefficients(self) -> None:
        calibration = cf.fit_calibration(_rows(), diameter_m=DIAMETER, source="unittest 合成")
        self.assertAlmostEqual(calibration["thrust"]["k"], THRUST_K, places=12)
        self.assertAlmostEqual(calibration["torque"]["k"], TORQUE_K, places=15)
        self.assertAlmostEqual(calibration["thrust"]["b"], 0.0, places=9)
        self.assertAlmostEqual(calibration["torque"]["b"], 0.0, places=12)
        self.assertAlmostEqual(calibration["thrust"]["metrics"]["r2"], 1.0, places=9)
        self.assertEqual(calibration["simulated"], False)
        self.assertEqual(calibration["warnings"], [])

    def test_metrics_scale_and_levels(self) -> None:
        calibration = cf.fit_calibration(_rows(), diameter_m=DIAMETER, source="unittest")
        m = calibration["thrust"]["metrics"]
        self.assertEqual(m["levels"], len(THRUST_RAWS))
        self.assertAlmostEqual(m["full_scale"], THRUST_K * max(THRUST_RAWS))
        self.assertIsNotNone(m["repeatability_pct_fs"])
        self.assertIsNotNone(m["hysteresis_pct_fs"])

    def test_repeatability_and_hysteresis_are_nonzero_with_offsets(self) -> None:
        # 重复 2 在同一水平偏移 +20 counts；卸载整体 +0.3%FS/k。
        offset = 0.003 * (THRUST_K * max(THRUST_RAWS)) / THRUST_K
        rows = _rows(
            thrust_raw_offsets={(2, i): 20.0 for i in range(len(THRUST_RAWS))},
        )
        for row in rows:
            if row["channel"] == "thrust" and row["direction"] == "unload":
                row["raw"] += offset
        calibration = cf.fit_calibration(rows, diameter_m=DIAMETER, source="unittest")
        m = calibration["thrust"]["metrics"]
        self.assertGreater(m["repeatability_pct_fs"], 0.0)
        self.assertGreater(m["hysteresis_pct_fs"], 0.0)
        self.assertEqual(calibration["warnings"], [])

    def test_warning_when_r2_low(self) -> None:
        rows = _rows()
        # 人为破坏若干点，使 R² 显著下降。
        rows[0]["raw"] += 30000
        rows[1]["raw"] += 25000
        calibration = cf.fit_calibration(rows, diameter_m=DIAMETER, source="unittest")
        self.assertTrue(any("R²" in w for w in calibration["warnings"]))

    def test_missing_torque_channel_raises(self) -> None:
        rows = [r for r in _rows() if r["channel"] == "thrust"]
        with self.assertRaises(ValueError):
            cf.fit_calibration(rows, diameter_m=DIAMETER, source="unittest")

    def test_fit_channel_needs_three_points(self) -> None:
        with self.assertRaises(ValueError):
            cf.fit_channel(_rows()[:2], "thrust")


class OutputTests(unittest.TestCase):
    def test_write_and_read_back_via_pipeline(self) -> None:
        calibration = cf.fit_calibration(_rows(), diameter_m=DIAMETER, source="unittest 合成")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "calib.json"
            cf.write_calibration(calibration, out)
            loaded = ce.load_calibration(out)
            raw = json.loads(out.read_text(encoding="utf-8"))
        self.assertAlmostEqual(loaded["thrust"]["k"], THRUST_K, places=12)
        self.assertFalse(loaded["simulated"])
        self.assertAlmostEqual(loaded["diameter_m"], DIAMETER)
        self.assertEqual(raw["thresholds"]["r2_min"], cf.R2_MIN)

    def test_write_refuses_overwrite(self) -> None:
        calibration = cf.fit_calibration(_rows(), diameter_m=DIAMETER, source="unittest")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "calib.json"
            cf.write_calibration(calibration, out)
            with self.assertRaises(FileExistsError):
                cf.write_calibration(calibration, out)
            cf.write_calibration(calibration, out, overwrite=True)


class CliTests(unittest.TestCase):
    def test_main_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            readings = Path(tmp) / "readings.csv"
            write_readings(readings, _rows())
            out = Path(tmp) / "calib.json"
            code = cf.main(
                ["--input", str(readings), "--output", str(out), "--diameter", str(DIAMETER)]
            )
            self.assertEqual(code, 0)
            loaded = ce.load_calibration(out)
            self.assertAlmostEqual(loaded["thrust"]["k"], THRUST_K, places=12)
            # 重复运行且不覆盖 → exit 2
            code2 = cf.main(
                ["--input", str(readings), "--output", str(out), "--diameter", str(DIAMETER)]
            )
            self.assertEqual(code2, 2)

    def test_main_missing_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = cf.main(
                ["--input", str(Path(tmp) / "nope.csv"), "--output", str(Path(tmp) / "o.json"), "--diameter", "0.4"]
            )
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
