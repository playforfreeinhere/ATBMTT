# A5/1 và TinyA5/1 — Nhóm 9
Chương trình Python minh họa hệ mã dòng: mã hóa, giải mã văn bản/file và xem từng bước biến đổi thanh ghi. Giao diện dùng Tkinter.

## 1. Cài đặt và chạy
Cài **Python 3.10 trở lên**, có **Tcl/Tk**. Trên Windows, giữ tùy chọn Tcl/Tk khi cài Python. Tải và giải nén toàn bộ repository, mở thư mục chứa README này trong VS Code rồi chạy
```powershell
py run_gui.py
```
Trên Linux/macOS, thay `py` bằng `python3`. Nếu báo thiếu `tkinter`, cài thành phần Tkinter phù hợp với bản Python đang dùng.
Không cần cài thư viện ngoài để chạy giao diện, CLI hoặc demo. `requirements.txt` chỉ chứa pytest cho kiểm thử.

## 2. Sử dụng giao diện
- Chọn TinyA5/1 hoặc A5/1, nhập khóa; chọn **Nạp ví dụ** để lấy dữ liệu mẫu.
- **Nhị phân / Tính tay:** nhập 0/1 → Mã hóa → xem thanh ghi, clock, majority và dòng S. Chọn **Đưa kết quả lên đầu vào → Giải mã** để khôi phục bản rõ.
- **Văn bản / File:** nhập văn bản tiếng Việt để mã hóa thành hex; khi giải mã, nhập bản mã hex.
- **Mã hóa file... / Giải mã file...:** chọn file đầu vào và tên đầu ra mới. Ảnh đã mã hóa là dữ liệu nhị phân; giải mã rồi mở file khôi phục bằng trình xem ảnh.
- Khi giải mã, giữ đúng thuật toán, khóa và frame. Chương trình không ghi đè file có sẵn.

| Thuật toán trong giao diện | Khóa | Frame | Ví dụ |
| --- | --- | --- | --- |
| TinyA5/1 | Chuỗi nhị phân đúng 23 bit | Không dùng | `10010101001110100110000`: `111 → 011 → 111` |
| A5/1 | Số không dấu 64 bit, thập phân hoặc `0x...` | Số không dấu 22 bit | Khóa `0x1223456789ABCDEF`, frame `0x134` |
