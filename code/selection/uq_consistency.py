"""UQ 口径一致性：把测量 U(k=2) 与 GP σ 合成为统一保守效率（D056 前置）v0.1。

输入：
- runs CSV（含 voltage_set_v/throttle_set_pct/eta_sys_mean|eta_sys/u_eta_sys_k2）
- surface CSV（含 voltage_set_v/throttle_set_pct/eta_pred|eta_sys_mean/eta_std）
按 (电压,油门) 最近邻匹配，输出统一口径对比表。
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for _p in (HERE, ROOT / "work" / "pylibs"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    from uq_utils import combine_sigma, from_u2
except ImportError:  # 当作为脚本从项目根运行时
    sys.path.insert(0, str(ROOT / "code" / "processing"))
    from uq_utils import combine_sigma, from_u2  # type: ignore

OUT_FIELDS = [
    "voltage_set_v", "throttle_set_pct", "eta_obs", "u_eta_sys_k2",
    "eta_pred", "eta_std", "u_meas", "sigma_total",
    "eta_cons_2sigma", "eta_cons_1sigma", "data_note",
]
DATA_NOTE = "UQ 口径统一（SIM/REFERENCE 代理）：测量 U(k=2) 与 GP σ 合成，非实测结论"


def _pick(row: dict, names: tuple[str, ...]) -> float | None:
    for n in names:
        if n in row and row[n] not in ("", None):
            try:
                return float(row[n])
            except ValueError:
                continue
    return None


def load_runs(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        v = _pick(r, ("voltage_set_v", "voltage_v"))
        t = _pick(r, ("throttle_set_pct", "throttle"))
        eta = _pick(r, ("eta_sys_mean", "eta_sys"))
        u2 = _pick(r, ("u_eta_sys_k2", "u_eta_sys"))
        if None in (v, t, eta):
            continue
        out.append({"v": v, "t": t, "eta": eta, "u2": u2})
    return out


def load_surface(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        v = _pick(r, ("voltage_set_v", "voltage_v"))
        t = _pick(r, ("throttle_set_pct", "throttle"))
        eta = _pick(r, ("eta_pred", "eta_sys_mean", "eta_sys"))
        std = _pick(r, ("eta_std", "gp_std_eta"))
        if None in (v, t, eta, std):
            continue
        out.append({"v": v, "t": t, "eta": eta, "std": std})
    return out


def match(runs: list[dict], surface: list[dict]) -> list[dict]:
    out = []
    for run in runs:
        best = min(surface, key=lambda s: (s["v"] - run["v"]) ** 2 + ((s["t"] - run["t"]) / 10.0) ** 2)
        u_meas = from_u2(run["u2"]) if run["u2"] is not None else 0.0
        sigma_total = combine_sigma(u_meas, best["std"])
        out.append({
            "voltage_set_v": run["v"], "throttle_set_pct": run["t"],
            "eta_obs": run["eta"], "u_eta_sys_k2": run["u2"],
            "eta_pred": best["eta"], "eta_std": best["std"],
            "u_meas": u_meas, "sigma_total": sigma_total,
            "eta_cons_2sigma": best["eta"] - 2.0 * sigma_total,
            "eta_cons_1sigma": best["eta"] - sigma_total,
            "data_note": DATA_NOTE,
        })
    out.sort(key=lambda r: (-r["eta_cons_2sigma"]))
    return out


def write_csv(rows: list[dict], output: Path, *, overwrite: bool = False) -> Path:
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{output}（加 --overwrite 覆盖）")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return output


def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="UQ 口径一致性（测量 U(k=2) + GP σ）")
    p.add_argument("--runs", default=str(ROOT / "data/processed/efficiency_map_runs.csv"))
    p.add_argument("--surface", default=str(ROOT / "data/processed/efficiency_map_surface_v0.4.csv"))
    p.add_argument("--output", default=str(ROOT / "data/processed/selection_uq_consistency_v0.1.csv"))
    p.add_argument("--overwrite", action="store_true")
    a = p.parse_args(argv)
    try:
        runs = load_runs(Path(a.runs))
        surf = load_surface(Path(a.surface))
        if not runs or not surf:
            raise ValueError("输入为空或缺少必需列")
        rows = match(runs, surf)
        write_csv(rows, Path(a.output), overwrite=a.overwrite)
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}")
        return 2
    print(f"候选 {len(rows)} 行 → {a.output}")
    for r in rows[:5]:
        print(f"  {r['voltage_set_v']:g}V/{r['throttle_set_pct']:g}% eta={r['eta_pred']:.4f} "
              f"σ_total={r['sigma_total']:.4f} cons2σ={r['eta_cons_2sigma']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
