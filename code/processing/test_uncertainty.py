"""uncertainty v0.1 测试。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, str(PROJECT_ROOT / "work" / "pylibs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import uncertainty as un  # noqa: E402

RAW = PROJECT_ROOT / "data/raw/20261117_SIM_22V2_50pct_R1.csv"
CALIB = PROJECT_ROOT / "data/metadata/calib_SIM_DEMO.json"


def _rows(n: int = 200):
    return [
        {"seq": str(i), "elapsed_s": f"{i * 0.001:.3f}", "thrust_raw": "28000", "torque_raw": "17000",
         "rpm": "6000", "voltage_v": "22.2", "current_a": "8.0"}
        for i in range(n)
    ]


def _calib():
    return {"thrust": {"k": 0.00035, "b": 0.0}, "torque": {"k": 5.882352941176471e-06, "b": 0.0},
            "propeller": {"diameter_m": 0.4572}}


class BasicTests(unittest.TestCase):
    def test_nominal_reasonable(self) -> None:
        report = un.propagate(_rows(), _calib(), rho=1.225, n=50, seed=1)
        nom = report["nominal"]
        self.assertAlmostEqual(nom["thrust_n"], 9.8, places=3)
        self.assertAlmostEqual(nom["torque_nm"], 0.1, places=4)
        self.assertGreater(nom["eta_sys"], 0.2)
        self.assertLess(nom["eta_sys"], 0.5)

    def test_ci_ordering_and_std(self) -> None:
        r = un.propagate(_rows(), _calib(), rho=1.225, n=200, seed=2)
        e = r["eta_sys"]
        self.assertLessEqual(e["p2_5"], e["mean"])
        self.assertLessEqual(e["mean"], e["p97_5"])
        self.assertGreater(e["std"], 0.0)
        self.assertLess(e["std"], 0.05)

    def test_deterministic(self) -> None:
        a = un.propagate(_rows(), _calib(), rho=1.225, n=100, seed=7)
        b = un.propagate(_rows(), _calib(), rho=1.225, n=100, seed=7)
        self.assertAlmostEqual(a["eta_sys"]["mean"], b["eta_sys"]["mean"], places=12)

    def test_sensitivity_keys(self) -> None:
        r = un.propagate(_rows(), _calib(), rho=1.225, n=100, seed=3)
        self.assertEqual(set(r["sensitivity_1sigma_eta_sys"]), set(un.DEFAULT_SIGMAS))
        top = max(r["sensitivity_1sigma_eta_sys"].items(), key=lambda kv: kv[1])
        self.assertGreater(top[1], 0.0)

    def test_invalid_n(self) -> None:
        with self.assertRaises(ValueError):
            un.propagate(_rows(), _calib(), rho=1.225, n=5)

    def test_cli_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "u.json"
            rc = un.main(["--input", str(RAW), "--calib", str(CALIB), "--n", "200", "--output", str(out)])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("eta_sys", data)
            self.assertAlmostEqual(data["eta_sys"]["mean"], 0.2843, delta=0.02)

    def test_cli_missing_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rc = un.main(["--input", str(Path(tmp) / "nope.csv"), "--calib", str(CALIB)])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
