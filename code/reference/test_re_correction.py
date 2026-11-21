"""`code/reference/re_correction.py` 单元测试（合成 + 真实 REFERENCE 少量校验）。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, PROJECT_ROOT / "code" / "simulation"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import propulsion_model as pm  # noqa: E402
import re_correction as rc  # noqa: E402


def _props_power_law(ct0: float = 0.110, a_t: float = 0.05, cp0: float = 0.045, a_p: float = -0.10) -> list[dict]:
    """与 prior_profile 同口径：CT=ct0*(n/n_ref)^aT，CP=cp0*(n/n_ref)^aP。"""
    props = []
    for diameter_in in (10.0, 12.0):
        d = diameter_in * 0.0254
        rows = []
        for rpm in (2500.0, 3500.0, 4500.0, 5500.0):
            ratio = (rpm / 60.0) / rc.N_REF_REV_S
            rows.append({"rpm": rpm, "ct": ct0 * ratio**a_t, "cp": cp0 * ratio**a_p})
        props.append({"prop": f"p{diameter_in:g}", "diameter_m": d, "diameter_in": diameter_in, "rows": rows})
    return props


def _props_re_law(nu: float, ct_exp: float = 0.08, cp_exp: float = -0.05) -> list[dict]:
    """CT=0.11*ReRatio^ct_exp：用于 pooled Re 拟合的精确恢复测试。"""
    props = []
    for diameter_in in (10.0, 12.0):
        d = diameter_in * 0.0254
        rows = []
        for rpm in (2500.0, 3500.0, 4500.0, 5500.0):
            ratio = rc.re_ratio(rpm, d, nu)
            rows.append({"rpm": rpm, "ct": 0.110 * ratio**ct_exp, "cp": 0.045 * ratio**cp_exp})
        props.append({"prop": f"p{diameter_in:g}", "diameter_m": d, "diameter_in": diameter_in, "rows": rows})
    return props


def _props_model_base(nu: float, ct_exp: float = 0.05, cp_exp: float = -0.10) -> list[dict]:
    """CT=ct_generic*ReRatio^ct_exp：用于乘性修正指数恢复测试。"""
    base = pm.ModelParams()
    props = []
    for diameter_in in (10.0, 12.0):
        d = diameter_in * 0.0254
        rows = []
        for rpm in (2500.0, 3500.0, 4500.0, 5500.0):
            ct_g, cp_g = rc._model_coeffs(rpm, d, base)
            ratio = rc.re_ratio(rpm, d, nu)
            rows.append({"rpm": rpm, "ct": ct_g * ratio**ct_exp, "cp": cp_g * ratio**cp_exp})
        props.append({"prop": f"p{diameter_in:g}", "diameter_m": d, "diameter_in": diameter_in, "rows": rows})
    return props


class PhysicsTests(unittest.TestCase):
    def test_kinematic_viscosity(self) -> None:
        nu20 = rc.air_kinematic_viscosity(20.0, 101.325)
        nu40 = rc.air_kinematic_viscosity(40.0, 101.325)
        self.assertAlmostEqual(nu20, 1.5e-5, delta=0.3e-5)
        self.assertGreater(nu40, nu20)  # 温度升高 ν 增大
        self.assertLess(rc.air_kinematic_viscosity(20.0, 200.0), nu20)  # 压力升高 ν 减小
        with self.assertRaises(ValueError):
            rc.air_kinematic_viscosity(20.0, 0.0)

    def test_reynolds_number(self) -> None:
        nu = 1.5e-5
        r1 = rc.reynolds_number(3000.0, 0.2544, nu)
        r2 = rc.reynolds_number(6000.0, 0.2544, nu)
        self.assertAlmostEqual(r2, 2 * r1)
        r3 = rc.reynolds_number(3000.0, 0.5088, nu)
        self.assertAlmostEqual(r3, 4 * r1)  # D² 依赖
        with self.assertRaises(ValueError):
            rc.reynolds_number(0.0, 0.2544, nu)

    def test_re_ratio_reference_state(self) -> None:
        nu = 1.5e-5
        self.assertAlmostEqual(rc.re_ratio(rc.N_REF_REV_S * 60.0, rc.D_REF_M, nu), 1.0)
        self.assertAlmostEqual(rc.re_ratio(rc.N_REF_REV_S * 120.0, rc.D_REF_M, nu), 2.0)


class FitTests(unittest.TestCase):
    def test_fit_power_law_exact(self) -> None:
        xs = [0.5, 1.0, 2.0, 4.0]
        ys = [2.0 * x**1.5 for x in xs]
        fit = rc.fit_power_law(xs, ys)
        self.assertAlmostEqual(fit["c0"], 2.0, places=6)
        self.assertAlmostEqual(fit["a"], 1.5, places=6)
        self.assertAlmostEqual(fit["r2"], 1.0, places=6)

    def test_fit_power_law_errors(self) -> None:
        with self.assertRaises(ValueError):
            rc.fit_power_law([1.0], [2.0])
        with self.assertRaises(ValueError):
            rc.fit_power_law([1.0, 1.0], [2.0, 3.0])

    def test_fit_pooled_recovers_synthetic(self) -> None:
        nu = rc.air_kinematic_viscosity()
        props = _props_re_law(nu, ct_exp=0.08, cp_exp=-0.05)
        pooled = rc.fit_pooled_re(props, nu)
        self.assertAlmostEqual(pooled["ct"]["a"], 0.08, places=5)
        self.assertAlmostEqual(pooled["cp"]["a"], -0.05, places=5)
        self.assertGreater(pooled["ct"]["r2"], 0.999)

    def test_fit_scale_exponents_recovers_synthetic(self) -> None:
        nu = rc.air_kinematic_viscosity()
        props = _props_model_base(nu, ct_exp=0.07, cp_exp=-0.12)
        scale = rc.fit_scale_exponents(props, nu, pm.ModelParams())
        self.assertAlmostEqual(scale["ct"], 0.07, places=5)
        self.assertAlmostEqual(scale["cp"], -0.12, places=5)


class CompareTests(unittest.TestCase):
    def _priors(self, ct0: float = 0.110, a_t: float = 0.05, cp0: float = 0.045, a_p: float = -0.10) -> dict:
        entries = []
        for diameter_in in (10.0, 12.0):
            entries.append(
                {"prop": f"p{diameter_in:g}", "ct0": ct0, "aT": a_t, "cp0": cp0, "aP": a_p}
            )
        return {"schema_version": "0.3", "do_not_apply": True, "props": entries}

    def test_compare_prior_near_perfect_re_positive(self) -> None:
        nu = rc.air_kinematic_viscosity()
        props = _props_power_law()
        priors = self._priors()
        pooled = rc.fit_pooled_re(props, nu)
        result = rc.compare(props, pooled, priors)
        summary = {row["prop"]: row for row in result["summary"]}
        self.assertEqual(len(result["points"]), 8)
        for row in summary.values():
            self.assertLess(row["ct_prior_err"], 1e-3)  # 合成同口径：先验误差≈0
            self.assertLess(row["cp_prior_err"], 1e-3)
            self.assertGreaterEqual(row["ct_re_err"], 0.0)
        self.assertTrue(all(k in result["points"][0] for k in ("ct_scaled", "cp_scaled", "re")))

    def test_compare_missing_prior_raises(self) -> None:
        nu = rc.air_kinematic_viscosity()
        props = _props_power_law()
        with self.assertRaises(KeyError):
            rc.compare(props, rc.fit_pooled_re(props, nu), {"props": []})


class OutputTests(unittest.TestCase):
    def test_write_csv_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "rows.csv"
            sumo = Path(tmp) / "sum.csv"
            rc.write_rows([{"prop": "x", "rpm": 3000.0, "re": 1.2e5}], out)
            rc.write_summary([{"prop": "x", "points": 1}], sumo)
            self.assertTrue(out.read_text(encoding="utf-8").startswith("prop,rpm,re"))
            self.assertIn("points", sumo.read_text(encoding="utf-8"))

    def test_plot_and_overwrite(self) -> None:
        nu = rc.air_kinematic_viscosity()
        props = _props_power_law()
        result = rc.compare(props, rc.fit_pooled_re(props, nu), CompareTests()._priors())
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "fig.png"
            rc.plot_compare(result["summary"], png)
            self.assertGreater(png.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                rc.plot_compare(result["summary"], png)


class CliTests(unittest.TestCase):
    def test_cli_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            out, sumo, png = tmp / "o.csv", tmp / "s.csv", tmp / "f.png"
            argv = [
                "--priors", str(PROJECT_ROOT / "data" / "metadata" / "uiuc_priors_v0.3.json"),
                "--output", str(out),
                "--summary", str(sumo),
                "--figure", str(png),
            ]
            self.assertEqual(rc.main(argv), 0)
            self.assertTrue(out.exists() and sumo.exists() and png.exists())
            self.assertEqual(rc.main(argv), 2)  # 未加 --overwrite，已存在应拒绝

    def test_cli_bad_priors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            bad = tmp / "priors.json"
            bad.write_text(json.dumps({"props": []}), encoding="utf-8")
            argv = [
                "--priors", str(bad),
                "--output", str(tmp / "o.csv"),
                "--summary", str(tmp / "s.csv"),
                "--figure", str(tmp / "f.png"),
            ]
            self.assertEqual(rc.main(argv), 2)  # 先验中无桨型 -> KeyError -> exit 2


if __name__ == "__main__":
    unittest.main()
