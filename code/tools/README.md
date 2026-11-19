# code/tools —— 软著与复现材料生成器（v0.1）

把仓库内容稳定导出为软件著作权登记材料与复现包清单，避免手工复制代码造成版本漂移。

| 文件 | 作用 |
| --- | --- |
| `source_pages.py` | 收集 `code/{acquisition,processing,simulation,selection,reference,tools}/*.py`，按路径排序、连续行号、每页 50 行生成「源代码页」，并输出清单 JSON（文件、行数、页数、SHA256） |
| `build_manifest.py` | 为复现包生成 SHA256 清单 CSV（收录 code/、docs/、data/reference/、data/processed/ 下的文本产物与根目录 md/txt；排除图片/Office/PDF/zip、`work/`、`__pycache__`、>2 MB 文件） |
| `test_tools.py` | 10 项测试：分页、行号、页眉、清单字段、SHA256、覆盖保护、真实仓库收集 |

## 用法

```powershell
# 源代码页 + 清单（输出到 docs/softcopyright/build/）
py -3.12 code\tools\source_pages.py --out-dir docs\softcopyright\build --overwrite

# 复现包 SHA256 清单
py -3.12 code\tools\build_manifest.py --output data\processed\release_manifest_v0.1.csv --overwrite

# 测试
py -3.12 -m unittest discover -s code\tools -p "test_*.py" -v
```

当前规模：34 个源文件、9,491 行 → 190 页（每页 50 行）；复现包清单收录 127 个文件、约 7.5 MiB。
软著提交一般取前 30 页 + 后 30 页（不足 60 页交全部）。

## 约定

- 产物可重复生成（`--overwrite` 显式覆盖）；`build/` 与清单 CSV 为生成物。
- 清单只做完整性校验，不含 `work/pylibs` 依赖与大体积原始 CSV。
- UIUC 参考数据仅镜像小样本，引用要求见 `docs/softcopyright/复现包清单_V1.0.md`。
- 所有 SIM/REFERENCE 结果不得作为实验结论；软著版本 V1.0 对应 2026-11-19 代码状态。
