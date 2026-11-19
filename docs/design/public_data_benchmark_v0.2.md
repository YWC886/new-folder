# 公开数据对标 v0.2 —— 多桨型静态对标（UIUC Vol.1）

版本：v0.2（草稿）｜日期：2026-11-19｜负责人：D｜状态：草稿
关联：`code/reference/`、`data/reference/`、`data/processed/`、`docs/design/public_data_benchmark_v0.1.md`

## 1. 目的与边界

v0.1 只对标了 APC 10x7E 一个桨。本版把对标扩展到 **7 个桨型 / 3 个品牌 / 6 个系列**
（共 112 个静态数据点），回答三个问题：

1. 通用参数模型（`propulsion_model` 的 C_T0/C_P0/雷诺指数先验）的偏差在
   **不同桨型**上是同向、同量级，还是随桨型分化？
2. 偏差的方向与量级能否用"品牌/系列"（细薄电桨、慢飞桨、运动桨、木质桨）解释？
3. 模型与实测的 **RPM 趋势**是否一致？误差是否随工作转速漂移？

边界（与 v0.1 相同，必须保持）：

- 参考数据是 **UIUC 真实风洞测量**（`REFERENCE`），模型是参数化仿真
  （`MODEL`，通用参数 `SIM`）；二者不是"验证通过"关系，**不得宣称实验验证**；
- 只比较**同转速下的静态系数**（RPM 扫描），不换算推力/扭矩，不做风速扫描
  （J、C_T(J)、C_P(J)、η 留待后续版本）；
- 模型不含桨径/螺距/翼型信息，**同一模型曲线对所有桨型完全相同**；因此可比的是
  量级、趋势与系统性偏差，不是同桨精确复现；
- 结论只用于校准先验、指导选型，不得据此宣称本项目仿真精度；
- 结果一律标 `REFERENCE`（实测）vs `MODEL`（SIM），不得与本项目实测/合成数据混用。

本轮为 **多桨型静态** 扩展，不是 v0.1 设想的风速扫描（见 §8 待办）。

## 2. 数据来源与镜像清单

| 项目 | 内容 |
| --- | --- |
| 数据库 | UIUC Propeller Database, Vols 1–4 |
| 主页 | <https://m-selig.ae.illinois.edu/props/propDB.html> |
| Volume 1 页面 | <https://m-selig.ae.illinois.edu/props/volume-1/propDB-volume-1.html> |
| 完整库下载 | <https://m-selig.ae.illinois.edu/props/download/UIUC-propDB.zip>（md5 `a41e484f1fd0fb6ff80b76e27410808b`） |
| 下载日期 | 2026-11-19（各文件头注释已注明） |
| 引用 | J.B. Brandt, R.W. Deters, G.K. Ananda, O.D. Dantsker, and M.S. Selig (2026, date downloaded), *UIUC Propeller Database, Vols 1-4*, University of Illinois at Urbana-Champaign, Department of Aerospace Engineering |
| 许可 | 科研/教学用途；引用须注明 UIUC；再分发请先联系 UIUC（webmaster@illinois.edu） |

本版镜像 7 个静态样本（`data/reference/uiuc/`，每个 16 个 RPM 点，均带来源/引用头注释）：

| # | 镜像文件 | 桨（展示名） | 品牌 / 系列 | 直径×螺距 | 数据点 | RPM 范围 | 源 URL（`.../volume-1/data/` 下） |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `apce_11x7_static_kt0534.txt` | APC-E 11x7 | APC / E（Electric） | 11×7 in | 16 | 1966–6320 | `apce_11x7_static_kt0534.txt` |
| 2 | `apce_11x8_static_kt0517.txt` | APC-E 11x8 | APC / E（Electric） | 11×8 in | 16 | 1655–6213 | `apce_11x8_static_kt0517.txt` |
| 3 | `apcsf_10x7_static_kt0827.txt` | APC-SF 10x7 | APC / SF（Slow Flyer） | 10×7 in | 16 | 2283–5987 | `apcsf_10x7_static_kt0827.txt` |
| 4 | `apcsp_9x6_static_2532rd.txt` | APC-Sport 9x6 | APC / Sport | 9×6 in | 16 | 2564–6521 | `apcsp_9x6_static_2532rd.txt` |
| 5 | `grcp_10x6_static_rd0851.txt` | Graupner-CAM 10x6 | Graupner / CAM | 10×6 in | 16 | 1987–6592 | `grcp_10x6_static_rd0851.txt` |
| 6 | `grsn_10x7_static_rd0787.txt` | Graupner-SN 10x7 | Graupner / SN（Super Nylon） | 10×7 in | 16 | 1954–6388 | `grsn_10x7_static_rd0787.txt` |
| 7 | `ance_8.5x6_static_2848cm.txt` | Aeronaut-CE 8.5x6 | Aeronaut / CE（Carbon Electric） | 8.5×6 in | 16 | 2489–6897 | `ance_8.5x6_static_2848cm.txt` |

源 URL 完整形式：`https://m-selig.ae.illinois.edu/props/volume-1/data/<文件名>`
（Volume 1 目录页不允许列目录，只能按文件名直取；本表文件名均已逐个 HTTP 200 核对）。

v0.1 的 `apce_10x7_static_pg0811.txt` 保留不动（v0.1 产物仍可复现）。
覆盖：APC 4 个（E×2、SF、Sport）、Graupner 2 个（CAM、SN）、Aeronaut 1 个（CE）。
说明：样本按**系列覆盖面**挑选，不是随机抽样，品牌/系列间比较只作指示性结论（见 §8）。

## 3. 数据格式与桨标签解析

静态文件为 UTF-8 文本，`#` 开头为注释、跳过空行，表头固定三列：

```
RPM    CT       CP
1966   0.0987   0.0434
...
```

- `RPM`：转速 [r/min]；`CT`、`CP`：静态推力/功率系数 [-]
- 解析器：`code/reference/uiuc_propdb.py::load_static()`，逐行校验 `RPM>0`、`CT/CP≥0`，
  输出 `rpm / ct / cp / n_rps=rpm/60`（v0.1 行为不变）
- 文件名解析（v0.2 新增）：`uiuc_propdb.parse_prop_label()` 解析
  `<prefix>_<直径>x<螺距>_static_<test_id>.txt`（直径可带小数，如 `8.5x6`），
  未知前缀或不合规文件名抛 `ValueError`：

| 前缀 | 品牌 | 系列代码 | 系列全称 |
| --- | --- | --- | --- |
| `apce` | APC | E | Electric (thin electric) |
| `apcsf` | APC | SF | Slow Flyer |
| `apcsp` | APC | Sport | Sport |
| `grcp` | Graupner | CAM | CAM Prop |
| `grsn` | Graupner | SN | Super Nylon |
| `ance` | Aeronaut | CE | Carbon Electric |

解析结果含 `file / prop（如 apce_11x7）/ brand / series / series_full / brand_series
（如 APC-E）/ diameter_in / pitch_in / size（保留原始数字，如 8.5x6）/ test_id /
display（如 "APC-E 11x7"）`。目录加载 `catalog_uiuc.load_catalog()` 遇到重复桨标签会报错。

## 4. 对标协议与统计方法

逐点（与 v0.1 相同）：

1. 对 UIUC 每个 RPM 点，用模型公式计算同转速系数：
   `C_T = C_T0 · (n/n_ref)^a_T`、`C_P = C_P0 · (n/n_ref)^a_P`，
   `n = RPM/60`，`n_ref = 100 r/s`；
   模型 v0.1 参数：`C_T0=0.110`、`C_P0=0.0450`、`a_T=−0.02`、`a_P=−0.035`
   （`code/simulation/propulsion_model.py::ModelParams`，本版未改）；
2. 相对误差（**带符号**）：`ct_rel_err = (ct_model − ct_ref)/ct_ref`，`cp_rel_err` 同理；
   负值表示模型**低估**参考系数；
3. 不换算推力/扭矩，不引入空气密度/桨径假设（系数本身无量纲）。

逐桨统计（`benchmark_catalog()` 的 per-prop 部分，`*_summary.csv` 一行一桨）：

- `points`、`rpm_min/rpm_max`；
- `ct_ref_mean/min/max`、`cp_ref_mean/min/max`（实测）；
- `ct_model_mean`、`cp_model_mean`（模型）；
- `ct/cp_rel_err_mean`（带符号均值，判断低估/高估方向）、`*_mean_abs`（均值绝对误差）、
  `*_max_abs`（最大绝对误差）；
- `all_positive`（该桨实测系数是否全为正）。

跨桨汇总（pooled，对全部 112 个点合并统计）：

- `props`、`points`、`brand_count`、`series_count`、`rpm_min/rpm_max`；
- `ct/cp_rel_err_mean`（带符号）、`*_mean_abs`、`*_max_abs`；
- `ct_underestimated_props` / `cp_underestimated_props`（带符号均值 < 0 的桨数）；
- `all_positive`。

产物（v0.2 新文件，v0.1 产物不覆盖）：

| 产物 | 内容 |
| --- | --- |
| `data/processed/uiuc_benchmark_v0.2.csv` | 逐点 16 列：桨标签 6 列 + `rpm/n_rps/ct_ref/cp_ref/ct_model/cp_model/ct_rel_err/cp_rel_err` + `data_note` |
| `data/processed/uiuc_benchmark_v0.2_summary.csv` | 逐桨 27 列：§4 逐桨统计 + 归档字段（`display` 等） |
| `data/processed/figures/uiuc_benchmark_v0.2.png` | CT vs RPM、CP vs RPM 双面板：7 条 REFERENCE 曲线（散点+细线）+ 1 条通用 MODEL 曲线（黑虚线）+ REFERENCE/MODEL 脚注 |

图件脚注固定为：
`REFERENCE (UIUC, measured) vs MODEL (SIM, generic params) — magnitude/trend check only`。
图中模型曲线是**一条**（同参数同曲线），这是 v0.2 要展示的"系统性偏差"，不是拟合结果。

## 5. 结果（2026-11-19 实跑）

范围：7 桨 / 112 点 / RPM 1655–6897。表中"误差均值"为带符号均值（负=模型低估），
"最大"为最大绝对相对误差。

| 桨（展示名） | 点数 | RPM 范围 | C_T 实测均值（范围） | C_P 实测均值（范围） | C_T 误差 均值/最大 | C_P 误差 均值/最大 |
| --- | --- | --- | --- | --- | --- | --- |
| APC-E 11x7 | 16 | 1966–6320 | 0.1051（0.0987–0.1093） | 0.0444（0.0434–0.0468） | +5.69% / 13.96% | +2.86% / 5.14% |
| APC-E 11x8 | 16 | 1655–6213 | 0.1036（0.0951–0.1136） | 0.0518（0.0503–0.0526） | +7.46% / 18.69% | −11.66% / 13.24% |
| APC-SF 10x7 | 16 | 2283–5987 | 0.1512（0.1409–0.1606） | 0.0731（0.0676–0.0797） | −26.51% / 31.50% | −37.33% / 43.53% |
| APC-Sport 9x6 | 16 | 2564–6521 | 0.1065（0.0960–0.1155） | 0.0576（0.0550–0.0598） | +4.38% / 16.55% | −21.00% / 22.48% |
| Graupner-CAM 10x6 | 16 | 1987–6592 | 0.0964（0.0828–0.1026） | 0.0424（0.0404–0.0450） | +15.62% / 35.82% | +7.83% / 11.02% |
| Graupner-SN 10x7 | 16 | 1954–6388 | 0.1289（0.1241–0.1305） | 0.0597（0.0561–0.0624） | −13.95% / 15.69% | −23.45% / 25.00% |
| Aeronaut-CE 8.5x6 | 16 | 2489–6897 | 0.1080（0.1046–0.1144） | 0.0521（0.0493–0.0567） | +2.51% / 7.03% | −12.60% / 18.15% |
| **pooled（112 点）** | 112 | 1655–6897 | — | — | **−0.69% / 11.37% / 35.82%** | **−13.62% / 16.68% / 43.53%** |

pooled 行误差列依次为：带符号均值 / 均值绝对误差 / 最大绝对误差。
系统性偏差计数：C_T 被低估 2/7 桨，C_P 被低估 5/7 桨；7 桨实测系数均全为正。

### 跨桨结论（3 条）

1. **C_P 系统性低估跨桨基本一致，C_T 无统一方向。** C_P 带符号 pooled 均值 −13.62%，
   5/7 桨为负（APC-E 11x8、APC-SF、APC-Sport、Graupner-SN、Aeronaut-CE），
   与 v0.1 单桨结论同向；C_T 带符号均值仅 −0.69%，只有 2/7 桨（APC-SF、Graupner-SN）
   为负。说明通用先验 `C_P0=0.0450` 整体偏"高效"，会让仿真效率偏高；
   `C_T0=0.110` 在细薄电桨量级基本居中，但对高升力桨不足。
2. **偏差量级由品牌/系列（平面形状+翼型）主导，不是直径/螺距。** 同为 10x7 的
   APC-SF（C_T 0.151 / C_P 0.073）与 Graupner-SN（0.129 / 0.0597）实测均值就相差
   约 17%/22%；与细薄电桨 APC-E 11x7（0.105 / 0.0444）、Aeronaut-CE 8.5x6
   （0.108 / 0.0521）相比差距更大（C_T/C_P 均值相差 1.4–1.6 倍）。
   误差最大的是 APC-SF（C_T 26.5%、C_P 37.3%，模型严重低估厚/高弯度慢飞桨），
   误差最小的是 Aeronaut-CE 8.5x6（C_T 3.4%）与 APC-E 11x7（C_T 5.7%、C_P 2.9%）。
   一条通用曲线无法同时覆盖所有系列，需按系列（至少按"细薄电桨 / 慢飞桨"两档）标定先验。
3. **RPM 趋势：C_T 方向相反，C_P 主要是水平偏移。** 7/7 桨实测 C_T 随 RPM 上升
   （首末点升幅约 5%–24%），而模型 C_T 因 a_T=−0.02 随 RPM 缓降（全段约 −3%），
   方向相反 → C_T 误差随转速单调漂移：低转速端普遍高估（Graupner-CAM 在
   1987 r/min 达 +35.8%，APC-E 11x7 在 1966 r/min 达 +14.0%），高转速端转为低估
   （APC-SF 在 5987 r/min 达 −31.5%，Aeronaut-CE 在 6897 r/min −4.1%）。
   C_P 不同：模型 C_P 全段近似水平（a_P=−0.035，全段仅降约 4%），而实测 C_P
   6/7 桨随 RPM 下降 4%–11%（仅 APC-SF 上升约 18%）；因此 C_P 误差主要是
   **水平偏移**（cp0 偏低），随转速漂移的方向取决于该桨实测斜率
   （Aeronaut-CE −18.2%→−11.3%，APC-SF −31.4%→−43.5%）。
   即：C_T 需按转速段校准斜率（或引入雷诺数正指数），C_P 优先校准 cp0 水平。

## 6. 产物清单

- 数据镜像：`data/reference/uiuc/` 下 8 个文件（v0.1 的 1 个 + v0.2 新增 7 个，均含头注释）；
- 逐点：`data/processed/uiuc_benchmark_v0.2.csv`（112 行 + 表头）；
- 逐桨：`data/processed/uiuc_benchmark_v0.2_summary.csv`（7 行 + 表头）；
- 图件：`data/processed/figures/uiuc_benchmark_v0.2.png`；
- 代码：`code/reference/catalog_uiuc.py`（v0.2 新增）、`code/reference/uiuc_propdb.py`
  （新增文件名解析，v0.1 API 不变）、`code/reference/test_reference.py`（新增测试）。

## 7. 质量门槛与测试

- `code/reference/test_reference.py` 共 **18** 项：
  - v0.1 原有 9 项全部保留并通过（解析 5 / 对标与产物 4）；
  - v0.2 新增 9 项：
    - 文件名解析 3 项：7 个默认文件标签（prop/brand_series/直径/螺距/display）、
      未知前缀报错、不合规文件名报错；
    - 目录统计 3 项：7 桨/112 点/3 品牌/6 系列与全正性、逐桨与 pooled 统计一致性
      （逐点误差重建、带符号均值、低估计数、量级区间）、重复桨标签报错；
    - 产物 3 项：逐点/逐桨 CSV 字段与行数+覆盖保护、PNG >30 KB+覆盖保护、
      缺文件时 CLI 返回码 2。
- 运行：`py -3.12 -m unittest discover -s code\reference -p "test_*.py" -v`
  → `Ran 18 tests ... OK`。
- 门槛：pooled C_T 均值绝对误差落在 5%–20%、C_P 落在 10%–25%（宽区间，防止
  参数微调使测试脆化），且 `cp_underestimated_props ≥ ct_underestimated_props`。

## 8. 限制与待办

1. 只有静态（RPM 扫描）数据，没有风速扫描，无法对标 J、η 与来流影响（v0.3 主题）；
2. 每桨仅 16 点，单风洞/单批次；UIUC 原始数据含雷诺数/马赫数修正说明，本版未逐条复核；
3. 模型不含直径/螺距/翼型参数（C_T/C_P 只随 RPM 变化），本版比较的是系统性偏差，
   不是"给定桨的预测精度"；
4. 样本按系列覆盖挑选、非随机（APC 4 / Graupner 2 / Aeronaut 1），品牌级结论仅指示性；
5. `grsn_10x7` 在 3148 r/min 的 C_P=0.0561 相对邻点有局部下凹，按镜像原样参与统计，
   未平滑/剔除；若需精细分析应回查原始报告；
6. 无测量不确定度，误差只作量级/趋势参考，不构成实验验证；
7. 待办：风速扫描解析与对标（v0.3）；按系列标定 C_T0/C_P0（先验 vs 标定两档）；
   增加桨型/品牌覆盖；按转速段报告误差；雷诺数修正选项。

## 9. 复现命令

```powershell
# 全部测试（18 项）
py -3.12 -m unittest discover -s code\reference -p "test_*.py" -v

# 多桨型对标（生成 v0.2 逐点 CSV、逐桨 CSV、图件；--overwrite 覆盖已有 v0.2 产物）
py -3.12 code\reference\catalog_uiuc.py --overwrite

# 指定子集/自定义目录
py -3.12 code\reference\catalog_uiuc.py --files apce_11x7_static_kt0534.txt ance_8.5x6_static_2848cm.txt --overwrite

# v0.1 单桨流程仍可复现（不受影响）
py -3.12 code\reference\benchmark_uiuc.py --reference data\reference\uiuc\apce_10x7_static_pg0811.txt --overwrite

# 控制台中文若乱码：先设置 PYTHONUTF8=1、PYTHONIOENCODING=utf-8
```

注：`catalog_uiuc.py` 默认读取 `data/reference/uiuc/` 的 7 个 v0.2 样本；matplotlib
来自仓库 vendored 的 `work/pylibs`（Agg 无界面后端），无需系统安装。

## 10. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 单桨（APC 10x7E）静态对标：样本入库、解析器、对标脚本、9 项测试 |
| 0.2 | 2026-11-19 | 多桨型静态对标：7 桨镜像（3 品牌/6 系列/112 点）、文件名桨标签解析、catalog 逐桨+pooled 统计、v0.2 CSV/图件、新增 9 项测试（共 18）、跨桨结论与限制 |
