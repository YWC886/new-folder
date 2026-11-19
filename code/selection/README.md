# code/selection · 选型匹配原型 v0.4

把「任务推力需求」映射为效率地图上的候选电压/油门组合，输出 Pareto 图与补测建议。**当前输入只有 SIM 模拟效率地图，输出仅用于验证软件链路，不是真实选型结论。**

v0.1 离散网格 → v0.2 油门线性插值 + 多目标排序 + U 过滤 → v0.3 GP 连续匹配 → v0.4 真多目标 Pareto（η/电流/稳健性）+ GP 补测点推荐。

## 文件

| 文件 | 用途 |
| --- | --- |
| `match_propulsion.py` | v0.2：读效率地图 runs CSV → 插值/网格候选 → 多目标排序 → Top-N 报告 CSV + Pareto 图 PNG |
| `test_selection.py` | v0.1/v0.2 共 20 项回归测试（读入、筛选、去重排序、插值、多目标、U 过滤、Pareto、报告、图件、CLI 端到端与退出码） |
| `gp_match.py` | v0.3：GP 连续匹配（thrust/eta 双 GP → 每电压油门扫描 → σ_gp 合成保守效率 → 多目标排序） |
| `test_gp_match.py` | v0.3 共 14 项测试（拟合、精确命中、过滤、排序、输出、CLI） |
| `multiobjective.py` | v0.4：GP 多目标 Pareto（η/电流/保守 η）+ knee + GP σ 补测点推荐（13×41 网格，自写非支配筛选） |
| `test_multiobjective.py` | v0.4 共 9 项测试（Pareto 性质、前沿排序、非法参数、CSV/PNG、推荐点边界与端到端） |

## 快速运行

```powershell
# 测试（20 + 14 + 9 = 43 项）
py -3.12 -m unittest discover -s code\selection -p "test_*.py" -v

# v0.4 示例：5 N ±10% 真多目标 Pareto（η / 电流 / 稳健性）+ knee
py -3.12 code\selection\multiobjective.py `
  --input data\processed\efficiency_map_runs.csv `
  --thrust 5 --tolerance 0.1 `
  --output data\processed\selection_v0.4_pareto.csv `
  --figure data\processed\figures\selection_v0.4.png `
  --overwrite

# v0.4 示例：GP σ 补测点推荐（限定已测油门区间，间距 ≥ 0.12）
py -3.12 code\selection\multiobjective.py `
  --input data\processed\efficiency_map_runs.csv `
  --suggest --n 5 --min-distance 0.12 `
  --output data\processed\gp_suggestions_v0.4.csv `
  --figure data\processed\figures\gp_suggestions_v0.4.png `
  --overwrite

# v0.3 示例：5 N ±10%，GP 连续匹配，eta_sys 排序
py -3.12 code\selection\gp_match.py `
  --input data\processed\efficiency_map_runs.csv `
  --thrust 5 --tolerance 0.1 --objective eta_sys `
  --output data\processed\selection_v0.3_gp.csv `
  --figure data\processed\figures\selection_v0.3.png `
  --overwrite
```

常用参数（v0.4 新增标 ★）：

| 参数 | 说明 |
| --- | --- |
| `--thrust` | 需求推力（N，必填，>0） |
| `--tolerance` | 相对公差（默认 0.1 = ±10%） |
| `--max-throttle` | 油门上限（%），默认 100；GP 扫描与补测推荐同受约束 |
| `--voltages` | 限定电压，逗号分隔，如 `22.2,29.6` |
| `--source` | `ANY`（默认）/`SIM`/`MEASURED` |
| `--top` | 返回条数（默认 5） |
| `--objective` | `eta_sys`（默认）/`current`/`balanced` |
| `--max-u` | 过滤 U(k=2) 超过该值的候选（如 0.03） |
| `--no-interp` | 仅 v0.2：关闭油门插值，只用网格点 |
| `--grid-points` | v0.3：每电压油门扫描点数（默认 101） |
| `--voltage-points` / `--throttle-points` | ★ v0.4：Pareto 候选网格（默认 13×41） |
| `--suggest` | ★ v0.4：切换到补测点推荐模式 |
| `--n` / `--min-distance` | ★ v0.4：推荐点数（默认 5）/ 与已测点最小归一化距离（默认 0.12） |
| `--output` / `--figure` | 报告 CSV / 图件 PNG；默认拒绝覆盖，加 `--overwrite` |

## 匹配逻辑

### v0.4（`multiobjective.py`，多目标视图）

1. 13 电压 × 41 油门候选网格 → GP 推力过滤（相对公差）；
2. 每个候选预测 η、σ_gp、电流，并算保守效率 `η − sqrt((2σ_gp)² + u_local²)`；
3. 三目标非支配筛选（η 大 / 电流小 / 保守 η 大）→ Pareto 前沿 → knee 点；
4. 补测推荐：贪心选 σ_gp 最大的未测点，要求与已测/已选点距离 ≥ `--min-distance`，油门限制在已测区间内。

### v0.3（`gp_match.py`）

1. 读入 runs CSV → 按来源/电压/油门上限/U 上限过滤；
2. 对推力与 η_sys 各拟合一个 GP（特征 `(V/30, throttle/100)`，核宽 LOOCV 选择）；
3. 每条电压曲线上以 101 点扫描 GP 推力 → 取最接近需求推力的油门 → 邻点线性细化；
4. 预测 η_sys ± σ_gp、附加通道（η_em/FM/rpm/电流）、保守效率
   `η_conservative = η_pred − sqrt((2σ_gp)² + u_local²)`；
5. 推力公差与 `--max-u` 过滤 → 复用 v0.2 多目标排序 → Top-N；`matched_by="gp"`。

### v0.2（`match_propulsion.py`）

1. 按 `(combo, 电压)` 分组、按推力排序：需求推力落在相邻两点之间 → **线性插值**出虚拟工作点（`matched_by=interp`）；否则回退公差内 η_sys 最高网格点（`matched_by=grid`）；
2. 排序：`eta_sys` / `current` / `balanced`（0.6·η + 0.2·(1−电流) + 0.2·(1−U)）；
3. 输出含 `matched_by`、`thrust_margin_N`、`eta_sys`、`eta_sys_conservative`、`current_a`、`u_eta_sys_k2`、`score`。

Pareto 图规则：灰色为全部观测工况，红线为推力—效率非支配前沿，黄带为需求推力 ±公差，Top-N 用彩色标记；SIM 强制红字。v0.4 另出 η–电流与 η–σ_gp 双面板。

## 数据诚信（硬约束）

1. 结果行保留 `source=SIM/MEASURED`；若命中 SIM，终端打印「⚠ …仅原型演示，不是选型结论」，图件红字「SIMULATED DATA — NOT EXPERIMENTAL」；
2. SIM 匹配结果**不得**写成采购/选型建议，也不得引用具体效率数值；
3. σ_gp 是 GP 预测标准差，不是 U(k=2)，不得混写；
4. 实机效率地图到位后，同一命令加 `--source MEASURED` 才是真实选型。

## 已知限制 / 下一步（v0.5）

- **无成本项**：没有真实产品价格表就不做成本目标（不伪造数据）；
- 目标未含重量、噪声、寿命、温升余量；
- 补测推荐是贪心启发式，未做贝叶斯优化收益量化；
- 候选网格分辨率有限（13×41），边界附近有离散化误差；
- GP 外推区（低油门/超已测范围）不可用于选型或安全结论；
- 实机数据到位后复核插值/GP 误差与 σ 合成公式。

设计文档：`docs/design/selection_matching_v0.1.md`、`selection_matching_v0.2.md`、`selection_matching_v0.3.md`、`selection_matching_v0.4.md`。
