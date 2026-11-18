"""DEMO TỔNG HỢP CHẠY TRỰC TIẾP.""" # File kiểm tra và trình diễn hoạt động của hai thuật toán mã hóa A5/1 và TinyA5/1.
from pathlib import Path
from tempfile import TemporaryDirectory
from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51Cipher

def encrypt_decrypt_bytes(data: bytes, key_64bit: int, frame_22bit: int) -> bytes: # Mã hóa hoặc giải mã một chuỗi byte bằng A5/1.
    if not isinstance(key_64bit, int) or not 0 <= key_64bit < (1 << 64): # Kiểm tra khóa có phải số nguyên không và có nằm trong phạm vi 64 bit không. Nếu không hợp lệ, chương trình thông báo lỗi ValueError.
        raise ValueError("Key must be a 64-bit unsigned integer")
    key_bits = [(key_64bit >> i) & 1 for i in range(64)]
    return A51Cipher(key_bits, frame_22bit).process_bytes(data) # Tạo bộ mã hóa A5/1, sinh dòng khóa và xử lý dữ liệu bằng phép XOR.

def encrypt_file(input_path: str, output_path: str, key: int, frame: int): # Mã hóa hoặc giải mã dữ liệu của một file
    open("xb") 
    result = encrypt_decrypt_bytes(Path(input_path).read_bytes(), key, frame)
    with Path(output_path).open("xb") as output:
        output.write(result)
    print(f"Processed {input_path} -> {output_path} ({len(result)} bytes)")

def run_tests(): # Kiểm tra tính đúng đắn của thuật toán
    assert # so sánh đầu ra dự kiến; tạo lại bộ mã hóa khi giải mã để reset S. Không thay thế bộ pytest vốn có nhiều ca dữ liệu sai và vector chuẩn.
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


def main(): # Kiểm tra toàn bộ quá trình mã hóa và giải mã file.
    # Câu có dấu lặp 100 lần, encode UTF-8 làm số byte khác số ký tự. TemporaryDirectory sinh thư mục riêng, tự dọn cả bản rõ, bản mã và bản khôi phục khi thoát with. So sánh read_bytes xác nhận chính xác mọi byte.
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
        
if __name__ == "__main__":
    main()
