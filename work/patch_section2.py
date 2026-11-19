# -*- coding: utf-8 -*-
"""用调研核实后的内容替换 proposal_content.py 中 SECTIONS['二'] 整块。"""
import io

PATH = r'D:\下载\创新\work\proposal_content.py'
src = io.open(PATH, encoding='utf-8').read()

NEW = '''    "二": [
        ("p", "多旋翼无人机动力系统一般由无刷直流电机、电子调速器（ESC）、螺旋桨和动力电池组成，"
              "其能量转换效率是电调效率、电机效率与螺旋桨效率共同作用的结果，任一环节的损耗都会直接表现为"
              "悬停功率增加和续航时间缩短。随着低空经济和工业级无人机应用的快速发展，动力系统效率的测试、"
              "建模与匹配优化已成为国内外研究热点。围绕“效率如何测、如何建模、如何匹配优化”，"
              "相关研究可归纳为以下几个方面。"),
        ("h", "2.1 动力系统效率测试与评价"),
        ("p", "国外较早建立了系统化的实验表征方法。Piljek 等针对多旋翼电推进系统提出了完整的台架表征流程，"
              "同步测量推力、扭矩、转速与母线电压、电流、功率，获得部件与系统效率随工况的变化规律[1]。"
              "Zhu 等通过实测与数值分析指出，小尺度螺旋桨在低雷诺数下性能分散显著，其推力与效率特性必须"
              "依靠实测数据而非缩比外推[2]；Goli 等通过实验研究了部件匹配对多旋翼推进系统效率的影响[3]。"
              "国内方面，赵安敏等研制了无人机电动力测试系统，在相同工况下推力、扭矩与电机效率的数值解与"
              "实测平均误差分别约为1.02%、10%和10.04%，说明电参量与力学量的同步测量精度、电机效率的"
              "间接推算误差是台架建设的关键难点[4]。Brandt 与 Selig 建立了低雷诺数螺旋桨性能数据库[5]；"
              "Park 等针对太阳能高空长航时无人机螺旋桨，将叶素动量理论与最小诱导损失设计相结合，并用"
              "Kriging 代理模型和风洞试验进行验证[6]。总体来看，国外偏重方法与数据共享，国内偏重测试系统"
              "研制，公开的宽工况系统级效率数据集仍然稀缺。"),
        ("h", "2.2 电机—螺旋桨匹配与选型优化"),
        ("p", "匹配与选型方面，Dai 等提出以效率为目标的电动多旋翼推进系统部件选型优化方法，"
              "将电机效率 MAP、螺旋桨特性与任务剖面耦合求解[7]；de Angelis 等建立了电动多旋翼性能分析与"
              "最优尺度设计方法，给出桨径、转速与电机参数的匹配关系[8]；Delbecq 等基于相似律建立了高效"
              "缩放与优化方法[9]；Biczyski 等将部件选型与飞行时间预估统一在一个 sizing 框架内[10]。"
              "这些工作表明：系统效率不是单部件效率的简单乘积，而是随油门、电压、转速与来流强耦合的非线性"
              "函数，必须依靠“匹配”而非“各自最优”取得全局最优；但其优化多以解析模型或厂商数据为基础，"
              "缺乏自建台架的实测闭环。"),
        ("h", "2.3 效率地图与数据驱动建模"),
        ("p", "传统效率建模依赖电机等效电路与损耗理论、螺旋桨动量与叶素理论等机理模型，能够反映效率变化的"
              "物理规律，但参数辨识成本高、外推能力弱，难以刻画电调的非线性损耗。近年来数据驱动方法发展迅速："
              "Goli 等利用人工神经网络评估无人机电推进系统性能，并对动力总成推力进行预测[11][12]；"
              "Kosova 等用神经网络直接预测无刷直流电机与螺旋桨效率[13]。这类方法以台架实测数据为输入，"
              "能够容纳电机、电调与螺旋桨的非线性与耦合，输出连续的效率/推力映射，即“效率地图”，"
              "并可进一步作为代理模型嵌入优化回路。效率地图最初广泛用于车用电机与电驱动系统，"
              "用于描述不同转速、转矩下的效率分布，为能量管理与控制策略提供依据。将其拓展到多旋翼"
              "电机—螺旋桨—电调系统，仍需解决多工况耦合、样本稀疏与模型泛化等问题：现有研究多针对单一"
              "部件或单一桨型，对“电压—油门—转速”三维工况的联合建模及不确定性量化仍不充分。"),
        ("h", "2.4 电调效率、多目标优化与控制分配"),
        ("p", "电调损耗（开关损耗、导通损耗及驱动方式差异）在中小功率多旋翼中不可忽略，但难以直接测量，"
              "公开文献多将其并入“电机+电调”整体效率处理。优化方面，遗传算法、NSGA-II 等多目标优化方法"
              "被用于桨型、电机与供电电压组合的寻优；Madruga 等用神经网络补偿气动效应并改进多旋翼控制分配[14]，"
              "说明同一推力需求在不同转速分配下所需电功率不同，控制分配层同样存在效率优化空间，"
              "为效率地图向控制层延伸提供了接口。"),
        ("h", "2.5 发展趋势与本项目切入点"),
        ("p", "综合来看，该方向正从“单部件机理建模”走向“系统级实测+数据驱动代理模型+多目标匹配优化”，"
              "从“地面静态台架”走向“含来流与姿态影响的宽域工况”，从“效率评价”走向“效率驱动的设计—控制"
              "一体化”。然而，同时具备自建同步测量台架、覆盖“电压×油门×转速”的宽工况效率地图，"
              "以及以系统效率为目标的电机 KV 值/桨径-螺距/电调参数/供电电压联合寻优的公开研究尚未见系统报道。"
              "此外，现有标准如 GB 42590—2023、GB/T 38924.1—2020 主要针对安全性与环境适应性，"
              "动力系统效率的测试与评价方法尚缺乏统一规范[15][16]。这正是本项目拟切入的方向。"),
        ("h", "参考文献"),
        ("refs", [
            "[1] PILJEK P, KOTARSKI D, KRZNAR M. Method for characterization of a multirotor UAV electric propulsion system[J]. Applied Sciences, 2020, 10(22): 8229.",
            "[2] ZHU H, JIANG Z, ZHAO H, et al. Aerodynamic performance of propellers for multirotor unmanned aerial vehicles: measurement, analysis, and experiment[J]. Shock and Vibration, 2021, 2021: 9538647.",
            "[3] GOLI S, KURTULUŞ D F, ALHEMS L M, et al. Experimental study on efficient propulsion system for multicopter UAV design applications[J]. Results in Engineering, 2023, 20: 101555.",
            "[4] ZHAO A, WANG T, LIU D. Design and research of an electric unmanned aerial vehicle power system[J]. Journal of Physics: Conference Series, 2024, 2746(1): 012029.",
            "[5] BRANDT J, SELIG M. Propeller performance data at low Reynolds numbers[C]//49th AIAA Aerospace Sciences Meeting. Reston: AIAA, 2011: AIAA 2011-1255.",
            "[6] PARK D, LEE Y, CHO T, et al. Design and performance evaluation of propeller for solar-powered high-altitude long-endurance unmanned aerial vehicle[J]. International Journal of Aerospace Engineering, 2018, 2018: 5782017.",
            "[7] DAI X H, QUAN Q, REN J R, et al. Efficiency optimization and component selection for propulsion systems of electric multicopters[J]. IEEE Transactions on Industrial Electronics, 2019, 66(10): 7800-7809.",
            "[8] DE ANGELIS E L, GIULIETTI F, ROSSETTI G, et al. Performance analysis and optimal sizing of electric multirotors[J]. Aerospace Science and Technology, 2021, 118: 107057.",
            "[9] DELBECQ S, BUDINGER M, OCHOTORENA A, et al. Efficient sizing and optimization of multirotor drones based on scaling laws and similarity models[J]. Aerospace Science and Technology, 2020, 102: 105873.",
            "[10] BICZYSKI M, SEHAB R, WHIDBORNE J F, et al. Multirotor sizing methodology with flight time estimation[J]. Journal of Advanced Transportation, 2020, 2020: 9689604.",
            "[11] GOLI S, KURTULUŞ D F, WAQAR M, et al. Artificial neural network for the evaluation of electric propulsion system in unmanned aerial vehicles[J]. Neural Computing and Applications, 2025, 37: 8945-8961.",
            "[12] GOLI S, KURTULUŞ D F, WAQAR M, et al. Data-driven thrust prediction for UAV powertrains using artificial neural networks[J]. Neural Computing and Applications, 2026, 38(8): 264.",
            "[13] KOSOVA İ, YÖNETKEN A, BAYRAM F. Prediction of brushless DC motor and propeller efficiency using an artificial neural network model[J]. Düzce Üniversitesi Bilim ve Teknoloji Dergisi, 2024, 12(4).",
            "[14] MADRUGA S P, TAVARES A H B M, LUIZ S O D, et al. Aerodynamic effects compensation on multi-rotor UAVs based on a neural network control allocation approach[J]. IEEE/CAA Journal of Automatica Sinica, 2022, 9(2): 295-312.",
            "[15] 国家市场监督管理总局, 国家标准化管理委员会. 民用无人驾驶航空器系统安全要求: GB 42590—2023[S]. 北京: 中国标准出版社, 2023.",
            "[16] 国家市场监督管理总局, 国家标准化管理委员会. 民用轻小型无人机系统环境试验方法 第1部分: 总则: GB/T 38924.1—2020[S]. 北京: 中国标准出版社, 2020.",
        ]),
    ],
'''

start = src.index('    "二": [')
end = src.index('    "三": [')
new_src = src[:start] + NEW + src[end:]
io.open(PATH, 'w', encoding='utf-8').write(new_src)
print('patched:', len(src), '->', len(new_src))
