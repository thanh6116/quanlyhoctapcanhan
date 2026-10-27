import sqlite3
import os
import re
import shutil
import unicodedata
from datetime import datetime

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qlht.db")

# Hai lịch thi cùng ngày có giờ bắt đầu cách nhau dưới số phút này được xem là trùng
SO_PHUT_THI_TOI_THIEU = 90
TEN_THU = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]


# Giờ bắt đầu - kết thúc của từng tiết học (tính bằng phút kể từ 0h)
TIET_GIO = {
    1: (7 * 60, 7 * 60 + 50),
    2: (8 * 60, 8 * 60 + 50),
    3: (9 * 60, 9 * 60 + 50),
    4: (10 * 60, 10 * 60 + 50),
    5: (12 * 60, 12 * 60 + 50),
    6: (13 * 60, 13 * 60 + 50),
    7: (14 * 60, 14 * 60 + 50),
    8: (15 * 60, 15 * 60 + 50),
    9: (16 * 60, 16 * 60 + 50),
    10: (17 * 60, 17 * 60 + 50),
    11: (18 * 60, 18 * 60 + 50),
    12: (19 * 60, 19 * 60 + 50),
}


def _khoang_gio_tiet(tiet_bd, tiet_kt):
    """(phút bắt đầu, phút kết thúc) của khoảng tiết. Tiết ngoài bảng giờ thì trả về None."""
    if tiet_bd not in TIET_GIO or tiet_kt not in TIET_GIO:
        return None
    return TIET_GIO[tiet_bd][0], TIET_GIO[tiet_kt][1]


def khoang_lich_hoc(tiet_bd, tiet_kt, gio_bd=None, gio_kt=None):
    """(phút bắt đầu, phút kết thúc) của một lịch học.

    Lịch nhập theo giờ (gio_bd, gio_kt có giá trị) thì dùng đúng giờ đã nhập;
    ngược lại đổi từ tiết qua bảng TIET_GIO. Không xác định được thì trả về None.
    """
    if gio_bd and gio_kt:
        bd, kt = _gio_ra_phut(gio_bd), _gio_ra_phut(gio_kt)
        return (bd, kt) if bd is not None and kt is not None else None
    return _khoang_gio_tiet(tiet_bd, tiet_kt)


def lich_hoc_trung(a, b):
    """Hai lịch học (cùng thứ) có chồng giờ không? a, b = (tiet_bd, tiet_kt, gio_bd, gio_kt).

    - Biết được giờ của cả hai: so sánh khoảng giờ nửa mở, học xong đúng lúc bắt đầu tiết
      sau thì không trùng.
    - Không biết giờ nhưng cả hai đều theo tiết: so sánh số tiết như cũ.
    - Còn lại (không đủ thông tin): coi là có thể trùng.
    """
    ka, kb = khoang_lich_hoc(*a), khoang_lich_hoc(*b)
    if ka is not None and kb is not None:
        return ka[0] < kb[1] and kb[0] < ka[1]
    if not (a[2] or a[3] or b[2] or b[3]):
        return a[0] <= b[1] and b[0] <= a[1]
    return True


def _phut_ra_gio(phut):
    return f"{phut // 60}h{phut % 60:02d}"


def mo_ta_gio_tiet(tiet_bd, tiet_kt):
    """Ví dụ (1, 3) -> '7h00-9h50'. Tiết ngoài bảng giờ thì trả về 'chưa rõ giờ'."""
    khoang = _khoang_gio_tiet(tiet_bd, tiet_kt)
    if khoang is None:
        return "chưa rõ giờ"
    return f"{_phut_ra_gio(khoang[0])}-{_phut_ra_gio(khoang[1])}"


def mo_ta_gio_lich_hoc(tiet_bd, tiet_kt, gio_bd=None, gio_kt=None):
    """Giờ học dạng '7h00-9h50' cho cả lịch theo tiết lẫn lịch nhập giờ tay."""
    khoang = khoang_lich_hoc(tiet_bd, tiet_kt, gio_bd, gio_kt)
    if khoang is None:
        return "chưa rõ giờ"
    return f"{_phut_ra_gio(khoang[0])}-{_phut_ra_gio(khoang[1])}"


def mo_ta_thoi_gian_hoc(tiet_bd, tiet_kt, gio_bd=None, gio_kt=None):
    """'tiết 1-3, 7h00-9h50' (theo tiết) hoặc '7h30-9h15' (nhập giờ tay)."""
    gio = mo_ta_gio_lich_hoc(tiet_bd, tiet_kt, gio_bd, gio_kt)
    if gio_bd and gio_kt:
        return gio
    return f"tiết {tiet_bd}-{tiet_kt}, {gio}"


def _hoc_trung_gio_thi(phut_bat_dau_thi, tiet_bd, tiet_kt, gio_bd=None, gio_kt=None):
    """Bài thi (giả định kéo dài SO_PHUT_THI_TOI_THIEU phút) có chồng lên giờ học không."""
    khoang = khoang_lich_hoc(tiet_bd, tiet_kt, gio_bd, gio_kt)
    if khoang is None:
        return True
    hoc_bd, hoc_kt = khoang
    return phut_bat_dau_thi < hoc_kt and hoc_bd < phut_bat_dau_thi + SO_PHUT_THI_TOI_THIEU


def _gio_ra_phut(text):
    """Đổi giờ dạng '07:30', '7h30', '7h' thành số phút trong ngày. Không đọc được thì trả về None."""
    m = re.search(r"(\d{1,2})\s*[:hH]\s*(\d{2})?", text or "")
    if not m:
        return None
    gio = int(m.group(1))
    phut = int(m.group(2)) if m.group(2) else 0
    if gio > 23 or phut > 59:
        return None
    return gio * 60 + phut


def chuan_hoa_gio(text):
    """'7h30' -> '07:30'. Không đọc được thì trả về None."""
    phut = _gio_ra_phut(text)
    if phut is None:
        return None
    return f"{phut // 60:02d}:{phut % 60:02d}"


def _thu_cua_ngay(ngay):
    """'26/10/2026' -> 'Thứ 2'. Sai định dạng thì trả về None."""
    try:
        return TEN_THU[datetime.strptime(ngay, "%d/%m/%Y").weekday()]
    except (ValueError, TypeError):
        return None


def _trung_gio_thi(gio_a, gio_b):
    """Hai giờ thi coi là trùng nếu quá gần nhau hoặc không xác định được giờ."""
    a, b = _gio_ra_phut(gio_a), _gio_ra_phut(gio_b)
    if a is None or b is None:
        return True
    return abs(a - b) < SO_PHUT_THI_TOI_THIEU


def _bo_dau(text):
    """Bỏ dấu tiếng Việt và chuyển về chữ thường để so khớp khi tìm kiếm."""
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D").lower()

# Ký tự đặc biệt vẫn được giữ lại khi so tên, vì chúng phân biệt môn học thật
# (ví dụ "Lập trình C", "Lập trình C++", "Lập trình C#" là ba môn khác nhau).
_KY_TU_GIU_LAI = "+#"


def _chuan_hoa_ten(text):
    """Chuẩn hóa tên để so sánh trùng: bỏ dấu, chữ thường, bỏ khoảng trắng và ký tự đặc biệt.

    'OOP' = 'O o p'; 'HỆ điều HÀnh' = 'Hệ điều hành'; 'MẠng@máy tính' = 'mạng máy tính'.
    Chỉ giữ lại chữ cái, chữ số và các ký tự trong _KY_TU_GIU_LAI.
    """
    return "".join(c for c in _bo_dau(text) if c.isalnum() or c in _KY_TU_GIU_LAI)


chuan_hoa_ten_mon = _chuan_hoa_ten


def ten_mon_hop_le(text):
    """Tên môn phải có ít nhất một chữ cái hoặc chữ số (không chỉ toàn dấu cách, ký tự lạ)."""
    return bool(_chuan_hoa_ten(text))


_RE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _ngay_vao(ngay):
    """'5/1/2026' hoặc '05/01/2026' -> '2026-01-05' (lưu dạng ISO để sắp xếp đúng thời gian).
    Giá trị đã là ISO hoặc không đọc được thì giữ nguyên."""
    if not ngay or _RE_ISO.match(ngay):
        return ngay
    try:
        return datetime.strptime(ngay, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return ngay


def _ngay_ra(ngay):
    """'2026-01-05' -> '05/01/2026' (dạng hiển thị trên giao diện)."""
    if ngay and _RE_ISO.match(ngay):
        try:
            return datetime.strptime(ngay, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return ngay
    return ngay


def _doi_cot_ngay(rows, vi_tri):
    """Đổi cột ngày ở vị trí `vi_tri` của mọi dòng từ ISO sang dd/mm/yyyy."""
    ket_qua = []
    for r in rows:
        r = list(r)
        r[vi_tri] = _ngay_ra(r[vi_tri])
        ket_qua.append(tuple(r))
    return ket_qua


class Database:
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._chuyen_ngay_sang_iso()

    def _chuyen_ngay_sang_iso(self):
        """Đổi ngày dd/mm/yyyy cũ trong CSDL sang yyyy-mm-dd. Chạy lại nhiều lần vẫn an toàn."""
        cac_cot = [("lich_thi", "ngay_thi"), ("bai_tap", "han_nop"), ("ghi_chu", "ngay_tao")]
        can_doi = []
        for bang, cot in cac_cot:
            self.cursor.execute(f"SELECT id, {cot} FROM {bang}")
            for id_, ngay in self.cursor.fetchall():
                moi = _ngay_vao(ngay)
                if moi != ngay:
                    can_doi.append((bang, cot, id_, moi))
        if not can_doi:
            return
        if os.path.exists(self.db_path):  # sao lưu một bản trước khi đổi
            shutil.copyfile(self.db_path, self.db_path + ".bak")
        for bang, cot, id_, moi in can_doi:
            self.cursor.execute(f"UPDATE {bang} SET {cot}=? WHERE id=?", (moi, id_))
        self.conn.commit()

    def _create_tables(self):
        """Tạo các bảng dữ liệu nếu có"""
        #bảng môn học
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mon_hoc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten_mon TEXT NOT NULL,
                so_tin_chi INTEGER DEFAULT 0,
                giang_vien TEXT,
                ghi_chu TEXT
            )
        """)
        #bảng lịch học 
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lich_hoc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mon_hoc_id INTEGER NOT NULL,
                thu TEXT NOT NULL,
                tiet_bat_dau INTEGER NOT NULL,
                tiet_ket_thuc INTEGER NOT NULL,
                phong_hoc TEXT,
                gio_bat_dau TEXT,
                gio_ket_thuc TEXT,
                FOREIGN KEY (mon_hoc_id) REFERENCES mon_hoc(id) ON DELETE CASCADE
            )
        """)
        # CSDL tạo từ phiên bản cũ chưa có hai cột giờ: thêm vào (không mất dữ liệu)
        self._them_cot_neu_thieu("lich_hoc", "gio_bat_dau", "TEXT")
        self._them_cot_neu_thieu("lich_hoc", "gio_ket_thuc", "TEXT")

        #bảng lịch thi
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lich_thi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mon_hoc_id INTEGER NOT NULL,
                ngay_thi TEXT NOT NULL,
                gio_thi TEXT,
                phong_thi TEXT,
                hinh_thuc TEXT,
                FOREIGN KEY (mon_hoc_id) REFERENCES mon_hoc(id) ON DELETE CASCADE
            )
        """)
        #bảng deadline
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bai_tap (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mon_hoc_id INTEGER,
                tieu_de TEXT NOT NULL,
                mo_ta TEXT,
                han_nop TEXT NOT NULL,
                muc_do_uu_tien TEXT DEFAULT 'Trung bình',
                trang_thai TEXT DEFAULT 'Chưa hoàn thành',
                FOREIGN KEY (mon_hoc_id) REFERENCES mon_hoc(id) ON DELETE SET NULL
            )
        """)

        #bảng ghi chú 
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ghi_chu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mon_hoc_id INTEGER,
                tieu_de TEXT NOT NULL,
                noi_dung TEXT,
                ngay_tao TEXT NOT NULL,
                FOREIGN KEY (mon_hoc_id) REFERENCES mon_hoc(id) ON DELETE SET NULL
            )
        """)

        self.conn.commit()

    def _them_cot_neu_thieu(self, bang, cot, kieu):
        self.cursor.execute(f"PRAGMA table_info({bang})")
        if cot not in [c[1] for c in self.cursor.fetchall()]:
            self.cursor.execute(f"ALTER TABLE {bang} ADD COLUMN {cot} {kieu}")

    def _id_nho_nhat_con_trong(self, ten_bang):
        """Tìm ID nhỏ nhất chưa được dùng trong bảng (1, 2, 3, ...)."""
        self.cursor.execute(f"SELECT id FROM {ten_bang} ORDER BY id")
        new_id = 1
        for (used_id,) in self.cursor.fetchall():
            if used_id != new_id:
                break
            new_id += 1
        return new_id

    # tên môn học
    def them_mon_hoc(self, ten_mon, so_tin_chi, giang_vien, ghi_chu=""):
        new_id = self._id_nho_nhat_con_trong("mon_hoc")
        self.cursor.execute(
            "INSERT INTO mon_hoc (id, ten_mon, so_tin_chi, giang_vien, ghi_chu) "
            "VALUES (?, ?, ?, ?, ?)",
            (new_id, ten_mon, so_tin_chi, giang_vien, ghi_chu),
        )
        self.conn.commit()
        return new_id

    def lay_danh_sach_mon_hoc(self):
        self.cursor.execute("SELECT * FROM mon_hoc ORDER BY id")
        return self.cursor.fetchall()

    def lay_mon_hoc(self, mon_hoc_id):
        """Lấy thông tin một môn học theo ID."""
        self.cursor.execute("SELECT * FROM mon_hoc WHERE id = ?", (mon_hoc_id,))
        return self.cursor.fetchone()

    def tim_kiem_mon_hoc(self, tu_khoa):
        """Tìm môn học theo tên (không phân biệt hoa thường và dấu)."""
        danh_sach = self.lay_danh_sach_mon_hoc()
        tu_khoa = (tu_khoa or "").strip()
        if not tu_khoa:
            return danh_sach
        goc = _bo_dau(tu_khoa)
        gon = _chuan_hoa_ten(tu_khoa)  # gõ "oop" vẫn tìm ra "O o p"
        return [
            m for m in danh_sach
            if goc in _bo_dau(m[1]) or (gon and gon in _chuan_hoa_ten(m[1]))
        ]

    def tim_mon_trung_ten(self, ten_mon, bo_qua_id=None):
        """Trả về môn học đã có cùng tên (không phân biệt hoa thường, dấu, khoảng trắng thừa)."""
        ten = _chuan_hoa_ten(ten_mon)
        for m in self.lay_danh_sach_mon_hoc():
            if m[0] != bo_qua_id and _chuan_hoa_ten(m[1]) == ten:
                return m
        return None

    def xoa_mon_hoc(self, mon_hoc_id):
        self.cursor.execute("DELETE FROM mon_hoc WHERE id = ?", (mon_hoc_id,))
        self.conn.commit()

    def sua_mon_hoc(self, mon_hoc_id, ten_mon, so_tin_chi, giang_vien, ghi_chu):
        self.cursor.execute(
            "UPDATE mon_hoc SET ten_mon=?, so_tin_chi=?, giang_vien=?, ghi_chu=? WHERE id=?",
            (ten_mon, so_tin_chi, giang_vien, ghi_chu, mon_hoc_id),
        )
        self.conn.commit()

    # lịch học
    @staticmethod
    def _gia_tri_thoi_gian_hoc(tiet_bd, tiet_kt, gio_bd, gio_kt):
        """Lịch nhập giờ tay: lưu tiết = 0 (cột tiết bắt buộc có giá trị) cùng hai giờ HH:MM."""
        if gio_bd and gio_kt:
            return 0, 0, chuan_hoa_gio(gio_bd), chuan_hoa_gio(gio_kt)
        return tiet_bd, tiet_kt, None, None

    def them_lich_hoc(self, mon_hoc_id, thu, tiet_bd, tiet_kt, phong_hoc,
                      gio_bd=None, gio_kt=None):
        """Thêm lịch học theo tiết (tiet_bd, tiet_kt) hoặc theo giờ nhập tay (gio_bd, gio_kt)."""
        tiet_bd, tiet_kt, gio_bd, gio_kt = self._gia_tri_thoi_gian_hoc(
            tiet_bd, tiet_kt, gio_bd, gio_kt
        )
        self.cursor.execute(
            "INSERT INTO lich_hoc (mon_hoc_id, thu, tiet_bat_dau, tiet_ket_thuc, phong_hoc, "
            "gio_bat_dau, gio_ket_thuc) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (mon_hoc_id, thu, tiet_bd, tiet_kt, phong_hoc, gio_bd, gio_kt),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def tim_xung_dot_lich_hoc(self, thu, tiet_bd, tiet_kt, bo_qua_id=None,
                              gio_bd=None, gio_kt=None):
        """Các lịch học cùng thứ và chồng giờ với lịch (tiết hoặc giờ nhập tay) đưa vào."""
        moi = (tiet_bd, tiet_kt, gio_bd, gio_kt)
        return [
            r for r in self._lich_hoc_cung_thu(thu)
            if r[0] != bo_qua_id and lich_hoc_trung(moi, (r[3], r[4], r[6], r[7]))
        ]

    def _lich_hoc_cung_thu(self, thu, mon_hoc_id=None, loai_tru_mon=False):
        """Các lịch học của một thứ, dạng (id, ten_mon, thu, tiet_bd, tiet_kt, phong, gio_bd, gio_kt)."""
        sql = """
            SELECT lich_hoc.id, mon_hoc.ten_mon, lich_hoc.thu,
                   lich_hoc.tiet_bat_dau, lich_hoc.tiet_ket_thuc, lich_hoc.phong_hoc,
                   lich_hoc.gio_bat_dau, lich_hoc.gio_ket_thuc
            FROM lich_hoc
            JOIN mon_hoc ON lich_hoc.mon_hoc_id = mon_hoc.id
            WHERE lich_hoc.thu = ?
        """
        tham_so = [thu]
        if loai_tru_mon:
            sql += " AND lich_hoc.mon_hoc_id IS NOT ?"
            tham_so.append(mon_hoc_id)
        self.cursor.execute(sql, tham_so)
        return self.cursor.fetchall()

    def lay_id_lich_hoc_xung_dot(self):
        """Tập ID các lịch học đang trùng với một lịch học khác."""
        ds = self.lay_thoi_khoa_bieu()
        ids = set()
        for i, a in enumerate(ds):
            for b in ds[i + 1:]:
                if a[2] == b[2] and lich_hoc_trung(
                    (a[3], a[4], a[6], a[7]), (b[3], b[4], b[6], b[7])
                ):
                    ids.update((a[0], b[0]))
        return ids

    def lay_thoi_khoa_bieu(self):
        """Trả về (id, ten_mon, thu, tiet_bd, tiet_kt, phong, gio_bd, gio_kt), xếp theo thứ rồi giờ học."""
        self.cursor.execute("""
            SELECT lich_hoc.id, mon_hoc.ten_mon, lich_hoc.thu,
                   lich_hoc.tiet_bat_dau, lich_hoc.tiet_ket_thuc, lich_hoc.phong_hoc,
                   lich_hoc.gio_bat_dau, lich_hoc.gio_ket_thuc
            FROM lich_hoc
            JOIN mon_hoc ON lich_hoc.mon_hoc_id = mon_hoc.id
        """)
        rows = self.cursor.fetchall()

        def khoa(r):
            thu = TEN_THU.index(r[2]) if r[2] in TEN_THU else len(TEN_THU)
            khoang = khoang_lich_hoc(r[3], r[4], r[6], r[7])
            return (thu, khoang[0] if khoang else 24 * 60, r[0])

        rows.sort(key=khoa)  # lịch nhập theo giờ và lịch theo tiết xếp chung đúng thứ tự giờ
        return rows

    def lay_lich_hoc(self, lich_id):
        """Trả về (id, mon_hoc_id, thu, tiet_bd, tiet_kt, phong_hoc, gio_bd, gio_kt) của một lịch học."""
        self.cursor.execute(
            "SELECT id, mon_hoc_id, thu, tiet_bat_dau, tiet_ket_thuc, phong_hoc, "
            "gio_bat_dau, gio_ket_thuc FROM lich_hoc WHERE id = ?",
            (lich_id,),
        )
        return self.cursor.fetchone()

    def sua_lich_hoc(self, lich_id, mon_hoc_id, thu, tiet_bd, tiet_kt, phong_hoc,
                     gio_bd=None, gio_kt=None):
        tiet_bd, tiet_kt, gio_bd, gio_kt = self._gia_tri_thoi_gian_hoc(
            tiet_bd, tiet_kt, gio_bd, gio_kt
        )
        self.cursor.execute(
            "UPDATE lich_hoc SET mon_hoc_id=?, thu=?, tiet_bat_dau=?, tiet_ket_thuc=?, "
            "phong_hoc=?, gio_bat_dau=?, gio_ket_thuc=? WHERE id=?",
            (mon_hoc_id, thu, tiet_bd, tiet_kt, phong_hoc, gio_bd, gio_kt, lich_id),
        )
        self.conn.commit()

    def xoa_lich_hoc(self, lich_id):
        self.cursor.execute("DELETE FROM lich_hoc WHERE id = ?", (lich_id,))
        self.conn.commit()

    # lịch thi
    def them_lich_thi(self, mon_hoc_id, ngay_thi, gio_thi, phong_thi, hinh_thuc):
        self.cursor.execute(
            "INSERT INTO lich_thi (mon_hoc_id, ngay_thi, gio_thi, phong_thi, hinh_thuc) VALUES (?, ?, ?, ?, ?)",
            (mon_hoc_id, _ngay_vao(ngay_thi), gio_thi, phong_thi, hinh_thuc),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def lay_lich_thi(self):
           self.cursor.execute("""
               SELECT lich_thi.id, mon_hoc.ten_mon, lich_thi.ngay_thi,
                      lich_thi.gio_thi, lich_thi.phong_thi, lich_thi.hinh_thuc
               FROM lich_thi
               JOIN mon_hoc ON lich_thi.mon_hoc_id = mon_hoc.id
           """)
           rows = self.cursor.fetchall()

           def khoa(r):
               phut = _gio_ra_phut(r[3])
               return (r[2], phut if phut is not None else 24 * 60, r[0])

           rows.sort(key=khoa)  # giờ không đọc được thì xếp cuối ngày
           return _doi_cot_ngay(rows, 2)

    def tim_xung_dot_lich_thi(self, ngay_thi, gio_thi, bo_qua_id=None):
        """Các lịch thi cùng ngày và có giờ thi trùng hoặc quá sát với giờ thi đưa vào."""
        self.cursor.execute("""
            SELECT lich_thi.id, mon_hoc.ten_mon, lich_thi.ngay_thi,
                   lich_thi.gio_thi, lich_thi.phong_thi, lich_thi.hinh_thuc
            FROM lich_thi
            JOIN mon_hoc ON lich_thi.mon_hoc_id = mon_hoc.id
            WHERE lich_thi.ngay_thi = ?
        """, (_ngay_vao(ngay_thi),))
        return [
            r for r in _doi_cot_ngay(self.cursor.fetchall(), 2)
            if r[0] != bo_qua_id and _trung_gio_thi(gio_thi, r[3])
        ]

    def tim_lich_hoc_trong_ngay_thi(self, ngay_thi, mon_hoc_id=None):
        """Lịch học của các môn KHÁC rơi vào cùng thứ với ngày thi."""
        thu = _thu_cua_ngay(ngay_thi)
        if thu is None:
            return []
        return self._lich_hoc_cung_thu(thu, mon_hoc_id, loai_tru_mon=True)

    def tim_lich_hoc_trung_gio_thi(self, ngay_thi, gio_thi, mon_hoc_id=None):
        """Lịch học (môn khác) ảnh hưởng tới lịch thi.

        Trả về (danh sách, chinh_xac):
        - chinh_xac=True : đọc được giờ thi, danh sách là các lịch học THẬT SỰ trùng giờ thi.
        - chinh_xac=False: không đọc được giờ thi, danh sách là mọi lịch học của môn khác cùng ngày.
        """
        cung_ngay = self.tim_lich_hoc_trong_ngay_thi(ngay_thi, mon_hoc_id)
        bat_dau = _gio_ra_phut(gio_thi)
        if bat_dau is None:
            return cung_ngay, False
        return [
            r for r in cung_ngay if _hoc_trung_gio_thi(bat_dau, r[3], r[4], r[6], r[7])
        ], True

    def lay_id_lich_thi_xung_dot(self):
        """Trả về (ID tô đỏ, ID tô cam).

        - Đỏ : lịch thi trùng lịch thi khác, hoặc giờ thi trùng giờ học của môn khác.
        - Cam: không đọc được giờ thi nhưng ngày thi có lịch học của môn khác.
        """
        self.cursor.execute(
            "SELECT id, mon_hoc_id, ngay_thi, gio_thi FROM lich_thi"
        )
        thi = _doi_cot_ngay(self.cursor.fetchall(), 2)
        self.cursor.execute(
            "SELECT mon_hoc_id, thu, tiet_bat_dau, tiet_ket_thuc, gio_bat_dau, gio_ket_thuc "
            "FROM lich_hoc"
        )
        hoc = self.cursor.fetchall()

        do, cam = set(), set()
        for i, a in enumerate(thi):
            for b in thi[i + 1:]:
                if a[2] == b[2] and _trung_gio_thi(a[3], b[3]):
                    do.update((a[0], b[0]))

            thu = _thu_cua_ngay(a[2])
            cung_ngay = [h for h in hoc if h[1] == thu and h[0] != a[1]] if thu else []
            if not cung_ngay:
                continue
            bat_dau = _gio_ra_phut(a[3])
            if bat_dau is None:
                cam.add(a[0])
            elif any(_hoc_trung_gio_thi(bat_dau, h[2], h[3], h[4], h[5]) for h in cung_ngay):
                do.add(a[0])
        return do, cam

    def lay_lich_thi_theo_id(self, thi_id):
        """Trả về (id, mon_hoc_id, ngay_thi, gio_thi, phong_thi, hinh_thuc) của một lịch thi."""
        self.cursor.execute(
            "SELECT id, mon_hoc_id, ngay_thi, gio_thi, phong_thi, hinh_thuc "
            "FROM lich_thi WHERE id = ?",
            (thi_id,),
        )
        row = self.cursor.fetchone()
        return _doi_cot_ngay([row], 2)[0] if row else None

    def sua_lich_thi(self, thi_id, mon_hoc_id, ngay_thi, gio_thi, phong_thi, hinh_thuc):
        self.cursor.execute(
            "UPDATE lich_thi SET mon_hoc_id=?, ngay_thi=?, gio_thi=?, phong_thi=?, hinh_thuc=? "
            "WHERE id=?",
            (mon_hoc_id, _ngay_vao(ngay_thi), gio_thi, phong_thi, hinh_thuc, thi_id),
        )
        self.conn.commit()

    def xoa_lich_thi(self, thi_id):
        self.cursor.execute("DELETE FROM lich_thi WHERE id = ?", (thi_id,))
        self.conn.commit()

    # deadline
    def them_bai_tap(self, mon_hoc_id, tieu_de, mo_ta, han_nop, muc_do_uu_tien):
        self.cursor.execute(
            """INSERT INTO bai_tap (mon_hoc_id, tieu_de, mo_ta, han_nop, muc_do_uu_tien, trang_thai)
               VALUES (?, ?, ?, ?, ?, 'Chưa hoàn thành')""",
            (mon_hoc_id, tieu_de, mo_ta, _ngay_vao(han_nop), muc_do_uu_tien),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def lay_danh_sach_bai_tap(self, chi_chua_hoan_thanh=False):
        query = """
            SELECT bai_tap.id, mon_hoc.ten_mon, bai_tap.tieu_de, bai_tap.mo_ta,
                   bai_tap.han_nop, bai_tap.muc_do_uu_tien, bai_tap.trang_thai
            FROM bai_tap
            LEFT JOIN mon_hoc ON bai_tap.mon_hoc_id = mon_hoc.id
        """
        if chi_chua_hoan_thanh:
            query += " WHERE bai_tap.trang_thai != 'Hoàn thành'"
        query += " ORDER BY bai_tap.han_nop, bai_tap.id"
        self.cursor.execute(query)
        return _doi_cot_ngay(self.cursor.fetchall(), 4)

    def lay_bai_tap(self, bai_tap_id):
        """Trả về (id, mon_hoc_id, tieu_de, mo_ta, han_nop, muc_do_uu_tien, trang_thai)."""
        self.cursor.execute(
            "SELECT id, mon_hoc_id, tieu_de, mo_ta, han_nop, muc_do_uu_tien, trang_thai "
            "FROM bai_tap WHERE id = ?",
            (bai_tap_id,),
        )
        row = self.cursor.fetchone()
        return _doi_cot_ngay([row], 4)[0] if row else None

    def sua_bai_tap(self, bai_tap_id, mon_hoc_id, tieu_de, mo_ta, han_nop,
                    muc_do_uu_tien, trang_thai):
        self.cursor.execute(
            "UPDATE bai_tap SET mon_hoc_id=?, tieu_de=?, mo_ta=?, han_nop=?, "
            "muc_do_uu_tien=?, trang_thai=? WHERE id=?",
            (mon_hoc_id, tieu_de, mo_ta, _ngay_vao(han_nop),
             muc_do_uu_tien, trang_thai, bai_tap_id),
        )
        self.conn.commit()

    def cap_nhat_trang_thai_bai_tap(self, bai_tap_id, trang_thai):
        self.cursor.execute(
            "UPDATE bai_tap SET trang_thai=? WHERE id=?", (trang_thai, bai_tap_id)
        )
        self.conn.commit()

    def xoa_bai_tap(self, bai_tap_id):
        self.cursor.execute("DELETE FROM bai_tap WHERE id = ?", (bai_tap_id,))
        self.conn.commit()

    # chú thích thêm
    def them_ghi_chu(self, mon_hoc_id, tieu_de, noi_dung, ngay_tao):
        self.cursor.execute(
            "INSERT INTO ghi_chu (mon_hoc_id, tieu_de, noi_dung, ngay_tao) VALUES (?, ?, ?, ?)",
            (mon_hoc_id, tieu_de, noi_dung, _ngay_vao(ngay_tao)),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def lay_danh_sach_ghi_chu(self):
        self.cursor.execute("""
            SELECT ghi_chu.id, mon_hoc.ten_mon, ghi_chu.tieu_de, ghi_chu.noi_dung, ghi_chu.ngay_tao
            FROM ghi_chu
            LEFT JOIN mon_hoc ON ghi_chu.mon_hoc_id = mon_hoc.id
            ORDER BY ghi_chu.ngay_tao DESC, ghi_chu.id DESC
        """)
        return _doi_cot_ngay(self.cursor.fetchall(), 4)

    def lay_ghi_chu(self, ghi_chu_id):
        """Trả về (id, mon_hoc_id, tieu_de, noi_dung, ngay_tao) của một ghi chú."""
        self.cursor.execute(
            "SELECT id, mon_hoc_id, tieu_de, noi_dung, ngay_tao FROM ghi_chu WHERE id = ?",
            (ghi_chu_id,),
        )
        row = self.cursor.fetchone()
        return _doi_cot_ngay([row], 4)[0] if row else None

    def sua_ghi_chu(self, ghi_chu_id, mon_hoc_id, tieu_de, noi_dung):
        self.cursor.execute(
            "UPDATE ghi_chu SET mon_hoc_id=?, tieu_de=?, noi_dung=? WHERE id=?",
            (mon_hoc_id, tieu_de, noi_dung, ghi_chu_id),
        )
        self.conn.commit()

    def xoa_ghi_chu(self, ghi_chu_id):
        self.cursor.execute("DELETE FROM ghi_chu WHERE id = ?", (ghi_chu_id,))
        self.conn.commit()

    def dong(self):
        self.conn.close()
