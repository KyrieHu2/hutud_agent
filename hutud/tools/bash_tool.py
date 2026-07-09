import os
import subprocess
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class RunPowerShellInput(BaseModel):
    """Input schema for the run_powershell tool."""

    command: str = Field(
        description=(
            "A safe Windows PowerShell command to execute in the current project directory. "
            "Use PowerShell commands only. "
            "Prefer read-only commands such as Get-ChildItem, Get-Content, Select-String, "
            "Get-Location, Get-Command, python --version, pip list, or running project tests. "
            "Do not use Linux/macOS bash commands such as ls -la, cat, grep, rm, chmod, sudo. "
            "Do not pass destructive commands that delete files, change system settings, "
            "shutdown/reboot the machine, access credentials, or modify protected paths."
        )
    )


@tool(
    "run_powershell",
    args_schema=RunPowerShellInput,
    description=(
        "Run a safe Windows PowerShell command in the current project directory and return stdout/stderr. "
        "Use this tool only with Windows PowerShell syntax. "
        "Use Get-ChildItem to list files, Get-Content to read files, Select-String to search text, "
        "Get-Location to show the current directory, and Get-Command to locate executables. "
        "Do not use bash/Linux/macOS commands."
    ),
)
def run_powershell(command: str) -> str:
    """Execute a safe Windows PowerShell command and return stdout/stderr."""
    dangerous = [
        "rm -rf /",
        "sudo",
        "shutdown",
        "reboot",
        "> /dev/",
        "del /s",
        "format",
        "reg delete",
        "Remove-Item -Recurse",
        "Remove-Item -Force",
        "Set-ExecutionPolicy",
        "Stop-Computer",
        "Restart-Computer",
    ]

    if any(d.lower() in command.lower() for d in dangerous):
        return "Error: Dangerous command blocked"

    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = (result.stdout + result.stderr).strip()
        return output[:50000] if output else "(no output)"

    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}"