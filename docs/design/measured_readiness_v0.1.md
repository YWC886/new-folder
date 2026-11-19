# MEASURED 通路就绪检查 v0.1（M0.4 门禁）

- 文档版本：v0.1（草稿，等待 M0.4 实机数据验证流程）
- 日期：2026-11-19
- 对应代码：`code/processing/measured_readiness.py`（10 项测试）
- 关联：D032（标定拟合口径）、D035（本门禁决策）、D007/D011（数据纪律）、D031/D033（REFERENCE 边界）

## 1. 目的

在硬件到位、双人砝码标定完成之前，先把"什么样的输入才算实测"固化为可执行检查，
避免 SIM / REFERENCE / 合成标定被误接入 MEASURED 通路，也避免为了"跑通"而修改
meta 或标定标记（学术诚信红线）。

本检查器是 **M0.4 的入场券**，不是标定质量评估：标定质量由 `calibration_fit` 的
R² / 重复性 / 迟滞指标与双人签字记录负责。

## 2. 检查项

| 对象 | 条件 | 级别 |
| --- | --- | --- |
| 标定 JSON | 顶层 `simulated` 必须显式 `false` | 错误 |
| 标定 JSON | `thrust.k/b`、`torque.k/b` 为有限数值且 `k ≠ 0`（量级 <1e9） | 错误 |
| 标定 JSON | `propeller.diameter_m` 可用，否则由 meta 兜底 | 警告→错误（两者都缺时） |
| meta JSON | 显式 `simulated: false`（SIM 数据必须拒绝） | 错误 |
| meta JSON | `mode == "serial"`（`simulate` 模式拒绝） | 错误 |
| meta JSON | `status == "ok"` | 警告 |
| meta JSON | `rows_written` 为正整数 | 错误 |
| 原始 CSV | 表头与 `compute_efficiency.RAW_FIELDS` 完全一致 | 错误 |
| 原始 CSV | 必需通道 `thrust_raw/torque_raw/rpm/voltage_v/current_a` 有可解析数值 | 错误 |
| 原始 CSV | 至少 1 行数据 | 错误 |

## 3. 用法与输出

```powershell
py -3.12 code\processing\measured_readiness.py `
  --input data\raw\20261119_MEASURED_22.2V_50pct_R1.csv `
  --calib data\metadata\calib_MEASURED.json
```

- 退出码：`0` 就绪；`1` 未就绪（列出错误）；`2` 用法/读取异常。
- `--json` 打印机器可读报告；`--output <path>` 另存 JSON（含 `ready/errors/warnings/facts/guidance`）。
- 建议顺序（M0.4 实机数据到位后）：
  1. `measured_readiness`（本门禁）→ `0`；
  2. `compute_efficiency --steady auto`；
  3. `aggregate_efficiency` → `plot_efficiency_map --uncertainty`；
  4. `selection ... --source MEASURED`（数据不足时仍以网格点匹配为主）。

## 4. SIM 拒绝演练（2026-11-19）

用已有 SIM 数据跑门禁，预期拒绝：

```text
py -3.12 code\processing\measured_readiness.py `
  --input data\raw\20261117_SIM_22V2_50pct_R1.csv `
  --calib data\metadata\calib_SIM_DEMO.json
```

实测结果：`NOT READY`，3 条错误（标定 simulated→True、meta simulated→True、meta.mode=simulate），
1 条警告（meta.status=completed），退出码 1；报告留存于 `work/tmp/measured_readiness/sim_refusal_report.json`
（临时，不入库）。说明门禁对 SIM 输入确实生效。

## 5. 边界与限制

- 只验证标记与结构，**无法验证数据真的来自传感器**；物理真实性依赖双人现场记录与签字。
- 检查器不修改任何输入；发现 SIM 输入应拒绝并保持原样。
- 阈值（R²/重复性/迟滞）由 `calibration_fit` 在生成标定时给出；门禁只判断"是否声称实测"。
- 尚未与 `compute_efficiency` 强制联动；v0.2 考虑增加 `--require-measured` 守门参数与 CI 步骤。

## 6. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 初版：检查项表、退出码、SIM 拒绝演练、边界与 v0.2 待办 |
