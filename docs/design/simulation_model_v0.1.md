# 推进—螺旋桨—电调物理仿真模型 v0.1

| 项 | 内容 |
| --- | --- |
| 状态 | 草稿 v0.1（2026-11-19） |
| 代码 | `code/simulation/propulsion_model.py`、`code/simulation/simulate_campaign.py` |
| 测试 | `code/simulation/test_simulation.py`（9 项，`py -3.12 -m unittest discover -s code\simulation -p "test_*.py" -v`） |
| 数据性质 | **全部为合成数据（SIM）**；模型参数为文献量级 + 工程取值，不代表任何具体产品 |
| 上游文档 | `docs/design/processing_pipeline_v0.1.md`、`docs/design/efficiency_map_v0.1.md` |

## 1. 目的与边界

在实机数据缺失期，用一套**可解释、可复算**的准稳态模型：

1. 生成协议 v0.1 兼容的合成 raw CSV + meta（含 ADC 计数、噪声、稳态前斜坡），供采集/处理/地图软件全链路联调；
2. 给效率地图提供物理上自洽的先验（效率随电压/负载的定性趋势），避免"假装有数据"；
3. 为后续选型匹配原型（方向三）提供可替换的代理真值。

**边界（必须遵守）**：

- 合成数据只能作为"软件联调与建模验证"的输入，**不得作为实验结果**；
- 效率地图/对比表强制标注 `SIM`；标定文件 `calib_SIM_PHYS10x4.json` 标记 `simulated:true`，报告/论文不得引用其系数；
- 模型不包含电池内阻压降、动态响应、温升对磁链的影响、轴承摩擦细节、桨叶压缩性与雷诺数全谱修正；
- 定量精度只到"量级与趋势正确"，任何与实测的偏差都需后续实采数据校准。

## 2. 模型方程

### 2.1 输入

| 符号 | 含义 | 默认值（v0.1） |
| --- | --- | --- |
| D | 桨径 | 0.2544 m（10 英寸） |
| C_T0 / C_P0 | 参考转速下的推力/功率系数 | 0.110 / 0.0450 |
| K_V | 电机 KV | 400 r/min/V |
| R | 相电阻（线—线等效） | 0.08 Ω |
| I_0 | 空载电流 | 1.2 A |
| η_esc,base / k_esc | 电调基准效率 / 负载损失系数 | 0.985 / 0.015 |
| n_ref | 系数参考转速（雷诺修正基准） | 100 rev/s |
| a_T, a_P | 雷诺修正指数 | −0.02 / −0.035 |
| T_amb / p_amb | 环境温度 / 气压 | 24 ℃ / 96 kPa |

空气密度按理想气体：`ρ = p·1000/(287.05·(T+273.15))`。

### 2.2 准稳态求解（`solve_operating_point`）

对给定母线电压 V 与油门指令 t（0–1）：

1. 电调有效电压 `V_eff = t·V`；电调效率 `η_esc = η_esc,base − k_esc·t²`；
2. 桨系数随转速做幂律修正：`C_T = C_T0·(n/n_ref)^a_T`，`C_P = C_P0·(n/n_ref)^a_P`；
3. 推力 `T = C_T·ρ·n²·D⁴`；轴功率 `P_shaft = C_P·ρ·n³·D⁵`；轴扭矩 `Q = P_shaft/(2πn)`；
4. 电机电压平衡（K_t = 60/(2πK_V)，K_e = K_t）：`V_eff = I·R + K_e·2πn` ⇒ `I = (V_eff − K_e·2πn)/R`；
5. 转矩平衡：`K_t·I = Q + K_t·I_0`；
6. 由 (4)(5) 消去 I 得关于 n 的二次方程 `a·n² + b·n + c = 0`（a=(C_P/2π)ρD⁵、b=K_tK_e·2π/R、c=K_tI_0−K_tV_eff/R），取正根；用不动点迭代刷新 C_T/C_P 的转速依赖（≤60 次，tol 1e-10 rev/s）；
7. 输出：`rpm, omega_rad_s, current_a（电机侧）, thrust_n, torque_nm, p_shaft_w, p_elec_w（=V_eff·I/η_esc）, eta_em, fm, eta_sys, esc_eta, ct, cp, rho`；
8. 效率口径与 D012 完全一致：`η_em=P_shaft/P_elec`、`P_ideal=T^1.5/√(2ρA)`、`FM=P_ideal/P_shaft`、`η_sys=FM·η_em`。

典型工作点（自检量级，非产品数据）：22.2 V 满油门 ≈ 8600 r/min / 10.6 N / 0.175 N·m / 8.5 A（电机侧）/ η_em≈0.82 / η_sys≈0.53；29.6 V 满油门 ≈ 18.5 N / η_sys≈0.56。

### 2.3 合成数据生成（`simulate_run`）

- 采样：默认 1000 S/s × 2.5 s；前 0.2 s 从 80% 斜坡到 100%（处理流水线取末尾稳态窗口）；
- 通道映射：`thrust_raw = round(T / k_t)`、`torque_raw = round(Q / k_q)`（k_t=0.00035 N/count、k_q=5.882352941176471e-06 N·m/count，模拟 24 bit ADC 满量程假定）；
- `voltage_v` = 母线电压（σ=0.01 V）；`current_a` = **电池侧电流** = `P_elec/V_bus`（σ=0.02 A），使流水线 `P_elec=U·I` 闭合；
- `rpm` σ=3 r/min；温度 25+0.05·P_shaft ℃；环境 24 ℃ / 96 kPa / 45%RH；
- run_id：`20261119_SIM_<V>V_<油门>pct_R<k>`；meta 仿采集程序 schema（`mode:"simulate"`、`simulated:true`、`data_notice`、`simulation{model,seed,params,operating_point}`、`test{...}`）。

## 3. 一键仿真战役（`simulate_campaign.py`）

```powershell
# 默认 4 电压 × 4 油门 = 16 工况（SCR 图件与汇总表）
py -3.12 code\simulation\simulate_campaign.py

# 覆盖已有产物（默认拒绝覆盖，防误删）
py -3.12 code\simulation\simulate_campaign.py --force

# 自定义网格
py -3.12 code\simulation\simulate_campaign.py --voltages 11.1,22.2 --throttles 25,100 --repeats 2
```

产物：

| 路径 | 内容 |
| --- | --- |
| `data/raw/<run_id>.csv` / `.meta.json` | 合成 raw 数据与条件（16 组） |
| `data/processed/<run_id>_processed.csv` | 逐样本物理量（14 列） |
| `data/metadata/<run_id>_efficiency.json` | 稳态窗口汇总（SIM 标记） |
| `data/metadata/calib_SIM_PHYS10x4.json` | 仿真"隐藏真值"标定（simulated:true） |
| `data/processed/efficiency_map_runs.csv` / `_grid.csv` | 16 行汇总与 4×4 网格 |
| `data/processed/figures/efficiency_map_v0.1.png` | η_sys 效率地图（SIM 红字） |
| `data/processed/simulation_campaign_summary.csv` | 模型 vs 流水线逐工况对比 |

## 4. 闭环验证结果（2026-11-19，16 工况）

`model` 为物理模型工作点，`pipe` 为合成 raw → 标定 → 流水线 → 稳态窗口的复原值：

| 指标 | 最大相对误差 |
| --- | --- |
| 推力 T | 0.28%（11.1 V / 25%，低推力噪声主导） |
| 转速 | <0.01% |
| η_sys | 1.59%（同上低功率角）；其余 15 工况 <0.4% |

这验证了"标定换算 + 效率链 + 稳态窗口"在软件层面自洽；**不验证**任何实机精度。

效率地图的定性规律（与文献一致的方向性）：同电压下 η_sys 随油门升高而升高；同推力下电压越高 η_sys 越高（电流更小、铜耗更低）；低电压/低油门角接近空载，效率趋近 0（模型不含空载损耗精化）。

## 5. 已知限制与 v0.2 待办

1. 电池内阻压降/满电—空电压差未建模（可加 `battery{r_internal, soc}`）；
2. 温升对 R、磁链的影响未建模；目前仅记录温度通道；
3. 雷诺修正仅幂律近似，未用 UIUC 等公开桨数据校核（方向二）；
4. 动态过程（加减速、阶跃响应）未建模，只做准稳态；
5. 模型 vs 流水线对比只覆盖合成标定的理想情形，未注入失配标定/未标定通道的鲁棒性用例；
6. 与 `work/prestudy/` 口径未逐项对照（出图形状/效率定义）。

## 6. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 初版：准稳态推进—螺旋桨—电调模型、合成数据生成、16 工况战役、闭环验证 |
