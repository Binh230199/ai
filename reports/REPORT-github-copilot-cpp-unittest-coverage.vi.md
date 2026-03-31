# Playbook Thực Chiến: Dùng GitHub Copilot Xây Hệ Thống Agentic Viết Unit Test C++ Và Đẩy Coverage Tới Mục Tiêu

## 1. Mục tiêu thực sự của bài toán

Người dùng nói rất rõ: đích đến là coverage 100%. Điều đó có nghĩa hệ thống không được dừng ở mức "đã viết vài test case". Nó phải có vòng lặp khép kín:

- setup môi trường build/test/coverage
- phân tích code và dependency boundaries
- thiết kế test matrix
- tạo mocks/fakes/seams nếu cần
- viết test cases
- chạy test và coverage
- đọc uncovered lines/branches
- sinh thêm test hoặc đề xuất seam/refactor có kiểm soát
- lặp cho tới khi đạt mục tiêu hoặc gặp blocker thực sự

Tuy nhiên, cần nói thẳng một điều: 100% coverage chỉ có giá trị nếu được hiểu là một tiêu chí đóng việc, không phải giấy phép để viết test vô nghĩa. Một hệ thống chuyên nghiệp phải tối ưu cả `coverage` lẫn `signal quality`.

## 2. Vì sao viết unit test C++ tự động khó hơn tưởng tượng

C++ testing automation thường thất bại vì các nguyên nhân sau:

1. Build system phức tạp, environment setup không deterministic.
2. Code có nhiều dependency ẩn, global state, singleton, macro, template, side effects.
3. Một function nhìn nhỏ nhưng seam testability nằm ở tầng khác.
4. Agent dễ viết test happy-path nhưng bỏ sót branch khó, error path, exception path.
5. Nếu không có coverage artifacts cấu trúc, agent không biết chính xác còn thiếu gì.
6. Nếu cho phép sửa production code tùy tiện, agent có thể phá semantics chỉ để tăng coverage.

## 3. Nguyên tắc thiết kế cho workflow này

### 3.1. Coverage target phải có scope rõ ràng

Đừng nói chung chung "100% coverage cho project" nếu job thực tế chỉ nhắm một module hoặc một tập function. Manifest phải chỉ rõ:

- target files
- target functions/classes
- loại coverage cần theo dõi: line, branch, function
- tool đo coverage

Ví dụ tốt:

```json
{
  "objective": "Reach 100% line and branch coverage for src/parser/*.cpp excluding generated code",
  "coverageTool": "llvm-cov",
  "targets": ["src/parser/lexer.cpp", "src/parser/tokenizer.cpp"]
}
```

### 3.2. Design-before-code

Trước khi viết test, phải có test matrix. Nếu không, agent sẽ viết theo cảm hứng, dẫn tới coverage tăng chậm và nhiều case trùng.

### 3.3. Tách setup, strategy, implementation, verification thành role riêng

Đây là chỗ multi-agent phát huy tác dụng. Không nên để một agent vừa đo coverage, vừa nghĩ test design, vừa sửa harness, vừa viết test.

### 3.4. Production refactor chỉ được phép khi có policy rõ ràng

Nhiều chỗ khó test trong C++ cần thêm seam, inject dependency, hoặc tách hàm nhỏ hơn. Điều đó hợp lệ, nhưng phải có policy:

- ưu tiên refactor không đổi semantics
- ưu tiên hạ tầng testability hơn logic change
- refactor phải được verify riêng

## 4. Kiến trúc agentic đề xuất

### 4.1. Vai trò agent

#### Orchestrator

Nhiệm vụ:

- xác định scope coverage
- tạo manifest
- chia pha setup, strategy, implementation, verification
- lặp tới khi coverage target đạt

#### Harness setup agent

Nhiệm vụ:

- phát hiện build system
- xác định framework: gtest/gmock/Catch2/custom
- cấu hình compile flags, sanitizer nếu cần, coverage flags
- tạo hoặc sửa test target cần thiết

#### Test strategist

Nhiệm vụ:

- phân tích target function/class
- lập test matrix
- phân loại dependency: pure, IO, network, clock, filesystem, singleton, global state
- đề xuất mock/fake/seam strategy

#### Test writer

Nhiệm vụ:

- hiện thực test cases theo matrix
- viết mocks/fakes hợp lệ
- giữ diff nhỏ và rõ ràng

#### Coverage verifier

Nhiệm vụ:

- chạy test
- thu coverage artifacts
- phân tích uncovered lines/branches
- trả về danh sách gap còn lại có cấu trúc

## 5. Các artifacts bắt buộc để workflow đóng kín

### 5.1. `artifacts/testing/manifest.json`

```json
{
  "jobId": "cpp-tests-parser-001",
  "objective": "Reach 100% line and branch coverage for parser module",
  "targets": ["src/parser/lexer.cpp", "src/parser/tokenizer.cpp"],
  "coverageTool": "llvm-cov",
  "currentCoverage": {
    "line": 0,
    "branch": 0
  },
  "exitCriteria": {
    "line": 100,
    "branch": 100,
    "tests": "pass"
  }
}
```

### 5.2. `artifacts/testing/test-matrix.md`

Liệt kê từng function và các case cần có:

- happy path
- boundary conditions
- invalid input
- error propagation
- exception path
- branch combinations
- state transitions

### 5.3. `artifacts/testing/uncovered.json`

Coverage verifier cập nhật file này sau mỗi vòng:

```json
{
  "files": [
    {
      "file": "src/parser/lexer.cpp",
      "uncoveredLines": [77, 78, 91],
      "uncoveredBranches": [
        { "line": 91, "branch": "false" }
      ],
      "notes": ["exception path not exercised"]
    }
  ]
}
```

### 5.4. `artifacts/testing/runbook.md`

Ghi các quyết định quan trọng:

- tại sao chọn mock/fake nào
- production seam nào được thêm
- branch nào khó cover và cách cover
- các lệnh build/test/coverage đã dùng

## 6. Workflow chi tiết từng pha

### Pha 1: Environment setup

Harness setup agent phải trả lời được các câu hỏi sau:

- project dùng CMake, Bazel, Make hay hệ khác?
- framework test nào có sẵn?
- compile database có sẵn không?
- coverage dùng gcov, llvm-cov hay lcov?
- command nào build nhanh nhất cho scope target?

Output của pha này phải chuẩn hóa thành:

- `build command`
- `test command`
- `coverage command`
- `artifacts paths`

Không có bước này, phần còn lại rất dễ sa lầy chỉ vì build environment.

### Pha 2: Discovery và classification

Test strategist đọc code mục tiêu và phân loại mỗi đơn vị kiểm thử:

#### Loại A: Pure logic

Không phụ thuộc IO/global state. Viết test trực tiếp.

#### Loại B: Interface-bound

Phụ thuộc interface có thể mock. Dùng gmock hoặc fake.

#### Loại C: Hard dependency

Phụ thuộc singleton, static function, time, filesystem, network, OS call.

Với loại C, strategist phải chỉ ra một trong các hướng:

- injectable seam
- wrapper abstraction
- deterministic fake
- limited refactor to create test seam

### Pha 3: Test matrix design

Test matrix nên có format như sau:

```markdown
## lexer::Tokenize

- case: empty input -> returns empty token list
- case: single identifier -> one token
- case: invalid char -> error branch
- case: escaped quote -> special branch
- case: end-of-input mid-string -> exception path

Dependencies
- none

Coverage intent
- line: 100
- branch: true/false on line 91, 105, 117
```

Nếu không map case tới uncovered branches cụ thể, 100% coverage sẽ rất chậm đạt.

### Pha 4: Implement tests

Test writer chỉ nên nhận:

- target file(s)
- test matrix đoạn liên quan
- mock strategy
- allowed production refactors nếu có
- verification commands

Test writer không nên tự ý mở rộng scope.

### Pha 5: Local verification

Sau mỗi cụm test:

- compile target test
- run target test
- thu coverage
- cập nhật `uncovered.json`

### Pha 6: Coverage triage loop

Coverage verifier phải trả về kết quả không mơ hồ:

```markdown
Current coverage:
- line: 92.4
- branch: 88.1

Remaining gaps:
- lexer.cpp: line 91 false branch not covered
- tokenizer.cpp: lines 144-146 exception path not covered

Likely missing tests:
- malformed string that exits via parse error
- dependency fake returning timeout
```

### Pha 7: Decide next action

Orchestrator quyết định một trong ba hướng:

1. viết thêm tests
2. sửa/mock harness
3. thêm seam/refactor production có kiểm soát

### Pha 8: Close only on quantified proof

Chỉ kết thúc khi:

- tests pass
- coverage report chứng minh target đạt
- không còn uncovered lines/branches trong scope

## 7. Thiết kế `.github/` primitives cho workflow C++ này

### 7.1. `cpp-testing.instructions.md`

```markdown
---
description: "Use when writing C++ unit tests, creating gmock-based doubles, improving coverage, or closing uncovered branches in C++ code."
---

# C++ Testing Workflow

- Always define coverage scope before implementing tests.
- Produce a test matrix before writing code.
- Prefer seams and dependency injection over brittle preprocessor hacks.
- Do not claim coverage targets without coverage artifacts.
- Refactor production only when required for testability and when semantics remain unchanged.
```

### 7.2. `write-cpp-tests.prompt.md`

```markdown
---
description: "Write C++ unit tests to a target coverage goal using the existing manifest and coverage artifacts."
agent: "orchestrator"
---

Load the test manifest from `artifacts/testing/manifest.json`.
Review the latest uncovered coverage report.
Delegate strategy, implementation, and verification.
Continue until the exit criteria are satisfied.
```

### 7.3. `test-strategist.agent.md`

Tool set: `[read, search]`

Body cần yêu cầu agent:

- xuất test matrix
- phân loại dependencies
- đề xuất seams cụ thể
- chỉ rõ uncovered branches cần nhắm tới

### 7.4. `test-writer.agent.md`

Tool set: `[read, search, edit, execute]`

Body cần ràng buộc:

- implement only assigned tests
- keep tests readable and deterministic
- do not change production behavior

### 7.5. `coverage-verifier.agent.md`

Tool set: `[read, search, execute]`

Body cần yêu cầu:

- run coverage commands
- emit uncovered lines/branches as structured data
- never edit code

## 8. Hook strategy cho C++ testing automation

### 8.1. PreToolUse

Các policy hữu ích:

- nếu job chỉ là test writing, không cho sửa file ngoài target scope và test harness scope
- nếu agent định sửa build scripts ở phạm vi rộng, yêu cầu ask
- deny destructive clean commands không cần thiết

### 8.2. PostToolUse

Sau `edit`:

- nếu file là test file hoặc harness file, chạy compile/test scope nhỏ
- nếu edit production seam, chạy cả production target compile + related tests
- ghi kết quả vào `runbook.md`

### 8.3. Stop

Ghi summary chuẩn hóa:

- target coverage trước/sau
- test files đã thêm
- mock/fake nào đã tạo
- seam/refactor nào đã thêm
- gap còn lại

## 9. Pattern quan trọng để đạt coverage nhanh mà không lãng phí token

### Pattern 1: Coverage gap drives prompt, không phải code size

Đừng bảo agent "viết thêm test cho file này". Hãy đưa cho nó gap cụ thể:

- line nào chưa cover
- branch nào chưa cover
- path nào chưa được kích hoạt

### Pattern 2: Separate strategy from implementation

Nếu strategist đã map `missing branch -> missing scenario`, writer không cần reasoning lại từ đầu.

### Pattern 3: Mock only at the boundary

Trong C++, mock quá sâu tạo test giòn và tốn thời gian. Chỉ mock ở nơi boundary rõ ràng:

- interface/service boundary
- filesystem/network/time abstraction
- external process boundary

### Pattern 4: Refactor for testability only under policy

Nếu function không thể test vì dính global state, hãy cho phép refactor nhỏ có kiểm soát:

- tách pure logic
- bọc syscall
- inject clock/env/dependency

Nhưng phải ghi lại lý do trong runbook.

### Pattern 5: Coverage loop ngắn, nhiều vòng

Một vòng tốt là:

- thêm một cụm test
- chạy target tests
- lấy uncovered summary
- quay lại prompt hẹp

Điều này thường rẻ hơn cố viết một phát thật nhiều test rồi debug cả đống.

## 10. Cách xử lý các trường hợp khó

### 10.1. Template-heavy code

Chiến lược:

- tìm entry points instantiation thật sự dùng trong build
- test qua public surface thay vì cố test mọi template internals riêng lẻ

### 10.2. Global state và singleton

Chiến lược:

- tạo reset hooks cho test
- wrap access qua interface mỏng
- dùng fake environment

### 10.3. Exceptions và fatal paths

Chiến lược:

- explicit exception tests
- malformed inputs từ test matrix
- verify both type and state after exception

### 10.4. Legacy code không có seam

Chiến lược:

- strategist đề xuất refactor nhỏ nhất có thể
- verifier chạy regression checks rộng hơn cho các refactor này

## 11. Tối ưu token và premium requests cho workflow viết test

1. Đừng paste coverage HTML/XML vào chat; chuyển thành `uncovered.json` nhỏ gọn.
2. Dùng strategist để sinh test matrix một lần rồi tái dùng nhiều vòng.
3. Writer chỉ đọc phần matrix liên quan.
4. Verifier xuất gap có cấu trúc, không kể chuyện dài.
5. Khi còn 1-2 branch, prompt cực hẹp theo uncovered path là rẻ nhất.
6. Đưa mock patterns phổ biến vào skill references thay vì nhắc lại mỗi lần.

## 12. Điều kiện hoàn thành chuẩn cho job coverage 100%

Job chỉ hoàn thành khi thỏa toàn bộ:

- line coverage trong scope đạt 100%
- branch coverage trong scope đạt 100%
- test target pass ổn định
- nếu có production seam/refactor, related regression checks pass
- final report ghi rõ evidence từ coverage tool

## 13. Final report format nên dùng

```markdown
# C++ Unit Test Coverage Report

## Objective
- Reach 100% line and branch coverage for parser module

## Scope
- src/parser/lexer.cpp
- src/parser/tokenizer.cpp

## Result
- line coverage: 100%
- branch coverage: 100%
- tests: pass

## Added tests
- tests/parser/lexer_test.cpp
- tests/parser/tokenizer_test.cpp

## Testability changes
- injected clock interface into tokenizer constructor

## Evidence
- command: <coverage command>
- artifact: artifacts/testing/final-coverage.json
```

## 14. Các anti-pattern đặc biệt nguy hiểm ở bài toán này

1. Chạy theo line coverage mà bỏ branch coverage.
2. Viết test theo implementation detail quá sâu.
3. Sửa production logic chỉ để test pass.
4. Không giữ test matrix nên liên tục viết case trùng nhau.
5. Không có verifier độc lập mà tin chính test writer.

## 15. Kết luận

Muốn Copilot viết unit test C++ tới coverage target cao, nhất là 100%, phải thiết kế nó như một hệ thống điều phối đo lường, không phải một generator code. Chìa khóa là coverage artifacts có cấu trúc, test matrix, roles tách bạch, hook-based verification, và chính sách rõ ràng cho testability refactor. Khi có những thứ đó, Copilot mới có thể làm việc tuần tự, có trí nhớ, có vòng lặp, và đi tới đích thay vì viết vài test đẹp rồi dừng lại.
