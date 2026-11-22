"""BEM v0.2 桨尖损失测试。"""
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (HERE, ROOT / "work" / "pylibs"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bem_propeller as bem  # noqa: E402


class TipLossTests(unittest.TestCase):
    def setUp(self) -> None:
        self.p = bem.BemParams()

    def test_tip_loss_range_and_trend(self) -> None:
        p = self.p
        phi = math.radians(12.0)
        f_root = bem.prandtl_tip_loss(0.2 * p.radius, phi, p)
        f_mid = bem.prandtl_tip_loss(0.6 * p.radius, phi, p)
        f_tip = bem.prandtl_tip_loss(0.99 * p.radius, phi, p)
        self.assertGreater(f_root, f_mid)
        self.assertGreater(f_mid, f_tip)
        self.assertGreater(f_tip, 0.0)
        self.assertLessEqual(f_root, 1.0)

    def test_solve_with_tip_loss_positive(self) -> None:
        m = bem.solve(4000.0, self.p)
        self.assertGreater(m["thrust_n"], 0.0)
        self.assertGreater(m["torque_nm"], 0.0)
        self.assertGreater(m["figure_of_merit"], 0.0)
        self.assertLess(m["figure_of_merit"], 1.0)


if __name__ == "__main__":
    unittest.main()
