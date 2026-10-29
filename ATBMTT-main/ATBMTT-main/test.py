"""Standalone demonstration; cipher implementations live exclusively in src/."""
from pathlib import Path
from tempfile import TemporaryDirectory

from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51Cipher


def encrypt_decrypt_bytes(data: bytes, key_64bit: int, frame_22bit: int) -> bytes:
    if not isinstance(key_64bit, int) or not 0 <= key_64bit < (1 << 64):
        raise ValueError('Key must be a 64-bit unsigned integer')
    key_bits = [(key_64bit >> i) & 1 for i in range(64)]
    return A51Cipher(key_bits, frame_22bit).process_bytes(data)


def encrypt_file(input_path: str, output_path: str, key: int, frame: int):
    result = encrypt_decrypt_bytes(Path(input_path).read_bytes(), key, frame)
    with Path(output_path).open('xb') as output:
        output.write(result)
    print(f'Processed {input_path} -> {output_path} ({len(result)} bytes)')


def run_tests():
    cipher = TinyA51Cipher([1, 0, 1, 1, 0, 0], [0, 1, 0, 1, 0, 1, 1, 0],
                           [1, 1, 0, 0, 1, 0, 1, 0, 1])
    stream, _ = cipher.generate_keystream(4)
    assert stream == [1, 0, 0, 1]
    print('PASS: TinyA5/1 teaching vector (6/8/9 bits)')
    plaintext = b'A5/1 Stream Cipher Implementation - FIT NEU 2026'
    key, frame = 0x123456789ABCDEF0, 0x123456
    ciphertext = encrypt_decrypt_bytes(plaintext, key, frame)
    assert ciphertext != plaintext
    assert encrypt_decrypt_bytes(ciphertext, key, frame) == plaintext
    print('PASS: A5/1 encryption/decryption')


def main():
    run_tests()
    with TemporaryDirectory(prefix='atbmtt-') as directory:
        source = Path(directory) / 'plain.txt'
        encrypted = Path(directory) / 'cipher.bin'
        decrypted = Path(directory) / 'decrypted.txt'
        source.write_text('Xin chào, bài tập A5/1!\n' * 100, encoding='utf-8')
        key, frame = 0xFEDCBA9876543210, 0x3FFFFF
        encrypt_file(str(source), str(encrypted), key, frame)
        encrypt_file(str(encrypted), str(decrypted), key, frame)
        assert source.read_bytes() == decrypted.read_bytes()
        print('PASS: File roundtrip')


if __name__ == '__main__':
    main()
