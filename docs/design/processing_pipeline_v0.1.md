# 数据处理与效率计算方案 v0.1

| 项 | 内容 |
| --- | --- |
| 状态 | **草稿 v0.1**（2026-11-19），D 评审后升 v0.2 |
| 实现 | `code/processing/compute_efficiency.py`（8 项回归测试通过） |
| 输入 | 原始 CSV（协议 v0.1）、标定 JSON、`meta.json` |
| 输出 | `data/processed/<run_id>_processed.csv`、`data/metadata/<run_id>_efficiency.json` |
| 责任人 | D（数据建模），评审：C、A |

> **数据诚信**：当前仅有模拟数据（`SIM`）与合成标定（`calib_SIM_DEMO.json`）。在实机静态砝码标定完成前，流水线输出只能证明"软件能算"，**不能作为效率结论**。

## 1. 流水线

```text
raw CSV（13 列）
   │  校验必需通道：thrust_raw, torque_raw, rpm, voltage_v, current_a
   ▼
标定 JSON（k_t/b_t, k_q/b_q, 桨径, 可选空气密度）
   │  换算：T = k_t·raw + b_t；Q = k_q·raw + b_q
   ▼
物理量：T[N], Q[N·m], n[r/min], ω[rad/s], U[V], I[A]
   │  P_shaft = Q·ω；P_elec = U·I；P_ideal = T^1.5/√(2ρA)
   ▼
效率：η_em = P_shaft/P_elec；FM = P_ideal/P_shaft；η_sys = FM·η_em
   │
   ├─► 逐样本 CSV（data/processed/，可复查每个点）
   └─► 稳态窗口汇总 JSON（data/metadata/，用于效率地图与报告）
```

## 2. 效率定义（统一口径，避免论文/汇报口径不一）

| 符号 | 名称 | 定义 | 物理含义 |
| --- | --- | --- | --- |
| `η_em` | 电机+电调效率 | `P_shaft / P_elec` | 电能 → 轴功率（含电调损耗、铜损、铁损、风摩） |
| `FM` | 螺旋桨品质因数 | `P_ideal / P_shaft`，`P_ideal = T^1.5/√(2ρA)` | 静态悬停动量理论理想功率 / 实际轴功率 |
| `η_sys` | 系统效率 | `P_ideal / P_elec = FM·η_em` | 电能 → "理想诱导功率"的总体利用率 |

- `ρ`（空气密度）：`--rho` 显式值 > 标定 JSON > 实测环境温压按 `ρ = p/(R·T)`（R=287.05 J/(kg·K)，p 单位 Pa，T 单位 K）> 默认 1.204 kg/m³。
- `A`（桨盘面积）：`A = πD²/4`；`D` 来自标定 JSON 的 `propeller.diameter_m`、`meta.json` 的 `test.prop_diameter_m` 或 `--diameter`。
- 注意：`FM` 的动量理论公式只适用于**静态悬停**（无来流）；有来流时要用推进效率 `η_p = T·V/P_shaft`，另立版本，禁止混用。

## 3. 标定 JSON 格式（v0.1）

```json
{
  "schema_version": "0.1",
  "simulated": false,
  "source": "2026-11-27 推力/反扭矩通道静态砝码标定（双人）",
  "thrust": {"k": 0.00035, "b": 0.0, "unit": "N per ADC count"},
  "torque": {"k": 5.88e-06, "b": 0.0, "unit": "N·m per ADC count"},
  "propeller": {"diameter_m": 0.4572},
  "air_density_kg_m3": 1.125
}
```

- 真实标定：`simulated: false`，`source` 写明日期、传感器编号、砝码等级与记录人；
- 合成/演示标定：`simulated: true`，并在 `source` 或 `data_notice` 里注明"仅流程联调"；
- 标定 JSON 放 `data/metadata/calib_<传感器编号>_<日期>.json`，`calib_SIM_DEMO.json` 仅作示例保留。

## 4. 汇总 JSON 关键字段

| 字段 | 说明 |
| --- | --- |
| `simulated` / `data_notice` / `simulated_reason` | 模拟标记与来源说明（必须随结果一起引用） |
| `rows` / `window.window_s` / `window.samples` | 样本量、稳态窗口长度与点数 |
| `window.thrust_N` … `window.eta_sys` | 稳态窗口内各量的 count/mean/std/min/max/relative_std |
| `conditions` | run_id、mode、组合、重复、电压/油门设定、桨径、操作人 |
| `assumptions.air_density_kg_m3` / `air_density_source` | 密度取值与来源 |
| `assumptions.eta_definitions` | 三个效率公式，供报告直接引用 |
| `calibration` | 实际使用的 k/b，保证可追溯 |
| `warnings` | 缺 meta、未标定、无效效率行等 |

## 5. 质量门槛（实机数据适用）

| 检查 | 门槛 | 处理 |
| --- | --- | --- |
| 必需通道完整、有限 | 100% | 缺一即报错退出，不静默跳过 |
| 稳态窗口 `thrust_N` 相对标准差 | ≤1% | 超过给 warning，需加长稳定时间 |
| `eta_em` | 0 < η < 1 | 越界视为标定/接线异常，停止分析 |
| `FM` | 0 < FM ≤ 1（动量理论上限附近的偏差需解释） | 越界视为标定/转速异常 |
| 标定 `simulated` | 必须为 false 才能进"实测"结论 | 否则只允许用于流程演示 |

## 6. 与后续模块的接口

- **效率地图**：按（电压, 油门/转速）网格汇总多次运行的 `window.*.mean` → `data/processed/efficiency_map_runs.csv` / `efficiency_map_grid.csv`（v0.1 已实现 `aggregate_efficiency.py`，成图见 `plot_efficiency_map.py` 与 `efficiency_map_v0.1.md`）；
- **GP 代理模型**：输入 `(U, n, 桨)`，输出 `η_sys`/`FM`，与 `work/prestudy/prestudy_gp.py` 对接；
- **选型匹配**：以效率地图/代理模型为代价面，搜索满足推力需求的组合（见 `docs/plan/拓展方向_ExpansionDirections_v0.1.md`）；
- **报告图件**：统一从汇总 JSON 出图，禁止手工抄数。

## 7. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 初版：定义 η_em / FM / η_sys、空气密度、标定 JSON、质量门槛；实现 `compute_efficiency.py` 并通过 8 项测试 |
