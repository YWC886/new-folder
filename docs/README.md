# docs/ 团队文档索引

> 本目录存放项目的过程文档（设计、采购、测试、会议、文献）。规划与申报正文不在此目录，见项目根目录的 `.docx` 文件。

## 目录结构

```text
docs\
├─ README.md                本索引（文档清单、写作与评审规范）
├─ decisions.md             技术决策记录（ADR）
├─ design\                  台架、采集、数据处理方案
│  ├─ bench_v0.1.md
│  ├─ daq_v0.1.md
│  ├─ data_dictionary_v0.1.md
│  ├─ processing_pipeline_v0.1.md
│  ├─ processing_pipeline_v0.2.md
│  ├─ calibration_fit_v0.1.md
│  ├─ efficiency_map_v0.1.md
│  ├─ efficiency_map_v0.3.md
│  ├─ efficiency_map_v0.4.md
│  ├─ simulation_model_v0.1.md
│  ├─ simulation_model_v0.2.md
│  ├─ simulation_model_v0.3.md
│  ├─ simulation_model_v0.4.md
│  ├─ public_data_benchmark_v0.1.md
│  ├─ public_data_benchmark_v0.2.md
│  ├─ selection_matching_v0.1.md
│  ├─ selection_matching_v0.2.md
│  ├─ selection_matching_v0.3.md
│  └─ selection_matching_v0.4.md
├─ procurement\             采购 BOM、询价、到货验收
│  ├─ bom_v0.1.md
│  └─ 询价单模板.md
├─ inputs\                  被测对象与实验室条件确认单
│  └─ 被测对象与实验室条件确认单_v0.1.md
├─ test\                    测试记录与报告
│  ├─ 静态砝码读数记录_v0.1.md
│  └─ 采集链路自检报告_v0.1.md
├─ plan\                    拓展方向与软件路线
│  └─ 拓展方向_v0.1.md
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
│  └─ roles.md
├─ softcopyright\           软著与复现材料（说明书、源代码页、复现包清单）
├─ meeting\                 会议纪要与行动项
│  └─ 会议纪要模板.md
```

## 文档清单

| 文档 | 版本 | 状态 | 负责人 | 更新日期 |
| --- | --- | --- | --- | --- |
| `design/bench_v0.1.md` | v0.1 | 草稿（待 B 评审） | B | 2026-11-19 |
| `design/daq_v0.1.md` | v0.1 | 草稿（待 C 评审） | C | 2026-11-19 |
| `design/data_dictionary_v0.1.md` | v0.1 | 草稿（随协议同步） | C/D | 2026-11-19 |
| `design/processing_pipeline_v0.1.md` | v0.1 | 草稿（基础口径；v0.2 为增量，口径不变） | D | 2026-11-19 |
| `design/processing_pipeline_v0.2.md` | v0.2 | 草稿（稳态 auto + 一阶不确定度，23 项测试） | D | 2026-11-19 |
| `design/calibration_fit_v0.1.md` | v0.1 | 草稿（静态砝码标定拟合：输入格式、指标、JSON、限制，15 项测试） | C/D | 2026-11-19 |
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
| `design/selection_matching_v0.4.md` | v0.4 | 草稿（GP 多目标 Pareto + 补测点推荐，43 项测试） | D | 2026-11-19 |
| `design/public_data_benchmark_v0.1.md` | v0.1 | 草稿（UIUC 静态 CT/CP 对标，9 项测试） | D | 2026-11-19 |
| `design/public_data_benchmark_v0.2.md` | v0.2 | 草稿（多桨型 8 桨/112 点 + pooled 统计 + 分组图，18 项测试） | D | 2026-11-19 |
| `research/literature_review_v0.1.md` | v0.1 | 草稿（六主题综述 + 差距 G1–G6；40 条参考文献） | lit-researcher | 2026-11-19 |
| `research/standards_regulation_v0.1.md` | v0.1 | 草稿（国标/团标/计量/安全/伦理，21 条来源） | standards-researcher | 2026-11-19 |
| `research/competition_softcopyright_v0.1.md` | v0.1 | 草稿（大创/赛事/软著/专利论文，15 条来源） | standards-researcher | 2026-11-19 |
| `research/project_deep_dive_v0.1.md` | v0.1 | 草稿（37 项能力矩阵、Top3 风险与下一步、给导师 7 问） | gap-analyst | 2026-11-19 |
| `research/ai_tooling_v0.1.md` | v0.1 | 草稿（AI 工具链与 4 名 Agent 分工、凭据边界） | Lead | 2026-11-19 |
| `softcopyright/软件说明书_V1.0.md` | V1.0 | 初稿（软著说明书；附源代码页生成器与复现包清单） | A/E | 2026-11-19 |
| `plan/拓展方向_v0.1.md` | v0.1 | 草稿（四方向 + 搁置清单） | A/D | 2026-11-19 |
| `procurement/bom_v0.1.md` | v0.1 | 草稿（11-25 询价） | C | 2026-11-19 |
| `procurement/询价单模板.md` | v0.1 | 可直接使用 | C | 2026-11-19 |
| `inputs/被测对象与实验室条件确认单_v0.1.md` | v0.1 | 待填写（11-21 冻结） | A | 2026-11-19 |
| `test/静态砝码读数记录_v0.1.md` | v0.1 | 模板 | B/C | 2026-11-19 |
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
| `code/reference/` | 公开数据对标（UIUC 单桨 + v0.2 多桨型目录） | 参考数据来源、许可证与对标记录（结果标 REFERENCE） |
| `code/tools/` | 软著/复现材料生成器（源代码页、SHA256 清单） | 把代码与文档稳定导出为登记/复现材料 |
| `docs/research/` | 文献、标准、竞赛/软著、项目深读、AI 工具 | 设计选择与成果材料的可核验依据 |
| `docs/softcopyright/` | 软著说明书、源代码页、复现包清单 | 登记材料与交付复现依据 |
| `data/` | raw / processed / metadata | 测试记录与标定结果 |
