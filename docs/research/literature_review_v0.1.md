# 多旋翼 UAV「电机—螺旋桨—电调」系统效率地图构建与匹配优化：外部文献调研（v0.1）

> 记录日期：2026-11-19（Asia/Shanghai）。面向大创项目「多旋翼 UAV 电机—螺旋桨—电调系统效率地图构建与匹配优化」（西北工业大学，指导教师：宋受俊）。
> 纪律：本报告只引用可核验来源（DOI 或可访问 URL）；凡未获取全文、仅据题名/摘要/数据库元数据作判断之处均明确注明；不确定项标注“待核实”；项目内部结论与公开文献严格分开；项目模拟（SIM）结果一律标注 SIM，不当作实验结论；公开数据与实测数据不混用。
> 配套文件：`docs/research/references.csv`（编号 L01–L40，与本报告参考文献一一对应）。

## 0. 摘要

本报告在 2020–2026 年为主、2005–2019 年经典方法为辅的时间窗内，围绕“电推进效率建模与效率地图、电机—螺旋桨—电调匹配选型、推力/扭矩台架测量与不确定度、GP/代理模型/贝叶斯优化/多目标优化、公开螺旋桨数据库、数字孪生与 DoE”六个主题检索并核验了 40 条来源（其中 2020 年后 27 条，含 3 个数据库条目按批次/访问年计；期刊会议文献 24 条）。核心判断：公开文献已充分证明“部件建模 + 性能地图 + 多目标优化”的可行性，但**把整链实测效率、地图平滑与不确定度传播、以及基于地图的匹配选型整合为一条可复现流程**的公开工作仍然稀少；台架不确定度预算、电调（ESC）效率实测、以及 DoE 在推进系统标定中的直接应用是相对薄弱环节。这为本项目“实测效率链 + GP 地图（含后验不确定度）+ Pareto 匹配 + 补测决策”的组合留出了可论证的差异化空间（详见 §4、§6）。

## 1. 调研范围、检索策略与核验方法

### 1.1 问题分解

按项目四个方向（见 `docs/plan/拓展方向_v0.1.md`）把调研问题拆成六个主题：

1. **电推进系统效率建模与效率地图**：部件级（螺旋桨/电机/电调/电池）效率模型、静态或准静态性能图（performance/static maps）、系统效率 η_sys 的定义与构建；
2. **电机—螺旋桨—电调匹配与选型**：部件匹配、参数选型、多目标优化、性能地图在选型中的使用；
3. **台架测量、标定与不确定度**：推力/扭矩/转速/电流/电压测量、测试台设计、标定流程、测量不确定度评定与传递；
4. **代理模型、高斯过程（GP）、贝叶斯优化（BO）与多目标优化**：DGP/稀疏 GP、DNN 代理、多保真优化、Pareto 前沿与决策；
5. **公开螺旋桨数据库**：UIUC、APC、OSU（Ohio State）、PropFolio；
6. **数字孪生、硬件在环（HIL）与试验设计（DoE）**：虚拟试验台、故障数据库、Taguchi/析因/响应面方法。

### 1.2 检索策略

| 主题 | 代表检索式（英文） | 数据源 | 时间窗 |
|---|---|---|---|
| 效率建模/地图 | `electric propulsion efficiency map UAV`、`motor-propeller efficiency`、`propulsion system performance maps` | Crossref、OpenAlex、Semantic Scholar | 2015–2026 |
| 匹配/选型 | `motor propeller matching`、`propulsion system optimization multicopter`、`integrated optimization motor propeller` | 同上 | 2015–2026 |
| 台架测量 | `thrust test stand`、`torque measurement propeller`、`UAV propulsion test bench`、`thrust measurement multirotor` | 同上 | 2005–2026 |
| 代理模型/优化 | `Gaussian process propeller`、`surrogate model UAV`、`Bayesian optimization propeller`、`multi-objective propulsion` | 同上 | 2015–2026 |
| 数据库 | 官网直接检索与页面核对 | UIUC、APC、PropFolio 官方页面 | 最新 |
| DoE/数字孪生/HIL | `design of experiments UAV`、`Taguchi UAV`、`digital twin propulsion UAV`、`hardware-in-the-loop UAV` | Crossref、OpenAlex | 2015–2026 |

补充说明：检索以英文文献为主；中文文献未系统检索（知网需机构账号，见 §1.4 局限），这是本报告的**已知缺口**，建议后续由项目组用校内账号补检并合入 v0.2。

### 1.3 核验与降级规则

1. 每条文献的题名、作者、年份、期刊/会议、DOI 至少经 Crossref 与 OpenAlex 两个独立接口之一核对；两者冲突时以 Crossref（出版商注册元数据）为准；
2. 数据库类来源以官方页面可访问（HTTP 200）且页面文字可读为准，记录访问日期；
3. 未获取摘要或全文的文献，正文只作**题名级**描述，不推断其数值结论、不虚构方法细节；
4. 无法确认的字段（卷号、页码、会议全称、数据库版本年份等）在 CSV 的 `note` 与 §9 标注“待核实”，正文不作断言；
5. 本报告未通读任何全文（PDF 获取受限，见 §1.4），所有方法描述均来自题名、摘要、出版元数据或官方数据库页面。

### 1.4 检索局限与失败记录（如实）

- **IEEE Xplore 文档页**：`web_fetch` 返回 HTTP 202 且正文为空（JS 挑战），无法直接读取页面；改用 Crossref/OpenAlex 元数据与 Semantic Scholar 单篇摘要接口。
- **PDF 不可读**：`web_fetch` 对 `application/pdf` 返回 unsupported content type，因此全文未通读。
- **部分出版商站点 403**：如 `matec-conferences.org`；其条目元数据经 Crossref 核实。
- **Semantic Scholar 搜索端点 429**：批量 search 被限流（单篇 DOI 查询可用），因此未做大规模语义检索。
- **OpenAlex 个别 DOI filter 不命中**（索引覆盖差异），以 Crossref 为准。
- **DoE 组合检索**：以 `"design of experiments"` 与 `multirotor`/`propeller`/`UAV propulsion` 组合检索（OpenAlex，2015–2026），**未发现直接用于电机—桨—电调推进系统标定的论文**；检索到的 DoE/Taguchi 应用集中在 UAV 气动外形设计（如 [L31]）。这不等于“该研究方向不存在”，仅表示本次检索范围内未检索到，正文按“检索范围内未见”表述。
- **OSU 数据库**：未检索到 Ohio State 螺旋桨数据的独立可下载入口，仅在 UIUC 数据库页面被作为对比数据提及（待核实），故 CSV 不单列 OSU 数据库条目。
- **中文文献**：知网未检索（无机构账号）。

## 2. 主题综述

### 2.1 电推进系统效率建模与效率地图

多旋翼电推进系统的效率建模通常沿“部件级 → 系统级”展开。Dai 等（2019）[L14] 将推进系统拆为螺旋桨、电机、电调、电池四类部件分别建模，把整体优化设计问题简化为若干可解耦的子问题，再依据最优部件参数在相应产品数据库中快速定位产品；论文报告了实验与统计分析，并称该方法已用于在线优化设计服务（以上据摘要）。这一“部件模型 + 解耦 + 数据库查表”的范式，是后续许多匹配选型工作的共同骨架。

Nam 等（2023）[L29] 则把“地图”推到系统层级：以转速与扭矩为两个独立变量，将电调、电机、螺旋桨、机体各环节的效率以等值线形式表达，从而在宽工况范围内整体分析电推进系统。其显著特点是**不依赖昂贵测量**，用制造商提供的数据即可计算；对 2 m 翼展无人机的 8 组螺旋桨/机体组合评估后，作者指出最高效率可因部件选择不同而相差 10% 以上（据摘要）。这直接说明“效率地图”在匹配选型中的价值，也暴露其代价：地图精度受厂商数据质量约束。

Piljek 等（2020）[L17] 给出另一条路线——**实验表征**：通过实验测量与辨识流程建立多旋翼推进单元的静态性能图（static maps），使效率/推力/扭矩关系可用于后续设计。相比 [L29] 的厂商数据路线，[L17] 更接近“实测建图”，但其公开摘要未涉及 GP 平滑与不确定度传播（摘要层面）。

此外，Shi 等（2017）[L12] 提出面向电动多旋翼的实用性能评估方法（题名级，摘要未获取）；Amici 等（2021）[L21] 系统综述了无人机推进系统设计策略；Theys 等（2016）[L07] 研究桨配置对多旋翼推进系统效率的影响；Etewa 等（2024）[L33] 面向固定翼 UAV 给出推进系统性能估计方法。这些工作共同说明：**效率不是单一部件的属性，而是“桨—电机—电调—电池—工况”耦合的结果**，必须以系统级指标（如 η_sys）表达，这与本项目方向一的 η_em/FM/η_sys 定义一致。

项目内部现状（内部文档口径）：方向一已把 raw CSV + 标定转换为 η_em、FM、η_sys，并完成稳态自动识别与一阶 RSS 不确定度预算（η_em ±1.44%、FM/η_sys ±2.26%，k=2）；效率地图 v0.4 用 RBF 核 GP 平滑，LOOCV 指标 ℓ=0.550、RMSE 0.001662、R²=0.9999，输出 21×21 均值/标准差面（内部文档；GP 属统计建模，非实测）。与 [L17][L29] 相比，本项目的差异点在于**实测整链 + 地图化 + 后验不确定度**三者合一。

### 2.2 电机—螺旋桨—电调匹配与选型方法

从检索结果看，匹配选型研究大致分三类：

**（1）解析/解耦优化 + 产品库选型。** 代表为 Dai 等（2019）[L14]：把系统目标（如悬停续航）分解到部件参数，再在数据库内选型。优点是计算快、工程可落地；局限是依赖产品库覆盖度与部件模型的准确性。

**（2）性能地图法。** 代表为 Nam 等（2023）[L29]：先构建各部件效率等值线，再在“转速—扭矩”平面上做组合评估，从而比较不同桨/机体组合在整个工况域的表现。该方法的优点是**全域可视**，适合方案筛选；局限是地图由数据插值/厂商数据生成，未必反映具体样机的偏差。

**（3）集成/多目标优化。** Duan 等（2020）[L20] 研究多状态下的高效电机—螺旋桨系统集成优化设计（题名级）；Xu 等（2024）[L32] 以功率密度与效率为目标对 UAV 电推进电机做多目标优化（题名级）；Mian 等（2021）[L25] 用物理基代理模型结合空间映射优化薄型电动桨（题名级）。这类工作把“设计变量”从选型扩展到几何/电磁设计，与本项目“在既有产品中匹配”的定位不同，但其多目标处理与代理模型技术可借鉴。

项目内部现状：方向三已完成插值/多目标/GP 连续匹配，v0.4 实现真多目标 Pareto（13×41 候选，η/电流/保守 η 非支配，knee=29.60 V/52.5%，28 个可行解、5 个前沿解）与 GP σ 补测点推荐（5 点）（内部文档，SIM/计算流程）。与文献相比，本项目把“实测效率地图”直接作为匹配输入、并用 GP 后验方差指导补测，这一组合在检索范围内较少见（详见 §4）。

### 2.3 台架测量、标定与不确定度

**测试台与测量链。** Hernandez 等（2021）[L23] 面向 UAV 电机—螺旋桨组开发效率分析测试台；Jatsun 等（2020）[L19] 设计倾转旋翼类 UAV 的实验测试台；Amici 等（2021）[L22] 对服务型 UAV 的电推进单元做实验表征；Zhao 等（2021）[L26] 设计并实现固定翼 UAV 的机载电推进测量系统；Cox 等（2025）[L38] 讨论多旋翼与轻于空气 UAV 的推进系统测试仪器。这些工作覆盖了“地面台架 → 机载测量 → 仪器化”的不同层次，可作为本项目测试链设计的参照。

**公开数据的测试传统。** UIUC 螺旋桨数据库 [L01] 的方法学源头见 Brandt 与 Selig（2011）[L05] 与 Deters 等（2014）[L06]：在低雷诺数下系统测量小桨性能，并讨论 Re 效应；Dantsker 等（2020）[L18] 与（2022）[L28] 分别给出 Aero-Naut CAM 折叠桨与 APC 电动固定桨的性能测试。UIUC 页面还说明其测试装置采用枢轴臂上的 load cell 测推力、torque cell 测扭矩，而 OSU 采用多轴 load cell 直接安装电机（页面文字，[L01]）——这是理解不同数据库系统偏差的重要背景。

**不确定度。** 不确定度评定的通用框架是 JCGM 100:2008（GUM）[L04]，其中 k=2 对应约 95% 覆盖概率的扩展不确定度表达。项目方向一采用一阶 RSS 合成并给出 η_em ±1.44%、FM/η_sys ±2.26%（k=2）（内部文档）。值得注意的是：在本次检索范围内，**未发现专门报告“电机—桨—电调”整链台架不确定度预算并传播到系统效率地图的公开论文**；多数测试类文献（如 [L18][L23][L28]）以性能数据与曲线为主，不确定度多未系统披露。这既是文献缺口，也是本项目可以形成方法学贡献的方向（见 §4 G2）。

**动态测试。** 检索到的工作以稳态/准稳态测量为主（[L23][L26][L28]）；面向动态推力/扭矩（如阶跃油门、风扰）的标准化测试方法在本次检索中未见直接文献，暂标“待核实”。本项目若涉及动态工况，需要自行设计并说明不确定度。

### 2.4 代理模型、高斯过程、贝叶斯优化与多目标优化

**GP/DGP。** 与本项目 GP 效率地图最接近的是 Røstum 等（2026）[L40]：该文比较深度高斯过程（DGP）、多层感知机（MLP）与稀疏 GP，使用 19 支直径 7–20 in 螺旋桨的风洞数据，按直径划分训练/测试集，并给出预测不确定度（据摘要）。其对象是**螺旋桨气动性能**而非“电机+电调+桨”的系统效率，但“用 GP 家族给出带不确定度的代理”与本项目 v0.4 的思路高度一致，是本报告认定的最近方法之一。

**其他代理模型。** Mian 等（2021）[L25] 用物理基代理模型 + 空间映射优化薄型电动桨；Karali 等（2024）[L34] 用深度神经网络 + 多目标遗传算法做 UAV 概念设计，摘要称计算时间较传统方法降低三个数量级以上；Alam（2026）[L39] 提出带物理特征的泄漏感知机器学习并做共形不确定度量化（题名级）。这些工作说明代理模型在 UAV 设计链中已较成熟，但多数面向“设计参数 → 性能”的正向预测，而非“实测数据 → 效率地图 → 选型决策”的闭环。

**贝叶斯优化与多目标。** Shahriari 等（2016）[L08] 是 BO 的经典综述；Mourousias 等（2024）[L35] 提出面向高空螺旋桨的多保真优化框架（摘要涉及贝叶斯优化，据检索命中）；多目标方面，Pareto 前沿 + 决策（knee point）是常见做法。项目方向三 v0.4 的 Pareto + knee（29.60 V/52.5%）与 GP σ 补测，在方法谱系上属于“代理模型辅助的多目标 + 主动采样”，与上述工作同源但应用对象不同。

项目内部口径提示：GP 平滑与 Pareto 结果均为计算/SIM 流程产物，需在论文与申报材料中按项目纪律标注 SIM，不能写成台架实验结论。

### 2.5 公开螺旋桨数据库与数据对标

**UIUC Propeller Database** [L01]：官方页面（访问 2026-11-19，HTTP 200）提供 Vols 1–4（2005–2022）数据与整库下载（UIUC-propDB.zip），并给出官方引用格式（Brandt, Deters, Ananda, Dantsker, Selig）。这是小桨低雷诺数数据最常用的公开源，也是本项目方向二对标的基准。

**APC 性能数据** [L02]：APC 官网 “Performance Data” 页面（访问 2026-11-19，HTTP 200）提供厂商性能数据，站点导航现指向 `performance-data-new/`，另有几何数据与文件下载入口。需注意：厂商数据的测试条件、仪器与不确定度未在页面上系统公开（待核实），直接用于论文对标时应说明来源与局限。

**PropFolio** [L03]：页面（访问 2026-11-19，HTTP 200）标题为 “PropFolio - Propeller Performance Database”；UIUC 页面称其为“现代化螺旋桨性能数据库（2026）”，含 APC 性能数据、OpenVSP 三维几何与不同 RPM 区间指标。其版本年份与数据许可**待核实**，引用前需再核对页面说明。

**OSU 数据**：未检索到独立数据库入口；UIUC 页面将其作为对比数据引用，相关测量方法与数据见 McCrink 与 Gregory（2015）[L09] 等。CSV 未单列 OSU 数据库，避免给出无法核验的链接。

**项目方向二现状（内部文档）**：已入库 UIUC Vol.1 APC 10x7E 静态 16 点；模型对 CT 的均值误差 6.14%、最大 14.65%，对 CP 的均值误差 13.83%、最大 14.95%，呈系统性低估 C_P。该结果属于**模型对标结论**（非实测），写作时需与公开数据来源、模型假设一同交代。与文献对照可知：低阶模型在低 Re 小桨上对扭矩/功率的偏差通常大于对推力的偏差，这与 [L06][L09][L11] 关于 Re 效应与 BEMT 适用范围的讨论方向一致；但具体数值不应外推到其他桨型。

### 2.6 数字孪生、硬件在环与试验设计（DoE）

**数字孪生/虚拟试验台。** Wachłaczenko（2025）[L37] 研究多旋翼 UAV 混合电推进系统的数字孪生（题名级）；Boggero 等（2019）[L15] 给出并联混合推进系统的虚拟试验台；Brulin 等（2024）[L36] 通过仿真与实验多旋翼推进系统生成故障数据库（题名级）。这些工作说明“推进系统 + 数字孪生/故障注入”已有基础，但公开文献多聚焦混合动力或故障诊断，**面向小型多旋翼“电—热—推力”整链效率的数字孪生**在本次检索中未见直接对应（待核实）。

**HIL。** Mishra 与 Kim（2021）[L27] 基于 HIL 仿真分析带 BLDC 推进电机的混合 UAV（题名级），可作为硬件在环方法参照。

**DoE。** 检索到的 DoE/Taguchi 应用主要在气动外形：Antoniou 等（2023）[L31] 用 Taguchi 方法对翼身融合 UAV 的前缘缝翼做参数化研究（题名级，Aerospace 10(8):720）。**未检索到**将析因设计/响应面/Taguchi 直接用于电机—桨—电调推进系统标定或效率地图采样的论文（§1.4）。项目方向一当前的 16 工况（4 电压 × 4 油门）属于全网格扫描而非统计 DoE；若在 v0.5 引入析因/响应面设计以减少标定工况数并量化交互效应，可形成方法学增量（见 §4 G5）。

## 3. 与项目四个方向的关联映射表

| 项目方向 | 项目现状（内部文档口径） | 对应文献 | 文献可借鉴点 | 差异 / 不可直接套用 |
|---|---|---|---|---|
| 方向一：效率链与效率地图 | raw CSV+标定 → η_em/FM/η_sys；稳态自动识别；一阶 RSS 不确定度（η_em ±1.44%、FM/η_sys ±2.26%，k=2）；GP 地图 v0.4（RBF，LOOCV ℓ=0.550、RMSE 0.001662、R²=0.9999，21×21 均值/标准差面） | [L14][L17][L29][L12][L40][L25] | 部件级效率模型与系统级地图表达；以转速/扭矩为独立变量的等值线思路；实验表征建图流程；GP 后验不确定度表达 | 文献多为部件级或厂商数据建图；[L17] 未报告 GP 平滑；本项目的“实测整链 + GP + UQ”组合需自行论证，不能引用文献代证 |
| 方向一：测量与不确定度 | 一阶 RSS 合成、k=2 报告；测试链含推力/扭矩/转速/电压/电流 | [L04][L23][L28][L38][L26][L22] | GUM 的 A/B 类评定与扩展不确定度表达；测试台设计；机载测量与仪器化经验 | 文献多不披露完整不确定度预算；“整链不确定度传播到效率地图”在检索范围内未见直接先例（待核实） |
| 方向一：物理仿真与热模型 | v0.1 16 工况闭环（4 电压×4 油门），推力/η_sys 复原误差 <0.3%/<1.6%；v0.2 电池内阻+温升/铜温漂；v0.4 双节点热网络（22.2 V 满油门 300 s 绕组峰值 82.9 °C、机壳 66.2 °C，冷却至 35 °C 132 s）（内部文档，SIM） | [L37][L15][L36][L27] | 数字孪生/虚拟试验台的分层建模；HIL 闭环验证思路；故障注入数据生成 | 文献对象多为混合动力/故障诊断，非小型多旋翼电—热—推力整链；双节点热网络参数需实测标定，不可照搬文献数值 |
| 方向二：公开数据对标 | UIUC Vol.1 APC 10x7E 静态 16 点入库；CT 均值误差 6.14%/最大 14.65%，CP 均值 13.83%/最大 14.95%（系统性低估 C_P） | [L01][L02][L03][L05][L06][L18][L28] | 数据库选择与引用规范；低 Re 测试条件与 Re 效应讨论；APC 系列测试与数据流程 | UIUC/APC 数据为静态、低 Re、特定装置条件；模型偏差不能外推到其他桨型；厂商数据不确定度未公开 |
| 方向三：匹配与选型 | 插值/多目标/GP 连续匹配；v0.4 Pareto（13×41 候选、knee=29.60 V/52.5%、28 可行/5 前沿）；GP σ 补测 5 点 | [L14][L20][L29][L32][L25] | 解耦优化 + 产品库选型；性能地图全域比较；多目标处理与代理模型加速 | 文献多依赖产品库/厂商数据或设计参数优化；本项目以实测地图为输入，需说明与文献的可比性 |
| 方向三：GP/BO 与补测 | GP 地图 + σ 补测点推荐（SIM）；v0.5 计划贝叶斯优化补测 | [L40][L08][L34][L35][L39] | DGP/稀疏 GP 与预测不确定度；BO 采集函数；多保真优化；共形不确定度量化 | [L40] 对象为桨气动而非系统效率；BO 多用于设计优化而非台架/标定补测；需重新定义目标函数与约束 |
| 方向四：成果与复现 | 软著 V1.0（说明书+源代码页 156 页、29 源文件、102 文件 SHA256 清单）、复现包、论文/竞赛材料（SIM 强制标注） | [L15][L36][L01][L02] | 虚拟试验台/故障数据库的可复现组织方式；公开数据集的引用与版本管理 | 检索范围内无直接面向“效率地图软著/复现包”的文献，方向四主要靠工程实践与规范，不能以文献替代 |

## 4. 创新点/差距分析

### 4.1 文献侧的共性做法

1. **部件建模 + 系统集成**是主流骨架（[L14][L21][L33]）；
2. **地图化表达**在近三年明显增多（[L29][L17]），但“地图”的数据来源多为厂商数据或单一实验单元；
3. **代理模型/优化**已较成熟（[L08][L25][L34][L35][L40]），但目标多为设计参数或气动性能；
4. **测试与数据**方面，公开数据库（[L01][L02][L03]）与方法论文（[L05][L06][L18][L28]）提供了可对标基础，但不确定度披露不足；
5. **数字孪生/HIL** 集中在混合动力与故障诊断（[L15][L27][L36][L37]），与小型多旋翼效率地图的直接结合较少。

### 4.2 差距（G1–G6）与本项目的相对位置

- **G1 整链实测效率地图缺失**：文献或以部件模型拼接（[L14]），或以厂商数据建图（[L29]），或以单一推进单元实测建静态图（[L17]）；“多环境、整链实测 + 平滑 + 不确定度”的地图在检索范围内未见直接对应。→ 本项目方向一 v0.4 的“实测 η 链 + GP 后验”具备差异化空间，但需在论文中明确与 [L17][L29] 的边界。
- **G2 台架不确定度预算与传播薄弱**：公开测试类文献多给性能曲线，少给完整不确定度预算，更少把不确定度传播到效率地图。→ 本项目 k=2 的 RSS 预算（±1.44%/±2.26%）可作为工程贡献点，但应补充 A/B 类分量明细与自由度说明（GUM [L04]）。
- **G3 ESC 效率实测数据稀缺**：ESC 常被当作“黑箱”或并入电机效率；专门讨论 ESC 功率效率设计与测量的工作较少（[L13] 属设计层面，题名级）。→ 项目若能把 ESC 损耗单列并测量，是可写入论文的观测点；但需注意与厂商规格的可比性。
- **G4 GP 不确定度用于“补测决策”的公开案例少**：DGP 用于桨气动预测不确定度（[L40]）、BO 用于设计优化（[L08][L35]），但“用 GP σ 指导台架补测点选择”的公开流程在检索范围内少见。→ 方向三 v0.4 的 GP σ 补测 5 点可整理为可复用流程（v0.5 贝叶斯优化补测）。
- **G5 DoE 未进入推进系统标定**：Taguchi/析因在 UAV 气动外形有应用（[L31]），推进系统标定仍以全网格扫描为主。→ 若 v0.5 用析因/响应面设计压缩标定工况并量化交互效应，可形成方法学空白点的补充（需实验验证收益，不可只做仿真）。
- **G6 电—热—推力整链数字孪生缺位**：现有 DT/HIL 工作偏混合动力或故障（[L15][L27][L36][L37]）。→ 项目 v0.2–v0.4 的电池压降、铜温漂、双节点热网络（SIM）若能与实测效率地图耦合，可作为“轻量数字孪生”的雏形；但必须标注 SIM 并说明参数来源。

**创新点候选（供申报书表述，需与实验证据匹配）**：
1. 面向小型多旋翼的“实测整链效率地图 + GP 后验不确定度”一体化构建流程；
2. 以实测地图为输入的 Pareto 匹配 + knee 决策 + GP σ 补测闭环；
3. 含 ESC 损耗分项的整链效率测量与不确定度预算；
4. 轻量电—热耦合仿真与效率地图的联动（SIM，需实测标定）。

## 5. 本项目可借鉴 vs 不可直接套用

### 5.1 可直接借鉴（含落地建议）

1. **部件—系统分层建模**（[L14][L21]）：把 η_sys 分解为 η_em、FM、η_esc 等因子，逐项测量与合成；本项目已有 η 链定义，可补 ESC 分项。
2. **“转速—扭矩”平面上的地图表达**（[L29]）：项目 GP 地图可用同一坐标做等值线展示，便于与文献对比。
3. **实验表征建图流程**（[L17]）：其“测量 + 辨识 → 静态图”的步骤可作为本项目标定 SOP 的参照（摘要层面）。
4. **GP/DGP 的预测不确定度**（[L40]）：把 GP 后验标准差作为地图质量指标与补测依据；本项目 v0.4 已实现，可进一步做校准检验（如覆盖概率）。
5. **BO 采集函数与多保真思想**（[L08][L35]）：v0.5 贝叶斯优化补测可直接采用 EI/UCB 类采集函数，并把仿真作为低保真信息源（需防止信息泄漏）。
6. **GUM 不确定度框架**（[L04]）：A/B 类评定、合成标准不确定度、k=2 扩展不确定度的表述方式，可直接用于论文与报告。
7. **公开数据库的引用与版本管理**（[L01][L02][L03]）：按官方引用格式标注访问日期与版本；把“公开数据”与“自测数据”分表管理（项目纪律已要求）。
8. **虚拟试验台/故障数据库的组织方式**（[L15][L36]）：复现包可参考其“模型—工况—数据—脚本”四件套结构。

### 5.2 不可直接套用（含原因）

1. **[L29] 的厂商数据路线**：其地图由制造商数据计算，不依赖测量；本项目强调实测，若直接套用会与项目定位冲突，只能作为对照基线。
2. **[L14] 的产品库选型假设**：其方法依赖较完整的商用产品数据库与部件模型；本项目聚焦特定电机/桨/电调组合，产品库覆盖不足时需自建模型。
3. **[L40] 的风洞桨气动数据**：对象是螺旋桨气动性能（CT/CP 等），不含电机/电调损耗；不能把其不确定度结论直接当作系统效率地图的误差。
4. **[L35] 的高空桨多保真框架**：面向高空低 Re/低压环境，与本项目地面台架工况差异大；其保真度层级不可照搬。
5. **[L37] 的混合动力数字孪生**：含发动机/发电机/电池混合架构，结构与多旋翼纯电推进不同；只能借鉴分层建模思想。
6. **[L38] 的测试仪器方案**：面向多旋翼与轻于空气 UAV 的仪器化，设备与量程未公开细节（题名级），不可直接复制其硬件配置。
7. **[L31] 的 Taguchi 气动应用**：用于外形参数研究，不是推进系统标定；方法可迁移，但因子/水平/响应需重新设计。
8. **UIUC/APC 数据本身**：静态、低 Re、特定装置条件，且 APC 厂商数据不确定度未公开；不能把“与数据库吻合”当作“模型正确”的充分证据，需报告偏差分布与适用边界。
9. **文献数值结论**：如 [L29] “最高效率可差 10% 以上”、[L34] “计算时间降三个数量级”等，均为原文献在其对象上的结论，不能直接引用为本项目预期收益。

## 6. 核心结论 5 条

1. **效率地图路线已被公开文献证明有效，但“整链实测 + 平滑 + 不确定度”一体化仍是空白带。** Nam 等（2023）[L29] 用转速—扭矩平面上的部件效率等值线做系统评估，Piljek 等（2020）[L17] 用实验表征建立静态图，Dai 等（2019）[L14] 用部件模型 + 产品库做解耦选型；三者的数据来源分别是厂商数据、单一单元实测与产品库，均未覆盖“多环境整链实测 + GP 后验不确定度”。本项目方向一 v0.4 的组合因此具备可论证的差异化，但必须在论文中明确与上述工作的边界与可比性。
2. **匹配优化的主流是“部件模型 + 数据库/厂商数据 + 解耦或多目标”，以实测效率地图为直接输入并联动补测决策的公开工作很少。** [L14][L20][L29][L32] 代表了解析/地图/集成优化三条路线；本项目方向三 v0.4 的 Pareto（13×41 候选、knee=29.60 V/52.5%、28 可行/5 前沿）+ GP σ 补测 5 点，在方法谱系上同源，但“实测地图 → Pareto → 主动补测”的闭环可整理为方法增量（SIM/计算流程，需实验验证）。
3. **台架与数据方面有可对标的成熟传统，但不确定度与 ESC 效率是薄弱环节。** UIUC [L01]、APC [L02]、PropFolio [L03] 提供了可核验的数据源，[L05][L06][L18][L28] 提供了低 Re 测试方法；然而公开文献普遍不披露完整不确定度预算，ESC 效率多被并入电机或按黑箱处理（[L13] 属设计层面）。本项目 k=2 的 RSS 预算（η_em ±1.44%、FM/η_sys ±2.26%）与 ESC 分项测量若能补齐分量明细，是可写入论文的工程贡献。
4. **GP/DGP 与贝叶斯优化在桨气动与设计优化中已成熟，但用于“推进系统效率地图的主动补测”仍少见。** Røstum 等（2026）[L40] 用 DGP 给出桨气动预测不确定度，Mourousias 等（2024）[L35] 用多保真/贝叶斯优化做高空桨优化，Shahriari 等（2016）[L08] 提供了 BO 综述；本项目把 GP σ 用于台架补测点选择（v0.4 已给 5 点，v0.5 计划贝叶斯优化），可复用其采集函数与校准检验方法，但目标函数需按“测量成本—信息增益”重新定义。
5. **DoE 在 UAV 气动外形有应用，但在推进系统标定中直接应用缺失；这是可写入方案的方法学空白点，但需实验验证。** Antoniou 等（2023）[L31] 用 Taguchi 方法做翼身融合 UAV 参数研究；本次检索未发现将析因/响应面/Taguchi 用于电机—桨—电调标定的公开论文。项目当前 16 工况全网格扫描若在 v0.5 改为析因/响应面设计，可减少工况数并量化交互效应，但收益必须由实测数据检验，不能只以仿真论证。

## 7. 最接近本项目的 4 篇方法对比

| 文献 | 研究对象/数据 | 方法链 | 与本项目的重合点 | 主要差异/不可套用处 | 可操作借鉴 |
|---|---|---|---|---|---|
| **L29** Nam 等（2023），IEEE Aerospace Conference | 2 m 翼展 UAV，8 组桨/机体组合；厂商数据 | 以转速、扭矩为独立变量 → 各部件（ESC/电机/桨/机体）效率等值线 → 系统级地图评估 | 效率地图用于匹配选型；系统级视角；宽工况 | 数据来自制造商而非实测；对象为固定翼机体组合；无 GP/UQ | 地图坐标与等值线表达；把“部件效率 → 系统效率”的合成方式作为对照基线 |
| **L17** Piljek 等（2020），Applied Sciences 10(22):8229 | 多旋翼推进单元（实验） | 实验测量 + 辨识流程 → 推进单元静态性能图 | 以实测数据建效率/推力图；面向多旋翼 | 单一推进单元；摘要未涉及 GP 平滑与不确定度传播；未覆盖选型匹配 | 标定 SOP、静态图构建步骤；作为“实测建图”的方法先例 |
| **L14** Dai 等（2019），IEEE/ASME T-Mech | 多旋翼推进系统；部件模型 + 产品库 | 桨/电机/ESC/电池建模 → 问题解耦为子问题 → 产品库选型 → 实验/统计验证 | 电机—桨—电调—电池整链建模；匹配选型目标（如悬停续航） | 依赖产品库覆盖与部件模型精度；优化目标是设计选型而非实测地图 | 解耦优化框架；把“续航/效率”作为选型目标的建模方式 |
| **L40** Røstum 等（2026），MATEC Web of Conferences 422:02007 | 19 支 7–20 in 螺旋桨风洞数据 | DGP vs MLP vs 稀疏 GP；按直径划分训练/测试 → 预测 + 不确定度 | GP 家族建模；预测不确定度；数据划分与泛化评估 | 对象为桨气动性能，不含电机/电调损耗；非系统效率地图；非台架补测决策 | DGP/稀疏 GP 的选型与校准检验；训练/测试划分与 UQ 报告方式 |

**逐篇要点：**

- **L29（最接近“地图 → 匹配”）**：它把效率地图从“单点性能”推进到“全域视图”，并用 8 组组合说明部件选择可使最高效率相差 10% 以上（据摘要）。对本项目而言，最有价值的是**地图的坐标设计与系统级合成逻辑**；最需要警惕的是其数据来源为厂商数据——这恰好是本项目“实测地图”的差异化所在。
- **L17（最接近“实测建图”）**：它证明“实验测量 + 辨识 → 静态图”的路线可行且可发表。本项目可在其基础上补充 GP 平滑、后验不确定度与多环境覆盖，从而把“静态图”升级为“带不确定度的效率地图”。
- **L14（最接近“整链匹配选型”）**：四类部件建模 + 解耦 + 产品库选型的框架成熟，可作为本项目选型模块的方法学参照；但其“产品库查表”假设与本项目“自测数据建模”不同，需在论文中说明替代关系。
- **L40（最接近“GP + 不确定度”）**：提供了 GP 家族在桨性能预测上的对比与 UQ 报告范式。本项目可借鉴其训练/测试划分与不确定度评估，但需把目标从“桨气动系数”换成“系统效率 η_sys”，并处理电机/电调损耗带来的额外不确定性。

> 说明：本节 4 篇为“最接近”，满足 3–5 篇的要求；其余文献（如 [L12][L20][L32]）在方法上相关但公开摘要不足以支撑逐条对比，故未列入方法对比表，避免过度解读。

## 8. 参考文献（L01–L40，与 `references.csv` 对应）

> 说明：以下条目均由 Crossref/OpenAlex 元数据或官方页面核验；未获取全文者仅题名级引用。DOI 链接统一写作 `https://doi.org/...`。

- [L01] Brandt, J.B.; Deters, R.W.; Ananda, G.K.; Dantsker, O.D.; Selig, M.S. (2022). *UIUC Propeller Database, Vols 1–4*. University of Illinois at Urbana-Champaign. https://m-selig.ae.illinois.edu/props/propDB.html
- [L02] APC Propellers. *Performance Data*（厂商性能数据页面，持续更新）. https://www.apcprop.com/technical-information/performance-data/
- [L03] PropFolio. *Propeller Performance Database*（年份待核实）. https://propfolio.live/
- [L04] JCGM (2008). *Evaluation of measurement data — Guide to the expression of uncertainty in measurement (GUM), JCGM 100:2008*. BIPM. https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf
- [L05] Brandt, J.B.; Selig, M.S. (2011). Propeller Performance Data at Low Reynolds Numbers. *AIAA 2011-1255*. https://doi.org/10.2514/6.2011-1255
- [L06] Deters, R.W.; Ananda Krishnan, G.K.; Selig, M.S. (2014). Reynolds Number Effects on the Performance of Small-Scale Propellers. *AIAA 2014-2151*. https://doi.org/10.2514/6.2014-2151
- [L07] Theys, B.; Dimitriadis, G.; Hendrick, P.; De Schutter, J. (2016). Influence of propeller configuration on propulsion system efficiency of multi-rotor UAVs. *2016 International Conference on Unmanned Aircraft Systems (ICUAS)*. https://doi.org/10.1109/ICUAS.2016.7502520
- [L08] Shahriari, B.; Swersky, K.; Wang, Z.; Adams, R.P.; de Freitas, N. (2016). Taking the Human Out of the Loop: A Review of Bayesian Optimization. *Proceedings of the IEEE, 104(1)*. https://doi.org/10.1109/JPROC.2015.2494218
- [L09] McCrink, M.H.; Gregory, J.W. (2015). Blade Element Momentum Modeling of Low-Re Small UAS Electric Propulsion Systems. *AIAA 2015-3296*. https://doi.org/10.2514/6.2015-3296
- [L10] McCrink, M.H.; Gregory, J.W. (2017). Blade Element Momentum Modeling of Low-Reynolds Electric Propulsion Systems. *Journal of Aircraft*. https://doi.org/10.2514/1.C033622
- [L11] MacNeill, R.; Verstraete, D. (2017). Blade element momentum theory extended to model low Reynolds number propeller performance. *The Aeronautical Journal*. https://doi.org/10.1017/aer.2017.32
- [L12] Shi, D.; Dai, X.; Zhang, X.; Quan, Q. (2017). A Practical Performance Evaluation Method for Electric Multicopters. *IEEE/ASME Transactions on Mechatronics*. https://doi.org/10.1109/TMECH.2017.2675913
- [L13] Shin, Y.T.; Teh, Y.-K. (2018). Design analysis and considerations of power efficient electronic speed controller for small-scale quadcopter unmanned aerial vehicle. *2018 IEEE 8th Annual Computing and Communication Workshop and Conference (CCWC)*. https://doi.org/10.1109/CCWC.2018.8301770
- [L14] Dai, X.; Quan, Q.; Ren, J.; Cai, K.-Y. (2019). An Analytical Design-Optimization Method for Electric Propulsion Systems of Multicopter UAVs With Desired Hovering Endurance. *IEEE/ASME Transactions on Mechatronics*. https://doi.org/10.1109/TMECH.2019.2890901
- [L15] Boggero, L.; Corpino, S.; De Martin, A.; Evangelista, G.; Fioriti, M.; Sorli, M. (2019). A Virtual Test Bench of a Parallel Hybrid Propulsion System for UAVs. *Aerospace, 6(7), 77*. https://doi.org/10.3390/aerospace6070077
- [L16] Dantsker, O.D.; Imtiaz, S.; Caccamo, M. (2019). Electric Propulsion System Optimization for Long-Endurance and Solar-Powered Unmanned Aircraft. *AIAA Propulsion and Energy 2019 Forum, AIAA 2019-4486*. https://doi.org/10.2514/6.2019-4486
- [L17] Piljek, P.; Kotarski, D.; Krznar, M. (2020). Method for Characterization of a Multirotor UAV Electric Propulsion System. *Applied Sciences, 10(22), 8229*. https://doi.org/10.3390/app10228229
- [L18] Dantsker, O.D.; Caccamo, M.; Deters, R.W.; Selig, M.S. (2020). Performance Testing of Aero-Naut CAM Folding Propellers. *AIAA AVIATION 2020 Forum, AIAA 2020-2762*. https://doi.org/10.2514/6.2020-2762
- [L19] Jatsun, S.; Emelyanova, O.; Martinez Leon, A.S. (2020). Design of an Experimental Test Bench for a UAV Type Convertiplane. *IOP Conference Series: Materials Science and Engineering, 714, 012009*. https://doi.org/10.1088/1757-899X/714/1/012009
- [L20] Duan, D.; Wang, Z.; Wang, Q.; Li, J. (2020). Research on Integrated Optimization Design Method of High-Efficiency Motor Propeller System for UAVs With Multi-States. *IEEE Access*. https://doi.org/10.1109/ACCESS.2020.3014411
- [L21] Amici, C.; Ceresoli, F.; Pasetti, M.; Saponi, M.; Tiboni, M.; Zanoni, S. (2021). Review of Propulsion System Design Strategies for Unmanned Aerial Vehicles. *Applied Sciences, 11(11), 5209*. https://doi.org/10.3390/app11115209
- [L22] Amici, C.; Ceresoli, F.; Saponi, M.; Pasetti, M.; Zanoni, S.; Borboni, A.; Tiboni, M.; Faglia, R. (2021). Experimental Characterization of an Electrical Propulsion Unit for Service UAVs. *I4SDG Workshop 2021 (Springer, Mechanisms and Machine Science)*. https://doi.org/10.1007/978-3-030-87383-7_34
- [L23] Hernandez, J.D.; Nandar, J.E.; Changoluisa, I.D.; Cruz, P.J.; Valencia, E. (2021). Test-bench Development for the Efficiency Analysis of UAV Motor-Propeller Sets. *2021 IEEE ETCM*. https://doi.org/10.1109/ETCM53643.2021.9590717
- [L24] Vargas Loureiro, E.; Oliveira, N.L.; Hallak, P.H.; de Souza Bastos, F.; Rocha, L.M.; Delmonte, R.G.P.; Lemonge, A.C. de C. (2021). Evaluation of low fidelity and CFD methods for the aerodynamic performance of a small propeller. *Aerospace Science and Technology, 108, 106402*. https://doi.org/10.1016/j.ast.2020.106402
- [L25] Mian, H.H.; Wang, G.; Zhou, H.; Wu, X. (2021). Optimization of thin electric propeller using physics-based surrogate model with space mapping. *Aerospace Science and Technology, 208, 106563*. https://doi.org/10.1016/j.ast.2021.106563
- [L26] Zhao, A.; Zhang, J.; Li, K.; Wen, D. (2021). Design and implementation of an innovative airborne electric propulsion measure system of fixed-wing UAV. *Aerospace Science and Technology, 109, 106357*. https://doi.org/10.1016/j.ast.2020.106357
- [L27] Mishra, A.K.; Kim, T. (2021). Analysis of a Hybrid Unmanned Aerial Vehicle with a BLDC Propulsion Motor Based on HIL Simulation. *2021 IEEE ITEC*. https://doi.org/10.1109/ITEC51675.2021.9490148
- [L28] Dantsker, O.D.; Caccamo, M.; Deters, R.W.; Selig, M.S. (2022). Performance Testing of APC Electric Fixed-Blade UAV Propellers. *AIAA AVIATION 2022 Forum, AIAA 2022-4020*. https://doi.org/10.2514/6.2022-4020
- [L29] Nam, H.-S.; Hwang, H.-S.; Lee, S.-H.; Lee, H.-T. (2023). Electric Propulsion System Optimization Using Performance Maps. *2023 IEEE Aerospace Conference*. https://doi.org/10.1109/AERO55745.2023.10115581
- [L30] Goli, S.; Kurtuluş, D.F.; Alhems, L.M.; Memon, A.M.; Imran, I.H. (2023). Experimental study on efficient propulsion system for multicopter UAV design applications. *Results in Engineering, 20, 101555*. https://doi.org/10.1016/j.rineng.2023.101555
- [L31] Antoniou, S.; Kapsalis, S.; Panagiotou, P.; Yakinthos, K. (2023). Parametric Investigation of Leading-Edge Slats on a Blended-Wing-Body UAV Using the Taguchi Method. *Aerospace, 10(8), 720*. https://doi.org/10.3390/aerospace10080720
- [L32] Xu, J.; Jin, W.; Lin, H.; Zhang, B.; Guo, H. (2024). Multiobjective Optimization Method to Maximize Power Density and Efficiency of an Electric Propulsion Motor in UAV Applications. *IEEE Transactions on Transportation Electrification*. https://doi.org/10.1109/TTE.2023.3319008
- [L33] Etewa, M.; Hassan, A.F.; Safwat, E.; Abozied, M.A.H.; El-Khatib, M.M.; Ramirez-Serrano, A. (2024). Performance Estimation of Fixed-Wing UAV Propulsion Systems. *Drones, 8(9), 424*. https://doi.org/10.3390/drones8090424
- [L34] Karali, H.; Inalhan, G.; Tsourdos, A. (2024). Advanced UAV Design Optimization Through Deep Learning-Based Surrogate Models. *Aerospace, 11(8), 669*. https://doi.org/10.3390/aerospace11080669
- [L35] Mourousias, N.; Marinus, B.G.; Runacres, M.C. (2024). A novel multi-fidelity optimization framework for high-altitude propellers. *Aerospace Science and Technology, 154, 109407*. https://doi.org/10.1016/j.ast.2024.109407
- [L36] Brulin, P.-Y.; Khenfri, F.; Rizoug, N. (2024). Generating Fault Databases Through Simulated and Experimental Multi-Rotor UAV Propulsion Systems. *IEEE Transactions on Vehicular Technology*. https://doi.org/10.1109/TVT.2024.3352172
- [L37] Wachłaczenko, M.J. (2025). Hybrid Electric Propulsion System Digital Twin for Multi-Rotor Unmanned Aerial Vehicles. *Sustainability, 17(11), 4901*. https://doi.org/10.3390/su17114901
- [L38] Cox, B.; Dantsker, O.D.; Deters, R.W. (2025). Propulsion System Testing Instrumentation for Multi-Rotor and Lighter-Than-Air UAVs. *AIAA SCITECH 2025 Forum, AIAA 2025-0252*. https://doi.org/10.2514/6.2025-0252
- [L39] Alam, M.I. (2026). Leakage-aware machine learning with physics-based features for propeller performance prediction and conformal uncertainty quantification. *Results in Engineering*. https://doi.org/10.1016/j.rineng.2026.113724
- [L40] Røstum, H.H.; Afonso, F.; Morlier, J. (2026). Deep Gaussian Processes for Probabilistic Prediction of UAV Propeller Aerodynamics. *MATEC Web of Conferences, 422, 02007*. https://doi.org/10.1051/matecconf/202642202007

## 9. 附录：核验记录与待核实清单

**核验方法记录：**
- 文献元数据：Crossref REST API（`https://api.crossref.org/works?filter=doi:...`）批量核对题名/作者/年份/期刊；OpenAlex（`https://api.openalex.org/works?filter=doi:...`）交叉核对；Semantic Scholar 单篇摘要接口用于 [L14] 等 IEEE 论文摘要。
- 数据库页面：UIUC、APC、PropFolio 均于 2026-11-19 访问并读取页面文字；GUM 为 BIPM 官方 PDF（`application/pdf`，`web_fetch` 不可解析正文，URL 可访问）。
- 摘要可得性：[L14][L17][L29][L34][L40] 摘要已核读；[L12][L13][L20][L30][L31][L32][L33][L35][L36][L37][L38][L39] 等仅题名/元数据级（部分摘要不可得或未系统读取），正文已按题名级表述处理。

**待核实清单：**
1. PropFolio 的发布年份与数据许可（UIUC 页面称“2026”，需以 PropFolio 官方说明为准）；
2. APC 性能数据的测试条件与不确定度说明（页面未系统公开）；
3. OSU 螺旋桨数据是否存在独立可下载入口（未检索到）；
4. [L22] 的丛书卷号/页码；[L23] 与 [L27] 的会议全称与页码；[L20] 的文章号/页码；
5. [L30] 摘要中关于 ESC 的具体实验细节（仅据检索命中判断涉及 ESC，未核读摘要全文）；
6. [L31] 是否为 Taguchi 正交表设计还是仅“Taguchi 方法”泛称（题名级）；
7. 中文文献缺口：知网未检索，建议 v0.2 补检（主题词：多旋翼 效率地图、电机 螺旋桨 匹配、拉力台 不确定度）；
8. 动态推力/扭矩测试的标准化方法：本次检索未见直接文献，待核实。

## 变更记录

- 0.1（2026-11-19）：首次形成外部文献调研报告；完成 40 条来源核验与 CSV 配套；明确整链实测地图、不确定度传播、ESC 效率、GP 补测决策与 DoE 标定五个差距点。
