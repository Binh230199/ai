# Agentic AI Workflow với GitHub Copilot — Research Chuyên Sâu (2026)

> **Mục tiêu**: Xây dựng hệ thống Agentic AI thay thế tối đa công việc hằng ngày của Software Engineer. Con người chỉ làm 2 việc: **viết/review Issue** và **approve/merge PR**. Mọi thứ còn lại — phân tích, thiết kế, code, test, doc, CI — do agents xử lý.
>
> **Phạm vi**: Platform-agnostic — áp dụng được cho Yocto, Android AOSP, Embedded Linux, hay bất kỳ môi trường nào. Không hard-code cho một platform cụ thể.

---

## 1. Kiến trúc tổng thể — Hai tầng Agent

Copilot có **hai tầng agent độc lập**, cần phân biệt rõ để thiết kế workflow đúng:

| Tầng | Tên | Chạy ở đâu | Trigger | Output |
|---|---|---|---|---|
| **Cloud** | Copilot Coding Agent | GitHub Actions (ephemeral sandbox) | GitHub Issue / `@copilot` mention / Copilot Chat | Pull Request |
| **Local** | Agent Mode (VS Code) | Máy local của developer | Chat prompt trong VS Code | Edit files trực tiếp + run terminal |

**Nguyên tắc thiết kế workflow**:
- Dùng **Agent Mode (local)** cho công việc cần tương tác nhanh: debug, POC, refactor nhỏ, viết test cho code đang mở.
- Dùng **Copilot Coding Agent (cloud)** cho công việc nặng, không muốn block máy: implement feature mới, fix bug từ backlog, cải thiện test coverage, update docs.
- Công việc lý tưởng là: **viết Issue → assign cho Coding Agent → review PR**.

---

## 2. Các Building Blocks Tùy Biến (Chính thức, đã verify)

Đây là 6 công cụ tùy biến chính thức theo [Copilot Customization Cheat Sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet):

| Công cụ | File / Vị trí | Kích hoạt | Dùng khi nào |
|---|---|---|---|
| **Custom Instructions** | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `AGENTS.md` | Tự động, luôn áp dụng | Standards, conventions, rules không bao giờ thay đổi |
| **Prompt Files** | `.github/prompts/*.prompt.md` | Thủ công (chọn trong chat) | Task lặp lại có input khác nhau mỗi lần (viết test, code review checklist) |
| **Custom Agents** | `.github/agents/AGENT-NAME.md` (repo) hoặc `agents/AGENT-NAME.md` trong repo `.github-private` (org) | Thủ công (chọn từ dropdown) | Persona chuyên biệt với tool hạn chế, persona riêng |
| **Agent Skills** | `.github/skills/<skill-name>/SKILL.md` (project) hoặc `~/.copilot/skills/<skill-name>/SKILL.md` (personal) | Tự động khi related | Workflow nhiều bước có script/resource đi kèm |
| **MCP Servers** | `mcp.json` (VS Code), repo settings (GitHub) | Tự động hoặc gọi tên tool | Kết nối external data/API/tools |
| **Hooks** | `.github/hooks/*.json` | Tự động tại lifecycle events | Validation, security check, logging, approve/deny tool use |

### 2.1 Custom Instructions — "DNA" của Agent

Custom instructions là lớp nền, luôn active. Đây là nơi encode **toàn bộ context bất biến** của project:

```markdown
<!-- .github/copilot-instructions.md -->
## Project Context
This is an embedded software project targeting automotive ECUs.
Build system: [specify per-repo]. Testing framework: [specify per-repo].

## Coding Standards
- Follow MISRA C:2012 for safety-critical modules
- All functions must have Doxygen headers
- No dynamic memory allocation in safety-critical paths

## Commit Convention
- Format: <type>(<scope>): <subject>
- Types: feat, fix, refactor, test, docs, ci

## Test Requirements
- Every new function must have unit tests
- Use AAA pattern (Arrange, Act, Assert)
- Coverage target: 80% line coverage minimum
```

**Tip**: Không dump toàn bộ code vào đây. Chỉ viết rules và context — Copilot sẽ tự dùng MCP tools để đọc code khi cần.

### 2.2 Custom Agents — Format Chính Xác

**File**: `.github/agents/AGENT-NAME.md` (plain Markdown, YAML frontmatter)

```markdown
---
name: implementer
description: Implements features from design specs using TDD. Writes production code and unit tests together.
tools:
  - codebase
  - editFiles
  - runCommands
  - terminal
---

You are a senior software engineer specializing in implementation.

## Your workflow
1. Read the design spec from the issue or attached document
2. Identify all files that need to be created or modified
3. Write unit tests FIRST (TDD red phase)
4. Implement code to make tests pass (TDD green phase)
5. Refactor while keeping tests green (TDD refactor phase)
6. Verify no regressions with `runCommands`

## Constraints
- Never skip tests
- Never modify files outside the task scope
- If you are unsure about the design, STOP and ask — do not guess
- Save a summary to `agent-output/implement-<date>.md`
```

**Lưu ý quan trọng từ official docs**:
- Tên file là `AGENT-NAME.md` (không phải `.agent.md`)
- `tools` list giới hạn agent chỉ dùng tools được phép (security hygiene)
- Default là agent có thể dùng tất cả tools nếu không khai báo `tools`
- Custom agents available ở: VS Code, JetBrains (preview), GitHub.com, Copilot CLI

### 2.3 Agent Skills — Reusable Playbooks

Skills là **folders chứa instructions + scripts**, Copilot tự load khi task liên quan. Đây là nơi encode "how to do X" cụ thể cho từng platform.

```
.github/skills/
├── build-validation/
│   ├── SKILL.md          ← instructions cho Copilot
│   └── scripts/
│       └── validate.sh   ← script thực thi
├── changelog-generator/
│   └── SKILL.md
└── static-analysis/
    ├── SKILL.md
    └── scripts/
        └── run-analysis.sh
```

**Ví dụ SKILL.md:**

```markdown
# Build Validation Skill

## When to use this skill
Use when you need to validate that a build succeeds after code changes.

## Steps
1. Run the validation script: `bash .github/skills/build-validation/scripts/validate.sh`
2. Parse the output for errors
3. If errors exist, report them in `agent-output/build-errors.md`
4. Never commit if validation fails

## Script behavior
The script accepts a TARGET env variable to specify build target.
Default: TARGET=all
```

**Đây là chỗ platform-specific logic đặt vào** — Skill `build-yocto`, `build-aosp`, `run-ctest`, `flash-target` đều có thể tạo riêng. Agent chọn đúng skill tự động dựa trên context.

### 2.4 Hooks — Control Plane của Agent

Hooks cho phép **intercept và control** hành vi agent tại các lifecycle events:

```
.github/hooks/
└── security-hooks.json
```

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {
        "type": "command",
        "bash": ".github/hooks/scripts/pre-tool-check.sh",
        "timeoutSec": 10
      }
    ],
    "sessionStart": [
      {
        "type": "command",
        "bash": "echo \"[$(date -u)] Session started\" >> logs/agent-audit.log"
      }
    ],
    "sessionEnd": [
      {
        "type": "command",
        "bash": ".github/hooks/scripts/cleanup-temp.sh",
        "timeoutSec": 30
      }
    ],
    "errorOccurred": [
      {
        "type": "command",
        "bash": "cat >> logs/agent-errors.jsonl"
      }
    ]
  }
}
```

**Hook types (theo official docs)**:
- `sessionStart` / `sessionEnd` — khởi tạo / cleanup environment
- `userPromptSubmitted` — log request cho audit
- `preToolUse` — **quan trọng nhất**: approve hoặc deny tool execution, block dangerous commands
- `postToolUse` — log kết quả, track metrics
- `agentStop` / `subagentStop` — callback khi agent hoàn thành
- `errorOccurred` — log và alert lỗi

**Cảnh báo**: Hooks chạy **synchronously** và block agent. Giữ execution time < 5 giây. Không log sensitive data.

### 2.5 Copilot Memory — Persistent Knowledge

Copilot Memory (public preview) cho phép agent **tích lũy hiểu biết về repo theo thời gian**:

- Memories là scoped facts về repo (cách handle DB connections, file coupling rules, patterns...)
- Tự validate lại trước khi dùng (check xem code vẫn tồn tại không)
- **Auto-delete sau 28 ngày** nếu không được validate lại
- Dùng bởi: Copilot Coding Agent, Copilot Code Review, Copilot CLI
- Enable trong: GitHub personal settings → Copilot → Copilot Memory

Thực tế: Memory giảm dần nhu cầu maintain custom instructions, vì Copilot tự học. Nhưng custom instructions vẫn cần cho **hard rules** (coding standards, security policies).

---

## 3. Agentic Workflow Architecture cho Software Engineer

### 3.1 Flow tổng thể: Issue → PR không cần intervention

```
[Bạn viết Issue]
      ↓
[Assign to Copilot Coding Agent]
      ↓ (GitHub Actions sandbox)
  ┌─────────────────────────────────┐
  │  1. Read issue + custom instructions + memories
  │  2. Explore codebase (MCP tools)
  │  3. Load relevant Skills
  │  4. Plan changes
  │  5. preToolUse hooks (security check)
  │  6. Implement (edit files)
  │  7. Run tests via terminal
  │  8. Fix failures (iterate)
  │  9. Security scan (built-in)
  │  10. Commit → Push → Open PR
  └─────────────────────────────────┘
      ↓
[Bạn nhận notification]
      ↓
[Review PR + comment corrections]
      ↓
[Copilot iterate theo comments]
      ↓
[Approve + Merge]
```

### 3.2 Subagents — Parallel Processing

Một custom agent có thể spawn **subagents** để xử lý song song. Subagents chạy trong isolated context, trả kết quả về main agent:

```
Main Agent (Implementer)
├── Subagent A: "Research how module X currently handles errors"
├── Subagent B: "Find all existing tests for this component"
└── Subagent C: "Check if there are open issues related to this"
     ↓ (all run in parallel)
Main Agent tổng hợp → implement
```

Subagents là **runtime process**, không cần cấu hình file. Main agent tự quyết định khi nào spawn. Bạn có thể explicit trong agent prompt: "Use subagents to research independently before implementing."

### 3.3 Workflow cho Automotive Software Engineer

```
Backlog Issues
(bug fix, new feature, tech debt,
 test coverage, docs, refactor)
        ↓
[Label + Assign to Custom Agent]
   - label: "bug" → Bug-Fix agent
   - label: "feature" → Implementer agent
   - label: "test" → Test-Coverage agent
   - label: "docs" → Docs agent
   - label: "security" → Security-Audit agent
        ↓
[Agent runs in cloud, bạn tiếp tục việc khác]
        ↓
[PR created with all changes]
        ↓
[Copilot Code Review auto-review]
        ↓
[Bạn review + testing output]
        ↓
[Approve / Request changes]
```

**Điểm mấu chốt**: Agents không biết bạn đang dùng Yocto hay AOSP cho đến khi bạn dạy chúng. Dạy qua 3 kênh:
1. **Custom instructions** — rules bất biến
2. **Agent Skills** — procedures platform-specific
3. **Copilot Memory** — tự học dần theo thời gian

---

## 4. Cấu Trúc File Repository — Platform-Agnostic Template

```
.github/
├── copilot-instructions.md       ← global rules (coding standards, conventions)
├── instructions/
│   ├── testing.instructions.md   ← test-specific rules
│   ├── security.instructions.md  ← security policies
│   └── documentation.instructions.md
├── agents/
│   ├── implementer.md            ← viết code + tests
│   ├── bug-fixer.md              ← debug + fix
│   ├── test-writer.md            ← tăng test coverage
│   ├── code-reviewer.md          ← review, suggest improvements
│   ├── security-auditor.md       ← read-only, chỉ audit
│   ├── docs-writer.md            ← README, API docs, changelogs
│   └── ci-debugger.md            ← debug CI/CD failures
├── prompts/
│   ├── write-unit-tests.prompt.md
│   ├── review-checklist.prompt.md
│   └── release-notes.prompt.md
├── skills/
│   ├── build-validation/
│   │   ├── SKILL.md
│   │   └── scripts/validate.sh   ← platform-specific, per-repo
│   ├── static-analysis/
│   │   ├── SKILL.md
│   │   └── scripts/run-analysis.sh
│   ├── test-runner/
│   │   ├── SKILL.md
│   │   └── scripts/run-tests.sh  ← CTest, GTest, pytest, etc.
│   └── changelog-generator/
│       └── SKILL.md
└── hooks/
    ├── audit-hooks.json           ← logging, compliance
    └── security-hooks.json        ← preToolUse safety checks

agent-output/                     ← artifacts từ agent runs (gitignored or tracked)
logs/                             ← agent audit logs
```

**Nguyên tắc platform-agnostic**: Custom instructions và agent profiles viết **generic**. Mọi thứ platform-specific (Yocto bitbake, AOSP make, CMake, etc.) đặt hết vào **Skills scripts**. Khi switch project, chỉ cần thay Skills scripts — không cần touch agents hay instructions.

---

## 5. MCP Servers — Mở Rộng Tool Set của Agent

MCP (Model Context Protocol) là standard mở cho phép agent gọi external tools. Cấu hình trong `mcp.json` hoặc VS Code settings.

**Recommended MCP servers cho Software Engineer:**

| MCP Server | Mục đích | Khi nào cần |
|---|---|---|
| `github` (built-in) | Đọc issues, PRs, comments, tìm code | Luôn cần — context về project |
| `filesystem` | Đọc/ghi file ngoài repo scope | Khi cần access build output, logs |
| `fetch` | Gọi HTTP API | Đọc docs kỹ thuật, spec sheets |
| Custom MCP | Internal CI/CD system, JIRA, Gerrit, code servers | Tùy infrastructure của team |

```json
// .vscode/mcp.json (dùng trong Agent Mode)
{
  "servers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    },
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
    }
  }
}
```

**Limitation quan trọng**: Copilot Coding Agent (cloud) chỉ access được repo hiện tại theo default. Muốn cross-repo context, phải cấu hình MCP server với broader access.

---

## 6. Chiến Lược Tối Ưu Quota Premium Requests

**Thực tế về cost**:
- Pro: ~300 premium requests/tháng
- Pro+: ~1.500/tháng
- Overage: $0.04/request
- Mỗi Coding Agent session = **1 request** (nhưng có model multiplier)
- Chat + Agent Mode cũng tính premium request

**Phân luồng theo model multiplier**:

| Task Type | Model Đề Xuất | Multiplier | Dùng khi |
|---|---|---|---|
| Explain code, answer questions | GPT-4.1 mini | 0x (free) | Research, Q&A |
| Small refactor, quick fix | Claude Haiku 4.5 | 0.33x | Nhiều task nhỏ |
| Complex implementation | Claude Sonnet | 1x | Standard tasks |
| Full feature implementation | Claude Opus / GPT-4.1 | 1x–2x | Chỉ khi thực sự cần |

**Chiến lược tiết kiệm**:
1. **Scope issue nhỏ**: Thay vì 1 issue lớn, split thành 3-5 issues nhỏ cụ thể → agent ít bị confused, ít re-run hơn.
2. **Custom instructions tốt**: Agent không cần hỏi lại nhiều lần.
3. **Skills thay cho prompting**: Thay vì giải thích "cách build", viết skill script → agent dùng trực tiếp.
4. **Copilot Memory**: Giảm cần context dump theo thời gian.
5. **Agent Mode cho task local**: Không tốn GitHub Actions minutes.
6. **Monitor**: GitHub → Settings → Billing → Copilot usage.

---

## 7. Limitations Thực Tế (Không Bỏ Qua)

Đây là những giới hạn chính thức, ảnh hưởng trực tiếp đến thiết kế workflow:

| Limitation | Ảnh hưởng | Giải pháp |
|---|---|---|
| Chỉ hoạt động với **GitHub-hosted repos** | Repo trên GitLab, Gerrit, internal server không dùng được Coding Agent | Dùng Agent Mode (local) cho repos không trên GitHub |
| **Một repo một lần** — không thể thay đổi nhiều repo trong 1 run | Cross-repo changes phải làm thủ công | Split task, mỗi task chỉ touch 1 repo |
| **Chỉ push vào branch `copilot/*`** — không commit thẳng vào main | Luôn phải tạo PR, không thể auto-merge hoàn toàn | Design workflow quanh PR review |
| Hooks chạy **synchronous**, block execution | Hook chậm = agent chậm | Giữ < 5 giây; dùng file append thay vì sync I/O |
| **Memories auto-delete sau 28 ngày** nếu không được re-validate | Knowledge decay | Dùng Custom instructions cho rules quan trọng; không rely 100% vào Memory |
| Custom agents trong **JetBrains/Eclipse/Xcode còn preview** | Có thể unstable trên non-VS Code IDEs | Dùng VS Code làm primary IDE cho agentic workflow |
| Không thể **approve/merge** PR của chính mình | Cần ít nhất 1 người có write access approve | Design tốt cho flow review của bạn |
| **Content exclusions không áp dụng** cho Coding Agent | Copilot sẽ thấy và có thể modify excluded files | Dùng `preToolUse` hook để block access vào sensitive files |

---

## 8. Roadmap Triển Khai Thực Tế (4 Giai Đoạn)

### Giai đoạn 1 — Nền tảng (Tuần 1-2)
- [ ] Tạo `.github/copilot-instructions.md` — encode coding standards hiện tại
- [ ] Enable Copilot Memory trong GitHub settings
- [ ] Tạo 2-3 Prompt Files cho task lặp lại nhiều nhất (viết test, review checklist)
- [ ] Test Agent Mode trong VS Code với task nhỏ để hiểu behavior

### Giai đoạn 2 — Custom Agents (Tuần 3-4)
- [ ] Tạo `implementer.md` agent — bắt đầu đơn giản, tinh chỉnh dần
- [ ] Tạo `bug-fixer.md` agent
- [ ] Test với bugs nhỏ từ backlog — học cách viết Issue tốt để agent hiểu đúng
- [ ] Tạo `logs/` và `agent-output/` folder để track agent work

### Giai đoạn 3 — Skills & Hooks (Tuần 5-6)
- [ ] Tạo `build-validation` skill với script phù hợp platform hiện tại
- [ ] Tạo `test-runner` skill
- [ ] Implement basic `sessionStart`/`sessionEnd` hooks cho audit logging
- [ ] Thêm `preToolUse` hook để block commands nguy hiểm

### Giai đoạn 4 — Full Automation (Tuần 7+)
- [ ] Tạo đủ bộ agents (test-writer, code-reviewer, docs-writer, ci-debugger)
- [ ] Cấu hình GitHub label triggers để auto-assign đúng agent
- [ ] Tinh chỉnh Custom instructions dựa trên patterns lỗi của agent
- [ ] Enable Copilot Code Review tự động trên mọi PR của Copilot
- [ ] Review metrics hàng tuần: PR merge rate, iteration count, request usage

---

## 9. Tips Viết Issue Tốt Cho Agent

Chất lượng Issue quyết định chất lượng output. Đây là template:

```markdown
## Context
[Mô tả context kỹ thuật: module nào, hiện tại làm gì]

## Problem / Goal
[Vấn đề cụ thể cần giải quyết / feature cần thêm]

## Acceptance Criteria
- [ ] [Tiêu chí 1 — cụ thể, measurable]
- [ ] [Tiêu chí 2]
- [ ] All new code has unit tests
- [ ] No regressions in existing tests

## Constraints
- [Bất kỳ ràng buộc kỹ thuật nào: file không được sửa, API không được thay đổi, ...]

## Resources
- Related file: `src/module/file.c`
- Spec: [link nếu có]
```

**Nguyên tắc**: Acceptance Criteria là **hợp đồng** với agent. Agent sẽ tự verify trước khi mở PR. Viết càng cụ thể, agent càng ít cần iteration.

---

## 10. Nguồn Tham Khảo Chính Thức

- [About Copilot Coding Agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent)
- [About Custom Agents](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-custom-agents)
- [About Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [About Hooks](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-hooks)
- [About Copilot Memory](https://docs.github.com/en/copilot/concepts/agents/copilot-memory)
- [Customization Cheat Sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet)
- [Customization Library](https://docs.github.com/en/copilot/tutorials/customization-library)
- [github/awesome-copilot](https://github.com/github/awesome-copilot) — community skills collection
