# 效率地图数据与图件方案 v0.1

| 项 | 内容 |
| --- | --- |
| 状态 | 草稿 v0.1 + 0.2 增量（2026-11-19） |
| 实现 | `code/processing/aggregate_efficiency.py`、`code/processing/plot_efficiency_map.py` |
| 测试 | 8 项汇总测试 + 3 项绘图冒烟测试（与流水线共 23 项），全部通过 |
| 输入 | 多份 `data/metadata/*_efficiency.json`（由 `compute_efficiency.py` 生成） |
| 输出 | `data/processed/efficiency_map_runs.csv`、`efficiency_map_grid.csv`、`data/processed/figures/efficiency_map_v0.1.png` |
| 责任人 | D，评审：C（数据接口）、B（物理合理性） |

> **当前为 16 工况 SIM 地图**（4 电压 × 4 油门，`simulate_campaign.py` 生成），图件是流程预览，不是效率地图结论。实机多工况数据到位后重跑同一脚本即可得到正式图。

## 1. 数据流

```text
raw CSV ──compute_efficiency.py──► <run_id>_efficiency.json（每次运行 1 份）
                                          │
                          aggregate_efficiency.py（扫描 data/metadata）
                                          │
              ┌───────────────────────────┴───────────────────────────┐
              ▼                                                       ▼
  efficiency_map_runs.csv                              efficiency_map_grid.csv
  （每次运行 1 行，含 source）                          （按 source/组合/电压/油门分组均值±std）
              │
              ▼
  plot_efficiency_map.py ──► data/processed/figures/efficiency_map_v0.1.png
```

## 2. `runs.csv` 字段（每次运行一行）

| 字段 | 说明 |
| --- | --- |
| `run_id` | 运行标识（来自 efficiency.json 的 conditions.run_id） |
| `source` | `SIM`（模拟）或 `MEASURED`（实机）；由 `simulated` 标记推导 |
| `mode` / `combo` / `repeat` / `operator` | 采集条件 |
| `motor` / `esc` / `prop` / `prop_diameter_m` | 被测对象（未填则"未填写"） |
| `voltage_set_v` / `throttle_set_pct` | 设定电压与油门（地图坐标轴） |
| `rows` / `window_samples` / `window_s` | 原始行数与稳态窗口信息 |
| `rpm_mean` / `thrust_N_mean` / `torque_Nm_mean` / `voltage_v_mean` / `current_a_mean` | 稳态均值 |
| `p_shaft_w_mean` / `p_elec_w_mean` | 轴功率/电功率均值 |
| `eta_em_mean` / `fm_mean` / `eta_sys_mean` | 三个效率指标均值 |
| `air_density_kg_m3` / `calibration_source` / `file` | 空气密度、标定来源、源文件（可追溯） |
| `steady_mode` | 选窗方式（`last` 末尾固定窗口 / `auto` 自动判稳） |
| `u_eta_em_k2` / `u_fm_k2` / `u_eta_sys_k2` | 该 run 的扩展不确定度 U(k=2)（来自汇总 JSON 的 `uncertainty`，旧 JSON 为空） |

## 3. `grid.csv` 字段（作图用）

按 `(source, combo, voltage_set_v, throttle_set_pct)` 分组：

| 字段 | 说明 |
| --- | --- |
| `runs` | 该工况的运行次数（重复次数） |
| `thrust_n_mean` / `rpm_mean` | 推力、转速组均值 |
| `eta_em_mean` / `eta_em_std` | 电机+电调效率均值 / 样本标准差（n=1 时为 0） |
| `fm_mean` / `fm_std` | 螺旋桨品质因数 |
| `eta_sys_mean` / `eta_sys_std` | 系统效率 |
| `u_eta_em_k2_max` / `u_fm_k2_max` / `u_eta_sys_k2_max` | 同组 runs 的 U(k=2) 最大值（保守，不随重复次数降低） |

## 4. 图件规则（`plot_efficiency_map.py`）

- 数据点 <4 或不足 2×2 网格 → 散点图（标注数值）；否则 → 热力图（`pcolormesh` + 色标）；
- 横轴 = 母线电压（V），纵轴 = 油门指令（%），颜色 = 所画指标（默认 `eta_sys`，可 `--field eta_em|fm|eta_sys`）；
- **SIM 数据必须显示红字「SIMULATED DATA — NOT EXPERIMENTAL」**；图标题含 `v0.1`；
- 输出默认 `data/processed/figures/efficiency_map_v0.1.png`，默认拒绝覆盖（`--overwrite` 才覆盖）。

## 5. 数据纪律

1. `runs.csv` 与 `grid.csv` 必须保留 `source` 列，SIM 与实测不得合并成同一行；
2. 终端与图件都会告警 SIM；报告中引用图件必须保留该标注；
3. 重复 `run_id` 只保留第一份并告警；坏 JSON 跳过并告警，全部无效时报错退出（退出码 2）；
4. 网格标准差是"运行间重复性"，不是测量不确定度；不确定度 U(k=2) 已由流水线一阶传播给出并带入 runs/grid，两者不可混用；

## 6. 已知限制 / v0.2 待办

- 16 工况地图仍是 SIM 预览；真实效率地图需实机 4 电压 × 8 转速 × 3 重复的网格数据；
- 未做温度/电压漂移修正；
- 未把 `work/prestudy/efficiency_demo.py` 的合成地图与真实流水线统一（口径相同、代码两套，需合并）；
- U 尚未画进图件（误差棒/置信带），v0.3 与绘图脚本一起改；
- 公开数据对标（UIUC 等）另见 `docs/plan/拓展方向_ExpansionDirections_v0.1.md` 方向二。

## 7. 复现命令

```powershell
py -3.12 -m unittest discover -s code\processing -p "test_*.py" -v
py -3.12 code\processing\aggregate_efficiency.py --dir data\metadata
py -3.12 code\processing\plot_efficiency_map.py
```

## 8. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 初版：aggregate + plot 实现，18 项测试通过；SIM 单点预览图 |
| 0.2 | 2026-11-19 | 增量：runs/grid 增加 `steady_mode` 与 U(k=2) 列（grid 取组内最大）；16 工况 SIM 地图替换单点图；汇总测试 7→8、合计 23 项 |
