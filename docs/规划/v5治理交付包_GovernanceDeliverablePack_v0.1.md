# v5 治理交付包 · v5 Governance Deliverable Pack（v0.1）

> 汇编：v5 治理总结与移交、阶段总结、v4 四线核对表、用户操作指引、命名索引。
> 数据边界：全部材料为 SIM/REFERENCE 性质，非实测。

---

# v5 治理总结与移交说明 · Governance Summary & Handover v0.1

> 范围：2026-11-22 第 101–110 轮自动化治理。对象：申报材料 v4 口径、四线一致性、导出与清单、双语命名索引。

## 1. 治理目标与结果

| # | 目标 | 结果 | 证据（可复核） |
|---|---|---|---|
| ① | 全仓一致性审计 | 脚本上线；HARD 2→**0**，SOFT 60→52（文献语境/预期输出） | `code/tools/audit_consistency.py`；`data/processed/consistency_audit_v0.1.md` |
| ② | v4 口径刷新 | 附件 01–04、开题 PPT v0.2、论文措辞、交叉核对表全部对齐 | `work/tmp/attach/build_attachments.py`、`docs/规划/开题答辩PPT_v0.2.pptx`、`docs/plan/v4口径四线核对表_V4ConsistencyCrossCheck_v0.1.md` |
| ③ | 导出/清单刷新 | Excel/Word 2026-11-22 版；结题材料包 37 项核对 | `data/exports/项目成果总览_20261122.xlsx`、`.docx`、`结题材料包清单_20261121.csv` |
| ④ | 中英双名 | 非破坏式命名索引（对外提交件保留正式中文名） | `docs/参考/文件命名与索引_FileNamingIndex_v0.2.md` |
| ⑤ | 边界标注 | 全部材料保留 SIM/REFERENCE/MEASURED 标注；审计覆盖禁词与路径 | 审计报告 + 各材料页脚/说明 |
| ⑥ | 每轮 CI | `round_close.py` 三连：manifest → check_release → audit，全绿 | 提交历史 R101–R110 |

## 2. 口径统一规则（今后材料必须遵守）

1. **同一桨型、不更换桨型**为 v4 申报口径；涉及多桨内容只允许作为「REFERENCE 方法验证，非项目主线」提及；
2. 关键问题固定为两条：①系统级效率准确测量与解耦；②效率地图建模精度与匹配应用（同桨型、电压—工作点匹配）；
3. 所有数值必须标注来源（SIM / REFERENCE / MEASURED）；SIM 与 REFERENCE 不得表述为实验结论；
4. 计数（源文件/行/页、文件数、测试数）以 `source_pages.py` 与 `build_manifest.py` 的最新产物为准，不得手写臆测。

## 3. 移交清单（给团队/导师）

- 申报表：`docs/申报/申报表/`（v3 草稿、1121 批注修订版 v2/v3/v4 及 PDF）；待办：成员姓名学号 → 系统第 2 步以后；Word 修订痕迹与最终 PDF。
- 附件：`docs/申报/附件/` 01–04（v4 刷新版）。
- 开题：`docs/规划/开题答辩PPT_v0.2.pptx`（18 页）+ `答辩PPT大纲_v0.1.md` + `开题答辩要点_DefenseKeyPoints_v0.1.md`。
- 论文：`docs/research/paper_method_draft_v0.1.md/.docx`（§4.1 占位表待实测填数）。
- 软件：`code/` 六子系统 + tools（测试 281）；一键回归 `code/tools/run_all_tests.py`；轮次收尾 `code/tools/round_close.py`。
- 数据：`data/processed/`（CSV/图）、`data/exports/`（Excel/Word/清单）；原始数据仍为准。

## 4. 已知风险

- 未 push 到远端（origin 仍为初始提交 92c177b），仓库备份仅在本机；
- 根目录还存在被 Word 占用的 `附件3…_已填写.docx` 重复件（待关闭 Word 后 `git rm`）；
- 本机 Word COM 偶发挂起，影响修订痕迹/PDF 自动导出，需人工兜底；
- 论文/答辩材料中的数字随轮次变化，引用前请查最新计数。


---

# v5 治理阶段总结（R101–R114）· v5 Governance Stage Summary

> 统计截至 R114（2026-11-22）。数据边界：全部成果为 SIM/REFERENCE 性质，非实测。

## 1. 增量一览

| 轮次 | 增量 | 提交/标签 |
|---|---|---|
| R101 | 一致性审计脚本 v0.1（HARD 2→1） | `3501785` |
| R102 | 否定语境豁免 + 审计接入 round_close（HARD=0） | `263857b` |
| R103 | 申报附件 01–04 按 v4 口径刷新 | `2659118` |
| R104 | 开题答辩 PPT v0.2（同桨型·电压对比页） | `7923b17`（PPT 不入清单） |
| R105 | Excel/Word 导出与结题清单刷新；修复源码页过期 CI 红灯 | `9ab89dc`、`a181d42` |
| R106 | 论文表述统一为 REFERENCE 方法验证 | `d78b493` |
| R107 | 中英双名索引 v0.2（非破坏式） | `a7810fe` |
| R108 | docs 索引治理补充 + 结题清单刷新 | `92f14f9` |
| R109 | v4 四线交叉核对表 | `c09e8be` |
| R110 | 导出刷新 + 里程碑 | `3a2ac74`，tag **r110** |
| R111 | v5 治理总结与移交说明 | `f563339` |
| R112 | 本地发布包 r111 + SHA256 | `a0754ab` |
| R113 | 论文 §4.2 实测填数规则 | `f6e2de4` |
| R114 | 待办与决策清单更新 | `6e968f4` |

## 2. 指标

- 测试：**281 项 / 6 套**（acquisition 5 / processing 91 / simulation 29 / selection 62 / reference 61 / tools 33）；
- 源码页：**69 源文件 / 16,135 行 / 323 页**；
- 复现清单：**202 文件**；
- 审计：HARD=**0**，SOFT=52（文献语境/计划输出）；
- CI：`round_close.py` 三连（manifest → check_release → audit）每轮全绿；
- 发布包：`data/exports/release_r111.zip`，85.3 MiB，SHA256 `78FC…D8`。

## 3. 口径与边界

- v4 口径：同一桨型、不更换桨型；关键问题两条；
- 多桨 UIUC 内容仅作「REFERENCE 方法验证，非项目主线」；
- 所有材料标注 SIM/REFERENCE/MEASURED，禁词与断链由审计机器检查。

## 4. 遗留（用户侧）

成员姓名学号 → 申报第 2–5 步；v3/v4 修订痕迹/最终 PDF（需 Word）；根目录重复 docx 清理；远端 push；BOM 采购与 M0.4 实测。

## 5. 建议下一步

1. 用户侧事项优先（成员信息、Word 材料、push）；
2. 实测启动后按论文 §4.2 规则填数；
3. 继续每轮 round_close + 小步文档治理。


---

# v4 口径四线交叉核对表 · V4 Consistency Cross-Check v0.1

> 目的：确认「同一桨型、不更换桨型、关键问题两项」在四类交付物中表述一致，并保留可复核证据。
> 扫描日期：2026-11-22。数据边界：所有材料均为 SIM / REFERENCE 结果，非实测。

## 1. 核对矩阵

| 交付物 | 桨型口径 | 关键问题 | 多桨/跨桨内容 | 结论 |
|---|---|---|---|---|
| 申报附件 01（前期基础摘要） | 未提"更换桨型"；UIUC 8 桨仅作 REFERENCE 方法验证 | 测量与解耦 + 建模与应用（见附件 04/说明） | 保留并加注「非项目主线；v4 口径为同一桨型」 | ✅ 一致 |
| 申报附件 02（团队分工与实施计划） | 无桨型更换描述；任务为同一台架、同一桨型 | 待实测填充 | 无 | ✅ 一致 |
| 申报附件 03（指导教师简介与条件） | 不涉及桨型口径 | 不涉及 | 无 | ✅ 一致 |
| 申报附件 04（已有成果佐证） | UIUC 8 桨 112 点标注「方法验证（REFERENCE）」 | 不涉及 | 加注 REFERENCE 限定 | ✅ 一致 |
| 开题答辩 PPT v0.2 | 「同一桨型·电压对比」页；地图页「电压×油门」 | 两条关键问题已写入 | 多桨对比页已删除 | ✅ 一致 |
| 论文 `paper_method_draft_v0.1` | §4 标注 REFERENCE 方法验证；v4 口径说明 | §4.1 占位表按实测替换 | UIUC 内容为方法验证 | ✅ 一致 |
| Excel/Word 导出（20261122） | 数据即现有 CSV，无新增口径 | — | 导出页含审计与材料目录 | ✅ 一致 |

## 2. 机器可查证据

- 禁词审计：`py -3.12 code/tools/audit_consistency.py` → `HARD=0`，报告 `data/processed/consistency_audit_v0.1.md`；
- 轮次收尾：`py -3.12 code/tools/round_close.py` → `PASS`（manifest / 清单 / 源码页 / 审计）；
- 附件重生成脚本：`work/tmp/attach/build_attachments.py`（v4 措辞与当前计数 69/16,135/323）；
- PPT 生成：`code/tools/build_proposal_defense_ppt.py`（输出 v0.2）。

## 3. 遗留与下一轮

- 申报表正文 v3/v4 的 Word 修订痕迹仍需本机 Word 可用时导出（用户侧）；
- 论文 §4.1 占位表待 M0.4 实测数据填列；
- Excel 导出中的测试计数在每轮新增测试后需随 `export_office.py` 重跑刷新。


---

# 用户操作指引（一页纸）· User Operations Guide v0.1

> 面向团队与导师：如何恢复备份、推送远端、继续申报与实测。所有命令在项目根目录 `D:\下载\创新` 执行。

## 1. 环境与回归

```powershell
# 解释器（系统默认 python 是 3.15，不能用于本项目）
py -3.12 --version

# 全仓测试（281 项，6 套）
py -3.12 code\tools\run_all_tests.py

# 轮次收尾（清单 + 源码页 + 审计，必须 PASS）
py -3.12 code\tools\round_close.py
```

## 2. 备份与恢复

- 本地发布包：`data/exports/release_r120.zip`（85.3 MiB），SHA256 见同名 `.sha256`；
- 校验：`certutil -hashfile data\exports\release_r120.zip SHA256`；
- 恢复：解压到新目录后用 `py -3.12 code\tools\run_all_tests.py` 验证即可。

## 3. 推送远端（待用户执行一次）

```powershell
git remote -v                 # 当前 origin 仍指向旧地址
git remote set-url origin <你的私有仓库地址>
git push origin main --tags   # 连同 r10…r120 里程碑标签
```

## 4. 申报表后续

1. 在系统「项目成员&指导教师」步骤录入成员姓名/学号（当前缺数据）；
2. 立项依据/经费预算已按 v4 口径准备，可直接复制；
3. 附件 01–04 在 `docs/申报/附件/`（可选上传，需等"上传成功"提示）；
4. 最终提交前请导师审核；导出 Word 修订痕迹需本机 Word。

## 5. 实测启动（M0.4）

1. 按 `docs/test/试验执行SOP_v0.1.md`（含一页速查版）执行双人砝码标定；
2. 生成标定：`py -3.12 code\processing\calibration_fit.py --input <读数.csv> --output data\metadata\calib_MEASURED.json --diameter 0.2544`；
3. 门禁：`py -3.12 code\processing\measured_readiness.py --input <raw.csv> --calib <calib.json>`；
4. 处理/地图：`compute_efficiency.py --require-measured` → `aggregate_efficiency.py` → `gp_surface.py`；
5. 填论文 §4.2 表（规则见论文本身）。

## 6. 常用数据位置

| 内容 | 路径 |
|---|---|
| 申报材料 | `docs/申报/` |
| 规划与答辩 | `docs/规划/` |
| 参考与命名索引 | `docs/参考/` |
| 设计与决策 | `docs/design/`、`docs/decisions.md` |
| 过程数据 | `data/processed/`（CSV/图） |
| Excel/Word 导出 | `data/exports/` |

## 7. 纪律

- 所有数值标注 SIM / REFERENCE / MEASURED，模拟/参考不得写成实测；
- 提交前 `round_close.py` 必须 PASS（审计 HARD=0）；
- 代码只用 `py -3.12`；含中文的 .ps1 用 `pwsh` 或 `Invoke-Expression (Get-Content -Raw -Encoding UTF8 ...)`。


---

# 文件命名与索引（中英对照）· File Naming & Index（v0.2）

> 目的：在不破坏对外提交文件正式中文名的前提下，为仓库内文档提供中英双名索引，便于检索与交接。
> 规则：`中文短名_EnglishName_v版本号.扩展名`；**对外提交材料保留正式中文名**（学校系统/邮件附件要求），本文件仅作映射索引。

## 1. 原则

| 类别 | 是否改名 | 说明 |
|---|---|---|
| 对外提交（申报表、附件 01–04、Word/PDF 交付物） | 否 | 保留官方中文名；在索引中给 English 别名 |
| 过程文档（design/plan/research/team） | 是（新文档起） | `中文短名_EnglishName_vX.Y.md` |
| 代码与自动产物 | 否 | 路径即接口（`code/**`、`data/**`） |
| 历史文件 | 择机批量 | 以索引为准，避免大面积改名导致断链 |

## 2. 申报目录映射（docs/申报/）

| 现有文件 | 建议 English 别名 | 状态 |
|---|---|---|
| `申报表/附件3…_已填写_大一新生版.docx` | `ProposalForm_Appendix3_filled_v1.docx` | 对外正式名，不改 |
| `申报表/申报表-修改版.docx` | `ProposalForm_Revised_v1.docx` | 对外名，不改 |
| `申报表/申报表_1121_批注修订_第456部分.docx` | `ProposalForm_Annotated_Sec456Rev_v1.docx` | 对外名，不改 |
| `申报表/申报表-修改版_v3草稿.docx` | `ProposalForm_v3Draft.docx` | 内部草稿 |
| `申报表/改动说明_第四五六部分.md/.docx` | `ChangeLog_Sec456_v1.md/.docx` | — |
| `附件/01_项目前期基础与预研摘要.pdf` | `Attachment01_PreliminaryFoundation.pdf` | 上传名，不改 |
| `附件/02_团队分工与实施计划.pdf` | `Attachment02_TeamPlan.pdf` | 同上 |
| `附件/03_指导教师简介与指导条件.pdf` | `Attachment03_AdvisorSupport.pdf` | 同上 |
| `附件/04_已有成果佐证.pdf` | `Attachment04_Achievements.pdf` | 同上 |
| `经费预算_5000元_v0.1.md` | `Budget5000_v0.1.md` | 内部 |
| `申报附件清单_v0.2.md` | `AttachmentChecklist_v0.2.md` | 内部 |

## 3. 规划目录映射（docs/规划/）

| 现有文件 | 建议 English 别名 | 状态 |
|---|---|---|
| `开题答辩PPT_v0.2.pptx` | `ProposalDefensePPT_v0.2.pptx` | 待答辩用 |
| `开题答辩PPT_v0.1.pptx` | `ProposalDefensePPT_v0.1.pptx` | 历史 |
| `答辩PPT大纲_v0.1.md` | `DefensePPTOutline_v0.1.md` | — |
| `开题拓展方向_v0.1.md` | `ExpansionDirections_v0.1.md` | 已部分更名 |
| `申报书对比分析与优化研究路径_v0.1.md/.docx/.pdf` | `ProposalReview_OptimizedRoadmap_v0.1.*` | — |
| `结题材料总目录_v0.1.md` | `ProjectCompletionIndex_v0.1.md` | — |
| `大创项目_推进规划与技术预研_v1.1.docx` | `ProjectPlan_PrelliminaryStudy_v1.1.docx` | 历史 |

## 4. 参考目录映射（docs/参考/）

| 现有文件 | 建议 English 别名 | 状态 |
|---|---|---|
| `软件环境与使用说明.md` | `SoftwareEnvironmentGuide.md` | — |
| `文件命名规范_FileNaming_v0.1.md` | 已双语 | — |
| `无人机电调_ESCLearningGuide_v0.1.md/.docx` | 已双语 | — |
| `项目技能清单.md` | `ProjectSkillsInventory.md` | — |
| `大创申报书_2023年光伏清洁机器人范本_非本项目.pdf` | `Reference_2023PVRobotSample_NOT_thisProject.pdf` | 参考范本 |

## 5. 维护约定

- 新增文档按 `中文短名_EnglishName_vX.Y.md` 命名；对外提交件例外并在本节登记；
- 重命名后必须同步：`docs/README.md` 索引、文档内引用（`audit_consistency.py` 路径检查可发现断链）、`build_manifest.py` 清单；
- 每轮收尾 `round_close.py` 自动检查清单与源码页一致性。


---
