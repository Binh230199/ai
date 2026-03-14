---
name: lang-powershell-scripting
description: >
  Use when writing, reviewing, or debugging PowerShell scripts on Windows for
  embedded development workflows. Covers script structure, error handling, parameter binding,
  pipeline patterns, file operations, ADB automation from Windows, toolchain setup,
  Gerrit/Artifactory REST API calls, and CI/CD pipeline scripting (Jenkins, GitLab CI)
  for automotive IVI / HUD / RSE projects targeting Android Automotive / Linux / QNX.
argument-hint: <script-name> [write|review|debug]
---

# PowerShell Scripting — Windows Embedded Development

Expert practices for writing reliable, maintainable PowerShell scripts
that power embedded development workflows on **Windows 10/11** development machines
targeting **Android Automotive (AOSP)**, **Linux BSP**, and **QNX** platforms.

Standards baseline: **PowerShell 5.1** (Windows built-in) · **PowerShell 7+ (Core)** recommended for cross-platform use.

---

## When to Use This Skill

- Build automation from Windows (invoke WSL, Gradle, CMake, NDK).
- ADB scripting on Windows (flash devices, capture logs, push files).
- Setting up toolchain environment variables (NDK, SDK, JDK, Python).
- Calling Gerrit / Jira / Artifactory REST APIs.
- Parsing build logs, error reports, or test result XMLs.
- Writing Jenkins pipeline `powershell {}` steps.
- Automating code review, branch management, or dependency checks.

---

## Script Skeleton — Always Start Here

```powershell
#Requires -Version 5.1
<#
.SYNOPSIS
    Flash a built AOSP image to a connected ADB device.

.DESCRIPTION
    Waits for an ADB device, pushes partition images, and reboots.

.PARAMETER Product
    AOSP product name (e.g. aosp_car_x86_64).

.PARAMETER Variant
    Build variant: eng | userdebug | user. Default: userdebug.

.EXAMPLE
    .\Flash-Target.ps1 -Product aosp_car_x86_64 -Variant userdebug
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string] $Product  = $env:PRODUCT ?? 'aosp_car_x86_64',
    [ValidateSet('eng', 'userdebug', 'user')]
    [string] $Variant  = $env:VARIANT ?? 'userdebug',
    [string] $OutDir   = $env:ANDROID_PRODUCT_OUT ?? (Join-Path $PSScriptRoot 'out')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ---------- constants ----------
$SCRIPT_DIR  = $PSScriptRoot
$TIMESTAMP   = Get-Date -Format 'yyyyMMdd_HHmmss'
$LOG_FILE    = Join-Path $SCRIPT_DIR "flash_${TIMESTAMP}.log"

# ---------- logging ----------
function Write-Log  { param([string]$Msg) Write-Host "  [INFO] $Msg" }
function Write-Warn { param([string]$Msg) Write-Warning $Msg }
function Write-Fail { param([string]$Msg) { Write-Error "[ERROR] $Msg"; exit 1 } }

# ---------- main ----------
function Main {
    Write-Log "Flashing $Product ($Variant) from $OutDir"
    Assert-AdbDevice
    # ... implementation
}

Main
```

**Rules**
- `Set-StrictMode -Version Latest` catches uninitialized variables and typos.
- `$ErrorActionPreference = 'Stop'` turns non-terminating errors into terminating ones.
- Use `[CmdletBinding()]` so your script supports `-Verbose`, `-WhatIf`, `-Confirm`.
- `#Requires -Version 5.1` prevents accidental execution on old PowerShell.
- Prefer `param()` block with type annotations and `[ValidateSet]` over raw string checks.

---

## Error Handling

```powershell
# Try/Catch with specific exceptions
try {
    $result = Invoke-RestMethod -Uri $Uri -Headers $headers
} catch [System.Net.WebException] {
    Write-Warn "Network error: $($_.Exception.Message)"
    throw
} catch {
    Write-Error "Unexpected error: $_"
    exit 1
}

# Check exit codes from native commands (adb, gradle, etc.)
adb devices
if ($LASTEXITCODE -ne 0) {
    Write-Fail "adb command failed (exit $LASTEXITCODE)"
}

# Wrapper for native command error checking
function Invoke-Native {
    [CmdletBinding()]
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command '$Exe $Arguments' exited with code $LASTEXITCODE"
    }
}

# Example
Invoke-Native -Exe 'adb' -Arguments @('devices')
Invoke-Native -Exe 'gradle' -Arguments @('assembleDebug', '--no-daemon')
```

---

## Variables, Types, and Strings

```powershell
# Always use $null check correctly
if ($null -eq $Value)   { ... }  # correct — $null on left side
if ($null -ne $Value)   { ... }  # correct
if ($Value -eq $null)   { ... }  # works BUT risky with arrays — use $null -eq style

# Prefer -eq/-ne over == for safety
if ($Variant -eq 'user') { ... }

# Multi-line strings (here-string)
$JsonBody = @"
{
    "product": "$Product",
    "variant": "$Variant"
}
"@

# Path joining — always use Join-Path, never string concatenation
$OutApk  = Join-Path $OutDir 'app' 'build' 'outputs' 'apk' 'debug' 'app-debug.apk'

# Environment variables
$SdkRoot = $env:ANDROID_HOME ?? 'C:\Android\sdk'
$Adb     = Join-Path $SdkRoot 'platform-tools' 'adb.exe'
```

---

## Cmdlet vs Alias — Always Use Full Names

```powershell
# CORRECT — full cmdlet names
Get-ChildItem -Path $OutDir -Filter '*.apk' -Recurse
Where-Object   { $_.LastWriteTime -gt $CutoffDate }
Select-Object  -ExpandProperty Name
ForEach-Object { Install-Apk -Path $_ }
Remove-Item    -Path $TempDir -Recurse -Force

# WRONG — aliases break in non-interactive / CI contexts
ls, dir, gci     # → Get-ChildItem
?, where         # → Where-Object
select           # → Select-Object
%                # → ForEach-Object
rm, del          # → Remove-Item
```

---

## File Operations

```powershell
# Existence checks
if (-not (Test-Path $ConfigFile)) {
    Write-Fail "Config not found: $ConfigFile"
}

# Create directories
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

# Read a text file
$Lines = Get-Content -Path $LogFile -Encoding UTF8

# Write with encoding
$Lines | Set-Content -Path $OutputFile -Encoding UTF8

# Safe temp file
$TempFile = [System.IO.Path]::GetTempFileName()
try {
    # ... use $TempFile
} finally {
    Remove-Item -Path $TempFile -ErrorAction SilentlyContinue
}

# Find files matching pattern
Get-ChildItem -Path $OutDir -Filter '*.apk' -Recurse |
    Where-Object { $_.Length -gt 0 } |
    ForEach-Object { Install-Apk -Path $_.FullName }
```

---

## ADB Automation

```powershell
function Assert-AdbDevice {
    $devices = & adb devices 2>&1 | Select-String 'device$'
    if (-not $devices) {
        Write-Fail "No ADB device connected. Check USB and adb usb authorization."
    }
    Write-Log "ADB device found."
}

function Install-Apk {
    param(
        [Parameter(Mandatory)][string] $ApkPath,
        [int] $Retries = 3
    )
    if (-not (Test-Path $ApkPath)) { Write-Fail "APK not found: $ApkPath" }

    for ($i = 1; $i -le $Retries; $i++) {
        Write-Log "Installing $ApkPath (attempt $i)..."
        & adb install -r -t "$ApkPath"
        if ($LASTEXITCODE -eq 0) { Write-Log "Installed successfully."; return }
        Write-Warn "Attempt $i failed. Retrying..."
        Start-Sleep -Seconds 2
    }
    Write-Fail "Failed to install $ApkPath after $Retries attempts."
}

function Get-Logcat {
    param(
        [int]    $DurationSec = 10,
        [string] $OutputPath  = (Join-Path $PSScriptRoot "logcat_$(Get-Date -Format 'HHmmss').log")
    )
    & adb logcat -c
    $job = Start-Job { & adb logcat }
    Start-Sleep -Seconds $DurationSec
    Stop-Job $job
    Receive-Job $job | Set-Content -Path $OutputPath -Encoding UTF8
    Remove-Job $job
    Write-Log "Logcat saved: $OutputPath"
}
```

---

## REST API Calls (Gerrit / Jira / Artifactory)

```powershell
function Invoke-GerritQuery {
    param(
        [Parameter(Mandatory)][string] $GerritUrl,
        [Parameter(Mandatory)][string] $Query,
        [System.Management.Automation.PSCredential] $Credential
    )

    $headers = @{ 'Accept' = 'application/json' }
    if ($Credential) {
        $encoded = [Convert]::ToBase64String(
            [Text.Encoding]::ASCII.GetBytes(
                "$($Credential.UserName):$($Credential.GetNetworkCredential().Password)"
            )
        )
        $headers['Authorization'] = "Basic $encoded"
    }

    $uri = "${GerritUrl}/a/changes/?q=${Query}&o=CURRENT_REVISION"
    $raw = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get
    # Gerrit prepends ')]}\' — strip it when using Invoke-WebRequest
    return $raw
}

# Upload artifact to Artifactory
function Publish-Artifact {
    param(
        [string] $ArtifactoryUrl,
        [string] $RepoPath,
        [string] $LocalFile,
        [System.Management.Automation.PSCredential] $Credential
    )
    $uri = "${ArtifactoryUrl}/${RepoPath}/$(Split-Path $LocalFile -Leaf)"
    Invoke-RestMethod -Uri $uri -Method Put -InFile $LocalFile -Credential $Credential
    Write-Log "Uploaded: $uri"
}
```

---

## WSL / Linux Interop

```powershell
# Run an AOSP build inside WSL from Windows
function Invoke-AospBuild {
    param([string] $AospRoot, [string] $Target = 'droid')
    $wslPath = $AospRoot -replace '\\', '/' -replace '^([A-Za-z]):', '/mnt/$1'.ToLower()
    wsl bash -c "cd '$wslPath' && source build/envsetup.sh && lunch ${Product}-${Variant} && m $Target"
    if ($LASTEXITCODE -ne 0) { Write-Fail "AOSP build failed." }
}

# Convert Windows path to WSL path
function ConvertTo-WslPath {
    param([string] $WindowsPath)
    $drive = $WindowsPath[0].ToString().ToLower()
    $rest  = $WindowsPath.Substring(2) -replace '\\', '/'
    return "/mnt/${drive}${rest}"
}
```

---

## CI/CD Patterns (Jenkins / GitLab)

```powershell
# Detect CI environment
function Test-CIEnvironment { return ($null -ne $env:CI) -or ($null -ne $env:JENKINS_URL) }

# Export variable for subsequent Jenkins stages
function Set-BuildProperty {
    param([string] $Key, [string] $Value)
    if ($env:JENKINS_URL) {
        Add-Content -Path 'build.properties' -Value "${Key}=${Value}"
    }
}

# Progress output visible in CI logs
function Write-Progress-CI {
    param([string] $Activity, [string] $Status)
    Write-Host "##[section]${Activity}: ${Status}"  # Azure DevOps / Jenkins
}

# Retry with exponential backoff (useful for flaky network calls)
function Invoke-WithRetry {
    param([scriptblock] $ScriptBlock, [int] $MaxRetries = 3, [int] $DelaySeconds = 5)
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try { return & $ScriptBlock }
        catch {
            if ($i -eq $MaxRetries) { throw }
            Write-Warn "Attempt $i failed: $($_.Exception.Message). Retrying in ${DelaySeconds}s..."
            Start-Sleep -Seconds $DelaySeconds
            $DelaySeconds *= 2
        }
    }
}
```

---

## Credential Safety

```powershell
# NEVER hardcode credentials
# $password = "myp@ssw0rd"  # FORBIDDEN

# Read from environment (set by CI secret or keychain)
$ApiToken = $env:GERRIT_API_TOKEN ?? (Read-Host 'Gerrit API Token' -AsSecureString | ConvertFrom-SecureString -AsPlainText)

# Use PSCredential for API calls
$securePass = ConvertTo-SecureString $ApiToken -AsPlainText -Force
$cred = [System.Management.Automation.PSCredential]::new('token', $securePass)
```

---

## Prerequisites

- PowerShell 5.1+ (Windows built-in) or PowerShell 7+ (cross-platform).
- [PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer) installed: `Install-Module PSScriptAnalyzer`.
- For ADB automation: Android Platform-Tools on PATH.
- API tokens stored in environment variables or a secrets manager — never hardcoded.


## Step-by-Step Workflows

### Step 1: Create the script file
Add `#Requires -Version 5.1` and `[CmdletBinding()]` at the top.

### Step 2: Define parameters with `param()` block
Mark required params with `[Parameter(Mandatory)]`; add `[ValidateSet(...)]` where appropriate.

### Step 3: Implement with `$ErrorActionPreference = 'Stop'`
Ensure unhandled errors terminate the script; use `try/catch` for recoverable errors.

### Step 4: Return structured output via the pipeline
Use `Write-Output` (not `Write-Host`) for pipeline-compatible output; return objects, not strings.

### Step 5: Lint with PSScriptAnalyzer
Run `Invoke-ScriptAnalyzer -Path script.ps1 -Severity Warning,Error`; fix all findings.


## Troubleshooting

- **`Execution of scripts is disabled`** — run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`; or use `-ExecutionPolicy Bypass` in CI pipelines.
- **Encoding issues with special characters** — save scripts as UTF-8 BOM; add `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` at the top.
- **`$null -eq $obj` vs `$obj -eq $null`** — always put `$null` on the left side to avoid unexpected behavior with collections.
- **Pipeline drops objects** — use `Write-Output` (pipeline-compatible) instead of `Write-Host` (host display only) for function return values.


## Pre-Commit Checklist

- [ ] `#Requires -Version 5.1` at top.
- [ ] `Set-StrictMode -Version Latest` and `$ErrorActionPreference = 'Stop'` set.
- [ ] `[CmdletBinding()]` on scripts that would benefit from `-WhatIf`/`-Verbose`.
- [ ] `param()` block with type annotations and `[ValidateSet]` where applicable.
- [ ] Native command exit codes checked via `$LASTEXITCODE`.
- [ ] Full cmdlet names used (no aliases like `ls`, `%`, `?`).
- [ ] `Join-Path` used for all path construction.
- [ ] No credentials hardcoded — read from `$env:*` or prompt with `Read-Host -AsSecureString`.
- [ ] `finally` blocks used to clean up temp files.
- [ ] Script tested with `Invoke-ScriptAnalyzer .\script.ps1 -Severity Error`.

---

## References

- [PowerShell Documentation](https://learn.microsoft.com/en-us/powershell/)
- [PowerShell Best Practices and Style Guide](https://poshcode.gitbook.io/powershell-practice-and-style/)
- [PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer)
- [ADB command reference](https://developer.android.com/tools/adb)
