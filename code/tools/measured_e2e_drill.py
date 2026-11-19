"""MEASURED 端到端演练（v0.1）——用人工合成的「演练夹具」打通门禁 → 流水线 → 汇总 → 选型。

目的
----
在真实台架数据（M0.4）到位前，验证 MEASURED 通路的**代码与标记纪律**是否闭环：
    1. `measured_readiness.assess` 判定就绪；
    2. `compute_efficiency(require_measured=True)` 通过并输出 `simulated:false` 汇总；
    3. `aggregate_efficiency(require_measured=True)` 只接受 MEASURED 来源；
    4. `match_propulsion.assert_measured` + 选型匹配可用；
    5. 负向对照：把同一数值改成 `simulated:true / mode:simulate` 后，门禁拒绝、流水线抛错。

边界
----
- 夹具全部写在**临时目录**（或显式 `--out-dir`），绝不写入仓库 `data/`；
- 夹具是人工合成的稳态数据，meta/标定中明确标注「演练夹具，不是真实测量/标定」；
- 本演练只证明标记与流程可闭环，**不证明**物理真实性、标定准确性或安全；
  真实 MEASURED 数据仍须双人签字、现场记录与 D032/D035 要求。
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _sub in ("processing", "selection"):
    _p = PROJECT_ROOT / "code" / _sub
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import aggregate_efficiency as agg  # noqa: E402
import compute_efficiency as ce  # noqa: E402
import match_propulsion as mp  # noqa: E402
import measured_readiness as mr  # noqa: E402

SCHEMA_VERSION = "0.1"
DRILL_DIAMETER_M = 0.4572
# 与 calib_SIM_PHYS10x4 同量级，但此处标定文件显式标记 simulated:false，仅作演练夹具
DRILL_THRUST_K = 0.00035
DRILL_TORQUE_K = 5.882352941176471e-06
DRILL_ROWS = 1200
DRILL_SAMPLE_RATE = 1000.0
DRILL_THRUST_RAW = 28000
DRILL_TORQUE_RAW = 17000
DRILL_RPM = 6000.0
DRILL_VOLTAGE_V = 22.2
DRILL_CURRENT_A = 8.0
DRILL_DATA_NOTICE = "演练夹具：人工合成稳态数据，仅用于验证 MEASURED 通路，不是真实测量"
DRILL_CALIB_SOURCE = "演练夹具：非真实标定，仅用于打通 MEASURED 通路，不得用于实验结论"


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds")


def make_calibration(path: Path, *, simulated: bool = False) -> dict:
    calibration = {
        "schema_version": SCHEMA_VERSION,
        "simulated": simulated,
        "source": DRILL_CALIB_SOURCE,
        "created_at": _iso(datetime(2026, 11, 19, 21, 0, 0) + timedelta(seconds=0)),
        "thrust": {"k": DRILL_THRUST_K, "b": 0.0, "unit": "N/count"},
        "torque": {"k": DRILL_TORQUE_K, "b": 0.0, "unit": "N·m/count"},
        "propeller": {"diameter_m": DRILL_DIAMETER_M},
    }
    path.write_text(json.dumps(calibration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return calibration


def make_raw_pair(directory: Path, *, stem: str, simulated: bool = False) -> tuple[Path, Path]:
    """写一对 `<stem>.csv` + `<stem>.meta.json`（人工合成稳态数据）。"""
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / f"{stem}.csv"
    meta_path = directory / f"{stem}.meta.json"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(ce.RAW_FIELDS)
        started = datetime(2026, 11, 19, 21, 0, 0)
        for index in range(DRILL_ROWS):
            writer.writerow(
                [
                    _iso(started + timedelta(milliseconds=index)),
                    f"{index / DRILL_SAMPLE_RATE:.3f}",
                    index,
                    int(index),
                    DRILL_THRUST_RAW,
                    DRILL_TORQUE_RAW,
                    f"{DRILL_RPM:.1f}",
                    f"{DRILL_VOLTAGE_V:.3f}",
                    f"{DRILL_CURRENT_A:.3f}",
                    "30.0",
                    "24.0",
                    "45.0",
                    "96.0",
                ]
            )
    meta = {
        "schema_version": SCHEMA_VERSION,
        "run_id": stem,
        "status": "ok",
        "mode": "serial",
        "simulated": simulated,
        "data_notice": DRILL_DATA_NOTICE,
        "started_at": _iso(datetime(2026, 11, 19, 21, 0, 0)),
        "finished_at": _iso(datetime(2026, 11, 19, 21, 0, 2)),
        "wall_duration_s": DRILL_ROWS / DRILL_SAMPLE_RATE,
        "rows_written": DRILL_ROWS,
        "csv_file": csv_path.name,
        "serial": {"port": "COM_DRILL", "baud": 115200},
        "simulation": None,
        "test": {
            "operator": "演练（非真实测量）",
            "combo": "DRILL10x4.5",
            "motor": "DRILL-M",
            "esc": "DRILL-ESC",
            "prop": "10x4.5",
            "voltage_set_v": DRILL_VOLTAGE_V,
            "throttle_set_pct": 50.0,
            "repeat": "R1",
            "prop_diameter_m": DRILL_DIAMETER_M,
            "notes": "MEASURED 端到端演练夹具；不是真实台架数据",
        },
        "error": None,
    }
    if simulated:
        meta["mode"] = "simulate"
        meta["simulation"] = {"seed": 20261119, "sample_rate_sps": DRILL_SAMPLE_RATE}
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return csv_path, meta_path


def _check(checks: list[dict], name: str, ok: bool, detail: str) -> None:
    checks.append({"name": name, "ok": bool(ok), "detail": detail})


def run_drill(out_dir: Path | None = None) -> dict:
    """执行 5 步演练；返回 {ok, checks, stats, workdir}。"""
    temporary = tempfile.TemporaryDirectory(prefix="measured_e2e_drill_") if out_dir is None else None
    root = Path(temporary.name) if temporary is not None else Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    checks: list[dict] = []
    stats: dict = {}
    try:
        calib_path = root / "calib_DRILL.json"
        calib = make_calibration(calib_path, simulated=False)
        loaded = ce.load_calibration(calib_path)
        _check(checks, "load_calibration", True, f"simulated={loaded['simulated']}")

        raw_csv, _meta_path = make_raw_pair(root, stem="DRILL_MEASURED", simulated=False)
        report = mr.assess(raw_csv, calib_path)
        _check(checks, "readiness_ready", report["ready"] and not report["errors"], f"errors={report['errors']}")

        summary_json = root / "DRILL_MEASURED_efficiency.json"
        summary = ce.compute_efficiency(
            raw_csv,
            calib_path,
            window_s=1.0,
            steady_mode="auto",
            steady_window_s=0.5,
            steady_threshold=0.01,
            output_csv=root / "DRILL_MEASURED_processed.csv",
            summary_json=summary_json,
            overwrite=True,
            require_measured=True,
        )
        thrust_mean = summary["window"]["thrust_N"]["mean"]
        _check(
            checks,
            "pipeline_measured",
            summary["simulated"] is False and summary["window"]["samples"] >= int(DRILL_SAMPLE_RATE * 0.5),
            f"simulated={summary['simulated']} samples={summary['window']['samples']} T={thrust_mean:.3f}N",
        )

        runs_csv = root / "efficiency_map_runs.csv"
        grid_csv = root / "efficiency_map_grid.csv"
        agg_result = agg.aggregate(
            [summary_json],
            runs_csv,
            grid_csv,
            overwrite=True,
            require_measured=True,
        )
        _check(
            checks,
            "aggregate_measured",
            agg_result["sources"] == ["MEASURED"],
            f"sources={agg_result['sources']} rows={len(agg_result['rows'])}",
        )

        runs = mp.load_runs(runs_csv)
        mp.assert_measured(runs)
        matched = mp.match(runs, thrust_required_n=thrust_mean, thrust_tolerance=0.1, top_n=3)
        _check(
            checks,
            "selection_measured",
            len(matched) >= 1,
            f"candidates={len(matched)} top={matched[0]['run_id'] if matched else '-'}",
        )

        # 负向对照：同样数值但显式标记 SIM → 门禁/流水线必须拒绝
        sim_csv, _ = make_raw_pair(root, stem="DRILL_SIM", simulated=True)
        sim_calib_path = root / "calib_SIM_DRILL.json"
        make_calibration(sim_calib_path, simulated=True)
        sim_report = mr.assess(sim_csv, sim_calib_path)
        rejected = {"readiness": not sim_report["ready"]}
        try:
            ce.compute_efficiency(
                sim_csv,
                sim_calib_path,
                window_s=1.0,
                output_csv=root / "DRILL_SIM_processed.csv",
                summary_json=root / "DRILL_SIM_efficiency.json",
                overwrite=True,
                require_measured=True,
            )
            rejected["pipeline"] = False
        except ValueError as exc:  # 预期路径
            rejected["pipeline"] = "MEASURED 守门拒绝" in str(exc)
        _check(
            checks,
            "negative_sim_rejected",
            rejected["readiness"] and rejected["pipeline"],
            f"readiness_rejected={rejected['readiness']} pipeline_rejected={rejected['pipeline']}",
        )

        stats.update(
            {
                "thrust_N": thrust_mean,
                "torque_Nm": summary["window"]["torque_Nm"]["mean"],
                "eta_sys": summary["window"]["eta_sys"]["mean"],
                "samples": summary["window"]["samples"],
                "candidates": len(matched),
                "workdir": str(root),
            }
        )
        return {"ok": all(item["ok"] for item in checks), "checks": checks, "stats": stats, "workdir": str(root)}
    finally:
        if temporary is not None:
            with contextlib.suppress(Exception):
                temporary.cleanup()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MEASURED 端到端演练：门禁 → 流水线 → 汇总 → 选型 + 负向对照（全部使用临时演练夹具）"
    )
    parser.add_argument("--out-dir", type=Path, default=None, help="可选：保留演练产物到指定目录（默认临时目录）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run_drill(args.out_dir)
    except Exception as exc:  # noqa: BLE001 —— CLI 边界：打印错误并给出 exit 2
        print(f"错误：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("MEASURED 端到端演练（临时夹具，非真实测量）")
        for item in result["checks"]:
            print(f"  [{'OK' if item['ok'] else 'FAIL'}] {item['name']}: {item['detail']}")
        stats = result["stats"]
        print(
            f"  统计：T={stats['thrust_N']:.3f} N，τ={stats['torque_Nm']:.4f} N·m，"
            f"η_sys={stats['eta_sys']:.4f}，稳态 {stats['samples']} 点，选型候选 {stats['candidates']} 个"
        )
        print(f"  工作目录：{result['workdir']}")
        print("  注意：演练夹具不是真实测量；真实 MEASURED 数据须双人签字与现场记录。")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
