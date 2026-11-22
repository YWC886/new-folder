# 会话记忆交接 MemoryPrimer v1.1

> 用途：把本仓关键状态压缩成"可继承的记忆提示"，供新会话/新 Agent 直接接管。以磁盘与 git 为准；叙述为历史记录。
> 更新：2026-11-22（v1.1：UQ 口径统一 D056、BEM 定论、计数与 HEAD 刷新、Hindsight 云端记忆已启用）。

## 0. 一句话

大创项目「多旋翼 UAV 电机—螺旋桨—电调系统效率地图」：软件原型 + 仿真/对标 + 文档体系已成型（6 子系统、317 项测试、257 文件复现清单），深化目标 `goal-feedf8e7-…` 进行到 22/240，UQ 口径已统一（D056），BEM 已定论"只作诊断"（D049–D055）。

## 1. 仓库与版本

- 路径：`D:\下载\创新`；远程 `https://github.com/YWC886/new-folder.git`
- HEAD：**`b5a33ff`**（R23：D056 + 论文 §4.6）；远端同步至 `b5a33ff`（R23 时 push 成功）
- 里程碑 tag：r10/r21/r27/r30/r40/r50/r60/r90/r100/r110/r120（详见 `git tag`）
- 健康度：`round_close PASS`——317 项测试 / 6 套；复现包清单 257 文件 0 缺失 0 SHA 不一致；源代码页 86 文件 / 17,614 行 / 353 页

## 2. 环境与坑（重要）

- **Python**：必须 `py -3.12`（系统默认 3.15 会 numpy cp312 导入失败）；依赖在 `work/pylibs`
- **PowerShell**：执行策略 Restricted → 用 `Get-Content -Raw -Encoding UTF8` + `Invoke-Expression`；GBK 控制台会把 `⚠` 打印当失败 → 设 `PYTHONIOENCODING=utf-8`（`round_close.py` 已注入）
- **Word/PowerPoint 占用**：导出 PDF/改 PPT 前须关闭文件，否则 `Permission denied`；申报表 v3/v4 修订痕迹仍未生成
- **网络**：GitHub push 间歇失败，重试即可
- **禁词审计**：项目自述禁 `多桨对比/跨桨型/更换桨型/多套硬件`（v4 口径=同一桨型、不换桨型）；`audit_consistency.py` HARD>0 即失败
- **Hindsight 记忆**：配置 `C:\Users\35509\.hindsight\coding-agent.json`（apiUrl + apiToken，本机用户目录，不入库）；bank `coding-agent::创新`

## 3. 代码资产（`code/` 6 子系统 + tools）

| 模块 | 主要内容 | 测试 |
|---|---|---|
| `acquisition/` | 采集模拟/串口、validate | 5 |
| `processing/` | compute_efficiency、calibration_fit、measured_readiness、aggregate/plot、gp_surface、uncertainty、design_matrix、uq_utils | 101 |
| `simulation/` | propulsion_model、电池压降/温升、transient/two_node 热网络、simulate_campaign | 29 |
| `selection/` | match v0.2、gp_match v0.3、multiobjective v0.4、bo_suggest v0.5、allocation_demo、uq_consistency | 64 |
| `reference/` | uiuc_propdb/catalog/benchmark/calibrate/bootstrap/prior_profile/re_correction/geometry_prior/bem_*（含 multiprop、lopo_transfer） | 85 |
| `tools/` | source_pages、build_manifest、check_release、run_all_tests、round_close、md2docx、export_office、release_package、audit_consistency 等 | 33 |

产物：`data/raw`（只读）、`data/processed`（CSV/图）、`data/metadata`（标定/汇总 JSON）、`data/exports`（xlsx/docx/zip）、`data/reference/uiuc`（8 桨 112 点）。

## 4. 关键决策（浓缩）

- D012 效率口径：η_em=P_shaft/P_elec；FM=T^1.5/√(2ρA)/P_shaft；η_sys=FM·η_em；禁 T/P 简化
- D023 REFERENCE 纪律；D031 多桨对标仅量级；D033/D042 先验 do_not_apply；D034 bootstrap≠U(k=2)
- D035–D040 MEASURED 门禁、`--require-measured`、CI/preflight、MEASURED e2e 演练
- D043 DoE 排程；D045 目标推力反解；D046 Office 导出只搬运不改数据
- D049–D055 BEM/几何代理：误差可降但**不稳定、不可迁移** → BEM 只作误差诊断，不接入主线、不替代实测
- **D056 不确定度口径统一**：`u_meas=U(k=2)/2`、`σ_total=sqrt(u_meas²+σ_model²)`、`η_cons=η−k·σ_total`（呈现 k=2）；禁止 U 与 σ_gp 直接相加、禁止 bootstrap 冒充 U
- D050 不确定度传播（SIM）：η_sys 0.2749、σ 0.0032、95% CI [0.2687, 0.2814]

## 5. 主要成果文件

- 论文：`docs/research/paper_method_draft_v0.1.md`（§4.4/§4.5 BEM 定位、§4.6 UQ 口径）+ .docx
- 申报：`docs/申报/申报表/`（v2/v3/v4 批注修订版 + 改动说明 + v3 草稿）；附件 01–04 PDF 在 `docs/申报/附件/`
- 开题 PPT：`docs/规划/开题答辩PPT_v0.2.pptx`（18 页）；讲稿/Q&A 在 `docs/plan/`
- 软著：`docs/softcopyright/`（说明书 + 源代码页 86 文件/353 页 + 复现包清单 257 文件）
- 治理：`docs/plan/v5治理总结与移交_GovernanceHandover_v0.1.md`、`结题材料总目录_v0.1.md`
- 深化索引：`docs/plan/深化成果索引_DeepeningResultsIndex_R8_v0.1.md`、`深化成果索引增补_R12R14.md`
- UQ 落地：`code/processing/uq_utils.py`、`code/selection/uq_consistency.py`、输出 `data/processed/selection_uq_consistency_v0.1.csv`

## 6. 目标与轮次

- 旧目标 m00439（`goal-d3258191-…`）已 complete（R124 v5 治理闭环）
- **当前目标** `goal-feedf8e7-296b-427e-afa4-70de03ae6dfb`：deepening，max 240，22/240，active/armed
- 恢复方式：说"继续自动化"即可；暂停说"暂停"

## 7. 未完成 / 待办

1. 深化线 R24+ 候选：①把 `uq_consistency` 接入选型/补测判据（统一输出 `eta_cons_2sigma`）；②`uncertainty.py` 改为输出 U(k=2) 换算与合成；③论文/答辩/结题材料同步；④BEM 分族修正或正式定论
2. 申报表第 2–5 步填写（**缺成员姓名学号**；第 1 步+经费预算已暂存；填写包 `docs/申报/第2-5步填写包_…md`）
3. v3/v4 申报表修订痕迹（Word「审阅→比较」）与 PDF
4. 硬件 M0.4：采购/台架/双人砝码标定/首采（`docs/inputs/M0.4启动包_…md` + 标定模板 CSV）
5. 文档计数可能滞后：README/软著三文档以 `round_close` 输出为准（317/257/86/353）

## 8. 新会话开场清单

1. `git status` / `git log -1` 确认 HEAD 与工作树；网络好时先 `git push origin main`
2. `py -3.12 code\tools\round_close.py` 验证测试与清单/源码页一致
3. 读本文件 + `docs/plan/深化成果索引_DeepeningResultsIndex_R8_v0.1.md`
4. 每轮固定流程：改动 → `source_pages.py --overwrite` → `round_close.py` → `git commit` → `git push`
