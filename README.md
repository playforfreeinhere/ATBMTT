# A5/1 và TinyA5/1 — Nhóm 9

Chương trình Python minh họa hệ mã dòng: mã hóa, giải mã văn bản/file và xem từng bước biến đổi thanh ghi. Giao diện dùng Tkinter; không cần trình duyệt, JavaScript hay máy chủ.

## 1. Cài đặt và chạy

Cài **Python 3.10 trở lên**, có **Tcl/Tk**. Trên Windows, giữ tùy chọn Tcl/Tk khi cài Python. Tải và giải nén toàn bộ repository, mở thư mục chứa README này trong VS Code rồi chạy:

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

Cả hai tab dùng chung bộ thiết lập. Tiny theo slide: thanh ghi 6/8/9 bit, clock 1/3/3, tap 2/4/5 — 6/7 — 2/7/8, lấy S sau khi dịch. Xem [ví dụ tính tay](docs/tiny_hand_example.md).

## 3. Đọc mã nguồn

Đọc theo thứ tự: lõi thuật toán → xử lý dữ liệu → giao diện → kiểm thử.

| File/thư mục | Chức năng |
| --- | --- |
| `run_gui.py` | Điểm khởi chạy duy nhất của giao diện |
| `src/a51.py` | A5/1 đầy đủ: nạp khóa/frame, dịch, sinh S, XOR byte |
| `src/tiny_a51.py` | TinyA5/1: sinh S và lịch sử từng bước |
| `ui/operations.py` | Kiểm tra khóa, xử lý văn bản và file; không phụ thuộc Tkinter |
| `ui/binary.py` | Xử lý chuỗi bit và định dạng bảng bước trung gian |
| `ui/gui.py` | Cửa sổ, hai tab và các nút; chạy tác vụ nặng ở luồng nền |
| `ui/cli.py` | Mã hóa/giải mã file bằng dòng lệnh |
| `tests/` | Kiểm thử lõi, dữ liệu, CLI và giao diện |
| `attacks/keystream_reuse.py` | Demo tác hại của dùng lại dòng khóa |
| `test.py` | Demo tổng hợp và kiểm tra khôi phục tệp văn bản |
| `data/sample_plain.txt` | Tệp văn bản mẫu |

Tất cả mã thực thi là Python. Thư mục đã được đưa ra gốc; không còn `ATBMTT-main/ATBMTT-main`, bản web hay các file mở nhanh trùng lặp.

## 4. Kiểm thử và demo

Tại thư mục gốc:

```powershell
py -m pip install -r requirements.txt
py -m pytest -v
py test.py
py -m attacks.keystream_reuse
```

`PASSED`: đạt. `SKIPPED`: chưa chạy; hai ca mở cửa sổ sẽ được bỏ qua nếu môi trường không có màn hình. `test.py` dùng file tạm và tự dọn sau khi kết thúc.

Chạy riêng lõi để xem ví dụ:

```powershell
py src/a51.py
py src/tiny_a51.py
```

CLI được giữ để chạy file bằng lệnh:

```powershell
py -m ui.cli encrypt data/sample_plain.txt data/sample_encrypted.bin 0x1A2B3C4D
py -m ui.cli decrypt data/sample_encrypted.bin data/sample_decrypted.txt 0x1A2B3C4D
```

CLI dùng bộ chuyển khóa số 32 bit `TinyA51(key)`, còn GUI dùng trực tiếp chuỗi 23 bit. Hai định dạng không thể thay thế cho nhau. Mỗi lần mã hóa/giải mã phải tạo lại đối tượng với cùng thiết lập; khi xử lý nhiều khối của một file thì giữ nguyên đối tượng giữa các khối.

## 5. Thành viên và nguồn tham khảo

Trịnh Duy Thành · Nguyên Như Chí Kiên · Lê Tuấn Hưng · Nguyễn Thanh Thảo.

Đóng góp được ghi nhận trong [lịch sử commit](https://github.com/playforfreeinhere/ATBMTT/commits/main/). Nhóm cần xác nhận phần tự thực hiện, phần tham khảo và phần AI hỗ trợ trong báo cáo.

- [Briceno, Goldberg và Wagner — A Pedagogical Implementation of A5/1](https://cryptome.wikileaks.org/jya/a51-pi.htm): đối chiếu cấu trúc và vector A5/1.
- Slide “Chương 2 — Mã hóa khóa đối xứng”, trang 46–50: quy tắc và ví dụ TinyA5/1.

Chương trình phục vụ học tập; không tích hợp xác thực tính toàn vẹn. Giải mã đúng dữ liệu mẫu không chứng minh hệ mã an toàn cho dữ liệu thực tế.
