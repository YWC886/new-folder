# 多工况试验方案生成器（design matrix）v0.1

- 模块：`code/processing/design_matrix.py`（测试：`code/processing/test_design_matrix.py`，10 项）
- 建立：2026-11-21 ｜ 作者：C（数据与软件）｜ 状态：可用（仅生成计划，不产生数据）

## 1. 目的

把 S2 阶段"电压 × 油门 × 桨型 × 重复"的试验安排展开为**可执行采集排程**：每条计划行都对应一次
`code/acquisition/acquire.py --mode serial` 采集的参数（`combo / voltage_set / throttle_set / repeat`），
避免口头排程导致工况缺漏、重复次数不足或换桨顺序混乱。

边界：

- 只生成**试验计划**，不生成测量数据、不做任何物理计算；
- 不替代 `measured_readiness` 门禁（D035）与双人标定（D032）；
- 计划行中的数据一律不得称为实测结果。

## 2. 设计类型

| 类型 | 排列规则 | 适用场景 |
|---|---|---|
| `full`（全因子） | 电压块 → 重复 → 桨型 → 油门（升序） | 主试验：覆盖完整组合、便于换桨与热平衡 |
| `sweep`（阶梯扫描） | 电压块 → pass（重复）→ 桨型 → 油门升 + 降 | 补充试验：观察温漂、迟滞与升/降两点一致性 |

行数公式：

- `full`：`N = |V| × |T| × |P| × R`
- `sweep`：`N = |V| × R × |P| × 2 × |T|`

其中 |V| 电压点数、|T| 油门点数、|P| 桨型数、R 重复次数。

`run_id` 命名：`<combo>_<prop>_<V>V_<T>pct_R<repeat>`，例如
`SIM10x4.5_SIM10x4.5_22.2V_50pct_R1`。

## 3. 字段

| 列 | 含义 |
|---|---|
| order | 运行顺序（1 起连续） |
| block | 电压块序号 |
| run_id | 建议采集文件名主体（采集脚本自行追加日期） |
| combo | 组合名（传给 `acquire.py --combo`） |
| prop_id | 桨型标识 |
| voltage_set_v | 母线电压设定（V） |
| throttle_set_pct | 油门设定（%） |
| direction | `hold`（全因子）/ `up`、`down`（阶梯） |
| repeat | 重复编号 |
| duration_s | 单次采集时长（s） |
| steady_window_s | 稳态窗口（s，供处理流水线） |
| notes | 自由备注 |

## 4. 默认基线计划（S2 主试验）

推荐参数（与申报书"多工况采集"一致、兼顾 5000 元预算与 12 月台架期）：

- 电压：11.1 / 14.8 / 22.2 V（3 点，3S–6S 常用区间）
- 油门：20 / 40 / 60 / 80 / 100 %（5 点，覆盖低载到满油门）
- 桨型：3 个候选（A/B/C）
- 重复：3 次
- 单次采集：5 s，稳态窗口 1.5 s

=> `full` 计划 **135 次运行**，纯采集约 11.25 min（不含换桨、防护检查与热平衡停机）。

命令：

```powershell
py -3.12 code\processing\design_matrix.py --voltages 11.1,14.8,22.2 --throttles 20,40,60,80,100 --props A,B,C --repeats 3 --design full --combo PROP-SET --output data\processed\design_matrix_v0.1.csv --summary data\metadata\design_matrix_v0.1.summary.json --overwrite
```

补充扫描（温漂/迟滞）：把 `--design` 改为 `sweep`，行数翻倍（每 pass 升 + 降）。

## 5. 与采集/处理链路衔接

1. 计划行 → `acquire.py --mode serial --combo <combo> --voltage-set <V> --throttle-set <T> --repeat <R> --run-id <run_id>`；
2. 采集完成后跑 `measured_readiness.py` 门禁（D035）；
3. 通过后 `compute_efficiency.py --require-measured` 生成逐样本与稳态汇总（D036）；
4. `aggregate_efficiency.py --require-measured` 汇总为 MEASURED 效率地图 runs/grid（D037）。

## 6. 限制与 v0.2 待办

- 仅离散命令点；未实现拉丁超立方（LHS）随机化——随机油门点对台架重复性要求更高，先保证
  "可复现的离散点 + 平衡设计"，LHS 留到台架稳定后作为补充；
- 未建模换桨、防护检查、电池更换与热平衡停顿；实际执行建议每电压块后停机检查；
- 未包含环境温湿度分层（冬季实验室温度变化大，可在 notes 注明并加记录）；
- v0.2：`--design lhs`、`--seed` 随机化、`--block-gap-s` 停顿时长、按 `acquire.py` 生成批处理脚本。

## 7. 变更记录

| 版本 | 日期 | 变更 |
|---|---|---|
| 0.1 | 2026-11-21 | 初版：full / sweep 设计、字段、默认基线计划（135 runs）、与采集/处理后链路衔接 |
