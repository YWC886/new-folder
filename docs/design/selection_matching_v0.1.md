# 选型匹配原型 v0.1

| 项 | 内容 |
| --- | --- |
| 状态 | **草稿 v0.1**（2026-11-19），SIM 原型；实机地图到位后升 v1.0 |
| 实现 | `code/selection/match_propulsion.py`；14 项回归测试 |
| 输入 | `data/processed/efficiency_map_runs.csv`（每次运行一行，含 `source`、工况、η 与 U） |
| 输出 | `data/processed/selection_top_n.csv`（Top-N 报告）、`data/processed/figures/selection_v0.1.png`（Pareto 图） |
| 责任人 | D（原型），评审：B（物理合理性）、A（需求定义） |

> **数据诚信**：当前效率地图全部为 `SIM`（`simulate_campaign.py` 合成数据）。匹配结果只证明"需求 → 筛选 → 排序 → 报告/图件"链路可用，**不是选型结论**，不得据此采购或写入报告。

## 1. 目的

台架建成后，团队会拿到多电压 × 多油门 × 多桨的效率地图。选型匹配回答：

> 给定任务推力需求（如悬停需 5 N），在现有动力组合里选哪组电压/油门，使系统效率最高、且满足推力与不确定度要求？

v0.1 先用仿真地图把接口与图件跑通，实机数据到位后替换 `--source MEASURED` 即可复用。

## 2. 算法（v0.1，离散网格匹配）

```text
runs.csv（16+ 工况点）
   │  过滤：|T − T_req| ≤ tol·T_req；油门 ≤ max_throttle；可选电压/来源
   ▼
候选集
   │  去重：同一 (combo, 电压) 只留 η_sys 最高点
   ▼
排序：η_sys 降序 → |T − T_req| 升序
   ▼
Top-N（默认 5）+ 报告 CSV + Pareto 图（灰点/红前沿/黄需求带/彩色 Top-N）
```

- 推力需求与公差：`T_req`、`tol`（默认 10%）；
- 排序只用 η_sys 均值；`u_eta_sys_k2` 随行输出，供人工判断（v0.2 起进入排序）；
- 无候选时抛错，命令行返回 2，并提示放宽公差/补电压点/扩充地图；
- 同一 (combo, 电压) 去重：避免"同一组合换不同油门"占满 Top-N。

## 3. 输出字段（`selection_top_n.csv`）

| 字段 | 说明 |
| --- | --- |
| `rank` / `run_id` / `source` / `combo` | 排名、来源运行、仿真组合标签 |
| `voltage_set_v` / `throttle_set_pct` | 电压与油门（决策变量） |
| `thrust_N` / `thrust_margin_N` | 实际推力与相对需求的偏差（正=超出） |
| `eta_sys` / `eta_em` / `fm` | 效率三件套 |
| `rpm` / `current_a` | 转速与电流（用于电源/电调校核） |
| `u_eta_sys_k2` | η_sys 的 U(k=2)，来自流水线不确定度块（SIM 时为先验 2.26%） |
| `prop_diameter_m` | 桨径（区分不同桨） |

## 4. 图件规则

- 横轴推力、纵轴 η_sys；灰色散点为全部工况，红线为非支配前沿（推力↓ / η_sys↑）；
- 黄色竖带 = 需求推力 ±公差，虚线 = 需求值；
- Top-N 用不同颜色/形状标记，旁注 `#k`；图例含电压/油门；
- 含 `SIM` 时红字「SIMULATED DATA — NOT EXPERIMENTAL (prototype only)」；
- 默认拒绝覆盖，`--overwrite` 才覆盖。

## 5. 验收（v0.1）

| 检查 | 结果 |
| --- | --- |
| 单元测试 | 14 项通过（读入、筛选、去重排序、Pareto、报告、图件、命令行端到端、无候选退出码） |
| SIM 端到端 | 5 N ±10% 需求 → 2 个候选：14.8 V/100%（η_sys 0.4570）与 29.6 V/50%（0.4569），图件已生成 |
| 数据标注 | 终端告警 + 图件红字；报告保留 `source` 列 |

## 6. 已知限制

- 油门网格离散（25/50/75/100%），匹配只能落在网格点，无法细调到需求推力；
- `combo` 只是仿真标签，尚无真实电机/电调/桨产品参数表；
- 排序未含不确定度与推力偏差惩罚；无成本/电流/重量等多目标；
- 与 GP 代理模型、补测点推荐未联动。

## 7. v0.2 待办

1. 网格插值/模型优化：相邻油门点之间按 `propulsion_model` 求解满足推力的最小功率点；
2. 产品参数表：电机 KV/R/I0、电调额定电流、桨径/螺距/质量，形成真实候选集；
3. 风险惩罚排序：`score = η_sys − k·U(k=2)` 或约束优化（推力误差 ≤ε、电流 ≤I_max）；
4. 多目标 Pareto（效率—推力余量—电流—成本），用 pymoo 输出候选集前沿；
5. 与 GP 补测推荐联动：匹配结果中 U 大的工况 → 推荐补测。

## 8. 复现命令

```powershell
py -3.12 -m unittest discover -s code\selection -p "test_*.py" -v
py -3.12 code\selection\match_propulsion.py --input data\processed\efficiency_map_runs.csv --thrust 5 --tolerance 0.1 --output data\processed\selection_top_n.csv --figure data\processed\figures\selection_v0.1.png --overwrite
```

## 9. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 初版：离散网格匹配 + Top-N 报告 + Pareto 图；14 项测试；SIM 端到端（5 N 需求 → 2 候选） |
