"""`code/reference/prior_profile.py` 测试（REFERENCE 逐桨先验 opt-in 对照）。"""

from __future__ import annotations

import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, PROJECT_ROOT / "code" / "simulation"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import prior_profile as pp  # noqa: E402

PRIORS = PROJECT_ROOT / "data" / "metadata" / "uiuc_priors_v0.3.json"
REF_DIR = PROJECT_ROOT / "data" / "reference" / "uiuc"


class LoadTests(unittest.TestCase):
    def test_load_real_priors(self) -> None:
        priors = pp.load_priors(PRIORS)
        self.assertTrue(priors["do_not_apply"])
        self.assertEqual(len(priors["props"]), 7)

    def test_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            pp.load_priors(PROJECT_ROOT / "data" / "metadata" / "nope.json")

    def test_reject_missing_do_not_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "priors.json"
            path.write_text('{"props": []}', encoding="utf-8")
            with self.assertRaises(ValueError):
                pp.load_priors(path)

    def test_find_prop(self) -> None:
        priors = pp.load_priors(PRIORS)
        entry = pp.find_prop(priors, "apce_11x7")
        self.assertAlmostEqual(entry["diameter_in"], 11.0)
        with self.assertRaises(ValueError):
            pp.find_prop(priors, "nope_1x1")


class ModelTests(unittest.TestCase):
    def test_model_from_prior(self) -> None:
        entry = pp.find_prop(pp.load_priors(PRIORS), "apce_11x7")
        model = pp.model_from_prior(entry)
        self.assertAlmostEqual(model.diameter_m, 11.0 * 0.0254)
        self.assertAlmostEqual(model.ct0, entry["ct0"])
        self.assertAlmostEqual(model.cp0, entry["cp0"])
        self.assertAlmostEqual(model.reynolds_ct_exp, entry["aT"])
        self.assertAlmostEqual(model.reynolds_cp_exp, entry["aP"])
        # 其余参数与默认保持
        default = pp.pm.ModelParams()
        self.assertAlmostEqual(model.kv_rpm_per_v, default.kv_rpm_per_v)

    def test_compare_prior_recovers_fitted_curve(self) -> None:
        entry = pp.find_prop(pp.load_priors(PRIORS), "apce_11x7")
        model = pp.model_from_prior(entry)
        rows = []
        for rpm in (2000.0, 3000.0, 4000.0, 5000.0):
            ct, cp = pp._coeffs(rpm, model.ct0, model.reynolds_ct_exp, model.cp0, model.reynolds_cp_exp, model.n_ref_rev_s)
            rows.append({"rpm": rpm, "ct": ct, "cp": cp})
        result = pp.compare_entry(entry, rows)
        self.assertLess(result["stats"]["ct_prior_mean_abs_err"], 1e-9)
        self.assertLess(result["stats"]["cp_prior_mean_abs_err"], 1e-9)
        self.assertGreater(result["stats"]["ct_generic_mean_abs_err"], 0.0)

    def test_compare_real_improves(self) -> None:
        entry = pp.find_prop(pp.load_priors(PRIORS), "apce_11x7")
        path = sorted(REF_DIR.glob("apce_11x7_static_*.txt"))[0]
        result = pp.compare_entry(entry, pp.up.load_static(path))
        stats = result["stats"]
        self.assertEqual(stats["points"], 16)
        self.assertLess(stats["ct_prior_mean_abs_err"], stats["ct_generic_mean_abs_err"])
        self.assertLess(stats["cp_prior_mean_abs_err"], stats["cp_generic_mean_abs_err"])
        self.assertGreater(stats["ct_improvement_x"], 2.0)
        self.assertGreater(stats["cp_improvement_x"], 2.0)


class OutputTests(unittest.TestCase):
    def test_csv_and_plot(self) -> None:
        priors = pp.load_priors(PRIORS)
        entry = pp.find_prop(priors, "apce_11x7")
        path = sorted(REF_DIR.glob("apce_11x7_static_*.txt"))[0]
        result = pp.compare_entry(entry, pp.up.load_static(path))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "cmp.csv"
            png = Path(tmp) / "cmp.png"
            pp.write_csv(result["rows"], out)
            text = out.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(",".join(pp.FIELDS)))
            self.assertEqual(len(text.strip().splitlines()), len(result["rows"]) + 1)
            with self.assertRaises(FileExistsError):
                pp.write_csv(result["rows"], out)
            pp.plot_compare([result["stats"]], png)
            self.assertGreater(png.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                pp.plot_compare([result["stats"]], png)

    def test_main_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.csv"
            png = Path(tmp) / "out.png"
            code = pp.main(["--priors", str(PRIORS), "--props", "apce_11x7", "--output", str(out), "--figure", str(png)])
            self.assertEqual(code, 0)
            self.assertTrue(out.is_file())
            self.assertTrue(png.is_file())
            rows = list(csv.DictReader(out.open(encoding="utf-8")))
            self.assertEqual(len(rows), 16)
            self.assertEqual(rows[0]["prop"], "apce_11x7")

    def test_main_bad_prop_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = pp.main(["--priors", str(PRIORS), "--props", "nope_1x1", "--output", str(Path(tmp) / "a.csv"), "--figure", str(Path(tmp) / "a.png")])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
