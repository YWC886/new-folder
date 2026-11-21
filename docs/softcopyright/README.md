# 软著与复现材料（v1.0）

本目录存放**软件著作权登记**与**复现包**相关材料，由脚本从仓库内容生成/维护，不手工复制代码。

> 软件全称：**多旋翼动力系统效率地图构建与匹配优化软件**
> 版本：**V1.0**（对应仓库 2026-11-21 状态，代码测试 277 项全绿）
> 状态：材料初稿，未提交登记；学校/著作权人信息待项目组确认后补填。

## 1. 目录

| 文件 | 说明 |
| --- | --- |
| `README.md` | 本文件：材料清单、生成命令、提交与复现指引 |
| `软件说明书_V1.0.md` | 软著说明书（功能、技术特点、运行环境、测试验证、权利声明） |
| `复现包清单_V1.0.md` | 复现包结构、收录文件、校验方式、排除项、引用与许可 |
| `build/源代码页_V1.0.txt` | 自动生成：全部源码按每页 50 行连续编号，共 **301 页**（约 817 KB） |
| `build/源代码清单_V1.0.json` | 自动生成：源文件列表、行数、SHA256、总页数 |
| `build/源文件目录_V1.0.txt` | 自动生成：单行一文件的目录（便于快速核对） |

**提交登记时**：从 `build/源代码页_V1.0.txt` 取**前 30 页 + 后 30 页**（不足 60 页交全部），
转 PDF/打印时保留页眉「软件名称/版本/页码」。说明书按登记系统模板调整格式即可。

## 2. 生成命令（可重复执行）

```powershell
# 源代码页 + 清单 JSON（--overwrite 覆盖旧产物）
py -3.12 code\tools\source_pages.py --out-dir docs\softcopyright\build --overwrite

# 复现包 SHA256 清单 CSV
py -3.12 code\tools\build_manifest.py --output data\processed\release_manifest_v0.1.csv --overwrite
```

两脚本规则：

- 源代码页：按 `code/{acquisition,processing,simulation,selection,reference,tools}/*.py` 收集，
  路径排序、连续行号、每页 50 行，页眉含软件名/版本/页码；清单 JSON 记录每个文件的 SHA256 与行数。
- 清单：收录 `code/`、`docs/`、`data/reference/`、`data/processed/` 下 ≤2 MB 的文本产物与根目录
  `*.md`/`*.txt`；排除图片/Office/PDF/zip、`work/`、`__pycache__`。

## 3. 复现与校验（最小步骤）

```powershell
# 1) 环境自检（Python 3.12 + 依赖）
$env:PYTHONIOENCODING = 'utf-8'
py -3.12 work\env\check_env.py

# 2) 全部分模块测试（当前 277 项）
foreach ($d in 'acquisition','processing','simulation','selection','reference','tools') {
    py -3.12 -m unittest discover -s "code\$d" -p "test_*.py"
}

# 3) 复现包完整性（对照清单抽查）
py -3.12 -c "import csv,hashlib,pathlib; rows=list(csv.DictReader(open('data/processed/release_manifest_v0.1.csv',encoding='utf-8'))); bad=[r['rel_path'] for r in rows if hashlib.sha256(pathlib.Path(r['rel_path']).read_bytes()).hexdigest()!=r['sha256']]; print('files:',len(rows),'mismatch:',bad[:5])"
```

## 4. 重要声明

- 仓库内全部 **SIM（仿真合成）** 与 **REFERENCE（UIUC 公开风洞数据）** 产物均**不是实验测量**，
  不得作为选型结论、论文结论或实机性能依据；实机验证待台架搭建与砝码标定后另行开展。
- UIUC Propeller Database 数据仅科研/教学用途，引用须注明来源（见 `复现包清单_V1.0.md` §4）。
- 本软件为大学生创新创业训练计划项目阶段性成果，未发表、未转让；正式登记前需经指导教师与学校审核。

## 5. 版本与变更

- 2026-11-19 v1.0：首版材料（说明书、源代码页生成器、复现包清单生成器）；对应代码测试 91 项。
- 2026-11-19 v1.0 重生成：随 v0.4 GP / 选型 v0.3 更新，源文件 27 个 / 6,941 行 / 139 页，清单 97 文件，全量 117 项测试。
- 2026-11-19 v1.0 重生成（v0.4）：随选型 v0.4 更新，源文件 29 个 / 7,756 行 / 156 页，清单 102 文件，全量 126 项测试。
- 2026-11-19 v1.0 重生成（v0.4 仿真）：随双节点热网络更新，源文件 31 个 / 8,328 行 / 167 页，清单 106 文件，全量 134 项测试。
- 2026-11-19 v1.0 重生成（多桨对标 + 调研集成）：随 UIUC 多桨型对标 v0.2 与 `docs/research/`（文献/标准/竞赛/项目深读）更新，源文件 32 个 / 9,004 行 / 181 页，清单 124 文件，全量 143 项测试。
- 2026-11-19 v1.0 重生成（标定拟合 v0.1）：新增 `code/processing/calibration_fit.py` + 测试 + 设计文档，源文件 34 个 / 9,491 行 / 190 页，清单 127 文件，全量 158 项测试。

- 2026-11-19 v1.0 重生成（逐桨反推 v0.3）：新增 `code/reference/calibrate_uiuc.py` + 测试 + 设计文档；源文件 36 个 / 10,025 行 / 201 页，清单 131 文件，全量 168 项测试（参考 28）。
- 2026-11-19 v1.0 重生成（bootstrap 不确定度 v0.1）：新增 `code/reference/bootstrap_priors.py` + 测试 + 设计文档；源文件 40 个 / 11,016 行 / 221 页，清单 138 文件，全量 188 项测试（处理 63）。
- 2026-11-19 v1.0 重生成（联动守门 v0.5）：新增 `compute_efficiency --require-measured` 与 `test_require_measured.py`；源文件 41 个 / 11,204 行 / 225 页，清单 139 文件，全量 193 项测试（处理 68）。
- 2026-11-19 v1.0 重生成（汇总守门 v0.6）：新增 `aggregate_efficiency --require-measured`；源文件 41 个 / 11,264 行 / 226 页，清单 139 文件，全量 197 项测试（处理 72）。
- 2026-11-19 v1.0 重生成（选型守门 + CI v0.7）：三入口 `--require-measured` 与 `run_all_tests.py`；源文件 42 个 / 11,512 行 / 231 页，清单 140 文件，全量 203 项测试（选型 47、工具 12）。
- 2026-11-19 v1.0 重生成（MEASURED 门禁 v0.1）：新增 `code/processing/measured_readiness.py` + 测试 + 设计文档。
- 2026-11-19 v1.0 重生成（提交前检查 v0.8）：新增 `code/tools/check_release.py` + `test_check_release.py`；源文件 44 个 / 11,833 行 / 237 页，清单 142 文件，全量 210 项测试（工具 19）。
- 2026-11-19 v1.0 重生成（MEASURED 演练 v0.9）：新增 `code/tools/measured_e2e_drill.py` + `test_measured_e2e_drill.py`；源文件 46 个 / 12,186 行 / **244 页**，清单 **145 文件**，全量 **215 项测试（工具 24）**，D040。
- 2026-11-19 v1.0 重生成（选型 v0.5 补测策略）：新增 `code/selection/bo_suggest.py` + `test_bo_suggest.py` 与设计文档；源文件 48 个 / 12,809 行 / **257 页**，清单 **149 文件**，全量 **230 项测试（选型 62）**，D041。
- 2026-11-20 文件归档整理：根目录申报/规划/参考文件归档到 `docs/申报/`（申报表、4 份附件 PDF、清单、预算）、`docs/规划/`、`docs/参考/`；清单重生成 **153 文件**（root 1 / docs 54 / code 54 / data_processed 35 / data_reference 9），全量 230 项测试不变。
- 2026-11-21 申报书改版对比分析：新增 `docs/规划/申报书对比分析与优化研究路径_v0.1.md`（md 入清单；docx/pdf 不计数）；清单重生成 **154 文件 / 8,103.7 KiB**（root 1 / docs 55 / code 54 / data_processed 35 / data_reference 9），全量 230 项测试不变；preflight 全通过。

## 更新记录

- 2026-11-21 prior-profile 对照 v0.4：新增 `code/reference/prior_profile.py` + `test_prior_profile.py` 与设计文档；参考 38→48 项测试（全仓 230→240）、源文件 48→50、行数 12,809→13,194、页数 257→264、清单 154→158 文件（约 8.0 MiB）。
- 2026-11-21 多工况试验排程 v0.1：新增 `code/processing/design_matrix.py` + 测试；处理 72→82 项（全仓 240→250）、源文件 50→52、行数 13,194→13,613、页数 264→273、清单 158→162 文件。
- 2026-11-21 Reynolds 修正负结果 v0.5 + 申报表 v3 草稿：新增 `code/reference/re_correction.py` + 测试（参考 48→61 项，全仓 250→263）；源文件 52→54、行数 13,613→15,022、页数 273→284、清单 162→171 文件（约 8.2 MiB）；`docs/申报/申报表/` 增加 v3 草稿 docx 与改动说明（docx 不计入清单）。

- 2026-11-21 试验排程 v0.2（target-thrust inversion / randomize）+ Round 24 收尾重生成：54 源文件 / 15,022 行 / 301 页；清单 171 文件 / 约 8.2 MiB；全量 277 项测试。
