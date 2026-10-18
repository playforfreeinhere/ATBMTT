class A51Cipher:
    """
    Thuật toán mã hóa dòng A5/1 (GSM)
    
    Cấu trúc gồm 3 thanh ghi LFSR:
      - R1: 19 bit (Clock bit ở vị trí index 8, Bit phản hồi = R1[18] ^ R1[17] ^ R1[16] ^ R1[13])
      - R2: 22 bit (Clock bit ở vị trí index 10, Bit phản hồi = R2[21] ^ R2[20])
      - R3: 23 bit (Clock bit ở vị trí index 10, Bit phản hồi = R3[22] ^ R3[21] ^ R3[20] ^ R3[7])
    """

    def __init__(self, key=None, frame_number=None):
        # Tạo thanh ghi R1 gồm 19 bit 0 ban đầu
        self.r1 = [0] * 19
        # Tạo thanh ghi R2 gồm 22 bit 0 ban đầu
        self.r2 = [0] * 22
        # Tạo thanh ghi R3 gồm 23 bit 0 ban đầu
        self.r3 = [0] * 23

        # Nếu có truyền Khóa K và Số khung Fn thì nạp khóa ngay
        if key is not None and frame_number is not None:
            self.setup_key(key, frame_number)

    def get_majority(self, b1, b2, b3):
        """Hàm tìm bit chiếm đa số giữa 3 bit b1, b2, b3 (trả về 0 hoặc 1)"""
        # Nếu tổng lớn hơn hoặc bằng 2 thì số lượng bit 1 nhiều hơn (đa số là 1), ngược lại là 0
        if (b1 + b2 + b3) >= 2:
            return 1
        else:
            return 0

    def clock_r1(self):
        """Dịch 1 nhịp thanh ghi R1"""
        # Tính bit phản hồi (feedback) của R1 theo đa thức GSM
        feedback = self.r1[18] ^ self.r1[17] ^ self.r1[16] ^ self.r1[13]
        # Dịch toàn bộ bit sang phải và chèn bit feedback mới vào vị trí đầu tiên (index 0)
        self.r1 = [feedback] + self.r1[:-1]

    def clock_r2(self):
        """Dịch 1 nhịp thanh ghi R2"""
        # Tính bit phản hồi (feedback) của R2
        feedback = self.r2[21] ^ self.r2[20]
        # Dịch toàn bộ bit sang phải và chèn bit feedback mới vào vị trí đầu tiên (index 0)
        self.r2 = [feedback] + self.r2[:-1]

    def clock_r3(self):
        """Dịch 1 nhịp thanh ghi R3"""
        # Tính bit phản hồi (feedback) của R3
        feedback = self.r3[22] ^ self.r3[21] ^ self.r3[20] ^ self.r3[7]
        # Dịch toàn bộ bit sang phải và chèn bit feedback mới vào vị trí đầu tiên (index 0)
        self.r3 = [feedback] + self.r3[:-1]

    def clock(self, ignore_majority=False):
        """
        Dịch các thanh ghi:
          - Nếu ignore_majority=True: Dịch cả 3 thanh ghi (dùng khi nạp khóa).
          - Nếu ignore_majority=False: Dịch theo quy tắc chiếm đa số (dùng khi sinh khóa).
        """
        if ignore_majority:
            # Dịch tất cả 3 thanh ghi đồng thời
            self.clock_r1()
            self.clock_r2()
            self.clock_r3()
        else:
            # 1. Lấy bit kiểm soát (clock bits) của 3 thanh ghi
            c1 = self.r1[8]
            c2 = self.r2[10]
            c3 = self.r3[10]

            # 2. Tìm bit đa số
            maj = self.get_majority(c1, c2, c3)

            # 3. Thanh ghi nào có bit kiểm soát trùng với bit đa số thì mới dịch
            if c1 == maj:
                self.clock_r1()
            if c2 == maj:
                self.clock_r2()
            if c3 == maj:
                self.clock_r3()

    def get_keystream_bit(self):
        """Sinh ra 1 bit khóa (Keystream bit)"""
        # Dịch các thanh ghi theo quy tắc đa số
        self.clock(ignore_majority=False)
        # Bit khóa sinh ra = Bit cuối của R1 XOR Bit cuối của R2 XOR Bit cuối của R3
        return self.r1[18] ^ self.r2[21] ^ self.r3[22]

    def setup_key(self, key, frame_number):
        """Quy trình nạp Khóa K (64 bit) và Frame Number Fn (22 bit) vào các thanh ghi"""
        # 1. Reset các thanh ghi về 0
        self.r1 = [0] * 19
        self.r2 = [0] * 22
        self.r3 = [0] * 23

        # 2. Nạp 64 bit của Khóa K (Dịch cả 3 thanh ghi đồng thời)
        for i in range(64):
            self.clock(ignore_majority=True)
            self.r1[0] = self.r1[0] ^ key[i]
            self.r2[0] = self.r2[0] ^ key[i]
            self.r3[0] = self.r3[0] ^ key[i]

        # 3. Chuyển Frame Number (số nguyên) thành danh sách 22 bit
        fn_bits = []
        for i in range(22):
            bit = (frame_number >> i) & 1
            fn_bits.append(bit)

        # 4. Nạp 22 bit của Frame Number Fn (Dịch cả 3 thanh ghi đồng thời)
        for i in range(22):
            self.clock(ignore_majority=True)
            self.r1[0] = self.r1[0] ^ fn_bits[i]
            self.r2[0] = self.r2[0] ^ fn_bits[i]
            self.r3[0] = self.r3[0] ^ fn_bits[i]

        # 5. Chạy 100 nhịp trộn xáo trộn trạng thái (Warm-up cycles)
        for _ in range(100):
            self.clock(ignore_majority=False)

    def encrypt_bytes(self, data):
        """Mã hóa / Giải mã mảng dữ liệu bytes (Dùng cho file văn bản, file ảnh...)"""
        # Tạo mảng lưu trữ kết quả byte
        result = bytearray()

        # Duyệt qua từng byte trong dữ liệu đầu vào
        for byte in data:
            cipher_byte = 0
            # Duyệt qua từng bit trong 1 byte (8 bit)
            for bit_index in range(8):
                # Sinh 1 bit dòng khóa
                ks_bit = self.get_keystream_bit()

                # Lấy 1 bit của dữ liệu gốc từ trái sang phải
                data_bit = (byte >> (7 - bit_index)) & 1

                # Thực hiện phép XOR giữa bit dữ liệu và bit khóa
                cipher_bit = data_bit ^ ks_bit

                # Ghép bit mã hóa vào cipher_byte
                cipher_byte = (cipher_byte << 1) | cipher_bit

            # Thêm byte đã mã hóa vào danh sách kết quả
            result.append(cipher_byte)

        # Trả về kết quả kiểu bytes
        return bytes(result)
