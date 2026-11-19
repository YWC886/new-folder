# 仿真模型 v0.4：电机双节点热网络（绕组 + 定子/机壳）

- 状态：v0.4 草稿（2026-11-19）
- 负责人：D
- 代码：`code/simulation/two_node_thermal.py`、`code/simulation/test_two_node_thermal.py`
- 上游：`simulation_model_v0.3.md`（单节点热瞬态）
- 数据性质：**SIM**（物理模型合成，参数为文献量级 + 工程假设，非实测）

## 1. 目的与边界

v0.3 用单一集总热容描述整机温升，无法区分"绕组先热、机壳后热"的短时行为，也无法给出
停机冷却曲线的形状。v0.4 把电机分为 **绕组节点** 与 **定子/机壳节点**，用于：

1. 观察短时过载（数十秒~数分钟）时绕组峰值温度相对单节点模型的高估/低估；
2. 给出加热—冷却两阶段温度曲线，为后续实测温升试验与热保护阈值提供方法框架；
3. 保持与 v0.3 相同的**稳态**结果（总热阻/总热容一致），便于做版本间对照。

**边界**：参数未经过实测辨识；只能看趋势、量级和方法的正确性，不能作为具体电机的热设计
结论或安全依据。

## 2. 模型

两个节点：绕组温度 `T_w`、定子/机壳温度 `T_s`；环境 `T_amb = 24 °C`。

```
C_w · dT_w/dt = k_loss · P_loss − (T_w − T_s) / R_ws
C_s · dT_s/dt = (T_w − T_s) / R_ws − (T_s − T_amb) / R_sa
```

- 热源：电机铜损的一部分 `k_loss · P_loss`（`k_loss=0.7`，与 v0.2 一致），其余视为铁损/杂散；
- 绕组温度 `T_w` 用于铜阻温度修正：`R_hot = R_20 · (1 + α_Cu · (T_w − 20))`；
- 每个时间步先用当前 `R_hot` 解电池压降与工作点（复用 v0.3 的 `_solve_with_sag`），
  再对两个节点做显式欧拉更新（`dt = 0.5 s`）；
- 与 v0.3 的等价关系：`R_ws + R_sa = 2.5 K/W`、`C_w + C_s = 45 J/K`（总热阻/总热容一致，
  稳态时两节点均等于单节点解；瞬态分配不同）。

### 参数表（工程假设，待实测辨识）

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `C_w` 绕组热容 | 15 J/K | 铜线 + 浸漆集中热容 |
| `C_s` 定子/机壳热容 | 30 J/K | 铁芯 + 机壳 |
| `R_ws` 绕组→定子热阻 | 0.7 K/W | 槽绝缘 + 端部导热 |
| `R_sa` 定子→环境热阻 | 1.8 K/W | 自然对流 + 辐射等效 |
| 总热阻 / 总热容 | 2.5 K/W / 45 J/K | 与 v0.3 一致 |
| `T_amb` / `p` | 24 °C / 96 kPa | 与 v0.2/v0.3 一致 |

## 3. 接口

```python
@dataclass(frozen=True)
class TwoNodeParams:
    winding_capacitance_j_per_k: float = 15.0
    stator_capacitance_j_per_k: float = 30.0
    winding_to_stator_r_k_per_w: float = 0.7
    stator_to_ambient_r_k_per_w: float = 1.8
    ambient_temp_c: float = 24.0
    pressure_kpa: float = 96.0
    # properties: total_capacitance_j_per_k, total_resistance_k_per_w

def duty_profile(ramp_s: float, throttle: float, heat_s: float): ...   # t -> 油门，heat_s 后为 0
def simulate_two_node(model=None, pack=None, *, voltage_v, throttle_fn,
                      duration_s=600.0, dt_s=0.5, thermal=None, density=None, ...) -> list[dict]
def single_node_reference(rows, *, model=None, pack=None, voltage_v, throttle_fn, dt_s,
                          thermal, density=None) -> list[float]
def write_csv(rows, path) -> Path
def plot_two_node(rows, output_png, *, single_node=None, overwrite=False) -> Path
def main(argv=None) -> int
```

CLI：

```powershell
# 加热 300 s + 冷却 300 s（22.2 V 满油门，5 s 斜坡）
py -3.12 code\simulation\two_node_thermal.py --overwrite
# 自定义参数（热容/热阻/时长）
py -3.12 code\simulation\two_node_thermal.py --heat-s 120 --cool-s 180 --c-winding 12 --c-stator 28 --overwrite
```

产物：`data/processed/two_node_thermal_v0.4.csv`（19 列）、
`data/processed/figures/two_node_thermal_v0.4.png`（三面板：双节点温度 + 单节点参考 / η_sys / 油门）。

## 4. 演示结果（22.2 V 满油门，加热 300 s → 冷却 300 s，SIM）

| 指标 | 双节点 | 单节点 v0.3 | 说明 |
| --- | --- | --- | --- |
| 加热段峰值（绕组） | **82.93 °C** | 80.07 °C | 单节点低估约 2.9 K（300 s 时） |
| 加热段峰值（定子/机壳） | 66.17 °C | — | 机壳显著滞后 |
| 绕组达 70 °C 时刻 | 116.5 s | — | 短时过载的关键量 |
| 截止时 η_sys | 0.5237 | 0.5237 | 稳态口径一致（D012） |
| 冷却至 35 °C 时刻 | 432 s（停机后 132 s） | — | 冷却曲线形状为双节点独有 |
| 600 s 末温 | 25.51 / 25.32 °C | — | 双节点均向环境回落 |

规律：

1. 加热初期热量集中在绕组，`T_w > T_s`，单节点模型低估绕组峰值；持续时间越长，差距越小
   （总热阻一致，稳态必然相同）；
2. 停机后机壳储热使绕组冷却先慢后快，冷却曲线不是单时间常数；
3. 短时过载（<1 min）的绕组温度由 `C_w` 与 `R_ws` 主导，热保护设计应优先关注这两个参数。

## 5. 数据规则

1. 本模块产物全部 `SIM`，CSV 每行 `data_notice` 含"物理仿真合成数据"与"不是实验结果"；
2. 图件强制红字 `SIMULATED DATA — NOT EXPERIMENTAL`；
3. 不得用本模型参数（`C_w`/`C_s`/`R_ws`/`R_sa`）冒充具体产品热参数；实测温升试验后才能替换
   （见 D029）。

## 6. 验收与测试

- `code/simulation/test_two_node_thermal.py` 8 项：稳态与单节点一致（绕组 ±0.5 K、定子按
  `R_sa` 分配）、加热期绕组高于定子、冷却段单调回落至近环境、稳态能量守恒
  （`q_ws ≈ q_sa ≈ heat`，2%）、非法参数、CSV/PNG 字段与覆盖保护、`duty_profile` 边界、
  CLI 端到端（成功 0 / 已存在 2 / `--overwrite` 0）。
- 仿真模块合计 29 项测试（21+8）；全仓 178 项（截至 2026-11-19 bootstrap 不确定度 v0.1 后）。

## 7. 限制与 v0.5 待办

- 参数未辨识：`C_w/C_s/R_ws/R_sa` 为工程假设，需温升阶跃/冷却试验辨识（建议双人、K 型热电偶 +
  数据记录仪，记录绕组与机壳两点温度）；
- 无强制风冷/转速依赖的对流系数（自然对流常数）；无辐射模型；
- 仅两节点，无法区分端部绕组/磁钢温度；
- 显式欧拉 `dt=0.5 s` 未做步长收敛性扫描（后续可做 `dt` 减半对照）；
- v0.5 方向：把热模型与效率地图联动（温度对 η 的修正）、加入热保护时间常数建议、
  用实测温升曲线做参数辨识（最小二乘）。

## 8. 变更记录

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 双节点热网络 + 冷却曲线 + 单节点对照；8 项测试；SIM 演示 22.2 V 满油门 |
