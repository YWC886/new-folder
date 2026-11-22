"""uq_utils 换算与合成测试。"""
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import uq_utils as uq  # noqa: E402


class UqUtilsTests(unittest.TestCase):
    def test_u2_roundtrip(self) -> None:
        self.assertAlmostEqual(uq.from_u2(0.02), 0.01, places=12)
        self.assertAlmostEqual(uq.to_u2(0.01), 0.02, places=12)
        self.assertAlmostEqual(uq.from_u2(uq.to_u2(0.003)), 0.003, places=12)

    def test_combine_sigma(self) -> None:
        self.assertAlmostEqual(uq.combine_sigma(0.003, 0.004), 0.005, places=12)
        self.assertAlmostEqual(uq.combine_sigma(0.0), 0.0)
        self.assertAlmostEqual(uq.combine_sigma(), 0.0)
        with self.assertRaises(ValueError):
            uq.combine_sigma(-1e-6)

    def test_conservative_eta(self) -> None:
        r = uq.conservative_eta(0.30, u2=0.02, sigma_model=0.004)
        self.assertAlmostEqual(r["u_meas"], 0.01)
        self.assertAlmostEqual(r["sigma_total"], math.sqrt(0.01**2 + 0.004**2))
        self.assertAlmostEqual(r["eta_cons"], 0.30 - 2 * r["sigma_total"])
        self.assertAlmostEqual(r["eta_cons_1sigma"], 0.30 - r["sigma_total"])


if __name__ == "__main__":
    unittest.main()
