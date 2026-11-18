"""GIAO DIỆN DÒNG LỆNH MÃ HÓA/GIẢI MÃ FILE BẰNG TINY."""

import argparse
from pathlib import Path
from src.tiny_a51 import TinyA51

def parse_key(value: str) -> int:
    value = value.strip()
    try:
        key = int(value, 16 if value.lower().startswith("0x") else 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Key must be decimal or hexadecimal") from exc
    if not 0 <= key < (1 << 32):
        raise argparse.ArgumentTypeError("Key must be a 32-bit unsigned integer")
    return key

def encrypt_file(in_path: str, out_path: str, key: int):
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
    encrypt_file(in_path, out_path, key)

def main():
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


if __name__ == "__main__":
    main()
