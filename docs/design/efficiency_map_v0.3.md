# 效率地图图件 v0.3：不确定度可视化

| 项 | 内容 |
| --- | --- |
| 状态 | 草稿 v0.3（2026-11-19） |
| 实现 | `code/processing/plot_efficiency_map.py`（`plot_map(..., show_uncertainty=False)`、CLI `--uncertainty`） |
| 测试 | `code/processing/test_plot_efficiency_map.py`（既有 3 项 + 新增 3 项；处理流水线合计 26 项） |
| 输入 | `data/processed/efficiency_map_runs.csv`（含 `u_eta_em_k2` / `u_fm_k2` / `u_eta_sys_k2` 列） |
| 输出 | `data/processed/figures/efficiency_map_v0.3.png`、`efficiency_map_v0.3_eta_em.png`（均需显式 `--output`） |
| 上游 | `compute_efficiency.py`（U 计算）、`aggregate_efficiency.py`（U 写入 CSV）、`docs/design/processing_pipeline_v0.2.md` |
| 责任人 | D，评审：A（接口）、B（物理合理性） |

> **数据诚信**：当前输入全部是 `source=SIM` 的仿真数据；U 是按传感器量级假设做的一阶**先验**传播，不是实测标定结果。图件继续强制红字「SIMULATED DATA — NOT EXPERIMENTAL」，不得作为实验结论或选型最终依据。

## 1. 目的

v0.1/v0.2 的效率地图只用颜色和数字展示指标均值，视觉上"每个点看起来很精确"，掩盖了输入不确定度。v0.3 把流水线已算出的扩展不确定度 U(k=2) 直接画到图上：散点图叠加误差棒、热力图在每格内标注 `±U绝对值`，让读者在比较工况时能看到可信区间，避免"高精度假象"。

## 2. 相对 v0.1 / v0.2 的增量

| 版本 | 已有能力 | 本版关系 |
| --- | --- | --- |
| 数据侧 v0.1 | 逐 run 指标均值 → runs CSV；散点/热力图脚本；SIM 红字；默认拒绝覆盖 | 保留，不改渲染口径 |
| 数据侧 v0.2 | `compute_efficiency` 一阶不确定度传播；runs/grid 增加 `steady_mode` 与 `u_*_k2` 列 | 本版消费 runs 中的 U 列，v0.2 已埋好数据接口 |
| 图件 v0.3（本文件） | `show_uncertainty` 开关（默认关）；CLI `--uncertainty`；误差棒/格内 ± 标注；U 缺失 warning 容错；新增 3 项测试（23→26） | 默认输出路径、默认覆盖策略、未开启时的渲染均与 v0.1 一致（同数据输出字节数一致：58842 B） |

## 3. U 的来源

`compute_efficiency.py` 的 `_uncertainty_block()` 按一阶相对不确定度 RSS 传播（各分量独立、小量），取 1σ 相对量级：推力 0.65%、扭矩 0.50%、转速 0.10%、电压 0.10%、电流 0.50%、空气密度 0.50%，报告 U=2u（约 95%）：

- u_rel(η_em) = √(u_Q² + u_rpm² + u_V² + u_I²) = 0.7211% → U=1.4422%
- u_rel(FM) = √((1.5·u_T)² + u_Q² + u_rpm² + (0.5·u_ρ)²) = 1.1282% → U=2.2565%
- u_rel(η_sys) = √((1.5·u_T)² + (0.5·u_ρ)² + u_V² + u_I²) = 1.1282% → U=2.2565%

`aggregate_efficiency.py` 从汇总 JSON 的 `uncertainty.U_rel_*_k2` 取出写入 runs CSV（当前 16 工况 SIM 值为 `u_eta_em_k2=0.0144222051`、`u_fm_k2=u_eta_sys_k2=0.02256656819`）；grid CSV 另存同格 `*_max`（保守，供选型用）。绘图脚本**只读 runs 行值**，不做放大、合并或按重复次数折减；同一工况多条 run 各自独立标注。

## 4. 渲染规则

- field 与 U 列一一对应：`eta_em→u_eta_em_k2`、`fm→u_fm_k2`、`eta_sys→u_eta_sys_k2`；U 为分数形式（0.0225666 即 ±2.26%），误差绝对值 = `value × U`。
- **散点模式**（<4 点或不足 2×2）：保留按均值着色的 `scatter` 与色标，叠加 `ax.errorbar(yerr=value*U, capsize=3)`，数值标注改为 `value ± value*U`（3 位小数）。
- **热力图模式**（≥4 点且电压/油门各 ≥2 唯一值）：`pcolormesh` 不变，每个有效格中央标注两行 `value` / `±value*U`（`fontsize=7`），文字颜色按 viridis 背景亮度取黑/白，保证深紫与亮黄格都可读。
- **U 缺失/非有限**：向 stderr 打印 `warning: <run_id> 的 <U列> 缺失或非有限（...），跳过该点误差，仍绘制该点`；该点只画均值（散点标注只写 value，热力图只写 value），不中断出图。
- **标题**：开启时在末尾追加 ` with U(k=2)`；基础标题仍用「Efficiency map v0.1 — ...」（v0.1 是图件方案名，不随脚本升级改动，避免破坏既有图件对比口径）。
- **SIM 标注**：红字「SIMULATED DATA — NOT EXPERIMENTAL」始终保留；颜色映射仍只表达指标均值（U 不参与着色）。
- 未开启 `show_uncertainty` 时：无误差棒、无 ± 标注、标题不含 U(k=2)，输出与 v0.1 完全一致；默认输出路径仍为 `efficiency_map_v0.1.png`，默认拒绝覆盖。

## 5. 示例命令与输出路径

```powershell
# 16 工况 SIM 图件（热力图 + 格内 U 标注）
py -3.12 code\processing\plot_efficiency_map.py --input data\processed\efficiency_map_runs.csv --output data\processed\figures\efficiency_map_v0.3.png --uncertainty --overwrite

# 附加验证：η_em 字段
py -3.12 code\processing\plot_efficiency_map.py --input data\processed\efficiency_map_runs.csv --field eta_em --uncertainty --output data\processed\figures\efficiency_map_v0.3_eta_em.png --overwrite

# 回归测试
py -3.12 -m unittest discover -s code\processing -p "test_*.py" -v
```

实测产物（2026-11-19）：`efficiency_map_v0.3.png` 88050 B、`efficiency_map_v0.3_eta_em.png` 90770 B；目视检查无乱码、格内两行标注无重叠，SIM 红字在轴下方。

## 6. 验收标准

1. 处理流水线测试全部通过：`Ran 26 tests ... OK`（既有 23 项 + 新增 3 项，其中新增为散点+U、2×2 热力图+U、U 缺失容错）。
2. 两条示例命令退出码 0，生成 PNG > 5 KB，图内 16 格均显示 `值` 与 `±U绝对值` 两行文本，可读、不重叠。
3. U 列缺失时仍出图且 stderr 有 warning（非致命）；不开启 `--uncertainty` 时输出与 v0.1 逐字节一致（已核对 58842 B）。
4. 图件标题含 `with U(k=2)`，SIM 红字保留。

## 7. 限制

- **U 是先验不是实测**：当前 U 的 1σ 分量是假设量级，来自 `work/research/bench_tech.md`；实机静态砝码标定与传感器校准后必须用实测重复性/迟滞/漂移替换并复核，超目标（如 η_sys 2.26% > 2.1%）先查标定，不得直接下结论。
- **U 不参与颜色映射**：颜色仍只表示均值，因此"颜色相近但误差棒长短不同"必须靠文字/误差棒读取，大图上不如置信带直观。
- **散点模式纵轴是油门指令（%）**：误差棒长度实际是指标的绝对不确定度，与纵轴量纲混绘，仅作视觉提示，定量值以 `value ± value*U` 标注和 CSV 为准。
- **旧数据无 U**：v0.2 之前的效率 JSON / runs CSV 没有 `u_*_k2` 列，开启开关只会得到 warning 和图，无误差信息。
- **未用 grid 的 `*_max`**：本图按 run 画，同格多条 run 的 U 可能不同；grid U 的保守口径留给选型，不在此图展示。
- **SIM 限制不变**：本图所有点来自物理仿真，误差棒只是先验量级，不能当作实测精度或实验结论；公开数据对标与实机地图到位前，结论性判断一律待验证。
- 密集网格/小图下 ± 标注可能拥挤，本版未做自动避让或交互提示（v0.4 可考虑）。

## 8. 相关文件与接口

- 数据：`data/processed/efficiency_map_runs.csv`（只读消费，本版不修改）；grid CSV 的 `*_max` 不用于此图。
- 代码：`code/processing/plot_efficiency_map.py`（作图）、`code/processing/aggregate_efficiency.py`（U 列来源）、`code/processing/compute_efficiency.py`（U 计算）。
- 文档：`docs/design/efficiency_map_v0.1.md`（数据流与图件基线）、`docs/design/processing_pipeline_v0.2.md`（U 传播细节）。
- 测试：`code/processing/test_plot_efficiency_map.py`（3 项既有 + 3 项新增）。

## 9. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| 0.1 | 2026-11-19 | 初版图件脚本：散点/热力图、SI 轴标签、SIM 红字、3 项冒烟测试（与流水线合计 23 项） |
| 0.2 | 2026-11-19 | 数据侧增量：runs/grid 增加 U(k=2) 列，图件尚未使用（见 `processing_pipeline_v0.2.md`） |
| 0.3 | 2026-11-19 | 本文件：`show_uncertainty`/`--uncertainty` 渲染误差棒与格内 ±；U 缺失 warning 容错；测试 23→26；生成 v0.3 图件；未改默认输出路径与未开启行为 |
