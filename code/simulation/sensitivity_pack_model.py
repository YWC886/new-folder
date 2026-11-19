# -*- coding: utf-8 -*-
r"""仿真模型 v0.2 敏感性分析：电池内阻压降 + 电机温升对效率地图的影响。

对比对象（同一物理模型、同一参数）：
- 理想母线（v0.1）：把名义电压当作恒定母线电压；
- 实际电池包（v0.2）：V_bus = V_oc − I_batt·R_pack，且电机温升通过
  R_hot = R_20·(1 + α·(T − 20)) 反馈到电机电阻。

输出（全部 SIM，不是实验结果）：
- CSV：data/processed/pack_model_sensitivity_v0.2.csv
- PNG：data/processed/figures/pack_model_impact_v0.2.png

用法：
    py -3.12 code\simulation\sensitivity_pack_model.py
    py -3.12 code\simulation\sensitivity_pack_model.py --overwrite
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_PYLIBS = ROOT / "work" / "pylibs"
if _PYLIBS.is_dir():
    sys.path.insert(0, str(_PYLIBS))
_SIM = ROOT / "code" / "simulation"
if str(_SIM) not in sys.path:
    sys.path.insert(0, str(_SIM))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from propulsion_model import ModelParams, PackModel, solve_operating_point  # noqa: E402

for _font in ("Microsoft YaHei", "SimHei", "DejaVu Sans"):
    from matplotlib import font_manager

    try:
        font_manager.findfont(_font, fallback_to_default=False)
        plt.rcParams["font.sans-serif"] = [_font]
        break
    except Exception:  # noqa: BLE001
        continue
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150

VOLTAGES = (11.1, 14.8, 22.2, 29.6)
THROTTLES = (25.0, 50.0, 75.0, 100.0)
CELL_NOMINAL_V = 3.7
DATA_NOTICE = "SIM 仿真敏感性分析：不是实验结果"

FIELDS = [
    "voltage_set_v",
    "cells",
    "throttle_pct",
    "rpm_ideal",
    "rpm_pack",
    "thrust_ideal_n",
    "thrust_pack_n",
    "p_elec_ideal_w",
    "p_elec_pack_w",
    "eta_sys_ideal",
    "eta_sys_pack",
    "delta_eta_sys",
    "delta_eta_sys_pct",
    "bus_voltage_v",
    "voltage_sag_v",
    "sag_pct_of_oc",
    "battery_current_a",
    "motor_temp_c",
    "winding_resistance_ohm",
    "p_loss_w",
    "p_shaft_w",
    "data_notice",
]


def cells_for_voltage(voltage_v: float) -> int:
    """按单节 3.7 V 名义电压推断串联节数（11.1=3S、14.8=4S、22.2=6S、29.6=8S）。"""
    if voltage_v <= 0:
        raise ValueError("voltage_v 必须 > 0")
    cells = int(round(voltage_v / CELL_NOMINAL_V))
    if cells < 1:
        raise ValueError("推断出的电池节数 < 1")
    return cells


def build_rows(params: ModelParams | None = None) -> list[dict]:
    model = params or ModelParams()
    rows: list[dict] = []
    for voltage in VOLTAGES:
        cells = cells_for_voltage(voltage)
        pack = PackModel(cells=cells)
        for throttle_pct in THROTTLES:
            throttle = throttle_pct / 100.0
            ideal = solve_operating_point(model, voltage, throttle)
            packed = solve_operating_point(model, voltage, throttle, pack=pack)
            delta = packed["eta_sys"] - ideal["eta_sys"]
            rows.append(
                {
                    "voltage_set_v": voltage,
                    "cells": cells,
                    "throttle_pct": throttle_pct,
                    "rpm_ideal": ideal["rpm"],
                    "rpm_pack": packed["rpm"],
                    "thrust_ideal_n": ideal["thrust_n"],
                    "thrust_pack_n": packed["thrust_n"],
                    "p_elec_ideal_w": ideal["p_elec_w"],
                    "p_elec_pack_w": packed["p_elec_w"],
                    "eta_sys_ideal": ideal["eta_sys"],
                    "eta_sys_pack": packed["eta_sys"],
                    "delta_eta_sys": delta,
                    "delta_eta_sys_pct": delta / ideal["eta_sys"] * 100.0 if ideal["eta_sys"] > 0 else math.nan,
                    "bus_voltage_v": packed["bus_voltage_v"],
                    "voltage_sag_v": packed["voltage_sag_v"],
                    "sag_pct_of_oc": packed["voltage_sag_v"] / voltage * 100.0,
                    "battery_current_a": packed["battery_current_a"],
                    "motor_temp_c": packed["motor_temp_c"],
                    "winding_resistance_ohm": packed["winding_resistance_ohm"],
                    "p_loss_w": packed["p_loss_w"],
                    "p_shaft_w": packed["p_shaft_w"],
                    "data_notice": DATA_NOTICE,
                }
            )
    return rows


def write_csv(rows: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (f"{value:.10g}" if isinstance(value, float) and math.isfinite(value) else value)
                    for key, value in row.items()
                }
            )
    return path


def plot_impact(rows: list[dict], output_png: Path, overwrite: bool = False) -> Path:
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"输出已存在（用 --overwrite 覆盖）：{output_png}")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6))
    colors = ("#1f77b4", "#2ca02c", "#ff7f0e", "#d62728")
    for color, voltage in zip(colors, VOLTAGES):
        series = sorted((row for row in rows if row["voltage_set_v"] == voltage), key=lambda r: r["throttle_pct"])
        throttles = [row["throttle_pct"] for row in series]
        eta_ideal = [row["eta_sys_ideal"] for row in series]
        eta_pack = [row["eta_sys_pack"] for row in series]
        delta_pp = [row["delta_eta_sys"] * 100.0 for row in series]
        ax1.plot(throttles, eta_ideal, color=color, linestyle="--", marker="o", markersize=4, label=f"{voltage:g} V ideal")
        ax1.plot(throttles, eta_pack, color=color, linestyle="-", marker="s", markersize=4, label=f"{voltage:g} V pack")
        ax2.plot(throttles, delta_pp, color=color, linestyle="-", marker="o", markersize=4, label=f"{voltage:g} V")
    ax1.set_xlabel("Throttle command (%)")
    ax1.set_ylabel("System efficiency η_sys")
    ax1.set_title("η_sys: ideal bus vs battery pack (SIM)")
    ax1.grid(True, linestyle=":", alpha=0.5)
    ax1.legend(fontsize=6.5, ncol=2)
    ax2.set_xlabel("Throttle command (%)")
    ax2.set_ylabel("Δη_sys (percentage points)")
    ax2.set_title("Efficiency loss due to pack sag + heating (SIM)")
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.axhline(0.0, color="gray", linewidth=0.8)
    ax2.legend(fontsize=7)
    for ax in (ax1, ax2):
        ax.text(
            0.5,
            -0.24,
            "SIMULATED DATA — NOT EXPERIMENTAL",
            transform=ax.transAxes,
            ha="center",
            va="top",
            color="crimson",
            fontsize=9,
            fontweight="bold",
        )
    fig.tight_layout()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png)
    plt.close(fig)
    return output_png


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="v0.2 电池内阻+温升敏感性分析（SIM，非实验）")
    parser.add_argument("--output", default="data/processed/pack_model_sensitivity_v0.2.csv", help="输出 CSV")
    parser.add_argument("--figure", default="data/processed/figures/pack_model_impact_v0.2.png", help="输出 PNG")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已有输出")
    args = parser.parse_args(argv)

    output = Path(args.output)
    figure = Path(args.figure)
    if output.exists() and not args.overwrite:
        print(f"错误：输出已存在（用 --overwrite 覆盖）：{output}", file=sys.stderr)
        return 2
    if figure.exists() and not args.overwrite:
        print(f"错误：输出已存在（用 --overwrite 覆盖）：{figure}", file=sys.stderr)
        return 2

    rows = build_rows()
    write_csv(rows, output)
    plot_impact(rows, figure, overwrite=args.overwrite)
    print("⚠ 仿真敏感性分析：合成数据，不是实验结果")
    print(f"CSV：{output}")
    print(f"图件：{figure}")
    worst = min(rows, key=lambda row: row["delta_eta_sys"])
    hottest = max(rows, key=lambda row: row["motor_temp_c"])
    print(
        f"η_sys 最大相对降幅：{min(row['delta_eta_sys_pct'] for row in rows):.2f}%"
        f"（{worst['voltage_set_v']:g} V / {worst['throttle_pct']:g}%）"
    )
    print(
        f"最高电机温度：{hottest['motor_temp_c']:.1f} °C"
        f"（{hottest['voltage_set_v']:g} V / {hottest['throttle_pct']:g}%）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
