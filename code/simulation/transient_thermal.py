"""电机一阶热瞬态模型 v0.3（SIM）。

在 v0.2 稳态热平衡基础上加入热容 C_th：
    C_th · dT/dt = k_loss · P_loss − (T − T_amb) / R_th
电池压降仍按代数关系瞬时更新；每个时间步用当前绕组温度求铜阻 R_hot，
再解固定电压工作点（v0.1 稳态求解器），因此 T 与工作点同步演化。

数据边界：全部为物理模型合成数据，参数为文献量级 + 工程假设，
不是实测、不代表具体产品；只能用于软件联调与建模方法验证。
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path

try:  # 支持 `py code/simulation/transient_thermal.py` 与 `-m` 两种调用
    from . import propulsion_model as pm
except ImportError:  # pragma: no cover - 直接脚本调用
    import propulsion_model as pm  # type: ignore[no-redef]

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_NOTICE = (
    "物理仿真合成数据（transient_thermal v0.3）：仅用于流程联调/建模验证，不是实验结果"
)

FIELDS = [
    "t_s",
    "throttle",
    "rpm",
    "thrust_n",
    "torque_nm",
    "p_shaft_w",
    "p_elec_w",
    "eta_em",
    "fm",
    "eta_sys",
    "bus_voltage_v",
    "battery_current_a",
    "voltage_sag_v",
    "motor_temp_c",
    "winding_resistance_ohm",
    "p_loss_w",
    "heat_w",
    "data_notice",
]


@dataclass(frozen=True)
class ThermalParams:
    """一阶热模型参数（工程量级，非具体产品实测）。"""

    thermal_capacitance_j_per_k: float = 45.0
    ambient_temp_c: float = 24.0
    pressure_kpa: float = 96.0


def ramp_profile(ramp_s: float, throttle: float):
    """返回 t -> 油门 的函数：前 ramp_s 秒线性斜坡，之后恒定。"""
    if not 0.0 < throttle <= 1.0:
        raise ValueError("throttle 必须落在 (0, 1]")
    if ramp_s < 0:
        raise ValueError("ramp_s 必须 >= 0")

    def profile(t: float) -> float:
        if t < 0:
            raise ValueError("t 必须 >= 0")
        if ramp_s <= 0:
            return throttle
        return throttle * min(1.0, t / ramp_s)

    return profile


def _pack_for_voltage(voltage_v: float) -> pm.PackModel:
    cells = max(1, int(round(voltage_v / pm.PackModel().cell_nominal_voltage_v)))
    return pm.PackModel(cells=cells)


def _solve_with_sag(
    model: pm.ModelParams,
    pack: pm.PackModel,
    v_oc: float,
    throttle: float,
    density: float,
    winding_r: float,
    max_iter: int,
    tol: float,
) -> dict:
    """内层迭代：给定绕组电阻，解母线电压与工作点。"""
    v_bus = v_oc
    for _ in range(max_iter):
        point = pm._solve_fixed_voltage_point(  # noqa: SLF001 - 同包内部复用
            model, v_bus, throttle, density, winding_r, 60, 1e-10
        )
        p_elec = point["p_elec_w"]
        i_batt = p_elec / v_bus if v_bus > 0 else 0.0
        v_new = v_oc - i_batt * pack.pack_resistance_ohm
        if abs(v_new - v_bus) < tol:
            return point | {
                "bus_voltage_v": v_new,
                "battery_current_a": p_elec / v_new if v_new > 0 else 0.0,
                "voltage_sag_v": v_oc - v_new,
            }
        v_bus = v_new
    raise ValueError("电池压降内层迭代未收敛")


def simulate_transient(
    model: pm.ModelParams | None = None,
    pack: pm.PackModel | None = None,
    *,
    voltage_v: float,
    throttle_fn,
    duration_s: float = 300.0,
    dt_s: float = 0.5,
    thermal: ThermalParams | None = None,
    density: float | None = None,
    inner_max_iter: int = 40,
    inner_tol: float = 1e-9,
) -> list[dict]:
    """一阶热瞬态仿真，返回逐时间步记录。"""
    if voltage_v <= 0:
        raise ValueError("voltage_v 必须 > 0")
    if duration_s <= 0:
        raise ValueError("duration_s 必须 > 0")
    if dt_s <= 0:
        raise ValueError("dt_s 必须 > 0")
    model = model or pm.ModelParams()
    pack = pack or _pack_for_voltage(voltage_v)
    thermal = thermal or ThermalParams()
    if thermal.thermal_capacitance_j_per_k <= 0:
        raise ValueError("thermal_capacitance_j_per_k 必须 > 0")
    if pack.motor_thermal_resistance_k_per_w < 0:
        raise ValueError("motor_thermal_resistance_k_per_w 必须 >= 0")
    if not 0.0 <= pack.thermal_share_of_losses <= 1.0:
        raise ValueError("thermal_share_of_losses 必须落在 [0, 1]")
    density = model.air_density() if density is None else float(density)
    if density <= 0:
        raise ValueError("density 必须 > 0")

    alpha = pack.copper_temp_coeff_per_c
    ref_temp = pack.winding_temp_ref_c
    r20 = model.resistance_ohm
    c_th = thermal.thermal_capacitance_j_per_k
    r_th = pack.motor_thermal_resistance_k_per_w
    k_loss = pack.thermal_share_of_losses
    t_amb = thermal.ambient_temp_c

    temp = t_amb
    rows: list[dict] = []
    steps = int(round(duration_s / dt_s))
    for i in range(steps + 1):
        t = i * dt_s
        throttle = throttle_fn(t)
        winding_r = r20 * (1.0 + alpha * (temp - ref_temp))
        point = _solve_with_sag(
            model, pack, voltage_v, throttle, density, winding_r, inner_max_iter, inner_tol
        )
        p_loss = max(point["p_elec_w"] - point["p_shaft_w"], 0.0)
        heat_w = k_loss * p_loss
        row = {
            "t_s": round(t, 6),
            "throttle": throttle,
            "rpm": point["rpm"],
            "thrust_n": point["thrust_n"],
            "torque_nm": point["torque_nm"],
            "p_shaft_w": point["p_shaft_w"],
            "p_elec_w": point["p_elec_w"],
            "eta_em": point["eta_em"],
            "fm": point["fm"],
            "eta_sys": point["eta_sys"],
            "bus_voltage_v": point["bus_voltage_v"],
            "battery_current_a": point["battery_current_a"],
            "voltage_sag_v": point["voltage_sag_v"],
            "motor_temp_c": temp,
            "winding_resistance_ohm": winding_r,
            "p_loss_w": p_loss,
            "heat_w": heat_w,
            "data_notice": DATA_NOTICE,
        }
        rows.append(row)
        # 显式欧拉：dT/dt = (k_loss·P_loss − (T−T_amb)/R_th) / C_th
        d_temp = (heat_w - (temp - t_amb) / r_th) / c_th if r_th > 0 else 0.0
        temp = temp + dt_s * d_temp
        if temp < t_amb:
            temp = t_amb
    return rows


def write_csv(rows: list[dict], path: Path | str) -> Path:
    """写出瞬态时间序列 CSV；存在即拒绝覆盖（与其它脚本一致）。"""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"输出已存在：{path}（需显式覆盖）")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def plot_transient(rows: list[dict], output_png: Path | str, overwrite: bool = False) -> Path:
    """T(t) 与 η_sys(t) 双面板图；SIM 红字强制标注。"""
    import sys as _sys

    _sys.path.insert(0, str(PROJECT_ROOT / "work" / "pylibs"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_png = Path(output_png)
    if output_png.exists() and not overwrite:
        raise FileExistsError(f"输出已存在：{output_png}（需 --overwrite）")
    output_png.parent.mkdir(parents=True, exist_ok=True)

    t = [r["t_s"] for r in rows]
    temp = [r["motor_temp_c"] for r in rows]
    eta = [r["eta_sys"] for r in rows]
    throttle = [r["throttle"] for r in rows]

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    axes[0].plot(t, temp, color="tab:red", lw=1.8)
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Motor temperature (°C)")
    axes[0].set_title("Motor temperature rise")
    axes[0].grid(True, ls=":", alpha=0.6)

    axes[1].plot(t, eta, color="tab:blue", lw=1.8)
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("System efficiency η_sys")
    axes[1].set_title("System efficiency vs time")
    axes[1].grid(True, ls=":", alpha=0.6)

    axes[2].plot(t, throttle, color="tab:green", lw=1.8)
    axes[2].set_xlabel("Time (s)")
    axes[2].set_ylabel("Throttle command")
    axes[2].set_title("Throttle profile")
    axes[2].set_ylim(-0.02, 1.02)
    axes[2].grid(True, ls=":", alpha=0.6)

    fig.suptitle("Transient thermal model v0.3 (SIM)", fontsize=12)
    fig.text(
        0.5,
        0.01,
        "SIMULATED DATA — NOT EXPERIMENTAL",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color="crimson",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(output_png, dpi=150)
    plt.close(fig)
    return output_png


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="电机一阶热瞬态仿真 v0.3（SIM）")
    parser.add_argument("--voltage", type=float, default=22.2, help="电池开路电压 V（默认 22.2）")
    parser.add_argument("--throttle", type=float, default=1.0, help="目标油门 0~1（默认 1.0）")
    parser.add_argument("--ramp-s", type=float, default=5.0, help="油门斜坡时长 s（默认 5）")
    parser.add_argument("--duration", type=float, default=300.0, help="仿真时长 s（默认 300）")
    parser.add_argument("--dt", type=float, default=0.5, help="时间步长 s（默认 0.5）")
    parser.add_argument("--thermal-capacitance", type=float, default=45.0, help="热容 J/K（默认 45）")
    parser.add_argument("--ambient", type=float, default=24.0, help="环境温度 °C（默认 24）")
    parser.add_argument(
        "--output",
        default="data/processed/transient_thermal_v0.3.csv",
        help="CSV 输出路径",
    )
    parser.add_argument(
        "--figure",
        default="data/processed/figures/transient_thermal_v0.3.png",
        help="PNG 输出路径",
    )
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有产物")
    args = parser.parse_args(argv)

    thermal = ThermalParams(
        thermal_capacitance_j_per_k=args.thermal_capacitance,
        ambient_temp_c=args.ambient,
    )
    profile = ramp_profile(args.ramp_s, args.throttle)
    try:
        rows = simulate_transient(
            voltage_v=args.voltage,
            throttle_fn=profile,
            duration_s=args.duration,
            dt_s=args.dt,
            thermal=thermal,
        )
    except ValueError as exc:
        print(f"错误：{exc}")
        return 2

    output = Path(args.output)
    figure = Path(args.figure)
    if (output.exists() or figure.exists()) and not args.overwrite:
        print(f"错误：产物已存在（{output} / {figure}）；如确需覆盖请加 --overwrite")
        return 2
    if output.exists():
        output.unlink()
    write_csv(rows, output)
    plot_transient(rows, figure, overwrite=True)
    last = rows[-1]
    peak = max(rows, key=lambda r: r["motor_temp_c"])
    print(f"步数：{len(rows)}（{args.duration:g} s / {args.dt:g} s）")
    print(f"末态温度：{last['motor_temp_c']:.2f} °C（峰值 {peak['motor_temp_c']:.2f} °C）")
    print(
        f"末态 η_sys：{last['eta_sys']:.4f}；母线电压 {last['bus_voltage_v']:.3f} V；"
        f"电池电流 {last['battery_current_a']:.2f} A"
    )
    print(f"CSV：{output}")
    print(f"图件：{figure}")
    print("⚠ 模拟数据：不是实验结果")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
