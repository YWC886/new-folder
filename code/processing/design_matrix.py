"""多工况试验方案生成器（v0.1，S2 阶段 DoE 计划）。

把"电压×油门×桨型×重复"展开成可直接执行的采集排程，输出 run_id 与参数表，
供 `code/acquisition/acquire.py` 的 `--combo/--voltage-set/--throttle-set/--repeat`
直接使用；本模块只生成计划，不产生任何测量数据。

设计类型（`--design`）：
- `full`：全因子，每电压块内按 重复→桨型→油门升序 排列（便于换桨与热平衡）；
- `sweep`：阶梯扫描，每电压块内 油门升→降 为一个 pass，重复 pass 次
  （便于观察温漂与迟滞；direction 列标记 up/down）。

数据边界：输出为试验计划，不是测量数据；实机采集须先通过 `measured_readiness`
门禁，并按 D032 双人标定流程执行。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SCHEMA_VERSION = "0.1"
FIELDS = (
    "order",
    "block",
    "run_id",
    "combo",
    "prop_id",
    "voltage_set_v",
    "throttle_set_pct",
    "direction",
    "repeat",
    "duration_s",
    "steady_window_s",
    "notes",
)
DATA_NOTE = (
    "试验计划（SIM 之外的实机排程）：仅生成采集参数与顺序，不是测量数据；"
    "实机采集须通过 measured_readiness 门禁并按 D032 双人标定（D043）"
)
DESIGNS = ("full", "sweep")


class DesignError(ValueError):
    """参数或配置错误。"""


@dataclass(frozen=True)
class DesignConfig:
    voltages: tuple[float, ...]
    throttles: tuple[float, ...]
    props: tuple[str, ...]
    repeats: int = 3
    duration_s: float = 5.0
    steady_window_s: float = 1.5
    design: str = "full"
    combo: str = "PROP-SET"
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.voltages or any(v <= 0 for v in self.voltages):
            raise DesignError("voltages 必须为非空正数序列")
        if not self.throttles or any(not (0 < t <= 100) for t in self.throttles):
            raise DesignError("throttles 必须在 (0, 100] 百分数范围内")
        if not self.props:
            raise DesignError("props 不能为空")
        if self.repeats < 1:
            raise DesignError("repeats 必须 >= 1")
        if self.duration_s <= 0 or self.steady_window_s <= 0:
            raise DesignError("duration_s 与 steady_window_s 必须为正")
        if self.steady_window_s > self.duration_s:
            raise DesignError("steady_window_s 不能大于 duration_s")
        if self.design not in DESIGNS:
            raise DesignError(f"design 必须是 {DESIGNS} 之一")


def _row(
    *,
    order: int,
    block: int,
    combo: str,
    prop_id: str,
    voltage: float,
    throttle: float,
    direction: str,
    repeat: int,
    duration_s: float,
    steady_window_s: float,
    notes: str,
) -> dict:
    return {
        "order": order,
        "block": block,
        "run_id": f"{combo}_{prop_id}_{voltage:g}V_{throttle:g}pct_R{repeat}",
        "combo": combo,
        "prop_id": prop_id,
        "voltage_set_v": round(float(voltage), 4),
        "throttle_set_pct": round(float(throttle), 4),
        "direction": direction,
        "repeat": repeat,
        "duration_s": float(duration_s),
        "steady_window_s": float(steady_window_s),
        "notes": notes,
    }


def build_full(cfg: DesignConfig) -> list[dict]:
    """全因子：电压块 → 重复 → 桨型 → 油门升序。"""
    rows: list[dict] = []
    order = 0
    for block, voltage in enumerate(cfg.voltages, start=1):
        for repeat in range(1, cfg.repeats + 1):
            for prop in cfg.props:
                for throttle in sorted(cfg.throttles):
                    order += 1
                    rows.append(
                        _row(
                            order=order,
                            block=block,
                            combo=cfg.combo,
                            prop_id=prop,
                            voltage=voltage,
                            throttle=throttle,
                            direction="hold",
                            repeat=repeat,
                            duration_s=cfg.duration_s,
                            steady_window_s=cfg.steady_window_s,
                            notes=cfg.notes,
                        )
                    )
    return rows


def build_sweep(cfg: DesignConfig) -> list[dict]:
    """阶梯扫描：电压块 → pass → 油门升 + 降。"""
    rows: list[dict] = []
    order = 0
    levels = sorted(cfg.throttles)
    for block, voltage in enumerate(cfg.voltages, start=1):
        for repeat in range(1, cfg.repeats + 1):
            for prop in cfg.props:
                for direction, seq in (("up", levels), ("down", list(reversed(levels)))):
                    for throttle in seq:
                        order += 1
                        rows.append(
                            _row(
                                order=order,
                                block=block,
                                combo=cfg.combo,
                                prop_id=prop,
                                voltage=voltage,
                                throttle=throttle,
                                direction=direction,
                                repeat=repeat,
                                duration_s=cfg.duration_s,
                                steady_window_s=cfg.steady_window_s,
                                notes=cfg.notes,
                            )
                        )
    return rows


def build_matrix(cfg: DesignConfig) -> list[dict]:
    """按 design 生成试验矩阵。"""
    if cfg.design == "full":
        rows = build_full(cfg)
    elif cfg.design == "sweep":
        rows = build_sweep(cfg)
    else:  # pragma: no cover - DesignConfig 已校验
        raise DesignError(f"未知 design：{cfg.design}")
    _check_unique(rows)
    return rows


def _check_unique(rows: list[dict]) -> None:
    seen: set[tuple] = set()
    for row in rows:
        key = (row["combo"], row["prop_id"], row["voltage_set_v"], row["throttle_set_pct"], row["repeat"], row["direction"])
        if key in seen:
            raise DesignError(f"试验矩阵出现重复组合：{key}")
        seen.add(key)


def summarize(rows: list[dict], cfg: DesignConfig) -> dict:
    n_runs = len(rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "data_note": DATA_NOTE,
        "design": cfg.design,
        "voltage_points": len(cfg.voltages),
        "throttle_points": len(cfg.throttles),
        "props": list(cfg.props),
        "repeats": cfg.repeats,
        "n_runs": n_runs,
        "planned_duration_s": round(n_runs * cfg.duration_s, 3),
        "duration_s": cfg.duration_s,
        "steady_window_s": cfg.steady_window_s,
        "blocks": len(cfg.voltages),
        "combo": cfg.combo,
    }


def write_csv(rows: list[dict], output: Path, *, overwrite: bool = False) -> Path:
    if not rows:
        raise DesignError("试验矩阵为空")
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output}（使用 --overwrite 覆盖）")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output


def write_summary(summary: dict, output: Path, *, overwrite: bool = False) -> Path:
    if output.exists() and not overwrite:
        raise FileExistsError(f"汇总文件已存在：{output}（使用 --overwrite 覆盖）")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def _parse_floats(text: str) -> tuple[float, ...]:
    try:
        values = tuple(float(part) for part in text.split(",") if part.strip())
    except ValueError as exc:
        raise DesignError(f"无法解析数值列表：{text}") from exc
    if not values:
        raise DesignError("数值列表为空")
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成多工况试验方案（S2 DoE 计划）")
    parser.add_argument("--voltages", default="11.1,14.8,22.2", help="母线电压点（逗号分隔，V）")
    parser.add_argument("--throttles", default="20,40,60,80,100", help="油门点（逗号分隔，%%）")
    parser.add_argument("--props", default="P1", help="桨型标识（逗号分隔）")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--design", choices=DESIGNS, default="full")
    parser.add_argument("--combo", default="PROP-SET")
    parser.add_argument("--duration", type=float, default=5.0, dest="duration_s")
    parser.add_argument("--steady-window", type=float, default=1.5, dest="steady_window_s")
    parser.add_argument("--seed", type=int, default=20261121, help="预留：v0.2 LHS 随机化种子")
    parser.add_argument("--notes", default="")
    parser.add_argument("--output", default="data/processed/design_matrix_v0.1.csv")
    parser.add_argument("--summary", default="data/metadata/design_matrix_v0.1.summary.json")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        cfg = DesignConfig(
            voltages=_parse_floats(args.voltages),
            throttles=_parse_floats(args.throttles),
            props=tuple(p.strip() for p in args.props.split(",") if p.strip()),
            repeats=args.repeats,
            duration_s=args.duration_s,
            steady_window_s=args.steady_window_s,
            design=args.design,
            combo=args.combo,
            notes=args.notes,
        )
        rows = build_matrix(cfg)
        out_csv = write_csv(rows, Path(args.output), overwrite=args.overwrite)
        summary = summarize(rows, cfg)
        out_summary = write_summary(summary, Path(args.summary), overwrite=args.overwrite)
    except (DesignError, FileExistsError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    print(f"试验计划：{cfg.design}，{summary['n_runs']} 次运行，预计 {summary['planned_duration_s']:.0f} s 采集时长")
    print(f"矩阵：{out_csv}")
    print(f"汇总：{out_summary}")
    print("注意：这是试验计划，不是测量数据；实机执行前须通过 measured_readiness 门禁（D043）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
