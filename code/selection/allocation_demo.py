"""拓展 E3 路径 A：同一总推力下的转速分配对总电功率影响（SIM 演示）。

数据：data/processed/efficiency_map_runs.csv（每电压内按推力单调插值 P_elec 与 η）。
模型：4 电机，2 台推力 T(1+s)、2 台 T(1-s)，总推力恒定 4T；
      单机 P_elec(T) 由实测点插值；总 P(s)=2·P(T(1+s))+2·P(T(1-s))。
输出：data/processed/allocation_E3_demo.csv + figures/allocation_E3_v0.1.png
注意：SIM 方法学演示，不是实验结果；分配仅静态功率层面，不涉及飞控。
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "pylibs"))
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import math  # noqa: E402

DATA = ROOT / "data" / "processed" / "efficiency_map_runs.csv"
OUT_CSV = ROOT / "data" / "processed" / "allocation_E3_demo.csv"
OUT_PNG = ROOT / "data" / "processed" / "figures" / "allocation_E3_v0.1.png"


def load_curves(path: Path) -> dict[float, list[tuple[float, float, float]]]:
    curves: dict[float, list] = {}
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r.get("source") or "").upper() != "SIM":
                continue
            v = float(r["voltage_set_v"])
            curves.setdefault(v, []).append(
                (float(r["thrust_N_mean"]), float(r["p_elec_w_mean"]), float(r["eta_sys_mean"]))
            )
    for v in curves:
        curves[v].sort()
    return curves


def interp(points: list[tuple[float, float]], x: float) -> float:
    if x <= points[0][0]:
        return points[0][1]
    if x >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0) if x1 > x0 else 0.0
            return y0 + t * (y1 - y0)
    return points[-1][1]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--thrust-per-motor", type=float, default=2.0, help="单机推力 T (N)")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args(argv)
    for p in (OUT_CSV, OUT_PNG):
        if p.exists() and not args.overwrite:
            print(f"错误：输出已存在（--overwrite 覆盖）：{p}")
            return 2
    curves = load_curves(DATA)
    rows = []
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for v in sorted(curves):
        pts = [(t, pe) for t, pe, _ in curves[v]]
        base = 4 * interp(pts, args.thrust_per_motor)
        ss = [i / 20 for i in range(0, 11)]
        ps = []
        for s in ss:
            th = args.thrust_per_motor
            total = 2 * interp(pts, th * (1 + s)) + 2 * interp(pts, th * (1 - s))
            ps.append(total)
            rows.append({
                "voltage_set_v": v,
                "thrust_per_motor_T": th,
                "skew_s": s,
                "p_elec_total_w": total,
                "p_rel_to_uniform": total / base - 1.0,
            })
        ax.plot(ss, [(p / base - 1.0) * 100 for p in ps], marker="o", label=f"{v:g} V")
    ax.set_xlabel("thrust skew s (high pair +s, low pair −s)")
    ax.set_ylabel("total electrical power change vs uniform (%)")
    ax.set_title("E3 path-A: allocation effect on total power (SIM demo, T=%.2f N/motor)" % args.thrust_per_motor)
    ax.axhline(0, color="gray", lw=0.8)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.text(0.5, 0.01, "SIMULATED DATA — NOT EXPERIMENTAL (allocation study only)", ha="center", color="crimson", fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["voltage_set_v", "thrust_per_motor_T", "skew_s", "p_elec_total_w", "p_rel_to_uniform"])
        w.writeheader()
        w.writerows(rows)
    fig.savefig(OUT_PNG, dpi=150)
    print(f"CSV：{OUT_CSV}（{len(rows)} 行）；图件：{OUT_PNG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
