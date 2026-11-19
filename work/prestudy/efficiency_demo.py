# -*- coding: utf-8 -*-
"""
预研演示：多旋翼动力系统效率链、效率地图与匹配优化的可复现示例。

说明
----
1) 本项目最终要用实测数据替换这里的模型参数；本脚本只用于
   - 验证分析方法与代码流程（效率链合成、效率地图、Pareto 匹配寻优）；
   - 生成“预研报告”中的示意图；
2) 采用的模型：
   螺旋桨（静态相似性）：T = Ct·ρ·n²·D⁴，Q = Cq·ρ·n²·D⁵，P_shaft = 2πnQ
   螺旋桨悬停效率（figure of merit）：FM = T^1.5 / (sqrt(2ρA)·P_shaft)
   电机损耗：铜损 P_cu = k_cu·Q²，铁损 P_fe = k_fe·n^1.5，风阻/机械 P_fw = k_fw·n³
   电调效率：η_esc = 0.985 − 0.02·(I/I_ref)²
   系统效率：η_sys = η_esc · η_motor · FM = T^1.5 / (sqrt(2ρA)·P_elec)
3) 脚本只依赖 numpy / pandas / matplotlib / pymoo；pymoo 不可用时自动退回网格枚举。
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, r'D:\下载\创新\work\pylibs')

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 中文字体
for _f in ('Microsoft YaHei', 'SimHei', 'SimSun'):
    try:
        font_manager.findfont(_f, fallback_to_default=False)
        plt.rcParams['font.sans-serif'] = [_f]
        break
    except Exception:
        continue
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120

OUT = r'D:\下载\创新\work\prestudy'
FIG = os.path.join(OUT, 'fig')
os.makedirs(FIG, exist_ok=True)

RHO = 1.225  # kg/m^3，标准海平面

# ---------------------------------------------------------------------------
# 模型参数（示范值；实测后需重新辨识）
# ---------------------------------------------------------------------------
CT = 0.105          # 推力系数（静态，示范值）
CP = 0.042          # 功率系数（静态，示范值）
CQ = CP / (2 * np.pi)

K_CU = 20.0         # 铜损系数 W/(N·m)²
K_FE = 0.020        # 铁损系数 W/(rev/s)^1.5
K_FW = 1.5e-5       # 风阻/机械损耗系数 W/(rev/s)³
ESC_ETA0 = 0.985    # 电调基础效率
ESC_LOSS = 0.02     # 电调损耗系数
I_REF = 40.0        # 电调参考电流 A


def prop_thrust(d_inch, n):
    """推力 N；d_inch 桨径（英寸），n 转速（rev/s）。"""
    d = np.asarray(d_inch, dtype=float) * 0.0254
    n = np.asarray(n, dtype=float)
    return CT * RHO * n ** 2 * d ** 4


def prop_torque(d_inch, n):
    d = np.asarray(d_inch, dtype=float) * 0.0254
    n = np.asarray(n, dtype=float)
    return CQ * RHO * n ** 2 * d ** 5


def prop_fm(d_inch, n):
    """螺旋桨悬停效率（figure of merit，静态）。"""
    d = np.asarray(d_inch, dtype=float) * 0.0254
    area = np.pi * (d / 2.0) ** 2
    t = prop_thrust(d_inch, n)
    p = 2 * np.pi * np.asarray(n, dtype=float) * prop_torque(d_inch, n)
    return np.where((t > 0) & (p > 0), t ** 1.5 / (np.sqrt(2 * RHO * area) * p), np.nan)


def motor_efficiency(n, q):
    """电机效率（含损耗模型）。"""
    p_shaft = 2 * np.pi * np.asarray(n, dtype=float) * np.asarray(q, dtype=float)
    p_cu = K_CU * np.asarray(q, dtype=float) ** 2
    p_fe = K_FE * np.asarray(n, dtype=float) ** 1.5
    p_fw = K_FW * np.asarray(n, dtype=float) ** 3
    return np.where(p_shaft > 0, p_shaft / (p_shaft + p_cu + p_fe + p_fw), np.nan)


def esc_efficiency(i):
    return ESC_ETA0 - ESC_LOSS * (np.asarray(i, dtype=float) / I_REF) ** 2


def chain_eff(d_inch, n, v_bus):
    """给定桨径、转速、母线电压，返回电调/电机/螺旋桨/系统效率与推力等。"""
    d_inch = np.asarray(d_inch, dtype=float)
    n = np.asarray(n, dtype=float)
    v_bus = np.asarray(v_bus, dtype=float)
    t = prop_thrust(d_inch, n)
    q = prop_torque(d_inch, n)
    p_shaft = 2 * np.pi * n * q
    fm = prop_fm(d_inch, n)
    eta_m = motor_efficiency(n, q)
    # 电调效率与电流互相耦合，迭代两次即可
    eta_esc = np.full_like(p_shaft, ESC_ETA0, dtype=float)
    for _ in range(3):
        p_in = p_shaft / (eta_m * eta_esc)
        current = p_in / np.maximum(v_bus, 1.0)
        eta_esc = esc_efficiency(current)
    eta_sys = eta_esc * eta_m * fm
    return {
        'T_N': t, 'Q_Nm': q, 'P_shaft_W': p_shaft, 'I_A': current,
        'eta_esc': eta_esc, 'eta_motor': eta_m, 'FM': fm, 'eta_sys': eta_sys,
    }


# ---------------------------------------------------------------------------
# 图 1：固定动力组合下效率随转速变化
# ---------------------------------------------------------------------------
def fig_efficiency_curve(d_inch=18.0, v_bus=22.2):
    n = np.linspace(20, 130, 400)  # rev/s
    r = chain_eff(d_inch, n, v_bus)
    fig, ax1 = plt.subplots(figsize=(7.2, 4.2))
    ax1.plot(n * 60, r['eta_esc'] * 100, label='电调效率', lw=1.6)
    ax1.plot(n * 60, r['eta_motor'] * 100, label='电机效率', lw=1.6)
    ax1.plot(n * 60, r['FM'] * 100, label='螺旋桨悬停效率 FM', lw=1.6)
    ax1.plot(n * 60, r['eta_sys'] * 100, label='系统效率', lw=2.4, color='k')
    ax1.set_xlabel('转速 (rpm)')
    ax1.set_ylabel('效率 (%)')
    ax1.set_title(f'效率链随转速变化（{d_inch:.0f} 英寸桨，{v_bus:.1f} V 母线）')
    ax1.grid(alpha=0.3)
    ax1.legend(loc='lower right', fontsize=8)
    ax1.set_ylim(0, 100)
    ax2 = ax1.twinx()
    ax2.plot(n * 60, r['T_N'], '--', color='tab:orange', lw=1.2, label='推力 (N)')
    ax2.set_ylabel('推力 (N)')
    ax2.legend(loc='upper left', fontsize=8)
    fig.tight_layout()
    path = os.path.join(FIG, 'fig1_efficiency_chain.png')
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 图 2：效率地图（油门 × 母线电压）
# ---------------------------------------------------------------------------
def fig_efficiency_map(d_inch=18.0, kv=400.0):
    voltages = np.linspace(11.1, 25.2, 45)        # 3S ~ 6S
    throttle = np.linspace(0.05, 1.0, 45)
    V, TH = np.meshgrid(voltages, throttle)
    n_max = kv * V * 0.85 / 60.0                  # rev/s，带载后最高转速
    n = TH * n_max
    r = chain_eff(d_inch, n, V)
    eta = r['eta_sys'] * 100
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    vmax = float(np.nanpercentile(eta, 99))
    im = ax.pcolormesh(V, TH * 100, eta, shading='auto', cmap='viridis',
                       vmin=0, vmax=max(vmax, 1.0))
    cs = ax.contour(V, TH * 100, eta, levels=[40, 45, 50, 55, 60], colors='w', linewidths=0.8)
    ax.clabel(cs, fmt='%.0f%%', fontsize=7, colors='w')
    ax.set_xlabel('母线电压 (V)')
    ax.set_ylabel('油门 (%)')
    ax.set_title(f'系统效率地图示例（{d_inch:.0f} 英寸桨，KV={kv:.0f}）')
    fig.colorbar(im, ax=ax, label='系统效率 (%)')
    fig.tight_layout()
    path = os.path.join(FIG, 'fig2_efficiency_map.png')
    fig.savefig(path)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 图 3：匹配优化（效率 vs 桨径的 Pareto 前沿）
# ---------------------------------------------------------------------------
def hover_rpm(d_inch, t_req):
    d = np.asarray(d_inch, dtype=float) * 0.0254
    return np.sqrt(np.asarray(t_req, dtype=float) / (CT * RHO * d ** 4))


def evaluate_combo(d_inch, kv, cells):
    """单轴悬停所需推力下的效率评价。cells：电池串数。"""
    v_bus = cells * 3.7
    n_req = hover_rpm(d_inch, T_REQ)
    n_cap = kv * v_bus * 0.85 / 60.0
    feasible = n_req <= n_cap * 1.02
    r = chain_eff(d_inch, n_req, v_bus)
    ok = feasible & (r['I_A'] <= 60.0) & np.isfinite(r['eta_sys'])
    return np.where(ok, r['eta_sys'], np.nan)


T_REQ = 4.0  # 单轴悬停推力需求 N（约 2 kg 四旋翼的 1/4 重量）

def fig_pareto():
    ds = np.round(np.arange(12, 24.5, 0.5), 1)
    kvs = np.arange(300, 1001, 20.0)
    cells_list = [3, 4, 5, 6]
    rows = []
    for d in ds:
        for kv in kvs:
            for c in cells_list:
                eta = float(evaluate_combo(d, kv, c))
                if np.isfinite(eta):
                    rows.append((d, kv, c, eta))
    df = pd.DataFrame(rows, columns=['D_inch', 'KV', 'cells', 'eta_sys'])
    # 每个 (D,KV) 取最优电池串数
    df = df.sort_values('eta_sys', ascending=False).drop_duplicates(['D_inch', 'KV'])
    df['eta_sys'] = df['eta_sys'] * 100
    # 手工 Pareto：目标 max eta_sys、min D
    pts = df[['D_inch', 'eta_sys']].values
    order = np.argsort(pts[:, 0])
    pareto_idx = []
    best = -np.inf
    for i in order:
        if pts[i, 1] > best:
            pareto_idx.append(i)
            best = pts[i, 1]
    pareto = df.iloc[pareto_idx].sort_values('D_inch')
    df.to_csv(os.path.join(OUT, 'matching_grid.csv'), index=False, encoding='utf-8-sig')
    pareto.to_csv(os.path.join(OUT, 'pareto.csv'), index=False, encoding='utf-8-sig')

    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    ax.scatter(df['D_inch'], df['eta_sys'], s=8, alpha=0.35, label='可行匹配方案')
    ax.plot(pareto['D_inch'], pareto['eta_sys'], 'o-', color='crimson', lw=2,
            ms=5, label='Pareto 前沿（效率优先）')
    for k, (_, row) in enumerate(pareto.iterrows()):
        if k % 2 and k != len(pareto) - 1:
            continue
        ax.annotate(f"KV {row.KV:.0f}/{int(row.cells)}S", (row.D_inch, row.eta_sys),
                    textcoords='offset points', xytext=(0, 8), fontsize=6,
                    ha='center', rotation=30)
    ax.set_xlabel('螺旋桨直径 (英寸)')
    ax.set_ylabel('悬停系统效率 (%)')
    ax.set_title(f'匹配优化的效率-桨径 Pareto 前沿（单轴悬停推力 {T_REQ:.0f} N，示范模型）')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(FIG, 'fig3_pareto.png')
    fig.savefig(path)
    plt.close(fig)
    return path, pareto


# ---------------------------------------------------------------------------
# pymoo 验证（可选）：连续变量 NSGA-II
# ---------------------------------------------------------------------------
def nsga2_demo():
    try:
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.core.problem import Problem
        from pymoo.optimize import minimize
    except Exception as exc:  # pragma: no cover
        return None, f'pymoo 不可用：{exc}'

    class MatchProblem(Problem):
        def __init__(self):
            super().__init__(n_var=3, n_obj=2, n_ieq_constr=2,
                             xl=np.array([12.0, 300.0, 3.0]),
                             xu=np.array([24.0, 1000.0, 6.0]))

        def _evaluate(self, x, out, *args, **kwargs):
            d, kv, cells = x[:, 0], x[:, 1], x[:, 2]
            v_bus = cells * 3.7
            n_req = hover_rpm(d, T_REQ)
            n_cap = kv * v_bus * 0.85 / 60.0
            r = chain_eff(d, n_req, v_bus)
            eta = np.where(np.isfinite(r['eta_sys']), r['eta_sys'], 0.0)
            # 目标：最大化效率、最小化桨径
            out['F'] = np.column_stack([-eta, d])
            # 约束：所需转速不超过可用转速，电流不超过 60 A
            out['G'] = np.column_stack([n_req - n_cap, r['I_A'] - 60.0])

    res = minimize(MatchProblem(), NSGA2(pop_size=80), ('n_gen', 120), seed=1, verbose=False)
    if res.F is None:
        return None, 'NSGA-II 未得到可行解'
    df = pd.DataFrame({'D_inch': res.X[:, 0], 'KV': res.X[:, 1], 'cells': res.X[:, 2],
                       'eta_sys': -res.F[:, 0] * 100})
    df = df.sort_values('D_inch')
    df.to_csv(os.path.join(OUT, 'nsga2_pareto.csv'), index=False, encoding='utf-8-sig')
    return df, 'ok'


def main():
    results = {}
    results['fig1'] = fig_efficiency_curve()
    results['fig2'] = fig_efficiency_map()
    results['fig3'], pareto = fig_pareto()
    nsga_df, msg = nsga2_demo()
    results['nsga2'] = msg

    # 文字摘要
    print('== 预研示例结果 ==')
    print('fig1:', results['fig1'])
    print('fig2:', results['fig2'])
    print('fig3:', results['fig3'])
    print('Pareto 方案数:', len(pareto))
    print(pareto.head(10).to_string(index=False))
    print('NSGA-II:', msg)
    if nsga_df is not None:
        print('NSGA-II Pareto 方案数:', len(nsga_df))
        print(nsga_df.head(8).to_string(index=False))


if __name__ == '__main__':
    main()
