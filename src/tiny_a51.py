"""LÕI TINYA5/1 THEO SLIDE — thanh ghi 6/8/9 bit, khóa trực tiếp 23 bit.

Clock r1[1], r2[3], r3[3]. Tap phản hồi: R1 = 2/4/5,
R2 = 6/7, R3 = 2/7/8. Index 0 là đầu nạp feedback.
Mỗi nhịp: đọc ba clock cũ → tính majority → dịch thanh ghi phù hợp
→ XOR ba bit cuối của trạng thái MỚI để lấy S. Không lấy S trước dịch.
step_verbose() trả cả S và lịch sử phục vụ tab Nhị phân/Tính tay.
process_bytes() dùng cùng lõi để mã hóa file/văn bản bằng XOR.

Hai cách nhập khóa không giống nhau:
- GUI: TinyA51Cipher nhận trực tiếp ba phần của chuỗi khóa 23 bit.
- CLI: TinyA51 nhận số 32 bit, XOR-fold thành trạng thái 23 bit.
Đó là phép chuyển định dạng minh họa, không phải cách dẫn xuất khóa an toàn.
Dòng khóa có thể tái tạo nếu thiết lập và vị trí trạng thái giống nhau.
"""


class TinyA51Cipher:
    """Bộ sinh Tiny từ ba danh sách bit và các phép xử lý dùng chung.

    Không nạp frame hay chạy 100 nhịp khởi động như A5/1 đầy đủ.
    Đầu vào ba danh sách là trạng thái khởi đầu trực tiếp.
    """

    def __init__(self, r1_init: list[int], r2_init: list[int], r3_init: list[int]):
        """Kiểm tra độ dài 6/8/9 và mọi phần tử phải là 0 hoặc 1.

        list(...) sao chép dữ liệu: khi đối tượng dịch thanh ghi, không làm đổi
        danh sách ban đầu mà bên gọi đang giữ để tạo bộ giải mã.
        """
        for bits, size in ((r1_init, 6), (r2_init, 8), (r3_init, 9)):
            if len(bits) != size or any(bit not in (0, 1) for bit in bits):
                raise ValueError(f"Register must contain exactly {size} bits")
        self.r1, self.r2, self.r3 = list(r1_init), list(r2_init), list(r3_init)

    def _clock_r1(self):
        """Tính phản hồi từ tap 2,4,5; dịch R1 và trả bit phản hồi để ghi log.

        Phải lấy giá trị tap trước khi sửa thanh ghi. self.r1[:-1] bỏ bit cuối.
        """
        feedback = self.r1[2] ^ self.r1[4] ^ self.r1[5]
        self.r1 = [feedback] + self.r1[:-1]
        return feedback

    def _clock_r2(self):
        """Dịch R2 dùng XOR tap 6,7; trả feedback và giữ độ dài 8 bit."""
        feedback = self.r2[6] ^ self.r2[7]
        self.r2 = [feedback] + self.r2[:-1]
        return feedback

    def _clock_r3(self):
        """Dịch R3 dùng XOR tap 2,7,8; trả feedback và giữ độ dài 9 bit."""
        feedback = self.r3[2] ^ self.r3[7] ^ self.r3[8]
        self.r3 = [feedback] + self.r3[:-1]
        return feedback

    def step_verbose(self, step_number: int) -> tuple[int, dict]:
        """Thực hiện một nhịp Tiny, trả (bit_S, log).

        step_number chỉ là nhãn trong lịch sử, không phải dữ liệu hay khóa.
        clocks: ba clock cũ; majority: bit đa số; clocked: ba giá trị True/False.
        feedbacks chứa phản hồi của thanh ghi được dịch, None nếu giữ nguyên.
        Sau khi dịch, bit là XOR r1[5], r2[7], r3[8]. log lưu bản sao trạng thái
        mới bằng copy() để những bước tiếp theo không làm thay đổi lịch sử.
        Các khóa trong dictionary log phục vụ ui/binary.py; tên r1/r2/r3 là
        trạng thái sau dịch, còn trạng thái trước được bên gọi lưu riêng.
        """
        # Phải chụp đủ clock cũ trước khi gọi bất kỳ _clock_r* nào.
        clocks = (self.r1[1], self.r2[3], self.r3[3])
        majority = int(sum(clocks) >= 2)
        clocked = tuple(bit == majority for bit in clocks)
        feedbacks = (
            self._clock_r1() if clocked[0] else None,
            self._clock_r2() if clocked[1] else None,
            self._clock_r3() if clocked[2] else None,
        )
        # Công thức này dùng thanh ghi đã cập nhật; không XOR các bit clock.
        bit = self.r1[5] ^ self.r2[7] ^ self.r3[8]
        log = {
            "step": step_number,
            "clock_bits": clocks,
            "majority": majority,
            "clocked": clocked,
            "feedbacks": feedbacks,
            "r1": self.r1.copy(),
            "r2": self.r2.copy(),
            "r3": self.r3.copy(),
            "keystream_bit": bit,
        }
        return bit, log

    def get_keystream_bit(self) -> int:
        """Trả riêng S cho xử lý byte bằng cách bỏ phần log của step_verbose(0).

        Dấu _ nhận giá trị không dùng; 0 là nhãn bước, không reset bộ sinh.
        Hiện hàm vẫn tạo log nội bộ rồi bỏ đi, ưu tiên dùng chung một quy tắc.
        """
        bit, _ = self.step_verbose(0)
        return bit

    def generate_keystream(self, length: int) -> tuple[list[int], list[dict]]:
        """Sinh length bit liên tiếp, trả (danh_sách_S, danh_sách_log).

        length phải là số nguyên không âm; bằng 0 trả hai danh sách rỗng.
        range(1, length+1) đặt nhãn bước từ 1 đến length, mỗi lần gọi tiến trạng thái.
        """
        if not isinstance(length, int) or length < 0:
            raise ValueError("Length must be a nonnegative integer")
        stream, logs = [], []
        for step in range(1, length + 1):
            bit, log = self.step_verbose(step)
            stream.append(bit)
            logs.append(log)
        return stream, logs

    def process_bits(self, bit_stream: list[int]):
        """Nhận list bit, trả (kết_quả_XOR, dòng_S, lịch_sử).

        zip ghép từng bit dữ liệu với bit S tương ứng. Dấu ^ thực hiện XOR.
        Dùng được cho cả hai chiều; cùng dữ liệu đi qua cùng dòng S hai lần
        sẽ khôi phục ban đầu, vì S XOR S = 0.
        """
        if any(bit not in (0, 1) for bit in bit_stream):
            raise ValueError("Input must contain only bits")
        stream, logs = self.generate_keystream(len(bit_stream))
        output = [bit ^ mask for bit, mask in zip(bit_stream, stream)]
        return output, stream, logs

    def keystream_bytes(self, length: int) -> bytes:
        """Sinh length byte dòng khóa, mỗi byte ghép từ 8 bit liên tiếp.

        byte bắt đầu 0; (byte << 1) | bit đẩy các bit cũ lên và chèn bit mới
        vào vị trí thấp. Vòng ngoài đếm byte, vòng trong đếm 8 bit.
        Không reset trạng thái giữa các byte hoặc các lần gọi.
        """
        if not isinstance(length, int) or length < 0:
            raise ValueError("Length must be a nonnegative integer")
        output = bytearray()
        for _ in range(length):
            byte = 0
            for _ in range(8):
                byte = (byte << 1) | self.get_keystream_bit()
            output.append(byte)
        return bytes(output)

    def process_bytes(self, data: bytes) -> bytes:
        """Trả byte dữ liệu XOR với byte dòng khóa tương ứng.

        keystream_bytes(len(data)) sinh đúng số byte cần dùng; zip ghép theo vị trí.
        Độ dài kết quả bằng đầu vào. Đối tượng tiếp tục dòng khóa sau khi trả kết quả.
        """
        return bytes(
            byte ^ mask for byte, mask in zip(data, self.keystream_bytes(len(data)))
        )

    # Hai tên trỏ cùng hàm; để giải mã đúng vẫn phải tạo bộ mới cùng trạng thái.
    encrypt = process_bytes
    decrypt = process_bytes


class TinyA51(TinyA51Cipher):
    """Lớp con của TinyA51Cipher, giữ cách nhập khóa số 32 bit cho CLI.

    Kế thừa toàn bộ quy tắc dịch, sinh S, mã hóa và giải mã của lớp cha.
    Chỉ thay cách tạo trạng thái ban đầu; GUI không đi qua lớp chuyển này.
    """

    def __init__(self, key: int):
        """Chuyển số nguyên không dấu 32 bit thành trạng thái Tiny 23 bit.

        key & ((1 << 23) - 1) lấy 23 bit thấp; key >> 23 lấy phần bit cao.
        XOR hai phần tạo state 23 bit (XOR-fold), có thể có nhiều khóa ra cùng state.
        [(state >> i) & 1 ...] tách bit thấp trước, i chạy từ 0 đến 22.
        bits[:6], bits[6:14], bits[14:] chia liên tiếp 6/8/9 phần tử.
        super().__init__ gọi lớp cha để kiểm tra và sao chép ba thanh ghi.
        """
        if not isinstance(key, int) or not 0 <= key < (1 << 32):
            raise ValueError("TinyA51 key must be a 32-bit unsigned integer")
        state = (key & ((1 << 23) - 1)) ^ (key >> 23)
        bits = [(state >> i) & 1 for i in range(23)]
        super().__init__(bits[:6], bits[6:14], bits[14:])


# Khối dưới chỉ chạy khi thực thi file/module trực tiếp, không chạy khi import.
if __name__ == "__main__":
    key = "10010101001110100110000"
    bits = [int(bit) for bit in key]
    plain = [1, 1, 1]
    cipher = TinyA51Cipher(bits[:6], bits[6:14], bits[14:])
    encrypted, stream, logs = cipher.process_bits(plain)
    for log in logs:
        print(
            f"Bước {log['step']}: clock={log['clock_bits']}, majority={log['majority']}, S={log['keystream_bit']}"
        )
        print("  R1:", log["r1"], "R2:", log["r2"], "R3:", log["r3"])
    decipher = TinyA51Cipher(bits[:6], bits[6:14], bits[14:])
    restored, _, _ = decipher.process_bits(encrypted)
    print("Bản rõ:", plain, "Dòng S:", stream, "Bản mã:", encrypted)
    print("Khôi phục:", restored)
    assert restored == plain
