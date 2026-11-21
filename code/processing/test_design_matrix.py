"""design_matrix 测试（10 项）。"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import design_matrix as dm  # noqa: E402


def toy_config(**kwargs) -> dm.DesignConfig:
    base = dict(
        voltages=(11.1, 14.8),
        throttles=(50.0, 25.0),
        props=("P1", "P2"),
        repeats=2,
        duration_s=4.0,
        steady_window_s=1.5,
        design="full",
        combo="TOY",
    )
    base.update(kwargs)
    return dm.DesignConfig(**base)


class BuildTests(unittest.TestCase):
    def test_full_factorial_count_and_uniqueness(self) -> None:
        cfg = toy_config()
        rows = dm.build_matrix(cfg)
        self.assertEqual(len(rows), 2 * 2 * 2 * 2)  # V*T*P*R
        self.assertEqual(len({r["run_id"] for r in rows}), len(rows))
        self.assertEqual([r["order"] for r in rows], list(range(1, len(rows) + 1)))

    def test_full_ordering_sorted_throttles_within_block(self) -> None:
        rows = dm.build_matrix(toy_config())
        first_block = [r for r in rows if r["block"] == 1]
        self.assertEqual({r["voltage_set_v"] for r in first_block}, {11.1})
        self.assertEqual(
            [r["throttle_set_pct"] for r in first_block[:2]],
            [25.0, 50.0],
        )

    def test_sweep_passes_up_and_down(self) -> None:
        cfg = toy_config(design="sweep")
        rows = dm.build_matrix(cfg)
        # V*passes(2)*P*T*2(direction)
        self.assertEqual(len(rows), 2 * 2 * 2 * 2 * 2)
        dirs = [r["direction"] for r in rows if r["block"] == 1][:4]
        self.assertEqual(dirs, ["up", "up", "down", "down"])

    def test_deterministic(self) -> None:
        self.assertEqual(dm.build_matrix(toy_config()), dm.build_matrix(toy_config()))

    def test_summary_totals(self) -> None:
        cfg = toy_config()
        rows = dm.build_matrix(cfg)
        summary = dm.summarize(rows, cfg)
        self.assertEqual(summary["n_runs"], 16)
        self.assertEqual(summary["planned_duration_s"], 64.0)
        self.assertEqual(summary["blocks"], 2)
        self.assertIn("不是测量数据", summary["data_note"])

    def test_invalid_inputs_raise(self) -> None:
        with self.assertRaises(dm.DesignError):
            toy_config(voltages=())
        with self.assertRaises(dm.DesignError):
            toy_config(throttles=(0.0,))
        with self.assertRaises(dm.DesignError):
            toy_config(repeats=0)
        with self.assertRaises(dm.DesignError):
            toy_config(steady_window_s=9.0, duration_s=4.0)
        with self.assertRaises(dm.DesignError):
            toy_config(design="lhs")


class OutputTests(unittest.TestCase):
    def test_write_csv_and_summary_with_protection(self) -> None:
        cfg = toy_config()
        rows = dm.build_matrix(cfg)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "matrix.csv"
            summary_path = Path(tmp) / "summary.json"
            dm.write_csv(rows, out)
            dm.write_summary(dm.summarize(rows, cfg), summary_path)
            text = out.read_text(encoding="utf-8")
            header = text.splitlines()[0].split(",")
            self.assertEqual(tuple(header), dm.FIELDS)
            with out.open(encoding="utf-8") as fh:
                parsed = list(csv.DictReader(fh))
            self.assertEqual(len(parsed), len(rows))
            self.assertEqual(parsed[0]["run_id"], rows[0]["run_id"])
            self.assertIn("n_runs", json.loads(summary_path.read_text(encoding="utf-8")))
            with self.assertRaises(FileExistsError):
                dm.write_csv(rows, out)
            with self.assertRaises(FileExistsError):
                dm.write_summary(dm.summarize(rows, cfg), summary_path)

    def test_write_empty_matrix_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(dm.DesignError):
                dm.write_csv([], Path(tmp) / "x.csv")


class CliTests(unittest.TestCase):
    def test_cli_end_to_end_and_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "m.csv"
            summary = Path(tmp) / "s.json"
            argv = [
                "--voltages", "11.1,14.8",
                "--throttles", "25,50",
                "--props", "P1",
                "--repeats", "2",
                "--output", str(out),
                "--summary", str(summary),
            ]
            self.assertEqual(dm.main(argv), 0)
            self.assertTrue(out.exists())
            self.assertEqual(dm.main(argv), 2)  # 已存在 → 拒绝
            self.assertEqual(dm.main(argv + ["--overwrite"]), 0)

    def test_cli_invalid_voltage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            argv = ["--voltages", "-1", "--output", str(Path(tmp) / "m.csv"), "--summary", str(Path(tmp) / "s.json")]
            self.assertEqual(dm.main(argv), 2)


if __name__ == "__main__":
    unittest.main()
