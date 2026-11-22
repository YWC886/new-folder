"""uq_consistency 合成与匹配测试。"""
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

import uq_consistency as uc  # noqa: E402


def make_runs(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["voltage_set_v", "throttle_set_pct", "eta_sys_mean", "u_eta_sys_k2"])
        w.writerow(["22.2", "50", "0.38", "0.02"])
        w.writerow(["29.6", "75", "0.53", "0.03"])


def make_surface(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["voltage_set_v", "throttle_set_pct", "eta_pred", "eta_std"])
        w.writerow(["22.2", "52", "0.385", "0.004"])
        w.writerow(["29.6", "74", "0.528", "0.006"])


class UqConsistencyTests(unittest.TestCase):
    def test_match_and_formula(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs, surf = Path(tmp) / "runs.csv", Path(tmp) / "surf.csv"
            make_runs(runs)
            make_surface(surf)
            rows = uc.match(uc.load_runs(runs), uc.load_surface(surf))
        self.assertEqual(len(rows), 2)
        top = rows[0]
        self.assertAlmostEqual(top["u_meas"], top["u_eta_sys_k2"] / 2.0, places=12)
        self.assertAlmostEqual(top["sigma_total"], (top["u_meas"] ** 2 + top["eta_std"] ** 2) ** 0.5, places=12)
        self.assertAlmostEqual(top["eta_cons_2sigma"], top["eta_pred"] - 2 * top["sigma_total"], places=12)
        self.assertIn("UQ", top["data_note"])

    def test_write_and_overwrite_protection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.csv"
            row = {"voltage_set_v": 22.2, "throttle_set_pct": 50, "eta_obs": 0.38,
                   "u_eta_sys_k2": 0.02, "eta_pred": 0.385, "eta_std": 0.004,
                   "u_meas": 0.01, "sigma_total": 0.01077, "eta_cons_2sigma": 0.3634,
                   "eta_cons_1sigma": 0.3742, "data_note": uc.DATA_NOTE}
            uc.write_csv([row], out)
            with self.assertRaises(FileExistsError):
                uc.write_csv([row], out)
            uc.write_csv([row], out, overwrite=True)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
