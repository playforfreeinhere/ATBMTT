# Ví dụ TinyA5/1

Khóa `10010101001110100110000` được chia thành R1 = `100101`, R2 = `01001110`, R3 = `100110000`.

| Thanh ghi | Độ dài | Clock | Tap phản hồi | Đầu ra |
| --- | --- | --- | --- | --- |
| R1 | 6 bit | 1 | 2, 4, 5 | 5 |
| R2 | 8 bit | 3 | 6, 7 | 7 |
| R3 | 9 bit | 3 | 2, 7, 8 | 8 |

Index 0 là đầu nạp phản hồi. Mỗi bước đọc ba clock, tính majority, dịch các thanh ghi có clock bằng majority, rồi XOR ba bit cuối để lấy S.

Bản rõ `111`, dòng S `100`, bản mã `011`. Khởi tạo lại cùng khóa để giải mã: `011 XOR 100 = 111`.

## Các bước

```text
Index thanh ghi tăng từ đầu nạp feedback (index 0) đến đầu ra.
TinyA5/1 và A5/1 lấy S sau khi quay.

Bước 1: clock=(0, 0, 1), majority=0, quay=(True, True, False)
  R1: 100101 → 110010
  R2: 01001110 → 10100111
  R3: 100110000 → 100110000
  S=1; 1 XOR 1 = 0

Bước 2: clock=(1, 0, 1), majority=1, quay=(True, False, True)
  R1: 110010 → 111001
  R2: 10100111 → 10100111
  R3: 100110000 → 010011000
  S=0; 1 XOR 0 = 1

Bước 3: clock=(1, 0, 0), majority=0, quay=(False, True, True)
  R1: 111001 → 111001
  R2: 10100111 → 01010011
  R3: 010011000 → 001001100
  S=0; 1 XOR 0 = 1

```
