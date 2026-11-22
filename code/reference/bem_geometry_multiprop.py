"""BEM 等效几何的跨桨可迁移性检验（REFERENCE-GEOM，留一桨型视角）。

对 UIUC 7 个桨型各自做 c/R × P 网格反演，比较最优点参数是否稳定。
输出：data/processed/bem_geometry_multiprop_v0.1.csv
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (HERE, ROOT / "work" / "pylibs"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bem_geometry_fit as fit  # noqa: E402
import bem_propeller as bem  # noqa: E402
import uiuc_propdb  # noqa: E402
from catalog_uiuc import DEFAULT_CATALOG_FILES  # noqa: E402

OUT = ROOT / "data" / "processed" / "bem_geometry_multiprop_v0.1.csv"
C_GRID = (0.05, 0.075, 0.10, 0.125, 0.15)
P_FACTORS = (0.75, 0.90, 1.00, 1.10, 1.25)


def main() -> int:
    catalog = ROOT / "data" / "reference" / "uiuc"
    rows_out = []
    for name in sorted(DEFAULT_CATALOG_FILES):
        path = catalog / name
        rows = uiuc_propdb.load_static(path)
        label = uiuc_propdb.parse_prop_label(path)
        pitch_nom = float(label["pitch_in"]) * 0.0254
        diameter = float(label["diameter_in"]) * 0.0254
        base_params = bem.BemParams(diameter_m=diameter, pitch_m=pitch_nom)
        base_ct, base_cp = fit.mae(base_params, rows)
        best = None
        for c in C_GRID:
            for f in P_FACTORS:
                p = bem.BemParams(diameter_m=diameter, pitch_m=pitch_nom * f, chord_ratio=c)
                ct, cp = fit.mae(p, rows)
                score = (ct + cp) / 2.0
                if best is None or score < best[0]:
                    best = (score, c, f, ct, cp)
        assert best is not None
        score, c, f, ct, cp = best
        rows_out.append({
            "prop": name,
            "display": label["display"],
            "diameter_in": label["diameter_in"],
            "pitch_in": label["pitch_in"],
            "baseline_ct_mae": round(base_ct, 2),
            "baseline_cp_mae": round(base_cp, 2),
            "best_chord_ratio": c,
            "best_pitch_factor": f,
            "best_ct_mae": round(ct, 2),
            "best_cp_mae": round(cp, 2),
        })
        print(f"{name:24s} base {base_ct:5.1f}/{base_cp:5.1f}  best c={c:.3f} f={f:.2f} -> {ct:5.1f}/{cp:5.1f}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)
    cs = [r["best_chord_ratio"] for r in rows_out]
    fs = [r["best_pitch_factor"] for r in rows_out]
    print(f"c/R: min {min(cs):.3f} max {max(cs):.3f}; pitch factor: min {min(fs):.2f} max {max(fs):.2f}")
    print("CSV:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
