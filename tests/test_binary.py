"""KIỂM THỬ CHUỖI BIT VÀ LỊCH SỬ — py -m pytest tests/test_binary.py -v.

Dùng ví dụ Tiny độc lập trong slide và vector tham chiếu A5/1.
Không chỉ kiểm tra giải mã khôi phục: còn kiểm tra S, clock, majority,
quyết định dịch và trạng thái trước/sau để phát hiện lỗi từng nhịp.
KEY là khóa Tiny mẫu 23 bit. Các hàm test_* do pytest tự tìm và chạy.
@pytest.mark.parametrize chạy cùng hàm với nhiều bộ dữ liệu; mỗi bộ là
một ca kiểm thử. pytest.raises kiểm tra lỗi đúng loại được phát sinh.
"""

import pytest

from ui.binary import process_binary, format_trace

KEY = "10010101001110100110000"


def test_hand_calculation_and_trace():
    # Ví dụ tính tay độc lập ở trang 49–50 của slide: 111 XOR 100 = 011.
    """Đối chiếu ví dụ Tiny trong slide: 111 XOR 100 = 011.

    Kiểm tra cả trạng thái ban đầu, clock 0/0/1, majority 0, dịch R1/R2 và
    trạng thái R1 sau bước đầu; giải mã phải trả 111. Không chỉ kiểm tra roundtrip.
    """
    result, stream, rows = process_binary("TinyA5/1", KEY, "", "111")
    assert result == "011"
    assert stream == "100"
    assert rows[0]["before"] == [
        [1, 0, 0, 1, 0, 1],
        [0, 1, 0, 0, 1, 1, 1, 0],
        [1, 0, 0, 1, 1, 0, 0, 0, 0],
    ]
    assert rows[0]["clock_bits"] == (0, 0, 1)
    assert rows[0]["majority"] == 0
    assert rows[0]["clocked"] == (True, True, False)
    assert rows[0]["after"][0] == [1, 1, 0, 0, 1, 0]
    assert process_binary("TinyA5/1", KEY, "", result)[0] == "111"
    assert "Bước 1" in format_trace(rows)


def test_full_a51_vector_and_decrypt():
    """Cho 114 bit bản rõ 0 để bản mã bằng chính dòng khóa tham chiếu A5/1.

    Vector hex chiếm 120 bit, trong đó chỉ 114 bit có nghĩa; zfill khôi phục
    số 0 đầu và [:114] bỏ phần đệm. Kiểm tra thêm độ dài thanh ghi và giải mã.
    """
    key = format(0x1223456789ABCDEF, "064b")
    frame = format(0x134, "022b")
    result, stream, rows = process_binary("A5/1", key, frame, "0" * 114)
    expected = bin(int("534eaa582fe8151ab6e1855a728c00", 16))[2:].zfill(120)[:114]
    assert result == stream == expected
    assert process_binary("A5/1", key, frame, result)[0] == "0" * 114
    assert [len(value) for value in rows[0]["before"]] == [19, 22, 23]


@pytest.mark.parametrize(
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
def test_binary_input_errors(key, data):
    """Mỗi cặp key/data trong parametrize phải làm phát sinh ValueError.

    Bao gồm khóa ngắn/dài, ký tự ngoài 0/1, rỗng, khoảng trắng giữa và vượt
    giới hạn 4096 bit. Không ghi nhận mọi lỗi là đúng: phải đúng loại ValueError.
    """
    with pytest.raises(ValueError):
        process_binary("TinyA5/1", key, "", data)


def test_full_binary_rejects_bad_frame():
    """Frame nhị phân 21 bit phải bị từ chối, vì A5/1 yêu cầu đúng 22 bit."""
    with pytest.raises(ValueError):
        process_binary("A5/1", "0" * 64, "0" * 21, "0")
