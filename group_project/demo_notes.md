# Kịch bản Demo RAG Chatbot (Thành viên 4)

## Mục tiêu
Trình bày khả năng hoạt động của giao diện Streamlit, quy trình hỏi đáp, khả năng hiển thị câu trả lời có trích dẫn (citation) và danh sách tài liệu tham khảo rõ ràng.

## Các bước thực hiện

1. **Khởi động ứng dụng**: Mở terminal tại thư mục gốc của dự án và chạy lệnh:
   ```bash
   streamlit run app.py
   ```

2. **Giới thiệu giao diện**:
   - Chỉ ra thanh sidebar bên trái hiển thị danh sách các **Câu hỏi Demo**.
   - Giới thiệu khu vực chat chính nơi người dùng tương tác với chatbot.
   - Nhấn mạnh rằng hệ thống đang lưu giữ lịch sử chat (Session State).

3. **Thực hiện Demo 3 câu hỏi**:
   - *Câu 1*: Chọn câu hỏi "Hình phạt cho tội tàng trữ trái phép chất ma tuý là gì?" từ sidebar và nhập vào khung chat. Đợi chatbot trả lời và mở rộng phần `📄 Nguồn tài liệu tham khảo` để cho thấy văn bản pháp luật được sử dụng.
   - *Câu 2*: Đặt câu hỏi "Luật Phòng chống ma tuý 2021 quy định các hình thức cai nghiện nào?". Nhấn mạnh tính năng trích dẫn trong câu trả lời khớp với nguồn tài liệu bên dưới (ví dụ `[Luật Phòng chống ma tuý 2021, Điều 3]`).
   - *Câu 3*: Đặt câu hỏi "Những nguồn nào được dùng để trả lời câu hỏi này?". Kiểm tra khả năng báo cáo lại nguồn tài liệu một cách chuẩn xác từ RAG chatbot.

4. **Kiểm tra ngoại lệ (Fallback / Xử lý biên)**:
   - Thử đặt một câu hỏi không liên quan để xem giao diện có crash không (đảm bảo hệ thống vẫn sẽ hiển thị câu trả lời fallback từ LLM cùng với một danh sách source rỗng an toàn, hoặc không crash khi pipeline trả về list rỗng).

5. **Kết luận**:
   - Nhấn mạnh sự mượt mà của UI.
   - Thông báo rằng UI đã sẵn sàng tích hợp hoàn toàn với logic `generate_with_citation()` của Task 10.
