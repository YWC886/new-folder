# docs/research/ 研究资料索引

> 记录日期：2026-11-19（Asia/Shanghai）。本目录集中存放**外部科研成果调研**与**项目深读**资料，供设计、申报与成果材料引用。
> 纪律（D030）：所有外部资料必须可核验（URL/DOI/官方渠道），不得编造文献、标准号或数据；REFERENCE 数据与 SIM/实测结论严格分离；引用时注明来源与检索日期。

## 文件清单

| 文档 | 内容 | 负责人 | 检索日期 | 核验状态 |
| --- | --- | --- | --- | --- |
| [`ai_tooling_v0.1.md`](ai_tooling_v0.1.md) | AI 工具链（ve 2.0.2 / arkcli 1.0.41 / 28 个 AI skills）与 4 名 Agent 分工、凭据安全边界 | Lead | 2026-11-19 | 本机实测（`ve.cmd --version`、`arkcli --version`、skills 目录） |
| [`literature_review_v0.1.md`](literature_review_v0.1.md) | 六主题文献综述（效率地图/推进性能/台架测量/代理模型/DoE/公开数据）、四方向关联、差距 G1–G6、最接近 4 篇对比 | lit-researcher | 2026-11-19 | 40 条参考文献；36 个 DOI 经 Crossref 核验 |
| [`references.csv`](references.csv) | L01–L40 参考文献表（9 列：编号/作者/题名/来源/年份/DOI/链接/类型/与本项目关系） | lit-researcher | 2026-11-19 | 36 DOI 存在性 + 题名/作者比对通过 |
| [`standards_regulation_v0.1.md`](standards_regulation_v0.1.md) | 无人机/推进相关国标、团标、计量规程、安全法规、学术伦理与数据规范；21 条来源 | standards-researcher | 2026-11-19 | 官方/标准平台页面；不确定处标"待核实" |
| [`competition_softcopyright_v0.1.md`](competition_softcopyright_v0.1.md) | 大创结题、创新大赛/挑战杯/CADC 匹配、软著登记材料与流程、专利/论文方向、风险清单；15 条来源 | standards-researcher | 2026-11-19 | 官方页面为主；赛事年份与校级要求标"待官方核实" |
| [`project_deep_dive_v0.1.md`](project_deep_dive_v0.1.md) | 申报目标 vs 现有能力（37 项矩阵）、Top3 风险、Top3 下一步、给导师 7 问、10 项文档待统一 | gap-analyst | 2026-11-19 | 基于仓库实跑 134 项测试与文档核对 |

## 关键结论速览

- **空档与机会**：文献调研未见「整链实测 + GP 平滑 + 不确定度传播 + 主动补测」一体化方案；匹配主流为部件模型 + 数据库；ESC 效率实测与 UQ 预算薄弱（详见 literature_review §6）。
- **最接近的 4 篇（引用优先）**：
  - Nam 2023, IEEE Aerospace — <https://doi.org/10.1109/AERO55745.2023.10115581>
  - Piljek 2020, Applied Sciences 10(22):8229 — <https://doi.org/10.3390/app10228229>
  - Røstum 2026, MATEC 422:02007 — <https://doi.org/10.1051/matecconf/202642202007>
  - Dai 2019, IEEE/ASME T-Mech — <https://doi.org/10.1109/TMECH.2019.2890901>
- **标准基线**：GB/T 38058—2019（民用多旋翼无人机系统试验方法，<150 kg）、GB/T 39567—2020（多旋翼无人机用无刷伺服电动机系统通用规范）、GB/T 46460—2025（无人机锂电池）、T/XJBX 001—2024（无人机桨发匹配试验技术规范，≤500 kg，最接近本项目）；计量溯源见 JJG 391—2009 / JJG 99—2022 / JJG 995—2005。
- **项目现实**：硬件链路与砝码标定尚未验证，全部物理量为 SIM；Top3 下一步为确认单冻结、最小硬件链路 + 双人静态标定、硬件等待期并行软件成果（详见 project_deep_dive §6）。
- **重要更正**：根目录 `大创申报书（修改）.pdf` 为 2023 年光伏清洁机器人范本，**不是本项目申报书**；本项目申报表为「附件3…_已填写_大一新生版.docx」与「…_已填写.docx」（个人信息待补）。

## 使用约定

1. **引用格式**：正文用 `[Lxx]`（对应 `references.csv`）或直接给 DOI/URL；标准引用给标准号 + 年份，不引二手转述。
2. **区分口径**：外部测量值标 REFERENCE；本项目仿真标 SIM；只有实测数据可写"实测"。禁止把文献值或仿真值冒充本项目实验结果。
3. **待核实项**：各文件末尾均有"待核实清单"；在正式材料引用前，须通过官方页面或指导教师确认。
4. **更新方式**：新增调研文档按 `中文短名_v0.x.md` 命名，并在本索引登记；实质修改升版本号并更新检索日期。
5. **Agent 协作**：外部调研由 Agent 在限定写范围内完成，Lead 复核后集成（任务与写范围见 `docs/decisions.md` D030）。

## 与项目其他文档的关系

| 目录/文档 | 关系 |
| --- | --- |
| `docs/design/` | 文献结论支撑设计选择（台架方案、采集通道、效率口径、GP 代理） |
| `docs/plan/拓展方向_v0.1.md` | 研究方向与调研结论对齐（四方向 + 搁置清单） |
| `docs/softcopyright/` | 软著登记要求、竞赛/成果材料规范来自本目录调研 |
| `code/reference/` | UIUC 公开数据对标实现；引用与许可约定见 `data/reference/README.md` |
