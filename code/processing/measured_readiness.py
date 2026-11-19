"""MEASURED 通路就绪检查（v0.1，M0.4 门禁）。

目的：在 M0.4 硬件链路与双人砝码标定完成前，先把"什么样的输入才算实测"
固化成可执行的检查器。只有同时满足以下条件的组合才允许进入 MEASURED 通路：

1. 原始 CSV 的 meta（`<run_id>.meta.json`）标记 `simulated: false`、`mode: "serial"`、
   `status: "ok"`、`rows_written > 0`；
2. 标定 JSON 标记 `simulated: false`，`thrust/torque` 的 `k ≠ 0`、`b` 有限；
3. 原始 CSV 表头与 `compute_efficiency.RAW_FIELDS` 一致，必需通道
   （thrust_raw / torque_raw / rpm / voltage_v / current_a）有有限数值；
4. 桨径可用（标定 `propeller.diameter_m` 或 meta `test.prop_diameter_m`）。

边界（D035）：
- 本检查器只验证**标记与结构**，无法验证数据是否真的来自传感器；物理真实性仍须
  双人签字（`docs/test/静态砝码读数记录_v0.1.md`）与现场记录。
- 检查器**不得**为通过检查而修改 meta/标定；发现 SIM 输入应拒绝并保留原样。
- 它是 M0.4 的"入场券"，不是标定质量评估（后者见 `calibration_fit` 的 R²/重复性/迟滞）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
for _p in (HERE,):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import compute_efficiency as ce  # noqa: E402

SCHEMA_VERSION = "0.1"
REQUIRED_CHANNELS = ce.REQUIRED_CHANNELS
READINESS_EXIT = {"ready": 0, "not_ready": 1, "usage": 2}


def _as_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def check_calibration(calibration: dict) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(calibration, dict):
        return ["标定 JSON 顶层必须是对象"], warnings, {}
    simulated = calibration.get("simulated")
    if simulated is not False:
        errors.append(
            f"标定 JSON 必须显式标记 simulated:false（当前 {simulated!r}）；"
            "SIM/合成标定不能进入 MEASURED 通路（D035）"
        )
    for channel in ("thrust", "torque"):
        block = calibration.get(channel)
        if not isinstance(block, dict):
            errors.append(f"标定缺少 {channel} 通道")
            continue
        k = _as_float(block.get("k"))
        b = _as_float(block.get("b"))
        if k is None or b is None:
            errors.append(f"标定 {channel}.k / {channel}.b 必须是数值")
        elif k == 0:
            errors.append(f"标定 {channel}.k 不能为 0（灵敏度为零）")
        elif not (abs(k) < 1e9 and abs(b) < 1e9):
            errors.append(f"标定 {channel}.k / b 超出合理量级")
    diameter = None
    prop = calibration.get("propeller")
    if isinstance(prop, dict):
        diameter = _as_float(prop.get("diameter_m"))
    if diameter is None or diameter <= 0:
        warnings.append("标定未提供 propeller.diameter_m（需由 meta test.prop_diameter_m 兜底）")
    return errors, warnings, {"simulated": simulated, "diameter_from_calibration_m": diameter}


def check_meta(meta: dict) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(meta, dict):
        return ["meta JSON 顶层必须是对象"], warnings, {}
    if meta.get("simulated") is not False:
        errors.append(
            f"meta 必须显式标记 simulated:false（当前 {meta.get('simulated')!r}）；"
            "SIM 合成数据不能进入 MEASURED 通路（D035）"
        )
    mode = meta.get("mode")
    if mode != "serial":
        errors.append(f"meta.mode 必须为 'serial'（当前 {mode!r}）")
    if meta.get("status") != "ok":
        warnings.append(f"meta.status 不是 'ok'（当前 {meta.get('status')!r}）")
    rows_written = meta.get("rows_written")
    if not isinstance(rows_written, int) or rows_written <= 0:
        errors.append(f"meta.rows_written 必须为正整数（当前 {rows_written!r}）")
    diameter = None
    test = meta.get("test")
    if isinstance(test, dict):
        diameter = _as_float(test.get("prop_diameter_m"))
    return errors, warnings, {
        "run_id": meta.get("run_id"),
        "simulated": meta.get("simulated"),
        "mode": mode,
        "rows_written": rows_written,
        "diameter_from_meta_m": diameter,
        "operator": test.get("operator") if isinstance(test, dict) else None,
    }


def check_rows(rows: list[dict]) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    if not rows:
        return ["原始 CSV 没有数据行"], warnings, {"rows": 0}
    header = list(rows[0].keys())
    if header != list(ce.RAW_FIELDS):
        errors.append(f"原始 CSV 表头与协议不一致：{header}")
    for channel in REQUIRED_CHANNELS:
        values = [_as_float(row.get(channel)) for row in rows]
        numeric = [value for value in values if value is not None]
        if not numeric:
            errors.append(f"必需通道 {channel} 没有可解析数值")
    rows_count = len(rows)
    return errors, warnings, {"rows": rows_count}


def load_meta(raw_csv: Path) -> tuple[dict | None, str | None]:
    meta_path = raw_csv.with_suffix(".meta.json")
    if not meta_path.exists():
        return None, f"缺少 meta 文件：{meta_path}"
    try:
        return json.loads(meta_path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"meta 读取失败：{exc}"


def read_raw_rows(raw_csv: Path) -> tuple[list[dict] | None, str | None]:
    if not raw_csv.exists():
        return None, f"原始 CSV 不存在：{raw_csv}"
    try:
        import csv

        with raw_csv.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            rows = [row for row in reader]
    except OSError as exc:
        return None, f"原始 CSV 读取失败：{exc}"
    return rows, None


def assess(raw_csv: str | Path, calibration_path: str | Path) -> dict:
    raw_csv = Path(raw_csv)
    calibration_path = Path(calibration_path)
    errors: list[str] = []
    warnings: list[str] = []
    facts: dict = {}

    try:
        calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"标定 JSON 读取失败：{exc}")
        calibration = None
    if calibration is not None:
        cal_errors, cal_warnings, cal_facts = check_calibration(calibration)
        errors.extend(cal_errors)
        warnings.extend(cal_warnings)
        facts.update(cal_facts)

    meta, meta_error = load_meta(raw_csv)
    if meta_error:
        errors.append(meta_error)
    if meta is not None:
        meta_errors, meta_warnings, meta_facts = check_meta(meta)
        errors.extend(meta_errors)
        warnings.extend(meta_warnings)
        facts.update(meta_facts)

    rows, rows_error = read_raw_rows(raw_csv)
    if rows_error:
        errors.append(rows_error)
    if rows is not None:
        row_errors, row_warnings, row_facts = check_rows(rows)
        errors.extend(row_errors)
        warnings.extend(row_warnings)
        facts.update(row_facts)

    diameter = facts.get("diameter_from_calibration_m") or facts.get("diameter_from_meta_m")
    if not diameter:
        errors.append("桨径缺失：标定 propeller.diameter_m 与 meta test.prop_diameter_m 均不可用")
    else:
        facts["diameter_m"] = diameter

    ready = not errors
    return {
        "schema_version": SCHEMA_VERSION,
        "raw_csv": str(raw_csv),
        "calibration": str(calibration_path),
        "ready": ready,
        "errors": errors,
        "warnings": warnings,
        "facts": facts,
        "guidance": (
            "可进入 MEASURED 通路：建议依次运行 compute_efficiency（--steady auto）→ "
            "aggregate_efficiency → 图标/选型；仍须双人签字与现场记录。"
            if ready
            else "拒绝进入 MEASURED 通路：请修正上述错误；禁止通过修改 meta/标定来绕过检查（D035）。"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MEASURED 通路就绪检查 v0.1（M0.4 门禁）")
    parser.add_argument("--input", required=True, help="原始 CSV（需同名 .meta.json）")
    parser.add_argument("--calib", required=True, help="标定 JSON")
    parser.add_argument("--json", action="store_true", help="输出 JSON 报告")
    parser.add_argument("--output", default=None, help="把 JSON 报告写入文件")
    args = parser.parse_args(argv)

    try:
        report = assess(args.input, args.calib)
    except Exception as exc:  # noqa: BLE001 - CLI 兜底
        print(f"错误：{exc}")
        return READINESS_EXIT["usage"]

    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"原始 CSV：{report['raw_csv']}")
        print(f"标定：{report['calibration']}")
        print(f"结论：{'✅ READY（可进入 MEASURED 通路）' if report['ready'] else '❌ NOT READY'}")
        for item in report["errors"]:
            print(f"  [错误] {item}")
        for item in report["warnings"]:
            print(f"  [警告] {item}")
        print(f"事实：{json.dumps(report['facts'], ensure_ascii=False)}")
        print(report["guidance"])
    return READINESS_EXIT["ready"] if report["ready"] else READINESS_EXIT["not_ready"]


if __name__ == "__main__":
    raise SystemExit(main())
