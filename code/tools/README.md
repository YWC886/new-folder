# code/tools —— 软著、复现材料与 CI（v0.2）

把仓库内容稳定导出为软件著作权登记材料与复现包清单，避免手工复制代码造成版本漂移；并提供六套测试的一键 CI 入口。

| 文件 | 作用 |
| --- | --- |
| `source_pages.py` | 收集 `code/{acquisition,processing,simulation,selection,reference,tools}/*.py`，按路径排序、连续行号、每页 50 行生成「源代码页」，并输出清单 JSON（文件、行数、页数、SHA256） |
| `build_manifest.py` | 为复现包生成 SHA256 清单 CSV（收录 code/、docs/、data/reference/、data/processed/ 下的文本产物与根目录 md/txt；排除图片/Office/PDF/zip、`work/`、`__pycache__`、>2 MB 文件） |
| `run_all_tests.py` | 一键运行六套子项目测试（acquisition/processing/simulation/selection/reference/tools），逐套打印 `[OK]/[FAIL]` 与总计；全部通过且 total>0 时 exit 0，否则 exit 1 |
| `test_tools.py` | 12 项测试：分页、行号、页眉、清单字段、SHA256、覆盖保护、真实仓库收集、CI 脚本成功/失败退出码 |

## 用法

```powershell
# 源代码页 + 清单（输出到 docs/softcopyright/build/）
py -3.12 code\tools\source_pages.py --out-dir docs\softcopyright\build --overwrite

# 复现包 SHA256 清单
py -3.12 code\tools\build_manifest.py --output data\processed\release_manifest_v0.1.csv --overwrite

# 一键 CI：六套测试合跑（全通过 exit 0）
py -3.12 code\tools\run_all_tests.py

# 本目录测试
py -3.12 -m unittest discover -s code\tools -p "test_*.py" -v
```

当前规模：42 个源文件、11,512 行 → 231 页（每页 50 行）；复现包清单收录 140 个文件、约 7.7 MiB。
软著提交一般取前 30 页 + 后 30 页（不足 60 页交全部）。

## 约定

- 产物可重复生成（`--overwrite` 显式覆盖）；`build/` 与清单 CSV 为生成物。
- 清单只做完整性校验，不含 `work/pylibs` 依赖与大体积原始 CSV。
- UIUC 参考数据仅镜像小样本，引用要求见 `docs/softcopyright/复现包清单_V1.0.md`。
- 所有 SIM/REFERENCE 结果不得作为实验结论；软著版本 V1.0 对应 2026-11-19 代码状态。
