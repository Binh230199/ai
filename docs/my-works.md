---
name: my-work-desciption
desciption: Tôi là một software engineer làm  việc tại LG Electronics Vietnam (LGEDV). Công việc của tôi là phát triển các phần mềm cho xe hơi (IVI, HUD, RSE,...). Là một software engineer, tôi thường có rất nhiều các công việc khác nhau trong mỗi ngày, như check mail, check jira ticket, design software, viết code, viết test, test thiết bị, viết document, fix static issues, fix bug, commit code, review code... Môi trường phát triển phần mềm của tôi thường là máy ảo Linux, và Window. Ngôn ngữ làm việc chính là C/C++, Java/Kotlin, tôi phát triển các service C++ chạy trên Linux và Android, đồng thời, tôi cũng làm các ứng dụng HMI cho xe hơi trên Android, phát triển App trên Android Studio và tích hợp nó vào AOSP
---

# Công việc của tôi - Một embedded software engineer

## 1. Mail - outlook
- Đọc các mail quan trọng: từ SWPL, FO (function owner), đồng nghiệp ở các teams khác (mỗi feature là một team), đồng nghiệp cùng team của tôi, các bộ phận trong công ty, trong team, quản lý của tôi,...
- Gửi mail phản hồi nếu tôi là người nhận trực tiếp hoặc có liên quan tới team dự án của tôi. => `Tối ưu được cách viết email nhanh chóng`

## 2. Jira - quản lý ticket/issue
- Kiểm tra tất cả các ticket đang được assign cho tôi. Nếu có ticket mới, kiểm tra xem nó là gì. Nếu nó đang in-progress, tôi sẽ tiếp tục làm nó. => `Tối ưu quy trình đọc, phân tích, và hiểu các ticket, có biện pháp tối ưu rút ngắn thời gian analyze một ticket bất kỳ`.
- Kiểm tra tất cả các ticket đang được assign cho các đồng nghiệp làm cùng feature với tôi. Mục đích là để nắm rõ các feature của đồng nghiệp đang có tiến độ như thế nào, và để học hỏi và hiểu cách làm của họ.  => `Tối ưu quy trình đọc, phân tích, và hiểu các ticket, có biện pháp tối ưu rút ngắn thời gian analyze một ticket bất kỳ, tóm tắt và show ra được quá trình phát triển của họ`.
- Tôi cũng có thể tự tạo các ticket mới và gán cho tôi để thực hiện, ví dụ như test, implement. -> `Tự tạo description, tự comment vào ticket`
- Nếu một ticket là BUG, đọc và phân tích bug xem nó là gì, đọc tất cả các description, comments, các tài liệu đính kèm như hình ảnh, file nén, (video nếu được, không được thì thôi), đọc log, đọc code base (nếu có). => `Phân tích tự động các bug/issue, đưa ra giải pháp, cách giải quyết (nếu có thể)`

## 3. Implement

### 3.1 Viết code

#### 3.1.1 C/C++


#### 3.1.2 Java/Kotlin


### 3.2 Build & Complile

#### 3.2.1 C/C++
- CMake project,  Makefile project trên Ubuntu (Yocto project).

#### 3.2.2 Java/Kotlin
- Gradle build trên android studio
- Soong build trên AOSP source code
### 3.3 Fix static issues: AUTOSAR C++14, CERT CPP, STATIC
- Chạy Local scan tool để scan xem code mới implement có tạo ra các static issue mới hay không, nếu có thì fix, fix cho tới khi nào không có các issue nào đáng lo ngại.
- Chạy tool chẩn đoán để port các file report từ Local scan tool để hiển thị các issue trực tiếp trên code. Giống như các công cụ Lint trên VSCode.
### 3.4 Viết Unittest
#### 3.4.1 C/C++
- Sử dụng Google Test framework (Gtest, GMock) để viết test
#### 3.4.2 Java/Kotlin
- Sử dụng JUnit, Mockito, ...
### 3.5 Testing
#### 3.2.1 Push C/C++ service vào board để test
- Sử dụng adb
#### 3.2.2 Push Android app vào board để test
- Sử dụng adb
## 4. Gerrit - Quản lý source code

### 4.1 Sync code
### 4.2 Push code
- Hướng dẫn push code:
- Hướng dẫn update patchset mới
### 4.3 Cherry-pick để rebase một commit để resolve conflict

### 4.4 Review code
#### 4.4.1 C/C++
1. Review chung

2. Review coding style

3. Review theo business logic

4. Review theo chuẩn rule nào đó

#### 4.4.2 Java/Kotlin
1. Review chung

2. Review coding style

3. Review theo business logic

4. Review theo chuẩn rule nào đó

## 5. Confluence - Quản lý tài liệu, workspace làm việc, document
### 5.1 Tìm kiếm các tài liệu trên Collab
- Tìm kiếm, tổng hợp thông tin từ các trang collab để cung cấp thông tin về một vấn đề nào đó. Ví dụ tôi đang bắt đầu nghiên cứu SELinux, tôi có thể sử dụng search trên collab để tìm các trang có thông tin về SELinux và học hỏi chúng
- Đọc và phân tích các trang collab.
### 5.2 Viết một bài viết mới
- Tôi viết các bài viết để lưu lại kiến thức trên trang cá nhân, hoặc viết các tài liệu về dự án để mọi người cùng theo dõi.

## 6. Coverity - Fix static issues
- Kiểm tra xem các issue nào được assign cho tôi, hoặc các đồng nghiệp của tôi. Lọc ra các issue theo mức độ(High, Medium, Low) để fix.
- Fix các issue đó ở local, sau đó chạy local tool để xác nhận là các issue đã được giải quyết ở local trước khi push commit lên trên server.
- Server sẽ có lịch build cố định, nếu commit đã được apply, server sẽ scan lại và tạo report mới. Tôi sẽ check report mới để xác nhận là các issue đã thực sự được fixed.

## 7. Các nền tảng khác, các công việc phụ vặt
-

