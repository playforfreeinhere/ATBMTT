"""Xử lý khóa, văn bản và file; độc lập với giao diện Tkinter."""

from pathlib import Path
from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51Cipher


def parse_unsigned(value: str, bits: int, label: str) -> int:
    try:
        text = value.strip()
        number = int(text, 16 if text.lower().startswith("0x") else 10)
    except ValueError as exc:
        raise ValueError(
            f"{label} phải là số thập phân hoặc hex bắt đầu bằng 0x."
        ) from exc
    if not 0 <= number < (1 << bits):
        raise ValueError(f"{label} phải nằm trong khoảng 0 đến {hex((1 << bits) - 1)}.")
    return number


def make_cipher(algorithm: str, key: str, frame: str):
    if algorithm == "TinyA5/1":
        bits = key.strip()
        if len(bits) != 23 or any(bit not in "01" for bit in bits):
            raise ValueError("Khóa TinyA5/1 phải có đúng 23 bit 0/1.")
        state = [int(bit) for bit in bits]
        cipher = TinyA51Cipher(state[:6], state[6:14], state[14:])
        return cipher.process_bytes
    if algorithm != "A5/1":
        raise ValueError("Thuật toán không hợp lệ.")
    number = parse_unsigned(key, 64, "Khóa A5/1")
    # Khóa hiển thị theo byte big-endian; nạp bit thấp trước trong từng byte.
    key_bits = [
        (byte >> bit) & 1 for byte in number.to_bytes(8, "big") for bit in range(8)
    ]
    cipher = A51Cipher(key_bits, parse_unsigned(frame, 22, "Số khung"))
    return cipher.process_bytes


def process_text(algorithm: str, key: str, frame: str, text: str, decrypt: bool) -> str:
    operation = make_cipher(algorithm, key, frame)
    if decrypt:
        try:
            data = bytes.fromhex(text)
        except ValueError as exc:
            raise ValueError("Bản mã phải là chuỗi hex hợp lệ, ví dụ: 0a12ff.") from exc
        try:
            return operation(data).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "Không đọc được UTF-8. Kiểm tra khóa, thuật toán, số khung và bản mã; "
                "với dữ liệu nhị phân hãy dùng mục File."
            ) from exc
    return operation(text.encode("utf-8")).hex()


def process_file(algorithm: str, key: str, frame: str, source: str, target: str) -> int:
    operation = make_cipher(algorithm, key, frame)
    first, second = Path(source), Path(target)
    if first.resolve() == second.resolve() or (
        second.exists() and first.samefile(second)
    ):
        raise ValueError("File đầu vào và đầu ra phải khác nhau.")
    # Chế độ xb không cho ghi đè, kể cả khi file vừa được tạo sau hộp thoại.
    with first.open("rb") as input_file:
        with second.open("xb") as output_file:
            total = 0
            while chunk := input_file.read(65536):
                output_file.write(operation(chunk))
                total += len(chunk)
    return total
