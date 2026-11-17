"""XỬ LÝ DỮ LIỆU CHO GIAO DIỆN — không import Tkinter.

parse_unsigned: chuỗi thập phân/hex → số không dấu có giới hạn bit.
make_cipher: đọc thuật toán và khóa → tạo bộ sinh mới, trả hàm xử lý byte.
process_text: UTF-8 ↔ byte mã hóa ↔ hex.
process_file: đọc/ghi nhị phân theo khối, giữ bộ sinh xuyên suốt file.

Các hàm này không đọc ô nhập và không sửa widget; ui/gui.py truyền dữ liệu
vào rồi nhận kết quả hoặc bắt lỗi ValueError/OSError. Nhờ vậy có thể kiểm
thử thuật toán xử lý dữ liệu mà không cần mở cửa sổ.
Bytes là dữ liệu thực; hex chỉ là cách viết byte bằng các ký tự 0–9, a–f.
Mỗi lần mã hóa/giải mã gọi make_cipher mới để dòng khóa bắt đầu từ đầu.
"""

from pathlib import Path
from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51Cipher


def parse_unsigned(value: str, bits: int, label: str) -> int:
    """Chuyển value sang số không dấu tối đa bits bit, hoặc báo ValueError.

    strip bỏ khoảng trắng hai đầu; tiền tố 0x dùng cơ số 16, còn lại cơ số 10.
    label chỉ dùng đặt tên dữ liệu trong thông báo lỗi. raise ... from exc
    giữ nguyên nguyên nhân lỗi ban đầu để hỗ trợ chẩn đoán.
    """
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
    """Tạo bộ sinh mới và trả phương thức process_bytes đã gắn với đối tượng.

    Tiny: khóa phải là 23 ký tự 0/1, chuyển thành int rồi chia 6/8/9 bit.
    A5/1: khóa là chuỗi số 64 bit; to_bytes(8, "big") đặt byte cao trước,
    nhưng mỗi byte được tách bit thấp trước khi đưa vào lõi A51Cipher.
    Ví dụ 0x12 thành byte 00010010; thứ tự nạp byte này là 0,1,0,0,1,0,0,0.
    Hàm trả cipher.process_bytes, không gọi nó ngay: bên nhận dùng operation(data).
    Phương thức này giữ đối tượng cipher nên trạng thái tồn tại giữa các khối.
    frame bị bỏ qua trong nhánh Tiny; thuật toán khác hai tên hợp lệ bị từ chối.
    """
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
    """Mã hóa văn bản thành hex hoặc giải mã hex thành văn bản UTF-8.

    decrypt=False: encode UTF-8 → XOR byte → hex. True: fromhex → XOR → decode.
    Tạo operation mới mỗi lần để dòng khóa bắt đầu lại. bytes.fromhex cho phép
    khoảng trắng hợp lệ trong chuỗi hex; độ dài chữ phải tạo được đủ byte.
    Lỗi hex và lỗi UTF-8 được đổi thành thông báo tiếng Việt. Giải mã sai khóa
    không nhất thiết báo lỗi: byte sai đôi khi vẫn là UTF-8 hợp lệ.
    """
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
    """Đọc source, ghi target và trả tổng byte đã xử lý.

    resolve và samefile ngăn đầu vào/đầu ra trỏ cùng file. rb đọc nhị phân;
    xb chỉ tạo file mới, không ghi đè file có sẵn. with tự đóng file khi thoát.
    Toán tử := vừa gán chunk vừa kiểm tra nó có rỗng không; hết file thì dừng.
    Khối 65.536 byte chỉ giới hạn phần đọc/ghi, không làm đổi kết quả mã hóa.
    operation được tạo một lần ngoài while để dòng khóa liên tục qua các khối.
    Lỗi giữa chừng có thể để lại file đầu ra chưa hoàn chỉnh, không tự xóa file đó.
    """
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
            # Giữ operation ngoài vòng lặp: không lặp lại đoạn đầu dòng S ở mỗi khối.
            while chunk := input_file.read(65536):
                output_file.write(operation(chunk))
                total += len(chunk)
    return total
