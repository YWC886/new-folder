"""答辩 PPT 骨架生成（16 页，文本版；后续可替换图为可编辑图表/图片）。"""
import sys
from pathlib import Path

ROOT = Path(r"D:\下载\创新")
sys.path.insert(0, str(ROOT / "work" / "pylibs"))
from pptx import Presentation  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

SLIDES = [
    ("多旋翼 UAV 电机—螺旋桨—电调系统效率地图", ["大创项目答辩 / 结题汇报", "2026-11-21 · 指导教师：宋受俊"]),
    ("1. 问题与目标", ["巡检作业：同推力下选哪支桨、哪档电压最省电", "目标：整链效率地图 + 选型依据 + 不确定度"]),
    ("2. 研究现状与缺口", ["部件表征 → 地图与优化 → 缺整链闭环", "公开数据多、台架实测少、电调损耗难测"]),
    ("3. 技术路线总览", ["S0 输入冻结 → S1 台架标定 → S2 多工况测试", "→ S3 建模地图 → S4 应用复测 → S5 结题"]),
    ("4. 台架与采集", ["单轴台架：桨盘离地≥1.5D，防护罩+急停", "ADS1256→STM32→串口 115200，≥1 kS/s"]),
    ("5. 标定与不确定度", ["M1 砝码双人加载/卸载 6 点拟合", "目标：R²≥0.9995，重复性/迟滞≤0.5%FS"]),
    ("6. 效率口径", ["η_em=P_shaft/P_elec；FM=T^1.5/√(2ρA)/P_shaft", "η_sys=FM·η_em；U(k=2) 地图不确定度带"]),
    ("7. 数据与地图", ["3 电压×5 油门×3 桨×3 重复 = 135 次排程", "GP 平滑代理：LOOCV RMSE 0.0017（16 SIM 点）"]),
    ("8. 选型与补测", ["多目标 Pareto：效率/电流/稳健性", "σ vs 不补测：网格 RMSE 约 6 倍改善（SIM 闭环）"]),
    ("9. 公开数据对标", ["UIUC 8 桨 112 点：通用先验 CT 11.37%/CP 16.68%", "逐桨先验可降到 0.3–1.5%（样本内上限，do_not_apply）"]),
    ("10. 仿真与热", ["电池压降+调速器：η 损失随油门增大", "双节点热网络：绕组峰值 82.9°C / 定子 66.2°C"]),
    ("11. 当前成果（软件原型）", ["281 项测试 / 60 源文件 / 310 页软著源代码页", "Excel 12 表、Word 报告、复现清单 182 文件"]),
    ("12. 风险与对策", ["采购延迟 / 标定超差 / 温升漂移 / 外推偏差 / 进度", "对策：询价锁 3 家、双人标定、可编程电源、风洞对照、门禁"]),
    ("13. 实测计划", ["M0.4 采集链路 + 砝码标定 → 135 工况", "实测后按论文 §4.1 占位表替换"]),
    ("14. 预期成果", ["台架 1 套 / 数据集 1 套 / 地图与工具 / 论文 / 可交接材料", "结论边界：SIM/REFERENCE 不写成实测"]),
    ("17. 备用页 数据字典与目录", ["RAW 13 列 / 串口协议 11 列 / 元数据与校验规则", "docs/design/data_dictionary_v0.1.md"]),
    ("17b. 备用页 运行环境与复现", ["py -3.12 + work/pylibs；281 项测试；check_release.py 一键校验", "docs/参考/软件环境与使用说明.md"]),
    ("15. 致谢 / Q&A", ["感谢指导教师与实验室支持", "Q&A"]),
]

IMGS = {
    2: "paper_method_evolution_v0.1.png",
    3: "plan_gantt_v0.1.png",
    7: "efficiency_map_v0.4.png",
    8: "selection_v0.4.png",
    9: "uiuc_benchmark_v0.2.png",
    10: "two_node_thermal_v0.4.png",
}
FIGDIR = ROOT / "data" / "processed" / "figures"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
for i, (title, bullets) in enumerate(SLIDES):
    layout = prs.slide_layouts[0] if i == 0 else prs.slide_layouts[1]
    s = prs.slides.add_slide(layout)
    s.shapes.title.text = title
    body = s.placeholders[1].text_frame
    body.text = bullets[0]
    for b in bullets[1:]:
        p = body.add_paragraph()
        p.text = b
    for p in body.paragraphs:
        p.font.size = Pt(20 if i == 0 else 18)
    if i > 0:
        body.paragraphs[0].font.size = Pt(20)
    if i in IMGS:
        img = FIGDIR / IMGS[i]
        if img.exists():
            s.shapes.add_picture(str(img), Inches(4.9), Inches(2.45), width=Inches(7.9))
out = ROOT / "docs" / "规划" / "答辩PPT骨架_v0.1.pptx"
prs.save(out)
print("saved", out, out.stat().st_size)
