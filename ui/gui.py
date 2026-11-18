"""GIAO DIỆN TKINTER HAI TAB."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from ui.binary import format_trace, process_binary
from ui.operations import parse_unsigned, process_file, process_text
# Khóa ví dụ cố định để đối chiếu với slide, không dùng làm khóa bảo mật.
TINY_KEY = "10010101001110100110000"
A51_KEY = "0x1223456789ABCDEF"

class CipherApp:
    def __init__(self, root):
        self.root = root
        # Chỉ worker xử lý thuật toán; Tkinter luôn được cập nhật từ luồng chính.
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.pending_kind = None
        self.buttons = []
        # Widget lưu dữ liệu hiển thị; results bên dưới lưu kết quả thuần cho nút reuse.
        self.inputs, self.outputs = {}, {}
        self.results = {"bit": "", "text": ""}
        self.algorithm = tk.StringVar(value="TinyA5/1")
        self.key = tk.StringVar(value=TINY_KEY)
        self.frame = tk.StringVar(value="0x134")
        self.hint = tk.StringVar()
        self.status = tk.StringVar()
        root.title("Nhóm 9 — TinyA5/1 và A5/1")
        root.geometry("1100x820")
        root.minsize(740, 600)
        root.protocol("WM_DELETE_WINDOW", self.close)
        panel = ttk.Frame(root, padding=16)
        panel.pack(fill="both", expand=True)
        self.build_settings(panel)
        self.tabs = ttk.Notebook(panel)
        self.tabs.pack(fill="both", expand=True, pady=10)
        self.build_tab("bit", "Nhị phân / Tính tay")
        self.build_tab("text", "Văn bản / File")
        ttk.Label(panel, textvariable=self.status, wraplength=1050).pack(anchor="w")
        self.load_example()
        self.tabs.select(1)

    def build_settings(self, panel):
        ttk.Label(
            panel, text="HỆ MÃ DÒNG — NHÓM 9", font=("Segoe UI", 18, "bold")
        ).pack(anchor="w")
        row = ttk.Frame(panel)
        row.pack(fill="x", pady=10)
        self.selector = ttk.Combobox(
            row,
            textvariable=self.algorithm,
            values=("TinyA5/1", "A5/1"),
            state="readonly",
            width=13,
        )
        self.selector.pack(side="left")
        self.selector.bind("<<ComboboxSelected>>", self.load_example)
        ttk.Label(row, text=" Khóa: ").pack(side="left")
        self.key_entry = ttk.Entry(row, textvariable=self.key, width=34)
        self.key_entry.pack(side="left")
        ttk.Label(row, text=" Frame: ").pack(side="left")
        self.frame_entry = ttk.Entry(row, textvariable=self.frame, width=12)
        self.frame_entry.pack(side="left")
        self.button(row, "Nạp ví dụ", self.load_example).pack(side="left", padx=8)
        ttk.Label(panel, textvariable=self.hint, wraplength=1050).pack(anchor="w")

    def build_tab(self, mode, title):
        tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(tab, text=title)
        label = (
            "Đầu vào: chuỗi 0/1 (tối đa 4096 bit)"
            if mode == "bit"
            else "Đầu vào: văn bản UTF-8 / bản mã hex"
        )
        ttk.Label(tab, text=label).pack(anchor="w")
        self.inputs[mode] = self.textbox(tab)
        row = ttk.Frame(tab)
        row.pack(fill="x")
        self.button(row, "Mã hóa", lambda: self.run(mode, False)).pack(
            side="left", padx=(0, 8)
        )
        self.button(row, "Giải mã", lambda: self.run(mode, True)).pack(
            side="left", padx=(0, 8)
        )
        self.button(row, "Đưa kết quả lên đầu vào", lambda: self.reuse(mode)).pack(
            side="left"
        )
        ttk.Label(tab, text="Kết quả").pack(anchor="w", pady=(8, 0))
        self.outputs[mode] = self.textbox(tab, readonly=True)
        if mode == "bit":
            ttk.Label(
                tab,
                text="Các bước: thanh ghi trước → sau; clock; majority; dòng khóa S",
            ).pack(anchor="w")
            self.trace = self.textbox(tab, readonly=True, height=7, wrap="none")
        else:
            row = ttk.Frame(tab)
            row.pack(fill="x", pady=8)
            self.button(row, "Mã hóa file...", lambda: self.run_file(False)).pack(
                side="left", padx=(0, 8)
            )
            self.button(row, "Giải mã file...", lambda: self.run_file(True)).pack(
                side="left"
            )

    def button(self, parent, label, command):
        button = ttk.Button(parent, text=label, command=command)
        self.buttons.append(button)
        return button

    @staticmethod
    def textbox(parent, readonly=False, height=4, wrap="word"):
        box = ScrolledText(
            parent,
            height=height,
            wrap=wrap,
            font=("Consolas", 10),
            state="disabled" if readonly else "normal",
        )
        box.pack(fill="both", expand=True, pady=5)
        return box

    @staticmethod
    def set_output(widget, value):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def update_algorithm(self):
        tiny = self.algorithm.get() == "TinyA5/1"
        self.frame_entry.configure(state="disabled" if tiny else "normal")
        self.hint.set(
            "Tiny 6/8/9 bit: khóa 23 bit = R1 || R2 || R3; clock 1/3/3; S lấy sau khi quay."
            if tiny
            else "A5/1 19/22/23 bit: khóa 64 bit (thập phân hoặc 0x...), frame 22 bit; S lấy sau khi quay."
        )

    def load_example(self, event=None):
        if self.future is not None:
            return
        tiny = self.algorithm.get() == "TinyA5/1"
        self.key.set(TINY_KEY if tiny else A51_KEY)
        self.frame.set("0x134")
        self.update_algorithm()
        for mode, value in [
            ("bit", "111" if tiny else "0" * 114),
            ("text", "Xin chào Việt Nam!"),
        ]:
            self.inputs[mode].delete("1.0", "end")
            self.inputs[mode].insert("1.0", value)
            self.results[mode] = ""
            self.set_output(self.outputs[mode], "")
        self.set_output(self.trace, "")
        self.status.set(
            "Đã nạp ví dụ. Tiny: 111 → 011 → 111; A5/1: vector chuẩn với bản rõ toàn 0."
        )

    def run(self, mode, decrypt):
        algorithm, key, frame = self.algorithm.get(), self.key.get(), self.frame.get()
        data = self.inputs[mode].get("1.0", "end-1c")
        if mode == "text":
            self.submit(mode, process_text, algorithm, key, frame, data, decrypt)
            return
        try:
            # Bộ xử lý bit nhận A5/1 ở dạng nhị phân, ô thiết lập nhận số.
            if algorithm == "A5/1":
                key = format(parse_unsigned(key, 64, "Khóa A5/1"), "064b")
                frame = format(parse_unsigned(frame, 22, "Số khung"), "022b")
        except ValueError as error:
            messagebox.showerror("Lỗi dữ liệu / khóa", str(error), parent=self.root)
            return
        self.direction = "Bản rõ" if decrypt else "Bản mã"
        self.submit(mode, process_binary, algorithm, key, frame, data)

    def reuse(self, mode):
        if self.results[mode]:
            self.inputs[mode].delete("1.0", "end")
            self.inputs[mode].insert("1.0", self.results[mode])

    def run_file(self, decrypt):
        if self.future is not None:
            return
        source = filedialog.askopenfilename(
            parent=self.root,
            title="Chọn file để giải mã" if decrypt else "Chọn file để mã hóa",
        )
        if not source:
            return
        name = Path(source).name
        if decrypt:
            name = name[:-4] if name.lower().endswith(".a51") else name + ".restored"
            name = "khoi_phuc_" + name
        else:
            name += ".a51"
        target = filedialog.asksaveasfilename(
            parent=self.root,
            title="Chọn tên file đầu ra mới",
            initialfile=name,
            confirmoverwrite=False,
        )
        if target:
            self.submit(
                "file",
                process_file,
                self.algorithm.get(),
                self.key.get(),
                self.frame.get(),
                source,
                target,
            )

    def set_busy(self, busy):
        for button in self.buttons:
            button.configure(state="disabled" if busy else "normal")
        self.selector.configure(state="disabled" if busy else "readonly")
        self.key_entry.configure(state="disabled" if busy else "normal")
        if busy:
            self.frame_entry.configure(state="disabled")
        else:
            self.update_algorithm()

    def submit(self, kind, function, *args):
        if self.future is not None:
            return
        self.pending_kind = kind
        self.future = self.executor.submit(function, *args)
        self.set_busy(True)
        self.status.set("Đang xử lý…")
        self.root.after(50, self.poll)

    def poll(self):
        if not self.future.done():
            self.root.after(50, self.poll)
            return
        try:
            result = self.future.result()
            if self.pending_kind == "file":
                self.status.set(
                    f"Đã lưu file: {result} byte. Dùng đúng khóa để khôi phục dữ liệu."
                )
            else:
                mode = self.pending_kind
                if mode == "bit":
                    output, stream, rows = result
                    display = f"{self.direction}: {output}\nDòng khóa S: {stream}"
                    self.set_output(self.trace, format_trace(rows))
                else:
                    output = display = result
                self.results[mode] = output
                self.set_output(self.outputs[mode], display)
                self.status.set("Hoàn tất. Giữ nguyên thiết lập để giải mã.")
        except Exception as error:
            self.status.set("Xử lý thất bại. Kiểm tra dữ liệu và thiết lập khóa.")
            messagebox.showerror("Không thể xử lý", str(error), parent=self.root)
        finally:
            self.future = None
            self.set_busy(False)

    def close(self):
        if self.future is not None:
            messagebox.showinfo(
                "Đang xử lý",
                "Vui lòng chờ xử lý xong trước khi đóng.",
                parent=self.root,
            )
            return
        self.executor.shutdown(wait=False)
        self.root.destroy()
        
def main():
    root = tk.Tk()
    CipherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
