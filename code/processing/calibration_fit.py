"""静态砝码标定拟合（v0.1）：读数 CSV → 可直接被 compute_efficiency 使用的标定 JSON。

输入为长表 CSV（列名不区分顺序，必需列）：

    channel,direction,repeat,applied,raw
    thrust,load,1,0,12
    thrust,load,1,9.79,28000
    ...
    torque,unload,3,0.98,16000

- `channel`：`thrust`（N）或 `torque`（N·m）
- `direction`：`load`（加载）或 `unload`（卸载）
- `repeat`：重复序号（>=1）
- `applied`：砝码/力臂施加的物理量（N 或 N·m，含 g=9.79 m/s² 的换算结果）
- `raw`：采集通道读数（ADC counts 或传感器原始值）

拟合模型：`applied = k * raw + b`（最小二乘）。输出 JSON 与
`compute_efficiency.load_calibration` 兼容（含 thrust / torque / propeller.diameter_m /
simulated=false / source / schema_version / metrics）。

数据诚信：本工具**只用于真实静态标定读数**；不得用仿真数据生成 simulated=false 的标定。
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_VERSION = "0.1"
REQUIRED_COLUMNS = ("channel", "direction", "repeat", "applied", "raw")
CHANNELS = {"thrust": "N", "torque": "N·m"}
DIRECTIONS = ("load", "unload")

R2_MIN = 0.9995
REPEATABILITY_MAX_PCT_FS = 0.5
HYSTERESIS_MAX_PCT_FS = 0.5


def _now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def load_readings(path: str | Path) -> list[dict]:
    """读取标定读数 CSV（跳过空行与 # 注释），返回规范化行列表。"""
    csv_path = Path(path)
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        lines = handle.readlines()
    # 跳过文件头部的空行/注释行，再交给 DictReader 解析表头。
    start = 0
    while start < len(lines) and (
        not lines[start].strip() or lines[start].lstrip().startswith("#")
    ):
        start += 1
    if start >= len(lines):
        raise ValueError("CSV 为空")
    reader = csv.DictReader(lines[start:])
    if reader.fieldnames is None:
        raise ValueError("CSV 缺少表头")
    headers = [h.strip() for h in reader.fieldnames]
    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        raise ValueError(f"CSV 缺少必需列：{missing}")
    rows: list[dict] = []
    for line_no, raw_row in enumerate(reader, start=start + 2):
        if raw_row is None or not any((v or "").strip() for v in raw_row.values()):
            continue
        first_cell = (raw_row.get(reader.fieldnames[0]) or "").strip()
        if first_cell.startswith("#"):
            continue
        channel = (raw_row["channel"] or "").strip().lower()
        direction = (raw_row["direction"] or "").strip().lower()
        if channel not in CHANNELS:
            raise ValueError(f"第 {line_no} 行 channel 非法：{channel!r}（应为 thrust/torque）")
        if direction not in DIRECTIONS:
            raise ValueError(f"第 {line_no} 行 direction 非法：{direction!r}（应为 load/unload）")
        try:
            repeat = int((raw_row["repeat"] or "").strip())
            applied = float((raw_row["applied"] or "").strip())
            raw_value = float((raw_row["raw"] or "").strip())
        except (TypeError, ValueError) as exc:
            raise ValueError(f"第 {line_no} 行 repeat/applied/raw 必须为数值") from exc
        if repeat < 1:
            raise ValueError(f"第 {line_no} 行 repeat 必须 >= 1")
        if not (math.isfinite(applied) and math.isfinite(raw_value)):
            raise ValueError(f"第 {line_no} 行 applied/raw 不得为 NaN 或无穷大")
        if applied < 0:
            raise ValueError(f"第 {line_no} 行 applied 不得为负")
        rows.append(
            {
                "channel": channel,
                "direction": direction,
                "repeat": repeat,
                "applied": applied,
                "raw": raw_value,
                "line_no": line_no,
            }
        )
    if not rows:
        raise ValueError("CSV 中没有有效数据行")
    return rows


def _fit_line(xs: list[float], ys: list[float]) -> tuple[float, float]:
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    if sxx == 0:
        raise ValueError("raw 读数全部相同，无法拟合（请检查传感器/采集链路）")
    k = sxy / sxx
    b = mean_y - k * mean_x
    return k, b


def fit_channel(readings: list[dict], channel: str) -> dict:
    """对单通道做最小二乘拟合并给出质量指标。"""
    if channel not in CHANNELS:
        raise ValueError(f"未知通道：{channel}")
    rows = [r for r in readings if r["channel"] == channel]
    if len(rows) < 3:
        raise ValueError(f"{channel} 通道有效点数不足（{len(rows)} < 3）")
    xs = [r["raw"] for r in rows]
    ys = [r["applied"] for r in rows]
    k, b = _fit_line(xs, ys)

    residuals = [y - (k * x + b) for x, y in zip(xs, ys)]
    ss_res = sum(e * e for e in residuals)
    mean_y = sum(ys) / len(ys)
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    rmse = math.sqrt(ss_res / len(ys))
    max_abs_error = max(abs(e) for e in residuals)

    levels = sorted({r["applied"] for r in rows})
    fs = levels[-1] - levels[0]
    if fs <= 0:
        raise ValueError(f"{channel} 的 applied 量程为 0，无法计算相对指标")

    # 重复性：同一 applied 水平、不同 repeat 读数换算出力值后的标准差 / FS。
    repeatability = None
    for level in levels:
        values = [k * r["raw"] + b for r in rows if r["applied"] == level]
        if len(values) >= 2:
            mean = sum(values) / len(values)
            std = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
            pct = std / fs * 100.0
            repeatability = pct if repeatability is None else max(repeatability, pct)

    # 迟滞：同一 applied 水平下 加载均值 与 卸载均值 之差 / FS。
    hysteresis = None
    for level in levels:
        loads = [k * r["raw"] + b for r in rows if r["applied"] == level and r["direction"] == "load"]
        unloads = [k * r["raw"] + b for r in rows if r["applied"] == level and r["direction"] == "unload"]
        if loads and unloads:
            delta = abs(sum(loads) / len(loads) - sum(unloads) / len(unloads)) / fs * 100.0
            hysteresis = delta if hysteresis is None else max(hysteresis, delta)

    return {
        "k": k,
        "b": b,
        "unit": f"{CHANNELS[channel]}/count",
        "metrics": {
            "n": len(rows),
            "levels": len(levels),
            "full_scale": fs,
            "r2": r2,
            "rmse": rmse,
            "max_abs_error": max_abs_error,
            "repeatability_pct_fs": repeatability,
            "hysteresis_pct_fs": hysteresis,
        },
    }


def fit_calibration(readings: list[dict], *, diameter_m: float, source: str) -> dict:
    """对 thrust 与 torque 两个通道拟合，返回 compute_efficiency 兼容的标定 JSON。"""
    if not (math.isfinite(diameter_m) and diameter_m > 0):
        raise ValueError("桨径 diameter_m 必须为正的有限数")
    thrust = fit_channel(readings, "thrust")
    torque = fit_channel(readings, "torque")

    warnings: list[str] = []
    for name, block in (("thrust", thrust), ("torque", torque)):
        m = block["metrics"]
        if m["r2"] < R2_MIN:
            warnings.append(f"{name} 拟合 R²={m['r2']:.6f} < {R2_MIN}（检查加载点/读数）")
        if m["repeatability_pct_fs"] is not None and m["repeatability_pct_fs"] > REPEATABILITY_MAX_PCT_FS:
            warnings.append(
                f"{name} 重复性 {m['repeatability_pct_fs']:.3f}%FS > {REPEATABILITY_MAX_PCT_FS}%FS"
            )
        if m["hysteresis_pct_fs"] is not None and m["hysteresis_pct_fs"] > HYSTERESIS_MAX_PCT_FS:
            warnings.append(
                f"{name} 迟滞 {m['hysteresis_pct_fs']:.3f}%FS > {HYSTERESIS_MAX_PCT_FS}%FS"
            )
        if m["hysteresis_pct_fs"] is None:
            warnings.append(f"{name} 缺少加载/卸载成对数据，迟滞未评估")

    return {
        "schema_version": SCHEMA_VERSION,
        "simulated": False,
        "source": source,
        "created_at": _now_iso(),
        "thrust": thrust,
        "torque": torque,
        "propeller": {"diameter_m": diameter_m},
        "thresholds": {
            "r2_min": R2_MIN,
            "repeatability_max_pct_fs": REPEATABILITY_MAX_PCT_FS,
            "hysteresis_max_pct_fs": HYSTERESIS_MAX_PCT_FS,
        },
        "warnings": warnings,
    }


def write_calibration(calibration: dict, output: str | Path, *, overwrite: bool = False) -> Path:
    output_path = Path(output)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"输出已存在（如需覆盖请显式 --overwrite）：{output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(calibration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="静态砝码标定拟合：读数 CSV → 标定 JSON（compute_efficiency 兼容）"
    )
    parser.add_argument("--input", required=True, help="标定读数 CSV")
    parser.add_argument("--output", required=True, help="输出标定 JSON 路径")
    parser.add_argument("--diameter", type=float, required=True, help="螺旋桨直径（m）")
    parser.add_argument("--source", default="静态砝码标定（双人、加载/卸载）", help="标定来源说明")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已有输出")
    args = parser.parse_args(argv)

    try:
        readings = load_readings(args.input)
        calibration = fit_calibration(readings, diameter_m=args.diameter, source=args.source)
        output_path = write_calibration(calibration, args.output, overwrite=args.overwrite)
    except (OSError, ValueError, FileExistsError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    print(f"标定读数：{len(readings)} 行 → {output_path}")
    for name in ("thrust", "torque"):
        block = calibration[name]
        m = block["metrics"]
        rep = "—" if m["repeatability_pct_fs"] is None else f"{m['repeatability_pct_fs']:.3f}%FS"
        hys = "—" if m["hysteresis_pct_fs"] is None else f"{m['hysteresis_pct_fs']:.3f}%FS"
        print(
            f"  {name}: k={block['k']:.6g} b={block['b']:.6g} {block['unit']}；"
            f"R²={m['r2']:.6f} RMSE={m['rmse']:.4g} 重复性={rep} 迟滞={hys}（n={m['n']}）"
        )
    for warning in calibration["warnings"]:
        print(f"  ⚠ {warning}")
    print("提示：输出标定仅反映本次静态标定读数；实机动态测试前须复核安装与线缆约束。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
