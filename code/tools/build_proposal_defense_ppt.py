"""开题答辩 PPT 生成（依据新版申报书 v3 草稿 + 已有成果，v0.1）。

运行（需 python-pptx）：
  C:\\Users\\35509\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\python\\python.exe code\\tools\\build_proposal_defense_ppt.py
"""
from pathlib import Path

ROOT = Path(r"D:\下载\创新")
from pptx import Presentation
from pptx.util import Inches, Pt

FIG = ROOT / "data" / "processed" / "figures"
OUT = ROOT / "docs" / "规划" / "开题答辩PPT_v0.2.pptx"

# (标题, 要点, 配图文件名或 None)
SLIDES = [
    ("多旋翼 UAV 电机—螺旋桨—电调系统效率地图构建与匹配优化",
     ["开题答辩 · 2027 年大创（萌创项目）", "指导教师：宋受俊 教授 ｜ 自动化学院 ｜ 2026-11-21"], None),
    ("汇报结构", ["背景与问题 → 现状与缺口 → 目标与内容 → 方案与路线 → 已有基础 → 进度与成果 → 风险与下一步"], None),
    ("研究背景：巡检作业的省电问题",
     ["电力线路/变电站/光伏电站巡检：单架次塔数、是否换电直接受效率影响", "同推力下选不同桨型/电压，电功率差异可达数个百分点"], None),
    ("问题定义",
     ["部件效率相乘≠整机效率：电调损耗、电池压降、系统耦合难以解耦", "缺少宽工况、系统级、带不确定度的效率数据与地图"], None),
    ("研究现状与缺口",
     ["三条线：台架效率测试 / 电机—螺旋桨匹配 / 效率建模与控制分配", "缺口：缺实测→建模→地图→复测闭环，公开宽工况数据稀缺"], "paper_method_evolution_v0.1.png"),
    ("研究目标",
     ["建可复现地面台架，测整链效率 η_sys(SIM→MEASURED)", "构建电压×油门效率地图（同一桨型，附 U(k=2)），给出悬停/巡航匹配依据"], None),
    ("研究内容（7 项）",
     ["文献与指标定义 / 台架搭建与标定 / 多工况采集", "效率模型构建与精度比较 / 效率地图 / 应用示例 / 实验验证"], None),
    ("技术路线（六环节 → 五阶段）",
     ["调研→台架→测试→建模→分析→复测", "S0 输入冻结 → S1 台架标定 → S2 多工况 → S3 建模地图 → S4 应用复测 → S5 结题"], "plan_gantt_v0.1.png"),
    ("台架与采集方案",
     ["单轴反扭矩臂台架：桨盘离地≥1.5D、5 mm PC 防护罩、急停串电调供电", "拉压力/扭矩传感器 + ADS1256(24bit) + STM32 + 串口 115200，≥1 kS/s"], None),
    ("标定与不确定度",
     ["M1 砝码双人加载/卸载 6 点，F=k·raw+b；目标 R²≥0.9995、重复性/迟滞≤0.5% FS", "η_sys 合成不确定度目标 U(k=2) ≤3%"], None),
    ("试验设计（DoE）与数据规模",
     ["3 电压×5 油门×3 桨×3 重复 = 135 次；GP 反解目标推力排程 30 次演示", "可编程电源固定母线电压；预热 30 s、稳态 3 s、温升 >5 ℃ 暂停"], None),
    ("建模与效率地图",
     ["机理模型 + 响应面/GP/神经网络，LOOCV 比较并给出失效边界", "GP 平滑代理：16 SIM 点 LOOCV RMSE 0.0017、R²=0.9999"], "efficiency_map_v0.4.png"),
    ("应用示例：悬停/巡航两点匹配",
     ["按工作点查询候选项，比较四档母线电压（同一桨型）；考虑推力裕度/最高转速/母线电流", "多目标 Pareto + 补测推荐：σ 策略网格 RMSE 约 6 倍改善（SIM 闭环）"], "selection_v0.4.png"),
    ("同一桨型·电压对比（v4 口径）",
     ["固定桨型 P1 10×4.5（不更换桨型）；悬停/巡航两工作点比较 11.1/14.8/22.2/29.6 V",
      "判据：同推力下 η_sys 差 ≥2% 且超 2·U(k=2) 才作为匹配依据；数值待实测（当前仅 SIM 方法演示）"], None),
    ("已有基础（软件原型与调研）",
     ["6 模块 281 项自动化测试：采集/处理/地图/仿真/选型/对标工具链", "40 篇文献 36 DOI 核验；UIUC 8 桨 112 点方法验证（REFERENCE）；软著材料 323 页"], "uiuc_benchmark_v0.2.png"),
    ("进度与预期成果",
     ["2026-11 冻结 → 12 标定/链路上线 → 2027-01~05 测试 → 2026-06~07 地图 → 08~09 复测 → 10 结题", "成果：台架1套 / 数据集1套 / 模型与地图 / 论文与软著 / 可交接材料"], "plan_gantt_v0.1.png"),
    ("风险与对策",
     ["采购延迟→询价锁3家/替代方案；标定超差→双人复标；温升漂移→暂停与冷却", "台架外推→风洞对照与定性修正；进度冲突→分批交付与导师例会"], None),
    ("下一步与致谢",
     ["下周：成员信息录入、导师签名、BOM 下单、最小链路采购", "感谢指导教师与实验室支持 · Q&A"], None),
]

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
for i, (title, bullets, img) in enumerate(SLIDES):
    layout = prs.slide_layouts[0] if i == 0 else prs.slide_layouts[1]
    s = prs.slides.add_slide(layout)
    s.shapes.title.text = title
    body = s.placeholders[1].text_frame
    body.text = bullets[0]
    for b in bullets[1:]:
        body.add_paragraph().text = b
    for p in body.paragraphs:
        p.font.size = Pt(20 if i == 0 else 17)
    if img:
        f = FIG / img
        if f.exists():
            s.shapes.add_picture(str(f), Inches(5.2), Inches(2.6), width=Inches(7.6))
OUT.parent.mkdir(parents=True, exist_ok=True)
try:
    prs.save(OUT)
    print("saved", OUT, OUT.stat().st_size)
except PermissionError:
    fallback = OUT.with_name(OUT.stem + "_新.pptx")
    prs.save(fallback)
    print("fallback", fallback, fallback.stat().st_size)
