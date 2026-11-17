"""CHẾ ĐỘ NHỊ PHÂN VÀ BẢNG BƯỚC TRUNG GIAN.

Không chuyển bản rõ qua UTF-8: chuỗi "111" ở đây là ba bit, trong khi
văn bản "111" ở chế độ text là ba byte UTF-8. Hai dữ liệu không giống nhau.
validate_bits kiểm tra và chuyển chuỗi sang list[int].
process_binary trả (bản kết quả, dòng khóa S, danh sách lịch sử từng bước).
format_trace chuyển lịch sử thành văn bản để hiển thị.

Tiny nhận khóa nhị phân 23 bit; A5/1 nhận khóa nhị phân 64 bit và frame
nhị phân 22 bit. GUI chuyển số thập phân/hex sang dạng này trước khi gọi.
Hai lõi đều lấy bit đầu ra SAU khi dịch; clock được đọc TRƯỚC khi dịch.
"""

from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51Cipher


def validate_bits(value: str, length=None, label="Dữ liệu") -> list[int]:
    """Bỏ khoảng trắng hai đầu, kiểm tra 0/1 và tùy chọn độ dài chính xác.

    Chuỗi rỗng hoặc khoảng trắng ở giữa bị từ chối. label giúp ghi rõ khóa,
    frame hay dữ liệu đang sai. Trả danh sách số nguyên, không phải ký tự.
    """
    value = value.strip()
    if not value or any(bit not in "01" for bit in value):
        raise ValueError(f"{label} chỉ được chứa 0 và 1, không để trống.")
    if length is not None and len(value) != length:
        raise ValueError(f"{label} phải có đúng {length} bit.")
    return [int(bit) for bit in value]


def process_binary(algorithm: str, key: str, frame: str, data: str):
    """Tính XOR theo từng bit và ghi trạng thái phục vụ mô phỏng.

    algorithm: TinyA5/1 hoặc A5/1; key/frame là chuỗi nhị phân đúng độ dài.
    data tối đa 4096 bit để bảng lịch sử không quá lớn. Tiny chia key trực tiếp.
    A5/1 đảo thứ tự bit TRONG mỗi nhóm 8 bit khóa để nạp LSB trước; thứ tự
    các byte giữ nguyên. frame được chuyển về số nguyên rồi lõi tự tách bit.
    Mỗi vòng lưu before trước khi sinh S, đọc after sau khi sinh. output_bit
    là input_bit XOR S. stream/output là list ký tự để join thành chuỗi.
    rows là list dictionary chứa step, before, after, clock_bits, majority,
    clocked, stream, input và output. Không có khóa con theo vòng như DES.
    Trả tuple (chuỗi_kết_quả, chuỗi_S, rows); không sửa giao diện.
    """
    source = validate_bits(data)
    if len(source) > 4096:
        raise ValueError(
            "Bảng từng bước giới hạn 4096 bit. Dùng chế độ file cho dữ liệu lớn."
        )
    if algorithm == "TinyA5/1":
        bits = validate_bits(key, 23, "Khóa / trạng thái TinyA5/1")
        cipher = TinyA51Cipher(bits[:6], bits[6:14], bits[14:])
    elif algorithm == "A5/1":
        bits = validate_bits(key, 64, "Khóa A5/1")
        frame_bits = validate_bits(frame, 22, "Số khung A5/1")
        loading_order = [
            bit
            for offset in range(0, 64, 8)
            for bit in reversed(bits[offset : offset + 8])
        ]
        cipher = A51Cipher(loading_order, int("".join(map(str, frame_bits)), 2))
    else:
        raise ValueError("Thuật toán không hợp lệ.")
    stream, output, rows = [], [], []
    for step, input_bit in enumerate(source, 1):
        # Sao chép các thanh ghi để lịch sử trước/sau không bị ghi đè về sau.
        before = [list(cipher.r1), list(cipher.r2), list(cipher.r3)]
        if algorithm == "TinyA5/1":
            bit, log = cipher.step_verbose(step)
        else:
            clocks = (cipher.r1[8], cipher.r2[10], cipher.r3[10])
            majority = int(sum(clocks) >= 2)
            bit = cipher.get_keystream_bit()
            log = {
                "clock_bits": clocks,
                "majority": majority,
                "clocked": tuple(clock == majority for clock in clocks),
                "r1": list(cipher.r1),
                "r2": list(cipher.r2),
                "r3": list(cipher.r3),
            }
        # Một vòng ứng với một bit bản rõ/bản mã, không phải một ký tự UTF-8.
        output_bit = input_bit ^ bit
        stream.append(str(bit))
        output.append(str(output_bit))
        rows.append(
            {
                "step": step,
                "before": before,
                "after": [log["r1"], log["r2"], log["r3"]],
                "clock_bits": log["clock_bits"],
                "majority": log["majority"],
                "clocked": log["clocked"],
                "stream": bit,
                "input": input_bit,
                "output": output_bit,
            }
        )
    return "".join(output), "".join(stream), rows


def format_trace(rows) -> str:
    """Chuyển rows thành văn bản nhiều dòng, không chạy lại thuật toán.

    Mỗi bước in clock, majority, ba trạng thái trước/sau và phép XOR.
    join(map(str, bits)) ghép list 0/1 thành chuỗi như 100101. enumerate(...,1)
    đặt tên R1/R2/R3; ký tự xuống dòng được thêm bằng "\n" khi join.
    """
    lines = [
        "Index thanh ghi tăng từ đầu nạp feedback (index 0) đến đầu ra.",
        "TinyA5/1 và A5/1 lấy S sau khi quay.",
        "",
    ]
    for row in rows:
        lines.append(
            f"Bước {row['step']}: clock={row['clock_bits']}, majority={row['majority']}, "
            f"quay={row['clocked']}"
        )
        for index, (before, after) in enumerate(zip(row["before"], row["after"]), 1):
            lines.append(
                f"  R{index}: {''.join(map(str, before))} → {''.join(map(str, after))}"
            )
        lines.append(
            f"  S={row['stream']}; {row['input']} XOR {row['stream']} = {row['output']}\n"
        )
    return "\n".join(lines)
