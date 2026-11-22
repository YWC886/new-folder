"""uq_annotate 测试：D056 列计算与覆盖保护。"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (HERE, ROOT / "code" / "processing"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import uq_annotate as ua  # noqa: E402


class UqAnnotateTests(unittest.TestCase):
    def test_columns_and_math(self) -> None:
        sel = [{"voltage_set_v": "22.2", "throttle_set_pct": "50", "eta_sys": "0.38", "gp_std_eta": "0.004"}]
        u2 = [{"v": 22.2, "t": 50, "u2": 0.02}]
        rows = ua.annotate(sel, u2)
        r = rows[0]
        self.assertAlmostEqual(r["u_meas"], 0.01, delta=1e-5)
        self.assertAlmostEqual(r["sigma_total"], (0.01 ** 2 + 0.004 ** 2) ** 0.5, delta=1e-5)
        self.assertAlmostEqual(r["eta_cons_2sigma"], 0.38 - 2 * r["sigma_total"], delta=1e-5)
        self.assertIn("D056", r["uq_note"])

    def test_write_overwrite_protection(self) -> None:
        rows = ua.annotate(
            [{"voltage_set_v": "22.2", "throttle_set_pct": "50", "eta_sys": "0.38", "gp_std_eta": "0.004"}],
            [{"v": 22.2, "t": 50, "u2": 0.02}],
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "a.csv"
            ua.write_csv(rows, out)
            with self.assertRaises(FileExistsError):
                ua.write_csv(rows, out)
            ua.write_csv(rows, out, overwrite=True)
            with out.open(encoding="utf-8") as fh:
                self.assertIn("eta_cons_2sigma", next(csv.reader(fh)))


if __name__ == "__main__":
    unittest.main()
