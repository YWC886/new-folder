# REFERENCE 逐桨先验 opt-in 对照（prior profile v0.1）

- 版本：v0.1（2026-11-21）
- 模块：`code/reference/prior_profile.py`（10 项测试）
- 数据：`data/metadata/uiuc_priors_v0.3.json`（7 桨，`do_not_apply: true`）
- 参考数据：`data/reference/uiuc/*.txt`（UIUC Propeller Database Vol.1，7 桨 / 112 静态点）
- 产物：`data/processed/prior_profile_vs_generic_v0.1.csv`（112 行）、`data/processed/figures/prior_profile_v0.1.png`

## 1. 目的与边界

回答一个建模问题：**如果比例模型（`CT=ct0·(n/n_ref)^aT`、`CP=cp0·(n/n_ref)^aP`）的先验参数换成目标桨型，误差能降到多少？**

这一步是"prior-informed 建模上限"的量化：

- 先验来自 UIUC 静态风洞数据的**逐桨反推**（`calibrate_uiuc.py`），属于 REFERENCE-derived；
- 按 D033/D034 固定 `do_not_apply: true`，**不是**本项目实测标定；
- 本对照只做 opt-in 参数包装（不改 `ModelParams` 默认值），不用于选型结论或宣称"模型已验证"；
- 实测校核仍须 M0.4 静态砝码标定 + D032 标定 JSON（`simulated:false`）。

## 2. 方法

1. `load_priors()` 校验先验 JSON（必须 `do_not_apply: true`）；
2. `model_from_prior(entry)` 用 `dataclasses.replace` 生成 opt-in `ModelParams`：`ct0←ct0`、`cp0←cp0`、`reynolds_ct_exp←aT`、`reynolds_cp_exp←aP`、`diameter_m←diameter_in×0.0254`，其余参数沿用默认（KV、电阻、无载电流、ESC 效率等）；
3. `compare_entry(entry, rows)` 在同一份 UIUC 静态曲线上逐点计算：
   - 通用先验（`ModelParams()` 默认值）的 `CT/CP` 相对误差；
   - 逐桨 prior profile 的 `CT/CP` 相对误差；
4. 汇总每桨平均绝对相对误差与提升倍数，输出 CSV 与柱状对比图。

> ⚠ 因为先验与参考数据来自同一批 112 个点，本对照是**样本内拟合残差**，提升倍数应理解为
> "换目标桨型参数后的误差上限"，不能当作对新桨型/新工况的泛化误差。

## 3. 结果（2026-11-21，SIM/REFERENCE 边界内）

| 桨型 | 点数 | C_T 通用 | C_T prior | 提升 | C_P 通用 | C_P prior | 提升 |
|---|---|---|---|---|---|---|---|
| apce_11x7 | 16 | 5.69% | 0.32% | 18.0× | 2.86% | 1.17% | 2.5× |
| apce_11x8 | 16 | 8.02% | 1.07% | 7.5× | 11.66% | 0.81% | 14.3× |
| apcsf_10x7 | 16 | 26.51% | 0.32% | 82.0× | 37.33% | 0.85% | 44.0× |
| apcsp_9x6 | 16 | 6.46% | 0.77% | 8.4× | 21.00% | 1.12% | 18.7× |
| grcp_10x6 | 16 | 15.62% | 1.51% | 10.3× | 7.83% | 0.47% | 16.6× |
| grsn_10x7 | 16 | 13.95% | 0.42% | 32.8× | 23.45% | 1.00% | 23.6× |
| ance_8.5x6 | 16 | 3.35% | 1.02% | 3.3× | 12.60% | 1.05% | 12.0× |

**总量对比**：通用先验 pooled 误差 C_T 11.37% / C_P 16.68%（`public_data_benchmark_v0.2`）；逐桨 prior profile 平均绝对残差约 **0.3%–1.5%**（C_T/C_P 各自），其中 apce_11x7 的 C_P 残差 1.17% 偏大（其 CP 拟合 `cp_log_r2≈0.30`，曲线近乎平坦、拟合信息量低）。

## 4. 解读

1. **先验错了会拖垮整链**：通用先验在 APC-SF 上单点误差可达 37%，说明"拿一个通用 C_T/C_P 参数做全桨选型"不可取；
2. **逐桨先验几乎可消除比例模型误差**：残差 0.3%–1.5% 已是数据自身噪声/拟合形式误差量级，比例模型在"已知目标桨型"时足够；
3. **真正的不确定性在"不知道目标桨型"时**：对新产品/新桨型，要么查它自己的风洞数据（UIUC/厂商），要么实机标定；本项目的实测效率地图正是解决这一点的路径；
4. **与实测标定的关系**：prior profile 可用于仿真建模/敏感性分析的参数初始化，但实测标定（D032）出厂后必须替换，二者不能混用。

## 5. 复现

```powershell
# 单桨（或 --props 多桨逗号分隔）
py -3.12 code\reference\prior_profile.py --props apce_11x7 --overwrite
# 全部 7 桨 / 112 点
py -3.12 code\reference\prior_profile.py --overwrite
# 测试
py -3.12 -m unittest discover -s code\reference -p "test_prior_profile.py" -v
```

## 6. 数据诚信与限制

- 输出 CSV 每行带 `data_note`（REFERENCE-derived，非实测标定）；
- 图件红字标注 `not a measurement U(k=2)`，与流水线 U(k=2) 严格区分（D034/D042）；
- 样本内对照：提升倍数不代表泛化能力；跨桨型/跨系列外推仍须实测；
- 未考虑：雷诺数真实修正（当前仅幂律近似）、风洞系统误差、桨面粗糙度/安装差异；
- 本模块不写回 `ModelParams` 默认值，不进入选型/地图主链路。

## 7. 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| 0.1 | 2026-11-21 | 首版：opt-in prior profile + 7 桨对照（10 项测试，D042） |
