# 效率不确定度传播 v0.1（Monte Carlo）

日期：2026-11-22　状态：完成（SIM 演示）　决策：D050

## 1. 目的与边界

把标定与测量的 1σ 误差假设传播到系统效率 η_sys，输出均值、标准差与 95% 区间，
为论文不确定度章节与 U(k=2) 口径（D012）提供软件实现。

- 输入为原始 CSV + 标定 JSON，误差假设由 `--sigmas` 或默认表给出；
- 本版本在 SIM/REFERENCE 数据上演示，结果标注非实测；实机数据接入后按同样流程重跑；
- 不替代实机标定与 GUM 逐项评定（D032/D035），仅作为传播工具与论文证据之一。

## 2. 方法与默认假设

稳态窗口（最后 3 s）上，对每次抽样给标定斜率/偏置、电压、电流、转速、空气密度施加高斯相对误差，
逐样本重算 T、Q、η_em、FM、η_sys；N=1000，固定随机种子可复现；再做单因素灵敏度（固定其它因子）。

| 误差源 | 1σ 假设 |
|---|---|
| `thrust_k` | 0.50% |
| `torque_k` | 0.50% |
| `thrust_b_rel` | 0.20% |
| `torque_b_rel` | 0.20% |
| `voltage` | 0.50% |
| `current` | 0.50% |
| `rpm` | 0.10% |
| `density` | 1.00% |

## 3. 结果（SIM 演示：20261117_SIM_22V2_50pct_R1）

| 指标 | 数值 |
|---|---|
| 名义 η_sys | 0.2749 |
| MC 均值 | 0.2749 |
| 标准差 | 0.0032 |
| 95% 区间 | [0.2687, 0.2814] |
| 名义推力 | 9.799 N |
| 名义电功率 | 177.493 W |

单因素灵敏度（η_sys 1σ 贡献）：

| 误差源 | 贡献 |
|---|---|
| `thrust_k` | 0.204 pp |
| `current` | 0.142 pp |
| `density` | 0.136 pp |
| `voltage` | 0.131 pp |
| `thrust_b_rel` | 0.082 pp |
| `rpm` | 0.000 pp |
| `torque_k` | 0.000 pp |
| `torque_b_rel` | 0.000 pp |

## 4. 解读

1. 在默认误差假设下，η_sys 的 95% 区间宽度约 1.27 pp；
2. 对 η_sys 影响最大的因素是 `thrust_k`（0.204 pp），其次 `current`；
3. 电压/电流误差主要经 P_elec 传播、标定斜率经推力/扭矩传播，二者量级需实机标定后替换假设；
4. 论文中应把「测量不确定度」与「GP 预测标准差」分开表述（D026/D034）。

## 5. 复现

```bash
py -3.12 code/processing/uncertainty.py --input data/raw/20261117_SIM_22V2_50pct_R1.csv \
  --calib data/metadata/calib_SIM_DEMO.json --n 1000 --output data/metadata/uncertainty_v0.1.json
py -3.12 -m unittest discover -s code/processing -p "test_uncertainty.py"
```

## 6. 限制与后续

- 误差独立同分布假设、未含温漂与台架外推误差；实机标定后需替换 `DEFAULT_SIGMAS`；
- v0.2 候选：接入 GUM 逐项 B 类评定、与 bootstrap 先验区间分离展示、生成区间图。

## 7. 变更记录

- 0.1（2026-11-22）：Monte Carlo 传播工具 + SIM 演示 + 7 项测试。

## 8. 与选型工具的口径衔接（D056，2026-11-22）

MC 得到的是 **1σ 模型波动**（σ_model），不能与测量不确定度 U(k=2) 直接相加，也不能把 bootstrap 区间当作 U。统一口径：

```
u_meas     = U(k=2) / 2          # 换算到 1σ
σ_total    = sqrt(u_meas² + σ_model²)
η_cons     = η − k · σ_total     # k=2 呈现保守值
```

落地位置：
- `code/processing/uq_utils.py`：`from_u2/to_u2/combine_sigma/conservative_eta/integrate_u2`；
- `code/processing/uncertainty.py --u-k2`：MC 输出直接附 u_meas/σ_total/η_cons；
- `code/selection/uq_annotate.py`：为任意选型 CSV 补 UQ 列（`eta_cons_2sigma` 等）；
- `code/selection/multiobjective.py --uq-k2`：Pareto 前沿按 D056 重算保守效率并重排；
- 论文 §4.6 给出实现与示例（SIM 合成数据），并说明若不换算会高估 σ_total 约 2 倍。

边界：U(k=2) 默认值 0.0226 来自 SIM 合成数据；实测后必须用 D032/M0.4 的标定 metrics 替换，并保留 `data_note` 标注。

## 9. 变更记录

- 0.2（2026-11-22）：补 §8 与选型工具的口径衔接（D056）及落地命令。
