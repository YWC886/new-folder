# 效率建模、效率地图与匹配优化技术调研

> **项目**：多旋翼无人机电机—螺旋桨—电调系统效率地图构建与匹配优化（大创创新训练项目）
> **文档定位**：`research_brief.md` 回答"做什么、别人做到哪"，`bench_tech.md` 回答"怎么测、测得准不准"，本文回答"**测完怎么建模、怎么成图、怎么优化选型**"。
> **去重约定**：`research_brief.md` 已著录的 15 篇文献与 2 项标准不再重复著录，正文以"简报[n]"标注（如 Dai 等 IEEE TIE 2019 为简报[7]）；`bench_tech.md` §1 已给出的效率定义与误差传播，本文只引用结论并保持符号一致（标注"同 bench §1.4"）。
> **可信度标注**：文中凡标 `[实测]` 者为文献/数据库数值，`[经验]` 为工程经验值，`[待验证]` 为机理推断或学界尚未定论，须由本项目台架数据检验。

---

## 0 结论速览

1. **效率链可乘性成立但有前提**：$\eta_{sys}=\eta_{esc}\eta_{mot}\eta_{prop}$ 只在各环节功率定义首尾相接时成立；整机台架只能可靠分离"电调+电机"合并效率与螺旋桨悬停效率 $FM$，两者相乘即得地图主指标 $\eta_{sys}$。
2. **电压维度有明确的机理最优点**：固定 $(T,n)$ 时电调导通损耗 $\propto I^2\propto 1/V_{dc}^2$、开关损耗 $\propto V_{dc}$，故存在 $V^*=(2k_1/k_2)^{1/3}$。这是"把供电电压当独立工况变量"最硬的立论依据，也是本项目区别于既有文献的切入点。
3. **电机高效区是一条脊线而非一个点**：给定转速下最优转矩 $T_{opt}=\sqrt{P_0/c}$（可变损耗=固定损耗），$T_{opt}$ 随转速上升而增大；用 5 个参数即可复现 80–90% 的效率面。
4. **地图主坐标建议 $(T,n)$ 或 $(T,V_{dc})$**，油门只作辅助坐标——油门是"指令量"，同一油门在不同电压下对应不同工作点，用它作坐标会把电压效应混进桨的特性里。
5. **建模首选高斯过程（Matérn 5/2 + WhiteKernel）**：100–200 点/组合即可给出带方差的效率面，方差图可直接标出"该加密测哪里"；规则网格配双三次样条作快速查表，TPS/RBF 作交叉校验。
6. **匹配优化是混合整数多目标问题**，推荐"GP 代理 + NSGA-II + 膝点决策 + 台架复测"闭环；纯枚举只用于 2–3 变量的基准校核。量级上 $\eta_{sys}\approx0.80\,FM$（取 $\eta_{esc}\eta_{mot}\approx0.80$），**只有 $FM\ge0.45$ 才落得到 0.35–0.60**；小桨实测 $FM$ 0.35–0.50 时系统效率只有 0.26–0.40（与 `bench_tech.md` §7.3 一致），申报书宜写 **0.30–0.55（待实测）**。

---

## 1 效率链机理建模

### 1.1 功率流与四个效率

能量流：`直流母线 → 电调(三相PWM) → 电机(轴) → 螺旋桨(气动) → 理想诱导功率`。悬停时飞行器不做有用功，末端必须用动量理论的**理想诱导功率**而非 $TV$（否则效率恒为 0）：

$$v_i=\sqrt{\frac{T}{2\rho A}},\quad P_{ideal}=T v_i=\frac{T^{3/2}}{\sqrt{2\rho A}},\quad A=\frac{\pi D^2}{4},\quad \eta_{sys}=\frac{P_{ideal}}{V_{dc}I_{dc}}$$

四个效率中，$FM=P_{ideal}/P_{shaft}$ 是**唯一全由力学量（$T,Q,n,\rho$）确定的环节**，不受电参量测量误差污染，因此本项目的可信核心是 $FM$ 与 $\eta_{sys}$，而 $\eta_{esc}$、$\eta_{mot}$ 只能靠模型反演或另设电机台架分离（见 §1.5）。

### 1.2 电调：三类损耗与效率近似式

三相六步（120°）换向时任一时刻仅两相导通，导通路径含 2 个 MOSFET；正弦驱动则三桥臂同时调制。工程上按"导通 + 开关 + 驱动 + 固定"四项建模即可，误差主要来自结温与死区。

| 损耗项 | 近似表达式 | 关键参数 | 量级/备注 |
|---|---|---|---|
| 导通 $P_{cond}$ | $2I_{dc}^2R_{ds(on)}(T_j)$（六步，两管串联）；正弦驱动用 $3I_{rms}^2R_{ds(on)}$ | $R_{ds(on)}$ 1–5 mΩ；其温度系数 $\alpha\approx0.005-0.008\ \mathrm{K^{-1}}$（Si） | 满载时可占电调损耗 60–80% `[经验]` |
| 开关 $P_{sw}$ | $\dfrac{6}{\pi}V_{dc}I_m(t_r+t_f)f_{sw}$ | $t_r+t_f$ 20–100 ns；$f_{sw}$ 8–32 kHz | $\propto V_{dc}f_{sw}$；低压大电流场景占比 <30% `[经验]` |
| 驱动 $P_{drv}$ | $6Q_gV_{gs}f_{sw}$ | $Q_g$ 20–60 nC；$V_{gs}$ 10–12 V | 通常 <0.5 W，可忽略但应写入模型 |
| 固定 $P_0$ | 控制板/BEC/采样 | 0.5–2 W | 决定轻载效率塌陷 |

$$\eta_{esc}=\frac{P_{ac}}{P_{dc}}=1-\frac{P_{cond}+P_{sw}+P_{drv}+P_0}{V_{dc}I_{dc}}$$

**三个可直接用于实验设计的推论**：

- **轻载塌陷**：$P_0$ 与 $P_{sw}$ 不随负载下降，10–20% 负载时 $\eta_{esc}$ 可跌到 0.80–0.88，峰值出现在 60–90% 负载 `[经验]`。故效率地图必须在低推力端加密，否则拟合会系统性高估小推力工况。
- **电压最优**：固定轴功率时 $I\propto1/V_{dc}$，令 $P_{loss}=k_1/V_{dc}^2+k_2V_{dc}$，得

$$V^*=\left(\frac{2k_1}{k_2}\right)^{1/3},\qquad \left.\frac{\partial P_{loss}}{\partial V_{dc}}\right|_{V^*}=0$$

  物理含义：升压降低导通损耗、但抬高开关损耗。若初始 $P_{cond}:P_{sw}=3:1$，电压翻倍后总损耗约降至 0.69 倍（$0.75+2\times0.25$），是可观测的效应。**这是本项目"电压作为独立变量"的核心假设，属机理推断，须实测验证** `[待验证]`。
- **反向效应**：电压过高时占空比很小，死区（约 1–2 V `[经验]`）与最小脉宽导致的电压损失占比上升，轻载效率反而下降；故 $V^*$ 会随负载移动，地图上应表现为"高效区随电压倾斜"。

### 1.3 电机：等效电路与四类损耗

稳态等效电路（单相）：$u=R_s i+L\frac{di}{dt}+K_e\omega$，$T_e=K_tI$。理想情形 $K_t[\mathrm{N\cdot m/A}]=K_e[\mathrm{V\cdot s/rad}]=9.55/KV[\mathrm{rpm/V}]$（如 KV=1000 → 9.55 mN·m/A）；实测 $K_t$ 常低 3–8%，差额即铁损与摩擦的等效"损失转矩" `[经验]`。

| 损耗 | 模型 | 与工况的关系 | 辨识方法 |
|---|---|---|---|
| 铜损 $P_{Cu}$ | $3I_{rms}^2R_s(T)$；六步换向 $2I_{dc}^2R_{ph}$ | $\propto T^2$ | 堵转/加载伏安法；$R_s(T)=R_{25}[1+0.00393(T-25)]$ |
| 铁损 $P_{Fe}$ | Steinmetz：$k_hfB^\alpha+k_ef^2B^2$，$\alpha\approx1.6-2.2$ | $\propto\omega^{1.6-2}$ | 空载扫转速，扣除铜损后拟合 |
| 机械 $P_{mech}$ | $T_f\omega+k_w\omega^3$（轴承+风阻） | 线性+三次 | 空载惰行法/双转速法分离 |
| 杂散 $P_{stray}$ | $(0.01-0.03)P_{in}$ | 近似比例 | 归入铁损拟合残差 |

$$\eta_{mot}=\frac{T\omega}{T\omega+P_{Cu}+P_{Fe}+P_{mech}+P_{stray}}$$

**效率-转速-转矩闭式关系**（本项目最有用的一个推导）：记 $P_{Cu}=cT^2$（$c=R_{eq}/K_t^2$）、固定损耗 $P_0(n)=P_{Fe}+P_{mech}$，则

$$\eta_{mot}(n,T)=\frac{T\omega}{T\omega+cT^2+P_0},\qquad \frac{\partial\eta}{\partial T}=0\Rightarrow T_{opt}=\sqrt{\frac{P_0}{c}},\qquad \eta_{max}=\frac{1}{1+2\sqrt{cP_0}/\omega}$$

三点结论：①最优工作点是"**可变损耗=固定损耗**"处，与电机学经典结论一致；②$T_{opt}\propto\sqrt{P_0(n)}$ 随转速上升，故**高效区是一条从低速小转矩指向高速大转矩的脊线**；③固定 $T$ 提高 $n$ 会同时抬高 $P_0$ 与输出功率，效率先升后降——这解释了为何"大桨低转速"通常优于"小桨高转速"（盘载荷效应，见 `bench_tech.md` §1.5）。

**参数辨识思路（5 参数即可）**：$R_s$（直流伏安/堵转，注意温升）、$K_e,K_t$（空载反电动势法或多转速稳态法）、$k_h,k_e$（空载损耗-转速拟合）、$T_f,k_w$（同前，用 $\omega$ 的一次/三次项分离）。**必须补偿逆变器非线性**：死区使实际相电压低于指令值 1–2 V，低占空比时会让 $K_e$ 辨识偏高 5% 以上 `[待验证]`。

### 1.4 螺旋桨：相似定理、$FM$ 与 BEMT

| 无量纲量 | 定义 | 用途 |
|---|---|---|
| 前进比 $J$ | $J=V_\infty/(nD)$ | 前飞工况；静态 $J=0$ |
| 推力系数 $C_T$ | $T/(\rho n^2D^4)$ | 静态 0.08–0.15 `[实测]`（UIUC 数据库量级） |
| 功率系数 $C_P$ | $P/(\rho n^3D^5)$ | 决定 $P\propto n^3$ 的标定关系 |
| 扭矩系数 $C_Q$ | $Q/(\rho n^2D^5)=C_P/(2\pi)$ | 与 $FM$ 直接换算 |
| 推进效率 $\eta_p$ | $JC_T/C_P$ | 仅前飞有意义 |
| 悬停效率 $FM$ | $P_{ideal}/P_{shaft}$ | **静态/悬停的唯一气动指标** |

$$FM=\frac{T^{3/2}}{\sqrt{2\rho A}\,Q\Omega}=\frac{C_T^{3/2}}{2\pi\sqrt{\pi/2}\,C_Q}\approx\frac{C_T^{3/2}}{7.874\,C_Q}$$

该式可直接把 UIUC 数据库的 $C_T,C_Q$ 换算成 $FM$ 做交叉校验（同 `bench_tech.md` §1.3）。

**动量理论**：$T=2\rho A v_i^2$，$P_i=\kappa T^{3/2}/\sqrt{2\rho A}$，诱导功率因子 $\kappa\approx1.1-1.2$ `[经验]`。它只给出"理想下限"，不含型阻与桨尖损失，故 $FM<1$ 且小桨显著偏低（低雷诺数）。

**BEMT 简述**：把桨叶沿展向分为微段，每段升阻由翼型数据给出，与动量守恒联立迭代入流角：

$$dT=\tfrac12\rho W^2Bc\,C_l\,dr=4\pi\rho r\,v_i(V_c+v_i)\,dr,\qquad dQ=\tfrac12\rho W^2Bc\,C_d\,r\,dr$$

BEMT 能预测 $C_T(J),C_P(J)$ 并解释"为何某桨高效"，但小桨工作在 $Re\approx10^4-10^5$，翼型升阻数据本身不确定度大，静态附近（$J\to0$）常高估 $FM$ `[待验证]`。**结论：BEMT 用于理解机理与筛选桨型，不作为效率地图的数值来源**；地图必须实测（Re 效应不可缩放，见 `bench_tech.md` 文献[5]）。

### 1.5 系统效率计算式、可分离性与灵敏度

| 可测量组合 | 可直接得到的量 | 不可分离的部分 |
|---|---|---|
| $V_{dc},I_{dc},T,Q,n$ | $\eta_{sys}$、$FM$、$\eta_{esc+mot}=P_{shaft}/P_{dc}$ | $\eta_{esc}$ 与 $\eta_{mot}$ 各自 |
| 增加三相功率分析仪 | $\eta_{esc}$、$\eta_{mot}$ 分别 | 仍受 PWM 方波带宽限制（误差可达 10%+，同 bench §1.2） |
| 增加电机测功机（MAGTROL） | 电机效率独立标定，可反演电调 | 轴系对接误差、联轴器附加损耗 |

对 $\eta_{sys}=T^{3/2}/(\sqrt{2\rho A}V_{dc}I_{dc})$ 与 $FM$ 作对数微分，得相对标准不确定度（与 `bench_tech.md` §1.4 同式）：

$$\left(\frac{u_\eta}{\eta}\right)^2_{sys}=\left(\tfrac32\frac{u_T}{T}\right)^2+\left(\tfrac12\frac{u_\rho}{\rho}\right)^2+\left(\frac{u_D}{D}\right)^2+\left(\frac{u_V}{V}\right)^2+\left(\frac{u_I}{I}\right)^2$$

$$\left(\frac{u_{FM}}{FM}\right)^2=\left(\tfrac32\frac{u_T}{T}\right)^2+\left(\frac{u_Q}{Q}\right)^2+\left(\frac{u_n}{n}\right)^2+\left(\frac{u_D}{D}\right)^2+\left(\tfrac12\frac{u_\rho}{\rho}\right)^2$$

**灵敏度排序**：推力（系数 1.5）> 电压/电流/扭矩/转速（系数 1.0）> 密度/直径（系数 0.5–1.0）。故标定资源应优先投向推力与扭矩；直径按卡尺测量即可，但**桨径必须按实测而非标称**（同规格桨实测直径差 1–2% 很常见 `[经验]`）。

**参数辨识三条路线**：A 分部件台架（精度最高、成本最高）；B 整机黑箱（本项目主线，$\eta_{sys}$ 与 $FM$ 可信）；C 混合（整机 + 电机单独标定，用 MAGTROL 台架补 $\eta_{mot}$，反演 $\eta_{esc}$）——**推荐 C**，它把"部件效率不可分"这一硬约束降级为"一次额外试验"。

---

## 2 效率地图构建

### 2.1 坐标变量怎么选

| 坐标方案 | 优点 | 缺点 | 建议用途 |
|---|---|---|---|
| 油门 $\delta$ × $V_{dc}$ | 贴近飞控实际输出，便于机载查表 | $\delta$ 是"指令"非"状态"，同 $\delta$ 不同电压对应不同工作点，桨特性被污染 | 辅助图、控制分配查表 |
| 转速 $n$ × 推力 $T$ | 物理正交（$n$ 定铁损/风阻，$T$ 定铜损），场最平滑，可跨电压复用 | 需闭环控转速，试验难度略高 | **主图（推荐）** |
| $T$ × $V_{dc}$ | 直接回答"给定推力选什么电压最省电" | 不同 $V_{dc}$ 的可达 $T$ 上限不同，域是梯形而非矩形 | **主图（推荐，与项目命题最契合）** |
| 归一化 $(T/T_{max},n/n_{max})$ | 可跨桨径/电机对比同一"相对工况" | 丢失绝对量纲，不能直接查功率 | 多桨对比、聚类 |
| $J$（前进比） | 前飞效率唯一正确坐标 | 静态台架 $J\equiv0$，不可用 | 二期风洞扩展 |

推荐布局：**主图 $\eta_{sys}(T,V_{dc})$ 每个桨-电机组合一张；辅图 $\eta_{sys}(T,n)$ 用于机理分析；曲线族 $\eta_{sys}$–$T$（按 $V_{dc}$ 分层）用于答辩展示**。这样"电压维度"在图上表现为一族可比较的曲线，故事最直观。

### 2.2 数据量要求

| 设计方法 | 特点 | 适用 |
|---|---|---|
| 全因子网格 | 便于插值、边界完整，点数随维数指数增长 | 2D 主图（每维 8–12 级） |
| 正交表 | 主效应可分离，交互项混杂 | 多桨/多电机筛选阶段 |
| 拉丁超立方 LHS | 空间填充好、边缘点少 | 3D 以上（$T,n,V_{dc}$）联合建模 |
| Sobol / Maximin | 均匀性更优、可增量 | GP 训练集、序贯设计起点 |
| 序贯（EI/最大方差） | 每次只在最不确定处补点，最省试验 | 高效区与约束边界加密 |

**经验法则**：GP 的可靠训练量约为 $10d-20d$（$d$ 为变量数），含噪声与非平稳时取上限；2D 规则网格 8×8=64 至 12×12=144 点/组合；3D（$T,n,V_{dc}$）联合建模需 120–200 点/组合。按项目"≥500 组工况"反推，可行配置是 **4–6 个桨-电机组合 × 100 点**，或 **3 个电压 × 2 桨 × 2 电机（12 组）× 40 点**（后者覆盖广、单图精度低，适合筛选）。

三点实操要求：①**中心点重复 3–5 次**估计纯误差（GUM A 类），否则无法区分模型失拟与随机误差；②**冷/热态各测一遍**或把 $T_j$ 记为协变量，否则温升会把效率漂移误判为工况效应；③**边界加密**：在 $I_{max}$、$T_{j,max}$ 与高效区边界附近补点，因为这些位置决定优化可行域。

### 2.3 插值与拟合方法对比

| 方法 | 平滑性/性质 | 样本需求 | 外推 | 优点 | 风险 |
|---|---|---|---|---|---|
| 分段线性（Delaunay/`tricontourf`） | $C^0$，保形无过冲 | 30–50 | 差（凸包外无定义） | 最稳、可解释、不假设函数形 | 等值线呈折线，梯度不可用 |
| 双三次样条（规则网格） | $C^2$ | 完整网格 ≥8×8 | 中 | 快、光滑、易查表 | 网格缺失需补插，边界振荡 |
| 双调和薄板样条 TPS | 最小弯曲能量，$C^1$ | 50–100 | 差 | 无需调参、全局光滑 | 对噪声敏感，需正则化 |
| RBF（高斯/多二次） | 灵活 | 50–150 | 差 | 实现简单、精度高 | 形状参数敏感、矩阵易病态 |
| Kriging/GP | 含噪声模型与后验方差 | 30–200 | 差但**能报不确定度** | 小样本最优、可序贯 | $O(n^3)$、核选择需经验 |

**推荐组合**：GP（Matérn 5/2 + WhiteKernel）作主模型与不确定度来源；TPS 作独立交叉校验（两者在数据密集区应吻合到 1 个百分点内，否则说明核或噪声模型有误）；规则网格用 `RectBivariateSpline` 生成论文/答辩用光滑等值线图。

### 2.4 可视化与高效区识别

| 图形 | 作用 | 实现要点 |
|---|---|---|
| 填充等值线 $\eta(T,V_{dc})$ | 主图，看"岛状"高效区 | `contourf` 20 级 + `contour` 叠加 0.9/0.95 倍峰值线 |
| 3D 曲面 | 答辩展示，直观但难读数 | `plot_surface` + 等高线投影 |
| 曲线族 $\eta$–$T$（按电压分层） | 证明"电压有最优" | 每电压一条线，标出峰值点连线 |
| 不确定度图 $\sigma_\eta$ | 标出数据稀疏区/该补测处 | GP `return_std=True` 的等值线 |
| 可行域叠加 | 把电流/温升/电压边界画在同一图上 | 用 `contour` 画 $I=I_{max}$ 等值线，阴影标不可行区 |

**高效区定义**（建议在报告中明确定义，避免各说各话）：取 $\eta\ge\eta_{max}-\Delta$（$\Delta=0.02-0.03$）的连通域为"高效区"；同时给出三个标量指标——①高效区面积占可行域比例；②高效区内最大可执行窗口（最大内接矩形，对应"可长期悬停的工况包线"）；③脊线 $n^*(T)=\arg\max_n\eta$，用于控制分配查表。

---

## 3 数据驱动建模

### 3.1 五类方法对比

| 方法 | 适用条件 | 样本需求 | 可解释性 | 典型精度 `[经验]` | 实现难度 |
|---|---|---|---|---|---|
| 响应面 RSM（二次多项式） | 平滑、单峰、变量 ≤5；用于筛选主效应 | 20–50 | **高**（系数即灵敏度） | $R^2$ 0.90–0.97 | 低（`PolynomialFeatures`+`Ridge`） |
| GP/克里金 | 平滑、小样本、需要不确定度 | 30–200 | 中（长度尺度=各变量重要度） | $R^2$ 0.95–0.995 | 中（核设计与超参优化） |
| ANN/MLP | 强非线性、样本充足、多桨多电机联合建模 | 500–2000 | 低（黑箱） | $R^2$ 0.97–0.995 | 中（归一化、调参、早停） |
| 梯度提升树 GBDT | 表格数据、含离散变量（桨型号、KV 档位） | 300–1000 | 中（特征重要性/SHAP） | $R^2$ 0.96–0.99 | 中（正则与早停） |
| **机理+数据混合（灰箱）** | 有物理先验、需外推、样本少 | 30–150 | **高**（残差可物理解释） | 通常最优 | 中高（需先建机理基线） |

**灰箱是本项目的最优解**：先用 1.2–1.4 节的机理式算出 $\eta_{sys}^{mech}(T,n,V_{dc})$，再用 GP 只拟合残差 $\varepsilon=\eta_{meas}-\eta_{mech}$。好处是外推区不会发散（机理项兜底）、所需样本减半、且残差图能直接指出"哪个部件模型错了"（若残差随 $n$ 单调增 → 铁损模型偏小）。这与 Forrester 等[10]的"先验+代理"框架一致。

### 3.2 验证协议（比模型选择更重要）

| 验证方式 | 做法 | 回答的问题 |
|---|---|---|
| 随机 5/10 折 | 打乱划分 | 内插精度（**会高估**，因同工况近邻泄漏） |
| **分组交叉验证** | 按桨型或电压分组（`GroupKFold`） | 跨工况泛化——**这才是地图可用的判据** |
| 留一法 LOO | $n<50$ 时用 | 小样本稳定性 |
| 外部验证 | 留出一整个桨型号/整个电压档 | "换一个桨还能不能预测" |
| 学习曲线 | 训练集 20%→100% | 样本是否够、该不该补测 |

操作顺序：先按桨型留出约 20% 作**最终检验集**（定稿后只跑一次，避免"用测试集调参"），其余用于交叉验证。指标报 $R^2$、RMSE、MAE 与 **MAPE**；工程上更有意义的是绝对误差：$\eta$ 的 RMSE **≤0.01（1 个百分点）** 才可用于选型决策。注意随机划分与分组划分的差距本身就是信息——若差 3 倍，说明模型学的是"试验批次"而不是物理。

### 3.3 超参数搜索

- **GP**：核超参由边际似然最大化（`L-BFGS-B`，多起点 5–10 次）；长度尺度初值取该变量量程的 1/4；`WhiteKernel` 初值取重复点标准差的平方。先试 Matérn 5/2，欠光滑再降 ν，过光滑再升。
- **MLP**：`RandomizedSearchCV` 或 Optuna(TPE)；2–3 隐层、32–128 宽、`early_stopping=True`；输入必须标准化。
- **GBDT**：`max_depth` 3–6、`learning_rate` 0.05、`n_estimators` 300–1000 + 验证集早停；特征里显式加入 $\log n$、$T/n^2$ 等物理组合项常比调参更有效。

### 3.4 小样本策略

| 策略 | 做法 | 收益 |
|---|---|---|
| DoE 先行 | LHS/Sobol 生成初始 40–60 点，再序贯补点 | 同样精度省 30–50% 试验 `[经验]` |
| 机理先验 | GP 均值函数取机理模型输出（等价于拟合残差） | 外推稳定、样本减半 |
| 迁移/微调 | 同系列桨（如 APC 10×4.7→10×5.5）预训练后少量数据微调 | 新桨只需 20–30 点 |
| 多保真 | 低保真=BEMT/厂商数据，高保真=台架，co-kriging 融合 | 用廉价数据补趋势 |
| 物理约束正则 | 强制 $\partial\eta/\partial T$ 单调段、$T\propto n^2$ 一致性 | 抑制过拟合、提升可信度 |

### 3.5 不确定度

三层要分开报，不要混成一个数：①**测量不确定度**（GUM 合成，见 §1.5）；②**模型不确定度**（GP 后验方差、集成方差、分位数回归区间）；③**工况/外推不确定度**（远离数据处必须标记）。工程表达用 95% 预测区间 $\eta\pm1.96\sigma$，并在图上以半透明带显示；选型决策只在"区间宽度 < 目标分辨率（如 0.02）"的区域内做。

---

## 4 匹配优化

### 4.1 决策变量

| 变量 | 符号 | 范围 | 类型 | 主要影响 |
|---|---|---|---|---|
| 电机 KV | $KV$ | 300–1000 rpm/V | 离散（步进 50–100） | 同电压下转速/扭矩分配 |
| 桨径 | $D$ | 5–30 in | 离散（0.5 in） | 盘载荷、$FM$、$P_{ideal}$ |
| 螺距（或 $P/D$） | $H$ | 3–12 in | 离散 | $C_T,C_P$、静态推力 |
| 电池串数 | $N_s$ | 3S–12S | 整数 | 母线电压、$V^*$ 位置 |
| 电池容量 | $C_b$ | 1–20 Ah | 连续/离散 | 航时、重量 |
| 电调时序/开关频率 | $f_{sw},\theta$ | 8–32 kHz，0–30° | 连续（进阶） | 换向损耗、$P_{sw}$ |
| 桨叶数 | $B$ | 2–4 | 整数 | $C_T$ 提升但 $FM$ 下降 |

### 4.2 目标与约束

| 目标 | 表达式 | 说明 |
|---|---|---|
| 系统效率 | $\max\ \eta_{sys}(T_h,V_{dc})$ | 主目标，悬停点效率 |
| 航时 | $\max\ t_e=\dfrac{C_bV_{nom}\cdot DoD}{P_{hover}}$，$P_{hover}=\dfrac{T_h^{3/2}}{\sqrt{2\rho A}\,\eta_{sys}}$ | 与效率非等价（受重量耦合） |
| 推力裕度 | $\max\ M_T=T_{max}/T_h$ 或 $T/W$ | 机动性与抗风 |
| 重量/成本 | $\min\ m(x),\ \min\ c(x)$ | 与航时强耦合（重量↑→$T_h$↑） |

| 约束 | 不等式 | 依据 |
|---|---|---|
| 推力需求 | $T_{avail}(x,V_{min})-T_{req}(1+k)\ge0$ | $k$=裕度 0.2–0.3 |
| 电流上限 | $I_{dc}(x)-I_{cont,esc}\le0$ | 电调连续电流 |
| 温升 | $T_j(x)-T_{j,lim}\le0$（或 $\Delta T_w\le\Delta T_{lim}$） | 磁钢退磁裕度，$T_{j,lim}$ 100–120 °C `[经验]` |
| 电压范围 | $V_{cell}\in[3.5,4.2]$ V，$N_s\in[3,12]$ | LiPo 安全窗口 |
| 桨尖马赫 | $M_{tip}=\pi Dn/(60a)\le0.6-0.7$ | 噪声与效率骤降（同 bench §1.5） |
| 效率下限 | $\eta_{sys}(x)-\eta_{min}\ge0$ | 排除"能飞但很费电"的解 |

### 4.3 标准数学形式

$$
\begin{aligned}
\min_{x}\quad & \mathbf{F}(x)=\big[\,f_1,f_2,f_3,f_4\,\big]^{\mathsf T}
=\big[\,-\eta_{sys}(x),\ -t_e(x),\ -M_T(x),\ m(x)\,\big]^{\mathsf T}\\
\text{s.t.}\quad
& g_1(x)=T_{req}(1+k)-T_{avail}(x)\le 0\\
& g_2(x)=I_{dc}(x)-I_{lim}\le 0\\
& g_3(x)=T_j(x)-T_{j,lim}\le 0\\
& g_4(x)=M_{tip}(x)-0.7\le 0\\
& g_5(x)=\eta_{min}-\eta_{sys}(x)\le 0\\
& x=(KV,D,H,N_s,C_b)\in\mathcal{X},\quad \mathcal{X}\ \text{为混合整数箱式域}
\end{aligned}
$$

单目标时用加权和 $f=\sum w_i\tilde f_i$（各目标先归一化到 [0,1]），但**权重法无法得到非凸 Pareto 前沿**，故报告应至少给 2–3 个目标的 Pareto 集，再由决策者选点。

### 4.4 算法对比与选择

| 算法 | 适用维度/规模 | 评估成本 | 约束处理 | 优点 | 缺点 |
|---|---|---|---|---|---|
| 网格/枚举 | ≤3 变量、全离散 | 高（组合爆炸） | 直接剔除 | 全局（网格分辨率内）、可并行、结果可信 | 5 变量 ×10 档 = 10⁵ 次，台架不可能 |
| GA | 5–20 维、混合变量 | 中 | 罚函数/修复算子 | 通用、易实现 | 单目标、需调参、无收敛保证 |
| **NSGA-II**[5] | 2–3 目标 | 中 | 约束支配（constraint domination） | Pareto 前沿均匀、精英保留 | 目标 >3 时退化 |
| MOEA/D | 多目标（可 >3） | 中 | 分解+罚 | 高维目标表现好 | 权重向量设计麻烦 |
| 贝叶斯优化[8] | ≤15–20 维、单次评估昂贵 | **极低**（10–50 次） | 约束 EI / 可行性模型 | 样本效率最高，可"边测边优" | 高维退化、并行化需批式采集 |

**本项目推荐路线**：①用 GP 代理替代真实台架（单次评估≈1 ms），在稠密网格上先做**枚举基准**（2–3 变量），得到可信的全局最优区间；②固定 $KV$、$D$ 的离散组合，对连续变量（$N_s$、$C_b$、$f_{sw}$）跑 **NSGA-II** 得 Pareto 前沿；③用**膝点 + 工程偏好**选 2–3 套方案；④台架复测，把实测点回灌 GP 重新训练（主动学习闭环）。若后期要"边测边优"（每次试验 5–10 min，预算 <100 次），改用约束贝叶斯优化。

### 4.5 Pareto 决策与工程落地

- **收敛判据**：超体积 HV 连续 20 代增幅 <1%；或与枚举基准的前沿做 IGD 比较。
- **选点方法**：膝点（到理想点距离最小/前沿拐点）优先；再用熵权-TOPSIS 做多准则排序，避免"拍脑袋加权"。
- **不确定性下的决策**：用 GP 的 $\eta\pm1.96\sigma$ 做**鲁棒优化**（最坏情形 $\eta-1.96\sigma$ 最大），避免选中"预测很好但方差很大"的边缘解。
- **与控制分配衔接**：得到效率地图后，可把多旋翼的推力分配从"伪逆最小范数"改为"最小电功率"[6,7]，让每个桨落在高效区。Dyer 等[7]已验证以能耗为目标分配可降低悬停功率（具体百分比见原文，本文不复述数值）。这一步把"选型优化"延伸到"运行优化"，是本项目可写的第二个创新点（**待核实**是否已有团队在效率地图上做分配）。

---

## 5 Python 工具链

| 库 | 用途 | 关键 API |
|---|---|---|
| `numpy` | 数组、广播、网格、数值微分 | `meshgrid`、`gradient`、`polyfit`、`interp` |
| `pandas` | 试验数据管理、分组统计、合并 | `read_csv`、`groupby().agg()`、`merge`、`to_parquet` |
| `scipy` | 插值、优化、统计 | `RBFInterpolator`、`RectBivariateSpline`、`griddata`、`least_squares`、`differential_evolution` |
| `sklearn` | 代理模型、验证、预处理 | `GaussianProcessRegressor`、`kernels.Matern/WhiteKernel`、`GroupKFold`、`cross_val_score`、`MLPRegressor`、`GradientBoostingRegressor`、`Pipeline` |
| `pymoo` | 多目标优化 | `ElementwiseProblem`、`NSGA2`、`minimize`、`Hypervolume` |
| `matplotlib` | 出图 | `contourf`、`tricontourf`、`plot_surface`、`errorbar` |
| 可选 | 序贯设计/灵敏度/调参 | `pyDOE3`(LHS)、`SALib`(Sobol)、`Optuna`、`plotly` |

```python
# ① 读数据 + GP 代理（含分组交叉验证）
import numpy as np, pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel as C
from sklearn.model_selection import GroupKFold, cross_val_score

df = pd.read_csv("bench.csv")            # V_dc, n, T, Q, I_dc, eta_sys, prop_id
X  = df[["V_dc", "n", "T"]].to_numpy()
y  = df["eta_sys"].to_numpy()
k  = C(1.0) * Matern(length_scale=[1, 1, 1], nu=2.5) + WhiteKernel(1e-3)
gp = GaussianProcessRegressor(k, normalize_y=True, n_restarts_optimizer=8).fit(X, y)
print(gp.kernel_)                        # 长度尺度≈各变量重要度
cv = GroupKFold(n_splits=5).split(X, y, groups=df["prop_id"])
print(cross_val_score(gp, X, y, cv=cv, scoring="neg_root_mean_squared_error"))
```

```python
# ② NSGA-II 匹配优化（代理模型在环）
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

class Match(ElementwiseProblem):
    def __init__(self, model, T_req=10.0, I_lim=60.0, dT_lim=60.0):
        super().__init__(n_var=4, n_obj=3, n_ieq_constr=3,
                         xl=np.array([300, 5, 3, 1.0]), xu=np.array([1000, 30, 12, 20.0]))
        self.model, self.T_req, self.I_lim, self.dT_lim = model, T_req, I_lim, dT_lim

    def _evaluate(self, x, out, *a, **kw):
        kv, D, ns, cb = np.round(x)                  # 近似整数化；严格需加舍入罚/混合变量
        eta, T, I, dT = self.model(kv, D, ns, cb)    # 返回效率、可用推力、电流、温升
        P_ideal = T ** 1.5 / np.sqrt(2 * 1.2 * np.pi * (D * 0.0254) ** 2 / 4)
        tend = cb * 3.7 * ns * 0.8 / (P_ideal / eta)  # 放电深度 0.8
        out["F"] = np.array([-eta, -tend, -T / self.T_req])   # 三目标均取最小
        out["G"] = np.array([self.T_req - T, I - self.I_lim, dT - self.dT_lim])  # ≤0 可行

res = minimize(Match(model), NSGA2(pop_size=120, eliminate_duplicates=True),
               ("n_gen", 300), seed=1, verbose=False)
print(res.X, res.F)                          # Pareto 解集与目标值
```

```python
# ③ 效率地图与不确定度（注意列顺序须与训练集一致：V_dc, n, T）
import numpy as np, matplotlib.pyplot as plt
V  = np.linspace(Vmin, Vmax, 60); Th = np.linspace(Tmin, Tmax, 60)
GV, GT = np.meshgrid(V, Th)
Q = np.c_[GV.ravel(), np.full(GV.size, n_fix), GT.ravel()]   # 固定转速切面
mu, sd = gp.predict(Q, return_std=True)
cf = plt.contourf(GV, GT, mu.reshape(GV.shape), levels=20, cmap="viridis")
plt.contour(GV, GT, mu.reshape(GV.shape), levels=[0.95 * mu.max()], colors="w")  # 高效区边界
plt.colorbar(cf, label=r"$\eta_{sys}$"); plt.xlabel(r"$V_{dc}$ / V"); plt.ylabel("T / N")
```

**版本注意**：`pymoo` 0.6.x 用 `ElementwiseProblem`（逐行，无需向量化）可避开大批量 `_evaluate` 的维度陷阱；0.5.x 以下写法不同，锁版本（`pymoo==0.6.1`）并在环境中固定 `scikit-learn==1.5.*` 以免 `GaussianProcessRegressor` 的随机性变化影响复现。

---

## 6 典型参数范围

| 参数 | 符号 | 典型范围 | 来源/可信度 |
|---|---|---|---|
| 电机 KV | $KV$ | 300–1000 rpm/V | 市售 2212–4110 级多旋翼电机常见档位 `[经验]` |
| 桨径 | $D$ | 5–30 in（0.127–0.762 m） | 项目设定，与 `bench_tech.md` 一致 |
| 供电电压 | $N_s$ | 3S–12S（11.1–44.4 V） | 项目设定 `[经验]` |
| 悬停效率 | $FM$ | 0.50–0.75（中大桨/高 Re）；0.35–0.62（5–30 in 实测） | 前者为任务书与教科书量级，后者见 `bench_tech.md` §7.3、UIUC 数据 `[实测]` |
| 电机效率 | $\eta_{mot}$ | 0.80–0.92（峰值，60–85% 额定） | `[经验]`，待本项目 MAGTROL 台架核实 |
| 电调效率 | $\eta_{esc}$ | 0.93–0.98（峰值）；轻载 0.80–0.88 | `[经验]` |
| 系统效率 | $\eta_{sys}$ | 0.35–0.60（任务书）；0.26–0.55（按 $FM$ 实测推算） | 见下方自洽性校核 |
| 推力系数 | $C_T$ | 0.08–0.15（静态） | UIUC 数据库量级 `[实测]` |
| 扭矩系数 | $C_Q$ | 0.008–0.015（静态） | 同上 |
| 扭矩常数 | $K_t$ | $\approx9.55/KV$ N·m/A | 理想关系，实测低 3–8% `[经验]` |
| 导通电阻 | $R_{ds(on)}$ | 1–5 mΩ（30–60 A 级） | 器件手册 `[实测]` |
| 开关频率 | $f_{sw}$ | 8–32 kHz | 市售电调 `[经验]` |
| 电池能量密度 | — | 150–250 Wh/kg（LiPo） | `[经验]` |
| 悬停功率 | $P_{hover}$ | 100–180 W/kg（起飞重量） | `[经验]`，强依赖盘载荷 |

**自洽性校核（重要）**：$\eta_{sys}=\eta_{esc}\eta_{mot}FM$，代入区间端点：

| 组合 | $\eta_{esc}$ | $\eta_{mot}$ | $FM$ | $\eta_{sys}$ | 对应场景 |
|---|---|---|---|---|---|
| 乐观 | 0.97 | 0.90 | 0.70 | **0.61** | 大桨、高 Re、接近峰值 |
| 典型 | 0.95 | 0.86 | 0.55 | **0.45** | 15 in 级、中等负载 |
| 保守 | 0.93 | 0.82 | 0.45 | **0.34** | 10 in 级、偏离高效区 |
| 小桨实测 | 0.92 | 0.80 | 0.35 | **0.26** | 5–8 in、低 Re、轻载 |

结论：任务书给的 0.35–0.60 对应 $FM$ 0.45–0.70，属"中大桨、设计良好"的情形；若本项目实测 $FM$ 落在 0.35–0.50（`bench_tech.md` 对 5–10 in 桨的判断），系统效率会落到 0.26–0.40。**建议申报书统一写"0.30–0.55（待实测）"，并说明区间宽度来自桨径与工况差异**——这比写 0.35–0.60 更稳，也更像做过功课。

---

## 7 参考文献

> 与 `research_brief.md` 已著录的 15 篇不重复；Dai 等（IEEE TIE 2019）、Piljek 等（Appl Sci 2020）、Zhao 等（JPCS 2024）、Goli 系列、Brandt & Selig 等见简报，本文正文以"简报[n]"引用。

[1] SHI D, DAI X, ZHANG X, et al. A practical performance evaluation method for electric multicopters[J]. IEEE/ASME Transactions on Mechatronics, 2017, 22(3): 1337-1348. DOI: [10.1109/TMECH.2017.2675913](https://doi.org/10.1109/TMECH.2017.2675913).

[2] KOTARSKI D, KRZNAR M, PILJEK P, et al. Experimental identification and characterization of multirotor UAV propulsion[J]. Journal of Physics: Conference Series, 2017, 870: 012003. DOI: [10.1088/1742-6596/870/1/012003](https://doi.org/10.1088/1742-6596/870/1/012003).

[3] GUR O, ROSEN A. Optimizing electric propulsion systems for unmanned aerial vehicles[J]. Journal of Aircraft, 2009, 46(4): 1340-1353. DOI: [10.2514/1.41027](https://doi.org/10.2514/1.41027).

[4] MAGNUSSEN Ø, OTTESTAD M, HOVLAND G. Multicopter design optimization and validation[J]. Modeling, Identification and Control, 2015, 36(2): 67-79. DOI: [10.4173/mic.2015.2.1](https://doi.org/10.4173/mic.2015.2.1).

[5] DEB K, PRATAP A, AGARWAL S, et al. A fast and elitist multiobjective genetic algorithm: NSGA-II[J]. IEEE Transactions on Evolutionary Computation, 2002, 6(2): 182-197. DOI: [10.1109/4235.996017](https://doi.org/10.1109/4235.996017).

[6] JOHANSEN T A, FOSSEN T I. Control allocation—A survey[J]. Automatica, 2013, 49(5): 1087-1103. DOI: [10.1016/j.automatica.2013.01.035](https://doi.org/10.1016/j.automatica.2013.01.035).

[7] DYER E, SIROUSPOUR S, JAFARINASAB M. Energy optimal control allocation in a redundantly actuated omnidirectional UAV[C]//2019 International Conference on Robotics and Automation (ICRA). Montreal: IEEE, 2019: 5316-5322. DOI: [10.1109/ICRA.2019.8793549](https://doi.org/10.1109/ICRA.2019.8793549).

[8] SHAHRIARI B, SWERSKY K, WANG Z, et al. Taking the human out of the loop: A review of Bayesian optimization[J]. Proceedings of the IEEE, 2016, 104(1): 148-175. DOI: [10.1109/JPROC.2015.2494218](https://doi.org/10.1109/JPROC.2015.2494218).

[9] ERICKSON R W, MAKSIMOVIĆ D. Fundamentals of power electronics[M]. 3rd ed. Cham: Springer, 2020. DOI: [10.1007/978-3-030-43881-4](https://doi.org/10.1007/978-3-030-43881-4).

[10] FORRESTER A I J, SÓBESTER A, KEANE A J. Engineering design via surrogate modelling: A practical guide[M]. Chichester: Wiley, 2008. DOI: [10.1002/9780470770801](https://doi.org/10.1002/9780470770801).

[11] RASMUSSEN C E, WILLIAMS C K I. Gaussian processes for machine learning[M]. Cambridge, MA: MIT Press, 2006. [http://gaussianprocess.org/gpml](http://gaussianprocess.org/gpml).

[12] FRIEDMAN J H. Greedy function approximation: A gradient boosting machine[J]. The Annals of Statistics, 2001, 29(5): 1189-1232. DOI: [10.1214/aos/1013203451](https://doi.org/10.1214/aos/1013203451).

---

## 8 尚不确定与待验证清单

| # | 事项 | 现状 | 建议动作 |
|---|---|---|---|
| 1 | $FM$ 区间分歧（0.50–0.75 vs 0.35–0.62） | 任务书/教科书偏乐观，实测数据偏低 | 台架先测 3 支桨（5/10/15 in）定标，再回改申报书数值 |
| 2 | 电压最优点 $V^*$ 是否可观测 | 机理推导成立，但幅度可能被死区/纹波掩盖 | 固定 $(T,n)$ 扫 3–4 个电压，看 $\eta_{sys}$ 差是否 > 测量不确定度（约 1–2%） |
| 3 | 电调效率峰值与轻载塌陷幅度 | 仅经验值 | 用功率分析仪做 5–100% 负载扫描 |
| 4 | Dai 等[简报7]效率增益的具体数值 | 未核对原文数值 | 写申报书前查原文，避免复述失真 |
| 5 | 是否已有"效率地图 + 联合寻优"公开报道 | 初步检索未见 | 补检 IEEE Xplore/CNKI（关键词：efficiency map, propulsion matching, multirotor） |
| 6 | BEMT 在 5–15 in 桨静态附近的偏差量级 | 定性知道偏低 Re 会高估 $FM$ | 用 UIUC 数据 + 自测数据对照，量化后决定是否写入申报书 |
| 7 | 温升对 $\eta$ 的漂移是否需单独建维 | 可能达 2–5 个百分点 | 冷/热态对比试验后决定是否把 $T_j$ 作为第 4 维 |
