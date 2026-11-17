"""A5/1 GSM: thanh ghi 19/22/23 bit, khóa 64 bit, frame 22 bit.

Index 0 là đầu nạp phản hồi. Dòng khóa được lấy sau khi dịch.
"""


class A51Cipher:
    def __init__(self, key: list[int] = None, frame_number: int = None):
        self.r1 = [0] * 19
        self.r2 = [0] * 22
        self.r3 = [0] * 23
        if (key is None) != (frame_number is None):
            raise ValueError("Provide both key and frame_number")
        if key is not None:
            self.setup_key(key, frame_number)

    def _clock_r1(self):
        feedback = self.r1[13] ^ self.r1[16] ^ self.r1[17] ^ self.r1[18]
        self.r1 = [feedback] + self.r1[:-1]

    def _clock_r2(self):
        feedback = self.r2[20] ^ self.r2[21]
        self.r2 = [feedback] + self.r2[:-1]

    def _clock_r3(self):
        feedback = self.r3[7] ^ self.r3[20] ^ self.r3[21] ^ self.r3[22]
        self.r3 = [feedback] + self.r3[:-1]

    def clock(self, ignore_majority: bool = False):
        """Nạp khóa/frame: dịch cả ba. Sinh dòng khóa: dịch theo majority."""
        clocks = (self.r1[8], self.r2[10], self.r3[10])
        majority = int(sum(clocks) >= 2)
        if ignore_majority or clocks[0] == majority:
            self._clock_r1()
        if ignore_majority or clocks[1] == majority:
            self._clock_r2()
        if ignore_majority or clocks[2] == majority:
            self._clock_r3()

    def setup_key(self, key: list[int], frame_number: int):
        """Nhận bit khóa theo thứ tự nạp; frame nạp từ bit thấp lên cao."""
        if len(key) != 64 or any(bit not in (0, 1) for bit in key):
            raise ValueError("Key must contain exactly 64 bits")
        if not isinstance(frame_number, int) or not 0 <= frame_number < (1 << 22):
            raise ValueError("Frame number must be a 22-bit unsigned integer")
        self.r1, self.r2, self.r3 = [0] * 19, [0] * 22, [0] * 23
        frame_bits = [(frame_number >> i) & 1 for i in range(22)]
        # Hai giai đoạn nạp dùng cùng phép dịch và XOR bit vào vị trí 0.
        for bit in list(key) + frame_bits:
            self.clock(ignore_majority=True)
            self.r1[0] ^= bit
            self.r2[0] ^= bit
            self.r3[0] ^= bit
        for _ in range(100):
            self.clock()

    def get_keystream_bit(self) -> int:
        self.clock()
        return self.r1[18] ^ self.r2[21] ^ self.r3[22]

    def process_bytes(self, data: bytes) -> bytes:
        """XOR từng byte với 8 bit dòng khóa; dùng cho cả hai chiều."""
        output = bytearray()
        for byte in data:
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
