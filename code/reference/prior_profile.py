"""REFERENCE-derived prior profile：把 UIUC 逐桨反推先验转成 opt-in 仿真参数并做闭环校核。

背景
----
`code/reference/calibrate_uiuc.py` 从 UIUC Propeller Database 静态数据逐桨反推了
`C_T = ct0*(n/n_ref)^aT` 与 `C_P = cp0*(n/n_ref)^aP`（见 `data/metadata/uiuc_priors_v0.3.json`）。
该先验是 REFERENCE-derived（公开风洞测量拟合），不是本项目实测标定，按 D033/D034 固定
`do_not_apply: true`，不得写入 `ModelParams` 默认值、不得用于选型结论。

本模块只做两件事（opt-in，不改默认行为）：
1. 把某个桨的逐桨先验包装成一份 `ModelParams`（仅用于敏感性/对照实验）；
2. 在同一份 UIUC 静态数据上比较【通用参数先验】与【逐桨 prior profile】的相对误差，
   回答"若把模型先验换成目标桨型，比例模型的误差能降到多少"。

纪律（D042）
------------
- 输出一律带 `DATA_NOTE`，标注 REFERENCE-derived、非实测标定；
- 只在显式传入 `--priors` 时启用，`ModelParams` 默认值不变；
- 本模块结果不能用于宣称"模型已验证"或"校准完成"——实测校核仍须 M0.4 静态砝码标定。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (PROJECT_ROOT / "code" / "simulation", PROJECT_ROOT / "work" / "pylibs"):
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import propulsion_model as pm  # noqa: E402
import uiuc_propdb as up  # noqa: E402

SCHEMA_VERSION = "0.1"
DATA_NOTE = "REFERENCE-derived prior profile（UIUC 静态数据反推）；opt-in 对照，不是实测标定（D033/D034/D042）"
DEFAULT_PRIORS = PROJECT_ROOT / "data" / "metadata" / "uiuc_priors_v0.3.json"
DEFAULT_REFERENCE_DIR = PROJECT_ROOT / "data" / "reference" / "uiuc"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "prior_profile_vs_generic_v0.1.csv"
DEFAULT_FIGURE = PROJECT_ROOT / "data" / "processed" / "figures" / "prior_profile_v0.1.png"

FIELDS = (
    "prop",
    "rpm",
    "ct_ref",
    "cp_ref",
    "ct_generic",
    "cp_generic",
    "ct_prior",
    "cp_prior",
    "ct_generic_rel_err",
    "cp_generic_rel_err",
    "ct_prior_rel_err",
    "cp_prior_rel_err",
    "data_note",
)
METRIC_FIELDS = ("prop", "points", "ct_generic_mean_abs_err", "cp_generic_mean_abs_err", "ct_prior_mean_abs_err", "cp_prior_mean_abs_err", "ct_improvement_x", "cp_improvement_x")


def load_priors(path: Path) -> dict:
    """读取逐桨先验 JSON 并校验关键字段。"""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"先验文件不存在：{path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("do_not_apply") is not True:
        raise ValueError("先验文件必须显式标记 do_not_apply: true（REFERENCE-derived，不是实测标定）")
    props = data.get("props")
    if not isinstance(props, list) or not props:
        raise ValueError("先验文件缺少非空 props 列表")
    for entry in props:
        for key in ("prop", "ct0", "aT", "cp0", "aP", "diameter_in"):
            if key not in entry:
                raise ValueError(f"先验条目缺少字段：{key}")
    return data


def find_prop(priors: dict, prop: str) -> dict:
    """按桨型标识（如 apce_11x7）查找先验条目。"""
    for entry in priors["props"]:
        if entry["prop"] == prop:
            return entry
    names = ", ".join(e["prop"] for e in priors["props"])
    raise ValueError(f"先验中没有桨型 {prop}；可用：{names}")


def model_from_prior(entry: dict, base: pm.ModelParams | None = None) -> pm.ModelParams:
    """把逐桨先验包装成 opt-in 的 ModelParams（其余参数沿用 base/默认值）。"""
    base = base or pm.ModelParams()
    diameter_m = float(entry["diameter_in"]) * 0.0254
    if diameter_m <= 0:
        raise ValueError("先验直径无效")
    return replace(
        base,
        diameter_m=diameter_m,
        ct0=float(entry["ct0"]),
        cp0=float(entry["cp0"]),
        reynolds_ct_exp=float(entry["aT"]),
        reynolds_cp_exp=float(entry["aP"]),
    )


def _coeffs(rpm: float, ct0: float, a_t: float, cp0: float, a_p: float, n_ref: float) -> tuple[float, float]:
    n = rpm / 60.0
    ratio = n / n_ref
    return ct0 * ratio**a_t, cp0 * ratio**a_p


def compare_entry(entry: dict, reference_rows: list[dict]) -> dict:
    """在同一条 UIUC 静态曲线上比较通用先验与逐桨 prior profile 的误差。"""
    if not reference_rows:
        raise ValueError("参考数据为空")
    generic = pm.ModelParams()
    prior = model_from_prior(entry, generic)
    rows = []
    for ref in reference_rows:
        rpm = float(ref["rpm"])
        ct_ref = float(ref["ct"])
        cp_ref = float(ref["cp"])
        ct_gen, cp_gen = _coeffs(rpm, generic.ct0, generic.reynolds_ct_exp, generic.cp0, generic.reynolds_cp_exp, generic.n_ref_rev_s)
        ct_pri, cp_pri = _coeffs(rpm, prior.ct0, prior.reynolds_ct_exp, prior.cp0, prior.reynolds_cp_exp, prior.n_ref_rev_s)
        rows.append(
            {
                "prop": entry["prop"],
                "rpm": rpm,
                "ct_ref": ct_ref,
                "cp_ref": cp_ref,
                "ct_generic": ct_gen,
                "cp_generic": cp_gen,
                "ct_prior": ct_pri,
                "cp_prior": cp_pri,
                "ct_generic_rel_err": (ct_gen - ct_ref) / ct_ref,
                "cp_generic_rel_err": (cp_gen - cp_ref) / cp_ref,
                "ct_prior_rel_err": (ct_pri - ct_ref) / ct_ref,
                "cp_prior_rel_err": (cp_pri - cp_ref) / cp_ref,
                "data_note": DATA_NOTE,
            }
        )
    n = len(rows)
    ct_generic = sum(abs(r["ct_generic_rel_err"]) for r in rows) / n
    cp_generic = sum(abs(r["cp_generic_rel_err"]) for r in rows) / n
    ct_prior = sum(abs(r["ct_prior_rel_err"]) for r in rows) / n
    cp_prior = sum(abs(r["cp_prior_rel_err"]) for r in rows) / n
    stats = {
        "prop": entry["prop"],
        "points": n,
        "ct_generic_mean_abs_err": ct_generic,
        "cp_generic_mean_abs_err": cp_generic,
        "ct_prior_mean_abs_err": ct_prior,
        "cp_prior_mean_abs_err": cp_prior,
        "ct_improvement_x": ct_generic / ct_prior if ct_prior > 0 else math.inf,
        "cp_improvement_x": cp_generic / cp_prior if cp_prior > 0 else math.inf,
    }
    return {"rows": rows, "stats": stats}


def write_csv(rows: list[dict], output: Path, overwrite: bool = False) -> Path:
    output = Path(output)
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出已存在（使用 --overwrite 覆盖）：{output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return output


def plot_compare(metrics: list[dict], output_png: Path, *, overwrite: bool = False) -> Path:
    """逐桨对比：通用先验 vs 逐桨 prior profile 的平均绝对误差（C_T / C_P）。"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_png = Path(output_png)
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"图件已存在（使用 --overwrite 覆盖）：{output_png}")
    output_png.parent.mkdir(parents=True, exist_ok=True)
    labels = [m["prop"] for m in metrics]
    x = range(len(labels))
    width = 0.38

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6))
    for ax, generic_key, prior_key, ylabel in (
        (axes[0], "ct_generic_mean_abs_err", "ct_prior_mean_abs_err", "C_T mean abs error [%]"),
        (axes[1], "cp_generic_mean_abs_err", "cp_prior_mean_abs_err", "C_P mean abs error [%]"),
    ):
        ax.bar([i - width / 2 for i in x], [m[generic_key] * 100 for m in metrics], width, label="generic prior (MODEL)", color="#9a9a9a")
        ax.bar([i + width / 2 for i in x], [m[prior_key] * 100 for m in metrics], width, label="per-prop prior profile (opt-in)", color="#2b6cb0")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, axis="y", linestyle=":", alpha=0.6)
    fig.suptitle("REFERENCE prior profile vs generic model — UIUC static data (magnitude check only)")
    fig.text(0.5, 0.01, "REFERENCE-derived priors (do not apply as calibration); not a measurement U(k=2) (D033/D034/D042)", ha="center", color="crimson", fontsize=8)
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    fig.savefig(output_png, dpi=150)
    plt.close(fig)
    return output_png


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UIUC 逐桨先验 prior profile 对照（opt-in，非实测标定）")
    parser.add_argument("--priors", default=str(DEFAULT_PRIORS))
    parser.add_argument("--reference-dir", default=str(DEFAULT_REFERENCE_DIR))
    parser.add_argument("--props", default=None, help="逗号分隔桨型标识；默认全部")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--figure", default=str(DEFAULT_FIGURE))
    parser.add_argument("--overwrite", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # pragma: no cover - argparse usage errors
        return 2 if exc.code else 0

    try:
        priors = load_priors(Path(args.priors))
        wanted = [s.strip() for s in args.props.split(",")] if args.props else [e["prop"] for e in priors["props"]]
        reference_dir = Path(args.reference_dir)
        rows: list[dict] = []
        metrics: list[dict] = []
        for prop in wanted:
            entry = find_prop(priors, prop)
            candidates = sorted(reference_dir.glob(f"{prop}_static_*.txt"))
            if not candidates:
                raise FileNotFoundError(f"参考目录中没有 {prop} 的静态文件：{reference_dir}")
            result = compare_entry(entry, up.load_static(candidates[0]))
            rows.extend(result["rows"])
            metrics.append(result["stats"])
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}")
        return 2

    try:
        csv_path = write_csv(rows, Path(args.output), overwrite=args.overwrite)
        png_path = plot_compare(metrics, Path(args.figure), overwrite=args.overwrite)
    except FileExistsError as exc:
        print(f"错误：{exc}")
        return 2

    print(f"通用先验 vs 逐桨 prior profile（REFERENCE，非实测）：{len(metrics)} 桨 / {len(rows)} 点")
    for m in metrics:
        print(
            f"  {m['prop']:<12} C_T {m['ct_generic_mean_abs_err']*100:5.2f}% → {m['ct_prior_mean_abs_err']*100:4.2f}% ({m['ct_improvement_x']:.1f}×)   "
            f"C_P {m['cp_generic_mean_abs_err']*100:5.2f}% → {m['cp_prior_mean_abs_err']*100:4.2f}% ({m['cp_improvement_x']:.1f}×)"
        )
    print(f"CSV：{csv_path}\n图件：{png_path}")
    print(f"注意：{DATA_NOTE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
