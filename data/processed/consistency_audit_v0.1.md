# 口径与引用一致性审计 v0.1

文件数：109；HARD 0；SOFT 75

## HARD（项目自述语境禁词，必须改）

- 无

## SOFT（文献语境/断链，复核）

- docs\decisions.md:31 [broken-ref] code/docs/data
- docs\design\calibration_fit_v0.1.md:16 [broken-ref] data/metadata/calib_SIM_
- docs\design\expansion_E1_multi_prop_v0.1.md:27 [broken-ref] data/processed/design_matrix_E1.csv
- docs\design\expansion_E1_multi_prop_v0.1.md:27 [broken-ref] data/metadata/design_matrix_E1.summary.json
- docs\design\geometry_prior_v0.1.md:38 [跨桨型] 但不足以跨桨型泛化；
- docs\design\prior_profile_v0.1.md:68 [跨桨型] - 样本内对照：提升倍数不代表泛化能力；跨桨型/跨系列外推仍须实测；
- docs\design\processing_pipeline_v0.1.md:59 [broken-ref] data/metadata/calib_
- docs\design\public_data_benchmark_v0.1.md:28 [broken-ref] data/apce_10x7_static_pg0811.txt
- docs\design\数据采集方案_DAQ_v0.1.md:57 [broken-ref] data/metadata/calib_
- docs\plan\Round20推进计划_UQ与DoE口径统一_v0.1.md:32 [broken-ref] data/processed/figures/selection_uq_consistency_v0.1.png
- docs\plan\Round20推进计划_UQ与DoE口径统一_v0.1.md:34 [broken-ref] docs/design/uq_selection_consistency_v0.1.md
- docs\plan\v4口径四线核对表_V4ConsistencyCrossCheck_v0.1.md:10 [更换桨型] | 申报附件 01（前期基础摘要） | 未提"更换桨型"；UIUC 8 桨仅作 REFERENCE 方法验证 | 测量与解耦 + 建模与应用（见附件 04/说明） | 保留并加注「非项目主线；v4 口径为同一桨型」 | ✅ 一致 |
- docs\plan\v4口径四线核对表_V4ConsistencyCrossCheck_v0.1.md:14 [多桨对比] | 开题答辩 PPT v0.2 | 「同一桨型·电压对比」页；地图页「电压×油门」 | 两条关键问题已写入 | 多桨对比页已删除 | ✅ 一致 |
- docs\plan\v5治理总结与移交_GovernanceHandover_v0.1.md:28 [broken-ref] docs/research/paper_method_draft_v0.1.md/.docx
- docs\plan\会话记忆交接_MemoryPrimer_v1.0.md:23 [多桨对比] - **禁词审计**：项目自述禁 `多桨对比/跨桨型/更换桨型/多套硬件`（v4 口径=同一桨型、不换桨型）；`audit_consistency.py` 会扫描（HARD>0 失败）
- docs\plan\会话记忆交接_MemoryPrimer_v1.0.md:23 [跨桨型] - **禁词审计**：项目自述禁 `多桨对比/跨桨型/更换桨型/多套硬件`（v4 口径=同一桨型、不换桨型）；`audit_consistency.py` 会扫描（HARD>0 失败）
- docs\plan\会话记忆交接_MemoryPrimer_v1.0.md:23 [更换桨型] - **禁词审计**：项目自述禁 `多桨对比/跨桨型/更换桨型/多套硬件`（v4 口径=同一桨型、不换桨型）；`audit_consistency.py` 会扫描（HARD>0 失败）
- docs\plan\会话记忆交接_MemoryPrimer_v1.0.md:23 [多套硬件] - **禁词审计**：项目自述禁 `多桨对比/跨桨型/更换桨型/多套硬件`（v4 口径=同一桨型、不换桨型）；`audit_consistency.py` 会扫描（HARD>0 失败）
- docs\plan\会话记忆交接_MemoryPrimer_v1.0.md:66 [broken-ref] docs/申报/第2-5步填写包_...md
- docs\plan\会话记忆交接_MemoryPrimer_v1.0.md:68 [broken-ref] docs/inputs/M0.4启动包_...md
- docs\plan\会话记忆交接_MemoryPrimer_v1.1.md:23 [多桨对比] - **禁词审计**：项目自述禁 `多桨对比/跨桨型/更换桨型/多套硬件`（v4 口径=同一桨型、不换桨型）；`audit_consistency.py` HARD>0 即失败
- docs\plan\会话记忆交接_MemoryPrimer_v1.1.md:23 [跨桨型] - **禁词审计**：项目自述禁 `多桨对比/跨桨型/更换桨型/多套硬件`（v4 口径=同一桨型、不换桨型）；`audit_consistency.py` HARD>0 即失败
- docs\plan\会话记忆交接_MemoryPrimer_v1.1.md:23 [更换桨型] - **禁词审计**：项目自述禁 `多桨对比/跨桨型/更换桨型/多套硬件`（v4 口径=同一桨型、不换桨型）；`audit_consistency.py` HARD>0 即失败
- docs\plan\会话记忆交接_MemoryPrimer_v1.1.md:23 [多套硬件] - **禁词审计**：项目自述禁 `多桨对比/跨桨型/更换桨型/多套硬件`（v4 口径=同一桨型、不换桨型）；`audit_consistency.py` HARD>0 即失败
- docs\plan\会话记忆交接_MemoryPrimer_v1.1.md:68 [broken-ref] docs/申报/第2-5步填写包_
- docs\plan\会话记忆交接_MemoryPrimer_v1.1.md:70 [broken-ref] docs/inputs/M0.4启动包_
- docs\plan\成果盘点与差距_GapReview_v0.1.md:30 [broken-ref] docs/README
- docs\plan\成果盘点与差距_GapReview_v0.1.md:33 [多桨对比] 9. 所有材料需机器可查的 SIM/REFERENCE/MEASURED 标注与“禁词”扫描（多桨对比/跨桨型/更换桨型/节能宣称等）。
- docs\plan\成果盘点与差距_GapReview_v0.1.md:33 [跨桨型] 9. 所有材料需机器可查的 SIM/REFERENCE/MEASURED 标注与“禁词”扫描（多桨对比/跨桨型/更换桨型/节能宣称等）。
- docs\plan\成果盘点与差距_GapReview_v0.1.md:33 [更换桨型] 9. 所有材料需机器可查的 SIM/REFERENCE/MEASURED 标注与“禁词”扫描（多桨对比/跨桨型/更换桨型/节能宣称等）。
- docs\plan\拓展方向_ExpansionDirections_v0.1.md:49 [broken-ref] code/processing/compare_reference.py
- docs\plan\拓展方向_ExpansionDirections_v0.1.md:52 [broken-ref] data/processed/uiuc_benchmark_v0.1
- docs\plan\拓展方向_ExpansionDirections_v0.1.md:87 [broken-ref] docs/README
- docs\plan\自动化轮次日志_AutomationRoundsLog_R81-R90_v0.1.md:6 [broken-ref] docs/参考/无人机电调_ESCLearningGuide_v0.1.md/.docx
- docs\plan\阶段总结_StageSummary_r40_deepening.md:11 [broken-ref] docs/README
- docs\plan\阶段总结_StageSummary_r90_v0.1.md:9 [broken-ref] docs/参考/无人机电调_ESCLearningGuide_v0.1.md/.docx
- docs\plan\阶段总结_StageSummary_r90_v0.1.md:9 [broken-ref] docs/design/电调效率测量_ESCMeasurement_v0.1.md/.docx
- docs\plan\阶段总结_StageSummary_r90_v0.1.md:12 [broken-ref] docs/plan/开题答辩要点_DefenseKeyPoints_v0.1.md/.docx
- docs\procurement\bom_v0.1.md:75 [broken-ref] docs/procurement/到货验收记录.md
- docs\procurement\询价单模板.md:59 [broken-ref] docs/procurement/quotes/
- docs\README.md:146 [broken-ref] docs/design/figs/
- docs\research\project_deep_dive_v0.1.md:126 [broken-ref] docs/README
- docs\research\project_deep_dive_v0.1.md:156 [broken-ref] data/processed/efficiency_map_
- docs\research\project_deep_dive_v0.1.md:227 [broken-ref] code/daq/
- docs\research\project_deep_dive_v0.1.md:252 [broken-ref] docs/design/bench_v0.2.md
- docs\research\project_deep_dive_v0.1.md:255 [broken-ref] docs/test/静态砝码读数记录_v1.0.md
- docs\research\project_deep_dive_v0.1.md:353 [broken-ref] code/daq/
- docs\softcopyright\复现包清单_V1.0.md:73 [broken-ref] docs/design/simulation_model_v
- docs\team\task_division_3person_v0.1.md:49 [broken-ref] docs/design/bench
- docs\team\task_division_3person_v0.1.md:50 [broken-ref] docs/design/daq
- docs\test\试验执行SOP_v0.1.md:80 [broken-ref] data/exports/项目成果总览_
- docs\test\静态砝码读数记录_v0.1.md:7 [broken-ref] data/metadata/calib_
- docs\test\静态砝码读数记录_v0.1.md:76 [broken-ref] data/metadata/calib_
- docs\申报\申报表\改动说明_第四五六部分.md:12 [更换桨型] | C8 | "前面有电调这里怎么没有了"；不涉及多套硬件 | §四研究内容 1/2/3 明确"电机 + 电调 + 螺旋桨"单套硬件；§四 3 与 §六（三）写入电调输入/输出电功率单独记录；全文删"多套硬件/更换桨型"表述 |
- docs\申报\申报表\改动说明_第四五六部分.md:12 [多套硬件] | C8 | "前面有电调这里怎么没有了"；不涉及多套硬件 | §四研究内容 1/2/3 明确"电机 + 电调 + 螺旋桨"单套硬件；§四 3 与 §六（三）写入电调输入/输出电功率单独记录；全文删"多套硬件/更换桨型"表述 |
- docs\申报\申报表\改动说明_第四五六部分.md:17 [多套硬件] | C22 | "不涉及多套硬件"（桨型相关） | §四 6 应用示例改为比较"供电电压与运行点"，不再写"比较不同桨型"；§四 5 保留"按桨型分图"仅作地图组织方式说明 |
- docs\申报\申报表\改动说明_第四五六部分.md:38 [多套硬件] 3. 确认 §四 6 应用示例"供电电压 + 运行点"的表述是否符合导师"不涉及多套硬件"的要求；
- docs\申报\申报表\改动说明_第四五六部分.md:55 [跨桨型] | C22 | 效率地图由“按桨型分图、跨桨型比较”改为“部件/系统分别成图、同一套被测硬件内比较” |
- docs\申报\申报表\改动说明_第四五六部分.md:69 [换不同桨型] - §一 项目简介：原“更换不同桨型、逐点采集”改为“同一桨型下逐点采集”；
- docs\申报\第2-5步填写包_Sec2to5FillPack_v0.1.md:172 [多套硬件] 测量与试验设计方面，采用同一时钟源触发或多通道同步采集卡，保证电参量与力学量同步；按 GUM 方法开展测量不确定度评定；用正交试验设计压缩试验点数量，同时保证在供电电压与油门两个维度上的覆盖（三个维度均在固定电机与电调的同一套测试硬件上，通
- docs\规划\v5治理交付包_GovernanceDeliverablePack_v0.1.md:35 [broken-ref] docs/research/paper_method_draft_v0.1.md/.docx
- docs\规划\v5治理交付包_GovernanceDeliverablePack_v0.1.md:109 [更换桨型] | 申报附件 01（前期基础摘要） | 未提"更换桨型"；UIUC 8 桨仅作 REFERENCE 方法验证 | 测量与解耦 + 建模与应用（见附件 04/说明） | 保留并加注「非项目主线；v4 口径为同一桨型」 | ✅ 一致 |
- docs\规划\v5治理交付包_GovernanceDeliverablePack_v0.1.md:113 [多桨对比] | 开题答辩 PPT v0.2 | 「同一桨型·电压对比」页；地图页「电压×油门」 | 两条关键问题已写入 | 多桨对比页已删除 | ✅ 一致 |
- docs\规划\申报书对比分析与优化研究路径_v0.1.md:4 [broken-ref] docs/申报/申报表/附件3
- docs\规划\申报书对比分析与优化研究路径_v0.1.md:193 [broken-ref] docs/procurement/budget_5000_v0.1.md
- docs\规划\申报书对比分析与优化研究路径_v0.1.md:224 [broken-ref] docs/procurement/budget_5000_v0.1.md
- docs\规划\申报书对比分析与优化研究路径_v0.1.md:224 [broken-ref] docs/research/bench_tech
- docs\规划\结题材料总目录_v0.1.md:20 [broken-ref] docs/规划/申报书对比分析与优化研究路径_v0.1.md/.docx
- docs\规划\结题材料总目录_v0.1.md:21 [broken-ref] docs/规划/阶段总结_StageSummary_r40.md
- docs\规划\结题材料总目录_v0.1.md:22 [broken-ref] docs/plan/项目待办与决策清单_TODOandDecisions_v0.1.md/.docx
- docs\规划\结题材料总目录_v0.1.md:41 [broken-ref] docs/research/paper_method_draft_v0.1.md/.docx
- README.md:26 [broken-ref] data/exports/项目成果总览_
- README.md:28 [broken-ref] data/exports/项目成果总览_
- README.md:58 [broken-ref] docs/申报/申报表/附件3
- README.md:178 [broken-ref] docs/申报/申报表/附件3
