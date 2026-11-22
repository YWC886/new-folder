# code/reference —— 公开参考数据对标

对公开风洞/厂商数据做**参考对标**，不产生实验结论。结果一律标
`REFERENCE`（UIUC 实测）vs `MODEL`（SIM，通用参数），**不得宣称实验验证**。

## 文件

| 文件 | 作用 |
| --- | --- |
| `uiuc_propdb.py` | UIUC Propeller Database 静态数据解析（`RPM CT CP`）；v0.2 起含文件名桨标签解析 `parse_prop_label()` |
| `benchmark_uiuc.py` | v0.1 单桨对标：仿真 vs UIUC 逐点 CT/CP + CSV + 双面板图 |
| `catalog_uiuc.py` | v0.2 多桨型对标：目录加载、逐桨 + pooled 统计、逐点/逐桨 CSV、分组图 |
| `calibrate_uiuc.py` | v0.3 逐桨参数反推：log 空间 OLS 拟合 `ct0/a_T/cp0/a_P` → 逐桨 CSV + `uiuc_priors_v0.3.json`（do_not_apply）+ 分组柱状图 |
| `bootstrap_priors.py` | v0.1 bootstrap 95% CI：逐点重采样重拟合，输出参数与内误差区间（非 U(k=2)，do_not_apply）+ boxplot/errorbar 图 |
| `prior_profile.py` | v0.4 prior profile：逐桨先验 → opt-in `ModelParams`，同数据对比通用先验 vs 逐桨先验（样本内上限，非实测；do_not_apply） |
| `re_correction.py` | v0.5 Reynolds 修正对标（负结果）：Re=n·D²/ν，替换式/乘性修正对照 generic/prior；结论不写入默认参数（D044） |
| `test_reference.py` + `test_calibration_uiuc.py` + `test_bootstrap_priors.py` + `test_prior_profile.py` + `test_re_correction.py` | 77 项测试（解析 / 文件名 / 目录统计 / 对标 / 逐桨反推 / bootstrap 区间 / prior profile 对照 / Re 修正 / CSV / PNG / 覆盖保护） |
| `geometry_prior.py` / `test_geometry_prior.py` | 几何特征代理（REFERENCE，LOPO 负结果，D049，8 项测试） |

## 用法

```powershell
# v0.1 单桨：解析检查 + 对标（产物 uiuc_benchmark_v0.1.*）
py -3.12 code\reference\uiuc_propdb.py --input data\reference\uiuc\apce_10x7_static_pg0811.txt
py -3.12 code\reference\benchmark_uiuc.py --reference data\reference\uiuc\apce_10x7_static_pg0811.txt --overwrite

# v0.2 多桨型：默认读 data/reference/uiuc 的 7 个样本，生成 v0.2 三个产物
py -3.12 code\reference\catalog_uiuc.py --overwrite

# v0.2 指定子集 / 自定义目录
py -3.12 code\reference\catalog_uiuc.py --reference-dir data\reference\uiuc --files apce_11x7_static_kt0534.txt ance_8.5x6_static_2848cm.txt --overwrite

# v0.3 逐桨参数反推（REFERENCE-derived priors，do_not_apply；产物 uiuc_calibration_v0.3.*）
py -3.12 code\reference\calibrate_uiuc.py --overwrite

# v0.1 逐桨先验 bootstrap 95% CI（REFERENCE 稳健性检查，非 U(k=2)）
py -3.12 code\reference\bootstrap_priors.py --overwrite
py -3.12 code\reference\prior_profile.py --overwrite

# v0.5 Reynolds 修正对标（负结果：单一 Re 幂律解释力极低，不写入默认参数）
py -3.12 code\reference\re_correction.py --overwrite

# 测试（61 项）
py -3.12 -m unittest discover -s code\reference -p "test_*.py" -v
```

控制台中文乱码时先设 `$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'`。
matplotlib 来自仓库 vendored 的 `work/pylibs`（Agg 无界面后端），无需系统安装。

## 产物

v0.1（保留不动）：

- `data/processed/uiuc_benchmark_v0.1.csv`：逐点 rpm/ct/cp（参考与模型）+ 相对误差 + data_note
- `data/processed/figures/uiuc_benchmark_v0.1.png`：CT、CP 各一子图，参考 vs 模型

v0.2（新增，不覆盖 v0.1）：

- `data/processed/uiuc_benchmark_v0.2.csv`：逐点 16 列（prop/brand/series/brand_series/diameter_in/pitch_in/file + rpm/n_rps/ct_ref/cp_ref/ct_model/cp_model/ct_rel_err/cp_rel_err + data_note），共 112 行数据
- `data/processed/uiuc_benchmark_v0.2_summary.csv`：逐桨 27 列（点数、RPM 范围、CT/CP 实测均值与极值、模型均值、相对误差带符号均值/均值绝对/最大绝对、all_positive），共 7 行数据
- `data/processed/figures/uiuc_benchmark_v0.2.png`：CT vs RPM、CP vs RPM 双面板；7 条 REFERENCE 曲线（散点+细线）+ 1 条通用 MODEL 曲线（黑虚线）+ 脚注 `REFERENCE (UIUC, measured) vs MODEL (SIM, generic params) — magnitude/trend check only`

v0.3（新增，不覆盖 v0.1/v0.2）：

- `data/processed/uiuc_calibration_v0.3.csv`：逐桨 19 列（prop/brand/series/diameter_in/pitch_in/points + ct0/aT/cp0/aP + ct_log_r2/cp_log_r2 + 反推前后平均绝对误差 + holdout 误差 + data_note），共 7 行
- `data/metadata/uiuc_priors_v0.3.json`：先验 JSON（schema 0.3，`do_not_apply:true` + disclaimer；不是本项目实测标定）
- `data/processed/figures/uiuc_calibration_v0.3.png`：逐桨 C_T / C_P 反推前后平均绝对误差分组柱状图（红字 D033）

结论：逐桨反推内误差 0.3–1.5%（C_T）/0.5–1.2%（C_P）；7 桨 a_T 全为正，通用先验 a_T=−0.02 方向相反；pooled C_T 11.90% / C_P 14.13%。

新增桨型：把镜像文件放进 `data/reference/uiuc/`，文件名需符合
`<prefix>_<直径>x<螺距>_static_<test_id>.txt`；`--files` 传入，或把文件名加入
`catalog_uiuc.DEFAULT_CATALOG_FILES`。新品牌前缀需在
`uiuc_propdb.PROP_PREFIXES` 增加映射（否则 `parse_prop_label()` 报错）。

## 数据约定

- 参考数据在 `data/reference/`，仅镜像小样本；完整 UIUC 库从官方 URL 下载，不入库；
- 引用时必须注明 UIUC Propeller Database（Brandt, Deters, Ananda, Dantsker, Selig）；
- 对标图脚注与 CSV `data_note` 固定说明"仅量级/趋势对标，不构成实验验证"；
- 参考数据不得与 `data/raw` 实测数据或 `SIM` 合成数据混用。

## 已知结论

v0.1（APC 10x7E 单桨 16 点）：C_T 相对误差均值 6.14%、最大 14.65%；
C_P 相对误差均值 13.83%、最大 14.95%（模型系统性低估 C_P）。

v0.2（7 桨 / 3 品牌 / 6 系列 / 112 点，RPM 1655–6897）：

- pooled：C_T 均值绝对误差 **11.37%**（带符号 −0.69%，最大 35.82%）；
  C_P 均值绝对误差 **16.68%**（带符号 −13.62%，最大 43.53%）；
- 系统性偏差：C_P 被低估 5/7 桨，C_T 仅 2/7；即通用先验 `C_P0=0.0450` 偏"高效"，
  该结论从单桨推广到多桨后仍成立；
- 桨型差异主导：APC-SF 10x7 误差最大（CT 26.5% / CP 37.3%），APC-E 11x7 与
  Aeronaut-CE 8.5x6 最小（CT 3–6%）；一条通用曲线不能覆盖所有系列；
- 趋势：7/7 桨实测 C_T 随 RPM 上升，模型 C_T 随 RPM 缓降（方向相反，低转速端高估、
  高转速端低估）；模型 C_P 全段近似水平，实测 C_P 6/7 桨随 RPM 下降 4%–11%
  （仅 APC-SF 上升约 18%），故 C_P 误差主要是 cp0 水平偏低，CT 还需校准斜率。

详见 `docs/design/public_data_benchmark_v0.2.md`。


v0.1 bootstrap 新增产物：

- `data/processed/uiuc_bootstrap_priors_v0.1.csv`：逐桨 23 列（参数点估计 + 95% CI + 内误差 + CI）
- `data/metadata/uiuc_priors_bootstrap_v0.1.json`：`do_not_apply:true` + disclaimer（非 U(k=2)）
- `data/processed/figures/uiuc_bootstrap_priors_v0.1.png`：a_T boxplot + ct0±CI 双面板

- `data/processed/prior_profile_vs_generic_v0.1.csv`：逐点 13 列（prop/rpm/ct_ref/cp_ref/ct_generic/cp_generic/ct_prior/cp_prior + 相对误差 + data_note），112 行
- `data/processed/figures/prior_profile_v0.1.png`：逐桨 CT/CP 平均绝对误差分组柱状图（generic vs opt-in prior，红字 D042）

- `data/processed/re_correction_v0.5.csv`：逐点 Re/CT/CP 参考值与三类模型值 + 相对误差（112 行）
- `data/processed/figures/re_correction_v0.5.png`：逐桨 CT/CP 平均绝对误差（generic / Re 替换 / Re 乘性 / prior，红字 D044）
- `data/metadata/re_correction_v0.5.summary.json`：pooled 拟合系数、R²、四方误差汇总与免责声明
