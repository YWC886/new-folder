# 仿真模型 v0.2：电池内阻压降 + 电机温升（SIM）

- 版本：v0.2 草稿（2026-11-19）
- 负责人：D（建模）
- 状态：代码与测试通过；纯仿真，不是实验结果
- 上游：`docs/design/simulation_model_v0.1.md`
- 代码：`code/simulation/propulsion_model.py`（新增 `PackModel`）、`code/simulation/sensitivity_pack_model.py`
- 测试：`code/simulation/test_simulation.py`
- 数据产物：`data/processed/pack_model_sensitivity_v0.2.csv`、`data/processed/figures/pack_model_impact_v0.2.png`

## 1. 目的与边界

v0.1 把 `voltage_v` 直接当作恒定母线电压，隐含"电池无内阻、电机不发热"的假设。
v0.2 在同一物理模型上加入两条工程上不可忽略的反馈：

1. **电池包内阻压降**：带载后母线电压低于开路电压；
2. **电机温升**：损耗使绕组温度升高，铜电阻随之增大（铜温漂），又反过来改变工作点。

**边界（必须保留）**：参数是文献量级 + 工程取值，不是任何具体电芯/电机的实测数据；
本模型只用于软件联调、敏感性分析与先验假设，**不得作为实验结果或论文结论**。
真实标定须用静态砝码 + 双人记录替换 `calib_*`，并用实机温升/内阻测量替换本文件参数。

## 2. 模型增量

### 2.1 电池包

- 名义电压视为 **开路电压** `V_oc`（即 `solve_operating_point` 的 `voltage_v` 输入）；
- 串联节数 `cells = round(V_oc / 3.7)`（11.1 V=3S、14.8 V=4S、22.2 V=6S、29.6 V=8S）；
- 包内阻 `R_pack = cells × R_cell`，默认 `R_cell = 0.008 Ω`；
- 电流关系：`I_batt = P_elec / V_bus`，母线电压满足 `V_bus = V_oc − I_batt·R_pack`。

### 2.2 电机温升与铜温漂

- 损耗：`P_loss = P_elec − P_shaft`；
- 一阶稳态温升（无热容/时间常数）：`T_motor = T_amb + R_th·k_loss·P_loss`，
  默认 `R_th = 2.5 K/W`、`k_loss = 0.7`（部分损耗由电调/铁耗承担，不计入绕组）；
- 铜电阻温漂：`R_hot = R_20·(1 + α_Cu·(T_motor − 20))`，`α_Cu = 0.00393 /K`。

### 2.3 联立求解

`V_bus`、`T_motor`、`R_hot` 三者互相依赖，采用不动点迭代（最多 `max_iter`，默认 60 次）：

```text
初值：V_bus = V_oc, R = R_20, T = T_amb
循环：
  1. 用 (V_bus, R, throttle) 解 v0.1 稳态工作点 → P_elec, P_shaft；
  2. V_bus' = V_oc − (P_elec / V_bus)·R_pack；
  3. T' = T_amb + R_th·k_loss·(P_elec − P_shaft)，R' = R_20·(1+α·(T'−20))；
  4. 三者变化小于容差 → 收敛；否则继续。
```

收敛判据：`|ΔV_bus| < 1e-9 V`、`|ΔT| < 1e-6 K`、`|ΔR| < 1e-12 Ω`；不收敛抛 `ValueError`。

API：

```python
from propulsion_model import ModelParams, PackModel, solve_operating_point

point = solve_operating_point(ModelParams(), 22.2, 1.0, pack=PackModel(cells=6))
# point 在 v0.1 字段之外新增：
#   open_circuit_voltage_v, pack_resistance_ohm, bus_voltage_v,
#   battery_current_a, voltage_sag_v, motor_temp_c,
#   winding_resistance_ohm, p_loss_w
```

`pack=None`（默认）保持 v0.1 行为完全不变，既有流水线与测试无需改动。

## 3. 敏感性结果（16 工况，SIM）

同一物理模型、同一参数，仅对比"理想母线 vs 电池包"：

| 指标 | 结果 |
|---|---|
| η_sys 最大绝对降幅 | 约 1.17 个百分点（29.6 V / 100%，0.5610 → 0.5493） |
| η_sys 最大相对降幅 | 约 2.09% |
| 最大母线压降 | 约 0.84 V（29.6 V / 100%，V_bus ≈ 28.76 V） |
| 最高电机温度 | 约 125 °C（29.6 V / 100%，工程上应加散热/降载） |
| 小油门影响 | 25% 油门时压降与温升都很小（<0.1 个百分点） |

规律：
1. 负载越大，压降、温升、铜损越显著，η_sys 降幅随油门单调增大；
2. 高电压（8S）大油门时压降与温升同时最大，是 v0.1 地图最乐观的角落；
3. 低电压小油门时两种模型几乎重合，说明 v0.1 在轻载区的偏差可忽略。

图件：`data/processed/figures/pack_model_impact_v0.2.png`（左：η_sys 理想/实际对比；右：Δη_sys）。

## 4. 复现

```powershell
py -3.12 code\simulation\sensitivity_pack_model.py --overwrite
py -3.12 -m unittest discover -s code\simulation -p "test_*.py" -v
py -3.12 code\simulation\propulsion_model.py --voltage 22.2 --throttle 1.0 --pack-cells 6
```

## 5. 验收与限制

验收：
- `PackModelTests` 6 项通过（压降、单调性、效率不优于理想、禁用时兼容 v0.1、非法输入、敏感性矩阵/CSV/PNG/覆盖保护）；
- 敏感性 CSV 16 行、PNG 可读；
- `pack=None` 时既有 15 项仿真测试全绿（v0.1 行为不变）。

限制 / v0.3 待办：
1. 无热容/热时间常数，只给稳态温度；动态温升需一阶热模型；
2. 内阻随 SOC/温度变化未建模（当前为常数）；
3. 未建电池放电曲线与低压截止；
4. 电调损耗分配（`k_loss`）为假设值，需实测校准；
5. 敏感性只覆盖 4 电压 × 4 油门单次；未做参数不确定度传播（与流水线 `uncertainty` 块联动是 v0.3 方向）。

## 6. 变更记录

- 0.1（2026-11-19）：初版，v0.2 电池+温升模型、敏感性脚本、15→21 项测试。
