"""Tool system for Dario-chan."""

import subprocess
import json
import os
from abc import ABC, abstractmethod


class Tool(ABC):
    """Base class for tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema parameters definition."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool and return result as string."""
        pass

    def to_definition(self) -> dict:
        """Convert to tool definition for LLM."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": list(self.parameters.keys()),
                },
            },
        }


class BashTool(Tool):
    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return "Execute a bash command. Use for running shell commands, file operations, and system tasks."

    @property
    def parameters(self) -> dict:
        return {
            "command": {
                "type": "string",
                "description": "The bash command to execute",
            }
        }

    def execute(self, command: str, **kwargs) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd(),
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            return output.strip()
        except subprocess.TimeoutExpired:
            return "Command timed out (30s limit)"
        except Exception as e:
            return f"Error executing command: {e}"


class FileReadTool(Tool):
    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read the contents of a file. Returns the full text content."

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Absolute path to the file to read",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of lines to read (optional)",
            },
        }

    def execute(self, path: str, limit: int | None = None, **kwargs) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                if limit:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= limit:
                            break
                        lines.append(line)
                    content = "".join(lines)
                else:
                    content = f.read()
            return content
        except FileNotFoundError:
            return f"File not found: {path}"
        except PermissionError:
            return f"Permission denied: {path}"
        except Exception as e:
            return f"Error reading file: {e}"


class FileWriteTool(Tool):
    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "Write content to a file. Creates the file if it doesn't exist, overwrites if it does."

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Absolute path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
        }

    def execute(self, path: str, content: str, **kwargs) -> str:
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ Written to {path}"
        except Exception as e:
            return f"Error writing file: {e}"


class FileEditTool(Tool):
    @property
    def name(self) -> str:
        return "file_edit"

    @property
    def description(self) -> str:
        return "Replace text in a file. Requires exact match of the old text."

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "Absolute path to the file to edit",
            },
            "old_text": {
                "type": "string",
                "description": "Exact text to replace",
            },
            "new_text": {
                "type": "string",
                "description": "Replacement text",
            },
        }

    def execute(self, path: str, old_text: str, new_text: str, **kwargs) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if old_text not in content:
                return f"Text not found in {path}. Use file_read first to see the current content."

            new_content = content.replace(old_text, new_text, 1)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return f"✅ Edited {path}"
        except Exception as e:
            return f"Error editing file: {e}"


class GrepTool(Tool):
    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return "Search for a pattern in files. Like grep but returns matching file paths and lines."

    @property
    def parameters(self) -> dict:
        return {
            "pattern": {
                "type": "string",
                "description": "Pattern to search for (regex supported)",
            },
            "path": {
                "type": "string",
                "description": "Directory or file to search in (default: current directory)",
            },
            "glob": {
                "type": "string",
                "description": "File glob pattern like '*.py' (optional)",
            },
        }

    def execute(self, pattern: str, path: str = ".", glob: str | None = None, **kwargs) -> str:
        try:
            import re
            results = []
            search_path = path if os.path.exists(path) else "."

            if os.path.isfile(search_path):
                files = [search_path]
            else:
                files = []
                for root, _, filenames in os.walk(search_path):
                    for fname in filenames:
                        if glob and not __import__("fnmatch").fnmatch(fname, glob):
                            continue
                        files.append(os.path.join(root, fname))

            for fpath in files:
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                results.append(f"{fpath}:{i}: {line.rstrip()}")
                except (UnicodeDecodeError, PermissionError):
                    continue

            if not results:
                return f"No matches found for '{pattern}'"
            return "\n".join(results[:100])
        except Exception as e:
            return f"Error searching: {e}"


# Tool registry
TOOL_REGISTRY: dict[str, Tool] = {}


def register_tool(tool: Tool) -> None:
    TOOL_REGISTRY[tool.name] = tool


def get_tool_definitions() -> list[dict]:
    """Get all tool definitions in LLM format."""
    return [tool.to_definition() for tool in TOOL_REGISTRY.values()]


def execute_tool(tool_name: str, args: dict) -> str:
    """Execute a tool by name with given arguments."""
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return f"Unknown tool: {tool_name}"
    return tool.execute(**args)


# Auto-register all built-in tools
for _tool_cls in [BashTool, FileReadTool, FileWriteTool, FileEditTool, GrepTool]:
    register_tool(_tool_cls())
del _tool_cls
