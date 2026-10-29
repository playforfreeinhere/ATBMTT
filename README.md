# ATBMTT — A5/1 & TinyA5/1 · Nhóm 9

## Chạy chương trình

**Windows:** tải repository bằng **Code → Download ZIP**, giải nén, rồi nhấp đúp **`chay.bat` ở thư mục ngoài cùng**. Giao diện theo mẫu PDF mở trong Chrome/Edge, không cần cài Python.

Trong VS Code, mở thư mục repository và chạy:

```powershell
py run_gui.py
```

Mã nguồn dự án nằm tại [`ATBMTT-main/ATBMTT-main`](ATBMTT-main/ATBMTT-main). Giữ nguyên thư mục khi chạy; không kéo riêng file BAT ra ngoài. Các file chạy ngoài cùng chuyển tiếp đến cùng ứng dụng bên trong.

## Tính năng

- TinyA5/1 theo Chương 4 tài liệu PDF: thanh ghi 6/8/9 bit, khóa 23 bit, nhập dữ liệu nhị phân. Ví dụ `111 → 011 → 111` với khóa `10010101001110100110000`.
- A5/1 GSM đầy đủ 19/22/23 bit, kiểm tra bằng hai burst 114 bit của vector chuẩn.
- Khung mã hóa/giải mã màu tím, kết quả xanh; mô phỏng các thanh ghi với nút Trước/Phát/Tiếp.
- Mã hóa/giải mã văn bản UTF-8 và file nhị phân thật ngay trên trình duyệt, không gửi dữ liệu lên mạng.

Xem [hướng dẫn chi tiết](ATBMTT-main/ATBMTT-main/README.md) và [đặc tả giao diện theo PDF](ATBMTT-main/ATBMTT-main/docs/giao_dien_web.md).

## Phát triển và kiểm thử

```powershell
cd ATBMTT-main/ATBMTT-main
py -m pip install -r requirements.txt
py -m pytest -q
node tests/web_core.cjs
```

Sửa giao diện trong `ui/web/`, rồi chạy `py ui/web/build.py` để cập nhật bản HTML độc lập. Tkinter trước đây được giữ dưới lệnh `py run_gui.py --desktop`; nó dùng biến thể Tiny khác, không dùng bản mã của nó để so với giao diện PDF mới.

AI hỗ trợ cài đặt, kiểm thử và hoàn thiện giao diện; nhóm cần ghi rõ phần hỗ trợ và tự giải thích được mã nguồn khi bảo vệ. Chương trình chỉ dùng cho học tập, không bảo vệ tính toàn vẹn dữ liệu.
