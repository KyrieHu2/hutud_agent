from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field


# 当前工作目录，限制工具只能操作这个目录里面的文件
WORKDIR = Path.cwd().resolve()


def safe_path(p: str) -> Path:
    """
    Convert a user-provided relative path into a safe absolute path under WORKDIR.

    Raises:
        ValueError: If the resolved path escapes the workspace.
    """
    path = (WORKDIR / p).resolve()

    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")

    return path


# =========================
# read_file tool
# =========================

class ReadFileInput(BaseModel):
    path: str = Field(
        description=(
            "Relative file path to read from the current workspace. "
            "Example: 'src/main.py' or 'README.md'. "
            "Absolute paths or paths escaping the workspace are not allowed."
        )
    )

    limit: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Optional maximum number of lines to return. "
            "If omitted, the whole file is returned up to the character limit."
        ),
    )


@tool(
    "read_file",
    args_schema=ReadFileInput,
    description=(
        "Read a text file from the current workspace and return its content. "
        "Use this tool when you need to inspect source code, configuration files, "
        "documentation, or other text files. "
        "The path must stay inside the workspace. "
        "The output is truncated to at most 50000 characters."
    ),
)
def read_file(path: str, limit: int | None = None) -> str:
    """Read a workspace text file and return its content."""
    try:
        text = safe_path(path).read_text(encoding="utf-8")
        lines = text.splitlines()

        if limit is not None and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more lines)"]

        return "\n".join(lines)[:50000]

    except Exception as e:
        return f"Error: {e}"


# =========================
# write_file tool
# =========================

class WriteFileInput(BaseModel):
    path: str = Field(
        description=(
            "Relative file path to write inside the current workspace. "
            "Example: 'src/main.py' or 'docs/notes.md'. "
            "Parent directories will be created automatically if needed. "
            "Absolute paths or paths escaping the workspace are not allowed."
        )
    )

    content: str = Field(
        description=(
            "Full text content to write into the file. "
            "This replaces the entire file if it already exists."
        )
    )


@tool(
    "write_file",
    args_schema=WriteFileInput,
    description=(
        "Write text content to a file inside the current workspace. "
        "Use this tool when you need to create a new file or fully replace an existing file. "
        "This tool creates parent directories automatically. "
        "The path must stay inside the workspace."
    ),
)
def write_file(path: str, content: str) -> str:
    """Write text content to a workspace file."""
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")

        return f"Wrote {len(content)} characters to {path}"

    except Exception as e:
        return f"Error: {e}"


# =========================
# edit_file tool
# =========================

class EditFileInput(BaseModel):
    path: str = Field(
        description=(
            "Relative file path to edit inside the current workspace. "
            "Example: 'src/main.py' or 'README.md'. "
            "Absolute paths or paths escaping the workspace are not allowed."
        )
    )

    old_text: str = Field(
        description=(
            "Exact text to find in the file. "
            "The edit will fail if this text does not exist exactly once or cannot be found."
        )
    )

    new_text: str = Field(
        description=(
            "Replacement text. "
            "Only the first occurrence of old_text will be replaced."
        )
    )


@tool(
    "edit_file",
    args_schema=EditFileInput,
    description=(
        "Edit a text file inside the current workspace by replacing the first occurrence "
        "of old_text with new_text. "
        "Use this tool for small, targeted code changes. "
        "Do not use this tool to rewrite an entire file; use write_file for that. "
        "The path must stay inside the workspace."
    ),
)
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Edit a workspace text file by replacing the first matching text block."""
    try:
        fp = safe_path(path)
        content = fp.read_text(encoding="utf-8")

        if old_text not in content:
            return f"Error: Text not found in {path}"

        fp.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")

        return f"Edited {path}"

    except Exception as e:
        return f"Error: {e}"

