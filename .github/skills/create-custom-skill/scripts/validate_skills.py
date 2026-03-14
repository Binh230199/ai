#!/usr/bin/env python3
"""
validate_skills.py — Audit all SKILL.md files for format compliance.

Usage:
    python validate_skills.py
    python validate_skills.py --fix-hints      # show suggested fixes inline
    python validate_skills.py --skills-dir /path/to/.github/skills
    python validate_skills.py --json           # machine-readable output

Exit code: 0 if all pass, 1 if any violations found.
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Rules configuration
# ---------------------------------------------------------------------------

# Required frontmatter fields (key, human description)
REQUIRED_FRONTMATTER = [
    ("name",        "frontmatter `name` field"),
    ("description", "frontmatter `description` field"),
]

# Required H2 sections (regex pattern, human label, severity)
# severity: "error" = must-have | "warning" = strongly recommended
REQUIRED_SECTIONS = [
    (r"^## When to Use",      "## When to Use This Skill",   "error"),
    (r"^## Prerequisites",    "## Prerequisites",             "warning"),
    (r"^## Step-by-Step",     "## Step-by-Step Workflows",   "warning"),
    (r"^## Troubleshooting",  "## Troubleshooting",          "warning"),
    (r"^## References",       "## References",               "warning"),
]

# Rules for frontmatter `name` field
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
NAME_MAX_LEN  = 64

# Rules for frontmatter `description` field
DESC_MAX_LEN  = 1024
DESC_TRIGGER  = re.compile(r"\bUse when\b", re.IGNORECASE)

# H1 title — every SKILL.md should have exactly one
H1_PATTERN = re.compile(r"^# .+", re.MULTILINE)

# ---------------------------------------------------------------------------
# Parser helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text). Frontmatter is the --- block."""
    fm: dict[str, str] = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm_raw = text[3:end].strip()
            body   = text[end + 4:].lstrip()
            # Naive YAML key parsing — handles scalar and folded `>` values
            current_key   = None
            current_lines: list[str] = []
            for line in fm_raw.splitlines():
                kv = re.match(r"^(\w[\w-]*):\s*(.*)", line)
                if kv:
                    if current_key:
                        fm[current_key] = " ".join(current_lines).strip()
                    current_key   = kv.group(1)
                    current_lines = [kv.group(2).strip().lstrip(">").strip()]
                elif current_key and line.startswith("  "):
                    current_lines.append(line.strip())
            if current_key:
                fm[current_key] = " ".join(current_lines).strip()
    return fm, body


def strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks (``` ... ```) so their content isn't checked for headings."""
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def h2_headings(body: str) -> list[str]:
    return re.findall(r"^(## .+)", strip_code_blocks(body), re.MULTILINE)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_skill(skill_dir: Path) -> list[dict]:
    """Return a list of issue dicts for one skill directory."""
    issues: list[dict] = []

    def issue(severity: str, code: str, message: str):
        issues.append({"severity": severity, "code": code, "message": message})

    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        issue("error", "MISSING_SKILL_MD", "SKILL.md not found in directory")
        return issues

    text = skill_file.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    # --- Frontmatter checks --------------------------------------------------

    # Required fields present
    for key, label in REQUIRED_FRONTMATTER:
        if key not in fm or not fm[key].strip():
            issue("error", f"FM_MISSING_{key.upper()}", f"Missing required {label}")

    # `name` field rules
    name_val = fm.get("name", "")
    if name_val:
        if not NAME_PATTERN.match(name_val):
            issue("error", "FM_NAME_INVALID",
                  f"`name` must be lowercase letters, digits, hyphens only: got '{name_val}'")
        if len(name_val) > NAME_MAX_LEN:
            issue("error", "FM_NAME_TOO_LONG",
                  f"`name` exceeds {NAME_MAX_LEN} characters ({len(name_val)})")
        if name_val != skill_dir.name:
            issue("error", "FM_NAME_DIR_MISMATCH",
                  f"`name` '{name_val}' does not match directory name '{skill_dir.name}'")

    # `description` field rules
    desc_val = fm.get("description", "")
    if desc_val:
        if len(desc_val) > DESC_MAX_LEN:
            issue("warning", "FM_DESC_TOO_LONG",
                  f"`description` exceeds {DESC_MAX_LEN} characters ({len(desc_val)})")
        if not DESC_TRIGGER.search(desc_val):
            issue("warning", "FM_DESC_NO_TRIGGER",
                  "`description` should start with 'Use when ...' to guide AI auto-loading")

    # --- Body checks ---------------------------------------------------------

    # H1 title — check on code-stripped body
    stripped_body = strip_code_blocks(body)
    h1_matches = H1_PATTERN.findall(stripped_body)
    if len(h1_matches) == 0:
        issue("error", "BODY_NO_H1", "No H1 title (# Title) found in body")
    elif len(h1_matches) > 1:
        issue("warning", "BODY_MULTIPLE_H1",
              f"Multiple H1 titles found ({len(h1_matches)}); only one expected")

    # Required H2 sections — search on stripped body
    for pattern, label, severity in REQUIRED_SECTIONS:
        if not re.search(pattern, stripped_body, re.MULTILINE):
            issue(severity, f"BODY_MISSING_{label.replace('## ', '').upper().replace(' ', '_')}",
                  f"Missing section: {label}")

    # No empty body (beyond just the title)
    non_blank_body_lines = [ln for ln in stripped_body.splitlines() if ln.strip()]
    if len(non_blank_body_lines) < 5:
        issue("warning", "BODY_TOO_SHORT",
              f"Body is very short ({len(non_blank_body_lines)} non-blank lines); likely incomplete")

    return issues


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

SEVERITY_COLOR = {
    "error":   "\033[91m",   # red
    "warning": "\033[93m",   # yellow
    "info":    "\033[94m",   # blue
}
RESET = "\033[0m"
BOLD  = "\033[1m"

def _c(text: str, code: str) -> str:
    """Colorize if stdout is a TTY."""
    if sys.stdout.isatty():
        return f"{code}{text}{RESET}"
    return text


def print_report(results: dict[str, list[dict]], fix_hints: bool) -> int:
    """Pretty-print results. Returns exit code (0=ok, 1=errors found)."""
    total_errors   = 0
    total_warnings = 0
    failed_skills: list[str] = []

    for skill_name, issues in sorted(results.items()):
        errors   = [i for i in issues if i["severity"] == "error"]
        warnings = [i for i in issues if i["severity"] == "warning"]
        total_errors   += len(errors)
        total_warnings += len(warnings)

        if not issues:
            print(f"  {_c('✓', SEVERITY_COLOR['info'])} {skill_name}")
            continue

        failed_skills.append(skill_name)
        print(f"\n  {_c('✗', SEVERITY_COLOR['error'])} {_c(skill_name, BOLD)}")
        for iss in issues:
            color  = SEVERITY_COLOR.get(iss["severity"], "")
            prefix = _c(f"    [{iss['severity'].upper():7}]", color)
            print(f"{prefix} {iss['code']}: {iss['message']}")

    print()
    print("─" * 60)
    summary_color = SEVERITY_COLOR["error"] if total_errors else (
                    SEVERITY_COLOR["warning"] if total_warnings else SEVERITY_COLOR["info"])
    print(_c(f"  {total_errors} error(s), {total_warnings} warning(s) "
             f"across {len(results)} skills", summary_color))

    if failed_skills and fix_hints:
        print()
        print(_c("  Fix hints:", BOLD))
        for s in failed_skills:
            print(f"    → Review: .github/skills/{s}/SKILL.md")

    return 1 if total_errors > 0 else 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate all SKILL.md files for format compliance."
    )
    parser.add_argument(
        "--skills-dir",
        default=None,
        help="Path to .github/skills directory (default: auto-detect from CWD)"
    )
    parser.add_argument(
        "--fix-hints",
        action="store_true",
        help="Print file paths for skills with issues"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of human-readable text"
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Suppress warnings, only report errors"
    )
    args = parser.parse_args()

    # Resolve skills directory
    if args.skills_dir:
        skills_root = Path(args.skills_dir).resolve()
    else:
        # Walk up from CWD looking for .github/skills
        cwd = Path.cwd()
        candidate = None
        for parent in [cwd, *cwd.parents]:
            p = parent / ".github" / "skills"
            if p.is_dir():
                candidate = p
                break
        if candidate is None:
            # Fallback: look for any 'skills' directory in cwd
            candidate = cwd
        skills_root = candidate

    if not skills_root.is_dir():
        print(f"ERROR: skills directory not found: {skills_root}", file=sys.stderr)
        return 2

    print(f"\n{_c('Scanning skills in:', BOLD)} {skills_root}\n")

    # Collect all skill directories (any immediate subdirectory)
    skill_dirs = sorted(
        d for d in skills_root.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )

    if not skill_dirs:
        print("No skill directories found.", file=sys.stderr)
        return 2

    results: dict[str, list[dict]] = {}
    for skill_dir in skill_dirs:
        issues = validate_skill(skill_dir)
        if args.errors_only:
            issues = [i for i in issues if i["severity"] == "error"]
        results[skill_dir.name] = issues

    if args.json:
        output = {
            "skills_dir": str(skills_root),
            "total_skills": len(results),
            "results": {
                name: issues for name, issues in results.items()
            },
            "summary": {
                "total_errors":   sum(len([i for i in v if i["severity"] == "error"])   for v in results.values()),
                "total_warnings": sum(len([i for i in v if i["severity"] == "warning"]) for v in results.values()),
                "passed":         sum(1 for v in results.values() if not v),
                "failed":         sum(1 for v in results.values() if v),
            }
        }
        print(json.dumps(output, indent=2))
        return 1 if output["summary"]["total_errors"] > 0 else 0

    return print_report(results, fix_hints=args.fix_hints)


if __name__ == "__main__":
    sys.exit(main())
