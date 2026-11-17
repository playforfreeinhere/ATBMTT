"""GIAO DIỆN DÒNG LỆNH MÃ HÓA/GIẢI MÃ FILE BẰNG TINY.

Chạy từ gốc: py -m ui.cli encrypt input.txt output.bin 0x1A2B3C4D
hoặc:        py -m ui.cli decrypt output.bin restored.txt 0x1A2B3C4D
-m bảo Python tìm ui.cli như module, để import src hoạt động đúng.
Bốn tham số: command, đường dẫn đầu vào, đầu ra mới, khóa số 32 bit.
CLI dùng lớp TinyA51 chuyển khóa số sang trạng thái 23 bit; không nhận
trực tiếp định dạng chuỗi bit 23 ký tự của GUI. Không trộn hai cách nhập.
Hàm mã hóa/giải mã dùng chung XOR; chương trình từ chối ghi đè file.
CLI đọc toàn bộ file vào bộ nhớ; bản GUI đọc file theo khối 65.536 byte.
"""

import argparse
from pathlib import Path

from src.tiny_a51 import TinyA51


def parse_key(value: str) -> int:
    """Đọc khóa thập phân/hex và kiểm tra khoảng 0 đến 2**32 - 1.

    argparse gọi hàm này qua type=parse_key. ArgumentTypeError làm argparse
    in lỗi nhập liệu, thay vì tiếp tục chạy với khóa không hợp lệ.
    """
    value = value.strip()
    try:
        key = int(value, 16 if value.lower().startswith("0x") else 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Key must be decimal or hexadecimal") from exc
    if not 0 <= key < (1 << 32):
        raise argparse.ArgumentTypeError("Key must be a 32-bit unsigned integer")
    return key


def encrypt_file(in_path: str, out_path: str, key: int):
    """Đọc file nhị phân, tạo Tiny mới với key và ghi bản mã vào file mới.

    resolve/samefile ngăn dùng cùng file. read_bytes đọc toàn bộ dữ liệu;
    open("xb") bảo vệ file đích đã có. Mỗi lần gọi tạo lại bộ sinh từ đầu.
    len(data) đếm byte, không phải số ký tự trong văn bản Unicode.
    """
    source, destination = Path(in_path), Path(out_path)
    if source.resolve() == destination.resolve() or (
        destination.exists() and source.samefile(destination)
    ):
        raise ValueError("Input and output must be different files")
    data = source.read_bytes()
    result = TinyA51(key).encrypt(data)
    # Chỉ tạo file mới để không ghi đè dữ liệu đã tồn tại.
    with destination.open("xb") as output:
        output.write(result)
    print(f"Processed {in_path} -> {out_path} ({len(data)} bytes)")


def decrypt_file(in_path: str, out_path: str, key: int):
    """Giải mã bằng cùng phép XOR và cùng khóa, dùng lại encrypt_file.

    Tên hàm khác nhau để người đọc CLI hiểu hướng thao tác; nội dung xử lý
    giống nhau do (P XOR S) XOR S = P. Hàm không đổi đuôi file thay người dùng.
    """
    encrypt_file(in_path, out_path, key)


def main():
    """Đọc bốn tham số dòng lệnh, chọn hàm rồi báo lỗi bằng mã thoát 1.

    choices chỉ nhận encrypt/decrypt. args là các giá trị đã parse; khóa
    đã đi qua parse_key. Bắt OSError/ValueError để không in traceback dài
    cho lỗi file hoặc đầu vào thường gặp; thành công kết thúc bình thường.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("encrypt", "decrypt"))
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("key", type=parse_key)
    args = parser.parse_args()
    try:
        operation = encrypt_file if args.command == "encrypt" else decrypt_file
        operation(args.input, args.output, args.key)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")


# Khối dưới chỉ chạy khi thực thi file/module trực tiếp, không chạy khi import.
if __name__ == "__main__":
    main()
