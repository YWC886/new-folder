"""补测批次计划 v0.1：把效率地图的 GP σ 补测建议转成可执行计划表（D056 口径）。

只生成计划，不产生数据；优先补测 "σ_total 最大" 的点（σ_total = sqrt(u_meas² + σ_gp²)）。
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import bo_suggest as bs

SCHEMA_VERSION = "0.1"
DATA_NOTE = "SIM 补测计划：由 GP 代理标准差与 D056 口径生成，仅用于安排台架测量，不是实验结果"
BATCH_FIELDS = [
    "rank",
    "voltage_set_v",
    "throttle_set_pct",
    "predicted_eta",
    "gp_std_eta",
    "u_meas",
    "sigma_total",
    "priority",
    "est_duration_s",
    "data_note",
]


def build_plan(
    runs: list[dict],
    *,
    n: int = 5,
    strategy: str = "sigma",
    min_distance: float = 0.12,
    u_k2: float = 0.0226,
    duration_s: float = 30.0,
) -> list[dict]:
    """返回按 priority（σ_total 降序）排列的补测计划行。"""
    if n < 1:
        raise ValueError("n 必须 ≥ 1")
    if duration_s <= 0:
        raise ValueError("est_duration_s 必须 > 0")
    if u_k2 < 0:
        raise ValueError("u_k2 必须 ≥ 0")
    u_meas = u_k2 / 2.0
    suggestions = bs.suggest(
        runs, n=n, strategy=strategy, min_distance=min_distance
    )
    rows = []
    for entry in suggestions:
        sigma_gp = float(entry["gp_std_eta"])
        sigma_total = math.sqrt(u_meas ** 2 + sigma_gp ** 2)
        rows.append(
            {
                "rank": 0,
                "voltage_set_v": float(entry["voltage_set_v"]),
                "throttle_set_pct": float(entry["throttle_set_pct"]),
                "predicted_eta": float(entry["gp_mean_eta"]),
                "gp_std_eta": sigma_gp,
                "u_meas": u_meas,
                "sigma_total": sigma_total,
                "priority": sigma_total,
                "est_duration_s": float(duration_s),
                "data_note": DATA_NOTE,
            }
        )
    rows.sort(key=lambda r: -r["priority"])
    for i, row in enumerate(rows, 1):
        row["rank"] = i
    return rows


def write_csv(rows: list[dict], path: Path | str, *, overwrite: bool = False) -> Path:
    out = Path(path)
    if out.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{out}（加 --overwrite 覆盖）")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=BATCH_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in row.items()})
    return out


def load_runs(path: Path | str) -> list[dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        rows = [dict(r) for r in csv.DictReader(fh)]
    if len(rows) < 4:
        raise ValueError("runs 数据不足 4 行，无法拟合 GP")
    return rows


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="生成补测批次计划（D056）")
    parser.add_argument("--runs", default="data/processed/efficiency_map_runs.csv")
    parser.add_argument("--output", default="data/processed/next_batch_plan_v0.1.csv")
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--strategy", default="sigma", choices=["sigma", "ei", "random"])
    parser.add_argument("--min-distance", type=float, default=0.12)
    parser.add_argument("--u-k2", type=float, default=0.0226)
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        runs = load_runs(args.runs)
        rows = build_plan(
            runs,
            n=args.n,
            strategy=args.strategy,
            min_distance=args.min_distance,
            u_k2=args.u_k2,
            duration_s=args.duration,
        )
        out = write_csv(rows, args.output, overwrite=args.overwrite)
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        print(f"错误：{exc}")
        return 2

    print(f"补测计划（{len(rows)} 点，U(k=2)={args.u_k2:g}，单点 {args.duration:g} s）：")
    for row in rows:
        print(
            f"  #{row['rank']} {row['voltage_set_v']:g} V / {row['throttle_set_pct']:.1f}%"
            f"｜预测 η={row['predicted_eta']:.4f}｜σ_gp={row['gp_std_eta']:.4f}"
            f"｜σ_total={row['sigma_total']:.4f}"
        )
    print(f"计划表：{out}")
    print("注意：" + DATA_NOTE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
