"""KHAI BÁO GÓI SRC VÀ CÁC LỚP ĐƯỢC XUẤT RA NGOÀI.

Dấu chấm trong .a51 và .tiny_a51 là import tương đối: lấy module trong src.
Nhờ các dòng import dưới đây có thể viết `from src import A51Cipher`.
A51Cipher: lõi A5/1 đầy đủ, nhận 64 bit khóa theo thứ tự nạp và số khung.
TinyA51Cipher: lõi Tiny, nhận trực tiếp trạng thái ba thanh ghi 6/8/9 bit.
TinyA51: lớp con chuyển khóa số 32 bit sang trạng thái Tiny cho CLI.
File không tạo đối tượng mã hóa, không mở cửa sổ và không tự chạy demo.
"""

from .a51 import A51Cipher
from .tiny_a51 import TinyA51Cipher, TinyA51
