# 补测批次计划 v0.1（Next Batch Plan）

## 1. 目的与边界

把效率地图的 "GP σ 补测建议" 转成**台架可执行的补测计划表**，按 D056 统一口径排序（优先补测测量不确定度与模型不确定性合成后最大的点）。

- 只生成计划，不产生数据、不替代实测、不改变效率地图；
- 输入为 SIM 稀疏地图（`data/processed/efficiency_map_runs.csv`），计划值仅供台架安排使用；
- 输出带 `data_note`，任何引用必须保留 "SIM 补测计划，不是实验结果" 的标注。

## 2. 算法

1. 读 runs CSV（≥4 点），用 `bo_suggest` 拟合 η 的 GP（LOOCV 选核宽）；
2. 在已测电压/油门区间内生成候选网格（13×41），按 `sigma` 策略贪心选 n 个点，点间归一化距离 ≥ `min_distance`（默认 0.12）；
3. D056 口径：`u_meas = U(k=2)/2`、`σ_total = sqrt(u_meas² + σ_gp²)`；
4. 按 `σ_total` 降序排行，输出计划表（每点默认 30 s 采集，含悬停/巡航两侧参考点）。

## 3. 字段

| 字段 | 含义 |
|---|---|
| rank | 优先级排序（σ_total 降序） |
| voltage_set_v / throttle_set_pct | 建议补测工况 |
| predicted_eta | GP 预测 η_sys（点估计，非实测） |
| gp_std_eta | GP 预测标准差（1σ，非 U） |
| u_meas | 测量不确定度（=U(k=2)/2） |
| sigma_total | 合成 1σ：sqrt(u_meas²+σ_gp²) |
| priority | 排序键（=sigma_total） |
| est_duration_s | 单点计划采集时长 |
| data_note | 数据边界标注 |

## 4. 用法

```bat
py -3.12 code\selection\batch_plan.py --overwrite
py -3.12 code\selection\batch_plan.py --n 8 --u-k2 0.0226 --duration 40 --output data\processed\next_batch_plan_v0.1.csv --overwrite
py -3.12 -m unittest discover -s code\selection -p "test_batch_plan.py"
```

SIM 演示（2026-11-23）：5 点计划 → `data/processed/next_batch_plan_v0.1.csv`；#1 `26.52 V / 34.4%`、#2 `26.52 V / 90.6%`、#3 `18.81 V / 34.4%`、#4 `18.81 V / 90.6%`、#5 `26.52 V / 62.5%`（σ_total 0.0153/0.0153/0.0143/0.0143/0.0140）。

## 5. 与现有工具的关系

- `gp_surface.py`：得 σ_gp 面；`bo_suggest.py`：策略对比与候选建议；
- `batch_plan.py`：把建议转成计划表（本工具）；
- `design_matrix.py`：把计划表转成采集排程（run_id/顺序/重复）；
- `measured_readiness.py` 与 `--require-measured` 守门：确保真正采集的是 MEASURED 数据。

## 6. 限制与后续

- 计划基于 SIM 地图与默认 U 值；实机后须用真实标定（D032/M0.4）替换 U(k=2)；
- 未纳入温升/冷却时间与换桨时间，仅按单点 30 s 估算；
- v0.2 候选：与 `design_matrix.py` 直接对接（输出排程）、按巡检悬停/巡航权重加权优先级、成本约束（每次上电总时长）。

## 7. 变更记录

- 0.1（2026-11-23）：计划表工具 + 3 项测试 + SIM 演示 5 点。
