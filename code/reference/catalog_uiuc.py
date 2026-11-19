"""UIUC 多桨型静态对标（v0.2，REFERENCE vs MODEL/SIM）。

把 UIUC Propeller Database Volume 1 的多个桨型**静态风洞数据**（RPM 扫描的 CT/CP）
与 `propulsion_model` 通用参数仿真放在同一 RPM 轴上比较，输出：
- `data/processed/uiuc_benchmark_v0.2.csv`：逐点数据（桨标签 + 参考值 + 模型值 + 相对误差）；
- `data/processed/uiuc_benchmark_v0.2_summary.csv`：逐桨统计（点数、RPM 范围、CT/CP 均值与
  极值、相对误差均值/最大、是否全为正）；
- `data/processed/figures/uiuc_benchmark_v0.2.png`：CT/CP 双面板分组图（各桨散点/细线 +
  通用模型曲线 + REFERENCE/MODEL 脚注）。

注意：
- 参考数据是真实风洞测量（UIUC），模型是参数化仿真，二者不是"验证通过"关系；
- 模型参数为文献量级 + 工程取值，不含桨径/螺距/翼型信息，同一模型曲线对所有桨型完全
  相同，因此可比的是量级/趋势与系统性偏差，不是同桨精确复现；
- 对标只用于校准先验，不用于宣称精度；所有结果标 `REFERENCE`（实测）vs `MODEL`（SIM）。
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

import benchmark_uiuc as bench  # noqa: E402
import propulsion_model as pm  # noqa: E402
import uiuc_propdb  # noqa: E402

REFERENCE_DIR = PROJECT_ROOT / "data" / "reference" / "uiuc"

# v0.2 对标的 7 个 UIUC Vol.1 静态数据镜像样本（覆盖 6 个品牌/系列：APC E/SF/Sport、
# Graupner CAM/Super Nylon、Aeronaut Carbon Electric）。
DEFAULT_CATALOG_FILES = (
    "apce_11x7_static_kt0534.txt",
    "apce_11x8_static_kt0517.txt",
    "apcsf_10x7_static_kt0827.txt",
    "apcsp_9x6_static_2532rd.txt",
    "grcp_10x6_static_rd0851.txt",
    "grsn_10x7_static_rd0787.txt",
    "ance_8.5x6_static_2848cm.txt",
)

CATALOG_DATA_NOTE = (
    "ct_ref/cp_ref 为 UIUC Vol.1 静态风洞数据（REFERENCE, measured）；"
    "ct_model/cp_model 为通用参数仿真（MODEL, SIM）；"
    "相对误差仅用于量级/趋势对标，不构成实验验证"
)

POINT_FIELDS = [
    "prop",
    "brand",
    "series",
    "brand_series",
    "diameter_in",
    "pitch_in",
    "file",
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

SUMMARY_FIELDS = [
    "prop",
    "display",
    "brand",
    "series",
    "brand_series",
    "diameter_in",
    "pitch_in",
    "file",
    "points",
    "rpm_min",
    "rpm_max",
    "ct_ref_mean",
    "ct_ref_min",
    "ct_ref_max",
    "cp_ref_mean",
    "cp_ref_min",
    "cp_ref_max",
    "ct_model_mean",
    "cp_model_mean",
    "ct_rel_err_mean",
    "ct_rel_err_mean_abs",
    "ct_rel_err_max_abs",
    "cp_rel_err_mean",
    "cp_rel_err_mean_abs",
    "cp_rel_err_max_abs",
    "all_positive",
]


def _resolve(path: Path | str, base: Path = PROJECT_ROOT) -> Path:
    """相对路径一律按项目根目录解析（脚本可从任意 CWD 运行）。"""
    path = Path(path)
    return path if path.is_absolute() else base / path


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def load_catalog(
    reference_dir: Path | str = REFERENCE_DIR,
    filenames: tuple[str, ...] | list[str] | None = None,
) -> list[dict]:
    """读取多桨型静态数据目录，返回 [{解析标签..., path, rows}, ...]。"""
    reference_dir = Path(reference_dir)
    names = tuple(filenames) if filenames else DEFAULT_CATALOG_FILES
    if not names:
        raise ValueError("桨型目录为空：未指定任何数据文件")
    entries: list[dict] = []
    seen: dict[str, str] = {}
    for name in names:
        path = reference_dir / name
        label = uiuc_propdb.parse_prop_label(path)
        if label["prop"] in seen:
            raise ValueError(
                f"重复的桨型标签 {label['prop']!r}：{seen[label['prop']]} 与 {name}"
            )
        seen[label["prop"]] = name
        rows = uiuc_propdb.load_static(path)
        entries.append({**label, "path": str(path), "rows": rows})
    return entries


def benchmark_catalog(
    entries: list[dict], model: pm.ModelParams | None = None
) -> dict:
    """逐桨对标并汇总，返回 {'rows': 逐点, 'props': per-prop 统计, 'pooled': 汇总}。"""
    if not entries:
        raise ValueError("桨型目录为空：先调用 load_catalog()")
    model = model or pm.ModelParams()

    point_rows: list[dict] = []
    per_prop: list[dict] = []
    for entry in entries:
        single = bench.benchmark(entry["rows"], model)
        for row in single["rows"]:
            point_rows.append(
                {
                    "prop": entry["prop"],
                    "brand": entry["brand"],
                    "series": entry["series"],
                    "brand_series": entry["brand_series"],
                    "diameter_in": entry["diameter_in"],
                    "pitch_in": entry["pitch_in"],
                    "file": entry["file"],
                    **row,
                    "data_note": CATALOG_DATA_NOTE,
                }
            )
        stats = single["stats"]
        ct_rels = [r["ct_rel_err"] for r in single["rows"]]
        cp_rels = [r["cp_rel_err"] for r in single["rows"]]
        ct_abs = [abs(v) for v in ct_rels]
        cp_abs = [abs(v) for v in cp_rels]
        per_prop.append(
            {
                "prop": entry["prop"],
                "display": entry["display"],
                "brand": entry["brand"],
                "series": entry["series"],
                "brand_series": entry["brand_series"],
                "diameter_in": entry["diameter_in"],
                "pitch_in": entry["pitch_in"],
                "file": entry["file"],
                "points": stats["points"],
                "rpm_min": stats["rpm_min"],
                "rpm_max": stats["rpm_max"],
                "ct_ref_mean": _mean([r["ct"] for r in entry["rows"]]),
                "ct_ref_min": min(r["ct"] for r in entry["rows"]),
                "ct_ref_max": max(r["ct"] for r in entry["rows"]),
                "cp_ref_mean": _mean([r["cp"] for r in entry["rows"]]),
                "cp_ref_min": min(r["cp"] for r in entry["rows"]),
                "cp_ref_max": max(r["cp"] for r in entry["rows"]),
                "ct_model_mean": _mean([r["ct_model"] for r in single["rows"]]),
                "cp_model_mean": _mean([r["cp_model"] for r in single["rows"]]),
                "ct_rel_err_mean": _mean(ct_rels),
                "ct_rel_err_mean_abs": _mean(ct_abs),
                "ct_rel_err_max_abs": max(ct_abs),
                "cp_rel_err_mean": _mean(cp_rels),
                "cp_rel_err_mean_abs": _mean(cp_abs),
                "cp_rel_err_max_abs": max(cp_abs),
                "all_positive": all(
                    r["ct"] > 0 and r["cp"] > 0 for r in entry["rows"]
                ),
            }
        )

    ct_rels_all = [r["ct_rel_err"] for r in point_rows]
    cp_rels_all = [r["cp_rel_err"] for r in point_rows]
    ct_abs_all = [abs(v) for v in ct_rels_all]
    cp_abs_all = [abs(v) for v in cp_rels_all]
    rpms = [r["rpm"] for r in point_rows]
    pooled = {
        "props": len(entries),
        "points": len(point_rows),
        "brand_count": len({e["brand"] for e in entries}),
        "series_count": len({e["brand_series"] for e in entries}),
        "rpm_min": min(rpms),
        "rpm_max": max(rpms),
        "ct_rel_err_mean": _mean(ct_rels_all),
        "ct_rel_err_mean_abs": _mean(ct_abs_all),
        "ct_rel_err_max_abs": max(ct_abs_all),
        "cp_rel_err_mean": _mean(cp_rels_all),
        "cp_rel_err_mean_abs": _mean(cp_abs_all),
        "cp_rel_err_max_abs": max(cp_abs_all),
        "ct_underestimated_props": sum(1 for p in per_prop if p["ct_rel_err_mean"] < 0),
        "cp_underestimated_props": sum(1 for p in per_prop if p["cp_rel_err_mean"] < 0),
        "all_positive": all(p["all_positive"] for p in per_prop),
    }
    return {"rows": point_rows, "props": per_prop, "pooled": pooled}


def write_point_csv(rows: list[dict], path: Path | str) -> Path:
    """写逐点 CSV（存在即报错，需调用方显式覆盖）。"""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"输出已存在：{path}（需显式覆盖）")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=POINT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in POINT_FIELDS})
    return path


def write_summary_csv(props: list[dict], path: Path | str) -> Path:
    """写逐桨统计 CSV（存在即报错，需调用方显式覆盖）。"""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"输出已存在：{path}（需显式覆盖）")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for prop in props:
            writer.writerow({key: prop[key] for key in SUMMARY_FIELDS})
    return path


def _import_pyplot():
    """加载 matplotlib（本项目 vendored 于 work/pylibs），使用无界面 Agg 后端。"""
    pylibs = PROJECT_ROOT / "work" / "pylibs"
    if pylibs.is_dir() and str(pylibs) not in sys.path:
        sys.path.insert(0, str(pylibs))
    try:
        import matplotlib
    except ImportError as exc:  # pragma: no cover - 环境缺依赖时给出可操作错误
        raise RuntimeError(
            "未找到 matplotlib；本项目依赖位于 work/pylibs（见 work/env/requirements.txt）"
        ) from exc
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def plot_catalog(
    result: dict,
    output_png: Path | str,
    overwrite: bool = False,
) -> Path:
    """绘制 CT/CP vs RPM 分组图（各桨 REFERENCE 曲线 + 通用 MODEL 曲线）。"""
    plt = _import_pyplot()

    output_png = Path(output_png)
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{output_png}（需 --overwrite）")
    output_png.parent.mkdir(parents=True, exist_ok=True)

    props = result["props"]
    rows = result["rows"]
    model = pm.ModelParams()
    model_rpm = sorted({r["rpm"] for r in rows})
    model_coeffs = bench.model_coefficients(model, model_rpm)

    colors = plt.colormaps["tab10"]
    markers = ["o", "s", "^", "v", "D", "P", "X"]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 5.2))
    for ax, ref_key, model_key, ylabel in (
        (axes[0], "ct_ref", "ct_model", "Thrust coefficient  C_T [-]"),
        (axes[1], "cp_ref", "cp_model", "Power coefficient  C_P [-]"),
    ):
        for index, prop in enumerate(props):
            points = [r for r in rows if r["prop"] == prop["prop"]]
            ax.plot(
                [p["rpm"] for p in points],
                [p[ref_key] for p in points],
                marker=markers[index % len(markers)],
                ms=4,
                lw=1.0,
                color=colors(index % 10),
                label=f"{prop['display']} (REFERENCE)",
            )
        ax.plot(
            model_rpm,
            [c[model_key] for c in model_coeffs],
            "k--",
            lw=1.8,
            label="generic model (MODEL, SIM)",
        )
        ax.set_xlabel("RPM [r/min]")
        ax.set_ylabel(ylabel)
        ax.grid(True, ls=":", alpha=0.6)
        ax.set_title(ylabel)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.tight_layout(rect=(0, 0.045, 1, 0.83))
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=4,
        fontsize=7.5,
        frameon=False,
        bbox_to_anchor=(0.5, 0.955),
    )
    fig.suptitle(
        "UIUC benchmark v0.2 — multi-prop static C_T/C_P vs generic-parameter model",
        fontsize=11,
        y=0.995,
    )
    fig.text(
        0.5,
        0.012,
        "REFERENCE (UIUC, measured) vs MODEL (SIM, generic params) — magnitude/trend check only",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color="dimgray",
    )
    fig.savefig(output_png, dpi=150)
    plt.close(fig)
    return output_png


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="UIUC 多桨型静态对标 v0.2（REFERENCE 实测 vs MODEL/SIM）"
    )
    parser.add_argument(
        "--reference-dir",
        default=str(REFERENCE_DIR),
        help="UIUC 静态数据镜像目录（默认 data/reference/uiuc）",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="指定文件名（默认 v0.2 的 7 个镜像样本）",
    )
    parser.add_argument(
        "--output",
        default="data/processed/uiuc_benchmark_v0.2.csv",
        help="逐点 CSV 输出（默认 data/processed/uiuc_benchmark_v0.2.csv）",
    )
    parser.add_argument(
        "--summary",
        default="data/processed/uiuc_benchmark_v0.2_summary.csv",
        help="逐桨统计 CSV 输出",
    )
    parser.add_argument(
        "--figure",
        default="data/processed/figures/uiuc_benchmark_v0.2.png",
        help="分组图 PNG 输出",
    )
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有产物")
    args = parser.parse_args(argv)

    output = _resolve(args.output)
    summary = _resolve(args.summary)
    figure = _resolve(args.figure)

    try:
        entries = load_catalog(args.reference_dir, args.files)
        result = benchmark_catalog(entries)
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}")
        return 2

    existing = [path for path in (output, summary, figure) if path.exists()]
    if existing and not args.overwrite:
        print("错误：产物已存在（" + " / ".join(str(p) for p in existing) + "）；如确需覆盖请加 --overwrite")
        return 2
    for path in existing:
        path.unlink()

    write_point_csv(result["rows"], output)
    write_summary_csv(result["props"], summary)
    plot_catalog(result, figure)

    pooled = result["pooled"]
    print(
        f"参考目录：{Path(args.reference_dir)}；桨型 {pooled['props']} 个"
        f"（{pooled['brand_count']} 品牌 / {pooled['series_count']} 系列），"
        f"数据点 {pooled['points']} 个，RPM {pooled['rpm_min']:g}–{pooled['rpm_max']:g}"
    )
    print("逐桨（REFERENCE=UIUC 实测；MODEL=通用参数 SIM）：")
    print(f"  {'prop':<12}{'pts':>4}  {'RPM range':<16}{'CT err':>9}{'CP err':>9}")
    for prop in result["props"]:
        print(
            f"  {prop['prop']:<12}{prop['points']:>4}  "
            f"{prop['rpm_min']:>6.0f}-{prop['rpm_max']:<9.0f}"
            f"{prop['ct_rel_err_mean_abs'] * 100:>8.2f}%"
            f"{prop['cp_rel_err_mean_abs'] * 100:>8.2f}%"
        )
    print(
        f"pooled：C_T 相对误差 均值 {pooled['ct_rel_err_mean_abs'] * 100:.2f}% / "
        f"最大 {pooled['ct_rel_err_max_abs'] * 100:.2f}%；"
        f"C_P 相对误差 均值 {pooled['cp_rel_err_mean_abs'] * 100:.2f}% / "
        f"最大 {pooled['cp_rel_err_max_abs'] * 100:.2f}%"
    )
    print(
        f"系统性偏差：C_T 被低估的桨 {pooled['ct_underestimated_props']}/{pooled['props']}；"
        f"C_P 被低估的桨 {pooled['cp_underestimated_props']}/{pooled['props']}"
    )
    print(f"CSV：{output}")
    print(f"CSV：{summary}")
    print(f"图件：{figure}")
    print("注意：REFERENCE 为 UIUC 真实风洞测量，MODEL 为通用参数仿真；仅作量级/趋势对标，不是实验验证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
