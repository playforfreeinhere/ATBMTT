"""ĐIỂM KHỞI CHẠY GIAO DIỆN — chạy: py run_gui.py.

File này chỉ gọi main() trong ui/gui.py, không chứa thuật toán mã hóa.
Luồng chương trình: run_gui → ui.gui → ui.operations/ui.binary → src.
Lệnh import nạp hàm main; hàm chỉ chạy khi file được thực thi trực tiếp
nhờ điều kiện __name__ == "__main__". Vì vậy import file không tự mở cửa sổ.
Tkinter có sẵn trong nhiều bộ cài Python; trên Windows cần thành phần Tcl/Tk.
"""

from ui.gui import main

# Khối dưới chỉ chạy khi thực thi file/module trực tiếp, không chạy khi import.
if __name__ == "__main__":
    main()
