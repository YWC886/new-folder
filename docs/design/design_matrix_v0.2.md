# design_matrix v0.2 — 目标推力反解与执行顺序随机化

- 版本：v0.2（2026-11-21）
- 代码：`code/processing/design_matrix.py`
- 测试：`code/processing/test_design_matrix.py`（19 项；处理 91 项）
- 决策：D043（v0.1 排程）、D045（v0.2 推力反解/随机化）
- 上游：`data/processed/efficiency_map_runs.csv`（GP 推力代理训练数据）
- 下游：`code/acquisition/acquire.py`（`--combo/--voltage-set/--throttle-set/--repeat`）

## 1. 目的与边界

v0.1 按「电压×油门×桨型×重复」生成全因子/阶梯扫描排程，油门是固定网格。但申报书 v3 的 DoE 表述是
「3 个电压 × 3 种桨型 × 6 个目标推力水平 × 3 次重复」——**以目标推力（而非油门）组织试验**，
才能保证不同桨型在相同气动载荷下比较。

v0.2 增加两个能力：

1. `--thrust-levels`：以目标推力（N）为输入，对每个（电压, 目标推力）用已有 runs 的 GP 推力代理
   二分反解油门，生成面向 S2 的排程；仅对 `--map-prop` 指定的桨型有效（换桨后须重新标定/重拟合）。
2. `--randomize`：按 `--seed` 在电压块内随机化执行顺序，用于消除「固定顺序 × 温漂」的系统偏差。

**边界**：本工具只生成试验计划，不产生任何数据；GP 推力代理来自有限工况（当前 16 个 SIM 工况），
反解出的油门只是**计划值**，实机执行时以实测推力/转速为准；超出代理范围的工况会被跳过并记录，
不得插值外推当作可执行点（D045）。

## 2. 目标推力反解算法

1. `load_thrust_runs(path)`：读取 runs CSV（需 `voltage_set_v`、`throttle_set_pct`、`thrust_N_mean`），
   过滤非法/负值，少于 4 点报错。
2. `fit_thrust_map(runs)`：特征 `(V/30, throttle/100)`，RBF 高斯过程，核宽按 LOOCV RMSE 在
   `LENGTH_SCALES` 中选；记录 `n / length_scale / loocv_rmse / r2`。
3. `invert_throttle(model, V, T*)`：对油门区间 [0, 100] 二分（收敛 1e-4 %），返回
   `(throttle_pct, 代理推力)`；若 `T* > 代理在 100% 油门的推力 + 0.02 N` 抛 `DesignError`（不可达）。
4. `build_thrust_matrix(cfg, levels, model, map_prop)`：电压块 → 重复 → 目标推力升序；
   不可达的水平写入 `skipped`；输出 `planned_thrust_n` 列（`THRUST_FIELDS = FIELDS + ("planned_thrust_n",)`）。
5. `randomize_rows(rows, seed)`：按块内洗牌并重排 `order`；同 seed 可复现。

## 3. SIM 演示（16 工况代理）

命令：

```
py -3.12 code\processing\design_matrix.py --voltages 11.1,14.8,22.2 \
  --throttles 20,40,60,80,100 --props SIM10x4.5 --repeats 3 \
  --thrust-levels 1,2,3,5,8,12 --thrust-map data\processed\efficiency_map_runs.csv \
  --map-prop SIM10x4.5 --output data\processed\design_matrix_v0.2_demo.csv \
  --summary data\metadata\design_matrix_v0.2_demo.summary.json --overwrite
```

结果：**30 次运行**（54 个候选工况中 24 个因超出代理范围被跳过），预计 150 s 采集；
代理拟合：n=16、核宽 0.8、LOOCV RMSE 0.206 N、R²=0.998。

| 电压 | 可达目标推力（N） | 跳过（N） |
|---|---|---|
| 11.1 V | 1、2 | 3、5、8、12 |
| 14.8 V | 1、2、3 | 5、8、12 |
| 22.2 V | 1、2、3、5、8 | 12 |

说明：跳过不是缺陷，而是代理覆盖范围的诚实反映——11.1 V 满油门仅约 2.7 N、14.8 V 约 4.8 N、
22.2 V 约 10.6 N（SIM 参数），因此「同一组 6 个推力水平跨 3 个电压」在低电压端不可行；
实机排程应按电压分别选择可达水平，或提高电压/换更大桨（由台架目标决定）。

## 4. 与 S2 排程的衔接

- 真实台架 S2 的推进顺序：**标定（D032）→ 单桨电压扫描 → 拟合推力代理 → 生成目标推力排程
  → 随机化执行 → 按 D043 汇总**；
- 多桨型：每个桨型单独拟合代理、单独生成排程（`--map-prop` 与 `--props` 同值），
  不同桨型的排程用 `--combo` 区分；
- 执行的每一行可直接映射到 `acquire.py`：`prop_id→--combo`、`voltage_set_v→--voltage-set`、
  `throttle_set_pct→--throttle-set`、`repeat→--repeat`、`run_id` 作为采集文件名主干；
- 实机采集须先通过 `measured_readiness`（M0.4 门禁），并遵守双人、防护罩、急停安全 SOP。

## 5. 限制与 v0.3 待办

- 代理只在 16 个 SIM 工况上训练；真实台架会用实测数据重拟合，外推区（高推力/低电压）不可用；
- 「跳过」后的排程不平衡（各电压点数不同），统计比较时须按电压分别分析，或显式补点；
- 随机化只做块内洗牌，未做平衡区组/LHS；
- 未包含换桨等待时间、热平衡等待时间（当前只计 duration_s）。

v0.3 候选：LHS/平衡区组、按电压自动选可达推力水平、与 `measured_readiness` 联动生成执行清单。

## 6. 变更记录

- 0.1（2026-11-21）：v0.1 全因子/阶梯扫描排程（D043）。
- 0.2（2026-11-21）：目标推力反解、不可达跳过、执行顺序随机化；19 项测试（D045）。
