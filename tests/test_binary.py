"""KIỂM THỬ CHUỖI BIT VÀ LỊCH SỬ."""
import pytest
from ui.binary import process_binary, format_trace
KEY = "10010101001110100110000"

def test_hand_calculation_and_trace(): # Kiểm thử TinyA5/1
    result, stream, rows = process_binary("TinyA5/1", KEY, "", "111")
    assert result == "011" # Kiểm tra bản mã và dòng khóa
    assert stream == "100"
    assert rows[0]["before"] == [ # Kiểm tra trạng thái ban đầu
        [1, 0, 0, 1, 0, 1],
        [0, 1, 0, 0, 1, 1, 1, 0],
        [1, 0, 0, 1, 1, 0, 0, 0, 0],
    ]
    assert rows[0]["clock_bits"] == (0, 0, 1) # Kiểm tra Majority
    assert rows[0]["majority"] == 0
    assert rows[0]["clocked"] == (True, True, False)
    assert rows[0]["after"][0] == [1, 1, 0, 0, 1, 0] # Kiểm tra trạng thái sau khi dịch
    assert process_binary("TinyA5/1", KEY, "", result)[0] == "111" # Kiểm tra giải mã
    assert "Bước 1" in format_trace(rows) # Kiểm tra lịch sử hiển thị

def test_full_a51_vector_and_decrypt(): # Kiểm thử A5/1 đầy đủ
    key = format(0x1223456789ABCDEF, "064b")
    frame = format(0x134, "022b")
    result, stream, rows = process_binary("A5/1", key, frame, "0" * 114) # Thực hiện mã hóa
    expected = bin(int("534eaa582fe8151ab6e1855a728c00", 16))[2:].zfill(120)[:114] # Kiểm tra vector tham chiếu
    assert result == stream == expected # Kiểm tra bản mã bản rõ và vector tham chiếu
    assert process_binary("A5/1", key, frame, result)[0] == "0" * 114 #  Kiểm tra giải mã và độ dài thanh ghi
    assert [len(value) for value in rows[0]["before"]] == [19, 22, 23]

@pytest.mark.parametrize( # Kiểm tra đầu vào có sai không?
    "key,data",
    [
        (KEY[:-1], "1"),
        (KEY + "0", "1"),
        (KEY, "abc"),
        (KEY, ""),
        (KEY, "1 0"),
        (KEY, "0" * 4097),
    ],
)
def test_binary_input_errors(key, data): # Kiểm tra chương trình báo lỗi (Đảm bảo chương trình từ chối dữ liệu không hợp lệ thay vì tiếp tục xử lý.)
    with pytest.raises(ValueError):
        process_binary("TinyA5/1", key, "", data)

def test_full_binary_rejects_bad_frame(): # Kiểm tra A5/1 có phát hiện khung có độ dài sai không.
    with pytest.raises(ValueError):
        process_binary("A5/1", "0" * 64, "0" * 21, "0")
