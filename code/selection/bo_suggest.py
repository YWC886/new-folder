"""选型补测策略对比 v0.1（Round 19）。

目的：把"下一个该测哪个工况"从单一的 σ 贪心扩展为可对比的策略集合，并用
「留出 + 模拟补测」的闭环实验量化各策略的地图精度收益与最优值搜索收益。

策略：
- ``sigma``  ：选择预测标准差最大且与已测/已选点保持最小距离的候选（全局不确定度最大处）；
- ``ei``     ：选择 Expected Improvement 最大处（目标 = 最大化 η_sys，ξ 控制探索强度）；
- ``random`` ：在合法候选内按固定种子随机选点（基线）。

重要边界：
- 全部基于 SIM/REFERENCE 数据与 GP 代理，不是实验结果，也不是选型结论；
- EI 的 improvement 是 GP 代理上的期望，不是真实测量收益；
- 闭环模拟中的"新测量值"来自全数据 GP 的预测均值（可加固定噪声），仅用于方法学对比。
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "work" / "pylibs", ROOT / "code" / "processing", ROOT / "code" / "selection"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np  # noqa: E402

import gp_surface as gp  # noqa: E402
import match_propulsion as mp  # noqa: E402

SCHEMA_VERSION = "0.1"
STRATEGIES = ("none", "sigma", "ei", "random")
SUGGEST_STRATEGIES = ("sigma", "ei", "random")
DATA_NOTE = "SIM 补测策略对比：GP 代理闭环模拟，仅供方法学参考，不是实验结果"
VOLTAGE_SCALE = gp.VOLTAGE_SCALE
THROTTLE_SCALE = gp.THROTTLE_SCALE

METRIC_FIELDS = (
    "strategy",
    "rounds",
    "grid_rmse_mean",
    "grid_rmse_std",
    "holdout_rmse_mean",
    "holdout_rmse_std",
    "best_eta_gap_mean",
    "best_eta_gap_std",
    "data_note",
)
SUGGEST_FIELDS = (
    "rank",
    "strategy",
    "voltage_set_v",
    "throttle_set_pct",
    "gp_mean_eta",
    "gp_std_eta",
    "score",
    "min_distance",
    "data_note",
)


def _eta(run: dict) -> float:
    """兼容 aggregate 的 eta_sys_mean 与简化 runs 的 eta_sys。"""

    for key in ("eta_sys_mean", "eta_sys"):
        value = run.get(key)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    raise ValueError("runs 缺少 eta_sys_mean / eta_sys 列")


def _features(runs: list[dict]) -> np.ndarray:
    return gp.features_of(runs)


def fit_eta(runs: list[dict]) -> dict:
    """拟合 η_sys 的 RBF-GP，返回 {gpfit, length_scale, loocv}。"""

    x = _features(runs)
    y = np.array([_eta(run) for run in runs], dtype=float)
    choice = gp.choose_length_scale(x, y)
    fit = gp.GPFit(x=x, y=y, length_scale=float(choice["length_scale"]))
    return {"gpfit": fit, "length_scale": float(choice["length_scale"]), "loocv": dict(choice)}


def expected_improvement(gpfit, x: np.ndarray, *, best: float, xi: float = 0.01) -> np.ndarray:
    """最大化目标的 Expected Improvement（高斯闭式）。"""

    mean, var = gpfit.predict(x)
    std = np.sqrt(np.asarray(var, dtype=float))
    std_safe = np.maximum(std, 1e-12)
    z = (mean - best - xi) / std_safe
    cdf = 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))
    pdf = np.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)
    return np.maximum((mean - best - xi) * cdf + std_safe * pdf, 0.0)


def _candidate_rows(runs: list[dict], *, voltage_points: int, throttle_points: int) -> list[dict]:
    voltages = mo_voltage_grid(runs, voltage_points)
    throttles = mo_throttle_grid(runs, throttle_points)
    rows = []
    for voltage in voltages:
        for throttle in throttles:
            rows.append({"voltage_set_v": float(voltage), "throttle_set_pct": float(throttle)})
    return rows


def mo_voltage_grid(runs: list[dict], points: int) -> np.ndarray:
    values = sorted({float(run["voltage_set_v"]) for run in runs})
    return np.linspace(min(values), max(values), points)


def mo_throttle_grid(runs: list[dict], points: int) -> np.ndarray:
    values = sorted({float(run["throttle_set_pct"]) for run in runs})
    return np.linspace(min(values), max(values), points)


def _min_distance(feature_row: np.ndarray, reference_features: np.ndarray) -> float:
    if len(reference_features) == 0:
        return float("inf")
    distances = np.sqrt(np.sum((reference_features - feature_row) ** 2, axis=1))
    return float(np.min(distances))


def suggest(
    runs: list[dict],
    *,
    n: int = 5,
    strategy: str = "sigma",
    min_distance: float = 0.12,
    voltage_points: int = 13,
    throttle_points: int = 41,
    xi: float = 0.01,
    seed: int = 20261119,
) -> list[dict]:
    """按指定策略给出 n 个补测建议（遵守与已测点的最小归一化距离）。"""

    if strategy not in SUGGEST_STRATEGIES:
        raise ValueError(f"未知策略：{strategy}（候选：{', '.join(SUGGEST_STRATEGIES)}）")
    if n < 1:
        raise ValueError("n 必须 ≥1")
    if not runs:
        raise ValueError("runs 不能为空")

    fitted = fit_eta(runs)
    gpfit = fitted["gpfit"]
    reference = _features(runs)
    best = float(np.max(gpfit.y)) if hasattr(gpfit, "y") else float(np.max([_eta(run) for run in runs]))

    candidates = _candidate_rows(runs, voltage_points=voltage_points, throttle_points=throttle_points)
    x_candidates = gp.features_of(candidates)
    mean, var = gpfit.predict(x_candidates)
    std = np.sqrt(np.asarray(var, dtype=float))

    if strategy == "sigma":
        score = std
    elif strategy == "ei":
        score = expected_improvement(gpfit, x_candidates, best=best, xi=xi)
    else:
        rng = np.random.default_rng(seed)
        score = rng.random(len(candidates))

    available = np.ones(len(candidates), dtype=bool)
    selected: list[int] = []
    for _ in range(n):
        chosen = -1
        best_score = -float("inf")
        for index in range(len(candidates)):
            if not available[index]:
                continue
            distance = _min_distance(x_candidates[index], reference)
            if distance < min_distance:
                continue
            candidate_score = float(score[index]) + 1e-9 * distance
            if candidate_score > best_score:
                best_score = candidate_score
                chosen = index
        if chosen < 0:
            break
        available[chosen] = False
        selected.append(chosen)
        reference = np.vstack([reference, x_candidates[chosen]])

    rows = []
    for rank, index in enumerate(selected, start=1):
        candidate = candidates[index]
        rows.append(
            {
                "rank": rank,
                "strategy": strategy,
                "voltage_set_v": round(float(candidate["voltage_set_v"]), 4),
                "throttle_set_pct": round(float(candidate["throttle_set_pct"]), 4),
                "gp_mean_eta": round(float(mean[index]), 6),
                "gp_std_eta": round(float(std[index]), 6),
                "score": round(float(score[index]), 8),
                "min_distance": round(_min_distance(x_candidates[index], _features(runs)), 4),
                "data_note": DATA_NOTE,
            }
        )
    return rows


def _fit_with(fit: dict, extra_rows: list[dict], extra_eta: list[float]) -> dict:
    """在已有观测上追加模拟测量点后重新拟合。"""

    x = np.vstack([fit["gpfit"].x, gp.features_of(extra_rows)])
    y = np.concatenate([fit["gpfit"].y, np.asarray(extra_eta, dtype=float)])
    choice = gp.choose_length_scale(x, y)
    return {"gpfit": gp.GPFit(x=x, y=y, length_scale=float(choice["length_scale"])), "loocv": dict(choice)}


def simulate_strategy(
    runs: list[dict],
    *,
    strategy: str,
    n: int = 5,
    rounds: int = 3,
    holdout: int = 4,
    voltage_points: int = 13,
    throttle_points: int = 41,
    min_distance: float = 0.12,
    xi: float = 0.01,
    seed: int = 20261119,
    noise_std: float = 0.002,
) -> dict:
    """闭环模拟：全数据 GP 充当"真实面"，留出部分实测点，补测 n 点后比较精度。"""

    if strategy not in STRATEGIES:
        raise ValueError(f"未知策略：{strategy}（候选：{', '.join(STRATEGIES)}）")
    if rounds < 1:
        raise ValueError("rounds 必须 ≥1")
    if holdout < 1 or holdout >= len(runs) - 3:
        raise ValueError("holdout 超出可用范围")

    truth = fit_eta(runs)["gpfit"]
    voltages = mo_voltage_grid(runs, voltage_points)
    throttles = mo_throttle_grid(runs, throttle_points)
    grid = [{"voltage_set_v": float(v), "throttle_set_pct": float(t)} for v in voltages for t in throttles]
    truth_grid, _ = truth.predict(gp.features_of(grid))
    rng = np.random.default_rng(seed)

    grid_rmse: list[float] = []
    holdout_rmse: list[float] = []
    best_gap: list[float] = []
    for _ in range(rounds):
        order = rng.permutation(len(runs))
        held = [runs[int(i)] for i in order[:holdout]]
        train = [runs[int(i)] for i in order[holdout:]]
        model = fit_eta(train)
        if strategy == "none":
            suggestions: list[dict] = []
        else:
            suggestions = suggest(
                train,
                n=n,
                strategy=strategy,
                min_distance=min_distance,
                voltage_points=voltage_points,
                throttle_points=throttle_points,
                xi=xi,
                seed=int(rng.integers(0, 2**31 - 1)),
            )
        sim_rows = [{"voltage_set_v": s["voltage_set_v"], "throttle_set_pct": s["throttle_set_pct"]} for s in suggestions]
        sim_eta, _ = truth.predict(gp.features_of(sim_rows))
        sim_eta = np.asarray(sim_eta, dtype=float) + rng.normal(0.0, noise_std, size=len(sim_rows))
        refit = _fit_with(model, sim_rows, [float(v) for v in sim_eta])
        pred_grid, _ = refit["gpfit"].predict(gp.features_of(grid))
        grid_rmse.append(float(np.sqrt(np.mean((pred_grid - truth_grid) ** 2))))
        pred_held, _ = refit["gpfit"].predict(gp.features_of(held))
        holdout_rmse.append(float(np.sqrt(np.mean((pred_held - np.asarray([_eta(r) for r in held])) ** 2))))
        best_gap.append(float(np.max(truth_grid) - np.max(pred_grid)))

    return {
        "strategy": strategy,
        "rounds": rounds,
        "grid_rmse": grid_rmse,
        "holdout_rmse": holdout_rmse,
        "best_gap": best_gap,
    }


def summarize(results: list[dict]) -> list[dict]:
    rows = []
    for result in results:
        rows.append(
            {
                "strategy": result["strategy"],
                "rounds": result["rounds"],
                "grid_rmse_mean": round(float(np.mean(result["grid_rmse"])), 8),
                "grid_rmse_std": round(float(np.std(result["grid_rmse"], ddof=1)) if result["rounds"] > 1 else 0.0, 8),
                "holdout_rmse_mean": round(float(np.mean(result["holdout_rmse"])), 8),
                "holdout_rmse_std": round(float(np.std(result["holdout_rmse"], ddof=1)) if result["rounds"] > 1 else 0.0, 8),
                "best_eta_gap_mean": round(float(np.mean(result["best_gap"])), 8),
                "best_eta_gap_std": round(float(np.std(result["best_gap"], ddof=1)) if result["rounds"] > 1 else 0.0, 8),
                "data_note": DATA_NOTE,
            }
        )
    return rows


def write_csv(rows: list[dict], path: Path, *, fields: tuple[str, ...], overwrite: bool = False) -> Path:
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{path}（如需覆盖加 --overwrite）")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _import_pyplot():
    plt = None
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"绘图需要 matplotlib（work/pylibs）：{exc}") from exc
    return plt


def plot_summary(rows: list[dict], path: Path, *, overwrite: bool = False) -> Path:
    for row in rows:
        if not row.get("data_note", "").startswith("SIM"):
            raise ValueError("图件只接受 SIM 标注数据")
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{path}（如需覆盖加 --overwrite）")
    path.parent.mkdir(parents=True, exist_ok=True)
    plt = _import_pyplot()
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6))
    strategies = [row["strategy"] for row in rows]
    grid_mean = [row["grid_rmse_mean"] * 1000 for row in rows]
    grid_std = [row["grid_rmse_std"] * 1000 for row in rows]
    gap_mean = [row["best_eta_gap_mean"] * 1000 for row in rows]
    gap_std = [row["best_eta_gap_std"] * 1000 for row in rows]
    axes[0].bar(strategies, grid_mean, yerr=grid_std, color="#4C72B0", capsize=4)
    axes[0].set_ylabel("grid RMSE vs truth [×10⁻³ η]")
    axes[0].set_title("Map accuracy after suggested batch")
    axes[1].bar(strategies, gap_mean, yerr=gap_std, color="#DD8452", capsize=4)
    axes[1].set_ylabel("best-η gap [×10⁻³ η]")
    axes[1].set_title("Best-value tracking gap")
    fig.suptitle("Selection v0.5 — suggested-measurement strategies (SIM, simulated loop)")
    fig.text(0.5, 0.015, "SIMULATED DATA — NOT EXPERIMENTAL", ha="center", color="crimson", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0.05, 1, 0.93))
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def run_comparison(
    runs: list[dict],
    *,
    rounds: int = 3,
    n: int = 5,
    holdout: int = 4,
    seed: int = 20261119,
) -> list[dict]:
    results = []
    for index, strategy in enumerate(("none",) + SUGGEST_STRATEGIES):
        results.append(
            simulate_strategy(
                runs,
                strategy=strategy,
                n=n,
                rounds=rounds,
                holdout=holdout,
                seed=seed + 17 * index,
            )
        )
    return summarize(results)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="补测策略对比（SIM 闭环模拟；不是实验结果）")
    parser.add_argument("--input", default="data/processed/efficiency_map_runs.csv", help="runs CSV")
    parser.add_argument("--n", type=int, default=5, help="每轮补测点数")
    parser.add_argument("--rounds", type=int, default=3, help="模拟轮数")
    parser.add_argument("--holdout", type=int, default=4, help="每轮留出实测点数")
    parser.add_argument("--strategy", choices=STRATEGIES, help="只跑单个策略（默认三策略对比）")
    parser.add_argument("--seed", type=int, default=20261119)
    parser.add_argument("--output", default="data/processed/bo_strategies_v0.5.csv")
    parser.add_argument("--figure", default="data/processed/figures/bo_strategies_v0.5.png")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        runs = mp.load_runs(Path(args.input))
        if args.strategy:
            result = simulate_strategy(
                runs, strategy=args.strategy, n=args.n, rounds=args.rounds, holdout=args.holdout, seed=args.seed
            )
            rows = summarize([result])
        else:
            rows = run_comparison(runs, rounds=args.rounds, n=args.n, holdout=args.holdout, seed=args.seed)
        write_csv(rows, Path(args.output), fields=METRIC_FIELDS, overwrite=args.overwrite)
        plot_summary(rows, Path(args.figure), overwrite=args.overwrite)
    except (ValueError, FileExistsError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    print(f"策略对比：{len(rows)} 行 → {args.output}")
    for row in rows:
        print(
            f"  {row['strategy']}: grid RMSE {row['grid_rmse_mean']:.6f} ± {row['grid_rmse_std']:.6f}；"
            f"holdout RMSE {row['holdout_rmse_mean']:.6f}；best-η gap {row['best_eta_gap_mean']:.6f}"
        )
    print(f"图件：{args.figure}")
    print("注意：SIM 闭环模拟，仅供方法学对比，不是实验结果或选型结论。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
