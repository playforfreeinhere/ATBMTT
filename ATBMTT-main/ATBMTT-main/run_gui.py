import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from pathlib import Path

from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51Cipher


def read_number(text, bits):
    text = text.strip()
    value = int(text, 16 if text.lower().startswith("0x") else 10)
    if not 0 <= value < (1 << bits):
        raise ValueError(f"Giá trị phải là số không dấu {bits} bit.")
    return value


def transform(data):
    if algorithm.get() == "A5/1":
        key = read_number(key_var.get(), 64)
        frame = read_number(frame_var.get(), 22)
        bits = [
            (byte >> i) & 1
            for byte in key.to_bytes(8, "big")
            for i in range(8)
        ]
        return A51Cipher(bits, frame).process_bytes(data)

    key = read_number(key_var.get(), 32)
    state = (key & ((1 << 23) - 1)) ^ (key >> 23)
    bits = [(state >> i) & 1 for i in range(23)]
    cipher = TinyA51Cipher(bits[:6], bits[6:14], bits[14:])
    stream, _ = cipher.generate_keystream(len(data) * 8)
    output = bytearray()
    for index, byte in enumerate(data):
        mask = 0
        for bit in stream[index * 8:index * 8 + 8]:
            mask = (mask << 1) | bit
        output.append(byte ^ mask)
    return bytes(output)


def run_text(decrypt=False):
    try:
        text = input_box.get("1.0", "end-1c")
        if decrypt:
            result = transform(bytes.fromhex(text)).decode("utf-8")
        else:
            result = transform(text.encode("utf-8")).hex()
        output_box.delete("1.0", "end")
        output_box.insert("1.0", result)
        status.set("Hoàn tất.")
    except Exception as error:
        messagebox.showerror(
            "Không thể xử lý",
            f"{error}\n\nKiểm tra khóa, số khung và dữ liệu đầu vào."
        )


def reuse():
    value = output_box.get("1.0", "end-1c")
    input_box.delete("1.0", "end")
    input_box.insert("1.0", value)


def run_file(decrypt=False):
    source = filedialog.askopenfilename(title="Chọn file đầu vào")
    if not source:
        return
    target = filedialog.asksaveasfilename(
        title="Chọn tên file đầu ra mới",
        initialfile="giai_ma.dat" if decrypt else "ban_ma.bin"
    )
    if not target:
        return
    try:
        if Path(target).exists():
            raise ValueError("File đầu ra đã tồn tại. Hãy chọn tên khác.")
        result = transform(Path(source).read_bytes())
        with open(target, "xb") as output:
            output.write(result)
        status.set(f"Đã lưu: {target}")
        messagebox.showinfo("Hoàn tất", f"Đã xử lý {len(result)} byte.")
    except Exception as error:
        messagebox.showerror("Không thể xử lý file", str(error))


root = tk.Tk()
root.title("A5/1 & TinyA5/1 — Nhóm 9")
root.geometry("850x680")

panel = ttk.Frame(root, padding=18)
panel.pack(fill="both", expand=True)

ttk.Label(
    panel, text="MÃ HÓA / GIẢI MÃ",
    font=("Segoe UI", 20, "bold")
).pack(anchor="w", pady=(0, 12))

settings = ttk.Frame(panel)
settings.pack(fill="x")

algorithm = tk.StringVar(value="TinyA5/1")
key_var = tk.StringVar(value="0x1A2B3C4D")
frame_var = tk.StringVar(value="0x134")
status = tk.StringVar(value="Sẵn sàng.")

for column, title in enumerate(["Thuật toán", "Khóa", "Số khung — A5/1"]):
    ttk.Label(settings, text=title).grid(
        row=0, column=column, sticky="w"
    )

ttk.Combobox(
    settings, textvariable=algorithm,
    values=["TinyA5/1", "A5/1"],
    state="readonly", width=15
).grid(row=1, column=0, padx=(0, 12), pady=6)

ttk.Entry(settings, textvariable=key_var, width=28).grid(
    row=1, column=1, padx=(0, 12)
)
ttk.Entry(settings, textvariable=frame_var, width=18).grid(
    row=1, column=2
)

ttk.Label(
    panel,
    text="Khóa: TinyA5/1 tối đa 32 bit; A5/1 tối đa 64 bit. "
         "Nhập số thập phân hoặc hex 0x..."
).pack(anchor="w", pady=8)

ttk.Label(
    panel, text="Đầu vào: văn bản để mã hóa / hex để giải mã"
).pack(anchor="w")

input_box = ScrolledText(panel, height=7, wrap="word")
input_box.pack(fill="both", expand=True, pady=6)
input_box.insert("1.0", "Xin chào! Đây là chương trình của Nhóm 9.")

actions = ttk.Frame(panel)
actions.pack(fill="x", pady=6)

for title, callback in [
    ("Mã hóa → Hex", lambda: run_text(False)),
    ("Giải mã → Văn bản", lambda: run_text(True)),
    ("Đưa kết quả lên đầu vào", reuse),
]:
    ttk.Button(actions, text=title, command=callback).pack(
        side="left", padx=(0, 8)
    )

ttk.Label(panel, text="Kết quả").pack(anchor="w")
output_box = ScrolledText(panel, height=7, wrap="word")
output_box.pack(fill="both", expand=True, pady=6)

files = ttk.Frame(panel)
files.pack(fill="x", pady=8)
ttk.Button(
    files, text="Mã hóa file…", command=lambda: run_file(False)
).pack(side="left", padx=(0, 8))
ttk.Button(
    files, text="Giải mã file…", command=lambda: run_file(True)
).pack(side="left")

ttk.Label(panel, textvariable=status, wraplength=790).pack(anchor="w")
ttk.Label(
    panel,
    text="Giải mã cần đúng thuật toán, khóa và số khung. "
         "Chỉ dùng cho học tập; dữ liệu không được xác thực.",
    wraplength=790
).pack(anchor="w", pady=8)

root.mainloop()