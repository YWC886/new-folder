# -*- coding: utf-8 -*-
"""plot_efficiency_map.py 的冒烟测试：网格图与单点图都能出 PNG，且禁止默认覆盖。

v0.3 新增：散点/热力图开启不确定度（show_uncertainty）能出 PNG；U 列缺失时 warning 不致命。
"""
from __future__ import annotations

import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

from aggregate_efficiency import RUN_FIELDS
from plot_efficiency_map import plot_map


def write_runs(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            record = {field: "" for field in RUN_FIELDS}
            record.update(row)
            writer.writerow(record)


class PlotEfficiencyMapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_grid_plot_created(self) -> None:
        runs = []
        for voltage in (14.8, 22.2):
            for throttle in (30.0, 50.0):
                runs.append(
                    {
                        "run_id": f"SIM_V{voltage}_T{throttle}",
                        "source": "SIM",
                        "combo": "DEMO",
                        "voltage_set_v": str(voltage),
                        "throttle_set_pct": str(throttle),
                        "eta_em_mean": "0.35",
                        "fm_mean": "0.80",
                        "eta_sys_mean": str(0.2 + voltage / 100.0 + throttle / 1000.0),
                    }
                )
        runs_csv = self.root / "runs.csv"
        write_runs(runs_csv, runs)
        output = self.root / "figs" / "map.png"
        result = plot_map(runs_csv, output, field="eta_sys")
        self.assertEqual(result, output)
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 5000)

    def test_single_point_plot_and_overwrite_protection(self) -> None:
        runs_csv = self.root / "one.csv"
        write_runs(
            runs_csv,
            [
                {
                    "run_id": "SIM_ONE",
                    "source": "SIM",
                    "combo": "DEMO",
                    "voltage_set_v": "22.2",
                    "throttle_set_pct": "50",
                    "eta_sys_mean": "0.2843",
                    "eta_em_mean": "0.354",
                    "fm_mean": "0.803",
                }
            ],
        )
        output = self.root / "one.png"
        plot_map(runs_csv, output, field="eta_sys")
        self.assertTrue(output.is_file())
        with self.assertRaises(FileExistsError):
            plot_map(runs_csv, output, field="eta_sys")
        plot_map(runs_csv, output, field="eta_sys", overwrite=True)

    def test_invalid_field_rejected(self) -> None:
        runs_csv = self.root / "runs.csv"
        write_runs(
            runs_csv,
            [
                {
                    "run_id": "X",
                    "source": "SIM",
                    "voltage_set_v": "22.2",
                    "throttle_set_pct": "50",
                    "eta_sys_mean": "0.28",
                }
            ],
        )
        with self.assertRaises(ValueError):
            plot_map(runs_csv, self.root / "x.png", field="bogus")

    def test_scatter_with_uncertainty_created(self) -> None:
        """单点（散点分支）+ show_uncertainty：输出文件名正确，U 齐全时无 warning。"""
        runs_csv = self.root / "scatter_u.csv"
        write_runs(
            runs_csv,
            [
                {
                    "run_id": "SIM_U_ONE",
                    "source": "SIM",
                    "combo": "DEMO",
                    "voltage_set_v": "22.2",
                    "throttle_set_pct": "50",
                    "eta_em_mean": "0.354",
                    "fm_mean": "0.803",
                    "eta_sys_mean": "0.2843",
                    "u_eta_em_k2": "0.0144222051",
                    "u_fm_k2": "0.02256656819",
                    "u_eta_sys_k2": "0.02256656819",
                }
            ],
        )
        output = self.root / "figs" / "efficiency_map_v0.3_single.png"
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = plot_map(runs_csv, output, field="eta_sys", show_uncertainty=True)
        self.assertEqual(result, output)
        self.assertEqual(result.name, "efficiency_map_v0.3_single.png")
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 5000)
        self.assertEqual(stderr.getvalue(), "")

    def test_heatmap_with_uncertainty_created(self) -> None:
        """2×2 热力图 + show_uncertainty：格内两行 ± 标注能正常出 PNG。"""
        runs = []
        for voltage in (14.8, 22.2):
            for throttle in (30.0, 50.0):
                runs.append(
                    {
                        "run_id": f"SIM_V{voltage}_T{throttle}",
                        "source": "SIM",
                        "combo": "DEMO",
                        "voltage_set_v": str(voltage),
                        "throttle_set_pct": str(throttle),
                        "eta_sys_mean": str(0.2 + voltage / 100.0 + throttle / 1000.0),
                        "u_eta_sys_k2": "0.02256656819",
                    }
                )
        runs_csv = self.root / "grid_u.csv"
        write_runs(runs_csv, runs)
        output = self.root / "figs" / "efficiency_map_v0.3_grid.png"
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = plot_map(runs_csv, output, field="eta_sys", show_uncertainty=True)
        self.assertEqual(result, output)
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 5000)
        self.assertEqual(stderr.getvalue(), "")

    def test_missing_uncertainty_warns_but_plots(self) -> None:
        """U 列缺失（空字符串）时 --uncertainty 仍出图，只向 stderr 打 warning。"""
        runs = []
        for voltage in (14.8, 22.2):
            for throttle in (30.0, 50.0):
                runs.append(
                    {
                        "run_id": f"SIM_NOU_V{voltage}_T{throttle}",
                        "source": "SIM",
                        "combo": "DEMO",
                        "voltage_set_v": str(voltage),
                        "throttle_set_pct": str(throttle),
                        "eta_sys_mean": "0.28",
                    }
                )
        runs_csv = self.root / "missing_u.csv"
        write_runs(runs_csv, runs)
        output = self.root / "figs" / "efficiency_map_v0.3_missing_u.png"
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = plot_map(runs_csv, output, field="eta_sys", show_uncertainty=True)
        self.assertEqual(result, output)
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 5000)
        self.assertIn("warning", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
