# 公开数据对标 v0.3：UIUC 参考数据逐桨参数反推（REFERENCE-derived priors）

- 版本：v0.3（草稿）
- 日期：2026-11-19
- 负责人：D（Lead 复核）
- 关联：`code/reference/calibrate_uiuc.py`、`docs/design/public_data_benchmark_v0.2.md`、D031、D033
- 数据来源：UIUC Propeller Database, Vol.1 静态风洞数据（镜像见 `data/reference/uiuc/`，引用见 `data/reference/README.md`）

## 1. 目的与边界

v0.2 已量化"通用参数先验（generic MODEL）"在 7 个桨型上的偏差：C_P 系统性低估约 13.6%、C_T 偏差无统一方向。v0.3 回答下一个问题：**如果只针对某个桨型，用公开风洞数据反推 CT/CP 的转速幂律参数，能把量级误差压到多少？** 输出作为后续实测标定（M0.4，见 D032）之前的量级参照。

**这不是本项目实测标定。** 输出 JSON 固定 `do_not_apply: true`：

- 禁止写入 `propulsion_model.ModelParams` 默认参数；
- 禁止用于选型结论、论文/软著中的"校准完成"表述；
- 实测标定以 M0.4 静态砝码读数（D032）为准，本项目数据优先级高于公开数据（D031）。

## 2. 方法

模型形式与仿真一致（n 为 rev/s，n_ref = 100）：

```
C_T(n) = ct0 * (n / n_ref) ** a_T
C_P(n) = cp0 * (n / n_ref) ** a_P
```

对每桨 16 个静态点，在 log 空间做 2 参数 OLS：

```
ln C_T = ln ct0 + a_T * ln(n / n_ref)
ln C_P = ln cp0 + a_P * ln(n / n_ref)
```

指标：

| 指标 | 含义 |
|---|---|
| `ct_err_abs_before` / `cp_err_abs_before` | 通用先验（`ct0=0.110, a_T=-0.02, cp0=0.045, a_P=-0.035`）的逐点平均绝对相对误差 |
| `ct_err_abs_after` / `cp_err_abs_after` | 逐桨反推参数在**同一批点**上的平均绝对相对误差（拟合内误差，偏乐观） |
| `ct_holdout_abs` / `cp_holdout_abs` | 确定性留出：每 4 点取第 1 个做 holdout（约 4 点），用其余点拟合后在留出点上的平均绝对相对误差（粗略泛化检查，非随机、非统计显著） |
| `ct_log_r2` / `cp_log_r2` | log 空间拟合优度 |

## 3. 结果（7 桨 / 112 点，2026-11-19）

| 桨型 | ct0 | a_T | cp0 | a_P | CT 内误差 | CP 内误差 |
|---|---|---|---|---|---|---|
| APC-E 11x7 | 0.1087 | +0.082 | 0.0439 | −0.027 | 0.32% | 1.17% |
| APC-E 11x8 | 0.1094 | +0.115 | 0.0514 | −0.017 | 1.07% | 0.81% |
| APC-SF 10x7 | 0.1601 | +0.142 | 0.0787 | +0.186 | 0.32% | 0.85% |
| APC-Sport 9x6 | 0.1134 | +0.202 | 0.0563 | −0.071 | 0.77% | 1.12% |
| Graupner-CAM 10x6 | 0.1034 | +0.184 | 0.0407 | −0.103 | 1.51% | 0.47% |
| Graupner-SN 10x7 | 0.1309 | +0.038 | 0.0587 | −0.041 | 0.42% | 1.00% |
| Aeronaut-CE 8.5x6 | 0.1099 | +0.062 | 0.0501 | −0.133 | 1.02% | 1.05% |

汇总（pooled，单一参数拟合全部 112 点）：

| 先验 | C_T 平均绝对误差 | C_P 平均绝对误差 |
|---|---|---|
| 通用 generic prior | 11.37% | 16.68% |
| pooled REFERENCE prior | 11.90% | 14.13% |

### 3.1 结论

1. **逐桨反推可把内误差压到 0.3–1.5%（C_T）与 0.5–1.2%（C_P）**，说明"桨型专用幂律"能很好描述 UIUC 静态数据；量级参照有效。
2. **通用先验的主要问题不是"系数差一点"，而是转速指数方向错误**：通用 a_T = −0.02（随转速下降），而 7 桨实测反推 a_T 全为正（+0.038…+0.202）；这解释了 v0.2 中"7/7 桨实测 C_T 随 RPM 上升而模型缓降"的方向相反现象。
3. **单一 pooled 先验无法替代逐桨先验**：pooled C_T 甚至比通用先验更差（11.90% vs 11.37%），C_P 略好（14.13% vs 16.68%）；跨桨差异必须逐桨处理。
4. holdout 误差与内误差同量级（未出现明显过拟合），但因每桨仅 ~4 个留出点、且为确定性留出，**不作为统计结论**。

## 4. 数据纪律

- 参考数据只镜像小样本（7 桨），不镜像 UIUC 完整库；引用注明 UIUC（D023/D031）。
- 输出 CSV/JSON 均带 `data_note` / `disclaimer`，`do_not_apply: true`。
- 图件红字 "REFERENCE (UIUC, measured) fit — not a project measurement; not a calibration result (D033)"。
- 任何进入仿真默认值或选型结论的参数，必须来自本项目 M0.4 实测标定（D032）。

## 5. 复现命令

```powershell
py -3.12 code\reference\calibrate_uiuc.py --overwrite
# 产物：
#   data/processed/uiuc_calibration_v0.3.csv        （19 列，逐桨一次一行）
#   data/metadata/uiuc_priors_v0.3.json             （do_not_apply=true）
#   data/processed/figures/uiuc_calibration_v0.3.png
py -3.12 -m unittest discover -s code\reference -p "test_calibration_uiuc.py" -v  # 10 项
```

## 6. 限制与 v0.4 待办

| 限制 | 说明 |
|---|---|
| 静态数据 | UIUC 静态文件无风速（J）与 Re 修正；本项目台架为静态悬停近似，可接受，但动态工况不能外推 |
| 点数少 | 每桨约 16 点、单一测试条件；反推参数不确定度未量化（应做 bootstrap 或加权最小二乘） |
| 幂律形式 | 仅 2 参数，无法刻画 UIUC 曲线中的台阶/非线性段（如 APC-SF 高转速段） |
| 非本项目数据 | 桨型、加工、表面状态与项目被测桨不同；只能作量级参照 |

v0.4 候选：①对数空间加权拟合 + 参数置信区间（bootstrap）；③以 v0.3 先验替换仿真默认值做**敏感性对比图**（仍标注 REFERENCE，不改变默认行为）；④与实测标定（M0.4）同图对比；⑤扩展到 Vol.1 风速扫描数据（需另抓 J 列）。

## 7. 变更记录

- 0.1（2026-11-19）：创建；7 桨参数反推、pooled 对比、图件与 10 项测试。
