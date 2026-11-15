"""Vietnamese desktop interface. Launch from the project root: python run_gui.py."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from src.a51 import A51Cipher
from src.tiny_a51 import TinyA51
from ui.binary import process_binary, format_trace


def parse_unsigned(value: str, bits: int, label: str) -> int:
    try:
        text = value.strip()
        number = int(text, 16 if text.lower().startswith('0x') else 10)
    except ValueError as exc:
        raise ValueError(f'{label} phải là số thập phân hoặc hex bắt đầu bằng 0x.') from exc
    if not 0 <= number < (1 << bits):
        raise ValueError(f'{label} phải nằm trong khoảng 0 đến {hex((1 << bits) - 1)}.')
    return number


def make_cipher(algorithm: str, key: str, frame: str):
    if algorithm == 'TinyA5/1':
        return TinyA51(parse_unsigned(key, 32, 'Khóa TinyA5/1')).encrypt
    if algorithm != 'A5/1':
        raise ValueError('Thuật toán không hợp lệ.')
    number = parse_unsigned(key, 64, 'Khóa A5/1')
    # Display the key as eight big-endian bytes, load each byte LSB first.
    key_bits = [(byte >> bit) & 1 for byte in number.to_bytes(8, 'big') for bit in range(8)]
    cipher = A51Cipher(key_bits, parse_unsigned(frame, 22, 'Số khung'))
    return cipher.process_bytes


def process_text(algorithm: str, key: str, frame: str, text: str, decrypt: bool) -> str:
    operation = make_cipher(algorithm, key, frame)
    if decrypt:
        try:
            data = bytes.fromhex(text)
        except ValueError as exc:
            raise ValueError('Bản mã phải là chuỗi hex hợp lệ, ví dụ: 0a12ff.') from exc
        try:
            return operation(data).decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError('Không đọc được UTF-8. Kiểm tra khóa, thuật toán, số khung và bản mã; '
                             'với dữ liệu nhị phân hãy dùng mục File.') from exc
    return operation(text.encode('utf-8')).hex()


def process_file(algorithm: str, key: str, frame: str, source: str, target: str) -> int:
    operation = make_cipher(algorithm, key, frame)
    first, second = Path(source), Path(target)
    if first.resolve() == second.resolve() or (second.exists() and first.samefile(second)):
        raise ValueError('File đầu vào và đầu ra phải khác nhau.')
    # Exclusive creation avoids overwriting user data, including a race after the dialog.
    with first.open('rb') as input_file:
        with second.open('xb') as output_file:
            total = 0
            while chunk := input_file.read(65536):
                output_file.write(operation(chunk))
                total += len(chunk)
    return total


class CipherApp:
    def __init__(self, root):
        self.root = root
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.pending_kind = None
        self.root.title('A5/1 & TinyA5/1 — Nhóm 9')
        self.root.geometry('1040x850')
        self.root.minsize(740, 600)
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.algorithm = tk.StringVar(value='TinyA5/1')
        self.key = tk.StringVar(value='0x1A2B3C4D')
        self.frame = tk.StringVar(value='0x134')
        self.status = tk.StringVar(value='Sẵn sàng. Nhập văn bản rồi chọn Mã hóa.')
        self.hint = tk.StringVar()
        self.source = tk.StringVar()
        self.target = tk.StringVar()
        self.buttons = []
        container = ttk.Frame(root, padding=20)
        container.pack(fill='both', expand=True)
        ttk.Label(container, text='HỆ MÃ DÒNG A5/1 & TINYA5/1',
                  font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        ttk.Label(container, text='Nhị phân từng bước • Văn bản UTF-8 • File • Nhóm 9').pack(anchor='w', pady=(4, 16))
        settings = ttk.LabelFrame(container, text='Thiết lập khóa', padding=12)
        settings.pack(fill='x')
        ttk.Label(settings, text='Thuật toán').grid(row=0, column=0, sticky='w')
        combo = ttk.Combobox(settings, textvariable=self.algorithm,
                             values=('TinyA5/1', 'A5/1'), state='readonly', width=14)
        combo.grid(row=1, column=0, padx=(0, 16), pady=5)
        combo.bind('<<ComboboxSelected>>', self.update_algorithm)
        ttk.Label(settings, text='Khóa (thập phân hoặc 0x...)').grid(row=0, column=1, sticky='w')
        ttk.Entry(settings, textvariable=self.key, width=28).grid(row=1, column=1, sticky='ew', padx=(0, 16))
        ttk.Label(settings, text='Số khung (A5/1)').grid(row=0, column=2, sticky='w')
        self.frame_entry = ttk.Entry(settings, textvariable=self.frame, width=16)
        self.frame_entry.grid(row=1, column=2)
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, textvariable=self.hint, wraplength=800).grid(row=2, column=0, columnspan=3, sticky='w')
        tabs = ttk.Notebook(container)
        tabs.pack(fill='both', expand=True, pady=14)
        text_tab = ttk.Frame(tabs, padding=12)
        file_tab = ttk.Frame(tabs, padding=12)
        self.build_binary_tab(tabs)
        tabs.add(text_tab, text='  Văn bản  ')
        tabs.add(file_tab, text='  File  ')
        ttk.Label(text_tab, text='Đầu vào: văn bản UTF-8 để mã hóa / chuỗi hex để giải mã').pack(anchor='w')
        self.input = ScrolledText(text_tab, height=6, wrap='word', font=('Consolas', 11))
        self.input.pack(fill='both', expand=True, pady=6)
        self.input.insert('1.0', 'Xin chào! Đây là demo hệ mã dòng A5/1 — Nhóm 9.')
        actions = ttk.Frame(text_tab)
        actions.pack(fill='x', pady=5)
        self.button(actions, 'Mã hóa → Hex', lambda: self.run_text(False)).pack(side='left', padx=(0, 8))
        self.button(actions, 'Giải mã → Văn bản', lambda: self.run_text(True)).pack(side='left', padx=(0, 8))
        self.button(actions, 'Đưa kết quả lên đầu vào', self.reuse_result).pack(side='left')
        ttk.Label(text_tab, text='Kết quả').pack(anchor='w', pady=(8, 0))
        self.output = ScrolledText(text_tab, height=6, wrap='word', font=('Consolas', 11), state='disabled')
        self.output.pack(fill='both', expand=True, pady=6)
        self.button(text_tab, 'Sao chép kết quả', self.copy_result).pack(anchor='e')
        ttk.Label(file_tab, text='Chọn file bất kỳ: văn bản, ảnh hoặc dữ liệu nhị phân.').pack(anchor='w', pady=(0, 14))
        for label, variable, callback in [('File đầu vào', self.source, self.choose_source),
                                          ('File đầu ra mới', self.target, self.choose_target)]:
            ttk.Label(file_tab, text=label).pack(anchor='w')
            row = ttk.Frame(file_tab)
            row.pack(fill='x', pady=(5, 14))
            ttk.Entry(row, textvariable=variable).pack(side='left', fill='x', expand=True)
            self.button(row, 'Chọn…', callback).pack(side='left', padx=(8, 0))
        row = ttk.Frame(file_tab)
        row.pack(fill='x')
        self.button(row, 'Mã hóa file', lambda: self.run_file(False)).pack(side='left', padx=(0, 8))
        self.button(row, 'Giải mã file', lambda: self.run_file(True)).pack(side='left')
        ttk.Label(file_tab, text='Giải mã bằng đúng thuật toán, khóa và số khung lúc mã hóa.\n'
                  'File mã hóa là dữ liệu nhị phân; chương trình không ghi đè file đã có.',
                  wraplength=750).pack(anchor='w', pady=20)
        ttk.Label(container, textvariable=self.status, wraplength=850).pack(anchor='w')
        ttk.Label(container, text='Chỉ dùng cho học tập. Các hệ mã này không xác thực dữ liệu; '
                  'khóa sai có thể không được phát hiện.', wraplength=850).pack(anchor='w', pady=(8, 0))
        self.update_algorithm()

    def build_binary_tab(self, tabs):
        tab = ttk.Frame(tabs, padding=12)
        tabs.add(tab, text='  Nhị phân / Tính tay  ')
        self.binary_algorithm = tk.StringVar(value='TinyA5/1')
        self.binary_key = tk.StringVar(value='10110001010110110010101')
        self.binary_frame = tk.StringVar(value=format(0x134, '022b'))
        self.binary_result = ''
        self.binary_hint = tk.StringVar()
        row = ttk.Frame(tab)
        row.pack(fill='x')
        ttk.Label(row, text='Thuật toán').pack(side='left', padx=(0, 8))
        combo = ttk.Combobox(row, textvariable=self.binary_algorithm,
                             values=('TinyA5/1', 'A5/1'), state='readonly', width=16)
        combo.pack(side='left')
        combo.bind('<<ComboboxSelected>>', self.update_binary_algorithm)
        self.button(row, 'Nạp ví dụ', self.load_binary_example).pack(side='left', padx=10)
        ttk.Label(tab, textvariable=self.binary_hint, wraplength=900).pack(anchor='w', pady=6)
        ttk.Label(tab, text='Khóa nhị phân: Tiny 23 bit / A5/1 64 bit').pack(anchor='w')
        ttk.Entry(tab, textvariable=self.binary_key).pack(fill='x', pady=4)
        ttk.Label(tab, text='Số khung nhị phân 22 bit (chỉ A5/1)').pack(anchor='w')
        self.binary_frame_entry = ttk.Entry(tab, textvariable=self.binary_frame)
        self.binary_frame_entry.pack(fill='x', pady=4)
        ttk.Label(tab, text='Đầu vào: chuỗi bit 0/1 (tối đa 4096 bit)').pack(anchor='w')
        self.binary_input = ScrolledText(tab, height=3, wrap='word', font=('Consolas', 10))
        self.binary_input.pack(fill='x', pady=4)
        self.binary_input.insert('1.0', '1011')
        row = ttk.Frame(tab)
        row.pack(fill='x', pady=5)
        self.button(row, 'Mã hóa bit', lambda: self.run_binary(False)).pack(side='left', padx=(0, 8))
        self.button(row, 'Giải mã bit', lambda: self.run_binary(True)).pack(side='left', padx=(0, 8))
        self.button(row, 'Đưa bản mã lên đầu vào', self.reuse_binary).pack(side='left')
        self.binary_output = ScrolledText(tab, height=4, wrap='word', font=('Consolas', 10), state='disabled')
        self.binary_output.pack(fill='x', pady=4)
        ttk.Label(tab, text='Các bước trung gian: trạng thái trước → sau, majority và dòng khóa S').pack(anchor='w')
        self.binary_trace = ScrolledText(tab, height=8, wrap='none', font=('Consolas', 10), state='disabled')
        self.binary_trace.pack(fill='both', expand=True, pady=4)
        self.update_binary_algorithm()

    def update_binary_algorithm(self, event=None):
        tiny = self.binary_algorithm.get() == 'TinyA5/1'
        self.binary_frame_entry.configure(state='disabled' if tiny else 'normal')
        self.binary_hint.set('Tiny 6/8/9 bit: khóa = R1 || R2 || R3 (index 0 trước); lấy S trước khi quay. '
                             'Chưa xác nhận biến thể của lớp.' if tiny else
                             'A5/1 19/22/23 bit: nạp khóa và frame, quay khởi động 100 lần; bảng bắt đầu khi sinh S.')

    def load_binary_example(self):
        tiny = self.binary_algorithm.get() == 'TinyA5/1'
        self.binary_key.set('10110001010110110010101' if tiny else format(0x1223456789ABCDEF, '064b'))
        self.binary_frame.set(format(0x134, '022b'))
        self.binary_input.delete('1.0', 'end')
        self.binary_input.insert('1.0', '1011' if tiny else '0' * 114)
        self.binary_result = ''
        self.update_binary_algorithm()
        self.status.set('Đã nạp ví dụ: Tiny S=1001, kết quả=0010; A5/1 là vector chuẩn với bản rõ toàn 0.')

    def run_binary(self, decrypt):
        self.binary_direction = 'Bản rõ khôi phục' if decrypt else 'Bản mã'
        self.submit('binary', process_binary, self.binary_algorithm.get(), self.binary_key.get(),
                    self.binary_frame.get(), self.binary_input.get('1.0', 'end-1c'))

    def reuse_binary(self):
        if self.binary_result:
            self.binary_input.delete('1.0', 'end')
            self.binary_input.insert('1.0', self.binary_result)

    def button(self, parent, label, command):
        button = ttk.Button(parent, text=label, command=command)
        self.buttons.append(button)
        return button

    def update_algorithm(self, event=None):
        full = self.algorithm.get() == 'A5/1'
        self.frame_entry.configure(state='normal' if full else 'disabled')
        self.hint.set('A5/1: khóa 64 bit (8 byte), số khung 22 bit.' if full else
                      'TinyA5/1: khóa 32 bit, biến thể minh họa thanh ghi 6/8/9 bit.')

    def submit(self, kind, function, *args):
        if self.future is not None:
            return
        self.pending_kind = kind
        self.future = self.executor.submit(function, *args)
        for button in self.buttons:
            button.configure(state='disabled')
        self.status.set('Đang xử lý…')
        self.root.after(50, self.poll)

    def poll(self):
        if not self.future.done():
            self.root.after(50, self.poll)
            return
        try:
            result = self.future.result()
            if self.pending_kind == 'binary':
                output, stream, rows = result
                self.binary_result = output
                for widget, content in ((self.binary_output, f'{self.binary_direction}: {output}\nDòng khóa S: {stream}'),
                                        (self.binary_trace, format_trace(rows))):
                    widget.configure(state='normal')
                    widget.delete('1.0', 'end')
                    widget.insert('1.0', content)
                    widget.configure(state='disabled')
                self.status.set(f'Hoàn tất {len(output)} bit. Dùng cùng khóa để giải mã.')
            elif self.pending_kind == 'text':
                self.output.configure(state='normal')
                self.output.delete('1.0', 'end')
                self.output.insert('1.0', result)
                self.output.configure(state='disabled')
                self.status.set('Hoàn tất. Có thể đưa kết quả lên đầu vào để thử chiều ngược lại.')
            else:
                self.status.set(f'Đã lưu file: {result} byte. Dùng đúng khóa để khôi phục dữ liệu.')
        except Exception as exc:
            self.status.set('Xử lý thất bại. Kiểm tra dữ liệu và thiết lập khóa.')
            messagebox.showerror('Không thể xử lý', str(exc), parent=self.root)
        finally:
            self.future = None
            for button in self.buttons:
                button.configure(state='normal')

    def run_text(self, decrypt):
        self.submit('text', process_text, self.algorithm.get(), self.key.get(), self.frame.get(),
                    self.input.get('1.0', 'end-1c'), decrypt)

    def run_file(self, decrypt):
        if not self.source.get().strip() or not self.target.get().strip():
            messagebox.showerror('Thiếu file', 'Hãy chọn file đầu vào và đầu ra.', parent=self.root)
            return
        self.submit('file', process_file, self.algorithm.get(), self.key.get(), self.frame.get(),
                    self.source.get(), self.target.get())

    def choose_source(self):
        path = filedialog.askopenfilename(parent=self.root, title='Chọn file đầu vào')
        if path:
            self.source.set(path)

    def choose_target(self):
        path = filedialog.asksaveasfilename(parent=self.root, title='Chọn tên file đầu ra mới')
        if path:
            self.target.set(path)

    def reuse_result(self):
        self.input.delete('1.0', 'end')
        self.input.insert('1.0', self.output.get('1.0', 'end-1c'))

    def copy_result(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.output.get('1.0', 'end-1c'))
        self.status.set('Đã sao chép kết quả.')

    def close(self):
        if self.future is not None:
            messagebox.showinfo('Đang xử lý', 'Vui lòng chờ xử lý xong trước khi đóng.', parent=self.root)
            return
        self.executor.shutdown(wait=False)
        self.root.destroy()


def main():
    root = tk.Tk()
    CipherApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
