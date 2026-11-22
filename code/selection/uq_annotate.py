"""给选型输出（match/gp_match/multiobjective）补 D056 统一口径列 v0.1。

输入：选型 CSV（含 voltage_set_v/throttle_set_pct 与 eta_sys 或 eta_pred；σ 列 eta_std/gp_std_eta 可选）
      runs CSV（提供 U(k=2) 列 u_eta_sys_k2）
输出：同表 + u_meas / sigma_total / eta_cons_2sigma / eta_cons_1sigma / uq_note
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (HERE, ROOT / "work" / "pylibs", ROOT / "code" / "processing"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from uq_utils import combine_sigma, from_u2  # noqa: E402

UQ_NOTE = "D056 统一口径（u_meas=U/2, σ_total=方差合成）；SIM/REFERENCE 代理，非实测结论"


def _f(row: dict, names: tuple[str, ...]) -> float | None:
    for n in names:
        v = row.get(n)
        if v not in (None, ""):
            try:
                return float(v)
            except ValueError:
                continue
    return None


def load_u2(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        v = _f(r, ("voltage_set_v", "voltage_v"))
        t = _f(r, ("throttle_set_pct", "throttle"))
        u2 = _f(r, ("u_eta_sys_k2", "u_eta_sys"))
        if None not in (v, t, u2):
            out.append({"v": v, "t": t, "u2": u2})
    return out


def annotate(sel_rows: list[dict], u2_rows: list[dict]) -> list[dict]:
    out = []
    for r in sel_rows:
        v = _f(r, ("voltage_set_v", "voltage_v"))
        t = _f(r, ("throttle_set_pct", "throttle"))
        eta = _f(r, ("eta_sys", "eta_pred", "eta_sys_mean"))
        std = _f(r, ("eta_std", "gp_std_eta"))
        if None in (v, t, eta):
            raise ValueError("选型表缺少电压/油门/效率列")
        best = min(u2_rows, key=lambda x: (x["v"] - v) ** 2 + ((x["t"] - t) / 10.0) ** 2) if u2_rows else None
        u2 = best["u2"] if best else 0.0
        u_meas = from_u2(u2)
        sigma = std if std is not None else 0.0
        sigma_total = combine_sigma(u_meas, sigma)
        row = dict(r)
        row.update({
            "u_meas": round(u_meas, 6),
            "sigma_total": round(sigma_total, 6),
            "eta_cons_2sigma": round(eta - 2.0 * sigma_total, 6),
            "eta_cons_1sigma": round(eta - sigma_total, 6),
            "uq_note": UQ_NOTE,
        })
        out.append(row)
    out.sort(key=lambda x: -float(x["eta_cons_2sigma"]))
    return out


def write_csv(rows: list[dict], output: Path, *, overwrite: bool = False) -> Path:
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with output.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return output


def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="选型输出补 D056 口径列")
    p.add_argument("--input", required=True)
    p.add_argument("--runs", default=str(ROOT / "data/processed/efficiency_map_runs.csv"))
    p.add_argument("--output", required=True)
    p.add_argument("--overwrite", action="store_true")
    a = p.parse_args(argv)
    try:
        with Path(a.input).open(encoding="utf-8-sig") as fh:
            sel_rows = list(csv.DictReader(fh))
        u2_rows = load_u2(Path(a.runs))
        if not sel_rows:
            raise ValueError("选型表为空")
        rows = annotate(sel_rows, u2_rows)
        write_csv(rows, Path(a.output), overwrite=a.overwrite)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"错误：{exc}")
        return 2
    print(f"标注 {len(rows)} 行 → {a.output}")
    for r in rows[:3]:
        print(f"  eta_cons(2σ)={r['eta_cons_2sigma']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
