# -*- coding: utf-8 -*-
r"""把台架原始 CSV 换算为物理量并计算效率链（电机+电调 / 螺旋桨 / 系统）。

用法：
    py -3.12 code\processing\compute_efficiency.py --input data\raw\<run>.csv --calib <calib.json> --window 3
    py -3.12 code\processing\compute_efficiency.py --input <raw.csv> --calib data\metadata\calib_SIM_DEMO.json `
        --rho 1.204 --output data\processed\<run>_processed.csv --summary data\metadata\<run>_efficiency.json

输入：协议 v0.1 的原始 CSV（13 列）+ 标定 JSON（推力/扭矩的 k、b、桨径；可选空气密度）。
输出：逐样本物理量 CSV（data/processed/）与稳态段汇总 JSON（data/metadata/）；已有文件不覆盖。

计算口径（详见 docs/design/processing_pipeline_v0.1.md）：
    T = k_t * thrust_raw + b_t                        [N]
    Q = k_q * torque_raw + b_q                        [N·m]
    omega = 2*pi*rpm/60                               [rad/s]
    P_shaft = Q * omega                               [W]
    P_elec  = U * I                                   [W]
    eta_em  = P_shaft / P_elec                        （电机+电调效率）
    P_ideal = T**1.5 / sqrt(2*rho*A)                  （动量理论理想功率）
    FM      = P_ideal / P_shaft                       （螺旋桨悬停品质因数）
    eta_sys = P_ideal / P_elec = FM * eta_em          （系统效率）

数据诚信：标定 JSON 或 meta.json 标记 simulated 时，输出同样标记 simulated；
模拟结果一律不是实验结果，不得写入论文/报告的实测结论。

v0.2（2026-11-19）新增：
    稳态窗口 --steady auto：滑动窗口相对标准差自动识别稳态段（默认 last 取末尾固定窗口）；
    uncertainty 块：一阶相对不确定度传播（1σ 分量，U=2u 约 95%），见 docs/design/processing_pipeline_v0.2.md。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FIELDS = [
    "host_ts",
    "elapsed_s",
    "seq",
    "device_time_ms",
    "thrust_raw",
    "torque_raw",
    "rpm",
    "voltage_v",
    "current_a",
    "motor_temp_c",
    "ambient_temp_c",
    "humidity_pct",
    "pressure_kpa",
]
REQUIRED_CHANNELS = ("thrust_raw", "torque_raw", "rpm", "voltage_v", "current_a")
DEFAULT_AIR_DENSITY = 1.204  # kg/m3，20 ℃、96 kPa 附近的近似值
R_SPECIFIC_AIR = 287.05  # J/(kg·K)
OUTPUT_FIELDS = [
    "host_ts",
    "elapsed_s",
    "seq",
    "thrust_N",
    "torque_Nm",
    "rpm",
    "omega_rad_s",
    "voltage_v",
    "current_a",
    "p_shaft_w",
    "p_elec_w",
    "eta_em",
    "fm",
    "eta_sys",
]
# 一阶不确定度传播假设（1σ 相对标准不确定度）。来源：work/research/bench_tech.md 的 U 预算量级；
# 实机静态标定与传感器校准完成后必须复核这些分量，不得直接作为论文不确定度结论。
UNCERTAINTY_REL_1SIGMA = {
    "thrust": 0.0065,       # 推力（0.65%，bench_tech 主导项）
    "torque": 0.005,        # 反扭矩
    "rpm": 0.001,           # 转速
    "voltage": 0.001,       # 母线电压
    "current": 0.005,       # 母线电流
    "air_density": 0.005,   # 空气密度（温压换算）
}
STEADY_CHANNELS = ("thrust_raw", "rpm")


def load_calibration(path: str | Path) -> dict:
    """读取并校验标定 JSON；返回规范化字典。"""
    calibration_path = Path(path).resolve()
    with calibration_path.open(encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError("标定 JSON 顶层必须为对象")

    result: dict = {
        "path": str(calibration_path),
        "schema_version": str(raw.get("schema_version", "unknown")),
        "simulated": bool(raw.get("simulated", False)),
        "source": str(raw.get("source", "未填写")),
        "rho": None,
        "diameter_m": None,
    }
    for key in ("thrust", "torque"):
        block = raw.get(key)
        if not isinstance(block, dict) or "k" not in block or "b" not in block:
            raise ValueError(f"标定 JSON 缺少 {key}.k / {key}.b")
        try:
            k = float(block["k"])
            b = float(block["b"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key}.k / {key}.b 必须为数值") from exc
        if not (math.isfinite(k) and math.isfinite(b)):
            raise ValueError(f"{key}.k / {key}.b 不得为 NaN 或无穷大")
        if k == 0:
            raise ValueError(f"{key}.k 不得为 0")
        result[key] = {"k": k, "b": b}

    propeller = raw.get("propeller") or {}
    if propeller:
        try:
            diameter = float(propeller.get("diameter_m", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError("propeller.diameter_m 必须为数值") from exc
        if diameter > 0:
            result["diameter_m"] = diameter

    rho = raw.get("air_density_kg_m3")
    if rho is not None:
        try:
            rho = float(rho)
        except (TypeError, ValueError) as exc:
            raise ValueError("air_density_kg_m3 必须为数值") from exc
        if not math.isfinite(rho) or rho <= 0:
            raise ValueError("air_density_kg_m3 必须为正的有限数")
        result["rho"] = rho
    return result


def air_density_from_conditions(temp_c: float, pressure_kpa: float) -> float:
    """由环境温度（℃）与大气压（kPa）估算空气密度（理想气体，干空气）。"""
    if not (math.isfinite(temp_c) and math.isfinite(pressure_kpa)):
        raise ValueError("温度与气压必须为有限数")
    if temp_c <= -273.15:
        raise ValueError("温度必须高于绝对零度")
    if pressure_kpa <= 0:
        raise ValueError("气压必须为正")
    return pressure_kpa * 1000.0 / (R_SPECIFIC_AIR * (temp_c + 273.15))


def _read_metadata(csv_path: Path) -> dict:
    meta_path = csv_path.with_suffix(".meta.json")
    if not meta_path.exists():
        return {}
    try:
        with meta_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _stats(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "mean": None, "std": None, "min": None, "max": None, "relative_std": None}
    mean = statistics.fmean(values)
    std = statistics.stdev(values) if len(values) >= 2 else 0.0
    return {
        "count": len(values),
        "mean": mean,
        "std": std,
        "min": min(values),
        "max": max(values),
        "relative_std": abs(std / mean) if abs(mean) > 1e-12 else None,
    }


def _parse_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != RAW_FIELDS:
            raise ValueError(f"表头不符合 raw schema v0.1：{reader.fieldnames}")
        rows = list(reader)
    if not rows:
        raise ValueError("CSV 没有数据行")

    parsed: list[dict] = []
    for line_number, row in enumerate(rows, start=2):
        values: dict[str, float] = {}
        for name in REQUIRED_CHANNELS:
            text = (row.get(name) or "").strip()
            if not text:
                raise ValueError(f"第 {line_number} 行必需通道 {name} 为空")
            try:
                value = float(text)
            except ValueError as exc:
                raise ValueError(f"第 {line_number} 行 {name} 不是数值") from exc
            if not math.isfinite(value):
                raise ValueError(f"第 {line_number} 行 {name} 不是有限数值")
            values[name] = value

        for name in ("elapsed_s", "ambient_temp_c", "pressure_kpa"):
            text = (row.get(name) or "").strip()
            if text:
                try:
                    candidate = float(text)
                except ValueError:
                    continue
                if math.isfinite(candidate):
                    values[name] = candidate
        parsed.append({"line": line_number, "values": values, "host_ts": (row.get("host_ts") or "").strip()})
    return parsed


def _estimate_sample_rate(rows: list[dict]) -> float:
    """由 elapsed_s 的中位间隔估计采样率；缺失时按 1000 S/s 假定。"""
    times = [r["values"]["elapsed_s"] for r in rows if "elapsed_s" in r["values"]]
    if len(times) >= 3:
        diffs = sorted(b - a for a, b in zip(times, times[1:]) if b > a)
        if diffs:
            median = diffs[len(diffs) // 2]
            if median > 0:
                return 1.0 / median
    return 1000.0


def _window_relative_std(window: list[dict], channels: tuple[str, ...]) -> dict:
    result: dict = {}
    for channel in channels:
        values = [float(r["values"][channel]) for r in window if channel in r["values"]]
        if len(values) < 2:
            result[channel] = None
            continue
        mean = statistics.fmean(values)
        std = statistics.stdev(values)
        result[channel] = (std / abs(mean)) if abs(mean) > 1e-12 else None
    return result


def detect_steady_window(
    rows: list[dict],
    *,
    window_s: float = 0.5,
    threshold: float = 0.01,
    channels: tuple[str, ...] = STEADY_CHANNELS,
) -> dict:
    """滑动窗口相对标准差自动识别最近一段稳态数据。

    从数据末尾向前滑动；取第一个所有通道相对标准差均 <= threshold 的窗口。
    找不到时回退到末尾窗口并在返回值中标注 applied=False。
    """
    if not rows:
        raise ValueError("没有数据行，无法识别稳态窗口")
    if window_s <= 0:
        raise ValueError("steady_window_s 必须大于 0")
    if not (0 < threshold < 1):
        raise ValueError("steady_threshold 必须落在 (0, 1)")

    total = len(rows)
    sample_rate = _estimate_sample_rate(rows)
    window_samples = max(2, min(int(round(window_s * sample_rate)), total))
    step = max(1, min(window_samples // 10, 50))

    best: tuple[int, dict] | None = None
    for start in range(total - window_samples, -1, -step):
        relative = _window_relative_std(rows[start : start + window_samples], channels)
        if all(value is not None and value <= threshold for value in relative.values()):
            best = (start, relative)
            break
    applied = best is not None
    if best is None:
        start = total - window_samples
        best = (start, _window_relative_std(rows[start:], channels))

    start, relative = best
    end = start + window_samples - 1
    times = [r["values"].get("elapsed_s") for r in rows]

    def time_at(index: int) -> float:
        value = times[index] if 0 <= index < len(times) else None
        return float(value) if value is not None else index / sample_rate

    start_s = time_at(start)
    end_s = time_at(end)
    return {
        "method": "sliding_relative_std",
        "applied": applied,
        "threshold": threshold,
        "channels": list(channels),
        "samples": window_samples,
        "start_index": start,
        "end_index": end,
        "start_s": start_s,
        "end_s": end_s,
        "duration_s": end_s - start_s if end_s > start_s else window_samples / sample_rate,
        "sample_rate_hz": sample_rate,
        "relative_std": relative,
        "note": None if applied else "未找到满足阈值的连续窗口，回退到末尾窗口",
    }


def _uncertainty_block() -> dict:
    """按一阶相对传播计算 U(k=2)（假设各通道相对不确定度独立）。"""
    u = UNCERTAINTY_REL_1SIGMA
    u_eta_em = math.sqrt(u["torque"] ** 2 + u["rpm"] ** 2 + u["voltage"] ** 2 + u["current"] ** 2)
    u_fm = math.sqrt(
        (1.5 * u["thrust"]) ** 2 + u["torque"] ** 2 + u["rpm"] ** 2 + (0.5 * u["air_density"]) ** 2
    )
    u_eta_sys = math.sqrt(
        (1.5 * u["thrust"]) ** 2 + (0.5 * u["air_density"]) ** 2 + u["voltage"] ** 2 + u["current"] ** 2
    )
    return {
        "method": "一阶相对不确定度传播（各分量独立；U = 2u，约 95%）",
        "components_1sigma_relative": dict(u),
        "sensitivities": {
            "eta_em": "由 Q、omega、U、I 传播",
            "fm": "由 T（指数 1.5）、rho（指数 0.5）、Q、omega 传播",
            "eta_sys": "由 T（1.5）、rho（0.5）、U、I 直接传播（避免与 FM/η_em 相关性重复计算）",
        },
        "u_rel_eta_em": u_eta_em,
        "u_rel_fm": u_fm,
        "u_rel_eta_sys": u_eta_sys,
        "U_rel_eta_em_k2": 2.0 * u_eta_em,
        "U_rel_fm_k2": 2.0 * u_fm,
        "U_rel_eta_sys_k2": 2.0 * u_eta_sys,
        "reference_targets_k2": {"eta_em": 0.015, "fm": 0.025, "eta_sys": 0.021},
        "note": "分量为假设值（bench_tech 量级），实机静态标定与传感器校准后必须复核",
    }


def assert_measured(calibration: dict, meta: dict, rows: list[dict]) -> None:
    """MEASURED 守门（`--require-measured`，D035/D036）。

    只验证"是否声称实测"的标记与结构，不验证物理真实性；物理真实性仍须
    双人签字与 M0.4 现场记录。
    """
    errors: list[str] = []
    if calibration.get("simulated") is not False:
        errors.append(f"标定 simulated 必须为 false（当前 {calibration.get('simulated')!r}）")
    if meta.get("simulated") is not False:
        errors.append(f"meta simulated 必须为 false（当前 {meta.get('simulated')!r}）")
    if meta.get("mode") != "serial":
        errors.append(f"meta mode 必须为 'serial'（当前 {meta.get('mode')!r}）")
    if not rows:
        errors.append("原始 CSV 没有数据行")
    else:
        for channel in REQUIRED_CHANNELS:
            ok = True
            for row in rows:
                values = row.get("values") or {}
                value = values.get(channel)
                if not isinstance(value, float) or not math.isfinite(value):
                    ok = False
                    break
            if not ok:
                errors.append(f"必需通道 {channel} 缺少有限数值")
    if errors:
        raise ValueError("MEASURED 守门拒绝：" + "；".join(errors))


def compute_efficiency(
    input_csv: str | Path,
    calibration: str | Path,
    window_s: float = 3.0,
    air_density: float | None = None,
    diameter_m: float | None = None,
    output_csv: str | Path | None = None,
    summary_json: str | Path | None = None,
    overwrite: bool = False,
    steady_mode: str = "last",
    steady_window_s: float = 0.5,
    steady_threshold: float = 0.01,
    require_measured: bool = False,
) -> dict:
    """执行换算与效率计算，写输出文件并返回汇总字典。"""
    if window_s <= 0:
        raise ValueError("window_s 必须大于 0")
    csv_path = Path(input_csv).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"原始 CSV 不存在：{csv_path}")

    calib = load_calibration(calibration)
    meta = _read_metadata(csv_path)
    simulated = bool(calib["simulated"] or meta.get("simulated", False))
    if simulated and not meta:
        meta_note = "缺少 meta.json，simulated 依据标定文件"
    elif simulated:
        meta_note = "meta.json 或标定文件标记 simulated"
    else:
        meta_note = "未发现 simulated 标记（仍不代表已通过实机标定验证）"

    prop_diameter = diameter_m or calib["diameter_m"]
    if prop_diameter is None:
        test_block = meta.get("test") or {}
        candidate = test_block.get("prop_diameter_m")
        prop_diameter = float(candidate) if candidate else None
    if not prop_diameter or prop_diameter <= 0:
        raise ValueError("缺少桨径：请在标定 JSON 的 propeller.diameter_m、meta.json 或 --diameter 中提供")
    disk_area = math.pi * prop_diameter**2 / 4.0

    rows = _parse_rows(csv_path)
    if require_measured:
        assert_measured(calib, meta, rows)

    # 空气密度：命令行 > 标定文件 > 实测温压均值 > 默认值
    rho = air_density if air_density is not None else calib["rho"]
    density_source = "命令行 --rho" if air_density is not None else "标定文件" if calib["rho"] else ""
    if rho is None:
        temps = [r["values"]["ambient_temp_c"] for r in rows if "ambient_temp_c" in r["values"]]
        pressures = [r["values"]["pressure_kpa"] for r in rows if "pressure_kpa" in r["values"]]
        if temps and pressures:
            rho = air_density_from_conditions(statistics.fmean(temps), statistics.fmean(pressures))
            density_source = "实测环境温压估算"
        else:
            rho = DEFAULT_AIR_DENSITY
            density_source = "默认值 1.204（未提供环境温压）"
    if not (math.isfinite(rho) and rho > 0):
        raise ValueError("空气密度必须为正的有限数")

    warnings: list[str] = []
    if not meta:
        warnings.append("缺少同名 meta.json：试验条件与 simulated 标记不完整")
    if not simulated:
        warnings.append("数据未标记 simulated：请确认已按静态砝码标定，否则结果不可作为实测结论")

    processed: list[dict] = []
    skipped = 0
    for row in rows:
        v = row["values"]
        thrust = calib["thrust"]["k"] * v["thrust_raw"] + calib["thrust"]["b"]
        torque = calib["torque"]["k"] * v["torque_raw"] + calib["torque"]["b"]
        rpm = v["rpm"]
        voltage = v["voltage_v"]
        current = v["current_a"]
        omega = 2.0 * math.pi * rpm / 60.0
        p_shaft = torque * omega
        p_elec = voltage * current
        p_ideal = thrust**1.5 / math.sqrt(2.0 * rho * disk_area) if thrust > 0 else None

        eta_em = p_shaft / p_elec if p_elec > 1e-9 else None
        fm = p_ideal / p_shaft if (p_ideal is not None and p_shaft > 1e-9) else None
        eta_sys = p_ideal / p_elec if (p_ideal is not None and p_elec > 1e-9) else None
        if eta_em is None or fm is None:
            skipped += 1

        processed.append(
            {
                "host_ts": row["host_ts"],
                "elapsed_s": v.get("elapsed_s", ""),
                "seq": v.get("seq", ""),
                "thrust_N": thrust,
                "torque_Nm": torque,
                "rpm": rpm,
                "omega_rad_s": omega,
                "voltage_v": voltage,
                "current_a": current,
                "p_shaft_w": p_shaft,
                "p_elec_w": p_elec,
                "eta_em": eta_em if eta_em is not None else "",
                "fm": fm if fm is not None else "",
                "eta_sys": eta_sys if eta_sys is not None else "",
            }
        )

    if skipped:
        warnings.append(f"{skipped} 行因电功率/轴功率无效而无法计算效率（已留空）")

    # 稳态窗口：last = 末尾固定窗口；auto = 滑动相对标准差自动识别
    if steady_mode not in ("last", "auto"):
        raise ValueError("steady_mode 只能是 'last' 或 'auto'")
    if steady_window_s <= 0:
        raise ValueError("steady_window_s 必须大于 0")
    if not (0 < steady_threshold < 1):
        raise ValueError("steady_threshold 必须落在 (0, 1)")

    elapsed = [float(r["elapsed_s"]) for r in processed if r["elapsed_s"] != ""]
    detection: dict | None = None
    if steady_mode == "auto":
        detection = detect_steady_window(rows, window_s=steady_window_s, threshold=steady_threshold)
        window = processed[detection["start_index"] : detection["end_index"] + 1]
        window_meta = {
            "mode": "auto",
            "requested_window_s": steady_window_s,
            "start_s": detection["start_s"],
            "end_s": detection["end_s"],
            "window_s": detection["duration_s"],
        }
    else:
        if elapsed:
            cutoff = max(elapsed) - window_s
            window = [r for r in processed if r["elapsed_s"] != "" and float(r["elapsed_s"]) >= cutoff]
            start_s = float(window[0]["elapsed_s"]) if window and window[0]["elapsed_s"] != "" else None
            end_s = float(window[-1]["elapsed_s"]) if window and window[-1]["elapsed_s"] != "" else None
        else:
            count = max(1, int(round(window_s * 1000)))  # 假定 1 kS/s
            window = processed[-count:]
            start_s = end_s = None
        window_meta = {
            "mode": "last",
            "requested_window_s": window_s,
            "start_s": start_s,
            "end_s": end_s,
            "window_s": (end_s - start_s) if (start_s is not None and end_s is not None and end_s > start_s) else window_s,
        }
    if not window:
        raise ValueError("稳态窗口为空，请检查 window_s 与数据时长")
    if detection is not None and not detection["applied"]:
        warnings.append(detection["note"] or "稳态自动识别回退到末尾窗口")

    def collect(key: str) -> list[float]:
        return [float(r[key]) for r in window if r[key] != ""]

    steady = {
        "mode": window_meta["mode"],
        "requested_window_s": window_meta["requested_window_s"],
        "window_s": window_meta["window_s"],
        "start_s": window_meta["start_s"],
        "end_s": window_meta["end_s"],
        "samples": len(window),
        "thrust_N": _stats(collect("thrust_N")),
        "torque_Nm": _stats(collect("torque_Nm")),
        "rpm": _stats(collect("rpm")),
        "voltage_v": _stats(collect("voltage_v")),
        "current_a": _stats(collect("current_a")),
        "p_shaft_w": _stats(collect("p_shaft_w")),
        "p_elec_w": _stats(collect("p_elec_w")),
        "eta_em": _stats(collect("eta_em")),
        "fm": _stats(collect("fm")),
        "eta_sys": _stats(collect("eta_sys")),
    }
    if detection is not None:
        steady["detection"] = detection
    for key in ("eta_em", "fm", "eta_sys"):
        if steady[key]["count"] == 0:
            warnings.append(f"稳态窗口内 {key} 无法计算")

    test_block = meta.get("test") or {}
    summary = {
        "schema_version": "0.2",
        "source_file": str(csv_path),
        "calibration_file": calib["path"],
        "calibration_source": calib["source"],
        "simulated": simulated,
        "data_notice": (
            "模拟数据：仅用于软件联调与流程验证，不是实验结果"
            if simulated
            else "实机数据：效率结论以此为准，但需确认静态标定与试验条件记录完整"
        ),
        "simulated_reason": meta_note,
        "rows": len(processed),
        "window": steady,
        "conditions": {
            "run_id": meta.get("run_id"),
            "mode": meta.get("mode"),
            "combo": test_block.get("combo"),
            "repeat": test_block.get("repeat"),
            "motor": test_block.get("motor"),
            "esc": test_block.get("esc"),
            "prop": test_block.get("prop"),
            "voltage_set_v": test_block.get("voltage_set_v"),
            "throttle_set_pct": test_block.get("throttle_set_pct"),
            "prop_diameter_m": prop_diameter,
            "operator": test_block.get("operator"),
        },
        "assumptions": {
            "air_density_kg_m3": rho,
            "air_density_source": density_source,
            "disk_area_m2": disk_area,
            "eta_definitions": {
                "eta_em": "P_shaft / P_elec（电机+电调）",
                "fm": "P_ideal / P_shaft，P_ideal = T^1.5 / sqrt(2 rho A)（静态悬停动量理论）",
                "eta_sys": "P_ideal / P_elec = FM * eta_em",
            },
        },
        "calibration": {
            "thrust": calib["thrust"],
            "torque": calib["torque"],
        },
        "uncertainty": _uncertainty_block(),
        "warnings": warnings,
        "computed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }

    output_path = Path(output_csv) if output_csv else PROJECT_ROOT / "data" / "processed" / f"{csv_path.stem}_processed.csv"
    summary_path = Path(summary_json) if summary_json else PROJECT_ROOT / "data" / "metadata" / f"{csv_path.stem}_efficiency.json"
    output_path = output_path.resolve()
    summary_path = summary_path.resolve()
    for target in (output_path, summary_path):
        if target.exists() and not overwrite:
            raise FileExistsError(f"输出文件已存在（如需覆盖请加 --overwrite）：{target}")
        target.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for record in processed:
            writer.writerow({key: (f"{record[key]:.6g}" if isinstance(record[key], float) else record[key]) for key in OUTPUT_FIELDS})

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    summary["_outputs"] = {"processed_csv": str(output_path), "summary_json": str(summary_path)}
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="原始 CSV → 物理量 + 效率链（稳态窗口汇总）")
    parser.add_argument("--input", required=True, help="原始 CSV（协议 v0.1）")
    parser.add_argument("--calib", required=True, help="标定 JSON（thrust/torque k、b，桨径等）")
    parser.add_argument("--window", type=float, default=3.0, help="稳态窗口长度，秒")
    parser.add_argument(
        "--steady",
        choices=["last", "auto"],
        default="last",
        help="稳态窗口选择：last=末尾固定窗口；auto=滑动相对标准差自动识别",
    )
    parser.add_argument("--steady-window", type=float, default=0.5, help="auto 模式滑动窗口长度，秒")
    parser.add_argument("--steady-threshold", type=float, default=0.01, help="auto 模式相对标准差阈值（默认 1%%）")
    parser.add_argument("--rho", type=float, help="空气密度 kg/m3；缺省按标定/实测/env/默认值")
    parser.add_argument("--diameter", type=float, help="桨径 m（覆盖标定/元数据）")
    parser.add_argument("--output", help="逐样本输出 CSV 路径")
    parser.add_argument("--summary", help="汇总 JSON 路径")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖输出文件（默认拒绝）")
    parser.add_argument(
        "--require-measured",
        action="store_true",
        help="MEASURED 守门：拒绝 SIM/合成标定或非 serial 输入（D035/D036）",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        summary = compute_efficiency(
            args.input,
            args.calib,
            window_s=args.window,
            air_density=args.rho,
            diameter_m=args.diameter,
            output_csv=args.output,
            summary_json=args.summary,
            overwrite=args.overwrite,
            steady_mode=args.steady,
            steady_window_s=args.steady_window,
            steady_threshold=args.steady_threshold,
            require_measured=args.require_measured,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"处理失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    window = summary["window"]
    window_line = f"样本：{summary['rows']} 行；稳态窗口（{window['mode']}）：{window['samples']} 点 / {window['window_s']:.3f} s"
    if window.get("start_s") is not None:
        window_line += f"（{window['start_s']:.3f}–{window['end_s']:.3f} s）"
    print(window_line)
    detection = window.get("detection")
    if detection is not None:
        relative_text = "、".join(
            f"{name} {value:.3%}" if value is not None else f"{name} n/a"
            for name, value in detection["relative_std"].items()
        )
        print(f"  稳态识别：applied={detection['applied']}；阈值 {detection['threshold']:.1%}；相对标准差 {relative_text}")
    print(f"空气密度：{summary['assumptions']['air_density_kg_m3']:.4f} kg/m3（{summary['assumptions']['air_density_source']}）")
    for label, key, fmt in (
        ("推力", "thrust_N", ".3f"),
        ("反扭矩", "torque_Nm", ".4f"),
        ("转速", "rpm", ".1f"),
        ("轴功率", "p_shaft_w", ".3f"),
        ("电功率", "p_elec_w", ".3f"),
    ):
        mean = window[key]["mean"]
        print(f"  {label}均值：{mean:{fmt}}" if mean is not None else f"  {label}均值：不可用")
    for label, key in (("电机+电调效率 eta_em", "eta_em"), ("螺旋桨品质因数 FM", "fm"), ("系统效率 eta_sys", "eta_sys")):
        mean = window[key]["mean"]
        print(f"  {label}：{mean:.4f}" if mean is not None else f"  {label}：不可用")
    uncertainty = summary["uncertainty"]
    print(
        "  相对不确定度 U(k=2)："
        f"eta_em ±{uncertainty['U_rel_eta_em_k2']:.1%}、"
        f"FM ±{uncertainty['U_rel_fm_k2']:.1%}、"
        f"eta_sys ±{uncertainty['U_rel_eta_sys_k2']:.1%}（一阶传播，待实机标定复核）"
    )
    if summary["simulated"]:
        print("⚠ 模拟数据：不是实验结果，仅用于流程验证")
    for warning in summary["warnings"]:
        print(f"警告：{warning}")
    print(f"逐样本 CSV：{summary['_outputs']['processed_csv']}")
    print(f"汇总 JSON：{summary['_outputs']['summary_json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
