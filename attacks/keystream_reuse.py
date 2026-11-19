"""DEMO TÁI SỬ DỤNG DÒNG KHÓA."""
from src.tiny_a51 import TinyA51

def demo_reuse(plain1: bytes, plain2: bytes, key: int):
    t1 = TinyA51(key)
    c1 = t1.encrypt(plain1)
    # Cố tình khởi tạo lại cùng khóa để S thứ hai trùng S thứ nhất.
    t2 = TinyA51(key)
    c2 = t2.encrypt(plain2)
    # XOR hai bản mã triệt tiêu S ở các vị trí bị tái sử dụng.
    xored = bytes(a ^ b for a, b in zip(c1, c2))
    return c1, c2, xored
    
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
"""Chương trình minh họa lỗ hổng tái sử dụng dòng khóa trong TinyA5/1.
Đầu tiên, hai bản rõ được mã hóa bằng cùng một khóa và cùng trạng thái khởi tạo, dẫn đến việc sinh ra hai dòng khóa giống nhau
Sau đó, chương trình thực hiện XOR hai bản mã và chứng minh rằng kết quả bằng XOR của hai bản rõ, do dòng khóa đã bị triệt tiêu. Cuối cùng, lệnh assert kiểm tra tính chính xác của kết quả.
Qua đó cho thấy việc tái sử dụng dòng khóa làm suy giảm tính bảo mật của hệ mã dòng."""
