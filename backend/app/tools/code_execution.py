import asyncio
import os
import subprocess
import tempfile

from app.tools.base import BaseTool

# Minimal environment for the child process
_SANDBOX_ENV = {
    "PATH": "/usr/bin:/bin:/usr/local/bin",
    "HOME": "/tmp",
    "PYTHONDONTWRITEBYTECODE": "1",
}


class CodeExecutionTool(BaseTool):
    name = "code_execution"
    description = "Execute Python code in a sandboxed environment and return the output."

    def get_definition(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute",
                    }
                },
                "required": ["code"],
            },
        }

    async def execute(self, input: dict) -> str:
        code = input.get("code", "")
        if not code.strip():
            return "Error: No code provided"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", tmp_path,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=_SANDBOX_ENV,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return "Error: Code execution timed out (30s limit)"

            output = ""
            if stdout:
                output += stdout.decode(errors="replace")
            if stderr:
                output += ("\n" if output else "") + stderr.decode(errors="replace")
            return output or "(no output)"
        finally:
            os.unlink(tmp_path)
