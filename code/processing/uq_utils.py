"""不确定度口径换算与合成（UQ 口径统一，D056 前置工具）v0.1。

约定（见 docs/plan/Round20推进计划_UQ与DoE口径统一_v0.1.md）：
- 测量侧对外报 U(k=2)，1σ 为 U/2；
- 模型/代理侧为 σ（1σ）；
- 合成 σ_total = sqrt(Σσᵢ²)；
- 保守效率 η_cons = η − 2·σ_total（95% 单侧近似），1σ 版本 η − σ_total。
"""
from __future__ import annotations

import math

SCHEMA_VERSION = "0.1"


def from_u2(u2: float) -> float:
    """U(k=2) → 1σ。"""
    if u2 < 0:
        raise ValueError("u2 不能为负")
    return u2 / 2.0


def to_u2(sigma: float) -> float:
    """1σ → U(k=2)。"""
    if sigma < 0:
        raise ValueError("sigma 不能为负")
    return 2.0 * sigma


def combine_sigma(*sigmas: float) -> float:
    """多个 1σ 分量按平方和开方合成。"""
    total = 0.0
    for s in sigmas:
        if s < 0:
            raise ValueError("sigma 分量不能为负")
        total += s * s
    return math.sqrt(total)


def conservative_eta(eta: float, *, u2: float = 0.0, sigma_model: float = 0.0,
                     k: float = 2.0) -> dict:
    """返回统一口径的保守效率：{eta, u_meas, sigma_model, sigma_total, eta_cons, eta_cons_1sigma}。"""
    u_meas = from_u2(u2)
    sigma_total = combine_sigma(u_meas, sigma_model)
    return {
        "eta": eta,
        "u_meas": u_meas,
        "sigma_model": sigma_model,
        "sigma_total": sigma_total,
        "eta_cons": eta - k * sigma_total,
        "eta_cons_1sigma": eta - sigma_total,
    }


def integrate_u2(eta: float, sigma_mc: float, u_k2: float, *, k: float = 2.0) -> dict:
    """把测量扩展不确定度 U(k=2) 与 MC 标准差合成（D056）。"""
    if u_k2 < 0 or sigma_mc < 0 or k <= 0:
        raise ValueError("u_k2/sigma_mc 必须非负、k 必须为正")
    u_meas = from_u2(u_k2)
    sigma_total = combine_sigma(u_meas, sigma_mc)
    return {
        "u_k2": u_k2,
        "u_meas": u_meas,
        "sigma_mc": sigma_mc,
        "sigma_total": sigma_total,
        "eta_cons_2sigma": eta - 2.0 * sigma_total,
        "eta_cons_1sigma": eta - sigma_total,
    }
