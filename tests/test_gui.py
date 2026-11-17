"""KIỂM THỬ XỬ LÝ VĂN BẢN/FILE VÀ CỬA SỔ TKINTER.

Chạy: py -m pytest tests/test_gui.py -v.
Phần xử lý dữ liệu kiểm tra UTF-8, file qua ranh giới khối, bảo vệ file cũ
và quy ước bit khóa A5/1; các ca đó không cần cửa sổ.
Hai ca test_window_* tạo GUI thật nên chỉ chạy khi có môi trường hiển thị.
skipif bỏ qua chúng trên hệ không phải Windows và không có DISPLAY.
Đây là kiểm tra khả dụng sơ bộ, không bảo đảm mọi cấu hình Windows có Tk.

Fixture tmp_path là thư mục tạm do pytest cung cấp và tách riêng mỗi ca.
Các vòng root.update() cho Tkinter xử lý sự kiện trong khi đợi future;
deadline dùng đồng hồ monotonic để tránh đợi vô hạn. finally đóng cửa sổ.
assert kiểm tra bằng nhau theo nội dung byte, không chỉ dựa vào tên file.
"""

import os
import sys
import tkinter as tk
import time

import pytest

from ui.gui import CipherApp
from ui.operations import make_cipher, process_file, process_text


@pytest.mark.parametrize(
    "algorithm,key",
    [("TinyA5/1", "10010101001110100110000"), ("A5/1", "0x1223456789ABCDEF")],
)
def test_text_and_binary_files(tmp_path, algorithm, key):
    """Kiểm tra UTF-8 và file nhị phân cho cả Tiny lẫn A5/1.

    bytes(range(256))*257 tạo 65.792 byte, lớn hơn khối 65.536 để phát hiện
    reset dòng khóa sai giữa các khối. Kiểm tra file khôi phục bằng byte và
    đảm bảo ghi đè/cùng file bị từ chối mà không làm hỏng dữ liệu gốc.
    """
    text = "Xin chào Việt Nam!\nDòng thứ hai 🔑"
    encrypted = process_text(algorithm, key, "0x134", text, False)
    assert bytes.fromhex(encrypted) != text.encode()
    assert process_text(algorithm, key, "0x134", encrypted, True) == text
    first, second, third = [tmp_path / name for name in ("plain", "cipher", "restored")]
    # Dữ liệu vượt một khối để kiểm tra bộ sinh không bị reset giữa các khối.
    data = bytes(range(256)) * 257
    first.write_bytes(data)
    assert process_file(algorithm, key, "0x134", str(first), str(second)) == len(data)
    assert process_file(algorithm, key, "0x134", str(second), str(third)) == len(data)
    assert third.read_bytes() == data
    with pytest.raises(FileExistsError):
        process_file(algorithm, key, "0x134", str(first), str(second))
    assert third.read_bytes() == data
    with pytest.raises(ValueError):
        process_file(algorithm, key, "0x134", str(first), str(first))
    assert first.read_bytes() == data


def test_gui_a51_key_byte_order():
    """Đối chiếu 14 byte đầu dòng khóa A5/1 với vector tham chiếu.

    bytes(14) là 14 byte 0, nên XOR trả chính S. Phát hiện việc đảo thứ tự
    byte hoặc nạp bit trong byte sai ở hàm tạo bộ mã của giao diện.
    """
    operation = make_cipher("A5/1", "0x1223456789ABCDEF", "0x134")
    assert operation(bytes(14)).hex() == "534eaa582fe8151ab6e1855a728c"


@pytest.mark.parametrize(
    "algorithm,key,frame,text,decrypt",
    [
        ("TinyA5/1", "-1", "0", "text", False),
        ("TinyA5/1", "0x100000000", "0", "text", False),
        ("A5/1", "abc", "0", "text", False),
        ("A5/1", "1", "0x400000", "text", False),
        ("TinyA5/1", "1", "0", "not hex", True),
    ],
)
def test_bad_input(algorithm, key, frame, text, decrypt):
    """Chạy nhiều đầu vào khóa/frame/hex sai và yêu cầu ValueError.

    Các bộ khóa âm, vượt giới hạn, không phải số hoặc frame quá lớn phải
    bị từ chối trước khi chương trình tạo ra dữ liệu được xem là hợp lệ.
    """
    with pytest.raises(ValueError):
        process_text(algorithm, key, frame, text, decrypt)


@pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="Requires a display; run under Xvfb on Linux",
)
def test_window_text_roundtrip():
    """Tạo cửa sổ thật, chạy mã hóa/giải mã qua worker và kiểm tra ô kết quả.

    root.update xử lý callback poll; chờ tối đa 10 giây. reuse đưa bản mã
    lên đầu vào. Kiểm tra frame bật cho A5/1 và tắt cho Tiny; finally đóng app.
    Decorator skipif bỏ qua ca này nếu môi trường Linux không có DISPLAY.
    """
    root = tk.Tk()
    app = CipherApp(root)
    try:
        expected = app.inputs["text"].get("1.0", "end-1c")
        for decrypt in (False, True):
            app.run("text", decrypt)
            deadline = time.monotonic() + 10
            while app.future is not None and time.monotonic() < deadline:
                root.update()
                time.sleep(0.01)
            assert app.future is None
            if not decrypt:
                assert app.outputs["text"].get("1.0", "end-1c") != expected
                app.reuse("text")
        assert app.outputs["text"].get("1.0", "end-1c") == expected
        app.algorithm.set("A5/1")
        app.update_algorithm()
        assert str(app.frame_entry["state"]) == "normal"
        app.algorithm.set("TinyA5/1")
        app.update_algorithm()
        assert str(app.frame_entry["state"]) == "disabled"
    finally:
        app.close()


@pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="Requires a display",
)
def test_window_binary_roundtrip():
    """Thử cả hai thuật toán qua nút xử lý tab bit, gồm lịch sử từng bước.

    load_example đổi khóa và bản rõ mẫu đúng thuật toán. Đợi worker xong rồi
    kiểm tra có Bước 1; đưa kết quả lên đầu vào và xác nhận bản rõ khôi phục.
    Ca này cần màn hình đồ họa, không phải kiểm thử headless thuần thuật toán.
    """
    root = tk.Tk()
    app = CipherApp(root)
    try:
        for algorithm in ("TinyA5/1", "A5/1"):
            app.algorithm.set(algorithm)
            app.load_example()
            original = app.inputs["bit"].get("1.0", "end-1c")
            for decrypt in (False, True):
                app.run("bit", decrypt)
                deadline = time.monotonic() + 10
                while app.future is not None and time.monotonic() < deadline:
                    root.update()
                    time.sleep(0.01)
                assert app.future is None
                assert "Bước 1" in app.trace.get("1.0", "end-1c")
                if not decrypt:
                    app.reuse("bit")
            assert app.results["bit"] == original
    finally:
        app.close()


def test_shared_tiny_key_matches_binary_mode():
    """Cùng khóa Tiny, byte UTF-8 của chữ A phải khớp dữ liệu bit 01000001.

    Phát hiện tab text và tab bit dùng khác cách chia khóa hoặc thứ tự bit.
    int(expected,2) đổi chuỗi bit ra số; :02x hiển thị đủ hai ký tự hex.
    """
    key = "10010101001110100110000"
    from ui.binary import process_binary

    expected = process_binary("TinyA5/1", key, "", "01000001")[0]
    assert process_text("TinyA5/1", key, "", "A", False) == f"{int(expected, 2):02x}"


def test_shared_full_key_matches_binary_mode():
    """Đối chiếu xử lý chữ A giữa đường số/hex của GUI và đường nhị phân.

    Cùng khóa/frame phải tạo cùng byte bản mã; kiểm tra lớp chuyển định dạng
    khóa A5/1 chứ không chỉ kiểm tra khả năng khôi phục dữ liệu.
    """
    from ui.binary import process_binary

    key, frame = 0x1223456789ABCDEF, 0x134
    expected = process_binary(
        "A5/1", format(key, "064b"), format(frame, "022b"), "01000001"
    )[0]
    assert (
        process_text("A5/1", hex(key), hex(frame), "A", False)
        == f"{int(expected, 2):02x}"
    )
