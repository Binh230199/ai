# Playbook Thực Chiến: Dùng GitHub Copilot Xây Hệ Thống Tự Động Fix Coverity Theo Lô

## 1. Mục tiêu bài toán

Mục tiêu không phải là "sửa được vài issue". Mục tiêu là xây một workflow mà khi đã nhận job thì phải đi hết tới điểm kết thúc:

- tự lấy issue từ Coverity qua API hoặc MCP
- hiểu rule và ngữ cảnh code
- nhóm issue hợp lý
- fix đúng theo hướng dẫn và root cause
- verify không phát sinh vấn đề mới
- lặp tới khi `remainingIssues == 0` hoặc hết phần scope được giao

Nếu hệ thống không có manifest, batching logic, verify gate và resume state, nó gần như chắc chắn sẽ làm dở dang.

## 2. Vì sao bài toán này khó với AI coding agent

Coverity remediation hàng loạt khó ở sáu điểm:

1. Nhiều issue có cùng warning text nhưng root cause khác nhau.
2. Nhiều issue khác nhau lại có thể chung một root cause.
3. Fix cơ học rất dễ tạo regression.
4. Issue list lớn làm context nổ tung nếu nhồi hết vào chat.
5. Nếu không partition tốt, AI sẽ nhảy qua lại giữa nhiều module.
6. Nếu không có loop verify, agent sẽ tưởng đã xong trong khi scan lại vẫn còn hàng đống.

## 3. Kiến trúc workflow đề xuất

### 3.1. Vai trò agent

#### Orchestrator

Giữ manifest, batch, tiêu chí kết thúc, và quyết định thứ tự thực hiện.

#### Coverity intake agent

Lấy dữ liệu từ MCP/API, chuẩn hóa thành artifacts.

#### Rule researcher

Đọc rule docs, hướng dẫn fix, và code hiện tại; sinh spec remediation.

#### Fixer

Chỉ sửa một batch cụ thể.

#### Verifier

Chạy local checks và query lại Coverity/MCP để xác nhận batch đã sạch.

### 3.2. Luồng end-to-end

```text
Trigger job
 -> intake issues
 -> normalize + dedupe + batch
 -> research one batch
 -> implement fixes
 -> local verify
 -> Coverity recheck
 -> update manifest
 -> repeat until remainingIssues == 0
 -> final report
```

## 4. Hợp đồng dữ liệu tối thiểu với Coverity MCP/API

Đừng để agent nhận output HTML hoặc text lộn xộn. MCP/API nên trả ít nhất các field sau:

```json
{
  "issues": [
    {
      "id": "CID-1001",
      "checker": "RESOURCE_LEAK",
      "impact": "high",
      "file": "src/foo.cpp",
      "line": 123,
      "function": "processData",
      "eventPath": [
        { "line": 120, "message": "Resource allocated" },
        { "line": 123, "message": "Resource not released" }
      ],
      "description": "Allocated resource is not freed on all paths",
      "fixGuidelineId": "rule-resource-leak-v3",
      "module": "parser"
    }
  ],
  "totalCount": 87,
  "snapshotId": "snap-2026-03-31"
}
```

Ngoài issue list, nên có thêm các endpoint hoặc tool MCP sau:

- `get_issue_details`
- `get_rule_guide`
- `get_related_issues`
- `recheck_issues`
- `list_remaining_issues`

## 5. Artifacts phải có để job không dở dang

### 5.1. `artifacts/coverity/issues.json`

Chứa issue raw đã chuẩn hóa.

### 5.2. `artifacts/coverity/manifest.json`

Chứa trạng thái job tổng thể:

```json
{
  "jobId": "coverity-parser-001",
  "objective": "Fix all Coverity issues in parser module",
  "snapshotId": "snap-2026-03-31",
  "remainingIssues": 87,
  "exitCriteria": {
    "remainingIssues": 0,
    "build": "pass",
    "localTests": "pass"
  },
  "batches": []
}
```

### 5.3. `artifacts/coverity/batches/*.json`

Mỗi batch là một file riêng để dễ resume và retry.

### 5.4. `artifacts/coverity/runbook.md`

Ghi tiến độ, decisions, lessons learned, blockers.

### 5.5. `artifacts/coverity/results/*.md`

Output chuẩn hóa từ worker và verifier.

## 6. Pattern batching đúng cho Coverity

### 6.1. Batch theo rule + module + risk

Batch nên theo bộ khóa sau:

- `checker`
- `module`
- `risk tier`

Ví dụ tốt:

- `RESOURCE_LEAK` trong `parser`
- `NULL_DEREFERENCE` trong `network`
- `UNINIT` trong `codec`

Ví dụ tệ:

- 20 issue bất kỳ mỗi batch

### 6.2. Batch theo root cause nếu issue trùng pattern

Nếu nhiều issue cùng xuất phát từ một helper function hoặc cùng một API misuse, nên fix root cause trước rồi re-check toàn nhóm.

### 6.3. Tách risky transformations

Các rule kiểu security, taint, ownership, lifetime thường nên batch riêng với stricter verification.

## 7. Workflow chi tiết từng pha

### Pha 1: Intake

Orchestrator gọi intake agent:

- fetch issues
- dedupe issue duplicates
- lưu `issues.json`
- tạo `manifest.json`

Output cần có:

- total issues
- grouping candidates
- high-risk rules
- files/modules hotspot

### Pha 2: Partition

Orchestrator chia batches và đặt trạng thái:

- `pending`
- `researching`
- `implementing`
- `verifying`
- `completed`
- `blocked`

Song song hóa chỉ nên áp dụng cho các batch không đụng cùng file hoặc cùng subsystem rủi ro.

### Pha 3: Research

Rule researcher phải trả về remediation spec dạng ngắn gọn:

```markdown
Batch: batch-resource-leak-parser

Root cause:
- Early returns bypass cleanup in parser transaction setup

Recommended fix:
- Replace raw ownership with RAII wrapper in files A and B
- Avoid manual cleanup duplication

Do not:
- Suppress warning
- Add cleanup in one path only

Verification:
- Build parser target
- Run parser unit tests
- Re-check these issue IDs
```

### Pha 4: Implement

Fixer agent chỉ nhận một batch. Prompt của fixer phải có:

- batch id
- issue ids
- files allowed to modify
- fix strategy
- verification commands
- stop conditions

Không để fixer tự quyết định chạy sang batch khác.

### Pha 5: Local verify

Ngay sau khi sửa:

- compile scope liên quan
- chạy test scope liên quan
- chạy static proxy checks nếu có

Hook `PostToolUse` có thể tự động kích hoạt verify hẹp cho touched files.

### Pha 6: Remote re-check

Verifier query lại Coverity qua MCP/API:

- issue ids trong batch đã hết chưa
- issue count module giảm đúng chưa
- có issue mới phát sinh ở touched files không

### Pha 7: Reconcile

Orchestrator cập nhật:

- `remainingIssues`
- batch status
- touched files ledger
- lesson learned

Nếu còn issue, quay lại pha partition hoặc research.

## 8. Thiết kế prompts và agents cho workflow này

### 8.1. `fix-coverity-batch.prompt.md`

```markdown
---
description: "Fix a batch of Coverity or static-analysis issues from an existing manifest and verify the results."
agent: "orchestrator"
---

Load the Coverity manifest from `artifacts/coverity/manifest.json`.
Pick the next eligible batch.
Delegate research, implementation, and verification.
Do not declare completion until manifest exit criteria are met.
Persist progress in artifacts after every batch.
```

### 8.2. `issue-researcher.agent.md`

Tool set: `[read, search]` cộng MCP docs nếu có.

Không cho edit.

### 8.3. `code-fixer.agent.md`

Tool set: `[read, search, edit, execute]`

Ràng buộc:

- only modify files in assigned batch
- do not broaden scope
- stop after local verification

### 8.4. `verifier.agent.md`

Tool set: `[read, search, execute]` cộng MCP recheck tools.

Không cho edit.

## 9. Hook strategy cho Coverity jobs

### 9.1. PreToolUse

Các checks nên có:

- nếu worker không phải fixer, deny `edit`
- nếu fixer chạm file ngoài `allowedFiles`, deny
- nếu command là full-repo destructive operation, deny

### 9.2. PostToolUse

Sau `edit`:

- cập nhật `touched-files.json`
- xác định module tương ứng
- chạy compile/test nhỏ nhất có thể
- append kết quả vào `batch-report.md`

### 9.3. Stop

Ghi summary chuẩn hóa:

- batch id
- status
- files changed
- local verification evidence
- recheck status

## 10. Chiến lược tránh tạo issue mới

### 10.1. Fix root cause, không fix warning text

Ví dụ:

- `RESOURCE_LEAK`: ưu tiên RAII/ownership fix, không chắp vá cleanup từng nhánh.
- `NULL_DEREFERENCE`: thêm invariant hoặc early-guard đúng nơi sinh ra nullability, không chỉ thêm `if (!p) return` vô tội vạ.

### 10.2. Giữ semantic delta nhỏ

Mỗi batch nên có diff nhỏ, tập trung. Diff càng lớn, xác suất phát sinh regression càng cao.

### 10.3. Dùng verifier độc lập

Không dùng chính fixer để tự tuyên bố batch an toàn.

### 10.4. Theo dõi file hotspots

Nếu một file bị nhiều batch đụng tới, nên:

- tuần tự hóa batch liên quan
- hoặc gộp lại thành root-cause batch lớn hơn

## 11. Cách tiết kiệm token và thời gian cho Coverity automation

1. Fetch issues dưới dạng JSON cấu trúc, không paste issue text vào chat.
2. Batch theo rule/module để tái sử dụng reasoning.
3. Research một lần cho một loại issue lặp lại.
4. Cho worker đọc đúng batch file thay vì đọc cả manifest lớn.
5. Dùng summary file chuẩn hóa để orchestrator không phải đọc log dài.
6. Chạy verify hẹp trước, verify rộng sau.
7. Dùng hooks để tự động ghi evidence thay vì bắt model tường thuật lại.

## 12. Điều kiện hoàn thành chuẩn cho một job Coverity

Một job chỉ được đánh dấu hoàn thành khi thỏa toàn bộ:

- `remainingIssues == 0` trong scope
- build pass cho scope liên quan
- test pass cho scope liên quan
- verifier không thấy issue mới ở touched files
- final report liệt kê đầy đủ batch, issue ids, evidence

## 13. Final report format nên dùng

```markdown
# Coverity Remediation Report

## Objective
- Fix all Coverity issues in parser module

## Snapshot
- start: 87 issues
- end: 0 issues

## Batches
- batch-resource-leak-parser: completed
- batch-null-deref-parser: completed

## Verification
- parser build: pass
- parser tests: pass
- coverity recheck: pass

## Risks / Follow-up
- none
```

## 14. Những chỗ dễ hỏng nhất

1. Không có recheck từ Coverity, chỉ tin local lint.
2. Batch sai, đụng chéo file liên tục.
3. Fixer đọc quá ít context nên patch sai semantics.
4. Worker không ghi evidence chuẩn hóa.
5. Orchestrator không cập nhật manifest sau mỗi batch.

## 15. Kết luận

Muốn Copilot fix Coverity thật sự tự động và làm tới cùng, phải coi đây là một bài toán quản trị batch + verification + recovery, không phải bài toán sinh code thuần túy. Khi đã có manifest, roles, hooks, MCP data contract và verifier độc lập, hệ thống mới có cơ hội làm đến hết backlog mà vẫn giữ an toàn kỹ thuật.
