# docs/ 团队文档索引

> 本目录存放项目的过程文档（设计、采购、测试、会议、文献）。规划与申报正文已归档到 `docs/规划/` 与 `docs/申报/`。

## 目录结构

```text
docs\
├─ README.md                本索引（文档清单、写作与评审规范）
├─ decisions.md             技术决策记录（ADR）
├─ 申报\                    申报材料（申报表、4 份附件 PDF、清单、预算）
│  ├─ README.md              申报材料索引与更新记录
│  ├─ 申报表\               附件3 模板与两版已填写、2026-11-21 导师改版（docx + 预览 PDF）
│  ├─ 附件\                 01 前期基础摘要 / 02 团队分工与实施计划 / 03 指导教师简介 / 04 已有成果佐证（PDF）
│  ├─ 申报附件清单_v0.1.md
│  └─ 经费预算_5000元_v0.1.md
├─ 规划\                    推进规划 v1/v1.1 + 第一阶段启动计划 + 申报书改版对比分析（docx + 预览 PDF）
├─ 参考\                    软件环境与使用说明、项目技能清单、2023 年范本 PDF（非本项目）
├─ design\                  台架、采集、数据处理方案
│  ├─ bench_v0.1.md
│  ├─ 数据采集方案_DAQ_v0.1.md
│  ├─ data_dictionary_v0.1.md
│  ├─ processing_pipeline_v0.1.md
│  ├─ processing_pipeline_v0.2.md
│  ├─ calibration_fit_v0.1.md
│  ├─ measured_readiness_v0.1.md
│  ├─ design_matrix_v0.1.md
│  ├─ design_matrix_v0.2.md
│  ├─ measured_e2e_drill_v0.1.md
│  ├─ efficiency_map_v0.1.md
│  ├─ efficiency_map_v0.3.md
│  ├─ efficiency_map_v0.4.md
│  ├─ simulation_model_v0.1.md
│  ├─ simulation_model_v0.2.md
│  ├─ simulation_model_v0.3.md
│  ├─ simulation_model_v0.4.md
│  ├─ public_data_benchmark_v0.1.md
│  ├─ public_data_benchmark_v0.2.md
│  ├─ public_data_benchmark_v0.3.md
│  ├─ bootstrap_priors_v0.1.md
│  ├─ prior_profile_v0.1.md
│  ├─ re_correction_v0.5.md
│  ├─ selection_matching_v0.1.md
│  ├─ selection_matching_v0.2.md
│  ├─ selection_matching_v0.3.md
│  ├─ selection_matching_v0.4.md
│  └─ selection_strategies_v0.5.md
├─ procurement\             采购 BOM、询价、到货验收
│  ├─ bom_v0.1.md
│  └─ 询价单模板.md
├─ inputs\                  被测对象与实验室条件确认单
│  └─ 被测对象与实验室条件确认单_v0.1.md
├─ test\                    测试记录与报告
│  ├─ 静态砝码读数记录_v0.1.md
│  └─ 采集链路自检报告_v0.1.md
├─ plan\                    拓展方向与软件路线
│  └─ 拓展方向_ExpansionDirections_v0.1.md
├─ research\                科研调研（文献、标准、竞赛/软著、项目深读、AI 工具）
│  ├─ README.md
│  ├─ ai_tooling_v0.1.md
│  ├─ literature_review_v0.1.md
│  ├─ references.csv
│  ├─ standards_regulation_v0.1.md
│  ├─ competition_softcopyright_v0.1.md
│  └─ project_deep_dive_v0.1.md
├─ literature\              文献检索与阅读记录
│  └─ 检索记录模板.md
├─ team\                    分工、看板、周报
│  ├─ roles.md
│  └─ task_division_3person_v0.1.md
├─ softcopyright\           软著与复现材料（说明书、源代码页、复现包清单）
├─ meeting\                 会议纪要与行动项
│  └─ 会议纪要模板.md
```

## 文档清单

| 文档 | 版本 | 状态 | 负责人 | 更新日期 |
| --- | --- | --- | --- | --- |
| `design/bench_v0.1.md` | v0.1 | 草稿（待 B 评审） | B | 2026-11-19 |
| `design/数据采集方案_DAQ_v0.1.md` | v0.1 | 草稿（待 C 评审） | C | 2026-11-19 |
| `design/data_dictionary_v0.1.md` | v0.1 | 草稿（随协议同步） | C/D | 2026-11-19 |
| `design/processing_pipeline_v0.1.md` | v0.1 | 草稿（基础口径；v0.2 为增量，口径不变） | D | 2026-11-19 |
| `design/processing_pipeline_v0.2.md` | v0.2 | 草稿（稳态 auto + 一阶不确定度，23 项测试） | D | 2026-11-19 |
| `design/calibration_fit_v0.1.md` | v0.1 | 草稿（静态砝码标定拟合：输入格式、指标、JSON、限制，15 项测试） | C/D | 2026-11-19 |
| `design/measured_readiness_v0.1.md` | v0.1 | 草稿（MEASURED 门禁：检查项、退出码、SIM 拒绝演练，10 项测试） | C/D | 2026-11-19 |
| `design/measured_e2e_drill_v0.1.md` | v0.1 | 草稿（MEASURED 端到端演练：6 项检查 + 负向对照，5 项测试） | D | 2026-11-19 |
| `design/efficiency_map_v0.1.md` | v0.1 | 草稿（aggregate + plot 已验证） | D | 2026-11-19 |
| `design/efficiency_map_v0.3.md` | v0.3 | 草稿（不确定度渲染：误差棒/格内 ±U，26 项测试） | D/E | 2026-11-19 |
| `design/efficiency_map_v0.4.md` | v0.4 | 草稿（GP 平滑代理 + LOOCV，38 项测试） | D | 2026-11-19 |
| `design/simulation_model_v0.1.md` | v0.1 | 草稿（模型 + 16 工况战役 + 闭环验证） | D | 2026-11-19 |
| `design/simulation_model_v0.2.md` | v0.2 | 草稿（电池内阻压降 + 温升/铜温漂敏感性，15 项测试） | D | 2026-11-19 |
| `design/simulation_model_v0.3.md` | v0.3 | 草稿（一阶热瞬态 T(t)/η_sys(t)，21 项测试） | D | 2026-11-19 |
| `design/simulation_model_v0.4.md` | v0.4 | 草稿（双节点热网络 + 冷却曲线，29 项测试） | D | 2026-11-19 |
| `design/selection_matching_v0.1.md` | v0.1 | 草稿（SIM 原型：Top-N + Pareto，14 项测试） | D | 2026-11-19 |
| `design/selection_matching_v0.2.md` | v0.2 | 草稿（油门插值 + 多目标 + U 过滤，20 项测试） | D | 2026-11-19 |
| `design/selection_matching_v0.3.md` | v0.3 | 草稿（GP 连续匹配 + σ 合成保守效率，34 项测试） | D | 2026-11-19 |
| `design/selection_matching_v0.4.md` | v0.4 | 草稿（GP 多目标 Pareto + 补测点推荐，43 项测试；v0.5 三入口守门后共 47 项） | D | 2026-11-19 |
| `design/selection_strategies_v0.5.md` | v0.5 | 草稿（补测策略对比：σ/EI/随机/不补测，闭环模拟，15 项测试 = 选型 62 项） | D | 2026-11-19 |
| `design/public_data_benchmark_v0.1.md` | v0.1 | 草稿（UIUC 静态 CT/CP 对标，9 项测试） | D | 2026-11-19 |
| `design/public_data_benchmark_v0.2.md` | v0.2 | 草稿（多桨型 8 桨/112 点 + pooled 统计 + 分组图，18 项测试） | D | 2026-11-19 |
| `design/public_data_benchmark_v0.3.md` | v0.3 | 草稿（逐桨参数反推 REFERENCE-derived priors，do_not_apply；10 项测试 = 参考共 28 项） | D | 2026-11-19 |
| `design/bootstrap_priors_v0.1.md` | v0.1 | 草稿（bootstrap 95% CI，非 U(k=2)；10 项测试 = 参考共 38 项） | D | 2026-11-19 |
| `design/prior_profile_v0.1.md` | v0.1 | 草稿（REFERENCE 逐桨先验 opt-in 对照：通用 vs prior，样本内上限；10 项测试 = 参考共 48 项） | D | 2026-11-21 |
| `design/re_correction_v0.5.md` | v0.5 | 草稿（Reynolds 修正负结果：单一 Re 幂律 R² 0.03–0.05，不写入默认参数；13 项测试 = 参考共 61 项，D044） | D | 2026-11-21 |
| `design/design_matrix_v0.1.md` | v0.1 | 草稿（多工况试验排程：full/sweep、字段、135 runs 基线；10 项测试 = 处理 82 项） | C/D | 2026-11-21 |
| `design/design_matrix_v0.2.md` | v0.2 | 草稿（目标推力反解 + 不可达跳过 + 顺序随机化；19 项测试 = 处理 91 项；D045） | C/D | 2026-11-21 |
| `design/geometry_prior_v0.1.md` | v0.1 | 完成（几何特征代理 + LOPO 负结果，REFERENCE，D049，8 项测试） | D | 2026-11-22 |
| `design/uncertainty_propagation_v0.1.md` | v0.1 | 完成（Monte Carlo η_sys 传播 + 灵敏度，SIM 演示，D050，7 项测试） | D | 2026-11-22 |
| `design/bem_lite_v0.1.md` | v0.1 | 完成（叶素动量 + 简化极曲线，APC 10x7E REFERENCE 对照，D051，8 项测试） | D | 2026-11-22 |
| `research/literature_review_v0.1.md` | v0.1 | 草稿（六主题综述 + 差距 G1–G6；40 条参考文献） | lit-researcher | 2026-11-19 |
| `research/standards_regulation_v0.1.md` | v0.1 | 草稿（国标/团标/计量/安全/伦理，21 条来源） | standards-researcher | 2026-11-19 |
| `research/competition_softcopyright_v0.1.md` | v0.1 | 草稿（大创/赛事/软著/专利论文，15 条来源） | standards-researcher | 2026-11-19 |
| `research/project_deep_dive_v0.1.md` | v0.1 | 草稿（37 项能力矩阵、Top3 风险与下一步、给导师 7 问） | gap-analyst | 2026-11-19 |
| `research/paper_method_draft_v0.1.md` | v0.1 | 草稿（方法骨架：台架/效率口径/DoE/GP/选型/补测；3 图、23 条参考文献、4 篇最接近工作对比表、§1.1 问题与贡献、§4.1 实测替换清单、§5.1 贡献、§5.2 风险表；数值全部 SIM/REFERENCE） | A/D | 2026-11-21 |
| `research/ai_tooling_v0.1.md` | v0.1 | 草稿（AI 工具链与 4 名 Agent 分工、凭据边界） | Lead | 2026-11-19 |
| `softcopyright/软件说明书_V1.0.md` | V1.0 | 初稿（软著说明书；附源代码页生成器与复现包清单） | A/E | 2026-11-19 |
| `plan/项目待办与决策清单_TODOandDecisions_v0.1.md` | v0.1 | 完整（阻塞项 B1–B5、内部待办 P1–P6、脚本约束、组会议程） | A | 2026-11-21 |
| `plan/会话记忆交接_MemoryPrimer_v1.2.md` | v1.2 | 已更新（状态/环境/资产/决策/目标/待办 + 开场清单；每轮交接用） | A | 2026-11-23 |
| `design/next_batch_plan_v0.1.md` | v0.1 | 草稿（补测批次计划：σ_total 优先级、字段、用法、限制；3 项测试） | C | 2026-11-23 |
| `plan/拓展方向_ExpansionDirections_v0.1.md` | v0.1 | 草稿（四方向 + 搁置清单） | A/D | 2026-11-19 |
| `procurement/bom_v0.1.md` | v0.1 | 草稿（11-25 询价） | C | 2026-11-19 |
| `procurement/询价单模板.md` | v0.1 | 可直接使用 | C | 2026-11-19 |
| `inputs/被测对象与实验室条件确认单_v0.1.md` | v0.1 | 待填写（11-21 冻结） | A | 2026-11-19 |
| `申报/README.md` | v0.1 | 已建立（申报材料索引与更新记录） | A | 2026-11-20 |
| `申报/申报附件清单_v0.1.md` | v0.2 | 可直接使用（附件为选填，01–04 PDF 已生成并归档） | A/D | 2026-11-20 |
| `申报/经费预算_5000元_v0.1.md` | v0.1 | 已录入申报系统并暂存（5000 元口径） | A/C | 2026-11-20 |
| `team/task_division_3person_v0.1.md` | v0.1 | 草稿（3 人小组分工与阶段计划） | A | 2026-11-20 |
| `规划/申报书对比分析与优化研究路径_v0.1.md` | v0.1 | 完成（改版 vs 原版差异总表、10 条问题清单、五阶段量化路径与门禁、7 条修改建议；docx/pdf 同步） | A/D | 2026-11-21 |
| `test/静态砝码读数记录_v0.1.md` | v0.1 | 模板 | B/C | 2026-11-19 |
| `test/试验执行SOP_v0.1.md` | v0.1 | 草稿（上电前检查/砝码标定/单工况流程/异常处置/入库门禁/复测判据；Word 版与 Excel 检查单同步） | B/C | 2026-11-21 |
| `test/试验执行SOP_一页版_v0.1.md` | v0.1 | 草稿（红线/上电前 6 查/标定/单工况/异常/收工一页速查；打印贴墙用） | B | 2026-11-21 |
| `test/采集链路自检报告_v0.1.md` | v0.1 | 已完成（仅模拟数据） | C | 2026-11-19 |
| `decisions.md` | — | 持续更新 | A | 2026-11-19 |
| `team/roles.md` | v0.1 | 草稿 | A | 2026-11-19 |
| `meeting/会议纪要模板.md` | — | 模板 | A | 2026-11-19 |

## 写作规范

1. **版本号**：`v0.x` 为草稿，`v1.0` 为评审冻结；每次实质修改升 0.1 并更新文档头部"更新日期"。
2. **状态**：草稿 → 评审中 → 冻结。冻结后修改需在文末"修改记录"注明原因与影响。
3. **事实与假设分开**：数值写"实测/手册/假设"，未验证的结论必须标注"待验证"，不得把模拟结果写成实测结果。
4. **单位**：采用 SI，力 N、扭矩 N·m、转速 r/min、电压 V、电流 A、温度 ℃。
5. **命名**：中文短名 + `_v0.x.md`；数据文件遵循 `日期_组合_电压_油门_重复.csv`。
6. **图表**：设计图用矢量/PNG 放 `docs/design/figs/`（待建），随文档版本一起提交。
7. **链接**：引用其他文档用相对路径；引用代码用仓库相对路径。

## 评审流程

1. 起草人提交草稿（Slack/微信 + 本目录文件）；
2. 评审人 48 h 内在文档头部写评审意见（或会议评审，纪要进 `docs/meeting/`）；
3. 起草人修订 → 版本 +0.1 → 状态改"评审中/冻结"；
4. 冻结版同步更新根目录 `README.md` 的交付物列表。

## 与其他目录的关系

| 目录 | 内容 | 关系 |
| --- | --- | --- |
| `work/research/` | 调研报告（bench_tech.md 等） | 本文档的技术依据 |
| `work/plan/` | 规划与阶段计划源文件 | 里程碑与分工依据 |
| `code/` | 采集与数据处理代码 | 采集方案与接口协议 |
| `code/processing/` | 效率计算流水线 | 处理方案与质量门槛的实现 |
| `code/simulation/` | 物理仿真模型与仿真战役 | 生成 SIM 数据、效率地图先验与闭环验证 |
| `code/selection/` | 选型匹配原型（Top-N / Pareto；v0.2 插值、v0.3 GP 连续匹配、v0.4 多目标 Pareto + 补测推荐） | 把效率地图转为任务需求匹配结论（当前 SIM） |
| `code/reference/` | 公开数据对标（UIUC 单桨 + v0.2 多桨型目录 + v0.3 逐桨参数反推 + bootstrap 95% CI，do_not_apply） | 参考数据来源、许可证与对标记录（结果标 REFERENCE） |
| `code/tools/`（含 Office 导出 `export_office.py`） | 软著/复现材料生成器（源代码页、SHA256 清单）、一键 CI（六套测试合跑）、提交前一致性检查与 MEASURED 端到端演练 | 把代码与文档稳定导出为登记/复现材料，固化测试、发布前门禁与 MEASURED 链路演练 |
| `docs/research/` | 文献、标准、竞赛/软著、项目深读、AI 工具 | 设计选择与成果材料的可核验依据 |
| `docs/softcopyright/` | 软著说明书、源代码页、复现包清单 | 登记材料与交付复现依据 |
| `data/` | raw / processed / metadata | 测试记录与标定结果 |

## 2026-11-22 治理补充（v5）

- `参考/文件命名与索引_FileNamingIndex_v0.2.md`：中英双名索引（对外提交件保留正式中文名）。
- `规划/开题答辩PPT_v0.2.pptx`：按 v4 口径（同一桨型、不更换桨型）替换多桨对比页。
- 论文 `research/paper_method_draft_v0.1.*`：对标表述统一为「REFERENCE 方法验证」。
- 一致性审计：`code/tools/audit_consistency.py` 已接入 `round_close.py`（HARD 必须为 0）。
- 当前计数：71 源文件 / 16,461 行 / 330 页；复现清单 228 文件；测试 289 项。

### 2026-11-22 M0.4 启动包

- `inputs/M0.4启动包_M0.4KickoffPack_v0.1.md`：采购→台架→双人标定→MEASURED 门禁→首采的完整清单与命令；
- `data/metadata/templates/calibration_readings_template.csv`：砝码读数长表模板（已用 `calibration_fit.py` 干跑验证，可生成合法标定 JSON）；
- 状态：硬件/标定未开始；网络受限导致远端 push 暂不可用（已记录）。
