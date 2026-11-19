# -*- coding: utf-8 -*-
"""选型匹配原型 v0.3：GP（高斯过程）连续匹配。

v0.2 的离散网格/线性插值只能命中少数网格点之间；v0.3 在效率地图 runs CSV 上
分别对推力、η_sys（以及 η_em/FM/rpm/电流）拟合 RBF 核 GP，然后：

1. 对每个候选电压，在油门 0–max 上扫描 GP 推力预测，求"刚好满足需求推力"的连续油门；
2. 该油门处用 GP 预测 η_sys 等指标，并给出预测标准差；
3. 保守效率 = η_sys_pred − sqrt((2σ_gp)² + U(k=2)_local²)（GP 置信 + 局部测量不确定度）；
4. 多目标排序（eta_sys / current / balanced）与 Pareto 图沿用 v0.2 逻辑。

边界：当前只有 SIM 数据，结果只验证软件链路，不是真实选型结论；GP 外推区不可信。
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "work" / "pylibs", ROOT / "code" / "processing"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np  # noqa: E402

import gp_surface as gp  # noqa: E402
from match_propulsion import OBJECTIVES, _score_candidates, load_runs, pareto_front  # noqa: E402

# gp_surface 在导入时会设置 matplotlib Agg；图件延迟导入即可
import matplotlib.pyplot as plt  # noqa: E402

GP_OUTPUT_FIELDS = [
    "rank",
    "run_id",
    "source",
    "combo",
    "voltage_set_v",
    "throttle_set_pct",
    "matched_by",
    "thrust_N",
    "thrust_margin_N",
    "eta_sys",
    "gp_std_eta",
    "eta_sys_conservative",
    "u_eta_sys_k2",
    "eta_em",
    "fm",
    "rpm",
    "current_a",
    "score",
    "prop_diameter_m",
    "data_note",
]

DATA_NOTE = "GP 连续匹配（SIM/参考运行数据）：仅供流程演示，不是选型结论"
EXTRA_CHANNELS = (("eta_em", "eta_em"), ("fm", "fm"), ("rpm", "rpm"), ("current_a", "current_a"))


def _as_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fit_models(runs: list[dict], *, length_scales: tuple[float, ...] = gp.LENGTH_SCALES) -> dict:
    """对推力/η_sys（及附加通道）拟合 GP；返回 GP 与 LOOCV 指标。"""
    if len(runs) < gp.MIN_POINTS:
        raise ValueError(f"有效数据点不足（需要 ≥{gp.MIN_POINTS}，实际 {len(runs)}）")
    x = gp.features_of(runs)
    y_thrust = np.asarray([r["thrust_N"] for r in runs], dtype=float)
    y_eta = np.asarray([r["eta_sys"] for r in runs], dtype=float)
    cv_thrust = gp.choose_length_scale(x, y_thrust, length_scales)
    cv_eta = gp.choose_length_scale(x, y_eta, length_scales)
    models: dict = {
        "thrust": gp.GPFit(x, y_thrust, length_scale=cv_thrust["length_scale"]),
        "eta": gp.GPFit(x, y_eta, length_scale=cv_eta["length_scale"]),
        "loocv": {"thrust": cv_thrust, "eta": cv_eta},
        "extra": {},
    }
    for display, key in EXTRA_CHANNELS:
        values = [r.get(key) for r in runs]
        if any(v is None for v in values):
            continue
        models["extra"][display] = gp.GPFit(x, np.asarray(values, dtype=float), length_scale=cv_eta["length_scale"])
    return models


def _feature(voltage: float, throttle: float) -> np.ndarray:
    return np.asarray([[voltage / gp.VOLTAGE_SCALE, throttle / gp.THROTTLE_SCALE]], dtype=float)


def _predict(gpfit: gp.GPFit, voltage: float, throttle: float) -> tuple[float, float]:
    mean, var = gpfit.predict(_feature(voltage, throttle))
    return float(mean[0]), float(var[0])


def _local_u(runs: list[dict], voltage: float, throttle: float) -> float | None:
    """同一电压下离目标油门最近的两个网格点 U(k=2) 取最大值（保守）。"""
    nearby = [
        r
        for r in runs
        if abs(r["voltage_set_v"] - voltage) <= 1e-9 and r.get("u_eta_sys_k2") is not None
    ]
    if not nearby:
        return None
    nearby.sort(key=lambda r: abs(r["throttle_set_pct"] - throttle))
    return max(r["u_eta_sys_k2"] for r in nearby[:2])


def _match_one_voltage(
    models: dict,
    runs: list[dict],
    *,
    voltage: float,
    thrust_required_n: float,
    grid_points: int,
    max_throttle_pct: float,
) -> dict | None:
    """在给定电压上扫描油门，找 GP 推力最接近需求的连续工作点。"""
    throttles = np.linspace(0.0, max_throttle_pct, max(3, int(grid_points)))
    x = np.column_stack([np.full_like(throttles, voltage / gp.VOLTAGE_SCALE), throttles / gp.THROTTLE_SCALE])
    means, _ = models["thrust"].predict(x)
    idx = int(np.argmin(np.abs(means - thrust_required_n)))
    throttle = float(throttles[idx])
    if 0 < idx < len(throttles) - 1:
        left, right = float(throttles[idx - 1]), float(throttles[idx + 1])
        m_left, m_right = float(means[idx - 1]), float(means[idx + 1])
        if abs(m_right - m_left) > 1e-12:
            t = (thrust_required_n - m_left) / (m_right - m_left)
            throttle = float(min(max(left + t * (right - left), 0.0), max_throttle_pct))
    thrust_pred, _ = _predict(models["thrust"], voltage, throttle)
    eta_pred, eta_var = _predict(models["eta"], voltage, throttle)
    extras = {name: _predict(fit, voltage, throttle)[0] for name, fit in models["extra"].items()}
    u_local = _local_u(runs, voltage, throttle)
    sigma = math.sqrt(max(eta_var, 0.0))
    combined = math.hypot(2.0 * sigma, u_local if u_local is not None else 0.0)
    return {
        "run_id": f"gp:combo@{voltage:g}V",
        "source": runs[0].get("source", ""),
        "combo": runs[0].get("combo", ""),
        "voltage_set_v": voltage,
        "throttle_set_pct": throttle,
        "matched_by": "gp",
        "thrust_N": thrust_pred,
        "thrust_margin_N": thrust_pred - thrust_required_n,
        "eta_sys": eta_pred,
        "gp_std_eta": sigma,
        "eta_sys_conservative": eta_pred - combined,
        "u_eta_sys_k2": u_local,
        "eta_em": extras.get("eta_em"),
        "fm": extras.get("fm"),
        "rpm": extras.get("rpm"),
        "current_a": extras.get("current_a"),
        "prop_diameter_m": runs[0].get("prop_diameter_m"),
        "data_note": DATA_NOTE,
    }


def match_gp(
    runs: list[dict],
    *,
    thrust_required_n: float,
    thrust_tolerance: float = 0.1,
    max_throttle_pct: float = 100.0,
    voltages: list[float] | None = None,
    top_n: int = 5,
    source: str = "ANY",
    objective: str = "eta_sys",
    max_u_k2: float | None = None,
    grid_points: int = 101,
) -> list[dict]:
    """GP 连续匹配：每个电压最多一个候选。"""
    if thrust_required_n <= 0:
        raise ValueError("thrust_required_n 必须大于 0")
    if not (0 <= thrust_tolerance < 1):
        raise ValueError("thrust_tolerance 必须落在 [0, 1)")
    if objective not in OBJECTIVES:
        raise ValueError(f"objective 必须是 {OBJECTIVES} 之一")
    if max_u_k2 is not None and max_u_k2 < 0:
        raise ValueError("max_u_k2 必须 >= 0")
    if grid_points < 3:
        raise ValueError("grid_points 必须 >= 3")

    allowed = [
        r
        for r in runs
        if (source == "ANY" or r.get("source") == source)
        and r.get("throttle_set_pct") is not None
        and r["throttle_set_pct"] <= max_throttle_pct
        and (voltages is None or r.get("voltage_set_v") in voltages)
    ]
    if len(allowed) < gp.MIN_POINTS:
        raise ValueError(f"筛选后可用数据点不足（{len(allowed)} < {gp.MIN_POINTS}）")
    models = fit_models(allowed)

    lower = thrust_required_n * (1.0 - thrust_tolerance)
    upper = thrust_required_n * (1.0 + thrust_tolerance)
    unique_voltages = sorted({r["voltage_set_v"] for r in allowed})
    candidates: list[dict] = []
    for voltage in unique_voltages:
        candidate = _match_one_voltage(
            models,
            allowed,
            voltage=voltage,
            thrust_required_n=thrust_required_n,
            grid_points=grid_points,
            max_throttle_pct=max_throttle_pct,
        )
        if candidate is None:
            continue
        if not (lower <= candidate["thrust_N"] <= upper):
            continue
        if candidate["throttle_set_pct"] > max_throttle_pct:
            continue
        if max_u_k2 is not None and candidate.get("u_eta_sys_k2") is not None and candidate["u_eta_sys_k2"] > max_u_k2:
            continue
        candidates.append(candidate)
    if not candidates:
        raise ValueError(
            f"GP 未找到满足推力 {lower:.3f}–{upper:.3f} N、油门 ≤{max_throttle_pct:g}% 的连续工作点；"
            "请放宽公差/油门上限或补充工况点"
        )
    ranked = _score_candidates(candidates, objective)
    for index, entry in enumerate(ranked[:top_n], start=1):
        entry["rank"] = index
    return ranked[:top_n]


def write_report(results: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GP_OUTPUT_FIELDS)
        writer.writeheader()
        for entry in results:
            writer.writerow({field: "" if entry.get(field) is None else entry.get(field) for field in GP_OUTPUT_FIELDS})
    return path


def plot_gp_selection(
    runs: list[dict],
    results: list[dict],
    output_png: Path,
    *,
    thrust_required_n: float,
    thrust_tolerance: float = 0.1,
    max_throttle_pct: float = 100.0,
    title: str = "Selection v0.3 (GP) — Thrust vs η_sys",
    overwrite: bool = False,
) -> Path:
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output_png}（如需覆盖加 --overwrite）")
    output_png.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(figsize=(9.0, 6.0), dpi=120)
    axes.scatter(
        [r["thrust_N"] for r in runs], [r["eta_sys"] for r in runs], s=22, c="#9aa4b2", label="efficiency map points", zorder=2
    )
    front = pareto_front(runs)
    axes.plot(
        [r["thrust_N"] for r in front],
        [r["eta_sys"] for r in front],
        color="#c0392b",
        linewidth=1.2,
        alpha=0.6,
        label="observed Pareto front",
        zorder=3,
    )
    try:
        models = fit_models(runs)
    except ValueError:
        models = None
    if models is not None:
        voltages = sorted({r["voltage_set_v"] for r in runs})
        colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd", "#17becf"]
        for i, voltage in enumerate(voltages):
            throttles = np.linspace(0.0, max_throttle_pct, 80)
            thrust_curve = np.asarray([_predict(models["thrust"], voltage, t)[0] for t in throttles])
            eta_curve = np.asarray([_predict(models["eta"], voltage, t)[0] for t in throttles])
            axes.plot(
                thrust_curve,
                eta_curve,
                color=colors[i % len(colors)],
                linewidth=1.0,
                linestyle="--",
                alpha=0.8,
                label=f"GP curve {voltage:g} V",
                zorder=3,
            )
    marker_colors = ["#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]
    marker_shapes = ["o", "s", "^", "D", "v"]
    for entry in results:
        rank = int(entry["rank"])
        color = marker_colors[(rank - 1) % len(marker_colors)]
        shape = marker_shapes[(rank - 1) % len(marker_shapes)]
        axes.scatter(
            [entry["thrust_N"]],
            [entry["eta_sys"]],
            s=95,
            marker=shape,
            edgecolors="black",
            linewidths=0.8,
            color=color,
            zorder=6,
            label=f"#{rank} {entry['voltage_set_v']:g} V / {entry['throttle_set_pct']:.1f}% (gp)",
        )
    lower = thrust_required_n * (1.0 - thrust_tolerance)
    upper = thrust_required_n * (1.0 + thrust_tolerance)
    axes.axvspan(lower, upper, color="#f1c40f", alpha=0.15, zorder=1)
    axes.axvline(thrust_required_n, color="#b7950b", linestyle="--", linewidth=1.0, zorder=1)
    axes.set_xlabel("Thrust (N)")
    axes.set_ylabel("System efficiency η_sys")
    axes.set_title(title)
    axes.grid(True, linestyle=":", alpha=0.5)
    axes.legend(loc="lower right", fontsize=7)
    if any(r.get("source") == "SIM" for r in runs):
        figure.subplots_adjust(bottom=0.17)
        figure.text(
            0.5,
            0.025,
            "SIMULATED DATA — NOT EXPERIMENTAL (GP prototype only)",
            ha="center",
            fontsize=10,
            color="#c0392b",
            fontweight="bold",
        )
    else:
        figure.tight_layout()
    figure.savefig(output_png, dpi=120, bbox_inches="tight")
    plt.close(figure)
    return output_png


def _fmt(value) -> str:
    return "—" if value is None else (f"{value:.4f}" if isinstance(value, float) else str(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GP 连续匹配：需求推力 → 连续油门候选 + 保守效率（原型）")
    parser.add_argument("--input", type=Path, default=Path("data/processed/efficiency_map_runs.csv"))
    parser.add_argument("--thrust", type=float, required=True, help="需求推力，N")
    parser.add_argument("--tolerance", type=float, default=0.1, help="推力公差（相对值，默认 ±10%%）")
    parser.add_argument("--max-throttle", type=float, default=100.0)
    parser.add_argument("--voltages", type=str, default="", help="限定电压，逗号分隔")
    parser.add_argument("--source", choices=["ANY", "SIM", "MEASURED"], default="ANY")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--objective", choices=list(OBJECTIVES), default="eta_sys")
    parser.add_argument("--max-u", type=float, default=None)
    parser.add_argument("--grid-points", type=int, default=101, help="油门扫描点数")
    parser.add_argument("--output", type=Path, default=Path("data/processed/selection_v0.3_gp.csv"))
    parser.add_argument("--figure", type=Path, default=Path("data/processed/figures/selection_v0.3.png"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        runs = load_runs(args.input)
        voltages = [float(item) for item in args.voltages.split(",") if item.strip()] or None
        results = match_gp(
            runs,
            thrust_required_n=args.thrust,
            thrust_tolerance=args.tolerance,
            max_throttle_pct=args.max_throttle,
            voltages=voltages,
            top_n=args.top,
            source=args.source,
            objective=args.objective,
            max_u_k2=args.max_u,
            grid_points=args.grid_points,
        )
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}")
        return 2

    if any(entry.get("source") == "SIM" for entry in results):
        print("⚠ GP 匹配结果来自 SIM 模拟效率地图：仅原型演示，不是选型结论")
    if args.output.exists() and not args.overwrite:
        print(f"错误：输出文件已存在：{args.output}（如需覆盖加 --overwrite）")
        return 2
    write_report(results, args.output)
    try:
        figure_path = plot_gp_selection(
            runs,
            results,
            args.figure,
            thrust_required_n=args.thrust,
            thrust_tolerance=args.tolerance,
            max_throttle_pct=args.max_throttle,
            overwrite=args.overwrite,
        )
    except FileExistsError as exc:
        print(f"错误：{exc}")
        return 2

    print(f"需求推力：{args.thrust:g} N ±{args.tolerance:.0%}；目标 {args.objective}；GP 候选 {len(results)} 个")
    for entry in results:
        print(
            f"  #{entry['rank']} {entry['source']} {entry['combo']} "
            f"{entry['voltage_set_v']:g} V / {entry['throttle_set_pct']:.2f}% [gp]："
            f"推力 {entry['thrust_N']:.3f} N（偏差 {entry['thrust_margin_N']:+.3f} N）、"
            f"η_sys {entry['eta_sys']:.4f}±{entry['gp_std_eta']:.4f}（1σ，保守 {_fmt(entry['eta_sys_conservative'])}）、"
            f"I {_fmt(entry['current_a'])} A、U(k=2) {_fmt(entry['u_eta_sys_k2'])}、score {entry['score']:.3f}"
        )
    print(f"报告：{args.output}")
    print(f"图件：{figure_path}")
    print("注意：GP 为数据平滑代理（外推区不可信），不是实验结果。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
