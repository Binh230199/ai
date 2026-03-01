Dựa trên công việc của bạn, đây là cách phân bổ theo đúng mục đích của từng loại file:

---

## Nguyên tắc phân loại

```
copilot-instructions.md  → "Tôi là ai, project này là gì" – luôn active
instructions/            → Rules tự động áp dụng khi edit file theo path
prompts/                 → Slash commands /tên – gọi khi cần, 1 task cụ thể
skills/                  → Workflow phức tạp có scripts/resources, portable
agents/                  → AI persona chuyên biệt, tool set riêng
hooks/                   → Tự động chạy tại lifecycle events, không bypass được
```

---

## Toàn bộ mapping từ công việc của bạn

```
.github/
│
├── copilot-instructions.md
│       "Tôi làm ở LGEDV, C++/Java/Kotlin, IVI/HUD/RSE,
│        Gerrit/Jira/Confluence/Coverity, AUTOSAR C++14,
│        build: CMake/Yocto/Soong, test: gtest/JUnit"
│       → Nền tảng context cho MỌI request
│
├── instructions/
│   ├── cpp-service.instructions.md       applyTo: src/**/*.cpp, src/**/*.h
│   │       AUTOSAR C++14 rules, no raw new/delete,
│   │       error_code usage, naming convention
│   │
│   ├── java-hmi.instructions.md          applyTo: **/*.java, **/*.kt
│   │       MVVM pattern, null safety, lifecycle rules,
│   │       AIDL binding conventions
│   │
│   ├── tests-cpp.instructions.md         applyTo: test/**/*.cpp
│   │       GTest/GMock conventions, fixture naming,
│   │       coverage target, mock patterns
│   │
│   ├── tests-java.instructions.md        applyTo: **/test/**/*.kt, **/test/**/*.java
│   │       JUnit5/Mockito patterns, AAA structure
│   │
│   └── code-review.instructions.md       applyTo: **/*.cpp, **/*.h, **/*.kt
│           Review checklist: AUTOSAR, null safety,
│           thread safety, resource management
│           (dùng cho review agent, không phải coding agent)
│
├── prompts/                              ← Slash commands /tên
│   ├── read-ticket.prompt.md             /read-ticket
│   │       Đọc Jira ticket + attachments + tóm tắt
│   │
│   ├── analyze-bug.prompt.md             /analyze-bug
│   │       Đọc bug ticket + download log + map to code + root cause
│   │
│   ├── weekly-report.prompt.md           /weekly-report
│   │       Pull Jira + Gerrit activity 7 ngày → format → post Confluence
│   │
│   ├── draft-email.prompt.md             /draft-email
│   │       Soạn email phản hồi / status update
│   │
│   ├── standup.prompt.md                 /standup
│   │       Pull activity hôm qua từ Jira+Gerrit → soạn nội dung standup
│   │
│   ├── create-ticket.prompt.md           /create-ticket
│   │       Tạo Jira ticket đầy đủ từ mô tả ngắn
│   │
│   ├── push-code.prompt.md               /push-code
│   │       Kiểm tra pre-push checklist + generate commit message + CR description
│   │
│   ├── review-commit.prompt.md           /review-commit
│   │       Review commit diff + cross-reference Jira ticket
│   │
│   ├── confluence-research.prompt.md     /confluence-research
│   │       Search Confluence → tổng hợp → optional: tạo bài viết
│   │
│   └── onboard-module.prompt.md          /onboard-module
│           Đọc Confluence + codebase → tạo module overview
│
├── skills/
│   ├── analyze-bug/                      ← Phức tạp hơn prompt: có scripts
│   │   ├── SKILL.md                      Download log/zip → parse stack trace
│   │   └── parse_log.py                  → map to source → root cause
│   │
│   ├── cpp-unit-test/                    ← Loop tự động đến 100% coverage
│   │   ├── SKILL.md
│   │   └── coverage_patterns.cpp
│   │
│   ├── java-unit-test/
│   │   ├── SKILL.md
│   │   └── mockito_patterns.kt
│   │
│   ├── fix-static-issues/               ← Chạy scan → đọc report → fix → verify
│   │   ├── SKILL.md
│   │   └── common_fixes.cpp
│   │
│   ├── coverity-fix/                    ← REST API → checklist → fix → verify
│   │   ├── SKILL.md
│   │   └── coverity_api.py
│   │
│   └── weekly-report/                   ← Đủ phức tạp để là skill (Jira + Gerrit + Confluence)
│       ├── SKILL.md
│       └── report_template.md
│
├── agents/
│   ├── code-reviewer.agent.md
│   │       tools: [read, search, usages]  ← KHÔNG có edit
│   │       Chuyên review: correctness, AUTOSAR style,
│   │       business logic vs Jira requirements
│   │       Handoff → "Fix Issues" agent
│   │
│   ├── feature-builder.agent.md
│   │       tools: [read, edit, search, runInTerminal]
│   │       Đọc Jira → implement → build → test → update ticket
│   │
│   ├── bug-fixer.agent.md
│   │       tools: [read, edit, search, runInTerminal]
│   │       analyze-bug skill → implement fix → verify → push
│   │
│   ├── tdd-cpp.agent.md
│   │       tools: [read, edit, runInTerminal]
│   │       Viết test → cmake → ctest → lcov → loop đến 100%
│   │
│   └── coverity-fixer.agent.md
│           tools: [read, edit, runInTerminal]
│           Batch fix Coverity issues với checklist
│
└── hooks/
    ├── pre-push-guard.json               PreToolUse
    │       Block "git push" nếu static scan chưa pass
    │       Block edit trong generated/ folders
    │
    ├── post-edit-format.json             PostToolUse
    │       Auto-format C++ files sau khi agent edit
    │       (clang-format hoặc internal formatter)
    │
    ├── coverage-guard.json               Stop
    │       Block agent báo "xong" nếu coverage < target
    │
    ├── static-guard.json                 Stop
    │       Block nếu còn Mandatory static issues
    │
    └── scripts/
            inject_context.py             SessionStart: inject branch + ticket ID
            guard_pre_tool.py             PreToolUse logic
            verify_coverage.py            Stop hook coverage check
            verify_static.py              Stop hook static check
```

---

## Tóm tắt quyết định

| Công việc | Loại | Lý do |
|-----------|------|-------|
| Đọc ticket đơn giản | `prompt` | 1 task, không cần scripts |
| Phân tích bug với log/zip | `skill` | Cần script download + parse |
| Fix static issues | `skill` | Có scripts chạy tool + parse report |
| Fix Coverity | `skill` + `agent` | Skill cho logic, agent cho persona batch |
| Viết unit test loop | `skill` + `agent` | Skill có coverage patterns, agent enforce loop |
| Review code | `agent` | Cần restrict tools (read-only) |
| Implement feature | `agent` | Cần full tools + Jira MCP context |
| Block push khi chưa pass | `hook` | Cần guarantee, không phải AI tự nhớ |
| Auto-format sau edit | `hook` | Tự động 100%, không nhắc |
| Rules khi viết C++ file | `instructions` | Áp dụng tự động theo path |