"""UIUC Propeller Database 解析器（v0.2）。

支持 Volume 1 的**静态**数据文件格式（RPM CT CP 三列文本），
可选空行与 `#` 注释行。参考数据只用于对标，不属于本项目实测/合成数据。
v0.2 新增：从文件名解析桨标签与几何参数（品牌/系列/直径/螺距），见
`parse_prop_label()`。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE = (
    PROJECT_ROOT / "data" / "reference" / "uiuc" / "apce_10x7_static_pg0811.txt"
)

STATIC_COLUMNS = ("RPM", "CT", "CP")

# UIUC Vol.1 文件名前缀 → (品牌, 系列短名, 系列全称)。
# 来源：Volume 1 页面按品牌/系列分组（Aeronaut Carbon Electric、APC Electric/Slow Flyer/
# Sport、Graupner CAM Prop/Super Nylon 等），见 data/reference/README.md 的来源链接。
PROP_PREFIXES: dict[str, tuple[str, str, str]] = {
    "apce": ("APC", "E", "Electric (thin electric)"),
    "apcsf": ("APC", "SF", "Slow Flyer"),
    "apcsp": ("APC", "Sport", "Sport"),
    "grcp": ("Graupner", "CAM", "CAM Prop"),
    "grsn": ("Graupner", "SN", "Super Nylon"),
    "ance": ("Aeronaut", "CE", "Carbon Electric"),
}

# 例：apce_11x7_static_kt0534.txt / ance_8.5x6_static_2848cm.txt
_STATIC_NAME_RE = re.compile(
    r"^(?P<prefix>[a-z][a-z0-9]*)_"
    r"(?P<diameter>\d+(?:\.\d+)?)x(?P<pitch>\d+(?:\.\d+)?)"
    r"_static(?:_(?P<test_id>[a-z0-9]+))?\.txt$",
    re.IGNORECASE,
)


def parse_prop_label(path: Path | str) -> dict:
    """从 UIUC 静态数据文件名解析桨标签与几何参数。

    例：`apce_11x7_static_kt0534.txt` → APC 的 E 系列、直径 11 in、螺距 7 in。
    只解析文件名，不做数据读取；返回 dict：
    `file/prop/brand/series/series_full/brand_series/diameter_in/pitch_in/size/test_id/display`。
    不合命名规则或未知品牌前缀时抛 ValueError。
    """
    name = Path(path).name
    match = _STATIC_NAME_RE.match(name)
    if match is None:
        raise ValueError(
            f"文件名不符合 UIUC 静态数据命名：{name!r}"
            "（期望形如 apce_11x7_static_kt0534.txt）"
        )
    prefix = match["prefix"].lower()
    if prefix not in PROP_PREFIXES:
        raise ValueError(
            f"未知品牌/系列前缀：{prefix!r}"
            f"（已知：{', '.join(sorted(PROP_PREFIXES))}）"
        )
    brand, series, series_full = PROP_PREFIXES[prefix]
    diameter = float(match["diameter"])
    pitch = float(match["pitch"])
    size = f"{match['diameter']}x{match['pitch']}"
    return {
        "file": name,
        "prop": f"{prefix}_{size}",
        "brand": brand,
        "series": series,
        "series_full": series_full,
        "brand_series": f"{brand}-{series}",
        "diameter_in": diameter,
        "pitch_in": pitch,
        "size": size,
        "test_id": match["test_id"].lower() or None,
        "display": f"{brand}-{series} {size}",
    }


def load_static(path: Path | str) -> list[dict]:
    """读取静态数据文件，返回 [{rpm, ct, cp, n_rps}, ...]。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"参考数据不存在：{path}")

    header: list[str] | None = None
    rows: list[dict] = []
    with path.open("r", encoding="utf-8-sig") as fh:
        for line_no, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if header is None:
                header = [p.upper() for p in parts]
                if set(header) != set(STATIC_COLUMNS) or len(header) != 3:
                    raise ValueError(
                        f"{path}:{line_no}: 表头应为 {' '.join(STATIC_COLUMNS)}，实际为 {line!r}"
                    )
                indices = {name: header.index(name) for name in STATIC_COLUMNS}
                continue
            try:
                rpm = float(parts[indices["RPM"]])
                ct = float(parts[indices["CT"]])
                cp = float(parts[indices["CP"]])
            except (ValueError, IndexError) as exc:
                raise ValueError(f"{path}:{line_no}: 无法解析数据行 {line!r}") from exc
            if rpm <= 0:
                raise ValueError(f"{path}:{line_no}: RPM 必须 > 0")
            if ct < 0 or cp < 0:
                raise ValueError(f"{path}:{line_no}: CT/CP 必须 >= 0")
            rows.append({"rpm": rpm, "ct": ct, "cp": cp, "n_rps": rpm / 60.0})

    if header is None:
        raise ValueError(f"{path}: 文件为空或只有注释")
    if not rows:
        raise ValueError(f"{path}: 没有有效数据行")
    return rows


def summarize(rows: list[dict]) -> dict:
    rpms = [r["rpm"] for r in rows]
    return {
        "points": len(rows),
        "rpm_min": min(rpms),
        "rpm_max": max(rpms),
        "ct_mean": sum(r["ct"] for r in rows) / len(rows),
        "cp_mean": sum(r["cp"] for r in rows) / len(rows),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UIUC 静态数据解析器（v0.1）")
    parser.add_argument("--input", default=str(DEFAULT_REFERENCE), help="静态数据文件路径")
    args = parser.parse_args(argv)
    try:
        rows = load_static(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(f"错误：{exc}")
        return 2
    stats = summarize(rows)
    print(f"文件：{args.input}")
    print(f"数据点：{stats['points']}，RPM {stats['rpm_min']:g}–{stats['rpm_max']:g}")
    print(f"CT 均值 {stats['ct_mean']:.4f}；CP 均值 {stats['cp_mean']:.4f}")
    print("来源：UIUC Propeller Database（引用时注明 UIUC）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
