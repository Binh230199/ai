---
name: lang-python-code-writing
description: >
  Use when writing, reviewing, or debugging Python scripts for embedded development
  workflows. Covers script structure, type hints, error handling, subprocess/ADB automation,
  serial communication, log parsing, REST API clients (Gerrit/Jira/Artifactory),
  data manipulation (JSON/XML/YAML), test harness utilities, and CI/CD tooling
  for automotive IVI / HUD / RSE projects targeting Android Automotive / Linux / QNX.
argument-hint: <script-or-module> [write|review|debug]
---

# Python Scripting — Embedded Development

Expert practices for writing reliable, maintainable Python scripts and tools
that support **Android Automotive (AOSP)**, **Linux BSP (Yocto/Buildroot)**,
and **QNX** embedded development workflows.

Standards baseline: **Python 3.10+** · **PEP 8** style · **type hints** throughout.

---

## When to Use This Skill

- Build automation and wrapper scripts around AOSP, Yocto, or CMake.
- ADB interaction scripts (install, logcat, shell commands, screenshots).
- Serial/UART console communication with target boards.
- Log parsing, report generation, and coredump analysis.
- REST API clients for Gerrit, Jira, Artifactory.
- Test harness utilities and on-target test runners.
- CI/CD pipeline helper tools (Jenkins, GitLab CI).
- Data conversion/migration between JSON/XML/YAML/CSV formats.

---

## Script Skeleton — Always Start Here

```python
#!/usr/bin/env python3
"""Flash a built AOSP image to a connected ADB device.

Usage:
    python flash_target.py --product aosp_car_x86_64 --variant userdebug
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# ---------- logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------- constants ----------
DEFAULT_PRODUCT = os.environ.get("PRODUCT", "aosp_car_x86_64")
DEFAULT_VARIANT = os.environ.get("VARIANT", "userdebug")


# ---------- argument parsing ----------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", default=DEFAULT_PRODUCT)
    parser.add_argument("--variant", choices=["eng", "userdebug", "user"],
                        default=DEFAULT_VARIANT)
    parser.add_argument("--out-dir", type=Path,
                        default=Path(os.environ.get("ANDROID_PRODUCT_OUT", "out")))
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


# ---------- main ----------
def main() -> int:
    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    log.info("Flashing %s (%s) from %s", args.product, args.variant, args.out_dir)
    # ... implementation
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Rules**
- `#!/usr/bin/env python3` shebang — portable across Linux/macOS.
- `from __future__ import annotations` — deferred annotation evaluation (Python 3.10 compat).
- `sys.exit(main())` — `main()` returns `int` exit code; never `sys.exit()` inside helper functions.
- Use `argparse` with `choices=` and `type=Path` for structured argument validation.
- Use `logging` — never bare `print()` for status output.

---

## Error Handling

```python
import subprocess
from subprocess import CalledProcessError

# Raising meaningful exceptions (prefer over sys.exit in library code)
class FlashError(RuntimeError):
    """Raised when flashing a target device fails."""

# subprocess — always use check=True or handle explicitly
def run_cmd(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command and raise on non-zero exit."""
    log.debug("$ %s", " ".join(cmd))
    return subprocess.run(cmd, check=True, text=True, **kwargs)

# Capture output
def get_adb_devices() -> str:
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
    return result.stdout

# Handle specific errors
try:
    run_cmd(["adb", "install", "-r", str(apk_path)])
except CalledProcessError as e:
    log.error("ADB install failed (exit %d): %s", e.returncode, e.stderr)
    raise FlashError(f"Could not install {apk_path}") from e
except FileNotFoundError:
    log.error("adb not found — is Android SDK platform-tools in PATH?")
    sys.exit(1)
```

---

## Pathlib — Filesystem Operations

```python
from pathlib import Path

# Build paths — no os.path.join
out_dir   = Path(os.environ["ANDROID_PRODUCT_OUT"])
apk_path  = out_dir / "system" / "app" / "MyCarApp" / "MyCarApp.apk"
log_file  = Path("/tmp") / f"build_{timestamp}.log"

# Checks
if not apk_path.exists():
    raise FileNotFoundError(f"APK not found: {apk_path}")

# Glob
apk_files = list(out_dir.glob("**/*.apk"))

# Create dirs
out_dir.mkdir(parents=True, exist_ok=True)

# Read / write text
content   = log_file.read_text(encoding="utf-8")
log_file.write_text(report, encoding="utf-8")

# Rename / delete
apk_path.rename(apk_path.with_suffix(".apk.bak"))
tmp_file.unlink(missing_ok=True)

# Iterate lines safely
for line in log_file.read_text(encoding="utf-8").splitlines():
    process_line(line)
```

---

## ADB Automation

```python
import subprocess
import time


def wait_for_device(timeout: int = 60) -> None:
    subprocess.run(["adb", "wait-for-device"], check=True, timeout=timeout)
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = subprocess.run(
            ["adb", "shell", "getprop", "sys.boot_completed"],
            capture_output=True, text=True
        )
        if result.stdout.strip() == "1":
            log.info("Device booted and ready.")
            return
        time.sleep(2)
    raise TimeoutError("Device did not complete boot within timeout.")


def install_apk(apk: Path, retries: int = 3) -> None:
    for attempt in range(1, retries + 1):
        try:
            run_cmd(["adb", "install", "-r", "-t", str(apk)])
            log.info("Installed: %s", apk.name)
            return
        except subprocess.CalledProcessError:
            if attempt == retries:
                raise
            log.warning("Install attempt %d failed. Retrying...", attempt)
            time.sleep(2)


def capture_logcat(duration: float = 10.0, output: Path | None = None) -> Path:
    if output is None:
        output = Path(f"/tmp/logcat_{int(time.time())}.log")
    subprocess.run(["adb", "logcat", "-c"], check=True)
    proc = subprocess.Popen(["adb", "logcat"], stdout=subprocess.PIPE, text=True)
    time.sleep(duration)
    proc.terminate()
    stdout, _ = proc.communicate()
    output.write_text(stdout, encoding="utf-8")
    log.info("Logcat saved: %s", output)
    return output


def adb_shell(cmd: str) -> str:
    result = subprocess.run(["adb", "shell", cmd], capture_output=True, text=True, check=True)
    return result.stdout.strip()
```

---

## Serial Communication

```python
# pip install pyserial
import serial
import threading


def open_serial(port: str = "/dev/ttyUSB0", baud: int = 115200) -> serial.Serial:
    return serial.Serial(port, baud, timeout=1)


def read_serial_until(ser: serial.Serial, marker: str, timeout: float = 30.0) -> str:
    """Read serial output until a marker string appears or timeout."""
    buf: list[str] = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").rstrip()
        if line:
            buf.append(line)
            log.debug("[serial] %s", line)
            if marker in line:
                return "\n".join(buf)
    raise TimeoutError(f"Marker '{marker}' not seen within {timeout}s")


def send_and_wait(ser: serial.Serial, command: str, prompt: str = "#") -> str:
    ser.write(f"{command}\n".encode())
    return read_serial_until(ser, prompt)
```

---

## Log Parsing

```python
import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    tag: str
    message: str


# Android logcat format: MM-DD HH:MM:SS.mmm PID TID Level Tag: Message
LOGCAT_RE = re.compile(
    r"^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+"   # timestamp
    r"(\d+)\s+(\d+)\s+"                                # pid tid
    r"([VDIWEF])\s+"                                    # level
    r"(.+?)\s*:\s*(.*)$"                               # tag: message
)


def parse_logcat_line(line: str) -> LogEntry | None:
    m = LOGCAT_RE.match(line)
    if not m:
        return None
    ts_str, _pid, _tid, level, tag, message = m.groups()
    ts = datetime.strptime(ts_str, "%m-%d %H:%M:%S.%f")
    return LogEntry(timestamp=ts, level=level, tag=tag, message=message)


def filter_crashes(log_path: Path) -> list[LogEntry]:
    entries = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        entry = parse_logcat_line(line)
        if entry and entry.level in ("E", "F") and "crash" in entry.message.lower():
            entries.append(entry)
    return entries
```

---

## REST API Clients (Gerrit / Jira / Artifactory)

```python
import json
import os
from urllib.parse import urlencode

import requests  # pip install requests


class GerritClient:
    """Thin client for Gerrit REST API."""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self._base = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._session.headers.update({"Accept": "application/json"})

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        r = self._session.get(f"{self._base}/a{path}", params=params, timeout=30)
        r.raise_for_status()
        # Gerrit prepends )]}' on authenticated responses
        return json.loads(r.text.lstrip(")]}'\n"))

    def get_open_changes(self, project: str) -> list[dict]:
        return self._get("/changes/", params={"q": f"status:open project:{project}", "o": "CURRENT_REVISION"})


def upload_artifact(url: str, local_path: Path, token: str) -> str:
    """Upload a file to Artifactory and return its download URL."""
    with local_path.open("rb") as fh:
        headers = {"X-JFrog-Art-Api": token, "Content-Type": "application/octet-stream"}
        r = requests.put(url, data=fh, headers=headers, timeout=120)
        r.raise_for_status()
    return r.json()["downloadUri"]
```

**Security**: Never hardcode credentials.

```python
# Read from environment — set by CI secrets or local .env (git-ignored)
GERRIT_USER  = os.environ["GERRIT_USER"]
GERRIT_TOKEN = os.environ["GERRIT_TOKEN"]
```

---

## YAML / JSON / XML Data Handling

```python
import json
import xml.etree.ElementTree as ET

import yaml  # pip install pyyaml

# JSON
config = json.loads(config_file.read_text())
config_file.write_text(json.dumps(config, indent=2))

# YAML
with open("config.yaml") as f:
    cfg = yaml.safe_load(f)                  # always safe_load — never yaml.load

# XML (Android Manifest / build configs)
tree = ET.parse("AndroidManifest.xml")
root = tree.getroot()
pkg  = root.get("{http://schemas.android.com/apk/res/android}package")
```

---

## Data Classes and Type Hints

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BuildConfig:
    product:    str
    variant:    str
    out_dir:    Path
    modules:    list[str]        = field(default_factory=list)
    clean:      bool             = False
    max_jobs:   int              = os.cpu_count() or 4

    def validate(self) -> None:
        if self.variant not in ("eng", "userdebug", "user"):
            raise ValueError(f"Invalid variant: {self.variant}")
        if not self.out_dir.is_dir():
            raise FileNotFoundError(f"out_dir not found: {self.out_dir}")
```

---

## Virtual Environment and Dependencies

```bash
# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
.\.venv\Scripts\Activate    # Windows PowerShell

pip install -r requirements.txt
```

```
# requirements.txt — pin major versions for reproducibility
requests>=2.31,<3
pyserial>=3.5,<4
PyYAML>=6.0,<7
```

---

## CI/CD Patterns

```python
import os


def is_ci() -> bool:
    return os.environ.get("CI", "false").lower() == "true"


def set_output(key: str, value: str) -> None:
    """Write a key=value pair to GitHub Actions / GitLab CI output."""
    if gh_output := os.environ.get("GITHUB_OUTPUT"):
        with open(gh_output, "a") as f:
            f.write(f"{key}={value}\n")
    elif os.environ.get("GITLAB_CI"):
        with open("build.env", "a") as f:
            f.write(f"{key}={value}\n")
```

---

## Prerequisites

- Python 3.8+ (`python3 --version` to verify).
- `pip` and `venv` available.
- For ADB scripts: Android Platform-Tools on PATH.
- Install project dependencies: `pip install -r requirements.txt` (if present).


## Step-by-Step Workflows

### Step 1: Create the script file
Add `#!/usr/bin/env python3`, a module docstring, and a `if __name__ == "__main__":` guard.

### Step 2: Add type hints
Annotate all function signatures with `typing` types; use `Optional[T]` for nullable params.

### Step 3: Implement with proper error handling
Catch specific exception types; never use bare `except:`; log before re-raising.

### Step 4: Use `pathlib` for file operations
Replace `os.path` with `pathlib.Path`; use `.read_text()` / `.write_text()`.

### Step 5: Run pylint / mypy
Fix all reported issues; annotate intentional suppressions with `# pylint: disable=<code>` and a comment.


## Troubleshooting

- **`ModuleNotFoundError`** — activate the correct virtual environment; run `pip install -r requirements.txt`.
- **`UnicodeDecodeError`** — open files with an explicit encoding: `open(path, encoding='utf-8', errors='replace')`.
- **`subprocess` hangs** — always set a `timeout=` parameter; avoid `shell=True` with user-controlled input (command injection risk).
- **`mypy` cannot infer type** — add explicit type annotations; use `cast(T, expr)` as a last resort with a comment.


## Pre-Commit Checklist

- [ ] `#!/usr/bin/env python3` shebang on executable scripts.
- [ ] `from __future__ import annotations` at top.
- [ ] `main()` returns `int`; caller uses `sys.exit(main())`.
- [ ] Type hints on all function signatures.
- [ ] `argparse` used for CLI arguments — no bare `sys.argv` slicing.
- [ ] `logging` used — no bare `print()` for status/debug output.
- [ ] `subprocess.run(..., check=True)` — always check exit codes.
- [ ] `pathlib.Path` used for all file/directory paths.
- [ ] Credentials from `os.environ` — never hardcoded.
- [ ] `yaml.safe_load()` — never `yaml.load()`.
- [ ] Script passes `ruff check .` and `mypy .` without errors.

---

## References

- [Python 3 Documentation](https://docs.python.org/3/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Ruff — fast Python linter](https://docs.astral.sh/ruff/)
- [Mypy — static type checker](https://mypy.readthedocs.io/)
- [subprocess Best Practices](https://docs.python.org/3/library/subprocess.html)
- [pyserial Documentation](https://pyserial.readthedocs.io/)
