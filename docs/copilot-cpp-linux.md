# GitHub Copilot – Agentic AI Thực Chiến
### Dành cho C++ Linux Service Engineer

---

## Mục Lục

1. [Tổng Quan – Agentic AI Sẽ Làm Được Gì Cho Bạn](#1)
2. [MCP Server Setup – Kết Nối Jira, Confluence, Coverity, Gerrit](#2)
3. [Use Case 1: Đọc Jira Ticket Đầy Đủ (Description, Comment, Attachments)](#3)
4. [Use Case 2: Weekly Progress Report Tự Động](#4)
5. [Use Case 3: Research Confluence → Tổng Hợp → Tạo Bài Viết](#5)
6. [Use Case 4: Coverity Issues – Kiểm Tra & Fix Tất Cả](#6)
7. [Use Case 5: Review Commit + Cross-Reference Jira Ticket](#7)
8. [Use Case 6: Unit Test → Run → Fix → Loop Đến 100% Coverage](#8)
9. [Customization Layer – Setup Cho C++ Linux Service](#9)
10. [Cấu Trúc File Hoàn Chỉnh](#10)
11. [Chiến Lược Xử Lý Khi Vấn Đề Lớn (Bulk Tasks)](#11)
12. [Bảng Tóm Tắt & Lộ Trình](#12)

---

## 1. Tổng Quan {#1}

### Agentic AI Sẽ Làm Được Gì Thực Sự

Những gì trước đây tốn 30 phút đến vài giờ context switching giữa Jira, IDE,
terminal, Confluence:

```
Trước đây (Manual):
─────────────────────────────────────────────────────
Open Jira → đọc ticket → open IDE → tìm file liên quan
→ implement → build → test → sửa lỗi → check coverage
→ open Confluence → tìm docs → quay lại code → ...
(hàng chục lần switch context, mỗi switch mất focus ~10 phút)

Với Agentic AI:
─────────────────────────────────────────────────────
[Agent Mode]
"Read PROJ-1234, understand requirements,
 find relevant code, implement, write tests,
 run until 100% coverage, update ticket."
→ Copilot đọc Jira, search codebase, implement,
  build, run tests, đọc coverage report, fix,
  loop cho đến khi xong → báo kết quả
(Bạn chỉ cần review và approve)
```

### Vòng Lặp Agentic – Tại Sao Nó Không Chỉ Là "Chat"

```
[Bạn ra đề]
     │
     ▼
  [Plan]  Copilot đọc Jira → hiểu requirements → plan steps
     │
     ▼
 [Execute] Tìm files → edit code → gọi cmake/make → run tests
     │
     ▼
 [Observe] Đọc build errors, test failures, coverage%
     │
     ▼
 [Replan]  Nếu coverage 87% < 100% → tìm uncovered branches → thêm test
     │
     ▼
  [Done]  100% coverage + all tests pass → commit + update Jira
```

Copilot **không chỉ gợi ý** – nó **tự chạy lệnh, đọc kết quả, và sửa tiếp**.

---

## 2. MCP Server Setup {#2}

### Kiến Trúc Kết Nối

```
Copilot Agent
     │
     ├── [MCP] Jira          → Tickets, comments, attachments, transitions
     ├── [MCP] Confluence     → Pages, spaces, search, create/update
     ├── [MCP] Coverity REST  → Issues, triage, assignment, checkers
     ├── [MCP] Fetch          → Download log files, zip files, any URL
     ├── [MCP] Filesystem     → Advanced file operations
     └── Built-in Tools       → Edit files, run terminal, search codebase
```

### File Setup

```bash
# Khởi tạo MCP cho workspace
mkdir -p .vscode
# Sau đó tạo .vscode/mcp.json (xem bên dưới)
```

```json
// .vscode/mcp.json – commit vào git, chia sẻ cả team
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
        "CONFLUENCE_API_TOKEN": "${input:atlassian-token}",
        "JIRA_PROJECTS_FILTER": "PROJ,PLATFORM,INFRA"
      }
    },
    "fetch": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-server-fetch"],
      "env": {
        "ALLOWED_DOMAINS": "your-company.atlassian.net,coverity.yourcompany.com,gerrit.yourcompany.com"
      }
    },
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "${workspaceFolder}",
        "${workspaceFolder}/tmp-downloads"
      ]
    }
  },
  "inputs": [
    {
      "type": "promptString",
      "id": "atlassian-email",
      "description": "Email Atlassian account của bạn"
    },
    {
      "type": "promptString",
      "id": "atlassian-token",
      "description": "Atlassian API Token (myaccount.atlassian.net → Security → API tokens)",
      "password": true
    }
  ]
}
```

**Một lần setup, dùng mãi mãi.** MCP servers tự start khi bạn mở workspace.
Status: Activity Bar → Copilot icon → MCP Servers.

### Coverity Connect REST API

Coverity Connect expose REST API tại `/api/v2/`. Không cần MCP riêng –
dùng `fetch` MCP hoặc `#fetch` tool với API token:

```bash
# Lấy Coverity API token
# Coverity Connect UI → Profile → API Keys → Generate
```

Sau đó dùng trong chat:
```
#fetch https://coverity.yourcompany.com/api/v2/issues?filters=...
```

Hoặc lưu token vào env và gọi qua script:

```python
# scripts/coverity_api.py
# Agent sẽ tự viết và chạy script này khi cần
import requests, os, json, sys

BASE_URL = "https://coverity.yourcompany.com/api/v2"
TOKEN = os.environ.get("COVERITY_TOKEN")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def get_my_issues(stream_name=None, limit=500):
    params = {
        "filters": json.dumps([
            {"columnKey": "owner", "matchMode": "oneOrMoreMatch",
             "matchers": [{"type": "user", "name": os.environ.get("COVERITY_USERNAME")}]}
        ]),
        "offset": 0, "limit": limit
    }
    if stream_name:
        params["streamName"] = stream_name
    resp = requests.get(f"{BASE_URL}/issues/search", headers=HEADERS, params=params)
    return resp.json()

if __name__ == "__main__":
    issues = get_my_issues(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps(issues, indent=2))
```

---

## 3. Use Case 1 – Đọc Jira Ticket Đầy Đủ {#3}

### Mục tiêu

Đọc hết nội dung một ticket: description, tất cả comments (kể cả cũ),
các file đính kèm như log, zip, hình ảnh màn hình.

### Vấn đề với attachments

Jira MCP trả về metadata của attachment (tên file, URL). Để đọc **nội dung**,
Copilot cần download file đó – dùng `fetch` MCP hoặc viết script download.

### Prompt thực tế

```
[Agent Mode]
"Đọc toàn bộ nội dung Jira ticket PROJ-1234:
 1. Description đầy đủ
 2. Tất cả comments (không bỏ sót comment nào)
 3. Với mỗi attachment:
    - Nếu là .log hoặc .txt: download và đọc nội dung
    - Nếu là .zip: download, giải nén vào tmp-downloads/, đọc các file logs bên trong
    - Nếu là hình ảnh (.png/.jpg): mô tả filename và URL để tôi xem thủ công
 4. Tổng hợp: vấn đề là gì, các thông tin quan trọng, bước tái tạo lỗi (nếu có)

Sau khi đọc xong, nếu đây là bug report:
 - Tìm trong codebase các file/function liên quan
 - Đề xuất nguyên nhân và hướng fix"
```

### Cách Copilot xử lý attachments

```
Jira MCP: jira_get_issue(PROJ-1234)
→ response có: fields.attachment = [
    {filename: "service.log", content: "https://company.atlassian.net/rest/api/2/attachment/content/12345"},
    {filename: "crash_dump.zip", content: "https://..."}
  ]

↓
fetch MCP: fetch_url("https://.../content/12345")
→ trả về nội dung file log dạng text

↓
Với .zip:
  Script: wget/curl download → unzip vào tmp-downloads/
  filesystem MCP: đọc các file bên trong
```

**Import:** Thêm thư mục download vào `.gitignore`:
```gitignore
# .gitignore
tmp-downloads/
```

### Ví dụ prompt ngắn hơn cho daily work

```
"Read PROJ-1234 with all attachments and summarize for me"

"Read PROJ-1234, identify the root cause from the attached crash log,
 and propose a fix in our C++ service code"

"Read PROJ-1234, understand the requirements completely,
 then start implementing in C++"
```

### Setup nhanh với Prompt File

```markdown
<!-- .github/prompts/read-ticket.prompt.md -->
# Read Jira Ticket Fully

Read the specified Jira ticket completely:
1. Description, acceptance criteria, all comments
2. Download and read content of all text/log/zip attachments
3. Save large attachments to tmp-downloads/
4. Summarize: problem statement, requirements, context, reproduction steps

Ticket ID: (will be specified in chat)
```

Dùng: gõ `/read-ticket` hoặc kéo file prompts vào chat → nhập ticket ID.

---

## 4. Use Case 2 – Weekly Progress Report {#4}

### Mục tiêu

Cuối tuần, tạo báo cáo tự động từ Jira: tôi đã làm gì, kết quả ra sao,
những gì đang blocked hoặc in-progress.

### Prompt

```
[Agent Mode + Jira MCP]
"Tạo weekly progress report cho tôi:

 Dữ liệu cần lấy từ Jira:
 1. Tickets CLOSED trong 7 ngày qua (assignee = tôi)
 2. Tickets IN PROGRESS hiện tại
 3. Tickets tôi có comment hoặc activity trong 7 ngày qua
    (kể cả tickets không assigned cho tôi nhưng tôi có contribute)
 4. Tickets được tạo bởi tôi trong tuần này

 Báo cáo format:
 ## Week of [ngày] – [tên tôi]

 ### ✅ Completed This Week
 [danh sách với: ticket ID, title, brief description of what was done]

 ### 🔄 In Progress
 [danh sách với: % complete estimate, blocker nếu có]

 ### 🤝 Contributed To (not primary assignee)
 [tickets không assigned nhưng tôi có đóng góp]

 ### ⚠️ Blocked / Waiting
 [tickets blocked với lý do]

 ### 📊 Stats
 [Số tickets completed, story points nếu có]

 Lưu file: reports/weekly/week-YYYY-WW.md"
```

### Prompt File để tái sử dụng

```markdown
<!-- .github/prompts/weekly-report.prompt.md -->
# Generate Weekly Progress Report

Generate my weekly report from Jira data.

Steps:
1. Get issues where: assignee = currentUser(), updated >= -7d
2. Get issues where: I added a comment in the last 7 days
3. Get issues where: I transitioned status in the last 7 days
4. Group by: Completed | In Progress | Contributed | Blocked
5. For each issue: get summary, description snippet, and my last comment
6. Format as professional progress report in markdown
7. Save to: reports/weekly/week-[YYYY-WW].md

Time period: last 7 days (Mon–Sun)
```

Dùng ngay: gõ `/weekly-report` trong chat mỗi cuối tuần.

### Mở rộng: Tạo luôn trên Confluence

```
"Tạo weekly report như trên, và sau đó:
 - Tạo/update page trên Confluence tại space TEAM > Weekly Reports > [tên tôi]
 - Title: 'Week [WW] Progress – [tên tôi]'
 - Nếu page tuần này đã tồn tại: update nội dung
 - Nếu chưa: tạo mới dưới parent page 'Weekly Reports'"
```

---

## 5. Use Case 3 – Research Confluence → Tạo Bài Viết {#5}

### Mục tiêu

Khi muốn nghiên cứu một chủ đề (ví dụ: "cách implement zero-copy networking
trong Linux service"), dùng AI search và tổng hợp từ Confluence nội bộ,
rồi tạo bài viết lưu lại trên trang cá nhân.

### Bước 1 – Research Mode (Ask Mode – Không sửa gì cả)

```
[Ask Mode]
"Tôi muốn nghiên cứu về zero-copy networking trong C++ Linux service.

 Hãy tìm kiếm trên Confluence:
 1. Search: 'zero-copy networking', 'sendfile', 'io_uring', 'splice'
 2. Search: 'Linux networking best practices' trong space PLATFORM
 3. Tìm bất kỳ tài liệu architecture/design nào liên quan đến networking layer

 Từ các kết quả tìm được:
 - Tổng hợp: các approach đang được dùng trong team
 - Tìm: performance benchmarks, known issues, gotchas
 - List: các Confluence pages liên quan nhất (title + URL)

 Kết hợp với kiến thức của bạn về chủ đề này để tạo overview đầy đủ."
```

### Bước 2 – Deep Dive (Đọc Các Pages Cụ Thể)

```
[Ask Mode]
"Đọc đầy đủ page Confluence có title '[tên page từ kết quả trước]'
 và tổng hợp:
 - Key insights
 - Code examples nếu có
 - Decisions made và lý do
 - Open questions hoặc TODO items"
```

### Bước 3 – Tạo Bài Viết Trên Confluence

```
[Agent Mode + Confluence MCP]
"Dựa trên research về zero-copy networking phía trên, hãy tạo một bài viết
 trên Confluence cá nhân của tôi:

 Location: ~[tên tôi] > TIL (Today I Learned) > [năm]
 Title: 'Zero-Copy Networking in C++ Linux Services – Study Notes'

 Structure bài viết:
 1. Overview – vấn đề zero-copy giải quyết gì
 2. Approaches (so sánh sendfile, splice, io_uring, mmap)
 3. Implementation notes – practical tips cho C++
 4. Internal references – link đến Confluence pages đã đọc
 5. External references – blog posts, man pages, papers
 6. My takeaways – bullet points học được gì
 7. Next steps – tôi sẽ thử implement gì

 Format: dùng Confluence macro đẹp, có code blocks, có table so sánh"
```

### Prompt File tái sử dụng

```markdown
<!-- .github/prompts/research-and-write.prompt.md -->
# Research Topic and Create Confluence Article

Research a technical topic using Confluence and my own knowledge,
then create a structured article on my personal Confluence space.

Steps:
1. Search Confluence for the topic keywords (broad search first)
2. Read the top 3-5 most relevant pages in full
3. Search for related discussions in JIRA (if issue-related)
4. Synthesize: what does the team know, what are the patterns used
5. Combine with up-to-date technical knowledge
6. Create Confluence page at: ~[my username] > TIL > [current year]
   with professional format, code examples, comparison tables, and references

Topic: (will be specified in chat)
```

---

## 6. Use Case 4 – Coverity: Kiểm Tra & Fix Tất Cả Issues {#6}

### Mục tiêu

Mở VS Code, hỏi Copilot: "Tôi có bao nhiêu Coverity issues? Hãy fix hết cho tôi."

### Bước 1 – Kiểm Tra Issues Được Assign

```
[Agent Mode]
"Kiểm tra tất cả Coverity static analysis issues đang assigned cho tôi:

 1. Gọi Coverity Connect REST API:
    GET https://coverity.yourcompany.com/api/v2/issues/search
    Auth: Bearer token từ COVERITY_TOKEN env var
    Filter: owner = tên tôi, status = New hoặc Triaged
    Stream: [tên stream của project, ví dụ: cpp-linux-service-main]

 2. Hoặc chạy: python scripts/coverity_api.py 'cpp-linux-service-main'

 3. Hiển thị kết quả dạng bảng:
    | CID | Checker | Severity | File | Line | Function | Status |

 4. Nhóm theo severity: High → Medium → Low
 5. Nhóm theo checker category để thấy patterns"
```

### Bước 2 – Fix Tất Cả (Chiến lược Checklist)

Với nhiều issues, dùng checklist file để có thể resume nếu bị interrupt:

```
[Agent Mode]
"Dựa trên danh sách Coverity issues vừa lấy được, hãy:

 1. Tạo file COVERITY_FIX_CHECKLIST.md với danh sách đầy đủ:
    ## High Severity (fix first)
    - [ ] CID-12345 | NULL_RETURN | src/service/connection.cpp:89 | handle_connect()
    - [ ] CID-12346 | RESOURCE_LEAK | src/service/handler.cpp:134 | process_request()
    ...
    ## Medium Severity
    ...
    ## Low Severity
    ...

 2. Fix từng issue theo thứ tự High → Medium → Low:
    a. Đọc chi tiết issue từ Coverity (context, event trace)
    b. Đọc code tại file:line được chỉ định
    c. Hiểu root cause từ Coverity event trace
    d. Fix đúng cách (không chỉ suppress warning)
    e. Đảm bảo: không phá logic hiện tại, không break tests
    f. Đánh dấu [x] trong checklist sau mỗi fix

 3. Sau mỗi 10 issues: chạy cmake --build build để verify không có compile errors

 4. Sau khi xong tất cả: chạy full test suite để confirm không có regression

 5. Tổng kết: tạo COVERITY_FIX_SUMMARY.md với:
    - Số issues fixed vs skipped (với lý do skip)
    - Patterns phổ biến nhất
    - Khuyến nghị để tránh lặp lại"
```

### Bước 3 (Optional) – Re-analyze Locally

```
[Agent Mode]
"Sau khi fix xong, chạy lại local Coverity analysis để verify:
 cov-build --dir cov-int cmake --build build
 cov-analyze --dir cov-int
 cov-format-errors --dir cov-int --emacs-style > coverity_local_results.txt

 Đọc kết quả: còn issue nào mới không? Fix nếu có."
```

### Prompt File

```markdown
<!-- .github/prompts/coverity-fix.prompt.md -->
# Fix Coverity Static Analysis Issues

Get all Coverity issues assigned to me and fix them systematically.

Steps:
1. Run: python scripts/coverity_api.py [stream-name] to get my assigned issues
2. Create COVERITY_FIX_CHECKLIST.md grouped by severity
3. For each issue (High first):
   - Fetch full issue details via Coverity REST API (event trace, context)
   - Read the file at the reported location
   - Fix the root cause (not just suppressing)
   - Mark [x] in checklist immediately
4. Build after every 10 fixes: cmake --build build
5. Run all tests when complete: cd build && ctest --output-on-failure
6. Create fix summary report

Stream name: (specify in chat, or leave empty for all streams)
```

### Common Coverity Checkers và Cách Fix

```cpp
// NULL_RETURN: Copilot sẽ tự fix theo pattern này
// Before (flagged by Coverity):
auto* conn = connection_pool.get();
conn->send(data);  // Coverity: conn có thể null

// After (fixed):
auto* conn = connection_pool.get();
if (!conn) {
    LOG_ERROR("Failed to get connection from pool");
    return std::errc::resource_unavailable_try_again;
}
conn->send(data);

// RESOURCE_LEAK: Pattern fix
// Before:
int fd = open(path.c_str(), O_RDONLY);
if (read(fd, buf, size) < 0) {
    return false;  // Coverity: fd leaked
}

// After: dùng RAII
struct FileGuard {
    int fd;
    ~FileGuard() { if (fd >= 0) close(fd); }
};
FileGuard guard{open(path.c_str(), O_RDONLY)};
if (guard.fd < 0 || read(guard.fd, buf, size) < 0) {
    return false;  // fd sẽ được close tự động
}
```

---

## 7. Use Case 5 – Review Commit + Cross-Reference Jira {#7}

### Mục tiêu

Review một commit: code quality, correctness, và quan trọng hơn – kiểm tra
xem code changes CÓ THỰC SỰ giải quyết được những gì trong Jira ticket không.

### Variant A – Review Commit Đơn Thuần

```
[Ask Mode – read-only, an toàn]
"Review commit abc1234f67:

 Lấy diff: git diff abc1234f67^1..abc1234f67

 Kiểm tra:
 1. CORRECTNESS: logic có đúng không? edge cases được handle chưa?
 2. THREAD SAFETY: shared state? race conditions? mutex pairing?
 3. ERROR HANDLING: lỗi có được propagate đúng không? resource leak?
 4. MEMORY MANAGEMENT: new/delete cân bằng? unique_ptr/shared_ptr dùng đúng?
 5. STYLE: C++ modern best practices, naming, readability
 6. TESTS: có test coverage cho changes không?

 Report format:
 [BLOCKER | MAJOR | MINOR | SUGGESTION] File:Line: Mô tả vấn đề + cách fix"
```

### Variant B – Review + Cross-Reference Jira (Mạnh Nhất)

```
[Agent Mode + Jira MCP]
"Review commit abc1234f67 và cross-reference với Jira ticket:

 Bước 1: Đọc Jira ticket PROJ-1234 đầy đủ
   - Requirements, acceptance criteria, description
   - Tất cả comments (đặc biệt từ reviewer/PM)
   - Attachments nếu có expected behavior hoặc test cases

 Bước 2: Lấy full diff của commit:
   git show abc1234f67

 Bước 3: Phân tích alignment:
   a. Những requirement nào đã được implement? ✅
   b. Những requirement nào CHƯA được implement? ❌
   c. Code có implement gì NGOÀI scope của ticket không? (scope creep)
   d. Có edge case nào trong ticket nhưng code bỏ sót không?

 Bước 4: Code quality review (technical)

 Bước 5: Kết luận: APPROVE / REQUEST CHANGES / NEEDS DISCUSSION
   với justification cụ thể cho từng điểm"
```

### Variant C – Review Toàn Bộ Branch (Trước Khi Tạo MR)

```
[Agent Mode + Jira MCP]
"Review toàn bộ changes trong branch của tôi trước khi tạo Merge Request:

 1. Lấy diff so với main: git diff main...HEAD
 2. Đọc ticket PROJ-1234 để hiểu context
 3. Multi-angle review với subagents song song:
    - Logic/Correctness review
    - Security review (input validation, buffer overflows, injection)
    - Performance review (unnecessary copies, O(n²) loops, blocking calls)
    - Test coverage review (có test cho mọi public function chưa?)
 4. Tạo MR description template để tôi fill in:
    ## Summary of Changes
    ## Testing Done
    ## Checklist"
```

### Prompt File cho Daily Review

```markdown
<!-- .github/prompts/review-commit.prompt.md -->
# Review Commit Against Jira Ticket

Steps:
1. Read the Jira ticket (with all comments and attachments)
2. Get the full git diff for the specified commit
3. Analyze:
   - Requirements coverage (what's addressed, what's missing)
   - Code correctness and edge cases
   - Thread safety and error handling
   - Test coverage
4. Final verdict: APPROVE / REQUEST CHANGES
5. List specific actionable feedback with file:line references

Commit: (specify hash or use HEAD)
Ticket: (specify PROJ-XXXX)
```

---

## 8. Use Case 6 – Unit Test → Run → Fix → 100% Coverage {#8}

### Mục tiêu

Tự động hóa vòng lặp: viết tests → build → run → check coverage → nếu chưa
đủ thì tìm các branch chưa covered → thêm tests → lặp lại. Đến khi 100%.

### Setup Coverage cho C++ / CMake / GTest / gcov

```cmake
# CMakeLists.txt (thêm vào)
option(COVERAGE "Enable coverage analysis" OFF)
if(COVERAGE)
  target_compile_options(your_service_tests PRIVATE --coverage -O0 -g)
  target_link_options(your_service_tests PRIVATE --coverage)
endif()
```

```bash
# scripts/coverage.sh – Agent sẽ gọi script này
#!/bin/bash
set -e
BUILD_DIR=${1:-build}
cmake -B $BUILD_DIR -DCOVERAGE=ON -DCMAKE_BUILD_TYPE=Debug
cmake --build $BUILD_DIR --target your_service_tests -- -j$(nproc)
cd $BUILD_DIR
./your_service_tests --gtest_output=xml:test_results.xml
cd ..
lcov --capture --directory $BUILD_DIR --output-file coverage.info \
     --exclude '*/test/*' --exclude '/usr/*' --exclude '*/third_party/*'
lcov --list coverage.info  # print per-file coverage
genhtml coverage.info --output-directory coverage_html
# Output total line coverage percentage on last line for agent to parse
lcov --summary coverage.info 2>&1 | grep "lines" | tail -1
```

### Prompt – Vòng Lặp Tự Động

```
[Agent Mode]
"Viết unit tests cho class ConnectionManager trong:
 #file:src/service/connection_manager.h
 #file:src/service/connection_manager.cpp

 Framework: Google Test + Google Mock
 Existing tests: #file:test/connection_manager_test.cpp (nếu có)

 Yêu cầu:
 - Cover tất cả public methods
 - Test both success and error paths
 - Test edge cases: null input, empty containers, max capacity, timeout
 - Mock external dependencies (logger, network socket) không gọi thật

 Sau khi viết xong, thực hiện vòng lặp tự động:

 LOOP:
   1. cmake -B build -DCOVERAGE=ON -DCMAKE_BUILD_TYPE=Debug
   2. cmake --build build --target your_service_tests -- -j$(nproc)
      → Nếu build fail: đọc error, fix test code, quay lại bước 1
   3. ./build/your_service_tests --gtest_filter='ConnectionManager*'
      → Nếu test fail: đọc failure output, fix test logic, quay lại bước 1
   4. bash scripts/coverage.sh
      → Đọc coverage report: file connection_manager.cpp: X% lines covered
      → Xem HTML report (genhtml output) để tìm uncovered lines (màu đỏ)
         Hoặc đọc: lcov --annotate coverage.info --demangle-cpp
      → Nếu X < 100%: tìm các branch/line chưa covered, thêm test cases
      → Quay lại bước 1
 END LOOP khi: 100% line coverage + 100% branch coverage cho connection_manager.cpp

 Dừng vòng lặp nếu: sau 5 iterations vẫn không đạt → báo cáo lý do"
```

### Stop Hook – Đảm Bảo 100% Trước Khi Agent "Xong"

```python
# .github/hooks/scripts/verify_coverage.py
# Stop Hook: Chặn agent báo done nếu coverage chưa đạt
import json, sys, subprocess, re

data = json.load(sys.stdin)
if data.get("stop_hook_active"):
    print(json.dumps({"continue": True}))
    sys.exit(0)

# Chỉ check khi có test files được edit
# (có thể skip hook nếu không liên quan đến tests)
result = subprocess.run(
    ["bash", "scripts/coverage.sh", "build"],
    capture_output=True, text=True
)
output = result.stdout + result.stderr

# Parse coverage percentage từ lcov output
match = re.search(r'lines\.*:\s*([\d.]+)%', output)
if not match:
    print(json.dumps({"continue": True}))
    sys.exit(0)

coverage = float(match.group(1))
TARGET = 100.0  # Thay bằng 80.0 nếu chỉ cần 80%

if coverage < TARGET:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "decision": "block",
            "reason": (
                f"Coverage is {coverage:.1f}%, target is {TARGET}%. "
                f"Find uncovered lines in coverage_html/index.html "
                f"and add more test cases."
            )
        }
    }))
else:
    print(json.dumps({"continue": True}))
```

```json
// .github/hooks/coverage-guard.json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "python3 .github/hooks/scripts/verify_coverage.py",
        "timeout": 120
      }
    ]
  }
}
```

### Custom Agent cho TDD Workflow

```markdown
<!-- .github/agents/tdd-cpp.agent.md -->
---
name: C++ TDD
description: Test-driven development for C++ Linux service – write tests, build, run, fix until 100% coverage
tools: ['read', 'edit', 'search', 'runInTerminal', 'problems']
model: claude-sonnet-4-6
---

You are a C++ TDD specialist for Linux service development.

## Your Workflow
1. Read the header file to understand the class interface completely
2. Read existing tests (if any) to understand patterns used
3. Write comprehensive GTest tests covering ALL branches
4. Run the coverage loop until 100% line + branch coverage:
   - cmake build → run tests → check lcov output → find uncovered → add tests → repeat
5. Only stop when coverage report shows 100% for the target file

## Testing Principles
- Use RAII mocks (Google Mock) – never modify production code paths for testability
- Each test must be isolated – no shared global state between tests
- Test names follow: ClassName_MethodName_Condition_ExpectedBehavior
- Group related tests in TEST_F with a fixture class
- Always test: null/empty input, boundary values, error returns, race-free behavior

## Build Commands
- Build tests:    cmake -B build -DCOVERAGE=ON && cmake --build build -- -j$(nproc)
- Run tests:      ./build/your_service_tests --gtest_output=xml:test_results.xml
- Coverage:       bash scripts/coverage.sh
- Find uncovered: open coverage_html/index.html or run: lcov --list coverage.info
```

### Ví dụ Output Sau Vòng Lặp

```
Iteration 1: 67.3% coverage – missing: error paths in connect(), timeout branch
→ Added 3 test cases
Iteration 2: 84.1% coverage – missing: retry logic in reconnect()
→ Added 2 test cases
Iteration 3: 93.7% coverage – missing: move constructor edge case
→ Added 1 test case
Iteration 4: 100.0% ✅ – All 23 tests pass

Total: 23 test cases, 4 iterations, ~8 minutes autonomous
```

---

## 9. Customization Layer Cho C++ Linux Service {#9}

### 9.1 Custom Instructions

```bash
/init   # Gõ lệnh này trong chat để Copilot tự generate file này từ codebase của bạn
```

Hoặc tạo thủ công:

```markdown
<!-- .github/copilot-instructions.md -->
# Project: [Tên Service] – C++ Linux Service

## Tech Stack
- C++17/20 | CMake 3.20+ | GCC 12 / Clang 15
- Google Test + Google Mock for unit testing
- gcov/lcov for coverage
- spdlog for logging | protobuf for serialization
- Linux (Ubuntu 22.04 target, ARM64 production)

## Directory Structure
- src/         → Production service code
- include/     → Public headers
- test/        → Unit tests (mirrors src/ structure)
- scripts/     → Build, test, coverage, deployment scripts
- proto/       → Protobuf definitions (DO NOT edit generated *.pb.cc/h)
- third_party/ → External dependencies (DO NOT modify)

## Build Commands
- Build:          cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -- -j$(nproc)
- Debug build:    cmake -B build -DCMAKE_BUILD_TYPE=Debug -DCOVERAGE=ON
- Run tests:      cd build && ctest --output-on-failure
- Coverage:       bash scripts/coverage.sh
- Lint:           clang-tidy -p build src/**/*.cpp

## Code Conventions
- Modern C++: prefer std::optional, std::expected, RAII, smart pointers
- Error handling: std::error_code or std::expected<T, E> – NEVER throw in hot paths
- Logging: spdlog levels: trace/debug/info/warn/error/critical
- No raw new/delete – use make_unique/make_shared
- Thread safety: document thread ownership; use std::mutex explicitly
- Max function length: 50 lines; max complexity: 10

## Critical Rules
- NEVER modify files in proto/ generated code – run: scripts/gen_proto.sh
- All public functions MUST have unit test coverage
- No C-style casts: use static_cast/reinterpret_cast explicitly
- No blocking calls in async context – use std::async or coroutines
```

### 9.2 Path-Specific Instructions

```markdown
<!-- .github/instructions/tests.instructions.md -->
---
applyTo: "test/**/*.cpp,test/**/*.h"
---
# Test File Conventions
- Framework: Google Test (gtest) + Google Mock (gmock)
- One test file per source file: test/foo_test.cpp for src/foo.cpp
- Fixture class name: class FooTest : public ::testing::Test
- Test naming: TEST_F(FooTest, MethodName_Condition_ExpectedResult)
- Mocks: class MockBar : public IBar { ... } in test/mocks/mock_bar.h
- No production logic in test files – test behavior, not implementation
- ASSERT_* for fatal failures, EXPECT_* for non-fatal
- Parameterized tests for multiple input cases: INSTANTIATE_TEST_SUITE_P
```

```markdown
<!-- .github/instructions/includes.instructions.md -->
---
applyTo: "include/**/*.h,src/**/*.h"
---
# Header File Rules
- Include guards OR #pragma once (use pragma once for new files)
- Forward declarations preferred over full includes in headers
- Public interface only in include/ – implementation details in src/
- All non-trivial public methods documented with Doxygen: @brief @param @return
- No implementation in headers except: templates, inline constexpr
```

### 9.3 Agent Skills

```markdown
<!-- .github/skills/cpp-unit-test/SKILL.md -->
---
name: cpp-unit-test
description: Generate, run, and iterate unit tests for C++ code until
             achieving specified coverage target using GTest and lcov.
             Use when asked to write tests, improve coverage, or test a class.
argument-hint: "[class-name] [coverage-target: 80|90|100]"
---

# C++ Unit Test Generation Skill

## Setup
- Framework: Google Test + Google Mock
- Build: cmake -B build -DCOVERAGE=ON && cmake --build build
- Run: ./build/your_service_tests
- Coverage: bash scripts/coverage.sh → parse lcov output

## Process
1. Read header to understand full interface
2. Check test/[module]_test.cpp for existing tests and patterns
3. Identify: all public methods, all branches, all error paths
4. Generate: success cases, error cases, boundary conditions, edge cases
5. Build → Run → Check coverage → Find uncovered → Add tests → Repeat
6. Stop when: target coverage reached AND all tests pass

## Coverage Report Parsing
After running scripts/coverage.sh, look for:
  "lines......: XX.X% (NNN of MMM lines)"
  "branches...: XX.X% (NNN of MMM branches)"

To find uncovered lines: look for lines showing "####" in lcov output
or open coverage_html/[filename].cpp.gcov.html
```

```markdown
<!-- .github/skills/coverity-fix/SKILL.md -->
---
name: coverity-fix
description: Fetch assigned Coverity static analysis issues via REST API
             and fix all of them in C++ code. Use when asked about
             Coverity issues, static analysis violations, or CID fixes.
argument-hint: "[stream-name] [severity: high|medium|low|all]"
---

# Coverity Fix Skill

## API Access
Script: python scripts/coverity_api.py [stream] [username]
Or direct REST: GET https://coverity.yourcompany.com/api/v2/issues/search
Auth: Bearer ${COVERITY_TOKEN}

## Process
1. Fetch all issues assigned to current user in specified stream
2. Create checklist file sorted by severity
3. For each issue:
   - Fetch full issue detail (event trace shows the exact code path)
   - Read the source file at reported location
   - Understand root cause from event trace
   - Apply proper fix (not annotation/suppression)
   - Verify fix with: cmake --build build && ctest
4. Mark checklist progress
5. Final summary report

## Common Patterns
See: [common-fixes.cpp](./common-fixes.cpp)
```

---

## 10. Cấu Trúc File Hoàn Chỉnh {#10}

```
your-cpp-linux-service/
│
├── AGENTS.md                               ← Guide cho background/coding agents
│
├── .github/
│   ├── copilot-instructions.md             ← Global DNA
│   │
│   ├── instructions/
│   │   ├── tests.instructions.md           applyTo: test/**
│   │   ├── includes.instructions.md        applyTo: include/**
│   │   └── scripts.instructions.md         applyTo: scripts/**/*.py,*.sh
│   │
│   ├── prompts/                            ← Slash commands /name
│   │   ├── read-ticket.prompt.md           /read-ticket
│   │   ├── weekly-report.prompt.md         /weekly-report
│   │   ├── research-and-write.prompt.md    /research-and-write
│   │   ├── coverity-fix.prompt.md          /coverity-fix
│   │   ├── review-commit.prompt.md         /review-commit
│   │   └── write-tests.prompt.md           /write-tests
│   │
│   ├── agents/
│   │   ├── tdd-cpp.agent.md               TDD loop custom agent
│   │   ├── code-reviewer.agent.md         Read-only review agent
│   │   └── feature-builder.agent.md       Full feature implementation
│   │
│   ├── skills/
│   │   ├── cpp-unit-test/
│   │   │   ├── SKILL.md
│   │   │   └── test-patterns.cpp          Reference patterns
│   │   ├── coverity-fix/
│   │   │   ├── SKILL.md
│   │   │   └── common-fixes.cpp
│   │   └── weekly-report/
│   │       └── SKILL.md
│   │
│   └── hooks/
│       ├── coverage-guard.json             Stop hook for coverage
│       └── scripts/
│           ├── verify_coverage.py
│           └── inject_context.py           Inject git branch + PROJ ticket
│
├── .vscode/
│   ├── mcp.json                            ← MCP: Jira, Confluence, fetch, filesystem
│   ├── toolsets.jsonc
│   └── settings.json
│
├── scripts/
│   ├── coverage.sh                         ← cmake + gcov + lcov pipeline
│   └── coverity_api.py                     ← Coverity REST API client
│
└── tmp-downloads/                          ← Jira attachments (gitignored)
```

```markdown
<!-- AGENTS.md (root) -->
# AGENTS.md – Instructions for AI Coding Agents

## Project: [Service Name] – C++ Linux Service

## Before Any Change
1. Read the header file of the class you are modifying FIRST
2. Check if any proto-generated files are affected → regenerate with scripts/gen_proto.sh
3. NEVER edit files in: proto/*.pb.cc, proto/*.pb.h, third_party/

## Mandatory Verification Before Task is Done
Build:       cmake -B build && cmake --build build -- -j$(nproc)
Tests:       cd build && ctest --output-on-failure
Coverage:    bash scripts/coverage.sh (target: 100% for new code)
Lint:        clang-tidy -p build src/**/*.cpp (zero new warnings)

## Definition of Done
- [ ] Compiles: zero errors, zero new warnings
- [ ] All existing tests pass
- [ ] New code has unit tests with ≥ 100% line coverage
- [ ] No new Coverity/clang-tidy warnings
- [ ] spdlog used for all new diagnostic messages (no printf/cout)

## Commit Message
type(PROJ-XXXX): imperative description
Types: feat | fix | refactor | test | docs | chore | perf
```

```json
// .vscode/settings.json
{
  "chat.promptFiles": true,
  "chat.agent.enabled": true,
  "chat.mcp.autoStart": true,
  "github.copilot.chat.codeGeneration.useInstructionFiles": true,
  "chat.tools.terminal.autoApprove": {
    "/^cmake/": true,
    "/^make/": true,
    "/^ninja/": true,
    "/^ctest/": true,
    "/^bash scripts\\//": true,
    "/^python3 scripts\\//": true,
    "git status": true,
    "git log": true,
    "git diff": true,
    "rm": false,
    "git push": false
  }
}
```

---

## 11. Chiến Lược Khi Vấn Đề Lớn {#11}

### Coverity: 50+ Issues

Dùng checklist + background agent:

```
[Background Agent]
"Fix tất cả Coverity issues trong COVERITY_FIX_CHECKLIST.md.
 Fix từng item [  ], đánh dấu [x] khi xong.
 Build mỗi 10 fixes, commit mỗi severity group.
 Nếu một issue không rõ: đánh dấu [?] và note lý do.
 Tiếp tục đến khi hết toàn bộ [ ] items."
```

Background agent chạy ngầm → bạn làm việc khác → kiểm tra progress khi rảnh.

### Unit Tests: Nhiều Classes Chưa Có Test

Dùng subagents song song cho các classes độc lập:

```markdown
<!-- .github/agents/batch-test-writer.agent.md -->
---
name: Batch Test Writer
description: Generate unit tests for multiple classes in parallel
tools: ['agent', 'read', 'edit', 'runInTerminal']
agents: ['C++ TDD']
---

Given a list of classes to test:
1. Identify which are independent (can be tested in any order)
2. Spawn C++ TDD subagents in parallel for independent classes
   (max 4 concurrent to avoid build conflicts)
3. For dependent classes: process in dependency order
4. Report final coverage for each class
```

Invoke:
```
"Write unit tests for ALL classes in src/service/ that have < 80% coverage.
 Process independent classes in parallel, build after each batch."
```

### Scale theo Số Lượng

| Số items | Chiến lược | Thời gian ước tính |
|---------|-----------|-------------------|
| 1–5 issues | Agent Mode thẳng | 5–15 phút |
| 5–20 issues | Agent + Stop Hook | 15–60 phút |
| 20–50 issues | Checklist file + Agent loop | 1–3 giờ |
| 50+ issues | Background Agent + Checklist | 3–8 giờ (chạy nền) |
| Nhiều modules song song | Batch Agent + Subagents | Parallel → nhanh hơn 3–4x |

---

## 12. Tổng Kết {#12}

### Tất Cả 6 Use Cases với 1 Bảng

| Use Case | Mode | MCPs Cần | Skill/Agent | Thời Gian Tiết Kiệm |
|---------|------|---------|------------|-------------------|
| Đọc Jira + Attachments | Agent | Jira + Fetch + Filesystem | `/read-ticket` | 10–20 phút |
| Weekly Report | Agent | Jira (+ Confluence) | `/weekly-report` | 30–60 phút |
| Research + Viết bài Confluence | Ask → Agent | Confluence | `/research-and-write` | 1–2 giờ |
| Coverity Fix All | Agent/Background | Fetch (REST API) | `/coverity-fix` + Stop Hook | 2–8 giờ |
| Review Commit vs Jira | Ask | Jira | `/review-commit` | 20–40 phút |
| Unit Test 100% Coverage | Agent (TDD loop) | — | C++ TDD agent + Stop Hook | 30 phút–3 giờ |

### Flow Hàng Ngày Thực Tế

```
Sáng (5 phút):
  /read-ticket PROJ-XXXX
  → Hiểu ticket đầy đủ, kể cả logs trong attachments

Trong ngày:
  "Implement PROJ-XXXX theo requirements, sau đó viết tests đạt 100% coverage"
  → Agent tự làm, bạn review kết quả

5 phút trước MR:
  /review-commit HEAD PROJ-XXXX
  → Verify changes khớp requirements trước khi push

Thứ Sáu chiều (2 phút):
  /weekly-report
  → Báo cáo tự động từ Jira, lưu lên Confluence

Khi nhận task dọn Coverity:
  /coverity-fix cpp-linux-service-main
  → Background agent xử lý qua đêm
```

### Lộ Trình Triển Khai

```
Tuần 1: Setup cơ bản
  ✓ Tạo .github/copilot-instructions.md (dùng /init)
  ✓ Tạo .vscode/mcp.json với Jira + Confluence + Fetch
  ✓ Test: đọc một ticket, tạo weekly report
  → Ngay lập tức tiết kiệm được 30–60 phút/tuần

Tuần 2: Prompt Files
  ✓ Tạo 4 prompt files cốt lõi (read-ticket, weekly-report, review-commit, coverity-fix)
  ✓ Tạo scripts/coverage.sh cho C++ coverage pipeline
  → Slash commands sẵn sàng, coverage loop hoạt động

Tuần 3: Agent Skills + Stop Hooks
  ✓ Tạo skill: cpp-unit-test, coverity-fix
  ✓ Setup Stop Hook cho coverage guard
  → Unit test workflow hoàn toàn tự động

Tuần 4+: Custom Agents + Background
  ✓ Tạo C++ TDD agent, code-reviewer agent
  ✓ Tập quen với Background Agent cho bulk tasks
  → Coverage loop + Coverity fix chạy nền, không block bạn
```

### Quick Reference Prompts

```bash
# Đọc ticket đầy đủ kể cả file đính kèm
"Read PROJ-1234 with all attachments"

# Weekly report
"Generate my weekly Jira report and save to reports/weekly/"

# Research + viết bài
"Research [topic] on Confluence and create a TIL article on my space"

# Coverity
"Check my Coverity issues in stream cpp-linux-service-main and fix all of them"

# Review
"Review commit HEAD against PROJ-1234 requirements"

# Unit tests
"Write unit tests for ConnectionManager until 100% line and branch coverage"

# Combine: ticket → implement → test → update
"Read PROJ-1234, implement the feature, write tests to 100% coverage,
 then update the ticket to In Review with a summary"
```

---

### Resources

- [VS Code Copilot Agent Mode](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode)
- [VS Code Agent Skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [VS Code Custom Agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
- [VS Code Hooks](https://code.visualstudio.com/docs/copilot/customization/hooks)
- [VS Code Background Agents](https://code.visualstudio.com/docs/copilot/agents/background-agents)
- [MCP Atlassian Server](https://github.com/sooperset/mcp-atlassian)
- [MCP Fetch Server](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch)
- [MCP Filesystem Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
- [Coverity REST API v2 Docs](https://sig-docs.synopsys.com/polaris/api/coverity)
- [Agent Skills Open Standard](https://agentskills.io/)
