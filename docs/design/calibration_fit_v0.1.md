# 静态砝码标定拟合工具 v0.1（`code/processing/calibration_fit.py`）

- 文档版本：v0.1（草稿）
- 日期：2026-11-19
- 负责人：C（采集/标定）
- 状态：软件流程已实现并通过 15 项单元测试；**尚未在实机读数上运行**（需 M0.4 硬件链路与双人静态砝码标定）

## 1. 目的与边界

把 M0.4「拉压力传感器 → 24 bit ADC → 串口 → CSV」链路产出的**静态砝码读数**，拟合为
`compute_efficiency` 可直接加载的标定 JSON（`thrust.k/b`、`torque.k/b`）。

- 输入必须是**真实加载/卸载读数**（双人、砝码等级与 g 依据见 `docs/test/静态砝码读数记录_v0.1.md`）。
- 输出固定为 `simulated: false`，但**不等于已验证**：拟合质量只说明本次静态标定的一致性，
  动态工况仍需复核安装约束、线缆应力与温漂（见 D032 与 §6 限制）。
- 禁止用仿真数据运行本工具生成 `simulated: false` 的标定；仿真标定见 `data/metadata/calib_SIM_*.json`。

## 2. 输入格式（长表 CSV）

```csv
channel,direction,repeat,applied,raw
thrust,load,1,0,12
thrust,load,1,9.79,28000
...
torque,unload,3,0.98,16000
```

| 列 | 含义 | 约束 |
|---|---|---|
| channel | 通道 | `thrust` / `torque` |
| direction | 加载方向 | `load` / `unload` |
| repeat | 重复序号 | 整数 ≥1 |
| applied | 施加物理量 | N / N·m，含 g=9.79 m/s² 换算，≥0 |
| raw | 原始读数 | ADC counts 或传感器原始值 |

空行与 `#` 注释行跳过；列顺序不限；编码 UTF-8（可带 BOM）。

## 3. 拟合与质量指标

对每通道做最小二乘 `applied = k·raw + b`，并计算：

| 指标 | 定义 | 门槛（默认） |
|---|---|---|
| R² | 1 − SS_res/SS_tot | ≥0.9995 |
| RMSE / max_abs_error | 残差统计（物理量单位） | 报告 |
| 重复性（%FS） | 同 applied 水平、跨 repeat 换算力值的样本标准差最大值 ÷ 量程 | ≤0.5%FS |
| 迟滞（%FS） | 同水平加载均值与卸载均值之差最大值 ÷ 量程 | ≤0.5%FS |

任一项超限写入 `warnings`（不阻断输出）；缺加载/卸载成对数据时迟滞记为 `null` 并告警。

## 4. 输出 JSON（`compute_efficiency.load_calibration` 兼容）

```json
{
  "schema_version": "0.1",
  "simulated": false,
  "source": "静态砝码标定（双人、加载/卸载）",
  "created_at": "...",
  "thrust": {"k": 0.00035, "b": 0.0, "unit": "N/count", "metrics": {"n": 24, "levels": 6, "full_scale": 12.25, "r2": 1.0, "rmse": 0.0, "max_abs_error": 0.0, "repeatability_pct_fs": 0.0, "hysteresis_pct_fs": 0.0}},
  "torque": {"k": 5.88e-06, "b": 0.0, "unit": "N·m/count", "metrics": {...}},
  "propeller": {"diameter_m": 0.4572},
  "thresholds": {"r2_min": 0.9995, "repeatability_max_pct_fs": 0.5, "hysteresis_max_pct_fs": 0.5},
  "warnings": []
}
```

## 5. 用法

```powershell
py -3.12 code\processing\calibration_fit.py `
  --input data\calibration\20261126_静态砝码标定_R1.csv `
  --output data\calibration\calib_MEASURED_20261126.json `
  --diameter 0.4572 `
  --source "静态砝码标定（B、C 双人，加载/卸载，M1 砝码）"
```

随后：

```powershell
py -3.12 code\processing\compute_efficiency.py `
  --input data\raw\<run_id>.csv --calib data\calibration\calib_MEASURED_20261126.json
```

## 6. 限制与待办

1. 仅两点式线性拟合（`b` 为截距）；零点漂移/温漂修正未建模，需要前后零位读数与复测。
2. 重复性与迟滞为本次读数内部统计，不含砝码质量、g、力臂长度的 B 类不确定度（见台架不确定性预算）。
3. 扭矩通道由力臂 + 砝码施加：力臂长度、水平度与摩擦须记录在记录表，否则迟滞会被低估。
4. 实机前须按 `docs/test/静态砝码读数记录_v0.1.md` 双人签署，并在 `decisions.md` D032 约束下复核。
5. v0.2 待办：分位温度修正（多点温度）、重复标定漂移统计、不确定度合成导出（与 `compute_efficiency` 的 U 表联动）。

## 7. 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| 0.1 | 2026-11-19 | 首版：读数解析、双通道拟合、质量指标、JSON 输出、CLI、15 项测试 |
