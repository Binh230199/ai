# GitHub Copilot – Cẩm Nang Agentic AI Toàn Diện
### Dành cho Embedded Software Engineer trong ngành Automotive

---

## Mục Lục

1. [Bức Tranh Toàn Cảnh – Từ Prompt đến Agentic](#1)
2. [Các Điểm Truy Cập Chat trong VS Code](#2)
3. [4 Chế Độ Agent: Ask / Plan / Agent / Custom](#3)
4. [Customization Layer – Toàn Bộ Cơ Chế Tùy Biến](#4)
   - 4.1 Custom Instructions (`copilot-instructions.md`)
   - 4.2 Path-Specific Instructions
   - 4.3 Prompt Files (Slash Commands)
   - 4.4 **Agent Skills** ⭐ Open Standard
   - 4.5 Custom Agents (`.agent.md`) + Handoffs
   - 4.6 Hooks – Deterministic Lifecycle Automation
   - 4.7 AGENTS.md
   - 4.8 Tool Sets
5. [MCP Servers – "Tay Chân" Kết Nối Thế Giới Bên Ngoài](#5)
6. [Tools – Vũ Khí Bên Trong Agent](#6)
7. [Subagents & Agent Orchestration](#7)
8. [Background Agents – Chạy Ngầm Không Cần Giám Sát](#8)
9. [Bài Toán 100 / 1000 Issues: Chiến Lược Xử Lý Hàng Loạt](#9)
10. [MCP Servers Thực Tế Cho Automotive Engineer](#10)
11. [Setup Cấu Trúc File Hoàn Chỉnh](#11)
12. [Quy Trình Tối Ưu Theo Từng Công Việc](#12)
13. [Tổng Kết – Ma Trận Khả Năng & Lộ Trình](#13)

---

## 1. Bức Tranh Toàn Cảnh {#1}

### Ba Tầng Tiến Hoá

```
[Level 1] Prompting       → Bạn hỏi, Copilot trả lời. Một chiều, thụ động.
                             Bạn vẫn phải làm phần lớn công việc sau đó.

[Level 2] Context-Aware   → Copilot hiểu codebase, custom instructions.
                             Trả lời đúng ngữ cảnh project, coding standard.

[Level 3] Agentic         → Copilot tự lập kế hoạch, thực thi nhiều bước,
                             dùng tools, gọi APIs bên ngoài, spawn subagents,
                             tự sửa lỗi, chạy nền – không cần bạn trực tiếp.
```

### Vòng Lặp Agentic – Điều Thực Sự Làm Cho AI "Tự Động"

Điểm then chốt khác biệt Agent với Chatbot thông thường là **vòng lặp tự điều chỉnh**:

```
User Prompt
     │
     ▼
  [Plan]  Copilot lập kế hoạch các bước cần làm
     │
     ▼
 [Execute] Dùng tools: đọc file, chạy terminal, gọi MCP, sửa code
     │
     ▼
 [Observe] Đọc kết quả: build output, test results, error messages
     │
     ▼
 [Replan]  Nếu thất bại → điều chỉnh kế hoạch → Execute lại
     │
     ▼
  [Done]  Khi tất cả bước pass → báo cáo kết quả cho user
```

Copilot không chỉ "gợi ý" – nó **tự hành động**:
- Đọc 10 file liên quan trước khi viết dòng code đầu
- Chạy `python build.py` sau khi sửa → đọc lỗi → tự fix → build lại
- Gọi Jira API để đọc ticket → implement → cập nhật ticket status
- Spawn 4 subagent review song song, mỗi cái focus một góc độ
- Chạy nền trong Git worktree, bạn tiếp tục làm việc khác

---

## 2. Các Điểm Truy Cập Chat trong VS Code {#2}

```
┌─────────────────────────────────────────────────────────┐
│  Chat View (Ctrl+Alt+I)  – Multi-turn, agents, tools    │
│  Inline Chat (Ctrl+I)    – In-place trong editor        │
│  Quick Chat (Ctrl+Shift+Alt+L) – Popup nhanh            │
│  Terminal Chat           – Gợi ý lệnh terminal          │
│  Command Line (code chat) – Từ ngoài VS Code            │
└─────────────────────────────────────────────────────────┘
```

### Chat View (Ctrl+Alt+I) – Trung Tâm Chính

Đây là nơi chứa tất cả agentic features. Có thể mở dưới dạng:
- Sidebar panel (mặc định)
- Editor tab (drag & drop ra)
- Cửa sổ riêng tách biệt

**Khi agent đang chạy, bạn có 3 lựa chọn tiếp theo:**

| Nút/Action | Ý nghĩa |
|-----------|---------|
| **Add to Queue** | Message mới chờ, tự gửi sau khi response hiện tại xong |
| **Steer with Message** | Điều hướng agent ngay (yield request hiện tại) |
| **Stop and Send** | Dừng request hiện tại, gửi message mới ngay |
| **Continue in Background** | Đẩy sang Background Agent, bạn làm việc tiếp |

### Inline Chat (Ctrl+I) – Nhanh, Tại Chỗ

Kích hoạt ngay trong editor. Dùng cho:
- Giải thích đoạn code đang chọn
- Refactor một hàm
- Fix lỗi compiler tại chỗ
- Thêm Doxygen comment

```
// Chọn ISR handler → Ctrl+I
"Explain this ISR and check for MISRA C:2012 violations"

// Chọn hàm → Ctrl+I
"Refactor to extract the validation logic into a separate function"
```

---

## 3. Bốn Chế Độ Agent {#3}

Nhìn vào dropdown trong Chat View:

```
┌─────────────────────────┐
│  ▼ Agent                │  ← Chế độ mạnh nhất
│  ▼ Ask                  │
│  ≡ Plan                 │  ← Bạn có thể đã bỏ qua cái này
│  Configure Custom Agents│  ← Tạo persona riêng của bạn
└─────────────────────────┘
```

### 3.1 Ask Mode – Nghiên Cứu Không Rủi Ro

Ask có agentic capability để research codebase nhưng **KHÔNG tự sửa file**.
Đây là mode an toàn nhất.

```
// Context variables hữu ích trong Ask:
#codebase         → Toàn bộ workspace
#file:path/to/x.c → File cụ thể
#selection        → Đoạn đang select
#sym:FunctionName → Symbol cụ thể
#problems         → Danh sách errors/warnings hiện tại
#terminalLastCommand → Output lệnh terminal vừa chạy
#fetch URL        → Nội dung từ URL (docs, specs)
```

**Dùng cho:** Hiểu code, phân tích kiến trúc, brainstorm giải pháp,
investigate bug, onboarding module mới.

```
"Where is the CAN receive buffer overflow handled? #codebase"
"Explain the state machine in BCM_LightControl.c #file:src/swc/BCM_LightControl.c"
"What MISRA rules are most commonly violated in #file:src/bsw/can/BCM_CAN.c"
```

### 3.2 Plan Mode ⭐ – Suy Nghĩ Trước Khi Code

Plan agent được thiết kế để **lập kế hoạch chi tiết trước khi viết bất kỳ
dòng code nào**. Đặc biệt quan trọng trong automotive nơi một sai sót thiết kế
tốn kém hơn nhiều so với sai lỗi code.

**Luồng hoạt động thực tế:**

```
1. Bạn describe feature/task ở high level
       ↓
2. Plan agent tự động spawn SUBAGENTS để research song song:
   - Subagent A: Phân tích codebase hiện tại
   - Subagent B: Tìm các module tương tự làm reference
   - Subagent C: Check requirements/ARXML definitions
       ↓
3. Plan agent hỏi bạn các câu clarifying questions
       ↓
4. Bạn trả lời → Plan agent tạo kế hoạch từng bước có thể review
       ↓
5. Bạn chỉnh sửa kế hoạch nếu cần
       ↓
6. Click "Start Implementation"
       → Option A: Agent Mode (tương tác, immediate)
       → Option B: Continue in Background (tự chạy, bạn làm việc khác)
```

```
[Plan Mode]
"Implement LIN bus slave node for BCM window motor control.
 The node must handle window up/down commands, report position feedback,
 support stall detection per LIN spec 2.2A.
 Check how the existing CAN module is structured as reference."
```

→ Plan agent research code, hỏi: "Có GPIO driver sẵn không? Driver layer
đang dùng abstraction nào? AUTOSAR LIN stack hay custom?"
→ Bạn trả lời → Plan tạo kế hoạch 9 bước với file list cụ thể
→ Review → Start Implementation

### 3.3 Agent Mode ⭐⭐ – Quan Trọng Nhất

Agent tự quyết định tất cả: đọc file nào, chạy lệnh gì, dùng tool gì.
**Lặp vòng lặp** (plan → execute → observe → replan) cho đến khi task xong.

**Built-in tools Agent có thể dùng:**

| Tool | Chức năng |
|------|----------|
| `editFiles` | Sửa nhiều file cùng lúc |
| `runInTerminal` | Chạy build, test, linting |
| `search` | Tìm kiếm trong codebase (semantic + text) |
| `read` | Đọc file bất kỳ |
| `fetch` | Gọi URL/API |
| `problems` | Đọc danh sách errors/warnings từ Problems panel |
| `usages` | Tìm tất cả nơi dùng một symbol |
| `runSubagent` | Spawn subagent độc lập với context window riêng |
| `changes` | Xem staged/unstaged changes |

**Terminal management trong Agent Mode:**
- Long-running commands có thể **push to background** (ví dụ: build watch mode)
- Agent chạy trong PowerShell/bash với shell integration đầy đủ
- Bạn có thể xem output inline trong chat hoặc mở terminal riêng
- Agent terminals hiển thị với chat icon trong terminals list

```
[Agent Mode – ví dụ multi-step thực tế]
"Implement the engine speed signal processing module per:
 Requirements: #file:requirements/ENGINE_SPEED_REQ.md
 Interface: #file:config/arxml/BCM_Interfaces.arxml
 Reference: #file:src/swc/BCM_FuelSensor.c

 After implementation:
 - Run MISRA analysis and fix all Mandatory/Required violations
 - Write unit tests with 100% MC/DC coverage
 - Run tests and fix any failures
 - Update module Doxygen documentation"
```
→ Agent TỰ: đọc 3 file → phân tích → viết code → viết test → build → chạy test
→ đọc lỗi → fix → build lại → chạy MISRA → fix violations → loop cho đến xong

### 3.4 Custom Agents – Persona Chuyên Biệt

Xem chi tiết đầy đủ tại [phần 4.5](#45-custom-agents).

**Quick start:** Gõ `/agents` trong chat → Configure Custom Agents → Create.

---

## 4. Customization Layer {#4}

Đây là bộ "DNA" bạn cài vào cho Copilot hiểu project. Tầng càng hoàn chỉnh,
output càng chính xác, bạn cần prompt càng ít.

```
Quick Reference – Dùng cái gì cho mục đích gì:
────────────────────────────────────────────────────────────────────
Mục tiêu                          Dùng
────────────────────────────────────────────────────────────────────
Standards áp dụng MỌI lúc         copilot-instructions.md
Rules theo file type/layer        *.instructions.md (path-specific)
Task hay làm, cần gọi lại         *.prompt.md (Prompt Files / Slash cmd)
Workflow có scripts/resources     SKILL.md (Agent Skills) ⭐ PORTABLE
Persona chuyên biệt + tool ctrl   *.agent.md (Custom Agents)
Automation tại lifecycle events   hooks/*.json
Guide cho background/coding agent AGENTS.md
Nhóm tools hay dùng cùng nhau     toolsets.jsonc (Tool Sets)
────────────────────────────────────────────────────────────────────
```

### 4.1 Custom Instructions (`copilot-instructions.md`)

**File:** `.github/copilot-instructions.md`

Tự động đính kèm vào **mọi** request. DNA chính của project.

**Khởi tạo nhanh bằng AI:** Gõ `/init` trong chat → Copilot tự phân tích
workspace và tạo file này, bạn chỉ cần review + chỉnh.

**Ví dụ đầy đủ cho AUTOSAR Automotive Embedded:**

```markdown
# Project: BCM (Body Control Module) – AUTOSAR Classic CP

## Architecture Overview
- AUTOSAR Classic CP stack on Renesas RH850/F1KM (160MHz, 4MB Flash, 384KB RAM)
- Compiler: GHS Multi v7.1.6 | MISRA C:2012 compliance mandatory
- Coding standard: AUTOSAR C++14 Guidelines where applicable
- RTOS: AUTOSAR OS (OSEK-based), 1ms base tick

## Directory Structure
- src/swc/    → Software Components (RTE-connected)
- src/bsw/    → Basic Software (CAN, LIN, ADC drivers)
- src/rte/    → Generated RTE code (DO NOT modify manually)
- generated/  → ARXML-generated code (DO NOT modify manually)
- test/       → Unit tests (GoogleTest framework)
- config/     → ARXML, DBC, LDF configuration files

## Code Conventions
- Functions: Doxygen comment block required (@brief, @param, @return, @note)
- Error handling: Std_ReturnType (E_OK / E_NOT_OK) – never raw int/bool
- Memory: NO dynamic allocation (no malloc/free/new/delete), static only
- Include guards: BCM_<MODULE>_<FILE>_H format
- Naming: PascalCase types/structs, UPPER_SNAKE macros, camelCase locals
- Module prefix: BCM_ for all module-level symbols/functions

## Build & Test Commands
- Build Release:   python build.py --target BCM --config Release
- Build Debug:     python build.py --target BCM --config Debug
- Unit Tests:      python build.py --target BCM_TEST && python run_tests.py
- MISRA Analysis:  python run_misra.py --module <module_name>
- Full check:      python ci_check.py (build + test + misra + coverage)

## Critical Rules
- NEVER modify files in generated/ or src/rte/ — regenerate with: python gen_code.py
- ALWAYS check E_NOT_OK in every Rte_Call_*, Rte_Read_*, Rte_Write_* call
- CAN signals follow DBC naming: can/BCM_BCM.dbc
- LIN signals follow LDF naming: lin/BCM_LIN.ldf
- Det_ReportError() MUST be called for all development errors

## Key Configuration Files
- SWC ports: config/arxml/BCM_Interfaces.arxml
- Memory map: config/BCM_MemMap.h
- Module config: config/BCM_Cfg.h
- OS config: config/OS_Cfg.h
```

**Enable/disable:**
- `Ctrl+,` → tìm "instruction file" → toggle checkbox

### 4.2 Path-Specific Instructions

**Files:** `.github/instructions/*.instructions.md`

Áp dụng rules **khác nhau** cho từng layer. Dùng `applyTo` glob pattern.
Nếu cả repo-wide và path-specific đều match → cả hai được dùng.

**Tùy chọn `excludeAgent`:** Ngăn agent cụ thể dùng instructions này.
- `excludeAgent: "code-review"` → Chỉ coding agent dùng
- `excludeAgent: "coding-agent"` → Chỉ code review dùng

```markdown
<!-- .github/instructions/swc.instructions.md -->
---
applyTo: "src/swc/**/*.c,src/swc/**/*.h"
---
# SWC Layer Rules
- All Rte_Call_*, Rte_Read_*, Rte_Write_* MUST check return value
- Use RTE_E_OK / RTE_E_LOST_COMMUNICATION, NOT plain E_OK for RTE codes
- Port interfaces must exactly match ARXML definition in config/arxml/
- No direct hardware register access — always via HAL abstraction
- Maximum cyclomatic complexity: 10 per function
- No function longer than 60 lines (including comments)
```

```markdown
<!-- .github/instructions/bsw.instructions.md -->
---
applyTo: "src/bsw/**/*.c,src/bsw/**/*.h"
---
# BSW Layer Rules
- Follow AUTOSAR BSW Module SWS specifications exactly
- Det_ReportError() mandatory for all development errors (module ID, instance, API, error)
- SchM_Enter_<Module>_<ExclusiveArea>() / SchM_Exit_*() must always be paired
- Module init state machine: UNINIT → INIT only (no re-init without DeInit)
- All ISRs must be declared with OS ISR categories
```

```markdown
<!-- .github/instructions/tests.instructions.md -->
---
applyTo: "test/**/*.c,test/**/*.cpp"
---
# Unit Test Conventions
- Framework: GoogleTest v1.14 + FakeIt for mocking
- One test file per source module: test/BCM_<Module>_test.cpp
- Stubs for external dependencies in test/stubs/ (auto-generated by python gen_stubs.py)
- Test naming: TEST(<ModuleName>_<FunctionName>, <Scenario>_<ExpectedBehavior>)
- Coverage target: 100% statement + 100% MC/DC for safety-relevant functions
- All tests must be deterministic (no timing dependencies, no random)
```

```markdown
<!-- .github/instructions/code-review.instructions.md -->
---
applyTo: "**/*.c,**/*.h"
excludeAgent: "coding-agent"
---
# Code Review Checklist – Automotive Embedded

## SAFETY (Block-level – must fix before merge)
- Array accesses have bounds checking or provably safe size
- No undefined behavior: overflow, null deref, out-of-bounds
- Volatile used correctly for hardware registers and ISR-shared vars
- SchM_Enter/Exit pairs balanced; no early returns inside critical sections
- No implicit trust of external input (CAN signals, LIN messages)

## AUTOSAR COMPLIANCE
- Det_ReportError called for every development error
- All RTE return values checked with if/switch
- No direct OS API calls outside of OS abstraction layer

## MISRA C:2012
- No implicit type conversions (Rule 10.1–10.8)
- No dead code paths remain after fixing (Rule 2.1, 2.2)
- All switch statements have explicit default case (Rule 16.4)
- No dynamic memory (Rule 21.3)

## CODE QUALITY
- No magic numbers — use named constants or #defines
- Single responsibility per function
- Cyclomatic complexity < 10

Report format: [SEVERITY] Rule/Standard: <detail> | <file>:<line>
SEVERITY levels: BLOCKER | MAJOR | MINOR | INFO
```

### 4.3 Prompt Files (Slash Commands)

**Files:** `.github/prompts/*.prompt.md`

Reusable prompts cho tasks lặp lại. Xuất hiện như slash commands khi gõ `/`
trong chat. Có thể reference files và context variables.

**Enable:**
```json
// .vscode/settings.json
{ "chat.promptFiles": true }
```

**Invoke:** Paperclip icon → Prompt... → chọn file, hoặc gõ `/` → chọn từ list.

```markdown
<!-- .github/prompts/review-misra.prompt.md -->
# MISRA C:2012 Review

Perform a comprehensive MISRA C:2012 review.

Check for violations including:
- Rule 10.x: Type conversions and implicit casts
- Rule 14.4: Controlling expression of if/while must be Boolean
- Rule 15.5: Single point of exit per function
- Rule 16.4: Every switch must have default
- Rule 17.x: Function pointer and parameter issues
- Rule 21.x: Standard library restrictions

For EACH violation found:
1. Rule number + category (Mandatory / Required / Advisory)
2. Exact code location and the problematic snippet
3. Why it violates the rule
4. Corrected code

Reference: #file:docs/MISRA_C_2012_Guidelines.md
Code: #selection
```

```markdown
<!-- .github/prompts/write-unit-test.prompt.md -->
# Generate Unit Tests

Generate comprehensive unit tests for the selected module.

Framework: GoogleTest + FakeIt
Stubs location: test/stubs/ (use python gen_stubs.py to regenerate if needed)

Coverage requirements:
- 100% statement coverage
- 100% MC/DC for all safety-relevant functions (suffixed _SR)
- All error paths (E_NOT_OK returns from RTE calls)
- Boundary values for all numeric parameters
- NULL pointer handling where applicable

For each test:
- Arrange: setup mocks and stubs
- Act: call the function under test
- Assert: verify return value AND side effects (port writes, Det calls)

Module to test: #selection or #file as specified
Test file template: #file:test/BCM_Template_test.cpp
```

```markdown
<!-- .github/prompts/generate-release-notes.prompt.md -->
# Generate Release Notes

Generate professional release notes for the current release.

Steps:
1. Use Jira MCP: get all tickets in the current fix version
2. Group by type: New Features | Bug Fixes | Improvements | Breaking Changes
3. Get git log: commits between last tag and HEAD
4. Cross-reference: match commit hashes to Jira ticket IDs
5. Filter: exclude internal/infra tickets (label: internal)
6. Format using template: #file:docs/release-notes-template.md
7. Create/update Confluence page in BCM/Release-Notes/ space

Version: (will be asked)
```

### 4.4 Agent Skills ⭐ – Open Standard (Ít Ai Biết)

**Files:** `.github/skills/<skill-name>/SKILL.md`

**Agent Skills là gì và tại sao khác với Prompt Files?**

| | Custom Instructions | Prompt Files | **Agent Skills** |
|--|--|--|--|
| Load khi nào | **Luôn luôn** | Khi bạn gọi | **On-demand, TỰ ĐỘNG khi relevant** |
| Nội dung | Instructions | Instructions | **Instructions + Scripts + Resources** |
| Portable | VS Code only | VS Code only | **VS Code + CLI + Coding Agent** |
| Standard | VS Code-specific | VS Code-specific | **Open standard (agentskills.io)** |
| Invoke | Tự động | Slash command `/` | Slash command `/` + **tự động** |

**Cơ chế 3 cấp tải (Progressive Disclosure):**
```
Level 1 – Discovery: Copilot luôn biết skill có tồn tại qua name + description
          (lightweight metadata, không tốn context)
          ↓
Level 2 – Loading: Khi request match description → Copilot load body của SKILL.md
          (chỉ khi relevant)
          ↓
Level 3 – Resource Access: Copilot đọc scripts, examples, docs trong skill folder
          (chỉ khi thực sự cần)
```

→ Bạn có thể cài 50 skills mà không lo context bloat.

**Tạo skill MISRA Fix:**

```bash
mkdir -p .github/skills/misra-fix
```

```markdown
<!-- .github/skills/misra-fix/SKILL.md -->
---
name: misra-fix
description: Fix MISRA C:2012 violations in automotive embedded C code targeting
             Renesas RH850. Use when asked to fix MISRA issues, static analysis
             violations, or improve coding standard compliance.
argument-hint: "[module-name] [rule-category: mandatory|required|advisory]"
---

# MISRA C:2012 Fix Skill

## Context
Automotive AUTOSAR Classic codebase. Compiler: GHS Multi v7.1.6.
Target: Renesas RH850/F1KM. MISRA tool: see misra-output-format.md.

## Process
1. Run: `python run_misra.py --module <module> --format json`
2. Parse output per format: [misra-output-format.md](./misra-output-format.md)
3. Group violations: Mandatory → Required → Advisory
4. Fix Mandatory first (block compliance), then Required
5. For each fix:
   - Preserve EXACT functional behavior
   - Add inline comment: /* MISRA C:2012 Rule X.Y: <brief justification> */
   - If fix is non-trivial, add /* MISRA DEVIATION: rule X.Y reason: ... */
6. Re-run analysis: verify fix count decreases, no new violations introduced
7. Run unit tests: fixes must not break existing tests

## Common Fix Patterns
See: [common-misra-fixes.c](./common-misra-fixes.c)

## Rules Requiring Human Review (NEVER fix automatically)
- Rule 1.3: Undefined behavior – always escalate to senior engineer
- Rule 17.3: Implicit function declarations
- Any violation in generated/ or src/rte/ – report only, do not fix
```

Thêm resources:
```
.github/skills/misra-fix/
    SKILL.md
    misra-output-format.md    ← Format output của MISRA tool cụ thể
    common-misra-fixes.c      ← Ví dụ fix patterns với before/after
    rule-severity-table.csv   ← Table phân loại Mandatory/Required/Advisory
```

**Skills nên tạo cho Automotive team:**
```
.github/skills/
├── misra-fix/              Fix MISRA C:2012 violations
├── autosar-swc-gen/        Generate AUTOSAR SWC từ ARXML + requirements
├── unit-test-gen/          Generate unit tests MC/DC automotive standard
├── traceability-check/     Check requirements → code → test linkage
├── can-dbc-validate/       Validate DBC file consistency với code
├── lin-ldf-validate/       Validate LDF vs LIN stack configuration
├── release-notes/          Generate release notes tự động
└── bug-triage/             Analyze ECU crash dumps và core dumps
```

**Invoke:**
```
/misra-fix BCM_CAN.c required
```
Hoặc Copilot tự động load khi bạn viết "fix the MISRA issues in this file".

**Shared skills community:**
- [github/awesome-copilot](https://github.com/github/awesome-copilot)
- [anthropics/skills](https://github.com/anthropics/skills)

### 4.5 Custom Agents (`.agent.md`) + Handoffs

**Files:** `.github/agents/*.agent.md`

Custom agents là **AI persona chuyên biệt** với tools riêng, model riêng,
instructions riêng. Xuất hiện trong dropdown cạnh Ask/Plan/Agent.

**Cấu trúc frontmatter đầy đủ:**

```markdown
---
name: Agent Name                    # Tên hiện trong dropdown
description: What this agent does   # Placeholder text trong chat input
tools: ['read', 'search', 'edit']   # Chỉ những tools này được phép
agents: ['Subagent A', 'Subagent B'] # Allowed subagents (* = all, [] = none)
model: claude-sonnet-4-6            # Model cụ thể
user-invokable: true                # Có hiện trong dropdown không
disable-model-invocation: false     # Ngăn agent khác spawn cái này
handoffs:
  - label: "→ Start Implementation"
    agent: implementer-agent
    prompt: "Implement the plan above."
    send: false                     # false = pre-fill, user review trước
    model: GPT-5.2 (copilot)
---

Body: instructions cho agent...
```

**Ví dụ Custom Agents thực tế:**

```markdown
<!-- .github/agents/misra-reviewer.agent.md -->
---
name: MISRA Reviewer
description: MISRA C:2012 compliance review – read-only, no code changes
tools: ['read', 'search', 'usages', 'problems']
model: claude-sonnet-4-6
handoffs:
  - label: "→ Fix Violations"
    agent: MISRA Fixer
    prompt: "Fix all Mandatory and Required violations found in the review."
    send: false
---

You are a strict MISRA C:2012 compliance reviewer for automotive embedded code.

## Role
Review ONLY. Do NOT modify any files (you have no edit tools).

## Output Format
For each violation:
`[MANDATORY|REQUIRED|ADVISORY] Rule X.Y: <description>`
`  File: <path>:<line>`
`  Code: <snippet>`
`  Fix:  <suggested correction>`

## Escalation
- Any Mandatory violation → flag as BLOCKER, do not approve
- Rule 1.3 violations → flag as SAFETY CRITICAL, require senior review
```

```markdown
<!-- .github/agents/automotive-tdd.agent.md -->
---
name: Automotive TDD
description: Test-driven development for AUTOSAR C modules
tools: ['agent']
agents: ['TDD Red', 'TDD Green', 'TDD Refactor', 'MISRA Reviewer']
handoffs:
  - label: "→ Review Results"
    agent: MISRA Reviewer
    prompt: "Review the TDD implementation for MISRA compliance."
    send: true
---

Implement features using Test-Driven Development:

1. Use **TDD Red** subagent: write FAILING tests only (no implementation)
   - Human reviews tests before continuing
2. Use **TDD Green** subagent: write MINIMAL code to make tests pass
3. Use **TDD Refactor** subagent: clean up while keeping tests green
4. Run MISRA Reviewer to verify compliance
5. Loop steps 2-4 until: all tests pass + no MISRA violations + coverage met
```

**Handoffs – Guided Workflows Giữa Agents:**

Handoff buttons xuất hiện sau response và cho phép transition sang agent khác
với context đầy đủ:

```
[Plan Agent response xong]
┌─────────────────────────────────┐
│  → Start Implementation         │  ← Handoff button
│  → Review with MISRA Reviewer   │  ← Handoff button
└─────────────────────────────────┘
```

**Quick create:** Gõ `/agents` trong chat để mở Configure Custom Agents menu.

**Chia sẻ agents với team:** Custom agents trong `.github/agents/` được share
qua git. Agents trong user profile thì dùng được trên mọi workspace.

### 4.6 Hooks – Deterministic Lifecycle Automation (Preview)

**Files:** `.github/hooks/*.json`

Hooks chạy **shell commands tại các điểm lifecycle** của agent session – bất kể
agent được prompt như thế nào. Đây là automation **đảm bảo 100%**, khác với
instructions (chỉ là guidance cho AI).

**8 Lifecycle Events:**

| Event | Kích hoạt khi | Dùng để |
|-------|-------------|---------|
| `SessionStart` | Session mới bắt đầu | Inject branch name, ticket ID, project state |
| `UserPromptSubmit` | User gửi bất kỳ prompt | Audit log, validate input |
| `PreToolUse` | Trước khi agent gọi tool | **Block lệnh nguy hiểm** |
| `PostToolUse` | Sau khi tool hoàn thành | **Tự chạy formatter/linter** |
| `PreCompact` | Trước khi context compact | Export state quan trọng |
| `SubagentStart` | Subagent được spawn | Inject context cho subagent |
| `SubagentStop` | Subagent kết thúc | Aggregate results |
| `Stop` | Session kết thúc | **Bắt buộc kiểm tra trước khi dừng** |

**Ví dụ hooks thực tế cho Automotive:**

```json
// .github/hooks/automotive-guardrails.json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python .github/hooks/scripts/guard_pre_tool.py",
        "windows": "python .github\\hooks\\scripts\\guard_pre_tool.py",
        "timeout": 5
      }
    ],
    "PostToolUse": [
      {
        "type": "command",
        "command": "python .github/hooks/scripts/post_tool_format.py"
      }
    ],
    "SessionStart": [
      {
        "type": "command",
        "command": "python .github/hooks/scripts/inject_context.py"
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python .github/hooks/scripts/verify_completion.py",
        "timeout": 60
      }
    ]
  }
}
```

```python
# guard_pre_tool.py – Chặn operations nguy hiểm TRƯỚC khi execute
import json, sys, os

data = json.load(sys.stdin)
tool_name = data.get("tool_name", "")
tool_input = data.get("tool_input", {})

# Chặn edit/delete trong generated/ và src/rte/
if tool_name in ["editFiles", "deleteFiles"]:
    files = tool_input.get("files", [])
    protected = [f for f in files
                 if "generated/" in f or "src/rte/" in f]
    if protected:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason":
                    f"BLOCKED: These files are auto-generated and must not be edited manually: {protected}. "
                    f"Use 'python gen_code.py' to regenerate."
            }
        }))
        sys.exit(0)

# Block git push trực tiếp từ agent
if tool_name == "runInTerminal":
    cmd = tool_input.get("command", "")
    if "git push" in cmd and "--dry-run" not in cmd:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason":
                    "Agent is attempting to push to remote. Please confirm this is intentional."
            }
        }))
        sys.exit(0)

print(json.dumps({"continue": True}))
```

```python
# post_tool_format.py – Auto-format sau mỗi lần agent edit C file
import json, sys, os

data = json.load(sys.stdin)
if data.get("tool_name") == "editFiles":
    files = data.get("tool_input", {}).get("files", [])
    c_files = [f for f in files if f.endswith(('.c', '.h'))]
    if c_files:
        files_str = " ".join(c_files)
        os.system(f"clang-format -i {files_str}")
        # Quick MISRA check để inject thông tin cho agent
        result = os.popen(f"python run_misra.py --files {files_str} --count-only").read().strip()
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext":
                    f"Auto-formatted {len(c_files)} C files. "
                    f"Current MISRA violation count: {result}"
            }
        }))
        sys.exit(0)

print(json.dumps({"continue": True}))
```

```python
# inject_context.py – Inject project state khi session bắt đầu
import json, sys, subprocess

branch = subprocess.check_output(
    ["git", "branch", "--show-current"], text=True).strip()
ticket = branch.split("/")[-1] if "/" in branch else "unknown"
misra_count = subprocess.check_output(
    ["python", "run_misra.py", "--count-only"], text=True).strip()

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext":
            f"Current branch: {branch} | Jira ticket: {ticket} | "
            f"Current MISRA violations: {misra_count}"
    }
}))
```

**Configure hooks via UI:** Gõ `/hooks` trong chat.

**Xem hook logs:** Output panel → "GitHub Copilot Chat Hooks"

**Xem hook diagnostics:** Right-click trong Chat View → Diagnostics

### 4.7 AGENTS.md

File hướng dẫn đặc biệt cho **background agents và coding agents** khi chạy
tự động. Đặt ở root của repository.

```markdown
# AGENTS.md – Instructions for AI Coding Agents

## Repository: BCM Body Control Module – AUTOSAR Classic CP

## CRITICAL: Before Any Change
1. Read header file of the affected module FIRST
2. Check ARXML: if function has port interface → regenerate, do NOT manually edit
3. NEVER touch: generated/ or src/rte/ folders → use: python gen_code.py
4. Check if affected module is in safety-relevant list (config/safety_requirements.csv)

## Build & Verification (All must pass before task is Done)
Build:      python build.py --target BCM --config Release
Tests:      python build.py --target BCM_TEST && python run_tests.py
MISRA:      python run_misra.py --module <changed_module>
Full CI:    python ci_check.py

## Definition of Done
- [ ] Compiles: zero warnings with -Wall -Wextra
- [ ] Tests: all pass, no regression
- [ ] MISRA: zero new Mandatory or Required violations
- [ ] Coverage: not below current baseline (see coverage_baseline.txt)
- [ ] Docs: Doxygen comments added/updated for every changed public function
- [ ] Change log: CHANGELOG.md updated

## Commit Message Format
type(BCM-<JIRA_ID>): imperative description

Types: feat | fix | refactor | test | docs | chore

## Working Notes
- Interrupt priority levels documented in: docs/interrupt_priority_matrix.xlsx
- If unsure about design decision: prefer conservative approach, add TODO comment
```

### 4.8 Tool Sets

Nhóm nhiều tools thành một entity, reference bằng `#toolset-name` trong chat.

```bash
# Command Palette: Chat: Configure Tool Sets
```

```jsonc
// .vscode/toolsets.jsonc
{
  "read-only": {
    "tools": ["read", "search", "usages", "problems", "changes"],
    "description": "Read-only analysis tools – safe, no side effects",
    "icon": "search"
  },
  "full-stack": {
    "tools": ["read", "edit", "search", "runInTerminal", "problems", "usages"],
    "description": "Full implementation toolkit",
    "icon": "tools"
  },
  "atlassian": {
    "tools": ["jira_*", "confluence_*"],
    "description": "Jira + Confluence tools",
    "icon": "globe"
  }
}
```

Dùng trong chat:
```
"Analyze the CAN driver for race conditions #read-only"
"Implement and test the feature #full-stack"
```

---

## 5. MCP Servers {#5}

**MCP (Model Context Protocol)** là open standard giúp Copilot kết nối với
bất kỳ external service nào. Copilot agent gọi MCP tools như gọi built-in tools.

**Kiến trúc:**
```
Copilot Agent
     │
     ├── Built-in Tools (file, terminal, search, fetch)
     │
     ├── MCP: Jira              → Tickets, sprints, comments, status
     ├── MCP: Confluence        → Pages, spaces, search, create/update
     ├── MCP: Filesystem        → Advanced file ops
     ├── MCP: Database          → SQL/NoSQL queries
     ├── MCP: REST/Fetch        → Codebeamer, Gerrit, any REST API
     ├── MCP: Browser           → Web automation, screenshot
     └── MCP: Custom (tự viết) → Bất kỳ service nào có API
```

**Thêm MCP – Option 1: Extensions Gallery**
`Ctrl+Shift+X` → tìm `@mcp` → chọn → Install in Workspace

**Thêm MCP – Option 2: `.vscode/mcp.json`** (commit vào git, share với team)

```json
{
  "servers": {
    "jira": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@sooperset/mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://your-company.atlassian.net",
        "CONFLUENCE_URL": "https://your-company.atlassian.net",
        "JIRA_USERNAME": "${input:atlassian-email}",
        "JIRA_API_TOKEN": "${input:atlassian-token}",
        "CONFLUENCE_USERNAME": "${input:atlassian-email}",
        "CONFLUENCE_API_TOKEN": "${input:atlassian-token}"
      }
    },
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${workspaceFolder}"]
    },
    "rest-fetch": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-server-fetch"],
      "env": {
        "ALLOWED_DOMAINS": "codebeamer.yourcompany.com,gerrit.yourcompany.com"
      }
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "atlassian-email",
      "description": "Atlassian Account Email"
    },
    {
      "type": "promptString",
      "id": "atlassian-token",
      "description": "Atlassian API Token (profile → security → API tokens)",
      "password": true
    }
  ]
}
```

**Cách dùng MCP tools:**

Tự động – agent quyết định:
```
"What are my open tickets in BCM-Sprint-42?"
→ Copilot tự gọi Jira MCP
```

Explicit – đặt `#` trước tool name:
```
"Review #jira:BCM-1234 and implement the changes"
```

MCP Resources (attach context từ MCP vào prompt):
Chat → Add Context → MCP Resources

MCP Prompts (slash commands từ server):
```
/mcp.jira.my-open-tickets
/mcp.confluence.search-page "engine speed"
```

**MCP Apps** – MCP server có thể trả về interactive UI (forms, lists, charts)
inline trong chat, không chỉ text. Ví dụ: hiển thị Jira sprint board
interactive ngay trong VS Code.

**Tool auto-approval cho MCP:**
```json
// settings.json
{
  "chat.tools.urls.autoApprove": {
    "https://your-company.atlassian.net/*": true,
    "https://codebeamer.yourcompany.com/*": true
  }
}
```

---

## 6. Tools – Vũ Khí Bên Trong Agent {#6}

### Các Built-in Tool Quan Trọng

**`#fetch`** – Gọi bất kỳ URL nào:
```
"Summarize the CAN specification from #fetch https://internal.company.com/specs/CAN_SPEC_v3.pdf"
"Get the latest MISRA guidelines from #fetch https://misra.org.uk"
```

**`#githubRepo`** – Tìm kiếm trong GitHub repo:
```
"How does the reference AUTOSAR stack handle SchM? #githubRepo AUTOSAR/autosar-classic-reference"
```

**`#problems`** – Đọc Problems panel hiện tại:
```
"Fix all the errors in #problems"
```

**`#changes`** – Xem staged/unstaged changes:
```
"Review my current changes in #changes for MISRA compliance"
```

### Tool Approval

Khi tool cần approval, VS Code show dialog với tool details. Bạn có thể:
- **Allow (once)** – Cho phép lần này
- **Allow (session)** – Cho phép toàn session
- **Allow (workspace)** – Luôn cho phép trong workspace này
- **Allow (always)** – Luôn cho phép

**Auto-approve terminal commands:**
```json
// settings.json
{
  "chat.tools.terminal.autoApprove": {
    "/^python build\\.py/": true,
    "/^python run_tests\\.py/": true,
    "/^python run_misra\\.py/": true,
    "/^python ci_check\\.py/": true,
    "git status": true,
    "git log": true,
    "rm": false,
    "git push": false
  }
}
```

**Tool Sandboxing (Experimental – macOS/Linux):**
```json
{
  "chat.tools.terminal.sandbox.enabled": true,
  "chat.tools.terminal.sandbox.linuxFileSystem": {
    "allowWrite": ["."],
    "denyWrite": ["./generated/", "./src/rte/"],
    "denyRead": [".env", "*.key"]
  }
}
```

### Edit Tool Parameters

Trước khi tool chạy, expand chevron trong confirmation dialog để xem và **edit
parameters trước** – ví dụ: sửa file paths, thay đổi hàm cần modify.

---

## 7. Subagents & Agent Orchestration {#7}

### Subagent là gì?

Khi main agent gặp subtask phức tạp, nó spawn **subagent** – AI agent độc lập
chạy trong **context window riêng biệt**, làm subtask, rồi báo **chỉ kết quả**
về cho main agent.

```
Main Agent (context A)
    │
    ├── Subagent 1: "Analyze CAN driver patterns" (context B)  ← PARALLEL
    ├── Subagent 2: "Research requirements in Codebeamer" (context C)  ← PARALLEL
    └── Subagent 3: "Check similar implementations" (context D)  ← PARALLEL

    Chờ tất cả xong → tổng hợp kết quả → implement
```

**Lợi ích quan trọng:**
- Main context **không bị bloat** bởi intermediate research
- Multiple subagents chạy **song song** → nhanh hơn đáng kể
- Mỗi subagent dùng model/tools tối ưu cho subtask của nó
- Isolate exploratory work – dead end không affect main context
- **Giảm token consumption** – chỉ summary được pass về, không full history

### Orchestration Patterns

**Pattern 1: Coordinator + Worker**

```markdown
<!-- .github/agents/feature-builder.agent.md -->
---
name: Feature Builder
description: Coordinates full feature development from plan to merge-ready code
tools: ['agent', 'edit', 'search', 'read', 'runInTerminal']
agents: ['BCM Researcher', 'BCM Implementer', 'MISRA Reviewer', 'Test Writer']
---

For each feature request:
1. Spawn BCM Researcher to analyze codebase and requirements (parallel with step 2)
2. Use Jira MCP to read ticket details (parallel with step 1)
3. Create implementation plan based on research results
4. Spawn BCM Implementer for each module change (can parallelize independent modules)
5. Spawn Test Writer to create unit tests
6. Run: python ci_check.py
7. Spawn MISRA Reviewer if violations exist → loop with Implementer until clean
8. Commit with conventional commit message
```

```markdown
<!-- .github/agents/bcm-researcher.agent.md -->
---
name: BCM Researcher
description: Research-only agent for BCM codebase analysis
tools: ['read', 'search', 'usages', 'fetch']
user-invokable: false          ← Hidden from dropdown, only usable as subagent
model: GPT-5.2 (copilot)       ← Fast model for research
---
Perform thorough code analysis. Return structured findings:
- Affected files and functions
- Similar existing patterns to follow
- Potential impact areas
- Open questions for the implementer
```

**Pattern 2: Multi-Perspective Review (Song Song)**

```markdown
<!-- .github/agents/thorough-reviewer.agent.md -->
---
name: Thorough Reviewer
description: Multi-angle parallel code review for automotive embedded
tools: ['agent', 'read', 'search']
---

Run PARALLEL subagents for independent analysis (do not let one influence another):

- **Safety Reviewer**: bounds checking, UB detection, ISR safety, critical sections
- **MISRA Reviewer**: MISRA C:2012 violations, rule-by-rule analysis
- **AUTOSAR Reviewer**: RTE usage, BSW compliance, state machine correctness
- **Architecture Reviewer**: module cohesion, naming, code duplication

Synthesize: prioritized report with BLOCKER | MAJOR | MINOR | INFO levels.
State what is DONE WELL, not just problems.
```

**Pattern 3: TDD Workflow**

```markdown
<!-- .github/agents/tdd-red.agent.md -->
---
name: TDD Red
description: Write failing tests only – no implementation code
tools: ['read', 'search', 'edit']
user-invokable: false
disable-model-invocation: false
---
Write ONLY test code. You are forbidden from modifying any non-test source files.
Tests must FAIL when run with the current implementation (that is the goal).
Cover: all acceptance criteria, boundary values, error paths.
```

**Invoke subagents explicitly:**
```
"Use BCM Researcher as a subagent to analyze the LIN driver,
 then implement the window control slave node based on its findings."
```

**Tool set for subagent control:**
```json
// enable runSubagent tool in custom agent
{ "tools": ["agent", "read", "edit"] }  // "agent" enables runSubagent
```

---

## 8. Background Agents {#8}

Background agents chạy **độc lập qua Copilot CLI**, dùng **Git worktrees**
để isolate hoàn toàn khỏi workspace đang làm việc.

### Khi nào dùng

```
Dùng Background Agent khi:         Dùng Local Agent khi:
─────────────────────────────────   ──────────────────────────────────
Task rõ ràng, well-defined          Task còn cần clarification
Không cần interactive feedback      Muốn xem progress real-time
Thực thi plan đã được review        Cần extension tools
Bạn muốn làm việc khác             Cần BYOK models
Implement danh sách issues cụ thể  Test failures cần instant fix
```

### Flow Hoàn Chỉnh

```
Step 1: [Plan Mode] Lập và review kế hoạch
               ↓
Step 2: Click "Start Implementation" → "Continue in Background"
               ↓
Step 3: VS Code tự tạo Git worktree mới (isolated folder)
               ↓
Step 4: Copilot CLI chạy ngầm – bạn tiếp tục làm việc bình thường
               ↓
Step 5: Monitor progress: Chat View → filter "Background Agents"
        Xem diffs trong Source Control → Worktrees
               ↓
Step 6: Khi xong: Working Set → Apply changes → resolve conflicts nếu có
```

### Quản Lý Sessions

- **Chat View sidebar** – Tất cả sessions (local + background)
- **Filter "Background Agents"** – Chỉ xem background sessions
- **Right-click session** → "Open as Editor" (xem như editor tab)
- **Right-click session** → "Resume in Terminal" (interact trực tiếp với CLI)
- **Open Worktree in New Window** – Xem toàn bộ worktree
- Background agent **commit sau mỗi turn** → aligned với git history

### Khởi Động Background Session

```
Option A: Chat View → Delegate Session dropdown → Background
Option B: Plan Mode → "Start Implementation" → "Continue in Background"
Option C: Command Palette → "Chat: New Background Agent"
Option D: Terminal → gh copilot agent "task description"  (Copilot CLI)
```

### Kết Hợp Custom Agent

```json
// settings.json – enable custom agents for background
{ "github.copilot.chat.cli.customAgents.enabled": true }
```
→ Khi tạo background session, chọn custom agent từ dropdown.
→ Background agent follow persona và rules của custom agent đó.

### Hand-off Local → Background

Khi đang chat local agent và muốn chuyển sang background:
1. Clarify requirements xong trong local
2. Delegate Session → Background
3. Full conversation history + context được carry over
4. Background agent tiếp tục từ đúng chỗ dừng

---

## 9. Bài Toán Hàng Loạt {#9}

### Tại Sao Chỉ Gửi Một Prompt Không Đủ

Khi có 100-1000 issues, nếu chỉ viết một prompt như "fix all 100 MISRA issues":
- **Context window limit**: Agent không thể giữ 100 issues + codebase + reasoning
  trong một context window
- **Không có checkpoint**: Nếu bị interrupt giữa chừng, không biết đã fix được bao nhiêu
- **Không verify**: Agent không tự kiểm tra lại toàn bộ sau khi xong
- **Risk**: Agent "nghĩ" mình đã fix nhưng thực ra bỏ sót

---

### Chiến Lược A: Script-Driven Batch – Khuyến Nghị Nhất

Yêu cầu Agent **viết script** drive iteration, không tự iteration trong agent:

```
[Agent Mode]
"Write a Python script `scripts/batch_misra_fix.py` that:
 1. Gets MISRA violations: python run_misra.py --module BCM_CAN --format json
 2. Groups by rule category (Mandatory / Required / Advisory)
 3. For each violation batch (10 per batch):
    - Print the violation details clearly
    - Apply the fix following our coding standards
    - Re-run MISRA on that file to verify the fix
    - Record result in batch_fix_log.csv: file, line, rule, status, new_count
 4. After all batches: run full MISRA + all unit tests
 5. Print final summary: fixed/failed/skipped counts

Then run the script and fix any issues you encounter."
```

Script này **iterable, resumable, verifiable** – bạn có thể xem `batch_fix_log.csv`
bất kỳ lúc nào để biết progress.

---

### Chiến Lược B: Stop Hook – Đảm Bảo Completion

Dùng `Stop` hook để **bắt buộc agent kiểm tra** trước khi được phép dừng:

```python
# .github/hooks/scripts/verify_completion.py
import json, sys, subprocess

data = json.load(sys.stdin)

# Tránh infinite loop (hook này chỉ chạy một lần thêm)
if data.get("stop_hook_active"):
    print(json.dumps({"continue": True}))
    sys.exit(0)

# Kiểm tra MISRA
result = subprocess.run(
    ["python", "run_misra.py", "--module", "BCM_CAN", "--severity", "mandatory,required", "--count-only"],
    capture_output=True, text=True
)
remaining = int(result.stdout.strip() or "0")

# Kiểm tra tests
test_result = subprocess.run(
    ["python", "run_tests.py", "--module", "BCM_CAN", "--exit-code"],
    capture_output=True
)
tests_pass = (test_result.returncode == 0)

if remaining > 0 or not tests_pass:
    reasons = []
    if remaining > 0:
        reasons.append(f"{remaining} MISRA Mandatory/Required violations remain")
    if not tests_pass:
        reasons.append("unit tests are failing")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "decision": "block",
            "reason": f"Task NOT complete: {' AND '.join(reasons)}. Continue working."
        }
    }))
else:
    print(json.dumps({"continue": True}))
```

→ Agent **không thể báo cáo "done"** cho đến khi script này return pass.

---

### Chiến Lược C: Background Agent + Checklist File

Tạo checklist file, background agent tick từng item:

```markdown
<!-- MISRA_FIX_CHECKLIST.md -->
# MISRA Fix Checklist – BCM_CAN Module
Generated: 2026-02-21 | Total: 100 violations

## Legend: [ ] TODO | [~] In Progress | [x] Fixed | [!] Needs Review | [s] Skipped

## MANDATORY (23 violations – fix first)
- [ ] BCM_CAN.c:145  Rule 10.3  Assignment to narrower type
- [ ] BCM_CAN.c:167  Rule 10.4  Mixed type binary operator
- [ ] BCM_CAN.c:198  Rule 10.1  Unsigned operand to unary minus
- [ ] BCM_CAN.c:234  Rule 14.4  Controlling expression not boolean
... (19 more)

## REQUIRED (51 violations)
- [ ] BCM_CAN.c:89   Rule 15.5  No single point of exit
- [ ] BCM_CAN.c:102  Rule 16.4  Missing default in switch
... (49 more)

## ADVISORY (26 violations)
...
```

Background Agent prompt:
```
"Work systematically through MISRA_FIX_CHECKLIST.md:
 - Fix each [ ] item in the source file
 - Mark [x] immediately after verifying the fix
 - Run quick MISRA check on the file after each fix to confirm
 - If a fix is complex or risky, mark [!] with a note instead of [x]
 - Commit after completing each CATEGORY (Mandatory / Required / Advisory)
 Continue until all items are [x] or [!]."
```

**Lợi ích:**
- Git commits tại mỗi category → có thể rollback từng nhóm
- Checklist là ground truth của progress → không bao giờ mất vị trí
- `[!]` items rõ ràng để human review
- Nếu agent bị interrupt: resume từ item `[ ]` đầu tiên còn lại

---

### Chiến Lược D: Subagent Parallelism Cho 1000+ Issues

Với 1000+ issues trải đều nhiều modules:

```markdown
<!-- .github/agents/mass-misra-fixer.agent.md -->
---
name: Mass MISRA Fixer
description: Fix large volumes of MISRA violations across entire codebase
tools: ['agent', 'read', 'search', 'runInTerminal']
agents: ['Module MISRA Fixer']
---

Process:
1. Run full MISRA analysis: python run_misra.py --all --format json
2. Group violations by MODULE (file prefix)
3. Identify independent modules (no cross-dependencies)
4. Spawn Module MISRA Fixer subagents IN PARALLEL for independent modules
   (max 5 parallel to avoid terminal conflicts)
5. For dependent modules: fix in dependency order
6. After all complete: run full analysis + all tests
7. Create summary report: MISRA_FIX_REPORT.md
```

```markdown
<!-- .github/agents/module-misra-fixer.agent.md -->
---
name: Module MISRA Fixer
description: Fix MISRA violations in a single module
tools: ['read', 'edit', 'runInTerminal', 'search']
user-invokable: false
---
Fix all MISRA violations in the specified module.
Always run misra-fix skill. Record each fix.
Verify with re-analysis. Run module unit tests after all fixes.
```

---

### Tóm Tắt Chiến Lược Theo Scale

| Số lượng issues | Chiến lược | Tại sao |
|----------------|-----------|--------|
| < 15 | Agent Mode prompt thẳng | Single context đủ |
| 15–50 | Agent Mode + Stop Hook | Hook đảm bảo completion |
| 50–200 | Background Agent + Checklist | Resumable, git checkpoints |
| 200–500 | Script-Driven Batch | Fully automated, verifiable log |
| 500+ | Mass Fixer Agent + Parallel Subagents | Phân chia module song song |

---

## 10. MCP Servers Cho Automotive {#10}

### Jira MCP

```
"Get all open tickets in BCM-Sprint-42 assigned to me"
"Read ticket BCM-1567 with all comments, sub-tasks, and linked tickets"
"Update ticket BCM-1567 status to 'In Review'"
"Create sub-task under BCM-1234: Unit tests for engine speed monitoring"
"Add comment to BCM-1567: Implementation complete. See commit abc1234."
"Get sprint velocity for last 4 sprints in BCM project"
"Find all tickets with label 'MISRA' that are still open"
```

**Full end-to-end workflow:**
```
[Agent Mode + Jira MCP + Confluence MCP]
"Read Jira ticket BCM-2891.
 Search Confluence for the related feature specification.
 Implement in C following our AUTOSAR conventions.
 Run unit tests and MISRA analysis.
 Fix any issues found.
 Update ticket to 'In Review' with implementation summary."
```

### Confluence MCP

```
"Find the CAN Bus specification page in BCM space"
"Get Software Architecture Document, chapter 3.2"
"Create page 'BCM v2.3.1 Release Notes' in BCM/Release-Notes/"
"Update API doc with new function signatures from #file:src/bcm_api.h"
"Search for 'AUTOSAR SWC interface coordinator BCM'"
"List all pages in BCM space modified in the last 7 days"
```

**Tự động hóa documentation:**
```
"After implementing BCM_EngineSpeed module:
 1. Update Confluence page 'BCM Engine Speed Module' with:
    - New functions and their descriptions
    - Updated state machine description
    - Changed RTE port interfaces
    - New/updated unit test coverage
 2. Maintain existing page structure and link formatting"
```

### Codebeamer MCP (qua REST)

Codebeamer có REST API v3. Dùng `mcp-server-fetch`:

```
"Get requirement CB-REQ-4521 from Codebeamer project BCM-SRS"
"Show all requirements in chapter 4.3 (CAN Communication) of BCM SRS"
"Get all child requirements of CB-REQ-4521"
"Update verification status of CB-REQ-4521 to VERIFIED"
"Find all requirements with status APPROVED but no linked tests"
"Get traceability chain: CB-REQ-4521 → design → implementation → test"
```

**Traceability automation – đặc thù automotive:**
```
[Agent Mode + Codebeamer MCP + Confluence MCP]
"Perform full traceability analysis for CAN Communication chapter:
 1. Get all requirements from Codebeamer chapter 4 (CAN Communication)
 2. For each requirement: find implementation file in codebase
 3. For each implementation: find linked unit tests
 4. Build matrix: REQ ID | Description | Impl File | Test File | Coverage %
 5. Create Confluence page 'CAN Traceability Matrix' with the table
 6. Flag: requirements with NO implementation (red)
 7. Flag: requirements with NO test coverage (yellow)"
```

### Gerrit MCP (qua REST)

```
"List my pending Gerrit code reviews"
"Get full diff for Gerrit change 98765"
"Submit inline comment on BCM_CAN.c line 145: 'Missing MISRA justification comment'"
"Get all open changes targeting branch release/2.x in BCM-Platform project"
"Check if change 98765 has score +2 Code-Review from all required approvers"
```

**Automated code review:**
```
[Agent Mode + Gerrit MCP]
"Get my pending Gerrit review for change 98765.
 Run multi-angle review:
  - MISRA C:2012 compliance
  - AUTOSAR architectural rules
  - Safety-relevant function analysis
  - Logic correctness vs requirements
 For EACH issue: submit inline Gerrit comment at exact file:line.
 Submit final review comment with overall assessment."
```

---

## 11. Setup Hoàn Chỉnh {#11}

### Cấu Trúc File

```
your-bcm-project/
│
├── AGENTS.md                               ← Background/coding agent guide
│
├── .github/
│   ├── copilot-instructions.md             ← Global DNA (always active)
│   │
│   ├── instructions/                       ← Path-specific rules
│   │   ├── swc.instructions.md             applyTo: src/swc/**
│   │   ├── bsw.instructions.md             applyTo: src/bsw/**
│   │   ├── tests.instructions.md           applyTo: test/**
│   │   ├── scripts.instructions.md         applyTo: scripts/**/*.py
│   │   └── code-review.instructions.md     applyTo: **/*.c,**/*.h
│   │
│   ├── prompts/                            ← Reusable slash commands
│   │   ├── review-misra.prompt.md
│   │   ├── write-unit-test.prompt.md
│   │   ├── generate-release-notes.prompt.md
│   │   ├── analyze-requirements.prompt.md
│   │   └── onboard-module.prompt.md
│   │
│   ├── agents/                             ← Custom agent personas
│   │   ├── misra-reviewer.agent.md
│   │   ├── automotive-tdd.agent.md
│   │   ├── feature-builder.agent.md
│   │   ├── thorough-reviewer.agent.md
│   │   ├── mass-misra-fixer.agent.md
│   │   ├── tdd-red.agent.md                user-invokable: false
│   │   ├── tdd-green.agent.md              user-invokable: false
│   │   └── bcm-researcher.agent.md         user-invokable: false
│   │
│   ├── skills/                             ← Agent Skills (portable)
│   │   ├── misra-fix/
│   │   │   ├── SKILL.md
│   │   │   ├── misra-output-format.md
│   │   │   └── common-misra-fixes.c
│   │   ├── autosar-swc-gen/
│   │   │   ├── SKILL.md
│   │   │   └── swc-template.c
│   │   ├── unit-test-gen/
│   │   │   ├── SKILL.md
│   │   │   └── test-template.cpp
│   │   ├── traceability-check/
│   │   │   └── SKILL.md
│   │   └── release-notes/
│   │       ├── SKILL.md
│   │       └── release-notes-template.md
│   │
│   └── hooks/                              ← Lifecycle automation
│       ├── automotive-guardrails.json
│       └── scripts/
│           ├── guard_pre_tool.py
│           ├── post_tool_format.py
│           ├── inject_context.py
│           └── verify_completion.py
│
└── .vscode/
    ├── mcp.json                            ← MCP servers (commit to git)
    ├── toolsets.jsonc                      ← Tool sets
    └── settings.json                       ← Copilot settings
```

### `.vscode/settings.json` Tối Ưu

```json
{
  "chat.promptFiles": true,
  "chat.agent.enabled": true,
  "chat.mcp.autoStart": true,
  "github.copilot.chat.codeGeneration.useInstructionFiles": true,
  "github.copilot.chat.codeGeneration.instructions": [
    { "text": "Always check for MISRA C:2012 compliance when generating C code for automotive embedded systems." }
  ],
  "github.copilot.enable": {
    "*": true,
    "markdown": true,
    "scminput": true
  },
  "github.copilot.chat.agent.autoApprove": false,
  "github.copilot.chat.cli.customAgents.enabled": true,
  "github.copilot.chat.organizationCustomAgents.enabled": true,
  "chat.tools.terminal.autoApprove": {
    "/^python build\\.py/": true,
    "/^python run_tests\\.py/": true,
    "/^python run_misra\\.py/": true,
    "/^python ci_check\\.py/": true,
    "/^python gen_stubs\\.py/": true,
    "git status": true,
    "git log": true,
    "git diff": true,
    "rm": false,
    "/git push(?!.*--dry-run)/": false
  }
}
```

---

## 12. Quy Trình Thực Tế {#12}

### Workflow 1: Jira Ticket → Code Hoàn Chỉnh

```
[Agent Mode + Jira MCP + Confluence MCP]
"Read ticket BCM-2891.
 Find related spec in Confluence.
 Implement changes in C per AUTOSAR conventions.
 Run ci_check.py. Fix anything that fails.
 Update ticket to In Review with implementation summary."

Trước: ~3-4 giờ (manual context switching)
Sau:   ~30-60 phút (review + sign-off vẫn cần người)
```

### Workflow 2: Plan → Implement → Background

```
1. [Plan Mode] "Plan the LIN slave node for window motor control"
   → Research → clarify → produce step-by-step plan

2. Review plan, chỉnh sửa nếu cần

3. Click "Start Implementation" → "Continue in Background"
   → Git worktree tạo → Copilot CLI chạy ngầm

4. [Tiếp tục làm việc khác]

5. Chat View → Background Agents → theo dõi progress

6. Khi xong: Working Set → Apply → resolve merge conflicts

Trước: blocked suốt 2-4 giờ implement
Sau:   chỉ mất 30 phút (plan + review + apply)
```

### Workflow 3: Multi-Angle Code Review Song Song

```
[Custom Agent: Thorough Reviewer]
"Review the latest changes to BCM_CAN module."

→ Agent spawn 4 subagents đồng thời:
  - Safety Reviewer (context isolated)
  - MISRA Checker (context isolated)
  - AUTOSAR Compliance (context isolated)
  - Architecture Checker (context isolated)
→ Tổng hợp: BLOCKER/MAJOR/MINOR report với locations

Trước: 1-2 giờ manual review
Sau:   5-10 phút
```

### Workflow 4: Traceability Matrix (Automotive Đặc Thù)

```
[Agent Mode + Codebeamer MCP + Confluence MCP]
"Generate full Requirements → Code → Test traceability matrix
 for CAN Communication chapter. Flag any gaps."

Trước: 1-2 ngày (manual cross-reference giữa 3 tools)
Sau:   20-30 phút
```

### Workflow 5: Bulk MISRA Fix

```
Scenario: 100 MISRA violations trong BCM_CAN module

[Background Agent + Checklist Strategy]
1. Agent tạo MISRA_FIX_CHECKLIST.md với 100 items
2. Background Agent fix từng item, tick checklist, commit mỗi category
3. Stop Hook verify completion trước khi báo xong
4. Bạn review checklist, merge

Trước: 2-3 ngày (manual fix từng cái)
Sau:   2-4 giờ autonomous (bạn làm việc khác trong lúc đó)
```

### Workflow 6: Release Notes Tự Động

```
[Prompt File: /release-notes]

Step 1: Jira MCP → get all tickets in fix version
Step 2: Group by type
Step 3: git log → match tickets
Step 4: Write to Confluence

Trước: 2+ giờ
Sau:   5-10 phút
```

### Workflow 7: Bug Investigation

```
[Ask Mode – read-only, completely safe]
"Analyze crash log: #file:logs/crash_20260221.log
 Module: BCM_CAN
 Source: #file:src/bsw/can/BCM_CAN.c

 1. Parse crash address and stack trace
 2. Identify root cause
 3. Propose fix with code
 4. Find similar patterns elsewhere that might have the same bug"
```

### Workflow 8: Onboarding a New Module

```
[Ask Mode]
"Give me a comprehensive overview of BCM_LightControl in #codebase:
 1. Purpose and responsibilities
 2. State machine (ASCII art diagram)
 3. All RTE interfaces (reads/writes with signal names)
 4. Key algorithms and timing requirements
 5. Known TODOs and limitations
 6. Module dependencies and callers"
```

---

## 13. Tổng Kết {#13}

### Ma Trận Khả Năng Đầy Đủ

| Khả Năng | File/Cách Setup | Áp Dụng Cho |
|---------|----------------|-------------|
| Ask Mode | Built-in | Phân tích, tìm hiểu, không sửa code |
| Plan Mode | Built-in | Lập kế hoạch phức tạp trước khi code |
| Agent Mode | Built-in | Multi-step autonomous với tools và build/test |
| Background Agent | Delegate → Background | Chạy nền, Git worktree isolated |
| Subagents | Dùng `agent` tool | Parallel isolated research và execution |
| Agent Orchestration | Custom Agents + `agents:` field | Multi-agent pipelines phức tạp |
| Custom Instructions | `.github/copilot-instructions.md` | DNA luôn active của toàn project |
| Path Instructions | `.github/instructions/*.instructions.md` | Rules theo layer/file type |
| Prompt Files | `.github/prompts/*.prompt.md` | Slash commands cho tasks lặp |
| **Agent Skills** | `.github/skills/*/SKILL.md` | **Portable, on-demand, có scripts** |
| Custom Agents | `.github/agents/*.agent.md` | Personas chuyên biệt + tool control |
| Handoffs | `handoffs:` trong agent file | Guided workflows giữa agents |
| Hooks | `.github/hooks/*.json` | Deterministic automation + guardrails |
| Tool Sets | `.vscode/toolsets.jsonc` | Group tools, reference bằng `#name` |
| AGENTS.md | Root repo | Guide cho background/coding agent |
| MCP Jira | `.vscode/mcp.json` | Tickets, sprints auto |
| MCP Confluence | `.vscode/mcp.json` | Documentation auto |
| MCP Codebeamer | `.vscode/mcp.json` | Requirements + traceability |
| MCP Gerrit | `.vscode/mcp.json` | Code review automation |
| Stop Hook | Hooks config | Đảm bảo completion cho bulk tasks |
| Batch Script | Agent-generated script | Scale đến hàng nghìn items |

### Lộ Trình Áp Dụng Theo Tuần

```
Week 1-2:   /init → review copilot-instructions.md
            + thêm path instructions cho SWC/BSW/test layer
            → Copilot bắt đầu "nói cùng ngôn ngữ" với project

Week 3-4:   Tạo 3-5 Agent Skills (misra-fix, unit-test-gen, autosar-swc-gen)
            → On-demand workflows, portable qua CLI
            + Thêm 2-3 Prompt Files cho tasks hay làm nhất
            → Slash commands sẵn sàng

Week 5-6:   Setup MCP Jira + Confluence
            → Loại bỏ context switching giữa tools
            + Setup Hooks bảo vệ generated/ folder
            → Guardrails an toàn cho agent

Week 7-8:   Tạo Custom Agents chuyên biệt
            (MISRA Reviewer, Thorough Reviewer, Feature Builder)
            + Cấu hình Background Agent workflow
            → Parallel autonomous execution

Week 9-10:  Setup Codebeamer + Gerrit MCP
            → Full traceability automation
            → Automated code review với inline comments

Week 11+:   Setup Orchestration (Coordinator + Workers)
            + Implement Stop Hooks cho bulk tasks
            + AGENTS.md để coding agent self-directed
            → Full agentic pipeline, minimal manual intervention
```

### Resources

- [VS Code Copilot Docs](https://code.visualstudio.com/docs/copilot/overview)
- [VS Code Agent Customization](https://code.visualstudio.com/docs/copilot/customization/overview)
- [VS Code Custom Agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
- [VS Code Agent Skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [VS Code Agent Hooks](https://code.visualstudio.com/docs/copilot/customization/hooks)
- [VS Code Subagents](https://code.visualstudio.com/docs/copilot/agents/subagents)
- [VS Code Background Agents](https://code.visualstudio.com/docs/copilot/agents/background-agents)
- [VS Code MCP Servers](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)
- [Agent Skills Open Standard](https://agentskills.io/)
- [MCP Servers Registry](https://github.com/modelcontextprotocol/servers)
- [Awesome Copilot Customizations](https://github.com/github/awesome-copilot)
- [Anthropic Reference Skills](https://github.com/anthropics/skills)
