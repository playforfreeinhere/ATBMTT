"""LÕI A5/1 — độc lập với giao diện, văn bản và thao tác file.

Ba thanh ghi r1/r2/r3 là danh sách bit dài 19/22/23. Index 0 là đầu
nạp phản hồi; phần tử cuối là đầu ra. Clock dùng các vị trí 8/10/10.
Khởi tạo: đặt thanh ghi về 0 → nạp 64 bit khóa → nạp 22 bit frame
→ dịch 100 nhịp theo majority mà chưa dùng đầu ra để mã hóa.
Mỗi bit S được lấy SAU khi dịch, bằng XOR ba đầu ra 18/21/22.

Ký hiệu Python cần đọc: ^ là XOR, << là dịch trái, >> là dịch phải,
& 1 lấy bit thấp, [:-1] lấy tất cả phần tử trừ phần tử cuối.
Một đối tượng giữ trạng thái giữa các lần gọi. Giải mã phải tạo đối tượng
mới với cùng thiết lập; xử lý tiếp các khối của cùng file thì không reset.
Bản xử lý file là mô hình dòng byte liên tục, không mô phỏng việc chia
và đổi frame theo toàn bộ giao thức GSM.
"""


class A51Cipher:
    """Bộ sinh dòng khóa có trạng thái cho A5/1.

    Các thuộc tính r1/r2/r3 thay đổi sau mỗi nhịp, không phải hằng số khóa.
    Hai đối tượng mới có cùng khóa/frame sẽ bắt đầu cùng trạng thái.
    """

    def __init__(self, key: list[int] = None, frame_number: int = None):
        """Tạo ba thanh ghi toàn 0 và thiết lập khóa nếu có đủ tham số.

        key: danh sách 64 số 0/1 THEO THỨ TỰ NẠP, không tự đảo byte ở đây.
        frame_number: số nguyên không dấu 22 bit. Cùng thiếu cả hai cho phép tạo
        trạng thái rỗng; chỉ cung cấp một trong hai sẽ bị từ chối.
        self là đối tượng hiện tại; [0] * 19 tạo danh sách gồm 19 số 0.
        """
        self.r1 = [0] * 19
        self.r2 = [0] * 22
        self.r3 = [0] * 23
        if (key is None) != (frame_number is None):
            raise ValueError("Provide both key and frame_number")
        if key is not None:
            self.setup_key(key, frame_number)

    def _clock_r1(self):
        """Dịch R1 một nhịp với phản hồi r1[13] ^ r1[16] ^ r1[17] ^ r1[18].

        Tính feedback từ trạng thái cũ rồi mới thay danh sách.
        [feedback] + self.r1[:-1] đưa bit mới vào đầu, loại bit cuối, giữ 19 bit.
        """
        feedback = self.r1[13] ^ self.r1[16] ^ self.r1[17] ^ self.r1[18]
        self.r1 = [feedback] + self.r1[:-1]

    def _clock_r2(self):
        """Dịch R2 một nhịp: XOR hai tap 20,21 rồi đưa phản hồi vào index 0.

        Bit cuối cũ bị loại bỏ; độ dài thanh ghi vẫn là 22.
        """
        feedback = self.r2[20] ^ self.r2[21]
        self.r2 = [feedback] + self.r2[:-1]

    def _clock_r3(self):
        """Dịch R3 một nhịp: XOR bốn tap 7,20,21,22 rồi nạp vào index 0.

        Không phải dịch vòng: bit đầu mới là phản hồi, không phải bản sao bit cuối.
        """
        feedback = self.r3[7] ^ self.r3[20] ^ self.r3[21] ^ self.r3[22]
        self.r3 = [feedback] + self.r3[:-1]

    def clock(self, ignore_majority: bool = False):
        """Quyết định thanh ghi nào dịch trong một nhịp; không trả bit S.

        clocks lưu ba bit điều khiển cũ, majority=1 nếu tổng ít nhất là 2.
        ignore_majority=True: dịch tất cả, dùng khi nạp khóa/frame.
        False: chỉ dịch thanh ghi có clock bằng majority, dùng từ giai đoạn
        khởi động trở đi. Điều kiện dùng ba giá trị đã đọc trước mọi phép dịch.
        int(True)=1, int(False)=0; mỗi nhịp majority dịch hai hoặc ba thanh ghi.
        """
        clocks = (self.r1[8], self.r2[10], self.r3[10])
        majority = int(sum(clocks) >= 2)
        if ignore_majority or clocks[0] == majority:
            self._clock_r1()
        if ignore_majority or clocks[1] == majority:
            self._clock_r2()
        if ignore_majority or clocks[2] == majority:
            self._clock_r3()

    def setup_key(self, key: list[int], frame_number: int):
        """Reset rồi nạp khóa, nạp frame và khởi động bộ sinh dòng khóa.

        Kiểm tra đúng 64 bit khóa, frame trong [0, 2**22). 1 << 22 là 2**22.
        frame_bits lấy 22 bit của frame từ thấp lên cao; list(key)+frame_bits
        là 86 bit nạp liên tiếp, khóa trước/frame sau, cùng quy tắc clock.
        Mỗi bit: dịch cả ba thanh ghi, XOR bit đó vào vị trí 0 của từng thanh ghi.
        100 nhịp cuối dùng majority để trộn trạng thái; chưa dùng S làm bản mã.
        Dấu ^= là gán sau XOR: r1[0] ^= bit tương đương r1[0] = r1[0] ^ bit.
        """
        if len(key) != 64 or any(bit not in (0, 1) for bit in key):
            raise ValueError("Key must contain exactly 64 bits")
        if not isinstance(frame_number, int) or not 0 <= frame_number < (1 << 22):
            raise ValueError("Frame number must be a 22-bit unsigned integer")
        self.r1, self.r2, self.r3 = [0] * 19, [0] * 22, [0] * 23
        # Frame nạp LSB trước: dịch phải i vị trí rồi & 1 giữ riêng bit đó.
        frame_bits = [(frame_number >> i) & 1 for i in range(22)]
        # Hai giai đoạn nạp dùng cùng phép dịch và XOR bit vào vị trí 0.
        for bit in list(key) + frame_bits:
            self.clock(ignore_majority=True)
            self.r1[0] ^= bit
            self.r2[0] ^= bit
            self.r3[0] ^= bit
        # _ cho biết không dùng chỉ số vòng lặp; 100 nhịp này chỉ trộn trạng thái.
        for _ in range(100):
            self.clock()

    def get_keystream_bit(self) -> int:
        """Tiến bộ sinh một nhịp và trả một bit dòng khóa 0/1.

        Phải clock trước, sau đó XOR các vị trí 18,21,22 của trạng thái mới.
        Gọi thêm lần nữa tiếp tục dòng khóa, không khởi tạo lại.
        """
        self.clock()
        return self.r1[18] ^ self.r2[21] ^ self.r3[22]

    def process_bytes(self, data: bytes) -> bytes:
        """XOR dữ liệu bytes với dòng khóa; trả bytes có cùng độ dài.

        Mỗi byte cần 8 lần sinh bit. mask ghép bit cao trước bằng phép << 1
        và | (OR); khi đủ 8 bit, byte ^ mask cho byte kết quả.
        bytearray cho phép append, bytes là dạng kết quả không sửa tại chỗ.
        Cùng phép xử lý dùng cho mã hóa và giải mã, nhưng giải mã phải tạo đối
        tượng mới với cùng trạng thái ban đầu. Nhiều khối cùng file dùng một đối tượng.
        """
        output = bytearray()
        for byte in data:
            # Mỗi byte có mặt nạ mới, nhưng trạng thái bộ sinh vẫn tiếp tục từ byte trước.
            mask = 0
            for _ in range(8):
                mask = (mask << 1) | self.get_keystream_bit()
            output.append(byte ^ mask)
        return bytes(output)


# Khối dưới chỉ chạy khi thực thi file/module trực tiếp, không chạy khi import.
if __name__ == "__main__":
    key = [1] * 32 + [0] * 32
    frame = 0x12345
    plain = "Hệ mã dòng A5/1 — Nhóm 9".encode("utf-8")
    encrypted = A51Cipher(key, frame).process_bytes(plain)
    restored = A51Cipher(key, frame).process_bytes(encrypted)
    print("Bản rõ:", plain.decode("utf-8"))
    print("Bản mã hex:", encrypted.hex())
    print("Khôi phục:", restored.decode("utf-8"))
    assert restored == plain
