# -*- coding: utf-8 -*-
"""规划书 v1.1 内容补丁：标准核查信息、GP 预研结果（8.11）、启动清单与附录更新。"""
import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.join(BASE, 'plan_part1.md')
P2 = os.path.join(BASE, 'plan_part2.md')


def read(path):
    with io.open(path, encoding='utf-8') as f:
        return f.read()


def write(path, text):
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def replace_once(text, old, new, tag):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f'[{tag}] expected 1 occurrence, got {n}')
    return text.replace(old, new, 1)


part1 = read(P1)
part1 = replace_once(
    part1,
    '**版本**：v1.0　　**编制日期**：2026-11-16',
    '**版本**：v1.1　　**编制日期**：2026-11-17',
    'version')
write(P1, part1)

part2 = read(P2)

# ---- 8.9 标准与数据源：替换第一条，补充国际标准 ----
old_89 = ('- GB/T 38058—2019《民用多旋翼无人机系统试验方法》：最相关的试验方法标准，'
          '可作试验大纲框架依据（是否含动力系统效率专项条款需查原文后再引用）。')
new_89 = (
    '- GB/T 38058—2019《民用多旋翼无人机系统试验方法》：已核实为现行国家标准，2019-10-18 发布、'
    '2020-05-01 实施，归口 SAC/TC 435，起草单位含中国航空综合技术研究所、大疆、北京航空航天大学等；'
    '标准适用于“民用多旋翼无人机系统及部件试验方法，最大起飞质量 150 kg 以下的民用轻小型电动多旋翼无人机系统及部件'
    '（其他类型可参照执行）”。可作为试验大纲的框架依据，但**是否包含动力系统效率/推力测试的专项条款尚未核实**，'
    '引用时只写标准名称，不写具体条款号。\n'
    '- 相关国际标准：ISO 4358:2023《Test methods for civil multi-copter unmanned aircraft system》'
    '（2023-05-04 发布，民用多旋翼试验方法），可作为试验设计的国际对照。'
)
part2 = replace_once(part2, old_89, new_89, '8.9')

# ---- 8.10 第 1 条：更新核查状态 ----
old_810 = '1. GB/T 38058—2019 原文是否含动力系统效率/推力测试条款（查原文后再引用）；'
new_810 = ('1. GB/T 38058—2019 已核实适用范围与发布实施信息，但尚未获取全文条款清单——需查原文确认'
           '是否含动力系统效率/推力测试条款（在此之前引用只写“试验方法标准”）；')
part2 = replace_once(part2, old_810, new_810, '8.10')

# ---- 新增 8.11 GP 预研结果 ----
section_811 = '''### 8.11 GP 代理模型预研（示范算例：学习曲线与不确定度）

- 目的：验证“效率地图 = 数据驱动模型”的完整流程——模拟台架采样 → GP 拟合 → 交叉验证 → 地图与不确定度 → 补测点推荐，并定量回答“每个组合需要多少测点”。
- 设置：18 in 桨、KV=400 的示范模型（`work/prestudy/prestudy_gp.py`），输入为归一化母线电压与油门，输出系统效率；120 个工况 × 3 次重复 = 360 条样本，模拟台架相对噪声 1.2%（约 0.7 个百分点）；核函数为 Matérn 5/2 + WhiteKernel，5 折交叉验证。
- 结果：GP 交叉验证 R²=0.949、RMSE=0.70 个百分点，已接近噪声水平（说明在该示范任务上 GP 达到数据精度上限）；同一数据下二次响应面（RSM）R²=0.892、RMSE=1.02 个百分点，GP 明显更优。
- 学习曲线：30 样本 R²≈0.51（不稳定）→ 60 样本 0.906 → 120 样本 0.936 → 180 样本 0.946 → 240 样本 0.934 → 300 样本 0.938；**约 120—180 条样本（40—60 个工况 × 3 重复）后进入平台期**，与调研“每组合 100—200 点”的建议一致，可作为正式试验规模的依据。
- 不确定度：95% 置信区间半宽在实测覆盖区约 1.4—2.3 个百分点，边界（尤其低油门端）明显更大；按“最大不确定度”自动推荐的下一个补测点全部集中在低油门边界，验证了“序贯补点 + 边界加密”的必要性。
- 结论与使用边界：①正式研究用实测数据重跑同一套流程（脚本、特征与数据格式已固定，只需替换数据源）；②示范模型较平滑，真实数据可能含更多局部结构，届时需增加机理约束（灰箱模型）与边界测点；③模型精度目标定为“预测误差 ≤1 个百分点或 ≤ 测量扩展不确定度（先达到者为准）”，避免无效增加测点。

![图 4　GP 预测的系统效率地图（左）与 95% 置信区间半宽（右，亮色为补测优先区）](../prestudy/fig/fig4_gp_map_uncertainty.png)

![图 5　效率模型学习曲线：GP（Matérn 5/2）与二次响应面对比](../prestudy/fig/fig5_learning_curve.png)

'''
marker = '---\n\n## 九、风险识别与应对'
part2 = replace_once(part2, marker, section_811 + marker, '8.11 insert')

# ---- 11.1 增加 GP 预研任务 ----
old_111 = ('- [ ] 学习 Python 基础并跑通 `work/prestudy/efficiency_demo.py`，看懂 3 张预研图'
           '（全员，技能 S1）')
new_111 = (old_111 + '\n- [ ] 跑通 `work/prestudy/prestudy_gp.py`，读懂学习曲线与不确定度图，'
           '理解“每组合测多少点”的依据（负责人 E，技能 O2/O3）')
part2 = replace_once(part2, old_111, new_111, '11.1')

# ---- 附录 C 第 5 条 ----
old_c = '5. 预研演示代码与图件：`work/prestudy/`（fig1—fig3、CSV）。'
new_c = ('5. 预研演示代码与图件：`work/prestudy/`（`efficiency_demo.py`、`prestudy_gp.py`、'
         'fig1—fig5、CSV、`gp_metrics.json`）。')
part2 = replace_once(part2, old_c, new_c, 'appC')

# ---- 附录 D 增加 GP 脚本行 ----
old_d = '| `work/prestudy/fig/` | 预研图件（图 1—图 3） |'
new_d = ('| `work/prestudy/prestudy_gp.py` | GP 代理模型、学习曲线与不确定度预研 |\n'
         '| `work/prestudy/fig/` | 预研图件（图 1—图 5） |')
part2 = replace_once(part2, old_d, new_d, 'appD')

write(P2, part2)
print('patched plan_part1.md / plan_part2.md OK')
for name, path in (('part1', P1), ('part2', P2)):
    print(name, len(read(path)), 'chars')
