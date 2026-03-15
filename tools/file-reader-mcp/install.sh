#!/usr/bin/env bash
# ============================================================
#  File Reader MCP — Setup Script (Linux / macOS)
#  Installs Python dependencies needed by server.py
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ------------------------------------------------------------
# Step 1: Find Python 3.10+
# ------------------------------------------------------------
echo "[1/3] Checking Python installation..."

PYTHON_EXE=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidate" &>/dev/null; then
        version=$("$candidate" -c "import sys; print(sys.version_info[:2])")
        major=$("$candidate" -c "import sys; print(sys.version_info.major)")
        minor=$("$candidate" -c "import sys; print(sys.version_info.minor)")
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON_EXE="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON_EXE" ]; then
    echo "ERROR: Python 3.10+ not found."
    echo "Install it with:"
    echo "  Ubuntu/Debian : sudo apt install python3.12 python3.12-venv"
    echo "  Fedora/RHEL   : sudo dnf install python3.12"
    echo "  macOS (brew)  : brew install python@3.12"
    exit 1
fi

echo "Using: $PYTHON_EXE ($("$PYTHON_EXE" --version))"

# ------------------------------------------------------------
# Step 2: Create virtual environment
# ------------------------------------------------------------
echo ""
echo "[2/3] Creating virtual environment (venv)..."

VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_EXE" -m venv "$VENV_DIR"
    echo "Virtual environment created."
else
    echo "Virtual environment already exists, skipping."
fi

VENV_PYTHON="$VENV_DIR/bin/python"

# ------------------------------------------------------------
# Step 3: Install dependencies
# ------------------------------------------------------------
echo ""
echo "[3/3] Installing dependencies into venv..."

"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt"

# ------------------------------------------------------------
# Done
# ------------------------------------------------------------
echo ""
echo "============================================================"
echo " Setup complete!"
echo "============================================================"
echo ""
echo "Next step: configure VS Code to use this MCP server."
echo "Open .vscode/mcp.json and set:"
echo "  \"command\": \"$VENV_PYTHON\""
echo "  \"args\": [\"$SCRIPT_DIR/server.py\"]"
echo ""
