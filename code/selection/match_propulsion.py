# -*- coding: utf-8 -*-
"""选型匹配原型 v0.2：推力需求 → 插值/网格候选 → 多目标排序 + Pareto 图。

输入是效率地图 runs CSV（`aggregate_efficiency.py` 的产物）。当前只有 SIM 数据，
因此本工具只验证"需求 → 匹配 → 报告/图件"的软件链路，**不是真实选型结论**。

v0.2 相对 v0.1：
- 油门插值：同一 (组合, 电压) 的相邻油门点之间按推力线性插值，
  得到'刚好满足需求推力'的虚拟工作点（`matched_by="interp"`）；无插值区间时回退网格点（`"grid"`）；
- 多目标排序：`--objective eta_sys|current|balanced`，balanced 用归一化加权分；
- 不确定度惩罚：`--max-u` 过滤 U(k=2) 过大的候选，并输出保守效率 `eta_sys_conservative=η_sys−U`。

用法：
    py -3.12 code\\selection\\match_propulsion.py --input data\\processed\\efficiency_map_runs.csv --thrust 3.0 --tolerance 0.05 --objective balanced
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "pylibs"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUTPUT_FIELDS = [
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
    "eta_sys_conservative",
    "eta_em",
    "fm",
    "rpm",
    "current_a",
    "u_eta_sys_k2",
    "score",
    "prop_diameter_m",
]

INPUT_FIELDS = [
    "run_id",
    "source",
    "combo",
    "voltage_set_v",
    "throttle_set_pct",
    "thrust_N_mean",
    "eta_sys_mean",
    "eta_em_mean",
    "fm_mean",
    "rpm_mean",
    "current_a_mean",
    "u_eta_sys_k2",
    "prop_diameter_m",
]

OBJECTIVES = ("eta_sys", "current", "balanced")


def _num(value) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _interp(left: float | None, right: float | None, t: float) -> float | None:
    if left is None or right is None:
        return None
    return left + (right - left) * t


def load_runs(path: Path) -> list[dict]:
    """读取效率地图 runs CSV；缺必需列或无数值行时抛 ValueError。"""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [field for field in INPUT_FIELDS if field not in fields]
        if missing:
            raise ValueError(f"runs CSV 缺少必需列：{missing}")
        runs: list[dict] = []
        for row in reader:
            thrust = _num(row.get("thrust_N_mean"))
            eta_sys = _num(row.get("eta_sys_mean"))
            if thrust is None or eta_sys is None:
                continue
            runs.append(
                {
                    "run_id": row.get("run_id", ""),
                    "source": row.get("source", ""),
                    "combo": row.get("combo", ""),
                    "voltage_set_v": _num(row.get("voltage_set_v")),
                    "throttle_set_pct": _num(row.get("throttle_set_pct")),
                    "thrust_N": thrust,
                    "eta_sys": eta_sys,
                    "eta_em": _num(row.get("eta_em_mean")),
                    "fm": _num(row.get("fm_mean")),
                    "rpm": _num(row.get("rpm_mean")),
                    "current_a": _num(row.get("current_a_mean")),
                    "u_eta_sys_k2": _num(row.get("u_eta_sys_k2")),
                    "prop_diameter_m": _num(row.get("prop_diameter_m")),
                }
            )
    if not runs:
        raise ValueError("runs CSV 中没有任何带数值推力/效率的行")
    return runs


def assert_measured(runs: list[dict]) -> None:
    """MEASURED 选型守门（D035/D036/D037/D038）：拒绝非实测来源的 runs。"""
    if not runs:
        raise ValueError("MEASURED 守门拒绝：没有可校验的 runs")
    bad = [run for run in runs if str(run.get("source", "")).upper() != "MEASURED"]
    if bad:
        sample = ", ".join(sorted({str(run.get("run_id", "?")) for run in bad})[:5])
        raise ValueError(
            f"MEASURED 守门拒绝：{len(bad)}/{len(runs)} 个 run 来源不是 MEASURED（示例：{sample}）；"
            "选型入口 --require-measured 仅接受实测效率地图"
        )


def pareto_front(runs: list[dict]) -> list[dict]:
    """推力—效率 Pareto 前沿（推力越小越好、η_sys 越大越好），按推力升序返回。"""
    ordered = sorted(runs, key=lambda item: (item["thrust_N"], -item["eta_sys"]))
    front: list[dict] = []
    best_eta = float("-inf")
    for run in ordered:
        if run["eta_sys"] > best_eta:
            front.append(run)
            best_eta = run["eta_sys"]
    return front


def _interp_candidate(left: dict, right: dict, required: float) -> dict | None:
    """在相邻两个网格点之间按推力线性插值；不覆盖需求推力时返回 None。"""
    low, high = (left, right) if left["thrust_N"] <= right["thrust_N"] else (right, left)
    span = high["thrust_N"] - low["thrust_N"]
    if span <= 1e-12 or not (low["thrust_N"] <= required <= high["thrust_N"]):
        return None
    t = (required - low["thrust_N"]) / span
    return {
        "run_id": f"interp:{low['run_id']}~{high['run_id']}",
        "source": low["source"],
        "combo": low["combo"],
        "voltage_set_v": low["voltage_set_v"],
        "throttle_set_pct": _interp(low["throttle_set_pct"], high["throttle_set_pct"], t),
        "thrust_N": required,
        "eta_sys": _interp(low["eta_sys"], high["eta_sys"], t),
        "eta_em": _interp(low["eta_em"], high["eta_em"], t),
        "fm": _interp(low["fm"], high["fm"], t),
        "rpm": _interp(low["rpm"], high["rpm"], t),
        "current_a": _interp(low["current_a"], high["current_a"], t),
        "u_eta_sys_k2": max(
            [u for u in (low.get("u_eta_sys_k2"), high.get("u_eta_sys_k2")) if u is not None],
            default=None,
        ),
        "prop_diameter_m": low["prop_diameter_m"],
        "matched_by": "interp",
    }


def _grid_candidate(run: dict) -> dict:
    entry = dict(run)
    entry["matched_by"] = "grid"
    return entry


def _score_candidates(candidates: list[dict], objective: str) -> list[dict]:
    """按目标排序候选，并写入归一化 score（仅 balanced 有意义，其余按目标排序）。"""
    if not candidates:
        return []
    eta_values = [c["eta_sys"] for c in candidates]
    cur_values = [c["current_a"] for c in candidates if c.get("current_a") is not None]
    u_values = [c["u_eta_sys_k2"] for c in candidates if c.get("u_eta_sys_k2") is not None]

    def _norm(value: float | None, values: list[float], *, invert: bool) -> float:
        if value is None or not values or max(values) <= min(values):
            return 0.5
        ratio = (value - min(values)) / (max(values) - min(values))
        return 1.0 - ratio if invert else ratio

    for candidate in candidates:
        eta_n = _norm(candidate["eta_sys"], eta_values, invert=False)
        cur_n = _norm(candidate.get("current_a"), cur_values, invert=True)
        u_n = _norm(candidate.get("u_eta_sys_k2"), u_values, invert=True)
        candidate["score"] = round(0.6 * eta_n + 0.2 * cur_n + 0.2 * u_n, 6)

    if objective == "eta_sys":
        candidates.sort(key=lambda c: (-c["eta_sys"], c.get("current_a") or 0.0))
    elif objective == "current":
        candidates.sort(key=lambda c: (c.get("current_a") if c.get("current_a") is not None else float("inf"), -c["eta_sys"]))
    elif objective == "balanced":
        candidates.sort(key=lambda c: (-c["score"], -c["eta_sys"]))
    return candidates


def match(
    runs: list[dict],
    *,
    thrust_required_n: float,
    thrust_tolerance: float = 0.1,
    max_throttle_pct: float = 100.0,
    voltages: list[float] | None = None,
    top_n: int = 5,
    source: str = "ANY",
    interpolate: bool = True,
    objective: str = "eta_sys",
    max_u_k2: float | None = None,
) -> list[dict]:
    """按推力需求筛选、插值并排序；同一 (combo, 电压) 只保留一个候选。"""
    if thrust_required_n <= 0:
        raise ValueError("thrust_required_n 必须大于 0")
    if not (0 <= thrust_tolerance < 1):
        raise ValueError("thrust_tolerance 必须落在 [0, 1)")
    if objective not in OBJECTIVES:
        raise ValueError(f"objective 必须是 {OBJECTIVES} 之一")
    if max_u_k2 is not None and max_u_k2 < 0:
        raise ValueError("max_u_k2 必须 >= 0")

    lower = thrust_required_n * (1.0 - thrust_tolerance)
    upper = thrust_required_n * (1.0 + thrust_tolerance)

    def _allowed(run: dict) -> bool:
        if source != "ANY" and run["source"] != source:
            return False
        if run["throttle_set_pct"] is None or run["throttle_set_pct"] > max_throttle_pct:
            return False
        if voltages is not None and (run["voltage_set_v"] is None or run["voltage_set_v"] not in voltages):
            return False
        if max_u_k2 is not None and run.get("u_eta_sys_k2") is not None and run["u_eta_sys_k2"] > max_u_k2:
            return False
        return True

    allowed = [run for run in runs if _allowed(run)]
    groups: dict[tuple[str, float | None], list[dict]] = {}
    for run in allowed:
        groups.setdefault((run["combo"], run["voltage_set_v"]), []).append(run)

    best_by_combo: dict[tuple[str, float | None], dict] = {}
    for key, group in groups.items():
        group.sort(key=lambda item: item["thrust_N"])
        chosen: dict | None = None
        if interpolate:
            for left, right in zip(group, group[1:]):
                if left["thrust_N"] <= thrust_required_n <= right["thrust_N"]:
                    candidate = _interp_candidate(left, right, thrust_required_n)
                    if candidate is None:
                        continue
                    if candidate["throttle_set_pct"] is not None and candidate["throttle_set_pct"] > max_throttle_pct:
                        continue
                    if (
                        max_u_k2 is not None
                        and candidate.get("u_eta_sys_k2") is not None
                        and candidate["u_eta_sys_k2"] > max_u_k2
                    ):
                        continue
                    chosen = candidate
                    break
        if chosen is None:
            grid = [run for run in group if lower <= run["thrust_N"] <= upper]
            if not grid:
                continue
            chosen = _grid_candidate(max(grid, key=lambda item: item["eta_sys"]))
        best_by_combo[key] = chosen

    candidates = list(best_by_combo.values())
    if not candidates:
        raise ValueError(
            f"没有满足推力 {lower:.3f}–{upper:.3f} N、油门 ≤{max_throttle_pct:g}% 的工况；"
            "请放宽公差、补充电压点或扩充效率地图工况"
        )

    ranked = _score_candidates(candidates, objective)
    results: list[dict] = []
    for index, run in enumerate(ranked[:top_n], start=1):
        entry = dict(run)
        entry["rank"] = index
        entry["thrust_margin_N"] = run["thrust_N"] - thrust_required_n
        entry["eta_sys_conservative"] = (
            None if run.get("u_eta_sys_k2") is None else run["eta_sys"] - run["u_eta_sys_k2"]
        )
        results.append(entry)
    return results


def write_report(results: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for entry in results:
            row = {}
            for field in OUTPUT_FIELDS:
                value = entry.get(field)
                row[field] = "" if value is None else value
            writer.writerow(row)
    return path


def _fmt(value) -> str:
    return "—" if value is None else (f"{value:.4f}" if isinstance(value, float) else str(value))


def plot_selection(
    runs: list[dict],
    results: list[dict],
    output_png: Path,
    *,
    thrust_required_n: float,
    thrust_tolerance: float = 0.1,
    title: str = "Selection prototype v0.2 — Thrust vs η_sys",
    overwrite: bool = False,
) -> Path:
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output_png}（如需覆盖加 --overwrite）")
    output_png.parent.mkdir(parents=True, exist_ok=True)

    figure, axes = plt.subplots(figsize=(9.0, 6.0), dpi=120)
    axes.scatter(
        [run["thrust_N"] for run in runs],
        [run["eta_sys"] for run in runs],
        s=22,
        c="#9aa4b2",
        label="efficiency map points",
        zorder=2,
    )

    front = pareto_front(runs)
    axes.plot(
        [run["thrust_N"] for run in front],
        [run["eta_sys"] for run in front],
        color="#c0392b",
        linewidth=1.4,
        label="Pareto front (min thrust / max eta)",
        zorder=3,
    )

    marker_colors = ["#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]
    marker_shapes = ["o", "s", "^", "D", "v"]
    label_offsets = [(8, 10), (8, -14), (8, -30), (8, -46), (8, -62)]
    for entry in results:
        rank = entry["rank"]
        color = marker_colors[(rank - 1) % len(marker_colors)]
        shape = marker_shapes[(rank - 1) % len(marker_shapes)]
        axes.scatter(
            [entry["thrust_N"]],
            [entry["eta_sys"]],
            s=90,
            marker=shape,
            edgecolors="black",
            linewidths=0.8,
            color=color,
            zorder=5,
            label=(
                f"#{rank} {entry['voltage_set_v']:g} V / {entry['throttle_set_pct']:.1f}%"
                f" ({entry['matched_by']})"
            ),
        )
        offset = label_offsets[(rank - 1) % len(label_offsets)]
        axes.annotate(
            f"#{rank}",
            xy=(entry["thrust_N"], entry["eta_sys"]),
            xytext=offset,
            textcoords="offset points",
            fontsize=9,
            color=color,
            fontweight="bold",
        )

    lower = thrust_required_n * (1.0 - thrust_tolerance)
    upper = thrust_required_n * (1.0 + thrust_tolerance)
    axes.axvspan(lower, upper, color="#f1c40f", alpha=0.15, zorder=1)
    axes.axvline(thrust_required_n, color="#b7950b", linestyle="--", linewidth=1.0, zorder=1)

    axes.set_xlabel("Thrust (N)")
    axes.set_ylabel("System efficiency η_sys")
    axes.set_title(title)
    axes.grid(True, linestyle=":", alpha=0.5)
    axes.legend(loc="lower right", fontsize=8)

    if any(run["source"] == "SIM" for run in runs):
        figure.subplots_adjust(bottom=0.17)
        figure.text(
            0.5,
            0.025,
            "SIMULATED DATA — NOT EXPERIMENTAL (prototype only)",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="任务推力需求 → 插值/网格候选 → 多目标排序 + Pareto 图（原型）")
    parser.add_argument("--input", type=Path, default=Path("data/processed/efficiency_map_runs.csv"))
    parser.add_argument("--thrust", type=float, required=True, help="需求推力，N")
    parser.add_argument("--tolerance", type=float, default=0.1, help="推力公差（相对值，默认 0.1=±10%%）")
    parser.add_argument("--max-throttle", type=float, default=100.0, help="最大油门百分比")
    parser.add_argument("--voltages", type=str, default="", help="限定电压，逗号分隔，如 22.2,29.6")
    parser.add_argument("--source", choices=["ANY", "SIM", "MEASURED"], default="ANY")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--objective", choices=list(OBJECTIVES), default="eta_sys", help="排序目标")
    parser.add_argument("--max-u", type=float, default=None, help="过滤 U(k=2) 超过该值的候选")
    parser.add_argument("--no-interp", action="store_true", help="关闭油门插值，只用网格点")
    parser.add_argument("--output", type=Path, default=Path("data/processed/selection_top_n.csv"))
    parser.add_argument("--figure", type=Path, default=Path("data/processed/figures/selection_v0.2.png"))
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--require-measured", action="store_true", help="MEASURED 守门：仅接受 source=MEASURED 的 runs（D038）")
    args = parser.parse_args(argv)

    try:
        runs = load_runs(args.input)
        if args.require_measured:
            assert_measured(runs)
        voltages = [float(item) for item in args.voltages.split(",") if item.strip()] or None
        results = match(
            runs,
            thrust_required_n=args.thrust,
            thrust_tolerance=args.tolerance,
            max_throttle_pct=args.max_throttle,
            voltages=voltages,
            top_n=args.top,
            source=args.source,
            interpolate=not args.no_interp,
            objective=args.objective,
            max_u_k2=args.max_u,
        )
    except (OSError, ValueError) as exc:
        print(f"错误：{exc}")
        return 2

    if any(entry["source"] == "SIM" for entry in results):
        print("⚠ 匹配结果来自 SIM 模拟效率地图：仅原型演示，不是选型结论")

    if args.output.exists() and not args.overwrite:
        print(f"错误：输出文件已存在：{args.output}（如需覆盖加 --overwrite）")
        return 2
    write_report(results, args.output)
    try:
        figure_path = plot_selection(
            runs,
            results,
            args.figure,
            thrust_required_n=args.thrust,
            thrust_tolerance=args.tolerance,
            overwrite=args.overwrite,
        )
    except FileExistsError as exc:
        print(f"错误：{exc}")
        return 2

    print(f"需求推力：{args.thrust:g} N ±{args.tolerance:.0%}；目标 {args.objective}；候选 {len(results)} 个")
    for entry in results:
        print(
            f"  #{entry['rank']} {entry['source']} {entry['combo']} "
            f"{entry['voltage_set_v']:g} V / {entry['throttle_set_pct']:.1f}% "
            f"[{entry['matched_by']}]：推力 {entry['thrust_N']:.3f} N（偏差 {entry['thrust_margin_N']:+.3f} N）、"
            f"η_sys {entry['eta_sys']:.4f}（保守 {_fmt(entry['eta_sys_conservative'])}）、"
            f"I {_fmt(entry['current_a'])} A、U(k=2) {_fmt(entry['u_eta_sys_k2'])}、score {entry['score']:.3f}"
        )
    print(f"报告：{args.output}")
    print(f"图件：{figure_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
