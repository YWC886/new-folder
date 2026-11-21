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

def _write_toy_thrust_runs(path: Path) -> None:
    """T = 0.0015 * V * throttle（单调、可解析），15 个点。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["run_id", "voltage_set_v", "throttle_set_pct", "thrust_N_mean"])
        writer.writeheader()
        for voltage in (11.1, 14.8, 22.2):
            for throttle in (20.0, 40.0, 60.0, 80.0, 100.0):
                writer.writerow(
                    {
                        "run_id": f"TOY_{voltage:g}V_{throttle:g}pct",
                        "voltage_set_v": voltage,
                        "throttle_set_pct": throttle,
                        "thrust_N_mean": 0.0015 * voltage * throttle,
                    }
                )


class ThrustInversionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.runs = Path(self.tmp.name) / "runs.csv"
        _write_toy_thrust_runs(self.runs)
        self.model = dm.fit_thrust_map(dm.load_thrust_runs(self.runs))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_fit_map_reasonable(self) -> None:
        self.assertEqual(self.model["n"], 15)
        self.assertGreater(self.model["r2"], 0.99)
        self.assertLess(self.model["loocv_rmse"], 0.05)

    def test_invert_recovers_target(self) -> None:
        throttle, thrust = dm.invert_throttle(self.model, 22.2, 2.0)
        self.assertAlmostEqual(throttle, 2.0 / (0.0015 * 22.2), delta=1.0)
        self.assertAlmostEqual(thrust, 2.0, delta=0.05)

    def test_invert_rejects_out_of_range(self) -> None:
        with self.assertRaises(dm.DesignError):
            dm.invert_throttle(self.model, 11.1, 10.0)
        with self.assertRaises(dm.DesignError):
            dm.invert_throttle(self.model, 22.2, 0.0)

    def test_build_thrust_matrix(self) -> None:
        cfg = toy_config(voltages=(11.1, 22.2), repeats=1, props=("P1", "P2"))
        rows, skipped = dm.build_thrust_matrix(cfg, (1.0, 2.0), self.model, "P1")
        self.assertEqual(len(rows), 3)  # 11.1 V 上限 1.665 N 跳过目标 2；22.2 V 两个水平都可达
        self.assertEqual(len(skipped), 1)
        self.assertTrue(all(r["prop_id"] == "P1" for r in rows))
        self.assertEqual([r["planned_thrust_n"] for r in rows], [1.0, 1.0, 2.0])

    def test_map_prop_must_be_in_props(self) -> None:
        cfg = toy_config(props=("P1",))
        with self.assertRaises(dm.DesignError):
            dm.build_thrust_matrix(cfg, (1.0,), self.model, "P9")

    def test_randomize_rows_reproducible(self) -> None:
        rows = dm.build_matrix(toy_config(voltages=(11.1, 14.8, 22.2), props=("P1",), repeats=1, throttles=(25.0, 50.0, 75.0)))
        a = dm.randomize_rows([dict(r) for r in rows], 7)
        b = dm.randomize_rows([dict(r) for r in rows], 7)
        self.assertEqual([r["run_id"] for r in a], [r["run_id"] for r in b])
        self.assertEqual(sorted(r["run_id"] for r in a), sorted(r["run_id"] for r in rows))
        self.assertEqual([r["order"] for r in a], list(range(1, len(a) + 1)))
        c = dm.randomize_rows([dict(r) for r in rows], 8)
        self.assertNotEqual([r["run_id"] for r in a], [r["run_id"] for r in c])

    def test_thrust_fields_csv(self) -> None:
        cfg = toy_config(voltages=(22.2,), repeats=1, props=("P1",))
        rows, _ = dm.build_thrust_matrix(cfg, (1.0,), self.model, "P1")
        out = Path(self.tmp.name) / "thrust.csv"
        dm.write_csv(rows, out, fields=dm.THRUST_FIELDS)
        header = out.read_text(encoding="utf-8").splitlines()[0]
        self.assertIn("planned_thrust_n", header)

    def test_cli_thrust_mode(self) -> None:
        out = Path(self.tmp.name) / "plan.csv"
        summary = Path(self.tmp.name) / "plan.summary.json"
        code = dm.main(
            [
                "--voltages", "22.2",
                "--throttles", "20,100",
                "--props", "P1",
                "--repeats", "1",
                "--thrust-levels", "1,2",
                "--thrust-map", str(self.runs),
                "--map-prop", "P1",
                "--output", str(out),
                "--summary", str(summary),
            ]
        )
        self.assertEqual(code, 0)
        self.assertTrue(out.exists() and summary.exists())
        data = json.loads(summary.read_text(encoding="utf-8"))
        self.assertEqual(data["mode"], "thrust")
        self.assertIn("planned_thrust_n", out.read_text(encoding="utf-8").splitlines()[0])
        again = dm.main(
            [
                "--voltages", "22.2",
                "--props", "P1",
                "--repeats", "1",
                "--thrust-levels", "1",
                "--thrust-map", str(self.runs),
                "--map-prop", "P1",
                "--output", str(out),
                "--summary", str(summary),
            ]
        )
        self.assertEqual(again, 2)

    def test_cli_missing_map_exit_2(self) -> None:
        code = dm.main(["--thrust-levels", "1", "--thrust-map", str(Path(self.tmp.name) / "nope.csv")])
        self.assertEqual(code, 2)

