# -*- coding: utf-8 -*-
r"""仿真战役：物理模型 → 合成 raw CSV/meta → 效率流水线 → 汇总 → 效率地图。

流程（一键跑通，全程 SIM 标注，不是实验结果）：
1. `propulsion_model.solve_operating_point` 对每个 (电压, 油门) 求稳态工作点；
2. 生成协议 v0.1 的合成 raw CSV（含 ADC 计数、噪声、稳态前斜坡）与同名 meta.json；
3. 调用 `compute_efficiency` 得到逐样本物理量 CSV 与稳态窗口 efficiency.json；
4. 调用 `aggregate_efficiency.aggregate` 生成 runs/grid CSV；
5. 调用 `plot_efficiency_map.plot_map` 生成效率地图 PNG；
6. 写出 model vs pipeline 对比表（验证换算与效率链闭环）。

用法：
    py -3.12 code\simulation\simulate_campaign.py
    py -3.12 code\simulation\simulate_campaign.py --voltages 11.1,22.2 --throttles 25,100 --repeats 1
    py -3.12 code\simulation\simulate_campaign.py --force      # 覆盖已有产物

数据诚信：合成数据与隐藏"真值"标定均标记 simulated=true；
效率地图/对比表只能用于软件联调与建模验证，绝不能当作实验结果。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _sub in ("processing", "simulation"):
    _path = ROOT / "code" / _sub
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from aggregate_efficiency import aggregate  # noqa: E402
from compute_efficiency import RAW_FIELDS, compute_efficiency  # noqa: E402
from plot_efficiency_map import plot_map  # noqa: E402
from propulsion_model import ModelParams, solve_operating_point  # noqa: E402

CALIB_THRUST_K = 0.00035  # N / count
CALIB_THRUST_B = 0.0
CALIB_TORQUE_K = 5.882352941176471e-06  # N·m / count
CALIB_TORQUE_B = 0.0
CALIB_DEFAULT_NAME = "calib_SIM_PHYS10x4.json"
COMBO_NAME = "SIM10x4.5"
OPERATOR = "仿真建模"
DATA_NOTICE = "物理仿真合成数据（propulsion_model v0.1）：仅用于流程联调/建模验证，不是实验结果"
BASE_TIME = datetime(2026, 11, 19, 20, 0, 0, tzinfo=timezone(timedelta(hours=8)))

CAMP_SUMMARY_FIELDS = [
    "run_id",
    "voltage_set_v",
    "throttle_set_pct",
    "repeat",
    "rpm_model",
    "rpm_pipe",
    "thrust_n_model",
    "thrust_n_pipe",
    "torque_nm_model",
    "torque_nm_pipe",
    "battery_current_a_model",
    "current_a_pipe",
    "eta_em_model",
    "eta_em_pipe",
    "fm_model",
    "fm_pipe",
    "eta_sys_model",
    "eta_sys_pipe",
    "thrust_rel_err",
    "rpm_rel_err",
    "eta_sys_rel_err",
]


def make_run_id(voltage_v: float, throttle_pct: float, repeat: int) -> str:
    return f"20261119_SIM_{voltage_v:g}V_{throttle_pct:g}pct_R{repeat}"


def build_calibration(params: ModelParams, created_at: str) -> dict:
    """隐藏"真值"标定：合成 ADC 计数 → 物理量。"""
    return {
        "schema_version": "0.1",
        "simulated": True,
        "source": "物理仿真隐藏真值标定（propulsion_model v0.1）：仅用于仿真闭环验证，绝不可用于实机测量或论文结论",
        "hidden_truth_of": "code/simulation/propulsion_model.py",
        "calibrated_at": created_at,
        "operator": OPERATOR,
        "thrust": {"k": CALIB_THRUST_K, "b": CALIB_THRUST_B},
        "torque": {"k": CALIB_TORQUE_K, "b": CALIB_TORQUE_B},
        "propeller": {"diameter_m": params.diameter_m},
        "notes": "合成 ADC 计数标定：k 由仿真采集卡满量程假定决定；真实系统必须用静态砝码双人标定",
    }


def ensure_calibration(path: Path, params: ModelParams, force: bool = False) -> Path:
    """确保仿真标定文件存在且与当前模型参数一致。"""
    expected = build_calibration(params, datetime.now().astimezone().isoformat(timespec="seconds"))
    if path.exists() and not force:
        try:
            with path.open(encoding="utf-8") as handle:
                existing = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"已存在的标定文件无法读取：{path}（如需重建请 --force）") from exc
        checks = [
            ("thrust", "k"),
            ("thrust", "b"),
            ("torque", "k"),
            ("torque", "b"),
        ]
        for block, key in checks:
            if not math.isclose(float(existing[block][key]), float(expected[block][key]), rel_tol=1e-9, abs_tol=1e-12):
                raise ValueError(f"已存在标定与当前模型参数不一致（{block}.{key}），如需重建请 --force：{path}")
        existing_d = float((existing.get("propeller") or {}).get("diameter_m", 0.0) or 0.0)
        if not math.isclose(existing_d, params.diameter_m, rel_tol=1e-9):
            raise ValueError(f"已存在标定桨径与模型不一致，如需重建请 --force：{path}")
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(expected, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def simulate_run(
    params: ModelParams,
    voltage_v: float,
    throttle_pct: float,
    duration_s: float,
    sample_rate: float,
    seed: int,
    noise: bool = True,
) -> tuple[list[dict], dict]:
    """生成一次仿真的 raw 数据行与工作点。"""
    if duration_s <= 0:
        raise ValueError("duration_s 必须 > 0")
    if sample_rate < 100:
        raise ValueError("sample_rate 必须 >= 100 S/s")
    throttle = throttle_pct / 100.0
    operating_point = solve_operating_point(params, voltage_v, throttle)
    rng = random.Random(seed)
    total = int(round(duration_s * sample_rate))
    if total < 10:
        raise ValueError("时长×采样率样本数太少")

    ramp_samples = max(1, min(total // 4, int(round(0.2 * sample_rate))))
    bus_voltage = voltage_v
    battery_current = operating_point["p_elec_w"] / bus_voltage

    def jitter(sigma: float) -> float:
        return rng.gauss(0.0, sigma) if noise else 0.0

    rows: list[dict] = []
    for index in range(total):
        ramp = 1.0 if index >= ramp_samples else 0.8 + 0.2 * index / ramp_samples
        thrust = max(0.0, operating_point["thrust_n"] * ramp + jitter(0.02))
        torque = max(0.0, operating_point["torque_nm"] * ramp + jitter(0.001))
        rpm = max(0.0, operating_point["rpm"] * ramp + jitter(3.0))
        voltage = max(0.0, bus_voltage + jitter(0.01))
        current = max(0.0, battery_current * ramp + jitter(0.02))
        motor_temp = min(90.0, 25.0 + 0.05 * operating_point["p_shaft_w"] * ramp) + jitter(0.2)
        ambient = params.ambient_temp_c + jitter(0.1)
        humidity = 45.0 + jitter(0.5)
        pressure = params.pressure_kpa + jitter(0.05)

        rows.append(
            {
                "host_ts": (BASE_TIME + timedelta(seconds=index / sample_rate)).isoformat(timespec="milliseconds"),
                "elapsed_s": f"{index / sample_rate:.3f}",
                "seq": index,
                "device_time_ms": int(round(index * 1000.0 / sample_rate)),
                "thrust_raw": int(round(thrust / CALIB_THRUST_K)),
                "torque_raw": int(round(torque / CALIB_TORQUE_K)),
                "rpm": f"{rpm:.1f}",
                "voltage_v": f"{voltage:.3f}",
                "current_a": f"{current:.3f}",
                "motor_temp_c": f"{motor_temp:.1f}",
                "ambient_temp_c": f"{ambient:.1f}",
                "humidity_pct": f"{humidity:.1f}",
                "pressure_kpa": f"{pressure:.2f}",
            }
        )
    return rows, operating_point


def write_run(raw_dir: Path, run_id: str, rows: list[dict], meta: dict) -> tuple[Path, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    csv_path = raw_dir / f"{run_id}.csv"
    meta_path = raw_dir / f"{run_id}.meta.json"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with meta_path.open("w", encoding="utf-8") as handle:
        json.dump(meta, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return csv_path, meta_path


def build_meta(
    run_id: str,
    params: ModelParams,
    operating_point: dict,
    voltage_v: float,
    throttle_pct: float,
    repeat: int,
    duration_s: float,
    sample_rate: float,
    rows_written: int,
    started: datetime,
    finished: datetime,
    seed: int,
) -> dict:
    return {
        "schema_version": "0.1",
        "run_id": run_id,
        "status": "ok",
        "mode": "simulate",
        "simulated": True,
        "data_notice": DATA_NOTICE,
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "wall_duration_s": round((finished - started).total_seconds(), 3),
        "rows_written": rows_written,
        "csv_file": f"{run_id}.csv",
        "serial": None,
        "simulation": {
            "model": "propulsion_model v0.1",
            "seed": seed,
            "sample_rate_sps": sample_rate,
            "params": asdict(params),
            "operating_point": {key: operating_point[key] for key in operating_point},
        },
        "test": {
            "operator": OPERATOR,
            "combo": COMBO_NAME,
            "motor": "仿真电机 400KV",
            "esc": "仿真电调 40A",
            "prop": "仿真桨 10x4.5",
            "voltage_set_v": voltage_v,
            "throttle_set_pct": throttle_pct,
            "repeat": repeat,
            "prop_diameter_m": params.diameter_m,
            "notes": "物理模型合成数据；参数为文献量级+工程取值，非具体产品实测",
        },
        "error": None,
    }


def _pipe_mean(summary: dict, key: str) -> float:
    entry = (summary.get("window") or {}).get(key) or {}
    value = entry.get("mean")
    return float(value) if value is not None else math.nan


def _rel_err(value: float, reference: float) -> float:
    if not math.isfinite(value) or not math.isfinite(reference) or abs(reference) < 1e-12:
        return math.nan
    return (value - reference) / reference


def run_campaign(
    voltages: list[float],
    throttles: list[float],
    *,
    repeats: int = 1,
    duration_s: float = 2.5,
    sample_rate: float = 1000.0,
    window_s: float = 1.5,
    raw_dir: Path | None = None,
    processed_dir: Path | None = None,
    metadata_dir: Path | None = None,
    figures_dir: Path | None = None,
    calib_path: Path | None = None,
    make_plot: bool = True,
    force: bool = False,
    params: ModelParams | None = None,
    base_seed: int = 20261119,
    noise: bool = True,
) -> dict:
    """跑一轮完整仿真战役，返回 {rows, runs_csv, grid_csv, figure, summary_csv, calibration}。"""
    if not voltages or not throttles:
        raise ValueError("voltages/throttles 不能为空")
    if any(value <= 0 for value in voltages):
        raise ValueError("电压必须 > 0")
    if any(not 0 < value <= 100 for value in throttles):
        raise ValueError("油门必须落在 (0, 100]")
    if repeats < 1:
        raise ValueError("repeats 必须 >= 1")
    model = params or ModelParams()

    raw_dir = Path(raw_dir) if raw_dir else ROOT / "data" / "raw"
    processed_dir = Path(processed_dir) if processed_dir else ROOT / "data" / "processed"
    metadata_dir = Path(metadata_dir) if metadata_dir else ROOT / "data" / "metadata"
    figures_dir = Path(figures_dir) if figures_dir else processed_dir / "figures"
    calib_path = Path(calib_path) if calib_path else metadata_dir / CALIB_DEFAULT_NAME

    runs_csv = processed_dir / "efficiency_map_runs.csv"
    grid_csv = processed_dir / "efficiency_map_grid.csv"
    figure_png = figures_dir / "efficiency_map_v0.1.png"
    summary_csv = processed_dir / "simulation_campaign_summary.csv"

    planned: list[tuple[float, float, int, str]] = []
    for voltage in voltages:
        for throttle in throttles:
            for repeat in range(1, repeats + 1):
                planned.append((voltage, throttle, repeat, make_run_id(voltage, throttle, repeat)))

    conflicts = [
        path
        for _, _, _, run_id in planned
        for path in (
            raw_dir / f"{run_id}.csv",
            raw_dir / f"{run_id}.meta.json",
            processed_dir / f"{run_id}_processed.csv",
            metadata_dir / f"{run_id}_efficiency.json",
        )
        if path.exists()
    ]
    for path in (runs_csv, grid_csv):
        if path.exists():
            conflicts.append(path)
    if make_plot and figure_png.exists():
        conflicts.append(figure_png)
    if summary_csv.exists():
        conflicts.append(summary_csv)
    if conflicts and not force:
        raise FileExistsError(f"已有 {len(conflicts)} 个仿真产物（如需覆盖请 force=True/--force）：{conflicts[0]}")

    calibration = ensure_calibration(calib_path, model, force=force)

    campaign_rows: list[dict] = []
    summaries: list[Path] = []
    for run_index, (voltage, throttle, repeat, run_id) in enumerate(planned):
        rows, operating_point = simulate_run(
            model,
            voltage,
            throttle,
            duration_s,
            sample_rate,
            seed=base_seed + run_index,
            noise=noise,
        )
        started = BASE_TIME + timedelta(seconds=run_index * 60)
        finished = started + timedelta(seconds=duration_s)
        meta = build_meta(
            run_id,
            model,
            operating_point,
            voltage,
            throttle,
            repeat,
            duration_s,
            sample_rate,
            len(rows),
            started,
            finished,
            seed=base_seed + run_index,
        )
        csv_path, _ = write_run(raw_dir, run_id, rows, meta)

        summary = compute_efficiency(
            csv_path,
            calibration,
            window_s=window_s,
            output_csv=processed_dir / f"{run_id}_processed.csv",
            summary_json=metadata_dir / f"{run_id}_efficiency.json",
            overwrite=force,
        )
        summaries.append(metadata_dir / f"{run_id}_efficiency.json")

        rpm_pipe = _pipe_mean(summary, "rpm")
        thrust_pipe = _pipe_mean(summary, "thrust_N")
        torque_pipe = _pipe_mean(summary, "torque_Nm")
        current_pipe = _pipe_mean(summary, "current_a")
        eta_em_pipe = _pipe_mean(summary, "eta_em")
        fm_pipe = _pipe_mean(summary, "fm")
        eta_sys_pipe = _pipe_mean(summary, "eta_sys")
        campaign_rows.append(
            {
                "run_id": run_id,
                "voltage_set_v": voltage,
                "throttle_set_pct": throttle,
                "repeat": repeat,
                "rpm_model": operating_point["rpm"],
                "rpm_pipe": rpm_pipe,
                "thrust_n_model": operating_point["thrust_n"],
                "thrust_n_pipe": thrust_pipe,
                "torque_nm_model": operating_point["torque_nm"],
                "torque_nm_pipe": torque_pipe,
                "battery_current_a_model": operating_point["p_elec_w"] / voltage,
                "current_a_pipe": current_pipe,
                "eta_em_model": operating_point["eta_em"],
                "eta_em_pipe": eta_em_pipe,
                "fm_model": operating_point["fm"],
                "fm_pipe": fm_pipe,
                "eta_sys_model": operating_point["eta_sys"],
                "eta_sys_pipe": eta_sys_pipe,
                "thrust_rel_err": _rel_err(thrust_pipe, operating_point["thrust_n"]),
                "rpm_rel_err": _rel_err(rpm_pipe, operating_point["rpm"]),
                "eta_sys_rel_err": _rel_err(eta_sys_pipe, operating_point["eta_sys"]),
            }
        )

    aggregate_result = aggregate(summaries, runs_csv, grid_csv, overwrite=True)
    figure = None
    if make_plot:
        figure = plot_map(runs_csv, figure_png, field="eta_sys", overwrite=True)

    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CAMP_SUMMARY_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in sorted(campaign_rows, key=lambda item: (item["voltage_set_v"], item["throttle_set_pct"])):
            writer.writerow(
                {
                    key: (f"{value:.10g}" if isinstance(value, float) and math.isfinite(value) else value)
                    for key, value in row.items()
                }
            )

    return {
        "rows": campaign_rows,
        "aggregate": aggregate_result,
        "runs_csv": runs_csv,
        "grid_csv": grid_csv,
        "figure": figure,
        "summary_csv": summary_csv,
        "calibration": calibration,
    }


def _parse_float_list(text: str) -> list[float]:
    values = [item.strip() for item in text.split(",") if item.strip()]
    if not values:
        raise ValueError("列表为空")
    return [float(item) for item in values]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="仿真战役：模型 → 合成 raw → 效率流水线 → 效率地图（SIM，非实验）")
    parser.add_argument("--voltages", default="11.1,14.8,22.2,29.6", help="母线电压列表 V，逗号分隔")
    parser.add_argument("--throttles", default="25,50,75,100", help="油门百分比列表，逗号分隔")
    parser.add_argument("--repeats", type=int, default=1, help="每工况重复次数")
    parser.add_argument("--duration", type=float, default=2.5, help="每次采集时长 s")
    parser.add_argument("--sample-rate", type=float, default=1000.0, help="采样率 S/s")
    parser.add_argument("--window", type=float, default=1.5, help="稳态窗口 s")
    parser.add_argument("--raw-dir", default=None, help="raw CSV 目录（默认 data/raw）")
    parser.add_argument("--processed-dir", default=None, help="processed 目录（默认 data/processed）")
    parser.add_argument("--metadata-dir", default=None, help="metadata 目录（默认 data/metadata）")
    parser.add_argument("--figures-dir", default=None, help="图件目录（默认 data/processed/figures）")
    parser.add_argument("--calib", default=None, help="仿真标定 JSON（默认 metadata/calib_SIM_PHYS10x4.json）")
    parser.add_argument("--no-plot", action="store_true", help="不生成效率地图 PNG")
    parser.add_argument("--force", action="store_true", help="覆盖已有产物（默认拒绝）")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_campaign(
            _parse_float_list(args.voltages),
            _parse_float_list(args.throttles),
            repeats=args.repeats,
            duration_s=args.duration,
            sample_rate=args.sample_rate,
            window_s=args.window,
            raw_dir=Path(args.raw_dir) if args.raw_dir else None,
            processed_dir=Path(args.processed_dir) if args.processed_dir else None,
            metadata_dir=Path(args.metadata_dir) if args.metadata_dir else None,
            figures_dir=Path(args.figures_dir) if args.figures_dir else None,
            calib_path=Path(args.calib) if args.calib else None,
            make_plot=not args.no_plot,
            force=args.force,
        )
    except (FileExistsError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    print("⚠ 仿真战役：合成数据，不是实验结果")
    print(f"工况数：{len(result['rows'])}；标定：{result['calibration']}")
    print(f"runs CSV：{result['runs_csv']}")
    print(f"grid CSV：{result['grid_csv']}")
    if result["figure"]:
        print(f"效率地图：{result['figure']}")
    print(f"模型对比表：{result['summary_csv']}")
    for row in result["rows"]:
        print(
            f"  {row['run_id']}: η_sys model={row['eta_sys_model']:.4f} / pipe={row['eta_sys_pipe']:.4f}"
            f"；推力 model={row['thrust_n_model']:.3f} / pipe={row['thrust_n_pipe']:.3f} N"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
