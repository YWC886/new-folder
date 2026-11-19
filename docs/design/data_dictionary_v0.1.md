# 数据字典 v0.1（采集与处理共用）

| 项 | 内容 |
| --- | --- |
| 状态 | 草稿 v0.1（2026-11-19），随 `code/acquisition` 协议 v0.1 同步 |
| 适用范围 | 原始 CSV、元数据 JSON、校验报告 JSON |
| 约束 | raw 只读；模拟数据文件名与 `meta.json` 必须标记 `SIM` / `simulated: true` |

## 1. 文件与命名

| 类型 | 路径 | 命名规则 | 说明 |
| --- | --- | --- | --- |
| 原始数据 | `data/raw/` | `YYYYMMDD_<组合>_<电压>_<油门>_<重复>.csv` | 例：`20261117_SIM_22V2_50pct_R1.csv`；SIM 表示模拟 |
| 元数据 | `data/raw/` | 同名 `.meta.json` | 采集条件、操作人、异常备注 |
| 校验报告 | `data/metadata/` | 同名 `.validation.json` | `validate.py` 生成 |
| 标定系数 | `data/metadata/` | `calib_<传感器编号>_<日期>.json` | 静态砝码标定结果（待建） |
| 处理后数据 | `data/processed/` | `<run_id>_processed.csv` | 由处理脚本生成，可重算 |

## 2. 串口行协议 v0.1（MCU → PC，固定 11 列）

| 序号 | 列名 | 类型 | 单位 | 必需 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1 | `seq` | uint32 | — | 是 | 从 0 递增，用于检测丢包 |
| 2 | `device_time_ms` | uint64 | ms | 是 | MCU 毫秒时间戳 |
| 3 | `thrust_raw` | uint32/int32 | ADC 计数 | 是 | 推力通道原始值，标定在 PC 侧做 |
| 4 | `torque_raw` | uint32/int32 | ADC 计数 | 否 | 反扭矩通道原始值 |
| 5 | `rpm` | float | r/min | 否 | 转速 |
| 6 | `voltage_v` | float | V | 否 | 母线电压 |
| 7 | `current_a` | float | A | 否 | 母线电流 |
| 8 | `motor_temp_c` | float | ℃ | 否 | 电机温度 |
| 9 | `ambient_temp_c` | float | ℃ | 否 | 环境温度 |
| 10 | `humidity_pct` | float | %RH | 否 | 相对湿度 |
| 11 | `pressure_kpa` | float | kPa | 否 | 大气压 |

- 分隔符 `,`，行尾 `\n`，UTF-8；未连接的通道**留空**，不得填 0（0 是有效读数）。
- 上位机按列名映射；新增列需升协议版本，不得插入已有序号中间。

## 3. 原始 CSV（落盘后，13 列）

| 列名 | 类型 | 单位 | 说明 |
| --- | --- | --- | --- |
| `host_ts` | string (ISO 8601) | — | 上位机接收时间（仅供参考） |
| `elapsed_s` | float | s | 自采集开始计时 |
| `seq` | int | — | 设备序号 |
| `device_time_ms` | int | ms | 设备时间戳 |
| `thrust_raw` | float | ADC 计数 | 必需、有限值 |
| `torque_raw` | float | ADC 计数 | 可空 |
| `rpm` | float | r/min | 可空 |
| `voltage_v` | float | V | 可空 |
| `current_a` | float | A | 可空 |
| `motor_temp_c` | float | ℃ | 可空 |
| `ambient_temp_c` | float | ℃ | 可空 |
| `humidity_pct` | float | %RH | 可空 |
| `pressure_kpa` | float | kPa | 可空 |

## 4. 元数据 JSON（`*.meta.json`）

| 字段组 | 字段 | 说明 |
| --- | --- | --- |
| identity | `run_id`、`operator`、`combo`、`repeat`、`mode`（simulate/serial） | 运行标识 |
| time | `started_at`、`finished_at`、`duration_s` | 采集时间 |
| interface | `port`、`baud`、`sample_rate_sps` | 串口/采样参数 |
| conditions | `voltage_set_v`、`throttle_set_pct`、`prop_diameter_m`、`ambient_*` | 测试条件 |
| anomalies | `notes`、`events[]` | 异常与人工备注 |
| simulated | `simulated: true/false` | **模拟数据必须为 true** |

## 5. 校验报告 JSON（`*.validation.json`）

| 字段 | 说明 |
| --- | --- |
| `schema_version` | 报告格式版本（当前 0.1） |
| `source_file` | 被校验 CSV 绝对路径 |
| `simulated` | 是否模拟数据 |
| `status` | `pass` / `warn` / `fail` |
| `rows`、`duration_s`、`estimated_sample_rate_sps` | 规模与采样率 |
| `errors[]`、`warnings[]` | 失败项/告警项文本 |
| `statistics` | 各通道 count/mean/std/min/max/missing |
| `steady_window` | 末尾窗口统计与 `relative_std` |
| `checked_at` | 校验时间 |

判定规则：

- **fail**：表头不符、无数据行、必需通道空/非有限值、`seq` 重复或缺失、设备时间倒退、采样率低于 `--min-sample-rate`；
- **warn**：可选通道整列缺失、元数据不可读、稳态窗口 `thrust_raw` 或 `rpm` 相对标准差 >1%；
- **pass ≠ 标定合格、≠ 物理意义正确、≠ 安全**。

## 6. 版本与变更

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 初版：对齐 `code/acquisition` 协议 v0.1 与校验器输出 |

变更规则：任何列增删、单位变化、命名规则调整 → 版本 +0.1 → 同步更新 `code/acquisition/README.md`、本文件、处理脚本与测试。
