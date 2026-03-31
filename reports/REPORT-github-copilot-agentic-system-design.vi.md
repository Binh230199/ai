# Xây Dựng Hệ Thống Agentic AI Chuyên Nghiệp Trên GitHub Copilot

## Tóm tắt điều hành

Nếu muốn GitHub Copilot làm việc như một kỹ sư tự động thay vì một chatbot biết code, tư duy thiết kế phải đổi từ "viết prompt tốt hơn" sang "xây runtime agentic tốt hơn". Một hệ thống như vậy cần ít nhất sáu lớp phối hợp với nhau:

1. `Control plane`: agent điều phối, todo, queue, trạng thái công việc, tiêu chí hoàn thành.
2. `Execution plane`: các worker chuyên biệt, tool restrictions, subagent handoff.
3. `Knowledge plane`: instructions, skills, playbook, runbook, issue manifest, memory bền vững.
4. `Policy plane`: hooks cưỡng chế hành vi, chặn thao tác nguy hiểm, ép verify trước khi đóng việc.
5. `Integration plane`: MCP/API, shell, test runner, coverage tools, static analysis servers.
6. `Recovery plane`: checkpoint, retry loop, batch ledger, resume workflow, final gating.

Thiết kế đúng không chỉ giúp Copilot làm được việc khó như fix hàng loạt static-analysis issues hoặc viết unit test coverage cao; nó còn quyết định hệ thống có đi tới đích một cách ổn định hay sa vào tình trạng "gà mắc tóc": đọc nhiều, sửa lung tung, verify yếu, hết token, và dở dang giữa chừng.

Tài liệu này tổng hợp các pattern thực chiến để triển khai một hệ thống agentic trên GitHub Copilot, dựa trên hai nguồn chính:

- Hiểu biết về primitives mà Copilot hỗ trợ: instructions, prompts, hooks, agents, skills, tools, MCP, subagents.
- Các bài học rút ra từ kiến trúc của Claude Code: query runtime chịu lỗi, scheduler công cụ, multi-agent orchestration, memory tự bảo trì, và productization ở mức hệ thống.

## 1. Luận điểm trung tâm

Một hệ thống agentic hiệu quả không được tối ưu cho câu trả lời đẹp. Nó phải được tối ưu cho tỷ lệ hoàn thành tác vụ từ đầu tới cuối.

Điều đó dẫn tới năm nguyên tắc kiến trúc:

1. `Completion-first`: chỉ coi công việc hoàn thành khi tiêu chí đầu ra được thỏa và đã verify.
2. `Manifest-driven`: mọi đơn vị công việc phải có manifest, trạng thái, owner, bằng chứng verify.
3. `Specialized roles`: không có một agent làm mọi thứ. Mỗi agent chỉ giữ một vai trò rõ ràng.
4. `Deterministic enforcement`: các chỗ quan trọng phải dùng hooks, không chỉ dùng instructions.
5. `Progressive context`: kiến thức tổng quát ở instructions, kiến thức nghiệp vụ ở skills, dữ liệu runtime ở artifacts/runbooks.

## 2. Khung năng lực thực tế của GitHub Copilot

Để thiết kế đúng, phải dùng đúng primitive cho đúng việc.

### 2.1. Workspace instructions

`copilot-instructions.md` hoặc `AGENTS.md` là nơi đặt luật nền tảng của cả workspace:

- coding standards
- build/test commands
- quy ước verify bắt buộc
- nguyên tắc dùng subagents
- quy tắc kết thúc công việc

Không nên nhồi toàn bộ runbook vào đây. Đây là lớp chính sách chung, áp dụng cho mọi task.

### 2.2. File-specific instructions

`.instructions.md` là nơi chứa policy hoặc guidance theo domain cụ thể, ví dụ:

- static analysis remediation
- C++ testing conventions
- mock strategy
- secure refactoring
- migration safety rules

Đây là lớp phù hợp nhất để encode kinh nghiệm đội ngũ theo dạng "Use when..." để model tự phát hiện khi cần.

### 2.3. Prompts

`.prompt.md` phù hợp cho tác vụ đơn tiêu điểm, ví dụ:

- `/fix-coverity-batch`
- `/write-cpp-tests`
- `/summarize-uncovered-lines`

Prompt không phải là workflow engine. Nó chỉ là cửa vào tốt cho một workflow.

### 2.4. Custom agents

`.agent.md` là nơi tạo các vai chuyên biệt với tool restrictions riêng:

- orchestrator
- issue-researcher
- code-fixer
- verifier
- test-strategist
- coverage-triager

Đây là primitive quan trọng nhất nếu muốn có multi-agent thực sự hiệu quả.

### 2.5. Skills

`SKILL.md` dùng cho workflow lặp lại, có procedure và tài nguyên đi kèm. Trong bài toán của bạn, skills là nơi nên chứa:

- rule remediation guides
- test harness setup playbooks
- command templates
- checklists để verify
- scripts hỗ trợ bóc dữ liệu thành artifacts

### 2.6. Hooks

Hooks là lớp cưỡng chế, không phải lớp gợi ý. Đây là chỗ quyết định hệ thống có thực chiến hay không.

Nên dùng hooks cho các việc như:

- chặn lệnh nguy hiểm hoặc quá rộng
- yêu cầu xin xác nhận với tool nhất định
- auto-run static analysis/test subset sau mỗi lần edit
- ghi lại touched files
- tạo session summary hoặc resume state khi agent dừng

### 2.7. MCP

MCP là cầu nối để agent lấy dữ liệu có cấu trúc từ hệ thống ngoài. Đây là con đường đúng cho các bài toán kiểu:

- lấy issue từ Coverity
- lấy rule docs
- query build metadata
- chạy internal quality gates
- lấy baseline coverage hoặc publish results

Không nên để agent scrape dữ liệu kiểu thủ công nếu có thể nhận JSON đã chuẩn hóa qua MCP/API.

### 2.8. Memory

Đừng đặt cược vào trí nhớ ngầm của chat. Trong hệ thống thực chiến, memory phải được ngoại hóa.

Nên tổ chức memory thành ba lớp:

- `Stable memory`: instructions, skills, permanent playbooks.
- `Project memory`: `artifacts/runbooks/*.md`, issue manifests, coverage manifests.
- `Session memory`: summary file và checkpoint file được cập nhật bằng hooks hoặc worker.

## 3. Bài học lớn rút ra từ Claude Code và cách ánh xạ sang Copilot

Từ việc mổ xẻ Claude Code, có thể rút ra các bài học rất thực dụng.

### 3.1. Bài học 1: Query loop phải có recovery, không được tin vào một turn duy nhất

Claude Code mạnh vì nó không coi một lượt model là đơn vị hoàn thành. Nó có retry, compaction, continuation, fallback, budget checks.

Ánh xạ sang Copilot:

- Orchestrator phải làm việc theo batch và checkpoint.
- Mỗi batch phải có file trạng thái.
- Sau mỗi worker run, phải ghi lại `done / failed / blocked / retry`.
- Nếu phiên bị ngắt, agent mới vẫn có thể resume từ runbook.

### 3.2. Bài học 2: Tool scheduling là vấn đề hệ thống

Claude Code phân biệt tool concurrency-safe và state-modifying. Điều đó tránh xung đột và giảm latency.

Ánh xạ sang Copilot:

- Chỉ cho nhiều subagents chạy song song ở pha nghiên cứu hoặc verify đọc-only.
- Pha sửa mã phải partition theo file ownership hoặc module ownership.
- Không cho hai fixer agents sửa cùng cụm file nếu không có isolation rõ ràng.

### 3.3. Bài học 3: Forked workers chỉ hiệu quả khi prompt của chúng hẹp và context của chúng sạch

Claude Code dùng forked agents với context tách biệt, prompt cache sharing và nhiệm vụ cực rõ.

Ánh xạ sang Copilot:

- Mỗi custom agent chỉ làm một vai trò.
- Tool set càng nhỏ càng tốt.
- Prompt cho subagent phải self-contained, có file path, mục tiêu, và tiêu chí done.
- Không dùng agent kiểu Swiss-army knife.

### 3.4. Bài học 4: Memory phải được tự bảo trì

Claude Code có extract memories và auto-dream. Bản chất của ý tưởng này là: những gì hệ thống học được phải được chuyển thành knowledge bền vững, không để thất lạc theo chat history.

Ánh xạ sang Copilot:

- Sau mỗi batch lớn, ghi ra `artifacts/lessons/*.md` hoặc cập nhật skill/reference.
- Nếu một rule Coverity lặp lại nhiều lần, biến nó thành remediation playbook trong skill.
- Nếu một kiểu mock C++ lặp lại nhiều lần, biến nó thành test template/reference.

### 3.5. Bài học 5: Chất lượng đến từ productization, không chỉ từ prompt engineering

Claude Code có feature gates, startup profiling, analytics, permission fences. Điểm chung là mọi thứ quan trọng đều được làm thành cơ chế.

Ánh xạ sang Copilot:

- Quy tắc không cho sửa file ngoài phạm vi phải ở hook.
- Verify bắt buộc phải ở hook hoặc explicit verifier agent gate.
- Tiêu chí đóng task phải được encode vào prompt và checklist, không để model tự phán đoán mơ hồ.

## 4. Kiến trúc đề xuất cho một hệ thống agentic chuyên nghiệp trên Copilot

### 4.1. Sơ đồ kiến trúc

```text
User / External trigger / MCP event
    -> Prompt or skill entrypoint
        -> Orchestrator agent
            -> load instructions + relevant skills
            -> create work manifest + todo
            -> spawn researcher / fixer / verifier agents
            -> update runbook and completion ledger
            -> repeat until exit criteria pass

Policy hooks
    -> PreToolUse: deny, ask, narrow scope
    -> PostToolUse: auto-verify, update touched files
    -> Stop/SubagentStop: persist summaries and results

Artifacts
    -> issues.json / batches.json / coverage.json
    -> runbook.md / touched-files.json / final-report.md

Integrations
    -> MCP Coverity / issue server / docs server
    -> build, test, coverage tools
    -> repo-local scripts
```

### 4.2. Các vai trò agent

Một hệ thống thực chiến tối thiểu nên có bốn vai trò.

#### Orchestrator

Nhiệm vụ:

- hiểu yêu cầu
- lập kế hoạch theo batch
- spawn subagents đúng vai
- quyết định khi nào retry hoặc repartition
- tổng hợp kết quả cuối cùng

Tool set nên có:

- `read`
- `search`
- `todo`
- `agent`
- MCP đọc manifest hoặc issue queues

Không nên cho orchestrator `edit` hoặc `execute` mặc định. Nếu nó vừa chỉ huy vừa sửa trực tiếp, hệ thống rất nhanh mất kỷ luật.

#### Researcher

Nhiệm vụ:

- đọc code và tài liệu
- xác định root cause
- tìm strategy fix hoặc test design
- tạo spec ngắn gọn cho fixer/test-writer

Tool set:

- `read`
- `search`
- `web` hoặc MCP docs nếu cần

#### Fixer / Test Writer

Nhiệm vụ:

- sửa code hoặc viết test theo spec
- chỉ chạm vào phạm vi đã chỉ định
- ghi rõ đã sửa gì và còn blocker gì

Tool set:

- `read`
- `search`
- `edit`
- `execute` nếu cần build/test cục bộ nhỏ

#### Verifier

Nhiệm vụ:

- chạy kiểm tra độc lập
- xác nhận không có regression
- đối chiếu issue count hoặc coverage target

Tool set:

- `read`
- `search`
- `execute`
- MCP để query hệ thống kiểm định ngoài nếu có

Verifier không nên có quyền `edit`, trừ khi bạn cố tình cho nó tạo báo cáo artifacts.

## 5. Layout triển khai nên dùng trong repo

Một workspace kiểu production nên có cấu trúc tối thiểu như sau:

```text
.github/
  copilot-instructions.md
  hooks/
    policy.json
  instructions/
    static-analysis.instructions.md
    cpp-testing.instructions.md
    verification.instructions.md
  agents/
    orchestrator.agent.md
    issue-researcher.agent.md
    code-fixer.agent.md
    verifier.agent.md
    test-strategist.agent.md
    coverage-verifier.agent.md
  prompts/
    fix-coverity-batch.prompt.md
    write-cpp-tests.prompt.md
  skills/
    coverity-batch-fix/
      SKILL.md
      references/
        remediation-patterns.md
        batching-strategy.md
      assets/
        batch-report-template.md
    cpp-unit-test-coverage/
      SKILL.md
      references/
        mock-patterns.md
        coverage-loop.md
      assets/
        test-matrix-template.md

artifacts/
  coverity/
  testing/
  session/
```

Điểm mấu chốt là `.github/` chứa kiến thức và policy, còn `artifacts/` chứa state runtime.

## 6. Những pattern quan trọng nhất để hệ thống không bị "gà mắc tóc"

### Pattern 1: Orchestrator chỉ điều phối, không trực tiếp lao vào sửa

Nếu orchestrator cũng là fixer, nó sẽ mất cái nhìn toàn cục, không giữ được queue, không biết tiến độ batch nào đang dở, và dễ bỏ quên việc verify.

Nguyên tắc:

- orchestrator giữ manifest và todo
- worker làm một việc cụ thể
- verifier xác nhận độc lập

### Pattern 2: Mọi workflow lớn đều phải manifest-driven

Ví dụ file manifest cho batch fixing:

```json
{
  "jobId": "coverity-2026-03-31-001",
  "objective": "Fix all outstanding Coverity issues for module X",
  "exitCriteria": {
    "remainingIssues": 0,
    "buildStatus": "pass",
    "testsStatus": "pass"
  },
  "batches": [
    {
      "id": "batch-rule-unsafe-cast",
      "status": "pending",
      "issueIds": ["CID-1001", "CID-1002"],
      "owner": null,
      "evidence": []
    }
  ]
}
```

Không có manifest thì model rất dễ tự huyễn hoặc rằng mình đã "xử lý gần hết".

### Pattern 3: Batch theo root cause, không batch mù theo số lượng

Đừng chia việc kiểu mỗi worker 20 issue ngẫu nhiên. Hãy batch theo:

- rule type
- module
- risk profile
- same root cause pattern

Lợi ích:

- giảm context switching
- tái sử dụng reasoning
- giảm token
- giảm xác suất fix không nhất quán

### Pattern 4: Research trước, write sau

Với các việc có rủi ro như static-analysis remediation hoặc test harness cho C++, nên tách hẳn pha research và pha write.

Research output phải là một spec có cấu trúc:

- files liên quan
- nguyên nhân kỹ thuật
- strategy fix/test
- constraints
- expected verification

Không cho fixer tự mò từ đầu nếu bài toán rủi ro cao.

### Pattern 5: Verify-before-close là luật bắt buộc

Không bao giờ cho hệ thống kết thúc vì model nói "đã xong". Chỉ đóng khi verifier hoặc hook đã tạo bằng chứng:

- build pass
- tests pass
- analyzer issue count giảm như kỳ vọng
- coverage đạt target
- không có file ngoài phạm vi bị sửa

### Pattern 6: Worker output phải ngắn, cấu trúc, và có actionability

Yêu cầu output chuẩn cho worker:

```text
Scope:
- batch / files / issue ids

Findings:
- root cause
- selected fix strategy

Changes:
- files touched
- why this fix is safe

Verification:
- commands run
- result

Remaining risks:
- blockers or follow-up
```

Nếu để worker kể chuyện dài, orchestrator rất tốn token để bóc ý chính.

### Pattern 7: Hạn chế context bằng artifacts thay vì chat dài

Thay vì nhồi toàn bộ issue list hoặc coverage report vào chat, hãy chuẩn hóa chúng thành file artifacts:

- `issues.json`
- `batches.json`
- `coverage-summary.json`
- `uncovered-lines.json`
- `runbook.md`

Agent đọc file khi cần. Đây là cách tiết kiệm token hiệu quả nhất.

### Pattern 8: Kinh nghiệm phải đóng gói thành skill, không lặp lại qua prompt tay

Một remediation guide tốt hoặc một C++ mock strategy tốt nên nằm trong skill/references, không nên copy-paste lại mỗi lần chat.

Khi lặp lại đủ nhiều, hãy nâng cấp:

- từ chat note -> reference doc
- từ reference doc -> skill
- từ skill -> hook hoặc policy nếu cần cưỡng chế

## 7. Phân vai cho từng primitive trong hệ thống thực chiến

### 7.1. `copilot-instructions.md`

Đây là nơi đặt hiến pháp của agentic system. Ví dụ:

```markdown
# Agentic System Rules

## Completion Contract
- Do not declare success without verification evidence.
- For batch jobs, completion requires manifest exit criteria to be satisfied.

## Delegation Rules
- Use subagents for research, implementation, and verification.
- Do not let two writer agents modify the same file set concurrently.

## Evidence Rules
- Every completed batch must record commands run and outcomes.
- Persist runtime state in artifacts rather than long chat summaries.
```

### 7.2. `static-analysis.instructions.md`

Đây là nơi encode kinh nghiệm fix static analysis:

```markdown
---
description: "Use when fixing static analysis findings, Coverity defects, null dereference, resource leak, unsafe cast, taint issues, or large remediation batches."
---

# Static Analysis Remediation

- Fix root causes, not warning texts.
- Prefer semantically safe edits over warning suppression.
- Group issues by root cause before editing.
- Re-run the relevant analysis or local proxy check after each batch.
- Record issue ids, touched files, and evidence in artifacts.
```

### 7.3. `cpp-testing.instructions.md`

Đây là nơi encode chiến lược viết unit test C++:

```markdown
---
description: "Use when writing C++ unit tests, setting up gtest or gmock, creating mocks, improving branch coverage, or driving coverage to a target."
---

# C++ Testing Rules

- Define the test scope and coverage target before writing tests.
- Prefer seam-based mocking over invasive production refactors.
- Every test file must include a coverage intention note in the runbook.
- Do not claim 100% coverage without command output and coverage artifacts.
```

### 7.4. Custom agents

Ví dụ `orchestrator.agent.md`:

```markdown
---
description: "Use when coordinating multi-step engineering work, batching issues, assigning subagents, and closing work only after verification."
tools: [read, search, todo, agent]
agents: [issue-researcher, code-fixer, verifier, test-strategist, coverage-verifier]
user-invocable: true
---

You are the orchestration layer for engineering automation.

## Responsibilities
- Convert user goals into manifests, batches, and exit criteria.
- Delegate work to specialized subagents.
- Never edit code directly.
- Do not declare completion without independent verification evidence.

## Workflow
1. Build or update the work manifest.
2. Spawn research agents for unclear or risky areas.
3. Spawn implementation agents on isolated batches.
4. Spawn verifier agents.
5. Update the runbook and continue until exit criteria are met.
```

### 7.5. Skills

Ví dụ `coverity-batch-fix/SKILL.md`:

```markdown
---
name: coverity-batch-fix
description: "Fix Coverity or static-analysis issues in batches. Use for issue intake, grouping by root cause, creating manifests, applying remediation patterns, and verifying zero remaining findings."
---

# Coverity Batch Fix

## When to Use
- Many static-analysis findings must be remediated end-to-end
- Findings can be fetched via MCP or API

## Procedure
1. Fetch issues and normalize them into artifacts/coverity/issues.json.
2. Partition into batches by rule, module, and risk.
3. Research the fix strategy for one batch.
4. Apply changes only within the assigned scope.
5. Verify locally and re-check issue counts.
6. Continue until remainingIssues == 0.

## References
- [Remediation patterns](./references/remediation-patterns.md)
- [Batching strategy](./references/batching-strategy.md)
```

### 7.6. Hooks

Ví dụ `policy.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python scripts/hooks/pre_tool_guard.py",
        "timeout": 10
      }
    ],
    "PostToolUse": [
      {
        "type": "command",
        "command": "python scripts/hooks/post_tool_verify.py",
        "timeout": 30
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python scripts/hooks/write_session_summary.py",
        "timeout": 15
      }
    ]
  }
}
```

## 8. Hook strategy để biến Copilot thành hệ thống đáng tin cậy

### 8.1. PreToolUse guard

PreToolUse nên làm ba việc:

1. từ chối lệnh phá hoại hoặc quá rộng
2. ép hỏi lại nếu agent chạm tới vùng nhạy cảm
3. ghi metadata để theo dõi worker đang làm gì

Ví dụ rules nên chặn:

- xoá hàng loạt file ngoài phạm vi
- chỉnh sửa toàn repo khi job chỉ nhắm một module
- chạy lệnh network hoặc deploy khi job là static analysis
- tự sửa chính hook hoặc policy files mà không có approval

### 8.2. PostToolUse verify

Đây là hook quan trọng nhất cho chất lượng. Sau các hành động `edit` hoặc `execute`, hook có thể:

- đọc danh sách touched files
- xác định test command hoặc static check tương ứng
- chạy verify ngắn cho phần vừa đổi
- ghi kết quả vào artifact

Không nên chạy test suite toàn cục sau từng edit. Hãy chạy verify theo phạm vi:

- file-level
- module-level
- batch-level

### 8.3. Stop / SubagentStop summary

Khi subagent kết thúc, nên buộc nó hoặc hook ghi ra một summary file chuẩn hóa. Lợi ích:

- orchestrator có thể resume mà không đọc lại toàn chat
- worker mới có thể kế thừa đúng trạng thái
- giảm token cho các vòng sau

## 9. Chiến lược tiết kiệm token và premium requests

Tối ưu chi phí không đến từ việc yêu model "hãy ngắn gọn". Nó đến từ thiết kế luồng làm việc.

### 9.1. Dùng research agent đọc ít, không cho writer đọc lại toàn bộ bối cảnh

Research agent bóc yêu cầu và viết spec ngắn. Writer chỉ nhận:

- batch id
- files liên quan
- strategy fix/test
- constraints
- exit criteria

Như vậy writer không phải ngốn token để đọc issue backlog lớn.

### 9.2. Đặt dữ liệu nặng vào file artifacts

Các file JSON/Markdown cho issues, coverage, batch report, verifier output luôn rẻ hơn việc copy vào chat.

### 9.3. Duy trì worker lâu hơn thay vì spawn lại liên tục

Nếu Copilot session/agent cho phép continue subagent, nên tái sử dụng worker đang có ngữ cảnh thay vì mở worker mới cho từng correction nhỏ.

### 9.4. Batch theo tri thức có thể tái sử dụng

Nếu 50 issue cùng rule, hãy nghiên cứu rule một lần, fix nhiều lần.

### 9.5. Đóng gói playbook vào skill

Skill là cách hiệu quả để tránh copy-paste remediation guide/test strategy mỗi lần.

### 9.6. Không lạm dụng `applyTo: "**"`

Chỉ những luật thật sự toàn cục mới nên luôn được nạp. Còn lại phải để on-demand.

### 9.7. Dùng MCP để lấy dữ liệu chuẩn hóa, không bắt agent parse output lộn xộn

Output càng structured, reasoning càng ít lãng phí.

## 10. Mẫu workflow chuẩn cho mọi bài toán tự động hóa lớn

Một workflow bền vững nên theo khung sau:

### Bước 1. Intake

- nhận mục tiêu
- tạo manifest
- định nghĩa exit criteria định lượng

### Bước 2. Partition

- chia batch theo root cause hoặc domain
- xác định batch nào được chạy song song

### Bước 3. Research

- spawn read-only agents
- sinh spec ngắn cho từng batch khó

### Bước 4. Implement

- spawn writer agents
- mỗi agent một scope

### Bước 5. Verify

- chạy local verification
- chạy external verification qua MCP/API nếu cần

### Bước 6. Reconcile

- cập nhật manifest
- nếu còn issue/gap, quay về Bước 2 hoặc Bước 3

### Bước 7. Close

- chỉ đóng khi manifest exit criteria đạt
- xuất final report có evidence

## 11. Các anti-pattern phá hỏng hệ thống agentic

1. `Một agent làm tất`: quá nhiều tool, quá nhiều role, output mơ hồ.
2. `Không có manifest`: không biết đã làm tới đâu, không biết còn gì.
3. `Chốt việc bằng lời nói`: không có verify độc lập.
4. `Hook quá nặng`: block session quá lâu, UX rất tệ.
5. `Writer agents đụng cùng file`: tạo conflict và reasoning lệch.
6. `Prompt dài như hợp đồng`: lặp lại cùng kiến thức thay vì skill/reference.
7. `Không có resume state`: phiên gián đoạn là làm lại từ đầu.
8. `Đuổi theo 100% coverage một cách mù quáng`: tạo test vô nghĩa hoặc overfit implementation.

## 12. Kế hoạch triển khai thực tiễn theo từng giai đoạn

### Giai đoạn 1: Tạo nền điều phối tối thiểu

- viết `copilot-instructions.md`
- tạo `orchestrator.agent.md`, `code-fixer.agent.md`, `verifier.agent.md`
- thêm `verification.instructions.md`
- tạo `artifacts/` layout

Mục tiêu: có thể chạy workflow researcher -> fixer -> verifier cho một batch nhỏ.

### Giai đoạn 2: Thêm hooks cưỡng chế

- thêm `PreToolUse` guard
- thêm `PostToolUse` verify cục bộ
- thêm `Stop` summary

Mục tiêu: hệ thống bớt phụ thuộc vào việc model "nhớ ngoan".

### Giai đoạn 3: Đóng gói domain knowledge

- tạo skill cho static analysis
- tạo skill cho C++ unit test/coverage
- thêm references và templates

Mục tiêu: giảm token, tăng tính lặp lại và chất lượng ổn định.

### Giai đoạn 4: Tích hợp MCP/API

- lấy issues từ Coverity
- lấy rule docs
- lấy coverage baseline / publish artifacts

Mục tiêu: agent làm việc trên dữ liệu cấu trúc thật, không copy tay.

### Giai đoạn 5: Batch automation ở quy mô lớn

- orchestrator đọc manifest lớn
- tự chia batch
- spawn nhiều worker theo phase
- verifier reconcile toàn cục

Mục tiêu: từ một assistant nâng cấp thành hệ thống tự động hóa kỹ thuật.

## 13. Checklist thiết kế trước khi đưa vào dùng thật

- Đã định nghĩa exit criteria định lượng chưa?
- Đã tách orchestrator khỏi writer chưa?
- Đã có verifier độc lập chưa?
- Đã có artifacts cho runtime state chưa?
- Đã có hook guard cho thao tác nguy hiểm chưa?
- Đã có strategy resume nếu session bị ngắt chưa?
- Đã đóng gói kiến thức lặp lại thành skill/reference chưa?
- Đã giới hạn tool theo role chưa?
- Đã phân định rõ batch nào có thể chạy song song chưa?
- Đã có final report format và evidence contract chưa?

## 14. Kết luận

Để GitHub Copilot trở thành một hệ thống agentic thực sự hiệu quả, cần thay đổi cách thiết kế từ prompt-centric sang runtime-centric. Điều quyết định hiệu quả không phải là một mega-prompt thông minh, mà là sự phối hợp đúng giữa instructions, skills, prompts, agents, hooks, memory artifacts, MCP và verification gates.

Thiết kế đúng sẽ cho ra một hệ thống có thể:

- tự intake công việc
- tự chia batch
- tự điều phối worker
- tự verify theo scope
- tự resume khi gián đoạn
- và chỉ kết thúc khi đạt đúng đích định lượng mà người dùng yêu cầu

Đó mới là một agentic system chuyên nghiệp.

## 15. Tài liệu liên quan trong repo này

- `reports/REPORT-github-copilot-coverity-batch-fix.vi.md`
- `reports/REPORT-github-copilot-cpp-unittest-coverage.vi.md`
- `reports/REPORT-claude-code-scientific-analysis.vi.md`
- `reports/REPORT-query-engine.md`
- `reports/REPORT-memory-system.md`
- `reports/REPORT-multi-agent-coordinator.md`
- `reports/REPORT-service-layer.md`
