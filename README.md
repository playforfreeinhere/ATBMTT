# ATBMTT — Hệ mã dòng A5/1 & TinyA5/1

## Chạy giao diện chính (theo mẫu PDF)

- Windows: nhấp đúp **`chay.bat`**. File này mở giao diện mới, không cần Python.
- Hoặc mở **`giao_dien.html`** bằng Chrome/Edge.
- Trong VS Code, chạy **`py run_gui.py`** để mở cùng giao diện đó.
- Giữ `chay.bat`, `run_gui.py` và `giao_dien.html` cùng thư mục. Không chuyển riêng file BAT ra Desktop; nếu cần hãy tạo shortcut.
- Có hai khung mã hóa/giải mã, mô phỏng thanh ghi Trước/Phát/Tiếp, chế độ nhị phân, UTF-8 và file. Tiny mặc định theo Chương 4 PDF: khóa `10010101001110100110000`, P=`111`, C=`011`.
- Mã nguồn giao diện chính: `ui/web/`. Chạy `python ui/web/build.py` sau khi sửa nguồn để cập nhật file HTML độc lập.
- Giao diện Tkinter trước đây chỉ mở khi gọi rõ **`py run_gui.py --desktop`**; Tiny của bản cũ có quy tắc khác.


Dự án: Hệ mã dòng A5/1 và TinyA5/1

Nhóm: Nhóm 9
Thành viên:
- Thành viên 1: Trịnh Duy Thành 
- Thành viên 2: Nguyên Như Chí Kiên
- Thành viên 3: Lê Tuấn Hưng
- Thành viên 4: Nguyễn Thanh Thảo

Mô tả
------
Bộ mã nguồn này chứa triển khai tham chiếu của thuật toán A5/1 và một phiên bản rút gọn TinyA5/1, kèm theo giao diện đơn giản, bộ kiểm thử và mã minh họa tấn công (keystream reuse).

Mục tiêu
-------
- Thực hiện và so sánh TinyA5/1 với A5/1 đầy đủ.
- Viết unit tests để kiểm chứng kết quả với vectơ kiểm thử.
- Minh họa tấn công khi tái sử dụng dòng khóa (keystream reuse).

Yêu cầu môi trường
------------------
- Python 3.10+ 

Cài đặt phụ thuộc
------------------
Tệp requirements.txt chứa các phụ thuộc tối thiểu. Cài đặt bằng:

```bash
python -m pip install -r requirements.txt
```

Cấu trúc dự án
---------------
- src/ — Mã nguồn lõi (tiny_a51.py, a51.py)
- ui/ — Giao diện CLI thử nghiệm (module ui.cli)
- tests/ — Unit tests (pytest)
- attacks/ — Ví dụ tấn công (keystream reuse)
- data/ — Tệp minh họa input/output
- README.md — Tài liệu hướng dẫn
- requirements.txt — Thư viện cần thiết

Hướng dẫn chạy
---------------
1. Cài đặt phụ thuộc:

```bash
python -m pip install -r requirements.txt
```

2. Chạy CLI mã hóa/giải mã mẫu:

```bash
python -m ui.cli encrypt data/sample_plain.txt data/sample_encrypted.bin 0x1A2B3C4D
python -m ui.cli decrypt data/sample_encrypted.bin data/sample_decrypted.txt 0x1A2B3C4D
```

3. Chạy unit tests:

```bash
python -m pytest -q
```

Ghi chú về đóng góp
-------------------
Để lịch sử commit thể hiện đóng góp của từng thành viên, mỗi thành viên nên:

```bash
git clone https://github.com/playforfreeinhere/ATBMTT.git
git checkout -b feature/<ten-thanh-vien>
# thực hiện thay đổi, commit rồi push
git push origin feature/<ten-thanh-vien>
```

Tài liệu nộp bài (bên ngoài GitHub)
----------------------------------
- Báo cáo Word: Phân tích, sơ đồ khối, tính tay ví dụ TinyA5/1 đối chiếu với kết quả chương trình, phân công công việc.
- Slide thuyết trình.
- Video demo (3–5 phút): Quay màn hình minh họa chạy chương trình, unit test, và log nội bộ TinyA5/1.

Quy ước thuật toán và API
-------------------------
- A5/1 dùng thanh ghi 19/22/23 bit; tap R3 là 7, 20, 21, 22 (đếm từ bit thấp, bắt đầu 0). Bộ test đối chiếu cả hai chuỗi 114 bit của vector tham chiếu Briceno/Goldberg/Wagner: khóa byte `12 23 45 67 89 AB CD EF`, frame `0x134`.
- `A51Cipher(key_bits, frame_number)` nhận đúng 64 bit theo thứ tự nạp và frame 22 bit. Với khóa dạng byte, nạp từng byte theo thứ tự, bit thấp trước trong mỗi byte. `process_bytes()` dùng chung cho mã hóa/giải mã.
- TinyA5/1 là biến thể phục vụ học tập của dự án, dùng thanh ghi 6/8/9 bit. Index 0 là đầu nạp feedback; lấy bit đầu ra trước khi dịch. `TinyA51Cipher(r1, r2, r3)` nhận ba danh sách bit và hỗ trợ `process_bits()` cùng log từng bước. Vector minh họa trong mã cho dòng khóa `1, 0, 0, 1`.
- `TinyA51(key)` cung cấp `keystream_bytes()`, `encrypt()` và `decrypt()` cho CLI. Khóa nguyên không dấu 32 bit được XOR-fold thành trạng thái 23 bit: `(key & ((1 << 23) - 1)) ^ (key >> 23)`. Chia lần lượt 6/8/9 bit thấp vào các danh sách thanh ghi, bit thấp trước. Đây là quy ước minh họa, có thể có khóa trùng trạng thái; không phải hàm dẫn xuất khóa bảo mật.
- Giải mã cần tạo đối tượng mới với cùng trạng thái/khóa. Đối tượng đang dùng tiếp tục dòng khóa qua các lần gọi.
- CLI từ chối ghi đè file đã tồn tại và từ chối dùng cùng file đầu vào/đầu ra. Khóa nhận dạng thập phân hoặc hex `0x...`; lỗi trả mã thoát khác 0.
- Dự án phục vụ học tập. TinyA5/1 và A5/1 không phù hợp để bảo vệ dữ liệu thực tế; mã hóa XOR ở đây không xác thực dữ liệu.

Chạy các demo độc lập từ thư mục gốc repository:

```bash
python src/a51.py
python src/tiny_a51.py
python test.py
python -m attacks.keystream_reuse
```

`test.py` dùng chung thuật toán trong `src/`, tạo file demo trong thư mục tạm và tự dọn dẹp. Bộ pytest kiểm tra vector A5/1, vector TinyA5/1, CLI, dữ liệu nhị phân/UTF-8, lỗi đầu vào và minh họa tái sử dụng dòng khóa.

Giao diện Tkinter cũ (Windows / VS Code)
------------------------------------
Mở đúng thư mục chứa `run_gui.py` bằng VS Code. Trong Terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_gui.py --desktop
```

Lệnh trên mở bản Tkinter cũ. Để mở giao diện chính theo PDF, chạy `py run_gui.py` hoặc nhấp đúp `chay.bat`.
Tkinter đi kèm bộ cài Python chính thức trên Windows; khi cài cần giữ tùy chọn Tcl/Tk. Trên Linux cần Python có Tkinter và màn hình đồ họa.

- Tab **Văn bản**: nhập văn bản → **Mã hóa → Hex** → **Đưa kết quả lên đầu vào** → **Giải mã → Văn bản**. Giữ nguyên thuật toán, khóa và số khung để khôi phục đúng văn bản.
- Tab **File**: chọn file đầu vào và tên file đầu ra mới, rồi chọn mã hóa hoặc giải mã. Hỗ trợ cả ảnh và file nhị phân; không ghi đè file đã có. Nếu thao tác bị gián đoạn hoặc hết dung lượng, file đầu ra có thể chưa hoàn chỉnh; hãy bỏ file đó và chọn tên mới khi thử lại.
- TinyA5/1 dùng khóa nguyên 32 bit. A5/1 dùng khóa nguyên 64 bit được biểu diễn thành 8 byte big-endian, sau đó nạp từng byte từ bit thấp đến bit cao. Ví dụ khóa `0x1223456789ABCDEF`, số khung `0x134` tương ứng vector chuẩn trong test.
- File đầu ra chỉ chứa dữ liệu mã hóa, không chứa khóa, thuật toán hoặc số khung. Bạn cần lưu lại các thiết lập để giải mã.
- Công cụ phục vụ minh họa; khóa sai không phải lúc nào cũng báo lỗi và các hệ mã này không bảo vệ tính toàn vẹn.

Hai chế độ phục vụ bài tập
-------------------------
Giao diện Tkinter cũ `python run_gui.py --desktop` có ba tab:

1. **Nhị phân / Tính tay**: TinyA5/1 nhận đúng 23 ký tự 0/1, chia trực tiếp thành R1 6 bit, R2 8 bit, R3 9 bit. A5/1 nhận khóa nhị phân 64 bit và frame nhị phân 22 bit. Nhấn **Nạp ví dụ**, mã hóa, đưa bản mã lên đầu vào và giải mã. Hiện trước/sau của từng thanh ghi, bit clock, majority, thanh ghi quay, S và XOR. Giới hạn bảng 4096 bit.
2. **Văn bản**: UTF-8 ↔ ciphertext hex. Phần này giữ quy ước khóa Tiny 32 bit XOR-fold của CLI cũ; không dán trực tiếp khóa 23 bit vào ô số. Thiết lập tab nhị phân được nhập riêng để tránh nhầm định dạng.
3. **File**: xử lý dữ liệu nhị phân thật theo từng khối, giữ trạng thái dòng khóa giữa các khối. Hai chiều dùng phép XOR và cùng thiết lập.

Xem [ví dụ tính tay](docs/tiny_hand_example.md). TinyA5/1 không có một biến thể chuẩn duy nhất; cần đối chiếu độ dài thanh ghi, tap, clock, thứ tự bit và thời điểm lấy S với ví dụ trên lớp trước khi khẳng định đáp ứng tiêu chí này.

### Bản một file cho máy Windows đang dùng mã cũ

Nếu không tải được ZIP, mở `run_gui_doc_lap.py`, sao chép toàn bộ nội dung vào `run_gui.py` trên máy, đặt cùng cấp với `test.py` và thư mục `src`. Đây là bản Tkinter dự phòng, không phải giao diện web theo PDF. Không thay thế file `run_gui.py` chính bằng bản này nếu đang dùng giao diện web.

Bản này chỉ phụ thuộc hai lõi `src/a51.py` và `src/tiny_a51.py` đã có. Cả tab bit lẫn tab văn bản/file đều dùng **cùng khóa Tiny trực tiếp 23 bit**, không XOR-fold 32 bit. Với A5/1, khóa và frame nhập thập phân hoặc `0x...`; bản rõ tab nhị phân vẫn là bit. Đổi thuật toán / Nạp ví dụ sẽ thay khóa và dữ liệu mẫu. File nhị phân không lưu kèm khóa/frame. Không dùng số 0/1 ở tab văn bản để thay cho chế độ bit: ba ký tự `111` là 24 bit UTF-8, còn `111` ở tab bit là 3 bit.

Bản một file chạy đồng bộ, phù hợp demo văn bản và file nhỏ. Khi hết dung lượng hoặc thao tác bị gián đoạn, file đầu ra có thể chưa hoàn chỉnh; chọn tên mới khi thử lại. Phiên bản `ui/gui.py` dùng worker để xử lý dữ liệu ở nền.

Giao diện web theo mẫu PDF (bản mới)
-----------------------------------
Nhấp đúp **`giao_dien.html`** hoặc `chay_web.bat`: chạy offline trên Chrome/Edge, không cần Python. Có các khung mã hóa/giải mã màu tím, kết quả xanh và visualizer Trước/Phát/Tiếp như Hình 3–5 của PDF. Giữ cả chế độ nhị phân, văn bản và file, cho TinyA5/1 lẫn A5/1 đầy đủ.

**Quan trọng:** Tiny của bản HTML theo đặc tả Chương 4 PDF: clock 1/3/3, tap X=2/4/5, Y=6/7, Z=2/7/8, lấy S sau khi quay. Ví dụ khóa `10010101001110100110000` mã hóa `111` thành `011`. Nó khác biến thể của CLI/Tkinter cũ; không trộn bản mã giữa các phiên bản. [Chi tiết đặc tả, nguồn tham khảo và cách kiểm thử](docs/giao_dien_web.md).
