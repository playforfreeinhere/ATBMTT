#1. Khai báo lớp và khởi tạo
class A51Cipher:
    def __init__(self, key: list[int] = None, frame_number: int = None):
        # Khởi tạo đối tượng các thanh ghi R1,R2,R3 lần lượt gồm 19, 22, 23 bit 0
        self.r1 = [0] * 19 
        self.r2 = [0] * 22 
        self.r3 = [0] * 23 
        
        # Kiểm tra một trong hai tham số key hoặc frame_number có bị thiếu hay không.
        if (key is None) != (frame_number is None):
            raise ValueError("Provide both key and frame_number")
        # Nếu phát sinh lỗi đưa ra kết quả là "Hãy cung cấp cả key và frame_number"
        if key is not None and frame_number is not None:
            self.setup_key(key, frame_number)
        # Nếu mà key và frame_number đã được cung cấp đầy đủ thì sẽ gọi hàm thiết lập key, frame_number cho đối tượng.
    
#2. Hàm tìm bit đa số   
    # Định nghĩa hàm nhận ba bit và trả về bit đa số
    def _get_majority(self, b1: int, b2: int, b3: int) -> int:
        return 1 if (b1 + b2 + b3) >= 2 else 0
        # Nếu tổng ba bit ít nhất bằng 2, có ít nhất hai bit 1, nên trả về 1. Ngược lại trả về 0

#3. Dịch thanh ghi R1,R2,R3
    # Định nghĩa hàm dịch R1,R2,R3 một nhịp 
    def _clock_r1(self):
        feedback = self.r1[18] ^ self.r1[17] ^ self.r1[16] ^ self.r1[13]
        # Tính bit phản hồi bằng PP XOR các bit có vị trí tại 18, 17, 13 
        self.r1 = [feedback] + self.r1[:-1]
        # Trả về kết quả là danh sách chứa các bit mới nối với danh sách lấy các bit (đã dịch phải) và bỏ đi trừ bit cuối
        # VD: Các bit dịch chuyển sang phải 1 đơn vị; bit cuối bị loại bỏ và bit đầu thay thế bằng feedback; độ dài thanh ghi giữ nguyên
    
    def _clock_r2(self):
        feedback = self.r2[21] ^ self.r2[20]
        # Tính bit phản hồi bằng PP XOR các bit có vị trí tại 21,20
        self.r2 = [feedback] + self.r2[:-1]
        # Trả về kết quả là danh sách chứa các bit mới nối với danh sách lấy các bit (đã dịch phải) và bỏ đi trừ bit cuối
    
    def _clock_r3(self):
        feedback = self.r3[22] ^ self.r3[21] ^ self.r3[20] ^ self.r3[7]
        # Tính bit phản hồi bằng PP XOR các bit có vị trí tại 22, 21, 20, 20, 7
        self.r3 = [feedback] + self.r3[:-1]
        # Trả về kết quả là danh sách chứa các bit mới nối với danh sách lấy các bit cũ (đã dịch phải) và bỏ đi bit cuối

#4. Điều khiển thanh ghi nào được dịch
    # Định nghĩa (khởi tạo) một nhịp dịch (điều khiển) chung với hai chế độ True/False và mặc định là False.
    # inore_majority có hai chế độ bao gồm True (bỏ qua majority và dịch cả ba thanh ghi); False (dịch theo majority)
    def clock(self, ignore_majority: bool = False):
        # Nếu đang ở chế độ dịch toàn bộ (ignore_majority: bool = False) thì dịch R1,R2,R3 một nhịp (chế độ này được dùng khi nạp khóa và số khung.)
        if ignore_majority:
            self._clock_r1()
            self._clock_r2()
            self._clock_r3()
        # Nếu ngược lại là bỏ qua majority (ignore_majority: bool = True) thì:
        else:
            c1, c2, c3 = self.r1[8], self.r2[10], self.r3[10]
            # Lấy 3 bit điều khiển c1,c2,c3 tương ứng với các bit có vị trí 8, 10, 10 trong R1,R2,R3 theo thứ tự
            m = self._get_majority(c1, c2, c3)
            # Tính bit đa số của ba bit điều khiển c1,c2,c3 rồi lưu vào m (majority)
           
            if c1 == m:
                self._clock_r1()
            # Nếu c1 = m thì dịch R1
            if c2 == m:
                self._clock_r2()
            # Nếu c2 = m thì dịch R2
            if c3 == m:
                self._clock_r3()
            # Nếu c3 = m thì dịch R3
    # Còn lại giữ nguyên không dịch nếu không bằng m
    
#5. Sinh một bit dòng khóa (tạo ra 1 bit ngẫu nhiên 0 hoặc 1 để thực hiện việc mã hóa)
    def get_keystream_bit(self) -> int:
        self.clock(ignore_majority=False)
    # Khởi tạo hàm sinh một bit dòng khóa và dịch các thanh ghi theo majority
        return self.r1[18] ^ self.r2[21] ^ self.r3[22]
        # Trả về kết quả 0 hoặc 1 sau khi dịch và XOR ba bit có vị trí lần lượt là 18,21,22 thuộc R1,R2,R3.

#6. Thiết lập khóa và số khung    
    def setup_key(self, key: list[int], frame_number: int):
    # Khởi tạo hàm khóa với dãy giá trị nguyên và số khung
        self.r1 = [0] * 19
        self.r2 = [0] * 22
        self.r3 = [0] * 23
        # Đặt lại toàn bộ 3 thanh ghi về 0 (bắt đầu từ trạng thái xác định)
        if len(key) != 64 or any(bit not in (0, 1) for bit in key):
            raise ValueError("Key must contain exactly 64 bits")
        # Kiểm tra các phần tử có khác 64 không hoặc khác 0 và 1
            # Báo lỗi nếu khóa không đúng yêu cầu đủ 64 bits và trả về True nếu tìm thấy ít nhất một phần từ không phải bit hợp lệ
        if not isinstance(frame_number, int) or not 0 <= frame_number < (1 << 22):
            raise ValueError("Frame number must be a 22-bit unsigned integer")
        # Kiểm tra số khung có phải số nguyên không và có nằm trong khoảng từ 0 đến 2^22 không ? (1 << 22 là dịch bit 1 sang trái 22 vị trí)
            # Báo lỗi nếu số khung không phù hợp (số khung phải bao gồm 22 bit là số nguyên không dấu)
        
        for i in range(64):
        # Lặp 64 lần với i từ 0 -> 63
            self.clock(ignore_majority=True) # Dịch thanh ghi trước khi nạp bit khóa hiện tại
            self.r1[0] ^= key[i]
            self.r2[0] ^= key[i]
            self.r3[0] ^= key[i]
            # XOR bit khóa thứ i lần lượt vào đầu R1,R2,R3
        
        fn_bits = [(frame_number >> i) & 1 for i in range(22)] # Tách số khung thành số bit (tạo danh sách 22 bit của số khung, bit tăng dần rồi dịch phải số khung i vị trí và giữ lại bit thấp nhât)
        # Nạp số khung
        for i in range(22): # Lặp qua 22 lần bit số khung
            self.clock(ignore_majority=True) # Dịch qua 3 thanh ghi
            self.r1[0] ^= fn_bits[i]
            self.r2[0] ^= fn_bits[i]
            self.r3[0] ^= fn_bits[i]
            # XOR bit số khung hiện tại vào đầu từng thanh ghi R1,R2,R3
        # Chạy
        for _ in range(100): # Lặp 100 lần dùng _ vì chương trình không cần giá trị chỉ số vòng lặp
            self.clock(ignore_majority=False) # Dịch theo majority (chưa lấy các bit đầu ra để mã hóa)

#7. Xử lý dữ liệu byte
    def process_bytes(self, data: bytes) -> bytes:
    # Khởi tạo hàm nhận dữ liệu bytes và trả về bytes (mã hóa và giải mã)
        result = bytearray() # sử dụng bytearray để tạo vùng chứa kết quả các chuỗi bytes và có thể thêm từng bytes vào đó(bytearray thay đổi được còn bytes thì không)
        for byte in data: # Vòng lặp duyệt từng byte đầu vào với mỗi byte là số nguyên từ 0 đến 255
            cipher_byte = 0 # Khởi tạo byte với kết quả hiện tại bằng 0
            for bit_index in range(8): # Lặp 8 lần (do mỗi byte có 8 bit)
                ks_bit = self.get_keystream_bit() # Sinh một bit dòng khóa mới. Mỗi lần gọi cũng làm trạng thái thanh ghi tiến thêm một nhịp.
                data_bit = (byte >> (7 - bit_index)) & 1 # Lấy từng bit dữ liệu theo thứ tự bit cao trước
                cipher_bit = data_bit ^ ks_bit # XOR bit dữ liệu với bit dòng khóa 
                cipher_byte = (cipher_byte << 1) | cipher_bit # Ghép bit mới vào byte kết quả; dịch trái KQ một bit và đặt bit mới vào vị trí thấp nhất 
            result.append(cipher_byte) # Sau khi ghép đủ 8 bit, thêm byte kết quả vào result
        return bytes(result) # Trả về kết quả là bytes (chuyển bytearray thành bytes)

#8. Khối demo chạy trực tiếp
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
