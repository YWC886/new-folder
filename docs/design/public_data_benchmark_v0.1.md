# 公开数据对标 v0.1 —— UIUC Propeller Database

版本：v0.1（草稿）｜日期：2026-11-19｜负责人：D｜状态：草稿
关联：`code/reference/`、`data/reference/`、`docs/decisions.md` D023

## 1. 目的与边界

用 UIUC Propeller Database 的**真实风洞测量**（静态 CT/CP）检查仿真模型
（`propulsion_model` v0.1 通用参数先验）的量级与趋势是否合理，量化"通用参数
先验"相对真实数据的偏差，为后续模型校核与选型提供参照。

边界：

- 参考数据是**真实风洞测量**，模型是参数化仿真，二者不是"验证通过"关系；
- 对标的桨为 APC 10x7E（10 英寸、7 英寸螺距），而模型参数（C_T0/C_P0/幂律指数）
  为文献量级 + 工程取值，不含桨距/翼型信息，所以比较的是**同量级/趋势**，
  不是同一桨的精确复现；
- 对标结果一律标 `REFERENCE`，不得混入实测/合成数据，不得据此宣称本项目的精度；
- 本轮只做静态（RPM 扫描）数据；风速扫描（J、C_T、C_P、η）留待 v0.2。

## 2. 数据来源与许可

| 项目 | 内容 |
| --- | --- |
| 数据库 | UIUC Propeller Database, Vols 1–4 |
| 主页 | <https://m-selig.ae.illinois.edu/props/propDB.html> |
| 完整库下载 | <https://m-selig.ae.illinois.edu/props/download/UIUC-propDB.zip>（md5 `a41e484f1fd0fb6ff80b76e27410808b`） |
| 本轮样本 | Vol.1 APC 10x7E 静态：<https://m-selig.ae.illinois.edu/props/volume-1/data/apce_10x7_static_pg0811.txt> |
| 引用 | J.B. Brandt, R.W. Deters, G.K. Ananda, O.D. Dantsker, and M.S. Selig (date downloaded), *UIUC Propeller Database, Vols 1-4*, University of Illinois at Urbana-Champaign |
| 许可 | 科研/教学用途；引用时注明 UIUC；再分发请先联系 UIUC（webmaster@illinois.edu） |

本仓库只镜像**一个 16 点样本**（`data/reference/uiuc/apce_10x7_static_pg0811.txt`，
含来源与引用注释）用于解析器/对标脚本开发与测试；不镜像完整数据库。
使用约定见 `data/reference/README.md`。

## 3. 数据格式

静态数据文件为 UTF-8 文本，支持 `#` 注释与空行，表头：

```
RPM    CT       CP
1975   0.0981   0.0547
...
```

- `RPM`：转速 [r/min]；`CT`、`CP`：静态推力/功率系数 [-]
- 解析器：`code/reference/uiuc_propdb.py::load_static()`，逐行校验 `RPM>0`、`CT/CP≥0`，
  输出 `rpm / ct / cp / n_rps=rpm/60`

## 4. 对标协议

1. 对 UIUC 每个 RPM 点，用模型公式计算同转速下的系数：
   `C_T = C_T0 · (n/n_ref)^a_T`、`C_P = C_P0 · (n/n_ref)^a_P`，其中
   `n = RPM/60`，`n_ref = 100 r/s`（模型 v0.1 参数：C_T0=0.110、C_P0=0.0450、
   a_T=−0.02、a_P=−0.035）；
2. 逐点相对误差 `ct_rel_err = (ct_model − ct_ref)/ct_ref`，`cp_rel_err` 同理；
3. 统计均值/最大绝对相对误差，输出 CSV 与双面板对比图；
4. 只比较**同转速下的系数**，不换算推力/扭矩（避免引入空气密度与桨径假设）。

复现命令：

```powershell
py -3.12 code\reference\uiuc_propdb.py --input data\reference\uiuc\apce_10x7_static_pg0811.txt
py -3.12 code\reference\benchmark_uiuc.py --reference data\reference\uiuc\apce_10x7_static_pg0811.txt --overwrite
```

产物：`data/processed/uiuc_benchmark_v0.1.csv`（9 列逐点数据）、
`data/processed/figures/uiuc_benchmark_v0.1.png`（CT/CP 双面板）。

## 5. 结果（2026-11-19 实跑）

样本：APC 10x7E 静态，16 点，RPM 1975–6542。

| 指标 | 模型均值 | UIUC 范围 | 相对误差均值 | 相对误差最大 |
| --- | --- | --- | --- | --- |
| C_T | 0.110（0.1132→0.1097） | 0.0981–0.1139 | **6.14%** | 14.65% |
| C_P | 0.045（0.0469→0.0447） | 0.0512–0.0547 | **13.83%** | 14.95% |

观察：

- **C_P 被系统性低估约 13–15%**：模型 C_P0=0.0450 明显低于 APC 10x7E 静态
  实测 0.051–0.055，说明通用参数先验偏"高效"，会让仿真效率偏高；
- **C_T 趋势相反**：UIUC 实测 C_T 随 RPM 上升（0.098→0.114，并在 5.4–5.6 krpm
  附近有台阶），模型用负指数（−0.02）呈缓慢下降；低转速端模型高估约 14.7%，
  高转速端低估约 3.7%；
- 二者量级同阶，说明模型结构可用，但**先验参数需要按目标桨型标定/校核**，
  不能直接用通用参数下"效率高低"的具体结论。

## 6. 质量门槛与测试

- `code/reference/test_reference.py` 共 9 项：解析（镜像样本/注释空行/缺表头/非数值）、
  摘要统计、模型系数公式一致性、对标统计合理区间、CSV 字段与覆盖保护、PNG 输出与覆盖保护；
- 运行：`py -3.12 -m unittest discover -s code\reference -p "test_*.py" -v` → Ran 9 tests OK。

## 7. 限制与待办（v0.2）

1. 只做了静态数据；风速扫描（J/CT/CP/η）需要新增解析器与对标脚本；
2. 只对标一个桨（APC 10x7E），需扩展到多桨型（不同直径/螺距）看参数敏感性；
3. 未做雷诺数/马赫数修正（UIUC 数据含修正说明，需按原始报告核对）；
4. 模型当前无桨距/翼型参数，无法做到同桨精确复现；v0.2 可引入 C_T0/C_P0 拟合
   （给定目标桨的实测曲线反推先验），并明确"先验 vs 标定后"两档；
5. 完整数据库（约 GB 级）不入库，按需下载后本地比对。

## 8. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 首个版本：UIUC 样本入库、解析器、对标脚本、9 项测试、结果与限制 |
