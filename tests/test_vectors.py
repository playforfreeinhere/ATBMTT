"""KIỂM THỬ LÕI, VECTOR THAM CHIẾU, CLI VÀ DEMO DÙNG LẠI DÒNG KHÓA.

Chạy: py -m pytest tests/test_vectors.py -v.
Vector A5/1 của Briceno/Goldberg/Wagner kiểm tra hai đoạn liên tiếp 114 bit.
Tiny kiểm tra ví dụ độc lập từ slide. Các ca còn lại kiểm tra tính lặp lại,
khôi phục dữ liệu, khóa sai, xử lý theo khối và CLI thực sự qua subprocess.

pytest tự truyền tmp_path vào ca cần file tạm. sys.executable bảo đảm
chương trình con dùng đúng Python đang chạy kiểm thử. returncode=0 là thành
công; stderr chứa thông báo lỗi. Một ca được parametrize tạo nhiều lượt chạy.
Vòng mã hóa/giải mã đơn thuần chưa đủ chứng minh đúng thuật toán, vì hai
chiều có thể cùng sai; vì vậy cần kết hợp vector độc lập và kiểm tra log.
"""

import pytest

from src.tiny_a51 import TinyA51


def test_keystream_repeatability():
    """Hai đối tượng Tiny mới cùng khóa phải sinh cùng 16 byte S.

    Kiểm tra tính xác định của bộ sinh, không phải chứng minh S ngẫu nhiên an toàn.
    """
    key = 0x1A2B3C
    t1 = TinyA51(key)
    t2 = TinyA51(key)
    a = t1.keystream_bytes(16)
    b = t2.keystream_bytes(16)
    assert a == b


def test_encrypt_decrypt_roundtrip():
    """Mã hóa rồi tạo bộ Tiny mới cùng khóa để giải mã.

    ljust(32,b"\x00") thêm byte 0 ở cuối cho đủ 32 byte. Phải so sánh với
    đầy đủ dữ liệu đã đệm, không bỏ byte 0 hoặc giải mã bằng trạng thái đã chạy.
    """
    key = 0xDEADBEEF
    t = TinyA51(key)
    data = b"Test data for encryption".ljust(32, b"\x00")
    c = t.encrypt(data)
    # Tạo bộ sinh mới cùng khóa để dòng S bắt đầu lại từ đầu.
    t2 = TinyA51(key)
    p = t2.decrypt(c)
    assert p == data


from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51Cipher
from attacks.keystream_reuse import demo_reuse


def test_a51_published_vector():
    # Vector tham chiếu A5/1 của Marc Briceno / Ian Goldberg / David Wagner:
    # Khóa theo byte 12 23 45 67 89 AB CD EF, frame 0x134;
    # Giữ thứ tự byte, nạp bit thấp trước trong từng byte.
    """Đối chiếu hai đoạn 114 bit LIÊN TIẾP bằng khóa/frame tham chiếu.

    Nạp từng byte khóa từ bit thấp lên cao; giữ cùng đối tượng qua hai đoạn.
    Mỗi đoạn thêm 6 bit 0 để đóng gói 114 thành 120 bit = 15 byte. Phép dịch
    (7-k) đặt bit vào vị trí cao trước; phần đệm không phải đầu ra thuật toán.
    """
    key = bytes.fromhex("1223456789abcdef")
    cipher = A51Cipher([(byte >> i) & 1 for byte in key for i in range(8)], 0x134)
    for expected in (
        "534eaa582fe8151ab6e1855a728c00",
        "24fd35a35d5fb6526d32f906df1ac0",
    ):
        bits = [cipher.get_keystream_bit() for _ in range(114)] + [0] * 6
        packed = bytes(
            sum(bits[j + k] << (7 - k) for k in range(8)) for j in range(0, 120, 8)
        )
        assert packed.hex() == expected


def test_tiny_hand_vector():
    # Biến thể theo slide: lấy đầu ra sau khi dịch thanh ghi.
    """Kiểm tra S=100 và trạng thái bước đầu theo ví dụ Tiny trong slide.

    Kiểm tra clock, thanh ghi dịch và R1 sau dịch để phát hiện lấy S sai thời điểm.
    """
    cipher = TinyA51Cipher(
        [1, 0, 0, 1, 0, 1], [0, 1, 0, 0, 1, 1, 1, 0], [1, 0, 0, 1, 1, 0, 0, 0, 0]
    )
    stream, logs = cipher.generate_keystream(3)
    assert stream == [1, 0, 0]
    assert logs[0]["clock_bits"] == (0, 0, 1)
    assert logs[0]["clocked"] == (True, True, False)
    assert logs[0]["r1"] == [1, 1, 0, 0, 1, 0]


def test_reuse_attack():
    """Xác nhận demo dùng lại S làm C1 XOR C2 đúng bằng P1 XOR P2.

    Bản mã cần khác bản rõ trong ví dụ đã chọn; zip so sánh phần chung
    của hai thông điệp có độ dài khác nhau.
    """
    p1, p2 = b"Hello world!", b"Attack at dawn!"
    c1, c2, result = demo_reuse(p1, p2, 0x12345)
    assert c1 != p1 and c2 != p2
    assert result == bytes(a ^ b for a, b in zip(p1, p2))


@pytest.mark.parametrize("key", [-1, 1 << 32, "invalid"])
def test_invalid_tiny_key(key):
    """Khóa Tiny số âm, lớn hơn 32 bit hoặc không phải số phải gây ValueError."""
    with pytest.raises(ValueError):
        TinyA51(key)


@pytest.mark.parametrize(
    "key,frame",
    [
        ([0] * 63, 0),
        ([2] * 64, 0),
        ([0] * 64, -1),
        ([0] * 64, 1 << 22),
        (None, 0),
        ([0] * 64, None),
    ],
)
def test_invalid_a51_input(key, frame):
    """Kiểm tra khóa thiếu bit, bit ngoài 0/1, frame âm/vượt giới hạn và thiếu tham số.

    Các bộ parametrize phải bị từ chối; không được khởi tạo trạng thái mơ hồ.
    """
    with pytest.raises(ValueError):
        A51Cipher(key, frame)


def test_invalid_tiny_registers():
    """R2 chỉ có 7 bit thay vì 8 phải bị từ chối ngay trong hàm khởi tạo."""
    with pytest.raises(ValueError):
        TinyA51Cipher([0] * 6, [0] * 7, [0] * 9)


@pytest.mark.parametrize("data", [b"", bytes(range(256)), "Xin chào Việt Nam".encode()])
def test_cli_roundtrip(tmp_path, data):
    """Chạy CLI thật qua subprocess cho file rỗng, đủ 256 giá trị byte và tiếng Việt.

    tmp_path chứa ba đường dẫn; source được ghi trước. Mỗi lệnh cần mã thoát 0,
    và file sau hai chiều phải giống từng byte. capture_output giữ stdout/stderr
    để pytest hiển thị nguyên nhân nếu lệnh thất bại.
    """
    import subprocess
    import sys

    source, encrypted, decrypted = (
        tmp_path / name for name in ("plain", "cipher", "back")
    )
    source.write_bytes(data)
    for command, first, second in [
        ("encrypt", source, encrypted),
        ("decrypt", encrypted, decrypted),
    ]:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ui.cli",
                command,
                str(first),
                str(second),
                "0x1A2B3C4D",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
    assert decrypted.read_bytes() == data


@pytest.mark.parametrize(
    "case", ["bad-key", "missing-input", "existing-output", "same-file"]
)
def test_cli_errors_preserve_files(tmp_path, case):
    """Thử khóa sai, đầu vào thiếu, đích đã có và cùng đầu vào/đầu ra.

    Chương trình phải thoát khác 0, thông báo không có Traceback và giữ nguyên
    nội dung hai file đã tạo. Đây là kiểm tra bảo vệ dữ liệu khi thao tác lỗi.
    """
    import subprocess
    import sys

    source, output = tmp_path / "input", tmp_path / "output"
    source.write_bytes(b"original input")
    output.write_bytes(b"original output")
    first = tmp_path / "missing" if case == "missing-input" else source
    second = source if case == "same-file" else output
    key = "invalid" if case == "bad-key" else "123"
    result = subprocess.run(
        [sys.executable, "-m", "ui.cli", "encrypt", str(first), str(second), key],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Traceback" not in result.stderr
    assert source.read_bytes() == b"original input"
    assert output.read_bytes() == b"original output"


def test_tiny_chunked_processing():
    """Mã hóa hai phần với một đối tượng phải bằng mã hóa toàn bộ với bộ mới.

    Phát hiện reset dòng khóa hoặc bỏ bit khi đổi khối. Không tạo bộ mới
    giữa data[:7] và data[7:] vì chúng thuộc cùng một thông điệp.
    """
    data = bytes(range(128))
    cipher = TinyA51(0xDEADBEEF)
    assert cipher.encrypt(data[:7]) + cipher.encrypt(data[7:]) == TinyA51(
        0xDEADBEEF
    ).encrypt(data)
