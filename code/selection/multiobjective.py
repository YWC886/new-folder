# -*- coding: utf-8 -*-
"""选型匹配 v0.4：GP 多目标 Pareto + 补测点推荐。

在 GP 平滑代理（`code/processing/gp_surface.py`，D026）上构建：

1. **多目标 Pareto**：在电压 × 油门网格上评估候选工作点，约束为
   |GP 推力 − 需求| ≤ 需求×公差；目标为
   - 最大化 η_sys（点估计）；
   - 最小化电池侧电流；
   - 最大化 η_sys_conservative（已扣 σ_gp 与 U(k=2)）。

   输出非支配前沿（Pareto front）、knee 点与全部可行候选，用于展示
   "效率—电流—稳健性" 的权衡，而不是单一排序。

2. **补测点推荐**：在同样的连续网格上取 GP 预测标准差 σ_gp 最大、且与已有测点/
   已选点保持最小归一化距离的工况，作为下一步台架补测候选。

> 全部输出为 **SIM/GP 原型**：不是选型结论，也不是实验结果；SIM 命中强制标注。
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

for _p in (ROOT / "code" / "processing", HERE, ROOT / "code" / "selection"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import gp_surface as gp  # noqa: E402  （内部把 work/pylibs 加入 sys.path）
import gp_match as gm  # noqa: E402
import match_propulsion as mp  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

PARETO_FIELDS = [
    "rank",
    "voltage_set_v",
    "throttle_set_pct",
    "thrust_N",
    "thrust_margin_N",
    "eta_sys",
    "eta_sys_conservative",
    "current_a",
    "gp_std_eta",
    "u_eta_sys_k2",
    "is_knee",
    "data_note",
]
SUGGEST_FIELDS = [
    "rank",
    "voltage_set_v",
    "throttle_set_pct",
    "gp_std_eta",
    "u_eta_sys_k2",
    "min_distance",
    "in_observed_box",
    "data_note",
]
DATA_NOTE_PARETO = "GP 多目标 Pareto（SIM/参考运行数据）：仅供流程演示，不是选型结论"
DATA_NOTE_SUGGEST = "GP 补测点推荐（SIM/参考运行数据）：仅用于规划下一轮台架补测，不是实验结果"


def _u_local(runs: list[dict], voltage: float, throttle: float) -> float | None:
    """取电压/油门最接近的两个已测点的 U(k=2) 最大值（保守）。"""
    candidates = [r for r in runs if r.get("u_eta_sys_k2") is not None]
    if not candidates:
        return None
    candidates.sort(
        key=lambda r: (abs(r["voltage_set_v"] - voltage), abs(r["throttle_set_pct"] - throttle))
    )
    return max(r["u_eta_sys_k2"] for r in candidates[:2])


def voltage_range(runs: list[dict]) -> tuple[float, float]:
    values = sorted({float(r["voltage_set_v"]) for r in runs})
    if not values:
        raise ValueError("runs 中没有可用电压")
    return values[0], values[-1]


def candidate_grid(
    runs: list[dict],
    *,
    voltage_points: int = 13,
    throttle_points: int = 41,
    min_throttle_pct: float = 0.0,
    max_throttle_pct: float = 100.0,
) -> tuple[np.ndarray, np.ndarray]:
    if voltage_points < 2:
        raise ValueError("voltage_points 必须 ≥2")
    if throttle_points < 2:
        raise ValueError("throttle_points 必须 ≥2")
    if not (0.0 <= min_throttle_pct < max_throttle_pct <= 100.0):
        raise ValueError("throttle 范围必须满足 0 ≤ min < max ≤ 100")
    v_min, v_max = voltage_range(runs)
    voltages = np.linspace(v_min, v_max, int(voltage_points))
    throttles = np.linspace(float(min_throttle_pct), float(max_throttle_pct), int(throttle_points))
    return voltages, throttles


def evaluate_candidates(
    models: dict,
    runs: list[dict],
    *,
    thrust_required_n: float,
    thrust_tolerance: float = 0.1,
    voltage_points: int = 13,
    throttle_points: int = 41,
    max_throttle_pct: float = 100.0,
) -> list[dict]:
    """在连续网格上评估 GP，返回全部可行候选（按推力公差过滤）。"""
    if thrust_required_n <= 0:
        raise ValueError("thrust_required_n 必须 >0")
    if not (0.0 < thrust_tolerance < 1.0):
        raise ValueError("thrust_tolerance 必须在 (0, 1) 内")
    voltages, throttles = candidate_grid(
        runs, voltage_points=voltage_points, throttle_points=throttle_points, max_throttle_pct=max_throttle_pct
    )
    candidates: list[dict] = []
    for voltage in voltages:
        for throttle in throttles:
            thrust, _ = gm._predict(models["thrust"], float(voltage), float(throttle))
            margin = thrust - thrust_required_n
            if abs(margin) > thrust_required_n * thrust_tolerance:
                continue
            eta, var_eta = gm._predict(models["eta"], float(voltage), float(throttle))
            sigma = math.sqrt(max(var_eta, 0.0))
            current_model = models["extra"].get("current_a")
            current = gm._predict(current_model, float(voltage), float(throttle))[0] if current_model else 0.0
            u_local = _u_local(runs, float(voltage), float(throttle)) or 0.0
            eta_conservative = eta - math.sqrt((2.0 * sigma) ** 2 + u_local**2)
            candidates.append(
                {
                    "voltage_set_v": float(voltage),
                    "throttle_set_pct": float(throttle),
                    "thrust_N": thrust,
                    "thrust_margin_N": margin,
                    "eta_sys": eta,
                    "eta_sys_conservative": eta_conservative,
                    "current_a": float(current),
                    "gp_std_eta": sigma,
                    "u_eta_sys_k2": u_local,
                }
            )
    return candidates


def dominates(a: dict, b: dict) -> bool:
    """a 支配 b：η 更大、电流更小、保守 η 更大，且至少一项严格更优。"""
    not_worse = (
        a["eta_sys"] >= b["eta_sys"]
        and a["current_a"] <= b["current_a"]
        and a["eta_sys_conservative"] >= b["eta_sys_conservative"]
    )
    strictly_better = (
        a["eta_sys"] > b["eta_sys"]
        or a["current_a"] < b["current_a"]
        or a["eta_sys_conservative"] > b["eta_sys_conservative"]
    )
    return not_worse and strictly_better


def pareto_front(candidates: list[dict]) -> list[dict]:
    """非支配筛选（O(n²)，候选数百到数千，足够）。"""
    front: list[dict] = []
    for candidate in candidates:
        dominated = False
        for other in candidates:
            if other is candidate:
                continue
            if dominates(other, candidate):
                dominated = True
                break
        if not dominated:
            front.append(candidate)
    return front


def _normalize(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi - lo < 1e-12:
        return [0.5 for _ in values]
    return [(value - lo) / (hi - lo) for value in values]


def mark_knee(front: list[dict]) -> None:
    """按“离理想点 (1, 0, 1) 最近”在归一化目标空间标记 knee。"""
    if not front:
        return
    eta_norm = _normalize([c["eta_sys"] for c in front])
    current_norm = _normalize([c["current_a"] for c in front])
    cons_norm = _normalize([c["eta_sys_conservative"] for c in front])
    best_index = 0
    best_distance = math.inf
    for index in range(len(front)):
        distance = math.sqrt(
            (1.0 - eta_norm[index]) ** 2 + current_norm[index] ** 2 + (1.0 - cons_norm[index]) ** 2
        )
        if distance < best_distance:
            best_distance = distance
            best_index = index
    for index, candidate in enumerate(front):
        candidate["is_knee"] = index == best_index


def rank_front(front: list[dict]) -> list[dict]:
    """前沿排序：保守 η 降序 → 电流升序 → 电压升序；并写 rank/is_knee/data_note。"""
    ordered = sorted(front, key=lambda c: (-c["eta_sys_conservative"], c["current_a"], c["voltage_set_v"]))
    mark_knee(ordered)
    for index, candidate in enumerate(ordered, start=1):
        candidate["rank"] = index
        candidate.setdefault("is_knee", False)
        candidate["data_note"] = DATA_NOTE_PARETO
    return ordered


def run_pareto(
    runs: list[dict],
    *,
    thrust_required_n: float,
    thrust_tolerance: float = 0.1,
    max_throttle_pct: float = 100.0,
    voltage_points: int = 13,
    throttle_points: int = 41,
) -> dict:
    models = gm.fit_models(runs)
    candidates = evaluate_candidates(
        models,
        runs,
        thrust_required_n=thrust_required_n,
        thrust_tolerance=thrust_tolerance,
        voltage_points=voltage_points,
        throttle_points=throttle_points,
        max_throttle_pct=max_throttle_pct,
    )
    if not candidates:
        raise ValueError(
            f"GP 未找到满足推力 {thrust_required_n:g} N ±{thrust_tolerance*100:g}% 的候选；请放宽公差或补充工况点"
        )
    front = rank_front(pareto_front(candidates))
    knee = next((entry for entry in front if entry.get("is_knee")), front[0])
    return {
        "front": front,
        "candidates": candidates,
        "knee": knee,
        "n_candidates": len(candidates),
        "n_front": len(front),
    }


def suggest_measurements(
    runs: list[dict],
    *,
    n: int = 5,
    min_distance: float = 0.12,
    voltage_points: int = 13,
    throttle_points: int = 41,
    max_throttle_pct: float | None = None,
) -> list[dict]:
    """GP σ 最大 + 空间间距约束的补测点推荐（贪心，限定在已测油门区间内插值）。"""
    if n < 1:
        raise ValueError("n 必须 ≥1")
    if not (0.0 < min_distance < 2.0):
        raise ValueError("min_distance 必须在 (0, 2) 内")
    models = gm.fit_models(runs)
    observed_throttles = [float(r["throttle_set_pct"]) for r in runs]
    throttle_lo = min(observed_throttles)
    throttle_hi = max(observed_throttles)
    if max_throttle_pct is not None:
        throttle_hi = min(throttle_hi, float(max_throttle_pct))
    voltages, throttles = candidate_grid(
        runs,
        voltage_points=voltage_points,
        throttle_points=throttle_points,
        min_throttle_pct=throttle_lo,
        max_throttle_pct=throttle_hi,
    )
    features = np.array(
        [[v / gp.VOLTAGE_SCALE, t / gp.THROTTLE_SCALE] for v in voltages for t in throttles], dtype=float
    )
    means, variances = models["eta"].predict(features)
    observed = np.array(
        [[r["voltage_set_v"] / gp.VOLTAGE_SCALE, r["throttle_set_pct"] / gp.THROTTLE_SCALE] for r in runs],
        dtype=float,
    )
    sigma = np.sqrt(np.clip(variances, 0.0, None))
    order = np.argsort(-sigma)
    selected: list[dict] = []
    selected_points: list[np.ndarray] = []
    voltage_lo, voltage_hi = float(voltages[0]), float(voltages[-1])
    for index in order:
        if len(selected) >= n:
            break
        point = features[index]
        distance_observed = float(np.min(np.linalg.norm(observed - point, axis=1)))
        distance_selected = (
            float(np.min(np.linalg.norm(np.vstack(selected_points) - point, axis=1))) if selected_points else math.inf
        )
        distance = min(distance_observed, distance_selected)
        if distance < min_distance:
            continue
        flat_voltage = float(voltages[index // len(throttles)])
        flat_throttle = float(throttles[index % len(throttles)])
        selected.append(
            {
                "voltage_set_v": flat_voltage,
                "throttle_set_pct": flat_throttle,
                "gp_std_eta": float(sigma[index]),
                "u_eta_sys_k2": _u_local(runs, flat_voltage, flat_throttle) or 0.0,
                "min_distance": distance,
                "in_observed_box": bool(voltage_lo - 1e-9 <= flat_voltage <= voltage_hi + 1e-9),
                "data_note": DATA_NOTE_SUGGEST,
            }
        )
        selected_points.append(point)
    for rank, entry in enumerate(selected, start=1):
        entry["rank"] = rank
    if not selected:
        raise ValueError("没有满足间距约束的补测点推荐；请减小 --min-distance 或增加网格密度")
    return selected


def write_csv(rows: list[dict], path: Path | str, *, fields: list[str], overwrite: bool = False) -> Path:
    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output}（如需覆盖加 --overwrite）")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return output


def plot_pareto(
    candidates: list[dict],
    front: list[dict],
    output_png: Path | str,
    *,
    thrust_required_n: float,
    thrust_tolerance: float = 0.1,
    overwrite: bool = False,
) -> Path:
    output = Path(output_png)
    if output.exists() and not overwrite:
        raise FileExistsError(f"图件已存在：{output}（如需覆盖加 --overwrite）")
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))
    ax = axes[0]
    ax.scatter(
        [c["current_a"] for c in candidates],
        [c["eta_sys"] for c in candidates],
        s=10,
        c="#9aa0a6",
        alpha=0.5,
        label="feasible candidates",
    )
    front_current = [c["current_a"] for c in front]
    front_eta = [c["eta_sys"] for c in front]
    ax.plot(front_current, front_eta, "-", color="#b2182b", lw=1.4, label="Pareto front")
    ax.scatter(front_current, front_eta, s=26, c="#2166ac", zorder=3, label="Pareto points")
    knee = next((c for c in front if c.get("is_knee")), None)
    if knee:
        ax.scatter(
            [knee["current_a"]],
            [knee["eta_sys"]],
            marker="*",
            s=200,
            c="#f1a340",
            edgecolors="black",
            zorder=4,
            label="#knee (ideal-point)",
        )
    ax.set_xlabel("Battery current (A)")
    ax.set_ylabel("η_sys (GP mean)")
    ax.set_title(f"Thrust {thrust_required_n:g} N ±{thrust_tolerance*100:g}% — efficiency vs current")
    ax.grid(True, ls=":", alpha=0.6)
    ax.legend(fontsize=8, loc="lower right")

    ax2 = axes[1]
    ax2.scatter(
        [c["gp_std_eta"] for c in candidates],
        [c["eta_sys"] for c in candidates],
        s=10,
        c="#9aa0a6",
        alpha=0.5,
        label="feasible candidates",
    )
    ax2.scatter(
        [c["gp_std_eta"] for c in front],
        [c["eta_sys"] for c in front],
        s=26,
        c="#2166ac",
        zorder=3,
        label="Pareto points",
    )
    if knee:
        ax2.scatter(
            [knee["gp_std_eta"]],
            [knee["eta_sys"]],
            marker="*",
            s=200,
            c="#f1a340",
            edgecolors="black",
            zorder=4,
        )
    ax2.set_xlabel("GP predictive std σ_gp (η_sys)")
    ax2.set_ylabel("η_sys (GP mean)")
    ax2.set_title("Point estimate vs smoothness uncertainty")
    ax2.grid(True, ls=":", alpha=0.6)
    ax2.legend(fontsize=8, loc="lower right")
    fig.suptitle("Selection v0.4 — GP multi-objective Pareto (SIM prototype)")
    fig.text(0.5, 0.01, "SIMULATED DATA — NOT EXPERIMENTAL (GP prototype only)", ha="center", color="crimson", fontsize=9, fontweight="bold")
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(output, dpi=150)
    plt.close(fig)
    return output


def plot_suggestions(
    runs: list[dict],
    suggestions: list[dict],
    output_png: Path | str,
    *,
    overwrite: bool = False,
) -> Path:
    output = Path(output_png)
    if output.exists() and not overwrite:
        raise FileExistsError(f"图件已存在：{output}（如需覆盖加 --overwrite）")
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ax.scatter(
        [r["voltage_set_v"] for r in runs],
        [r["throttle_set_pct"] for r in runs],
        s=40,
        c="#636363",
        marker="o",
        label="observed runs",
        zorder=2,
    )
    ax.scatter(
        [s["voltage_set_v"] for s in suggestions],
        [s["throttle_set_pct"] for s in suggestions],
        s=[60 + 400 * s["gp_std_eta"] / max(s2["gp_std_eta"] for s2 in suggestions) for s in suggestions],
        c="#d73027",
        marker="X",
        edgecolors="black",
        label="GP σ-suggested measurements",
        zorder=3,
    )
    for suggestion in suggestions:
        ax.annotate(
            f"#{suggestion['rank']} σ={suggestion['gp_std_eta']:.3f}",
            (suggestion["voltage_set_v"], suggestion["throttle_set_pct"]),
            textcoords="offset points",
            xytext=(8, 6),
            fontsize=8,
        )
    ax.set_xlabel("Bus voltage (V)")
    ax.set_ylabel("Throttle command (%)")
    ax.set_title("GP next-measurement suggestions (SIM prototype)")
    ax.grid(True, ls=":", alpha=0.6)
    ax.legend(fontsize=8, loc="best")
    fig.text(0.5, 0.01, "SIMULATED DATA — NOT EXPERIMENTAL (planning only)", ha="center", color="crimson", fontsize=9, fontweight="bold")
    fig.tight_layout(rect=(0, 0.04, 1, 1.0))
    fig.savefig(output, dpi=150)
    plt.close(fig)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="选型 v0.4：GP 多目标 Pareto + 补测点推荐")
    parser.add_argument("--input", required=True, help="效率地图 runs CSV")
    parser.add_argument("--thrust", type=float, help="需求推力（N）；pareto 模式必填")
    parser.add_argument("--tolerance", type=float, default=0.1, help="推力相对公差（默认 0.1）")
    parser.add_argument("--max-throttle", type=float, default=100.0)
    parser.add_argument("--voltage-points", type=int, default=13)
    parser.add_argument("--throttle-points", type=int, default=41)
    parser.add_argument("--output", default="data/processed/selection_v0.4_pareto.csv")
    parser.add_argument("--figure", default="data/processed/figures/selection_v0.4.png")
    parser.add_argument("--suggest", action="store_true", help="运行补测点推荐模式")
    parser.add_argument("--n", type=int, default=5, help="推荐点数（suggest 模式）")
    parser.add_argument("--min-distance", type=float, default=0.12)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--require-measured", action="store_true", help="MEASURED 守门：仅接受 source=MEASURED 的 runs（D038）")
    parser.add_argument("--uq-k2", type=float, default=0.0, help="可选：统一 U(k=2) 测量不确定度；>0 时按 D056 重算保守效率")
    args = parser.parse_args(argv)

    try:
        runs = mp.load_runs(Path(args.input))
        if args.require_measured:
            mp.assert_measured(runs)
    except (ValueError, FileNotFoundError) as exc:
        print(f"错误：{exc}")
        return 2

    try:
        if args.suggest:
            suggestions = suggest_measurements(
                runs,
                n=args.n,
                min_distance=args.min_distance,
                voltage_points=args.voltage_points,
                throttle_points=args.throttle_points,
                max_throttle_pct=args.max_throttle,
            )
            csv_path = write_csv(suggestions, args.output, fields=SUGGEST_FIELDS, overwrite=args.overwrite)
            png_path = plot_suggestions(runs, suggestions, args.figure, overwrite=args.overwrite)
            print(f"补测点推荐：{len(suggestions)} 个候选（GP σ 最大 + 间距 ≥ {args.min_distance:g}）")
            for entry in suggestions:
                print(
                    f"  #{entry['rank']} {entry['voltage_set_v']:.2f} V / {entry['throttle_set_pct']:.1f}%"
                    f"：σ_gp={entry['gp_std_eta']:.4f}，U(k=2)={entry['u_eta_sys_k2']:.4f}，"
                    f"最近已测距离={entry['min_distance']:.3f}"
                )
            print(f"报告：{csv_path}\n图件：{png_path}")
            print("注意：补测点推荐来自 GP 预测标准差，仅用于规划台架补测，不是实验结果。")
            return 0

        if args.thrust is None:
            print("错误：pareto 模式需要 --thrust")
            return 2
        result = run_pareto(
            runs,
            thrust_required_n=args.thrust,
            thrust_tolerance=args.tolerance,
            max_throttle_pct=args.max_throttle,
            voltage_points=args.voltage_points,
            throttle_points=args.throttle_points,
        )
        if args.uq_k2 > 0:
            u_meas = args.uq_k2 / 2.0
            for row in result["front"]:
                sigma_total = math.sqrt(u_meas ** 2 + float(row["gp_std_eta"]) ** 2)
                row["eta_sys_conservative"] = row["eta_sys"] - 2.0 * sigma_total
            result["front"].sort(key=lambda r: -r["eta_sys_conservative"])
            for i, row in enumerate(result["front"], 1):
                row["rank"] = i
            mark_knee(result["front"])
            result["knee"] = result["front"][0]
        csv_path = write_csv(result["front"], args.output, fields=PARETO_FIELDS, overwrite=args.overwrite)
        png_path = plot_pareto(
            result["candidates"],
            result["front"],
            args.figure,
            thrust_required_n=args.thrust,
            thrust_tolerance=args.tolerance,
            overwrite=args.overwrite,
        )
        print(
            f"需求推力 {args.thrust:g} N ±{args.tolerance*100:g}%：可行候选 {result['n_candidates']} 个，"
            f"Pareto 前沿 {result['n_front']} 个"
        )
        knee = result["knee"]
        print(
            f"  knee：{knee['voltage_set_v']:.2f} V / {knee['throttle_set_pct']:.1f}%"
            f"｜η {knee['eta_sys']:.4f}（保守 {knee['eta_sys_conservative']:.4f}）"
            f"｜I {knee['current_a']:.2f} A｜σ_gp {knee['gp_std_eta']:.4f}"
        )
        print(f"报告：{csv_path}\n图件：{png_path}")
        print("注意：GP 多目标 Pareto 为 SIM 原型，外推区不可信，不是选型结论。")
        return 0
    except (ValueError, FileExistsError) as exc:
        print(f"错误：{exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
