---
name: my-work-description
description: >
  Tôi là một Software Engineer tại LG Electronics Vietnam (LGEDV),
  phát triển phần mềm cho xe hơi (IVI, HUD, RSE). Ngôn ngữ chính: C/C++,
  Java/Kotlin. Môi trường: Linux VM (Ubuntu/Yocto) và Windows.
  Tôi phát triển C++ services chạy trên Linux/Android và HMI apps tích hợp vào AOSP.
  Công cụ hàng ngày: Outlook, Jira, Confluence, Gerrit, Coverity.
  File này mô tả đầy đủ công việc hàng ngày để Agentic AI có thể nhận diện
  và tự động hoá từng phần.
---

# Mô Tả Công Việc – Software Engineer tại LGEDV Automotive

---

## 1. Email – Outlook

### Mô tả công việc
- Đọc và phân loại email mỗi sáng: từ SWPL (Software Program Lead),
  FO (Function Owner), các team feature khác, đồng nghiệp cùng team, ban quản lý.
- Email quan trọng thường liên quan đến: thay đổi requirement, bug report,
  meeting invite, review request, release schedule, customer issue.
- Soạn và gửi email phản hồi khi tôi là người nhận trực tiếp (To:) hoặc
  khi nội dung liên quan đến feature/module tôi đang phụ trách.
- Soạn email báo cáo tiến độ (status update) định kỳ hoặc theo yêu cầu.
- Forward và escalate email tới đúng người phụ trách khi cần.

### Tối ưu bằng AI
- **Đọc & phân loại:** AI đọc và tóm tắt các email dài, phân loại theo mức ưu tiên
  (action required / FYI / digest later).
- **Soạn phản hồi:** AI draft email phản hồi dựa trên nội dung email gốc và
  context dự án, tôi chỉ review và gửi.
- **Status update:** AI tổng hợp tình trạng tickets từ Jira và tự động soạn
  email báo cáo tiến độ tuần.

---

## 2. Jira – Quản Lý Ticket / Issue

### 2.1 Kiểm tra ticket của tôi

#### Mô tả công việc
- Mỗi sáng: vào Jira kiểm tra tất cả tickets đang **assigned cho tôi**.
- Với ticket mới: đọc description để hiểu yêu cầu, đọc acceptance criteria,
  xem design documents đính kèm (link Confluence, file PDF, hình ảnh mockup).
- Với ticket đang In Progress: đánh giá còn bao nhiêu việc cần làm, có blocker không.
- Với ticket đã done: confirm đã có unit test + static analysis pass + code review.
- Các trạng thái tôi cần transition: To Do → In Progress → In Review → Done.
- Tôi comment vào ticket để update tiến độ, ghi lại các quyết định kỹ thuật,
  note các vấn đề gặp phải trong quá trình implement.

#### Tối ưu bằng AI
- AI đọc toàn bộ ticket (description, comments cũ, file đính kèm như log, zip)
  và tạo bản tóm tắt: "Cần làm gì, file nào liên quan, acceptance criteria là gì."
- AI phân tích ticket và map sang codebase: "Module nào bị ảnh hưởng, function
  nào cần sửa."
- AI draft comment tiến độ vào ticket sau khi implement xong.
- AI transition status tự động sau khi implementation + tests đã pass.

### 2.2 Theo dõi ticket của đồng nghiệp

#### Mô tả công việc
- Theo dõi các ticket assigned cho đồng nghiệp cùng feature (cùng epic/sprint).
- Mục đích: nắm tiến độ tổng thể của feature, phát hiện dependency sớm
  ("Feature A của tôi chờ API từ Feature B của bạn X").
- Đọc các comment và code changes để học hỏi cách tiếp cận của họ.
- Nếu thấy ticket của đồng nghiệp bị blocked và tôi có thể giúp → chủ động.

#### Tối ưu bằng AI
- AI tổng hợp tiến độ sprint: "Team đang ở đâu, ticket nào blocked, deadline nào
  có nguy cơ slip."
- AI so sánh approach giữa ticket của tôi và ticket tương tự của đồng nghiệp,
  phát hiện inconsistency.

### 2.3 Tạo ticket mới

#### Mô tả công việc
- Tôi tự tạo sub-task hoặc task mới khi phát hiện việc cần làm không có ticket:
  ví dụ viết unit test, refactor module, fix performance issue.
- Điền đầy đủ: summary, description rõ ràng, acceptance criteria, story points,
  link parent epic, assign cho mình, set sprint.
- Comment vào ticket khi có cập nhật quan trọng.

#### Tối ưu bằng AI
- AI tự tạo ticket với description đầy đủ dựa trên mô tả ngắn gọn của tôi.
- AI tự động comment "Implementation complete. See commit [hash]. CI: pass."
  sau khi code được push.

### 2.4 Phân tích bug

#### Mô tả công việc
- Khi nhận ticket loại Bug hoặc Defect:
  1. Đọc title và description: vấn đề là gì, reproduce steps như thế nào.
  2. Đọc tất cả comments theo thứ tự thời gian: ai đã phân tích gì, giải pháp
     nào đã thử, thông tin bổ sung từ tester/customer.
  3. Xem attachments: log file (`.log`, `.txt`), crash dump (`.zip`), screenshot,
     video recording (nếu có).
  4. Tìm trong log: stack trace, error code, timestamp của sự kiện.
  5. Map log → codebase: tìm file/function xuất hiện trong stack trace.
  6. Reproduce locally hoặc trên board nếu có thể.
  7. Root cause analysis → implement fix → verify → push commit → update ticket.

#### Tối ưu bằng AI
- AI đọc toàn bộ ticket kể cả download và parse log files trong attachments.
- AI tự tìm stack trace trong log, map sang source code, pinpoint suspect functions.
- AI đề xuất root cause và cách fix dựa trên log analysis + code reading.
- AI viết analysis report vào ticket comment.

---

## 3. Implement

### 3.1 Viết code

#### 3.1.1 C/C++ Linux Service

##### Mô tả công việc
- Implement các **system services chạy trên Linux** (Ubuntu / Yocto-based distro)
  cho automotive ECU (IVI head unit, HUD, RSE).
- Ngôn ngữ: C++17, theo coding standard **AUTOSAR C++14 Guidelines**.
- Kiến trúc thường gặp: state machine, event-driven, publisher-subscriber,
  client-server qua IPC (D-Bus, socket, shared memory).
- Đọc và implement theo Software Design Description (SDD) trên Confluence.
- Implement interface: đọc header file định nghĩa API, implement `.cpp` tương ứng.
- Tích hợp với các service khác qua IPC: đọc IDL/D-Bus interface definition.
- Error handling: sử dụng `std::error_code`, không throw trong hot path.
- Logging: sử dụng internal logging framework (tương đương spdlog).
- Memory: RAII, smart pointers, không dùng raw new/delete.
- Thread safety: document ownership rõ ràng, lock/unlock balance.

##### Tối ưu bằng AI
- AI đọc SDD + header file → implement `.cpp` đầy đủ theo đúng design pattern.
- AI sinh code boilerplate cho state machine, IPC handler, event dispatcher.
- AI implement theo interface definition mà không cần giải thích lặp lại convention.

#### 3.1.2 Java/Kotlin – Android Automotive HMI

##### Mô tả công việc
- Implement **HMI (Human-Machine Interface) apps** cho màn hình xe hơi trên Android.
- Platform: **AOSP** (Android Open Source Project), custom automotive build.
- IDE: Android Studio (cho development) + command-line Soong build (cho integration).
- Architecture: MVVM với ViewModel + LiveData + Repository pattern.
- IPC với C++ backend: qua **AIDL** (Android Interface Definition Language),
  bind service, handle Binder transactions.
- UI: custom View, ConstraintLayout, fragment navigation.
- Theming: follow automotive HMI design spec (màu sắc, font, layout theo
  display resolution của từng xe model).
- Tích hợp vào AOSP: thêm app vào product makefile, define permissions,
  set up SELinux policy, system app (không qua Play Store).

##### Tối ưu bằng AI
- AI đọc AIDL interface → sinh ViewModel + Repository tương ứng.
- AI implement UI dựa trên mockup description hoặc layout spec.
- AI viết AOSP integration files (Android.bp, SELinux .te file, product makefile).

### 3.2 Build & Compile

#### 3.2.1 C/C++ – CMake / Makefile / Yocto

##### Mô tả công việc
- **CMake project**: `cmake -B build && cmake --build build -- -j$(nproc)`
- **Makefile project**: một số legacy service dùng Makefile thuần.
- **Yocto**: build toàn bộ image cho ECU, recipe `.bb` để integrate service.
  `bitbake <recipe-name>` trên build server hoặc local.
- Cross-compile: toolchain cho ARM target, không phải x86 native.
- Đọc và hiểu build error, linker error, dependency missing.
- Đôi khi cần sửa `CMakeLists.txt` hoặc `Android.mk` khi thêm file mới.

##### Tối ưu bằng AI
- AI đọc build error output → tìm root cause → fix (missing include, wrong linker flag,
  undefined symbol...).
- AI tự thêm source files mới vào `CMakeLists.txt` khi implement xong.
- AI sinh Yocto recipe khi cần package một service mới.

#### 3.2.2 Java/Kotlin – Gradle / Soong

##### Mô tả công việc
- **Android Studio / Gradle**: build và run trực tiếp trong IDE cho development.
  `./gradlew assembleDebug` hoặc `./gradlew test`.
- **Soong build (AOSP)**: build toàn bộ hoặc module cụ thể trong AOSP source tree.
  `m <module_name>` hoặc `mmm <path/to/module>`.
- Sửa `Android.bp` khi thêm dependency, thêm file, hoặc thay đổi build config.
- Build error trong AOSP thường phức tạp: dependency graph lớn,
  error message nhiều noise.

##### Tối ưu bằng AI
- AI đọc Soong/Gradle build error → phân tích → đề xuất fix.
- AI tự update `Android.bp` khi implement file mới.

### 3.3 Fix Static Issues

#### Mô tả công việc
- Sau khi implement xong, chạy **local static analysis tool** trước khi push.
- Standards được enforce:
  - **AUTOSAR C++14 Guidelines** (cho C++ service)
  - **CERT C++ Coding Standard**
  - Internal STATIC rules của project
- Quy trình:
  1. Chạy scan tool: `./run_static_analysis.sh <module>`
  2. Tool sinh report dạng XML/JSON.
  3. Chạy diagnostic tool để hiển thị issues trực tiếp trên code trong IDE
     (giống Lint / clang-tidy integration).
  4. Đọc từng issue: rule nào bị vi phạm, tại file:line nào, severity là gì.
  5. Fix issue: đảm bảo không thay đổi logic, chỉ fix style/safety violation.
  6. Chạy lại scan: xác nhận issue đã biến mất, không có issue mới.
  7. Lặp lại cho đến khi clean.
- Không push code nếu còn Mandatory/Required violations.

#### Tối ưu bằng AI
- AI nhận report từ static tool → fix tất cả issues tự động → verify lại.
- AI phân biệt issue nào có thể fix tự động an toàn vs issue nào cần human judgment.
- Stop Hook: chặn agent báo "xong" nếu scan còn issues chưa resolved.

### 3.4 Viết Unit Test

#### 3.4.1 C/C++ – Google Test / GMock

##### Mô tả công việc
- Framework: **Google Test (gtest)** + **Google Mock (gmock)**.
- Mỗi module có một test file: `test/<ModuleName>_test.cpp`.
- Mock external dependencies (IPC calls, hardware abstraction) bằng GMock.
- Coverage target: **line coverage + branch coverage** cho tất cả code mới.
- Quy trình:
  1. Đọc header để hiểu interface cần test.
  2. Viết test fixture: `class FooTest : public ::testing::Test`.
  3. Viết test cases: success path, error path, edge cases, boundary values.
  4. Build với coverage flags: `cmake -DCOVERAGE=ON`.
  5. Chạy tests: `ctest --output-on-failure`.
  6. Check coverage: `lcov` → `genhtml` → xem HTML report.
  7. Tìm uncovered branches → thêm test cases → lặp lại.
- Không push nếu coverage giảm so với baseline.

##### Tối ưu bằng AI
- AI viết test cases đầy đủ từ header file.
- AI tự loop: viết test → build → run → đọc coverage → thêm test → đến 100%.
- Stop Hook: block nếu coverage chưa đạt target.

#### 3.4.2 Java/Kotlin – JUnit / Mockito

##### Mô tả công việc
- Framework: **JUnit 5** + **Mockito** (hoặc MockK cho Kotlin).
- Viết unit tests cho ViewModel, Repository, Use Case layer.
- Mock Android framework dependencies (Context, etc.) để test chạy trên JVM.
- **Instrumented tests** (chạy trên device/emulator): Espresso cho UI tests.
- Coverage: JaCoCo report tích hợp trong Gradle.

##### Tối ưu bằng AI
- AI viết JUnit tests cho ViewModel/Repository từ source code.
- AI viết Mockito stubs cho AIDL service interfaces.

### 3.5 Testing Trên Thiết Bị (Device Testing)

#### 3.5.1 Push C/C++ Service lên Board

##### Mô tả công việc
- Target board: automotive ECU (ARM-based), kết nối qua USB hoặc mạng nội bộ.
- Công cụ chính: **ADB (Android Debug Bridge)** hoặc SSH + SCP.
- Quy trình:
  1. Cross-compile tạo binary cho ARM target.
  2. Push binary lên board: `adb push <binary> /system/bin/` hoặc `scp`.
  3. Set executable permission: `adb shell chmod +x /system/bin/<binary>`.
  4. Restart service: `adb shell stop <service>; adb shell start <service>`
     hoặc `systemctl restart <service>` nếu board chạy systemd.
  5. Monitor logs real-time: `adb logcat` hoặc `journalctl -f`.
  6. Reproduce test scenarios: gửi CAN signals, simulate user input qua HMI.
  7. Kiểm tra behavior so với expected in acceptance criteria.
  8. Nếu có crash: lấy crash dump, đọc core dump với `gdb` cross-debugger.

##### Tối ưu bằng AI
- AI viết test script tự động push binary, restart service, đọc log, verify output.
- AI phân tích crash dump / logcat output, xác định root cause.

#### 3.5.2 Push Android App lên Board

##### Mô tả công việc
- Build APK hoặc system image có chứa app.
- Với APK development build: `adb install -r <app.apk>`.
- Với AOSP integration: flash toàn bộ image hoặc push chỉ partition cụ thể.
- Test các HMI interactions: touch, knob input, voice command.
- Verify integration với backend C++ service qua AIDL binding.
- Check UI rendering đúng không: resolution, theming, animation.

---

## 4. Gerrit – Quản Lý Source Code

### 4.1 Sync Code

#### Mô tả công việc
- Fetch latest changes từ remote: `repo sync` (với Repo tool trong AOSP)
  hoặc `git fetch && git rebase origin/main`.
- Resolve conflicts nếu có sau khi rebase.
- Kiểm tra không có build regression sau khi sync: build lại và chạy tests.

#### Tối ưu bằng AI
- AI phân tích conflict markers → đề xuất resolution đúng semantic.

### 4.2 Push Code

#### Mô tả công việc
- Commit message format: `[Type][Module/Feature] Brief description`
  ví dụ: `[Fix][MediaService] Fix null pointer in playback handler`
- Push lên Gerrit để tạo Change Request (CR):
  `git push origin HEAD:refs/for/main`
- Thêm reviewer: FO (Function Owner), đồng nghiệp review chéo, tech lead.
- Điền Code Review form: self-review checklist, test evidence, impact analysis.
- Nếu reviewer request changes: sửa code → `git commit --amend` → push lại
  để tạo **new patchset** trên cùng Change ID:
  `git push origin HEAD:refs/for/main`
- Theo dõi CR đến khi có Vote +2 Code-Review + +1 Verified → Submit.

#### Tối ưu bằng AI
- AI generate commit message chuẩn format từ changes.
- AI điền CR description: summary of changes, test evidence, risk assessment.
- AI verify checklist trước khi push (static issues, tests, coverage).

### 4.3 Cherry-pick / Rebase / Resolve Conflict

#### Mô tả công việc
- **Cherry-pick**: lấy một commit từ branch khác áp dụng vào branch hiện tại.
  Thường dùng khi backport fix vào release branch cũ.
  `git cherry-pick <commit-hash>` → resolve conflicts nếu có.
- **Rebase**: cập nhật branch sau khi main đã có changes mới.
  `git rebase origin/main` → resolve conflicts từng commit.
- **Conflict resolution**: đọc cả hai phiên bản (ours vs theirs),
  hiểu context để merge đúng semantic, không chỉ chọn một phía.

#### Tối ưu bằng AI
- AI phân tích conflict: đọc cả `<<<<<<` và `>>>>>>>` sections,
  hiểu business logic của từng phiên bản → đề xuất merged result đúng.

### 4.4 Review Code

#### Mô tả công việc
Tôi được assign là reviewer cho Change Requests của đồng nghiệp.

##### 4.4.1 C/C++

**Review chung:**
- Đọc description của CR và ticket Jira liên quan để hiểu context.
- Xem toàn bộ diff: file nào thay đổi, impact scope có đúng không.
- Kiểm tra: không có dead code, không có commented-out code, không debug prints.

**Review coding style (AUTOSAR C++14 / CERT CPP):**
- Naming conventions: class, function, variable, macro theo standard.
- No implicit conversions, explicit cast expressions.
- Smart pointer usage, no raw owning pointers.
- `const` correctness.
- No magic numbers: dùng named constants.

**Review business logic:**
- Đối chiếu implementation với Jira ticket requirements và SDD trên Confluence.
- Verify state transitions hợp lệ.
- Check error handling: tất cả return values được kiểm tra.
- Check thread safety: shared state có được protect đúng không.
- Check resource management: file descriptors, sockets, memory.
- Edge cases: null input, empty container, overflow, timeout.

**Review theo rule:**
- Compile với `-Wall -Wextra`: không có warning mới.
- Unit tests có cover code mới không.
- Static analysis: không có new violations.

##### 4.4.2 Java/Kotlin

**Review chung:**
- Component lifecycle đúng (Activity/Fragment/Service lifecycle).
- No memory leaks: Context references, listener unregistration.

**Review coding style:**
- Kotlin idioms: prefer `val`, data classes, extension functions đúng chỗ.
- Null safety: không dùng `!!` trừ khi có lý do rõ ràng.

**Review business logic:**
- AIDL binding error handling.
- LiveData/StateFlow observed đúng lifecycle.
- Permission handling.

**Review theo rule:**
- ProGuard / R8 rules không làm break AIDL interface.
- AOSP integration rules (system permissions, security policies).

#### Tối ưu bằng AI
- AI review toàn bộ diff và cross-reference với Jira ticket:
  "Code có implement đúng requirements không? Có thiếu gì không?"
- AI submit inline Gerrit comments tại đúng file:line với nội dung cụ thể.
- AI review song song nhiều góc độ qua subagents: correctness, style, security, tests.
- AI tổng hợp: APPROVE / REQUEST CHANGES với justification.

---

## 5. Confluence – Tài Liệu & Knowledge Base

### 5.1 Tìm Kiếm Thông Tin

#### Mô tả công việc
- Khi bắt đầu implement feature mới: tìm Software Design Description (SDD),
  Interface Document, Architecture Document liên quan.
- Khi debug bug: tìm các trang mô tả behavior của module bị lỗi.
- Khi onboard module mới: đọc overview, history, design decisions.
- Search cách: keyword search → filter by space → sort by last modified.
- Thường phải đọc nhiều trang, tổng hợp thông tin từ nhiều nguồn.
- Tìm hiểu chủ đề mới (ví dụ SELinux, Binder, Audio HAL):
  search → đọc → tổng hợp → áp dụng vào project.

#### Tối ưu bằng AI
- AI search và tổng hợp thông tin từ nhiều Confluence pages về một chủ đề.
- AI đọc SDD và tóm tắt: "Cần implement gì, interface là gì, dependency là gì."
- AI cross-reference nhiều documents và chỉ ra inconsistency hoặc outdated info.

### 5.2 Viết Bài Viết Mới

#### Mô tả công việc
- **Personal notes / TIL**: lưu lại kiến thức học được, troubleshooting steps,
  gotchas khi làm việc với một technology/module. Đặt tại space cá nhân.
- **Project documentation**: viết hoặc update technical spec, design note,
  API documentation, meeting minutes. Đặt tại project space.
- **How-to guides**: hướng dẫn setup môi trường, quy trình build, deploy...
  để đồng nghiệp mới có thể đọc và làm theo.
- Format Confluence: headings, code blocks (với syntax highlight), tables,
  panels (info/warning/note macros), page links, attachments.

#### Tối ưu bằng AI
- AI soạn bài viết Confluence đầy đủ từ notes ngắn gọn của tôi.
- AI research topic trên Confluence hiện có → tổng hợp → tạo bài viết tổng quan.
- AI update page cũ khi có thông tin mới (ví dụ: sau khi upgrade component version).

---

## 6. Coverity – Static Analysis (Server-side)

### Mô tả công việc
- **Coverity Connect** là server chạy full static analysis trên toàn bộ codebase
  sau mỗi nightly build (lịch build cố định, thường sau giờ làm việc).
- Checkers phổ biến: `NULL_RETURN`, `RESOURCE_LEAK`, `USE_AFTER_FREE`,
  `BUFFER_OVERFLOW`, `DEADLOCK`, `DIVIDE_BY_ZERO`, `UNINIT`.
- Quy trình của tôi:
  1. **Xem issues assigned cho tôi**: vào Coverity Connect UI, filter by owner = tôi,
     status = New hoặc Triaged, stream = project stream.
  2. **Đọc issue detail**: Coverity hiển thị **event trace** – chuỗi code path
     dẫn đến defect. Đây là thông tin quan trọng nhất để hiểu root cause.
  3. **Fix local**: mở source file, đọc code, fix root cause
     (không chỉ annotate để suppress).
  4. **Verify local**: chạy local scan tool để xác nhận issue không còn,
     và không có new issues.
  5. **Push commit** lên Gerrit.
  6. **Wait for nightly build**: sau khi commit được applied, chờ server build lại.
  7. **Check server report**: verify issue đã disappear trên Coverity Connect.
- Tôi cũng theo dõi issues của đồng nghiệp để nắm tình trạng chất lượng code.

### Tối ưu bằng AI
- AI gọi Coverity Connect REST API → lấy danh sách issues assigned cho tôi.
- AI đọc event trace từ API → hiểu code path dẫn đến lỗi → fix đúng.
- AI tạo checklist, fix từng issue, track progress.
- AI verify fix với local tool trước khi push.
- AI tổng hợp pattern: "Loại lỗi nào tôi hay tạo ra? Cần chú ý điều gì?"

---

## 7. Các Công Việc Khác

### 7.1 Daily Stand-up / Meeting

#### Mô tả công việc
- Báo cáo hàng ngày: hôm qua làm gì, hôm nay sẽ làm gì, có blocker không.
- Sprint planning: estimate story points, chọn tickets cho sprint mới.
- Technical discussion: design review, architecture decision, trade-off analysis.

#### Tối ưu bằng AI
- AI tổng hợp activity của tôi trong ngày hôm qua (từ Jira + Gerrit)
  → soạn nội dung stand-up sẵn cho tôi.

### 7.2 Onboard Module / Feature Mới

#### Mô tả công việc
- Khi được assign vào feature/module mới:
  1. Đọc Confluence: architecture overview, design documents, history.
  2. Đọc codebase: tìm entry point, trace data flow, hiểu state machine.
  3. Chạy và build module để hiểu dependency.
  4. Đọc existing tests để hiểu expected behavior.

#### Tối ưu bằng AI
- AI đọc codebase + Confluence → tạo module overview: "Module này làm gì,
  dependencies là gì, các function quan trọng là gì, flow chính là gì."

### 7.3 Generate Weekly Report

#### Mô tả công việc
- Cuối tuần hoặc đầu tuần sau: tổng hợp những gì đã làm trong tuần.
- Nguồn dữ liệu: Jira (tickets transitioned, comments added), Gerrit (CRs pushed/reviewed).
- Format: theo template của team/dự án, thường gồm:
  Completed | In Progress | Blocked | Plan Next Week.
- Nộp cho manager hoặc update lên Confluence.

#### Tối ưu bằng AI
- AI pull data từ Jira + Gerrit → tổng hợp → soạn report theo template.
- AI post report lên Confluence tự động.

### 7.4 Environment Setup & Maintenance

#### Mô tả công việc
- Maintain Linux VM: Ubuntu cho development.
- Setup build environment: toolchain, SDK, AOSP repo sync (repo init + repo sync,
  thường mất vài giờ).
- Maintain dotfiles, aliases, development scripts.
- Debug environment issues: wrong toolchain version, missing library, permission issues.

#### Tối ưu bằng AI
- AI phân tích build environment error và đề xuất fix.
- AI viết setup scripts cho môi trường mới.
