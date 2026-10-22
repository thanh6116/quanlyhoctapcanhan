"""
Chức năng chính:
  1. Quản lý danh sách môn học
  2. Thời khóa biểu (lịch học theo tuần)
  3. Lịch thi
  4. Quản lý bài tập / deadline (có cảnh báo sắp đến hạn)
  5. Ghi chú bài giảng quan trọng
  6. Thống kê tổng quan (số môn, số bài tập còn hạn, biểu đồ)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date

from database import Database, mo_ta_gio_tiet

DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
PRIORITIES = ["Thấp", "Trung bình", "Cao", "Khẩn cấp"]
STATUSES = ["Chưa hoàn thành", "Đang làm", "Hoàn thành"]

class QLHTApp(tk.Tk):
    """Cửa sổ chính của ứng dụng."""
    def __init__(self):
        super().__init__()
        self.title("Phần mềm quản lí học tập cá nhân ")
        self.geometry("1000x650")
        self.minsize(900, 600)

        self.db = Database()

        self._build_style()
        self._build_layout()
        self.refresh_all()

    # ------------------------------------------------------------------
    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=5)
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Card.TLabel", font=("Segoe UI", 22, "bold"))

    def _build_layout(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_dashboard = ttk.Frame(notebook)
        self.tab_monhoc = ttk.Frame(notebook)
        self.tab_tkb = ttk.Frame(notebook)
        self.tab_lichthi = ttk.Frame(notebook)
        self.tab_baitap = ttk.Frame(notebook)
        self.tab_ghichu = ttk.Frame(notebook)

        notebook.add(self.tab_dashboard, text="  Tổng quan  ")
        notebook.add(self.tab_monhoc, text="  Môn học  ")
        notebook.add(self.tab_tkb, text="  Thời khóa biểu  ")
        notebook.add(self.tab_lichthi, text="  Lịch thi  ")
        notebook.add(self.tab_baitap, text="  Bài tập / Deadline  ")
        notebook.add(self.tab_ghichu, text="  Ghi chú  ")

        self._build_tab_dashboard()
        self._build_tab_monhoc()
        self._build_tab_tkb()
        self._build_tab_lichthi()
        self._build_tab_baitap()
        self._build_tab_ghichu()

    # ================= TAB TỔNG QUAN =================
    def _build_tab_dashboard(self):
        frame = self.tab_dashboard
        ttk.Label(frame, text="Tổng quan học tập", style="Header.TLabel").pack(
            anchor="w", padx=15, pady=10
        )

        cards_frame = ttk.Frame(frame)
        cards_frame.pack(fill="x", padx=15, pady=5)

        self.card_mon = self._make_card(cards_frame, "Số môn học", "0")
        self.card_baitap = self._make_card(cards_frame, "Bài tập chưa xong", "0")
        self.card_thi = self._make_card(cards_frame, "Lịch thi sắp tới", "0")
        self.card_ghichu = self._make_card(cards_frame, "Ghi chú", "0")

        ttk.Label(frame, text="⏰ Deadline gần nhất (7 ngày tới)", style="Header.TLabel").pack(
            anchor="w", padx=15, pady=(20, 5)
        )

        cols = ("mon", "tieu_de", "han_nop", "uu_tien")
        self.tree_deadline = ttk.Treeview(frame, columns=cols, show="headings", height=8)
        for c, t, w in zip(
            cols, ["Môn học", "Tiêu đề", "Hạn nộp", "Ưu tiên"], [180, 300, 150, 100]
        ):
            self.tree_deadline.heading(c, text=t)
            self.tree_deadline.column(c, width=w, anchor="w")
        self.tree_deadline.pack(fill="both", expand=True, padx=15, pady=5)

        ttk.Button(frame, text="Làm mới", command=self.refresh_all).pack(
            anchor="e", padx=15, pady=10
        )

    def _make_card(self, parent, title, value):
        card = ttk.Frame(parent, relief="groove", padding=15)
        card.pack(side="left", fill="both", expand=True, padx=5)
        lbl_value = ttk.Label(card, text=value, style="Card.TLabel")
        lbl_value.pack()
        ttk.Label(card, text=title).pack()
        return lbl_value

    # ================= TAB MÔN HỌC =================
    def _build_tab_monhoc(self):
        frame = self.tab_monhoc
        form = ttk.LabelFrame(frame, text="Thêm môn học mới", padding=10)
        form.pack(fill="x", padx=15, pady=10)

        ttk.Label(form, text="Tên môn học:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.mh_ten = ttk.Entry(form, width=30)
        self.mh_ten.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Số tín chỉ:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.mh_tinchi = ttk.Spinbox(form, from_=1, to=10, width=10)
        self.mh_tinchi.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Giảng viên:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.mh_gv = ttk.Entry(form, width=30)
        self.mh_gv.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Ghi chú:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.mh_ghichu = ttk.Entry(form, width=30)
        self.mh_ghichu.grid(row=1, column=3, padx=5, pady=5)

        ttk.Button(form, text="Thêm môn học", command=self.them_mon_hoc).grid(
            row=2, column=0, columnspan=4, pady=10
        )

        search_frame = ttk.Frame(frame)
        search_frame.pack(fill="x", padx=15)
        ttk.Label(search_frame, text="🔍 Tìm môn học theo tên:").pack(side="left", padx=5)
        self.mh_timkiem = ttk.Entry(search_frame, width=30)
        self.mh_timkiem.pack(side="left", padx=5)
        self.mh_timkiem.bind("<KeyRelease>", lambda e: self.refresh_monhoc())
        ttk.Button(
            search_frame, text="Xóa tìm kiếm", command=self.xoa_tim_kiem_mon_hoc
        ).pack(side="left", padx=5)

        list_frame = ttk.LabelFrame(frame, text="Danh sách môn học", padding=10)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("id", "ten", "tinchi", "gv", "ghichu")
        self.tree_monhoc = ttk.Treeview(list_frame, columns=cols, show="headings")
        headers = ["ID", "Tên môn", "Tín chỉ", "Giảng viên", "Ghi chú"]
        widths = [40, 220, 70, 180, 200]
        for c, h, w in zip(cols, headers, widths):
            self.tree_monhoc.heading(c, text=h)
            self.tree_monhoc.column(c, width=w, anchor="w")
        self.tree_monhoc.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_monhoc.yview)
        self.tree_monhoc.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", padx=15, pady=(0, 10))
        ttk.Button(btn_frame, text="Xóa môn học đã chọn", command=self.xoa_mon_hoc).pack(
            side="right", padx=5
        )
        ttk.Button(btn_frame, text="Sửa môn học đã chọn", command=self.sua_mon_hoc).pack(
            side="right", padx=5
        )
        # Nhấp đúp vào một dòng để sửa nhanh
        self.tree_monhoc.bind("<Double-1>", lambda e: self.sua_mon_hoc())

    def them_mon_hoc(self):
        ten = self.mh_ten.get().strip()
        if not ten:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập tên môn học.")
            return
        try:
            tinchi = int(self.mh_tinchi.get())
        except ValueError:
            tinchi = 0
        gv = self.mh_gv.get().strip()
        ghichu = self.mh_ghichu.get().strip()

        self.db.them_mon_hoc(ten, tinchi, gv, ghichu)
        self.mh_ten.delete(0, tk.END)
        self.mh_gv.delete(0, tk.END)
        self.mh_ghichu.delete(0, tk.END)
        self.refresh_all()
        messagebox.showinfo("Thành công", f"Đã thêm môn học '{ten}'.")

    def xoa_mon_hoc(self):
        selected = self.tree_monhoc.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn môn học cần xóa.")
            return
        item = self.tree_monhoc.item(selected[0])
        mon_id, ten = item["values"][0], item["values"][1]
        if messagebox.askyesno(
            "Xác nhận",
            f"Xóa môn học '{ten}'?\n(Lịch học và lịch thi liên quan sẽ bị xóa; "
            f"bài tập và ghi chú sẽ được giữ lại nhưng không gắn môn)",
        ):
            self.db.xoa_mon_hoc(mon_id)
            self.refresh_all()

    def refresh_monhoc(self):
        for row in self.tree_monhoc.get_children():
            self.tree_monhoc.delete(row)
        tu_khoa = self.mh_timkiem.get() if hasattr(self, "mh_timkiem") else ""
        for mh in self.db.tim_kiem_mon_hoc(tu_khoa):
            self.tree_monhoc.insert("", "end", values=mh)
        self._refresh_mon_hoc_comboboxes()

    def xoa_tim_kiem_mon_hoc(self):
        self.mh_timkiem.delete(0, tk.END)
        self.refresh_monhoc()

    def sua_mon_hoc(self):
        """Mở cửa sổ chỉnh sửa môn học đang chọn."""
        selected = self.tree_monhoc.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn môn học cần sửa.")
            return
        mon_id = self.tree_monhoc.item(selected[0])["values"][0]
        mon = self.db.lay_mon_hoc(mon_id)
        if not mon:
            messagebox.showerror("Lỗi", "Không tìm thấy môn học này.")
            self.refresh_all()
            return
        _, ten, tinchi, gv, ghichu = mon

        win = tk.Toplevel(self)
        win.title("Sửa môn học")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        form = ttk.Frame(win, padding=15)
        form.pack(fill="both", expand=True)

        ttk.Label(form, text="Tên môn học:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        e_ten = ttk.Entry(form, width=30)
        e_ten.insert(0, ten or "")
        e_ten.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Số tín chỉ:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        e_tc = ttk.Spinbox(form, from_=1, to=10, width=10)
        e_tc.set(str(tinchi if tinchi is not None else 1))
        e_tc.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form, text="Giảng viên:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        e_gv = ttk.Entry(form, width=30)
        e_gv.insert(0, gv or "")
        e_gv.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(form, text="Ghi chú:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        e_gc = ttk.Entry(form, width=30)
        e_gc.insert(0, ghichu or "")
        e_gc.grid(row=3, column=1, padx=5, pady=5)

        def luu():
            ten_moi = e_ten.get().strip()
            if not ten_moi:
                messagebox.showwarning(
                    "Thiếu dữ liệu", "Vui lòng nhập tên môn học.", parent=win
                )
                return
            try:
                tinchi_moi = int(e_tc.get())
            except ValueError:
                tinchi_moi = 0
            self.db.sua_mon_hoc(
                mon_id, ten_moi, tinchi_moi, e_gv.get().strip(), e_gc.get().strip()
            )
            win.destroy()
            self.refresh_all()
            messagebox.showinfo("Thành công", f"Đã cập nhật môn học '{ten_moi}'.")

        btns = ttk.Frame(form)
        btns.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btns, text="Lưu thay đổi", command=luu).pack(side="left", padx=5)
        ttk.Button(btns, text="Hủy", command=win.destroy).pack(side="left", padx=5)

        e_ten.focus_set()
        win.bind("<Return>", lambda e: luu())
        win.bind("<Escape>", lambda e: win.destroy())

    def _refresh_mon_hoc_comboboxes(self):
        mon_list = self.db.lay_danh_sach_mon_hoc()
        names = [f"{m[0]} - {m[1]}" for m in mon_list]
        for combo in [self.tkb_mon, self.thi_mon, self.bt_mon, self.gc_mon]:
            combo["values"] = names

    # ================= TAB THỜI KHÓA BIỂU =================
    def _build_tab_tkb(self):
        frame = self.tab_tkb
        form = ttk.LabelFrame(frame, text="Thêm lịch học", padding=10)
        form.pack(fill="x", padx=15, pady=10)

        ttk.Label(form, text="Môn học:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.tkb_mon = ttk.Combobox(form, width=27, state="readonly")
        self.tkb_mon.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Thứ:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.tkb_thu = ttk.Combobox(form, values=DAYS, width=12, state="readonly")
        self.tkb_thu.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Tiết bắt đầu:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.tkb_bd = ttk.Spinbox(form, from_=1, to=12, width=10)
        self.tkb_bd.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(form, text="Tiết kết thúc:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.tkb_kt = ttk.Spinbox(form, from_=1, to=12, width=10)
        self.tkb_kt.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        ttk.Label(form, text="Phòng học:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.tkb_phong = ttk.Entry(form, width=30)
        self.tkb_phong.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(form, text="Thêm vào TKB", command=self.them_lich_hoc).grid(
            row=2, column=3, pady=5
        )

        list_frame = ttk.LabelFrame(frame, text="Thời khóa biểu trong tuần (dòng đỏ: trùng lịch học)", padding=10)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("id", "mon", "thu", "bd", "kt", "phong")
        self.tree_tkb = ttk.Treeview(list_frame, columns=cols, show="headings")
        headers = ["ID", "Môn học", "Thứ", "Tiết BĐ", "Tiết KT", "Phòng"]
        widths = [40, 220, 90, 70, 70, 150]
        for c, h, w in zip(cols, headers, widths):
            self.tree_tkb.heading(c, text=h)
            self.tree_tkb.column(c, width=w, anchor="w")
        self.tree_tkb.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_tkb.yview)
        self.tree_tkb.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(frame, text="Xóa lịch học đã chọn", command=self.xoa_lich_hoc).pack(
            anchor="e", padx=15, pady=(0, 10)
        )

    def them_lich_hoc(self):
        mon = self.tkb_mon.get()
        thu = self.tkb_thu.get()
        if not mon or not thu:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng chọn môn học và thứ.")
            return
        mon_id = int(mon.split(" - ")[0])
        try:
            bd = int(self.tkb_bd.get())
            kt = int(self.tkb_kt.get())
        except ValueError:
            messagebox.showwarning("Lỗi", "Tiết học phải là số.")
            return
        if kt < bd:
            messagebox.showwarning("Lỗi", "Tiết kết thúc phải >= tiết bắt đầu.")
            return
        phong = self.tkb_phong.get().strip()

        trung = self.db.tim_xung_dot_lich_hoc(thu, bd, kt)
        if trung:
            ds = "\n".join(self._mo_ta_lich_hoc(r) for r in trung)
            if not messagebox.askyesno(
                "⚠ Cảnh báo trùng lịch học",
                f"Lịch học mới ({thu}, tiết {bd}-{kt}) bị TRÙNG với:\n{ds}"
                "\n\nBạn vẫn muốn thêm?",
                icon="warning",
            ):
                return

        self.db.them_lich_hoc(mon_id, thu, bd, kt, phong)
        self.tkb_phong.delete(0, tk.END)
        self.refresh_tkb()
        self.refresh_lichthi()

    def xoa_lich_hoc(self):
        selected = self.tree_tkb.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn dòng cần xóa.")
            return
        item = self.tree_tkb.item(selected[0])
        self.db.xoa_lich_hoc(item["values"][0])
        self.refresh_tkb()
        self.refresh_lichthi()

    def refresh_tkb(self):
        for row in self.tree_tkb.get_children():
            self.tree_tkb.delete(row)
        self.tree_tkb.tag_configure("conflict", foreground="#c62828", background="#ffebee")
        xung_dot = self.db.lay_id_lich_hoc_xung_dot()
        for lh in self.db.lay_thoi_khoa_bieu():
            tags = ("conflict",) if lh[0] in xung_dot else ()
            self.tree_tkb.insert("", "end", values=lh, tags=tags)

    @staticmethod
    def _mo_ta_lich_hoc(r):
        gio = mo_ta_gio_tiet(r[3], r[4])
        return f"  • {r[1]} ({r[2]}, tiết {r[3]}-{r[4]}, {gio}, phòng {r[5] or '—'})"

    @staticmethod
    def _mo_ta_lich_thi(r):
        return f"  • {r[1]} (ngày {r[2]}, giờ {r[3] or 'chưa rõ'}, phòng {r[4] or '—'})"

    # ================= TAB LỊCH THI =================
    def _build_tab_lichthi(self):
        frame = self.tab_lichthi
        form = ttk.LabelFrame(frame, text="Thêm lịch thi", padding=10)
        form.pack(fill="x", padx=15, pady=10)

        ttk.Label(form, text="Môn học:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.thi_mon = ttk.Combobox(form, width=27, state="readonly")
        self.thi_mon.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Ngày thi (dd/mm/yyyy):").grid(
            row=0, column=2, sticky="w", padx=5, pady=5
        )
        self.thi_ngay = ttk.Entry(form, width=15)
        self.thi_ngay.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Giờ thi:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.thi_gio = ttk.Entry(form, width=27)
        self.thi_gio.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Phòng thi:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.thi_phong = ttk.Entry(form, width=15)
        self.thi_phong.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(form, text="Hình thức:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.thi_hinhthuc = ttk.Combobox(
            form, values=["Tự luận", "Trắc nghiệm", "Vấn đáp", "Thực hành", "Tiểu luận"], width=27
        )
        self.thi_hinhthuc.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(form, text="Thêm lịch thi", command=self.them_lich_thi).grid(
            row=2, column=3, pady=5
        )

        list_frame = ttk.LabelFrame(frame, text="Danh sách lịch thi (đỏ: trùng lịch thi hoặc trùng giờ học; cam: cùng ngày có lịch học, chưa rõ giờ thi)", padding=10)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("id", "mon", "ngay", "gio", "phong", "hinhthuc")
        self.tree_thi = ttk.Treeview(list_frame, columns=cols, show="headings")
        headers = ["ID", "Môn học", "Ngày thi", "Giờ thi", "Phòng thi", "Hình thức"]
        widths = [40, 200, 100, 100, 100, 120]
        for c, h, w in zip(cols, headers, widths):
            self.tree_thi.heading(c, text=h)
            self.tree_thi.column(c, width=w, anchor="w")
        self.tree_thi.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_thi.yview)
        self.tree_thi.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(frame, text="Xóa lịch thi đã chọn", command=self.xoa_lich_thi).pack(
            anchor="e", padx=15, pady=(0, 10)
        )

    def them_lich_thi(self):
        mon = self.thi_mon.get()
        ngay = self.thi_ngay.get().strip()
        if not mon or not ngay:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng chọn môn học và nhập ngày thi.")
            return
        try:
            datetime.strptime(ngay, "%d/%m/%Y")
        except ValueError:
            messagebox.showwarning("Sai định dạng", "Ngày thi phải theo dạng dd/mm/yyyy.")
            return
        mon_id = int(mon.split(" - ")[0])
        gio = self.thi_gio.get().strip()
        phong = self.thi_phong.get().strip()
        hinhthuc = self.thi_hinhthuc.get().strip()

        canh_bao = []
        trung_thi = self.db.tim_xung_dot_lich_thi(ngay, gio)
        if trung_thi:
            ds = "\n".join(self._mo_ta_lich_thi(r) for r in trung_thi)
            canh_bao.append(f"Trùng lịch THI cùng ngày với:\n{ds}")
        trung_hoc, chinh_xac = self.db.tim_lich_hoc_trung_gio_thi(ngay, gio, mon_id)
        if trung_hoc:
            ds = "\n".join(self._mo_ta_lich_hoc(r) for r in trung_hoc)
            if chinh_xac:
                canh_bao.append(f"Giờ thi {gio} TRÙNG GIỜ HỌC của môn khác:\n{ds}")
            else:
                canh_bao.append(
                    f"Ngày thi {ngay} có LỊCH HỌC của môn khác "
                    f"(chưa đọc được giờ thi nên chưa so sánh chính xác):\n{ds}"
                )
        if canh_bao:
            if not messagebox.askyesno(
                "⚠ Cảnh báo trùng lịch",
                "\n\n".join(canh_bao) + "\n\nBạn vẫn muốn thêm lịch thi này?",
                icon="warning",
            ):
                return

        self.db.them_lich_thi(mon_id, ngay, gio, phong, hinhthuc)
        self.thi_ngay.delete(0, tk.END)
        self.thi_gio.delete(0, tk.END)
        self.thi_phong.delete(0, tk.END)
        self.refresh_lichthi()

    def xoa_lich_thi(self):
        selected = self.tree_thi.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn dòng cần xóa.")
            return
        item = self.tree_thi.item(selected[0])
        self.db.xoa_lich_thi(item["values"][0])
        self.refresh_lichthi()

    def refresh_lichthi(self):
        for row in self.tree_thi.get_children():
            self.tree_thi.delete(row)
        self.tree_thi.tag_configure("conflict", foreground="#c62828", background="#ffebee")
        self.tree_thi.tag_configure("hoc_cung_ngay", foreground="#e65100", background="#fff3e0")
        trung_thi, trung_hoc = self.db.lay_id_lich_thi_xung_dot()
        for lt in self.db.lay_lich_thi():
            if lt[0] in trung_thi:
                tags = ("conflict",)
            elif lt[0] in trung_hoc:
                tags = ("hoc_cung_ngay",)
            else:
                tags = ()
            self.tree_thi.insert("", "end", values=lt, tags=tags)

    # ================= TAB BÀI TẬP / DEADLINE =================
    def _build_tab_baitap(self):
        frame = self.tab_baitap
        form = ttk.LabelFrame(frame, text="Thêm bài tập / deadline", padding=10)
        form.pack(fill="x", padx=15, pady=10)

        ttk.Label(form, text="Môn học:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.bt_mon = ttk.Combobox(form, width=27, state="readonly")
        self.bt_mon.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Tiêu đề:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.bt_tieude = ttk.Entry(form, width=30)
        self.bt_tieude.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Hạn nộp (dd/mm/yyyy):").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.bt_han = ttk.Entry(form, width=27)
        self.bt_han.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Mức ưu tiên:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.bt_uutien = ttk.Combobox(form, values=PRIORITIES, width=27, state="readonly")
        self.bt_uutien.set("Trung bình")
        self.bt_uutien.grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(form, text="Mô tả:").grid(row=2, column=0, sticky="nw", padx=5, pady=5)
        self.bt_mota = tk.Text(form, width=60, height=3)
        self.bt_mota.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        ttk.Button(form, text="Thêm bài tập", command=self.them_bai_tap).grid(
            row=3, column=3, pady=5
        )

        list_frame = ttk.LabelFrame(frame, text="Danh sách bài tập", padding=10)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("id", "mon", "tieude", "han", "uutien", "trangthai")
        self.tree_bt = ttk.Treeview(list_frame, columns=cols, show="headings")
        headers = ["ID", "Môn học", "Tiêu đề", "Hạn nộp", "Ưu tiên", "Trạng thái"]
        widths = [40, 160, 220, 100, 90, 120]
        for c, h, w in zip(cols, headers, widths):
            self.tree_bt.heading(c, text=h)
            self.tree_bt.column(c, width=w, anchor="w")
        self.tree_bt.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_bt.yview)
        self.tree_bt.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", padx=15, pady=(0, 10))

        ttk.Label(btn_frame, text="Đổi trạng thái:").pack(side="left", padx=5)
        self.bt_trangthai_combo = ttk.Combobox(
            btn_frame, values=STATUSES, width=18, state="readonly"
        )
        self.bt_trangthai_combo.pack(side="left", padx=5)
        ttk.Button(
            btn_frame, text="Cập nhật", command=self.cap_nhat_trang_thai
        ).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Xóa bài tập đã chọn", command=self.xoa_bai_tap).pack(
            side="right", padx=5
        )

    def them_bai_tap(self):
        mon = self.bt_mon.get()
        tieude = self.bt_tieude.get().strip()
        han = self.bt_han.get().strip()
        if not tieude or not han:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập tiêu đề và hạn nộp.")
            return
        try:
            datetime.strptime(han, "%d/%m/%Y")
        except ValueError:
            messagebox.showwarning("Sai định dạng", "Hạn nộp phải theo dạng dd/mm/yyyy.")
            return
        mon_id = int(mon.split(" - ")[0]) if mon else None
        mota = self.bt_mota.get("1.0", tk.END).strip()
        uutien = self.bt_uutien.get()

        self.db.them_bai_tap(mon_id, tieude, mota, han, uutien)
        self.bt_tieude.delete(0, tk.END)
        self.bt_han.delete(0, tk.END)
        self.bt_mota.delete("1.0", tk.END)
        self.refresh_baitap()
        self.refresh_dashboard()

    def cap_nhat_trang_thai(self):
        selected = self.tree_bt.selection()
        trangthai = self.bt_trangthai_combo.get()
        if not selected or not trangthai:
            messagebox.showwarning("Chưa chọn", "Chọn bài tập và trạng thái cần cập nhật.")
            return
        item = self.tree_bt.item(selected[0])
        self.db.cap_nhat_trang_thai_bai_tap(item["values"][0], trangthai)
        self.refresh_baitap()
        self.refresh_dashboard()

    def xoa_bai_tap(self):
        selected = self.tree_bt.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn bài tập cần xóa.")
            return
        item = self.tree_bt.item(selected[0])
        self.db.xoa_bai_tap(item["values"][0])
        self.refresh_baitap()
        self.refresh_dashboard()

    def refresh_baitap(self):
        for row in self.tree_bt.get_children():
            self.tree_bt.delete(row)
        for bt in self.db.lay_danh_sach_bai_tap():
            bt_list = list(bt)
            if bt_list[1] is None:
                bt_list[1] = "(Không gắn môn)"
            row_id = self.tree_bt.insert("", "end", values=bt_list)

            # Tô màu cảnh báo theo hạn nộp và trạng thái
            try:
                han_date = datetime.strptime(bt_list[4], "%d/%m/%Y").date()
                today = date.today()
                so_ngay_con_lai = (han_date - today).days
                if bt_list[6] == "Hoàn thành":
                    self.tree_bt.tag_configure("done", foreground="#2e7d32")
                    self.tree_bt.item(row_id, tags=("done",))
                elif so_ngay_con_lai < 0:
                    self.tree_bt.tag_configure("overdue", foreground="#c62828")
                    self.tree_bt.item(row_id, tags=("overdue",))
                elif so_ngay_con_lai <= 3:
                    self.tree_bt.tag_configure("urgent", foreground="#e65100")
                    self.tree_bt.item(row_id, tags=("urgent",))
            except ValueError:
                pass

    # ================= TAB GHI CHÚ =================
    def _build_tab_ghichu(self):
        frame = self.tab_ghichu
        form = ttk.LabelFrame(frame, text="Thêm ghi chú bài giảng", padding=10)
        form.pack(fill="x", padx=15, pady=10)

        ttk.Label(form, text="Môn học:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.gc_mon = ttk.Combobox(form, width=27, state="readonly")
        self.gc_mon.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Tiêu đề:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.gc_tieude = ttk.Entry(form, width=30)
        self.gc_tieude.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Nội dung:").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self.gc_noidung = tk.Text(form, width=70, height=5)
        self.gc_noidung.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        ttk.Button(form, text="Lưu ghi chú", command=self.them_ghi_chu).grid(
            row=2, column=3, pady=5
        )

        list_frame = ttk.LabelFrame(frame, text="Danh sách ghi chú", padding=10)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("id", "mon", "tieude", "noidung", "ngay")
        self.tree_gc = ttk.Treeview(list_frame, columns=cols, show="headings")
        headers = ["ID", "Môn học", "Tiêu đề", "Nội dung", "Ngày tạo"]
        widths = [40, 150, 180, 280, 100]
        for c, h, w in zip(cols, headers, widths):
            self.tree_gc.heading(c, text=h)
            self.tree_gc.column(c, width=w, anchor="w")
        self.tree_gc.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_gc.yview)
        self.tree_gc.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(frame, text="Xóa ghi chú đã chọn", command=self.xoa_ghi_chu).pack(
            anchor="e", padx=15, pady=(0, 10)
        )

    def them_ghi_chu(self):
        mon = self.gc_mon.get()
        tieude = self.gc_tieude.get().strip()
        noidung = self.gc_noidung.get("1.0", tk.END).strip()
        if not tieude:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập tiêu đề ghi chú.")
            return
        mon_id = int(mon.split(" - ")[0]) if mon else None
        ngay_tao = date.today().strftime("%d/%m/%Y")

        self.db.them_ghi_chu(mon_id, tieude, noidung, ngay_tao)
        self.gc_tieude.delete(0, tk.END)
        self.gc_noidung.delete("1.0", tk.END)
        self.refresh_ghichu()
        self.refresh_dashboard()

    def xoa_ghi_chu(self):
        selected = self.tree_gc.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn ghi chú cần xóa.")
            return
        item = self.tree_gc.item(selected[0])
        self.db.xoa_ghi_chu(item["values"][0])
        self.refresh_ghichu()
        self.refresh_dashboard()

    def refresh_ghichu(self):
        for row in self.tree_gc.get_children():
            self.tree_gc.delete(row)
        for gc in self.db.lay_danh_sach_ghi_chu():
            gc_list = list(gc)
            if gc_list[1] is None:
                gc_list[1] = "(Không gắn môn)"
            if gc_list[3] and len(gc_list[3]) > 60:
                gc_list[3] = gc_list[3][:60] + "..."
            self.tree_gc.insert("", "end", values=gc_list)

    # ================= DASHBOARD =================
    def refresh_dashboard(self):
        mon_list = self.db.lay_danh_sach_mon_hoc()
        bai_tap_list = self.db.lay_danh_sach_bai_tap(chi_chua_hoan_thanh=True)
        lich_thi_list = self.db.lay_lich_thi()
        ghi_chu_list = self.db.lay_danh_sach_ghi_chu()
        self.card_mon.config(text=str(len(mon_list)))
        self.card_baitap.config(text=str(len(bai_tap_list)))
        # Đếm lịch thi sắp tới (từ hôm nay trở đi)
        today = date.today()
        sap_toi = 0
        for lt in lich_thi_list:
            try:
                ngay_thi = datetime.strptime(lt[2], "%d/%m/%Y").date()
                if ngay_thi >= today:
                    sap_toi += 1
            except ValueError:
                pass
        self.card_thi.config(text=str(sap_toi))
        self.card_ghichu.config(text=str(len(ghi_chu_list)))
        # Danh sách deadline trong 7 ngày tới
        for row in self.tree_deadline.get_children():
            self.tree_deadline.delete(row)
        for bt in bai_tap_list:
            try:
                han_date = datetime.strptime(bt[4], "%d/%m/%Y").date()
                so_ngay = (han_date - today).days
                if 0 <= so_ngay <= 7:
                    mon_ten = bt[1] if bt[1] else "(Không gắn môn)"
                    self.tree_deadline.insert(
                        "", "end", values=(mon_ten, bt[2], bt[4], bt[5])
                    )
            except ValueError:
                pass

    # ================= REFRESH TẤT CẢ =================
    def refresh_all(self):
        self.refresh_monhoc()
        self.refresh_tkb()
        self.refresh_lichthi()
        self.refresh_baitap()
        self.refresh_ghichu()
        self.refresh_dashboard()

    def on_close(self):
        self.db.dong()
        self.destroy()

if __name__ == "__main__":
    app = QLHTApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
