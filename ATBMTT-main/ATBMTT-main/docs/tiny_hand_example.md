# Ví dụ TinyA5/1 6/8/9 bit

Đây là biến thể đang có trong repository; chưa có tài liệu lớp để xác nhận đúng biến thể được giao. Không suy ra quy tắc từ riêng ảnh chụp ciphertext.

- R1 = `101100` (6 bit), clock index 2, tap index 2 và 5.
- R2 = `01010110` (8 bit), clock index 3, tap index 4 và 7.
- R3 = `110010101` (9 bit), clock index 3, tap index 5 và 8.
- Index 0 là đầu nạp feedback, đầu ra là index cuối. Khóa/trạng thái trực tiếp là R1 || R2 || R3: `10110001010110110010101`.
- Mỗi bước: lấy S bằng XOR các đầu ra trước khi quay; majority = bit chiếm đa số của ba clock; chỉ thanh ghi có clock bằng majority được quay; nạp XOR các tap vào index 0.
- Bản rõ `1011`, dòng khóa `1001`, bản mã `0010`; giải mã `0010 XOR 1001 = 1011`.

Các trạng thái trung gian từ cùng lõi dùng trong chương trình, để đối chiếu tính tay:

```text
Index thanh ghi tăng từ đầu nạp feedback (index 0) đến đầu ra.
TinyA5/1 lấy S trước khi quay; A5/1 lấy S sau khi quay.

Bước 1: clock=(1, 1, 0), majority=1, quay=(True, True, False)
  R1: 101100 → 110110
  R2: 01010110 → 00101011
  R3: 110010101 → 110010101
  S=1; 1 XOR 1 = 0

Bước 2: clock=(0, 0, 0), majority=0, quay=(True, True, True)
  R1: 110110 → 011011
  R2: 00101011 → 00010101
  R3: 110010101 → 111001010
  S=0; 0 XOR 0 = 0

Bước 3: clock=(1, 1, 0), majority=1, quay=(True, True, False)
  R1: 011011 → 001101
  R2: 00010101 → 10001010
  R3: 111001010 → 111001010
  S=0; 1 XOR 0 = 1

Bước 4: clock=(1, 0, 0), majority=0, quay=(False, True, True)
  R1: 001101 → 001101
  R2: 10001010 → 11000101
  R3: 111001010 → 111100101
  S=1; 1 XOR 1 = 0

```
