"""batch_plan v0.1 测试。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import batch_plan as bp


def toy_runs() -> list[dict]:
    rows = []
    for v in (11.1, 22.2):
        for t in (25, 50, 75, 100):
            rows.append(
                {
                    "voltage_set_v": v,
                    "throttle_set_pct": t,
                    "eta_sys": 0.1 + 0.004 * v * t / 100.0,
                }
            )
    return rows


class PlanTests(unittest.TestCase):
    def test_fields_and_order(self) -> None:
        rows = bp.build_plan(toy_runs(), n=4, u_k2=0.02, duration_s=20.0)
        self.assertTrue(1 <= len(rows) <= 4)
        for row in rows:
            self.assertEqual(set(row), set(bp.BATCH_FIELDS))
            self.assertAlmostEqual(row["u_meas"], 0.01)
            self.assertAlmostEqual(row["sigma_total"], (0.01**2 + row["gp_std_eta"] ** 2) ** 0.5)
            self.assertAlmostEqual(row["priority"], row["sigma_total"])
            self.assertAlmostEqual(row["est_duration_s"], 20.0)
        priorities = [r["priority"] for r in rows]
        self.assertEqual(priorities, sorted(priorities, reverse=True))
        self.assertEqual([r["rank"] for r in rows], list(range(1, len(rows) + 1)))

    def test_invalid_args(self) -> None:
        for kwargs in ({"n": 0}, {"duration_s": 0.0}, {"u_k2": -1.0}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    bp.build_plan(toy_runs(), **kwargs)

    def test_write_and_overwrite(self) -> None:
        rows = bp.build_plan(toy_runs(), n=3)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.csv"
            bp.write_csv(rows, out)
            self.assertTrue(out.exists())
            with self.assertRaises(FileExistsError):
                bp.write_csv(rows, out)
            bp.write_csv(rows, out, overwrite=True)


class ScheduleTests(unittest.TestCase):
    def test_schedule_rows(self) -> None:
        plan = bp.build_plan(toy_runs(), n=3, duration_s=25.0)
        sched = bp.to_schedule(plan, combo="NEXT", repeats=2, duration_s=25.0, steady_window_s=3.0)
        self.assertEqual(len(sched), len(plan) * 2)
        self.assertEqual(sorted(sched[0]), sorted(bp.SCHEDULE_FIELDS))
        self.assertEqual(len({r["run_id"] for r in sched}), len(sched))
        for row in sched:
            self.assertAlmostEqual(row["duration_s"], 25.0)
            self.assertAlmostEqual(row["steady_window_s"], 3.0)

    def test_schedule_invalid(self) -> None:
        plan = bp.build_plan(toy_runs(), n=2)
        with self.assertRaises(ValueError):
            bp.to_schedule(plan, repeats=0)
        with self.assertRaises(ValueError):
            bp.to_schedule(plan, duration_s=10.0, steady_window_s=12.0)

    def test_schedule_write_and_overwrite(self) -> None:
        plan = bp.build_plan(toy_runs(), n=2)
        sched = bp.to_schedule(plan, repeats=1)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sched.csv"
            bp.write_schedule(sched, out)
            self.assertTrue(out.exists())
            with self.assertRaises(FileExistsError):
                bp.write_schedule(sched, out)
            bp.write_schedule(sched, out, overwrite=True)


if __name__ == "__main__":
    unittest.main()
