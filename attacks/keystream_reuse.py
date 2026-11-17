"""DEMO TÁI SỬ DỤNG DÒNG KHÓA — chạy: py -m attacks.keystream_reuse.

Hai đối tượng Tiny được tạo mới bằng cùng khóa nên sinh cùng dòng S.
Với C1 = P1 XOR S và C2 = P2 XOR S, ta có C1 XOR C2 = P1 XOR P2.
Nếu biết một bản rõ, có thể suy ra bản rõ kia trong phần dòng khóa trùng.
Không biết bản rõ nào thì quan hệ XOR chưa tự động tiết lộ cả hai thông điệp.
Đây là demo lỗi sử dụng dòng khóa, không phải thuật toán phá khóa A5/1.
zip chỉ ghép đến độ dài ngắn hơn nếu hai thông điệp khác kích thước.
"""

from src.tiny_a51 import TinyA51


def demo_reuse(plain1: bytes, plain2: bytes, key: int):
    """Trả (C1, C2, C1_XOR_C2) từ hai bản rõ và cùng khóa Tiny số 32 bit.

    Tạo t1/t2 RIÊNG BIỆT cùng khóa làm dòng khóa bắt đầu trùng nhau. Nếu chỉ
    dùng một đối tượng liên tục, thông điệp sau dùng đoạn S tiếp theo và không
    còn là tình huống dùng lại đoạn đầu như demo này. zip giới hạn theo độ dài
    ngắn hơn. Hàm không tự biết hay khôi phục khóa bí mật.
    """
    t1 = TinyA51(key)
    c1 = t1.encrypt(plain1)
    # Cố tình khởi tạo lại cùng khóa để S thứ hai trùng S thứ nhất.
    t2 = TinyA51(key)
    c2 = t2.encrypt(plain2)
    # XOR hai bản mã triệt tiêu S ở các vị trí bị tái sử dụng.
    xored = bytes(a ^ b for a, b in zip(c1, c2))
    return c1, c2, xored


# Khối dưới chỉ chạy khi thực thi file/module trực tiếp, không chạy khi import.
if __name__ == "__main__":
    p1 = b"Hello, this is message A.".ljust(64, b" ")
    p2 = b"Attack at dawn! This is message B.".ljust(64, b" ")
    c1, c2, x = demo_reuse(p1, p2, key=0x12345)
    print("Cipher1:", c1.hex())
    print("Cipher2:", c2.hex())
    print("XOR (should equal p1^p2):", x.hex())
    expected = bytes(a ^ b for a, b in zip(p1, p2))
    print("p1^p2:", expected.hex())
    assert x == expected
