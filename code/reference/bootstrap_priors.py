"""UIUC 逐桨先验的参数不确定度（bootstrap，v0.1）。

在 `calibrate_uiuc.py`（v0.3，逐桨 log-OLS 反推 `ct0/a_T/cp0/a_P`）之上，
用**逐点重采样 bootstrap** 给出参数的 95% 百分位区间，并统计反推误差的分布，
回答"这组 REFERENCE-derived 先验本身有多不确定"。

边界（与 D031/D033 一致）：
- 仍是 REFERENCE（UIUC 实测）拟合，不是本项目实测标定；输出 `do_not_apply: true`。
- bootstrap 只反映"这 16 个点内部的重采样波动"，不包含 UIUC 风洞的系统误差、
  桨型/加工差异，因此**不是测量不确定度 U(k=2)**，不能与 `compute_efficiency`
  的不确定度块直接相加或比较。
- 每桨仅 ~16 点，bootstrap 区间偏乐观；用途仅限于"量级参照的稳健性检查"。
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, PROJECT_ROOT / "code" / "simulation"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import calibrate_uiuc as cal  # noqa: E402
import catalog_uiuc as catalog  # noqa: E402
import propulsion_model as pm  # noqa: E402

SCHEMA_VERSION = "0.1"
N_BOOT_DEFAULT = 200
CI_LEVEL = 0.95
SEED_DEFAULT = 20261119
MIN_BOOT = 10
DATA_NOTE = (
    "bootstrap 95% 百分位区间：仅反映 16 点内部重采样波动，"
    "非测量不确定度 U(k=2)，do_not_apply=true"
)
DISCLAIMER = (
    "REFERENCE-derived prior 的 bootstrap 区间：来源为 UIUC Vol.1 静态数据，"
    "不是本项目实测标定；区间偏乐观且不含风洞系统误差；按 D031/D033/D034 "
    "不得写入仿真默认值、选型结论或论文的校准表述。"
)

OUT_FIELDS = [
    "prop",
    "points",
    "ct0",
    "aT",
    "cp0",
    "aP",
    "ct0_lo",
    "ct0_hi",
    "aT_lo",
    "aT_hi",
    "cp0_lo",
    "cp0_hi",
    "aP_lo",
    "aP_hi",
    "ct_err_abs",
    "cp_err_abs",
    "ct_err_lo",
    "ct_err_hi",
    "cp_err_lo",
    "cp_err_hi",
    "n_boot",
    "ci_level",
    "data_note",
]


def _now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def percentile(sorted_values: list[float], q: float) -> float:
    """线性插值百分位（q∈[0,1]，输入需已排序）。"""
    if not sorted_values:
        raise ValueError("空样本无法取百分位")
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"百分位必须在 [0,1]：{q}")
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


def _ci(values: list[float], level: float = CI_LEVEL) -> tuple[float, float]:
    ordered = sorted(values)
    alpha = (1.0 - level) / 2.0
    return percentile(ordered, alpha), percentile(ordered, 1.0 - alpha)


def _fit_from_rows(rows: list[dict], n_ref: float) -> dict | None:
    """对给定行（ct/cp>0）做 log-OLS；无法拟合返回 None。"""
    good = [row for row in rows if row["ct"] > 0 and row["cp"] > 0]
    if len(good) < 4:
        return None
    xs = [math.log(row["n_rps"] / n_ref) for row in good]
    if len(set(xs)) < 2:
        return None
    ct_fit = cal._log_linear_fit(xs, [math.log(row["ct"]) for row in good])
    cp_fit = cal._log_linear_fit(xs, [math.log(row["cp"]) for row in good])
    return {"ct0": ct_fit["c0"], "aT": ct_fit["a"], "cp0": cp_fit["c0"], "aP": cp_fit["a"]}


def bootstrap_entry(
    entry: dict,
    model: pm.ModelParams | None = None,
    *,
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = SEED_DEFAULT,
    ci_level: float = CI_LEVEL,
) -> dict:
    """对单桨做 bootstrap：返回点估计 + 参数区间 + 反推误差区间。"""
    if n_boot < MIN_BOOT:
        raise ValueError(f"n_boot 过小（{n_boot} < {MIN_BOOT}）")
    if not 0.5 <= ci_level < 1.0:
        raise ValueError(f"ci_level 必须在 [0.5, 1)：{ci_level}")
    model = model or pm.ModelParams()
    n_ref = model.n_ref_rev_s
    rows = [row for row in entry["rows"] if row["ct"] > 0 and row["cp"] > 0]
    point = cal.fit_prop(entry, model)

    rng = random.Random(seed)
    samples = {"ct0": [], "aT": [], "cp0": [], "aP": []}
    ct_errors: list[float] = []
    cp_errors: list[float] = []
    for _ in range(n_boot):
        picked = [rows[rng.randrange(len(rows))] for _ in range(len(rows))]
        fitted = _fit_from_rows(picked, n_ref)
        if fitted is None:
            continue
        for key in samples:
            samples[key].append(fitted[key])
        errs = cal._model_errors(rows, fitted["ct0"], fitted["aT"], fitted["cp0"], fitted["aP"], n_ref)
        ct_errors.append(errs["ct_mean_abs"])
        cp_errors.append(errs["cp_mean_abs"])
    if not samples["ct0"]:
        raise ValueError(f"{entry['prop']} bootstrap 全部失败（有效样本不足）")

    result = {
        "prop": entry["prop"],
        "points": len(rows),
        "ct0": point["ct0"],
        "aT": point["aT"],
        "cp0": point["cp0"],
        "aP": point["aP"],
        "ct_err_abs": point["ct_err_abs_after"],
        "cp_err_abs": point["cp_err_abs_after"],
        "n_boot": len(samples["ct0"]),
        "ci_level": ci_level,
        "data_note": DATA_NOTE,
    }
    for key in ("ct0", "aT", "cp0", "aP"):
        lo, hi = _ci(samples[key], ci_level)
        result[f"{key}_lo"] = lo
        result[f"{key}_hi"] = hi
    for key, values in (("ct_err", ct_errors), ("cp_err", cp_errors)):
        lo, hi = _ci(values, ci_level)
        result[f"{key}_lo"] = lo
        result[f"{key}_hi"] = hi
    result["_samples"] = samples
    return result


def bootstrap_catalog(
    entries: list[dict],
    model: pm.ModelParams | None = None,
    *,
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = SEED_DEFAULT,
    ci_level: float = CI_LEVEL,
) -> dict:
    model = model or pm.ModelParams()
    props = [bootstrap_entry(entry, model, n_boot=n_boot, seed=seed, ci_level=ci_level) for entry in entries]
    return {
        "props": props,
        "pooled": _bootstrap_pooled(entries, model, n_boot=n_boot, seed=seed + 7919, ci_level=ci_level),
    }


def _bootstrap_pooled(
    entries: list[dict],
    model: pm.ModelParams,
    *,
    n_boot: int,
    seed: int,
    ci_level: float,
) -> dict:
    """跨桨 pooled 先验的 bootstrap（与逐桨相同的重采样口径）。"""
    n_ref = model.n_ref_rev_s
    rows = [row for entry in entries for row in entry["rows"] if row["ct"] > 0 and row["cp"] > 0]
    point = cal.fit_catalog(entries, model)["pooled"]
    rng = random.Random(seed)
    samples = {"ct0": [], "aT": [], "cp0": [], "aP": []}
    for _ in range(n_boot):
        picked = [rows[rng.randrange(len(rows))] for _ in range(len(rows))]
        fitted = _fit_from_rows(picked, n_ref)
        if fitted is None:
            continue
        for key in samples:
            samples[key].append(fitted[key])
    result = {
        "props": point["props"],
        "points": point["points"],
        "ct0": point["ct0"],
        "aT": point["aT"],
        "cp0": point["cp0"],
        "aP": point["aP"],
        "n_boot": len(samples["ct0"]) if samples["ct0"] else 0,
        "ci_level": ci_level,
    }
    for key in ("ct0", "aT", "cp0", "aP"):
        if samples[key]:
            lo, hi = _ci(samples[key], ci_level)
            result[f"{key}_lo"] = lo
            result[f"{key}_hi"] = hi
    return result


def build_summary(result: dict, *, n_boot: int, seed: int, ci_level: float) -> dict:
    props = []
    for prop in result["props"]:
        props.append({key: value for key, value in prop.items() if not key.startswith("_")})
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "source": "UIUC Propeller Database, Vol.1 — static wind-tunnel data (REFERENCE)",
        "method": "per-prop point bootstrap (resample 16 points with replacement, refit log-OLS)",
        "n_boot_requested": n_boot,
        "seed": seed,
        "ci_level": ci_level,
        "do_not_apply": True,
        "disclaimer": DISCLAIMER,
        "props": props,
        "pooled": result["pooled"],
    }


def write_csv(results: list[dict], path: str | Path) -> Path:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"输出已存在：{path}（需显式覆盖）")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerow({key: result[key] for key in OUT_FIELDS})
    return path


def write_summary(summary: dict, path: str | Path) -> Path:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"输出已存在：{path}（需显式覆盖）")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _import_pyplot():
    pylibs = PROJECT_ROOT / "work" / "pylibs"
    if pylibs.is_dir() and str(pylibs) not in sys.path:
        sys.path.insert(0, str(pylibs))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def plot_bootstrap(result: dict, output_png: str | Path, overwrite: bool = False) -> Path:
    plt = _import_pyplot()
    output_png = Path(output_png)
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{output_png}（需 --overwrite）")
    output_png.parent.mkdir(parents=True, exist_ok=True)

    props = result["props"]
    labels = [prop["prop"] for prop in props]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.0))

    a_t = [prop["_samples"]["aT"] for prop in props]
    axes[0].boxplot(a_t, showfliers=False)
    axes[0].set_xticks(range(1, len(labels) + 1))
    axes[0].set_xticklabels(labels, rotation=25, ha="right", fontsize=7.5)
    axes[0].axhline(0.0, color="#8c8c8c", ls="--", lw=1.2, label="a_T = 0")
    axes[0].axhline(pm.ModelParams().reynolds_ct_exp, color="crimson", ls=":", lw=1.2, label="generic a_T = -0.02")
    axes[0].set_ylabel("bootstrap a_T [-]")
    axes[0].set_title("C_T exponent bootstrap distribution")
    axes[0].grid(True, axis="y", ls=":", alpha=0.6)
    axes[0].legend(fontsize=8)
    axes[0].tick_params(axis="x", labelrotation=25, labelsize=7.5)

    positions = list(range(len(props)))
    centers = [prop["ct0"] for prop in props]
    lower = [prop["ct0"] - prop["ct0_lo"] for prop in props]
    upper = [prop["ct0_hi"] - prop["ct0"] for prop in props]
    axes[1].errorbar(positions, centers, yerr=[lower, upper], fmt="o", capsize=3, color="#2b7bba", label="ct0 ± 95% CI")
    axes[1].axhline(pm.ModelParams().ct0, color="crimson", ls=":", lw=1.2, label="generic ct0 = 0.110")
    axes[1].set_xticks(positions)
    axes[1].set_xticklabels(labels, rotation=25, ha="right", fontsize=7.5)
    axes[1].set_ylabel("ct0 [-] (C_T at n_ref)")
    axes[1].set_title("ct0 point estimate with bootstrap 95% CI")
    axes[1].grid(True, axis="y", ls=":", alpha=0.6)
    axes[1].legend(fontsize=8)

    fig.suptitle("UIUC bootstrap uncertainty — reference-prior robustness only (not measurement U; do not apply)")
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    fig.text(
        0.5,
        0.012,
        "REFERENCE (UIUC, measured) bootstrap — not a project measurement; not U(k=2) (D034)",
        ha="center",
        fontsize=8.5,
        color="crimson",
    )
    fig.savefig(output_png, dpi=150)
    plt.close(fig)
    return output_png


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UIUC 逐桨先验 bootstrap 不确定度 v0.1（do_not_apply）")
    parser.add_argument("--reference-dir", default=str(catalog.REFERENCE_DIR))
    parser.add_argument("--files", nargs="*", default=None)
    parser.add_argument("--output", default="data/processed/uiuc_bootstrap_priors_v0.1.csv")
    parser.add_argument("--summary", default="data/metadata/uiuc_priors_bootstrap_v0.1.json")
    parser.add_argument("--figure", default="data/processed/figures/uiuc_bootstrap_priors_v0.1.png")
    parser.add_argument("--n-boot", type=int, default=N_BOOT_DEFAULT)
    parser.add_argument("--seed", type=int, default=SEED_DEFAULT)
    parser.add_argument("--ci", type=float, default=CI_LEVEL)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    output = catalog._resolve(args.output)
    summary_path = catalog._resolve(args.summary)
    figure = catalog._resolve(args.figure)
    try:
        entries = catalog.load_catalog(args.reference_dir, args.files)
        result = bootstrap_catalog(entries, n_boot=args.n_boot, seed=args.seed, ci_level=args.ci)
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}")
        return 2

    existing = [path for path in (output, summary_path, figure) if path.exists()]
    if existing and not args.overwrite:
        print("错误：产物已存在（" + " / ".join(str(p) for p in existing) + "）；如确需覆盖请加 --overwrite")
        return 2
    for path in existing:
        path.unlink()

    write_csv(result["props"], output)
    summary = build_summary(result, n_boot=args.n_boot, seed=args.seed, ci_level=args.ci)
    write_summary(summary, summary_path)
    plot_bootstrap(result, figure)

    print(f"桨型 {len(result['props'])} 个；bootstrap {result['props'][0]['n_boot']} 次/桨，CI {args.ci:.0%}")
    for prop in result["props"]:
        print(
            f"  {prop['prop']:<12} ct0 {prop['ct0']:.4f} [{prop['ct0_lo']:.4f}, {prop['ct0_hi']:.4f}]  "
            f"aT {prop['aT']:+.3f} [{prop['aT_lo']:+.3f}, {prop['aT_hi']:+.3f}]"
        )
    pooled = result["pooled"]
    print(f"pooled：aT {pooled['aT']:+.3f} [{pooled.get('aT_lo', float('nan')):+.3f}, {pooled.get('aT_hi', float('nan')):+.3f}]")
    print(f"CSV：{output}")
    print(f"汇总 JSON：{summary_path}（do_not_apply=true）")
    print(f"图件：{figure}")
    print(DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
