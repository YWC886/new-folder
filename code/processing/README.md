# code/processing · 效率计算流水线 v0.8（含标定拟合 v0.1、MEASURED 门禁 v0.1、联动守门 v0.5、试验排程 v0.2）

把台架原始 CSV 换算为物理量，并计算「电机+电调效率 / 螺旋桨品质因数 / 系统效率」三件套；支持稳态窗口自动识别、一阶不确定度传播、效率地图汇总/成图与 GP 平滑代理；另有 M0.4 门禁 `measured_readiness.py`（v0.1）检查输入是否具备实测资格。**当前只用模拟数据验证过，尚无实机数据。**

## 文件

| 文件 | 用途 |
| --- | --- |
| `compute_efficiency.py` | 原始 CSV + 标定 JSON → 逐样本物理量 CSV + 稳态窗口汇总 JSON（含 `uncertainty`） |
| `aggregate_efficiency.py` | 多份 `efficiency.json` → 效率地图 `runs.csv`（每次运行一行，含 U 与选窗方式）+ `grid.csv`（分组均值±标准差与 U 最大值） |
| `plot_efficiency_map.py` | `runs.csv` → 效率地图 PNG（散点/热力图；`--uncertainty` 画 U(k=2) 误差棒/格内标注；SIM 强制标注） |
| `gp_surface.py` | `runs.csv` → RBF 核 GP 平滑代理：LOOCV 选核宽、21×21 网格预测 η_sys 均值/标准差 CSV + 双面板图（v0.4） |
| `calibration_fit.py` | 静态砝码读数长表 CSV → `simulated:false` 标定 JSON（k/b + R²/重复性/迟滞指标 + warnings；仅真实读数，v0.1） |
| `measured_readiness.py` | MEASURED 通路就绪门禁（v0.1）：检查 meta/标定/表头/必需通道/桨径；SIM 输入拒绝，退出码 0/1/2（D035） |
| `test_processing.py` | 12 项回归测试（公式、空气密度、标记、缺通道/缺标定、禁止覆盖、稳态 auto/回退、U 公式） |
| `test_aggregate.py` | 8 项测试（展平、分组统计、去重、坏文件、覆盖保护、来源标记、U/mode 传播） |
| `test_plot_efficiency_map.py` | 6 项测试（网格图、单点图、非法字段、`--uncertainty` 误差棒/格内标注、U 缺失容错） |
| `test_gp_surface.py` | 12 项测试（读取兼容、LOOCV、核宽搜索、网格输出、CSV/PNG、覆盖保护、错误输入） |
| `test_calibration_fit.py` | 15 项测试（读数解析、精确 k/b 复原、重复性/迟滞、R² 告警、覆盖保护、CLI 端到端并读回标定） |
| `test_measured_readiness.py` | 10 项测试（SIM 拒绝、有效样本就绪、缺 meta/通道/桨径、标定标记、CLI 退出码与 JSON 输出） |
| `design_matrix.py` | 多工况试验排程（v0.2）：`full`/`sweep` 计划 + `--thrust-levels` 目标推力反解（GP 代理二分反查油门，不可达跳过）+ `--randomize` 顺序随机化（D043/D045） |
| `test_design_matrix.py` | 19 项测试（全因子/阶梯行数与唯一 run_id、排序、确定性、汇总、非法输入、CSV/JSON 覆盖保护、CLI；推力反解精确性/越界拒绝/随机化可复现/THRUST_FIELDS） |
| `test_require_measured.py` | 5 项测试（`--require-measured`：SIM/合成拒绝、有效样本通过、默认关闭、CLI 参数接线） |
| `../README.md`（本文件） | 用法、公式、数据诚信约定 |

## 快速运行

```powershell
# 模块测试（98 项测试：流水线 12 + 汇总 12 + 绘图 6 + GP 12 + 标定拟合 15 + MEASURED 门禁 10 + 联动守门 5 + 试验排程 19）
py -3.12 -m unittest discover -s code\processing -p "test_*.py" -v

# 用模拟数据 + 合成标定跑通流水线（自动识别稳态窗口，输出带 simulated 标记）
py -3.12 code\processing\compute_efficiency.py `
  --input data\raw\20261119_SIM_22.2V_50pct_R1.csv `
  --calib data\metadata\calib_SIM_PHYS10x4.json `
  --window 1.5 --steady auto --steady-window 0.5 --steady-threshold 0.01

# 也可固定末尾窗口（v0.1 行为）
py -3.12 code\processing\compute_efficiency.py `
  --input data\raw\20261117_SIM_22V2_50pct_R1.csv `
  --calib data\metadata\calib_SIM_DEMO.json --window 3 --steady last

# 汇总为效率地图数据（扫描 data\metadata\*_efficiency.json）
py -3.12 code\processing\aggregate_efficiency.py --dir data\metadata --overwrite

# 绘制效率地图（v0.3 可加 --uncertainty）
py -3.12 code\processing\plot_efficiency_map.py --uncertainty --overwrite

# v0.1 静态砝码标定拟合（仅真实读数；输出 simulated:false 标定 JSON，含质量指标）
py -3.12 code\processing\calibration_fit.py `
  --input data\calibration\静态砝码读数.csv `
  --output data\calibration\calib_MEASURED.json --diameter 0.4572

# MEASURED 通路门禁（M0.4；0=就绪，1=未就绪，SIM 输入会被拒绝）
py -3.12 code\processing\measured_readiness.py `
  --input data\raw\<run_id>.csv --calib data\metadata\calib_MEASURED.json

# 联动守门：在效率计算入口同样拒绝 SIM/合成输入（默认关闭，实测运行显式开启）
py -3.12 code\processing\compute_efficiency.py `
  --input data\raw\<run_id>.csv --calib data\metadata\calib_MEASURED.json `
  --window 1.5 --steady auto --require-measured

# 汇总守门：效率地图汇总同样只接受实测来源（含 SIM 时 exit 2）
py -3.12 code\processing\aggregate_efficiency.py --dir data\metadata --require-measured

# GP 平滑代理（LOOCV 自动选核宽；输出网格 CSV + 双面板图）
py -3.12 code\processing\gp_surface.py --overwrite
```

输出：

- `data/processed/<run_id>_processed.csv`：14 列逐样本物理量（`thrust_N, torque_Nm, rpm, omega_rad_s, p_shaft_w, p_elec_w, eta_em, fm, eta_sys` 等）；
- `data/metadata/<run_id>_efficiency.json`：稳态窗口均值/标准差、选窗方式与识别结果（`window.mode/detection`）、空气密度来源、标定系数、`simulated` 标记、`uncertainty` 块与警告；
- `data/processed/efficiency_map_runs.csv`：每次运行一行（含 `source=SIM/MEASURED`、工况、效率均值、`steady_mode`、U(k=2)）；
- `data/processed/efficiency_map_grid.csv`：按（source, 组合, 电压, 油门）分组的均值±标准差 + U 最大值；
- `data/processed/figures/efficiency_map_v0.1.png` / `_v0.3.png`：散点（<4 点）或热力图（≥2×2 网格），SIM 数据带红字标注；
- `data/processed/efficiency_map_surface_v0.4.csv`：GP 网格预测（`voltage_set_v, throttle_set_pct, eta_pred, eta_std, data_note`，默认 21×21=441 行）；
- `data/processed/figures/efficiency_map_v0.4.png`：GP 均值热力图 + 预测标准差（1σ）双面板。

## 稳态窗口（v0.2）

- `--steady last`（默认）：取最后 `--window` 秒；适合已知稳定段足够长的场景。
- `--steady auto`：从末尾向前滑动（步长 = 窗口采样数/10，最多 50 点），取首个 `thrust_raw` 与 `rpm` 相对标准差均 ≤ `--steady-threshold`（默认 1%）的窗口；找不到则回退末尾 `--window` 窗口并在 `warnings` 中提示。
- 汇总 JSON 的 `window.mode` 记录选窗方式，`window.detection` 记录 `applied / threshold / start_s / end_s / relative_std` 等，便于复查。

## 不确定度（v0.2，一阶相对传播）

1σ 相对量级：u_T=0.65%、u_Q=0.50%、u_rpm=0.10%、u_V=0.10%、u_I=0.50%、u_ρ=0.50%（来源 `work/research/bench_tech.md` 量级，**实机标定后必须复核**）。

```text
u(η_em)  = sqrt(u_Q² + u_rpm² + u_V² + u_I²)                    → U(k=2) ≈ 1.44%
u(FM)    = sqrt((1.5u_T)² + u_Q² + u_rpm² + (0.5u_ρ)²)          → U(k=2) ≈ 2.26%
u(η_sys) = sqrt((1.5u_T)² + (0.5u_ρ)² + u_V² + u_I²)            → U(k=2) ≈ 2.26%
```

`uncertainty` 块含 `components_1sigma_relative`、`sensitivities`、`U_rel_*_k2`、`reference_targets_k2`（η_em 1.5%、FM 2.5%、η_sys 2.1%）与 `note`。一阶传播忽略输入相关性，属于先验估计，不是实测标定结果。

## GP 平滑代理（v0.4）

- 特征：`x = (V/30, throttle/100)`；核：`k = σ_f²·exp(-||x-x'||²/(2ℓ²)) + σ_n²·δ`（σ_f²=1、σ_n²=1e-5）；
- 核宽 ℓ 在 0.05–1.00（步长 0.05）上按 **LOOCV RMSE** 选最小；
- 输出网格 `eta_pred`（GP 均值）与 `eta_std`（预测标准差，1σ；边缘/外推处更大）；
- **预测标准差 ≠ 测量不确定度 U(k=2)**：前者反映代理模型对数据的拟合置信，后者需要标定数据；两者在文档中分开表述；
- SIM 数据输入时终端与图件均标注非实验；外推区不得用于选型结论。

## MEASURED 通路门禁（v0.1，M0.4）

- 目的：只有"声称实测"的输入（meta `simulated:false`、`mode:"serial"`、标定 `simulated:false`、表头与必需通道齐全、桨径可用）才允许进入 MEASURED 通路；SIM/REFERENCE 输入应被拒绝。
- 检查器只验证标记与结构，**不修改输入**；数据物理真实性依赖双人签字与现场记录（D032/D035）。
- 退出码：`0` 就绪、`1` 未就绪（列出错误）、`2` 用法/读取异常；`--json/--output` 输出机器可读报告。
- 2026-11-19 SIM 拒绝演练：`data\raw\20261117_SIM_22V2_50pct_R1.csv` + `calib_SIM_DEMO.json` → 3 条错误、exit 1，门禁生效。
- 联动守门（v0.5）：`compute_efficiency --require-measured` 在解析后调用同一组检查（`assert_measured`），SIM/合成/非 serial 输入直接 `ValueError`（CLI exit 1），默认关闭以保持 SIM 演示兼容（D036）。
- 汇总守门（v0.6，2026-11-19）：`aggregate_efficiency --require-measured` 仅接受 `source=MEASURED` 且 `mode=serial` 的汇总行（`assert_measured`），混杂 SIM 时直接拒绝（CLI exit 2，D037）；`--dir data\metadata` 演练拒绝 17 个 SIM run。

## 公式（与 docs/design/processing_pipeline_v0.1/0.2 一致）

```text
T = k_t·thrust_raw + b_t                       [N]
Q = k_q·torque_raw + b_q                       [N·m]
ω = 2π·rpm/60                                  [rad/s]
P_shaft = Q·ω                                  [W]
P_elec  = U·I                                  [W]
η_em  = P_shaft / P_elec                       （电机 + 电调）
P_ideal = T^1.5 / sqrt(2ρA)                    （动量理论，静态悬停）
FM = P_ideal / P_shaft                         （螺旋桨品质因数）
η_sys = P_ideal / P_elec = FM·η_em             （系统效率）
```

空气密度优先级：`--rho` > 标定 JSON 的 `air_density_kg_m3` > 实测环境温压（`ρ = p/(R·T)`，R=287.05）> 默认 1.204 kg/m³。桨盘面积 `A = πD²/4`，桨径来自标定 JSON、meta.json 或 `--diameter`。

## 数据诚信（硬约束）

1. 标定 JSON 或 `meta.json` 标记 `simulated: true` → 汇总 JSON 的 `simulated` 为 true，终端打印「⚠ 模拟数据：不是实验结果」；
2. **`calib_SIM_DEMO.json` 的系数是任意构造的**，只能用于流程联调；真实标定必须来自双人静态砝码试验（`docs/test/静态砝码读数记录_v0.1.md`）；
3. 未标记模拟的数据仍会提示「需确认静态标定」；效率结论必须等实机标定后才可写入报告；
4. 输出文件默认不覆盖（防误删证据）；需要覆盖显式加 `--overwrite`；
5. 效率地图的 `runs.csv`/`grid.csv` 必须保留 `source` 列（`SIM`/`MEASURED`），图中 SIM 数据强制显示「SIMULATED DATA — NOT EXPERIMENTAL」；严禁把 SIM 行当实测结果引用；
6. 不确定度表是**先验量级**，不得当作已标定的实测 U；实机标定后须用重复性/迟滞/零点数据替换并复核；
7. GP 预测标准差只表示代理模型置信，不得写成测量不确定度。

## 已知限制 / 下一步

- GP 只有 16 个 SIM 点（4 电压×4 油门）；外推区（电压/油门超出数据范围）仅作趋势参考，不保证物理合理；
- 一阶传播忽略输入相关性，后续可做 Monte Carlo / GUM 完整传播；
- auto 判稳只用 `thrust_raw`/`rpm` 两通道，未含电压/电流；电池缓慢掉压时可能低估电功率漂移；
- 下一步：GP 结果并入选型匹配（软件代理 + 保守效率）、与 `work/prestudy` 口径统一；实机多工况数据到位后重跑 aggregate + plot + gp_surface 即得到正式效率地图。

## 试验排程（design_matrix v0.1）

把 S2 阶段「电压 × 油门 × 桨型 × 重复」展开为可执行采集排程（不是测量数据；D043）。

```powershell
py -3.12 code\processing\design_matrix.py --voltages 11.1,14.8,22.2 --throttles 20,40,60,80,100 --props A,B,C --repeats 3 --design full --output data\processed\design_matrix_v0.1.csv --summary data\metadata\design_matrix_v0.1.summary.json --overwrite
```

设计类型：`full`（全因子，N=|V|×|T|×|P|×R）与 `sweep`（阶梯升/降，行数翻倍）。默认基线 135 次运行（约 11.25 min 采集）。
设计文档：`docs/design/design_matrix_v0.1.md`。
