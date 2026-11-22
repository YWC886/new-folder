# 仿真 DoE 合同 v0.1（DoE × 仿真闭环）

日期：2026-11-22　状态：草稿（仿真侧）　依据：D043 design_matrix v0.2、D041 补测策略
边界：本合同只约束**仿真地图上的闭环实验**（SIM），不改变实机 DoE 口径；实机仍按 M0.4 启动包执行。

## 1. 目标

在现有 16 点 SIM 效率地图（`data/processed/efficiency_map_runs.csv`）上，量化以下问题的边际收益：

1. 按补测策略（σ / EI / random）各追加 5 点，对应「网格 RMSE、holdout RMSE、最优值 gap」的改善幅度；
2. 以 design_matrix v0.2 的目标推力反解（`--thrust-levels`）生成补充工况时，反解误差与不可达率；
3. 多轮（≥3）迭代后收益是否仍显著（判断补测是否值得实机执行）。

## 2. 设计

- 代理真值面：用 16 点拟合的 GP（kernel=1，σ_f²=1，σ_n²=1e-5，ℓ 由 LOOCV 选择）；
- 候选网格：电压 × 油门 13×41（与 v0.5 一致）；留出集每轮随机抽取 4 点；
- 追加点：n=5，min_distance=0.12（与 `bo_suggest.py` 默认一致），策略 none/sigma/ei/random；
- 轮数：10；随机种子固定（可复现）；噪声 σ=0.002。

## 3. 指标与判据

| 指标 | 定义 | 通过判据 |
|---|---|---|
| 网格 RMSE | 追加后 GP 在 21×21 网格上 vs 真值面 | σ 策略较 none 改善 ≥30% |
| holdout RMSE | 每轮留出点的预测误差 | σ 策略较 none 改善 ≥30% |
| 最优值 gap | 预测最优点与真值最优点的 η 差 | EI 策略 |gap| ≤ 0.002 |
| 反解误差 | `invert_throttle` 目标推力误差 | ≤0.02 N（rel ≤1%） |
| 不可达率 | 超出代理可达范围的工况占比 | 记录并注明，不得外推 |

## 4. 产出与衔接

- 复用 `code/selection/bo_suggest.py`（v0.5）与 `code/processing/design_matrix.py`（v0.2）现有接口；
- 产物：`data/processed/sim_doe_contract_v0.1.csv`（策略×轮次指标）+ 图 1 张；
- 结论写入论文 §4.3 与答辩「DoE」页；实机执行时按 M0.4 启动包替换为 MEASURED 数据。

## 5. 限制

- 代理真值面来自 16 点，本身含模型误差；本实验只回答「策略相对优劣」，不回答绝对精度；
- 不涉及多桨型、不更换桨型（v4 口径）；
- 结果标注 SIM，不得作为节能量或选型结论。
