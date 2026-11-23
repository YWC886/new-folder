"""U(k=2) 敏感性分析 v0.1：测量不确定度如何影响选型 Pareto/knee。

对一组 U(k=2) 取值，重复"重算保守效率 → 重排前沿"，输出 knee 迁移与 Top-N 排名变化。
SIM 原型，不是选型结论（D056/D057）。
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import multiobjective as mo
import match_propulsion as mp

SCHEMA_VERSION = "0.1"
DATA_NOTE = "SIM 敏感性分析：U(k=2) 取值影响 Pareto 排序，仅方法学演示，不是选型结论"
OUT_FIELDS = [
    "u_k2",
    "n_front",
    "knee_voltage_set_v",
    "knee_throttle_set_pct",
    "knee_eta_sys",
    "knee_eta_cons_2sigma",
    "top1_voltage_set_v",
    "top1_throttle_set_pct",
    "top1_eta_cons_2sigma",
    "data_note",
]


def _recompute(front: list[dict], u_k2: float) -> list[dict]:
    u_meas = u_k2 / 2.0
    rows = []
    for row in front:
        sigma_gp = float(row["gp_std_eta"])
        sigma_total = math.sqrt(u_meas**2 + sigma_gp**2)
        item = dict(row)
        item["eta_sys_conservative"] = item["eta_sys"] - 2.0 * sigma_total
        rows.append(item)
    rows.sort(key=lambda r: -r["eta_sys_conservative"])
    for i, row in enumerate(rows, 1):
        row["rank"] = i
    return rows


def run_sensitivity(
    runs: list[dict],
    *,
    thrust_required_n: float = 5.0,
    thrust_tolerance: float = 0.1,
    u_values: tuple[float, ...] = (0.0, 0.01, 0.02, 0.0226, 0.03, 0.05),
    max_throttle_pct: float = 100.0,
) -> list[dict]:
    if not u_values:
        raise ValueError("u_values 不能为空")
    if any(u < 0 for u in u_values):
        raise ValueError("U(k=2) 取值必须 ≥ 0")
    result = mo.run_pareto(
        runs,
        thrust_required_n=thrust_required_n,
        thrust_tolerance=thrust_tolerance,
        max_throttle_pct=max_throttle_pct,
    )
    base_front = result["front"]
    if not base_front:
        raise ValueError("Pareto 前沿为空：请放宽推力公差或补充地图点")
    out = []
    for u in u_values:
        ranked = _recompute(base_front, u)
        top = ranked[0]
        out.append(
            {
                "u_k2": float(u),
                "n_front": len(ranked),
                "knee_voltage_set_v": float(top["voltage_set_v"]),
                "knee_throttle_set_pct": float(top["throttle_set_pct"]),
                "knee_eta_sys": float(top["eta_sys"]),
                "knee_eta_cons_2sigma": float(top["eta_sys_conservative"]),
                "top1_voltage_set_v": float(ranked[0]["voltage_set_v"]),
                "top1_throttle_set_pct": float(ranked[0]["throttle_set_pct"]),
                "top1_eta_cons_2sigma": float(ranked[0]["eta_sys_conservative"]),
                "data_note": DATA_NOTE,
            }
        )
    return out


def write_csv(rows: list[dict], path: Path | str, *, overwrite: bool = False) -> Path:
    out = Path(path)
    if out.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{out}（加 --overwrite 覆盖）")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in row.items()})
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="U(k=2) 对选型 Pareto 的敏感性分析（SIM）")
    parser.add_argument("--input", default="data/processed/efficiency_map_runs.csv")
    parser.add_argument("--thrust", type=float, default=5.0)
    parser.add_argument("--tolerance", type=float, default=0.1)
    parser.add_argument("--u-values", default="0,0.01,0.02,0.0226,0.03,0.05")
    parser.add_argument("--output", default="data/processed/uq_sensitivity_v0.1.csv")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        runs = mp.load_runs(Path(args.input))
        u_values = tuple(float(x) for x in args.u_values.split(",") if x.strip())
        rows = run_sensitivity(
            runs,
            thrust_required_n=args.thrust,
            thrust_tolerance=args.tolerance,
            u_values=u_values,
        )
        out = write_csv(rows, args.output, overwrite=args.overwrite)
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        print(f"错误：{exc}")
        return 2

    print(f"U(k=2) 敏感性（{len(rows)} 个取值，需求推力 {args.thrust:g} N）：")
    for row in rows:
        print(
            f"  U={row['u_k2']:.4g}｜knee {row['knee_voltage_set_v']:g} V / {row['knee_throttle_set_pct']:.1f}%"
            f"｜η_cons(2σ)={row['knee_eta_cons_2sigma']:.4f}"
        )
    print(f"报告：{out}")
    print("注意：" + DATA_NOTE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
