# Round 20 推进计划：UQ 与 DoE 选型判据口径统一 v0.1

> 继承自 `docs/plan/会话记忆交接_MemoryPrimer_v1.0.md`；目标 `goal-feedf8e7…`（深化，19/240 → 本轮 20）。
> 状态：计划已立，代码增量待下一轮执行；先统一口径，再改代码，避免"两套不确定度各说各话"。

## 1. 为什么要统一

当前仓内存在三套"不确定性"表述：

| 来源 | 定义 | 现状 |
|---|---|---|
| `processing/compute_efficiency.py` | U(k=2) 稳态窗传播（k=2） | 每个汇总 JSON 的 `u_eta_sys_k2`（D012/D050） |
| `processing/uncertainty.py` | Monte Carlo 1σ（输入项标定/噪声） | 单点 demo：η_sys 0.2749，σ 0.0032，95% CI [0.2687, 0.2814] |
| `selection` 各入口 | `eta_sys_conservative = η − sqrt((2σ_gp)² + u_local²)`（D027/D028） | 选型/Pareto 排序用"保守效率" |

问题：`2σ_gp`（GP 预测不确定性）与测量 U(k=2) 是**两种不同来源**，简单平方相加缺少书面约定；MC 的 1σ 与 U(k=2) 的换算关系也未写死。若不统一，选型结论与论文表述会冲突。

## 2. 统一口径（草案，待 D056）

- **测量不确定度**：`u_meas = U(k=2)/2`（即 k=2 覆盖因子换算为 1σ）；保留 `U(k=2)` 作为对外报告值；
- **代理/模型不确定度**：`σ_model` 为 GP 预测标准差（或 bootstrap 区间半宽/1.96，需在文档注明来源）；
- **合成（1σ）**：`σ_total = sqrt(u_meas² + σ_model²)`；
- **保守效率（对外比较用）**：`η_cons = η_pred − 2·σ_total`（95% 单侧近似），并同时输出 `η_cons_1σ = η_pred − σ_total` 供敏感性检查；
- **禁止**：把 `U(k=2)` 与 `σ_gp` 直接相加、或把 bootstrap 区间当作 U(k=2)（D034）。

## 3. 落地任务（下一轮起）

1. `code/processing/uncertainty.py` 增加 `to_u2(sigma)` / `from_u2(u2)` 与 `combine_sigma(*sigmas)` 小函数 + 2 项测试；
2. 新增 `code/selection/uq_consistency.py`：
   - 输入：`runs CSV`（含 `eta_sys_mean`、`u_eta_sys_k2`）+ GP 预测 CSV（含 `eta_pred`、`eta_std`）；
   - 输出：`data/processed/selection_uq_consistency_v0.1.csv`（每候选：η_pred、u_meas、σ_model、σ_total、η_cons_2σ、η_cons_1σ，差值对比旧 `eta_sys_conservative`）；
   - 图：`data/processed/figures/selection_uq_consistency_v0.1.png`（排序变化：旧 vs 新，含 SIM 红字）；
   - 测试 ≥5 项（换算闭环、合成、旧新排序差异、CSV/PNG 保护、CLI）。
3. 文档 `docs/design/uq_selection_consistency_v0.1.md` + 决策 **D056**；
4. 论文 §3.6/§4.3 补一句统一口径（引用 D056），Word 重生成；
5. `source_pages.py --overwrite` → `round_close.py` → commit → push。

## 4. 验收判据

- `round_close PASS`（测试数按实际增加）；
- 一致性 CSV 中 `σ_total` 与 `sqrt(u_meas²+σ_model²)` 误差 <1e-9；
- 新旧排序差异有明确表格（允许排名变化，但必须解释原因）；
- 所有图件带 "SIMULATED DATA — NOT EXPERIMENTAL" 标注。

## 5. 风险

- 现有 selection 代码中 `2σ_gp + u_local` 的组合若被文档/论文引用，需同步改写，避免双重口径；
- 若 `u_eta_sys_k2` 缺失（旧汇总 JSON），新流程应 fallback 为 `None` 并 warning，不阻塞。

## 6. 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| 0.1 | 2026-11-22 | 建立 Round 20 计划：三套不确定度现状、统一口径草案（D056 待立）、落地任务与验收判据。 |
