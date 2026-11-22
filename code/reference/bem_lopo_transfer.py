"""留一桨型全局修正迁移检验（REFERENCE-GEOM, BEM v0.4）。

对每个桨型留出，在其余 6 桨上选择一组全局修正（弦长比缩放 × 桨距因子），
再在被留出桨上验证：若 ≤20% 才可写入论文"可接受对照"。
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

OUT = ROOT / "data" / "processed" / "bem_lopo_transfer_v0.1.csv"
C_SCALES = (0.70, 0.80)
P_FACTORS = (1.05, 1.15)


def prop_spec(name: str):
    path = ROOT / "data" / "reference" / "uiuc" / name
    rows = uiuc_propdb.load_static(path)
    label = uiuc_propdb.parse_prop_label(path)
    return rows, float(label["diameter_in"]) * 0.0254, float(label["pitch_in"]) * 0.0254


def err(rows, diameter, pitch, c_scale, p_factor):
    params = bem.BemParams(diameter_m=diameter, pitch_m=pitch * p_factor,
                           chord_ratio=0.11 * c_scale)
    return fit.mae(params, rows)


def main() -> int:
    specs = {name: prop_spec(name) for name in sorted(DEFAULT_CATALOG_FILES)}
    names = list(specs)
    out = []
    for held in names:
        train = [n for n in names if n != held]
        best = None
        for cs in C_SCALES:
            for pf in P_FACTORS:
                tot = sum(sum(err(*specs[n], cs, pf)) for n in train)
                if best is None or tot < best[0]:
                    best = (tot, cs, pf)
        assert best is not None
        _, cs, pf = best
        rows, dia, pitch = specs[held]
        base_ct, base_cp = err(rows, dia, pitch, 1.0, 1.0)
        corr_ct, corr_cp = err(rows, dia, pitch, cs, pf)
        out.append({
            "held_out": held, "c_scale": cs, "p_factor": pf,
            "base_ct_mae": round(base_ct, 2), "base_cp_mae": round(base_cp, 2),
            "corr_ct_mae": round(corr_ct, 2), "corr_cp_mae": round(corr_cp, 2),
        })
        print(f"{held:24s} c×{cs:.2f} P×{pf:.2f}  {base_ct:5.1f}/{base_cp:5.1f} -> {corr_ct:5.1f}/{corr_cp:5.1f}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    mc = sum(r["corr_ct_mae"] for r in out) / len(out)
    mp = sum(r["corr_cp_mae"] for r in out) / len(out)
    bc = sum(r["base_ct_mae"] for r in out) / len(out)
    bp = sum(r["base_cp_mae"] for r in out) / len(out)
    print(f"POOLED base {bc:.1f}/{bp:.1f} -> LOPO-corrected {mc:.1f}/{mp:.1f}")
    print("CSV:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
