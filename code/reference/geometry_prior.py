"""Geometry/Reynolds-featured propeller surrogate prior v0.1 (REFERENCE only).

目的：用 UIUC 公开静态数据（REFERENCE）拟合一个「几何 + 转速」特征的线性代理，
以留一桨型（leave-one-prop-out, LOPO）交叉验证评估其相对通用参数模型的改进。
边界：REFERENCE 数据样本内/样本外验证，不是本项目实测，不得写入 ModelParams 默认值（D042/D049）。
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (str(PROJECT_ROOT / "work" / "pylibs"), str(PROJECT_ROOT / "code" / "simulation")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402

import uiuc_propdb  # noqa: E402
from catalog_uiuc import DEFAULT_CATALOG_FILES, REFERENCE_DIR  # noqa: E402
from propulsion_model import ModelParams  # noqa: E402

SCHEMA_VERSION = "0.1"
DATA_NOTE = "REFERENCE 几何特征代理（UIUC 数据样本/留一桨型验证），非本项目实测，do_not_apply 语义参照 D042/D049"
OUT_FIELDS = (
    "prop", "brand", "series", "diameter_in", "pitch_in", "pitch_ratio",
    "points", "generic_ct_mae", "geo_ct_mae", "generic_cp_mae", "geo_cp_mae",
)


def _features(rows: list[dict], D_m: float, pitch_ratio: float) -> np.ndarray:
    """特征：[1, D, P/D, n_norm, n_norm^2]。"""
    out = []
    for r in rows:
        n_norm = r["n_rps"] / 100.0
        out.append([1.0, D_m, pitch_ratio, n_norm, n_norm * n_norm])
    return np.asarray(out, dtype=float)


def _stack(entries: list[dict], field: str) -> tuple[np.ndarray, np.ndarray]:
    """把多个桨型的点按各自几何特征堆叠。"""
    Xs, ys = [], []
    for e in entries:
        label = e["label"]
        D_m = float(label["diameter_in"]) * 0.0254
        pr = _pitch_ratio(label)
        Xs.append(_features(e["rows"], D_m, pr))
        ys.append(np.asarray([r[field] for r in e["rows"]], dtype=float))
    return np.vstack(Xs), np.concatenate(ys)


def fit_linear(entries: list[dict], field: str) -> np.ndarray:
    """在给定桨型集合上拟合线性代理（每点用其所属桨型的几何特征）。"""
    X, y = _stack(entries, field)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef


def predict(coef: np.ndarray, rows: list[dict], D_m: float, pitch_ratio: float) -> np.ndarray:
    return _features(rows, D_m, pitch_ratio) @ coef


def load_entries() -> list[dict]:
    entries = []
    for name in DEFAULT_CATALOG_FILES:
        path = REFERENCE_DIR / name
        if not path.exists():
            continue
        label = uiuc_propdb.parse_prop_label(path)
        rows = uiuc_propdb.load_static(path)
        entries.append({"label": label, "rows": rows})
    if len(entries) < 3:
        raise ValueError(f"桨型数量不足（{len(entries)}），至少需要 3 个")
    return entries


def generic_errors(label: dict, rows: list[dict], model: ModelParams) -> tuple[float, float]:
    ct_errs, cp_errs = [], []
    for r in rows:
        n_norm = r["n_rps"] / 100.0
        ct = model.ct0 * n_norm**model.reynolds_ct_exp
        cp = model.cp0 * n_norm**model.reynolds_cp_exp
        ct_errs.append(abs(ct - r["ct"]) / r["ct"])
        cp_errs.append(abs(cp - r["cp"]) / r["cp"])
    return float(np.mean(ct_errs)), float(np.mean(cp_errs))


def _pitch_ratio(label: dict) -> float:
    d = float(label["diameter_in"])
    return float(label["pitch_in"]) / d if d else 0.0


def _mae(pred: np.ndarray, rows: list[dict], field: str) -> float:
    ref = np.asarray([r[field] for r in rows], dtype=float)
    return float(np.mean(np.abs(pred - ref) / ref))


def lopo_benchmark(entries: list[dict], model: ModelParams | None = None) -> dict:
    """留一桨型：在其余桨型上拟合线性代理，预测被留出的桨型。"""
    model = model or ModelParams()
    out_rows = []
    for i, entry in enumerate(entries):
        label = entry["label"]
        D_m = float(label["diameter_in"]) * 0.0254
        pr = _pitch_ratio(label)
        train = [e for j, e in enumerate(entries) if j != i]
        coef_ct = fit_linear(train, "ct")
        coef_cp = fit_linear(train, "cp")
        rows = entry["rows"]
        geo_ct = _mae(predict(coef_ct, rows, D_m, pr), rows, "ct")
        geo_cp = _mae(predict(coef_cp, rows, D_m, pr), rows, "cp")
        g_ct, g_cp = generic_errors(label, rows, model)
        out_rows.append({
            "prop": label["prop"],
            "brand": label["brand"],
            "series": label["series_full"],
            "diameter_in": label["diameter_in"],
            "pitch_in": label["pitch_in"],
            "pitch_ratio": round(pr, 4),
            "points": len(rows),
            "generic_ct_mae": round(g_ct, 6),
            "geo_ct_mae": round(geo_ct, 6),
            "generic_cp_mae": round(g_cp, 6),
            "geo_cp_mae": round(geo_cp, 6),
        })
    pooled = {
        "points": sum(r["points"] for r in out_rows),
        "generic_ct_mae": round(float(np.mean([r["generic_ct_mae"] for r in out_rows])), 6),
        "geo_ct_mae": round(float(np.mean([r["geo_ct_mae"] for r in out_rows])), 6),
        "generic_cp_mae": round(float(np.mean([r["generic_cp_mae"] for r in out_rows])), 6),
        "geo_cp_mae": round(float(np.mean([r["geo_cp_mae"] for r in out_rows])), 6),
    }
    return {"rows": out_rows, "pooled": pooled}


def write_csv(rows: list[dict], output: Path, *, overwrite: bool = False) -> Path:
    output = Path(output)
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output


def _import_pyplot():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
        return plt
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"matplotlib 不可用：{exc}") from exc


def plot_compare(rows: list[dict], figure: Path, *, overwrite: bool = False) -> Path:
    figure = Path(figure)
    if figure.exists() and not overwrite:
        raise FileExistsError(f"图件已存在：{figure}")
    plt = _import_pyplot()
    labels = [r["prop"] for r in rows]
    x = np.arange(len(labels))
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    for ax, field, title in (
        (axes[0], "ct", "C_T mean abs error (LOPO)"),
        (axes[1], "cp", "C_P mean abs error (LOPO)"),
    ):
        ax.bar(x - 0.2, [r[f"generic_{field}_mae"] * 100 for r in rows], 0.4, label="generic prior")
        ax.bar(x + 0.2, [r[f"geo_{field}_mae"] * 100 for r in rows], 0.4, label="geometry-feature LOPO")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
        ax.set_title(title)
        ax.set_ylabel("relative error [%]")
        ax.grid(True, axis="y", linestyle=":", alpha=0.5)
        ax.legend(fontsize=8)
    fig.suptitle("Geometry/Reynolds-feature surrogate prior v0.1 — UIUC static, leave-one-prop-out")
    fig.text(0.5, 0.02, "REFERENCE-only validation — not a project measurement (D042/D049)", ha="center", color="crimson", fontsize=9)
    fig.tight_layout(rect=(0, 0.05, 1, 0.93))
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, dpi=150)
    plt.close(fig)
    return figure


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Geometry/Reynolds-feature propeller prior (REFERENCE)")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "data/processed/geometry_prior_v0.1.csv"))
    parser.add_argument("--figure", default=str(PROJECT_ROOT / "data/processed/figures/geometry_prior_v0.1.png"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        entries = load_entries()
        result = lopo_benchmark(entries)
        write_csv(result["rows"], Path(args.output), overwrite=args.overwrite)
        plot_compare(result["rows"], Path(args.figure), overwrite=args.overwrite)
    except (ValueError, FileExistsError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    pooled = result["pooled"]
    print(f"桨型 {len(result['rows'])} 个 / {pooled['points']} 点（LOPO）")
    for r in result["rows"]:
        print(f"  {r['prop']:<14} C_T {r['generic_ct_mae']*100:5.2f}% -> {r['geo_ct_mae']*100:5.2f}%  "
              f"C_P {r['generic_cp_mae']*100:5.2f}% -> {r['geo_cp_mae']*100:5.2f}%")
    print(f"pooled：C_T {pooled['generic_ct_mae']*100:.2f}% -> {pooled['geo_ct_mae']*100:.2f}%；"
          f"C_P {pooled['generic_cp_mae']*100:.2f}% -> {pooled['geo_cp_mae']*100:.2f}%")
    print(f"CSV：{args.output}\n图件：{args.figure}\n注意：{DATA_NOTE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
