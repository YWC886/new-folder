"""bem_propeller v0.1 测试。"""
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

import bem_propeller as bem  # noqa: E402

APC10x7 = bem.BemParams()


class BasicTests(unittest.TestCase):
    def test_plausible_ranges(self) -> None:
        r = bem.solve(4000.0, APC10x7)
        self.assertTrue(r["converged"])
        self.assertGreater(r["thrust_n"], 1.0)
        self.assertLess(r["thrust_n"], 80.0)
        self.assertGreater(r["ct"], 0.02)
        self.assertLess(r["ct"], 0.25)
        self.assertGreater(r["cp"], 0.01)
        self.assertLess(r["cp"], 0.15)

    def test_thrust_monotonic_in_rpm(self) -> None:
        t = [bem.solve(rpm, APC10x7)["thrust_n"] for rpm in (2000, 3000, 4000, 5000)]
        self.assertEqual(t, sorted(t))

    def test_ct_cp_roughly_flat(self) -> None:
        ct = [bem.solve(rpm, APC10x7)["ct"] for rpm in (2000, 3000, 4000)]
        self.assertLess(max(ct) / min(ct), 1.6)

    def test_invalid_rpm(self) -> None:
        with self.assertRaises(ValueError):
            bem.solve(0.0, APC10x7)

    def test_integrate_positive(self) -> None:
        T, Q = bem.integrate(5.0, 2 * 3.14159 * 60, APC10x7)
        self.assertGreater(T, 0)
        self.assertGreater(Q, 0)

    def test_clamp_cl(self) -> None:
        cl, cd = bem._cl_cd(1.0, APC10x7)
        self.assertLessEqual(abs(cl), APC10x7.cl_max + 1e-9)
        self.assertGreater(cd, 0)

    def test_cli_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "b.json"
            rc = bem.main(["--rpm", "4000", "--output", str(out)])
            self.assertEqual(rc, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("ct", data)

    def test_cli_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rc = bem.main(["--rpm", "0", "--output", str(Path(tmp) / "b.json")])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
