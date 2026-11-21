"""论文 §2 方法演进图：部件表征 → 地图/优化 → 本文闭环（示意图，非实验结果）。"""
import sys
from pathlib import Path

ROOT = Path(r"D:\下载\创新")
sys.path.insert(0, str(ROOT / "work" / "pylibs"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

cols = [
    ("部件级表征", "电机/桨/电调单独测", "Piljek 2020 · Cox 2025", "#9dc3e6"),
    ("地图与优化", "性能地图驱动选型/优化", "Nam 2023 · Røstum 2026", "#a9d18e"),
    ("整链闭环（本文）", "实测 + GP + UQ + 复测", "本文目标（D012/D026/D043）", "#f4b183"),
]
fig, ax = plt.subplots(figsize=(10.5, 3.4))
for i, (title, body, who, color) in enumerate(cols):
    x = i * 3.4
    ax.add_patch(plt.Rectangle((x, 0.75), 3.0, 1.6, facecolor=color, edgecolor="#555", lw=1.2, alpha=0.9))
    ax.text(x + 1.5, 2.05, title, ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(x + 1.5, 1.45, body, ha="center", va="center", fontsize=9.5)
    ax.text(x + 1.5, 1.02, who, ha="center", va="center", fontsize=8, color="#333")
    if i < 2:
        ax.annotate("", xy=(x + 3.35, 1.55), xytext=(x + 3.02, 1.55),
                    arrowprops=dict(arrowstyle="->", lw=1.6, color="#555"))
ax.set_xlim(-0.2, 10.3)
ax.set_ylim(0.5, 2.6)
ax.axis("off")
fig.text(0.5, 0.93, "方法演进：从部件表征到整链闭环", ha="center", fontsize=11.5, transform=fig.transFigure)
fig.text(0.5, 0.06, "SCHEMATIC ONLY（示意，非实验结果）", ha="center", color="crimson", fontsize=8.5)
fig.tight_layout(rect=(0, 0.1, 1, 0.9))
out = ROOT / "data" / "processed" / "figures" / "paper_method_evolution_v0.1.png"
fig.savefig(out, dpi=150)
print("saved", out, out.stat().st_size)
