"""留一桨型全局修正迁移结果测试（REFERENCE-GEOM）。"""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "data" / "processed" / "bem_lopo_transfer_v0.1.csv"


class LopoTransferTests(unittest.TestCase):
    def load(self) -> list[dict]:
        with CSV.open(encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def test_shape_and_pooled_improvement(self) -> None:
        rows = self.load()
        self.assertEqual(len(rows), 7)
        base = sum(float(r["base_ct_mae"]) + float(r["base_cp_mae"]) for r in rows) / 7
        corr = sum(float(r["corr_ct_mae"]) + float(r["corr_cp_mae"]) for r in rows) / 7
        self.assertLess(corr, base)

    def test_correction_choice_in_grid(self) -> None:
        rows = self.load()
        for r in rows:
            self.assertIn(float(r["c_scale"]), (0.70, 0.80))
            self.assertIn(float(r["p_factor"]), (1.05, 1.15))


if __name__ == "__main__":
    unittest.main()
