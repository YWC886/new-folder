"""公开数据对标 v0.5：Reynolds 修正的通用比例模型（REFERENCE 口径，非实测）。

目的
----
v0.2/v0.3/v0.4 表明通用参数（ct0=0.110, aT=-0.02, cp0=0.045, aP=-0.035）与 UIUC 7 桨静态
数据存在系统性偏差：C_P 一致低估、C_T 方向相反（实测随 RPM 上升）。v0.4 的逐桨先验虽然
把样本内误差压到 0.3–1.5%，但需要"已知目标桨型参数"。

本模块回答中间问题：**只用一个通用 Re 修正（几何无关、跨桨共享 ct0/cp0 与 Re 指数）能否
部分修正偏差？** 三段对比：
  1) generic：现有默认参数；
  2) re：跨桨 pooled 拟合 CT/CP vs (Re/Re_ref) 的幂律（单一 ct0/cp0 + 单一指数）；
  3) prior：逐桨 REFERENCE 先验（v0.4，样本内上限）。

边界
----
- 全部为 REFERENCE（UIUC 风洞测量）对标：不是本项目实测，不构成校准或验证结论；
- 非泛化评估：re 与 prior 都在同一批 112 点上拟合，只能说明"若修正形式正确，误差能到多低"；
- 不写入 `propulsion_model.ModelParams` 默认值（D033/D034/D042 纪律延续）。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
_PYLIBS = PROJECT_ROOT / "work" / "pylibs"
if _PYLIBS.is_dir() and str(_PYLIBS) not in sys.path:
    sys.path.insert(0, str(_PYLIBS))

for _p in (PROJECT_ROOT / "code" / "simulation",):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import propulsion_model as pm  # noqa: E402

import catalog_uiuc as cu  # noqa: E402
import uiuc_propdb as up  # noqa: E402

SCHEMA_VERSION = "0.5"
N_REF_REV_S = 100.0  # ModelParams.n_ref_rev_s 默认
D_REF_M = 0.2544  # 10 英寸参考桨（Re 归一化基准）
NU_AIR_20C = 1.5e-5  # m^2/s，20 °C 干空气
R_AIR = 287.05
DATA_NOTE = "REFERENCE (UIUC) 对标：非本项目实测，不构成校准/验证；样本内拟合，非泛化评估"

SUM_FIELDS = [
    "prop",
    "points",
    "diameter_in",
    "ct_generic_err",
    "ct_re_err",
    "ct_scaled_err",
    "ct_prior_err",
    "cp_generic_err",
    "cp_re_err",
    "cp_scaled_err",
    "cp_prior_err",
    "re_gain_ct",
    "re_gain_cp",
]
POINT_FIELDS = [
    "prop",
    "rpm",
    "re",
    "ct_ref",
    "cp_ref",
    "ct_generic",
    "cp_generic",
    "ct_re",
    "cp_re",
    "ct_scaled",
    "cp_scaled",
]


def air_kinematic_viscosity(temp_c: float = 24.0, pressure_kpa: float = 96.0) -> float:
    """干空气运动黏度 ν = μ/ρ（Sutherland μ + 理想气体 ρ）。"""
    if pressure_kpa <= 0:
        raise ValueError("pressure_kpa 必须为正")
    t = temp_c + 273.15
    if t <= 0:
        raise ValueError("temp_c 太低（需高于绝对零度）")
    mu = 1.458e-6 * t**1.5 / (t + 110.4)  # Pa·s
    rho = pressure_kpa * 1000.0 / (R_AIR * t)
    return mu / rho


def reynolds_number(rpm: float, diameter_m: float, nu: float) -> float:
    """旋翼 Reynolds 数（工程定义）：Re = n·D²/ν，n 为 rps。"""
    if rpm <= 0 or diameter_m <= 0 or nu <= 0:
        raise ValueError("rpm、diameter_m、nu 必须为正")
    return (rpm / 60.0) * diameter_m**2 / nu


def re_ratio(rpm: float, diameter_m: float, nu: float) -> float:
    """相对参考状态的 Re 比：(n·D²)/(n_ref·D_ref²)。"""
    return reynolds_number(rpm, diameter_m, nu) / (
        N_REF_REV_S * D_REF_M**2 / nu
    )


def fit_power_law(x: list[float], y: list[float]) -> dict:
    """log-log OLS：y = c0 · x^a。返回 dict(c0, a, r2, n)。"""
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("至少 2 个点且 x/y 等长")
    xs = [math.log(v) for v in x]
    ys = [math.log(v) for v in y]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((v - mx) ** 2 for v in xs)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    if sxx == 0:
        raise ValueError("x 无变化，无法拟合指数")
    slope = sxy / sxx
    intercept = my - slope * mx
    ss_tot = sum((v - my) ** 2 for v in ys)
    ss_res = sum((v - (intercept + slope * u)) ** 2 for u, v in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return {"c0": math.exp(intercept), "a": slope, "r2": r2, "n": n}


def _load_props() -> list[dict]:
    props = []
    for filename in cu.DEFAULT_CATALOG_FILES:
        path = cu.REFERENCE_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"缺少参考数据：{path}")
        label = up.parse_prop_label(path.name)
        rows = up.load_static(path)
        props.append(
            {
                "prop": label["prop"],
                "diameter_m": label["diameter_in"] * 0.0254,
                "diameter_in": label["diameter_in"],
                "rows": rows,
            }
        )
    return props


def fit_pooled_re(props: list[dict], nu: float) -> dict:
    """跨桨 pooled 拟合：CT、CP 对 Re 比值的单一幂律。"""
    xs, cts, cps = [], [], []
    for entry in props:
        for row in entry["rows"]:
            ratio = re_ratio(row["rpm"], entry["diameter_m"], nu)
            xs.append(ratio)
            cts.append(row["ct"])
            cps.append(row["cp"])
    ct_fit = fit_power_law(xs, cts)
    cp_fit = fit_power_law(xs, cps)
    return {
        "nu_m2_s": nu,
        "n_ref_rev_s": N_REF_REV_S,
        "d_ref_m": D_REF_M,
        "ct": ct_fit,
        "cp": cp_fit,
    }


def fit_scale_exponents(props: list[dict], nu: float, base: pm.ModelParams) -> dict:
    """乘性 Re 修正：model * (Re/Re_ref)^a，a 由 log(ref/model) 对 log(Re比) 过原点 OLS。

    与"替换式"pooled 拟合不同：保留通用模型 ct0/cp0 量级，仅用 Re 因子修正趋势。
    """
    num_ct, num_cp, den = [], [], []
    for entry in props:
        for row in entry["rows"]:
            ratio = re_ratio(row["rpm"], entry["diameter_m"], nu)
            ct_g, cp_g = _model_coeffs(row["rpm"], entry["diameter_m"], base)
            num_ct.append(math.log(row["ct"] / ct_g))
            num_cp.append(math.log(row["cp"] / cp_g))
            den.append(math.log(ratio))
    sxx = sum(v * v for v in den)
    if sxx == 0:
        raise ValueError("Re 比无变化，无法拟合乘性修正")
    return {
        "ct": sum(x * y for x, y in zip(num_ct, den)) / sxx,
        "cp": sum(x * y for x, y in zip(num_cp, den)) / sxx,
    }


def _model_coeffs(rpm: float, diameter_m: float, base: pm.ModelParams) -> tuple[float, float]:
    ratio = (rpm / 60.0) / base.n_ref_rev_s
    return (
        base.ct0 * ratio ** base.reynolds_ct_exp,
        base.cp0 * ratio ** base.reynolds_cp_exp,
    )


def _prior_coeffs(priors: dict, prop: str, rpm: float) -> tuple[float, float]:
    for entry in priors.get("props", []):
        if entry["prop"] == prop:
            ratio = (rpm / 60.0) / N_REF_REV_S
            return (
                float(entry["ct0"]) * ratio ** float(entry["aT"]),
                float(entry["cp0"]) * ratio ** float(entry["aP"]),
            )
    raise KeyError(f"先验中缺少桨型：{prop}")


def _mean_abs(rel: list[float]) -> float:
    return sum(abs(v) for v in rel) / len(rel) if rel else 0.0


def compare(
    props: list[dict],
    pooled: dict,
    priors: dict,
    base: pm.ModelParams | None = None,
    scale: dict | None = None,
) -> dict:
    """逐点对比 generic / re / prior 三种系数来源。"""
    base = base or pm.ModelParams()
    scale = scale or {"ct": 0.0, "cp": 0.0}
    points: list[dict] = []
    per_prop: dict[str, dict] = {}
    for entry in props:
        prop = entry["prop"]
        rel = {
            "ct": {"generic": [], "re": [], "scaled": [], "prior": []},
            "cp": {"generic": [], "re": [], "scaled": [], "prior": []},
        }
        for row in entry["rows"]:
            ratio = re_ratio(row["rpm"], entry["diameter_m"], pooled["nu_m2_s"])
            ct_g, cp_g = _model_coeffs(row["rpm"], entry["diameter_m"], base)
            ct_re = pooled["ct"]["c0"] * ratio ** pooled["ct"]["a"]
            cp_re = pooled["cp"]["c0"] * ratio ** pooled["cp"]["a"]
            ct_scaled = ct_g * ratio ** scale["ct"]
            cp_scaled = cp_g * ratio ** scale["cp"]
            ct_pr, cp_pr = _prior_coeffs(priors, prop, row["rpm"])
            points.append(
                {
                    "prop": prop,
                    "rpm": row["rpm"],
                    "re": reynolds_number(row["rpm"], entry["diameter_m"], pooled["nu_m2_s"]),
                    "ct_ref": row["ct"],
                    "cp_ref": row["cp"],
                    "ct_generic": ct_g,
                    "cp_generic": cp_g,
                    "ct_re": ct_re,
                    "cp_re": cp_re,
                    "ct_scaled": ct_scaled,
                    "cp_scaled": cp_scaled,
                }
            )
            rel["ct"]["generic"].append((ct_g - row["ct"]) / row["ct"])
            rel["cp"]["generic"].append((cp_g - row["cp"]) / row["cp"])
            rel["ct"]["re"].append((ct_re - row["ct"]) / row["ct"])
            rel["cp"]["re"].append((cp_re - row["cp"]) / row["cp"])
            rel["ct"]["scaled"].append((ct_scaled - row["ct"]) / row["ct"])
            rel["cp"]["scaled"].append((cp_scaled - row["cp"]) / row["cp"])
            rel["ct"]["prior"].append((ct_pr - row["ct"]) / row["ct"])
            rel["cp"]["prior"].append((cp_pr - row["cp"]) / row["cp"])
        per_prop[prop] = {
            "prop": prop,
            "points": len(entry["rows"]),
            "diameter_in": entry["diameter_in"],
            "ct_generic_err": _mean_abs(rel["ct"]["generic"]) * 100,
            "ct_re_err": _mean_abs(rel["ct"]["re"]) * 100,
            "ct_scaled_err": _mean_abs(rel["ct"]["scaled"]) * 100,
            "ct_prior_err": _mean_abs(rel["ct"]["prior"]) * 100,
            "cp_generic_err": _mean_abs(rel["cp"]["generic"]) * 100,
            "cp_re_err": _mean_abs(rel["cp"]["re"]) * 100,
            "cp_scaled_err": _mean_abs(rel["cp"]["scaled"]) * 100,
            "cp_prior_err": _mean_abs(rel["cp"]["prior"]) * 100,
            "re_gain_ct": _mean_abs(rel["ct"]["generic"]) / max(_mean_abs(rel["ct"]["re"]), 1e-12),
            "re_gain_cp": _mean_abs(rel["cp"]["generic"]) / max(_mean_abs(rel["cp"]["re"]), 1e-12),
        }
    return {"points": points, "summary": [per_prop[e["prop"]] for e in props]}


def write_rows(points: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=POINT_FIELDS)
        writer.writeheader()
        for row in points:
            writer.writerow({k: (f"{v:.10g}" if isinstance(v, float) else v) for k, v in row.items()})


def write_summary(summary: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUM_FIELDS)
        writer.writeheader()
        for row in summary:
            writer.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in row.items()})


def _import_pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def plot_compare(summary: list[dict], figure: Path, *, overwrite: bool = False) -> Path:
    figure = Path(figure)
    if figure.exists() and not overwrite:
        raise FileExistsError(f"图件已存在：{figure}（--overwrite 覆盖）")
    plt = _import_pyplot()
    labels = [row["prop"] for row in summary]
    x = list(range(len(labels)))
    width = 0.2
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.8))
    for ax, ylabel, key in (
        (axes[0], "C_T mean abs error [%]", "ct"),
        (axes[1], "C_P mean abs error [%]", "cp"),
    ):
        ax.bar([v - width for v in x], [row[f"{key}_generic_err"] for row in summary], width, label="generic", color="#8c8c8c")
        ax.bar(x, [row[f"{key}_re_err"] for row in summary], width, label="Re-corrected (pooled)", color="#2e6da4")
        ax.bar([v + width for v in x], [row[f"{key}_scaled_err"] for row in summary], width, label="Re-scaling (pooled)", color="#e08b2d")
        ax.bar([v + 2 * width for v in x], [row[f"{key}_prior_err"] for row in summary], width, label="per-prop prior (v0.4)", color="#3a9e5f")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=9)
        ax.set_ylabel(ylabel)
        ax.grid(True, axis="y", linestyle=":", alpha=0.5)
        ax.legend(fontsize=8)
    fig.suptitle("Reynolds-corrected generic model vs per-prop prior — UIUC static (REFERENCE, in-sample)", fontsize=11)
    fig.text(0.5, 0.015, "REFERENCE-derived fit — not a project measurement; not U(k=2) (D031/D033/D042/D044)", ha="center", color="crimson", fontsize=9)
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure, dpi=150)
    plt.close(fig)
    return figure


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UIUC Re 修正 vs 逐桨先验（REFERENCE 对标）")
    parser.add_argument("--reference-dir", default=str(cu.REFERENCE_DIR))
    parser.add_argument("--priors", default=str(PROJECT_ROOT / "data" / "metadata" / "uiuc_priors_v0.3.json"))
    parser.add_argument("--temp-c", type=float, default=24.0)
    parser.add_argument("--pressure-kpa", type=float, default=96.0)
    parser.add_argument("--output", default=str(PROJECT_ROOT / "data" / "processed" / "re_correction_v0.5.csv"))
    parser.add_argument("--summary", default=str(PROJECT_ROOT / "data" / "metadata" / "re_correction_v0.5_summary.csv"))
    parser.add_argument("--figure", default=str(PROJECT_ROOT / "data" / "processed" / "figures" / "re_correction_v0.5.png"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        for path in (Path(args.output), Path(args.summary), Path(args.figure)):
            if path.exists() and not args.overwrite:
                raise FileExistsError(f"输出已存在：{path}（--overwrite 覆盖）")
        priors = json.loads(Path(args.priors).read_text(encoding="utf-8"))
        nu = air_kinematic_viscosity(args.temp_c, args.pressure_kpa)
        props = _load_props()
        pooled = fit_pooled_re(props, nu)
        base_model = pm.ModelParams()
        scale = fit_scale_exponents(props, nu, base_model)
        result = compare(props, pooled, priors, base=base_model, scale=scale)
        write_rows(result["points"], Path(args.output))
        write_summary(result["summary"], Path(args.summary))
        plot_compare(result["summary"], Path(args.figure), overwrite=args.overwrite)
    except (ValueError, FileNotFoundError, KeyError, FileExistsError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    print(f"点数：{len(result['points'])}；桨型：{len(result['summary'])}")
    print(f"pooled CT: c0={pooled['ct']['c0']:.6g} a={pooled['ct']['a']:+.4f} R2={pooled['ct']['r2']:.4f}")
    print(f"pooled CP: c0={pooled['cp']['c0']:.6g} a={pooled['cp']['a']:+.4f} R2={pooled['cp']['r2']:.4f}")
    print(f"scale exponents: CT {scale['ct']:+.4f}, CP {scale['cp']:+.4f}")
    for row in result["summary"]:
        print(
            f"  {row['prop']:<12} CT err generic {row['ct_generic_err']:.2f}% → re {row['ct_re_err']:.2f}% "
            f"→ scaled {row['ct_scaled_err']:.2f}% → prior {row['ct_prior_err']:.2f}% | CP "
            f"{row['cp_generic_err']:.2f}% → {row['cp_re_err']:.2f}% → scaled {row['cp_scaled_err']:.2f}% "
            f"→ prior {row['cp_prior_err']:.2f}%"
        )
    print(f"CSV：{args.output}")
    print(f"汇总：{args.summary}")
    print(f"图件：{args.figure}")
    print(f"注意：{DATA_NOTE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
