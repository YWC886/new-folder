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
