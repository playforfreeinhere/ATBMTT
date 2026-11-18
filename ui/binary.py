"""CHẾ ĐỘ NHỊ PHÂN VÀ BẢNG BƯỚC TRUNG GIAN."""

from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51Cipher
def validate_bits(value: str, length=None, label="Dữ liệu") -> list[int]:
    """Bỏ khoảng trắng hai đầu, kiểm tra 0/1 và tùy chọn độ dài chính xác."""
    value = value.strip()
    if not value or any(bit not in "01" for bit in value):
        raise ValueError(f"{label} chỉ được chứa 0 và 1, không để trống.")
    if length is not None and len(value) != length:
        raise ValueError(f"{label} phải có đúng {length} bit.")
    return [int(bit) for bit in value]

def process_binary(algorithm: str, key: str, frame: str, data: str):
    """Tính XOR theo từng bit và ghi trạng thái phục vụ mô phỏng."""
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
    """Chuyển rows thành văn bản nhiều dòng, không chạy lại thuật toán."""
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
