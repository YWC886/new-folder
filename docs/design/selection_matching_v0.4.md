# 选型匹配 v0.4 · GP 多目标 Pareto + 补测点推荐

日期：2026-11-19 · 状态：草稿（SIM 原型） · 负责人：D

## 1. 目的与边界

在 v0.3（GP 连续匹配）基础上补齐两件事：

1. **真多目标 Pareto**：不再只用一个加权分，而是同时看「效率 η_sys」「电池电流 I」「稳健性（保守效率 η−sqrt((2σ_gp)²+u²))」三个目标，输出非支配前沿与 knee 点；
2. **GP 补测点推荐闭环**：用 GP 预测标准差 σ 找信息量最大的未测工况，指导下一轮台架补测（当前为 SIM 规划演示）。

**不做成本项**：目前没有真实产品价格表，无法把「成本」作为可解释目标；伪造价格会污染选型结论。成本项推迟到建立产品参数表之后（v0.5）。

边界：输入仍为 SIM 效率地图（`efficiency_map_runs.csv`，16 工况）；输出仅为软件链路与原型的可复核产物，不是选型结论、不是实验结果。

## 2. v0.4 增量

| 能力 | 说明 |
| --- | --- |
| 候选网格 | 13 电压 × 41 油门（可调），GP 推力按公差过滤 |
| 多目标支配 | η 越大越好、电流越小越好、保守 η 越大越好 |
| Pareto 前沿 | O(n²) 非支配筛选；按保守 η 降序编号 |
| Knee 点 | 归一化后距理想点 (η_max, I_min, cons_max) 最近的前沿点 |
| 补测推荐 | 贪心：σ_gp 最大 + 与已测/已选点归一化距离 ≥ `--min-distance` |
| 边界修正 | 推荐油门限定在**已测油门区间**内（不做 0% 外推） |
| 图件 | 双面板 Pareto（η–I；η–σ_gp）+ 推荐点 V–油门散点 |

## 3. 算法

### 3.1 候选评估

```text
候选 = {(V_i, t_j) | i=1..13, j=1..41}
(V, t) → GP_thrust(V, t) → 若 |T−T_req| ≤ tol·T_req 则保留
       → GP_eta(V, t) = (η, σ_gp)
       → 电流 = GP_current(V, t)
       → 保守效率 = η − sqrt((2σ_gp)² + u_local²)
```

`u_local(V,t)`：同电压下与 (V,t) 最接近的两个已测点的 U(k=2) 最大值（保守取大）。

### 3.2 支配与前沿

对 a、b 两个候选：a 支配 b ⇔ a 的 η 更大、电流更小、保守 η 更大，且至少一项严格更优。

```python
def dominates(a, b):
    ge = (a.eta_sys >= b.eta_sys and a.current_a <= b.current_a
          and a.eta_sys_conservative >= b.eta_sys_conservative)
    gt = (a.eta_sys > b.eta_sys or a.current_a < b.current_a
          or a.eta_sys_conservative > b.eta_sys_conservative)
    return ge and gt
```

knee 点：对前沿三项目标做 min-max 归一化（电流取反），选距理想点 (1,0,1) 最近者。

### 3.3 补测推荐（贪心）

```text
已选 = ∅；已测 = 全部观测工况
repeat:
  候选 = 网格点（V 13 × t 41，t ∈ [已测最小油门, 已测最大油门]）
  过滤：与 已测∪已选 的归一化距离 < min_distance 的候选
  选 σ_gp 最大者加入已选
until len(已选) == n
```

归一化距离：`sqrt(((V−V')/30)² + ((t−t')/100)²)`；阈值默认 `min_distance=0.12`。

## 4. 接口

```python
# code/selection/multiobjective.py
candidate_grid(runs, *, voltage_points=13, throttle_points=41,
               min_throttle_pct=0, max_throttle_pct=100)
evaluate_candidates(models, runs, *, thrust_required_n, thrust_tolerance=0.1,
                    voltage_points, throttle_points, max_throttle_pct)
dominates(a: dict, b: dict) -> bool
pareto_front(candidates: list[dict]) -> list[dict]
mark_knee(front: list[dict]) -> dict | None
run_pareto(runs, *, thrust_required_n, thrust_tolerance=0.1, max_throttle_pct=100.0,
           voltage_points=13, throttle_points=41) -> dict  # front/candidates/knee/n_*
suggest_measurements(runs, *, n=5, min_distance=0.12, voltage_points=13,
                     throttle_points=41, max_throttle_pct=None) -> list[dict]
plot_pareto(candidates, front, output_png, *, thrust_required_n, thrust_tolerance=0.1, overwrite=False)
plot_suggestions(runs, suggestions, output_png, overwrite=False)
```

CLI：

```powershell
# Pareto
py -3.12 code\selection\multiobjective.py `
  --input data\processed\efficiency_map_runs.csv `
  --thrust 5 --tolerance 0.1 `
  --output data\processed\selection_v0.4_pareto.csv `
  --figure data\processed\figures\selection_v0.4.png --overwrite

# 补测推荐
py -3.12 code\selection\multiobjective.py `
  --input data\processed\efficiency_map_runs.csv `
  --suggest --n 5 --min-distance 0.12 `
  --output data\processed\gp_suggestions_v0.4.csv `
  --figure data\processed\figures\gp_suggestions_v0.4.png --overwrite
```

## 5. SIM 演示结果（16 工况地图，不是实验结论）

需求推力 5 N ±10%：

- 可行候选 **28** 个，Pareto 前沿 **5** 个；
- knee：**29.60 V / 52.5%**，η 0.4694（保守 0.4458）、电流 2.57 A、σ_gp 0.0034；
- 前沿覆盖 22.2 V/75–100%（高 η、中电流）→ 29.6 V/50–75%（低电流、η 略低）的权衡带。

补测推荐 5 点：26.52 V/34.4%（σ 0.0104）、26.52 V/90.6%、18.81 V/34.4%（σ 0.0088）、18.81 V/90.6%、26.52 V/62.5%（σ 0.0083）——均落在已测电压/油门区间内，间距满足 ≥0.12。

产物：

| 文件 | 说明 |
| --- | --- |
| `data/processed/selection_v0.4_pareto.csv` | 5 行 × 12 列 Pareto 前沿 |
| `data/processed/figures/selection_v0.4.png` | η–I 与 η–σ_gp 双面板 |
| `data/processed/gp_suggestions_v0.4.csv` | 5 行 × 8 列补测建议 |
| `data/processed/figures/gp_suggestions_v0.4.png` | V–油门散点（X 标记、σ 缩放） |

## 6. 数据诚信

1. 输出 CSV 每行带 `data_note`（Pareto / 补测建议各一条），图件红字 SIM 标注；
2. σ_gp 是 GP 平滑代理的预测标准差，**不是**测量不确定度 U(k=2)，两者不得混写；
3. 外推区（低油门、超已测电压/油门范围）不可信，补测推荐已限制在已测油门区间内；
4. 不得把 Pareto/knee 数值写成采购或设计结论，尤其不得作为安全边界依据。

## 7. 测试

`code/selection/test_multiobjective.py` 9 项：Pareto 基本性质（可行、σ>0、保守≤η、knee 唯一）、前沿非支配且按保守 η 降序、无候选报错、非法参数、CSV/PNG 覆盖保护、推荐点边界/间距/排序、推荐 CSV+PNG、main pareto 端到端（成功/已存在/无候选）、main suggest 端到端。

选型模块合计 **43 项**（v0.1/v0.2 共 20 + v0.3 14 + v0.4 9）。

## 8. 限制与 v0.5 待办

- **无成本项**：需建立真实产品参数/价格表后再加入成本目标（当前明确不伪造）；
- 目标仍只含效率/电流/稳健性，未含重量、噪声、寿命、温升余量；
- 补测推荐为贪心启发式，未做贝叶斯优化/主动学习的收益量化；
- 候选网格分辨率有限（13×41），可行性边界附近存在离散化误差；
- 实机数据到位后须用 `--source MEASURED` 重跑，并复核 GP/σ 合成公式。

## 9. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 初版：真多目标 Pareto + knee + GP 补测推荐 + 演示与 9 项测试，D028 |
