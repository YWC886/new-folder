"""多桨等效几何反演结果的稳定性测试（REFERENCE-GEOM）。"""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "data" / "processed" / "bem_geometry_multiprop_v0.1.csv"


class MultiPropTests(unittest.TestCase):
    def load(self) -> list[dict]:
        with CSV.open(encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def test_csv_shape_and_improvement(self) -> None:
        rows = self.load()
        self.assertEqual(len(rows), 7)
        for r in rows:
            b = float(r["baseline_ct_mae"]) + float(r["baseline_cp_mae"])
            o = float(r["best_ct_mae"]) + float(r["best_cp_mae"])
            self.assertLess(o, b)

    def test_parameter_clusters(self) -> None:
        rows = self.load()
        cs = {float(r["best_chord_ratio"]) for r in rows}
        fs = {float(r["best_pitch_factor"]) for r in rows}
        self.assertTrue(cs.issubset({0.05, 0.075, 0.10, 0.125, 0.15}))
        self.assertTrue(fs.issubset({0.75, 0.90, 1.00, 1.10, 1.25}))
        self.assertGreaterEqual(min(cs), 0.075)
        self.assertLessEqual(max(cs), 0.10)


if __name__ == "__main__":
    unittest.main()
