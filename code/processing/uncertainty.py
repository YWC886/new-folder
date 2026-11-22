"""效率不确定度传播 v0.1：标定/测量误差 → η_sys 的 Monte Carlo 置信区间。

输入：原始 CSV（串口 11 列协议）+ 标定 JSON（compute_efficiency 格式）。
方法：在稳态窗口上抽样误差因子（k、b、电压、电流、转速、空气密度），
逐样本重算 η_em / FM / η_sys，输出分位数、均值、标准差与单因素灵敏度贡献。
边界：SIM/REFERENCE 数据结果仍标注非实测；本工具不替代实机标定（D032/D035）。
"""
from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import compute_efficiency as ce  # noqa: E402

SCHEMA_VERSION = "0.1"
DEFAULT_N = 1000
DEFAULT_SEED = 20261122
# 1σ 相对误差假设（可由用户覆盖）：标定斜率、偏置、电压、电流、转速、空气密度
DEFAULT_SIGMAS = {
    "thrust_k": 0.005, "torque_k": 0.005, "thrust_b_rel": 0.002, "torque_b_rel": 0.002,
    "voltage": 0.005, "current": 0.005, "rpm": 0.001, "density": 0.01,
}


def _pct(values: list[float], q: float) -> float:
    s = sorted(values)
    if not s:
        return 0.0
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return s[int(k)]
    return s[lo] * (hi - k) + s[hi] * (k - lo)


def _nominal(rows: list[dict], calib: dict, rho: float) -> dict:
    kt, bt = calib["thrust"]["k"], calib["thrust"]["b"]
    kq, bq = calib["torque"]["k"], calib["torque"]["b"]
    d = calib.get("propeller", {}).get("diameter_m", 0.4572)
    area = math.pi * d * d / 4.0
    n = len(rows)
    s_t = sum(float(r["thrust_raw"]) for r in rows) / n
    s_q = sum(float(r["torque_raw"]) for r in rows) / n
    u = sum(float(r["voltage_v"]) for r in rows) / n
    i = sum(float(r["current_a"]) for r in rows) / n
    rpm = sum(float(r["rpm"]) for r in rows) / n
    t = kt * s_t + bt
    q = kq * s_q + bq
    w = 2 * math.pi * rpm / 60.0
    p_shaft = q * w
    p_elec = u * i
    eta_em = p_shaft / p_elec if p_elec else 0.0
    p_ideal = t**1.5 / math.sqrt(2 * rho * area) if t > 0 else 0.0
    fm = p_ideal / p_shaft if p_shaft else 0.0
    return {"thrust_n": t, "torque_nm": q, "p_shaft_w": p_shaft, "p_elec_w": p_elec,
            "eta_em": eta_em, "fm": fm, "eta_sys": fm * eta_em}


def propagate(rows: list[dict], calib: dict, *, rho: float, n: int = DEFAULT_N,
              seed: int = DEFAULT_SEED, sigmas: dict | None = None) -> dict:
    if n < 10:
        raise ValueError("n 至少为 10")
    sig = dict(DEFAULT_SIGMAS)
    if sigmas:
        sig.update(sigmas)
    rng = random.Random(seed)
    kt, bt = calib["thrust"]["k"], calib["thrust"]["b"]
    kq, bq = calib["torque"]["k"], calib["torque"]["b"]
    d = calib.get("propeller", {}).get("diameter_m", 0.4572)
    area = math.pi * d * d / 4.0
    m = len(rows)
    st = sum(float(r["thrust_raw"]) for r in rows) / m
    sq = sum(float(r["torque_raw"]) for r in rows) / m
    u0 = sum(float(r["voltage_v"]) for r in rows) / m
    i0 = sum(float(r["current_a"]) for r in rows) / m
    rev = sum(float(r["rpm"]) for r in rows) / m
    samples = {"eta_sys": [], "eta_em": [], "fm": [], "thrust_n": [], "p_elec_w": []}
    contrib = {k: [] for k in sig}
    for _ in range(n):
        e = {k: rng.gauss(0.0, v) for k, v in sig.items()}
        t = kt * (1 + e["thrust_k"]) * st * (1 + e["thrust_b_rel"]) + bt
        q = kq * (1 + e["torque_k"]) * sq * (1 + e["torque_b_rel"]) + bq
        u = u0 * (1 + e["voltage"])
        i = i0 * (1 + e["current"])
        rpm = rev * (1 + e["rpm"])
        rho_i = rho * (1 + e["density"])
        w = 2 * math.pi * rpm / 60.0
        p_shaft = q * w
        p_elec = u * i
        eta_em = p_shaft / p_elec
        p_ideal = t**1.5 / math.sqrt(2 * rho_i * area) if t > 0 else 0.0
        fm = p_ideal / p_shaft
        samples["eta_sys"].append(fm * eta_em)
        samples["eta_em"].append(eta_em)
        samples["fm"].append(fm)
        samples["thrust_n"].append(t)
        samples["p_elec_w"].append(p_elec)
    nominal = _nominal(rows, calib, rho)
    eta = samples["eta_sys"]
    mean = sum(eta) / n
    var = sum((x - mean) ** 2 for x in eta) / (n - 1)
    # 单因素灵敏度：固定其它因素为 0，计算 1σ 下 η_sys 的标准差
    for key in sig:
        vals = []
        for _ in range(n):
            e = {k: 0.0 for k in sig}
            e[key] = rng.gauss(0.0, sig[key])
            t = kt * (1 + e["thrust_k"]) * st * (1 + e["thrust_b_rel"]) + bt
            q = kq * (1 + e["torque_k"]) * sq * (1 + e["torque_b_rel"]) + bq
            u = u0 * (1 + e["voltage"])
            i = i0 * (1 + e["current"])
            rpm = rev * (1 + e["rpm"])
            rho_i = rho * (1 + e["density"])
            w = 2 * math.pi * rpm / 60.0
            p_shaft = q * w
            p_elec = u * i
            eta_em = p_shaft / p_elec
            p_ideal = t**1.5 / math.sqrt(2 * rho_i * area) if t > 0 else 0.0
            fm = p_ideal / p_shaft
            vals.append(fm * eta_em)
        mu = sum(vals) / n
        contrib[key] = math.sqrt(sum((x - mu) ** 2 for x in vals) / (n - 1))
    return {
        "schema_version": SCHEMA_VERSION,
        "n": n, "seed": seed, "sigmas": sig, "rho": rho,
        "nominal": nominal,
        "eta_sys": {"mean": mean, "std": math.sqrt(var),
                    "p2_5": _pct(eta, 0.025), "p50": _pct(eta, 0.5), "p97_5": _pct(eta, 0.975)},
        "eta_em": {"mean": sum(samples["eta_em"]) / n, "std": _std(samples["eta_em"])},
        "fm": {"mean": sum(samples["fm"]) / n, "std": _std(samples["fm"])},
        "thrust_n": {"mean": sum(samples["thrust_n"]) / n, "std": _std(samples["thrust_n"])},
        "p_elec_w": {"mean": sum(samples["p_elec_w"]) / n, "std": _std(samples["p_elec_w"])},
        "sensitivity_1sigma_eta_sys": {k: v for k, v in contrib.items()},
    }


def _std(values: list[float]) -> float:
    mu = sum(values) / len(values)
    return math.sqrt(sum((x - mu) ** 2 for x in values) / (len(values) - 1))


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="η_sys Monte Carlo uncertainty propagation")
    parser.add_argument("--input", required=True, help="原始 CSV（11 列协议）")
    parser.add_argument("--calib", required=True, help="标定 JSON")
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--rho", type=float, default=1.204)
    parser.add_argument("--output", default=str(PROJECT_ROOT / "data/metadata/uncertainty_v0.1.json"))
    args = parser.parse_args(argv)
    try:
        parsed = ce._parse_rows(Path(args.input))
        rows = [dict(r["values"]) if isinstance(r, dict) and "values" in r else dict(r) for r in parsed]
        last = max(float(r["elapsed_s"]) for r in rows)
        window = [r for r in rows if float(r["elapsed_s"]) >= last - 3.0]
        calib = ce.load_calibration(Path(args.calib))
        report = propagate(window, calib, rho=args.rho, n=args.n, seed=args.seed)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    print(f"η_sys MC：mean={report['eta_sys']['mean']:.4f} std={report['eta_sys']['std']:.4f} "
          f"95%CI=[{report['eta_sys']['p2_5']:.4f}, {report['eta_sys']['p97_5']:.4f}]")
    print(f"名义值 η_sys={report['nominal']['eta_sys']:.4f}；输出 {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
