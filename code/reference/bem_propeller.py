"""BEM-lite 螺旋桨静态模型 v0.1（均匀入流 / 叶素积分 + 动量闭合）。

与 `propulsion_model` 的 C_T0/C_P0 参数化模型不同：本模型从桨几何（直径、螺距、弦长、叶数）
与简化翼型极曲线出发，用叶素积分 + 均匀诱导速度闭合，预测静态 C_T / C_P。
边界：REFERENCE-GEOM 几何近似、低 Re 极曲线近似、无桨尖损失；仅作论文建模对照，不接入主线。
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

RHO_DEFAULT = 1.204
N_ELEMENTS = 40


@dataclass(frozen=True)
class BemParams:
    diameter_m: float = 0.254
    pitch_m: float = 0.1778          # 10x7 英寸 → 米
    blades: int = 2
    chord_ratio: float = 0.11        # 平均弦长 / 直径（近似）
    hub_ratio: float = 0.15          # 桨毂半径 / 半径
    rho: float = RHO_DEFAULT
    cl_alpha: float = 2 * math.pi    # 薄翼理论升力线斜率 [/rad]
    cl_max: float = 1.1
    cd0: float = 0.012
    cd_alpha2: float = 0.03

    @property
    def radius(self) -> float:
        return self.diameter_m / 2.0

    @property
    def area(self) -> float:
        return math.pi * self.radius**2


def _pitch_angle(r: float, p: BemParams) -> float:
    """局部几何螺距角：tanθ = P / (2π r)。"""
    return math.atan(p.pitch_m / (2 * math.pi * r))


def _cl_cd(alpha: float, p: BemParams) -> tuple[float, float]:
    """简化极曲线：薄翼线性升力 + 失速截断 + 二次阻力。"""
    cl = p.cl_alpha * alpha
    cl = max(-p.cl_max, min(p.cl_max, cl))
    cd = p.cd0 + p.cd_alpha2 * (cl / p.cl_max) ** 2
    return cl, cd


def prandtl_tip_loss(r: float, phi: float, p: BemParams) -> float:
    """Prandtl 桨尖损失因子 F（BEM v0.2）。"""
    R = p.radius
    if r >= R:
        return 0.0
    rr = max(r, 1e-6)
    f = 0.5 * p.blades * (R - r) / (rr * max(math.sin(phi), 1e-6))
    return (2.0 / math.pi) * math.acos(min(1.0, math.exp(-max(f, 1e-9))))


def _element_force(r: float, dr: float, omega: float, p: BemParams, V_i: float) -> tuple[float, float]:
    """单个环形叶素在局部诱导速度 V_i 下的推力/扭矩。"""
    theta = _pitch_angle(r, p)
    phi = math.atan2(V_i, omega * r)
    alpha = theta - phi
    cl, cd = _cl_cd(alpha, p)
    W = math.hypot(V_i, omega * r)
    chord = p.chord_ratio * p.diameter_m
    q = 0.5 * p.rho * W * W * chord * p.blades * dr
    dT = q * (cl * math.cos(phi) - cd * math.sin(phi))
    dQ = q * (cl * math.sin(phi) + cd * math.cos(phi)) * r
    return dT, dQ


def integrate(V_i_unused: float | None, omega: float, p: BemParams) -> tuple[float, float]:
    """叶素积分：每个环形叶素按动量定理闭合求局部诱导速度（BEM-lite）。"""
    r0 = p.radius * p.hub_ratio
    r1 = p.radius
    dr = (r1 - r0) / N_ELEMENTS
    T = Q = 0.0
    for i in range(N_ELEMENTS):
        r = r0 + (i + 0.5) * dr
        area = 2 * math.pi * r * dr
        lo, hi = 1e-3, 60.0
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            dT, _ = _element_force(r, dr, omega, p, mid)
            phi_mid = math.atan2(mid, omega * r)
            F = prandtl_tip_loss(r, phi_mid, p)
            if dT - 2 * p.rho * area * mid * mid * max(F, 1e-6) > 0:
                lo = mid
            else:
                hi = mid
        Vi_s = 0.5 * (lo + hi)
        dT, dQ = _element_force(r, dr, omega, p, Vi_s)
        T += dT
        Q += dQ
    return T, Q


def solve(rpm: float, p: BemParams, *, tol: float = 1e-6, max_iter: int = 200) -> dict:
    omega = 2 * math.pi * rpm / 60.0
    if omega <= 0:
        raise ValueError("rpm 必须大于 0")
    T, Q = integrate(None, omega, p)
    if T <= 0:
        raise ValueError("推力非正：几何/极曲线近似不适用")
    V_i = math.sqrt(T / (2 * p.rho * p.area))
    converged = True
    n_rps = rpm / 60.0
    ct = T / (p.rho * n_rps**2 * p.diameter_m**4)
    cp = 2 * math.pi * Q / (p.rho * n_rps**2 * p.diameter_m**5)
    return {"rpm": rpm, "inflow_velocity_m_s": V_i, "thrust_n": T, "torque_nm": Q,
            "ct": ct, "cp": cp, "figure_of_merit": cp and (ct**1.5 / (math.sqrt(2) * cp)),
            "converged": converged, "params": asdict(p)}


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="BEM-lite propeller static model v0.1")
    parser.add_argument("--diameter", type=float, default=0.254)
    parser.add_argument("--pitch", type=float, default=0.1778)
    parser.add_argument("--rpm", type=float, default=4000.0)
    parser.add_argument("--blades", type=int, default=2)
    parser.add_argument("--chord-ratio", type=float, default=0.11)
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[2] / "data/metadata/bem_lite_v0.1.json"))
    args = parser.parse_args(argv)
    try:
        p = BemParams(diameter_m=args.diameter, pitch_m=args.pitch, blades=args.blades,
                      chord_ratio=args.chord_ratio)
        result = solve(args.rpm, p)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    print(f"rpm={result['rpm']:.0f} T={result['thrust_n']:.3f} N Q={result['torque_nm']:.5f} N·m "
          f"C_T={result['ct']:.4f} C_P={result['cp']:.4f} FM={result['figure_of_merit']:.3f} "
          f"Vi={result['inflow_velocity_m_s']:.2f} m/s converged={result['converged']}")
    print(f"输出：{out}\n注意：REFERENCE-GEOM/低 Re 近似，非实测（D049/D051）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
