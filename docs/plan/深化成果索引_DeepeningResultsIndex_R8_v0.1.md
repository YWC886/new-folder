# 深化目标成果索引（Rounds 1–8）

日期：2026-11-22　目标：`goal-feedf8e7-…`（max 240）　状态：持续进行中

## 1. 新增代码与测试

| 文件 | 作用 | 测试 |
|---|---|---|
| `code/reference/geometry_prior.py` | 几何/转速特征线性代理（LOPO 验证） | `test_geometry_prior.py`（8） |
| `code/processing/uncertainty.py` | 标定/测量误差 → η_sys Monte Carlo 传播 + 灵敏度 | `test_uncertainty.py`（7） |
| `code/reference/bem_propeller.py` | BEM-lite 叶素动量静态桨模型（局部动量闭合） | `test_bem_propeller.py`（8） |

全仓测试：**304 项 / 6 套**；源代码页 75 文件 / 16,933 行 / 339 页；复现包清单 237 文件。

## 2. 关键结果（全部 REFERENCE/SIM，非实测）

| 结果 | 内容 | 决策 |
|---|---|---|
| 几何代理 LOPO | C_T 11.37%→**19.21%**；C_P 16.68%→**19.61%**（未优于通用先验） | D049 |
| η_sys 不确定度 | 名义 0.2749，MC 95% 区间 **[0.2687, 0.2814]**，最大贡献推力标定斜率 | D050 |
| BEM-lite（APC 10x7E） | C_T 误 53.0%、C_P 误 26.5%、FM≈0.687；REFERENCE-GEOM 近似 | D051 |
| 仿真 DoE 合同 | σ 策略网格/ holdout 改善 83.9%/92.4%（PASS），EI 次之，random 最优值跟踪 FAIL | 合同 §6 |

## 3. 文档与论文

- 设计文档：`docs/design/geometry_prior_v0.1.md`、`uncertainty_propagation_v0.1.md`、`bem_model_plan_v0.1.md`、`bem_lite_v0.1.md`、`sim_doe_contract_v0.1.md`；
- 论文：新增 §3.6（不确定度传播实现）、§4.3（建模对照与不确定度）、§4.1 占位表当前值对齐；Word 已重生成；
- 产物：`data/processed/geometry_prior_v0.1.csv`、`data/metadata/uncertainty_v0.1.json`、`data/metadata/bem_lite_v0.1.json`、`data/processed/sim_doe_contract_v0.1.csv`、对应图件。

## 4. 使用与复现

```bash
py -3.12 code/reference/geometry_prior.py --overwrite
py -3.12 code/processing/uncertainty.py --input data/raw/20261117_SIM_22V2_50pct_R1.csv --calib data/metadata/calib_SIM_DEMO.json
py -3.12 code/reference/bem_propeller.py --rpm 4000
py -3.12 code/tools/round_close.py
```

## 5. 边界与后续

- 全部结果标注 SIM / REFERENCE，不构成实测结论；实机后须以 MEASURED 数据重跑；
- 后续：BEM v0.2（桨尖损失 + 几何细化 + 8 桨迁移）、答辩/结题材料同步、论文 §4 占位表实测填充。
