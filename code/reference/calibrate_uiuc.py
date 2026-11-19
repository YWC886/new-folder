"""UIUC 静态参考数据的逐桨参数反推（v0.3，REFERENCE-derived priors）。

用途：在**不修改仿真默认参数**的前提下，用 UIUC Vol.1 静态风洞数据（REFERENCE）反推
每个桨的 `ct0 / a_T / cp0 / a_P`（模型形式同 `propulsion_model`：

    C_T(n) = ct0 * (n / n_ref) ** a_T
    C_P(n) = cp0 * (n / n_ref) ** a_P

），并给出反推前后相对误差与留出点（holdout）误差，用于回答"通用先验与桨型专用先验
差多少"，为 M0.4 实测标定与后续选型提供**参照量级**。

边界（重要）：
- 这是**参考数据反推**，不是本项目实测标定；输出 JSON 标记 `do_not_apply: true`，
  禁止直接写入仿真默认参数、选型结论或软著/论文的"校准完成"表述（D031/D033）。
- 拟合是在 log 空间对 2 个参数做 OLS；每桨约 16 点，holdout 只做确定性留出（非随机），
  仅用于粗略泛化检查，不构成统计显著证据。
- 数据来源与引用见 `data/reference/README.md`（UIUC，科研/教学用途，注明引用）。
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, PROJECT_ROOT / "code" / "simulation"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import benchmark_uiuc as bench  # noqa: E402
import catalog_uiuc as catalog  # noqa: E402
import propulsion_model as pm  # noqa: E402

SCHEMA_VERSION = "0.3"
DATA_NOTE = (
    "参数由 UIUC 静态风洞数据（REFERENCE, measured）反推；"
    "仅作先验量级参考，do_not_apply=true，禁止直接用于仿真默认值或选型结论"
)
DISCLAIMER = (
    "REFERENCE-derived prior：来源为 UIUC Propeller Database Vol.1 静态测量，"
    "不是本项目实测标定；按 D031/D033 不得据此宣称校准完成，"
    "仅可在 M0.4 实测数据到位前作为量级参照。"
)

CALIBRATION_FIELDS = [
    "prop",
    "brand",
    "series",
    "diameter_in",
    "pitch_in",
    "points",
    "ct0",
    "aT",
    "cp0",
    "aP",
    "ct_log_r2",
    "cp_log_r2",
    "ct_err_abs_before",
    "cp_err_abs_before",
    "ct_err_abs_after",
    "cp_err_abs_after",
    "ct_holdout_abs",
    "cp_holdout_abs",
    "data_note",
]


def _now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _log_linear_fit(xs: list[float], ys: list[float]) -> dict:
    """OLS 拟合 ln(y) = ln(c0) + a·x；返回 {c0, a, r2, n}。"""
    if len(xs) < 3:
        raise ValueError(f"拟合点数不足（{len(xs)} < 3）")
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        raise ValueError("RPM 全部相同，无法拟合转速指数")
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    a = sxy / sxx
    intercept = mean_y - a * mean_x
    residuals = [y - (intercept + a * x) for x, y in zip(xs, ys)]
    ss_res = sum(e * e for e in residuals)
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {"c0": math.exp(intercept), "a": a, "r2": r2, "n": len(xs)}


def _model_errors(rows: list[dict], ct0: float, a_t: float, cp0: float, a_p: float, n_ref: float) -> dict:
    ct_rels: list[float] = []
    cp_rels: list[float] = []
    for row in rows:
        ratio = row["n_rps"] / n_ref
        ct = ct0 * ratio**a_t
        cp = cp0 * ratio**a_p
        ct_rels.append((ct - row["ct"]) / row["ct"])
        cp_rels.append((cp - row["cp"]) / row["cp"])
    return {
        "ct_mean_abs": sum(abs(v) for v in ct_rels) / len(ct_rels),
        "cp_mean_abs": sum(abs(v) for v in cp_rels) / len(cp_rels),
        "ct_max_abs": max(abs(v) for v in ct_rels),
        "cp_max_abs": max(abs(v) for v in cp_rels),
    }


def _split_holdout(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """确定性留出：每 4 个点取第 1 个作为 holdout（至少保留 4 个训练点）。"""
    if len(rows) < 6:
        return list(rows), []
    holdout = [row for index, row in enumerate(rows) if index % 4 == 0]
    train = [row for index, row in enumerate(rows) if index % 4 != 0]
    if len(train) < 4 or not holdout:
        return list(rows), []
    return train, holdout


def fit_prop(entry: dict, model: pm.ModelParams | None = None) -> dict:
    """对单桨数据反推 ct0/aT/cp0/aP，并给出反推前后误差与 holdout 误差。"""
    model = model or pm.ModelParams()
    n_ref = model.n_ref_rev_s
    rows = [row for row in entry["rows"] if row["ct"] > 0 and row["cp"] > 0]
    if len(rows) < 4:
        raise ValueError(f"{entry['prop']} 有效数据点不足（{len(rows)} < 4）")

    xs = [math.log(row["n_rps"] / n_ref) for row in rows]
    ct_fit = _log_linear_fit(xs, [math.log(row["ct"]) for row in rows])
    cp_fit = _log_linear_fit(xs, [math.log(row["cp"]) for row in rows])

    generic_ct = model.ct0 * (model.n_ref_rev_s / model.n_ref_rev_s) ** model.reynolds_ct_exp
    _ = generic_ct  # 仅说明：通用模型按同一 rpm 轴计算，见 bench.model_coefficients
    before = _model_errors(rows, model.ct0, model.reynolds_ct_exp, model.cp0, model.reynolds_cp_exp, n_ref)
    after = _model_errors(rows, ct_fit["c0"], ct_fit["a"], cp_fit["c0"], cp_fit["a"], n_ref)

    train, holdout = _split_holdout(rows)
    if holdout:
        xs_train = [math.log(row["n_rps"] / n_ref) for row in train]
        ct_train = _log_linear_fit(xs_train, [math.log(row["ct"]) for row in train])
        cp_train = _log_linear_fit(xs_train, [math.log(row["cp"]) for row in train])
        hold = _model_errors(holdout, ct_train["c0"], ct_train["a"], cp_train["c0"], cp_train["a"], n_ref)
        ct_holdout = hold["ct_mean_abs"]
        cp_holdout = hold["cp_mean_abs"]
    else:
        ct_holdout = None
        cp_holdout = None

    return {
        "prop": entry["prop"],
        "display": entry["display"],
        "brand": entry["brand"],
        "series": entry["series"],
        "diameter_in": entry["diameter_in"],
        "pitch_in": entry["pitch_in"],
        "points": len(rows),
        "ct0": ct_fit["c0"],
        "aT": ct_fit["a"],
        "cp0": cp_fit["c0"],
        "aP": cp_fit["a"],
        "ct_log_r2": ct_fit["r2"],
        "cp_log_r2": cp_fit["r2"],
        "ct_err_abs_before": before["ct_mean_abs"],
        "cp_err_abs_before": before["cp_mean_abs"],
        "ct_err_abs_after": after["ct_mean_abs"],
        "cp_err_abs_after": after["cp_mean_abs"],
        "ct_holdout_abs": ct_holdout,
        "cp_holdout_abs": cp_holdout,
        "data_note": DATA_NOTE,
    }


def fit_catalog(entries: list[dict], model: pm.ModelParams | None = None) -> dict:
    """逐桨反推 + pooled 反推，返回 {props, pooled, pooled_errors}。"""
    model = model or pm.ModelParams()
    props = [fit_prop(entry, model) for entry in entries]

    all_rows = [row for entry in entries for row in entry["rows"] if row["ct"] > 0 and row["cp"] > 0]
    n_ref = model.n_ref_rev_s
    xs = [math.log(row["n_rps"] / n_ref) for row in all_rows]
    ct_fit = _log_linear_fit(xs, [math.log(row["ct"]) for row in all_rows])
    cp_fit = _log_linear_fit(xs, [math.log(row["cp"]) for row in all_rows])
    before = _model_errors(all_rows, model.ct0, model.reynolds_ct_exp, model.cp0, model.reynolds_cp_exp, n_ref)
    after = _model_errors(all_rows, ct_fit["c0"], ct_fit["a"], cp_fit["c0"], cp_fit["a"], n_ref)
    return {
        "props": props,
        "pooled": {
            "props": len(entries),
            "points": len(all_rows),
            "ct0": ct_fit["c0"],
            "aT": ct_fit["a"],
            "cp0": cp_fit["c0"],
            "aP": cp_fit["a"],
            "ct_log_r2": ct_fit["r2"],
            "cp_log_r2": cp_fit["r2"],
            "ct_err_abs_before": before["ct_mean_abs"],
            "cp_err_abs_before": before["cp_mean_abs"],
            "ct_err_abs_after": after["ct_mean_abs"],
            "cp_err_abs_after": after["cp_mean_abs"],
        },
    }


def build_priors(result: dict, model: pm.ModelParams | None = None) -> dict:
    model = model or pm.ModelParams()
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "source": "UIUC Propeller Database, Vol.1 — static wind-tunnel data (REFERENCE)",
        "reference_dir": "data/reference/uiuc",
        "model_form": "CT=ct0*(n/n_ref)**aT; CP=cp0*(n/n_ref)**aP",
        "n_ref_rev_s": model.n_ref_rev_s,
        "do_not_apply": True,
        "disclaimer": DISCLAIMER,
        "props": result["props"],
        "pooled": result["pooled"],
    }


def write_calibration_csv(props: list[dict], path: str | Path) -> Path:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"输出已存在：{path}（需显式覆盖）")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CALIBRATION_FIELDS)
        writer.writeheader()
        for prop in props:
            writer.writerow({key: prop[key] for key in CALIBRATION_FIELDS})
    return path


def write_priors_json(priors: dict, path: str | Path) -> Path:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"输出已存在：{path}（需显式覆盖）")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(priors, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _import_pyplot():
    pylibs = PROJECT_ROOT / "work" / "pylibs"
    if pylibs.is_dir() and str(pylibs) not in sys.path:
        sys.path.insert(0, str(pylibs))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def plot_calibration(result: dict, output_png: str | Path, overwrite: bool = False) -> Path:
    plt = _import_pyplot()
    output_png = Path(output_png)
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{output_png}（需 --overwrite）")
    output_png.parent.mkdir(parents=True, exist_ok=True)

    props = result["props"]
    labels = [p["display"] for p in props]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9))
    width = 0.38
    positions = list(range(len(props)))
    for ax, before_key, after_key, title in (
        (axes[0], "ct_err_abs_before", "ct_err_abs_after", "C_T mean abs error"),
        (axes[1], "cp_err_abs_before", "cp_err_abs_after", "C_P mean abs error"),
    ):
        before = [p[before_key] * 100 for p in props]
        after = [p[after_key] * 100 for p in props]
        ax.bar([x - width / 2 for x in positions], before, width, label="generic prior (MODEL)", color="#8c8c8c")
        ax.bar([x + width / 2 for x in positions], after, width, label="per-prop REFERENCE prior", color="#2b7bba")
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=7.5)
        ax.set_ylabel("relative error [%]")
        ax.set_title(title)
        ax.grid(True, axis="y", ls=":", alpha=0.6)
        ax.legend(fontsize=8)
    fig.suptitle("UIUC v0.3 — per-prop REFERENCE-derived priors (reference fit only; do not apply)")
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    fig.text(
        0.5,
        0.012,
        "REFERENCE (UIUC, measured) fit — not a project measurement; not a calibration result (D033)",
        ha="center",
        fontsize=8.5,
        color="crimson",
    )
    fig.savefig(output_png, dpi=150)
    plt.close(fig)
    return output_png


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="UIUC 静态数据逐桨参数反推 v0.3（REFERENCE-derived priors；do_not_apply）"
    )
    parser.add_argument("--reference-dir", default=str(catalog.REFERENCE_DIR))
    parser.add_argument("--files", nargs="*", default=None)
    parser.add_argument("--output", default="data/processed/uiuc_calibration_v0.3.csv")
    parser.add_argument("--priors", default="data/metadata/uiuc_priors_v0.3.json")
    parser.add_argument("--figure", default="data/processed/figures/uiuc_calibration_v0.3.png")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    output = catalog._resolve(args.output)
    priors_path = catalog._resolve(args.priors)
    figure = catalog._resolve(args.figure)

    try:
        entries = catalog.load_catalog(args.reference_dir, args.files)
        result = fit_catalog(entries)
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}")
        return 2

    existing = [path for path in (output, priors_path, figure) if path.exists()]
    if existing and not args.overwrite:
        print(
            "错误：产物已存在（" + " / ".join(str(p) for p in existing) + "）；如确需覆盖请加 --overwrite"
        )
        return 2
    for path in existing:
        path.unlink()

    write_calibration_csv(result["props"], output)
    write_priors_json(build_priors(result), priors_path)
    plot_calibration(result, figure)

    pooled = result["pooled"]
    print(f"桨型 {pooled['props']} 个 / {pooled['points']} 点（REFERENCE-derived prior，do_not_apply）")
    print(f"  {'prop':<12}{'ct0':>8}{'aT':>8}{'cp0':>10}{'aP':>8}{'CT err':>9}{'CP err':>9}")
    for prop in result["props"]:
        print(
            f"  {prop['prop']:<12}{prop['ct0']:>8.4f}{prop['aT']:>8.3f}"
            f"{prop['cp0']:>10.4f}{prop['aP']:>8.3f}"
            f"{prop['ct_err_abs_after'] * 100:>8.2f}%{prop['cp_err_abs_after'] * 100:>8.2f}%"
        )
    print(
        f"generic prior 误差：C_T {pooled['ct_err_abs_before'] * 100:.2f}% / "
        f"C_P {pooled['cp_err_abs_before'] * 100:.2f}%；"
        f"per-prop prior（pooled 拟合）：C_T {pooled['ct_err_abs_after'] * 100:.2f}% / "
        f"C_P {pooled['cp_err_abs_after'] * 100:.2f}%"
    )
    print(f"CSV：{output}")
    print(f"先验 JSON：{priors_path}（do_not_apply=true）")
    print(f"图件：{figure}")
    print(DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
