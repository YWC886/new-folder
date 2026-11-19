"""电机双节点热网络 v0.4（SIM）：绕组节点 + 定子/机壳节点。

v0.3 用单一集总热容，无法区分"绕组先热、机壳后热"的短时行为。
本模型把电机分成两个节点：

    C_w · dT_w/dt = k_loss · P_loss − (T_w − T_s) / R_ws
    C_s · dT_s/dt = (T_w − T_s) / R_ws − (T_s − T_amb) / R_sa

绕组温度 T_w 用于铜阻温度修正（R_hot = R_20·(1+α·(T_w−20))），
每个时间步与电池压降、工作点联立求解。总热阻 R_ws + R_sa 与 v0.3 的
R_th=2.5 K/W 一致、总热容 C_w + C_s 与 v0.3 的 45 J/K 一致，
因此稳态与 v0.3 相同，仅瞬态分配不同（绕组更热、机壳滞后）。

数据边界：全部为物理模型合成数据，参数为文献量级 + 工程假设，
不是实测、不代表具体产品；只能用于软件联调与建模方法验证。
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

try:  # 支持 `py code/simulation/two_node_thermal.py` 与 `-m` 两种调用
    from . import propulsion_model as pm
    from . import transient_thermal as tt
except ImportError:  # pragma: no cover - 直接脚本调用
    import propulsion_model as pm  # type: ignore[no-redef]
    import transient_thermal as tt  # type: ignore[no-redef]

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_NOTICE = (
    "物理仿真合成数据（two_node_thermal v0.4）：仅用于流程联调/建模验证，不是实验结果"
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
    "winding_temp_c",
    "stator_temp_c",
    "winding_resistance_ohm",
    "p_loss_w",
    "heat_w",
    "data_notice",
]


@dataclass(frozen=True)
class TwoNodeParams:
    """双节点热参数（工程量级，非具体产品实测）。"""

    winding_capacitance_j_per_k: float = 15.0
    stator_capacitance_j_per_k: float = 30.0
    winding_to_stator_r_k_per_w: float = 0.7
    stator_to_ambient_r_k_per_w: float = 1.8
    ambient_temp_c: float = 24.0
    pressure_kpa: float = 96.0

    @property
    def total_capacitance_j_per_k(self) -> float:
        return self.winding_capacitance_j_per_k + self.stator_capacitance_j_per_k

    @property
    def total_resistance_k_per_w(self) -> float:
        return self.winding_to_stator_r_k_per_w + self.stator_to_ambient_r_k_per_w


def duty_profile(ramp_s: float, throttle: float, heat_s: float):
    """t -> 油门：前 ramp_s 斜坡升到 throttle，保持到 heat_s，之后为 0（冷却）。"""
    if not 0.0 < throttle <= 1.0:
        raise ValueError("throttle 必须落在 (0, 1]")
    if ramp_s < 0:
        raise ValueError("ramp_s 必须 >= 0")
    if heat_s <= 0:
        raise ValueError("heat_s 必须 > 0")

    def profile(t: float) -> float:
        if t < 0:
            raise ValueError("t 必须 >= 0")
        if t >= heat_s:
            return 0.0
        if ramp_s <= 0:
            return throttle
        return throttle * min(1.0, t / ramp_s)

    return profile


def simulate_two_node(
    model: pm.ModelParams | None = None,
    pack: pm.PackModel | None = None,
    *,
    voltage_v: float,
    throttle_fn,
    duration_s: float = 600.0,
    dt_s: float = 0.5,
    thermal: TwoNodeParams | None = None,
    density: float | None = None,
    inner_max_iter: int = 40,
    inner_tol: float = 1e-9,
) -> list[dict]:
    """双节点热瞬态仿真，返回逐时间步记录。"""
    if voltage_v <= 0:
        raise ValueError("voltage_v 必须 > 0")
    if duration_s <= 0:
        raise ValueError("duration_s 必须 > 0")
    if dt_s <= 0:
        raise ValueError("dt_s 必须 > 0")
    model = model or pm.ModelParams()
    pack = pack or tt._pack_for_voltage(voltage_v)  # noqa: SLF001 - 同包复用
    thermal = thermal or TwoNodeParams()
    if thermal.winding_capacitance_j_per_k <= 0:
        raise ValueError("winding_capacitance_j_per_k 必须 > 0")
    if thermal.stator_capacitance_j_per_k <= 0:
        raise ValueError("stator_capacitance_j_per_k 必须 > 0")
    if thermal.winding_to_stator_r_k_per_w <= 0:
        raise ValueError("winding_to_stator_r_k_per_w 必须 > 0")
    if thermal.stator_to_ambient_r_k_per_w <= 0:
        raise ValueError("stator_to_ambient_r_k_per_w 必须 > 0")
    if not 0.0 <= pack.thermal_share_of_losses <= 1.0:
        raise ValueError("thermal_share_of_losses 必须落在 [0, 1]")
    density = model.air_density() if density is None else float(density)
    if density <= 0:
        raise ValueError("density 必须 > 0")

    alpha = pack.copper_temp_coeff_per_c
    ref_temp = pack.winding_temp_ref_c
    r20 = model.resistance_ohm
    c_w = thermal.winding_capacitance_j_per_k
    c_s = thermal.stator_capacitance_j_per_k
    r_ws = thermal.winding_to_stator_r_k_per_w
    r_sa = thermal.stator_to_ambient_r_k_per_w
    k_loss = pack.thermal_share_of_losses
    t_amb = thermal.ambient_temp_c

    t_w = t_amb
    t_s = t_amb
    rows: list[dict] = []
    steps = int(round(duration_s / dt_s))
    for i in range(steps + 1):
        t = i * dt_s
        throttle = throttle_fn(t)
        winding_r = r20 * (1.0 + alpha * (t_w - ref_temp))
        if throttle <= 0.0:
            point = {
                "rpm": 0.0,
                "thrust_n": 0.0,
                "torque_nm": 0.0,
                "p_shaft_w": 0.0,
                "p_elec_w": 0.0,
                "eta_em": 0.0,
                "fm": 0.0,
                "eta_sys": 0.0,
                "bus_voltage_v": voltage_v,
                "battery_current_a": 0.0,
                "voltage_sag_v": 0.0,
            }
        else:
            point = tt._solve_with_sag(  # noqa: SLF001 - 同包复用
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
            "winding_temp_c": t_w,
            "stator_temp_c": t_s,
            "winding_resistance_ohm": winding_r,
            "p_loss_w": p_loss,
            "heat_w": heat_w,
            "data_notice": DATA_NOTICE,
        }
        rows.append(row)
        # 显式欧拉两步耦合：先算流入/流出热流，再更新两个节点
        q_ws = (t_w - t_s) / r_ws
        d_tw = (heat_w - q_ws) / c_w
        d_ts = (q_ws - (t_s - t_amb) / r_sa) / c_s
        t_w = max(t_w + dt_s * d_tw, t_amb)
        t_s = max(t_s + dt_s * d_ts, t_amb)
    return rows


def single_node_reference(
    rows: list[dict],
    *,
    model: pm.ModelParams | None = None,
    pack: pm.PackModel | None = None,
    voltage_v: float,
    throttle_fn,
    dt_s: float,
    thermal: TwoNodeParams,
    density: float | None = None,
) -> list[float]:
    """用 v0.3 单节点模型计算等效总热容/总热阻下的温度参考序列。"""
    duration_s = rows[-1]["t_s"] if rows else 0.0
    ref = tt.simulate_transient(
        model=model,
        pack=pack,
        voltage_v=voltage_v,
        throttle_fn=throttle_fn,
        duration_s=duration_s,
        dt_s=dt_s,
        thermal=tt.ThermalParams(
            thermal_capacitance_j_per_k=thermal.total_capacitance_j_per_k,
            ambient_temp_c=thermal.ambient_temp_c,
            pressure_kpa=thermal.pressure_kpa,
        ),
        density=density,
    )
    return [r["motor_temp_c"] for r in ref]


def write_csv(rows: list[dict], path: Path | str) -> Path:
    """写出双节点瞬态 CSV；存在即拒绝覆盖。"""
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


def plot_two_node(
    rows: list[dict],
    output_png: Path | str,
    *,
    single_node: list[float] | None = None,
    overwrite: bool = False,
) -> Path:
    """温度（双节点 + 可选单节点参考）/ η_sys / 油门 三面板图；SIM 红字强制标注。"""
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
    t_w = [r["winding_temp_c"] for r in rows]
    t_s = [r["stator_temp_c"] for r in rows]
    eta = [r["eta_sys"] for r in rows]
    throttle = [r["throttle"] for r in rows]

    fig, axes = plt.subplots(1, 3, figsize=(14.0, 4.4))
    ax = axes[0]
    ax.plot(t, t_w, color="tab:red", lw=1.9, label="winding node (2-node)")
    ax.plot(t, t_s, color="tab:orange", lw=1.9, label="stator node (2-node)")
    if single_node is not None and len(single_node) == len(rows):
        ax.plot(t, single_node, color="tab:gray", lw=1.2, ls="--", label="single node (v0.3)")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Two-node thermal response")
    ax.grid(True, ls=":", alpha=0.6)
    ax.legend(fontsize=8, loc="best")

    axes[1].plot(t, eta, color="tab:blue", lw=1.8)
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("System efficiency η_sys")
    axes[1].set_title("System efficiency vs time")
    axes[1].grid(True, ls=":", alpha=0.6)

    axes[2].plot(t, throttle, color="tab:green", lw=1.8)
    axes[2].set_xlabel("Time (s)")
    axes[2].set_ylabel("Throttle command")
    axes[2].set_title("Heat / cool profile")
    axes[2].set_ylim(-0.02, 1.02)
    axes[2].grid(True, ls=":", alpha=0.6)

    fig.suptitle("Two-node thermal model v0.4 (SIM)", fontsize=12)
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
    parser = argparse.ArgumentParser(description="电机双节点热网络 v0.4（SIM）")
    parser.add_argument("--voltage", type=float, default=22.2, help="电池开路电压 V（默认 22.2）")
    parser.add_argument("--throttle", type=float, default=1.0, help="目标油门 0~1（默认 1.0）")
    parser.add_argument("--ramp-s", type=float, default=5.0, help="升温斜坡时长 s（默认 5）")
    parser.add_argument("--heat-s", type=float, default=300.0, help="加热结束时刻 s（默认 300）")
    parser.add_argument("--cool-s", type=float, default=300.0, help="冷却时长 s（默认 300）")
    parser.add_argument("--dt", type=float, default=0.5, help="时间步长 s（默认 0.5）")
    parser.add_argument("--c-winding", type=float, default=15.0, help="绕组热容 J/K（默认 15）")
    parser.add_argument("--c-stator", type=float, default=30.0, help="定子/机壳热容 J/K（默认 30）")
    parser.add_argument("--r-ws", type=float, default=0.7, help="绕组→定子热阻 K/W（默认 0.7）")
    parser.add_argument("--r-sa", type=float, default=1.8, help="定子→环境热阻 K/W（默认 1.8）")
    parser.add_argument("--ambient", type=float, default=24.0, help="环境温度 °C（默认 24）")
    parser.add_argument(
        "--output", default="data/processed/two_node_thermal_v0.4.csv", help="CSV 输出路径"
    )
    parser.add_argument(
        "--figure", default="data/processed/figures/two_node_thermal_v0.4.png", help="PNG 输出路径"
    )
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有产物")
    args = parser.parse_args(argv)

    thermal = TwoNodeParams(
        winding_capacitance_j_per_k=args.c_winding,
        stator_capacitance_j_per_k=args.c_stator,
        winding_to_stator_r_k_per_w=args.r_ws,
        stator_to_ambient_r_k_per_w=args.r_sa,
        ambient_temp_c=args.ambient,
    )
    profile = duty_profile(args.ramp_s, args.throttle, args.heat_s)
    duration = args.heat_s + args.cool_s
    try:
        rows = simulate_two_node(
            voltage_v=args.voltage,
            throttle_fn=profile,
            duration_s=duration,
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
    try:
        reference = single_node_reference(
            rows,
            voltage_v=args.voltage,
            throttle_fn=profile,
            dt_s=args.dt,
            thermal=thermal,
        )
    except ValueError:
        reference = None
    plot_two_node(rows, figure, single_node=reference, overwrite=True)

    heat_rows = [r for r in rows if r["t_s"] < args.heat_s]
    cool_rows = [r for r in rows if r["t_s"] >= args.heat_s]
    peak_winding = max(r["winding_temp_c"] for r in heat_rows)
    peak_stator = max(r["stator_temp_c"] for r in heat_rows)
    last_heat = heat_rows[-1]
    last_cool = cool_rows[-1]
    peak_single = max(reference[: len(heat_rows)]) if reference else float("nan")
    print(f"步数：{len(rows)}（{duration:g} s / {args.dt:g} s）")
    print(
        f"加热段峰值：绕组 {peak_winding:.2f} °C / 定子 {peak_stator:.2f} °C"
        f"（单节点等效 {peak_single:.2f} °C 参考）"
    )
    print(
        f"加热结束（{args.heat_s:g} s）：绕组 {last_heat['winding_temp_c']:.2f} °C、"
        f"定子 {last_heat['stator_temp_c']:.2f} °C、η_sys {last_heat['eta_sys']:.4f}"
    )
    print(
        f"冷却结束（{duration:g} s）：绕组 {last_cool['winding_temp_c']:.2f} °C、"
        f"定子 {last_cool['stator_temp_c']:.2f} °C"
    )
    print(f"CSV：{output}")
    print(f"图件：{figure}")
    print("⚠ 模拟数据：不是实验结果")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
