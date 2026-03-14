---
name: lang-bash-scripting
description: >
  Use when writing, reviewing, or debugging Bash shell scripts on Linux for
  embedded development workflows. Covers script structure, error handling (set -euo pipefail),
  argument parsing, string/array manipulation, file operations, process management,
  ADB automation, build system helpers (AOSP/Yocto), log parsing, and CI/CD integration
  for automotive IVI / HUD / RSE projects running on Linux or QNX targets.
argument-hint: <script-name> [write|review|debug]
---

# Bash Scripting — Linux Embedded Development

Expert practices for writing reliable, portable Bash scripts that support
**Android (AOSP)**, **Linux BSP (Yocto/Buildroot)**, and **QNX** embedded
development workflows.

Standards baseline: **Bash 4.4+** · **POSIX sh** where cross-distro portability is required.

---

## When to Use This Skill

- Writing build helper, flash, or deployment scripts for embedded targets.
- Automating ADB interactions (flashing, log capture, screen recording).
- Parsing build logs, coredumps, or serial console output.
- Writing CI/CD pipeline step scripts (Jenkins, GitLab CI).
- Wrapping AOSP `m`/`make`, Yocto `bitbake`, or CMake commands.
- Managing SSH connections to target boards.

---

## Script Skeleton — Always Start Here

```bash
#!/usr/bin/env bash
# ============================================================
# Script: flash_target.sh
# Description: Flash a built image to a connected ADB device.
# Usage: ./flash_target.sh [--product <product>] [--variant <variant>]
# ============================================================
set -euo pipefail
IFS=$'\n\t'

# ---------- constants ----------
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"

# ---------- defaults ----------
PRODUCT="${PRODUCT:-aosp_car_x86_64}"
VARIANT="${VARIANT:-userdebug}"

# ---------- logging ----------
log()  { echo "[INFO]  $*"; }
warn() { echo "[WARN]  $*" >&2; }
die()  { echo "[ERROR] $*" >&2; exit 1; }

# ---------- cleanup ----------
cleanup() {
    log "Cleaning up temporary files..."
    # rm -f /tmp/flash_$$.tmp
}
trap cleanup EXIT

# ---------- usage ----------
usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS]

Options:
  --product PRODUCT   AOSP product name (default: $PRODUCT)
  --variant VARIANT   Build variant: eng|userdebug|user (default: $VARIANT)
  -h, --help          Show this help

Environment:
  PRODUCT, VARIANT    Override defaults via env vars
EOF
}

# ---------- argument parsing ----------
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --product) PRODUCT="$2"; shift 2 ;;
            --variant) VARIANT="$2"; shift 2 ;;
            -h|--help) usage; exit 0 ;;
            *) die "Unknown argument: $1" ;;
        esac
    done
}

# ---------- main ----------
main() {
    parse_args "$@"
    log "Flashing $PRODUCT ($VARIANT)..."
    # ... implementation
}

main "$@"
```

**Rules**
- `set -euo pipefail` MUST be the first statement — exits on error, unbound variable, or pipe failure.
- `IFS=$'\n\t'` prevents word-splitting bugs on filenames with spaces.
- Use `readonly` for constants — prevents accidental overwrite.
- Always define `cleanup()` + `trap cleanup EXIT` when creating temp files or long-running processes.

---

## Error Handling

```bash
# Die with message and exit code
die() { echo "[ERROR] $*" >&2; exit 1; }

# Check required commands exist
require_cmd() {
    for cmd in "$@"; do
        command -v "$cmd" &>/dev/null || die "Required command not found: $cmd"
    done
}

# Example
require_cmd adb fastboot python3 repo

# Conditional on exit code (without triggering set -e)
if ! adb devices | grep -q "device$"; then
    die "No ADB device connected. Check USB connection."
fi

# Preserving exit code in pipelines
adb logcat | tee /tmp/logcat.log | grep -i "fatal" || true
```

---

## Variables and Strings

```bash
# Quoting rules — always double-quote variables
log "Building: $PRODUCT"                      # correct
log "Building: ${PRODUCT}"                    # explicit boundary — use with adjacent chars
log "Path: ${SCRIPT_DIR}/out/${PRODUCT}"      # combine

# Default values
OUT_DIR="${OUT_DIR:-/tmp/build_output}"
MAX_JOBS="${MAX_JOBS:-$(nproc)}"               # default = CPU count

# Subshell capture (prefer $() over backticks)
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
KERNEL_VERSION="$(uname -r)"

# String manipulation
FILENAME="system-image-123.zip"
NAME="${FILENAME%.zip}"          # strip suffix → system-image-123
EXT="${FILENAME##*.}"            # extension → zip
BASE="${FILENAME##*/}"           # basename (pure bash, no subshell)
```

---

## Arrays

```bash
# Indexed array
MODULES=("MyCarApp" "CarService" "AudioHAL")

for module in "${MODULES[@]}"; do
    log "Building: $module"
    m "$module"
done

# Array length
log "Module count: ${#MODULES[@]}"

# Append
MODULES+=("NewModule")

# Passing arrays to functions (as individual args)
build_modules "${MODULES[@]}"

build_modules() {
    local modules=("$@")
    for m in "${modules[@]}"; do echo "  $m"; done
}
```

---

## File Operations

```bash
# Check existence before use
[[ -f "$CONFIG_FILE" ]] || die "Config not found: $CONFIG_FILE"
[[ -d "$OUT_DIR" ]]     || mkdir -p "$OUT_DIR"
[[ -x "$TOOL_PATH" ]]   || die "Tool not executable: $TOOL_PATH"

# Safe temp file (always cleaned up by trap)
TMPFILE="$(mktemp /tmp/build_XXXXXX.log)"
trap 'rm -f "$TMPFILE"' EXIT

# Read file line by line (handles spaces in lines)
while IFS= read -r line; do
    echo "Processing: $line"
done < "$INPUT_FILE"

# Find files matching pattern
find "${OUT_DIR}" -name "*.apk" -type f | while IFS= read -r apk; do
    log "APK: $apk"
done
```

---

## ADB Automation

```bash
# Wait for device
wait_for_device() {
    log "Waiting for ADB device..."
    adb wait-for-device
    adb shell getprop sys.boot_completed | grep -q "1" || {
        log "Waiting for boot to complete..."
        adb wait-for-device shell while [[ \"\$(getprop sys.boot_completed)\" != \"1\" ]]\; do sleep 1\; done
    }
    log "Device ready."
}

# Install APK with retry
install_apk() {
    local apk="$1"
    local retries=3
    local i=0
    while (( i++ < retries )); do
        if adb install -r -t "$apk"; then
            log "Installed: $apk"
            return 0
        fi
        warn "Install attempt $i failed, retrying..."
        sleep 2
    done
    die "Failed to install $apk after $retries attempts."
}

# Capture logcat for N seconds
capture_logcat() {
    local duration="${1:-10}"
    local output="${2:-/tmp/logcat_$(date +%s).log}"
    adb logcat -c
    adb logcat > "$output" &
    local PID=$!
    sleep "$duration"
    kill "$PID" 2>/dev/null || true
    log "Logcat saved: $output"
}

# Push + sync partition
push_and_sync() {
    local local_path="$1"
    local remote_path="$2"
    adb push "$local_path" "$remote_path"
    adb shell sync
}
```

---

## AOSP Build Helpers

```bash
# Source build environment
setup_aosp_env() {
    local aosp_root="${1:?AOSP root required}"
    [[ -f "$aosp_root/build/envsetup.sh" ]] || die "Not an AOSP tree: $aosp_root"
    # shellcheck source=/dev/null
    source "$aosp_root/build/envsetup.sh"
    lunch "${PRODUCT}-${VARIANT}"
}

# Build module with timing
build_module() {
    local module="$1"
    log "Building $module..."
    local start_ts; start_ts=$(date +%s)
    m "$module" 2>&1 | tee "${LOG_DIR}/${module}_build.log"
    local elapsed=$(( $(date +%s) - start_ts ))
    log "Built $module in ${elapsed}s"
}

# Check if out/ is stale (PRODUCT changed)
check_out_dir() {
    local out_product
    out_product="$(cat "${ANDROID_BUILD_TOP}/out/.product" 2>/dev/null || echo "")"
    if [[ "$out_product" != "$PRODUCT" ]]; then
        warn "out/ is from a different product ($out_product). Consider: make installclean"
    fi
}
```

---

## Process Management

```bash
# Run with timeout
run_with_timeout() {
    local timeout="$1"; shift
    timeout "$timeout" "$@" || die "Command timed out after ${timeout}s: $*"
}

# Run in background, track PID
start_serial_monitor() {
    minicom -D /dev/ttyUSB0 -b 115200 > "$LOG_DIR/serial.log" 2>&1 &
    SERIAL_PID=$!
    trap 'kill $SERIAL_PID 2>/dev/null' EXIT
    log "Serial monitor PID: $SERIAL_PID"
}

# Parallel builds (wait for all)
for module in "${MODULES[@]}"; do
    m "$module" &
done
wait  # wait for all background jobs
log "All modules built"
```

---

## CI/CD Patterns

```bash
# Detect CI environment
is_ci() { [[ "${CI:-false}" == "true" ]]; }

# Set output for different CI systems
set_ci_output() {
    local key="$1" value="$2"
    if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
        echo "${key}=${value}" >> "$GITHUB_OUTPUT"
    elif [[ -n "${GITLAB_CI:-}" ]]; then
        echo "${key}=${value}" | tee -a build.env
    fi
}

# Colored output (disable in CI)
if is_ci || [[ ! -t 1 ]]; then
    RED="" GREEN="" YELLOW="" RESET=""
else
    RED="\033[0;31m" GREEN="\033[0;32m" YELLOW="\033[1;33m" RESET="\033[0m"
fi

log()  { echo -e "${GREEN}[INFO]${RESET}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${RESET}  $*" >&2; }
die()  { echo -e "${RED}[ERROR]${RESET} $*" >&2; exit 1; }
```

---

## Prerequisites

- Bash 4.0+ (`bash --version` to verify).
- Standard GNU coreutils installed.
- For ADB scripts: Android Platform-Tools on PATH.
- `shellcheck` installed for linting (`apt install shellcheck` or `brew install shellcheck`).


## Step-by-Step Workflows

### Step 1: Create the script file
Add `#!/usr/bin/env bash` as the first line and `set -euo pipefail` as the second.

### Step 2: Parse arguments
Use `getopts` for short flags or a `case "$1"` block; validate all required arguments early.

### Step 3: Implement with functions
Use `main()` as the entry point called at the bottom; keep each function focused on one task.

### Step 4: Add error handling and traps
Use `trap 'cleanup' EXIT`; check return codes of commands that may fail silently.

### Step 5: Test and lint
Run `bash -n script.sh` (syntax check) and `shellcheck script.sh` (lint); fix all findings.


## Troubleshooting

- **`syntax error near unexpected token`** — check for Windows-style line endings (`\r\n`); convert with `dos2unix script.sh`.
- **Variable unexpectedly empty** — quote all expansions: `"$VAR"` not `$VAR`; use `${VAR:-default}` for safe defaults.
- **`command not found` in CI** — add the tool install path to `PATH` in the CI environment; use absolute paths for external tools.
- **Script exits silently** — `set -e` exits on first non-zero return; add `|| true` for commands where failure is acceptable.


## Pre-Commit Checklist

- [ ] `#!/usr/bin/env bash` shebang present.
- [ ] `set -euo pipefail` on line after shebang.
- [ ] All variables double-quoted: `"$VAR"`, `"${VAR}"`.
- [ ] No unquoted command substitutions: use `"$(cmd)"`.
- [ ] `readonly` on constants.
- [ ] `trap cleanup EXIT` used when temp files or background processes exist.
- [ ] `command -v` used to check required tools.
- [ ] No hardcoded absolute paths — use variables with documented defaults.
- [ ] Script tested with `bash -n script.sh` (syntax check) and `shellcheck script.sh`.

---

## References

- [Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [ShellCheck](https://www.shellcheck.net/)
- [Advanced Bash-Scripting Guide](https://tldp.org/LDP/abs/html/)
