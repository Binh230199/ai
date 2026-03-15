@echo off
REM ============================================================
REM  File Reader MCP — Setup Script (Windows)
REM  Installs Python dependencies needed by server.py
REM ============================================================

setlocal

echo [1/3] Checking Python installation...

REM Prefer the standard CPython from the user's local AppData install
REM (avoids MSYS2/Git/Conda Pythons which may not have binary wheels for all packages)
set "PYTHON_EXE="
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) do (
    if exist %%P (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%~P"
    )
)

REM Fall back to whatever 'python' is on PATH
if not defined PYTHON_EXE (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
    )
)

if not defined PYTHON_EXE (
    echo ERROR: Python is not installed or not on PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version

echo.
echo [2/3] Creating virtual environment (venv)...
if not exist "%~dp0venv\" (
    "%PYTHON_EXE%" -m venv "%~dp0venv"
    echo Virtual environment created.
) else (
    echo Virtual environment already exists, skipping.
)

echo.
echo [3/3] Installing dependencies into venv...

REM Detect whether the venv uses Scripts\ (standard CPython) or bin\ (MSYS2/Git Python)
set "VENV_PYTHON="
if exist "%~dp0venv\Scripts\python.exe" set "VENV_PYTHON=%~dp0venv\Scripts\python.exe"
if exist "%~dp0venv\bin\python.exe"     set "VENV_PYTHON=%~dp0venv\bin\python.exe"

if "%VENV_PYTHON%"=="" (
    echo ERROR: Could not locate python.exe inside the new venv.
    echo The virtual environment may not have been created correctly.
    echo Falling back to the global Python...
    set "VENV_PYTHON=python"
)

echo Using: %VENV_PYTHON%
"%VENV_PYTHON%" -m pip install --upgrade pip
"%VENV_PYTHON%" -m pip install -r "%~dp0requirements.txt"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install one or more packages.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Setup complete!
echo ============================================================
echo.
echo Next step: configure VS Code to use this MCP server.
echo Open .vscode\mcp.json and make sure the command points to:
echo   %VENV_PYTHON%
echo.
pause
