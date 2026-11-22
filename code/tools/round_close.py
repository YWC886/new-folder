"""轮次收尾脚本：重建复现包清单 + 运行提交前检查（preflight）。

用法：py -3.12 code/tools/round_close.py
退出码：0 全部通过；1 有失败项
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
TOOLS = ROOT / "code" / "tools"


def run(script: str, *args: str) -> int:
    print(f"== {script} {' '.join(args)} ==")
    return subprocess.call([sys.executable, str(TOOLS / script), *args], cwd=str(ROOT), env=ENV)


def main() -> int:
    rc = run("build_manifest.py", "--overwrite")
    if rc != 0:
        return rc
    rc = run("check_release.py")
    if rc != 0:
        return rc
    rc = run("audit_consistency.py")
    print("结论：round_close", "PASS" if rc == 0 else "FAIL")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
