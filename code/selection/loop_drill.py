"""补测闭环演练 v0.1：SIM 重采样，量化"补测后地图变好多少"。

流程：确定性留出 → 训练 GP → batch_plan 选 5 点 → 用"真实面 + 噪声"模拟测量 →
并入后重拟合 → 比较留出 RMSE。仅用于方法学验证（SIM），不产生真实数据。
"""
from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

import numpy as np

import batch_plan as bp
import gp_surface as gp

SCHEMA_VERSION = "0.1"
DATA_NOTE = "SIM 闭环演练：补测点由代理模型模拟，不是实测数据，不构成实验结果"


def _eta(row: dict) -> float:
    for key in ("eta_sys_mean", "eta_sys"):
        if key in row and row[key] not in ("", None):
            return float(row[key])
    raise ValueError("runs 行缺少 eta_sys_mean/eta_sys 列")


def fit_model(rows: list[dict]) -> tuple[gp.GPFit, dict]:
    x = gp.features_of(rows)
    y = np.array([_eta(r) for r in rows], dtype=float)
    best = gp.choose_length_scale(x, y)
    return gp.GPFit(x, y, length_scale=best["length_scale"]), best


def predict_one(model: gp.GPFit, row: dict) -> tuple[float, float]:
    x = gp.features_of([row])
    mean, var = model.predict(x)
    mean_arr = np.atleast_1d(np.asarray(mean, dtype=float))
    var_arr = np.atleast_1d(np.asarray(var, dtype=float))
    return float(mean_arr[0]), float(var_arr[0])


def rmse_on(model: gp.GPFit, rows: list[dict]) -> float:
    errs = [predict_one(model, row)[0] - _eta(row) for row in rows]
    return float(math.sqrt(sum(e * e for e in errs) / len(errs)))


def split_holdout(rows: list[dict], every: int = 4) -> tuple[list[dict], list[dict]]:
    if every < 2:
        raise ValueError("holdout_every 必须 ≥ 2")
    test = [r for i, r in enumerate(rows) if i % every == every - 1]
    train = [r for i, r in enumerate(rows) if i % every != every - 1]
    if len(test) < 2 or len(train) < 6:
        raise ValueError("数据不足：至少需要 6 训练点 + 2 留出点")
    return train, test


def run_drill(
    rows: list[dict],
    *,
    holdout_every: int = 4,
    n: int = 5,
    seed: int = 20261123,
    noise_std: float = 0.002,
    u_k2: float = 0.0226,
) -> dict:
    if noise_std < 0:
        raise ValueError("noise_std 必须 ≥ 0")
    train, test = split_holdout(rows, holdout_every)
    before_model, before_fit = fit_model(train)
    before_rmse = rmse_on(before_model, test)

    plan = bp.build_plan(train, n=n, u_k2=u_k2)
    truth_model, _ = fit_model(rows)
    rng = random.Random(seed)
    measured = []
    for row in plan:
        mean, _ = predict_one(truth_model, row)
        value = mean + rng.gauss(0.0, noise_std)
        measured.append(
            {
                "voltage_set_v": row["voltage_set_v"],
                "throttle_set_pct": row["throttle_set_pct"],
                "eta_sys": value,
            }
        )

    augmented = train + measured
    after_model, after_fit = fit_model(augmented)
    after_rmse = rmse_on(after_model, test)
    improvement = (before_rmse - after_rmse) / before_rmse * 100.0 if before_rmse > 0 else 0.0

    return {
        "schema_version": SCHEMA_VERSION,
        "data_note": DATA_NOTE,
        "n_train": len(train),
        "n_holdout": len(test),
        "n_planned": len(plan),
        "holdout_every": holdout_every,
        "before_rmse": before_rmse,
        "after_rmse": after_rmse,
        "improvement_pct": improvement,
        "before_length_scale": before_fit["length_scale"],
        "after_length_scale": after_fit["length_scale"],
        "seed": seed,
        "noise_std": noise_std,
        "planned": plan,
        "measured_sim": measured,
    }


def write_outputs(result: dict, *, json_path: Path | str, csv_path: Path | str, overwrite: bool = False) -> tuple[Path, Path]:
    jp, cp = Path(json_path), Path(csv_path)
    for p in (jp, cp):
        if p.exists() and not overwrite:
            raise FileExistsError(f"输出已存在：{p}（加 --overwrite 覆盖）")
    jp.parent.mkdir(parents=True, exist_ok=True)
    jp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with cp.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["rank", "voltage_set_v", "throttle_set_pct", "predicted_eta", "gp_std_eta", "sigma_total", "data_note"],
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in result["planned"]:
            writer.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in row.items()})
    return jp, cp


def load_runs(path: Path | str) -> list[dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="SIM 补测闭环演练（D057）")
    parser.add_argument("--runs", default="data/processed/efficiency_map_runs.csv")
    parser.add_argument("--holdout-every", type=int, default=4)
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261123)
    parser.add_argument("--noise-std", type=float, default=0.002)
    parser.add_argument("--u-k2", type=float, default=0.0226)
    parser.add_argument("--output-json", default="data/processed/loop_drill_v0.1.json")
    parser.add_argument("--output-csv", default="data/processed/loop_drill_plan_v0.1.csv")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        rows = load_runs(args.runs)
        result = run_drill(
            rows,
            holdout_every=args.holdout_every,
            n=args.n,
            seed=args.seed,
            noise_std=args.noise_std,
            u_k2=args.u_k2,
        )
        jp, cp = write_outputs(result, json_path=args.output_json, csv_path=args.output_csv, overwrite=args.overwrite)
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        print(f"错误：{exc}")
        return 2

    print(
        f"闭环演练：训练 {result['n_train']} 点 / 留出 {result['n_holdout']} 点 / 计划 {result['n_planned']} 点\n"
        f"  留出 RMSE：{result['before_rmse']:.6f} → {result['after_rmse']:.6f}"
        f"（改善 {result['improvement_pct']:.1f}%）\n"
        f"  核宽：{result['before_length_scale']:.2f} → {result['after_length_scale']:.2f}"
    )
    print(f"JSON：{jp}\n计划：{cp}")
    print("注意：" + DATA_NOTE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
