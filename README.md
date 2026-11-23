# 多旋翼 UAV 电机—螺旋桨—电调系统效率地图构建与匹配优化

西北工业大学 2026—2027 秋“高峰领航计划”选题 · 大学生创新创业训练计划（创新训练项目）
指导教师：宋受俊 教授（自动化学院）　项目组：5 名 2026 级本科生

**一句话**：把效率评价对象从单个部件扩展到“电调—电机—螺旋桨”整体，搭地面测试台架、建系统效率地图、做参数匹配优化，为多旋翼动力系统选型与能耗分析提供量化依据。

## 当前状态（2026-11-21）

> **当前口径（2026-11-23）**：全仓 **326 项测试 / 6 套**；复现包清单 **268 文件**；源代码页 **90 源文件 / 18,131 行 / 363 页**（以上由 `round_close.py` 实时校验；历史变更记录中的数字为当时快照）。

| 事项 | 状态 |
| --- | --- |
| 大创申报表填写 | 已完成两版：`…_已填写_大一新生版.docx`（按 2026 级新生条件改写，待补个人信息）；2026-11-21 收导师改版 `申报表-修改版.docx/.pdf`（已归档 `docs/申报/申报表/`） |
| 申报书改版分析 | `docs/规划/申报书对比分析与优化研究路径_v0.1.md`（+ `.docx` / `.pdf`）：11 章差异总表、10 条问题清单（名称—目标—成果不一致、量化指标缺位、预算—BOM 未对齐等）、优化后的五阶段研究路径与量化门禁、7 条可直接插入申报书的修改建议 |
| 项目推进规划 | **v1.1**：347 页，11 章 + 4 附录（WBS、进度、分工、环境、技术预研、风险、技能清单、启动清单） |
| 第一阶段启动计划 | 2026-11-17 至 11-30 逐日安排、5 个里程碑、技能分配与交付物清单 |
| 环境搭建 | Python 科学计算/建模/优化工具链可用（见 `docs/参考/软件环境与使用说明.md`）；VS Code 扩展已装 |
| 技术预研 | 效率链/效率地图/Pareto 演示 + GP 代理模型预研（学习曲线、不确定度、补测点推荐） |
| 最小采集链路 | 模拟采集与只读校验已通过（5000 行、1000 S/s、5 项测试）；标定拟合工具 `calibration_fit.py` 已就绪（读数 CSV → `simulated:false` 标定 JSON，15 项测试）；MEASURED 通路门禁 `measured_readiness.py` v0.1 已就绪（10 项测试，SIM 输入拒绝演练 exit 1）；实机串口与砝码标定待验证 |
| 数据处理流水线 | **v0.2 + 地图 v0.3 + GP v0.4**：原始 CSV + 标定 → 逐样本推力/扭矩/轴功率/电功率/η_em/FM/η_sys + 稳态汇总 JSON；稳态自动识别（`--steady auto`，推力/转速相对标准差 ≤1%）+ 一阶不确定度传播（U(k=2)：η_em 1.44%、FM/η_sys 2.26%）；效率地图汇总（runs/grid 带 U 列）+ 热力图（v0.3 支持 `--uncertainty`：误差棒与格内 ±U）；GP 平滑代理 v0.4（LOOCV 核宽 0.550、RMSE 0.001662、R² 0.9999，21×21 预测均值/标准差面）；91 项测试通过（含试验排程 19 项）；`compute_efficiency --require-measured` 与 `aggregate_efficiency --require-measured` 联动/汇总守门（拒绝 SIM/合成输入）；SIM 单点预览（9.799 N / 0.100 N·m / η_sys 0.2843） |
| 物理仿真与战役 | **v0.2 + v0.3 + v0.4**：准稳态推进—螺旋桨—电调模型 + 可选 `PackModel`（电池内阻压降 + 温升/铜温漂）；16 工况敏感性：η_sys 最大相对降幅约 2.09%、最高电机温度约 125 °C；v0.3 一阶热瞬态（`C_th`，τ≈112.5 s）给出 T(t)/η_sys(t)（22.2 V 满油门 300 s：24→80 °C）；v0.4 双节点热网络（绕组 + 定子/机壳，总热阻/热容与 v0.3 等价）给出加热—冷却曲线（22.2 V 满油门 300 s→停机 300 s：绕组峰值 82.9 °C、机壳 66.2 °C，单节点低估绕组约 2.9 K；冷却至 35 °C 用时 132 s）；v0.1 一键战役闭环（推力/η_sys 复原误差 <0.3% / <1.6%）；33 项测试通过；全部标注 SIM |
| 选型匹配原型 | **v0.1 + v0.2 + v0.3 + v0.4 + v0.5**：效率地图 → 推力需求 → 候选组合 + Pareto 图；v0.2 增加油门插值（精确命中需求推力）、多目标排序（`--objective eta_sys/current/balanced`）、U(k=2) 过滤与保守效率列；v0.3 引入 GP 连续匹配（thrust/η 双 GP → 每电压油门扫描 → `σ_gp` 与 U 合成保守效率）；v0.4 真多目标 Pareto（η — 电池电流 — 保守效率；5 N ±10% → 28 可行/5 前沿，knee 29.60 V/52.5%）+ GP σ 补测点推荐（5 点，限定已测油门区间）；v0.5 补测策略对比（σ/EI/随机/不补测，10 轮闭环模拟：σ 策略网格 RMSE 0.00634→0.00102、holdout 0.0191→0.0015；SIM 方法学证据）；SIM 演示（5 N ±10% → 3 个 GP 候选，22.2 V/68.2% 最优）；62 项测试通过；三入口 `--require-measured` 守门（仅接受 MEASURED runs CSV）；结果强制 SIM 标注，非选型结论 |
| 公开数据对标 | **v0.1 + v0.2 + v0.3 + v0.4 + v0.5**：UIUC Propeller Database 静态数据入库（8 个桨、112 点、3 品牌/6 系列、RPM 1,655–6,897，全部 REFERENCE）+ 解析/目录化对标；单桨 APC 10x7E：C_T 均值误差 6.14%、C_P 13.83%；多桨 pooled：C_T 绝对均值 11.37%（带符号 −0.69%）、C_P 16.68%（带符号 −13.62%，系统性低估）；v0.3 逐桨反推 CT/CP 幂律参数：内误差 0.3–1.5%（C_T）/0.5–1.2%（C_P），7 桨 a_T 全为正（通用先验 −0.02 方向相反），输出 `data/metadata/uiuc_priors_v0.3.json`（`do_not_apply:true`，仅参照、非本项目标定）；bootstrap 不确定度 v0.1：7/7 桨 a_T 的 95% CI 均在 0 以上且远离通用 −0.02（稳健）、pooled a_T CI [+0.028,+0.177] 很宽（不可靠先验），该区间非 U(k=2)；v0.4 prior-profile 对照：同数据 7 桨/112 点，通用先验 vs 逐桨先验误差 11.37%/16.68% → 0.3–1.5%（样本内上限，opt-in 不改默认）；v0.5 Reynolds 修正：单一 Re 幂律解释力极低（pooled CT R² 0.046 / CP 0.027；7 桨均值 CT 10.96%、CP 14.17%，远差于逐桨先验），负结果、不写入默认参数（D044）；69 项测试通过 |
| 软著与复现材料 | **v1.0**：软件说明书 + 自动生成源代码页（82 个源文件 / 17,333 行 / 347 页，含前 30+后 347 页提交指引）+ 复现包 SHA256 清单（250 个文件，约 8.6 MiB）+ 一键 CI、提交前一致性检查与 MEASURED 端到端演练（六套 312 项测试）；产物在 `docs/softcopyright/`；33 项工具测试 |
| 成果导出（Excel/Word） | **v0.1**：`code/tools/export_office.py` 把关键数据汇总为 Excel 工作簿（10 个工作表，含数据边界声明）+ Word 成果报告（成果概览/图件/验证/下一步）；`data/exports/项目成果总览_<日期>.xlsx`、`项目成果报告_<日期>.docx`（D046） |
| 论文与结题材料 | **v0.1 方法草稿**：`docs/research/paper_method_draft_v0.1.md` + 自动转换 Word 版（`code/tools/md2docx.py`，3 图/6 节/23 条参考文献（DOI 已核验）+ 最接近工作对比表）；全部数值标注 SIM/REFERENCE，投稿前须补实测与导师审阅（D047） |
| 试验执行 SOP | **v0.1**：`docs/test/试验执行SOP_v0.1.md` + Word 版；覆盖上电前检查、双人砝码标定、单工况流程、异常处置、入库门禁与复测判据；Excel 检查单见 `data/exports/项目成果总览_*.xlsx` 的「08b_试验执行检查单」；另有一页速查版 `docs/test/试验执行SOP_一页版_v0.1.docx`（打印贴墙用）（D048） |
| 软件拓展方向 | `docs/plan/拓展方向_ExpansionDirections_v0.1.md`：处理与效率地图自动化、公开数据对标、选型匹配原型、软著/竞赛/复现包；实机依赖项已按用户要求搁置 |
| 科研调研与资料 | `docs/research/`（索引 `docs/research/README.md`）：文献综述 40 条（36 DOI 经 Crossref 核验）、标准法规（GB/T 38058—2019、GB/T 39567—2020、T/XJBX 001—2024 等）、竞赛/软著登记要求、项目深读（37 项能力矩阵、Top3 风险与下一步）；4 名 Agent 完成、Lead 复核集成 |
| Python 解释器 | 已修复：系统默认 `python` 升至 3.15 与 `work/pylibs`（cp312）不兼容 → 安装 3.12.10，项目命令统一用 `py -3.12`（FAQ 第 10 条） |
| 依赖完整性 | `work/env/requirements.txt` 已补全 pandas / python-docx / openpyxl / lxml 等；`check_env.py` 全通过，采集 5 项测试通过（2026-11-19） |
| 团队过程文档 | `docs/` 初版：台架/采集方案 v0.1、BOM v0.1、输入确认单、测试记录模板、决策记录、分工与会议模板 |
| 可选工具 | 火山引擎 CLI `ve` 2.0.2 + 6 个 Agent Skills 已装（凭证未配置，用法见软件环境说明第八节） |
| AI 工具与 Agent 项目组 | 2026-11-19：`ve` 2.0.2 + `arkcli` 1.0.41 + **28 个 arkcli AI skills**（`.agents\skills` / `.claude\skills` 双装）+ 6 个 volcengine core skills；组建 4 名 Agent（文献调研 / 标准合规 / 项目深读 / 多桨对标）；凭证未配置（不联网调用、不产生费用）；工具用途与边界见 `docs/research/ai_tooling_v0.1.md`；研究资料见 `docs/research/` |
| 待确认输入 | 被测电机/桨/电调型号、台架位置与电源、团队人员信息（11-21 确认单冻结） |

## 交付物索引

| 文件 | 说明 |
| --- | --- |
| `docs/规划/大创项目_推进规划与技术预研_v1.1.docx` / `_预览.pdf` | 项目推进规划（主文档） |
| `docs/规划/大创项目_第一阶段启动计划_2026-11-17至11-30.docx` / `_预览.pdf` | 两周启动计划（可直接执行） |
| `docs/规划/申报书对比分析与优化研究路径_v0.1.md` / `.docx` / `.pdf` | 申报书改版对比分析（差异总表、问题清单、五阶段优化路径与量化门禁、修改建议） |
| `docs/参考/项目技能清单.md` | 6 类 30+ 项技能、L1—L3 标准、三阶段学习路径 |
| `docs/参考/软件环境与使用说明.md` | 环境总览、安装步骤、复现命令、FAQ、火山引擎 CLI（v1.2，2026-11-19） |
| `docs/申报/` | 申报材料：`申报表/`（附件3 模板与已填写两版 + 预览 PDF）、`附件/`（01 前期基础摘要 / 02 团队分工与实施计划 / 03 指导教师简介与指导条件 / 04 已有成果佐证，PDF 可直接上传）、`申报附件清单_v0.1.md`、`经费预算_5000元_v0.1.md` |
| `docs/` | 团队过程文档：`design/`（台架、采集、处理流水线）、`plan/`（拓展方向）、`procurement/`（BOM）、`inputs/`（确认单）、`test/`（标定记录）、`research/`（文献/标准/竞赛/项目深读）、`literature/`、`team/`、`meeting/` |
| `docs/research/` | 科研调研资料：`literature_review_v0.1.md` + `references.csv`（40 条）、`standards_regulation_v0.1.md`、`competition_softcopyright_v0.1.md`、`project_deep_dive_v0.1.md`、`ai_tooling_v0.1.md`；索引与引用约定见 `docs/research/README.md` |
| `code/acquisition/` | 最小采集链路：模拟/串口采集、数据字典、只读校验与回归测试 |
| `code/processing/` | 效率计算与效率地图：`compute_efficiency.py`（流水线，含稳态 auto + 不确定度）、`aggregate_efficiency.py`（多 run 汇总）、`plot_efficiency_map.py`（成图，v0.3 支持 `--uncertainty`）、`gp_surface.py`（v0.4 GP 平滑代理 + LOOCV）、`calibration_fit.py`（v0.1 静态砝码标定拟合 → `simulated:false` 标定 JSON）、`measured_readiness.py`（v0.1 MEASURED 通路门禁）、`compute_efficiency --require-measured` 联动守门、`design_matrix.py`（v0.2 目标推力反解排程 + 顺序随机化 full/sweep）、91 项测试 |
| `code/selection/` | 选型匹配原型：`match_propulsion.py`（v0.2 推力需求 → 插值/网格候选 → 多目标 Top-N + Pareto 图）、`gp_match.py`（v0.3 GP 连续匹配 + σ 合成保守效率）、`multiobjective.py`（v0.4 GP 多目标 Pareto + knee + GP σ 补测点推荐）、`bo_suggest.py`（v0.5 补测策略对比：σ/EI/随机/不补测，闭环模拟）、62 项测试、三入口 `--require-measured` 守门；当前仅 SIM 原型 |
| `code/simulation/` | 物理仿真：`propulsion_model.py`（准稳态模型 + v0.2 `PackModel` 电池内阻/温升）、`simulate_campaign.py`（一键仿真战役）、`sensitivity_pack_model.py`（电池/温升敏感性）、`transient_thermal.py`（v0.3 一阶热瞬态）、`two_node_thermal.py`（v0.4 双节点热网络 + 冷却曲线）、33 项测试；产物 `efficiency_map_v0.1.png`（16 工况 SIM 地图）、`pack_model_impact_v0.2.png`、`transient_thermal_v0.3.png`、`two_node_thermal_v0.4.png` 与 `simulation_campaign_summary.csv` |
| `code/reference/` | 公开数据对标：`uiuc_propdb.py`（单桨解析）、`benchmark_uiuc.py`（单桨 CT/CP 对标）、`catalog_uiuc.py`（v0.2 多桨目录 + pooled 统计 + 分组图）、`calibrate_uiuc.py`（v0.3 逐桨参数反推，REFERENCE-derived priors，do_not_apply）、`bootstrap_priors.py`（bootstrap 95% CI，非 U(k=2)）、`prior_profile.py`（v0.4 逐桨先验 opt-in 对照）、`re_correction.py`（v0.5 Reynolds 修正负结果，不写入默认参数，D044）、69 项测试；参考数据非本项目实测 |
| `code/tools/` | 软著/复现材料、CI、提交前检查与 MEASURED 演练：`source_pages.py`（源代码页 + 清单 JSON）、`build_manifest.py`（复现包 SHA256 清单）、`run_all_tests.py`（六套测试一键合跑）、`check_release.py`（提交前：测试 + 清单 + 源代码页新鲜度）、`measured_e2e_drill.py`（MEASURED 端到端演练，临时夹具）、24 项测试 |
| `docs/softcopyright/` | 软著材料：`软件说明书_V1.0.md`、`复现包清单_V1.0.md`、`build/`（自动生成源代码页 347 页 + 文件清单） |
| `data/raw/`、`data/processed/`、`data/metadata/`、`data/reference/` | 原始（只读）/处理后/校验与标定/公开参考数据；样例为模拟或参考数据（分别带 `SIM`、`REFERENCE` 标记） |
| `docs/申报/申报表/附件3：…_已填写_大一新生版.docx` | 已填写的申报表（个人信息待补；原件保留在 `docs/申报/申报表/`） |
| `work/research/` | 调研报告：`bench_tech.md`（台架/测量）、`modeling_opt.md`（建模/优化）、`research_brief.md`（文献综述） |
| `work/prestudy/` | 预研代码与图件：`efficiency_demo.py`、`prestudy_gp.py`、`fig1—fig5`、CSV/JSON |
| `work/plan/` | 规划源文件（Markdown）、拼装与转换脚本、各版渲染图 |

## 快速开始

```powershell
# 若本机 python 不是 3.12（FAQ 第 10 条），以下命令一律改用 py -3.12

# 环境自检（自动加载 work/pylibs 本地依赖）
python work/env/check_env.py

# 预研演示：效率链 / 效率地图 / Pareto
python work/prestudy/efficiency_demo.py

# GP 代理模型预研：学习曲线与不确定度
python work/prestudy/prestudy_gp.py

# 最小采集链路：模拟采集 + 只读校验 + 回归测试
python code/acquisition/acquire.py --mode simulate --duration 5 --sample-rate 1000
python code/acquisition/validate.py --input <原始CSV路径> --window 3
python -m unittest discover -s code/acquisition -p "test_*.py" -v

# 效率计算流水线（当前仅 SIM 数据 + 合成标定联调，输出带 ⚠ 模拟数据 标记）
py -3.12 code\processing\compute_efficiency.py --input data\raw\20261117_SIM_22V2_50pct_R1.csv --calib data\metadata\calib_SIM_DEMO.json --window 3
py -3.12 -m unittest discover -s code\processing -p "test_*.py" -v
# v0.1 静态砝码标定拟合（真实读数 → simulated:false 标定 JSON；实机 M0.4 使用）
py -3.12 code\processing\calibration_fit.py --input data\calibration\静态砝码读数.csv --output data\calibration\calib_MEASURED.json --diameter 0.4572

# MEASURED 通路门禁（0=就绪；SIM 输入 exit 1）
py -3.12 code\processing\measured_readiness.py --input data\raw\<run_id>.csv --calib data\metadata\calib_MEASURED.json

# 联动守门：效率计算入口拒绝 SIM/合成输入（默认关闭，实测显式开启）
py -3.12 code\processing\compute_efficiency.py --input data\raw\<run_id>.csv --calib data\metadata\calib_MEASURED.json --steady auto --require-measured

# 汇总守门：效率地图汇总只接受实测来源（含 SIM 时 exit 2）
py -3.12 code\processing\aggregate_efficiency.py --dir data\metadata --require-measured

# 效率地图数据汇总 + 成图（SIM 数据图件强制标注，非实验结果）
py -3.12 code\processing\aggregate_efficiency.py --dir data\metadata
py -3.12 code\processing\plot_efficiency_map.py
# v0.3：把 U(k=2) 画进图（误差棒 / 格内 ±U）
py -3.12 code\processing\plot_efficiency_map.py --uncertainty --output data\processed\figures\efficiency_map_v0.3.png --overwrite
# v0.4：GP 平滑代理（LOOCV 选核宽；输出 21×21 预测均值/标准差面，非物理模型）
py -3.12 code\processing\gp_surface.py --overwrite

# 物理仿真：单工作点 / 一键战役（模型 → 合成 raw → 流水线 → 效率地图；全部 SIM）
py -3.12 code\simulation\propulsion_model.py --voltage 22.2 --throttle 0.5
py -3.12 code\simulation\propulsion_model.py --voltage 22.2 --throttle 1.0 --pack-cells 6   # v0.2 电池+温升
py -3.12 code\simulation\simulate_campaign.py
py -3.12 code\simulation\sensitivity_pack_model.py --overwrite                              # v0.2 敏感性
py -3.12 code\simulation\transient_thermal.py --overwrite                                   # v0.3 热瞬态
py -3.12 code\simulation\two_node_thermal.py --overwrite                                    # v0.4 双节点热网络（加热+冷却）
py -3.12 -m unittest discover -s code\simulation -p "test_*.py" -v

# 选型匹配原型（SIM 效率地图 → 推力需求 Top-N + Pareto 图；非选型结论）
py -3.12 code\selection\match_propulsion.py --input data\processed\efficiency_map_runs.csv --thrust 5 --tolerance 0.1 --output data\processed\selection_top_n.csv --figure data\processed\figures\selection_v0.1.png --overwrite
# v0.2：油门插值 + 多目标排序 + 保守效率（3 N ±5%，balanced）
py -3.12 code\selection\match_propulsion.py --input data\processed\efficiency_map_runs.csv --thrust 3.0 --tolerance 0.05 --objective balanced --output data\processed\selection_v0.2_thrust3.csv --figure data\processed\figures\selection_v0.2.png --overwrite
# v0.3：GP 连续匹配（5 N ±10%，eta_sys 排序；σ_gp 与 U 合成保守效率）
py -3.12 code\selection\gp_match.py --input data\processed\efficiency_map_runs.csv --thrust 5 --tolerance 0.1 --objective eta_sys --output data\processed\selection_v0.3_gp.csv --figure data\processed\figures\selection_v0.3.png --overwrite
# v0.4：GP 多目标 Pareto（η/电流/稳健性）+ knee（5 N ±10%）
py -3.12 code\selection\multiobjective.py --input data\processed\efficiency_map_runs.csv --thrust 5 --tolerance 0.1 --output data\processed\selection_v0.4_pareto.csv --figure data\processed\figures\selection_v0.4.png --overwrite
# v0.4：GP σ 补测点推荐（限定已测油门区间，间距 ≥0.12）
py -3.12 code\selection\multiobjective.py --input data\processed\efficiency_map_runs.csv --suggest --n 5 --min-distance 0.12 --output data\processed\gp_suggestions_v0.4.csv --figure data\processed\figures\gp_suggestions_v0.4.png --overwrite

# 选型结果按统一口径（D056）输出：U(k=2)=0.0226 时重算保守效率并重排 Pareto
py -3.12 code\selection\multiobjective.py --input data\processed\efficiency_map_runs.csv --thrust 5 --tolerance 0.1 --uq-k2 0.0226 --output data\processed\selection_v0.4_pareto_u2.csv --figure data\processed\figures\selection_v0.4_uq.png --overwrite
# 对已有选型 CSV 补 UQ 列（u_meas/sigma_total/eta_cons_2sigma）
py -3.12 code\selection\uq_annotate.py --input data\processed\selection_v0.4_pareto.csv --runs data\processed\efficiency_map_runs.csv --output data\processed\selection_v0.4_pareto_uq.csv --overwrite
# 补测批次计划（D056）：GP σ + U(k=2) 合成优先级
py -3.12 code\selection\batch_plan.py --overwrite
# 同时生成 design_matrix 兼容采集排程
py -3.12 code\selection\batch_plan.py --schedule data\processed\next_batch_schedule_v0.1.csv --repeats 1 --overwrite

# v0.5：补测策略对比（σ / EI / 随机 / 不补测；10 轮闭环模拟，SIM 方法学）
py -3.12 code\selection\bo_suggest.py --rounds 10 --overwrite
py -3.12 -m unittest discover -s code\selection -p "test_*.py" -v

# 公开数据对标：UIUC 静态数据解析 + 模型对标（参考数据非本项目实测，结果标 REFERENCE）
py -3.12 code\reference\uiuc_propdb.py --input data\reference\uiuc\apce_10x7_static_pg0811.txt
py -3.12 code\reference\benchmark_uiuc.py --reference data\reference\uiuc\apce_10x7_static_pg0811.txt --overwrite
# v0.2：多桨型目录对标（8 桨 112 点；per-prop + pooled 统计与分组图）
py -3.12 code\reference\catalog_uiuc.py --reference-dir data\reference\uiuc --output data\processed\uiuc_benchmark_v0.2.csv --summary data\processed\uiuc_benchmark_v0.2_summary.csv --figure data\processed\figures\uiuc_benchmark_v0.2.png --overwrite
# v0.3 逐桨参数反推（REFERENCE-derived priors，do_not_apply）
py -3.12 code\reference\calibrate_uiuc.py --overwrite
# v0.5 Reynolds 修正对标（负结果：单一 Re 幂律解释力极低，不写入默认参数）
py -3.12 code\reference\re_correction.py --overwrite
py -3.12 -m unittest discover -s code\reference -p "test_*.py" -v

# 软著/复现材料：源代码页（按每页 50 行连续编号）+ 复现包 SHA256 清单
py -3.12 code\tools\source_pages.py --out-dir docs\softcopyright\build --overwrite
py -3.12 code\tools\build_manifest.py --output data\processed\release_manifest_v0.1.csv --overwrite
py -3.12 -m unittest discover -s code\tools -p "test_*.py" -v

# 一键 CI：六套测试合跑（acquisition/processing/simulation/selection/reference/tools）
py -3.12 code\tools\run_all_tests.py

# 提交前一致性检查：六套测试 + 复现包清单 SHA256 + 软著源代码页新鲜度（全部通过 exit 0）
py -3.12 code\tools\check_release.py
py -3.12 code\tools\export_office.py --overwrite   # 导出 Excel 成果总览 + Word 成果报告到 data\exports\\
py -3.12 code\tools\md2docx.py --input docs\research\paper_method_draft_v0.1.md --output docs\research\paper_method_draft_v0.1.docx --overwrite   # Markdown → Word
py -3.12 code\tools\md2docx.py --input docs\test\试验执行SOP_v0.1.md --output docs\test\试验执行SOP_v0.1.docx --overwrite   # SOP → Word

# MEASURED 端到端演练：临时合成夹具串起门禁→流水线→汇总→选型，并做 SIM 负向对照
py -3.12 code\tools\measured_e2e_drill.py
```

> 依赖安装在 `work/pylibs/`（不污染系统环境，且不入 Git）；完整安装步骤见 `docs/参考/软件环境与使用说明.md`。

## 目录约定

- `work/research/` 调研报告 · `work/prestudy/` 预研代码与图 · `work/plan/` 规划文档源文件 · `work/env/` 环境脚本
- `code/acquisition/` 采集程序与数据字典 · `code/processing/` 效率流水线 · `code/simulation/` 物理仿真 · `code/selection/` 选型匹配 · `code/reference/` 公开数据对标 · `code/tools/` 软著/复现材料生成
- `data/raw/` 原始数据（禁止覆盖） · `data/processed/` 处理后数据 · `data/metadata/` 校验与标定记录 · `data/reference/` 公开参考数据（只读，注明来源/许可）
- `docs/` 团队过程文档（设计、采购、确认单、测试、文献、会议、分工） · `docs/research/` 科研调研资料 · `docs/softcopyright/` 软著与复现材料
- `docs/申报/` 申报材料（申报表、4 份附件 PDF、清单、预算） · `docs/规划/` 推进规划与阶段计划（docx + 预览 PDF） · `docs/参考/` 环境说明、技能清单、2023 年范本 PDF
- 申报表相关：模板 `docs/申报/申报表/附件3：…（创新训练项目）.docx` 保持未改动；填写结果另存新文件

## 下一步

**软件拓展（实机数据到位前优先，见 `docs/plan/拓展方向_ExpansionDirections_v0.1.md`）**

1. ✅ 效率地图 v0.2 + v0.3 + v0.4：不确定度传播、稳态自动识别、`--uncertainty` 误差棒/格内 ±U、GP 平滑代理（LOOCV 核宽 0.550、RMSE 0.001662、R² 0.9999，21×21 预测面）已完成（38 项测试，`docs/design/processing_pipeline_v0.2.md`、`efficiency_map_v0.3.md`、`efficiency_map_v0.4.md`）；剩余：与 prestudy 口径统一（GP 已并入选型 v0.3，见 D027）；
2. ✅ 仿真模型 v0.2 + v0.3 + v0.4：电池内阻压降、温升/铜温漂敏感性（16 工况）、一阶热瞬态 T(t)/η_sys(t) 与双节点热网络（绕组/机壳 + 冷却曲线）已完成（33 项测试，`docs/design/simulation_model_v0.2.md`、`simulation_model_v0.3.md`、`simulation_model_v0.4.md`）；剩余：v0.5 用实测温升/冷却曲线辨识热参数（公开桨数据校核已由 `code/reference/` 承接）；
3. ✅ 公开数据对标 v0.1 + v0.2 + v0.3 + v0.4 + v0.5：单桨 UIUC 入库 + 解析器 + CT/CP 对标（v0.1，9 项测试）→ 多桨目录 v0.2（8 桨 112 点、per-prop/pooled 统计、分组图，18 项测试）→ 逐桨参数反推 v0.3（7 桨内误差 0.3–1.5%/0.5–1.2%，a_T 方向与通用先验相反；输出 do_not_apply）→ bootstrap 不确定度 v0.1（7/7 桨 a_T CI 远离 0、pooled CI 很宽；非 U(k=2)）→ prior-profile 对照 v0.4（通用先验 vs 逐桨先验，误差 11.37%/16.68% → 0.3–1.5%，样本内上限，opt-in 不改默认）→ Reynolds 修正 v0.5（单一 Re 幂律解释力极低：pooled CT R² 0.046/CP 0.027，7 桨均值 CT 10.96%/CP 14.17%，负结果、不写入默认，69 项测试，`docs/design/re_correction_v0.5.md`）；剩余：更多桨型/风速扫描、几何特征回归（v0.6 留出验证）、与实测标定同图对比、联合置信椭圆；
4. ✅ 选型匹配原型 v0.1 + v0.2 + v0.3 + v0.4 + v0.5：离散网格 → 油门插值/多目标 → GP 连续匹配 → 真多目标 Pareto + knee + GP σ 补测点推荐 → 补测策略对比（σ/EI/随机/不补测，闭环模拟验证补测收益约 6.2×；62 项测试，`docs/design/selection_matching_v0.1.md`、`selection_matching_v0.2.md`、`selection_matching_v0.3.md`、`selection_matching_v0.4.md`、`selection_strategies_v0.5.md`）；三入口 `--require-measured` 守门（D038）；剩余：成本项（需真实产品参数/价格表）、把 EI/σ 输出接入实机补测清单、实机数据重跑；
5. ✅ 软著材料（`软件说明书_V1.0.md`、自动生成的源代码页 347 页、复现包 SHA256 清单 250 文件）已完成（33 项工具测试，`docs/softcopyright/`）；剩余：按登记系统模板转换格式与学校审核。
5b. ✅ 静态砝码标定拟合工具 v0.1（`calibration_fit.py`：读数 CSV → `simulated:false` 标定 JSON，k/b + R²/重复性/迟滞指标 + warnings，15 项测试，D032）已完成；M0.4 实测读数到位后直接生成 MEASURED 标定并重跑流水线。
5c. ✅ MEASURED 通路就绪门禁 v0.1（`measured_readiness.py`：检查 meta/标定/表头/必需通道/桨径，SIM 输入拒绝演练通过，10 项测试，D035）；M0.4 后先过门禁再进 MEASURED 通路。
5d. ✅ 联动守门（`compute_efficiency --require-measured`：复用同一组检查，SIM/合成/非 serial 拒绝，默认关闭，5 项测试，D036）已完成；剩余：CI 步骤与选型入口同类守门。
5e. ✅ 汇总守门（`aggregate_efficiency --require-measured`：仅接受 `MEASURED`/`serial` 汇总，`--dir data\metadata` 演练拒绝 17 个 SIM run、exit 2，4 项测试，D037）已完成；剩余：MEASURED e2e 演练。
5f. ✅ 选型入口守门 + 一键 CI（三入口 `--require-measured`，2/1/1 项拒绝测试；`code/tools/run_all_tests.py` 六套 203 项一键合跑、全绿 exit 0，D038）已完成；剩余：把 CI 接入提交前检查清单与后续 e2e 演练。
5g. ✅ 提交前一致性检查（`check_release.py`：六套测试 + 复现包清单逐文件 SHA256 + 软著源代码页新鲜度，全部通过 exit 0；真实仓库演练 312 项测试 / 250 文件 / 82 源文件 347 页全 OK，7 项测试，D039）已完成；剩余：纳入每次提交前的固定动作与后续 MEASURED e2e 演练。
5h. ✅ MEASURED 端到端演练（`measured_e2e_drill.py`：临时合成夹具串起门禁 → 流水线 → 汇总 → 选型 + SIM 负向对照，6 项检查全通过；仓库 `data/` 无残留；5 项测试，D040）已完成；剩余：M0.4 真实读数后重跑并归档演练报告。

**硬件与数据（线下推进，按启动计划里程碑）**

6. 11-21 前冻结被测对象与场地电源条件（`docs/inputs/被测对象与实验室条件确认单_v0.1.md`）；
7. 11-24 台架草图 v0.1 / 采集方案 v0.1 评审，11-25 前完成 BOM v0.1 + 3 家询价；
8. 11-26 至 11-27 搭最小采集链路 + 静态砝码读数（双人），11-30 第一阶段复盘；
9. 12 月初下单，12 月完成台架搭建与采集链路联调，进入部件测试。
