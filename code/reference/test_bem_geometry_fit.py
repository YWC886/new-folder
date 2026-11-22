"""BEM 几何细化筛选测试（REFERENCE-GEOM，单桨）。"""
import csv
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (HERE, ROOT / "work" / "pylibs"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bem_geometry_fit as fit  # noqa: E402
import uiuc_propdb  # noqa: E402

CSV = ROOT / "data" / "processed" / "bem_geometry_fit_v0.1.csv"


class GeometryFitTests(unittest.TestCase):
    def test_baseline_mae_matches_v02(self) -> None:
        rows = uiuc_propdb.load_static(fit.SAMPLE)
        ct, cp = fit.mae(fit.bem.BemParams(diameter_m=fit.D, pitch_m=fit.P, chord_ratio=0.11), rows)
        self.assertAlmostEqual(ct, 41.1, delta=2.0)
        self.assertAlmostEqual(cp, 22.3, delta=2.0)

    def test_grid_csv_has_improvement_and_fields(self) -> None:
        self.assertTrue(CSV.exists())
        rows = list(csv.DictReader(CSV.open(encoding="utf-8")))
        self.assertGreaterEqual(len(rows), 50)
        self.assertEqual(set(rows[0].keys()),
                         {"chord_ratio", "pitch_m", "ct_mae_pct", "cp_mae_pct", "score"})
        best = min(rows, key=lambda r: float(r["score"]))
        self.assertLess(float(best["score"]), (41.1 + 22.3) / 2.0)


if __name__ == "__main__":
    unittest.main()
