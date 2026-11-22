# 会话记忆交接 MemoryPrimer v1.0

> 用途：把本仓全部关键状态压缩成"可继承的记忆提示"，供新会话/新 Agent 直接接管。
> 生成日期：2026-11-22；以磁盘与 git 为准，叙述性内容为历史记录。

## 0. 一句话

大创项目「多旋翼 UAV 电机—螺旋桨—电调系统效率地图」：软件原型 + 仿真/对标 + 文档体系已成型（6 子系统、312 项测试、250 文件清单），当前自动化深化目标进行到第 19 轮，处于 **blocked（会话上下文上限 + GitHub 网络不可达）**，需要在**新会话**恢复并先 push。

## 1. 仓库与版本

- 路径：`D:\下载\创新`；远程 `https://github.com/YWC886/new-folder.git`
- HEAD：**`90f81e3`**（R19：论文 §4.5 BEM 定位）；远端最新 **`68506de`**（本地领先 1 个提交，网络恢复后 `git push origin main`）
- 里程碑 tag：`milestone-2026-11-19-r10`、`-11-21-r21`、`-11-21-r27`、`-11-21-r30`、`-11-21-r40`、`-11-21-r50`、`-11-21-r60`、`-11-22-r90`、`-11-22-r100`、`-11-22-r110`、`-11-22-r120`
- 健康度：312 项测试 / 6 套全绿；`round_close` PASS（清单 250 文件 0 缺失 0 SHA 不一致；源代码页 82 文件 / 17,333 行 / 347 页）；工作树干净

## 2. 环境与坑（重要）

- **Python**：必须用 `py -3.12`（系统默认 python 是 3.15，会报 numpy cp312 导入错误）；依赖在 `work/pylibs`
- **PowerShell**：执行策略 Restricted，禁止 .ps1；含中文脚本用 `Get-Content -Raw -Encoding UTF8` + `Invoke-Expression`；控制台 GBK 会让测试打印 `⚠` 假失败 → 设 `PYTHONIOENCODING=utf-8`（`round_close.py` 已注入）
- **Word/PowerPoint 占用**：导出 PDF/改 PPT 前需关闭对应文件，否则报 `Permission denied`；v3 申报表修订痕迹/PDF 仍未生成
- **网络**：GitHub push 间歇失败（`Connection was reset` / `connect timeout`），需重试
- **禁词审计**：项目自述禁 `多桨对比/跨桨型/更换桨型/多套硬件`（v4 口径=同一桨型、不换桨型）；`audit_consistency.py` 会扫描（HARD>0 失败）

## 3. 代码资产（`code/` 6 子系统 + tools）

| 模块 | 主要内容 | 测试 |
|---|---|---|
| `acquisition/` | 采集模拟/串口、validate | 5 |
| `processing/` | compute_efficiency、calibration_fit、measured_readiness、aggregate、plot、gp_surface、uncertainty、design_matrix | 98 |
| `simulation/` | propulsion_model、pack 压降/温升、transient/two_node 热网络、simulate_campaign | 29 |
| `selection/` | match_propulsion v0.2、gp_match v0.3、multiobjective v0.4、bo_suggest v0.5、allocation_demo | 62 |
| `reference/` | uiuc_propdb、catalog、benchmark、calibrate、bootstrap、prior_profile、re_correction、geometry_prior、bem_propeller、bem_geometry_*、bem_lopo_transfer | 85+ |
| `tools/` | source_pages、build_manifest、check_release、run_all_tests、round_close、md2docx、export_office、release_package、audit_consistency 等 | 33 |

产物目录：`data/raw`（只读）、`data/processed`（CSV/图）、`data/metadata`（标定/汇总 JSON）、`data/exports`（xlsx/docx/zip）、`data/reference/uiuc`（8 桨 112 点）
文档目录：`docs/申报`、`docs/规划`、`docs/参考`、`docs/design`（约 33 篇）、`docs/research`、`docs/plan`、`docs/softcopyright`、`docs/test`、`docs/inputs`、`docs/decisions.md`（D001–D055）

## 4. 关键决策（浓缩）

- D012 效率口径：η_em=P_shaft/P_elec；FM=T^1.5/√(2ρA)/P_shaft；η_sys=FM·η_em；禁 T/P 简化
- D023 REFERENCE 纪律；D031 多桨对标仅量级；D033/D042 先验 do_not_apply；D034 bootstrap≠U(k=2)
- D035–D040：MEASURED 门禁、`--require-measured`、CI 脚本、preflight、MEASURED e2e 演练
- D043 DoE 排程；D045 目标推力反解；D046 Office 导出只搬运不改数据
- D049–D055 BEM/几何代理：单桨/跨桨反演误差可降但**不稳定、不可迁移** → BEM 只作误差诊断，不接入主线、不替代实测
- D050 不确定度传播：SIM 演示 η_sys 0.2749，σ 0.0032，95% CI [0.2687, 0.2814]

## 5. 主要成果文件（给新会话直接引用）

- 论文草稿：`docs/research/paper_method_draft_v0.1.md`（§4.4/§4.5 为 BEM 定位）；对应 .docx
- 申报：`docs/申报/申报表/`（v2/v3/v4 批注修订版 + 改动说明 + v3 草稿）；附件 01–04 PDF 在 `docs/申报/附件/`
- 开题 PPT：`docs/规划/开题答辩PPT_v0.2.pptx`（18 页）；答辩讲稿/Q&A 在 `docs/plan/`
- 软著：`docs/softcopyright/`（说明书 + 源代码页当前 82 文件/347 页 + 复现包清单 250 文件）
- 治理：`docs/plan/v5治理总结与移交_GovernanceHandover_v0.1.md`、`v5治理交付包_...pdf`、`结题材料总目录_v0.1.md`
- 深化索引：`docs/plan/深化成果索引_DeepeningResultsIndex_R8_v0.1.md`、`深化成果索引增补_R12R14.md`

## 6. 目标与轮次

- **旧目标** m00439（`goal-d3258191-…`）已 complete（R124，v5 治理闭环）
- **当前目标** `goal-feedf8e7-296b-427e-afa4-70de03ae6dfb`：deepening，max 240，19/240，**blocked**（会话上下文上限 + 网络）
- 恢复方式：新会话说"恢复深化目标/继续自动化" → `update_goal resume`（当前 revision 6）

## 7. 未完成 / 待办

1. `git push origin main`（本地领先 1 提交 `90f81e3`）
2. 申报表第 2–5 步填写（**缺成员姓名学号**；第 1 步+经费预算已暂存；填写包在 `docs/申报/第2-5步填写包_...md`）
3. v3/v4 申报表修订痕迹（Word「审阅→比较」）与 PDF
4. 硬件 M0.4：采购/台架/双人砝码标定/首采（`docs/inputs/M0.4启动包_...md` + 标定模板 CSV）
5. 深化线 Round 20+ 候选：UQ/DoE 与选型判据口径统一；BEM 分组修正或定论；论文/答辩/结题材料同步

## 8. 新会话建议开场

1. `git status`/`git log -1` 确认 HEAD 与工作树；网络好时先 push；
2. `py -3.12 code\tools\round_close.py` 验证 312 项测试 + 清单/源码页一致；
3. 读 `docs/plan/深化成果索引_DeepeningResultsIndex_R8_v0.1.md` + 本文件；
4. 按第 7 节优先级继续；每轮固定：改动 → `source_pages.py --overwrite` → `round_close.py` → commit → push。
