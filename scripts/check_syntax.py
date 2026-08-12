"""代码质量自检脚本。"""
from __future__ import annotations

import ast
import os
from pathlib import Path


def check_syntax() -> bool:
    """检查所有 Python 文件的语法。"""
    root = "app"
    issues = []
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            if fn.endswith(".py"):
                count += 1
                path = Path(dirpath) / fn
                try:
                    with path.open(encoding="utf-8") as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    issues.append(f"{path}: {e}")
    if issues:
        print("FAIL")
        for i in issues:
            print(f"  {i}")
        return False
    print(f"OK: {count} files checked")
    return True


if __name__ == "__main__":
    ok = check_syntax()
    exit(0 if ok else 1)
