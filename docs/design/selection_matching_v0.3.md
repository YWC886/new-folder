# 选型匹配原型 v0.3：GP 连续匹配（`code/selection/gp_match.py`）

> 状态：**v0.3 草稿（SIM 原型）**，2026-11-19。
> 输入仍为 16 工况 SIM 效率地图；所有结论只用于验证软件链路，**不是选型结论**。

## 1. 目的与边界

v0.2 用「相邻油门点线性插值」在离散工况间命中需求推力，但：

- 插值只沿单条电压曲线，无法利用相邻工况的平滑性；
- 无法给出预测标准差，保守效率只能粗暴减 U(k=2)；
- 需求推力超出网格点范围（尤其低推力区）时只能回退网格点。

v0.3 把 GP 平滑代理（`code/processing/gp_surface.py`，D026）引入匹配流程：对推力与效率分别拟合高斯过程，

- 在每条电压曲线上**连续扫描**油门，反解满足需求推力的工作点；
- 给出 η_sys 的预测标准差 σ_gp，与不确定度合成后得到保守效率：

  `η_conservative = η_pred − sqrt((2·σ_gp)² + u_local²)`

  其中 `u_local` 取该电压下最近两个网格点 U(k=2) 的最大值（保守）。
- 保留 v0.2 的多目标排序（`eta_sys` / `current` / `balanced`）与 U 过滤。

**边界**：GP 是数据平滑，不是物理模型；外推区（尤其油门 > 已测范围、推力 < 最小值）不可信，不得用于选型或安全结论。

## 2. 方法

1. 读 runs CSV（字段同 `match_propulsion.INPUT_FIELDS`，13 列）；
2. 按来源/电压/油门上限过滤后，拟合两个 GP：
   - 推力模型：`thrust_N_mean ~ (V/30, throttle/100)`；
   - 效率模型：`η_sys_mean ~ (V/30, throttle/100)`；
   - 核宽由 `gp_surface.choose_length_scale` 以 LOOCV RMSE 选择；附加通道（η_em、FM、rpm、current）用效率模型的核宽分别拟合；
3. 每条电压曲线：在 `[0, max_throttle_pct]` 上以 101 点扫描 GP 推力，取最接近需求推力的油门，并在相邻扫描点间线性细化；
4. 预测该点 η_sys、σ_gp 与附加通道；计算保守效率；
5. 过滤：|推力 − 需求| ≤ 需求×公差、`u_local ≤ max_u`（可选）；
6. 复用 `match_propulsion._score_candidates` 按目标排序（min-max 归一化），输出 Top-N。

### 为什么不是"全局寻优"

需求推力对应的是一个**等推力线**；GP 在 (V, throttle) 平面上连续，理论上可解一条曲线上的任意点。当前实现按电压分别扫描，等价于"固定电池包选型下的油门寻优"，与真实选型流程（先定电压/电池节数，再定油门）一致，也避免跨电压插值带来的伪工作点。

## 3. 接口

```python
fit_models(runs, *, length_scales=gp.LENGTH_SCALES) -> dict
match_gp(runs, *, thrust_required_n, thrust_tolerance=0.1, max_throttle_pct=100.0,
         voltages=None, top_n=5, source="ANY", objective="eta_sys",
         max_u_k2=None, grid_points=101) -> list[dict]
write_report(results, path) -> Path
plot_gp_selection(runs, results, output_png, *, thrust_required_n,
                  thrust_tolerance=0.1, max_throttle_pct=100.0,
                  title=..., overwrite=False) -> Path
```

输出 20 列：`rank, run_id, source, combo, voltage_set_v, throttle_set_pct, matched_by, thrust_N, thrust_margin_N, eta_sys, gp_std_eta, eta_sys_conservative, u_eta_sys_k2, eta_em, fm, rpm, current_a, score, prop_diameter_m, data_note`。`matched_by="gp"`，`run_id="gp:<combo>@<V>V"`。

CLI：

```powershell
py -3.12 code\selection\gp_match.py `
  --input data\processed\efficiency_map_runs.csv `
  --thrust 5 --tolerance 0.1 --objective eta_sys `
  --output data\processed\selection_v0.3_gp.csv `
  --figure data\processed\figures\selection_v0.3.png `
  --overwrite
```

参数：`--voltages`、`--source`、`--top`、`--objective`、`--max-u`、`--grid-points`（默认 101）、`--max-throttle`；默认拒绝覆盖，错误 exit 2。

## 4. SIM 演示（5 N ±10%，目标 `eta_sys`）

16 工况 SIM 地图（`data/processed/efficiency_map_runs.csv`）：

| # | 电压 / 油门 | 推力 (N) | η_sys ± σ_gp | 保守 η | 电流 (A) | score |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 22.2 V / 68.22% | 4.999 | 0.4641 ± 0.0046 | 0.4397 | 3.20 | 0.828 |
| 2 | 29.6 V / 51.09% | 4.998 | 0.4625 ± 0.0031 | 0.4391 | 2.41 | 0.768 |
| 3 | 14.8 V / 100%（油门上限边界） | 4.788 | 0.4570 | 0.4337 | 4.60 | 0.100 |

解读（仅流程演示）：

- 同推力下 22.2 V / 29.6 V 的 η 接近，29.6 V 电流更小、σ 更小（曲线更密）；
- 14.8 V 在 100% 油门仍差 0.212 N，属于**边界候选**，实际选型应直接排除或补充更高油门工况；
- 保守效率普遍比点估计低约 2–3 个百分点（σ_gp 与 U 合成），提示"别只看均值"。

产物：`data/processed/selection_v0.3_gp.csv`、`data/processed/figures/selection_v0.3.png`（灰点观测 + 红 Pareto + 各电压 GP 曲线 + 需求黄带 + SIM 红字）。

## 5. 测试

`code/selection/test_gp_match.py` 共 **14 项**（toy 2 电压 × 4 油门，`thrust = 0.2·V·t/100` 可解析）：

- 拟合：GP 返回、LOOCV 指标、最少点数、`_local_u` 保守取值；
- 匹配：精确命中（3 N → 20 V/≈74.84%）、电压过滤（10 V 无候选）、来源过滤、`--max-u` 过滤、无候选报错、非法参数、η 排序、balanced 分数；
- 输出：CSV 字段与 data_note、PNG 与覆盖保护、CLI 端到端（成功 0 / 已存在 2 / 无候选 2）。

全套选型测试 20（v0.1/v0.2）+ 14（v0.3）= **34 项**。

## 6. 已知限制 / v0.4 待办

1. **σ_gp 不是 U(k=2)**：σ_gp 是数据平滑的预测标准差，U 是测量不确定度；当前合成公式为工程近似（`2σ_gp` 与 `u_local` 平方和），须在实机数据上复核；
2. 外推区不可信：GP 曲线在油门接近 0 与 > 已测范围时是外推，图件中已用虚线表示，但仍需在报告中显式提示；
3. 油门边界候选（如 14.8 V/100%）标记为 `边界候选`，排序时应降权或排除（v0.4）；
4. 未建产品参数表（KV、R、I0、ESC 额定、桨径/螺距、成本），多目标仍只有 η/电流/U；
5. 真多目标 Pareto（效率—电流—成本—U）与 GP 补测点推荐闭环（用 σ 选下一个测量点）未做；
6. 实机数据到位后，同一命令加 `--source MEASURED` 重跑，并复核插值/外推误差。

## 7. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | v0.3 初稿：GP 连续匹配（thrust/eta 双 GP + 油门扫描 + σ 合成保守效率 + 复用多目标排序），14 项测试，SIM 演示 5 N ±10% → 3 候选 |
