# -*- coding: utf-8 -*-
"""对 plan_part1.md / plan_part2.md 做定点修订：甘特表改为按月份表、8.8 插入预研图。"""
import io
import re

BASE = r'D:\下载\创新\work\plan'


def read(name):
    with open(f'{BASE}\\{name}', encoding='utf-8') as f:
        return f.read()


def write(name, text):
    with open(f'{BASE}\\{name}', 'w', encoding='utf-8') as f:
        f.write(text)


gantt = """### 5.2 月度任务安排（按月份列出重点）

| 时间 | 阶段 | 重点任务 | 里程碑/检查点 |
| --- | --- | --- | --- |
| 2026-11 | 启动与基础学习 | 启动会、分工、周报与看板、文献检索 5 篇、安全培训、Python 基础 | 周报与看板建立 |
| 2026-12 | 文献与方案 | 20 篇文献、指标体系初稿、台架方案初稿、采购询价 | 方案初稿组内评审 |
| 2027-01 | 方案定型与采购 | 台架方案/BOM 定稿、下单、课程补强 | **M1 方案评审通过** |
| 2027-02 | 台架搭建 | 加工/3D 打印、装配、电气接线、初步标定 | 台架组装完成 |
| 2027-03 | 标定与联调 | 推力/扭矩标定、同步采集联调、重复性试验、SOP 定稿 | **M2 台架验收** |
| 2027-04 | 部件测试 | 电机空载/负载、电调效率、螺旋桨 FM 测试 | 部件数据完成约 50% |
| 2027-05 | 系统组合测试 | 6 组组合多工况测试、数据入库、质量检查 | **M3 数据集完成** |
| 2027-06 | 清洗与机理建模 | 数据清洗、损耗参数辨识、不确定度评定 | 机理模型 v1 |
| 2027-07 | 数据驱动与地图 | 模型对比、混合建模、效率地图绘制 | **M4 模型与地图完成** |
| 2027-08 | 匹配优化 | 优化模型、Pareto 前沿、推荐方案 | Pareto 方案集 |
| 2027-09 | 台架验证 | 推荐方案复测、模型修正、补充实验 | **M5 优化方案验证** |
| 2027-10 | 总结与结题 | 研究报告、论文/软著、答辩材料 | **M6 结题** |

"""

figs = """
预研图件（示例模型输出，正式版替换为实测数据）：

![图 1　效率链随转速变化（18 英寸桨、22.2 V 母线）：电调/电机/螺旋桨 FM/系统效率与推力](../prestudy/fig/fig1_efficiency_chain.png)

![图 2　系统效率地图示例（18 英寸桨、KV=400）：油门×母线电压](../prestudy/fig/fig2_efficiency_map.png)

![图 3　匹配优化的桨径—悬停效率 Pareto 前沿（4 N 单轴推力，示例模型）](../prestudy/fig/fig3_pareto.png)
"""


def main():
    p1 = read('plan_part1.md')
    start = p1.index('### 5.2 月度任务安排')
    end = p1.index('### 5.3 关键路径与缓冲')
    p1 = p1[:start] + gantt + p1[end:]
    write('plan_part1.md', p1)
    print('part1 updated, gantt replaced')

    p2 = read('plan_part2.md')
    marker = '### 8.8 预研演示与工具链验证'
    seg_start = p2.index(marker)
    tail = p2[seg_start:]
    # 在 8.8 结论段之后、8.9 之前插入图
    anchor = '\n### 8.9 '
    idx = tail.index(anchor)
    tail = tail[:idx] + figs + tail[idx:]
    p2 = p2[:seg_start] + tail
    write('plan_part2.md', p2)
    print('part2 updated, figures inserted')
    print('part1 chars:', len(p1), 'part2 chars:', len(p2))


if __name__ == '__main__':
    main()
