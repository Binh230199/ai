# Hướng Dẫn Thiết Kế Agentic AI Workflow
### Khi nào dùng Instructions / Prompt / Skill / Agent / Hook

---

## Tổng Quan – 5 Công Cụ, 5 Mục Đích Khác Nhau

```
┌─────────────────────────────────────────────────────────────────────┐
│  INSTRUCTIONS  → "AI phải biết điều này MỌI LÚC"                   │
│  PROMPT        → "Tôi muốn AI làm việc X ngay bây giờ"             │
│  SKILL         → "Việc X cần tài nguyên/script kèm theo"           │
│  AGENT         → "Việc X có nhiều nhánh, loop, hoặc cần persona"   │
│  HOOK          → "Việc Y phải tự động xảy ra, AI không được bỏ qua"│
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phần 1 – Instructions

### Định nghĩa
File markdown tự động đính kèm vào **mọi** request mà không cần gọi.
AI luôn biết nội dung này, dù bạn không nhắc.

### File
```
.github/copilot-instructions.md          ← Global, áp dụng toàn workspace
.github/instructions/*.instructions.md  ← Path-specific, áp dụng theo glob pattern
```

### Nội dung phù hợp
- Project là gì, tech stack gì, môi trường gì
- Coding conventions và naming rules
- Build commands, test commands
- Những gì AI KHÔNG ĐƯỢC làm (ví dụ: không edit generated files)
- Những gì AI phải làm trong MỌI trường hợp

### Nội dung KHÔNG phù hợp
- Hướng dẫn task cụ thể → dùng Prompt hoặc Skill
- Workflow step-by-step → dùng Prompt hoặc Skill
- Rules chỉ áp dụng khi review → dùng path instructions với `excludeAgent`

### Chọn Global vs Path-Specific

| Câu hỏi | Trả lời | Dùng |
|---------|--------|------|
| Rule này áp dụng cho toàn bộ project? | Yes | `copilot-instructions.md` |
| Rule này chỉ áp dụng cho file C++? | Yes | `cpp.instructions.md` với `applyTo: **/*.cpp` |
| Rule này chỉ cho test files? | Yes | `tests.instructions.md` với `applyTo: test/**` |
| Rule này chỉ cho review, không phải coding? | Yes | `code-review.instructions.md` với `excludeAgent: coding-agent` |

### Ví dụ

```markdown
<!-- .github/copilot-instructions.md -->
# Project: RSE (Rear Seat Entertainment) – C++ Linux Service

## Build
- Build: cmake -B build && cmake --build build -- -j$(nproc)
- Test:  ctest --output-on-failure
- Static: ./run_static.sh

## Rules
- NEVER edit: generated/, src/rte/
- ALWAYS use std::error_code for error handling, never throw
- ALWAYS add Doxygen comment for public functions
```

```markdown
<!-- .github/instructions/cpp.instructions.md -->
---
applyTo: "src/**/*.cpp,src/**/*.h"
---
- Follow AUTOSAR C++14 Guidelines
- No raw new/delete – use smart pointers
- Max function length: 50 lines
```

### Checklist quyết định

```
□ Thông tin này AI cần biết trong MỌI conversation?    → instructions
□ Chỉ cần khi edit file loại cụ thể?                  → path instructions
□ Chỉ xuất hiện khi tôi gọi một task cụ thể?          → KHÔNG phải instructions
```

---

## Phần 2 – Prompt

### Định nghĩa
File markdown chứa instructions cho **một task cụ thể**.
Xuất hiện như slash command `/tên` khi bạn gõ `/` trong chat.
Không tự động chạy – chỉ chạy khi bạn gọi.

### File
```
.github/prompts/*.prompt.md
```

### Khi nào dùng Prompt
- Task lặp đi lặp lại mà bạn không muốn gõ lại mỗi lần
- Workflow **tuyến tính** – không có điều kiện if/else, không có loop
- Không cần file kèm theo (template, script, examples)
- Có thể gọi Skills bên trong để tái sử dụng logic

### Khi nào KHÔNG dùng Prompt
- Cần file template kèm theo → dùng **Skill**
- Cần chạy script → dùng **Skill**
- Có rẽ nhánh (if C++ thì X, if Java thì Y) → dùng **Agent**
- Có vòng lặp (loop until coverage = 100%) → dùng **Agent**
- Cần restrict tools (read-only) → dùng **Agent**

### Cấu trúc Prompt

```markdown
<!-- .github/prompts/ten-task.prompt.md -->
# Tên Task

[Mô tả ngắn gọn task làm gì]

## Steps
1. [Bước 1]
2. [Bước 2]
3. [Bước 3]

[Reference files nếu cần]
#file:path/to/reference.md

[Input argument nếu cần]
Target: (specify in chat)
```

### Prompt Gọi Skill

```markdown
<!-- .github/prompts/analyze-bug.prompt.md -->
Use the `analyze-bug` skill to fully analyze the specified bug ticket.
Ticket: (specify in chat)
```

### Prompt Orchestrate Nhiều Skills

```markdown
<!-- .github/prompts/resolve-bug.prompt.md -->
# Full Bug Resolution

1. Use `analyze-bug` skill → understand root cause
2. Fix the code based on analysis
3. Use `cpp-unit-test` skill → write regression test
4. Use `fix-static-issues` skill → verify no new violations
5. Update Jira ticket with resolution summary
6. Use `5-whys` skill → write post-mortem on Confluence

Ticket: (specify in chat)
```

### Checklist quyết định

```
□ Tôi muốn gọi task này bằng /slash-command?           → prompt
□ Workflow chạy từ trên xuống dưới, không rẽ nhánh?    → prompt phù hợp
□ Không cần file template hay script kèm theo?          → prompt (không cần skill)
□ Workflow gọi nhiều skills theo thứ tự?                → prompt orchestrator
□ Workflow có if/else hoặc loop?                        → KHÔNG phải prompt → Agent
```

---

## Phần 3 – Skill

### Định nghĩa
Một **folder** chứa SKILL.md và các file tài nguyên kèm theo (scripts, templates,
examples). AI load khi relevant, portable qua VS Code / CLI / Coding Agent.

### File
```
.github/skills/<skill-name>/
    SKILL.md              ← Instructions bắt buộc
    script.py             ← Scripts (optional)
    template.md           ← Templates (optional)
    examples/             ← Examples (optional)
    patterns.cpp          ← Reference patterns (optional)
```

### Khi nào dùng Skill thay vì Prompt

| Tiêu chí | Prompt | Skill |
|---------|--------|-------|
| Chỉ có instructions | ✅ | ✅ |
| Cần file template | ❌ | ✅ |
| Cần chạy script (.py, .sh) | ❌ | ✅ |
| Cần examples/patterns để AI tham khảo | ❌ | ✅ |
| Dùng được trên Copilot CLI | ❌ | ✅ |
| Dùng được trong Background Agent | ❌ | ✅ |
| Các prompt khác nhau gọi cùng logic | ❌ | ✅ |

### Nguyên tắc đơn giản
> **Nếu task cần file gì kèm theo để làm đúng → Skill.**
> Nếu chỉ là hướng dẫn thuần → Prompt đủ rồi.

### Cấu trúc SKILL.md

```markdown
---
name: ten-skill
description: Mô tả NGẮN GỌN khi nào AI nên dùng skill này.
             Dùng để AI tự nhận biết khi relevant.
argument-hint: "[argument1] [argument2]"
---

# Tên Skill

## Context
[Project/tech context cần biết]

## Process
1. [Bước 1 – có thể reference script: python .github/skills/ten-skill/script.py]
2. [Bước 2]
3. [Bước 3]

## Resources
- Template: [template.md](./template.md)
- Examples: [examples/](./examples/)
- Common patterns: [patterns.cpp](./patterns.cpp)

## Rules / Constraints
[Những điều AI phải/không được làm khi dùng skill này]
```

### Ví dụ Thực Tế

```
Phân tích bug RRRSE-3050:
  - Jira MCP đọc ticket                     → instructions trong SKILL.md
  - fetch MCP download log                  → instructions trong SKILL.md
  - Parse Android logcat/Linux syslog       → parse_log.py (PHẢI có script)
  - Log patterns hay gặp (crash, ANR, segfault) → log_patterns.md (PHẢI có file)
  → Cần file kèm theo → SKILL ✅

Write 5-Whys post-mortem:
  - Template 5-whys chuẩn của team          → template.md (PHẢI có)
  - Example bài viết mẫu                    → example.md (PHẢI có)
  → Cần file kèm theo → SKILL ✅

Generate weekly report:
  - Pull Jira activity                      → instructions đủ
  - Pull Gerrit activity                    → instructions đủ
  - Format report                           → report_template.md (PHẢI có)
  → Cần template → SKILL ✅

Đọc ticket và tóm tắt:
  - Chỉ call Jira MCP và tóm tắt           → chỉ instructions
  → Không cần gì thêm → PROMPT đủ ✅
```

### Checklist quyết định

```
□ Task cần chạy script Python/Shell?                   → skill
□ Task cần file template để output đúng format?        → skill
□ Task cần examples để AI biết how-to?                 → skill
□ Nhiều prompts/agents sẽ gọi cùng logic này?          → skill (tái sử dụng)
□ Cần dùng từ CLI hoặc Background Agent?               → skill (portable)
□ Không cần gì kèm theo, chỉ instructions?             → prompt đủ
```

---

## Phần 4 – Agent

### Định nghĩa
AI persona chuyên biệt với **tools riêng, instructions riêng, model riêng**.
Xuất hiện trong dropdown cạnh Ask/Plan/Agent.
Phù hợp khi workflow có **logic phức tạp** mà prompt không xử lý được.

### File
```
.github/agents/*.agent.md
```

### Khi nào dùng Agent

**Tiêu chí bắt buộc – có ÍT NHẤT MỘT trong các điều này:**

| Tiêu chí | Giải thích |
|---------|-----------|
| **Có rẽ nhánh** | IF C++ → làm X, IF Java → làm Y |
| **Có vòng lặp** | Loop until coverage = 100%, loop until build pass |
| **Cần restrict tools** | Reviewer chỉ được read, không được edit |
| **Cần persona nhất quán** | "Bạn là strict AUTOSAR reviewer, không bao giờ approve nếu..." |
| **Orchestrate subagents** | Spawn nhiều AI song song để review nhiều góc độ |
| **Workflow quá dài** | Nhiều bước, nhiều decisions, không fit trong prompt |
| **Cần handoff** | Sau khi xong → chuyển sang agent khác với button click |

### Cấu trúc Agent File

```markdown
---
name: Tên Agent
description: Mô tả – khi nào dùng agent này
tools: ['read', 'edit', 'search', 'runInTerminal']   ← Chỉ tools được phép
model: claude-sonnet-4-6
user-invokable: true          ← false nếu chỉ dùng làm subagent
handoffs:
  - label: "→ Tên bước tiếp theo"
    agent: Tên Agent Tiếp Theo
    prompt: "Context để pass sang agent kia"
    send: false               ← false = user review trước khi send
---

[Instructions cho persona]

## Workflow
[Step-by-step có branching/looping]

## Constraints
[Những gì agent này KHÔNG được làm]
```

### Ví dụ Thực Tế

```markdown
<!-- agents/bug-fixer.agent.md -->
---
name: Bug Fixer
tools: ['read', 'edit', 'search', 'runInTerminal', 'problems']
handoffs:
  - label: "→ Write 5-Whys"
    agent: Documentation Writer
    prompt: "Write 5-whys for the bug just fixed."
    send: false
---

## Workflow

Step 1: Use `analyze-bug` skill

Step 2: Fix root cause in code

Step 3: [BRANCH by language]
  IF C++ service (src/**/*.cpp):
    → Use `cpp-unit-test` skill
    → Use `fix-static-issues` skill
  IF Java/Kotlin (src/**/*.java, **/*.kt):
    → Use `java-unit-test` skill

Step 4: [LOOP until all pass]
  → cmake --build build
  → ctest --output-on-failure
  IF build fail → read error → fix → retry (max 5)
  IF coverage < 100% → add more tests → retry

Step 5: Update Jira ticket
```

### Agent vs Prompt – Quyết Định Nhanh

```
Cần làm task X
        │
        ├── X có rẽ nhánh (if/else)?              ─┐
        ├── X có vòng lặp (loop/retry)?             ├── YES → Agent
        ├── X cần restrict tools (read-only)?       │
        ├── X cần spawn subagents?                 ─┘
        │
        └── Tất cả NO?
                │
                ├── X cần file kèm? → Skill (+ optional Prompt wrapper)
                └── X chỉ cần instructions? → Prompt
```

### Checklist quyết định

```
□ Workflow có if/else (branch theo ngôn ngữ, loại lỗi, ...)?    → agent
□ Workflow có loop (retry, iterate until done)?                  → agent
□ Cần AI KHÔNG được dùng một số tools (vd: read-only reviewer)? → agent
□ Workflow quá phức tạp, prompt sẽ rất dài và khó maintain?     → agent
□ Muốn có handoff button chuyển sang workflow tiếp theo?         → agent
□ Cần spawn subagents để làm việc song song?                     → agent
□ Không có điều nào trên? → Prompt hoặc Skill là đủ
```

---

## Phần 5 – Hook

### Định nghĩa
Shell commands tự động chạy tại **lifecycle events** của agent session.
**Không phụ thuộc vào AI** – chạy dù AI có nhớ hay không.
Đây là cơ chế enforcement, không phải guidance.

### File
```
.github/hooks/*.json
.github/hooks/scripts/*.py
```

### Sự Khác Biệt Cốt Lõi

```
Instructions: "AI ơi, đừng edit generated/"
→ AI CÓ THỂ quên hoặc bị override bởi prompt mạnh

Hook (PreToolUse): Script block mọi edit vào generated/
→ AI KHÔNG THỂ edit dù prompt thế nào – hệ thống chặn
```

### 8 Events và Mục Đích

| Event | Khi nào chạy | Dùng để |
|-------|------------|---------|
| `SessionStart` | Mở chat mới | Inject git branch, Jira ticket ID, project state |
| `UserPromptSubmit` | Mỗi khi gửi message | Audit log, validate input |
| `PreToolUse` | **Trước** khi tool chạy | **BLOCK** lệnh nguy hiểm, bảo vệ files |
| `PostToolUse` | **Sau** khi tool xong | Auto-format, chạy lint, inject thông tin |
| `Stop` | AI chuẩn bị báo "xong" | **BLOCK** nếu chưa đủ điều kiện done |
| `SubagentStart` | Subagent được spawn | Inject context cho subagent |
| `SubagentStop` | Subagent kết thúc | Aggregate results |
| `PreCompact` | Context sắp compact | Export state quan trọng |

### Khi nào dùng Hook

**Nguyên tắc:** Nếu bạn viết "AI nhớ phải làm X sau mỗi lần..." thì đó là Hook, không phải Instruction.

| Tình huống | Nên dùng |
|-----------|---------|
| "AI đừng edit generated/" | Instruction (guidance) |
| **Phải** block edit generated/ 100% | **Hook PreToolUse** |
| "AI nhớ format code sau khi sửa" | Instruction (guidance) |
| **Phải** format 100%, không bao giờ bỏ sót | **Hook PostToolUse** |
| "AI nhớ check coverage trước khi báo xong" | Instruction (guidance) |
| **Phải** block AI báo xong nếu coverage < 100% | **Hook Stop** |
| Inject context tự động mỗi session | **Hook SessionStart** |

### Cấu trúc Hook

```json
// .github/hooks/ten-hook.json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python3 .github/hooks/scripts/guard.py",
        "timeout": 10
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python3 .github/hooks/scripts/verify_done.py",
        "timeout": 60
      }
    ]
  }
}
```

```python
# Script PreToolUse – Block/Allow tool
import json, sys

data = json.load(sys.stdin)
tool_name = data.get("tool_name", "")
tool_input = data.get("tool_input", {})

# Block edit trong thư mục generated/
if tool_name in ["editFiles", "deleteFiles"]:
    files = tool_input.get("files", [])
    blocked = [f for f in files if "generated/" in f]
    if blocked:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Cannot edit generated files: {blocked}"
            }
        }))
        sys.exit(0)

print(json.dumps({"continue": True}))
```

```python
# Script Stop – Block nếu chưa đủ điều kiện
import json, sys, subprocess

data = json.load(sys.stdin)
if data.get("stop_hook_active"):          # Tránh infinite loop
    print(json.dumps({"continue": True}))
    sys.exit(0)

# Kiểm tra coverage
result = subprocess.run(["bash", "scripts/coverage.sh"],
                        capture_output=True, text=True)
import re
match = re.search(r'lines\.*:\s*([\d.]+)%', result.stdout)
coverage = float(match.group(1)) if match else 0

if coverage < 100.0:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "decision": "block",
            "reason": f"Coverage {coverage:.1f}% < 100%. Add more tests."
        }
    }))
else:
    print(json.dumps({"continue": True}))
```

### Checklist quyết định

```
□ Cần GUARANTEE điều gì đó xảy ra (không thể bỏ qua)?  → hook
□ Cần BLOCK AI trước khi nó thực hiện một action?       → hook PreToolUse
□ Cần chạy gì đó TỰ ĐỘNG sau mỗi lần AI edit file?     → hook PostToolUse
□ Cần đảm bảo AI không báo "xong" khi chưa đủ tiêu chí?→ hook Stop
□ Cần inject context vào đầu mỗi session tự động?       → hook SessionStart
□ Chỉ muốn nhắc AI nhớ làm gì đó? → instruction (không cần hook)
```

---

## Phần 6 – Flowchart Quyết Định Tổng Hợp

```
Tôi muốn làm gì?
        │
        ├─[A]─ AI cần biết thông tin này MỌI LÚC, không cần gọi
        │              → INSTRUCTION
        │              (copilot-instructions.md hoặc path instructions)
        │
        ├─[B]─ Tôi muốn GỌI một task cụ thể khi cần
        │              │
        │              ├── Task có rẽ nhánh (if/else)?          ──┐
        │              ├── Task có vòng lặp?                      │ YES
        │              ├── Cần restrict tools?                    ├──→ AGENT
        │              ├── Cần spawn subagents song song?         │
        │              └── Cần handoff sang workflow khác?      ──┘
        │                      │
        │                      │ NO (tuyến tính)
        │                      │
        │              ├── Task cần script/template/examples?
        │              │         YES → SKILL (+ optional Prompt wrapper)
        │              │         NO  → PROMPT
        │              │
        │              └── Prompt này gọi nhiều skills?
        │                        YES → PROMPT orchestrator
        │
        └─[C]─ Tôi muốn điều gì đó TỰ ĐỘNG xảy ra (không cần gọi)
                       │
                       ├── Chỉ muốn AI nhớ → INSTRUCTION
                       └── PHẢI đảm bảo, không được bỏ qua → HOOK
                                   │
                                   ├── Trước khi tool chạy → PreToolUse
                                   ├── Sau khi tool xong   → PostToolUse
                                   ├── Khi AI báo xong     → Stop
                                   └── Khi mở session      → SessionStart
```

---

## Phần 7 – Ứng Dụng Cho Công Việc Thực Tế

### Mapping Nhanh Cho LGEDV Engineer

| Công việc hàng ngày | Loại | File |
|--------------------|------|------|
| AI biết tôi làm C++/Java, AUTOSAR, Gerrit... | `instruction` | `copilot-instructions.md` |
| AI biết rules AUTOSAR khi edit file C++ | `instruction` | `cpp.instructions.md` |
| AI biết JUnit patterns khi viết test | `instruction` | `tests-java.instructions.md` |
| Đọc Jira ticket + tóm tắt | `prompt` | `read-ticket.prompt.md` |
| Soạn email phản hồi | `prompt` | `draft-email.prompt.md` |
| Soạn nội dung standup | `prompt` | `standup.prompt.md` |
| Tạo Jira ticket từ mô tả ngắn | `prompt` | `create-ticket.prompt.md` |
| Onboard module mới | `prompt` | `onboard-module.prompt.md` |
| Phân tích bug (có log/zip cần parse) | `skill` | `analyze-bug/` |
| Viết unit test C++ loop đến coverage | `skill` | `cpp-unit-test/` |
| Viết unit test Java/Kotlin | `skill` | `java-unit-test/` |
| Fix static issues (cần chạy scan tool) | `skill` | `fix-static-issues/` |
| Fix Coverity (cần REST API script) | `skill` | `coverity-fix/` |
| Viết 5-Whys post-mortem (cần template) | `skill` | `5-whys/` |
| Weekly report (cần report template) | `skill` | `weekly-report/` |
| Fix bug end-to-end (analyze→fix→test→doc) | `agent` | `bug-fixer.agent.md` |
| Implement feature (Jira→code→test→update) | `agent` | `feature-builder.agent.md` |
| Review code (read-only, không được edit) | `agent` | `code-reviewer.agent.md` |
| Viết test loop đến 100% (có branching C++/Java) | `agent` | `tdd-agent.agent.md` |
| Batch fix Coverity (checklist + loop) | `agent` | `coverity-fixer.agent.md` |
| Block edit vào generated/ folder | `hook` | `protect-generated.json` |
| Auto-format C++ sau mỗi lần agent edit | `hook` | `post-format.json` |
| Block agent báo xong nếu coverage < 100% | `hook` | `coverage-guard.json` |
| Block agent báo xong nếu còn static issues | `hook` | `static-guard.json` |
| Inject git branch + ticket ID vào context | `hook` | `inject-context.json` |

---

## Phần 8 – Anti-patterns Thường Gặp

### ❌ Dùng Instructions cho task-specific workflow
```markdown
<!-- WRONG: copilot-instructions.md -->
When asked to analyze a bug:
1. Read the Jira ticket
2. Download log files
3. Parse stack trace...

→ Đây là task-specific → nên là Prompt hoặc Skill
```

### ❌ Dùng Prompt khi cần loop
```markdown
<!-- WRONG: prompts/write-tests.prompt.md -->
Write unit tests, run coverage, if < 100% add more tests, loop until done.

→ "Loop until done" không phải tuyến tính → nên là Agent
```

### ❌ Dùng Instructions để enforce thay vì Hook
```markdown
<!-- WRONG: copilot-instructions.md -->
ALWAYS run clang-format after editing C++ files.

→ AI có thể quên → nên là Hook PostToolUse
```

### ❌ Tạo Skill khi không cần file kèm
```
WRONG: .github/skills/read-ticket/SKILL.md
  (chỉ có instructions, không có script/template/example)

→ Prompt đơn giản hơn và đủ dùng
```

### ❌ Dùng Agent khi workflow tuyến tính
```markdown
<!-- WRONG: agents/read-ticket.agent.md -->
---
name: Ticket Reader
tools: ['read']
---
Read a Jira ticket and summarize it.

→ Không có branching/loop/restrict → Prompt là đủ, Agent thừa
```

---

## Tóm Tắt Một Trang

```
┌──────────────┬────────────────────────────┬──────────────────────────────┐
│    Loại      │  Dùng khi                  │  Không dùng khi              │
├──────────────┼────────────────────────────┼──────────────────────────────┤
│ Instruction  │ AI cần biết mọi lúc        │ Task cụ thể, có script       │
│              │ Rules theo file type       │                              │
├──────────────┼────────────────────────────┼──────────────────────────────┤
│ Prompt       │ Task tuyến tính            │ Có if/else hay loop          │
│              │ Slash command nhanh        │ Cần file/script kèm          │
│              │ Orchestrate nhiều skills   │                              │
├──────────────┼────────────────────────────┼──────────────────────────────┤
│ Skill        │ Cần script/template/example│ Chỉ có instructions thuần    │
│              │ Dùng từ CLI/Background     │                              │
│              │ Tái sử dụng bởi nhiều      │                              │
│              │ prompts/agents             │                              │
├──────────────┼────────────────────────────┼──────────────────────────────┤
│ Agent        │ Có if/else, loop, retry    │ Workflow tuyến tính đơn giản │
│              │ Restrict tools             │                              │
│              │ Persona nhất quán          │                              │
│              │ Orchestrate subagents      │                              │
│              │ Handoff workflows          │                              │
├──────────────┼────────────────────────────┼──────────────────────────────┤
│ Hook         │ Phải GUARANTEE xảy ra      │ Chỉ muốn AI "nhớ"            │
│              │ Block action nguy hiểm     │ (→ dùng instruction thay)    │
│              │ Auto-run sau tool          │                              │
│              │ Block "done" khi chưa xong │                              │
└──────────────┴────────────────────────────┴──────────────────────────────┘
```
