"""Python 代码执行工具。"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from typing import Any

from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger


class PythonExecTool(BaseTool):
    """Python 代码执行工具。"""

    name = "python_exec"
    description = "执行 Python 代码并返回结果"

    def __init__(self, timeout: float = 5.0) -> None:
        self.timeout = timeout

    async def execute(self, **kwargs: Any) -> ToolResult:
        code = kwargs.get("code", "")
        if not code:
            return ToolResult(success=False, output="", error="No code provided")

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                temp_path = f.name

            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            output = result.stdout.strip()
            error = result.stderr.strip()
            if result.returncode != 0:
                return ToolResult(success=False, output=output, error=error or "Execution failed")
            return ToolResult(success=True, output=output or "(no output)")
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error="Execution timed out")
        except Exception as e:
            logger.error(f"Python exec error: {e}")
            return ToolResult(success=False, output="", error=str(e))


__all__ = ["PythonExecTool"]
