# 选型匹配 v0.2 —— 油门插值 + 多目标排序 + 不确定度惩罚

版本：v0.2（草稿）｜日期：2026-11-19｜负责人：D｜状态：草稿
关联：`code/selection/`、`docs/decisions.md` D024、效率地图 v0.3（U 列）

## 1. 目的与边界

在 v0.1「离散网格匹配」基础上，让"需求推力 → 候选组合"更贴近真实选型：

1. **油门插值**：离散网格只能命中 25/50/75/100% 四个油门，需求推力常落在两点之间；
   在相邻网格点之间按推力线性插值，得到"刚好满足需求"的虚拟工作点；
2. **多目标排序**：效率之外还关心电流/不确定度，提供 `eta_sys`、`current`、`balanced` 三种排序；
3. **不确定度惩罚**：过滤 U(k=2) 过大的候选，并输出保守效率 `η_sys − U`。

边界：本工具仍是**软件链路原型**，当前输入为 SIM 效率地图；SIM 命中时终端告警、图件红字，
不得写成采购/选型建议，也不得引用具体效率数值。实机地图到位后用 `--source MEASURED` 复用。

## 2. v0.2 相对 v0.1

| 能力 | v0.1 | v0.2 |
| --- | --- | --- |
| 候选来源 | 仅网格点（公差内） | 相邻油门点线性插值（精确推力）+ 网格回退 |
| 排序 | η_sys 降序 | `eta_sys` / `current` / `balanced` 归一化加权分 |
| 不确定度 | 仅输出 U 列 | `--max-u` 过滤 + `eta_sys_conservative` 保守效率列 |
| 输出字段 | 15 列 | 18 列（新增 `matched_by`、`eta_sys_conservative`、`score`） |
| 测试 | 14 项 | 20 项 |

## 3. 插值算法

按 `(combo, 电压)` 分组，组内按推力升序排列；若需求推力 `T_req` 落在相邻两点
`(T_l, η_l)`、`(T_r, η_r)` 之间（含端点）：

```text
t        = (T_req − T_l) / (T_r − T_l)
throttle = throttle_l + t·(throttle_r − throttle_l)
eta      = eta_l + t·(eta_r − eta_l)        # 其余指标同样线性插值
U        = max(U_l, U_r)                    # 保守取大
```

约束（不满足则放弃该插值点、回退网格）：

- 插值油门 ≤ `--max-throttle`；
- `U > --max-u`（若给定）；
- 两端点满足来源/电压/油门过滤。

回退网格：公差 `T_req·(1±tol)` 内取 η_sys 最高的点（v0.1 逻辑）。

> 插值是**工程近似**：真实 η(T) 在低推力段非线性明显，插值点只用于候选排序，
> v0.3 将改用物理模型/GP 代理插值。

## 4. 多目标排序

候选集内先做 min-max 归一化：

- `η_norm`：η_sys 越大越好；
- `I_norm`：电流越小越好（`1 − norm(I)`）；
- `U_norm`：U(k=2) 越小越好（`1 − norm(U)`）。

`balanced` 分数：`score = 0.6·η_norm + 0.2·I_norm + 0.2·U_norm`，按 score 降序；
`eta_sys` 按 η_sys 降序（电流小者优先）；`current` 按电流升序（η 高者优先）。
`score` 只在候选集内可比，不跨需求/跨次运行比较。

## 5. 输出字段

| 字段 | 说明 |
| --- | --- |
| `rank` | 排序序号 |
| `run_id` | 网格点原始 run_id；插值点为 `interp:<左run>~<右run>` |
| `source` | `SIM` / `MEASURED`（硬性保留） |
| `combo`、`voltage_set_v`、`throttle_set_pct` | 组合、电压、油门（插值点为小数） |
| `matched_by` | `interp` / `grid` |
| `thrust_N`、`thrust_margin_N` | 候选推力与相对需求偏差（插值点偏差≈0） |
| `eta_sys`、`eta_sys_conservative` | 系统效率均值 / 保守效率（`η_sys − U`） |
| `eta_em`、`fm`、`rpm`、`current_a` | 其他物理量 |
| `u_eta_sys_k2` | 不确定度 U(k=2)（插值取两端最大） |
| `score` | 排序分（候选集内归一化） |
| `prop_diameter_m` | 桨径 |

## 6. 演示（SIM 效率地图，2026-11-19）

命令：

```powershell
py -3.12 code\selection\match_propulsion.py --input data\processed\efficiency_map_runs.csv `
  --thrust 3.0 --tolerance 0.05 --objective balanced `
  --output data\processed\selection_v0.2_thrust3.csv --figure data\processed\figures\selection_v0.2.png --overwrite
```

结果（3 个插值候选，全部 `matched_by=interp`，推力精确 3.000 N）：

| # | 电压 / 油门 | η_sys | 保守 η | 电流 A | U(k=2) | score |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 22.2 V / 52.0% | 0.3896 | 0.3670 | 1.781 | 0.02257 | 0.807 |
| 2 | 14.8 V / 78.2% | 0.3915 | 0.3689 | 2.653 | 0.02257 | 0.700 |
| 3 | 29.6 V / 37.4% | 0.3575 | 0.3350 | 1.405 | 0.02257 | 0.300 |

解读（仅演示）：14.8 V 插值点 η 略高但电流大；22.2 V 在效率与电流间折中，balanced 排第一；
29.6 V 电流最小但效率最低。三者 U 相同（同一 U 表），故 U 项不改变相对排序。
**以上数值为 SIM，不是实验结论。**

## 7. 测试与质量门槛

`code/selection/test_selection.py` 共 20 项：原有 14 项（读入/筛选/去重/排序/Pareto/报告/图件/CLI）
+ 6 项 v0.2（插值精确推力、网格回退、插值油门超限回退、`--max-u` 过滤、`current` vs `eta_sys`、
balanced 分数与保守效率）。运行：

```powershell
py -3.12 -m unittest discover -s code\selection -p "test_*.py" -v
```

## 8. 限制与下一步（v0.3）

1. 插值为经验线性，未用物理模型；v0.3 用 `propulsion_model`/GP 代理解析插值；
2. 多目标仍是加权和，v0.3 用 pymoo 做真 Pareto（效率—电流—成本—U）；
3. 产品目录（电机/电调/桨/成本）未建立，`combo` 仍为仿真标签；
4. 未与 GP 补测点推荐联动：匹配结果 U 高的区域应反向推荐补测工况；
5. 实机地图到位后需复核插值误差是否落在 U(k=2) 内。

## 9. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 离散网格匹配、Top-N、Pareto 图、14 项测试 |
| 0.2 | 2026-11-19 | 油门插值 + 多目标排序 + U 过滤/保守效率，20 项测试；插值油门/U 越限回退网格 |
