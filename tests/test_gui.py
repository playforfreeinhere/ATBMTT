"""KIỂM THỬ XỬ LÝ VĂN BẢN/FILE VÀ CỬA SỔ TKINTER."""
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
    with pytest.raises(ValueError):
        process_text(algorithm, key, frame, text, decrypt)

@pytest.mark.skipif(
    sys.platform != "win32" and not os.environ.get("DISPLAY"),
    reason="Requires a display; run under Xvfb on Linux",
)
def test_window_text_roundtrip():
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
    key = "10010101001110100110000"
    from ui.binary import process_binary
    expected = process_binary("TinyA5/1", key, "", "01000001")[0]
    assert process_text("TinyA5/1", key, "", "A", False) == f"{int(expected, 2):02x}"

def test_shared_full_key_matches_binary_mode():
    from ui.binary import process_binary
    key, frame = 0x1223456789ABCDEF, 0x134
    expected = process_binary(
        "A5/1", format(key, "064b"), format(frame, "022b"), "01000001"
    )[0]
    assert (
        process_text("A5/1", hex(key), hex(frame), "A", False)
        == f"{int(expected, 2):02x}"
    )
