# -*- coding: utf-8 -*-
"""把 aggregate_efficiency.py 生成的 runs CSV 画成效率地图（散点或热力图）。

用法：
    py -3.12 code\\processing\\plot_efficiency_map.py --input data\\processed\\efficiency_map_runs.csv
    py -3.12 code\\processing\\plot_efficiency_map.py --input data\\processed\\efficiency_map_runs.csv --uncertainty --output data\\processed\\figures\\efficiency_map_v0.3.png

输出默认：data\\processed\\figures\\efficiency_map_v0.1.png（v0.3 图件请显式给 --output）
SIM 数据会在图上强制标注「SIMULATED DATA — NOT EXPERIMENTAL」。

v0.3（2026-11-19）新增：show_uncertainty / --uncertainty。开启后按 field 读取 runs CSV 的
u_eta_em_k2 / u_fm_k2 / u_eta_sys_k2（扩展不确定度 U(k=2)，分数形式）：
  * 散点模式：ax.errorbar 叠加 yerr=value*U（capsize=3），标注改为「value ± value*U」；
  * 热力图模式：每个格内中央标注两行「value / ±value*U」（fontsize 7，颜色按背景亮度）；
  * 某点 U 缺失/非有限：仅跳过该点误差并打印 warning 到 stderr，仍正常出图。
U 是先验估计（一阶传播，不是实测），不参与颜色映射；详见 docs/design/efficiency_map_v0.3.md。
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

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

for _font in ("Microsoft YaHei", "SimHei", "DejaVu Sans"):
    try:
        font_manager.findfont(_font, fallback_to_default=False)
        plt.rcParams["font.sans-serif"] = [_font]
        break
    except Exception:  # noqa: BLE001
        continue
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150

FIELDS = ("eta_em", "fm", "eta_sys")
FIELD_LABELS = {"eta_em": "Motor+ESC efficiency η_em", "fm": "Propeller figure of merit FM", "eta_sys": "System efficiency η_sys"}
# field → runs CSV 中对应的扩展不确定度 U(k=2) 列（分数形式，如 0.0225666 = ±2.26%）
U_FIELDS = {"eta_em": "u_eta_em_k2", "fm": "u_fm_k2", "eta_sys": "u_eta_sys_k2"}


def _num(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return math.nan
    return number if math.isfinite(number) else math.nan


def read_runs(path: Path) -> list[dict]:
    if not path.is_file():
        raise FileNotFoundError(f"runs CSV 不存在：{path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"runs CSV 为空：{path}")
    return rows


def _value_label(value: float, uncertainty: float) -> str:
    """散点标注：有 U 时写「value ± value*U」，否则只写 value。"""
    if math.isfinite(uncertainty):
        return f"{value:.3f} ± {abs(value * uncertainty):.3f}"
    return f"{value:.3f}"


def _cell_label(value: float, uncertainty: float) -> str:
    """热力图格内两行标注：第一行 value，第二行 ±value*U；无 U 时只写 value。"""
    if math.isfinite(uncertainty):
        return f"{value:.3f}\n±{abs(value * uncertainty):.3f}"
    return f"{value:.3f}"


def _contrast_color(rgba, threshold: float = 0.5) -> str:
    """按背景色亮度选黑/白文字，保证格内标注可读。"""
    luminance = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
    return "black" if luminance > threshold else "white"


def plot_map(
    runs_csv: Path,
    output_png: Path,
    field: str = "eta_sys",
    overwrite: bool = False,
    show_uncertainty: bool = False,
) -> Path:
    if field not in FIELDS:
        raise ValueError(f"field 必须是 {FIELDS} 之一")
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"输出已存在（用 --overwrite 覆盖）：{output_png}")

    rows = read_runs(runs_csv)
    u_field = U_FIELDS[field]
    points: list[tuple[float, float, float, float]] = []
    for row in rows:
        value = _num(row.get(f"{field}_mean"))
        voltage = _num(row.get("voltage_set_v"))
        throttle = _num(row.get("throttle_set_pct"))
        if not (math.isfinite(value) and math.isfinite(voltage) and math.isfinite(throttle)):
            continue
        uncertainty = math.nan
        if show_uncertainty:
            uncertainty = _num(row.get(u_field))
            if not math.isfinite(uncertainty):
                run_id = row.get("run_id") or "?"
                raw = row.get(u_field)
                print(
                    f"warning: {run_id} 的 {u_field} 缺失或非有限（{raw!r}），跳过该点误差，仍绘制该点",
                    file=sys.stderr,
                )
        points.append((voltage, throttle, value, uncertainty))
    if not points:
        raise ValueError("没有可画的数据点（需要 voltage_set_v / throttle_set_pct / 指标均值）")

    sources = sorted({row.get("source", "") for row in rows if row.get("source")})
    simulated = "SIM" in sources
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    values = [point[2] for point in points]

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    unique_x = sorted(set(xs))
    unique_y = sorted(set(ys))
    use_heatmap = len(points) >= 4 and len(unique_x) >= 2 and len(unique_y) >= 2
    if use_heatmap:
        lookup = {(x, y): value for x, y, value, _ in points}
        u_lookup = {(x, y): uncertainty for x, y, _, uncertainty in points}
        matrix = [[lookup.get((x, y), math.nan) for x in unique_x] for y in unique_y]
        image = ax.pcolormesh(unique_x, unique_y, matrix, shading="nearest", cmap="viridis")
        colorbar = fig.colorbar(image, ax=ax)
        colorbar.set_label(FIELD_LABELS[field])
        ax.set_xticks(unique_x)
        ax.set_yticks(unique_y)
        if show_uncertainty:
            for y in unique_y:
                for x in unique_x:
                    value = lookup.get((x, y), math.nan)
                    if not math.isfinite(value):
                        continue
                    label = _cell_label(value, u_lookup.get((x, y), math.nan))
                    color = _contrast_color(image.cmap(image.norm(value)))
                    ax.annotate(label, (x, y), ha="center", va="center", fontsize=7, color=color, zorder=4)
    else:
        scatter = ax.scatter(xs, ys, c=values, cmap="viridis", s=160, edgecolors="black", zorder=3)
        colorbar = fig.colorbar(scatter, ax=ax)
        colorbar.set_label(FIELD_LABELS[field])
        if show_uncertainty:
            bars = [(x, y, abs(value * uncertainty)) for x, y, value, uncertainty in points if math.isfinite(uncertainty)]
            if bars:
                ax.errorbar(
                    [item[0] for item in bars],
                    [item[1] for item in bars],
                    yerr=[item[2] for item in bars],
                    fmt="none",
                    ecolor="black",
                    elinewidth=1.0,
                    capsize=3,
                    capthick=1.0,
                    zorder=2,
                )
        for x, y, value, uncertainty in points:
            ax.annotate(_value_label(value, uncertainty), (x, y), textcoords="offset points", xytext=(6, 6), fontsize=8)

    ax.set_xlabel("Bus voltage (V)")
    ax.set_ylabel("Throttle command (%)")
    title = f"Efficiency map v0.1 — {FIELD_LABELS[field]}"
    if show_uncertainty:
        title += " with U(k=2)"
    ax.set_title(title)
    ax.grid(True, linestyle=":", alpha=0.5)
    note = "sources: " + ", ".join(sources)
    if simulated:
        note += "   |   SIMULATED DATA — NOT EXPERIMENTAL"
        ax.text(
            0.5,
            -0.16,
            "SIMULATED DATA — NOT EXPERIMENTAL",
            transform=ax.transAxes,
            ha="center",
            va="top",
            color="crimson",
            fontsize=9,
            fontweight="bold",
        )
    else:
        ax.text(0.5, -0.14, note, transform=ax.transAxes, ha="center", va="top", fontsize=8, color="dimgray")
    fig.tight_layout()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png)
    plt.close(fig)
    return output_png


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="绘制效率地图（SIM 数据强制标注；v0.3 可叠加 U(k=2)）")
    parser.add_argument("--input", default="data/processed/efficiency_map_runs.csv", help="runs CSV")
    parser.add_argument("--output", default="data/processed/figures/efficiency_map_v0.1.png", help="输出 PNG")
    parser.add_argument("--field", default="eta_sys", choices=FIELDS, help="绘制指标")
    parser.add_argument("--uncertainty", action="store_true", help="叠加 U(k=2) 误差棒/格内 ± 标注")
    parser.add_argument("--overwrite", action="store_true", help="允许覆盖已有输出")
    args = parser.parse_args(argv)
    try:
        output = plot_map(Path(args.input), Path(args.output), args.field, args.overwrite, args.uncertainty)
    except (FileNotFoundError, ValueError, FileExistsError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    print(f"图件：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
