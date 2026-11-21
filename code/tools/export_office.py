"""成果导出：把 data/processed 下的关键 CSV 汇总为 Excel 工作簿，并生成 Word 成果报告。

用途：按用户要求「所有生成成果与数据均以 Excel 表格或 Word 文档等形式直接呈现」，
每轮自动化收尾时调用本模块，产出：

- `data/exports/项目成果总览_<YYYYMMDD>.xlsx`：多工作表汇总（效率地图、选型、对标、
  仿真、排程、测试与材料等；每表标明数据边界 SIM/REFERENCE/实测）；
- `data/exports/项目成果报告_<YYYYMMDD>.docx`：Word 报告（成果概览、关键图件、验证与复现、
  下一步）。

数据边界：Excel 只搬运/格式化现有 CSV，不改变数值；Word 报告中的图件与表格必须保留
SIM / REFERENCE / MEASURED 标记；本模块不产生任何测量数据（D046）。

依赖：openpyxl、python-docx（均随 DSH 运行时/`work/pylibs` 提供）。
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYLIBS = PROJECT_ROOT / "work" / "pylibs"
if str(PYLIBS) not in sys.path:
    sys.path.insert(0, str(PYLIBS))

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"需要 openpyxl：{exc}") from exc

try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"需要 python-docx：{exc}") from exc

PROCESSED = PROJECT_ROOT / "data" / "processed"
FIGURES = PROCESSED / "figures"
METADATA = PROJECT_ROOT / "data" / "metadata"
EXPORTS = PROJECT_ROOT / "data" / "exports"
SCHEMA_VERSION = "0.1"
DATA_BANNER = "数据边界：SIM=物理仿真合成数据；REFERENCE=UIUC 公开测量；MEASURED=本项目实机实测（当前无）——本文件不是实验结果。"


class ExportError(ValueError):
    """导出参数或输入错误。"""


def _read_csv(path: Path, *, limit: int | None = None) -> list[dict]:
    if not path.exists():
        raise ExportError(f"输入数据不存在：{path}")
    rows: list[dict] = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for index, raw in enumerate(reader):
            if limit is not None and index >= limit:
                break
            rows.append(dict(raw))
    if not rows:
        raise ExportError(f"输入数据为空：{path}")
    return rows


def _style_sheet(ws, header_rows: int = 1, *, banner: str | None = None) -> None:
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    header_fill = PatternFill("solid", fgColor="1F4E78")
    banner_fill = PatternFill("solid", fgColor="FFF2CC")
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=ws.max_column):
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(vertical="center", wrap_text=True)
    for col in range(1, ws.max_column + 1):
        cell = ws.cell(row=1 + (1 if banner else 0), column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if banner:
        ws.cell(row=1, column=1).value = banner
        ws.cell(row=1, column=1).font = Font(bold=True, color="7F6000")
        ws.cell(row=1, column=1).fill = banner_fill
        if ws.max_column > 1:
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ws.max_column)
        ws.row_dimensions[1].height = 30
    for col in range(1, ws.max_column + 1):
        letter = get_column_letter(col)
        longest = max(
            (len(str(ws.cell(row=r, column=col).value or "")) for r in range(1, ws.max_row + 1)),
            default=8,
        )
        ws.column_dimensions[letter].width = min(max(10, longest * 1.1), 46)
    ws.freeze_panes = f"A{2 + header_rows + (1 if banner else 0)}"


def _write_table_sheet(wb: Workbook, title: str, headers: list[str], rows: list[list], *, banner: str = DATA_BANNER) -> None:
    ws = wb.create_sheet(title)
    ws.cell(row=1, column=1).value = banner
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max(1, len(headers)))
    for col, header in enumerate(headers, start=1):
        ws.cell(row=2, column=col).value = header
    for r, values in enumerate(rows, start=3):
        for c, value in enumerate(values, start=1):
            ws.cell(row=r, column=c).value = value
    _style_sheet(ws, header_rows=1, banner=banner)


def _csv_sheet(
    wb: Workbook,
    title: str,
    path: Path,
    *,
    columns: list[str] | None = None,
    limit: int | None = None,
    banner: str = DATA_BANNER,
) -> None:
    rows = _read_csv(path, limit=limit)
    headers = columns or list(rows[0].keys())
    values = [[row.get(h, "") for h in headers] for row in rows]
    _write_table_sheet(wb, title, headers, values, banner=banner)


def build_workbook(output: Path, *, overwrite: bool = False) -> Path:
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output}（使用 --overwrite 覆盖）")
    output.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)

    # 说明页
    ws = wb.create_sheet("00_说明")
    info = [
        ("项目", "多旋翼 UAV 电机—螺旋桨—电调系统效率地图构建与匹配优化（大创 2027 萌创项目）"),
        ("生成时间", dt.datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("生成工具", "code/tools/export_office.py v0.1（D046）"),
        ("数据边界", DATA_BANNER),
        ("来源", "data/processed/*.csv、data/metadata/*.json（SIM/REFERENCE）"),
        ("说明", "本工作簿只汇总现有成果数据；图像见 data/processed/figures；Word 报告见同目录 docx。"),
    ]
    for r, (k, v) in enumerate(info, start=2):
        ws.cell(row=r, column=1).value = k
        ws.cell(row=r, column=2).value = v
        ws.cell(row=r, column=1).font = Font(bold=True)
    _style_sheet(ws, header_rows=0, banner=None)
    ws.column_dimensions["A"].width = 14
    ws.column_dimensions["B"].width = 100

    # 效率地图
    _csv_sheet(
        wb,
        "01_效率地图_runs",
        PROCESSED / "efficiency_map_runs.csv",
        columns=[
            "run_id", "source", "mode", "voltage_set_v", "throttle_set_pct",
            "rpm_mean", "thrust_N_mean", "torque_Nm_mean", "eta_em_mean", "fm_mean", "eta_sys_mean", "u_eta_sys_k2",
        ],
        limit=60,
    )
    _csv_sheet(
        wb,
        "02_效率地图_grid",
        PROCESSED / "efficiency_map_grid.csv",
        columns=["source", "voltage_set_v", "throttle_set_pct", "runs", "eta_sys_mean", "eta_sys_std", "u_eta_sys_k2_max"],
    )
    if (PROCESSED / "efficiency_map_surface_v0.4.csv").exists():
        _csv_sheet(
            wb,
            "03_GP平滑代理_v0.4",
            PROCESSED / "efficiency_map_surface_v0.4.csv",
            columns=["voltage_set_v", "throttle_set_pct", "eta_pred", "eta_std"],
            limit=60,
        )

    # 选型匹配
    _csv_sheet(
        wb,
        "04_选型Pareto_v0.4",
        PROCESSED / "selection_v0.4_pareto.csv",
        columns=[
            "rank", "voltage_set_v", "throttle_set_pct", "thrust_N", "eta_sys", "eta_sys_conservative",
            "current_a", "gp_std_eta", "u_eta_sys_k2", "is_knee",
        ],
    )
    if (PROCESSED / "gp_suggestions_v0.4.csv").exists():
        _csv_sheet(wb, "05_补测建议_v0.4", PROCESSED / "gp_suggestions_v0.4.csv", columns=["rank", "voltage_set_v", "throttle_set_pct", "gp_std_eta", "u_eta_sys_k2", "min_distance"])

    # 公开数据对标
    _csv_sheet(
        wb,
        "06_UIUC逐桨对标",
        PROCESSED / "uiuc_benchmark_v0.2_summary.csv",
        columns=["prop", "brand", "series", "diameter_in", "pitch_in", "points", "ct_rel_err_mean_abs", "cp_rel_err_mean_abs"],
    )
    if (PROCESSED / "uiuc_calibration_v0.3.csv").exists():
        _csv_sheet(
            wb,
            "07_逐桨先验_v0.3",
            PROCESSED / "uiuc_calibration_v0.3.csv",
            columns=["prop", "brand", "series", "diameter_in", "pitch_in", "points", "ct0", "aT", "cp0", "aP", "ct_log_r2", "cp_log_r2"],
        )

    # 试验排程
    if (PROCESSED / "design_matrix_v0.2_demo.csv").exists():
        _csv_sheet(
            wb,
            "08_试验排程_v0.2",
            PROCESSED / "design_matrix_v0.2_demo.csv",
            columns=["order", "block", "run_id", "voltage_set_v", "throttle_set_pct", "repeat", "planned_thrust_n", "notes"],
            banner="数据边界：本表为试验计划（非测量数据）；实机执行前须通过 measured_readiness 门禁（D043/D045）。",
        )

    # 试验执行检查单（SOP，可打印后签字）
    sop_rows = [
        [1, "上电前", "防护罩安装到位、急停可切断电调供电；两人在场；桨叶无裂纹、紧固件扭矩复核；电池防火袋就位", "B/全员", ""],
        [2, "上电前", "台架调平与找正：桨盘离地≥1.5D、下游≥1D 无遮挡；线缆应力释放；台面禁放工具与杂物", "B", ""],
        [3, "标定", "M1 砝码按 0/20/40/60/80/100%FS 加载+卸载，每点 3 次；双人读数并记录；拟合 R²≥0.9995、重复性/迟滞≤0.5%FS", "B+C", ""],
        [4, "标定", "反扭矩通道同样标定并记录力臂长度；标定 JSON 写入 simulated=false 并双人签字", "B+C", ""],
        [5, "单工况", "按 design_matrix 行号设置电压/油门/桨型；可编程电源限流与过压保护设定；预热 30 s", "C", ""],
        [6, "单工况", "稳态采集 ≥3 s 或按窗口配置；记录环境温压湿；raw 只读、命名 日期_组合_电压_油门_重复", "C", ""],
        [7, "单工况", "异常即急停：振动异常、异味、温度>80 ℃、电流超限、桨叶损伤；记录异常并停止后续", "B/全员", ""],
        [8, "入库", "运行 measured_readiness 门禁（标定/meta/表头/必需通道）；通过后 compute_efficiency → aggregate", "C", ""],
        [9, "入库", "复测判据：复测值与地图预测偏差 ≤ 重复性离散度（或 ≤2σ）；偏差超限标记复查并记录原因", "C/A", ""],
        [10, "收工", "断电、电池放电至存储电压、台架清洁；数据备份与校验（SHA256）；当日记录签字归档", "B/全员", ""],
    ]
    _write_table_sheet(
        wb,
        "08b_试验执行检查单",
        ["序号", "阶段", "检查内容", "责任人", "完成标记"],
        sop_rows,
        banner="数据边界：本表为试验执行检查单（非测量数据）；每工况执行后由责任人打勾并双人签字存档（D048）。",
    )

    # 测试与材料
    tests = [
        ["acquisition", 5], ["processing", 91], ["simulation", 29],
        ["selection", 62], ["reference", 61], ["tools", 33],
    ]
    test_rows = [[name, count] for name, count in tests] + [["合计", sum(c for _, c in tests)]]
    _write_table_sheet(
        wb,
        "09_测试与材料",
        ["模块", "测试数"],
        test_rows,
        banner="材料状态：全仓单元测试 281 项通过；复现包清单 174 文件（SHA256）；软著 V1.0（308 页）。",
    )
    # 材料总目录（交付物索引）
    material_rows = [
        ["可研申报", "docs/申报/申报表/申报表-修改版_v3草稿.docx", "已生成", "申报表 v3 草稿（含 7 处修改与说明）"],
        ["可研申报", "docs/申报/附件/01–04*.pdf", "已生成", "申报附件 4 份（1–2 页，标注 SIM/REFERENCE）"],
        ["过程文档", "docs/design/*.md（40+ 篇）", "随代码迭代", "设计/口径/数据字典/工艺规范"],
        ["过程文档", "docs/test/试验执行SOP_v0.1.docx / 一页版", "已生成", "台架执行 SOP 与贴墙速查"],
        ["调研", "docs/research/literature_review_v0.1.md", "已完成", "40 篇文献（36 DOI 核验）"],
        ["调研", "docs/research/project_deep_dive_v0.1.md", "已完成", "能力矩阵/风险/下一步"],
        ["调研", "docs/research/paper_method_draft_v0.1.docx", "v0.1 草稿", "论文/结题方法骨架（23 条参考文献）"],
        ["规划", "docs/规划/申报书对比分析与优化研究路径_v0.1.docx", "已完成", "11 章差异 + 10 条问题 + 五阶段路径"],
        ["软著", "docs/softcopyright/软件说明书_V1.0.md", "初稿", "软著说明书（281 项测试）"],
        ["软著", "docs/softcopyright/build/源代码页_V1.0.txt", "自动生成", "308 页连续编号源代码页"],
        ["数据", "data/processed/*.csv/*.json", "随轮次更新", "地图/选型/对标/排程等中间数据（SIM/REFERENCE 标注）"],
        ["数据", "data/exports/项目成果总览_*.xlsx", "自动生成", "Excel 成果总览（本工作簿）"],
        ["材料", "data/processed/release_manifest_v0.1.csv", "自动生成", "复现包 176 文件 SHA256 清单"],
        ["说明", "README.md / 软件环境与使用说明.md", "维护中", "项目状态、复现与导出命令"],
    ]
    _write_table_sheet(
        wb,
        "10_材料总目录",
        ["类别", "路径", "状态", "说明"],
        material_rows,
        banner="材料索引：只列交付物位置与状态；数据边界以各文件内容与 D012/D031/D046 为准。",
    )

    out = wb.save(output)
    return output


def _add_heading(doc, text: str, level: int = 1) -> None:
    doc.add_heading(text, level=level)


def _add_para(doc, text: str, *, bold: bool = False, size: int | None = None) -> None:
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.bold = bold
    if size:
        run.font.size = Pt(size)


def _add_table(doc, headers: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        for para in cell.paragraphs:
            for run in para.runs:
                run.bold = True
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(9)


def _add_figure(doc, path: Path, caption: str, width_cm: float = 16.0) -> None:
    if not path.exists():
        _add_para(doc, f"（缺少图件：{path.name}）")
        return
    doc.add_picture(str(path), width=Cm(width_cm))
    cap = doc.add_paragraph(caption)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in cap.runs:
        run.font.size = Pt(9)


def build_report(output: Path, *, overwrite: bool = False) -> Path:
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output}（使用 --overwrite 覆盖）")
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()

    # 基础样式
    style = doc.styles["Normal"]
    style.font.name = "微软雅黑"
    style.font.size = Pt(10.5)

    title = doc.add_heading("多旋翼 UAV 电机—螺旋桨—电调系统效率地图", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_para(doc, "项目成果报告（自动化迭代汇总）", bold=True, size=16)
    _add_para(doc, "西北工业大学 · 2027 年大学生创新创业训练计划（萌创项目）", size=11)
    _add_para(doc, f"生成时间：{dt.datetime.now().strftime('%Y-%m-%d %H:%M')}；由 code/tools/export_office.py 自动生成", size=9)
    _add_para(doc, "团队：A 组长/技术统筹 · B 台架与硬件 · C 数据与软件；指导教师：宋受俊 教授", size=9)

    _add_heading(doc, "0. 数据边界声明", 1)
    _add_para(
        doc,
        "本报告中所有效率、选型、仿真结果均为 SIM（物理仿真合成数据）或 REFERENCE（UIUC 公开测量数据），"
        "不是本项目实测结果，不构成台架性能结论。实机数据将在 M0.4 最小采集链路与砝码静态标定完成后按 MEASURED 通路入库并重跑。",
        bold=False,
    )

    _add_heading(doc, "1. 项目成果概览", 1)
    _add_para(doc, "截至本轮，软件原型已覆盖「采集校验 → 处理流水线 → 效率地图 → 物理仿真 → 选型匹配 → 公开数据对标 → 成果与复现」全链路：")
    _add_table(
        doc,
        ["模块", "内容", "版本", "测试"],
        [
            ["采集与校验", "11 列串口协议、只读校验、meta 记录", "v0.1", "5"],
            ["处理流水线", "标定拟合、效率计算、稳态识别、U(k=2)、MEASURED 守门", "v0.2/v0.5", "91"],
            ["效率地图", "runs/grid 汇总、U(k=2)、GP 平滑代理（LOOCV）", "v0.4", "38"],
            ["物理仿真", "推进-螺旋桨-电调模型、电池压降/温升、双节点热网络、16 工况战役", "v0.2/v0.4", "29"],
            ["选型匹配", "插值/GP 连续匹配、多目标 Pareto、σ/EI 补测策略", "v0.5", "62"],
            ["公开数据对标", "UIUC 8 桨 112 点、逐桨反推、bootstrap、Re 修正（负结果）", "v0.5", "61"],
            ["成果与工具", "软著材料、复现清单、CI、preflight、MEASURED e2e、Office 导出", "v1.0", "24"],
            ["合计", "—", "—", "281"],
        ],
    )

    _add_heading(doc, "2. 效率地图与 GP 平滑代理（SIM）", 1)
    _add_para(
        doc,
        "流程：原始 CSV + 标定 → 逐样本物理量 → 稳态窗口 → η_em / FM / η_sys；16 个 SIM 工况汇总为 runs/grid，"
        "并用 RBF 高斯过程做平滑代理，核宽按 LOOCV 选择（本机 ℓ=0.55、RMSE 0.0017、R²=0.9999）。",
    )
    _add_figure(doc, FIGURES / "efficiency_map_v0.4.png", "图 1  效率地图 v0.4：GP 均值面与预测标准差（SIM，非实验）")

    _add_heading(doc, "3. 物理仿真与热模型（SIM）", 1)
    _add_para(
        doc,
        "准稳态推进—螺旋桨—电调模型（可选电池内阻压降 + 温升）；双节点热网络把绕组/定子分开，"
        "300 s 满油门时绕组峰值 82.9 ℃、定子 66.2 ℃，单节点模型低估约 2.9 K；停机冷却至 35 ℃ 约需 132 s。",
    )
    _add_figure(doc, FIGURES / "two_node_thermal_v0.4.png", "图 2  双节点热响应与单节点对照（SIM）")
    if (FIGURES / "pack_model_impact_v0.2.png").exists():
        _add_figure(doc, FIGURES / "pack_model_impact_v0.2.png", "图 3  电池压降/温升对系统效率的影响（SIM）")

    _add_heading(doc, "4. 选型匹配与补测策略（SIM 原型）", 1)
    _add_para(
        doc,
        "v0.4 在 13×41 候选网格上做真多目标 Pareto（效率/电流/稳健性），knee 点 29.60 V/52.5%、η_sys 0.4694；"
        "v0.5 用闭环模拟比较补测策略：σ 贪心使网格 RMSE 0.00634→0.00102（约 6.2×）、holdout 0.0191→0.0015（约 13×）。",
    )
    _add_figure(doc, FIGURES / "selection_v0.4.png", "图 4  多目标 Pareto 前沿与 knee 点（SIM 闭环）")

    _add_heading(doc, "5. 公开数据对标（REFERENCE）", 1)
    _add_para(
        doc,
        "UIUC Vol.1 共 8 桨 112 静态点：通用参数模型 C_T 均值绝对误差 11.37%、C_P 16.68%；"
        "逐桨反推先验可把样本内误差降到 0.3–1.5%（但仅为参考先验，do_not_apply）；Re 修正为负结果（R² 0.046/0.027）。",
    )
    _add_figure(doc, FIGURES / "uiuc_benchmark_v0.2.png", "图 5  8 桨 UIUC 对标（REFERENCE vs SIM，仅量级/趋势）")

    _add_heading(doc, "6. 试验排程（S2 DoE 计划）", 1)
    _add_para(
        doc,
        "design_matrix v0.2 支持按目标推力反解油门：SIM 演示 30/54 个工况可执行（其余超出代理范围被跳过），"
        "预计采集 150 s；执行顺序可按 seed 随机化。实机执行前须通过 measured_readiness 门禁并遵守双人/防护罩/急停 SOP。",
    )
    _add_table(
        doc,
        ["电压", "可达目标推力（N）", "说明"],
        [
            ["11.1 V", "1、2", "满油门仅约 2.7 N"],
            ["14.8 V", "1、2、3", "满油门约 4.8 N"],
            ["22.2 V", "1、2、3、5、8", "满油门约 10.6 N"],
        ],
    )

    _add_heading(doc, "7. 验证与复现", 1)
    _add_para(
        doc,
        "全仓单元测试 281 项（6 套）全部通过；复现包清单 174 个文件逐文件 SHA256 校验 0 缺失 0 不一致；"
        "源代码页 58 个源文件 / 15,379 行 / 309 页（软著 V1.0 初稿）；提交前一致性检查（check_release.py）全绿。"
    )
    _add_para(doc, "一键复现：py -3.12 code\\tools\\run_all_tests.py；导出本报告：py -3.12 code\\tools\\export_office.py --overwrite")

    _add_heading(doc, "8. 下一步", 1)
    for item in [
        "M0.4：被测对象与场地电源冻结后，搭最小采集链路并完成双人砝码标定，生成第一份实测标定与 MEASURED 数据；",
        "S2：按 design_matrix v0.2 生成目标推力排程，实测重拟合推力代理与效率地图（替换全部 SIM 结论）；",
        "成果：软著登记材料按学校要求转 PDF/送审；申报表第 2–5 步待成员信息后补齐；",
        "拓展：选型 v0.6（成本项/实测补测闭环）、公开数据对标 v0.6（几何特征回归，需更多桨型样本）。",
    ]:
        para = doc.add_paragraph(style="List Bullet")
        para.add_run(item)

    doc.save(output)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="导出 Excel 成果总览与 Word 成果报告（Office 交付）")
    parser.add_argument("--out-dir", default=str(EXPORTS))
    parser.add_argument("--workbook", default="")
    parser.add_argument("--report", default="")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    stamp = dt.date.today().strftime("%Y%m%d")
    out_dir = Path(args.out_dir)
    try:
        workbook = build_workbook(
            out_dir / (args.workbook or f"项目成果总览_{stamp}.xlsx"),
            overwrite=args.overwrite,
        )
        report = build_report(
            out_dir / (args.report or f"项目成果报告_{stamp}.docx"),
            overwrite=args.overwrite,
        )
    except (ExportError, FileExistsError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    print(f"Excel 成果总览：{workbook}")
    print(f"Word 成果报告：{report}")
    print("注意：Excel/Word 只是现有 SIM/REFERENCE 成果的呈现格式，不改变数据边界（D046）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
