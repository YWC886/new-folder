"""重点项目进度甘特图 v0.1（SIM/计划性，不是实验结果）。"""
import sys
from pathlib import Path

ROOT = Path(r"D:\下载\创新")
sys.path.insert(0, str(ROOT / "work" / "pylibs"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.dates as mdates  # noqa: E402
from datetime import date  # noqa: E402

phases = [
    ("申报与输入冻结", date(2026, 11, 1), date(2026, 11, 30), "申报表/确认单/BOM"),
    ("采购与采集链路", date(2026, 12, 1), date(2026, 12, 31), "传感器/24bit ADC/串口"),
    ("台架搭建与标定", date(2027, 1, 1), date(2027, 2, 28), "双人砝码标定/U(k=2)"),
    ("部件与组合测试", date(2027, 3, 1), date(2027, 5, 31), "≥135 工况实测"),
    ("效率地图与应用", date(2027, 6, 1), date(2027, 7, 31), "GP 地图/选型/补测"),
    ("复测修正与结题", date(2027, 8, 1), date(2027, 10, 31), "论文/软著/报告"),
]

fig, ax = plt.subplots(figsize=(11.5, 4.2))
for i, (name, start, end, note) in enumerate(phases):
    y = len(phases) - i
    ax.barh(y, (end - start).days, left=start, height=0.55, color="#3b6ea5", alpha=0.85)
    ax.text(start, y + 0.38, name, fontsize=9, va="bottom", fontweight="bold")
    ax.text(start, y - 0.32, note, fontsize=7.5, va="top", color="#555")

ax.axvline(date(2026, 12, 4), color="crimson", ls="--", lw=1.2)
ax.text(date(2026, 12, 5), len(phases) + 0.9, "学院审核 12-04", color="crimson", fontsize=8)
ax.set_yticks([])
ax.set_xlim(date(2026, 10, 25), date(2027, 11, 10))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax.set_title("多旋翼动力系统效率地图项目 · 进度计划（2026-11 → 2027-10）", fontsize=11)
ax.grid(axis="x", ls=":", alpha=0.5)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
fig.text(0.5, 0.02, "PLANNING CHART（计划性，非实验结果）— 依据申报表六阶段与 M0.1–M0.5", ha="center", color="crimson", fontsize=9)
fig.tight_layout(rect=(0, 0.05, 1, 1))
out = ROOT / "data" / "processed" / "figures" / "plan_gantt_v0.1.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=150)
print("saved", out, out.stat().st_size)
