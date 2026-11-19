# -*- coding: utf-8 -*-
r"""只读校验台架原始 CSV：结构、序号、时间、样本率、缺失值和稳态波动。

用法：
    python code\acquisition\validate.py --input data\raw\<run_id>.csv --window 3
    python code\acquisition\validate.py --input <csv> --min-sample-rate 990 --output <json>

输出：终端摘要，另可选写 JSON 报告；不会修改原始 CSV。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from datetime import datetime
from pathlib import Path

from acquire import DEVICE_FIELDS, RAW_FIELDS, REQUIRED_DEVICE_FIELDS


def _limited_append(items: list[str], message: str, limit: int = 50) -> None:
    if len(items) < limit:
        items.append(message)


def _number_stats(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "mean": statistics.fmean(values) if values else None,
        "std": statistics.stdev(values) if len(values) >= 2 else 0.0 if values else None,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
    }


def validate_file(
    input_path: str | Path,
    window_s: float = 3.0,
    min_sample_rate: float | None = None,
) -> dict:
    """返回结构化质量报告；调用方可据 status/errors 判断是否通过。"""
    if window_s <= 0:
        raise ValueError("window_s 必须大于 0")
    path = Path(input_path).resolve()
    report = {
        "schema_version": "0.1",
        "source_file": str(path),
        "simulated": None,
        "status": "fail",
        "rows": 0,
        "duration_s": None,
        "estimated_sample_rate_sps": None,
        "errors": [],
        "warnings": [],
        "statistics": {},
        "steady_window": {},
    }
    errors: list[str] = report["errors"]
    warnings: list[str] = report["warnings"]

    metadata_path = path.with_suffix(".meta.json")
    if metadata_path.exists():
        try:
            with metadata_path.open(encoding="utf-8") as handle:
                report["simulated"] = json.load(handle).get("simulated")
        except (OSError, json.JSONDecodeError) as exc:
            _limited_append(warnings, f"元数据读取失败：{exc}")
    else:
        _limited_append(warnings, "缺少同名 .meta.json，无法确认采集模式与试验条件")

    try:
        handle = path.open(newline="", encoding="utf-8-sig")
    except OSError as exc:
        _limited_append(errors, f"文件读取失败：{exc}")
        return report

    with handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != RAW_FIELDS:
            _limited_append(errors, f"表头不符合 schema v0.1：{reader.fieldnames}")
            return report
        rows = list(reader)

    report["rows"] = len(rows)
    if not rows:
        _limited_append(errors, "CSV 没有数据行")
        return report

    records = []
    sequences = []
    device_times = []
    elapsed_values = []
    channel_values = {name: [] for name in DEVICE_FIELDS[2:]}

    for row_index, row in enumerate(rows, start=2):
        try:
            datetime.fromisoformat(row["host_ts"])
        except (TypeError, ValueError):
            _limited_append(errors, f"第 {row_index} 行 host_ts 不是 ISO8601 时间")

        values = {}
        device_time = None
        for name in DEVICE_FIELDS:
            text = (row.get(name) or "").strip()
            if not text:
                if name in REQUIRED_DEVICE_FIELDS:
                    _limited_append(errors, f"第 {row_index} 行必填字段 {name} 为空")
                continue
            try:
                value = float(text)
                if not math.isfinite(value):
                    raise ValueError
            except ValueError:
                _limited_append(errors, f"第 {row_index} 行 {name} 不是有限数值")
                continue

            if name in {"seq", "device_time_ms"} and not value.is_integer():
                _limited_append(errors, f"第 {row_index} 行 {name} 必须为整数")
                continue
            if name in {"seq", "device_time_ms"} and value < 0:
                _limited_append(errors, f"第 {row_index} 行 {name} 不得为负数")
                continue

            values[name] = value
            if name == "seq":
                sequences.append(int(value))
            elif name == "device_time_ms":
                device_time = int(value)
                device_times.append(device_time)
            else:
                channel_values[name].append(value)

        elapsed_text = (row.get("elapsed_s") or "").strip()
        try:
            elapsed = float(elapsed_text)
            if not math.isfinite(elapsed) or elapsed < 0:
                raise ValueError
            elapsed_values.append(elapsed)
        except ValueError:
            _limited_append(errors, f"第 {row_index} 行 elapsed_s 无效")
        records.append((device_time, values))

    if len(sequences) != len(set(sequences)):
        _limited_append(errors, "序号存在重复")
    if any(later <= earlier for earlier, later in zip(sequences, sequences[1:])):
        _limited_append(errors, "序号非严格递增（可能乱序或重复）")
    if sequences:
        missing = sorted(set(range(min(sequences), max(sequences) + 1)) - set(sequences))
        if missing:
            _limited_append(errors, f"序号缺号（前 10 个）：{missing[:10]}")
    if any(later < earlier for earlier, later in zip(device_times, device_times[1:])):
        _limited_append(errors, "设备时间非单调递增")

    if len(device_times) >= 2:
        time_span_s = (device_times[-1] - device_times[0]) / 1000.0
        report["duration_s"] = max(elapsed_values) if elapsed_values else time_span_s
        if time_span_s > 0:
            estimated_rate = (len(device_times) - 1) / time_span_s
            report["estimated_sample_rate_sps"] = estimated_rate
            if min_sample_rate is not None and estimated_rate < min_sample_rate:
                _limited_append(errors, f"估计样本率 {estimated_rate:.3f} S/s 低于要求 {min_sample_rate:.3f} S/s")
    elif elapsed_values:
        report["duration_s"] = max(elapsed_values)

    for name, values in channel_values.items():
        stats = _number_stats(values)
        stats["missing"] = len(rows) - len(values)
        report["statistics"][name] = stats
        if not values:
            _limited_append(warnings, f"通道 {name} 全部缺失")

    cutoff = device_times[-1] - window_s * 1000.0 if device_times else None
    for name in ("thrust_raw", "rpm"):
        values = [
            record_values[name]
            for device_time, record_values in records
            if device_time is not None and cutoff is not None and device_time >= cutoff and name in record_values
        ]
        stats = _number_stats(values)
        report["steady_window"][name] = stats
        if len(values) >= 2 and stats["mean"] is not None and abs(stats["mean"]) > 1e-12:
            relative_std = abs(stats["std"] / stats["mean"])
            report["steady_window"][name]["relative_std"] = relative_std
            if relative_std > 0.01:
                _limited_append(warnings, f"稳态窗口内 {name} 相对标准差 {relative_std:.3%} 超过 1%")

    report["status"] = "fail" if errors else "pass_with_warnings" if warnings else "pass"
    report["checked_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="只读校验原始 CSV 并输出 JSON 质量报告")
    parser.add_argument("--input", required=True, help="原始 CSV 路径")
    parser.add_argument("--window", type=float, default=3.0, help="末尾稳态窗口长度，秒")
    parser.add_argument("--min-sample-rate", type=float, help="最低样本率，S/s；不指定则不设下限")
    parser.add_argument("--output", help="JSON 报告路径；已有文件不覆盖")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = validate_file(args.input, args.window, args.min_sample_rate)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", encoding="utf-8") as handle:
            handle.write(text)
        print(f"校验报告：{output_path}")
    else:
        print(text, end="")
    print(f"校验结论：{report['status']}；错误 {len(report['errors'])} 项，警告 {len(report['warnings'])} 项")
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
