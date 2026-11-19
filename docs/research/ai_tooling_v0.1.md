# AI 工具链与 Agent 项目组（v0.1）

> 记录日期：2026-11-19（Asia/Shanghai）。用途：说明本项目可用的 AI 工具、安装状态、Agent 项目组分工与使用边界。
> 纪律：AI 工具只做辅助（检索、整理、代码草稿、复核清单）；**事实性结论必须可核验**，不得编造文献/标准/数据；SIM 与实测、REFERENCE 与实验结论严格区分；AI 生成内容在对外材料中标注。

## 1. 已安装并验证的工具

| 工具 | 版本 / 位置 | 状态 | 验证命令 |
|---|---|---|---|
| Volcengine CLI（`ve`） | 2.0.2，`%APPDATA%\npm\ve.cmd` | ✅ 已装（2026-11-17），`ve.cmd --version` 返回 2.0.2 | `ve.cmd --version` |
| Ark CLI（`arkcli`） | 1.0.41，`%USERPROFILE%\.volcengine\proxy-cli\bin\arkcli.exe` | ✅ 可用（`ve.cmd arkcli --help` 正常）；升级已安排到 npm 全局副本（Windows 需进程退出后应用，日志 `%USERPROFILE%\.arkcli\update-apply.log`） | `ve.cmd arkcli --version` |
| arkcli AI Skills | 28 个，`%USERPROFILE%\.agents\skills\` 与 `%USERPROFILE%\.claude\skills\` 同步安装 | ✅ 已装（2026-11-19）：arkcli-agent / api-explorer / auth / billing / chat / code-example / config / connect / custommodel / datasets / deploy / docs / doctor / gen / helper / infer-endpoint / models / onboard / plans / pricing / profile / resources / shared / train-finetune / understand / usage / vmp / vmp-workflows | `arkcli +connect list` |
| Volcengine Agent Skills（core） | 6 个：volcengine-cli / troubleshooting / knowledge-search / find-skills / billing-and-cost-management / feedback | ✅ 已装（2026-11-17），与 arkcli skills 并存 | 查看 `.agents\skills` |
| DSH Agent Teams | 本会话：Lead + 4 名 teammate | ✅ 运行中（见第 2 节） | `list_agents` / 任务看板 |

## 2. Agent 项目组（2026-11-19 组建）

| 角色 | 负责范围 | 产出 |
|---|---|---|
| Lead（本 Agent） | 统筹、代码/数据主线（效率流水线、地图、仿真、选型、对标集成）、索引与验证 | 代码/数据/文档更新、全量测试、最终交付 |
| `lit-researcher` | 外部科研成果调研：UAV 电推进效率建模、台架测量、GP/代理模型、公开桨数据库 | `docs/research/literature_review_v0.1.md`、`references.csv` |
| `standards-researcher` | 标准/法规/竞赛/软著/专利调研 | `docs/research/standards_regulation_v0.1.md`、`competition_softcopyright_v0.1.md` |
| `gap-analyst` | 项目深读：申报目标 vs 现有能力 vs 差距/风险/下一阶段计划 | `docs/research/project_deep_dive_v0.1.md` |
| `benchmark-builder` | UIUC 多桨型静态对标 v0.2（代码/数据/图件/测试） | `code/reference/`、`data/reference/uiuc/`、`docs/design/public_data_benchmark_v0.2.md` |

协作约定：每个 Agent 认领共享任务（`team_task_*`）后在限定写范围内工作；Lead 复核、集成、跑全量测试；结果汇总到 `docs/research/README.md`。

## 3. 凭据与安全边界

- **未配置**任何云凭证：没有 `ve login` / `ve configure set`，无 AK/SK；未调用任何云 API、未产生费用、未写入密钥。
- 因此需要云端鉴权的 arkcli 能力（chat/gen/models 等）暂不可用；本地 skills、文档检索与 Web 研究可用。
- 如后续需要云端能力：由项目负责人使用自己的账号执行 `ve.cmd login` 或注入 `VOLCENGINE_ACCESS_KEY`/`VOLCENGINE_SECRET_KEY` 环境变量；**密钥不得写入仓库、文档或聊天记录**（D011）。

## 4. 使用边界与风险

1. AI 检索可能出现幻觉：文献条目必须核对 URL/DOI；标准号与条款必须以官方渠道为准（待核实处明确标注）。
2. AI 生成的代码须跑测试；生成的结论须与代码/数据/产物一致；不得把 SIM/REFERENCE 结果写成实验结论。
3. 软著/竞赛/专利材料涉及学校与官方审核：AI 仅做初稿整理，最终以学校通知与登记机关要求为准。
4. 所有研究资料入库前检查：来源可访问、日期明确、与项目问题相关、无版权/许可冲突（UIUC 数据仅镜像小样本，见 D023）。

## 变更记录

- 0.1（2026-11-19）：首次记录 AI 工具安装状态（ve 2.0.2、arkcli 1.0.41、28 arkcli skills、6 volcengine skills）与 4 名 Agent 分工。
