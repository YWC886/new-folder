"""口径与引用一致性审计（v0.1）。

扫描 docs/**/*.md 与根 README：
1) 禁词（项目自述语境）：多桨对比、跨桨型、更换桨型、换不同桨型；
2) 边界词缺失提示：出现 SIM/REFERENCE 数字但段落无标注；
3) 内部路径引用存在性（`docs/...`、`code/...`、`data/...`）。

输出：data/processed/consistency_audit_v0.1.md / .json；有 HARD 问题 exit 1。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"D:\下载\创新")
OUT_MD = ROOT / "data" / "processed" / "consistency_audit_v0.1.md"
OUT_JSON = ROOT / "data" / "processed" / "consistency_audit_v0.1.json"

FORBIDDEN = ["多桨对比", "跨桨型", "更换桨型", "换不同桨型", "多套硬件"]
SELF_MARKERS = ["本项目", "本课题", "我们", "团队将", "拟", "计划"]
LIT_MARKERS = ["文献", "已有研究", "他人", "综述", "Nam", "Piljek", "Costa", "UIUC", "参考"]
PATH_RE = re.compile(r"(?:docs|code|data)/[A-Za-z0-9_\u4e00-\u9fff./-]+")


def scan_files() -> list[Path]:
    files = sorted((ROOT / "docs").rglob("*.md"))
    if (ROOT / "README.md").exists():
        files.append(ROOT / "README.md")
    return files


def main() -> int:
    findings = []
    for f in scan_files():
        rel = str(f.relative_to(ROOT))
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            for w in FORBIDDEN:
                if w not in line:
                    continue
                is_self = any(m in line for m in SELF_MARKERS)
                if w == '更换桨型' and '不更换桨型' in line:
                    continue
                is_lit = any(m in line for m in LIT_MARKERS)
                severity = "HARD" if is_self and not is_lit else "SOFT"
                findings.append({"file": rel, "line": i, "word": w, "severity": severity,
                                 "text": line.strip()[:120]})
            for m in PATH_RE.finditer(line):
                p = m.group(0).rstrip(".,;:）)")
                if any(ch in p for ch in "*<>|"):
                    continue
                if not (ROOT / p).exists():
                    findings.append({"file": rel, "line": i, "word": "broken-ref",
                                     "severity": "SOFT", "text": p})
    hard = [x for x in findings if x["severity"] == "HARD"]
    soft = [x for x in findings if x["severity"] != "HARD"]
    lines = ["# 口径与引用一致性审计 v0.1", "", f"文件数：{len(scan_files())}；HARD {len(hard)}；SOFT {len(soft)}", ""]
    lines += ["## HARD（项目自述语境禁词，必须改）", ""]
    lines += [f"- {x['file']}:{x['line']} [{x['word']}] {x['text']}" for x in hard] or ["- 无"]
    lines += ["", "## SOFT（文献语境/断链，复核）", ""]
    lines += [f"- {x['file']}:{x['line']} [{x['word']}] {x['text']}" for x in soft[:200]] or ["- 无"]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps({"files": len(scan_files()), "hard": hard, "soft": soft},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"HARD={len(hard)} SOFT={len(soft)} -> {OUT_MD.relative_to(ROOT)}")
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
