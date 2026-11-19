"""效率地图 v0.4：GP（高斯过程）平滑代理与交叉验证。

在效率地图 runs CSV（电压 × 油门 × η_sys）上拟合 RBF 核高斯过程：
    k(x, x') = σ_f² · exp(-||x - x'||² / (2ℓ²)) + σ_n²·δ
输入特征按固定尺度归一化：x = (V / 30, throttle / 100)。
输出：网格预测均值/标准差 CSV（`*_surface_v0.4.csv`）+ 双面板图（均值/标准差）。

边界：仅用于 SIM 效率地图的平滑/补测建议与趋势查看，不产生实验结论。
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PYLIBS = PROJECT_ROOT / "work" / "pylibs"
if str(_PYLIBS) not in sys.path:
    sys.path.insert(0, str(_PYLIBS))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

VOLTAGE_SCALE = 30.0
THROTTLE_SCALE = 100.0
DEFAULT_SIGNAL_VAR = 1.0
DEFAULT_NOISE_VAR = 1e-5
MIN_POINTS = 3
LENGTH_SCALES = tuple(round(0.05 + 0.05 * i, 3) for i in range(20))  # 0.05 … 1.00
REQUIRED_COLUMNS = ("voltage_set_v", "throttle_set_pct")
ETA_FIELD_CANDIDATES = ("eta_sys_mean", "eta_sys")
GRID_FIELDS = ("voltage_set_v", "throttle_set_pct", "eta_pred", "eta_std", "data_note")
DATA_NOTE = "GP 平滑代理（SIM/参考运行数据）：预测值仅供参考，不是实验结果"


def load_runs(path: Path | str, *, eta_field: str | None = None) -> list[dict]:
    """读取 runs CSV（兼容 aggregate 的 `eta_sys_mean` 与简写 `eta_sys`）。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"输入不存在：{path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in fields]
        if missing:
            raise ValueError(f"缺少必需列：{missing}")
        if eta_field is None:
            for candidate in ETA_FIELD_CANDIDATES:
                if candidate in fields:
                    eta_field = candidate
                    break
            else:
                raise ValueError(f"缺少 η_sys 列（需要以下之一：{ETA_FIELD_CANDIDATES}）")
        elif eta_field not in fields:
            raise ValueError(f"指定的 η 列不存在：{eta_field}")
        rows: list[dict] = []
        for raw in reader:
            try:
                voltage = float(raw["voltage_set_v"])
                throttle = float(raw["throttle_set_pct"])
                eta = float(raw[eta_field])
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "voltage_set_v": voltage,
                    "throttle_set_pct": throttle,
                    "eta_sys": eta,
                    "run_id": (raw.get("run_id") or "").strip(),
                    "source": (raw.get("source") or "").strip(),
                }
            )
    if len(rows) < MIN_POINTS:
        raise ValueError(f"有效数据点不足（需要 ≥{MIN_POINTS}，实际 {len(rows)}）")
    return rows


def features_of(runs: list[dict]) -> np.ndarray:
    voltage = np.asarray([r["voltage_set_v"] for r in runs], dtype=float)
    throttle = np.asarray([r["throttle_set_pct"] for r in runs], dtype=float)
    return np.column_stack([voltage / VOLTAGE_SCALE, throttle / THROTTLE_SCALE])


def rbf_kernel(x1: np.ndarray, x2: np.ndarray, length_scale: float, signal_var: float = DEFAULT_SIGNAL_VAR) -> np.ndarray:
    if length_scale <= 0:
        raise ValueError("length_scale 必须 > 0")
    sqdist = np.sum((x1[:, None, :] - x2[None, :, :]) ** 2, axis=-1)
    return signal_var * np.exp(-0.5 * sqdist / (length_scale**2))


@dataclass
class GPFit:
    x: np.ndarray
    y: np.ndarray
    length_scale: float
    noise_var: float = DEFAULT_NOISE_VAR
    signal_var: float = DEFAULT_SIGNAL_VAR
    chol: np.ndarray = field(init=False, repr=False)
    alpha: np.ndarray = field(init=False, repr=False)
    y_mean: float = field(init=False)

    def __post_init__(self) -> None:
        n = len(self.y)
        kernel = rbf_kernel(self.x, self.x, self.length_scale, self.signal_var)
        self.chol = np.linalg.cholesky(kernel + self.noise_var * np.eye(n))
        self.y_mean = float(np.mean(self.y))
        centered = self.y - self.y_mean
        self.alpha = np.linalg.solve(self.chol.T, np.linalg.solve(self.chol, centered))

    def predict(self, x_star: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        cross = rbf_kernel(x_star, self.x, self.length_scale, self.signal_var)
        mean = cross @ self.alpha + self.y_mean
        solved = np.linalg.solve(self.chol, cross.T)
        var = self.signal_var - np.sum(solved**2, axis=0)
        return mean, np.clip(var, 1e-12, None)

    def loocv(self) -> tuple[np.ndarray, np.ndarray]:
        """留一交叉验证（利用 K^-1 对角元的闭式解）。"""
        n = len(self.y)
        inv_chol = np.linalg.solve(self.chol, np.eye(n))
        kernel_inv = inv_chol.T @ inv_chol
        diag = np.diag(kernel_inv)
        loo_mean = self.y_mean + (self.y - self.y_mean) - self.alpha / diag
        loo_var = 1.0 / diag
        return loo_mean, loo_var


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if y_true.shape != y_pred.shape:
        raise ValueError("y_true 与 y_pred 形状不一致")
    residuals = y_true - y_pred
    rmse = float(np.sqrt(np.mean(residuals**2)))
    denom = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float("nan") if denom <= 0 else 1.0 - float(np.sum(residuals**2)) / denom
    return {"n": int(len(y_true)), "rmse": rmse, "r2": r2}


def choose_length_scale(x: np.ndarray, y: np.ndarray, candidates: tuple[float, ...] = LENGTH_SCALES) -> dict:
    """在候选长度尺度上做 LOOCV，取 RMSE 最小者（并列取较小 ℓ）。"""
    best: dict | None = None
    for length_scale in candidates:
        gp = GPFit(x, y, length_scale=length_scale)
        loo_mean, _ = gp.loocv()
        rmse = float(np.sqrt(np.mean((y - loo_mean) ** 2)))
        candidate = {"length_scale": float(length_scale), "loocv_rmse": rmse}
        if best is None or (rmse, length_scale) < (best["loocv_rmse"], best["length_scale"]):
            best = candidate
    assert best is not None
    gp = GPFit(x, y, length_scale=best["length_scale"])
    loo_mean, _ = gp.loocv()
    best.update(regression_metrics(y, loo_mean))
    return best


def predict_grid(gp: GPFit, voltages: list[float], throttles: list[float]) -> list[dict]:
    points = [(v, t) for v in voltages for t in throttles]
    x_star = np.asarray([[v / VOLTAGE_SCALE, t / THROTTLE_SCALE] for v, t in points], dtype=float)
    mean, var = gp.predict(x_star)
    rows: list[dict] = []
    for (v, t), mu, sigma2 in zip(points, mean, var):
        rows.append(
            {
                "voltage_set_v": float(v),
                "throttle_set_pct": float(t),
                "eta_pred": float(mu),
                "eta_std": float(math.sqrt(max(sigma2, 0.0))),
                "data_note": DATA_NOTE,
            }
        )
    return rows


def write_csv(rows: list[dict], output: Path | str, *, overwrite: bool = False) -> Path:
    output = Path(output)
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{output}（加 --overwrite 覆盖）")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GRID_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output


def plot_surface(
    runs: list[dict],
    grid_rows: list[dict],
    output_png: Path | str,
    *,
    title: str = "Efficiency surface v0.4 (GP surrogate)",
    overwrite: bool = False,
) -> Path:
    output_png = Path(output_png)
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{output_png}（加 --overwrite 覆盖）")
    output_png.parent.mkdir(parents=True, exist_ok=True)

    voltages = sorted({row["voltage_set_v"] for row in grid_rows})
    throttles = sorted({row["throttle_set_pct"] for row in grid_rows})
    v_index = {v: i for i, v in enumerate(voltages)}
    t_index = {t: i for i, t in enumerate(throttles)}
    mean_grid = np.full((len(throttles), len(voltages)), np.nan)
    std_grid = np.full_like(mean_grid, np.nan)
    for row in grid_rows:
        mean_grid[t_index[row["throttle_set_pct"]], v_index[row["voltage_set_v"]]] = row["eta_pred"]
        std_grid[t_index[row["throttle_set_pct"]], v_index[row["voltage_set_v"]]] = row["eta_std"]

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    extent = [min(voltages), max(voltages), min(throttles), max(throttles)]
    obs_v = [r["voltage_set_v"] for r in runs]
    obs_t = [r["throttle_set_pct"] for r in runs]

    image_mean = axes[0].imshow(
        mean_grid, origin="lower", aspect="auto", extent=extent, cmap="viridis", interpolation="nearest"
    )
    axes[0].scatter(obs_v, obs_t, c="white", edgecolors="black", s=28, label="observed (runs CSV)", zorder=3)
    axes[0].set_title("Predicted η_sys (GP mean)")
    axes[0].set_xlabel("Bus voltage (V)")
    axes[0].set_ylabel("Throttle command (%)")
    axes[0].legend(loc="lower right", fontsize=8)
    fig.colorbar(image_mean, ax=axes[0], label="η_sys (predicted)")

    image_std = axes[1].imshow(
        std_grid, origin="lower", aspect="auto", extent=extent, cmap="magma", interpolation="nearest"
    )
    axes[1].scatter(obs_v, obs_t, c="white", edgecolors="black", s=28, label="observed (runs CSV)", zorder=3)
    axes[1].set_title("GP predictive std (1σ)")
    axes[1].set_xlabel("Bus voltage (V)")
    axes[1].set_ylabel("Throttle command (%)")
    axes[1].legend(loc="lower right", fontsize=8)
    fig.colorbar(image_std, ax=axes[1], label="η_sys std")

    fig.suptitle(title)
    fig.text(0.5, 0.015, "SIM/REFERENCE DATA — NOT EXPERIMENTAL", ha="center", color="crimson", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(output_png, dpi=150)
    plt.close(fig)
    return output_png


def _grid_ticks(values: list[float], n: int = 21) -> list[float]:
    unique = sorted(set(values))
    if len(unique) >= 2:
        low, high = unique[0], unique[-1]
    else:
        low = max(0.0, unique[0] * 0.8)
        high = unique[0] * 1.2
    return [round(low + (high - low) * i / (n - 1), 4) for i in range(n)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="效率地图 v0.4：GP 平滑代理与交叉验证")
    parser.add_argument("--input", type=Path, default=Path("data/processed/efficiency_map_runs.csv"))
    parser.add_argument("--output-csv", type=Path, default=Path("data/processed/efficiency_map_surface_v0.4.csv"))
    parser.add_argument("--figure", type=Path, default=Path("data/processed/figures/efficiency_map_v0.4.png"))
    parser.add_argument("--length-scale", type=float, default=None, help="固定核长度尺度；缺省用 LOOCV 网格搜索")
    parser.add_argument("--no-optimize", action="store_true", help="使用默认长度尺度 0.25（不搜索）")
    parser.add_argument("--grid", type=int, default=21, help="每个轴网格点数")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        runs = load_runs(args.input)
        x = features_of(runs)
        y = np.asarray([r["eta_sys"] for r in runs], dtype=float)
        if args.length_scale is not None:
            length_scale = args.length_scale
            gp = GPFit(x, y, length_scale=length_scale)
            loo_mean, _ = gp.loocv()
            cv = {"length_scale": length_scale, **regression_metrics(y, loo_mean)}
        elif args.no_optimize:
            length_scale = 0.25
            gp = GPFit(x, y, length_scale=length_scale)
            loo_mean, _ = gp.loocv()
            cv = {"length_scale": length_scale, **regression_metrics(y, loo_mean)}
        else:
            cv = choose_length_scale(x, y)
            length_scale = cv["length_scale"]
            gp = GPFit(x, y, length_scale=length_scale)

        voltages = _grid_ticks([r["voltage_set_v"] for r in runs], args.grid)
        throttles = _grid_ticks([r["throttle_set_pct"] for r in runs], args.grid)
        grid_rows = predict_grid(gp, voltages, throttles)
        write_csv(grid_rows, args.output_csv, overwrite=args.overwrite)
        plot_surface(runs, grid_rows, args.figure, overwrite=args.overwrite)
    except (FileNotFoundError, ValueError, FileExistsError) as exc:
        print(f"错误：{exc}")
        return 2

    print(f"输入：{args.input}（{len(runs)} 点）")
    print(f"核长度尺度 ℓ={cv['length_scale']:.3f}；LOOCV RMSE={cv['rmse']:.6f}，R²={cv['r2']:.4f}")
    print(f"网格：{len(voltages)}×{len(throttles)}={len(grid_rows)} 点 → {args.output_csv}")
    print(f"图件：{args.figure}")
    print("注意：预测为 GP 平滑代理，仅供趋势/补测建议，不是实验结果。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
