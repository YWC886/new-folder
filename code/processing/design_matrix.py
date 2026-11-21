"""多工况试验方案生成器（v0.2，S2 阶段 DoE 计划）。

把"电压×油门×桨型×重复"展开成可直接执行的采集排程，输出 run_id 与参数表，
供 `code/acquisition/acquire.py` 的 `--combo/--voltage-set/--throttle-set/--repeat`
直接使用；本模块只生成计划，不产生任何测量数据。

设计类型（`--design`）：
- `full`：全因子，每电压块内按 重复→桨型→油门升序 排列（便于换桨与热平衡）；
- `sweep`：阶梯扫描，每电压块内 油门升→降 为一个 pass，重复 pass 次
  （便于观察温漂与迟滞；direction 列标记 up/down）。

v0.2 新增：
- `--thrust-levels`：以「目标推力水平」代替油门，基于已有 runs CSV 的 GP 推力代理
  反解每个（电压, 目标推力）对应的油门（仅对 `--map-prop` 指定的桨型有效，
  其余桨型须各自标定后重复本步骤）；
- `--randomize`：按 `--seed` 在电压块内随机化执行顺序（不改变重复/桨型归属）。

数据边界：输出为试验计划，不是测量数据；实机采集须先通过 `measured_readiness`
门禁，并按 D032 双人标定流程执行。GP 推力反解属计划用途，不构成测量（D045）。
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from gp_surface import GPFit, THROTTLE_SCALE, VOLTAGE_SCALE, choose_length_scale, features_of

SCHEMA_VERSION = "0.2"
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
THRUST_LEVELS_NOTE = "thrust_levels 必须为非空正数序列"
THRUST_FIELDS = FIELDS + ("planned_thrust_n",)


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


def load_thrust_runs(path: Path) -> list[dict]:
    """读取已有 runs CSV（效率地图 runs 表）作为 GP 推力代理的训练数据。"""
    if not path.exists():
        raise DesignError(f"推力代理数据不存在：{path}")
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or ()
        missing = [c for c in ("voltage_set_v", "throttle_set_pct") if c not in fields]
        if missing:
            raise DesignError(f"推力代理数据缺少列：{missing}")
        thrust_field = "thrust_N_mean" if "thrust_N_mean" in fields else ("thrust_N" if "thrust_N" in fields else None)
        if thrust_field is None:
            raise DesignError("推力代理数据缺少推力列（thrust_N_mean / thrust_N）")
        runs: list[dict] = []
        for raw in reader:
            try:
                voltage = float(raw["voltage_set_v"])
                throttle = float(raw["throttle_set_pct"])
                thrust = float(raw[thrust_field])
            except (TypeError, ValueError) as exc:
                raise DesignError(f"推力代理数据含非数值行：{raw}") from exc
            if not (voltage > 0 and 0.0 <= throttle <= 100.0 and thrust >= 0.0):
                raise DesignError(f"推力代理数据含范围非法行：{raw}")
            runs.append({"voltage_set_v": voltage, "throttle_set_pct": throttle, "thrust_n": thrust})
    if len(runs) < 4:
        raise DesignError(f"推力代理至少需要 4 个数据点（当前 {len(runs)}）")
    return runs


def fit_thrust_map(runs: list[dict]) -> dict:
    """在（电压, 油门）上拟合 GP 推力代理，核宽按 LOOCV 选择。"""
    x = features_of(runs)
    y = np.asarray([float(r["thrust_n"]) for r in runs], dtype=float)
    fit = choose_length_scale(x, y)
    gp = GPFit(x=x, y=y, length_scale=fit["length_scale"])
    return {
        "gp": gp,
        "length_scale": fit["length_scale"],
        "loocv_rmse": fit["loocv_rmse"],
        "r2": fit["r2"],
        "n": len(runs),
    }


def _predict_thrust(model: dict, voltage: float, throttle: float) -> float:
    x = np.asarray([[voltage / VOLTAGE_SCALE, throttle / THROTTLE_SCALE]], dtype=float)
    mean, _ = model["gp"].predict(x)
    return float(mean[0])


def invert_throttle(
    model: dict,
    voltage: float,
    target_thrust_n: float,
    *,
    max_throttle: float = 100.0,
    tol_n: float = 0.02,
    max_iter: int = 80,
) -> tuple[float, float]:
    """二分反解油门：返回 (throttle_pct, 代理预测推力 N)。"""
    if target_thrust_n <= 0:
        raise DesignError("目标推力必须为正")
    low, high = 0.0, float(max_throttle)
    f_high = _predict_thrust(model, voltage, high)
    if target_thrust_n > f_high + tol_n:
        raise DesignError(f"目标推力 {target_thrust_n:g} N 超出 {voltage:g} V 的代理上限 {f_high:.3f} N")
    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        if _predict_thrust(model, voltage, mid) < target_thrust_n:
            low = mid
        else:
            high = mid
        if high - low < 1e-4:
            break
    throttle = 0.5 * (low + high)
    return throttle, _predict_thrust(model, voltage, throttle)


def build_thrust_matrix(
    cfg: DesignConfig,
    thrust_levels: tuple[float, ...],
    model: dict,
    map_prop: str,
) -> tuple[list[dict], list[dict]]:
    """按目标推力生成排程（仅对 map_prop 有效）；返回 (rows, skipped)。"""
    if not thrust_levels or any(level <= 0 for level in thrust_levels):
        raise DesignError(THRUST_LEVELS_NOTE)
    if map_prop not in cfg.props:
        raise DesignError(f"map-prop「{map_prop}」不在 props 中：{list(cfg.props)}")
    rows: list[dict] = []
    skipped: list[dict] = []
    order = 0
    for block, voltage in enumerate(cfg.voltages, start=1):
        for repeat in range(1, cfg.repeats + 1):
            for level in sorted(thrust_levels):
                try:
                    throttle, thrust_pred = invert_throttle(model, voltage, float(level))
                except DesignError as exc:
                    skipped.append({"voltage_set_v": round(float(voltage), 4), "planned_thrust_n": float(level), "reason": str(exc)})
                    continue
                order += 1
                row = _row(
                    order=order,
                    block=block,
                    combo=cfg.combo,
                    prop_id=map_prop,
                    voltage=voltage,
                    throttle=round(throttle, 3),
                    direction="hold",
                    repeat=repeat,
                    duration_s=cfg.duration_s,
                    steady_window_s=cfg.steady_window_s,
                    notes=f"target={float(level):g}N pred={thrust_pred:.3f}N",
                )
                row["planned_thrust_n"] = round(float(level), 4)
                rows.append(row)
    if not rows:
        raise DesignError("没有可执行的工况（目标推力均超出代理范围）")
    _check_unique(rows)
    return rows, skipped


def randomize_rows(rows: list[dict], seed: int) -> list[dict]:
    """按电压块内随机化执行顺序，并重排序号（保证可复现）。"""
    if not rows:
        return []
    rng = random.Random(seed)
    blocks: dict[int, list[dict]] = {}
    for row in rows:
        blocks.setdefault(int(row["block"]), []).append(row)
    out: list[dict] = []
    for block in sorted(blocks):
        group = list(blocks[block])
        rng.shuffle(group)
        out.extend(group)
    for index, row in enumerate(out, start=1):
        row["order"] = index
    return out


def summarize(rows: list[dict], cfg: DesignConfig, *, extra: dict | None = None) -> dict:
    n_runs = len(rows)
    summary = {
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
    if extra:
        summary.update(extra)
    return summary


def write_csv(
    rows: list[dict],
    output: Path,
    *,
    overwrite: bool = False,
    fields: tuple[str, ...] = FIELDS,
) -> Path:
    if not rows:
        raise DesignError("试验矩阵为空")
    if output.exists() and not overwrite:
        raise FileExistsError(f"输出文件已存在：{output}（使用 --overwrite 覆盖）")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
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
    parser.add_argument("--seed", type=int, default=20261121, help="随机化种子（--randomize）")
    parser.add_argument("--randomize", action="store_true", help="按 --seed 在电压块内随机化执行顺序")
    parser.add_argument("--thrust-levels", default="", help="目标推力水平（N，逗号分隔）；提供后按 GP 推力代理反解油门")
    parser.add_argument("--thrust-map", default="data/processed/efficiency_map_runs.csv", dest="thrust_map")
    parser.add_argument("--map-prop", default="SIM10x4.5", dest="map_prop", help="推力代理对应的桨型标识")
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
        try:
            thrust_levels = tuple(float(part) for part in args.thrust_levels.split(",") if part.strip())
        except ValueError as exc:
            raise DesignError(f"无法解析 --thrust-levels：{args.thrust_levels}") from exc
        skipped: list[dict] = []
        stage: dict = {"mode": "throttle", "randomized": bool(args.randomize)}
        if thrust_levels:
            model = fit_thrust_map(load_thrust_runs(Path(args.thrust_map)))
            rows, skipped = build_thrust_matrix(cfg, thrust_levels, model, args.map_prop)
            fields = THRUST_FIELDS
            stage.update(
                {
                    "mode": "thrust",
                    "design": "full-thrust",
                    "throttle_points": None,
                    "thrust_levels": list(thrust_levels),
                    "thrust_map": str(args.thrust_map),
                    "map_prop": args.map_prop,
                    "thrust_map_fit": {
                        "n": model["n"],
                        "length_scale": model["length_scale"],
                        "loocv_rmse": model["loocv_rmse"],
                        "r2": model["r2"],
                    },
                }
            )
        else:
            rows = build_matrix(cfg)
            fields = FIELDS
        if args.randomize:
            rows = randomize_rows(rows, args.seed)
            stage["seed"] = args.seed
        out_csv = write_csv(rows, Path(args.output), overwrite=args.overwrite, fields=fields)
        if skipped:
            stage["skipped"] = skipped
        summary = summarize(rows, cfg, extra=stage)
        out_summary = write_summary(summary, Path(args.summary), overwrite=args.overwrite)
    except (DesignError, FileExistsError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    print(f"试验计划：{summary.get('design')}，{summary['n_runs']} 次运行，预计 {summary['planned_duration_s']:.0f} s 采集时长")
    if skipped:
        print(f"跳过工况：{len(skipped)} 个（目标推力超出对应电压的代理范围）")
    print(f"矩阵：{out_csv}")
    print(f"汇总：{out_summary}")
    print("注意：这是试验计划，不是测量数据；实机执行前须通过 measured_readiness 门禁（D043/D045）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
