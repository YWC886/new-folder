# 仿真模型 v0.3：电机一阶热瞬态（SIM）

- 版本：v0.3 草稿（2026-11-19）
- 负责人：D（建模）
- 状态：代码与测试通过；纯仿真，不是实验结果
- 上游：`docs/design/simulation_model_v0.2.md`
- 代码：`code/simulation/transient_thermal.py`
- 测试：`code/simulation/test_transient_thermal.py`（6 项）
- 数据产物：`data/processed/transient_thermal_v0.3.csv`、`data/processed/figures/transient_thermal_v0.3.png`

## 1. 目的与边界

v0.2 只给**稳态**电机温度（`T = T_amb + R_th·k_loss·P_loss`），无法回答：
"从冷态起转后多久到某温度"、"短时大油门是否安全"、"温度随时间如何影响效率"。
v0.3 在 v0.2 基础上加入热容，得到**一阶热瞬态**：

```text
C_th · dT/dt = k_loss · P_loss(t) − (T − T_amb) / R_th
```

每个时间步：用当前 `T` 算铜阻 `R_hot` → 解电池压降与固定电压工作点 → 算损耗 → 欧拉更新 `T`。

**边界**：参数仍为文献量级 + 工程假设（`C_th = 45 J/K`、`R_th = 2.5 K/W`、`k_loss = 0.7`）；
只用于软件联调、热趋势与安全边界先验，**不得作为实验结果或论文结论**。

## 2. 模型与实现

| 项 | 说明 |
| --- | --- |
| 状态变量 | 绕组/电机温度 `T`（单节点集总热容） |
| 热输入 | `k_loss·P_loss`，`P_loss = P_elec − P_shaft` |
| 散热 | `(T − T_amb)/R_th` |
| 温度反馈 | `R_hot = R_20·(1 + α_Cu·(T − 20))` 进入电磁方程 |
| 电池 | 代数压降 `V_bus = V_oc − I_batt·R_pack`（内层不动点迭代 ≤40 次，容差 1e-9 V） |
| 时间积分 | 显式欧拉，`dt` 默认 0.5 s；`T` 不低于环境温度 |
| 时间常数 | `τ = R_th·C_th`，默认 2.5×45 = 112.5 s |

API：

```python
import propulsion_model as pm
import transient_thermal as tt

rows = tt.simulate_transient(
    pm.ModelParams(), pm.PackModel(cells=6),
    voltage_v=22.2, throttle_fn=tt.ramp_profile(5.0, 1.0),
    duration_s=300.0, dt_s=0.5,
    thermal=tt.ThermalParams(thermal_capacitance_j_per_k=45.0),
)
# 每行字段见 tt.FIELDS：t_s, throttle, rpm, thrust_n, ..., motor_temp_c,
# winding_resistance_ohm, p_loss_w, heat_w, data_notice
```

CLI：

```powershell
py -3.12 code\simulation\transient_thermal.py --overwrite
py -3.12 code\simulation\transient_thermal.py --voltage 29.6 --throttle 1.0 --duration 600 --overwrite
```

## 3. 演示结果（SIM，22.2 V / 6S，5 s 斜坡到 100%，300 s）

| 量 | 结果 |
| --- | --- |
| 初温 → 末温 | 24 °C → 80.1 °C（峰值 80.1 °C；900 s 长跑收敛到 v0.2 稳态 84.7 °C 附近） |
| 时间常数 | 112.5 s；约 2.7τ 时完成约 93% 温升 |
| η_sys | 稳态后约 0.524，随温升仅有小幅变化（该模型中温升对 η 的一阶影响很小） |
| 母线/电流 | 21.80 V / 8.30 A（末态） |

规律：热时间常数远大于电/机械时间常数，短工况（<30 s）几乎不受温升影响；
持续大油门 >2τ 后温升显著，8S 满油门长跑会超过 120 °C（见 v0.2 敏感性表），需散热或降载。

## 4. 复现与验收

```powershell
py -3.12 code\simulation\transient_thermal.py --overwrite
py -3.12 -m unittest discover -s code\simulation -p "test_*.py" -v   # 21 项
```

验收：
- 长时间恒油门收敛到 v0.2 稳态温度（±1 K）；
- 加热阶段温度单调不减；
- 温升 63.2% 的时刻落在 `τ` 的 0.7–1.4 倍内；
- 非法输入抛 `ValueError`；CSV 字段 = `FIELDS`；PNG > 10 KB；默认拒绝覆盖；
- 每行 `data_notice` 保留 SIM 声明。

## 5. 限制 / v0.4 待办

1. 单节点集总热容：未区分绕组/铁芯/机壳，`C_th` 需实测辨识；
2. 散热只与温差有关（未含转速强制对流/环境风速）；
3. `k_loss` 仍为固定分配比例，需实测电调/电机损耗分配；
4. 电池仍为常数内阻 + 开路电压，未含 SOC 下降与放电曲线；
5. 未模拟停机后的冷却曲线（把 `throttle_fn` 设 0 可粗测，但无风冷项）；
6. 未做参数不确定度传播（与 `uncertainty` 块联动）。

## 6. 变更记录

- 0.1（2026-11-19）：初版一阶热瞬态模型、CLI/CSV/PNG、6 项测试、22.2 V 演示结果。
