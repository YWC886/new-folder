"""`code/tools/measured_e2e_drill.py` 的测试（5 项）。"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import measured_e2e_drill as drill


class DrillTests(unittest.TestCase):
    def test_drill_all_checks_pass(self) -> None:
        result = drill.run_drill()
        self.assertTrue(result["ok"])
        names = [item["name"] for item in result["checks"]]
        self.assertEqual(
            names,
            ["load_calibration", "readiness_ready", "pipeline_measured", "aggregate_measured", "selection_measured", "negative_sim_rejected"],
        )
        self.assertTrue(all(item["ok"] for item in result["checks"]))
        self.assertGreaterEqual(result["stats"]["candidates"], 1)
        self.assertGreater(result["stats"]["thrust_N"], 5.0)

    def test_negative_control_rejects_sim(self) -> None:
        result = drill.run_drill()
        negative = next(item for item in result["checks"] if item["name"] == "negative_sim_rejected")
        self.assertTrue(negative["ok"])
        self.assertIn("readiness_rejected=True", negative["detail"])
        self.assertIn("pipeline_rejected=True", negative["detail"])

    def test_drill_leaves_no_repo_artifacts(self) -> None:
        data_dir = drill.PROJECT_ROOT / "data" / "raw"
        before = {path.name for path in data_dir.glob("DRILL*")}
        drill.run_drill()
        after = {path.name for path in data_dir.glob("DRILL*")}
        self.assertEqual(before, after)
        self.assertEqual(after, set())

    def test_cli_json_returns_zero(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = drill.main(["--json"])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(len(payload["checks"]), 6)

    def test_cli_out_dir_keeps_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "drill"
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = drill.main(["--out-dir", str(out_dir), "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(Path(payload["workdir"]).resolve(), out_dir.resolve())
            self.assertTrue((out_dir / "calib_DRILL.json").is_file())
            self.assertTrue((out_dir / "DRILL_MEASURED.csv").is_file())
            self.assertTrue((out_dir / "DRILL_MEASURED.meta.json").is_file())
            self.assertTrue((out_dir / "efficiency_map_runs.csv").is_file())


if __name__ == "__main__":
    unittest.main()
