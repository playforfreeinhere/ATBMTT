""" A5/1."""
class A51Cipher:
    """Bộ sinh dòng khóa có trạng thái cho A5/1."""
    def __init__(self, key: list[int] = None, frame_number: int = None):
        """Tạo ba thanh ghi toàn 0 và thiết lập khóa nếu có đủ tham số."""
        self.r1 = [0] * 19
        self.r2 = [0] * 22
        self.r3 = [0] * 23
        if (key is None) != (frame_number is None):
            raise ValueError("Provide both key and frame_number")
        if key is not None:
            self.setup_key(key, frame_number)
    
    def _clock_r1(self):
        """Dịch R1 một nhịp với phản hồi r1[13] ^ r1[16] ^ r1[17] ^ r1[18]."""
        feedback = self.r1[13] ^ self.r1[16] ^ self.r1[17] ^ self.r1[18]
        self.r1 = [feedback] + self.r1[:-1]
    def _clock_r2(self):
        """Dịch R2 một nhịp: XOR hai tap 20,21 rồi đưa phản hồi vào index 0."""
        feedback = self.r2[20] ^ self.r2[21]
        self.r2 = [feedback] + self.r2[:-1]
    def _clock_r3(self):
        """Dịch R3 một nhịp: XOR bốn tap 7,20,21,22 rồi nạp vào index 0."""
        feedback = self.r3[7] ^ self.r3[20] ^ self.r3[21] ^ self.r3[22]
        self.r3 = [feedback] + self.r3[:-1]
    
    def clock(self, ignore_majority: bool = False):
        """Quyết định thanh ghi nào dịch trong một nhịp; không trả bit S."""
        clocks = (self.r1[8], self.r2[10], self.r3[10])
        majority = int(sum(clocks) >= 2)
        if ignore_majority or clocks[0] == majority:
            self._clock_r1()
        if ignore_majority or clocks[1] == majority:
            self._clock_r2()
        if ignore_majority or clocks[2] == majority:
            self._clock_r3()
   
    def setup_key(self, key: list[int], frame_number: int):
        """Reset rồi nạp khóa, nạp frame và khởi động bộ sinh dòng khóa."""
        if len(key) != 64 or any(bit not in (0, 1) for bit in key):
            raise ValueError("Key must contain exactly 64 bits")
        if not isinstance(frame_number, int) or not 0 <= frame_number < (1 << 22):
            raise ValueError("Frame number must be a 22-bit unsigned integer")
        self.r1, self.r2, self.r3 = [0] * 19, [0] * 22, [0] * 23
        # Frame nạp LSB trước: dịch phải i vị trí rồi & 1 giữ riêng bit đó.
        frame_bits = [(frame_number >> i) & 1 for i in range(22)] # Chuyển số nguyên thành dạng nhị phân 22 bit có dạng 0,1; dịch i lần, lấy bit thấp nhất rồi lặp lại 22 lần
        # Hai giai đoạn nạp dùng cùng phép dịch và XOR bit vào vị trí 0.
        for bit in list(key) + frame_bits: # Thực hiện lặp 86 lần listkey(64 bit) + framebit(22 bit)
            self.clock(ignore_majority=True)
            self.r1[0] ^= bit
            self.r2[0] ^= bit
            self.r3[0] ^= bit
        for _ in range(100):
            self.clock()
  
    def get_keystream_bit(self) -> int:
        """Tiến bộ sinh một nhịp và trả một bit dòng khóa 0/1."""
        self.clock()
        return self.r1[18] ^ self.r2[21] ^ self.r3[22]
  
    def process_bytes(self, data: bytes) -> bytes:
        """XOR dữ liệu bytes với dòng khóa; trả bytes có cùng độ dài."""
        output = bytearray()
        for byte in data:
            # Mỗi byte có mặt nạ mới, nhưng trạng thái bộ sinh vẫn tiếp tục từ byte trước.
            mask = 0
            for _ in range(8):
                mask = (mask << 1) | self.get_keystream_bit()
            output.append(byte ^ mask)
        return bytes(output)

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
