"""BEM 几何细化筛选：以等效弦长比/等效桨距拟合 APC 10x7E（REFERENCE 单桨校准，不泛化）。"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "code" / "reference", ROOT / "work" / "pylibs"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bem_propeller as bem  # noqa: E402
import uiuc_propdb  # noqa: E402

SAMPLE = ROOT / "data" / "reference" / "uiuc" / "apce_10x7_static_pg0811.txt"
OUT_CSV = ROOT / "data" / "processed" / "bem_geometry_fit_v0.1.csv"
OUT_FIG = ROOT / "data" / "processed" / "figures" / "bem_geometry_fit_v0.1.png"
D = 0.254
P = 0.1778


def mae(params: bem.BemParams, rows: list[dict]) -> tuple[float, float]:
    ce, cpe = [], []
    for r in rows:
        m = bem.solve(r["rpm"], params)
        ce.append(abs(m["ct"] - r["ct"]) / r["ct"])
        cpe.append(abs(m["cp"] - r["cp"]) / r["cp"])
    return sum(ce) / len(ce) * 100.0, sum(cpe) / len(cpe) * 100.0


def main() -> int:
    rows = uiuc_propdb.load_static(SAMPLE)
    grid = []
    best = None
    for c in [0.07 + 0.01 * i for i in range(9)]:          # 0.07..0.15
        for p in [0.140 + 0.005 * i for i in range(17)]:   # 0.140..0.220
            params = bem.BemParams(diameter_m=D, pitch_m=p, chord_ratio=c)
            ct_mae, cp_mae = mae(params, rows)
            score = (ct_mae + cp_mae) / 2.0
            grid.append({"chord_ratio": round(c, 3), "pitch_m": round(p, 4),
                         "ct_mae_pct": round(ct_mae, 2), "cp_mae_pct": round(cp_mae, 2),
                         "score": round(score, 2)})
            if best is None or score < best["score"]:
                best = dict(grid[-1])
    base = bem.BemParams(diameter_m=D, pitch_m=P, chord_ratio=0.11)
    b_ct, b_cp = mae(base, rows)
    print(f"baseline (c=0.11, P=0.1778): CT {b_ct:.1f}% CP {b_cp:.1f}%")
    print(f"best fit: {best['chord_ratio']} / {best['pitch_m']}: CT {best['ct_mae_pct']}% CP {best['cp_mae_pct']}%")
    print(f"candidates: {len(grid)} (grid scan)")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_CSV.write_text("\ufeff", encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(grid[0].keys()))
        w.writeheader()
        w.writerows(grid)

    try:
        import matplotlib

        matplotlib.use("Agg")
        sys.path.insert(0, str(ROOT / "work" / "pylibs"))
        import matplotlib.pyplot as plt

        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
        fig, ax = plt.subplots(figsize=(7.2, 4.4))
        best_ct = best["ct_mae_pct"]
        bars = [b_ct, b_cp, best_ct, best["cp_mae_pct"]]
        ax.bar(["基线 CT", "基线 CP", "拟合 CT", "拟合 CP"], bars,
               color=["#7f9fbf", "#7f9fbf", "#d98b5f", "#d98b5f"])
        for i, v in enumerate(bars):
            ax.text(i, v + 0.6, f"{v:.1f}%", ha="center", fontsize=9)
        ax.set_ylabel("平均绝对误差 [%]")
        ax.set_title("BEM 几何细化筛选：等效弦长/桨距拟合（APC 10x7E，REFERENCE）")
        ax.text(0.5, -0.16, "REFERENCE-GEOM 校准结果，单桨拟合，不构成实测或泛化结论（D053）",
                transform=ax.transAxes, ha="center", color="crimson", fontsize=8.5)
        fig.tight_layout()
        fig.savefig(OUT_FIG, dpi=140)
        plt.close(fig)
        print("figure:", OUT_FIG.relative_to(ROOT))
    except Exception as exc:  # noqa: BLE001
        print("figure skipped:", exc)
    print("csv:", OUT_CSV.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
