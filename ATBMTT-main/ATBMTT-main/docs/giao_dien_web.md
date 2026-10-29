# Giao diện theo mẫu PDF

## Chạy trên máy cá nhân

Nhấp đúp `giao_dien.html` để mở bằng Chrome/Edge. Không cần Python, Flask, npm, tài khoản hay kết nối Internet. Đây là giao diện offline HTML/CSS/JavaScript, không phải ứng dụng Flask của nhóm tác giả PDF. Có thể dùng `chay_web.bat` trên Windows. Trong môi trường có chính sách doanh nghiệp chặn file HTML, có thể phục vụ cùng thư mục bằng `py -m http.server 8000` rồi mở địa chỉ máy cục bộ tương ứng trong trình duyệt.

Mã được chia `ui/web/core.js` (thuật toán), `styles.css`, `index.html`, `app.js` (giao diện). `python ui/web/build.py` ghép thành một file độc lập `giao_dien.html`. Không sửa riêng bản ghép rồi quên cập nhật nguồn.

## Đối chiếu tài liệu người dùng cung cấp

Nguồn tham khảo: `1007410230-Khung-Bao-Cao-Mon-an-Toan-Bảo-Mật-Thong-Tin.pdf`, Chương 4, Hình 3–5, trang PDF 19–21. Chỉ tham khảo bố cục và đặc tả thuật toán; không có mã nguồn tác giả để sao chép. AI hỗ trợ đọc đặc tả, viết và kiểm thử mã; nhóm cần tự hiểu, xác minh và ghi nhận việc sử dụng AI khi nộp bài.

PDF có các phần mô tả Tiny không thống nhất. Chương 3 nhắc đến độ dài thanh ghi khác, còn phần cài đặt Chương 4 mô tả rõ 6/8/9 bit. Giao diện này chọn **đặc tả Chương 4**, không giả định đây là biến thể được dạy trong lớp.

- Khóa 23 bit chia theo thứ tự ký tự X (6), Y (8), Z (9); index 0 bên trái, đầu nạp feedback.
- Clock: X[1], Y[3], Z[3].
- Feedback: X[2] XOR X[4] XOR X[5]; Y[6] XOR Y[7]; Z[2] XOR Z[7] XOR Z[8].
- Quay các thanh ghi có clock bằng majority; nạp feedback vào index 0. Sau khi quay, lấy S = X[5] XOR Y[7] XOR Z[8].
- Ví dụ PDF: khóa `10010101001110100110000`, P=`111`, S=`100`, C=`011`; giải mã C khôi phục P.

Biến thể này **khác** `src/tiny_a51.py` cũ (clock X[2], tap khác, S trước khi quay). Giao diện HTML dùng lõi JavaScript riêng theo PDF; giao diện Tkinter và CLI cũ được giữ nguyên để không âm thầm đổi kết quả cũ. Không trộn bản mã của hai biến thể. Không dùng lại dòng khóa trong thực tế.

A5/1 đầy đủ dùng thanh ghi 19/22/23 bit, clock 8/10/10, tap R3 chuẩn 7/20/21/22. Khóa nhập số nguyên thập phân hoặc hex được đổi sang 8 byte big-endian, nạp bit thấp trước trong từng byte; frame 22 bit nạp bit thấp trước; khởi động 100 nhịp. Kiểm tra cả hai burst 114 bit của vector Briceno/Goldberg/Wagner, không gán vector này là NIST/RFC.

## Tính năng

- Nhị phân: hai khung mã hóa/giải mã như PDF, validation khóa, kết quả màu xanh, chuyển bản mã sang ô giải mã.
- Mô phỏng: mỗi bit có ba pha (trước quay / quyết định majority / sau quay), nút Trước, Phát-Tạm dừng, Tiếp; hiển thị clock trước quay và thanh ghi theo pha. Sau quay, clock đang tô trên thanh ghi là vị trí clock trong trạng thái mới; panel ghi giá trị đã dùng trước quay.
- Văn bản: UTF-8 sang hex và ngược lại; cùng khóa/thuật toán/frame. Chèn kết quả bằng textContent để dữ liệu không trở thành HTML.
- File: toàn bộ xử lý trong trình duyệt, tối đa 2 MB cho demo; giữ trạng thái giữa các khối 4096 byte. Tải file qua Blob; không gửi lên mạng. Không lưu khóa/frame trong file, không xác thực dữ liệu. Khóa sai có thể vẫn cho dữ liệu đọc được.
- Đối chiếu: nút hiển thị kỳ vọng/thực tế và PASS/FAIL cho ví dụ PDF và hai burst A5/1 chuẩn.

## Kiểm tra

```
node tests/web_core.cjs
python tests/web_ui.py
```

Kiểm tra trình duyệt cần Playwright và Chromium; không phải phụ thuộc của ứng dụng người dùng. Trong môi trường cloud, chính sách chặn điều hướng `file://`; browser test nạp chính nội dung file ghép bằng `set_content`. Không thay đổi chính sách. Đã kiểm tra thao tác UI, mã hóa/giải mã UTF-8, tải và giải mã file nhị phân thật cho hai thuật toán; việc nhấp đúp mở file trên Windows của người dùng chưa được kiểm chứng từ máy này.
