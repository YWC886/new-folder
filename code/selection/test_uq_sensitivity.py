"""`uq_sensitivity` 测试：U(k=2) 敏感性输出与边界。"""

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

import uq_sensitivity as us


def toy_runs() -> list[dict]:
    runs = []
    for voltage in (20.0, 28.0):
        for throttle in (25.0, 50.0, 75.0, 100.0):
            runs.append(
                {
                    "voltage_set_v": voltage,
                    "throttle_set_pct": throttle,
                    "thrust_N": 0.0025 * voltage * throttle,
                    "eta_sys": 0.30 + 0.0015 * throttle,
                }
            )
    return runs


class SensitivityTests(unittest.TestCase):
    def test_one_row_per_u_and_monotonic_knee(self) -> None:
        rows = us.run_sensitivity(toy_runs(), thrust_required_n=5.0, u_values=(0.0, 0.02, 0.05))
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["n_front"] == rows[0]["n_front"] for row in rows))
        cons = [row["knee_eta_cons_2sigma"] for row in rows]
        self.assertTrue(cons[0] >= cons[1] >= cons[2])
        for row in rows:
            self.assertLessEqual(row["knee_eta_cons_2sigma"], row["knee_eta_sys"])
            self.assertGreaterEqual(row["knee_voltage_set_v"], 20.0)
            self.assertLessEqual(row["knee_voltage_set_v"], 28.0)

    def test_write_csv_and_overwrite(self) -> None:
        rows = us.run_sensitivity(toy_runs(), u_values=(0.0, 0.02))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "s.csv"
            us.write_csv(rows, out)
            head = out.read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(head, ",".join(us.OUT_FIELDS))
            with self.assertRaises(FileExistsError):
                us.write_csv(rows, out)

    def test_invalid_u_values(self) -> None:
        with self.assertRaises(ValueError):
            us.run_sensitivity(toy_runs(), u_values=())
        with self.assertRaises(ValueError):
            us.run_sensitivity(toy_runs(), u_values=(0.01, -0.02))

    def test_cli_missing_input_returns_2(self) -> None:
        rc = us.main(["--input", "data/processed/no_such_file.csv"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
