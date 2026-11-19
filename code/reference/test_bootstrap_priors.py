"""`code/reference/bootstrap_priors.py` 测试（REFERENCE-derived prior 的 bootstrap 区间）。"""

from __future__ import annotations

import csv
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, PROJECT_ROOT / "code" / "simulation"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bootstrap_priors as boot  # noqa: E402

N_REF = 100.0


def write_static(path: Path, ct0: float, a_t: float, cp0: float, a_p: float, *, noise: bool) -> None:
    lines = ["RPM    CT    CP"]
    for rpm in range(1800, 6600, 300):  # 16 点
        n = rpm / 60.0
        ratio = n / N_REF
        jitter = 1.0 + 0.002 * math.sin(rpm / 300.0) if noise else 1.0
        lines.append(
            f"{rpm}    {ct0 * ratio**a_t * jitter:.8f}    {cp0 * ratio**a_p * jitter:.8f}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_catalog(directory: Path, *, noise: bool = True) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    write_static(directory / "apce_10x6_static_t0001.txt", 0.105, -0.02, 0.047, -0.035, noise=noise)
    write_static(directory / "apcsf_11x5_static_t0002.txt", 0.135, 0.01, 0.062, -0.010, noise=noise)
    return ["apce_10x6_static_t0001.txt", "apcsf_11x5_static_t0002.txt"]


class BootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        names = make_catalog(self.dir / "uiuc")
        self.entries = boot.catalog.load_catalog(self.dir / "uiuc", names)
        self.result = boot.bootstrap_catalog(self.entries, n_boot=60, seed=7)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_ci_contains_point_estimate(self) -> None:
        for prop in self.result["props"]:
            for key in ("ct0", "aT", "cp0", "aP"):
                self.assertLessEqual(prop[f"{key}_lo"], prop[key] + 1e-12)
                self.assertGreaterEqual(prop[f"{key}_hi"], prop[key] - 1e-12)
            for key in ("ct_err", "cp_err"):
                self.assertLessEqual(prop[f"{key}_lo"], prop[f"{key}_hi"])

    def test_deterministic_with_seed(self) -> None:
        again = boot.bootstrap_catalog(self.entries, n_boot=60, seed=7)
        for a, b in zip(self.result["props"], again["props"]):
            for key in ("ct0", "aT", "cp0", "aP"):
                self.assertEqual(a[key], b[key])
                self.assertEqual(a[f"{key}_lo"], b[f"{key}_lo"])
                self.assertEqual(a[f"{key}_hi"], b[f"{key}_hi"])

    def test_noiseless_data_gives_tight_ci(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            names = make_catalog(base / "uiuc", noise=False)
            entries = boot.catalog.load_catalog(base / "uiuc", names)
            result = boot.bootstrap_catalog(entries, n_boot=30, seed=3)
        for prop in result["props"]:
            self.assertLess(prop["ct0_hi"] - prop["ct0_lo"], 1e-7)
            self.assertLess(prop["aT_hi"] - prop["aT_lo"], 1e-7)

    def test_pooled_present(self) -> None:
        pooled = self.result["pooled"]
        self.assertEqual(pooled["props"], 2)
        self.assertEqual(pooled["points"], 32)
        self.assertIn("aT_lo", pooled)
        self.assertIn("aT_hi", pooled)

    def test_invalid_n_boot_and_ci(self) -> None:
        entry = self.entries[0]
        with self.assertRaises(ValueError):
            boot.bootstrap_entry(entry, n_boot=3)
        with self.assertRaises(ValueError):
            boot.bootstrap_entry(entry, ci_level=1.5)


class OutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        names = make_catalog(self.dir / "uiuc")
        entries = boot.catalog.load_catalog(self.dir / "uiuc", names)
        self.result = boot.bootstrap_catalog(entries, n_boot=40, seed=11)
        self.summary = boot.build_summary(self.result, n_boot=40, seed=11, ci_level=boot.CI_LEVEL)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_csv_fields_and_overwrite(self) -> None:
        out = self.dir / "boot.csv"
        boot.write_csv(self.result["props"], out)
        with out.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 2)
        self.assertEqual(list(rows[0].keys()), boot.OUT_FIELDS)
        with self.assertRaises(FileExistsError):
            boot.write_csv(self.result["props"], out)

    def test_summary_flags(self) -> None:
        out = self.dir / "boot.json"
        boot.write_summary(self.summary, out)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        self.assertTrue(loaded["do_not_apply"])
        self.assertIn("不是本项目实测标定", loaded["disclaimer"])
        self.assertEqual(loaded["n_boot_requested"], 40)
        self.assertEqual(loaded["ci_level"], boot.CI_LEVEL)
        self.assertLessEqual(loaded["props"][0]["ct0_lo"], loaded["props"][0]["ct0"])
        with self.assertRaises(FileExistsError):
            boot.write_summary(self.summary, out)

    def test_plot_outputs_png(self) -> None:
        out = self.dir / "boot.png"
        boot.plot_bootstrap(self.result, out)
        self.assertGreater(out.stat().st_size, 10_000)
        with self.assertRaises(FileExistsError):
            boot.plot_bootstrap(self.result, out)


class CliTests(unittest.TestCase):
    def test_main_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            names = make_catalog(base / "uiuc")
            argv = [
                "--reference-dir",
                str(base / "uiuc"),
                "--files",
                *names,
                "--output",
                str(base / "boot.csv"),
                "--summary",
                str(base / "boot.json"),
                "--figure",
                str(base / "boot.png"),
                "--n-boot",
                "25",
            ]
            self.assertEqual(boot.main(argv), 0)
            self.assertTrue((base / "boot.csv").exists() and (base / "boot.png").exists())
            self.assertEqual(boot.main(argv), 2)
            self.assertEqual(boot.main(argv + ["--overwrite"]), 0)

    def test_main_missing_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            code = boot.main(
                [
                    "--reference-dir",
                    str(base / "nope"),
                    "--files",
                    "apce_10x6_static_t0001.txt",
                    "--output",
                    str(base / "o.csv"),
                    "--summary",
                    str(base / "o.json"),
                    "--figure",
                    str(base / "o.png"),
                ]
            )
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
