# 答辩/结题 PPT 大纲 v0.1（16 页）

> 用途：把现有材料映射到答辩页；数据引用一律标注 SIM/REFERENCE/MEASURED。素材路径见 `docs/规划/结题材料总目录_v0.1.md`。

| 页 | 标题 | 内容要点 | 素材 |
|---|---|---|---|
| 1 | 封面 | 项目名、团队、指导教师、日期 | — |
| 2 | 问题与目标 | 巡检场景"选桨/选电压最省电"；效率地图目标 | 论文 §1 |
| 3 | 研究现状与缺口 | 部件表征→地图优化→缺闭环（方法演进图） | `paper_method_evolution_v0.1.png` |
| 4 | 技术路线总览 | 六阶段甘特 + S0–S5 门禁 | `plan_gantt_v0.1.png` |
| 5 | 台架与采集 | 单轴台架、传感器、ADS1256/串口协议 | `docs/design/bench_v0.1.md`、`daq_v0.1.md` |
| 6 | 标定与不确定度 | M1 砝码双人标定、U(k=2) 预算 | SOP、`calibration_fit_v0.1.md` |
| 7 | 效率口径 | η_em / FM / η_sys 三定义与边界 | 论文 §3、D012 |
| 8 | 数据与地图 | DoE 排程、GP 平滑面 + σ | `efficiency_map_v0.4.png` |
| 9 | 选型与补测 | 多目标 Pareto、σ/EI 补测收益 | `selection_v0.4.png`、`bo_strategies_v0.5.png` |
| 10 | 公开数据对标 | UIUC 8 桨/112 点、先验反推 | `uiuc_benchmark_v0.2.png` |
| 11 | 仿真与热 | 电池压降、单/双节点热网络 | `pack_model_impact_v0.2.png`、`two_node_thermal_v0.4.png` |
| 12 | 当前成果（原型） | 281 测试、60 文件、312 页软著、Excel/Word | Excel「10_材料总目录」 |
| 13 | 风险与对策 | 采购/标定/温升/外推/进度 | 论文 §5.2 |
| 14 | 实测计划 | M0.4 起 135 工况排程与替换表 | 论文 §4.1、`design_matrix_v0.2.md` |
| 15 | 预期成果 | 台架/数据集/地图/工具/论文 | 论文 §5.1 |
| 16 | 致谢/Q&A | 导师与实验室支持 | — |

## 制作说明

- 图件统一从 `data/processed/figures/` 取；表格优先用 Excel 12 表截图；
- 每页底部保留数据边界标注（SIM/REFERENCE/MEASURED）；
- 下一步可用 ppt-master 技能生成可编辑 PPTX。
