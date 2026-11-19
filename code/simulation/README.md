# code/simulation —— 物理仿真与仿真战役（SIM）

> **数据诚信**：本目录产物全部为物理模型合成的 **SIM** 数据，参数为文献量级 + 工程取值，
> 不是实测、不代表具体产品。只能用于软件联调/建模方法验证；报告与论文不得引用为实验结果。

## 文件

| 文件 | 说明 |
| --- | --- |
| `propulsion_model.py` | 准稳态推进—螺旋桨—电调模型：`ModelParams` + `solve_operating_point`；v0.2 新增可选 `PackModel`（电池内阻压降 + 温升/铜温漂反馈，`pack=None` 保持 v0.1 行为） |
| `simulate_campaign.py` | 一键战役：模型 → 合成 raw CSV/meta → 效率流水线 → runs/grid 汇总 → 效率地图 → 模型对比表 |
| `sensitivity_pack_model.py` | v0.2 敏感性分析：16 工况下"理想母线 vs 电池包"的 η_sys 降幅、压降、温升，输出 CSV + 对比图 |
| `transient_thermal.py` | v0.3 一阶热瞬态：热容 `C_th` + 温升/铜阻反馈的 T(t)、η_sys(t) 时间序列，输出 CSV + 三面板图 |
| `two_node_thermal.py` | v0.4 双节点热网络（绕组 + 定子/机壳）：加热—冷却曲线、绕组温度用于铜阻修正；总热阻/热容与 v0.3 一致，附单节点对照 |
| `test_simulation.py` | 15 项测试：工作点量级、单调性、转矩平衡、转速上界、非法输入、战役闭环、覆盖保护、标定一致性、电池压降/温升/包模型兼容性 |
| `test_transient_thermal.py` | 6 项测试：稳态收敛、加热单调性、时间常数量级、非法输入、CSV/PNG 输出与覆盖保护、SIM 声明 |
| `test_two_node_thermal.py` | 8 项测试：稳态与单节点一致（总热阻/热容等价）、加热期绕组高于定子、冷却段单调回落、稳态能量守恒、非法参数、CSV/PNG 覆盖保护、CLI 端到端 |

## 用法

```powershell
# 单工作点（打印物理量）
py -3.12 code\simulation\propulsion_model.py --voltage 22.2 --throttle 0.5

# v0.2：启用 6S 电池包 + 温升模型
py -3.12 code\simulation\propulsion_model.py --voltage 22.2 --throttle 1.0 --pack-cells 6

# 完整仿真战役（默认 4 电压 × 4 油门，需几分钟内）
py -3.12 code\simulation\simulate_campaign.py

# 覆盖已有产物 / 不生成 PNG
py -3.12 code\simulation\simulate_campaign.py --force
py -3.12 code\simulation\simulate_campaign.py --no-plot

# v0.2 电池/温升敏感性分析
py -3.12 code\simulation\sensitivity_pack_model.py --overwrite

# v0.3 一阶热瞬态（默认 22.2 V、5 s 斜坡、300 s）
py -3.12 code\simulation\transient_thermal.py --overwrite

# v0.4 双节点热网络（加热 300 s + 冷却 300 s）
py -3.12 code\simulation\two_node_thermal.py --overwrite

# 回归测试（29 项）
py -3.12 -m unittest discover -s code\simulation -p "test_*.py" -v
```

## 产物（默认路径）

- `data/raw/20261119_SIM_*`：合成 raw CSV + meta；
- `data/processed/20261119_SIM_*_processed.csv`：逐样本物理量；
- `data/metadata/20261119_SIM_*_efficiency.json`：稳态汇总（`simulated:true`）；
- `data/metadata/calib_SIM_PHYS10x4.json`：仿真隐藏真值标定（`simulated:true`）；
- `data/processed/efficiency_map_runs.csv`、`efficiency_map_grid.csv`；
- `data/processed/figures/efficiency_map_v0.1.png`（SIM 红字强制标注）；
- `data/processed/simulation_campaign_summary.csv`：模型 vs 流水线误差表；
- v0.2：`data/processed/pack_model_sensitivity_v0.2.csv`、
  `data/processed/figures/pack_model_impact_v0.2.png`；
- v0.3：`data/processed/transient_thermal_v0.3.csv`、
  `data/processed/figures/transient_thermal_v0.3.png`；
- v0.4：`data/processed/two_node_thermal_v0.4.csv`、
  `data/processed/figures/two_node_thermal_v0.4.png`（含单节点对照曲线）。

## 安全约定

1. 不覆盖已有产物：默认 `FileExistsError`，需显式 `--force`；
2. 仿真标定与模型参数绑定：参数变化而未 `--force` 时拒绝复用旧标定；
3. meta 中 `mode:"simulate"`、`simulated:true`、`data_notice` 必须保留，下游据此打 SIM 标记；
4. 仿真 run_id 带日期与 `SIM` 前缀，避免与实机文件混名；
5. v0.2/v0.3/v0.4 参数（内阻/R_th/k_loss/C_th/C_w/C_s/R_ws/R_sa）为工程假设，只用于敏感性/瞬态趋势，不得引用为实测；热参数须由温升试验辨识后替换。

详见 `docs/design/simulation_model_v0.1.md`、`docs/design/simulation_model_v0.2.md`、
`docs/design/simulation_model_v0.3.md`、`docs/design/simulation_model_v0.4.md`。
