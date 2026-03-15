---
name: mcp-local-tool
description: >
  Use when asked to create a new local MCP (Model Context Protocol) tool/server
  for GitHub Copilot — file readers, API wrappers, CLI integrations, or any
  capability that Copilot cannot do natively. Covers the full workflow: Python
  MCP server implementation, dependency setup, VS Code mcp.json registration,
  Windows installation script, and end-to-end verification. Applies to any
  OS-local tool that must run without internet access (corporate environments).
argument-hint: <tool-name> [what the tool should do]
---

# Building Local MCP Tools for GitHub Copilot

MCP (Model Context Protocol) is an open standard that lets you register custom
**tools** that GitHub Copilot can call from Chat. The tool runs as a local
process on your machine — no cloud, no internet, no data leaving the company.

This skill covers the full workflow for building, installing, and registering
a Python-based MCP tool.

## When to Use This Skill

- User wants Copilot to read/process a file type it doesn't natively support (PDF, Word, Excel, …).
- User wants Copilot to call a local CLI tool, internal REST API, or database.
- User wants to extend Copilot with any domain-specific capability.
- User is in a restricted corporate environment where only GitHub Copilot is allowed.

## Prerequisites

- VS Code with GitHub Copilot Chat extension.
- **Standard CPython 3.10+** from [python.org](https://www.python.org/downloads/)
  installed to `%LOCALAPPDATA%\Programs\Python\Python31x\`.
  > ⚠️ **Important:** Do NOT use MSYS2/Git/Conda Python as the venv Python — they
  > create `bin\` layout venvs and cannot install binary wheels (e.g., `pymupdf`).
  > Always use `%LOCALAPPDATA%\Programs\Python\Python31x\python.exe` explicitly.
- MCP Python SDK: `pip install mcp`
- Workspace folder open in VS Code (so `.vscode/mcp.json` is resolved correctly).

## Directory Layout

```
<workspace>/
├── .vscode/
│   └── mcp.json                  ← registers the server with VS Code/Copilot
└── tools/
    └── <tool-name>-mcp/
        ├── server.py             ← MCP server implementation
        ├── requirements.txt      ← Python dependencies
        └── install.bat           ← Windows setup script (creates venv, installs deps)
```

## Step-by-Step Workflow

### Step 1: Design the tools

Decide what tools the MCP server will expose. Each tool has:
- A **name** (snake_case, e.g. `read_pdf`)
- A **description** (tells Copilot when to call it — be specific)
- An **inputSchema** (JSON Schema for parameters)

Rule of thumb: **one tool per distinct action**. Do not make one giant tool.

### Step 2: Implement `server.py`

Minimal skeleton:

```python
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

server = Server("my-tool")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="my_action",
            description="Does X when the user needs Y. Returns Z.",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_param": {"type": "string", "description": "What this param is"}
                },
                "required": ["input_param"],
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "my_action":
        result = do_something(arguments["input_param"])
        return [types.TextContent(type="text", text=result)]
    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream,
                         server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

**Security checklist for `server.py`:**
- [ ] Validate and `Path.resolve()` all file paths — prevent path traversal.
- [ ] Never expose shell commands with user-controlled input (no `subprocess` with f-strings).
- [ ] Wrap all tool logic in `try/except` and return errors as `TextContent`, never crash.
- [ ] Return meaningful error messages that Copilot can relay back to the user.

### Step 3: Create `requirements.txt`

```
mcp>=1.0.0
# add libraries your tool needs, e.g.:
# pymupdf>=1.24.0
# python-docx>=1.1.0
# openpyxl>=3.1.0
```

### Step 4: Create `install.bat` (Windows)

The installer must:
1. Explicitly use the standard CPython path (not the PATH-resolved `python`).
2. Create a venv inside the tool directory.
3. Use `python.exe -m pip install` (not `pip.exe` — more reliable).

```bat
@echo off
setlocal

REM --- Prefer standard CPython, avoid MSYS2/Git Python ---
set "PYTHON_EXE="
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) do (
    if exist %%P if not defined PYTHON_EXE set "PYTHON_EXE=%%~P"
)
if not defined PYTHON_EXE (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYTHON_EXE=python"
)
if not defined PYTHON_EXE (
    echo ERROR: Python 3.10+ not found. Install from https://www.python.org/downloads/
    pause & exit /b 1
)
echo Using: %PYTHON_EXE%

REM --- Create venv ---
if not exist "%~dp0venv\" (
    "%PYTHON_EXE%" -m venv "%~dp0venv"
)

REM --- Install dependencies ---
"%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip
"%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 ( echo ERROR: pip install failed. & pause & exit /b 1 )

echo.
echo Setup complete! Reload VS Code (Ctrl+Shift+P > Developer: Reload Window).
pause
```

### Step 5: Register in `.vscode/mcp.json`

> ⚠️ **Critical rules for `mcp.json` on Windows:**
> - Use **hardcoded absolute paths with `\\`** — do NOT use `${workspaceFolder}`.
>   `${workspaceFolder}` produces mixed-slash paths (`D:\AI/tools/...`) that cause `ENOENT`.
> - No `// comments` — strict JSON only. Comments cause silent parse failures.
> - The `command` must point to the **venv's `Scripts\python.exe`**, not global Python.

```json
{
  "servers": {
    "<tool-name>": {
      "type": "stdio",
      "command": "D:\\path\\to\\tools\\<tool-name>-mcp\\venv\\Scripts\\python.exe",
      "args": ["D:\\path\\to\\tools\\<tool-name>-mcp\\server.py"],
      "description": "One-line description of what this tool does"
    }
  }
}
```

### Step 6: Verify the server works

Test the MCP handshake from PowerShell before reloading VS Code:

```powershell
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' |
  & "D:\path\to\venv\Scripts\python.exe" "D:\path\to\server.py"
```

Expected output contains `"result":{"protocolVersion":"2024-11-05",...}`.
If it returns a valid JSON object, the server is ready.

### Step 7: Reload VS Code and use the tool

1. `Ctrl+Shift+P` → **Developer: Reload Window**
2. Open Copilot Chat and ask Copilot to use the tool naturally:
   ```
   Read this file: C:\path\to\document.pdf
   ```

Copilot will automatically call the tool when it detects the need.

## Common Pitfalls & Fixes

| Symptom | Cause | Fix |
|---|---|---|
| `ENOENT` on server start | Mixed-slash path in `mcp.json` from `${workspaceFolder}` | Use hardcoded `\\` absolute paths |
| `The system cannot find the path specified` | MSYS2/Git Python created `bin\` venv instead of `Scripts\` | Recreate venv with CPython from `%LOCALAPPDATA%\Programs\Python\` |
| `Preparing metadata ... error` during pip | MSYS2 GCC Python can't build native extensions | Same fix — use standard CPython |
| Tool not called by Copilot | Tool `description` is too vague | Rewrite description: "Use when user asks to X. Returns Y." |
| Server starts but tool errors | Unhandled exception crashing the server | Wrap all tool logic in `try/except`, return error as `TextContent` |
| `// comments` in mcp.json | Comments = invalid JSON → silent parse failure | Remove all comments from `mcp.json` |

## Useful Python Libraries for MCP Tools

| Need | Library | Install |
|---|---|---|
| Read PDF | `pymupdf` | `pip install pymupdf` |
| Read Word (.docx) | `python-docx` | `pip install python-docx` |
| Read Excel (.xlsx) / CSV | `openpyxl` | `pip install openpyxl` |
| HTTP requests / REST API | `httpx` or `requests` | `pip install httpx` |
| Run CLI commands safely | stdlib `subprocess` | built-in |
| Parse HTML | `beautifulsoup4` | `pip install beautifulsoup4` |
| SQLite database | stdlib `sqlite3` | built-in |
| YAML / TOML config files | `pyyaml` / `tomllib` | `pip install pyyaml` |

## References

- [MCP specification](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [VS Code MCP server docs](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
