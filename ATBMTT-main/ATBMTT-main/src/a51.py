class A51Cipher:
    def __init__(self, key: list[int] = None, frame_number: int = None):
        self.r1 = [0] * 19
        self.r2 = [0] * 22
        self.r3 = [0] * 23
        if (key is None) != (frame_number is None):
            raise ValueError("Provide both key and frame_number")
        if key is not None and frame_number is not None:
            self.setup_key(key, frame_number)
    def _get_majority(self, b1: int, b2: int, b3: int) -> int:
        return 1 if (b1 + b2 + b3) >= 2 else 0
    def _clock_r1(self):
        feedback = self.r1[18] ^ self.r1[17] ^ self.r1[16] ^ self.r1[13]
        self.r1 = [feedback] + self.r1[:-1]
    def _clock_r2(self):
        feedback = self.r2[21] ^ self.r2[20]
        self.r2 = [feedback] + self.r2[:-1]
    def _clock_r3(self):
        feedback = self.r3[22] ^ self.r3[21] ^ self.r3[20] ^ self.r3[7]
        self.r3 = [feedback] + self.r3[:-1]
    def clock(self, ignore_majority: bool = False):
        if ignore_majority:
            self._clock_r1()
            self._clock_r2()
            self._clock_r3()
        else:
            c1, c2, c3 = self.r1[8], self.r2[10], self.r3[10]
            m = self._get_majority(c1, c2, c3)
            if c1 == m:
                self._clock_r1()
            if c2 == m:
                self._clock_r2()
            if c3 == m:
                self._clock_r3()
    def get_keystream_bit(self) -> int:
        self.clock(ignore_majority=False)
        return self.r1[18] ^ self.r2[21] ^ self.r3[22]
    def setup_key(self, key: list[int], frame_number: int):
        self.r1 = [0] * 19
        self.r2 = [0] * 22
        self.r3 = [0] * 23
        if len(key) != 64 or any(bit not in (0, 1) for bit in key):
            raise ValueError("Key must contain exactly 64 bits")
        if not isinstance(frame_number, int) or not 0 <= frame_number < (1 << 22):
            raise ValueError("Frame number must be a 22-bit unsigned integer")
        for i in range(64):
            self.clock(ignore_majority=True)
            self.r1[0] ^= key[i]
            self.r2[0] ^= key[i]
            self.r3[0] ^= key[i]
        fn_bits = [(frame_number >> i) & 1 for i in range(22)]
        for i in range(22):
            self.clock(ignore_majority=True)
            self.r1[0] ^= fn_bits[i]
            self.r2[0] ^= fn_bits[i]
            self.r3[0] ^= fn_bits[i]
        for _ in range(100):
            self.clock(ignore_majority=False)
    def process_bytes(self, data: bytes) -> bytes:
        result = bytearray()
        for byte in data:
            cipher_byte = 0
            for bit_index in range(8):
                ks_bit = self.get_keystream_bit()
                data_bit = (byte >> (7 - bit_index)) & 1
                cipher_bit = data_bit ^ ks_bit
                cipher_byte = (cipher_byte << 1) | cipher_bit
            result.append(cipher_byte)
        return bytes(result)
if __name__ == "__main__":
    key_64bit = [1] * 32 + [0] * 32  
    fn = 0x12345                     
    cipher_enc = A51Cipher(key_64bit, fn)
    plaintext_data = "Hệ mã dòng A5/1 - Nhóm 9".encode('utf-8')
    print("DEMO THUẬT TOÁN A5/1 ĐẦY ĐỦ (GSM)")
    print(f"Bản rõ ban đầu  : {plaintext_data.decode('utf-8')}")
    ciphertext_data = cipher_enc.process_bytes(plaintext_data)
    print(f"Bản mã (Hex)    : {ciphertext_data.hex()}")
    cipher_dec = A51Cipher(key_64bit, fn)
    recovered_data = cipher_dec.process_bytes(ciphertext_data)
    print(f"Giải mã khôi phục: {recovered_data.decode('utf-8')}")
    assert recovered_data == plaintext_data, "Lỗi: Giải mã A5/1 không khớp bản rõ!"
    print("-> KIỂM THỬ THÀNH CÔNG: Mã hóa và giải mã A5/1 hoàn tất chuẩn xác.")
