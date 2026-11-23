"""loop_drill v0.1 测试。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import loop_drill as ld


def toy_runs(n_v: int = 4, n_t: int = 4) -> list[dict]:
    rows = []
    for v in (11.1, 14.8, 22.2, 29.6)[:n_v]:
        for t in (25, 50, 75, 100)[:n_t]:
            # 光滑规律 + 轻微曲率，便于 GP 学习
            eta = 0.10 + 0.00035 * v * t - 0.0000015 * (t - 60) ** 2
            rows.append({"voltage_set_v": v, "throttle_set_pct": t, "eta_sys": eta})
    return rows


class DrillTests(unittest.TestCase):
    def test_drill_runs_and_reports(self) -> None:
        result = ld.run_drill(toy_runs(), holdout_every=4, n=3, seed=1, noise_std=0.001)
        self.assertEqual(result["n_planned"], 3)
        self.assertEqual(result["n_train"] + result["n_holdout"], len(toy_runs()))
        for key in ("before_rmse", "after_rmse", "improvement_pct"):
            self.assertIsInstance(result[key], float)
        self.assertGreater(result["before_rmse"], 0.0)
        self.assertGreater(result["after_rmse"], 0.0)

    def test_deterministic_seed(self) -> None:
        a = ld.run_drill(toy_runs(), n=3, seed=7, noise_std=0.002)
        b = ld.run_drill(toy_runs(), n=3, seed=7, noise_std=0.002)
        self.assertEqual(a["after_rmse"], b["after_rmse"])
        self.assertEqual([r["voltage_set_v"] for r in a["planned"]], [r["voltage_set_v"] for r in b["planned"]])

    def test_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            ld.run_drill(toy_runs(), holdout_every=1)
        with self.assertRaises(ValueError):
            ld.run_drill(toy_runs(), noise_std=-0.1)
        with self.assertRaises(ValueError):
            ld.split_holdout(toy_runs(n_v=1, n_t=2), every=4)

    def test_write_outputs_and_overwrite(self) -> None:
        result = ld.run_drill(toy_runs(), n=3)
        with tempfile.TemporaryDirectory() as tmp:
            jp = Path(tmp) / "drill.json"
            cp = Path(tmp) / "plan.csv"
            ld.write_outputs(result, json_path=jp, csv_path=cp)
            self.assertTrue(jp.exists() and cp.exists())
            with self.assertRaises(FileExistsError):
                ld.write_outputs(result, json_path=jp, csv_path=cp)
            ld.write_outputs(result, json_path=jp, csv_path=cp, overwrite=True)


if __name__ == "__main__":
    unittest.main()
