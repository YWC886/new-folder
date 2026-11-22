"""ESC 效率测量接线示意图（SIM-agnostic 原理图，非产品接线图）。"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "pylibs"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = ROOT / "data" / "processed" / "figures" / "esc_measurement_v0.1.png"


def box(ax, x, y, w, h, title, sub=""):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc="#e8f0fb", ec="#2c5f9e", lw=1.6)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center", fontsize=12, weight="bold")
    if sub:
        ax.text(x + w / 2, y + h * 0.25, sub, ha="center", va="center", fontsize=9, color="#333")


def arrow(ax, x1, y1, x2, y2, text="", dy=0.12):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16, lw=1.8, color="#333"))
    if text:
        ax.text((x1 + x2) / 2, max(y1, y2) + dy, text, ha="center", fontsize=9, color="#a33")


fig, ax = plt.subplots(figsize=(13, 4.6))
ax.set_xlim(0, 13); ax.set_ylim(0, 5); ax.axis("off")

box(ax, 0.3, 2.2, 2.0, 1.5, "可编程直流电源", "限流保护 / 固定母线电压")
box(ax, 3.0, 2.2, 1.25, 1.5, "分流器", "75 mV / 60 A")
box(ax, 4.9, 2.2, 1.6, 1.5, "电调 (ESC)", "被测环节")
box(ax, 7.2, 2.2, 1.6, 1.5, "电机", "三相")
box(ax, 9.5, 2.2, 1.5, 1.5, "台架", "推力 / 扭矩")
box(ax, 11.6, 2.2, 1.1, 1.5, "螺旋桨", "")

arrow(ax, 2.3, 2.95, 3.0, 2.95, "U_bus")
arrow(ax, 4.25, 2.95, 4.9, 2.95, "I_in")
arrow(ax, 6.5, 2.95, 7.2, 2.95, "3 相 PWM")
arrow(ax, 8.8, 2.95, 9.5, 2.95, "T / Q / n")
arrow(ax, 11.0, 2.95, 11.6, 2.95)

# 测量点标注
pts = [
    (2.65, 2.2, 1.55, "P1: 母线电压 U_bus"),
    (3.9, 2.05, 1.22, "P2: 母线电流 I_in（分流器+隔离放大）"),
    (5.7, 2.05, 0.89, "P3: 电调输出三相 U/I（功率分析仪或相电流+相电压）"),
    (8.35, 2.05, 1.55, "P4: 转速 n、扭矩 Q、推力 T"),
]
for x, y, ly, t in pts:
    ax.plot([x], [y], marker="v", color="#c0392b", ms=9)
    ax.text(x, ly, t, ha="center", fontsize=8.2, color="#c0392b")

ax.text(0.2, 0.55, "效率口径（D012）：P_elec,in = U_bus·I_in；P_esc,out = 三相电功率；η_esc = P_esc,out/P_elec,in；"
        "P_shaft = Q·ω；η_em = P_shaft/P_esc,out；η_sys = P_shaft/P_elec,in", fontsize=9, color="#1a5")
ax.text(0.2, 0.18, "示意原理图，非产品接线图；实测须按 SOP 双人、限流、防护罩、急停到位；本图不构成任何实测结论（SIM/REFERENCE/MEASURED 纪律）",
        fontsize=8.5, color="#666")
fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=150)
print("saved", OUT, OUT.stat().st_size)
