# 开题答辩 PPT v0.2 更新方案 _DefensePPTv0.2Plan_v0.1

基于 `开题答辩PPT_v0.1.pptx`（17 页 / 6 图）与新增材料。

## 1. 拟新增/调整

| 动作 | 页 | 内容 | 素材 |
|---|---|---|---|
| 新增 | 6a | 开题答辩要点（一页纸浓缩：3 问 + 边界 + 3 件事） | `开题答辩要点_DefenseKeyPoints_v0.1` |
| 新增 | 18 | Q&A 备用页（8 问速答表） | `答辩Q与A备用页_DefenseQandA_v0.1` |
| 新增 | 19 | 电调效率测点 P1–P4 示意 | `esc_measurement_v0.1.png` |
| 调整 | 13 | 已有基础：281 项测试 / 67 源文件 / 321 页 | `阶段总结_StageSummary_r90_v0.1` |
| 备注 | 全部 | 加演讲备注（逐页讲稿句） | `开题试讲讲稿_DefenseSpeechScript_v0.1` |

## 2. 制作约束

- 使用 `code/tools/build_proposal_defense_ppt.py` 的页模板追加，保持字体/配色一致；
- PPT 若被 PowerPoint 占用，脚本自动 fallback 生成 `_新.pptx`（R63 经验）；
- 完成后用 python-pptx 校验：页数、每页标题非空、图片数 ≥7、无空文本框；
- 生成后 present，并更新 `docs/规划/` 索引与材料清单。

## 3. 时间安排

1. R97–R98：方案与脚本参数确认（本轮完成方案）；
2. R99：生成 v0.2 并校验；
3. R100 里程碑：试讲计时（8–10 分钟）+ 反馈修订清单。