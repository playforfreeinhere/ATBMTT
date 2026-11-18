"""KIỂM THỬ CHUỖI BIT VÀ LỊCH SỬ."""
import pytest
from ui.binary import process_binary, format_trace
KEY = "10010101001110100110000"

def test_hand_calculation_and_trace():
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
    with pytest.raises(ValueError):
        process_binary("TinyA5/1", key, "", data)

def test_full_binary_rejects_bad_frame():
    with pytest.raises(ValueError):
        process_binary("A5/1", "0" * 64, "0" * 21, "0")
