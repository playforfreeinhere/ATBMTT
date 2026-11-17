"""GIAO DIỆN TKINTER HAI TAB — chỉ điều phối nhập/xuất và tác vụ nền.

Khởi chạy bằng `py run_gui.py`, không chạy trực tiếp file nằm trong ui/.
Tab bit = Nhị phân/Tính tay; tab text = Văn bản/File. algorithm, key,
frame là StringVar dùng chung cho cả hai tab. inputs/outputs lưu widget;
results lưu kết quả thuần để đưa ngược lên ô nhập, không kèm nhãn hay log.

Luồng bấm nút: run/run_file → submit → worker xử lý → poll nhận kết quả
→ cập nhật widget. ThreadPoolExecutor chạy việc nặng ngoài luồng giao diện;
root.after lên lịch kiểm tra kết quả trên luồng chính để Tkinter không đơ.
Không gọi hàm sửa widget bên trong worker. Khi đang chạy, khóa các nút và
ô thiết lập để tránh thao tác chồng chéo. Thuật toán nằm trong src/, còn
UTF-8, khóa và file được xử lý bởi operations.py hoặc binary.py.
TINY_KEY và A51_KEY chỉ là khóa ví dụ, không tự sinh khóa cho người dùng.
"""

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
    """Quản lý một cửa sổ và một worker xử lý dữ liệu.

    Mọi widget và StringVar thuộc đối tượng này; thuật toán được gọi qua
    các hàm bên ngoài, không cài đặt lại trong lớp giao diện.
    """

    def __init__(self, root):
        """Tạo trạng thái ứng dụng, thiết lập cửa sổ và xây dựng hai tab.

        root là cửa sổ Tk đã tạo bên ngoài. executor có tối đa một luồng worker;
        future=None nghĩa là đang rảnh. pending_kind cho biết kết quả thuộc tab nào.
        inputs/outputs ánh xạ "bit"/"text" tới ô nhập/kết quả; results giữ chuỗi thuần.
        StringVar liên kết biến Python với widget; set() thay giá trị hiển thị,
        get() đọc giá trị hiện tại. protocol gắn nút đóng cửa sổ với close().
        load_example nạp mẫu; tabs.select(1) mở tab thứ hai Văn bản/File lúc đầu.
        """
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
        """Tạo hàng thiết lập thuật toán, khóa, frame và nút nạp ví dụ.

        Combobox readonly chỉ cho chọn hai tên có sẵn. bind liên kết sự kiện
        đổi lựa chọn với load_example; command ở Button là hàm gọi khi bấm nút.
        pack(side="left") xếp các thành phần trên cùng hàng từ trái sang phải.
        """
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
        """Dùng chung một hàm để tạo tab bit hoặc text, tránh lặp toàn bộ bố cục.

        mode quyết định nhãn, ô lịch sử và nút file; title là tên tab. lambda tạo
        hàm chưa chạy ngay, nhớ mode và chỉ gọi run/reuse khi người dùng bấm nút.
        Hai tab có ô nhập, ba nút xử lý, ô kết quả. Tab bit thêm trace; tab text
        thêm hai hộp thoại file. fill="both", expand=True cho phép ô giãn theo cửa sổ.
        """
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
        """Tạo nút, lưu vào self.buttons và trả widget để bên gọi bố trí bằng pack.

        Danh sách chung cho phép khóa/mở tất cả nút khi tác vụ nền bắt đầu/kết thúc.
        """
        button = ttk.Button(parent, text=label, command=command)
        self.buttons.append(button)
        return button

    @staticmethod
    def textbox(parent, readonly=False, height=4, wrap="word"):
        """Tạo ô nhiều dòng có thanh cuộn, trả widget ScrolledText.

        readonly=True làm ô bị disabled để không gõ sửa kết quả. height là số dòng
        ước lượng; wrap="word" xuống dòng theo từ, "none" giữ nguyên dòng lịch sử.
        @staticmethod nghĩa là hàm tiện ích này không dùng self.
        """
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
        """Thay toàn bộ nội dung ô kết quả rồi khóa nhập trở lại.

        Tkinter Text dùng "1.0" = dòng 1 cột 0, "end" = cuối ô. Widget disabled
        không cho insert/delete nên phải chuyển normal trước, disabled sau.
        """
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def update_algorithm(self):
        """Bật ô frame cho A5/1, tắt cho Tiny và cập nhật nhắc quy tắc.

        Hàm này không tự đổi khóa hoặc chạy mã hóa; load_example mới nạp khóa mẫu.
        """
        tiny = self.algorithm.get() == "TinyA5/1"
        self.frame_entry.configure(state="disabled" if tiny else "normal")
        self.hint.set(
            "Tiny 6/8/9 bit: khóa 23 bit = R1 || R2 || R3; clock 1/3/3; S lấy sau khi quay."
            if tiny
            else "A5/1 19/22/23 bit: khóa 64 bit (thập phân hoặc 0x...), frame 22 bit; S lấy sau khi quay."
        )

    def load_example(self, event=None):
        """Nạp mẫu đúng thuật toán vào cả hai tab và xóa kết quả/lịch sử cũ.

        event=None để dùng được cả callback Combobox (có event) và Button (không có).
        Nếu future đang tồn tại thì không nạp đè. Tiny dùng 111, A5/1 dùng 114 bit 0
        để đối chiếu vector. Key/frame/ô nhập đều được reset, không giữ mẫu người dùng.
        """
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
        """Đọc dữ liệu hiện tại rồi gửi một tác vụ text hoặc bit cho worker.

        mode xác định tab; decrypt chỉ hướng mã hóa/giải mã và nhãn kết quả.
        get("1.0","end-1c") bỏ ký tự xuống dòng cuối mà Tkinter Text tự thêm.
        Tab text chuyển thẳng cho process_text. Tab bit chuyển khóa số A5/1 thành
        64 bit, frame thành 22 bit có đủ số 0 đầu. Tiny đã là chuỗi 23 bit.
        Hai chiều bit đều dùng cùng process_binary vì XOR đối xứng; direction
        chỉ quyết định nhãn "Bản rõ" hay "Bản mã" khi poll hiển thị.
        """
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
        """Lấy chuỗi kết quả thuần của tab và đưa về ô nhập để thử chiều ngược lại.

        Không sao chép nhãn, dòng S hay bảng trạng thái; giữ nguyên khóa và frame.
        Kết quả rỗng thì không sửa ô nhập.
        """
        if self.results[mode]:
            self.inputs[mode].delete("1.0", "end")
            self.inputs[mode].insert("1.0", self.results[mode])

    def run_file(self, decrypt):
        """Mở hộp chọn đầu vào/đầu ra rồi gửi process_file sang worker.

        Hủy hộp thoại trả chuỗi rỗng và dừng thao tác. Khi mã hóa, tên gợi ý thêm
        .a51; khi giải mã, bỏ .a51 nếu có và thêm khoi_phuc_. Chỉ đổi tên không
        làm giải mã: dữ liệu phải thật sự qua process_file với đúng thiết lập.
        confirmoverwrite=False bỏ câu hỏi ghi đè ở hộp thoại; process_file vẫn
        mở xb nên file đã tồn tại sẽ bị từ chối, không bị thay thế.
        """
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
        """Khóa các nút, khóa thuật toán/khóa/frame khi worker đang chạy.

        Khi xong, khôi phục Combobox readonly và dùng update_algorithm để frame
        chỉ mở nếu là A5/1. Hàm được gọi trên luồng chính, không ở worker.
        """
        for button in self.buttons:
            button.configure(state="disabled" if busy else "normal")
        self.selector.configure(state="disabled" if busy else "readonly")
        self.key_entry.configure(state="disabled" if busy else "normal")
        if busy:
            self.frame_entry.configure(state="disabled")
        else:
            self.update_algorithm()

    def submit(self, kind, function, *args):
        """Gửi function(*args) vào executor và lên lịch poll sau 50 mili giây.

        *args gom các tham số vị trí cần chuyển cho hàm xử lý. future giữ tác vụ
        đã gửi, có thể lấy kết quả/lỗi về sau. Nếu đang có future thì bỏ yêu cầu mới.
        Không gọi result() ngay tại đây vì sẽ chặn cửa sổ cho tới khi xử lý xong.
        """
        if self.future is not None:
            return
        self.pending_kind = kind
        self.future = self.executor.submit(function, *args)
        self.set_busy(True)
        self.status.set("Đang xử lý…")
        self.root.after(50, self.poll)

    def poll(self):
        """Kiểm tra worker đã xong và hiển thị kết quả trên luồng Tkinter.

        future.done() chưa xong thì after(50, poll) hẹn lần kiểm tra tiếp, không đệ
        quy đồng bộ. future.result() trả dữ liệu hoặc ném lại lỗi từ worker.
        file trả số byte; bit trả (output, stream, rows); text trả một chuỗi.
        results chỉ giữ output thuần, display có thể thêm nhãn/dòng S để người đọc.
        except hiển thị lỗi; finally luôn xóa future và mở lại điều khiển,
        kể cả khi tác vụ thất bại. Không sửa hoặc xóa dữ liệu đầu vào ở đây.
        """
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
        """Chỉ đóng khi worker đã được thu kết quả và future trở về None.

        Nếu còn tác vụ thì nhắc chờ. shutdown(wait=False) dừng nhận việc mới;
        root.destroy() hủy cửa sổ, làm vòng mainloop kết thúc.
        """
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
    """Tạo cửa sổ gốc, gắn CipherApp và chạy vòng sự kiện mainloop.

    Tk() tạo môi trường GUI; mainloop lắng nghe bấm nút, gõ và callback after
    cho tới khi đóng. Import ui.gui không tự chạy hàm này.
    """
    root = tk.Tk()
    CipherApp(root)
    root.mainloop()


# Khối dưới chỉ chạy khi thực thi file/module trực tiếp, không chạy khi import.
if __name__ == "__main__":
    main()
