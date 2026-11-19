# 多旋翼 UAV 电机-螺旋桨-电调系统效率地图与匹配优化——研究现状调研简报

> 用途：为《大学生创新创业训练计划项目申报表》（创新训练项目）提供文献与事实支撑。
> 编制说明：本简报全部文献均经实际检索核实（Crossref/DOI 记录、出版社页面、标准信息页），每一条给出 DOI 或可访问 URL；凡未取得原文全文、仅依据题录/摘要/页面信息判断的论断，均在正文中标注「据题录/摘要」或「待核实」。**未收录任何无法核实的文献。**

---

## A. 研究现状及发展动态（初稿）

多旋翼无人机的续航与载荷能力受制于"电池能量密度—动力系统效率"这对矛盾；在电池短期难有量级突破的背景下，提升电机、螺旋桨、电调（ESC）及其匹配的效率成为提升航时最现实的途径。围绕"效率如何测、如何建模、如何优化"，国内外已形成若干相对独立的研究脉络。

**（1）效率评价与地面测试。** 国外较早建立系统化表征方法：Piljek 等提出多旋翼电推进系统的完整台架表征流程，同步测量推力、扭矩、转速与电压、电流、功率，获得部件与系统效率随工况的变化[1]；Zhu 等实测发现小尺度桨低雷诺数下性能分散显著，须实测而非缩比外推[3]；Goli 等通过实验讨论部件匹配对系统效率的影响[4]。国内赵安敏等（北航/天鹰）搭建无人机电动力测试系统，多工况下推力、扭矩、电机效率的数值解与实测误差分别约 1.02%、10%、10.04%[2]，说明**电参量与力学量的同步测量精度、电机效率的间接推算误差是台架建设的关键难点**。Park 等对太阳能高空长航时螺旋桨以叶素动量理论结合最小诱导损失设计，并用 Kriging 代理模型与风洞试验验证[15]，代表"设计—仿真—实测"闭环。总体看，国外偏重方法与数据开放（如 Brandt 与 Selig 的低雷诺数桨数据库[14]），国内偏重测试系统研制，**公开的宽工况系统级效率数据集仍稀缺**。

**（2）电机-螺旋桨匹配与选型优化。** Dai 等以效率为目标优化部件选型，将电机效率 MAP、螺旋桨特性与任务剖面耦合求解最优组合[7]，是"匹配寻优"最清晰的代表工作；de Angelis 等建立电多旋翼性能分析与最优尺度方法，给出桨径、转速与电机参数的匹配关系[6]；Delbecq 等基于相似律建立高效尺度化与优化方法[8]；Biczyski 等把选型与飞行时间预估统一在一个 sizing 框架内[9]。这些工作表明：**系统效率非单部件效率的简单乘积，而是随油门、电压、转速、来流强耦合的非线性函数，须靠"匹配"而非"各自最优"取得全局最优**。但其优化多以解析模型或厂商数据为基础，缺乏自建台架的实测闭环。

**（3）效率地图与数据驱动建模。** 传统方法依赖等效电路、叶素理论等机理模型，参数辨识成本高、外推弱，难以刻画电调非线性损耗。近年数据驱动兴起：Goli 等用神经网络评估无人机电推进系统性能[5]，并实现 UAV 动力总成推力预测[11]；Kosova 等用 ANN 直接预测无刷直流电机与螺旋桨效率[12]。这类方法**以台架实测数据为输入，可容纳电机、电调、螺旋桨的非线性与耦合，输出连续的效率/推力映射（即"效率地图"），并可直接嵌入优化回路作为代理模型**。不足是公开研究多为单一部件或单一桨型，样本与工况覆盖有限，对"电压—油门—转速"三维工况的联合建模及不确定性量化仍不充分。

**（4）电调效率、多目标优化与控制分配。** 电调损耗（开关、导通及驱动方式差异）在中小功率多旋翼中不可忽略，但难直接测量，常并入"电机+电调"整体效率；正弦驱动、能量回馈架构已量产（如 DJI E800，见 D-6）。优化上，遗传算法、NSGA-II 等多目标方法被广泛用于桨型/电机/电压组合寻优（本项目自行实现验证）；Madruga 等用神经网络补偿气动效应、改进控制分配[10]，说明**同一推力需求在不同转速分配下电功率不同，控制分配层同样存在效率优化空间**，为"效率地图"向控制层延伸提供接口。

**（5）趋势小结。** 该方向正从"单部件机理建模"走向"系统级实测+数据驱动代理模型+多目标匹配优化"，从"地面静态台架"走向"含来流/姿态的宽域工况"，从"效率评价"走向"效率驱动的设计—控制一体化"。**尚未见公开报道同时具备：自建同步测量台架、覆盖电压×油门×转速的宽工况效率地图、以系统效率为目标的电机-KV/桨径-螺距/电调参数/电压联合寻优。** 这正是本项目切入点（基于有限检索，待核实）。

---

## B. 参考文献

> 格式参照 GB/T 7714—2015（电子资源/期刊/会议）。所有条目均经 Crossref DOI 记录、出版社页面或标准信息页核实；末尾括注核实方式。

[1] PILJEK P, KOTARSKI D, KRZNAR M. Method for characterization of a multirotor UAV electric propulsion system[J]. Applied Sciences, 2020, 10(22): 8229. https://doi.org/10.3390/app10228229 （Crossref 记录核实）

[2] ZHAO A, WANG T, LIU D. Design and research of an electric unmanned aerial vehicle power system[J]. Journal of Physics: Conference Series, 2024, 2746(1): 012029. https://doi.org/10.1088/1742-6596/2746/1/012029 （IOP 文章页全文题录+摘要核实，含误差数据）

[3] ZHU H, JIANG Z, ZHAO H, et al. Aerodynamic performance of propellers for multirotor unmanned aerial vehicles: measurement, analysis, and experiment[J]. Shock and Vibration, 2021, 2021: 9538647. https://doi.org/10.1155/2021/9538647 （Crossref 记录核实）

[4] GOLI S, KURTULUŞ D F, ALHEMS L M, et al. Experimental study on efficient propulsion system for multicopter UAV design applications[J]. Results in Engineering, 2023, 20: 101555. https://doi.org/10.1016/j.rineng.2023.101555 （Crossref 记录核实）

[5] GOLI S, KURTULUŞ D F, WAQAR M, et al. Artificial neural network for the evaluation of electric propulsion system in unmanned aerial vehicles[J]. Neural Computing and Applications, 2025, 37: 8945-8961. https://doi.org/10.1007/s00521-025-11043-6 （Crossref 记录核实）

[6] de ANGELIS E L, GIULIETTI F, ROSSETTI G, et al. Performance analysis and optimal sizing of electric multirotors[J]. Aerospace Science and Technology, 2021, 118: 107057. https://doi.org/10.1016/j.ast.2021.107057 （Crossref 记录核实）

[7] DAI Y, 等. Efficiency optimization and component selection for propulsion systems of electric multicopters[J]. IEEE Transactions on Industrial Electronics, 2019, 66: 7800-. https://doi.org/10.1109/TIE.2018.2885715 （经 Crossref 收录该文的参考文献条目核实；作者全名与终止页码待核实）

[8] DELBECQ S, BUDINGER M, OCHOTORENA A, et al. Efficient sizing and optimization of multirotor drones based on scaling laws and similarity models[J]. Aerospace Science and Technology, 2020, 102: 105873. https://doi.org/10.1016/j.ast.2020.105873 （Crossref 记录核实）

[9] BICZYSKI M, SEHAB R, WHIDBORNE J F, et al. Multirotor sizing methodology with flight time estimation[J]. Journal of Advanced Transportation, 2020, 2020: 9689604. https://doi.org/10.1155/2020/9689604 （Crossref 记录核实）

[10] MADRUGA S P, TAVARES A H B M, LUIZ S O D, et al. Aerodynamic effects compensation on multi-rotor UAVs based on a neural network control allocation approach[J]. IEEE/CAA Journal of Automatica Sinica, 2022, 9(2): 295-312. https://doi.org/10.1109/JAS.2021.1004266 （Crossref 记录核实）

[11] GOLI S, KURTULUŞ D F, WAQAR M, et al. Data-driven thrust prediction for UAV powertrains using artificial neural networks[J]. Neural Computing and Applications, 2026, 38(8): 264. https://doi.org/10.1007/s00521-026-12003-4 （Crossref 完整记录+摘要核实）

[12] KOSOVA İ, YÖNETKEN A, BAYRAM F. Prediction of brushless DC motor and propeller efficiency using an artificial neural network model[J]. Düzce Üniversitesi Bilim ve Teknoloji Dergisi, 2024, 12(4). https://doi.org/10.29130/dubited.1424236 （Crossref 记录核实）

[13] GUR O. Maximum propeller efficiency estimation[J]. Journal of Aircraft, 2014, 51(6): 2035-2038. https://doi.org/10.2514/1.C032557 （Crossref 记录核实）

[14] BRANDT J, SELIG M. Propeller performance data at low Reynolds numbers[C]//49th AIAA Aerospace Sciences Meeting. Reston: AIAA, 2011. https://doi.org/10.2514/6.2011-1255 （经两篇 Crossref 收录文献的参考文献条目互相印证；原文未获取）

[15] PARK D, LEE Y, CHO T, et al. Design and performance evaluation of propeller for solar-powered high-altitude long-endurance unmanned aerial vehicle[J]. International Journal of Aerospace Engineering, 2018, 2018: 5782017. https://doi.org/10.1155/2018/5782017 （Crossref 完整记录+摘要核实）

**标准与行业资料（不计入上述 15 条文献）**

[16] 国家市场监督管理总局, 国家标准化管理委员会. 民用无人驾驶航空器系统安全要求: GB 42590—2023[S]. 北京: 中国标准出版社, 2023. https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=0DC41035BA23EF2C5B94E6482492AF1E （国家标准全文公开系统条目页核实）

[17] 民用轻小型无人机系统环境试验方法 第1部分：总则: GB/T 38924.1—2020[S]. https://www.spc.org.cn/online/fd8635692bf72b7b1490be3e4a315513.html （中国标准在线服务网条目页核实；发布年份以页面为准）

---

## C. 事实卡片

### C-1 典型效率范围（**重要：以下为工程经验区间，本次检索未获得权威统一统计口径，标注"待核实"，须以自建台架实测为准**）

| 对象 | 常见区间 | 说明与依据 |
|---|---|---|
| 螺旋桨气动效率 η_prop（静推力/悬停，小直径低雷诺数桨） | 约 0.45~0.70（经验值，待核实） | 小尺度桨低雷诺数下效率显著低于全尺寸桨；Gur 给出螺旋桨效率上限的理论估算方法[13]，但实际值随桨型/工况大幅变化 |
| 无刷电机本体效率 | 约 0.80~0.92（经验值，待核实） | 高效区通常位于额定转速/扭矩的 60%~85%；轻载与堵转区效率快速下降 |
| 电调（ESC）效率 | 约 0.93~0.98（经验值，待核实） | 开关+导通损耗为主；正弦驱动优于方波驱动（DJI E800 采用正弦驱动并支持减速能量回收，见 D-6）。**电调损耗难以单独测量，公开文献多并入"电机+电调"整体处理** |
| 系统总效率（电池电功率 → 推力功率 P=T^(3/2)/√(2ρA)） | 约 0.35~0.60（经验值，待核实） | 典型悬停工况下系统效率偏低；这也是"效率地图"存在的意义——效率随工况变化可达数倍，单点标称效率不足以支撑选型 |

> 可核实的**测量误差**基准：赵安敏等的测试系统在相同工况下，推力、扭矩、电机效率的数值解与实测平均误差分别约 1.02%、10%、10.04%[2]——可作为本项目台架精度设计的对标参考。

### C-2 常见测试台架构成与传感器方案

依据文献[1][2][3][4]归纳的典型构成：

1. **机械台架**：铝型材/钢板底座 + 立柱 + 推力测量悬臂（单自由度/六分量），需做动平衡与减振；桨盘距地面/障碍物距离须控制以减小地面效应（文献[3]强调小桨对边界条件敏感）。
2. **力/力矩测量**：推力用称重式拉压力传感器（Load Cell）或单点式称重传感器；扭矩用**反扭矩台（torque stand，电机定子反装于轴承上，由力臂+称重传感器测得反扭矩）**或旋转扭矩传感器（滑环/遥测）。
3. **转速测量**：光电/霍尔转速传感器（桨毂贴反光片或磁钢），或由电调 RPM 反馈（精度较低，需标定）。
4. **电参量测量**：直流电子负载/功率分析仪同步采集母线电压、电流、功率（推荐四线制、高采样率 ≥1 kHz 以捕捉电调 PWM 纹波）；三相侧可选功率分析仪测相电压/相电流。
5. **控制与采集**：PWM/舵机测试仪或单片机/DAC 给定油门（0~100%，步进 1%~5%），LabVIEW/DAQ（如 NI USB-6009/6210、HX711+Arduino）同步记录；每工况稳定 3~5 s 后取平均，重复 3 次。
6. **环境控制（进阶）**：风洞或轴流风机提供来流（模拟前飞），温湿度/气压记录；电池侧用可编程直流电源替代电池以固定电压并消除电压跌落影响（**这是把"电压"作为独立工况变量的关键**）。

### C-3 常用建模方法对比

| 方法 | 优点 | 缺点 | 代表文献 |
|---|---|---|---|
| 电机等效电路（d-q/稳态） | 物理意义明确、参数少 | 难以刻画铁耗/开关损耗；参数随温度漂移 | 通用电机学；[4] |
| 螺旋桨叶素动量理论 BEMT / 最小诱导损失 | 可外推、可指导设计 | 低雷诺数翼型数据缺乏，静推力工况精度差 | [15] |
| 相似律/缩放律 | 便于快速估算与选型 | 忽略雷诺数效应，跨尺度误差大 | [8][9] |
| 响应面/Kriging 代理模型 | 样本需求小、可做优化 | 高维工况下精度受限 | [15] |
| 人工神经网络 ANN / 数据驱动 | 拟合强非线性、可多输入多输出、易嵌入优化 | 需足够实测数据、外推不可靠、可解释性差 | [5][11][12] |
| 多物理场/CFD 联合仿真 | 细节丰富 | 计算成本高，难以在线使用 | [2][15] |

### C-4 常用优化算法（据文献调研与本项目预研）

- **单目标**：序列二次规划 SQP、fmincon、遗传算法 GA、粒子群 PSO（用于给定任务剖面下的效率最大化）。
- **多目标**：**NSGA-II**（效率—航时—成本/重量—噪声的 Pareto 前沿）、MOEA/D；配合代理模型（Kriging/ANN）构成"代理模型 + 进化算法"的经典组合。
- **选型类组合优化**：枚举 + 剪枝（电机×桨×电压组合数有限时最可靠）、混合整数规划。
- **本项目的建议**：先用枚举建立"可信基准"，再用 NSGA-II 求 Pareto 前沿，最后在实测数据上回代验证（避免"优化结果只在模型里最优"）。

### C-5 相关国家标准/行业标准（本次检索确认存在的）

| 编号 | 名称 | 与本项目关系 |
|---|---|---|
| GB 42590—2023 | 民用无人驾驶航空器系统安全要求（强制性国标） | 安全性要求；不含效率测试方法[16] |
| GB/T 38924.1—2020 | 民用轻小型无人机系统环境试验方法 第1部分：总则（系列标准） | 环境适应性试验；不含动力系统效率测试[17] |

> **待核实（重要）**：本次在公开渠道（国家标准全文公开系统、全国标准信息公共服务平台、中国标准在线服务网）检索，**未发现专门针对"多旋翼动力系统效率测试/效率地图"的国家标准或行业标准**。该结论受检索范围限制，申报书中建议表述为"现有标准多集中于安全性与环境适应性，动力系统效率测试方法尚缺乏统一规范（据公开标准信息检索，待进一步核实）"，而不宜断言"无标准"。

### C-6 典型电机 KV 与桨径规格范围（产业公开信息）

- **电机 KV**：小型多旋翼常用 300~1000 KV；高压大拉力平台偏低 KV（如 T-MOTOR MN5208 KV340，商家页面标称单轴最大推力约 4.1 kg，**该数值来自经销页面，待核实**）。
- **桨径**：5~30 英寸常见；工业级多旋翼多用 15~30 英寸（如 T-MOTOR HEP-L 30 英寸碳纤维多旋翼桨，页面：https://store.tmotor.com/cn/product/hep-l-30-10-5-carbon-fiber-multirotor-propeller.html ）。
- **电压平台**：3S~12S（11.1~44.4 V）锂聚合物电池为主；大拉力平台多用 6S~12S。
- **配套关系经验**：KV 越高→同电压下转速越高→需配小直径/小螺距桨；KV 越低→配大桨。这一"KV—桨径—电压"三角关系正是本项目匹配寻优的核心变量组。

---

## D. 可写入"已有基础/研究现状"的行业与产业事实（每条 1 句 + 来源）

1. **低空经济已成为国家战略性新兴产业方向，而续航能力是制约无人机规模化应用的核心瓶颈之一**——北航学报一篇氢燃料电池混合动力无人机综述指出："在低空经济崛起与绿色航空发展的背景下，氢燃料电池混合动力无人机凭借高能量密度和零排放等优势，成为突破传统锂电无人机续航瓶颈的关键路径"。来源：http://bhxb.buaa.edu.cn/bhzk/article/pdf/preview/2007abbf-2dbb-4097-bd1f-cce07f6be240 （摘要页；正式卷期页码待核实）
2. **低空飞行器动力系统已形成多元技术路线，其发展现状与关键挑战被系统性梳理**，说明动力系统是低空飞行器竞争力的核心环节。来源：《航空工程进展》"低空飞行器动力系统"综述，http://hkgcjz.ijournals.net.cn/hkgcjz/article/pdf/2026022 （题录/摘要级，卷期待核实）
3. **我国已发布民用无人驾驶航空器系统强制性国家标准 GB 42590—2023**，标志无人机系统安全要求进入强制规范阶段。来源：https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=0DC41035BA23EF2C5B94E6482492AF1E
4. **民用轻小型无人机已建立环境试验方法系列标准（GB/T 38924 系列）**，但标准体系侧重环境适应性与安全性，尚未覆盖动力系统效率的测试与评价方法（据公开标准信息检索，待核实）。来源：https://www.spc.org.cn/online/fd8635692bf72b7b1490be3e4a315513.html
5. **产业界已通过电调架构升级提升系统效率**：DJI E800 多旋翼动力系统面向 3~5 kg 级机型，采用"从方波驱动到正弦驱动"的电调架构，并可在减速时回收能量以降低能耗。来源：https://www-v1.dji.com/cn/e800.html （产品页）
6. **工业级多旋翼桨叶已形成系列化规格（如 30 英寸碳纤维桨）**，桨型选择空间大，客观上使"匹配寻优"具有显著工程价值。来源：https://store.tmotor.com/cn/product/hep-l-30-10-5-carbon-fiber-multirotor-propeller.html
7. **高校已开展动力系统效率测试台架研制**（如北航团队的无人机电动力测试系统，可验证推进系统效率并为螺旋桨数值计算提供校核[2]），说明"自建台架"是本领域通用且被认可的本科/研究生创新训练路径。
8. **西北工业大学机构知识库中检索到相关学位论文《电动固旋翼无人机动力系统建模与优化设计》**（题名来自检索结果摘要；原链接已失效，作者、年份与学位类型**待核实**），可作为"本校已有研究基础"的线索，但**在申报书中引用前必须核实原文**。来源（失效）：https://ir.nwpu.edu.cn/bitstream/39AN3IGR/271308/2/1071941pdf.pdf

---

## 附：本次调研的诚实性说明与待办

1. **已核实**：B 部分 [1]–[6]、[8]–[13]、[15] 的题录信息（标题/期刊/年/卷/页/DOI）来自 Crossref 官方 API 返回；[2] 另经 IOP 文章页确认作者、单位与摘要原文；[16][17] 经标准信息平台条目页确认。
2. **部分核实**：[7]（Dai 等）经 Crossref 收录文献的参考文献条目确认 DOI 与标题，作者全名与页码未获取；[14]（Brandt & Selig）经两篇文献的参考文献列表互证，原文未获取。
3. **未收录**：检索中出现的若干无法确认作者/年份的条目（如 J. Phys.: Conf. Ser. 2111:012005 "A Simple Brushless Motor and Propeller Test Stand"、AIAA 2022-4020 Dantsker 等）——其存在性有线索但题录不完整，本着"宁可少而真"原则不列入正式参考文献，若需使用请先补齐题录。
4. **必须标注"待核实"的内容**：① C-1 全部效率区间（工程经验值）；② "未见公开报道同时具备台架+宽工况地图+联合寻优"的判断；③ "国标未覆盖效率测试方法"的结论；④ 西工大学位论文的作者与年份；⑤ 具体厂商标称推力数值。
5. **建议下一步**：若需中文核心期刊文献（如《航空学报》《航空动力学报》《中国惯性技术学报》等），需通过知网/万方/维普机构账号检索并核验，本次公开检索未能稳定访问其全文页；建议由团队用学校图书馆账号补 3~5 篇中文文献并替换/补充 B 部分，以增强申报书的中文文献支撑。
