# 补测闭环演练 v0.1（Loop Drill）

## 1. 目的与边界

在硬件到位前，用 SIM 数据量化"补测一批点后，效率地图到底改善多少"。**仅方法学演练**：补测点由代理模型模拟，不是实测数据，不构成实验结果，也不替代 M0.4 后的真实复测。

## 2. 流程

1. **确定性留出**：按行序每 4 点取第 4 个为留出（4/16），其余 12 点训练；
2. 训练集拟合 η 的 GP（LOOCV 选核宽），计算留出 RMSE（before）；
3. `batch_plan.build_plan` 按 D056/D057 选择 5 个补测点（σ_total 优先级）；
4. 「真实面」= 全量数据 GP，对补测点取均值 + 高斯噪声（seed 固定）模拟测量值；
5. 训练集 + 模拟测量点 → 重拟合 → 同一留出集 RMSE（after）；
6. 输出 JSON 摘要（before/after RMSE、改善百分比、核宽变化、计划点清单）与计划 CSV。

## 3. 基准结果（2026-11-23，SIM）

| 项 | 值 |
|---|---|
| 训练 / 留出 / 补测点 | 12 / 4 / 5 |
| 留出 RMSE | **0.069201 → 0.020377（改善 70.6%）** |
| GP 核宽 | 0.50 → 0.45 |
| 产物 | `data/processed/loop_drill_v0.1.json`、`data/processed/loop_drill_plan_v0.1.csv` |

**解读。** 稀疏 16 点地图上，补 5 个 D056 口径高优先级点即可把留出误差降约 7 成；这说明"补测优先级"策略在代理层面有效，也为 M0.4 后的真实复测提供预期收益参照（真实改善会小于该值，因为噪声/温漂/装夹误差未建模）。

## 4. 用法

```bat
py -3.12 code\selection\loop_drill.py --overwrite
py -3.12 code\selection\loop_drill.py --n 8 --seed 42 --noise-std 0.005 --overwrite
py -3.12 -m unittest discover -s code\selection -p "test_loop_drill.py"
```

测试 4 项：正常流程与字段、seed 决定性、非法参数、JSON/CSV 覆盖保护。

## 5. 与其它工具关系

`gp_surface`（σ 面）→ `batch_plan`（计划/排程）→ **`loop_drill`（本工具，量化收益）** → 实机 `design_matrix` + MEASURED 门禁。

## 6. 限制与后续

- "真实面"仍是 GP 代理而非物理真值；改善幅度偏乐观；
- 未模拟补测后 U(k=2) 变化（假定不变）、未含温升/换桨时间；
- v0.2 候选：用真实 MEASURED 数据替换"真实面"、按巡检悬停/巡航权重加权、与 `design_matrix` 输出直接串排程。

## 7. 变更记录

- 0.1（2026-11-23）：闭环演练工具 + 4 项测试 + SIM 基准（70.6%）。
