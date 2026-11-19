# -*- coding: utf-8 -*-
r"""电机—螺旋桨—电调系统静态悬停物理模型（仿真建模 v0.1 / v0.2 扩展）。

用途：为效率地图流水线生成**物理上自洽**的合成工况数据；不是实验结果。
模型假设（详见 docs/design/simulation_model_v0.1.md、v0.2.md）：
1. 直流电机稳态：V_eff = V_bus·throttle（理想 PWM），反电动势 E = Ke·ω，电流 I = (V_eff - E)/R；
2. 电磁转矩 Q_m = Kt·I；Kt = Ke = 60/(2π·KV)（SI 单位下数值相等）；
3. 摩擦/风阻等效为常值阻力矩 Q_f = Kt·I0（简化，未建风阻随转速项）；
4. 螺旋桨静态特性：T = Ct·ρ·n²·D⁴，P = Cp·ρ·n³·D⁵，Q_p = P/(2πn)；
   Ct/Cp 对转速做弱修正（雷诺数效应）：Ct ∝ n^α_ct，Cp ∝ n^α_cp；
5. 电调效率 η_esc 随电流二次下降：η_esc = clamp(η0 - k·(I/I_rated)², 0.85, 0.99)；
6. 稳态方程解一元二次方程求 n（对 Ct/Cp 的转速依赖做不动点迭代）；
7. 空气密度由环境温压按理想气体计算（R=287.05 J/(kg·K)）。
v0.2 扩展（可选 PackModel，默认关闭以保持 v0.1 行为）：
8. 电池包内阻压降：V_bus = V_oc − I_batt·R_pack（R_pack = 节数 × 单节内阻）；
9. 电机温升一阶稳态：T_motor = T_amb + R_th·k_loss·P_loss（P_loss = P_elec − P_shaft）；
10. 铜绕组温漂：R_hot = R_20·(1 + α_Cu·(T_motor − 20))，与 8/9 联立不动点迭代。

运行示例：
    py -3.12 code\simulation\propulsion_model.py --voltage 22.2 --throttle 0.5
    py -3.12 code\simulation\propulsion_model.py --voltage 22.2 --throttle 1.0 --pack-cells 6
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

R_SPECIFIC_AIR = 287.05


def air_density(temp_c: float, pressure_kpa: float) -> float:
    if pressure_kpa <= 0:
        raise ValueError("pressure_kpa 必须 > 0")
    if temp_c <= -273.15:
        raise ValueError("temp_c 必须 > -273.15")
    return pressure_kpa * 1000.0 / (R_SPECIFIC_AIR * (temp_c + 273.15))


@dataclass(frozen=True)
class ModelParams:
    """模型参数（v0.1：10 英寸桨 + 400KV 电机的典型量级）。

    参数是"文献量级 + 工程取值"，不是任何具体产品的实测参数；换真实型号需重新标定。
    """

    diameter_m: float = 0.2544  # 10 英寸
    ct0: float = 0.110  # 桨推力系数（参考转速下）
    cp0: float = 0.0450  # 桨功率系数（参考转速下）
    kv_rpm_per_v: float = 400.0
    resistance_ohm: float = 0.08
    no_load_current_a: float = 1.2
    esc_rated_a: float = 40.0
    esc_eta_base: float = 0.985
    esc_eta_loss_coeff: float = 0.015
    reynolds_ct_exp: float = -0.02
    reynolds_cp_exp: float = -0.035
    n_ref_rev_s: float = 100.0
    ambient_temp_c: float = 24.0
    pressure_kpa: float = 96.0

    @property
    def kt(self) -> float:
        """转矩常数 [N·m/A]。"""
        return 60.0 / (2.0 * math.pi * self.kv_rpm_per_v)

    @property
    def ke(self) -> float:
        """反电动势常数 [V·s/rad]（SI 下与 kt 数值相等）。"""
        return self.kt

    @property
    def disk_area_m2(self) -> float:
        return math.pi * self.diameter_m**2 / 4.0

    def air_density(self) -> float:
        return air_density(self.ambient_temp_c, self.pressure_kpa)


@dataclass(frozen=True)
class PackModel:
    """v0.2 电池包 + 电机热模型参数（工程量级，非具体产品实测）。

    voltage_v 仍表示"电池开路电压/名义电压"；启用后求解母线电压压降与温升。
    """

    cells: int = 6
    cell_nominal_voltage_v: float = 3.7
    cell_internal_resistance_ohm: float = 0.008
    motor_thermal_resistance_k_per_w: float = 2.5
    thermal_share_of_losses: float = 0.7
    winding_temp_ref_c: float = 20.0
    copper_temp_coeff_per_c: float = 0.00393

    @property
    def pack_resistance_ohm(self) -> float:
        return self.cells * self.cell_internal_resistance_ohm


def _solve_fixed_voltage_point(
    model: ModelParams,
    voltage_bus: float,
    throttle: float,
    density: float,
    resistance_ohm: float,
    max_iter: int,
    tol: float,
) -> dict:
    """给定母线电压与电机电阻，解稳态转速并返回 v0.1 全部物理量（内部函数）。"""
    kt = model.kt
    ke = model.ke
    diameter = model.diameter_m
    v_eff = voltage_bus * throttle
    q_f = kt * model.no_load_current_a
    b = kt * ke * 2.0 * math.pi / resistance_ohm
    # 初值：空载转速上界
    n = v_eff / (ke * 2.0 * math.pi)
    n = max(n, 1e-3)

    for _ in range(max_iter):
        ratio = max(n, 1e-6) / model.n_ref_rev_s
        ct = model.ct0 * ratio ** model.reynolds_ct_exp
        cp = model.cp0 * ratio ** model.reynolds_cp_exp
        a = (cp / (2.0 * math.pi)) * density * diameter**5
        c = q_f - kt * v_eff / resistance_ohm
        discriminant = b * b - 4.0 * a * c
        if discriminant < 0:
            raise ValueError("稳态方程无实根：检查参数或输入（可能电压过低/阻力矩过大）")
        n_new = (-b + math.sqrt(discriminant)) / (2.0 * a)
        if abs(n_new - n) < tol:
            n = n_new
            break
        n = n_new
    else:
        raise ValueError("转速迭代未收敛")

    omega = 2.0 * math.pi * n
    current = max((v_eff - ke * omega) / resistance_ohm, 0.0)
    thrust = ct * density * n**2 * diameter**4
    torque_prop = cp * density * n**3 * diameter**5 / (2.0 * math.pi * n)
    p_shaft = torque_prop * omega
    esc_eta = min(0.99, max(0.85, model.esc_eta_base - model.esc_eta_loss_coeff * (current / model.esc_rated_a) ** 2))
    p_elec = v_eff * current / esc_eta if current > 0 else 0.0
    eta_em = p_shaft / p_elec if p_elec > 0 else 0.0
    p_ideal = thrust**1.5 / math.sqrt(2.0 * density * model.disk_area_m2) if thrust > 0 else 0.0
    fm = p_ideal / p_shaft if p_shaft > 0 else 0.0
    eta_sys = fm * eta_em

    return {
        "voltage_v": voltage_bus,
        "throttle": throttle,
        "rho": density,
        "rpm": n * 60.0,
        "omega_rad_s": omega,
        "current_a": current,
        "thrust_n": thrust,
        "torque_nm": torque_prop,
        "p_shaft_w": p_shaft,
        "p_elec_w": p_elec,
        "eta_em": eta_em,
        "fm": fm,
        "eta_sys": eta_sys,
        "esc_eta": esc_eta,
        "ct": ct,
        "cp": cp,
    }


def solve_operating_point(
    model: ModelParams,
    voltage_v: float,
    throttle: float,
    rho: float | None = None,
    max_iter: int = 60,
    tol: float = 1e-10,
    pack: PackModel | None = None,
) -> dict:
    """给定开路电压与油门，解稳态工作点；pack=None 时与 v0.1 行为一致。

    返回 v0.1 字段 + （pack 非空时）pack_resistance_ohm、bus_voltage_v、
    battery_current_a、voltage_sag_v、motor_temp_c、winding_resistance_ohm、
    p_loss_w、eta_sys_ideal_bus_w（无效则省略）。
    """
    if voltage_v <= 0:
        raise ValueError("voltage_v 必须 > 0")
    if not 0.0 < throttle <= 1.0:
        raise ValueError("throttle 必须落在 (0, 1]")
    density = model.air_density() if rho is None else float(rho)
    if density <= 0:
        raise ValueError("rho 必须 > 0")

    if pack is None:
        return _solve_fixed_voltage_point(model, voltage_v, throttle, density, model.resistance_ohm, max_iter, tol)

    if pack.cells < 1:
        raise ValueError("pack.cells 必须 >= 1")
    if pack.cell_internal_resistance_ohm < 0:
        raise ValueError("cell_internal_resistance_ohm 必须 >= 0")
    if pack.motor_thermal_resistance_k_per_w < 0:
        raise ValueError("motor_thermal_resistance_k_per_w 必须 >= 0")
    if not 0.0 < pack.thermal_share_of_losses <= 1.0:
        raise ValueError("thermal_share_of_losses 必须落在 (0, 1]")

    r_pack = pack.pack_resistance_ohm
    r_winding = model.resistance_ohm
    motor_temp = model.ambient_temp_c
    bus_voltage = voltage_v
    point: dict | None = None
    for _ in range(max_iter):
        point = _solve_fixed_voltage_point(model, bus_voltage, throttle, density, r_winding, max_iter, tol)
        battery_current = point["p_elec_w"] / bus_voltage if point["p_elec_w"] > 0 else 0.0
        bus_next = max(voltage_v - battery_current * r_pack, 1e-9)
        p_loss = max(point["p_elec_w"] - point["p_shaft_w"], 0.0)
        temp_next = model.ambient_temp_c + pack.motor_thermal_resistance_k_per_w * pack.thermal_share_of_losses * p_loss
        r_next = model.resistance_ohm * (1.0 + pack.copper_temp_coeff_per_c * (temp_next - pack.winding_temp_ref_c))
        if abs(bus_next - bus_voltage) < 1e-9 and abs(temp_next - motor_temp) < 1e-6 and abs(r_next - r_winding) < 1e-12:
            bus_voltage, motor_temp, r_winding = bus_next, temp_next, r_next
            break
        bus_voltage, motor_temp, r_winding = bus_next, temp_next, r_next
    else:
        raise ValueError("电池内阻/温升联立迭代未收敛")

    point = _solve_fixed_voltage_point(model, bus_voltage, throttle, density, r_winding, max_iter, tol)
    battery_current = point["p_elec_w"] / bus_voltage if point["p_elec_w"] > 0 else 0.0
    point.update(
        {
            "open_circuit_voltage_v": voltage_v,
            "pack_resistance_ohm": r_pack,
            "bus_voltage_v": bus_voltage,
            "battery_current_a": battery_current,
            "voltage_sag_v": voltage_v - bus_voltage,
            "motor_temp_c": motor_temp,
            "winding_resistance_ohm": r_winding,
            "p_loss_w": max(point["p_elec_w"] - point["p_shaft_w"], 0.0),
        }
    )
    return point


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="静态悬停物理模型单点求解（仿真，非实测）")
    parser.add_argument("--voltage", type=float, default=22.2, help="电池开路/名义电压 V")
    parser.add_argument("--throttle", type=float, default=0.5, help="油门 0–1")
    parser.add_argument("--rho", type=float, default=None, help="空气密度（默认按模型环境温压）")
    parser.add_argument("--pack-cells", type=int, default=0, help="电池节数；>0 启用 v0.2 电池内阻+温升模型")
    parser.add_argument("--cell-resistance", type=float, default=0.008, help="单节内阻 Ω")
    parser.add_argument("--thermal-resistance", type=float, default=2.5, help="电机热阻 K/W")
    args = parser.parse_args(argv)
    pack = None
    if args.pack_cells > 0:
        pack = PackModel(
            cells=args.pack_cells,
            cell_internal_resistance_ohm=args.cell_resistance,
            motor_thermal_resistance_k_per_w=args.thermal_resistance,
        )
    try:
        result = solve_operating_point(ModelParams(), args.voltage, args.throttle, args.rho, pack=pack)
    except ValueError as exc:
        print(f"错误：{exc}")
        return 2
    print("⚠ 仿真结果：物理模型合成数据，不是实验结果")
    keys = [
        "rpm",
        "thrust_n",
        "torque_nm",
        "current_a",
        "p_shaft_w",
        "p_elec_w",
        "eta_em",
        "fm",
        "eta_sys",
    ]
    if pack is not None:
        keys.extend(["bus_voltage_v", "battery_current_a", "voltage_sag_v", "motor_temp_c", "winding_resistance_ohm"])
    for key in keys:
        print(f"{key}: {result[key]:.6g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
