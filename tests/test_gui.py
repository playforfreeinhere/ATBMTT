"""KIỂM THỬ XỬ LÝ VĂN BẢN/FILE VÀ CỬA SỔ TKINTER."""
import os
import sys
import tkinter as tk
import time
import pytest
from ui.gui import CipherApp
from ui.operations import make_cipher, process_file, process_text

@pytest.mark.parametrize( # Kiểm thử văn bản và file
    "algorithm,key",
    [("TinyA5/1", "10010101001110100110000"), ("A5/1", "0x1223456789ABCDEF")],
)
def test_text_and_binary_files(tmp_path, algorithm, key): # Kiểm tra mã hóa văn bản
    text = "Xin chào Việt Nam!\nDòng thứ hai 🔑"
    encrypted = process_text(algorithm, key, "0x134", text, False)
    
    assert bytes.fromhex(encrypted) != text.encode() # Kiểm tra bản mã khác bản rõ và giải mã khôi phục đúng văn bản ban đầu.
    assert process_text(algorithm, key, "0x134", encrypted, True) == text
    
    first, second, third = [tmp_path / name for name in ("plain", "cipher", "restored")] # Kiểm tra mã hóa file
    # Dữ liệu vượt một khối để kiểm tra bộ sinh không bị reset giữa các khối.
    data = bytes(range(256)) * 257
    first.write_bytes(data)
    
    assert process_file(algorithm, key, "0x134", str(first), str(second)) == len(data) # Kiểm tra file được mã hóa và giải mã đầy đủ, không mất dữ liệu.
    assert process_file(algorithm, key, "0x134", str(second), str(third)) == len(data)
    assert third.read_bytes() == data
    
    with pytest.raises(FileExistsError): # Kiểm tra chương trình không cho ghi đè file đã tồn tại.
        process_file(algorithm, key, "0x134", str(first), str(second))
    assert third.read_bytes() == data
    with pytest.raises(ValueError): # Kiểm tra chương trình không cho dùng cùng một đường dẫn làm file đầu vào và đầu ra.
        process_file(algorithm, key, "0x134", str(first), str(first))
    assert first.read_bytes() == data

def test_gui_a51_key_byte_order(): # Kiểm tra chương trình nạp khóa đúng thứ tự bit và sinh đúng dòng khóa A5/1.
    operation = make_cipher("A5/1", "0x1223456789ABCDEF", "0x134")
    assert operation(bytes(14)).hex() == "534eaa582fe8151ab6e1855a728c"

@pytest.mark.parametrize( # Kiểm tra dữ liệu nhập sai
    "algorithm,key,frame,text,decrypt",
    [
        ("TinyA5/1", "-1", "0", "text", False),
        ("TinyA5/1", "0x100000000", "0", "text", False),
        ("A5/1", "abc", "0", "text", False),
        ("A5/1", "1", "0x400000", "text", False),
        ("TinyA5/1", "1", "0", "not hex", True),
    ],
)
def test_bad_input(algorithm, key, frame, text, decrypt): # Đảm bảo phần nhập liệu từ chối dữ liệu không hợp lệ.
    with pytest.raises(ValueError):
        process_text(algorithm, key, frame, text, decrypt)

@pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="Requires a display; run under Xvfb on Linux",
)
def test_window_text_roundtrip(): # Kiểm thử giao diện văn bản
    root = tk.Tk()
    app = CipherApp(root)
    try:
        expected = app.inputs["text"].get("1.0", "end-1c") # Lấy văn bản ban đầu
        
        for decrypt in (False, True): # Thử mã hóa và giải mã
            app.run("text", decrypt)
            
            deadline = time.monotonic() + 10 # Đợi chương trình xử lý
            while app.future is not None and time.monotonic() < deadline:
                root.update()
                time.sleep(0.01)
            
            assert app.future is None # Xác nhận tác vụ đã kết thúc.
            if not decrypt:
                assert app.outputs["text"].get("1.0", "end-1c") != expected # Kiểm tra kết quả
                
                app.reuse("text") # Kiểm tra ô nhập frame
        assert app.outputs["text"].get("1.0", "end-1c") == expected
        app.algorithm.set("A5/1")
        app.update_algorithm()
        assert str(app.frame_entry["state"]) == "normal"
        app.algorithm.set("TinyA5/1")
        app.update_algorithm()
        assert str(app.frame_entry["state"]) == "disabled" # Kiểm tra giao diện mã hóa, giải mã văn bản và tự động bật/tắt ô nhập frame đúng thuật toán.
    finally:
        app.close()

@pytest.mark.skipif( 
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="Requires a display",
)
def test_window_binary_roundtrip(): # Kiểm thử giao diện chuỗi bit (Kiểm tra giao diện xử lý bit chính xác và hiển thị được từng bước hoạt động của thuật toán.)
    root = tk.Tk()
    app = CipherApp(root)
    try:
        for algorithm in ("TinyA5/1", "A5/1"): # Lần lượt chọn hai thuật toán và tải dữ liệu mẫu.
            app.algorithm.set(algorithm)
            app.load_example()
            original = app.inputs["bit"].get("1.0", "end-1c") # Lưu chuỗi bit ban đầu.
            for decrypt in (False, True): #  Thực hiện mã hóa rồi giải mã.
                app.run("bit", decrypt)
                deadline = time.monotonic() + 10
                while app.future is not None and time.monotonic() < deadline:
                    root.update()
                    time.sleep(0.01)
                assert app.future is None
                assert "Bước 1" in app.trace.get("1.0", "end-1c") # Kiểm tra giao diện có hiển thị lịch sử mô phỏng.
                if not decrypt:
                    app.reuse("bit")
            assert app.results["bit"] == original # Xác nhận chuỗi bit sau giải mã giống ban đầu.
    finally: 
        app.close() 

def test_shared_tiny_key_matches_binary_mode(): # Kiểm tra tính đồng nhất của TinyA5/1 ( Đảm bảo chế độ mã hóa văn bản và chuỗi bit của TinyA5/1 cho kết quả giống nhau khi dùng cùng dữ liệu và khóa.)
    key = "10010101001110100110000" # Mã hóa chuỗi bit 01000001 (ký tự A) bằng chế độ xử lý bit.
    from ui.binary import process_binary
    expected = process_binary("TinyA5/1", key, "", "01000001")[0]
    assert process_text("TinyA5/1", key, "", "A", False) == f"{int(expected, 2):02x}" # Mã hóa ký tự A bằng chế độ văn bản rồi so sánh kết quả với chế độ bit.

def test_shared_full_key_matches_binary_mode(): # Kiểm tra tính đồng nhất của A5/1 (Đảm bảo hai chế độ sử dụng cùng quy tắc nạp khóa, frame và sinh dòng khóa.)
    from ui.binary import process_binary
    key, frame = 0x1223456789ABCDEF, 0x134 # Mã hóa ký tự A dưới dạng chuỗi bit bằng A5/1. 
    expected = process_binary(
        "A5/1", format(key, "064b"), format(frame, "022b"), "01000001"
    )[0]
    assert ( # So sánh kết quả mã hóa giữa chế độ văn bản và chuỗi bit.
        process_text("A5/1", hex(key), hex(frame), "A", False)
        == f"{int(expected, 2):02x}"
    )
"""
File kiểm thử này sử dụng thư viện pytest để kiểm tra chức năng mã hóa và giải mã văn bản, file và giao diện Tkinter của hai thuật toán TinyA5/1 và A5/1.
Chương trình kiểm tra khả năng khôi phục dữ liệu gốc, xử lý file lớn mà không làm mất dữ liệu, phát hiện đầu vào không hợp lệ và ngăn ghi đè file.
Ngoài ra, các bài test còn kiểm tra thao tác trên giao diện, việc hiển thị lịch sử thuật toán và tính đồng nhất giữa chế độ mã hóa văn bản với chuỗi bit.
"""
