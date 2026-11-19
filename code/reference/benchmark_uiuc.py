"""仿真模型 vs UIUC 参考数据对标（v0.1，SIM/REFERENCE 对比）。

把 `propulsion_model` 的静态 CT/CP 曲线与 UIUC 静态风洞数据放在同一 RPM 轴上比较，
输出逐点相对误差 CSV 与对比图。注意：
- 参考数据是真实风洞测量（UIUC），模型是参数化仿真，二者不是"验证通过"关系；
- 模型参数为文献量级 + 工程取值，且当前模型不带桨距/翼型信息；
- 对标只说明"量级与趋势是否同阶"，用于校准先验，不用于宣称精度。
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE, PROJECT_ROOT / "code" / "simulation"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import propulsion_model as pm  # noqa: E402
import uiuc_propdb  # noqa: E402

FIELDS = [
    "rpm",
    "n_rps",
    "ct_ref",
    "cp_ref",
    "ct_model",
    "cp_model",
    "ct_rel_err",
    "cp_rel_err",
    "data_note",
]

DATA_NOTE = (
    "ct_ref/cp_ref 为 UIUC 参考数据（真实风洞测量）；ct_model/cp_model 为参数化仿真；"
    "相对误差仅用于量级对标，不构成实验验证"
)


def model_coefficients(model: pm.ModelParams, rpm_values: list[float]) -> list[dict]:
    """按模型公式给出各 RPM 下的 CT/CP（仅依赖转速，不含电压）。"""
    out: list[dict] = []
    for rpm in rpm_values:
        n = rpm / 60.0
        ratio = max(n, 1e-6) / model.n_ref_rev_s
        out.append(
            {
                "rpm": rpm,
                "n_rps": n,
                "ct_model": model.ct0 * ratio**model.reynolds_ct_exp,
                "cp_model": model.cp0 * ratio**model.reynolds_cp_exp,
            }
        )
    return out


def benchmark(reference_rows: list[dict], model: pm.ModelParams | None = None) -> dict:
    """逐点比较参考 CT/CP 与模型 CT/CP，返回 rows 与汇总统计。"""
    if not reference_rows:
        raise ValueError("参考数据为空")
    model = model or pm.ModelParams()
    coeffs = model_coefficients(model, [r["rpm"] for r in reference_rows])
    by_rpm = {c["rpm"]: c for c in coeffs}
    rows: list[dict] = []
    for ref in reference_rows:
        mod = by_rpm[ref["rpm"]]
        ct_rel = (mod["ct_model"] - ref["ct"]) / ref["ct"]
        cp_rel = (mod["cp_model"] - ref["cp"]) / ref["cp"]
        rows.append(
            {
                "rpm": ref["rpm"],
                "n_rps": ref["n_rps"],
                "ct_ref": ref["ct"],
                "cp_ref": ref["cp"],
                "ct_model": mod["ct_model"],
                "cp_model": mod["cp_model"],
                "ct_rel_err": ct_rel,
                "cp_rel_err": cp_rel,
                "data_note": DATA_NOTE,
            }
        )
    ct_abs = [abs(r["ct_rel_err"]) for r in rows]
    cp_abs = [abs(r["cp_rel_err"]) for r in rows]
    stats = {
        "points": len(rows),
        "rpm_min": min(r["rpm"] for r in rows),
        "rpm_max": max(r["rpm"] for r in rows),
        "ct_mean_abs_rel_err": sum(ct_abs) / len(ct_abs),
        "ct_max_abs_rel_err": max(ct_abs),
        "cp_mean_abs_rel_err": sum(cp_abs) / len(cp_abs),
        "cp_max_abs_rel_err": max(cp_abs),
    }
    return {"rows": rows, "stats": stats}


def write_csv(rows: list[dict], path: Path | str) -> Path:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"输出已存在：{path}（需显式覆盖）")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def plot_comparison(rows: list[dict], output_png: Path | str, overwrite: bool = False) -> Path:
    _sys = sys
    _sys.path.insert(0, str(PROJECT_ROOT / "work" / "pylibs"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_png = Path(output_png)
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{output_png}（需 --overwrite）")
    output_png.parent.mkdir(parents=True, exist_ok=True)

    rpm = [r["rpm"] for r in rows]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    for ax, ref_key, mod_key, label in (
        (axes[0], "ct_ref", "ct_model", "Thrust coefficient C_T"),
        (axes[1], "cp_ref", "cp_model", "Power coefficient C_P"),
    ):
        ax.plot(rpm, [r[mod_key] for r in rows], "s--", color="tab:blue", lw=1.5, ms=4, label="model v0.1 (SIM, generic params)")
        ax.plot(rpm, [r[ref_key] for r in rows], "o-", color="black", lw=1.2, ms=4, label="UIUC reference (wind tunnel)")
        ax.set_xlabel("RPM")
        ax.set_ylabel(label)
        ax.grid(True, ls=":", alpha=0.6)
        ax.legend(fontsize=8)
        ax.set_title(label)
    fig.suptitle("UIUC benchmark v0.1 — APC 10x7E static vs simulation model", fontsize=11)
    fig.text(
        0.5,
        0.01,
        "REFERENCE (UIUC, measured) vs MODEL (SIM, generic parameters) — magnitude/trend check only",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color="dimgray",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(output_png, dpi=150)
    plt.close(fig)
    return output_png


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="仿真模型 vs UIUC 静态数据对标（v0.1）")
    parser.add_argument("--reference", default=str(uiuc_propdb.DEFAULT_REFERENCE), help="UIUC 静态数据文件")
    parser.add_argument("--output", default="data/processed/uiuc_benchmark_v0.1.csv", help="逐点 CSV")
    parser.add_argument("--figure", default="data/processed/figures/uiuc_benchmark_v0.1.png", help="对比图 PNG")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有产物")
    args = parser.parse_args(argv)

    try:
        reference = uiuc_propdb.load_static(args.reference)
        result = benchmark(reference)
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}")
        return 2

    output = Path(args.output)
    figure = Path(args.figure)
    if (output.exists() or figure.exists()) and not args.overwrite:
        print(f"错误：产物已存在（{output} / {figure}）；如确需覆盖请加 --overwrite")
        return 2
    if output.exists():
        output.unlink()
    if figure.exists():
        figure.unlink()
    write_csv(result["rows"], output)
    plot_comparison(result["rows"], figure, overwrite=True)

    stats = result["stats"]
    print(f"参考数据：{args.reference}（{stats['points']} 点，RPM {stats['rpm_min']:g}–{stats['rpm_max']:g}）")
    print(
        f"C_T 相对误差：均值 {stats['ct_mean_abs_rel_err'] * 100:.2f}% / 最大 {stats['ct_max_abs_rel_err'] * 100:.2f}%"
    )
    print(
        f"C_P 相对误差：均值 {stats['cp_mean_abs_rel_err'] * 100:.2f}% / 最大 {stats['cp_max_abs_rel_err'] * 100:.2f}%"
    )
    print(f"CSV：{output}")
    print(f"图件：{figure}")
    print("注意：REFERENCE 为真实风洞测量，MODEL 为参数化仿真；仅作量级/趋势对标，不是实验验证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
