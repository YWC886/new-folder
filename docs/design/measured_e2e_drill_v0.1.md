# MEASURED 端到端演练 v0.1（`code/tools/measured_e2e_drill.py`）

> 状态：草稿（v0.1，2026-11-19）。目标：在真实台架数据（M0.4）到位前，验证 MEASURED 通路的
> **标记纪律与代码闭环**。本演练不产生实验结论。

## 1. 目的与边界

- 验证链路：`measured_readiness`（门禁）→ `compute_efficiency --require-measured`（流水线）→
  `aggregate_efficiency --require-measured`（汇总）→ `match_propulsion`（选型入口）→ 负向对照。
- 全部产物写在**临时目录**（或显式 `--out-dir`），绝不写入仓库 `data/`。
- 演练夹具为**人工合成稳态数据**（1200 行、1000 S/s），meta/标定中明确标注「演练夹具，不是真实测量/标定」。
- 本演练证明的是**标记与流程可闭环**，不证明物理真实性、标定准确性、量程或安全。

## 2. 演练步骤

| # | 检查 | 断言 |
| --- | --- | --- |
| 1 | `load_calibration` | 标定 JSON 可加载，`simulated:false` |
| 2 | `readiness_ready` | `measured_readiness.assess` 返回 `ready:true`、无 errors |
| 3 | `pipeline_measured` | `compute_efficiency(require_measured=True)` 通过，`simulated:false`，稳态样本 ≥500 |
| 4 | `aggregate_measured` | `aggregate(require_measured=True)` 的 `sources == ["MEASURED"]` |
| 5 | `selection_measured` | `match_propulsion.assert_measured` 通过，按演练推力匹配到 ≥1 候选 |
| 6 | `negative_sim_rejected` | 同数值但标记 SIM 时：门禁 `ready:false`、流水线抛 `MEASURED 守门拒绝` |

## 3. 演练结果（2026-11-19）

```
[OK] load_calibration: simulated=False
[OK] readiness_ready: errors=[]
[OK] pipeline_measured: simulated=False samples=500 T=9.800N
[OK] aggregate_measured: sources=['MEASURED'] rows=1
[OK] selection_measured: candidates=1 top=DRILL_MEASURED
[OK] negative_sim_rejected: readiness_rejected=True pipeline_rejected=True
统计：T=9.800 N，τ=0.1000 N·m，η_sys=0.2842，稳态 500 点，选型候选 1 个
```

`exit 0` 表示 6 项检查全部通过；任一失败 `exit 1`，参数/异常 `exit 2`。

## 4. 复现命令

```powershell
# 临时目录演练（默认）
py -3.12 code\tools\measured_e2e_drill.py

# 保留夹具与产物到指定目录（便于人工检查；仍不得入库）
py -3.12 code\tools\measured_e2e_drill.py --out-dir work\tmp\measured_e2e_drill --json
```

## 5. 测试

`code/tools/test_measured_e2e_drill.py` 5 项：全链路 6 检查通过、负向对照生效、仓库 `data/raw` 不产生 `DRILL*` 残留、
CLI `--json` 退出码与 6 项检查、`--out-dir` 夹具落盘。

## 6. 限制与下一步

- 夹具数值为人工设定常数，**不能**用于评估标定质量、量程、噪声或安全边界；
- 未覆盖：串口采集、ADS1256 时序、双人砝码标定签署、实机电磁干扰、台架安全 SOP；
- 下一步：M0.4 后用真实读数运行 `calibration_fit.py` 生成 MEASURED 标定，重跑本演练的
  `--out-dir` 版本并归档报告；随后再做 `--require-measured` 的真实地图/选型闭环。

## 7. 变更记录

- 0.1（2026-11-19）：首版演练脚本 + 5 项测试 + 负向对照；对应全仓 215 项测试（工具 24）。
