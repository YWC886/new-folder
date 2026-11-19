# -*- coding: utf-8 -*-
r"""多旋翼台架最小采集链路：模拟数据或串口数据写入只增不改的原始 CSV。

用法：
    python code\acquisition\acquire.py --mode simulate --duration 5 --sample-rate 1000
    python code\acquisition\acquire.py --mode serial --port COM5 --duration 10

输入：模拟模式无需硬件；串口模式接收 UTF-8 CSV 行，协议见同目录 README.md。
输出：data/raw/<run_id>.csv 与同名 .meta.json；已有文件绝不覆盖。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYLIBS = PROJECT_ROOT / "work" / "pylibs"

DEVICE_FIELDS = [
    "seq",
    "device_time_ms",
    "thrust_raw",
    "torque_raw",
    "rpm",
    "voltage_v",
    "current_a",
    "motor_temp_c",
    "ambient_temp_c",
    "humidity_pct",
    "pressure_kpa",
]
RAW_FIELDS = ["host_ts", "elapsed_s", *DEVICE_FIELDS]
REQUIRED_DEVICE_FIELDS = {"seq", "device_time_ms", "thrust_raw"}


def parse_device_line(line: str) -> dict[str, str] | None:
    """解析一行设备数据；表头、空行和注释返回 None，坏帧抛出 ValueError。"""
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    values = next(csv.reader([text]))
    if values == DEVICE_FIELDS:
        return None
    if len(values) != len(DEVICE_FIELDS):
        raise ValueError(f"列数应为 {len(DEVICE_FIELDS)}，实际为 {len(values)}")

    row = {name: value.strip() for name, value in zip(DEVICE_FIELDS, values)}
    for name in REQUIRED_DEVICE_FIELDS:
        if not row[name]:
            raise ValueError(f"必填字段 {name} 为空")

    for name in ("seq", "device_time_ms"):
        try:
            value = int(row[name])
        except ValueError as exc:
            raise ValueError(f"{name} 必须为整数") from exc
        if value < 0:
            raise ValueError(f"{name} 不得为负数")

    for name in DEVICE_FIELDS[2:]:
        value = row[name]
        if not value:
            continue
        try:
            number = float(value)
        except ValueError as exc:
            raise ValueError(f"{name} 必须为数值或空值") from exc
        if not math.isfinite(number):
            raise ValueError(f"{name} 不得为 NaN 或无穷大")
    return row


def simulate_samples(duration: float, sample_rate: float, seed: int):
    """生成确定性的合成样本，仅用于软件联调，不代表任何真实台架性能。"""
    if duration <= 0 or sample_rate <= 0:
        raise ValueError("duration 和 sample_rate 必须大于 0")
    rng = random.Random(seed)
    count = max(1, int(round(duration * sample_rate)))
    for index in range(count):
        elapsed = index / sample_rate
        thrust = 28000.0 + 25.0 * math.sin(2 * math.pi * 0.4 * elapsed) + rng.gauss(0, 10)
        torque = 17000.0 + 15.0 * math.sin(2 * math.pi * 0.3 * elapsed) + rng.gauss(0, 8)
        rpm = 6000.0 + 3.0 * math.sin(2 * math.pi * 0.5 * elapsed) + rng.gauss(0, 2)
        voltage = 22.2 + rng.gauss(0, 0.006)
        current = 8.0 + 0.01 * math.sin(2 * math.pi * 0.2 * elapsed) + rng.gauss(0, 0.008)
        yield {
            "seq": str(index),
            "device_time_ms": str(int(round(index * 1000.0 / sample_rate))),
            "thrust_raw": f"{thrust:.3f}",
            "torque_raw": f"{torque:.3f}",
            "rpm": f"{rpm:.3f}",
            "voltage_v": f"{voltage:.5f}",
            "current_a": f"{current:.5f}",
            "motor_temp_c": f"{35.0 + 0.02 * elapsed:.3f}",
            "ambient_temp_c": "24.000",
            "humidity_pct": "45.000",
            "pressure_kpa": "96.000",
        }


def safe_run_id(value: str) -> str:
    run_id = re.sub(r"[^0-9A-Za-z_.-]+", "_", value.strip()).strip("._-")
    if not run_id or run_id in {".", ".."}:
        raise ValueError("run_id 必须至少包含一个字母、数字、点、下划线或连字符")
    return run_id


def acquire(
    mode: str,
    output_dir: str | Path,
    run_id: str | None = None,
    duration: float = 5.0,
    sample_rate: float = 1000.0,
    seed: int = 20261117,
    port: str | None = None,
    baud: int = 115200,
    operator: str = "未填写",
    combo: str = "未填写",
    motor: str = "未填写",
    esc: str = "未填写",
    prop: str = "未填写",
    voltage_set: float | None = None,
    throttle_set: float | None = None,
    repeat: str = "R1",
    prop_diameter_m: float | None = None,
    notes: str = "",
) -> tuple[Path, Path, int]:
    """执行一次采集并返回 CSV 路径、元数据路径和样本数。"""
    if mode not in {"simulate", "serial"}:
        raise ValueError("mode 必须为 simulate 或 serial")
    if duration <= 0:
        raise ValueError("duration 必须大于 0")
    if mode == "serial" and not port:
        raise ValueError("串口模式必须指定 --port")
    if prop_diameter_m is not None and prop_diameter_m <= 0:
        raise ValueError("prop_diameter_m 必须大于 0")

    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + mode.upper()
    run_id = safe_run_id(run_id)
    csv_path = destination / f"{run_id}.csv"
    metadata_path = destination / f"{run_id}.meta.json"
    if csv_path.exists() or metadata_path.exists():
        raise FileExistsError(f"原始数据或元数据已存在，拒绝覆盖：{csv_path}")

    started_at = datetime.now().astimezone()
    started_monotonic = time.monotonic()
    rows_written = 0
    status = "completed"
    error_message = None

    try:
        with csv_path.open("x", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=RAW_FIELDS)
            writer.writeheader()

            if mode == "simulate":
                samples = simulate_samples(duration, sample_rate, seed)
                for sample in samples:
                    device_ms = int(sample["device_time_ms"])
                    row = {
                        "host_ts": (started_at + timedelta(milliseconds=device_ms)).isoformat(timespec="milliseconds"),
                        "elapsed_s": f"{device_ms / 1000.0:.6f}",
                        **sample,
                    }
                    writer.writerow(row)
                    rows_written += 1
            else:
                if PYLIBS.is_dir():
                    sys.path.insert(0, str(PYLIBS))
                try:
                    import serial  # type: ignore
                except ImportError as exc:
                    raise RuntimeError("缺少 pyserial，请按软件环境与使用说明安装") from exc

                with serial.Serial(port=port, baudrate=baud, timeout=0.2) as device:
                    deadline = started_monotonic + duration
                    while time.monotonic() < deadline:
                        raw_line = device.readline()
                        if not raw_line:
                            continue
                        line = raw_line.decode("utf-8", errors="strict")
                        sample = parse_device_line(line)
                        if sample is None:
                            continue
                        now_monotonic = time.monotonic()
                        row = {
                            "host_ts": datetime.now().astimezone().isoformat(timespec="milliseconds"),
                            "elapsed_s": f"{now_monotonic - started_monotonic:.6f}",
                            **sample,
                        }
                        writer.writerow(row)
                        rows_written += 1

            handle.flush()
            os.fsync(handle.fileno())

        if rows_written == 0:
            raise RuntimeError("采集结束时未收到有效样本；原始 CSV 已保留用于排查")
    except Exception as exc:
        status = "interrupted"
        error_message = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        finished_at = datetime.now().astimezone()
        metadata = {
            "schema_version": "0.1",
            "run_id": run_id,
            "status": status,
            "mode": mode,
            "simulated": mode == "simulate",
            "data_notice": "合成数据，仅用于软件联调，不是实验结果" if mode == "simulate" else "实机串口采集",
            "started_at": started_at.isoformat(timespec="milliseconds"),
            "finished_at": finished_at.isoformat(timespec="milliseconds"),
            "wall_duration_s": round(time.monotonic() - started_monotonic, 6),
            "rows_written": rows_written,
            "csv_file": csv_path.name,
            "serial": None if mode == "simulate" else {"port": port, "baud": baud, "settings": "8N1"},
            "simulation": None if mode == "serial" else {"seed": seed, "sample_rate_sps": sample_rate},
            "test": {
                "operator": operator,
                "combo": combo,
                "motor": motor,
                "esc": esc,
                "prop": prop,
                "voltage_set_v": voltage_set,
                "throttle_set_pct": throttle_set,
                "repeat": repeat,
                "prop_diameter_m": prop_diameter_m,
                "notes": notes,
            },
            "error": error_message,
        }
        with metadata_path.open("x", encoding="utf-8") as handle:
            json.dump(metadata, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

    return csv_path, metadata_path, rows_written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="模拟/串口采集到原始 CSV；已有文件不覆盖")
    parser.add_argument("--mode", choices=["simulate", "serial"], default="simulate")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "data" / "raw"))
    parser.add_argument("--run-id", help="建议：日期_组合_电压_油门_重复，例如 20261127_M1P1_22V2_50pct_R1")
    parser.add_argument("--duration", type=float, default=5.0, help="采集时长，秒")
    parser.add_argument("--sample-rate", type=float, default=1000.0, help="仅模拟模式：样本率，S/s")
    parser.add_argument("--seed", type=int, default=20261117, help="仅模拟模式：随机种子")
    parser.add_argument("--port", help="实机串口，例如 COM5 或 /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--operator", default="未填写", help="至少两名在场人员")
    parser.add_argument("--combo", default="未填写")
    parser.add_argument("--motor", default="未填写")
    parser.add_argument("--esc", default="未填写")
    parser.add_argument("--prop", default="未填写")
    parser.add_argument("--voltage-set", type=float)
    parser.add_argument("--throttle-set", type=float)
    parser.add_argument("--repeat", default="R1")
    parser.add_argument("--prop-diameter-m", type=float)
    parser.add_argument("--notes", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        csv_path, metadata_path, rows = acquire(**vars(args))
    except Exception as exc:
        print(f"采集失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"采集完成：{rows} 行")
    print(f"原始 CSV：{csv_path}")
    print(f"元数据：{metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
