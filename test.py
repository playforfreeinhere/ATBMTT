"""DEMO TỔNG HỢP CHẠY TRỰC TIẾP — lệnh: py test.py.

Không phải file chính mở GUI và không cài đặt lại lõi thuật toán.
run_tests() kiểm tra ví dụ Tiny và vòng mã hóa/giải mã byte của A5/1.
main() tạo tệp UTF-8 tạm, mã hóa, giải mã và so sánh toàn bộ byte.
TemporaryDirectory tự dọn dữ liệu demo khi thoát khối with.
assert kiểm tra điều kiện; nếu sai, Python ném AssertionError và dừng.
Bộ pytest chi tiết nằm trong tests/; demo này giúp trình bày trên lớp.
Lưu ý: hàm chuyển khóa số trong file demo nạp bit thấp của TOÀN SỐ trước,
khác cách GUI hiển thị 8 byte big-endian rồi nạp bit thấp trong từng byte.
Vì vậy cùng số khóa không đảm bảo bản mã demo này giống bản GUI.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51Cipher


def encrypt_decrypt_bytes(data: bytes, key_64bit: int, frame_22bit: int) -> bytes:
    """Tạo bộ A5/1 mới và XOR dữ liệu bytes, dùng được cho hai chiều.

    Kiểm tra khóa 64 bit; frame do A51Cipher kiểm tra. Ở riêng demo này,
    (key_64bit >> i) & 1 tách toàn số từ bit thấp lên, không dùng quy ước
    8 byte big-endian của GUI. Hai chiều đều dùng cùng quy ước nên khôi phục đúng.
    """
    if not isinstance(key_64bit, int) or not 0 <= key_64bit < (1 << 64):
        raise ValueError("Key must be a 64-bit unsigned integer")
    key_bits = [(key_64bit >> i) & 1 for i in range(64)]
    return A51Cipher(key_bits, frame_22bit).process_bytes(data)


def encrypt_file(input_path: str, output_path: str, key: int, frame: int):
    """Đọc toàn bộ file, gọi bộ xử lý byte và ghi vào đường dẫn mới.

    open("xb") không ghi đè file đã có. Đây là helper demo file nhỏ, không
    phải hàm đọc theo khối đang được giao diện sử dụng.
    """
    result = encrypt_decrypt_bytes(Path(input_path).read_bytes(), key, frame)
    with Path(output_path).open("xb") as output:
        output.write(result)
    print(f"Processed {input_path} -> {output_path} ({len(result)} bytes)")


def run_tests():
    """Chạy hai kiểm tra nhanh: ví dụ Tiny S=100 và A5/1 khôi phục văn bản.

    assert so sánh đầu ra dự kiến; tạo lại bộ mã hóa khi giải mã để reset S.
    Không thay thế bộ pytest vốn có nhiều ca dữ liệu sai và vector chuẩn.
    """
    cipher = TinyA51Cipher(
        [1, 0, 0, 1, 0, 1], [0, 1, 0, 0, 1, 1, 1, 0], [1, 0, 0, 1, 1, 0, 0, 0, 0]
    )
    stream, _ = cipher.generate_keystream(3)
    assert stream == [1, 0, 0]
    print("PASS: TinyA5/1 teaching vector (6/8/9 bits)")
    plaintext = b"A5/1 Stream Cipher Implementation - FIT NEU 2026"
    key, frame = 0x123456789ABCDEF0, 0x123456
    ciphertext = encrypt_decrypt_bytes(plaintext, key, frame)
    assert ciphertext != plaintext
    assert encrypt_decrypt_bytes(ciphertext, key, frame) == plaintext
    print("PASS: A5/1 encryption/decryption")


def main():
    """Chạy kiểm tra nhanh rồi demo vòng mã hóa/giải mã tệp UTF-8 2.800 byte.

    Câu có dấu lặp 100 lần, encode UTF-8 làm số byte khác số ký tự.
    TemporaryDirectory sinh thư mục riêng, tự dọn cả bản rõ, bản mã và bản khôi
    phục khi thoát with. So sánh read_bytes xác nhận chính xác mọi byte.
    """
    run_tests()
    with TemporaryDirectory(prefix="atbmtt-") as directory:
        source = Path(directory) / "plain.txt"
        encrypted = Path(directory) / "cipher.bin"
        decrypted = Path(directory) / "decrypted.txt"
        source.write_text("Xin chào, bài tập A5/1!\n" * 100, encoding="utf-8")
        key, frame = 0xFEDCBA9876543210, 0x3FFFFF
        encrypt_file(str(source), str(encrypted), key, frame)
        encrypt_file(str(encrypted), str(decrypted), key, frame)
        assert source.read_bytes() == decrypted.read_bytes()
        print("PASS: File roundtrip")


# Khối dưới chỉ chạy khi thực thi file/module trực tiếp, không chạy khi import.
if __name__ == "__main__":
    main()
