# 数据处理与效率计算方案 v0.2

| 项 | 内容 |
| --- | --- |
| 状态 | **草稿 v0.2**（2026-11-19），实机标定后升 v1.0 |
| 实现 | `code/processing/compute_efficiency.py`、`aggregate_efficiency.py`、`plot_efficiency_map.py`（23 项回归测试通过） |
| 输入 | 原始 CSV（协议 v0.1）、标定 JSON、`meta.json` |
| 输出 | `data/processed/<run_id>_processed.csv`、`data/metadata/<run_id>_efficiency.json`、效率地图 runs/grid CSV、图件 |
| 责任人 | D（数据建模），评审：C、A |
| 前版 | `processing_pipeline_v0.1.md`（效率口径与标定 JSON 格式不变，本版为增量） |

> **数据诚信**：当前所有产物仍来自 `SIM` 模拟数据与合成标定（`calib_SIM_*.json`）。不确定度块是"按传感器量级一阶传播"的**先验估计**，不是实测标定结果；在实机静态砝码标定完成前，不得把 η、FM 或 U 值写进报告结论。

## 1. v0.2 相对 v0.1 的增量

| 增量 | 内容 | 解决什么问题 |
| --- | --- | --- |
| 稳态窗口自动识别 | `--steady auto`：从末尾向前滑动，取首个 `thrust_raw`、`rpm` 相对标准差均 ≤ 阈值（默认 1%）的窗口；找不到则回退末尾窗口并给 warning | 固定"最后 N 秒"可能截到爬升/衰减段，导致效率被低估或方差被放大 |
| 不确定度传播 | 汇总 JSON 新增 `uncertainty` 块：η_em / FM / η_sys 的一阶相对不确定度 U(k=2) | 为效率地图与选型结论提供误差棒，避免"高精度假象" |
| 地图数据带不确定度 | runs CSV 新增 `steady_mode`、`u_eta_em_k2`、`u_fm_k2`、`u_eta_sys_k2`；grid CSV 新增三项 `*_max`（同格多条运行取最大，保守） | 作图/比对时可直接引用误差信息 |
| 汇总 schema 升版 | `schema_version: "0.2"`，`window.mode/start_s/end_s`、`window.detection` 为新增字段，旧字段保留 | 兼容 v0.1 消费者（只读 mean/std 的代码不受影响） |

## 2. 稳态窗口自动识别

```text
processed（逐样本物理量）
   │  从末尾向前，步长 step = max(1, min(window_samples // 10, 50))
   ▼
候选窗口（长度 steady_window_s，默认 0.5 s）
   │  计算 channels = (thrust_raw, rpm) 的相对标准差
   ▼
所有通道 rel_std ≤ steady_threshold（默认 1%）？
   ├── 是 → applied=True，采用该窗口
   └── 否 → 继续前移；到尾仍未找到 → applied=False，回退末尾 window（--window 指定）
```

实现要点：

- `detect_steady_window(rows, *, window_s=0.5, threshold=0.01, channels=("thrust_raw","rpm"))`：返回 `method / applied / threshold / channels / samples / start_index / end_index / start_s / end_s / duration_s / sample_rate_hz / relative_std / note`；
- 采样率由 `elapsed_s` 中位间隔倒数估计，缺省 1000 S/s；
- 阈值只用于**选窗**，不替代质量门槛；相对标准差过大的数据仍会在 `warnings` 中提示；
- 爬升段处理：`simulate_campaign.py` 生成的前 0.2 s 为软启动斜坡，auto 模式可自动跳过（实测 22.2 V/50% 工况识别到 2.0–2.499 s，thrust 相对标准差 0.73%、rpm 0.07%）。

CLI：

```powershell
py -3.12 code\processing\compute_efficiency.py `
  --input data\raw\20261119_SIM_22.2V_50pct_R1.csv `
  --calib data\metadata\calib_SIM_PHYS10x4.json `
  --window 1.5 --steady auto --steady-window 0.5 --steady-threshold 0.01
```

## 3. 不确定度传播（一阶，相对形式）

一阶假设：各输入相对不确定度独立、小量；忽略高阶项与输入间相关性。取 1σ 相对量级（来源：`work/research/bench_tech.md` 与传感器数据手册量级，实机标定后必须复核）：

| 输入 | 符号 | 1σ 相对不确定度 |
| --- | --- | --- |
| 推力 | u_T | 0.65% |
| 反扭矩 | u_Q | 0.50% |
| 转速 | u_rpm | 0.10% |
| 母线电压 | u_V | 0.10% |
| 电流 | u_I | 0.50% |
| 空气密度 | u_ρ | 0.50% |

传播公式（η_em = Qω/(UI)，FM = T^1.5/(√(2ρA)·Qω)，η_sys = FM·η_em）：

```text
u_rel(η_em) = sqrt( u_Q² + u_rpm² + u_V² + u_I² )
u_rel(FM)   = sqrt( (1.5·u_T)² + u_Q² + u_rpm² + (0.5·u_ρ)² )
u_rel(η_sys)= sqrt( (1.5·u_T)² + (0.5·u_ρ)² + u_V² + u_I² )   # 直接由输入传播，避免 FM/η_em 相关项重复计算
U(k=2)      = 2 · u_rel
```

代入上表：u_rel(η_em)=0.7211% → U=1.4422%；u_rel(FM)=1.12824% → U=2.2565%；u_rel(η_sys)=1.12824% → U=2.2565%。`uncertainty.reference_targets_k2` 记录设计目标（η_em 1.5%、FM 2.5%、η_sys 2.1%），当前仅 η_sys 的超标（2.26% > 2.1%）是**待实机标定后复核项**，不是结论性缺陷。

输出字段（`uncertainty`）：

| 字段 | 说明 |
| --- | --- |
| `method` | `first_order_relative` |
| `components_1sigma_relative` | 六个输入的 1σ 相对值 |
| `sensitivities` | η_em/FM/η_sys 对各输入的灵敏度系数（如 1.5、0.5） |
| `u_rel_eta_em` / `u_rel_fm` / `u_rel_eta_sys` | 1σ 相对合成不确定度 |
| `U_rel_eta_em_k2` / `U_rel_fm_k2` / `U_rel_eta_sys_k2` | 扩展不确定度（k=2） |
| `reference_targets_k2` / `note` | 设计目标与适用边界 |

## 4. 效率地图数据（v0.2）

- `aggregate_efficiency.py` 从 `uncertainty` 块取三项 U，写入 runs CSV：`u_eta_em_k2`、`u_fm_k2`、`u_eta_sys_k2`；
- grid CSV 对同一 (source, 组合, 电压, 油门) 分组取三项 U 的**最大值**：`u_eta_em_k2_max`、`u_fm_k2_max`、`u_eta_sys_k2_max`（保守，后续可改加权）；
- runs CSV 另加 `steady_mode`，便于区分 last/auto 两种选窗方式；
- 16 工况仿真战役重跑后：16 行 runs、16 行 grid，`steady_mode=last`，U 值 1.442%/2.257%/2.257%；图件 `efficiency_map_v0.1.png` 不变（58,842 B）。

## 5. 质量门槛（v0.2 增补）

| 检查 | 门槛 | 处理 |
| --- | --- | --- |
| 稳态窗口自动识别 | `thrust_raw`、`rpm` rel_std ≤1%（默认） | 超阈值回退并 warning；报告需注明选窗方式 |
| 不确定度目标 | η_em ≤1.5%、FM ≤2.5%、η_sys ≤2.1%（k=2） | 超目标先查标定与采样，不得直接下结论 |
| 其余 | 同 v0.1（通道完整性、η 范围、FM 范围、SIM 标记） | 不静默跳过 |

## 6. 测试与验证

| 模块 | 测试数 | 关键断言 |
| --- | --- | --- |
| `test_processing.py` | 12 | 公式、simulated 标记、空气密度优先级、缺通道/缺标定拒绝、覆盖保护、auto 跳过爬升、无稳态回退、last 元数据、U 值与公式一致 |
| `test_aggregate.py` | 8 | runs/grid 字段与统计、去重、坏 JSON、覆盖保护、MEASURED 标记、U/mode 传播 |
| `test_plot_efficiency_map.py` | 3 | 2×2 网格图、单点图 + 覆盖保护、非法 field |
| 合计 | **23** | `py -3.12 -m unittest discover -s code\processing -p "test_*.py"` → OK |

## 7. 已知限制与待办

- 不确定度表是**先验量级**：实机静态砝码标定完成后，用实测重复性/迟滞/零点漂移替换，并把 `reference_targets_k2` 变为验收项；
- 一阶传播忽略输入相关性（如 U 与 I 同源、ρ 与温度相关），后续可做 Monte Carlo 或 GUM 完整传播；
- auto 选窗只对 thrust_raw/rpm 判稳，未对电压电流判稳；电池电压缓慢下降时可能低估电功率漂移，v0.3 可加电压/电流通道；
- 尚未把 U 画进效率地图（误差棒/置信带），v0.3 与 `plot_efficiency_map.py` 一起改；
- `--window` 与 `--steady-window` 语义不同（前者仅 last 模式用），README 需示例说明。

## 8. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 初版：效率口径、标定 JSON、质量门槛、8 项测试 |
| 0.2 | 2026-11-19 | 增量：稳态自动识别（auto）、一阶不确定度传播（U(k=2)）、地图 runs/grid 增加 steady_mode 与 U 列、schema 0.2、测试 18→23 |
