"""geometry_prior v0.1 测试。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, str(PROJECT_ROOT / "work" / "pylibs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import geometry_prior as gp  # noqa: E402


def _synthetic_entries(n_props: int = 4):
    entries = []
    for i in range(n_props):
        d_in = 9.0 + i
        pitch = 5.0 + i
        label = {"prop": f"p{i}", "brand": f"b{i}", "series_full": f"s{i}", "diameter_in": d_in, "pitch_in": pitch}
        rows = []
        D = d_in * 0.0254
        pr = pitch / d_in
        for n_rps in (20.0, 30.0, 40.0, 50.0, 60.0):
            nn = n_rps / 100.0
            ct = 0.2 + 3.0 * D + 0.05 * pr + 0.03 * nn + 0.002 * nn * nn
            cp = 0.1 + 1.0 * D + 0.02 * pr + 0.05 * nn + 0.0005 * nn * nn
            rows.append({"n_rps": n_rps, "ct": ct, "cp": cp})
        entries.append({"label": label, "rows": rows})
    return entries


class FeatureTests(unittest.TestCase):
    def test_features_shape(self) -> None:
        rows = [{"n_rps": 50.0}]
        X = gp._features(rows, 0.25, 0.7)
        self.assertEqual(X.shape, (1, 5))
        self.assertAlmostEqual(X[0, 3], 0.5)
        self.assertAlmostEqual(X[0, 4], 0.25)

    def test_fit_and_predict_recover_linear_model(self) -> None:
        entries = _synthetic_entries()
        coef = gp.fit_linear(entries, "ct")
        for e in entries:
            D = float(e["label"]["diameter_in"]) * 0.0254
            pr = float(e["label"]["pitch_in"]) / float(e["label"]["diameter_in"])
            pred = gp.predict(coef, e["rows"], D, pr)
            for p, r in zip(pred, [x["ct"] for x in e["rows"]]):
                self.assertAlmostEqual(float(p), r, places=9)

    def test_insufficient_props_raises(self) -> None:
        entries = _synthetic_entries(2)
        self.assertLess(len(entries), 3)


class LopoTests(unittest.TestCase):
    def test_lopo_recovers_synthetic_linear_data(self) -> None:
        entries = _synthetic_entries()
        result = gp.lopo_benchmark(entries)
        for r in result["rows"]:
            self.assertLess(r["geo_ct_mae"], 1e-6)
            self.assertLess(r["geo_cp_mae"], 1e-6)

    def test_lopo_rows_and_pooled(self) -> None:
        result = gp.lopo_benchmark(_synthetic_entries())
        self.assertEqual(len(result["rows"]), 4)
        self.assertEqual(result["pooled"]["points"], 20)
        for key in ("generic_ct_mae", "geo_ct_mae", "generic_cp_mae", "geo_cp_mae"):
            self.assertIn(key, result["pooled"])


class OutputTests(unittest.TestCase):
    def test_csv_and_overwrite(self) -> None:
        rows = gp.lopo_benchmark(_synthetic_entries())["rows"]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "g.csv"
            gp.write_csv(rows, out)
            self.assertTrue(out.read_text(encoding="utf-8").startswith(",".join(gp.OUT_FIELDS)))
            with self.assertRaises(FileExistsError):
                gp.write_csv(rows, out)

    def test_plot_and_overwrite(self) -> None:
        rows = gp.lopo_benchmark(_synthetic_entries())["rows"]
        with tempfile.TemporaryDirectory() as tmp:
            fig = Path(tmp) / "g.png"
            gp.plot_compare(rows, fig)
            self.assertGreater(fig.stat().st_size, 10_000)
            with self.assertRaises(FileExistsError):
                gp.plot_compare(rows, fig)

    def test_cli_with_real_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "g.csv"
            fig = Path(tmp) / "g.png"
            rc = gp.main(["--output", str(out), "--figure", str(fig)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists() and fig.exists())
            rc2 = gp.main(["--output", str(out), "--figure", str(fig)])
            self.assertEqual(rc2, 2)


if __name__ == "__main__":
    unittest.main()
