# -*- coding: utf-8 -*-
"""
预研：GP 代理模型 + 学习曲线 + 效率地图不确定度（示范算例）。

目的
----
1) 用“模拟台架数据”验证数据驱动建模流程：采样 → GP 拟合 → 交叉验证 → 地图 + 不确定度 → 补测点推荐；
2) 给出“每个组合需要多少测点”的可复现依据（学习曲线），支撑规划书中“100—200 点/组合”的建议；
3) 与二次响应面（RSM）对比，展示“小样本时 GP 的优势与代价”。

注意：数据来自 efficiency_demo.py 的示范模型（非实测），正式研究须用实测数据替换。
"""

import json
import os
import sys

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, r'D:\下载\创新\work\pylibs')

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

for _f in ('Microsoft YaHei', 'SimHei', 'SimSun'):
    try:
        font_manager.findfont(_f, fallback_to_default=False)
        plt.rcParams['font.sans-serif'] = [_f]
        break
    except Exception:
        continue
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120

from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold

import efficiency_demo as ed

FIG = os.path.join(BASE, 'fig')
os.makedirs(FIG, exist_ok=True)
RNG = np.random.default_rng(20261117)

D_INCH = 18.0
KV = 400.0
V_CELL = 3.7


# ---------------------------------------------------------------------------
# 1. 模拟台架采样：工况 (V, throttle)，重复 3 次，叠加 1.2% 相对噪声
# ---------------------------------------------------------------------------
def simulate(n_points=120, reps=3, noise=0.012):
    v = RNG.uniform(3 * V_CELL, 6 * V_CELL, n_points)
    th = RNG.uniform(0.15, 1.0, n_points)
    n_max = KV * v * 0.85 / 60.0  # rev/s
    n = th * n_max
    r = ed.chain_eff(D_INCH, n, v)
    eta = r['eta_sys'] * 100.0  # %
    rows = []
    for i in range(n_points):
        for _ in range(reps):
            rows.append({
                'V_dc': v[i], 'throttle': th[i], 'rpm': n[i] * 60.0,
                'thrust_N': r['T_N'][i],
                'eta_sys_pct': eta[i] * (1.0 + RNG.normal(0.0, noise)),
            })
    return rows


def features(rows):
    x = np.array([[r['V_dc'] / 22.2, r['throttle']] for r in rows], dtype=float)
    y = np.array([r['eta_sys_pct'] for r in rows], dtype=float)
    return x, y


def fit_gp(x, y):
    kernel = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(
        nu=2.5, length_scale=[0.3, 0.3], length_scale_bounds=(1e-2, 1e2)
    ) + WhiteKernel(1e-4, (1e-8, 1.0))
    gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True,
                                  n_restarts_optimizer=1, random_state=0)
    gp.fit(x, y)
    return gp


# ---------------------------------------------------------------------------
# 2. 与二次响应面（RSM）对比
# ---------------------------------------------------------------------------
def rsm_design(x):
    x1, x2 = x[:, 0], x[:, 1]
    return np.column_stack([np.ones_like(x1), x1, x2, x1 * x1, x2 * x2, x1 * x2])


def fit_rsm(x, y):
    coef, *_ = np.linalg.lstsq(rsm_design(x), y, rcond=None)
    return lambda xx: rsm_design(xx) @ coef


# ---------------------------------------------------------------------------
# 3. 交叉验证与学习曲线
# ---------------------------------------------------------------------------
def cv_score(model_fit, x, y, n_splits=5):
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=7)
    pred = np.zeros_like(y)
    for tr, te in kf.split(x):
        pred[te] = model_fit(x[tr], y[tr])(x[te]) if model_fit is fit_rsm else model_fit(x[tr], y[tr]).predict(x[te])
    return r2_score(y, pred), float(np.sqrt(mean_squared_error(y, pred)))


def learning_curve(x, y, sizes, folds=4):
    out = []
    for m in sizes:
        scores = []
        for k in range(folds):
            idx = RNG.permutation(len(y))
            tr, te = idx[:m], idx[m:]
            if len(te) < 15:
                continue
            try:
                gp = fit_gp(x[tr], y[tr])
                scores.append(r2_score(y[te], gp.predict(x[te])))
            except Exception:
                continue
        if scores:
            out.append({'samples': int(m), 'r2_mean': float(np.mean(scores)),
                        'r2_std': float(np.std(scores))})
    return out


def main():
    rows = simulate()
    x, y = features(rows)

    # GP 交叉验证
    kf = KFold(n_splits=5, shuffle=True, random_state=7)
    pred = np.zeros_like(y)
    for tr, te in kf.split(x):
        gp = fit_gp(x[tr], y[tr])
        pred[te] = gp.predict(x[te])
    r2_gp = r2_score(y, pred)
    rmse_gp = float(np.sqrt(mean_squared_error(y, pred)))

    # RSM 交叉验证
    pred_rsm = np.zeros_like(y)
    for tr, te in kf.split(x):
        f = fit_rsm(x[tr], y[tr])
        pred_rsm[te] = f(x[te])
    r2_rsm = r2_score(y, pred_rsm)
    rmse_rsm = float(np.sqrt(mean_squared_error(y, pred_rsm)))

    # 学习曲线
    sizes = [30, 60, 120, 180, 240, 300]
    lc = learning_curve(x, y, sizes)

    # 全量 GP，用于地图与不确定度
    gp = fit_gp(x, y)

    # 效率地图网格（18 英寸桨，KV=400）
    v_grid = np.linspace(3 * V_CELL, 6 * V_CELL, 60)
    th_grid = np.linspace(0.15, 1.0, 60)
    V, TH = np.meshgrid(v_grid, th_grid)
    xx = np.column_stack([(V.ravel() / 22.2), TH.ravel()])
    mean, std = gp.predict(xx, return_std=True)
    mean = mean.reshape(V.shape)
    std = std.reshape(V.shape)
    half95 = 1.96 * std

    # 不确定度最大的候选点（补测建议）
    cand_v = np.linspace(3 * V_CELL, 6 * V_CELL, 24)
    cand_th = np.linspace(0.15, 1.0, 24)
    CV_, CTH_ = np.meshgrid(cand_v, cand_th)
    cxx = np.column_stack([CV_.ravel() / 22.2, CTH_.ravel()])
    _, cstd = gp.predict(cxx, return_std=True)
    order = np.argsort(cstd)[::-1]
    suggest = []
    for idx in order:
        vv, tt = CV_.ravel()[idx], CTH_.ravel()[idx]
        # 简单去重：与已有点距离足够远才推荐
        dist = np.min(np.sqrt(((np.array([vv / 22.2, tt]) - x) ** 2).sum(axis=1)))
        if dist < 0.08:
            continue
        suggest.append({'V_dc': round(float(vv), 2), 'throttle': round(float(tt), 3),
                        'std_pct': round(float(cstd[idx]), 3)})
        if len(suggest) >= 5:
            break

    # 图 4：GP 效率地图 + 不确定度
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.3))
    ax = axes[0]
    im = ax.pcolormesh(V, TH * 100, mean, shading='auto', cmap='viridis')
    cs = ax.contour(V, TH * 100, mean, levels=[40, 45, 50, 55, 60], colors='w', linewidths=0.8)
    ax.clabel(cs, fmt='%.0f%%', fontsize=7, colors='w')
    ax.set_xlabel('母线电压 (V)')
    ax.set_ylabel('油门 (%)')
    ax.set_title('GP 预测的系统效率地图（18 英寸桨，KV=400）')
    fig.colorbar(im, ax=ax, label='系统效率 (%)')

    ax = axes[1]
    im2 = ax.pcolormesh(V, TH * 100, half95, shading='auto', cmap='magma_r')
    ax.scatter([r['V_dc'] for r in rows[::3]], [r['throttle'] * 100 for r in rows[::3]],
               s=6, c='cyan', alpha=0.6, label='训练点（每 3 个重复取 1）')
    ax.set_xlabel('母线电压 (V)')
    ax.set_ylabel('油门 (%)')
    ax.set_title('95% 置信区间半宽（补测优先区：亮色）')
    fig.colorbar(im2, ax=ax, label='半宽 (%)')
    ax.legend(loc='lower left', fontsize=7)
    fig.tight_layout()
    fig4 = os.path.join(FIG, 'fig4_gp_map_uncertainty.png')
    fig.savefig(fig4)
    plt.close(fig)

    # 图 5：学习曲线（GP vs RSM）
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    if lc:
        ax.errorbar([d['samples'] for d in lc], [d['r2_mean'] for d in lc],
                    yerr=[d['r2_std'] for d in lc], marker='o', capsize=3, label='GP（Matérn 5/2）')
    ax.axhline(r2_rsm, ls='--', color='tab:orange', label=f'二次响应面（全量，R²={r2_rsm:.3f}）')
    ax.set_xlabel('训练样本数（含重复）')
    ax.set_ylabel('交叉验证 R²')
    ax.set_title('效率模型学习曲线：小样本下的精度')
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig5 = os.path.join(FIG, 'fig5_learning_curve.png')
    fig.savefig(fig5)
    plt.close(fig)

    # 保存指标
    metrics = {
        'setting': {'d_inch': D_INCH, 'kv': KV, 'n_points': len(rows) // 3,
                    'reps': 3, 'noise_rel': 0.012},
        'gp_cv': {'r2': round(float(r2_gp), 4), 'rmse_pct': round(rmse_gp, 3)},
        'rsm_cv': {'r2': round(float(r2_rsm), 4), 'rmse_pct': round(rmse_rsm, 3)},
        'learning_curve': lc,
        'map_range_pct': {'min': round(float(np.nanmin(mean)), 2),
                          'max': round(float(np.nanmax(mean)), 2)},
        'suggest_next_points': suggest,
        'figs': [os.path.basename(fig4), os.path.basename(fig5)],
    }
    with open(os.path.join(BASE, 'gp_metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print('=== GP 预研结果 ===')
    print(f'样本：{len(rows)//3} 个工况 × 3 重复 = {len(rows)} 条')
    print(f'GP 5 折交叉验证：R² = {r2_gp:.4f}，RMSE = {rmse_gp:.3f} %')
    print(f'RSM 5 折交叉验证：R² = {r2_rsm:.4f}，RMSE = {rmse_rsm:.3f} %')
    print('学习曲线：')
    for d in lc:
        print(f"  {d['samples']:>3} 样本  R²={d['r2_mean']:.4f} ± {d['r2_std']:.4f}")
    print('95%% CI 半宽范围：%.2f%%—%.2f%%' % (float(np.nanmin(half95)), float(np.nanmax(half95))))
    print('建议补测点（按不确定度从大到小）：')
    for s in suggest:
        print(f"  V={s['V_dc']:.1f} V, throttle={s['throttle']:.0%}, std={s['std_pct']:.2f}%")
    print('图件：', fig4, fig5)
    print('指标：', os.path.join(BASE, 'gp_metrics.json'))


if __name__ == '__main__':
    main()
