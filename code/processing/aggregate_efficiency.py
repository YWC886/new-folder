# -*- coding: utf-8 -*-
"""把多次运行的 efficiency.json 汇总为效率地图数据（runs 明细 + 网格统计）。

用法：
    py -3.12 code\\processing\\aggregate_efficiency.py --dir data\\metadata
    py -3.12 code\\processing\\aggregate_efficiency.py data\\metadata\\a_efficiency.json ... --output out\\runs.csv

输出（默认）：
    data\\processed\\efficiency_map_runs.csv  每次运行一行（原始统计均值，供散点/审查）
    data\\processed\\efficiency_map_grid.csv  按 (source, 组合, 电压, 油门) 分组均值±标准差（供作图）

注意：SIM 与实测数据会分到不同 source 行；报告中严禁把 SIM 行当实测结果。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path

METRICS = (
    "thrust_N",
    "torque_Nm",
    "rpm",
    "voltage_v",
    "current_a",
    "p_shaft_w",
    "p_elec_w",
    "eta_em",
    "fm",
    "eta_sys",
)

RUN_FIELDS = [
    "run_id",
    "source",
    "mode",
    "combo",
    "repeat",
    "motor",
    "esc",
    "prop",
    "voltage_set_v",
    "throttle_set_pct",
    "prop_diameter_m",
    "operator",
    "rows",
    "window_samples",
    "window_s",
    "rpm_mean",
    "thrust_N_mean",
    "torque_Nm_mean",
    "voltage_v_mean",
    "current_a_mean",
    "p_shaft_w_mean",
    "p_elec_w_mean",
    "eta_em_mean",
    "fm_mean",
    "eta_sys_mean",
    "air_density_kg_m3",
    "calibration_source",
    "steady_mode",
    "u_eta_em_k2",
    "u_fm_k2",
    "u_eta_sys_k2",
    "file",
]

GRID_FIELDS = [
    "source",
    "combo",
    "voltage_set_v",
    "throttle_set_pct",
    "runs",
    "thrust_n_mean",
    "rpm_mean",
    "eta_em_mean",
    "eta_em_std",
    "fm_mean",
    "fm_std",
    "eta_sys_mean",
    "eta_sys_std",
    "u_eta_em_k2_max",
    "u_fm_k2_max",
    "u_eta_sys_k2_max",
]


def _num(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _fmt(value) -> str:
    number = _num(value)
    return "" if number is None else f"{number:.10g}"


def flatten_summary(summary: dict, path: Path) -> dict:
    """把一份 efficiency.json 压成一行 runs 明细。"""
    if not isinstance(summary, dict) or not isinstance(summary.get("window"), dict):
        raise ValueError("缺少 window 统计段")
    window = summary["window"]
    conditions = summary.get("conditions") or {}
    row = {
        "run_id": str(conditions.get("run_id") or path.stem.replace("_efficiency", "")),
        "source": "SIM" if summary.get("simulated") else "MEASURED",
        "mode": conditions.get("mode", ""),
        "combo": conditions.get("combo", ""),
        "repeat": conditions.get("repeat", ""),
        "motor": conditions.get("motor", ""),
        "esc": conditions.get("esc", ""),
        "prop": conditions.get("prop", ""),
        "voltage_set_v": _fmt(conditions.get("voltage_set_v")),
        "throttle_set_pct": _fmt(conditions.get("throttle_set_pct")),
        "prop_diameter_m": _fmt(conditions.get("prop_diameter_m")),
        "operator": conditions.get("operator", ""),
        "rows": summary.get("rows", ""),
        "window_samples": window.get("samples", ""),
        "window_s": _fmt(window.get("window_s")),
        "air_density_kg_m3": _fmt((summary.get("assumptions") or {}).get("air_density_kg_m3")),
        "calibration_source": summary.get("calibration_source", ""),
        "steady_mode": window.get("mode", ""),
        "file": str(path),
    }
    uncertainty = summary.get("uncertainty") or {}
    row["u_eta_em_k2"] = _fmt(uncertainty.get("U_rel_eta_em_k2"))
    row["u_fm_k2"] = _fmt(uncertainty.get("U_rel_fm_k2"))
    row["u_eta_sys_k2"] = _fmt(uncertainty.get("U_rel_eta_sys_k2"))
    for metric in METRICS:
        entry = window.get(metric) or {}
        row[f"{metric}_mean"] = _fmt(entry.get("mean"))
    return row


def load_summaries(paths: list[Path]) -> tuple[list[dict], list[str]]:
    """读取并展平多个 JSON；坏文件跳过并记录 warning。"""
    rows: list[dict] = []
    warnings: list[str] = []
    seen: dict[str, Path] = {}
    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as handle:
                summary = json.load(handle)
            row = flatten_summary(summary, path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            warnings.append(f"跳过 {path}: {exc}")
            continue
        run_id = row["run_id"]
        if run_id in seen:
            warnings.append(f"重复 run_id「{run_id}」：{seen[run_id]} 与 {path}，保留前者")
            continue
        seen[run_id] = path
        rows.append(row)
    rows.sort(key=lambda item: (_num(item["voltage_set_v"]) or 0.0, _num(item["throttle_set_pct"]) or 0.0, item["combo"]))
    return rows, warnings


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def build_grid(rows: list[dict]) -> list[dict]:
    """按 (source, combo, 电压, 油门) 分组，输出均值±标准差。"""
    groups: dict[tuple, list[dict]] = {}
    for row in rows:
        key = (row["source"], row["combo"], row["voltage_set_v"], row["throttle_set_pct"])
        groups.setdefault(key, []).append(row)

    grid: list[dict] = []
    for (source, combo, voltage, throttle), members in sorted(groups.items()):
        def values(field: str) -> list[float]:
            return [value for value in (_num(member.get(field)) for member in members) if value is not None]

        entry = {
            "source": source,
            "combo": combo,
            "voltage_set_v": voltage,
            "throttle_set_pct": throttle,
            "runs": len(members),
            "thrust_n_mean": "",
            "rpm_mean": "",
        }
        for metric in ("thrust_N", "rpm", "eta_em", "fm", "eta_sys"):
            vals = values(f"{metric}_mean")
            key = "thrust_n_mean" if metric == "thrust_N" else ("rpm_mean" if metric == "rpm" else metric)
            if metric == "eta_em":
                entry["eta_em_mean"] = _fmt(statistics.fmean(vals)) if vals else ""
                entry["eta_em_std"] = _fmt(_std(vals)) if vals else ""
            elif metric == "fm":
                entry["fm_mean"] = _fmt(statistics.fmean(vals)) if vals else ""
                entry["fm_std"] = _fmt(_std(vals)) if vals else ""
            elif metric == "eta_sys":
                entry["eta_sys_mean"] = _fmt(statistics.fmean(vals)) if vals else ""
                entry["eta_sys_std"] = _fmt(_std(vals)) if vals else ""
            else:
                entry[key] = _fmt(statistics.fmean(vals)) if vals else ""
        for field in ("u_eta_em_k2", "u_fm_k2", "u_eta_sys_k2"):
            vals = values(field)
            entry[f"{field}_max"] = _fmt(max(vals)) if vals else ""
        grid.append(entry)
    return grid


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def aggregate(
    paths: list[Path],
    output_csv: Path,
    grid_output: Path | None = None,
    overwrite: bool = False,
) -> dict:
    if not paths:
        raise ValueError("没有输入文件")
    rows, warnings = load_summaries(paths)
    if not rows:
        raise ValueError("没有可用的 efficiency.json：" + "；".join(warnings[:5]))

    targets = [output_csv] + ([grid_output] if grid_output else [])
    for target in targets:
        if target.exists() and not overwrite:
            raise FileExistsError(f"输出已存在（用 --overwrite 覆盖）：{target}")

    grid = build_grid(rows)
    write_csv(output_csv, RUN_FIELDS, rows)
    if grid_output:
        write_csv(grid_output, GRID_FIELDS, grid)

    sources = sorted({row["source"] for row in rows})
    return {
        "rows": rows,
        "grid": grid,
        "warnings": warnings,
        "sources": sources,
        "output_csv": str(output_csv),
        "grid_output": str(grid_output) if grid_output else None,
    }


def discover_inputs(inputs: list[str], directory: str | None, pattern: str) -> list[Path]:
    if inputs:
        return [Path(item) for item in inputs]
    folder = Path(directory) if directory else Path("data/metadata")
    if not folder.is_dir():
        raise FileNotFoundError(f"目录不存在：{folder}")
    return sorted(folder.glob(pattern))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="汇总 efficiency.json 为效率地图数据（runs + grid）")
    parser.add_argument("inputs", nargs="*", help="efficiency.json 路径（留空则用 --dir/--pattern）")
    parser.add_argument("--dir", default=None, help="扫描目录（默认 data/metadata）")
    parser.add_argument("--pattern", default="*_efficiency.json", help="目录内匹配模式")
    parser.add_argument("--output", default="data/processed/efficiency_map_runs.csv", help="runs 明细 CSV")
    parser.add_argument("--grid-output", default="data/processed/efficiency_map_grid.csv", help="网格统计 CSV")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已有输出")
    args = parser.parse_args(argv)

    try:
        paths = discover_inputs(args.inputs, args.dir, args.pattern)
        result = aggregate(paths, Path(args.output), Path(args.grid_output) if args.grid_output else None, args.overwrite)
    except (FileNotFoundError, ValueError, FileExistsError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    print(f"运行数：{len(result['rows'])}；网格行数：{len(result['grid'])}；数据来源：{', '.join(result['sources'])}")
    if "SIM" in result["sources"]:
        print("⚠ 包含 SIM 模拟数据：效率地图仅供流程演示，不是实验结果", file=sys.stderr)
    for warning in result["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)
    print(f"runs CSV：{result['output_csv']}")
    if result["grid_output"]:
        print(f"grid CSV：{result['grid_output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
