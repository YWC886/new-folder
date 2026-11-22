# 文件命名规范 v0.1（中英双语）

- 生效：2026-11-22；适用范围：此后**新生成**的文件（已有文件暂不改名，避免引用/清单连锁）
- 规则：`中文短名_EnglishName_v版本号.扩展名`
  - 中文短名：与内容对应的 2–8 字，如「申报书对比分析」
  - EnglishName：简短英文词组，首字母大写驼峰，如 `ProposalComparison`
  - 版本号：`v0.1`、`v1.0` 等；日期戳用于一次性导出物（如 `_20261121`）
- 示例：
  - `申报书对比分析_ProposalComparison_v0.1.md`
  - `电调效率测量_ESCMeasurement_v0.1.docx`
  - `开题答辩_ProposalDefense_v0.1.pptx`
- 例外：代码脚本沿用现有 `snake_case.py`；`data/processed` 下由脚本自动生成的 CSV/JSON 保持程序内命名（避免破坏流水线）。
- 后续如需对已有高价值交付物批量改名（方案 B），先重命名 + 全仓引用替换 + 重建清单，再提交。
