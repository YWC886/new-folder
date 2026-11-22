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
